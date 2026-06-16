import time
import requests
from config import OUTSCRAPER_API_KEY

OUTSCRAPER_BASE = "https://api.app.outscraper.com"


def search_businesses(term: str, location: str, limit: int = 20) -> list[dict]:
    """Search Google Maps via Outscraper for local businesses."""
    headers = {"X-API-KEY": OUTSCRAPER_API_KEY}
    params = {
        "query": f"{term} in {location}",
        "limit": limit,
        "async": False,
        "fields": "name,phone,site,full_address,email,owner_name",
    }
    resp = requests.get(f"{OUTSCRAPER_BASE}/maps/search-v3", headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()

    # Outscraper returns nested list
    results = []
    for group in data.get("data", []):
        if isinstance(group, list):
            results.extend(group)
        elif isinstance(group, dict):
            results.append(group)
    return results


def scrape_website_emails(websites: list[str]) -> dict:
    """Scrape emails from business websites using Outscraper."""
    headers = {"X-API-KEY": OUTSCRAPER_API_KEY}
    params = {"query": ",".join(websites), "async": False}
    resp = requests.get(
        f"{OUTSCRAPER_BASE}/emails-and-contacts",
        headers=headers,
        params=params,
    )
    resp.raise_for_status()
    results = {}
    for item in resp.json().get("data", []):
        url = item.get("query", "")
        emails = item.get("emails", [])
        if emails:
            results[url] = emails[0]
    return results


def get_business_details(business_id: str) -> dict:
    """Not needed for Outscraper — details come in the search response."""
    return {}
