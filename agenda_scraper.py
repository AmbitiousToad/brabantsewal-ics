from icalendar import Calendar, Event
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
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
            a_tag = h3.find("a")
            relative_url = a_tag["href"] if a_tag and "href" in a_tag.attrs else None
            detail_url = f"https://www.vvvbrabantsewal.nl{relative_url}" if relative_url else None
            all_items.append({
                "title": title,
                "datum": datum,
                "locatie": locatie,
                "raw_text": text_blob.strip(),
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
    return date(year, month_map[month.lower()], int(day))

def generate_uid(title, event_date):
    seed = f"{title}-{event_date.isoformat()}"
    uid_hash = hashlib.md5(seed.encode()).hexdigest()
    return f"{uid_hash}@brabantsewal.ics"

def build_description(item):
    desc = ""
    if item.get("url"):
        desc += f"Meer informatie: {item['url']}\n"
    if item.get("raw_text"):
        desc += item["raw_text"]
    return desc.strip()

def generate_ics(events):
    cal = Calendar()
    cal.add("prodid", "-//Brabantse Wal Agenda//NL")
    cal.add("version", "2.0")
    os.makedirs(os.path.dirname(ICS_FILE), exist_ok=True)

    for item in events:
        event_date = parse_date(item["datum"])
        if not event_date:
            continue
        event = Event()
        event.add("summary", item["title"])
        event.add("uid", generate_uid(item["title"], event_date))
        event.add("location", item["locatie"] or "Brabantse Wal")
        event.add("dtstart", event_date)  # ✅ dit zorgt voor VALUE=DATE
        event.add("status", "CONFIRMED")
        event.add("description", build_description(item))
        if item.get("url"):
            event.add("url", item["url"])
        cal.add_component(event)

    with open(ICS_FILE, "wb") as f:
        f.write(cal.to_ical())

if __name__ == "__main__":
    events = fetch_items()
    generate_ics(events)
