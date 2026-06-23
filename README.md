# job-radar

[![CI](https://github.com/waynehacking8/job-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/waynehacking8/job-radar/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A daily email digest of NEW Taiwan ML / LLM / GPU job openings — pulled from the ATS APIs your
target employers actually run on, not from LinkedIn scraping.** Runs on GitHub Actions; you never
see the same posting twice.

> Sibling of [`gh-radar`](https://github.com/waynehacking8/gh-radar) (trending GitHub tools). Same
> shape — isolated sources → de-dup memory → ranked digest → email — pointed at the job market.

## Why ATS APIs instead of LinkedIn

LinkedIn job search is bot-blocked and JS-rendered; scraping it from a cron runner is fragile and
against ToS. But most large/foreign employers run their careers site on **Workday**, **Greenhouse**,
or **Lever** — all of which expose **keyless JSON endpoints** that work headlessly. job-radar hits
those directly, so a posting's title, location, URL, and date are structured data, not scraped HTML.
(LinkedIn and the Phenom/Eightfold portals — Qualcomm, MediaTek — are deliberately out of scope, the
same way gh-radar skips the X API. A LinkedIn *Job Alert* covers those by email.)

## How it works

```
GitHub Actions cron (multi-window)
        |
        v
  collect()  ── Workday CXS ┐
             ── Greenhouse  ┼─ each source self-isolates (one outage ≠ no digest)
             ── Lever       ┘
        |
        v
  select()   filter: Taiwan only · ML/LLM/GPU keyword · drop sales/HR/intern
             rank:   strong vs adjacent keyword hits + title bonus + freshness
        |
        v
  render()  →  email()  →  remember()  (seen.json so tomorrow only shows NEW)
```

A typical digest (real run):

```
# Job Radar — 2026-06-23
_14 new Taiwan ML / LLM / GPU openings via Greenhouse, Workday._

## 🟢 Strong fit (4)
### 1. Machine Learning Scientist (LLM & Agents) — Appier · Taipei
### 3. GPU Firmware Engineer — NVIDIA · Taiwan, Taipei
## 🔵 Adjacent (10)
...
```

## Setup (GitHub Actions)

Fork/clone, then add repo **Settings → Secrets and variables → Actions**:

| Secret | What |
|---|---|
| `GMAIL_USER` | your Gmail address (the sender) |
| `GMAIL_APP_PASSWORD` | a Gmail **App Password** (needs 2FA) — not your login password |
| `EMAIL_TO` | where to send the digest (defaults to `GMAIL_USER` if unset) |

The cron (`.github/workflows/radar.yml`) fires several windows a day; a daily sentinel makes every
fire after the first a no-op, so you get **one digest/day**. The browsable archive lands in
`digests/`, the de-dup memory in `state/seen.json` — both committed back by the job.

### Run locally

```bash
cp config.example.env config.env && $EDITOR config.env   # SMTP creds (optional)
./run.sh                                                 # prints the digest if SMTP unset
python -m unittest discover -s tests -t .                # tests
```

## Add an employer

Edit the registry at the top of [`job_radar/sources.py`](job_radar/sources.py):

```python
WORKDAY    += [{"company": "Foo", "host": "foo.wd1.myworkdayjobs.com", "tenant": "foo", "site": "External"}]
GREENHOUSE += [{"company": "Bar", "board": "bar"}]        # boards-api.greenhouse.io/v1/boards/<board>/jobs
LEVER      += [{"company": "Baz", "handle": "baz"}]        # api.lever.co/v0/postings/<handle>
```

A wrong Workday `site` just yields 0 for that employer (the source self-isolates) — it can't break
the run. Tune keywords/location/terms via env (see `config.example.env` and `job_radar/config.py`).

## Honest limits

- **Workday "N Locations" rows are dropped.** The search payload doesn't name the city for
  multi-location reqs, so they can't be confirmed Taiwan without a per-job detail fetch (the upgrade
  path). A handful of Taiwan multi-location roles may be missed.
- **Coverage = Workday + Greenhouse + Lever only.** NVIDIA, Micron, Cadence, Appier, Gogolook are in;
  AMD/Qualcomm/MediaTek/LINE/Foxconn/TSMC run on Phenom/Eightfold/custom portals and need their own
  adapters. PRs welcome.
- **No relevance LLM.** Filtering is keyword + location regex (fast, free, deterministic) — it favors
  recall, so the "Adjacent" tier carries some noise by design; the "Strong" tier is the clean one.

## License

MIT.
