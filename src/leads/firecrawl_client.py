"""
Firecrawl lead scraper — finds businesses and extracts emails from their websites.
Free tier: 500 credits/month. Sign up at firecrawl.dev.
"""
import re
import time
import requests
from config import FIRECRAWL_API_KEY

BASE = "https://api.firecrawl.dev"

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Junk emails we never want to keep
EMAIL_BLOCKLIST = (
    "example.com", "sentry.io", "wixpress.com", "godaddy.com",
    "squarespace.com", "@2x", ".png", ".jpg", ".gif", ".webp",
    "yourdomain", "domain.com", "email.com",
)


def _headers():
    return {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json",
    }


def search_businesses(term: str, location: str, limit: int = 10) -> list[dict]:
    """
    Use Firecrawl search to find local businesses and scrape their pages.
    Returns list of dicts: {name, website, email, phone}.
    """
    query = f"{term} in {location} contact"
    payload = {
        "query": query,
        "limit": limit,
        "scrapeOptions": {"formats": ["markdown"]},
    }

    try:
        resp = requests.post(f"{BASE}/v1/search", headers=_headers(), json=payload, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f"    Firecrawl search error: {e}")
        return []

    data = resp.json()
    results = []

    for item in data.get("data", []):
        url = item.get("url", "")
        title = item.get("title", "") or ""
        # Skip directory aggregators — we want real business sites
        if any(d in url for d in ("yelp.com", "yellowpages.com", "facebook.com",
                                  "mapquest.com", "bbb.org", "angi.com", "thumbtack.com")):
            continue

        content = item.get("markdown", "") or item.get("description", "") or ""
        email = _best_email(content, url)
        phone = _first_phone(content)

        results.append({
            "name": _clean_name(title),
            "website": url,
            "email": email,
            "phone": phone,
        })

    return results


def scrape_emails(url: str) -> str:
    """Scrape a single website for the best contact email. 1 credit."""
    payload = {"url": url, "formats": ["markdown"]}
    try:
        resp = requests.post(f"{BASE}/v1/scrape", headers=_headers(), json=payload, timeout=60)
        resp.raise_for_status()
        content = resp.json().get("data", {}).get("markdown", "")
        return _best_email(content, url)
    except Exception:
        return ""


def get_credits() -> dict:
    """Check remaining Firecrawl credits."""
    try:
        resp = requests.get(f"{BASE}/v1/team/credit-usage", headers=_headers(), timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ── helpers ────────────────────────────────────────────────────────────────────

def _best_email(text: str, url: str) -> str:
    """Pick the most likely business contact email from scraped text."""
    candidates = [e.lower() for e in EMAIL_RE.findall(text or "")]
    clean = [e for e in candidates if not any(b in e for b in EMAIL_BLOCKLIST)]
    if not clean:
        return ""

    # Prefer emails on the business's own domain
    domain = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    on_domain = [e for e in clean if domain and domain in e]
    pool = on_domain or clean

    # Prefer info@/contact@/office@ over personal-looking ones
    for prefix in ("info@", "contact@", "office@", "hello@", "sales@", "admin@"):
        for e in pool:
            if e.startswith(prefix):
                return e
    return pool[0]


def _first_phone(text: str) -> str:
    m = re.search(r"\(?\b\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}\b", text or "")
    if not m:
        return ""
    digits = re.sub(r"\D", "", m.group(0))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return m.group(0)


def _clean_name(title: str) -> str:
    # Strip common title suffixes like " | Home", " - Plumbing Tampa"
    name = re.split(r"[|\-–—:]", title)[0].strip()
    return name[:80]
