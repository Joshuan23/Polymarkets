"""
Free lead scraper using Yellow Pages — no API key required.
"""
import time
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def search_yellowpages(term: str, location: str, limit: int = 20) -> list[dict]:
    """Search Yellow Pages for local businesses. Returns list of dicts with name, phone, website, email."""
    results = []
    page = 1

    while len(results) < limit:
        url = "https://www.yellowpages.com/search"
        params = {
            "search_terms": term,
            "geo_location_terms": location,
            "page": page,
        }

        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"    YP fetch error (page {page}): {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        listings = soup.select("div.result")

        if not listings:
            break

        for listing in listings:
            if len(results) >= limit:
                break

            name = _text(listing.select_one("a.business-name span"))
            phone = _text(listing.select_one("div.phones.phone.primary"))
            website = ""
            website_tag = listing.select_one("a.track-visit-website")
            if website_tag:
                website = website_tag.get("href", "")

            email = _extract_email(listing.get_text())

            if name:
                results.append({
                    "name": name,
                    "phone": _clean_phone(phone),
                    "website": website,
                    "email": email,
                })

        page += 1
        time.sleep(1.5)

    return results[:limit]


def _text(tag) -> str:
    return tag.get_text(strip=True) if tag else ""


def _clean_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return phone


def _extract_email(text: str) -> str:
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""
