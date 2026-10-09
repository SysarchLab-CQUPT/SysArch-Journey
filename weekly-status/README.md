# 周报

每周日晚上 19:00（北京时间）由 GitHub Actions 自动生成当周的周报，文件名是
`YYYY-MM-DD.md`（即那一周周一的日期）。报告同时会写入 Actions 的运行摘要。

周日晚 19:00 之后到 24:00 之间完成的交付不在这份报告里；周一再手动触发一次，
会覆盖同一份文件把数据补齐。

## 报告内容

- 顶部：统计区间，北京时间周一 00:00 到下周周一 00:00，左闭右开。
- 所属模块汇总：每个模块本周的任务数、新增、交付、到期、到期未完成、历史逾期。
- 按人分组：每位执行人本周交付、当前未关闭、本周到期未完成、历史逾期、未认领风险，
  以及任务明细。

任务明细里的**完成用时（天）**＝从认领确认（没有认领记录时从创建）到任务关闭的
自然日天数；任务还没关闭时显示 `-`。

入选规则：只统计"本周创建""本周关闭""DDL 在本周"这三类任务，取并集并按 Issue 去重。

## 手动生成

```bash
GH_TOKEN=<你的 GitHub 令牌> python3 weekly-status/scripts/generate_report.py \
    --repo <owner>/<repo> --week-start 2026-10-06
```

`--week-start` 必须是周一。省略时：周日生成当周，其他日子生成上一个完整周。

## 测试

```bash
python3 -B -m unittest discover -s weekly-status/scripts -p 'test_*.py'
```

`test_directory_options.py` 会检查 Issue 表单里的模块下拉与 `chapters/` 下的章节
是否一一对应。**新增、删除或重命名章节后**，如果表单没同步，这个测试会失败。

同步不需要手动改 YAML：

```bash
python3 scripts/update-modules.py      # 编译整本书时会自动调用
```
