import os
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import datetime, timezone

URL = "https://www.tu-sport.de/sportprogramm/kurse/?tx_dwzeh_courses%5Baction%5D=show&tx_dwzeh_courses%5BsportsDescription%5D=768&cHash=302c5e58dded9777b08d1305c1398488"
TARGET_DAYS = set(os.environ.get("TARGET_DAYS", "").split(","))
TARGET_START_HOUR = int(os.environ.get("TARGET_START_HOUR", 17))
TARGET_END_HOUR = int(os.environ.get("TARGET_END_HOUR", 20))


def fetch_html():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml",
        "Connection": "keep-alive",
    }

    response = requests.get(URL, headers=headers, timeout=20)
    response.raise_for_status()

    if len(response.text) < 1000:
        raise ValueError("HTML unexpectedly short → likely blocked or invalid response")

    return response.text


def parse_slots(html):
    soup = BeautifulSoup(html, "html.parser")
    timetable = soup.select_one("div.timetable")
    if not timetable:
        # Sometimes the site returns a "Loading" page or a Maintenance page
        return []

    rows = timetable.find_all("div", class_="table-row")
    current_day = None
    matches = []

    for row in rows:
        head = row.select_one("div.table-head")
        if head:
            # Clean up potential &nbsp; or hidden characters
            current_day = head.get_text(strip=True).replace('\xa0', ' ').strip()
            print(f"Parsed day: {repr(current_day)} | TARGET_DAYS: {repr(TARGET_DAYS)}", flush=True)
            continue

        if not current_day or current_day not in TARGET_DAYS:
            continue

        for slot in row.select("div.date.bookable"):
            time_el = slot.select_one("strong.time")
            if time_el:
                time_text = time_el.get_text(strip=True)
                try:
                    start_hour = int(time_text.split(":")[0])
                    # Adjusted to include the 21:00 slot if that's what you want
                    if TARGET_START_HOUR <= start_hour <= TARGET_END_HOUR:
                        matches.append({"day": current_day, "time": time_text})
                except (ValueError, IndexError):
                    continue
    return matches


def send_email(available_slots):
    subject = "🎾 Tennis court available"

    body_lines = [f"{s['day']} {s['time']}" for s in available_slots]
    body = "Available slots:\n\n" + "\n".join(body_lines)
    body += f"\n\nBook here:\n{URL}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["NOTIFY_EMAIL"]

    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.sendmail(
            os.environ["SMTP_USER"],
            os.environ["NOTIFY_EMAIL"],
            msg.as_string()
        )

    print(f"Email sent for {len(available_slots)} slot(s).")


def main():
    import sys
    print("Script started", flush=True)
    sys.stdout.flush()
    print(f"TARGET_DAYS: {repr(TARGET_DAYS)}", flush=True)
    print(f"TARGET_TIMES: {repr(TARGET_TIMES)}", flush=True)
    now = datetime.now(timezone.utc)
    print("Run at:", now.isoformat())

    html = fetch_html()
    print("HTML fetched, length:", len(html))

    slots = parse_slots(html)
    print("After parsing")

    print(f"Found {len(slots)} matching slot(s).")

    for s in slots:
        print(f"  {s['day']} {s['time']}")

    if slots:
        send_email(slots)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
