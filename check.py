"""Nintendo Museum ticket checker -> private email alert.

Same logic as BruceJian43/nintendo-museum-ticket-checker (Chrome extension),
ported to Python so it can run on a schedule in GitHub Actions and email you.

Config comes from environment variables (set as GitHub Actions secrets/vars):
  GMAIL_ADDRESS       Gmail account that sends the alert
  GMAIL_APP_PASSWORD  16-character Google app password (not your normal password)
  ALERT_TO            Where to send alerts (defaults to GMAIL_ADDRESS)
  DATE_FROM, DATE_TO  Inclusive date window, YYYY-MM-DD
  TEST_EMAIL          "true" sends an email with the current status no matter what
  STATE_FILE          Where previously-alerted dates are remembered
"""

import json
import os
import smtplib
import sys
import time
from datetime import date, datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import unquote

import requests

BASE_URL = "https://museum-tickets.nintendo.com/en"
CALENDAR_URL = f"{BASE_URL}/calendar"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

DATE_FROM = date.fromisoformat(os.environ.get("DATE_FROM") or "2026-11-01")
DATE_TO = date.fromisoformat(os.environ.get("DATE_TO") or "2026-11-01")
STATE_FILE = Path(os.environ.get("STATE_FILE") or "state/seen.json")
TEST_EMAIL = (os.environ.get("TEST_EMAIL") or "").lower() == "true"


def months_in_window(start: date, end: date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def fetch_available_dates() -> list[str]:
    s = requests.Session()
    s.headers["User-Agent"] = UA

    # Step 1: open the calendar page to get session + XSRF cookies
    r = s.get(CALENDAR_URL, timeout=30)
    r.raise_for_status()
    token = s.cookies.get("XSRF-TOKEN")
    if not token:
        raise RuntimeError("No XSRF-TOKEN cookie returned (site may be blocking this runner).")

    headers = {
        "accept": "application/json, text/plain, */*",
        "x-requested-with": "XMLHttpRequest",
        "x-xsrf-token": unquote(token),
        "referer": CALENDAR_URL,
    }

    # Step 2: query each month that overlaps the trip window
    found = []
    for year, month in months_in_window(DATE_FROM, DATE_TO):
        url = f"{BASE_URL}/api/calendar?target_year={year}&target_month={month}"
        resp = s.get(url, headers=headers, timeout=30)
        if not resp.ok:
            print(f"WARN: {year}-{month:02d} returned HTTP {resp.status_code}")
            continue
        calendar = (resp.json().get("data") or {}).get("calendar") or {}
        for day, d in calendar.items():
            try:
                day_date = date.fromisoformat(day)
            except ValueError:
                continue
            if not (DATE_FROM <= day_date <= DATE_TO):
                continue
            # Same "bookable" condition the extension uses
            if d.get("apply_type") == 3 and d.get("sale_status") == 1 and d.get("open_status") == 1:
                found.append(day)
        print(f"{year}-{month:02d}: checked {len(calendar)} days")
    return sorted(set(found))


def send_email(subject: str, body: str):
    sender = os.environ["GMAIL_ADDRESS"]
    to = os.environ.get("ALERT_TO") or sender
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(sender, os.environ["GMAIL_APP_PASSWORD"].replace(" ", ""))
        smtp.send_message(msg)
    print(f"Email sent: {subject}")


def pretty(d: str) -> str:
    return date.fromisoformat(d).strftime("%a %b %-d")


def check_once(test_email: bool) -> bool:
    """One check. Returns True if the calendar was read successfully."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] Checking {DATE_FROM} to {DATE_TO}")

    seen = set()
    if STATE_FILE.exists():
        seen = set(json.loads(STATE_FILE.read_text()))

    try:
        available = fetch_available_dates()
    except Exception as e:
        print(f"ERROR: {e}")
        if test_email:
            send_email(
                "⚠️ Nintendo Museum checker: test run failed",
                f"The checker couldn't read the ticket calendar:\n\n{e}\n\nChecked at {now}.",
            )
        return False

    print("Available:", available or "none")
    new = [d for d in available if d not in seen]
    lines = "\n".join(f"  • {pretty(d)}  ({d})" for d in available)

    if new:
        send_email(
            f"🎟️ Nintendo Museum tickets open: {', '.join(pretty(d) for d in new)}",
            "Tickets just showed up for your trip dates:\n\n"
            f"{lines}\n\nBook fast: {CALENDAR_URL}\n\nChecked at {now}.",
        )
    elif test_email:
        status = f"Currently available:\n\n{lines}" if available else "Nothing available right now."
        send_email(
            "✅ Nintendo Museum checker is working",
            f"Test run OK. Watching {pretty(DATE_FROM.isoformat())} – {pretty(DATE_TO.isoformat())}.\n\n"
            f"{status}\n\nYou'll get an email only when new dates open up.\n\nChecked at {now}.",
        )

    # Remember only dates that are currently open, so a date that sells out
    # and reopens later triggers a fresh alert.
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(available))
    return True


def main():
    # A test run checks once; scheduled runs check CHECKS times, INTERVAL seconds apart
    # (GitHub's schedule can't go below every 5 minutes, so each run covers 5 minutes).
    checks = 1 if TEST_EMAIL else int(os.environ.get("CHECKS") or 5)
    interval = int(os.environ.get("INTERVAL") or 60)
    ok = 0
    for i in range(checks):
        if i:
            time.sleep(interval)
        ok += check_once(TEST_EMAIL)
    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
