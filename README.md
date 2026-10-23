# Nintendo Museum ticket alert (private email)

Checks the Nintendo Museum calendar about once a minute (a run starts every 5 min and checks 5 times) from GitHub Actions and
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

## Phone call alert (optional)
If these secrets are set, it also calls your phone when tickets open
(and on a test run):
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` – from the Twilio Console home page
- `TWILIO_FROM` – your Twilio trial number, e.g. `+15551234567`
- `CALL_TO` – your verified phone number, e.g. `+14075551234`

Save the Twilio number as a contact so *Silence Unknown Callers* doesn't block it.

## Turning it off
Actions tab → the workflow → ⋯ → *Disable workflow*. Do this after your trip.

## Notes
- GitHub's schedule is best-effort; runs can be 5–15 min late at busy times.
- If the test email says the site blocked the request, GitHub's servers are
  being refused by Nintendo; fall back to the original Chrome extension.
- The repo is public so Actions minutes are free and unlimited. Secrets
  (your Gmail address and app password) are never shown publicly.
