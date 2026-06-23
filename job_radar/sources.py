"""Job sources. Each `src_*()` returns a list[Job] and self-isolates (returns []
on any failure) so one broken employer can't sink the run.

Why these three ATSs and not LinkedIn: Workday, Greenhouse and Lever all expose
keyless JSON endpoints that work headlessly from a cron runner. LinkedIn and the
Phenom/Eightfold portals (Qualcomm, MediaTek) are JS-rendered / bot-blocked and
would need a headful browser — deliberately out of scope (same reason gh-radar
skips the X API). Add an employer by extending the registry below.
"""
import sys
import time
from datetime import datetime, timezone

from .clients import get_json, post_json
from .models import Job

# --------------------------------------------------------------------- registry
# Workday: the public job URL is https://{host}/en-US/{site}{externalPath};
# the CXS search endpoint is https://{host}/wday/cxs/{tenant}/{site}/jobs.
# NOTE: only true Workday tenants belong here. AMD / Qualcomm / MediaTek run on
# Phenom / Eightfold (custom JSON, JS-gated) — they need their own adapters, not
# this CXS shape, so they're intentionally absent in v1.
WORKDAY = [
    {"company": "NVIDIA",  "host": "nvidia.wd5.myworkdayjobs.com", "tenant": "nvidia",  "site": "NVIDIAExternalCareerSite"},
    {"company": "Micron",  "host": "micron.wd1.myworkdayjobs.com", "tenant": "micron",  "site": "External"},
    {"company": "Cadence", "host": "cadence.wd1.myworkdayjobs.com","tenant": "cadence", "site": "External_Careers"},
]
GREENHOUSE = [
    {"company": "Appier", "board": "appier"},
]
LEVER = [
    {"company": "Gogolook", "handle": "Gogolook"},
]

# Imported lazily to avoid a config<->sources cycle at module load.
from . import config  # noqa: E402


def _job(source, company, job_id, title, location, url, posted="", snippet=""):
    return Job(
        key=f"{source}:{company}:{job_id}",
        company=company, title=title or "", location=location or "",
        url=url or "", source=source, posted=posted or "", snippet=snippet or "",
    )


# --------------------------------------------------------------------- Workday
def _workday_one(c):
    base = f"https://{c['host']}/wday/cxs/{c['tenant']}/{c['site']}/jobs"
    pub = f"https://{c['host']}/en-US/{c['site']}"
    out = {}
    for term in config.SEARCH_TERMS:
        try:
            data = post_json(base, {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": term})
        except Exception as e:  # noqa: BLE001
            print(f"    ! workday {c['company']} '{term}': {e}", file=sys.stderr)
            continue
        for p in data.get("jobPostings", []) or []:
            ep = p.get("externalPath") or ""
            if not ep or ep in out:
                continue
            bullets = " ".join(p.get("bulletFields") or [])
            out[ep] = _job(
                "workday", c["company"], ep,
                p.get("title", ""), p.get("locationsText", ""),
                pub + ep, posted=p.get("postedOn", ""),
                snippet=f"{p.get('title','')} {bullets}",
            )
    return list(out.values())


def src_workday():
    jobs = []
    for c in WORKDAY:
        n0 = len(jobs)
        jobs += _workday_one(c)
        print(f"  workday:{c['company']}: {len(jobs) - n0}", file=sys.stderr)
    return jobs


# --------------------------------------------------------------------- Greenhouse
def src_greenhouse():
    jobs = []
    for c in GREENHOUSE:
        try:
            data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{c['board']}/jobs?content=true")
        except Exception as e:  # noqa: BLE001
            print(f"  ! greenhouse {c['company']}: {e}", file=sys.stderr)
            continue
        got = 0
        for j in data.get("jobs", []) or []:
            loc = (j.get("location") or {}).get("name", "")
            jobs.append(_job(
                "greenhouse", c["company"], str(j.get("id", "")),
                j.get("title", ""), loc, j.get("absolute_url", ""),
                posted=j.get("updated_at", ""), snippet=j.get("title", ""),
            ))
            got += 1
        print(f"  greenhouse:{c['company']}: {got}", file=sys.stderr)
    return jobs


# --------------------------------------------------------------------- Lever
def src_lever():
    jobs = []
    for c in LEVER:
        try:
            data = get_json(f"https://api.lever.co/v0/postings/{c['handle']}?mode=json")
        except Exception as e:  # noqa: BLE001
            print(f"  ! lever {c['company']}: {e}", file=sys.stderr)
            continue
        got = 0
        for p in data or []:
            cats = p.get("categories") or {}
            ms = p.get("createdAt")
            posted = ""
            if isinstance(ms, (int, float)):
                posted = datetime.fromtimestamp(ms / 1000, timezone.utc).date().isoformat()
            team = cats.get("team", "")
            jobs.append(_job(
                "lever", c["company"], str(p.get("id", "")),
                p.get("text", ""), cats.get("location", ""), p.get("hostedUrl", ""),
                posted=posted, snippet=f"{p.get('text','')} {team}",
            ))
            got += 1
        print(f"  lever:{c['company']}: {got}", file=sys.stderr)
    return jobs


SOURCES = [("workday", src_workday), ("greenhouse", src_greenhouse), ("lever", src_lever)]
