"""Build actual RTL, run directed/random programs, compare against a sequential ISA model.
Usage (repo root): python chapters/04-processor-core/code/04-pipeline/run.py
Requires Python 3.10+ and Icarus Verilog (iverilog/vvp).
All generated files are placed under build/rtl-pipeline/.
"""
from pathlib import Path
import csv
import json
import random
import subprocess

SRC = Path(__file__).resolve().parent
ROOT = SRC.parents[3]
BUILD = ROOT / 'build/rtl-pipeline'
MASK = 0xffffffff


def encode(op, rd=0, a=0, b=0, imm=0):
    if op in ('add', 'sub'):
        return ((0x20 if op == 'sub' else 0) << 25) | b << 20 | a << 15 | rd << 7 | 0x33
    if op in ('addi', 'lw'):
        return (imm & 0xfff) << 20 | a << 15 | (2 if op == 'lw' else 0) << 12 | rd << 7 | (3 if op == 'lw' else 0x13)
    if op == 'sw':
        n = imm & 0xfff
        return (n >> 5) << 25 | b << 20 | a << 15 | 2 << 12 | (n & 31) << 7 | 0x23
    n = imm & 0x1fff
    assert op == 'beq' and imm % 2 == 0
    return (n >> 12) << 31 | ((n >> 5) & 63) << 25 | b << 20 | a << 15 | ((n >> 1) & 15) << 8 | ((n >> 11) & 1) << 7 | 0x63


def asm(op, rd=0, a=0, b=0, imm=0):
    text = (f'{op} x{rd}, x{a}, x{b}' if op in ('add', 'sub') else
            f'addi x{rd}, x{a}, {imm}' if op == 'addi' else
            f'lw x{rd}, {imm}(x{a})' if op == 'lw' else
            f'sw x{b}, {imm}(x{a})' if op == 'sw' else
            f'beq x{a}, x{b}, {imm:+d}')
    return encode(op, rd, a, b, imm), text


def signed(n, width):
    return n - (1 << width) if n & (1 << (width - 1)) else n


