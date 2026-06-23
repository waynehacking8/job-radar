#!/usr/bin/env python3
"""Entry point — keeps `python radar.py` working (CI/cron unchanged). All logic
lives in the job_radar/ package; see job_radar/__init__.py for the layout."""
from job_radar.cli import main

if __name__ == "__main__":
    main()
