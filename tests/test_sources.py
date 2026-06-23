import unittest
from unittest import mock

from job_radar import config, sources

WD_FIXTURE = {
    "total": 1,
    "jobPostings": [{
        "title": "AI Computing SW Engineer, TensorRT-LLM",
        "externalPath": "/job/Taiwan-Taipei/AI-SW-Engineer_JR123",
        "locationsText": "Taipei, Taiwan",
        "postedOn": "Posted 5 Days Ago",
        "bulletFields": ["JR123"],
    }],
}
GH_FIXTURE = {"jobs": [{
    "id": 4242, "title": "Machine Learning Engineer",
    "location": {"name": "Taipei, Taiwan"},
    "absolute_url": "https://boards.greenhouse.io/appier/jobs/4242",
    "updated_at": "2026-06-20T10:00:00Z",
}]}
LV_FIXTURE = [{
    "id": "abc-123", "text": "ML Engineer",
    "categories": {"location": "Taipei", "team": "AI"},
    "hostedUrl": "https://jobs.lever.co/Gogolook/abc-123",
    "createdAt": 1718000000000,
}]


class TestWorkday(unittest.TestCase):
    def test_parses_and_builds_url_and_key(self):
        one = [{"company": "NVIDIA", "host": "h.wd5.myworkdayjobs.com",
                "tenant": "nvidia", "site": "Ext"}]
        with mock.patch.object(sources, "WORKDAY", one), \
             mock.patch.object(config, "SEARCH_TERMS", ["LLM"]), \
             mock.patch.object(sources, "post_json", return_value=WD_FIXTURE) as p:
            jobs = sources.src_workday()
        self.assertEqual(len(jobs), 1)               # deduped across terms
        j = jobs[0]
        self.assertEqual(j.url,
                         "https://h.wd5.myworkdayjobs.com/en-US/Ext/job/Taiwan-Taipei/AI-SW-Engineer_JR123")
        self.assertEqual(j.key, "workday:NVIDIA:/job/Taiwan-Taipei/AI-SW-Engineer_JR123")
        self.assertEqual(j.location, "Taipei, Taiwan")
        self.assertEqual(j.posted, "Posted 5 Days Ago")
        # the CXS endpoint is what we POST to
        self.assertEqual(p.call_args[0][0],
                         "https://h.wd5.myworkdayjobs.com/wday/cxs/nvidia/Ext/jobs")

    def test_bad_endpoint_isolates_to_empty(self):
        with mock.patch.object(sources, "WORKDAY",
                               [{"company": "X", "host": "h", "tenant": "t", "site": "s"}]), \
             mock.patch.object(config, "SEARCH_TERMS", ["LLM"]), \
             mock.patch.object(sources, "post_json", side_effect=RuntimeError("403")):
            self.assertEqual(sources.src_workday(), [])


class TestGreenhouse(unittest.TestCase):
    def test_parses(self):
        with mock.patch.object(sources, "GREENHOUSE", [{"company": "Appier", "board": "appier"}]), \
             mock.patch.object(sources, "get_json", return_value=GH_FIXTURE):
            jobs = sources.src_greenhouse()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].key, "greenhouse:Appier:4242")
        self.assertEqual(jobs[0].location, "Taipei, Taiwan")
        self.assertEqual(jobs[0].url, "https://boards.greenhouse.io/appier/jobs/4242")


class TestLever(unittest.TestCase):
    def test_parses_and_converts_timestamp(self):
        with mock.patch.object(sources, "LEVER", [{"company": "Gogolook", "handle": "Gogolook"}]), \
             mock.patch.object(sources, "get_json", return_value=LV_FIXTURE):
            jobs = sources.src_lever()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].key, "lever:Gogolook:abc-123")
        self.assertEqual(jobs[0].posted, "2024-06-10")   # 1718000000000 ms -> ISO date
        self.assertIn("AI", jobs[0].snippet)             # team folded into snippet


if __name__ == "__main__":
    unittest.main()
