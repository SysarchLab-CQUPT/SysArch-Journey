"""Deterministic SVG/PDF diagrams and an offline HTML cycle explorer.
The same primitives generate both formats. Requires reportlab for vector PDF.
Run AFTER run.py. Waveform inputs are checked against the simulator's VCD.
"""
from pathlib import Path
import csv
import html
import json
import os
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

SRC = Path(__file__).resolve().parent
CH = SRC.parents[1]
ROOT = SRC.parents[3]
BUILD = ROOT / 'build/rtl-pipeline'
FONT = os.environ.get('DIAGRAM_FONT', 'C:/Windows/Fonts/msyh.ttc')
pdfmetrics.registerFont(TTFont('DiagramCN', FONT))
INK, BLUE, TEAL, RED, GREY = '#16324f', '#2563eb', '#008575', '#bc3f4a', '#64748b'


class Diagram:
    def __init__(self, name, w, h, section='04-pipeline'):
        self.path = CH / 'figures' / section / name
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.w, self.h = w, h
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img"><title>{name}</title>',
                    '<rect width="100%" height="100%" fill="white"/>']
        self.pdf = canvas.Canvas(str(self.path.with_suffix('.pdf')), pagesize=(w, h))
        self.pdf.setTitle(name)
    def rect(self, x, y, w, h, fill='#f3f6fb', stroke='#d7e1ed', radius=8):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>')
        self.pdf.setFillColor(HexColor(fill)); self.pdf.setStrokeColor(HexColor(stroke))
        self.pdf.roundRect(x, self.h-y-h, w, h, radius, fill=1, stroke=1)
    def text(self, x, y, text, size=16, color=INK, center=False):
        anchor = 'middle' if center else 'start'
        self.svg.append(f'<text x="{x}" y="{y}" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}">{html.escape(str(text))}</text>')
        self.pdf.setFont('DiagramCN', size); self.pdf.setFillColor(HexColor(color))
        (self.pdf.drawCentredString if center else self.pdf.drawString)(x, self.h-y, str(text))
    def line(self, pts, color=BLUE, width=2, arrow=True, dash=False):
        p = ' '.join(f'{x},{y}' for x,y in pts)
        self.svg.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="7 4"' if dash else '')+'/>')
        self.pdf.setStrokeColor(HexColor(color)); self.pdf.setLineWidth(width)
        self.pdf.setDash([7,4] if dash else [])
        path=self.pdf.beginPath(); path.moveTo(pts[0][0], self.h-pts[0][1])
        for x,y in pts[1:]: path.lineTo(x,self.h-y)
        self.pdf.drawPath(path); self.pdf.setDash([])
        if arrow:
            x,y=pts[-1]; px,py=pts[-2]; dx,dy=x-px,y-py
            length=(dx*dx+dy*dy)**.5; ux,uy=dx/length,dy/length
            triangle=[(x,y),(x-9*ux+4*uy,y-9*uy-4*ux),(x-9*ux-4*uy,y-9*uy+4*ux)]
            self.svg.append(f'<polygon points="'+ ' '.join(f'{a},{b}' for a,b in triangle)+f'" fill="{color}"/>')
            self.pdf.setFillColor(HexColor(color)); p=self.pdf.beginPath();p.moveTo(x,self.h-y)
            for a,b in triangle[1:]:p.lineTo(a,self.h-b)
            p.close();self.pdf.drawPath(p,fill=1,stroke=0)
    def save(self):
        self.path.with_suffix('.svg').write_text('\n'.join(self.svg+['</svg>']),encoding='utf-8')
        self.pdf.showPage();self.pdf.save()


