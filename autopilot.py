"""
NeverMiss Autopilot
Runs daily to find leads, verify emails, and send outreach automatically.
Usage: python autopilot.py
"""
import sqlite3
import uuid
import time
import re
import socket
import smtplib
import dns.resolver
from datetime import datetime
from config import (
    DB_PATH, YOUR_EMAIL, YOUR_NAME,
    CALENDLY_LINK, GMAIL_APP_PASSWORD
)

# ── Settings ──────────────────────────────────────────────────────────────────

DAILY_EMAIL_LIMIT = 40  # emails to send per run (keep low for Gmail safety)

# Search targets — edit these for your city and niches
SEARCH_TARGETS = [
    ("plumber", "Tampa FL"),
    ("hvac", "Tampa FL"),
    ("electrician", "Tampa FL"),
    ("roofer", "Tampa FL"),
    ("auto repair", "Tampa FL"),
]

RESULTS_PER_SEARCH = 25  # Outscraper results per search (free = 100/month total)

# ── Database ──────────────────────────────────────────────────────────────────

def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            first_name TEXT, last_name TEXT, email TEXT,
            title TEXT, company TEXT, linkedin_url TEXT,
            phone TEXT,
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
    for col in ["phone"]:
        try:
            c.execute(f"ALTER TABLE leads ADD COLUMN {col} TEXT")
        except Exception:
            pass
    conn.commit()
    conn.close()

# ── Lead Finding ──────────────────────────────────────────────────────────────

def _save_lead(c, name, phone, email):
    """Insert a lead if new. Returns 1 if saved, 0 if duplicate/skip."""
    if not name:
        return 0
    try:
        c.execute("""
            INSERT OR IGNORE INTO leads
              (id, first_name, last_name, email, title, company, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "", "", email or None, "Owner", name, phone or None))
        return 1 if c.rowcount else 0
    except Exception:
        return 0


def find_leads():
    """Find leads — Firecrawl (gets emails) if key is set, else Yellow Pages (phones only)."""
    from config import FIRECRAWL_API_KEY

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    total_saved = 0
    with_email = 0

    if FIRECRAWL_API_KEY:
        from src.leads.firecrawl_client import search_businesses as fc_search
        for term, location in SEARCH_TARGETS:
            print(f"  Firecrawl: {term} in {location}...")
            try:
                businesses = fc_search(term, location, limit=RESULTS_PER_SEARCH)
            except Exception as e:
                print(f"  Error searching {term}: {e}")
                continue
            for biz in businesses:
                saved = _save_lead(c, biz.get("name", ""), biz.get("phone", ""), biz.get("email", ""))
                total_saved += saved
                if saved and biz.get("email"):
                    with_email += 1
            time.sleep(1)
        print(f"  ({with_email} of {total_saved} new leads have emails)")
    else:
        from src.leads.yellowpages_client import search_yellowpages
        for term, location in SEARCH_TARGETS:
            print(f"  Yellow Pages: {term} in {location}...")
            try:
                businesses = search_yellowpages(term, location, RESULTS_PER_SEARCH)
            except Exception as e:
                print(f"  Error searching {term}: {e}")
                continue
            for biz in businesses:
                total_saved += _save_lead(c, biz.get("name", ""), biz.get("phone", ""), biz.get("email", ""))
            time.sleep(2)

    conn.commit()
    conn.close()
    return total_saved

# ── Email Verification ─────────────────────────────────────────────────────────

def get_mx(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return str(sorted(records, key=lambda r: r.preference)[0].exchange).rstrip('.')
    except Exception:
        return ""

def smtp_verify(email):
    domain = email.split('@')[1]
    mx = get_mx(domain)
    if not mx:
        return False
    try:
        with smtplib.SMTP(timeout=8) as smtp:
            smtp.connect(mx, 25)
            smtp.helo('verify.local')
            smtp.mail(YOUR_EMAIL)
            code, _ = smtp.rcpt(email)
            return code == 250
    except Exception:
        return True  # assume valid if server blocks probe

def verify_new_leads(limit=100):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, email FROM leads
        WHERE email IS NOT NULL AND email != ''
        AND email_sent = 0
        AND notes IS NULL
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()

    removed = 0
    for lead_id, email in rows:
        try:
            if not smtp_verify(email):
                c.execute("UPDATE leads SET email_sent=1, notes='bounced-precheck' WHERE id=?", (lead_id,))
                removed += 1
            time.sleep(0.2)
        except Exception:
            pass

    conn.commit()
    conn.close()
    return removed

# ── Email Sending ──────────────────────────────────────────────────────────────

def is_valid_email(email):
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return False
    domain = email.split('@')[1]
    try:
        socket.getaddrinfo(domain, None)
        return True
    except socket.gaierror:
        return False

def build_email(lead):
    first = lead["first_name"] or "there"
    company = lead["company"] or "your business"
    subject = f"quick question about {company}"
    body = f"""Hi {first},

Quick question — when someone calls {company} and nobody picks up, what happens to that customer?

I help local service business owners set up a system that texts missed callers back within 60 seconds, books the job automatically, and follows up for a Google review after. Most owners recover 3–5 jobs in the first week.

Worth a 15-minute call to see if it makes sense for you? You can grab a time here: {CALENDLY_LINK}

{YOUR_NAME}

..."""
    return subject, body

def send_email(to_email, subject, body):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = YOUR_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(YOUR_EMAIL, GMAIL_APP_PASSWORD)
        smtp.sendmail(YOUR_EMAIL, to_email, msg.as_string())

def send_batch():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT id, first_name, last_name, email, company FROM leads
        WHERE email IS NOT NULL AND email != ''
        AND email_sent = 0
        AND (notes IS NULL OR notes != 'bounced-precheck')
        ORDER BY created_at ASC
        LIMIT ?
    """, (DAILY_EMAIL_LIMIT,))
    leads = [dict(r) for r in c.fetchall()]
    conn.close()

    sent = skipped = errors = 0
    for lead in leads:
        try:
            if not is_valid_email(lead["email"]):
                skipped += 1
                _mark_sent(lead["id"], "invalid-domain")
                continue

            subject, body = build_email(lead)
            send_email(lead["email"], subject, body)
            _mark_sent(lead["id"])
            sent += 1
            print(f"  Sent → {lead['first_name'] or ''} {lead['last_name'] or ''} @ {lead['company'] or lead['email']}")
            time.sleep(1.5)

        except Exception as e:
            errors += 1
            print(f"  Error → {lead.get('email')}: {e}")

    return sent, skipped, errors

