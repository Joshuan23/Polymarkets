"""
$100K Outbound Sales Engine
Usage:
  python main.py dashboard           — show live revenue tracker
  python main.py scrape <niche>      — pull leads from Apollo (default: real_estate)
  python main.py send <niche>        — generate + send emails to queued leads
  python main.py preview <niche>     — preview email copy before sending
  python main.py mark <id> <field>   — update a lead (e.g. mark abc123 deal_closed)
  python main.py leads               — list recent leads
  python main.py niches              — list available niches
"""
import sys
import json

sys.path.insert(0, "src")

from leads.icp import PROFILES, DEFAULT_NICHE
from leads.apollo_client import search_leads, save_leads_to_db
from outreach.email_generator import generate_email, personalize_subject
from outreach.mailchimp_client import (
    add_or_update_subscriber, create_campaign, send_campaign, plain_text_to_html
)
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


def cmd_send(niche: str):
    profile = PROFILES.get(niche)
    if not profile:
        print(f"Unknown niche '{niche}'.")
        return

    leads = list_leads(limit=200)
    unsent = [l for l in leads if not l["email_sent"] and l.get("email")]

    if not unsent:
        print("No unsent leads with emails. Run `python main.py scrape` first.")
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
            # 1. Generate personalized email
            email_data = generate_email(lead, profile, "initial")
            subject = personalize_subject(email_data["subject"], lead["first_name"])
            body_html = plain_text_to_html(email_data["body"])

            # 2. Add to Mailchimp
            add_or_update_subscriber(lead, tags=[niche, "outbound-sequence"])

            # 3. Create and send campaign
            campaign_id = create_campaign(
                subject=subject,
                body_html=body_html,
                from_name=YOUR_NAME,
                reply_to=YOUR_EMAIL,
            )
            send_campaign(campaign_id)

            # 4. Mark as sent in DB
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
