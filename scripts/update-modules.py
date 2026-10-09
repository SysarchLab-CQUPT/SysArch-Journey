#!/usr/bin/env python3
"""把 Issue 表单里的"章节"下拉同步成 chapters/ 下的实际章节。

用法：
  python3 scripts/update-modules.py

处理的表单（每个表单只改开头的"第N章 …"这一整段，其余选项原样保留）：
  .github/ISSUE_TEMPLATE/task_request.yml             id: module
  .github/ISSUE_TEMPLATE/technical_qa.yml             id: module
  .github/ISSUE_TEMPLATE/contribution_certificate.yml id: direction

新增、删除、重命名或调整章节顺序之后跑一次，各个表单的下拉就与 chapters/
对齐了。编译整本书时 build.sh 会自动调用，所以平时不用记这一步。

"配套代码与实验环境""排版、图表与校对"这类非章节选项不在本脚本的管理范围内，
它们原样保留在每个表单自己的位置。

weekly-status/scripts/test_directory_options.py 会检查任务表单与 chapters/ 是否
一致，两边不一致时 CI 会失败——这个脚本就是用来修它的。
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# （表单文件，需要同步的字段 id）
FORMS = (
    (".github/ISSUE_TEMPLATE/task_request.yml", "module"),
    (".github/ISSUE_TEMPLATE/technical_qa.yml", "module"),
    (".github/ISSUE_TEMPLATE/contribution_certificate.yml", "direction"),
)

CHAPTER_OPTION = re.compile(r"^第\d+章\s")
OPTION_LINE = re.compile(r"^(\s*)- (.*)$")
CHAPTER_TITLE = re.compile(r"\\chapter\{([^}]*)\}")


def chapter_labels():
    """按目录名顺序，从各章 chapter.tex 里取出"第N章 标题"。"""
    chapters = ROOT / "chapters"
    labels = []
    if not chapters.is_dir():
        return labels
    for child in sorted(path for path in chapters.iterdir() if path.is_dir()):
        entry = child / "chapter.tex"
        if not entry.is_file():
            continue
        match = CHAPTER_TITLE.search(entry.read_text(encoding="utf-8"))
        if not match:
            continue
        number = re.match(r"^(\d+)", child.name)
        title = match.group(1).strip()
        labels.append("第%d章 %s" % (int(number.group(1)), title) if number else title)
    return labels


def option_target(lines, field_id):
    """返回 (options 行号, 选项行区间起, 选项行区间止)，找不到返回 None。"""
    field = None
    for index, line in enumerate(lines):
        if re.match(r"^\s*id:\s*%s\s*$" % re.escape(field_id), line):
            field = index
            break
    if field is None:
        return None, "找不到 id: %s" % field_id

    options = None
    for index in range(field + 1, len(lines)):
        if re.match(r"^\s*validations:", lines[index]):
            break
        if re.match(r"^\s*options:\s*$", lines[index]):
            options = index
            break
    if options is None:
        return None, "找不到 options:"

    end = options + 1
    while end < len(lines) and OPTION_LINE.match(lines[end]):
        end += 1
    if end == options + 1:
        return None, "options 是空的"
    return options, end


def sync_form(path, field_id, labels):
    lines = path.read_text(encoding="utf-8").splitlines()
    options, detail = option_target(lines, field_id)
    if options is None:
        return "跳过（%s）" % detail

    block = lines[options + 1:detail]
    indent = OPTION_LINE.match(block[0]).group(1)

    # 找出开头的"第N章 …"连续段，整段换成最新的章节列表
    first = next(
        (index for index, line in enumerate(block)
         if CHAPTER_OPTION.match(OPTION_LINE.match(line).group(2))),
        None,
    )
    if first is None:
        first = 0
    last = first
    while last < len(block) and CHAPTER_OPTION.match(OPTION_LINE.match(block[last]).group(2)):
        last += 1

    updated = block[:first] + ["%s- %s" % (indent, label) for label in labels] + block[last:]
    if updated == block:
        return "已是最新（%d 个章节选项）" % len(labels)

    path.write_text("\n".join(lines[:options + 1] + updated + lines[detail:]) + "\n", encoding="utf-8")
    return "已更新为 %d 个章节选项" % len(labels)


def main():
    labels = chapter_labels()
    if not labels:
        raise SystemExit("chapters/ 下没有找到章节，未做任何修改。")
    for relative, field_id in FORMS:
        path = ROOT / relative
        if not path.is_file():
            print("%-52s 跳过（文件不存在）" % relative)
            continue
        print("%-52s %s" % (relative, sync_form(path, field_id, labels)))
    print("当前章节：" + "、".join(labels))


if __name__ == "__main__":
    main()
