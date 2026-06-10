import requests
import os

CALENDLY_TOKEN = os.getenv("CALENDLY_ACCESS_TOKEN", "")
BASE = "https://api.calendly.com"
HEADERS = {"Authorization": f"Bearer {CALENDLY_TOKEN}", "Content-Type": "application/json"}


def get_user_info() -> dict:
    resp = requests.get(f"{BASE}/users/me", headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("resource", {})


def get_scheduled_calls(min_start: str = None) -> list[dict]:
    """Fetch upcoming scheduled events."""
    user = get_user_info()
    user_uri = user.get("uri")

    params = {"user": user_uri, "status": "active", "count": 50}
    if min_start:
        params["min_start_time"] = min_start

    resp = requests.get(f"{BASE}/scheduled_events", headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json().get("collection", [])


def get_booking_link() -> str:
    user = get_user_info()
    return user.get("scheduling_url", os.getenv("CALENDLY_LINK", ""))


def count_new_bookings_since(iso_date: str) -> int:
    calls = get_scheduled_calls(min_start=iso_date)
    return len(calls)
