import os
import json
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import datetime, timezone

URL = "https://www.tu-sport.de/sportprogramm/kurse/?tx_dwzeh_courses%5Baction%5D=show&tx_dwzeh_courses%5BsportsDescription%5D=768&cHash=302c5e58dded9777b08d1305c1398488"
SEEN_FILE = "/tmp/seen_slots.json"  # persists within a single run only

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

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_slots():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    timetable = soup.select_one("div.timetable")
    rows = timetable.select("div.table-row")

    current_day = None
    matches = []

    for row in rows:
        head = row.select_one("div.table-head")
        if head:
            current_day = head.get_text(strip=True)
            continue

        if current_day not in TARGET_DAYS:
            continue

        for slot in row.select("div.date.bookable"):
            a = slot.find("a")
            if not a:
                continue

            time_text = slot.select_one("strong.time")
            if not time_text:
                continue
            time_text = time_text.get_text(strip=True)

            if time_text not in TARGET_TIMES:
                continue

            field = slot.select_one("span.detail")
            field = field.get_text(strip=True) if field else "?"

            href = a.get("href", "")
            booking_url = href if href.startswith("http") else f"https://www.zeh.tu-berlin.de{href}"

            matches.append({
                "day": current_day,
                "time": time_text,
                "field": field,
                "url": booking_url,
                "key": f"{current_day}|{time_text}|{field}",
            })

    return matches

def send_email(slots):
    lines = [f"{s['day']}  {s['time']}  {s['field']}\n  👉 {s['url']}" for s in slots]
    body = "The following tennis court slots are available:\n\n" + "\n\n".join(lines)
    body += f"\n\nFull timetable: {URL}"

    msg = MIMEText(body)
    msg["Subject"] = f"🎾 Tennis slot available! ({len(slots)} new)"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["NOTIFY_EMAIL"]

    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.sendmail(os.environ["SMTP_USER"], os.environ["NOTIFY_EMAIL"], msg.as_string())

    print(f"Email sent for {len(slots)} slot(s).")

def main():
    print(datetime.now(timezone.utc).isoformat())

    slots = fetch_slots()
    seen = load_seen()

    new_slots = [s for s in slots if s["key"] not in seen]

    if new_slots:
        send_email(new_slots)
        seen.update(s["key"] for s in new_slots)
        save_seen(seen)
    else:
        print(f"No new slots. ({len(slots)} known slot(s) already seen.)")

if __name__ == "__main__":
    main()