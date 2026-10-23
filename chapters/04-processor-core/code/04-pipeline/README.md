# 4.04 / 4.05：结构图、RTL 与波形配套实验

对应 [Issue #6](https://github.com/SysarchLab-CQUPT/SysArch-Journey/issues/6)。正文位于本章 `04-pipeline.tex` 与 `05-hazard.tex`。这是一套教学数据通路，支持 ADD、SUB、ADDI、LW、SW、BEQ 六种指令，不是完整 RV32I CPU。

## 阅读与运行

直接打开本目录 `index.html` 可阅读完整教材：桌面侧栏与移动端目录、代码复制、图形放大和逐拍实验都在同一页面。在线地址为 https://sysarchlab-cqupt.github.io/SysArch-Journey/chapters/04-processor-core/code/04-pipeline/ 。

先阅读 4.04 的时序合同，再到页面末尾 C1～C17 的逐拍实验观察真实仿真状态。独立图解版为 `explorer.html`。PDF 图与 SVG 图由同一组几何元素生成。HTML 内的代码和轨迹由脚本嵌入，编辑 RTL 后应重新运行生成步骤，避免网页与源码不一致。

基础实验只需电脑，不需 FPGA。安装 Python 3.10+ 和 Icarus Verilog，确保 `iverilog`、`vvp` 在 PATH。Windows 可使用 MSYS2 UCRT64 的 `mingw-w64-ucrt-x86_64-iverilog` 包；其他系统按 Icarus 官方安装说明配置。

从仓库根目录运行：

```text
python chapters/04-processor-core/code/04-pipeline/run.py
```

`run.py` 使用实际 RTL 仿真，核对寄存器写回、存储器写入与独立的顺序参考模型，并检查暂停/冲刷的逐拍约束。2026-10-23 使用 Icarus Verilog 13.0 stable 执行，8 个案例全部通过；共 197 条输入指令，其中 160 条为固定种子随机序列。默认路径不依赖 Python 第三方包。

本稿没有完成 Vivado 上板、综合资源统计、静态时序分析或完整 ISA 合规性验证。本稿的可复现入口统一使用 Icarus；核心模块另通过 Verilog-2001 语法检查。

## 文件映射

| 文件 | 对应硬件 / 工作 |
|---|---|
| `pipeline_demo.v` | 五级集成数据通路、四组流水寄存器、存储器接口、分支重定向 |
| `decoder.v` | 六条指令的译码、立即数、源寄存器使用标记 |
| `regfile.v` | 双读单写、x0、WB 到 ID 的显式旁路 |
| `forward_unit.v` | EX 两路操作数的前递选择，最近写者优先 |
| `hazard_unit.v` | Load-Use 检测、前端使能和两路 flush |
| `tb_pipeline.sv` | 存储器模型、时钟复位、周期断言、VCD 与事件导出 |
| `run.py` | 测试输入、机器码、顺序参考模型、结果比对 |
| `generate_assets.py` | 解析 VCD、校验波形、生成 SVG/PDF/HTML、从真实 RTL 提取教材代码 |
| `build_reader.py` / `reader-template.html` | 从同一份 LaTeX 生成完整 HTML 教材，使用原生 MathML，无 CDN 依赖 |
| `listings/` | 自动提取的教材代码片段，不是独立模块，不应重复加入仿真编译 |

## 输出与波形

所有运行产物在 `build/rtl-pipeline/`，每个案例一个子目录。

- `program.hex` / `program.txt`：实际载入的机器码与汇编对照。
- `memory.hex`：初始数据存储器，第 i 个字的初值为 `(i + 1) * 16`。
- `trace.csv`：每个上升沿 **NBA 更新之前** 的状态，C1 为解除复位后的第一个有效采样边沿。
- `events.csv`：真实发生的 W（寄存器写回）与 S（存储器写入）。分别比较两类事件的顺序。
- `wave.vcd`：原始仿真波形，使用 GTKWave 打开。
- `simulation.log`：周期约束结果；总结果见 `summary.json`。
- `waveform-provenance.json`：图形中的控制信号与 VCD 的逐拍核对结果。

贯穿案例的关键周期：C4 两路 EX/MEM 前递；C5 混合 EX/MEM 与 MEM/WB 前递；C6 store 数据前递；C7 Load-Use 检出；C8 EX 空泡；C9 WB 前递；C11 分支重定向；C12 ID/EX 两级无效。

预期最终效果：x1=5、x2=10、x3=5、x4=5、x5=15、x6=15、x7=0、x8=30；字节地址 0 的字为 5，地址 4 保持初值 32，地址 8 为 30。

## 重新生成图、网页及代码摘录

先运行仿真，再安装 `reportlab`，指定本地有权使用的 TrueType 中文字体。

```powershell
# Windows PowerShell（默认即使用此字体）
$env:DIAGRAM_FONT = 'C:/Windows/Fonts/msyh.ttc'
python chapters/04-processor-core/code/04-pipeline/generate_assets.py
```

Linux/macOS 用 `DIAGRAM_FONT=/path/to/chinese.ttf python .../generate_assets.py`。字体不随工程分发，PDF 嵌入字体子集；如需要发布给不同许可证要求的项目，可指定开源中文 TrueType 字体重新生成。

生成器使用规则布局的矩形、正交连线与文本，SVG 在网页中直接显示，PDF 用于 LaTeX。没有使用生成式图片，也没有手填理想波形。控制信号逐拍与原始 VCD 核对；代码片段从编译过的 `pipeline_demo.v` 提取。

完成全书编译后，使用 Pandoc 3.12.1 生成完整网页（`PANDOC` 可指定其绝对路径）：

```text
python chapters/04-processor-core/code/04-pipeline/build_reader.py
```

顺序为：`run.py` → `generate_assets.py` → 全书编译 → `build_reader.py`。网页与 LaTeX 共用正文，不维护另一份手写内容。提交时连同生成的 HTML 与 SVG 一起提交；GitHub Pages 在现有全书发布流程中复制这些静态文件，不需要在线安装 Pandoc。

## 编译教材

遵守仓库根目录 README，使用 XeLaTeX 与 latexmk：

```powershell
.\scripts\build.ps1
```

全书产物为 `build/main.pdf`。常用 TeX 包还包括 ctex、fandol、subfiles、gbt7714。所有正文、图表与代码均放在第 4 章目录，未修改全书装配入口或共享样式。

## 模型边界

指令与数据存储器均为组合读，数据写入发生在上升沿；两个端口分离。测试中只允许对齐且处于数组范围内的访问。不支持的指令会让测试平台报错；DUT 本身没有实现非法指令异常。

store 数据在 EX 取得，因此相邻 load→store 数据相关也停一拍；没有另做 WB→MEM store 专用旁路。BEQ 在 EX 使用前递后的两个寄存器值，不成立则顺序推进，成立则取消 IF、ID 两条年轻指令。同步 BRAM、Cache、AXI 或异常支持需要新的接口与控制设计。

## 验收对应

| 验收点 | 本次交付 |
|---|---|
| 结构与 RTL 对应 | 4.04 的结构图、字段表、译码控制表、寄存器堆与流水寄存器代码 |
| 五级数据与控制 | `pipeline_demo.v` 与两组自动提取的寄存器清单 |
| 前递与 Load-Use | 4.05 前递选择器、暂停控制、定向序列及实测波形 |
| 仿真验证 | 8 组测试、逐拍约束、事件对比、原始 VCD、可重生成图 |
| 教材规范 | 两节 LaTeX、6 组 SVG/PDF 图、参考文献、实验入口与思考题 |
