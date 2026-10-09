# 从指令集到智能应用 · 撰写指南

这是一本**多人协作编写**的 LaTeX 教材。本仓库是写作与协作的场所：正文按章、按节拆成独立
文件，每个人只改自己负责的文件；工作通过 GitHub Issue 认领、交付和复核。

书名和整体大纲还在确定中，定下来之后会补充到这份文档里。目前各章都是占位骨架。

> 这份指南面向**参与撰写的人**，只讲三件事：怎么把书编译出来、怎么认领和交付任务、
> 怎么增删章节。项目的背景与规划不在这里展开。

## 快速开始

需要 TeX Live 的 XeLaTeX（建议同时安装 `latexmk`）。编辑器推荐 VS Code + LaTeX Workshop，
仓库里的 `.vscode/settings.json` 已经配好，不用另外设置。

```bash
# 全书编译 → build/main.pdf
scripts/build.sh

# 只编译某一章（写作时常用，速度快）→ build/04-processor-core/chapter.pdf
scripts/build.sh chapters/04-processor-core/chapter.tex

# 清掉全部编译产物，只留源码
scripts/clean.sh
```

Windows 用 `.\scripts\build.ps1`、`.\scripts\clean.ps1`，参数相同。

**编译产物只会出现在 `build/` 里**，仓库的其它目录都只放源码。编译之后请确认
`build/main.log` 中没有 `! ` 开头的错误、没有 undefined reference。

## 认领任务

写作任务都在 Issues 里，标题以 `[TASK]` 开头的就是。完整流程：

| 环节 | 谁来做 | 操作 |
|---|---|---|
| ① 找任务 | 你 | 在 Issues 里挑一个自己做得来的 |
| ② 认领 | 你 | 在 Issue 下评论 `/assign` |
| ③ 确认 | 任务发布者 | 回复 `/confirm`，你自动成为 Assignee |
| ④ 交付 | 你 | 完成后评论 `/complete` 发起复核 |
| ⑤ 复核 | 其他成员 | 3 位不同成员分别评论 `LGTM`，通过后 Issue 自动关闭 |
| ⑥ 登记 | 你 | 用"贡献登记"模板登记工时与交付物 |

几个要知道的规则：

- 认领后如果 2 小时内没被确认，机器人会再提醒发布者一次，你不用催。
- 截止时间（DDL）前 12 小时，机器人会 @ 你提醒。
- 复核要凑够 3 个不同的人，自己投的 `LGTM` 不计票。
- 任务 Issue 被手动提前关闭会自动重新打开，必须走完复核。
- 你必须是仓库协作者，否则第三步会失败（机器人会提示无法设为 Assignee）。

没有合适的任务，或者发现该做的事没人提：用"任务发布"模板自己建一个，填好所属模块、
交付清单、预估天数和 DDL。**交付清单要写成 `- [ ] 事项` 的形式**，CI 会检查格式，
不合格会在 Issue 下留言告诉你哪里不对。

任务之外还有几种模板："技术问题"用来提问（写清章节位置和完整报错），
"报告文档问题"用来报错字、技术错误和排版问题，"协作项目提议"用来发起多人参与的子课题。

## 目录结构

```
.
├── main.tex                 全书装配入口（只有主编改）
├── config/
│   ├── document.tex         书名、编著者、单位等元信息
│   ├── appearance.tex       页面、配色、代码字号等排版参数
│   ├── manifest.tex         章的清单（脚本生成，勿手改）
│   └── README.md            配置宏索引（脚本生成）
├── frontmatter/
│   ├── preface.tex          前言
│   ├── figures/             前言的图
│   └── code/                前言的代码
├── chapters/                正文各章，一章一目录
│   └── 04-processor-core/
│       ├── chapter.tex      本章的节清单与章标题
│       ├── 01-single-cycle.tex   一节一个文件
│       ├── 02-pipeline.tex
│       ├── figures/         本章的图：节专属的放同名子目录，共用的直接放这里
│       ├── code/            本章的代码，规则同上
│       └── refs.bib         本章参考文献
├── backmatter/
│   ├── appendix.tex         附录
│   ├── references.tex       参考文献（汇总各章 refs.bib）
│   ├── figures/             附录的图
│   └── code/                附录的代码（例如示例程序）
├── styles/                  排版样式（改动需主编确认）
├── scripts/                 构建、清理与结构维护脚本
├── weekly-status/           每周任务周报（生成脚本，报告会提交到这里）
└── build/                   编译产物（唯一）：main.pdf、main.log 等
```

