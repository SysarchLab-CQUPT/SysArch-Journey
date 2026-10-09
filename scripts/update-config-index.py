#!/usr/bin/env python3
"""生成 config/README.md：配置宏索引。

遍历 config/ 下的 .tex 文件，列出每个宏的定义位置，方便作者查找
“书名、配色、页面参数”写在哪个文件里。manifest.tex 是生成文件，跳过。
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    lines = [
        "# 配置宏索引",
        "",
        "由 scripts/update-config-index.py 生成，勿手工修改。",
        "业务值在 config/ 下对应的 .tex 文件中维护。",
        "",
    ]
    count = 0
    for file in sorted((ROOT / "config").glob("*.tex")):
        if file.name == "manifest.tex":
            continue
        entries = []
        for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
            match = re.search(r"\\newcommand\{\\([A-Za-z]+)\}", line)
            if match:
                entries.append((match.group(1), number))
        if not entries:
            continue
        lines += ["## " + file.name, "", "| 宏 | 定义位置 |", "|---|---|"]
        for name, number in entries:
            lines.append("| `\\%s` | [%d](<%s#L%d>) |" % (name, number, file.name, number))
        lines.append("")
        count += len(entries)
    (ROOT / "config" / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print("已更新 config/README.md，收录 %d 个宏。" % count)


if __name__ == "__main__":
    main()
