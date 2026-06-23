"""Email delivery via SMTP (Gmail). Prints the digest instead if SMTP is unset.
Retries transient failures; raises (red job) on a real, configured-but-failed send
so a missed digest never looks like a silent success. (Mirrors gh-radar.)"""
import os
import smtplib
import sys
import time
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

from .render import md_to_html


def send_email(subject, md):
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    pw = os.environ.get("SMTP_PASS")
    to = os.environ.get("EMAIL_TO") or user      # unset -> fall back to sender
    if not (host and user and pw and to):
        print("  i SMTP not configured — printing digest instead.\n", file=sys.stderr)
        # Write UTF-8 bytes directly: a non-UTF-8 console (e.g. Windows cp950)
        # would otherwise crash print() on an emoji in the digest.
        sys.stdout.buffer.write((md + "\n").encode("utf-8"))
        return False
    msg = MIMEText(md_to_html(md), "html", "utf-8")
    msg["Subject"] = str(Header(subject, "utf-8"))     # safe for em dash / Chinese
    msg["From"] = formataddr(("Job Radar", user))
    msg["To"] = to
    try:
        port = int(os.environ.get("SMTP_PORT", "587"))
    except ValueError:
        port = 587
    attempts = 4
    backoff = 5.0          # linear: 5s, 10s, 15s
    last_err = None
    for attempt in range(1, attempts + 1):
        try:
            with smtplib.SMTP(host, port, timeout=30) as s:
                s.ehlo()
                s.starttls()
                s.login(user, pw)
                s.sendmail(user, [to], msg.as_string())
            tag = f" (attempt {attempt})" if attempt > 1 else ""
            print(f"  ✓ emailed digest to {to}{tag}")
            return True
        except (smtplib.SMTPException, OSError) as e:    # transient: auth blip, TLS reset, timeout
            last_err = e
            print(f"  ! email attempt {attempt}/{attempts} failed: {e}", file=sys.stderr)
            if attempt < attempts:
                time.sleep(backoff * attempt)
    raise RuntimeError(f"email delivery failed after {attempts} attempts: {last_err}")
