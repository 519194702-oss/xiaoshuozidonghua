import json
import tempfile
import unittest
from pathlib import Path

import novel_automation as na


class NovelAutomationTests(unittest.TestCase):
    def test_generate_project_contains_expected_sections(self):
        project = na.NovelAutomator("雾城来信", "悬疑", "许知远", "追寻真相也要守住自我", 3).build_project()
        markdown = na.project_to_markdown(project)

        self.assertIn("# 雾城来信", markdown)
        self.assertIn("## 简介", markdown)
        self.assertIn("## 剧情大纲", markdown)
        self.assertIn("## 分章剧情与正文草稿", markdown)
        self.assertEqual(len(project.chapters), 3)
        self.assertTrue(all(chapter.draft for chapter in project.chapters))

    def test_json_output_is_valid(self):
        project = na.NovelAutomator("星门", "科幻", "陆遥", "用勇气面对未知", 2).build_project()
        payload = json.loads(na.project_to_json(project))

        self.assertEqual(payload["title"], "星门")
        self.assertEqual(payload["genre"], "科幻")
        self.assertEqual(len(payload["chapters"]), 2)

    def test_proofread_reports_empty_and_repetition(self):
        self.assertIn("文本为空", na.proofread_text("")[0])
        report = "\n".join(na.proofread_text("他非常非常紧张，在在门口停下。"))
        self.assertIn("在在", report)
        self.assertIn("非常非常", report)

    def test_cli_generate_writes_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "novel.md"
            na.main([
                "generate",
                "--title",
                "测试小说",
                "--genre",
                "都市",
                "--chapters",
                "1",
                "--output",
                str(output),
            ])
            self.assertTrue(output.exists())
            self.assertIn("测试小说", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