def architecture():
    d=Diagram('rtl-datapath',1240,560)
    d.text(28,35,'从结构图读出 RTL：五级数据通路与四组流水寄存器',23)
    labels=[('IF','取指','PC + 指令存储器'),('ID','译码','译码器 + 寄存器堆'),('EX','执行','前递 MUX + ALU'),('MEM','访存','数据存储器'),('WB','写回','写回 MUX')]
    for i,(a,b,c) in enumerate(labels):
        x=24+i*246
        d.rect(x,70,200,228,fill='#f4f8fc')
        d.text(x+16,101,a,24,BLUE);d.text(x+96,100,b,18)
        d.rect(x+12,132,176,65,fill='#ffffff')
        d.text(x+100,159,c,14,center=True)
        d.text(x+100,182,['imem_addr','rs1 / rs2 / rd','ex_a / ex_b','dmem_addr','wb_data'][i],14,center=True)
        d.text(x+15,232,['PC → instr','控制与数据打包','计算 / 比较 / 目标','load / store','写入寄存器堆'][i],15)
        d.text(x+15,263,['顺序取 PC+4','WB→ID 同拍旁路','BEQ 在本级决策','本例组合读、边沿写','valid && reg_write'][i],13,GREY)
        if i<4:
            bx=x+210
            d.rect(bx,128,18,152,fill='#dce9fb',stroke=BLUE,radius=2)
            d.line([(x+188,164),(bx,164)])
            d.line([(bx+18,164),(x+246+12,164)])
            d.text(bx+9,320,['IF/ID','ID/EX','EX/MEM','MEM/WB'][i],12,BLUE,True)
    # Separate orthogonal lanes for backward routes.
    d.line([(1108,298),(1108,355),(370,355),(370,298)],TEAL)
    d.text(785,345,'WB → ID：同拍读写旁路',15,TEAL)
    d.line([(744,278),(775,278),(775,395),(560,395),(560,298)],TEAL)
    d.text(800,395,'EX/MEM → EX：ALU 结果前递',15,TEAL)
    d.line([(1108,355),(1108,435),(605,435),(605,298)],TEAL)
    d.text(785,425,'MEM/WB → EX：写回值前递',15,TEAL)
    d.line([(680,298),(680,485),(124,485),(124,298)],RED,dash=True)
    d.text(150,475,'redirect：重定向 PC，冲刷 IF/ID 与 ID/EX',15,RED)
    d.text(28,521,'蓝色：正向数据流    绿色：旁路 / 前递    红色虚线：控制返回    竖条：上升沿保存状态',15,GREY)
    d.save()
    d=Diagram('rtl-mapping',1100,425)
    d.text(26,34,'组合逻辑决定“下一个值”，时序逻辑决定“何时保存”',23)
    for i,(title,lines) in enumerate([
        ('寄存器 / D 触发器',['posedge clk','q <= d;','只在时钟边沿更新']),
        ('MUX / 选择器',['assign y = sel ? b : a;','两个数据入口，一个选择信号','选择信号变化即重新求值']),
        ('ALU / 组合运算',['alu_sub ? a-b : a+b','结果依赖当前操作数','没有独立时钟'])]):
        x=26+i*360; d.rect(x,78,328,174);d.text(x+16,110,title,19,BLUE)
        for j,l in enumerate(lines):d.text(x+16,148+j*32,l,15)
    d.rect(100,302,215,68,fill='#e8f4f0');d.text(207,344,'当前流水寄存器 Q',18,center=True)
    d.rect(442,302,215,68);d.text(550,344,'组合电路计算 D',18,center=True)
    d.rect(785,302,215,68,fill='#e8f4f0');d.text(892,344,'下一组寄存器 Q',18,center=True)
    d.line([(315,336),(442,336)]);d.line([(657,336),(785,336)])
    d.text(709,296,'上升沿采样',14,BLUE,True);d.save()
    d=Diagram('forward-paths',1100,490,'05-hazard')
    d.text(25,35,'前递的选择点：先得到真实 rs2，再选择 ALU 的第二操作数',23)
    for y,title,note in [(85,'ID/EX','寄存器堆读值'),(190,'EX/MEM','ALU 结果；load 尚未就绪'),(295,'MEM/WB','最终 wb_data')]:
        d.rect(25,y,265,72);d.text(40,y+28,title,20,BLUE);d.text(40,y+55,note,14)
    d.rect(405,120,165,80,fill='#e8f4f0');d.text(487,152,'前递 MUX A',19,center=True);d.text(487,180,'forward_a',15,center=True)
    d.rect(405,280,165,80,fill='#e8f4f0');d.text(487,312,'前递 MUX B',19,center=True);d.text(487,340,'forward_b',15,center=True)
    for x,y,color in [(320,121,BLUE),(345,226,TEAL),(370,331,TEAL)]:
        d.line([(290,y),(x,y),(x,140+(x-320)*.6),(405,140+(x-320)*.6)],color)
        d.line([(x,y),(x,300+(x-320)*.6),(405,300+(x-320)*.6)],color)
    d.rect(680,125,145,68);d.text(752,165,'ALU',21,center=True)
    d.line([(570,152),(680,152)]);d.text(575,140,'ex_a',14,BLUE)
    d.rect(680,280,145,75);d.text(752,311,'立即数 MUX',17,center=True);d.text(752,337,'alu_imm',15,center=True)
    d.line([(570,306),(680,306)]);d.text(600,294,'ex_rs2',14,TEAL)
    d.line([(752,280),(752,193)]);d.text(766,240,'ex_b',14,BLUE)
    d.line([(660,403),(752,403),(752,355)]);d.text(605,424,'idex_imm',15,BLUE)
    d.rect(910,260,165,70);d.text(992,289,'store_data',17,center=True);d.text(992,312,'EX/MEM 保存',14,center=True)
    d.line([(610,306),(610,375),(887,375),(887,294),(910,294)],TEAL)
    d.rect(910,80,165,70);d.text(992,110,'BEQ 比较器',17,center=True);d.text(992,135,'ex_a == ex_rs2',14,center=True)
    d.line([(625,152),(625,66),(992,66),(992,80)],TEAL)
    d.line([(610,375),(870,375),(870,121),(910,121)],TEAL)
    d.text(25,467,'优先级：最近的匹配写者优先；00=ID/EX，10=EX/MEM，01=MEM/WB。',16,GREY);d.save()


