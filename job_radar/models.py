"""The core data model. One typed Job replaces an untyped dict so a mistyped field
fails loudly and the available signals are self-documenting."""
from dataclasses import dataclass, field


@dataclass
class Job:
    # --- identity / dedup ---
    key: str                       # stable: "{source}:{company}:{job_id}"
    company: str
    title: str
    location: str
    url: str

    # --- provenance ---
    source: str = ""               # "workday" | "greenhouse" | "lever"
    posted: str = ""               # ISO date if the ATS gives one, else ""
    snippet: str = ""              # short text matched against keywords

    # --- derived ---
    tags: list = field(default_factory=list)   # matched keyword hits, e.g. ["LLM","CUDA"]
    fit: str = ""                  # "strong" | "medium"
    score: float = 0.0
