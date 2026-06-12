import requests
from config import HUNTER_API_KEY

HUNTER_BASE = "https://api.hunter.io/v2"


def domain_search(domain: str, limit: int = 10) -> list[dict]:
    """Find all emails associated with a domain."""
    resp = requests.get(f"{HUNTER_BASE}/domain-search", params={
        "domain": domain,
        "limit": limit,
        "api_key": HUNTER_API_KEY,
    })
    resp.raise_for_status()
    return resp.json().get("data", {}).get("emails", [])


def find_email(domain: str, first_name: str, last_name: str) -> dict:
    """Find email for a specific person at a domain."""
    resp = requests.get(f"{HUNTER_BASE}/email-finder", params={
        "domain": domain,
        "first_name": first_name,
        "last_name": last_name,
        "api_key": HUNTER_API_KEY,
    })
    resp.raise_for_status()
    return resp.json().get("data", {})


def get_credits() -> dict:
    """Check remaining Hunter.io credits."""
    resp = requests.get(f"{HUNTER_BASE}/account", params={"api_key": HUNTER_API_KEY})
    resp.raise_for_status()
    data = resp.json().get("data", {})
    return data.get("requests", {})
