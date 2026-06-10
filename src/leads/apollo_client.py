import requests
import sqlite3
from config import APOLLO_API_KEY, DB_PATH

APOLLO_BASE = "https://api.apollo.io/v1"


def search_leads(titles: list[str], industries: list[str], company_sizes: list[str],
                 locations: list[str] = None, page: int = 1, per_page: int = 25) -> list[dict]:
    """Search Apollo for prospects matching ICP."""
    headers = {"x-api-key": APOLLO_API_KEY, "Content-Type": "application/json"}
    payload = {
        "person_titles": titles,
        "organization_industry_tag_ids": industries,
        "organization_num_employees_ranges": company_sizes,
        "page": page,
        "per_page": per_page,
    }
    if locations:
        payload["person_locations"] = locations

    resp = requests.post(f"{APOLLO_BASE}/mixed_people/search", json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return data.get("people", [])


def enrich_lead(first_name: str, last_name: str, domain: str) -> dict:
    """Enrich a lead to get email address."""
    headers = {"x-api-key": APOLLO_API_KEY, "Content-Type": "application/json"}
    payload = {"first_name": first_name, "last_name": last_name, "domain": domain}
    resp = requests.post(f"{APOLLO_BASE}/people/match", json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json().get("person", {})


def save_leads_to_db(leads: list[dict]):
    """Persist leads to local SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            title TEXT,
            company TEXT,
            linkedin_url TEXT,
            status TEXT DEFAULT 'new',
            email_sent INTEGER DEFAULT 0,
            reply_received INTEGER DEFAULT 0,
            call_booked INTEGER DEFAULT 0,
            deal_closed INTEGER DEFAULT 0,
            deal_value REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    inserted = 0
    for lead in leads:
        try:
            c.execute("""
                INSERT OR IGNORE INTO leads (id, first_name, last_name, email, title, company, linkedin_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.get("id"),
                lead.get("first_name"),
                lead.get("last_name"),
                lead.get("email"),
                lead.get("title"),
                lead.get("organization", {}).get("name") if lead.get("organization") else None,
                lead.get("linkedin_url"),
            ))
            if c.rowcount:
                inserted += 1
        except Exception:
            continue
    conn.commit()
    conn.close()
    return inserted
