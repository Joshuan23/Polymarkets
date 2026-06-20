"""
Free lead scraper using Yellow Pages — no API key required.
"""
import time
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def search_yellowpages(term: str, location: str, limit: int = 20) -> list[dict]:
    """Search Yellow Pages for local businesses."""
    results = []
    page = 1

    # Warm up the session with a homepage visit
    try:
        SESSION.get("https://www.yellowpages.com", timeout=10)
        time.sleep(1)
    except Exception:
        pass

    while len(results) < limit:
        # Use the direct URL format YP uses internally
        slug_term = term.replace(" ", "-").lower()
        slug_loc = location.replace(" ", "-").replace(",", "").lower()
        url = f"https://www.yellowpages.com/{slug_loc}/{slug_term}"
        if page > 1:
            url += f"?page={page}"

        try:
            resp = SESSION.get(url, timeout=15)
            if resp.status_code == 404:
                # Fall back to search endpoint
                resp = SESSION.get(
                    "https://www.yellowpages.com/search",
                    params={"search_terms": term, "geo_location_terms": location, "page": page},
                    timeout=15,
                )
            resp.raise_for_status()
        except Exception as e:
            print(f"    YP fetch error (page {page}): {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")

        # Try multiple selectors — YP changes their HTML periodically
        listings = (
            soup.select("div.result")
            or soup.select("div.v-card")
            or soup.select("article.result")
            or soup.select("[class*='result']")
        )

        if not listings:
            print(f"    YP: no listings found on page {page} (site may have changed layout)")
            break

        for listing in listings:
            if len(results) >= limit:
                break

            name = (
                _text(listing.select_one("a.business-name span"))
                or _text(listing.select_one("h2.n a"))
                or _text(listing.select_one("a.business-name"))
                or _text(listing.select_one("[class*='business-name']"))
            )

            phone = (
                _text(listing.select_one("div.phones.phone.primary"))
                or _text(listing.select_one(".phone"))
                or _text(listing.select_one("[class*='phone']"))
            )

            website = ""
            for sel in ["a.track-visit-website", "a[href*='http'][class*='website']", "a.website-link"]:
                tag = listing.select_one(sel)
                if tag:
                    website = tag.get("href", "")
                    break

            email = _extract_email(listing.get_text())

            if name and name.strip():
                results.append({
                    "name": name.strip(),
                    "phone": _clean_phone(phone),
                    "website": website,
                    "email": email,
                })

        page += 1
        time.sleep(2)

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
