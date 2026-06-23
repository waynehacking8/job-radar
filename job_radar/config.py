"""Configuration: state paths, the keyword/location patterns that define "a job
worth surfacing", scoring weights, and env helpers. All tunables live here."""
import os
import re
from pathlib import Path

UA = "job-radar/1.0 (+https://github.com/waynehacking8/job-radar)"

STATE_DIR = Path(os.environ.get("JOB_RADAR_HOME", Path.home() / ".job-radar"))
SEEN_PATH = STATE_DIR / "seen.json"
# Daily-run sentinel: holds the date of the last completed run so the multi-window
# fallback cron can fire many times a day (drop-resistant) while only the first
# fire of the day actually fetches + emails; later fires no-op.
LAST_RUN_PATH = STATE_DIR / "last-run"

SEEN_TTL_DAYS = int(os.environ.get("SEEN_TTL_DAYS", "30"))
MAX_ITEMS = int(os.environ.get("JOB_RADAR_MAX_ITEMS", "60"))
HTTP_TIMEOUT = int(os.environ.get("JOB_RADAR_HTTP_TIMEOUT", "25"))


def split_env(name, default):
    """Comma- (or |-) separated env list, trimmed and empty-filtered."""
    raw = os.environ.get(name, default)
    sep = "|" if "|" in raw else ","
    return [x.strip() for x in raw.split(sep) if x.strip()]


# Server-side narrowing: the searchText terms we POST to Workday so it returns
# ML-ish postings instead of a company's entire board. (Greenhouse/Lever return
# the whole board and we filter client-side.)
SEARCH_TERMS = split_env(
    "JOB_RADAR_SEARCH_TERMS",
    "machine learning,deep learning,LLM,GPU,inference,CUDA,PyTorch,MLOps",
)

# Location gate — Taiwan only (the user's stated scope). A posting must match this
# to be kept. Workday "N Locations" rows that don't name a city are dropped (see
# the note in sources.src_workday).
LOCATION_RE = re.compile(
    os.environ.get("JOB_RADAR_LOCATION_RE",
                   r"taiwan|taipei|hsinchu|taichung|tainan|新竹|台北|臺北|台中|台南|台灣|臺灣"),
    re.I,
)

# Relevance — a job is kept only if its title+snippet hits one of these. Split into
# STRONG (on-the-nose for an LLM-inference / GPU candidate) and MEDIUM (adjacent),
# which also drives ranking. Word-boundaried where a bare token would over-match.
STRONG_RE = re.compile(
    r"\bLLM\b|large language model|\bGPU\b|CUDA|tensor[\s-]?core|kernel|TensorRT|vLLM|"
    r"\bNCCL\b|inference|serving|quantization|model optimization|deep learning|"
    r"機器學習|深度學習|推論|大型語言模型",
    re.I,
)
MEDIUM_RE = re.compile(
    r"machine learning|\bML\b|\bAI\b|\bMLOps\b|PyTorch|TensorFlow|演算法|algorithm|"
    r"computer vision|\bNLP\b|人工智慧|model",
    re.I,
)
# Hard excludes — drop even on a keyword hit. Sales/HR/finance/pure-fab roles that
# trip "AI"/"model"/"algorithm" but are not engineering fits.
EXCLUDE_RE = re.compile(
    r"\bsales\b|account manager|recruit|talent acquisition|\bHR\b|marketing|"
    r"business development|financial analyst|supply chain|legal|\bintern\b|technician",
    re.I,
)

# Ranking weights.
W_STRONG = 10.0          # per strong keyword hit
W_MEDIUM = 3.0           # per medium keyword hit
W_TITLE_BONUS = 8.0      # the hit is in the TITLE, not just the description
W_FRESH = 5.0            # posted within FRESH_DAYS
FRESH_DAYS = 14
