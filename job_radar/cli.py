"""Pipeline: collect from every source -> filter/rank -> render -> email ->
remember. Each stage is a small function so the flow reads top-down. (Same shape
as gh-radar's cli.)"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from . import config
from .email_out import send_email
from .filter import evaluate
from .render import render_md
from .sources import SOURCES
from .state import already_ran_today, load_seen, mark_ran_today, save_seen


def collect():
    """Run every source (isolated) and gather jobs, deduped by key. Returns
    (jobs, errors) — errors is how many sources raised, so the caller can tell a
    genuinely quiet day from a total outage."""
    by_key = {}
    errors = 0
    for label, fn in SOURCES:
        try:
            jobs = fn() or []
        except Exception as e:  # noqa: BLE001 — one bad source must not sink the rest
            print(f"  ! source {label} crashed: {e}", file=sys.stderr)
            errors += 1
            continue
        for j in jobs:
            by_key.setdefault(j.key, j)        # first writer wins; keys are stable
    return list(by_key.values()), errors


def select(jobs, seen):
    """Drop already-seen, keep only Taiwan + on-topic (filter.evaluate), rank."""
    cutoff = time.time() - config.SEEN_TTL_DAYS * 86400
    out = [j for j in jobs if seen.get(j.key, 0) <= cutoff and evaluate(j)]
    out.sort(key=lambda j: j.score, reverse=True)
    return out[: config.MAX_ITEMS]


def main():
    when = datetime.now().strftime("%Y-%m-%d")
    if already_ran_today(when):
        print(f"job-radar: already ran today ({when}) — skipping this window.", file=sys.stderr)
        return

    print("job-radar: collecting…", file=sys.stderr)
    jobs, errors = collect()
    seen = load_seen()
    top = select(jobs, seen)

    if not top:
        if not jobs:
            # Nothing from ANY source — an outage, not a quiet day. Fail loudly so
            # the Actions job goes red, rather than sending a false 'nothing new'.
            raise RuntimeError(
                f"no jobs collected from any source ({errors}/{len(SOURCES)} crashed) "
                f"— aborting instead of emailing a false 'nothing new'")
        # Genuinely nothing new (all seen / off-topic / not Taiwan). Heartbeat so a
        # quiet day reads as 'ran, nothing new', not a broken run.
        print("  nothing new today.", file=sys.stderr)
        send_email(f"Job Radar — {when}（今天沒有新職缺）",
                   f"# Job Radar — {when}\n\n"
                   "_今天掃過所有來源，沒有發現新的台灣對口職缺——可能都看過了。系統運作正常，明天見。_\n")
        mark_ran_today(when)
        return

    md = render_md(top, when)

    out_dir = os.environ.get("JOB_RADAR_DIGEST_DIR")
    if out_dir:
        path = Path(out_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / f"job-radar-{when}.md").write_text(md, encoding="utf-8")
        print(f"  ✓ wrote {path / f'job-radar-{when}.md'}", file=sys.stderr)

    send_email(f"Job Radar — {when} ({len(top)} jobs)", md)

    now = time.time()
    for j in top:
        seen[j.key] = now
    save_seen(seen)
    mark_ran_today(when)
