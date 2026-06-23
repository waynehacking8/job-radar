import unittest

from job_radar.models import Job
from job_radar.render import md_to_html, render_md


def mk(title, fit, score):
    return Job(key="k", company="ACME", title=title, location="Taipei, Taiwan",
               url="https://x/job", source="workday", fit=fit, score=score,
               tags=["LLM", "CUDA"])


class TestRender(unittest.TestCase):
    def test_groups_strong_before_medium(self):
        jobs = [mk("AI Engineer", "medium", 3), mk("LLM Inference Engineer", "strong", 18)]
        md = render_md(jobs, "2026-06-23")
        self.assertIn("Strong fit", md)
        self.assertIn("Adjacent", md)
        # the strong section must appear before the adjacent section
        self.assertLess(md.index("Strong fit"), md.index("Adjacent"))
        self.assertIn("[Apply →](https://x/job)", md)
        self.assertIn("ACME", md)

    def test_html_escapes_and_converts(self):
        jobs = [mk("C++ & CUDA <kernel>", "strong", 10)]
        html = md_to_html(render_md(jobs, "2026-06-23"))
        self.assertIn("&lt;kernel&gt;", html)        # angle brackets escaped
        self.assertIn("&amp;", html)                  # ampersand escaped
        self.assertIn('<a href="https://x/job">', html)  # link converted
        self.assertIn("<strong>ACME</strong>", html)  # bold converted


if __name__ == "__main__":
    unittest.main()
