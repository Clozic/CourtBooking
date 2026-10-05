# Project Map

## Purpose
Polls the TU Berlin Hochschulsport tennis course page and emails when a bookable slot matches target days/hours. (Inferred from code.)

## Requirements
Not yet stated by learner.

## Components
- `check_tennis.py`: fetch_html (requests), parse_slots (BeautifulSoup), send_email (SMTP/STARTTLS), main.
- `test_check_tennis.py`: unittest for parse_slots with sample HTML.
- `html.txt`: saved copy of the target page (885 lines).
- `.github/workflows/check_tennis.yml`: runs script on GitHub Actions (manual / repository_dispatch).
- `requirements.txt`: requests, beautifulsoup4.

## Main Flow
GitHub Actions trigger -> check_tennis.py -> GET tu-sport.de page -> parse div.timetable for `div.date.bookable` in TARGET_DAYS and hour range -> if matches: SMTP email.
Who sends repository_dispatch (scheduler)? unknown.

## Data and Trust Boundaries
No storage. Config via env/secrets/vars: NOTIFY_EMAIL, SMTP_*, TARGET_DAYS, TARGET_START_HOUR, TARGET_END_HOUR. External: tu-sport.de (HTML, untrusted), SMTP server.

## Build and Deployment
`pip install -r requirements.txt`; `python check_tennis.py`; `python -m unittest`. Deployed via GitHub Actions workflow (Python 3.11).

## Unknowns
- Learner's goal for this repo.
- Trigger source for repository_dispatch (cron removed in last commit).
- No dedupe: same slot may be emailed on every run.
- Workflow sets TARGET_DATE/TARGET_TIMES, unused in script.
