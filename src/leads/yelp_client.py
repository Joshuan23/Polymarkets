import requests
from config import YELP_API_KEY

YELP_BASE = "https://api.yelp.com/v3"


def search_businesses(term: str, location: str, limit: int = 20) -> list[dict]:
    """Search Yelp for local businesses by type and location."""
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {
        "term": term,
        "location": location,
        "limit": min(limit, 50),
        "sort_by": "review_count",
    }
    resp = requests.get(f"{YELP_BASE}/businesses/search", headers=headers, params=params)
    resp.raise_for_status()
    return resp.json().get("businesses", [])


def get_business_details(business_id: str) -> dict:
    """Get full details for a business including website URL."""
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    resp = requests.get(f"{YELP_BASE}/businesses/{business_id}", headers=headers)
    resp.raise_for_status()
    return resp.json()
