import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
import re

BASE_URL = "https://www.vvvbrabantsewal.nl/agenda?page={}"
MAX_PAGES = 20  # Stop bij pagina 20 om overbelasting te voorkomen
ICS_FILE = "index.ics"

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

            # Zoek datum en locatie op heuristiek
            datum = next((l for l in lines if re.search(r"\d{1,2} \w+", l.lower())), None)
            locatie = next((l for l in lines if l.isupper() and len(l) < 40), None)

            all_items.append({
                "title": title,
                "datum": datum,
                "locatie": locatie,
            })
    return all_items

def parse_date(datum_str):
    # Simpele parser: pakt eerste datum
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

def generate_ics(events):
    cal = Calendar()
    for item in events:
        date = parse_date(item["datum"])
        if not date:
            continue
        e = Event()
        e.name = item["title"]
        e.begin = date
        e.location = item["locatie"] or "Brabantse Wal"
        cal.events.add(e)
    with open(ICS_FILE, "w", encoding="utf-8") as f:
        f.writelines(cal)

if __name__ == "__main__":
    items = fetch_items()
    generate_ics(items)