def reference(words, initial):
    """Decode machine words independently of the assembler's instruction tuples."""
    regs, mem, pc, writes, stores = [0] * 32, initial.copy(), 0, [], []
    while pc < len(words) * 4:
        ins = words[pc // 4]
        op, rd, a, b = ins & 127, (ins >> 7) & 31, (ins >> 15) & 31, (ins >> 20) & 31
        nxt, value = pc + 4, None
        if op == 0x33:
            value = regs[a] - regs[b] if ins >> 30 & 1 else regs[a] + regs[b]
        elif op == 0x13:
            value = regs[a] + signed(ins >> 20, 12)
        elif op == 3:
            value = mem[(regs[a] + signed(ins >> 20, 12)) & MASK]
        elif op == 0x23:
            off = signed(((ins >> 25) << 5) | ((ins >> 7) & 31), 12)
            addr = (regs[a] + off) & MASK
            mem[addr] = regs[b]
            stores.append((pc, addr, regs[b]))
        elif op == 0x63:
            off = ((ins >> 31) << 12) | (((ins >> 7) & 1) << 11) | (((ins >> 25) & 63) << 5) | (((ins >> 8) & 15) << 1)
            if regs[a] == regs[b]:
                nxt = pc + signed(off, 13)
        if value is not None and rd:
            regs[rd] = value & MASK
            writes.append((pc, rd, regs[rd]))
        pc = nxt
    return writes, stores, regs, mem


def cases():
    A = asm
    yield 'walkthrough', [
        A('addi', 1, imm=5), A('add', 2, 1, 1), A('sub', 3, 2, 1),
        A('sw', b=3), A('lw', 4), A('add', 5, 4, 2),
        A('addi', 6, imm=15), A('beq', a=5, b=6, imm=12),
        A('addi', 7, imm=99), A('sw', b=7, imm=4),
        A('add', 8, 5, 6), A('sw', b=8, imm=8)], 1, 1
    yield 'priority', [A('addi', 1, imm=1), A('addi', 1, 1, imm=2), A('add', 2, 1, 1)], 0, 0
    yield 'wb_id', [A('addi', 1, imm=9), A('addi'), A('addi'), A('add', 2, 1, 1)], 0, 0
    yield 'x0_false_dependency', [A('lw', 0), A('addi', 2, imm=5), A('lw', 5), A('addi', 3, imm=5)], 0, 0
    yield 'load_store', [A('lw', 1), A('sw', b=1, imm=4), A('lw', 2, imm=4), A('sw', a=2, b=1, imm=4)], 2, 0
    yield 'load_overwrites_alu', [A('addi', 1, imm=99), A('lw', 1), A('add', 2, 1, 1)], 1, 0
    yield 'load_branch', [A('lw', 1), A('beq', a=1, b=0, imm=8), A('addi', 2, imm=7), A('beq', a=1, b=1, imm=12), A('sw', b=2, imm=4), A('addi', 3, imm=99), A('addi', 4, imm=-1)], 1, 1
    # Fixed seed, no branches: overlapping destinations, x0, negative immediates,
    # loads/stores with aligned addresses, and many adjacent RAW dependencies.
    rng = random.Random(20261023)
    program = []
    for _ in range(160):
        op = rng.choice(['add', 'sub', 'addi', 'lw', 'sw'])
        rd, a, b = rng.randrange(8), rng.randrange(8), rng.randrange(8)
        imm = rng.randrange(-16, 17)
        if op in ('lw', 'sw'): a, imm = 0, rng.randrange(16) * 4
        program.append(A(op, rd, a, b, imm))
    yield 'random_160', program, None, 0


def build_sim():
    files = ['decoder.v', 'regfile.v', 'forward_unit.v', 'hazard_unit.v', 'pipeline_demo.v', 'tb_pipeline.sv']
    with (BUILD / 'compile.log').open('w') as log:
        subprocess.run(['iverilog', '-g2012', '-Wall', '-s', 'tb_pipeline', '-o', str(BUILD / 'sim.vvp')] +
                       [str(SRC / f) for f in files], stdout=log, stderr=subprocess.STDOUT, check=True)
    return ['vvp', str(BUILD / 'sim.vvp')]


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    exe = build_sim()
    summary = []
    for name, program, stalls, redirects in cases():
        folder = BUILD / name
        folder.mkdir(exist_ok=True)
        words = [p[0] for p in program]
        initial = {i * 4: (i + 1) * 16 for i in range(256)}
        (folder / 'program.hex').write_text(''.join(f'{w:08x}\n' for w in words + [0x13] * (512 - len(words))))
        (folder / 'memory.hex').write_text(''.join(f'{initial[i*4]:08x}\n' for i in range(256)))
        (folder / 'program.txt').write_text('\n'.join(f'{i*4:04x}  {word:08x}  {text}' for i, (word, text) in enumerate(program)) + '\n')
        result = subprocess.run(exe + [f'+CYCLES={len(words)*2+12}'], cwd=folder, capture_output=True, text=True)
        (folder / 'simulation.log').write_text(result.stdout + result.stderr)
        if result.returncode: raise RuntimeError(f'{name}: simulator failed; see {folder}/simulation.log')
        with (folder / 'events.csv').open() as f: events = list(csv.DictReader(f))
        expected_w, expected_s, regs, mem = reference(words, initial)
        for kind, expected in [('W', expected_w), ('S', expected_s)]:
            actual = [tuple(int(e[k], 16) for k in ('pc', 'dest', 'data')) for e in events if e['kind'] == kind]
            assert actual == expected, (name, kind, actual, expected)
        with (folder / 'trace.csv').open() as f: trace = list(csv.DictReader(f))
        nstall = sum(int(r['load_use']) for r in trace)
        nbranch = sum(int(r['redirect']) for r in trace)
        assert stalls is None or nstall == stalls, (name, 'stalls', nstall)
        assert nbranch == redirects, (name, 'redirects', nbranch)
        if name == 'priority':
            e = next(r for r in trace if int(r['pc_e'], 16) == 8)
            assert (e['forward_a'], e['forward_b'], int(e['ex_a'],16)) == ('2','2',3)
        if name == 'walkthrough':
            assert regs[8] == 30 and mem[8] == 30 and regs[7] == 0 and mem[4] == initial[4]
        item = dict(name=name, status='PASS', instructions=len(words), register_writes=len(expected_w), stores=len(expected_s), stalls=nstall, redirects=nbranch)
        summary.append(item)
        print(json.dumps(item))
    (BUILD / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(f'PASS: {len(summary)} programs; RTL traces and VCD files in {BUILD}')


if __name__ == '__main__': main()
