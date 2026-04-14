import os
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import datetime, timezone

URL = "https://www.tu-sport.de/sportprogramm/kurse/?tx_dwzeh_courses%5Baction%5D=show&tx_dwzeh_courses%5BsportsDescription%5D=768&cHash=302c5e58dded9777b08d1305c1398488"

TARGET_DAYS = {
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
}

# Zeitbereich statt exakter Stringvergleich → robuster gegen Änderungen
TARGET_START_HOUR = 17
TARGET_END_HOUR = 21  # exklusiv (21 bedeutet bis 20:59 Startzeit)


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
    if timetable is None:
        # Debug-Snapshot schreiben
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(html)
        raise ValueError("timetable not found → HTML structure changed or blocked")

    rows = timetable.select("div.table-row")

    current_day = None
    matches = []

    for row in rows:
        # Wochentag erkennen
        head = row.select_one("div.table-head")
        if head:
            current_day = head.get_text(strip=True)
            continue

        if current_day not in TARGET_DAYS:
            continue

        # Slots extrahieren
        slots = row.select("div.date.bookable")

        for slot in slots:
            time_el = slot.select_one("strong.time")
            if not time_el:
                continue

            time_text = time_el.get_text(strip=True)

            # Zeitbereich extrahieren (Startstunde)
            try:
                start_hour = int(time_text.split(":")[0])
            except Exception:
                continue  # falls Format unerwartet ist

            if TARGET_START_HOUR <= start_hour < TARGET_END_HOUR:
                matches.append({
                    "day": current_day,
                    "time": time_text
                })

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
    main()