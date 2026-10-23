"""Export a focused review PDF and a source/results ZIP after the full book build.
Requires pypdf. Run from any working directory. Does not publish or change Git state.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import zipfile
from pypdf import PdfReader, PdfWriter

SRC = Path(__file__).resolve().parent
ROOT = SRC.parents[3]
CH = SRC.parents[1]
OUT = ROOT / 'build/delivery'


def main():
    OUT.mkdir(exist_ok=True)
    reader = PdfReader(ROOT / 'build/main.pdf')
    aux = (ROOT / 'build/main.aux').read_text(encoding='utf-8')
    log = (ROOT / 'build/main.log').read_text(encoding='utf-8', errors='replace')
    assert not re.search(r'^!|undefined references|undefined citations|Overfull', log, re.M), 'Resolve book diagnostics before packaging'
    def page(label):
        n = re.search(r'\\newlabel\{' + re.escape(label) + r'\}\{\{[^}]*\}\{(\d+)\}', aux).group(1)
        return reader.page_labels.index(n)
    a, b, end, refs = [page(label) for label in ['sec:04-processor-core-04', 'sec:04-processor-core-05', 'sec:04-processor-core-06', 'ch:references']]
    selected = list(range(a, end)) + list(range(refs, len(reader.pages)))
    writer = PdfWriter()
    for p in selected: writer.add_page(reader.pages[p])
    # Preserve named links for included figures, tables, listings and references.
    for name, destination in reader.named_destinations.items():
        old = reader.get_destination_page_number(destination)
        if old in selected: writer.add_named_destination(name, selected.index(old))
    writer.add_outline_item('4.04 五级流水线：从结构图到 RTL', 0)
    writer.add_outline_item('4.05 冒险、前递、暂停与冲刷', b-a)
    writer.add_outline_item('参考文献（沿用全书编号）', end-a)
    writer.add_metadata({'/Title':'4.04–4.05 从结构图到 RTL：五级流水线与数据冒险', '/Subject':'Issue #6 教材阅读稿；真实仿真及代码配套'})
    pdf = OUT / 'rtl-pipeline-guide.pdf'
    with pdf.open('wb') as f: writer.write(f)
    tests = json.loads((ROOT / 'build/rtl-pipeline/summary.json').read_text())
    metadata = {
        'source_commit':subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'branch':subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
        'source_page_range':[a+1, end], 'excerpt_pages':len(writer.pages), 'full_book_pages':len(reader.pages),
        'simulation':'Icarus Verilog 13.0 stable', 'hdl':'Verilog-2001 DUT; SystemVerilog testbench',
        'tests':tests, 'waveform_check':json.loads((ROOT/'build/rtl-pipeline/waveform-provenance.json').read_text()),
    }
    (OUT / 'verification.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
    (OUT / 'DELIVERY.txt').write_text(
        '本交付包对应 SysArch-Journey Issue #6。\n\n'
        '先阅读 rtl-pipeline-guide.pdf（两节正文及参考文献，沿用全书页码与引文编号）。\n'
        '打开 chapters/04-processor-core/code/04-pipeline/index.html 可离线查看交互图解。\n'
        'chapters/ 是需要合入现有仓库的第4章文件，不要替换整本书的其他章节。\n'
        'build/rtl-pipeline/ 包含实测 VCD、CSV、测试输入与日志。\n'
        'verification.json 记录基线版本、工具和验证结果。\n'
        '完整复现命令与实验边界见代码目录 README.md。\n'
        '完整教材已按仓库脚本编译；build/main.log 没有错误、未解析引用或溢出版心。\n', encoding='utf-8')
    files = [CH/'04-pipeline.tex', CH/'05-hazard.tex', CH/'refs.bib']
    files += [p for p in SRC.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files += [p for section in ['04-pipeline','05-hazard'] for p in (CH/'figures'/section).glob('*') if p.stem!='pipeline-stages']
    for test in tests:
        files += [p for p in (ROOT/'build/rtl-pipeline'/test['name']).iterdir() if p.is_file()]
    files += [ROOT/'build/rtl-pipeline'/p for p in ['summary.json','waveform-provenance.json','compile.log']]
    archive = OUT / 'issue-6-textbook-delivery.zip'
    hashes = {}
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in files:
            name = p.relative_to(ROOT).as_posix()
            z.write(p, name); hashes[name] = hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [pdf, OUT/'verification.json', OUT/'DELIVERY.txt']:
            z.write(p, p.name); hashes[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
        z.writestr('SHA256SUMS.json', json.dumps(hashes, indent=2))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name, expected in hashes.items(): assert hashlib.sha256(z.read(name)).hexdigest()==expected
    print(json.dumps({'pdf':str(pdf), 'pages':len(writer.pages), 'zip':str(archive), 'files':len(hashes), 'bytes':archive.stat().st_size},ensure_ascii=False))


if __name__ == '__main__': main()
