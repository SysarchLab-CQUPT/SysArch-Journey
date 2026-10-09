#!/usr/bin/env python3
"""新建一章的骨架。

用法：
  python3 scripts/new-chapter.py 03 riscv-isa "指令集架构与汇编" \
      --sections "overview:指令集的作用;asm:RISC-V 汇编入门;from-asm:从汇编到机器码"

参数：
  序号      两位数字，决定章在全书中的顺序，例如 03
  目录名    英文短名，用于生成目录与标签，例如 riscv-isa
  章标题    中文标题

节之间用分号分隔，每节写成 “文件名:标题”；只写标题时自动命名为 s01、s02……
生成后请运行：python3 scripts/update-manifest.py
"""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHAPTER_TEMPLATE = """% 第{number}章 {title}
% 由 scripts/new-chapter.py 生成。
% 单章预览：scripts/build.sh chapters/{folder}/chapter.tex
%
% 素材约定（路径都相对本章目录）：
%   本节专属的图   figures/<节文件名>/xxx     代码  code/<节文件名>/xxx
%   本章多节共用   figures/xxx                代码  code/xxx
%   跨章复用       放在主用它的那一章，其他章用 ../NN-xxx/figures/xxx 引用
\\documentclass[../../main.tex]{{subfiles}}

\\begin{{document}}

\\chapter{{{title}}}
\\label{{ch:{folder}}}
{inputs}
\\end{{document}}
"""

SECTION_TEMPLATE = """\\section{{{title}}}
\\label{{sec:{folder}-{index}}}

% TODO：撰写本节正文。建议结构：
%   1) 问题引入与学习目标
%   2) 原理与机制（配图、公式）
%   3) 示例或实验步骤
%   4) 小结与思考题
本节待撰写。
"""

BIB_TEMPLATE = """% 第{number}章 参考文献。
% 每章单独维护自己的 .bib，避免多人同时编辑同一文件。
"""


def parse_sections(raw):
    items = []
    for position, chunk in enumerate([c.strip() for c in raw.split(";") if c.strip()], 1):
        if ":" in chunk:
            slug, title = chunk.split(":", 1)
        else:
            slug, title = "s%02d" % position, chunk
        items.append((slug.strip(), title.strip()))
    return items


def main():
    parser = argparse.ArgumentParser(description="新建一章的 LaTeX 骨架")
    parser.add_argument("number", help="两位序号，例如 03")
    parser.add_argument("slug", help="英文短名，例如 riscv-isa")
    parser.add_argument("title", help="章标题")
    parser.add_argument("--sections", default="", help="分号分隔的节列表，格式 文件名:标题")
    args = parser.parse_args()

    folder = "%s-%s" % (args.number, args.slug)
    chapter_dir = ROOT / "chapters" / folder
    if chapter_dir.exists():
        raise SystemExit("目录已存在：%s" % chapter_dir)
    chapter_dir.mkdir(parents=True)

    sections = parse_sections(args.sections)
    inputs = []
    for index, (slug, title) in enumerate(sections, 1):
        filename = "%02d-%s.tex" % (index, slug)
        (chapter_dir / filename).write_text(
            SECTION_TEMPLATE.format(title=title, folder=folder, index="%02d" % index),
            encoding="utf-8",
        )
        # 用相对本章目录的路径，重命名章目录时不必再改这些行。
        inputs.append("\\input{%s}" % filename[:-4])

    (chapter_dir / "chapter.tex").write_text(
        CHAPTER_TEMPLATE.format(
            number=args.number,
            title=args.title,
            folder=folder,
            inputs=("\n".join(inputs) + "\n") if inputs else "",
        ),
        encoding="utf-8",
    )
    (chapter_dir / "refs.bib").write_text(BIB_TEMPLATE.format(number=args.number), encoding="utf-8")

    # 本章专属的图与代码各有一个目录，跟着章目录一起搬。
    for name in ("figures", "code"):
        (chapter_dir / name).mkdir()
        (chapter_dir / name / ".gitkeep").write_text("", encoding="utf-8")

    print("已创建 chapters/%s（%d 节）。" % (folder, len(sections)))
    print("下一步：python3 scripts/update-manifest.py")


if __name__ == "__main__":
    main()
