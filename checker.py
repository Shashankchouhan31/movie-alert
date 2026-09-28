import json
import os
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

# ==================== EDIT THIS PART ====================
# Add one block per movie. Copy and paste a block to add more.
# live_keywords: alert if ANY of these words appear on the page
# required_text: (optional) alert only if ALL of these also appear
MOVIES = [
    {
        "name": "Doremon (BookMyShow)",
        "url": "https://in.bookmyshow.com/movies/hyderabad/doraemon-castle-of-the-undersea-devil/ET00507337",
        "live_keywords": ["Book tickets"],
        "required_text": [],
    },
    {
        "name": "Avengers Doomsday (BookMyShow)",
        "url": "https://in.bookmyshow.com/movies/hyderabad/avengers-doomsday/ET00439706",
        "live_keywords": ["Book tickets"],
        "required_text": ["imax"],
    },
    {
       "name": "Dune Part 3 (BookMyShow)",
        "url": "https://in.bookmyshow.com/movies/hyderabad/dune-part-three/ET00491771",
        "live_keywords": ["Book tickets"],
        "required_text": ["imax"],
    },
]
# ================= NO NEED TO EDIT BELOW =================

NTFY_TOPIC = os.environ["NTFY_TOPIC"]
STATE_FILE = Path("state.json")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def send_alert(name, url):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=f"Tickets are live: {name}".encode("utf-8"),
        headers={
            "Title": "Tickets live!",
            "Click": url,
            "Priority": "high",
            "Tags": "movie_camera,tada",
        },
        timeout=15,
    )


def is_live(page, movie):
    page.goto(movie["url"], wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    text = page.inner_text("body").lower()

    print("PAGE TITLE:", page.title())
    print("TEXT LENGTH:", len(text))
    print("TEXT START:", text[:200].replace("\n", " "))

    if not any(k.lower() in text for k in movie["live_keywords"]):
        return False
    return all(r.lower() in text for r in movie["required_text"])


def main():
    state = load_state()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, locale="en-IN")
        page = context.new_page()

        for movie in MOVIES:
            name = movie["name"]
            if state.get(name):
                print("Already alerted, skipping:", name)
                continue
            try:
                if is_live(page, movie):
                    print("LIVE:", name)
                    send_alert(name, movie["url"])
                    state[name] = True
                else:
                    print("Not yet:", name)
            except Exception as e:
                print("Problem checking", name, "-", e)

        browser.close()

    STATE_FILE.write_text(json.dumps(state, indent=2))


main()
