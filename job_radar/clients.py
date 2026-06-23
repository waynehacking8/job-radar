"""Tiny stdlib HTTP — JSON GET/POST over urllib, so the whole tool stays
dependency-free (matches gh-radar's no-third-party-deps stance). Each call
returns parsed JSON or raises; sources catch and self-isolate."""
import json
import time
import urllib.request
from urllib.error import HTTPError, URLError

from . import config


def _request(url, *, data=None, headers=None, attempts=3):
    """One JSON request with linear backoff on transient errors. `data` (bytes)
    makes it a POST. Returns parsed JSON."""
    hdrs = {"User-Agent": config.UA, "Accept": "application/json"}
    if data is not None:
        hdrs["Content-Type"] = "application/json"
    hdrs.update(headers or {})
    last = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs)
            with urllib.request.urlopen(req, timeout=config.HTTP_TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except HTTPError as e:
            # 4xx (bad endpoint/blocked) won't fix on retry — fail fast.
            if 400 <= e.code < 500:
                raise
            last = e
        except (URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
            last = e
        if attempt < attempts:
            time.sleep(1.5 * attempt)
    raise last


def get_json(url, headers=None):
    return _request(url, headers=headers)


def post_json(url, body, headers=None):
    return _request(url, data=json.dumps(body).encode("utf-8"), headers=headers)
