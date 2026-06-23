"""job-radar — a daily email digest of NEW Taiwan ML / LLM / GPU job openings,
fetched from the ATS APIs your target employers actually run on (Workday, Greenhouse,
Lever), not from LinkedIn scraping.

Layout (mirrors the pipeline, top-down):
  cli.py        orchestration: collect -> select -> render -> email -> remember
  sources.py    ATS fetchers (Workday CXS / Greenhouse / Lever) + the company registry
  models.py     the typed Job record
  filter.py     relevance (keyword) + location + ranking
  render.py     the Markdown digest + email-safe HTML
  email_out.py  SMTP delivery (Gmail app password), retries, heartbeat-vs-outage
  state.py      de-dup memory (seen jobs) + the daily-run sentinel
  config.py     constants, keyword/location patterns, env helpers
  clients.py    tiny urllib JSON GET/POST (stdlib only — no third-party deps)
"""
