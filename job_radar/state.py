"""De-dup memory: which jobs we've already emailed, with timestamps. Tolerates a
corrupt/hand-edited file and writes atomically so a crash can't leave it broken.
(Same design as gh-radar's state — proven, generic.)"""
import json
import time

from . import config


def load_seen():
    try:
        data = json.loads(config.SEEN_PATH.read_text())
        if not isinstance(data, dict):
            return {}
        return {k: v for k, v in data.items() if isinstance(v, (int, float))}
    except Exception:  # noqa: BLE001
        return {}


def save_seen(seen):
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - config.SEEN_TTL_DAYS * 86400
    seen = {k: v for k, v in seen.items() if isinstance(v, (int, float)) and v > cutoff}
    tmp = config.SEEN_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(seen))
    tmp.replace(config.SEEN_PATH)        # atomic — never leaves a half-written file


def already_ran_today(when):
    """True if a run already completed today. Lets the multi-window cron fire
    repeatedly while only the first fire of the day does the work."""
    try:
        return config.LAST_RUN_PATH.read_text().strip() == when
    except Exception:  # noqa: BLE001
        return False


def mark_ran_today(when):
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = config.LAST_RUN_PATH.with_suffix(".tmp")
    tmp.write_text(when)
    tmp.replace(config.LAST_RUN_PATH)    # atomic
