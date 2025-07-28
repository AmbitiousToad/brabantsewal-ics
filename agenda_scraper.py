import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
import re
import hashlib
import os

BASE_URL = "https://www.vvvbrabantsewal.nl/agenda?page={}"
MAX_PAGES = 20
ICS_FILE = "calendar/index.ics"

def fetch_items():
    all_items = []
    for page in range(1, MAX_PAGES + 1):
        url = BASE_URL.format(page)
        print(f"Fetching: {url}")
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        titles = soup.find_all("h3")

        if not titles:
            break

        for h3 in titles:
            title = h3.text.strip()
            parent = h3.parent
            text_blob = parent.get_text(separator="\n", strip=True)
            lines = text_blob.splitlines()

            datum = next((l for l in lines if re.search(r"\d{1,2} \w+", l.lower())), None)
            locatie = next((l for l in lines if l.isupper() and len(l) < 40), None)

            # Detailpagina opzoeken
            a_tag = h3.find("a")
            relative_url = a_tag["href"] if a_tag and "href" in a_tag.attrs else None
            detail_url = f"https://www.vvvbrabantsewal.nl{relative_url}" if relative_url else None

            all_items.append({
                "title": title,
                "datum": datum,
                "locatie": locatie,
                "description": text_blob.strip(),
                "url": detail_url
            })
    return all_items

def parse_date(datum_str):
    if not datum_str:
        return None
    match = re.search(r"(\d{1,2}) (\w+)", datum_str)
    if not match:
        return None
    day, month = match.groups()
    month_map = {
        "januari": 1, "februari": 2, "maart": 3, "april": 4,
        "mei": 5, "juni": 6, "juli": 7, "augustus": 8,
        "september": 9, "oktober": 10, "november": 11, "december": 12
    }
    if month.lower() not in month_map:
        return None
    now = datetime.now()
    year = now.year
    if month_map[month.lower()] < now.month:
        year += 1
    return datetime(year, month_map[month.lower()], int(day))

def generate_uid(title, date):
    seed = f"{title}-{date.isoformat()}"
    uid_hash = hashlib.md5(seed.encode()).hexdigest()
    return f"{uid_hash}@brabantsewal.ics"

def generate_ics(events):
    cal = Calendar()
    now = datetime.utcnow()
    os.makedirs(os.path.dirname(ICS_FILE), exist_ok=True)

    for item in events:
        parsed_date = parse_date(item["datum"])
        if not parsed_date:
            continue

        e = Event()
        e.name = item["title"]
        e.begin = parsed_date.date()  # gehele dag event
        e.uid = generate_uid(item["title"], parsed_date)
        e.location = item["locatie"] or "Brabantse Wal"
        e.description = item["description"]

        if item.get("url"):
            e.url = item["url"]
            e.description += f"\n\nMeer info: {item['url']}"

        e.status = "confirmed"
        e.created = now
        e.sequence = 0

        cal.events.add(e)

    with open(ICS_FILE, "w", encoding="utf-8") as f:
        f.writelines(cal)

if __name__ == "__main__":
    events = fetch_items()
    generate_ics(events)
