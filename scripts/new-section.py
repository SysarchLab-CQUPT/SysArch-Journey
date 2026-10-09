#!/usr/bin/env python3
"""在已有的一章里新增一节。

用法：
  python3 scripts/new-section.py chapters/04-processor-core "浮点运算与除法"
  python3 scripts/new-section.py chapters/04-processor-core "浮点运算与除法" 05-float

参数：
  章目录    例如 chapters/04-processor-core
  节标题    例如 "浮点运算与除法"
  文件名    可选，例如 05-float；省略时自动命名为 sNN

脚本做两件事：
  1. 在章目录里生成一节的文件骨架；
  2. 在本章 chapter.tex 的节清单末尾补上对应的 \\input 行。

节在章内的顺序由文件名的数字前缀决定。要重排，改文件名前缀，
再把 chapter.tex 里对应几行的先后调整一下即可。
"""

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SECTION_TEMPLATE = """% 本节专属的素材：图放本章目录的 figures/{stem}/，代码放 code/{stem}/。
% 章内多节共用的放 figures/ 或 code/ 根下；跨章复用的放在主用它的那一章。
% 正文里按相对本章目录的路径引用，例如 \\includegraphics{{figures/{stem}/xxx}}。
\\section{{{title}}}
\\label{{sec:{chapter}-{index}}}

% TODO：撰写本节正文。建议结构：
%   1) 问题引入与学习目标
%   2) 原理与机制（配图、公式）
%   3) 示例或实验步骤
%   4) 小结与思考题
本节待撰写。
"""


def next_index(chapter_dir):
    used = []
    for path in chapter_dir.glob("*.tex"):
        match = re.match(r"^(\d+)-", path.name)
        if match:
            used.append(int(match.group(1)))
    return max(used, default=0) + 1


def insert_input(chapter_tex, stem):
    lines = chapter_tex.read_text(encoding="utf-8").splitlines()
    entry = "\\input{%s}" % stem
    if entry in lines:
        return False
    last = None
    for position, line in enumerate(lines):
        if line.strip().startswith("\\input{"):
            last = position
    if last is None:
        end = next((p for p, l in enumerate(lines) if l.strip() == "\\end{document}"), len(lines))
        lines.insert(end, entry)
    else:
        lines.insert(last + 1, entry)
    chapter_tex.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="在已有章里新增一节")
    parser.add_argument("chapter_dir", help="章目录，例如 chapters/04-processor-core")
    parser.add_argument("title", help="节标题")
    parser.add_argument("filename", nargs="?", default="", help="可选文件名，例如 05-float")
    args = parser.parse_args()

    chapter_dir = (ROOT / args.chapter_dir).resolve()
    chapter_tex = chapter_dir / "chapter.tex"
    if not chapter_tex.is_file():
        raise SystemExit("找不到 %s，请确认这是章目录。" % chapter_tex)

    chapter = re.sub(r"^\d+-", "", chapter_dir.name)
    index = next_index(chapter_dir)

    if args.filename:
        stem = args.filename.strip()
        match = re.match(r"^(\d+)", stem)
        if match:
            index = int(match.group(1))
        stem = "%02d-%s" % (index, re.sub(r"^\d+-", "", stem))
    else:
        stem = "%02d-s%02d" % (index, index)

    target = chapter_dir / (stem + ".tex")
    if target.exists():
        raise SystemExit("文件已存在：%s" % target)

    target.write_text(
        SECTION_TEMPLATE.format(title=args.title, chapter=chapter, index="%02d" % index, stem=stem),
        encoding="utf-8",
    )
    insert_input(chapter_tex, stem)

    print("已新增 chapters/%s/%s.tex" % (chapter_dir.name, stem))
    print("本节素材目录（用到时再建）：chapters/%s/figures/%s/ 与 chapters/%s/code/%s/"
          % (chapter_dir.name, stem, chapter_dir.name, stem))
    print("下一步：scripts/build.sh chapters/%s/chapter.tex 预览本章" % chapter_dir.name)


if __name__ == "__main__":
    main()
