#!/usr/bin/env python3
"""生成 config/manifest.tex —— 正文各章的装配清单。

约定：
  chapters/<NN>-<名称>/chapter.tex    一章的入口
  chapters/<NN>-<名称>/refs.bib       该章参考文献（可选）

章的顺序完全由目录名前缀决定。新增、删除或调整章节时，只需要改动
chapters/ 下的目录，然后重新运行本脚本即可；main.tex 不用动，
清单文件也是生成的，因此多人同时写作不会在装配处产生冲突。
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "chapters"


def chapter_dirs():
    if not CHAPTERS.is_dir():
        return []
    return sorted(
        (p for p in CHAPTERS.iterdir() if p.is_dir() and (p / "chapter.tex").is_file()),
        key=lambda p: p.name,
    )


def main():
    dirs = chapter_dirs()
    bibs = ["chapters/%s/refs" % d.name for d in dirs if (d / "refs.bib").is_file()]
    lines = [
        "% 本文件由 scripts/update-manifest.py 自动生成，请勿手工修改。",
        "% 章的清单来自 chapters/ 下的目录（按目录名排序）。",
        "",
    ]
    lines += ["\\subfile{chapters/%s/chapter}" % d.name for d in dirs]
    lines += [
        "",
        "% 参考文献：各章 refs.bib 按章顺序合并。",
        "\\def\\BibliographyResources{%s}" % ",".join(bibs),
        "\\HasBibliography%s" % ("true" if bibs else "false"),
    ]
    (ROOT / "config" / "manifest.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("已更新 config/manifest.tex：%d 章，%d 个参考文献文件。" % (len(dirs), len(bibs)))


if __name__ == "__main__":
    main()
