"""Relevance: decide which fetched jobs to surface, and rank them. A job is kept
only if it is (a) in Taiwan, (b) not an excluded function (sales/HR/intern...), and
(c) hits a STRONG or MEDIUM keyword. The same keyword hits drive the score."""
import re
from datetime import datetime, timezone

from . import config


def _hits(text):
    strong = {m.group(0).upper() for m in config.STRONG_RE.finditer(text)}
    medium = {m.group(0).upper() for m in config.MEDIUM_RE.finditer(text)}
    return strong, medium


def fresh_days(posted):
    """Age in days if the posted field is parseable (ISO date, or Workday's
    'Posted N Days Ago' / 'Today' / 'Yesterday' text), else None."""
    posted = (posted or "").strip()
    if not posted:
        return None
    try:
        d = datetime.fromisoformat(posted.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return max(0, (datetime.now(timezone.utc) - d).days)
    except ValueError:
        pass
    low = posted.lower()
    if "today" in low or "just posted" in low:
        return 0
    if "yesterday" in low:
        return 1
    m = re.search(r"(\d+)\+?\s*day", low)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\+?\s*month", low)
    if m:
        return int(m.group(1)) * 30
    return None


def evaluate(job):
    """Set job.tags / job.fit / job.score in place; return True to keep it.

    ponytail: location is gated on the ATS-provided text only. Workday rows that
    read 'N Locations' (no city) can't be confirmed Taiwan from the search payload
    and are dropped — a per-job detail fetch is the upgrade if those matter.
    """
    if config.EXCLUDE_RE.search(job.title):       # title only — snippet is too broad
        return False
    if not config.LOCATION_RE.search(job.location):
        return False

    strong, medium = _hits(f"{job.title}\n{job.snippet}")
    if not (strong or medium):
        return False

    title_strong, title_medium = _hits(job.title)
    score = len(strong) * config.W_STRONG + len(medium) * config.W_MEDIUM
    if title_strong or title_medium:
        score += config.W_TITLE_BONUS
    age = fresh_days(job.posted)
    if age is not None and age <= config.FRESH_DAYS:
        score += config.W_FRESH

    job.tags = sorted(strong) + sorted(medium - strong)
    job.fit = "strong" if strong else "medium"
    job.score = score
    return True
