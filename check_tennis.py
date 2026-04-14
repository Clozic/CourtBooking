import os
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import datetime, timezone

now = datetime.now(timezone.utc)

URL = "https://www.tu-sport.de/sportprogramm/kurse/?tx_dwzeh_courses%5Baction%5D=show&tx_dwzeh_courses%5BsportsDescription%5D=768&cHash=302c5e58dded9777b08d1305c1398488"

TARGET_TIMES = {
    "17:00-18:00",
    "18:00-19:00",
    "19:00-20:00",
    "20:00-21:00",
}

TARGET_DAYS = {
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
}

def fetch_slots():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "de-DE,de;q=0.9",
    }

    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    timetable = soup.select_one("div.timetable.table")

    if timetable is None:
        raise ValueError("timetable not found in HTML")

    rows = timetable.select("div.table-row")

    current_day = None
    matches = []

    for row in rows:
        # 1. Detect weekday header
        head = row.select_one("div.table-head")
        if head:
            current_day = head.get_text(strip=True)
            continue

        # 2. Process slots only if weekday matches
        if current_day not in TARGET_DAYS:
            continue

        # 3. Extract all slots for that weekday
        slots = row.select("div.date.bookable strong.time")

        for slot in slots:
            time_text = slot.get_text(strip=True)

            if time_text in TARGET_TIMES:
                matches.append({
                    "day": current_day,
                    "time": time_text
                })

    return matches

def send_email(available_slots):
    subject = "🎾 Tennis court available!"
    body = "The following slots are available:\n\n" + "\n".join(available_slots)
    body += f"\n\nBook here: {URL}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["NOTIFY_EMAIL"]

    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.sendmail(os.environ["SMTP_USER"], os.environ["NOTIFY_EMAIL"], msg.as_string())

    print(f"Email sent for {len(available_slots)} slot(s).")

def main():
    print(datetime.now(timezone.utc).isoformat())
    available = fetch_slots()

    if available:
        lines = [f"{s['day']} {s['time']}" for s in available]
        send_email(lines)

if __name__ == "__main__":
    main()