def read_vcd_samples(file):
    scope, names, vals, result = [], {}, {}, []
    groups, t = [], 0
    def process(time, changes):
        # Snapshot immediately BEFORE the active rising edge (before NBA updates).
        clk = names.get('tb_pipeline.clk'); rst = names.get('tb_pipeline.rst')
        if any(code==clk and value=='1' for code,value in changes) and vals.get(clk)=='0' and vals.get(rst)=='0':
            result.append((time, vals.copy()))
        for code,value in changes: vals[code]=value
    for raw in file.read_text().splitlines():
        l=raw.strip()
        if l.startswith('$scope'):scope.append(l.split()[2])
        elif l.startswith('$upscope'):scope.pop()
        elif l.startswith('$var'):
            parts=l.split(); names['.'.join(scope+[parts[4]])]=parts[3]
        elif l.startswith('#'):
            process(t,groups);t=int(l[1:]);groups=[]
        elif l.startswith('b'):
            v,c=l[1:].split();groups.append((c,v))
        elif l and l[0] in '01xz':groups.append((l[1:],l[0]))
    process(t,groups)
    return names,result


def waveforms():
    trace=list(csv.DictReader((BUILD/'walkthrough/trace.csv').open()))
    names,samples=read_vcd_samples(BUILD/'walkthrough/wave.vcd')
    mapping={'load_use':'load_use','forward_a':'forward_a','forward_b':'forward_b','redirect':'redirect','pc_en':'pc_en','ifid_en':'ifid_en','ifid_flush':'ifid_flush','idex_flush':'idex_flush'}
    assert len(samples)==len(trace)
    for row,(t,vals) in zip(trace,samples):
        for k,name in mapping.items(): assert int(vals[names['tb_pipeline.dut.'+name]],2)==int(row[k]),(t,k)
        assert int(vals[names['tb_pipeline.dut.imem_addr']],2)==int(row['pc_f'],16)
        for col,reg in [('pc_d','ifid'),('pc_e','idex'),('pc_m','exmem'),('pc_w','memwb')]:
            valid=vals[names['tb_pipeline.dut.'+reg+'_valid']]=='1'
            pc=int(vals[names['tb_pipeline.dut.'+reg+'_pc']],2) if valid else 0xffffffff
            assert pc==int(row[col],16),(t,col)
    assert all(b[0]-a[0]==10000 for a,b in zip(samples,samples[1:]))
    for title,first,last,filename in [('Load-Use：C7 检测，C8 空泡，C9 写回前递',5,11,'wave-load-use'),('分支：C11 判断成立，C12 两级失效',9,15,'wave-branch')]:
        rows=trace[first-1:last];cw=112;x0=220
        fields=['clk','pc_f','pc_d','pc_e','pc_m','pc_w','load_use','forward_a','forward_b','redirect','pc_en','ifid_en','ifid_flush','idex_flush']
        d=Diagram(filename,1040,735,'05-hazard');d.text(22,32,title,22)
        d.text(22,57,'实测 VCD：周期内电平；各周期右边界为采样上升沿（NBA 更新之前）',14,GREY)
        for i,r in enumerate(rows):
            x=x0+i*cw;d.text(x+cw/2,87,'C'+r['cycle'],16,BLUE,True)
            d.line([(x,101),(x,685)],'#e1e8f0',1,False)
        for j,key in enumerate(fields):
            y=112+j*40;d.text(25,y+20,key,17)
            for i,r in enumerate(rows):
                x=x0+i*cw
                if key=='clk':
                    d.line([(x,y+4),(x+cw/2,y+4),(x+cw/2,y+27),(x+cw,y+27),(x+cw,y+4)],GREY,1.5,False)
                    continue
                v=r[key];is_pc=key in ['pc_f','pc_d','pc_e','pc_m','pc_w']
                if is_pc or key.startswith('forward'):
                    text='空泡' if v=='ffffffff' else ('0x'+v[-2:] if is_pc else {'0':'00','1':'01','2':'10'}[v])
                    color=TEAL if key.startswith('forward') and v!='0' else INK
                    d.rect(x+2,y,cw-4,30,fill='#eff7f5' if color==TEAL else '#f5f7fb',radius=2)
                    d.text(x+cw/2,y+21,text,15,color,True)
                else:
                    high=v=='1';yy=y+4 if high else y+27
                    color=RED if high and key in ['load_use','redirect','idex_flush'] else BLUE
                    p=[(x,yy),(x+cw,yy)]
                    if i and rows[i-1][key]!=v:p.insert(0,(x,y+4 if not high else y+27))
                    d.line(p,color,2,False)
        d.text(24,718,'PC 为字节地址；空泡由 valid=0 表示；10/01 是二进制选择编码。',14,GREY);d.save()
    d=Diagram('cycle-table',1160,600,'05-hazard');d.text(24,33,'同一条指令跨周期移动：暂停与冲刷怎样改变时序',23)
    x0,cw=260,51
    for c in range(1,18):d.text(x0+(c-1)*cw+cw/2,72,str(c),15,BLUE,True)
    listing=(BUILD/'walkthrough/program.txt').read_text().splitlines()
    for i,line in enumerate(listing):
        pc=i*4;y=95+i*37;d.text(22,y+22,line[:4]+'  '+line.split('  ',2)[2],13)
        for c,row in enumerate(trace[:17]):
            stages=[s for s,k in zip(['IF','ID','EX','MEM','WB'],['pc_f','pc_d','pc_e','pc_m','pc_w']) if int(row[k],16)==pc]
            stage='/'.join(stages)
            if not stage:continue
            color=RED if pc in (32,36) else BLUE
            d.rect(x0+c*cw+1,y,cw-3,30,fill='#fceeed' if color==RED else '#edf3fd',radius=2)
            d.text(x0+c*cw+cw/2,y+21,stage,12,color,True)
    d.text(24,574,'红色两行是错误路径；C7/C8 的 ID 停留对应一次暂停；分支后目标在 C12 重新取指。',15,GREY);d.save()
    (BUILD/'waveform-provenance.json').write_text(json.dumps({'source':'walkthrough/wave.vcd','sample_rule':'pre-rising-edge, pre-NBA','samples_checked':len(trace),'signals_checked':list(mapping)+['pc_f','pc_d','pc_e','pc_m','pc_w'],'valid_mask_checked':True,'clock_period_ps':10000,'result':'PASS'},indent=2))
    return trace


