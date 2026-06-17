"""
Verify emails via SMTP before sending.
Catches bad addresses without sending an actual email.
Run: python verify_leads.py
"""
import sqlite3
import smtplib
import dns.resolver
import time
from config import DB_PATH, YOUR_EMAIL

def get_mx(domain: str) -> str:
    """Get the mail server for a domain."""
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return str(sorted(records, key=lambda r: r.preference)[0].exchange).rstrip('.')
    except Exception:
        return ""

def smtp_verify(email: str) -> bool:
    """Check if an email exists by probing the mail server."""
    domain = email.split('@')[1]
    mx = get_mx(domain)
    if not mx:
        return False
    try:
        with smtplib.SMTP(timeout=10) as smtp:
            smtp.connect(mx, 25)
            smtp.helo('verify.local')
            smtp.mail(YOUR_EMAIL)
            code, _ = smtp.rcpt(email)
            return code == 250
    except Exception:
        # Server blocked probe — assume valid to avoid false negatives
        return True

def verify_batch(limit: int = 200):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get unsent leads with emails
    c.execute("""
        SELECT id, email FROM leads
        WHERE email IS NOT NULL AND email != ''
        AND email_sent = 0
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()

    print(f"\nVerifying {len(rows)} emails...\n")
    valid = 0
    invalid = 0

    for lead_id, email in rows:
        try:
            ok = smtp_verify(email)
            if not ok:
                # Mark as sent so it gets skipped
                c.execute("UPDATE leads SET email_sent=1, notes='bounced-precheck' WHERE id=?", (lead_id,))
                invalid += 1
                print(f"  BAD   {email}")
            else:
                valid += 1
                print(f"  OK    {email}")
            time.sleep(0.3)
        except Exception as e:
            valid += 1  # assume valid on error

    conn.commit()
    conn.close()
    print(f"\nDone: {valid} valid, {invalid} removed.")
    print(f"Now run: python main.py send local_service 100")

if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 9999
    verify_batch(limit)
