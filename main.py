"""
$100K Outbound Sales Engine
Usage:
  python main.py dashboard           — show live revenue tracker
  python main.py scrape <niche>      — pull leads from Apollo (requires paid plan)
  python main.py import <file.csv>   — import leads from a CSV file (free path)
  python main.py send <niche>        — generate + send emails to queued leads
  python main.py preview <niche>     — preview email copy before sending
  python main.py mark <id> <field>   — update a lead (e.g. mark abc123 deal_closed)
  python main.py leads               — list recent leads
  python main.py niches              — list available niches

CSV format for import:
  first_name,last_name,email,title,company,linkedin_url
  (linkedin_url column is optional)

Free lead sources:
  - LinkedIn (export connections): linkedin.com/mynetwork/invite-connect/connections/
  - Hunter.io free tier: 25 searches/month
  - Google Maps manually for local businesses (hvac_plumbing niche)
"""
import sys
import json

sys.path.insert(0, "src")

from leads.icp import PROFILES, DEFAULT_NICHE
from leads.apollo_client import search_leads, save_leads_to_db
from outreach.email_generator import generate_email, personalize_subject
from outreach.mailchimp_client import plain_text_to_html
from outreach.smtp_client import send_email
from dashboard.tracker import get_stats, mark_lead, list_leads, print_dashboard
from config import YOUR_NAME, YOUR_EMAIL


def cmd_dashboard():
    print_dashboard()


def cmd_scrape(niche: str):
    profile = PROFILES.get(niche)
    if not profile:
        print(f"Unknown niche '{niche}'. Run `python main.py niches` to see options.")
        return

    print(f"\nScraping leads for niche: {niche}")
    print(f"Target: {profile['description']}\n")

    leads = search_leads(
        titles=profile["titles"],
        industries=[],
        company_sizes=profile["company_sizes"],
        per_page=50,
    )

    if not leads:
        print("No leads returned. Check your APOLLO_API_KEY in .env")
        return

    saved = save_leads_to_db(leads)
    print(f"Saved {saved} new leads ({len(leads)} returned by Apollo).")
    print_dashboard()


def cmd_preview(niche: str):
    profile = PROFILES.get(niche)
    if not profile:
        print(f"Unknown niche '{niche}'.")
        return

    sample_lead = {
        "first_name": "Sarah",
        "last_name": "Johnson",
        "title": profile["titles"][0],
        "company": "Sample Co",
        "email": "sarah@example.com",
    }

    print(f"\n=== EMAIL PREVIEW FOR NICHE: {niche.upper()} ===\n")
    for touch in ["initial", "followup_1", "followup_2", "breakup"]:
        result = generate_email(sample_lead, profile, touch)
        subject = personalize_subject(result["subject"], sample_lead["first_name"])
        print(f"--- Touch {touch.upper()} ---")
        print(f"Subject: {subject}")
        print(f"\n{result['body']}\n")
        print("-" * 50 + "\n")


def cmd_import(csv_file: str):
    """Import leads from a CSV file into the local database."""
    import csv
    import uuid

    expected = ["first_name", "last_name", "email", "title", "company"]
    try:
        with open(csv_file, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = [h.strip().lower() for h in (reader.fieldnames or [])]
            missing = [col for col in expected if col not in headers]
            if missing:
                print(f"CSV is missing required columns: {missing}")
                print(f"Required: {expected}")
                return

            import sqlite3
            from config import DB_PATH
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id TEXT PRIMARY KEY,
                    first_name TEXT, last_name TEXT, email TEXT,
                    title TEXT, company TEXT, linkedin_url TEXT,
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

            inserted = skipped = 0
            for row in reader:
                row = {k.strip().lower(): v.strip() for k, v in row.items()}
                lead_id = str(uuid.uuid4())
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO leads
                          (id, first_name, last_name, email, title, company, linkedin_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        lead_id,
                        row.get("first_name", ""),
                        row.get("last_name", ""),
                        row.get("email", ""),
                        row.get("title", ""),
                        row.get("company", ""),
                        row.get("linkedin_url", ""),
                    ))
                    if c.rowcount:
                        inserted += 1
                    else:
                        skipped += 1
                except Exception:
                    skipped += 1

            conn.commit()
            conn.close()
            print(f"\nImported {inserted} leads ({skipped} skipped as duplicates).")
            print_dashboard()

    except FileNotFoundError:
        print(f"File not found: {csv_file}")


def cmd_send(niche: str):
    profile = PROFILES.get(niche)
    if not profile:
        print(f"Unknown niche '{niche}'.")
        return

    leads = list_leads(limit=200)
    unsent = [l for l in leads if not l["email_sent"] and l.get("email")]

    if not unsent:
        print("No unsent leads with emails. Run `python main.py import <file.csv>` or `python main.py scrape` first.")
        return

    print(f"\nPreparing to send to {len(unsent)} leads in niche: {niche}\n")
    confirm = input(f"Send emails to {len(unsent)} leads? [y/N] ")
    if confirm.lower() != "y":
        print("Cancelled.")
        return

    sent = 0
    errors = 0
    for lead in unsent:
        try:
            email_data = generate_email(lead, profile, "initial")
            subject = personalize_subject(email_data["subject"], lead["first_name"])
            body_html = plain_text_to_html(email_data["body"])

            send_email(
                to_email=lead["email"],
                subject=subject,
                body_html=body_html,
                body_text=email_data["body"],
            )

            mark_lead(lead["id"], "email_sent", 1)
            sent += 1
            print(f"  Sent to {lead['first_name']} {lead['last_name']} @ {lead['company']}")

        except Exception as e:
            errors += 1
            print(f"  Error sending to {lead.get('email')}: {e}")

    print(f"\nDone: {sent} sent, {errors} errors.")
    print_dashboard()


def cmd_mark(lead_id: str, field: str, value: str = "1"):
    try:
        val = float(value) if "." in value else int(value)
    except ValueError:
        val = value
    mark_lead(lead_id, field, val)
    print(f"Updated lead {lead_id}: {field} = {val}")
    print_dashboard()


def cmd_leads():
    leads = list_leads(limit=20)
    if not leads:
        print("No leads yet. Run `python main.py scrape <niche>` first.")
        return
    print(f"\n{'ID':<12} {'Name':<22} {'Company':<25} {'Email':<30} {'Sent':>5} {'Reply':>6} {'Call':>5} {'Closed':>7}")
    print("-" * 115)
    for l in leads:
        name = f"{l['first_name'] or ''} {l['last_name'] or ''}".strip()
        print(f"{(l['id'] or '')[:12]:<12} {name:<22} {(l['company'] or ''):<25} {(l['email'] or ''):<30} "
              f"{l['email_sent']:>5} {l['reply_received']:>6} {l['call_booked']:>5} {l['deal_closed']:>7}")
    print()


def cmd_niches():
    print("\nAvailable niches:\n")
    for key, profile in PROFILES.items():
        print(f"  {key:<20} {profile['description']}")
    print()


COMMANDS = {
    "dashboard": (cmd_dashboard, []),
    "scrape": (cmd_scrape, ["niche"]),
    "import": (cmd_import, ["csv_file"]),
    "preview": (cmd_preview, ["niche"]),
    "send": (cmd_send, ["niche"]),
    "mark": (cmd_mark, ["lead_id", "field", "value?"]),
    "leads": (cmd_leads, []),
    "niches": (cmd_niches, []),
}


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]
    fn, _ = COMMANDS[cmd]
    fn_args = args[1:]
    fn(*fn_args)
