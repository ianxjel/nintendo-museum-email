# Nintendo Museum ticket alert (private email)

Checks the Nintendo Museum calendar every ~10 minutes from GitHub Actions and
emails you when bookable tickets appear in your date window. Ported from
[BruceJian43/nintendo-museum-ticket-checker](https://github.com/BruceJian43/nintendo-museum-ticket-checker)
(same API, same "bookable" rule). Default window: **Nov 1, 2026 only**.

## Setup (~5 min)

1. **Create a private repo** on GitHub (e.g. `museum-alert`) and upload
   `check.py`, `README.md`, and `.github/workflows/check.yml`.
   (Hidden folder: if the web uploader skips it, use *Add file → Create new file*
   and type the path `.github/workflows/check.yml`, then paste the contents.)

2. **Make a Gmail app password**: myaccount.google.com/apppasswords
   (needs 2-Step Verification on). Name it anything; copy the 16 characters.

3. **Add secrets**: repo → Settings → Secrets and variables → Actions →
   *New repository secret*:
   - `GMAIL_ADDRESS` – the Gmail that sends
   - `GMAIL_APP_PASSWORD` – the app password
   - `ALERT_TO` – (optional) where alerts go; defaults to `GMAIL_ADDRESS`

4. *(Optional)* Narrow the dates: same page → **Variables** tab →
   `DATE_FROM` / `DATE_TO` as `YYYY-MM-DD`.

5. **Test it**: Actions tab → *Nintendo Museum ticket alert* → *Run workflow*.
   You should get a "✅ checker is working" email (or "⚠️ test run failed" with the reason).

After that it runs on its own. You get an email only when a **new** date opens;
if a date sells out and reopens, you're alerted again.

## Turning it off
Actions tab → the workflow → ⋯ → *Disable workflow*. Do this after your trip.

## Notes
- GitHub's schedule is best-effort; runs can be 5–15 min late at busy times.
- If the test email says the site blocked the request, GitHub's servers are
  being refused by Nintendo; fall back to the original Chrome extension.
- Private repos get 2,000 free Actions minutes/month and each run bills as
  1 minute, so every-10-min uses ~144 min/day (~1,900 through Nov 4). If you
  use Actions for other things, change the cron to `*/15` — and disable this
  after the trip either way.