def _mark_sent(lead_id, notes=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if notes:
        c.execute("UPDATE leads SET email_sent=1, notes=? WHERE id=?", (notes, lead_id))
    else:
        c.execute("UPDATE leads SET email_sent=1 WHERE id=?", (lead_id,))
    conn.commit()
    conn.close()

# ── Stats ──────────────────────────────────────────────────────────────────────

def print_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM leads")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM leads WHERE email_sent=0 AND email IS NOT NULL AND email != ''")
    queued = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM leads WHERE email_sent=1 AND (notes IS NULL OR notes='') ")
    sent = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM leads WHERE reply_received=1")
    replies = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM leads WHERE call_booked=1")
    calls = c.fetchone()[0]
    conn.close()
    print(f"\n  Leads in DB:    {total}")
    print(f"  Queued to send: {queued}")
    print(f"  Emails sent:    {sent}")
    print(f"  Replies:        {replies}")
    print(f"  Calls booked:   {calls}\n")

# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"  NeverMiss Autopilot — {datetime.now().strftime('%b %d, %Y %I:%M %p')}")
    print(f"{'='*50}\n")

    ensure_db()

    print("[ 1/3 ] Finding new leads...")
    new_leads = find_leads()
    print(f"        {new_leads} new leads added\n")

    print("[ 2/3 ] Verifying emails...")
    removed = verify_new_leads(limit=150)
    print(f"        {removed} bad emails removed\n")

    print("[ 3/3 ] Sending emails...")
    sent, skipped, errors = send_batch()
    print(f"\n        {sent} sent, {skipped} skipped, {errors} errors\n")

    print("[ DONE ] Today's stats:")
    print_stats()
    print("Run again tomorrow. Replies will appear in your Gmail inbox.\n")