## 多人协作规则

一句话：**主编负责装配，作者按章按节分文件写作。** 每个人只改自己的文件，
不需要在共享文件上排队，也就不会互相冲突。

| 想做什么 | 只改这些文件 | 不要动 |
|---|---|---|
| 写某一节正文 | `chapters/NN-xxx/MM-*.tex` | 别人的章节目录 |
| 调整本章节顺序、章标题 | `chapters/NN-xxx/chapter.tex` | `main.tex`、`config/manifest.tex` |
| 新增或删除一章 | 用脚本，见下一节 | `main.tex` |
| 改书名、编著者 | `config/document.tex` | 各章正文里的硬编码书名 |
| 改页面、配色 | `config/appearance.tex` | `styles/project.sty`（涉及全书写法） |
| 加本章的图、代码 | 本章目录的 `figures/`、`code/` | 别的章目录、直接把长代码贴进正文 |
| 跨章复用一张图 | 放在主用它的那一章，别的章用 `../NN-xxx/figures/…` 引用 | 复制成好几份 |
| 加参考文献 | 本章的 `refs.bib` | 别的章的 `refs.bib` |

三条硬规则：

1. **一章一目录、一节一文件。** 谁写谁负责，不要顺手改别人的文件。
2. **生成文件不手改。** `config/manifest.tex`、`config/README.md` 由脚本生成；
   `main.tex` 由主编维护，其他人不要改。
3. **共享内容只写一遍。** 书名、单位、配色等统一放 `config/`，正文引用宏。

编译产物和中间文件都已被 `.gitignore` 忽略——`build/` 目录、各式 `.aux` / `.log` /
`.synctex.gz`，以及不在 `figures/` 目录下的 PDF。所以 `git status` 里看不到它们是正常的。
放在各单元 `figures/` 里的插图 PDF 会被正常提交。

## 增删章节

章节顺序由目录名的数字前缀决定，装配清单是扫描目录自动生成的，所以增删章节都不用动
`main.tex`。编译整本书前脚本会自动刷新清单、并同步各 Issue 表单里的章节下拉，
忘记手动同步也不会出问题。

### 新增一章

```bash
python3 scripts/new-chapter.py 09 embedded-linux "嵌入式 Linux 系统构建" \
    --sections "intro:本章导览;build:构建系统;driver:驱动开发"
scripts/build.sh                       # 直接编译即可
```

三个位置参数依次是**序号**（两位数字，决定章的位置）、**目录名**（英文短名，用于路径和
标签）、**章标题**（显示用）。`--sections` 用分号分隔，每节写成 `文件名:标题`，
只写标题会自动命名为 `s01`、`s02`。生成的结构是：

```
chapters/09-embedded-linux/
├── chapter.tex      章入口：\chapter{标题} + 各节的 \input
├── 01-intro.tex     一节一个文件
├── 02-build.tex
├── 03-driver.tex
└── refs.bib         本章自己的参考文献
```

### 新增一节、一个小节

```bash
python3 scripts/new-section.py chapters/04-processor-core "浮点运算与除法" 05-float
```

脚本会建好 `05-float.tex`，并把 `\input{05-float}` 追加到本章 `chapter.tex`。
节在章内的顺序由文件名前缀决定。

小节不是文件，直接写在所属节的 `.tex` 里：

```latex
\subsection{流水线冒险的三种来源}
\label{sec:04-processor-core-02-hazard}
```

### 删除一章、一节

```bash
rm -rf chapters/09-embedded-linux     # 删掉整章
scripts/build.sh                      # 清单会自动更新
```

删节则是删掉节文件，再在本章 `chapter.tex` 里删掉对应的 `\input` 行。

两个注意点：如果有别处用 `\cref{ch:09-...}` 引用过被删的章，会变成未解析引用；
另外 Issue 表单的章节下拉也要跟着变——这一步会在编译时自动完成；单独跑的话是
`python3 scripts/update-modules.py`。`weekly-status` 的测试会校验表单与 `chapters/`
是否一致，不一致时 CI 会报错。

### 调整章节顺序或改名

改目录名的数字前缀（`08-` 改成 `10-`）即可，章目录内部不用改。改完名后，
章里的 `\label{ch:08-xxx}` 仍保留旧写法，不影响编译，但建议顺手改一下。

## 写作约定