def excerpts():
    # Extract textbook listings from the actual compiled file, without hand-copying.
    source=(SRC/'pipeline_demo.v').read_text()
    spans={'ex-operands':('    wire [31:0] ex_a','    wire load_use'),
           'pipeline-registers':('    // IF:','    // Older instructions'),
           'late-stages':('    // Older instructions','    assign dmem_addr')}
    target=SRC/'listings';target.mkdir(exist_ok=True)
    for name,(a,b) in spans.items():
        (target/(name+'.v')).write_text(source[source.index(a):source.index(b)])
    (target/'walkthrough.txt').write_text((BUILD/'walkthrough/program.txt').read_text())


def webpage(trace):
    figs=[('结构到 RTL','04-pipeline/rtl-mapping'),('五级数据通路','04-pipeline/rtl-datapath'),('前递网络','05-hazard/forward-paths'),('指令时序','05-hazard/cycle-table'),('Load-Use 波形','05-hazard/wave-load-use'),('分支冲刷波形','05-hazard/wave-branch')]
    diagrams=''.join(f'<section id="fig{i}"><h2>{i+1:02d} / {title}</h2><img alt="{title}" src="../../figures/{f}.svg"></section>' for i,(title,f) in enumerate(figs))
    codes=''.join(f'<details><summary>{name}</summary><pre><code>{html.escape((SRC/name).read_text())}</code></pre></details>' for name in ['pipeline_demo.v','decoder.v','regfile.v','forward_unit.v','hazard_unit.v','tb_pipeline.sv'])
    listing=(BUILD/'walkthrough/program.txt').read_text()
    text=r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>从结构图到 RTL · 五级流水线图解实验</title><style>
    :root{--ink:#16324f;--blue:#2563eb;--green:#008575;--red:#bc3f4a}*{box-sizing:border-box}body{margin:0;background:#eef3f8;color:var(--ink);font:16px/1.8 "Microsoft YaHei",sans-serif}header{padding:55px max(28px,calc((100vw - 1140px)/2));background:#122b46;color:white}header small{letter-spacing:.16em;color:#9ebede}h1{font-size:38px;line-height:1.4;margin:18px 0}main{max-width:1200px;margin:auto;padding:28px}section{padding:30px;background:white;border:1px solid #dce5ef;border-radius:16px;margin:0 0 26px}h2{font-size:24px;margin:0 0 18px}p{max-width:80ch}img{display:block;width:100%;height:auto}nav{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}a{color:var(--blue)}nav a{background:#dfeafb;border-radius:20px;padding:5px 15px;text-decoration:none}.stages{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:20px 0}.stage{padding:15px;background:#f3f6fb;border-top:4px solid var(--blue);border-radius:7px;min-height:116px}.stage b{display:block;font-size:21px}.stage span{font:14px/1.5 Consolas,monospace;overflow-wrap:anywhere}.bubble{border-color:#a7b4c3;color:#687b90}.controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap}button{border:0;border-radius:7px;background:var(--blue);color:white;padding:9px 16px;cursor:pointer;font:inherit}input{flex:1;min-width:200px}.status{padding:16px;border-left:4px solid var(--green);background:#eaf6f2;min-height:85px}pre{font:14px/1.65 Consolas,monospace;background:#10283f;color:#e0edf8;padding:20px;overflow:auto;border-radius:8px}summary{padding:12px;cursor:pointer;font-weight:bold}details{border:1px solid #dce5ef;margin:10px 0;border-radius:8px}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:9px;border-bottom:1px solid #dde5ee}.note{color:#5c7087;font-size:14px}.pill{display:inline-block;padding:4px 13px;border-radius:16px;background:#e7f5f0;color:var(--green)}@media(max-width:760px){h1{font-size:27px}.stages{grid-template-columns:1fr}section{padding:18px}main{padding:14px}}@media print{header{background:white;color:#16324f}section{break-inside:avoid}button,input{display:none}}
    </style><header><small>CHAPTER 04 · STRUCTURE → RTL → WAVEFORM</small><h1>从结构图到 RTL<br>看见五级流水线里的每一拍</h1><p>4.04 / 4.05 配套图解实验。图形由代码生成；逐拍数据来自已运行的 Verilog，波形已与原始 VCD 核对。</p></header><main><nav>__NAV__</nav>
    <section><h2>先约定这颗教学数据通路的边界</h2><p>32 位、顺序单发射、五级流水；仅支持 ADD / SUB / ADDI / LW / SW / BEQ。指令与数据分开存储，组合读、上升沿写，BEQ 在 EX 级决策。这个固定延迟模型用于解释机制；接同步 BRAM、Cache 或 AXI 时必须重新设计握手和等待。</p><span class="pill">实际仿真：8 / 8 测试通过</span><p class="note">完整教材正文和分析见仓库 04-pipeline.tex、05-hazard.tex 及编译后的 PDF。下方原始代码与教材引用来自同一组源文件。</p></section>
    <section id="explorer"><h2>逐拍观察：拖动 C1 → C17</h2><div class="controls"><button id="prev">上一拍</button><input id="cycle" type="range" min="1" max="17" value="7" aria-label="仿真周期"><button id="next">下一拍</button><strong id="cycleLabel"></strong></div><div id="stages" class="stages"></div><div id="status" class="status" aria-live="polite"></div><pre id="signals"></pre><details><summary>贯穿示例：地址、机器码和汇编</summary><pre>__PROGRAM__</pre></details><p class="note">每一列表示该周期结束的上升沿之前的状态。无效级显示“空泡”，其中旧数据不参与架构更新。</p></section>
    __FIGS__
    <section><h2>三条阅读线索</h2><p><b>先找寄存器边界。</b>以 ID/EX 为例，当前指令的 PC、源寄存器号、读值、立即数和后级控制一起进入下一拍。非阻塞赋值的右值来自边沿前，所以多级寄存器同时更新仍然只前进一级。</p><p><b>再问数据何时可用。</b>ALU 的结果在 EX 结束时可用，下一拍可以从 EX/MEM 送回 EX；load 在 EX 得到的只是地址，数据到 MEM 结束才可用。相邻消费者必须留在 ID 一拍。</p><p><b>最后看副作用门控。</b>暂停保持 PC 和 IF/ID，却把 ID/EX 置为无效；分支冲刷取消年轻指令；寄存器写使能和存储器写使能都与 valid 相与。看到无效级仍有旧地址不意味着真的写了内存。</p></section>
    <section><h2>可运行的代码</h2><p>在仓库根目录运行 <code>python chapters/04-processor-core/code/04-pipeline/run.py</code>。输出位于 <code>build/rtl-pipeline/</code>；<code>trace.csv</code> 是逐拍记录，<code>wave.vcd</code> 可用 GTKWave 打开。</p>__CODES__</section><footer class="note">配套 Issue #6 · 2026-10-23 · 所有图片均为可重生成的 SVG / PDF 矢量图</footer></main>
    <script>const rows=__DATA__;const program=__MAP__;const slider=document.getElementById('cycle');function show(){const c=Number(slider.value),r=rows[c-1];document.getElementById('cycleLabel').textContent='C'+c;document.getElementById('stages').innerHTML=['IF','ID','EX','MEM','WB'].map((s,i)=>{const pc=r[['pc_f','pc_d','pc_e','pc_m','pc_w'][i]],v=pc!=='ffffffff';return `<div class="stage ${v?'':'bubble'}"><b>${s}</b><span>${v?'0x'+pc.slice(-2)+'<br>'+ (program[parseInt(pc,16)]||'NOP (填充)'):'空泡 / valid = 0'}</span></div>`}).join('');let msg='各级正常推进。先看每级 PC，再看前递选择及写使能。';if(c===4)msg='ADD 的两个源操作数均来自 EX/MEM：forward_a = forward_b = 10，5 + 5 = 10。';if(c===5)msg='SUB 的 A 端取较新的 EX/MEM，B 端取 MEM/WB：10 − 5 = 5。';if(c===6)msg='SW 的数据由 EX/MEM 前递到 ex_rs2；ALU 的 B 端仍选择立即数 0。';if(c===7)msg='LW 在 EX、ADD 在 ID：load_use = 1。此边沿保持 PC 和 IF/ID，向 ID/EX 注入空泡，LW 继续到 MEM。';if(c===8)msg='EX 出现空泡；ADD 仍在 ID；LW 已到 MEM。本周期解除暂停，边沿后 ADD 进入 EX。';if(c===9)msg='ADD 进入 EX，从 MEM/WB 前递载入值 5，与 x2 的 10 相加得到 15。';if(c===11)msg='BEQ 比较两个前递值 15：redirect = 1。目标是 0x1c + 12 = 0x28；IF/ID 与 ID/EX 在边沿失效。';if(c===12)msg='目标指令在 IF；ID、EX 为空泡。错误路径的 ADDI 和 SW 不会产生写回或存储副作用。';document.getElementById('status').textContent=msg;document.getElementById('signals').textContent=['load_use','forward_a','forward_b','redirect','pc_en','ifid_en','ifid_flush','idex_flush'].map(k=>k.padEnd(13)+' = '+(k.startsWith('forward')?Number(r[k]).toString(2).padStart(2,'0'):r[k])).join('\n');}slider.oninput=show;document.getElementById('prev').onclick=()=>{slider.value=Math.max(1,Number(slider.value)-1);show()};document.getElementById('next').onclick=()=>{slider.value=Math.min(17,Number(slider.value)+1);show()};show();</script></html>'''
    mapping={i*4:line.split('  ',2)[2] for i,line in enumerate(listing.splitlines())}
    for key,val in {'__NAV__':'<a href="#explorer">逐拍实验</a>'+''.join(f'<a href="#fig{i}">{title}</a>' for i,(title,_) in enumerate(figs)), '__FIGS__':diagrams,'__CODES__':codes,'__PROGRAM__':html.escape(listing),'__DATA__':json.dumps(trace,ensure_ascii=False),'__MAP__':json.dumps(mapping,ensure_ascii=False)}.items():text=text.replace(key,val)
    (SRC/'explorer.html').write_text(text,encoding='utf-8')


if __name__=='__main__':
    architecture();trace=waveforms();excerpts();webpage(trace)
    print('PASS: 6 SVG/PDF figures; VCD cross-check; compiled-code excerpts; offline HTML explorer')
