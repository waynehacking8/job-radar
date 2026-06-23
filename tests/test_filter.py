import unittest

from job_radar.filter import evaluate, fresh_days
from job_radar.models import Job


def mk(title, location, snippet="", posted=""):
    return Job(key="k", company="X", title=title, location=location, url="u",
               source="workday", snippet=snippet, posted=posted)


class TestEvaluate(unittest.TestCase):
    def test_keeps_taiwan_llm_role_as_strong(self):
        j = mk("AI Computing SW Engineer, TensorRT-LLM", "Taipei, Taiwan")
        self.assertTrue(evaluate(j))
        self.assertEqual(j.fit, "strong")
        self.assertGreater(j.score, 0)
        self.assertIn("TENSORRT", " ".join(j.tags).upper())

    def test_drops_non_taiwan(self):
        self.assertFalse(evaluate(mk("Senior GPU Kernel Engineer", "US, CA, Santa Clara")))

    def test_drops_excluded_function_even_with_keyword(self):
        # "AI" hits MEDIUM but the title is a sales role -> excluded.
        self.assertFalse(evaluate(mk("AI Solutions Sales Manager", "Taipei, Taiwan")))
        self.assertFalse(evaluate(mk("Machine Learning Intern", "Hsinchu, Taiwan")))

    def test_drops_off_topic(self):
        self.assertFalse(evaluate(mk("Mechanical Design Engineer", "Hsinchu, Taiwan")))

    def test_medium_fit_when_only_adjacent_keyword(self):
        j = mk("AI Engineer", "Taipei, Taiwan")
        self.assertTrue(evaluate(j))
        self.assertEqual(j.fit, "medium")

    def test_title_keyword_outscores_snippet_only(self):
        in_title = mk("LLM Inference Engineer", "Taipei, Taiwan")
        in_snip = mk("Software Engineer", "Taipei, Taiwan", snippet="works on LLM inference")
        evaluate(in_title)
        evaluate(in_snip)
        self.assertGreater(in_title.score, in_snip.score)

    def test_chinese_keywords_match(self):
        self.assertTrue(evaluate(mk("機器學習工程師", "新竹")))


class TestFreshDays(unittest.TestCase):
    def test_iso_date(self):
        self.assertIsNotNone(fresh_days("2026-06-01"))
        self.assertGreaterEqual(fresh_days("2026-06-01"), 0)

    def test_workday_text(self):
        self.assertEqual(fresh_days("Posted Today"), 0)
        self.assertEqual(fresh_days("Posted Yesterday"), 1)
        self.assertEqual(fresh_days("Posted 5 Days Ago"), 5)
        self.assertEqual(fresh_days("Posted 30+ Days Ago"), 30)

    def test_unparseable_is_none(self):
        self.assertIsNone(fresh_days(""))
        self.assertIsNone(fresh_days("recently"))


if __name__ == "__main__":
    unittest.main()