- 层级：`\chapter` → `\section` → `\subsection`，交叉引用用 `\label` 加 `\cref`。
- 要点框：`\KeyPoint{标题}{说明}`。
- 封面、章首页与页脚装饰都由 TikZ 直接绘制，强度在 `config/appearance.tex` 里调：
  把 `\CoverBadgeBorderTint`（封面"工作稿"标签描边）、`\ChapterGridTint`（章首页角落网格）、
  `\ChapterBottomTint` 与 `\BodyBottomTint`（章首页与正文页底部的电路走线）设为 `0`，
  即可关闭对应装饰（黑白打印或投稿时用得上）。底部电路线会按奇偶页镜像，
  始终从页面外侧伸进来，像电路从页面边缘继续延伸。
- 图片和代码按"越专用越靠近正文"放：
  - 本节专用 → 本章的 `figures/<节文件名>/` 与 `code/<节文件名>/`（目录用到时再建）
  - 本章多节共用 → 本章的 `figures/` 与 `code/`
  - 跨章复用 → 放在主用它的那一章，别的章写 `../NN-xxx/figures/文件名`
  - 前言、附录 → 各自的 `figures/` 与 `code/`
- **章里的路径一律相对本章目录写**（每章都在 `chapters/NN-xxx/`，所以两种编译方式都能找到）。
  前言和附录是全书级文件，由 `main.tex` 直接读入，引用素材时写从仓库根目录起的路径，
  例如 `\CodeListing{backmatter/code/hello.c}{...}`。
- 正文里这样引用：
  ```latex
  \includegraphics{figures/02-pipeline/hazard}
  \CodeListing{code/02-pipeline/pipeline.v}{五级流水线的实现}
  ```
  不要把长代码直接贴进正文。
- 定义、定理、例题：直接使用 `definition`、`theorem`、`example` 环境。
- 一节的写法建议按"问题引入 → 原理机制 → 示例或实验 → 小结与思考题"展开。
- 未确认的结论、数据、型号不要写成既成事实，统一用占位并标明出处。
- 占位内容统一写成 `待补充` 或 `% TODO`，便于收尾时统一检索。

## 编辑器里编译（VS Code）

`.vscode/settings.json` 已经配好：保存时自动编译，产物统一写进 `build/`，
不会散落在 `.tex` 旁边。

| 想做的事 | 改哪里 |
|---|---|
| 保存即编译整本书（当前设置） | `rootFile.useSubFile` 设为 `false` |
| 保存时只编译正在写的那一章 | `rootFile.useSubFile` 设为 `true`（产物在该章目录的 `build/`） |
| 关掉保存即编译，改为手动触发 | `autoBuild.run` 改成 `"never"` |

一个容易踩的坑：`main.tex` 开头有一行魔法注释 `% !TeX program = xelatex`。LaTeX Workshop
默认会据此决定编译器，一旦生效就会**跳过**配置好的 recipe，改用裸 `xelatex` 编译；
而裸 `xelatex` 没有输出目录参数，PDF 和中间文件就落到了仓库根目录。所以配置里把
`latex-workshop.latex.build.enableMagicComments` 设为 `false`，让编辑器始终使用配置好的
`latexmk (xelatex)` recipe。那行注释保留着，供 TeXstudio 等其他编辑器识别。

如果改了 `.vscode/settings.json` 后行为没有变化，用命令面板执行一次
**Developer: Reload Window**。另外请不要手动选择 `xelatex`、`pdflatex` 这类单步配方。

## 每周周报

每周日晚上 19:00（北京时间）自动生成当周的任务周报，提交到 `weekly-status/`，
同时显示在 Actions 的运行摘要里。报告里能看到各模块的任务数、交付情况、每位成员的
交付明细，以及每项任务的完成用时（天）。

周日晚 19:00 之后完成的交付不在这份报告里；周一再手动触发一次会覆盖同一份文件，
把数据补齐。

字段说明和手动生成方法见 [weekly-status/README.md](weekly-status/README.md)。

> 生成周报的 workflow 会向当前分支推送一次提交。如果给 `main` 开了分支保护，
> 要在保护规则里允许 GitHub Actions 推送，否则这一步会失败（报告仍会生成在运行摘要里）。

## 还有问题

不确定该改哪个文件、编译报错看不懂、或者发现流程本身有问题：用"技术问题"模板提一个 Issue，
把章节位置、你做了什么、完整的报错信息写清楚。
