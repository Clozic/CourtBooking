# Learning Progress

## Git sync and staging
- Introduced (Claude explained): remote/origin, pull/push, staging vs unstaged, comparing hashes to check pushes.
- Demonstrated: learner pushed .vibe-wise and fixed wrong-path `git add` after explanation.
- Needs reinforcement: relative paths in git add.

## Trigger / scheduling
- Introduced: GitHub Actions workflow, triggers, stateless runner.
- Demonstrated understanding: learner described cron-job.org -> GitHub API dispatch, release window one week ahead, widened window for deviations, rate-limit observation (60s denied, 120s ok).
- Needs reinforcement: token expiry, shared datacenter IP vs frequency as block cause.

## Dedupe / persistent storage (drawback 3)
- Learner chose to target this; wants DB-like storage, also to log first-seen times to study release-time deviations (drawback 1). Learner-proposed: table with timeslot, booking time, opening time.
- Introduced (Claude): identity key, upsert, unique constraint, runner is stateless so storage is external. Claude noted app cannot observe bookings, only first seen/last seen/disappeared.
- Learner reasoning so far: slot has no date on timetable; Kursid in link; same weekday/time in a later week should count as a new session.
- Verified in html.txt: each card links to anmeldung.fcgi?Kursid=N and has span.dates (season range) and span.detail (Feld). Detail page lists individual dates; open date has radio button, others "z.Z. keine Buchung".

## Session identity design (confirmed, not implemented)
- Learner decided: session identified by calendar date and time; unlock time is not a key (non-unique); wants date derived from the existing HTML, no second request (avoids block risk/runtime).
- Learner objections raised: statelessness prevents knowing a slot is new; simultaneous unlocks.
- Claude explained: key vs attribute; date derivation separate from newness; first_seen is an upper bound on unlock time.
- Proposed by Claude, confirmed by learner (Confirm and continue): key = Kursid + session_date (court added by Claude since Feld 1/2/3 share date and time); date = first date with that weekday whose start >= now in Europe/Berlin (assumption unverified: started slots not listed); columns Kursid, session_date, feld, day, time, first_seen_at, last_seen_at, notified_at; flow: insert+email if new, else update last_seen_at only.
- Open: storage location (runner is wiped each run), old-row cleanup, recording own bookings (not decided).
- Needs reinforcement: key vs attribute, UTC vs Berlin time.

## Storage choice
- Learner requirements: read/write on every detection; human-accessible for maintenance; no login needed now, but personal data or other authenticated APIs possible later.
- Learner decided: hosted database (reason: avoid a git commit per cron run). Accepted downside: must evaluate free-tier limits.
- Learner decided: send email first, then write notified_at; duplicate email acceptable (also accepts race-condition duplicates).
- Learner's first overlap idea (last_seen_at in the future) was incorrect; Claude explained race condition, atomic insert, unique constraint, Actions `concurrency:`.
- last_seen_at kept for analysis (disappearance), not email logic. Claude explained: store observations not estimates; runs only in cron window so disappearance only visible inside window; booking-to-disappearance lag unverified.
- booked_by_me: manual column filled by learner, scope (now/later) undecided. Auto-detect would need site login (separate, later).

## Database type and provider (confirmed, not implemented)
- Learner decided: relational SQL (fits fixed columns; SQL widely used, worth learning).
- Learner decided: Neon free (reason: auto-wake on query vs Supabase 7-day pause needing manual resume). Confirmed via Confirm and continue.
- Claude explained CU-hours (size x hours awake; compute stays awake whole cron window at 2-min runs). Sources say 100 CU-h is monthly; behavior on exhaustion unverified.
- Open: autoscaling max (proposed by Claude: cap low), learner to verify limits on Neon pricing page.

## Table and DB flow (confirmed, not implemented)
- Learner wrote database.sql: court_slots(course_id INT, session_date DATE, field TEXT, timeslot TEXT -> to be split into start_time/end_time TIME, first_seen_at/last_seen_at TIMESTAMPTZ DEFAULT now(), notified_at TIMESTAMPTZ, booked_by_me BOOLEAN DEFAULT false, PK(course_id, session_date)). Ran in Neon successfully.
- Learner fixed after review: missing comma, PK placeholders, real->text, booked_by_me default, consistent case. Learner idea: DEFAULT now().
- Learner decided: psycopg (Data API later, e.g. setting booked_by_me via Postman). DATABASE_URL as one secret.
- Learner initially placed DB write only after email; Claude showed that re-emails every run. Learner revised.
- Learner decided (confirmed): parse -> one batched upsert -> one email listing rows with empty notified_at -> one batched UPDATE notified_at. Reasoned call count (~4 slots/run expected) and chose batching.
- Claude additions confirmed: update last_seen_at on all existing rows; one connection, opened only if slots found; DATABASE_URL in workflow env, psycopg in requirements.txt.
- Claude explained: connection vs statement cost; INSERT ... ON CONFLICT DO UPDATE + RETURNING (names only).
- Needs reinforcement: which function does what (fetch vs parse).

## Pending decision
Learner writes the code (start_time/end_time columns, parse_slots extension incl. session_date in Europe/Berlin, upsert, email, notified_at update). Claude reviews. No code by Claude.
