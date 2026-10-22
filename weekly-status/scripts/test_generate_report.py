"""Report regression tests run only by GitHub Actions."""

import os
import sys
import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import generate_report as report


START, END = report.week_range(date(2026, 8, 31))

# 测试用的模块，对应仓库里真实的一章，让报告分组与链接可预期。
CHAPTER = ("第9章 TinyML 与嵌入式智能应用部署", "chapters/09-edge-intelligence")
CHAPTER_BODY = "### 所属模块\n" + CHAPTER[0]


def body_with_estimate(days):
    return CHAPTER_BODY + "\n### 预估天数\n" + str(days)


def issue(number=1, state="open", created_at="2026-09-01T00:00:00Z", body="", assignees=None,
          title="[TASK] Test", **fields):
    result = {
        "number": number, "state": state, "created_at": created_at, "body": body,
        "assignees": assignees or [], "title": title,
        "html_url": "https://example.test/%s" % number, "user": {"login": "creator"},
    }
    result.update(fields)
    return result


def comment(body, login="github-actions[bot]", created_at="2026-09-01T00:00:00Z", user_type="Bot", id=1):
    return {"body": body, "created_at": created_at, "id": id,
            "user": {"login": login, "type": user_type}}


class ReportTest(unittest.TestCase):
    def test_week_boundary_is_beijing_half_open(self):
        self.assertTrue(report.in_week("2026-08-30T16:00:00Z", START, END))
        self.assertFalse(report.in_week("2026-09-06T16:00:00Z", START, END))

    def test_default_week_follows_the_sunday_evening_schedule(self):
        # 周日 19:00 的定时任务统计当周（本周一 00:00 起）
        self.assertEqual(report.default_week_start(datetime(2026, 9, 6, 19, tzinfo=report.BEIJING)),
                         date(2026, 8, 31))
        # 其他日子手动触发时统计上一个完整周
        now = datetime(2026, 9, 7, 9, tzinfo=report.BEIJING)
        self.assertEqual(report.default_week_start(now), date(2026, 8, 31))
        self.assertEqual(report.default_week_start(datetime(2026, 9, 9, 9, tzinfo=report.BEIJING)),
                         date(2026, 8, 31))

    def test_ddl_boundary_2400_and_invalid_values(self):
        self.assertEqual(report.parse_ddl("2026-09-01 24:00"), datetime(2026, 9, 2, 0, tzinfo=report.BEIJING))

        def reasons(number, ddl):
            body = "### 截止时间（DDL）\n" + ddl if ddl is not None else ""
            return report.week_reasons(issue(number=number, created_at="2026-08-01T00:00:00Z", body=body), START, END)

        self.assertEqual(reasons(1, "2026-08-31 00:00"), ["本周到期"])
        self.assertEqual(reasons(2, "2026-09-06 23:59"), ["本周到期"])
        self.assertEqual(reasons(3, "2026-09-06 24:00"), [])
        self.assertEqual(reasons(4, "2026-09-01 24:00"), ["本周到期"])
        self.assertEqual(reasons(5, None), [])
        self.assertEqual(reasons(6, "2026-09-31 12:00"), [])

    def test_week_reasons_are_the_deduplicated_union_of_all_three_conditions(self):
        body = CHAPTER_BODY + "\n### 截止时间（DDL）\n2026-09-03 12:00"
        task = issue(7, state="closed", body=body, closed_at="2026-09-04T00:00:00Z")
        self.assertEqual(report.week_reasons(task, START, END), ["本周新增", "本周交付", "本周到期"])

        text = report.build_report([task, task], {}, START, END, modules=[CHAPTER])
        self.assertIn("| 总计 | 1 | 1 | 1 | 1 | 0 | 0 |", text)
        self.assertIn(
            "| [%s](https://github.com/owner/repo/tree/HEAD/chapters/09-edge-intelligence) | 1 | 1 | 1 | 1 | 0 | 0 |"
            % CHAPTER[0], text)
        self.assertIn("[#7](https://example.test/7)", text)

    def test_person_issue_rows_match_their_six_column_header(self):
        body = CHAPTER_BODY + "\n### 截止时间（DDL）\n2026-09-03 18:00"
        task = issue(26, body=body, assignees=[{"login": "alice"}])
        text = report.build_report([task], {}, START, END, modules=[CHAPTER])
        self.assertIn("| Issue | 任务 | 所属模块 | 状态 | 完成用时（天） | DDL |", text)
        lines = text.splitlines()
        header_index = lines.index("| Issue | 任务 | 所属模块 | 状态 | 完成用时（天） | DDL |")
        separator = lines[header_index + 1]
        issue_row = next(line for line in lines[header_index + 2:] if "[#26]" in line)
        column_count = len(lines[header_index].strip("|").split("|"))
        self.assertEqual(len(separator.strip("|").split("|")), column_count)
        self.assertEqual(len(issue_row.strip("|").split("|")), column_count)

    def test_updated_or_commented_tasks_outside_the_three_conditions_are_excluded(self):
        old = "2026-08-01T00:00:00Z"
        updated = issue(created_at=old, updated_at="2026-09-02T00:00:00Z")
        commented = issue(number=2, created_at=old)
        text = report.build_report([updated, commented], {
            1: [], 2: [comment("ordinary comment", "alice", "2026-09-03T00:00:00Z", "User")],
        }, START, END)
        self.assertNotIn("[#1](https://example.test/1)", text)
        self.assertNotIn("[#2](https://example.test/2)", text)
        self.assertNotIn("@alice", text)

    def test_only_github_actions_markers_are_counted(self):
        comments = [comment("<!-- task-assignment:resolved claimant=alice -->", login="other-bot", id=1)]
        events, _, _, lgtm_count = report.analyze_comments(comments, START, END)
        self.assertEqual(events, [])
        self.assertEqual(lgtm_count, 0)

    def test_assignment_failures_do_not_count_as_confirmations(self):
        for state in ("resolved", "failed"):
            for message in (
                "认领未完成：该任务已经分配给 @bob。",
                "无法将 @alice 设为 Assignee。请确认该成员具有仓库协作权限后重新评论 `/assign`。",
            ):
                with self.subTest(state=state, message=message):
                    body = "<!-- task-assignment:%s claimant=alice -->\n%s" % (state, message)
                    events, _, _, _ = report.analyze_comments([comment(body)], START, END)
                    self.assertEqual(events, [])

    def test_assignment_retry_counts_only_success(self):
        comments = [
            comment("<!-- task-assignment:pending claimant=alice -->", id=1),
            comment("<!-- task-assignment:failed claimant=alice -->", id=2),
            comment("<!-- task-assignment:pending claimant=alice -->", id=3),
            comment("<!-- task-assignment:resolved claimant=alice -->\n认领已确认：@alice 现为该任务的执行人。", id=4),
        ]
        events, _, _, _ = report.analyze_comments(comments, START, END)
        self.assertEqual(events, [("认领确认", "alice")])

    def test_lgtm_is_deduplicated_and_excludes_executor_and_bots(self):
        comments = [
            comment("<!-- task-review:pending executor=alice -->", id=1),
            comment("LGTM", "bob", user_type="User", id=2),
            comment("lgtm", "bob", user_type="User", id=3),
            comment("LGTM", "alice", user_type="User", id=4),
            comment("LGTM", "robot", user_type="Bot", id=5),
        ]
        events, _, _, lgtm_count = report.analyze_comments(comments, START, END)
        self.assertEqual(events, [("提交验收", "alice"), ("有效LGTM", "bob")])
        self.assertEqual(lgtm_count, 1)

    def test_lgtm_with_a_substantive_suggestion_counts_as_a_review_vote(self):
        comments = [
            comment("<!-- task-review:pending executor=alice -->", id=1),
            comment("LGTM：建议补充图 4 的引用，并说明实验步骤。", "bob", user_type="User", id=2),
            comment("LGTM 很好", "carol", user_type="User", id=3),
        ]
        events, _, _, lgtm_count = report.analyze_comments(comments, START, END)
        self.assertEqual(events, [("提交验收", "alice"), ("有效LGTM", "bob"), ("有效LGTM", "carol")])
        self.assertEqual(lgtm_count, 2)
        self.assertEqual(report.lgtm_credit_level("LGTM"), "plain")
        self.assertEqual(
            report.lgtm_credit_level("LGTM：建议补充图 4 的引用，并说明实验步骤。"),
            "suggestion",
        )
        self.assertIsNone(report.lgtm_credit_level("Good LGTM"))

    def test_effective_lgtm_progress_from_zero_through_three(self):
        for expected in range(4):
            with self.subTest(expected=expected):
                comments = [comment("<!-- task-review:pending executor=alice -->", id=1)]
                comments.extend(comment("LGTM", "reviewer%s" % index, user_type="User", id=index + 2)
                                for index in range(expected))
                _, _, _, lgtm_count = report.analyze_comments(comments, START, END)
                self.assertEqual(lgtm_count, expected)
                self.assertEqual(report.current_status(issue(), lgtm_count),
                                 "未交付（未关闭）；LGTM %d/3" % expected)

    def test_cross_week_votes_show_total_progress_but_only_weekly_votes_contribute(self):
        comments = [
            comment("<!-- task-assignment:resolved claimant=alice -->", id=1),
            comment("<!-- task-review:pending executor=alice -->", created_at="2026-08-29T00:00:00Z", id=2),
            comment("LGTM", "bob", "2026-08-29T01:00:00Z", "User", id=3),
            comment("LGTM", "BOB", user_type="User", id=4),
            comment("LGTM", "carol", user_type="User", id=5),
            comment("LGTM", "dave", user_type="User", id=6),
            comment("<!-- task-review:resolved executor=alice -->", id=7),
            comment("LGTM", "eve", user_type="User", id=8),
        ]
        events, state, executor, lgtm_count = report.analyze_comments(comments, START, END)
        self.assertEqual(events, [("认领确认", "alice"), ("有效LGTM", "carol"), ("有效LGTM", "dave")])
        self.assertEqual((state, executor, lgtm_count), ("resolved", "alice", 3))

    def test_status_is_not_inferred_from_assignment_or_review(self):
        task = issue()
        comments = [
            comment("<!-- task-assignment:resolved claimant=alice -->", id=1),
            comment("<!-- task-review:pending executor=alice -->", id=2),
            comment("LGTM", "bob", user_type="User", id=3),
            comment("LGTM", "carol", user_type="User", id=4),
            comment("LGTM", "dave", user_type="User", id=5),
        ]
        text = report.build_report([task], {1: comments}, START, END)
        self.assertIn("| 总计 | 1 | 1 | 0 | 0 | 0 | 0 |", text)
        self.assertEqual(report.current_status(issue(state="closed"), 0), "已交付（已关闭）；LGTM 0/3")

    def test_legacy_task_quality_is_reported(self):
        missing = report.template_quality(issue(body=CHAPTER_BODY))
        self.assertIn("截止时间（DDL）", missing)
        self.assertIn("预估天数", missing)
        self.assertNotIn("所属模块", missing)

    def test_completion_days_counts_from_assignment_confirmation(self):
        task = issue(5, state="closed", created_at="2026-08-20T00:00:00Z", body=CHAPTER_BODY,
                     closed_at="2026-09-04T00:00:00Z")
        comments = [
            comment("<!-- task-assignment:pending claimant=alice -->", id=1),
            comment("<!-- task-assignment:resolved claimant=alice -->\n认领已确认：@alice 现为该任务的执行人。",
                    created_at="2026-08-31T00:00:00Z", id=2),
        ]
        self.assertAlmostEqual(report.completion_days(task, comments), 4.0)
        text = report.build_report([task, issue(6, state="closed", body=CHAPTER_BODY,
                                                closed_at="2026-09-02T00:00:00Z")],
                                   {5: comments}, START, END, modules=[CHAPTER])
        self.assertIn("| 4 |", text)

    def test_completion_days_falls_back_to_creation_and_skips_unfinished_tasks(self):
        closed = issue(6, state="closed", created_at="2026-08-30T00:00:00Z",
                       closed_at="2026-09-02T00:00:00Z", body=CHAPTER_BODY)
        self.assertAlmostEqual(report.completion_days(closed, []), 3.0)
        self.assertIsNone(report.completion_days(issue(7, body=CHAPTER_BODY), []))
        self.assertEqual(report.format_days(None), "-")
        self.assertEqual(report.format_days(10.0), "10")
        self.assertEqual(report.format_days(1.26), "1.3")
        self.assertEqual(report.format_days(0.5), "0.5")

    def test_estimated_task_days_accepts_positive_numbers_only(self):
        self.assertEqual(report.estimated_task_days(issue(body=body_with_estimate("2.5"))), 2.5)
        self.assertIsNone(report.estimated_task_days(issue(body=body_with_estimate("0"))))
        self.assertIsNone(report.estimated_task_days(issue(body=body_with_estimate("-1"))))
        self.assertIsNone(report.estimated_task_days(issue(body=body_with_estimate("abc"))))
        self.assertIsNone(report.estimated_task_days(issue(body=CHAPTER_BODY)))

    def test_score_report_tracks_cumulative_and_weekly_points(self):
        current = issue(
            1,
            state="closed",
            created_at="2026-08-25T00:00:00Z",
            closed_at="2026-09-04T00:00:00Z",
            body=body_with_estimate("5"),
            assignees=[{"login": "alice"}],
        )
        previous = issue(
            2,
            state="closed",
            created_at="2026-08-17T00:00:00Z",
            closed_at="2026-08-20T00:00:00Z",
            body=body_with_estimate("2"),
            assignees=[{"login": "alice"}],
        )
        shared = issue(
            3,
            state="closed",
            created_at="2026-08-31T00:00:00Z",
            closed_at="2026-09-06T00:00:00Z",
            body=body_with_estimate("4"),
            assignees=[{"login": "alice"}, {"login": "bob"}],
        )
        outside_week = issue(
            4,
            state="closed",
            created_at="2026-09-01T00:00:00Z",
            closed_at="2026-09-08T00:00:00Z",
            body=body_with_estimate("10"),
            assignees=[{"login": "alice"}],
        )
        comments = {
            1: [
                comment(
                    "<!-- task-assignment:resolved claimant=alice -->\n认领已确认：@alice 现为该任务的执行人。",
                    created_at="2026-08-31T00:00:00Z",
                )
            ]
        }

        text = report.build_score_report(
            [current, previous, shared, outside_week],
            comments,
            START,
            END,
            modules=[CHAPTER],
        )

        self.assertIn("# 人员积分统计：2026-08-31", text)
        self.assertIn("| 1 | @alice | 9 | 0 | 0 | 9 | 7 | 3 | 0 | 0 | 0 | 2026-09-06 |", text)
        self.assertIn("| 2 | @creator | 0 | 0 | 3.2 | 3.2 | 1.6 | 0 | 0 | 0 | 4 | 2026-09-01 |", text)
        self.assertIn("| 3 | @bob | 2 | 0 | 0 | 2 | 2 | 1 | 0 | 0 | 0 | 2026-09-06 |", text)
        self.assertIn("| 合计（人次） | - | 11 | 0 | 3.2 | 14.2 | 10.6 | 4 | 0 | 0 | 4 | - |", text)
        self.assertNotIn("| [#4](https://example.test/4) | Test | @alice |", text)
        self.assertIn("| 每人积分（天） |", text)

    def test_score_report_marks_completed_tasks_without_a_named_executor(self):
        task = issue(
            7,
            state="closed",
            created_at="2026-08-31T00:00:00Z",
            closed_at="2026-09-02T00:00:00Z",
            body=body_with_estimate("2"),
        )
        text = report.build_score_report([task], {}, START, END, modules=[CHAPTER])
        self.assertIn("| 1 | @creator | 0 | 0 | 0.8 | 0.8 | 0.8 | 0 | 0 | 0 | 1 |", text)
        self.assertIn("有 1 个已完成任务未能确定执行人，共 2 天积分未计入个人排名。", text)

    def test_completed_task_without_estimate_gets_no_completion_points(self):
        task = issue(
            10,
            state="closed",
            created_at="2026-08-31T00:00:00Z",
            closed_at="2026-09-02T00:00:00Z",
            body=CHAPTER_BODY,
            assignees=[{"login": "alice"}],
        )
        text = report.build_score_report([task], {}, START, END, modules=[CHAPTER])
        self.assertNotIn("@alice", text)
        self.assertIn(
            "有 1 个已完成任务缺少有效的“预估天数”（必须为大于 0 的数字），未计入任务完成积分。",
            text,
        )

    def test_score_report_awards_lgtm_review_and_task_publication_points(self):
        task = issue(
            8,
            state="open",
            created_at="2026-08-20T00:00:00Z",
            body=CHAPTER_BODY,
        )
        comments = [
            comment("<!-- task-review:pending executor=dave -->", created_at="2026-09-01T00:00:00Z", id=1),
            comment("LGTM", "alice", "2026-09-01T01:00:00Z", "User", id=2),
            comment(
                "LGTM：建议补充图 4 的引用，并说明实验步骤。",
                "bob",
                "2026-09-02T00:00:00Z",
                "User",
                id=3,
            ),
            comment(
                "LGTM：建议补充图 4 的引用，并说明实验步骤。",
                "alice",
                "2026-09-03T00:00:00Z",
                "User",
                id=4,
            ),
            comment("LGTM 很好", "carol", "2026-09-04T00:00:00Z", "User", id=5),
            comment("<!-- task-review:resolved executor=dave -->", created_at="2026-09-05T00:00:00Z", id=6),
        ]

        text = report.build_score_report([task], {8: comments}, START, END, modules=[CHAPTER])

        self.assertIn("| 1 | @creator | 0 | 0 | 0.8 | 0.8 | 0 | 0 | 0 | 0 | 1 | 2026-08-20 |", text)
        self.assertIn("| 2 | @alice | 0 | 0.5 | 0 | 0.5 | 0.5 | 0 | 1 | 1 | 0 | 2026-09-03 |", text)
        self.assertIn("| 3 | @bob | 0 | 0.5 | 0 | 0.5 | 0.5 | 0 | 1 | 1 | 0 | 2026-09-02 |", text)
        self.assertIn("| 4 | @carol | 0 | 0.2 | 0 | 0.2 | 0.2 | 0 | 1 | 0 | 0 | 2026-09-04 |", text)
        self.assertIn("| 合计（人次） | - | 0 | 1.2 | 0.8 | 2 | 1.2 | 0 | 3 | 2 | 1 | - |", text)
        self.assertIn("LGTM + 修改建议", text)
        self.assertIn("单独 LGTM", text)

    def test_suggestion_upgrade_only_adds_the_weekly_point_difference(self):
        task = issue(
            9,
            state="open",
            created_at="2026-08-20T00:00:00Z",
            body=CHAPTER_BODY,
        )
        comments = [
            comment("<!-- task-review:pending executor=dave -->", created_at="2026-08-30T00:00:00Z", id=1),
            comment("LGTM", "alice", "2026-08-30T01:00:00Z", "User", id=2),
            comment(
                "LGTM：建议补充图 4 的引用，并说明实验步骤。",
                "alice",
                "2026-09-01T00:00:00Z",
                "User",
                id=3,
            ),
        ]
        text = report.build_score_report([task], {9: comments}, START, END, modules=[CHAPTER])
        self.assertIn("| 2 | @alice | 0 | 0.5 | 0 | 0.5 | 0.3 | 0 | 1 | 1 | 0 |", text)

    def test_module_labels_resolve_to_chapter_paths(self):
        modules = report.repo_modules()
        self.assertIn(CHAPTER, modules)
        self.assertEqual(report.resolve_module(CHAPTER[0], modules), CHAPTER)
        self.assertEqual(report.resolve_module("chapters/09-edge-intelligence", modules), CHAPTER)
        self.assertEqual(report.resolve_module("09-edge-intelligence", modules), CHAPTER)
        self.assertEqual(report.resolve_module("排版、图表与校对", modules), ("排版、图表与校对", None))

    def test_unknown_module_keeps_its_own_group(self):
        text = report.build_report([issue(9, body="### 所属模块\n某个已改名的旧章节")], {},
                                   START, END, modules=[CHAPTER])
        self.assertIn("某个已改名的旧章节", text)
        self.assertNotIn("tree/HEAD/chapters", text)

    def test_module_delivery_uses_closed_at_and_assignees(self):
        tasks = [
            issue(state="closed", body=CHAPTER_BODY, closed_at="2026-09-01T00:00:00Z",
                  assignees=[{"login": "alice"}, {"login": "bob"}]),
            issue(number=2, body=CHAPTER_BODY, assignees=[{"login": "carol"}]),
        ]
        text = report.build_report(tasks, {2: [comment("<!-- task-review:resolved executor=carol -->")]},
                                   START, END, modules=[CHAPTER])
        self.assertIn("| 总计 | 2 | 2 | 1 | 0 | 0 | 0 |", text)
        self.assertIn("### @alice", text)
        self.assertIn("### @bob", text)
        self.assertIn("| [#1](https://example.test/1) | Test |", text)
        self.assertIn("| [#2](https://example.test/2) | Test |", text)
        self.assertIn("### @carol", text)

    def test_delivery_week_uses_closed_at_boundaries(self):
        tasks = [issue(number=index, state="closed", created_at="2026-08-01T00:00:00Z",
                       closed_at=closed_at, body=CHAPTER_BODY, assignees=[{"login": "alice"}])
                 for index, closed_at in enumerate([
                     "2026-08-30T15:59:59Z", "2026-08-30T16:00:00Z",
                     "2026-09-06T15:59:59Z", "2026-09-06T16:00:00Z"], 1)]
        text = report.build_report(tasks, {}, START, END, modules=[CHAPTER])
        self.assertIn("| 总计 | 2 | 0 | 2 | 0 | 0 | 0 |", text)
        self.assertIn("### @alice", text)

    def test_current_unclosed_and_overdue_columns(self):
        overdue_body = "### 截止时间（DDL）\n2026-09-01 24:00"
        active = issue(body=overdue_body, assignees=[{"login": "alice"}, {"login": "bob"}])
        pending = issue(number=2, assignees=[{"login": "bob"}])
        text = report.build_report([active, pending], {1: [], 2: []}, START, END,
                                   now=datetime(2026, 9, 7, tzinfo=report.BEIJING))
        self.assertIn("| 0 | 1 | 1 | 0 | 0 |", text)
        self.assertIn("| 总计 | 2 | 2 | 0 | 1 | 1 | 0 |", text)
        self.assertIn("### @alice", text)
        self.assertIn("### @bob", text)

    def test_report_starts_with_title_and_seven_column_module_table(self):
        text = report.build_report([], {}, START, END)
        lines = text.splitlines()
        self.assertEqual(lines[0], "# 周报：2026-08-31")
        header_index = lines.index(
            "| 所属模块 | 任务数 | 本周新增 | 本周交付 | 本周到期 | 本周到期未完成 | 历史逾期 |")
        self.assertEqual(len(lines[header_index].strip("|").split("|")), 7)

    def test_pull_requests_and_non_tasks_do_not_count(self):
        tasks = [issue(state="closed", pull_request={"url": "https://example.test/pr"}),
                 issue(number=2, state="closed", title="Not a task")]
        text = report.build_report(tasks, {}, START, END, modules=[CHAPTER])
        self.assertNotIn("[#1]", text)
        self.assertNotIn("[#2]", text)

    def test_main_fetches_comments_for_all_tasks_needed_by_scores(self):
        class Client:
            calls = []

            def __init__(self, token):
                pass

            def get_paginated(self, path, params=None):
                self.calls.append((path, params))
                if path.endswith("/issues"):
                    return [
                        issue(1, comments=2),
                        issue(2, created_at="2026-08-01T00:00:00Z", updated_at="2026-09-02T00:00:00Z", comments=4),
                        issue(3, comments=0),
                    ]
                if path.endswith("/issues/1/comments"):
                    return []
                if path.endswith("/issues/2/comments"):
                    return []
                raise AssertionError("unexpected comment request: " + path)

        with TemporaryDirectory() as temporary, mock.patch.dict(os.environ, {"GH_TOKEN": "token"}, clear=False), \
                mock.patch.object(report, "GitHubClient", Client), \
                mock.patch.object(report, "repo_modules", return_value=[]):
            report.main(["--repo", "org/repo", "--week-start", "2026-08-31", "--output-dir", temporary])
            weekly_path = Path(temporary) / "2026-08-31.md"
            score_path = Path(temporary) / "scores" / "2026-08-31.md"
            self.assertTrue(weekly_path.is_file())
            self.assertTrue(score_path.is_file())
            self.assertNotIn("人员积分统计", weekly_path.read_text(encoding="utf-8"))
            self.assertIn("# 人员积分统计：2026-08-31", score_path.read_text(encoding="utf-8"))

        self.assertEqual(Client.calls, [
            ("/repos/org/repo/issues", {"state": "all"}),
            ("/repos/org/repo/issues/1/comments", None),
            ("/repos/org/repo/issues/2/comments", None),
        ])

    def test_api_failure_does_not_create_report(self):
        class FailingClient:
            def __init__(self, token):
                pass

            def get_paginated(self, path, params=None):
                raise RuntimeError("network failure")

        with TemporaryDirectory() as temporary, mock.patch.dict(os.environ, {"GH_TOKEN": "token"}, clear=False), \
                mock.patch.object(report, "GitHubClient", FailingClient):
            output = Path(temporary) / "output"
            with self.assertRaises(RuntimeError):
                report.main(["--repo", "org/repo", "--week-start", "2026-08-31", "--output-dir", str(output)])
            self.assertFalse(output.exists())

    def test_pagination_follows_next_link(self):
        class Client(report.GitHubClient):
            def __init__(self):
                pass

            def _request(self, url):
                if "page=1" in url:
                    return [{"id": 1}], '<https://api.github.com/test?page=2>; rel="next"'
                return [{"id": 2}], ""

        self.assertEqual([item["id"] for item in Client().get_paginated("/test")], [1, 2])


if __name__ == "__main__":
    unittest.main()
