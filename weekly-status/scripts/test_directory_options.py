"""Keep the static GitHub form options aligned with the chapters in this repository."""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import generate_report as report


class ModuleOptionsTest(unittest.TestCase):
    def test_form_options_match_chapters(self):
        root = Path(__file__).resolve().parents[2]
        form = (root / ".github/ISSUE_TEMPLATE/task_request.yml").read_text(encoding="utf-8")
        field = form.split("id: module\n", 1)[1].split("    validations:", 1)[0]
        options = re.findall(r"^        - (.+)$", field, re.MULTILINE)
        self.assertEqual(len(options), len(set(options)), "Issue 表单的模块选项有重复")

        modules = report.repo_modules(root)
        self.assertEqual(options, [label for label, _ in modules],
                         "Issue 表单的模块选项与 chapters/ 下的章节不一致")

        for label, path in modules:
            with self.subTest(label=label):
                self.assertEqual(report.resolve_module(label, modules), (label, path))
                if path:
                    self.assertTrue((root / path / "chapter.tex").is_file())


if __name__ == "__main__":
    unittest.main()
