import sqlite3
from config import DB_PATH


def get_stats() -> dict:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute("SELECT COUNT(*) FROM leads")
        total = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM leads WHERE email_sent = 1")
        emailed = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM leads WHERE reply_received = 1")
        replies = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM leads WHERE call_booked = 1")
        calls = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM leads WHERE deal_closed = 1")
        closed = c.fetchone()[0]

        c.execute("SELECT SUM(deal_value) FROM leads WHERE deal_closed = 1")
        revenue = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM leads WHERE email_sent = 0 AND email != ''")
        queued = c.fetchone()[0]

    except sqlite3.OperationalError:
        return {"error": "No data yet — run `python main.py scrape` first."}

    conn.close()

    return {
        "total_leads": total,
        "queued_to_email": queued,
        "emails_sent": emailed,
        "replies": replies,
        "calls_booked": calls,
        "deals_closed": closed,
        "revenue_earned": revenue,
        "reply_rate": f"{(replies/emailed*100):.1f}%" if emailed else "0%",
        "close_rate": f"{(closed/calls*100):.1f}%" if calls else "0%",
        "revenue_to_goal": f"${revenue:,.0f} / $100,000",
        "progress_pct": f"{(revenue/100000*100):.1f}%",
    }


def mark_lead(lead_id: str, field: str, value=1):
    conn = sqlite3.connect(DB_PATH)
    allowed = {"email_sent", "reply_received", "call_booked", "deal_closed", "deal_value", "status", "notes"}
    if field not in allowed:
        raise ValueError(f"Unknown field: {field}")
    conn.execute(f"UPDATE leads SET {field} = ? WHERE id = ?", (value, lead_id))
    conn.commit()
    conn.close()


def list_leads(status: str = None, limit: int = 20) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if status:
        c.execute("SELECT * FROM leads WHERE status = ? LIMIT ?", (status, limit))
    else:
        c.execute("SELECT * FROM leads LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def print_dashboard():
    stats = get_stats()
    if "error" in stats:
        print(f"\n  {stats['error']}\n")
        return

    bar_len = 30
    pct = min(float(stats["progress_pct"].rstrip("%")) / 100, 1.0)
    bar = "█" * int(bar_len * pct) + "░" * (bar_len - int(bar_len * pct))

    print(f"""
╔══════════════════════════════════════════╗
║        $100K REVENUE TRACKER             ║
╠══════════════════════════════════════════╣
║  {stats['revenue_to_goal']:<40} ║
║  [{bar}] {stats['progress_pct']:>6}  ║
╠══════════════════════════════════════════╣
║  Leads in DB       {stats['total_leads']:<22} ║
║  Queued to email   {stats['queued_to_email']:<22} ║
║  Emails sent       {stats['emails_sent']:<22} ║
║  Replies           {stats['replies']:<22} ║
║  Calls booked      {stats['calls_booked']:<22} ║
║  Deals closed      {stats['deals_closed']:<22} ║
╠══════════════════════════════════════════╣
║  Reply rate        {stats['reply_rate']:<22} ║
║  Close rate        {stats['close_rate']:<22} ║
╚══════════════════════════════════════════╝
""")
