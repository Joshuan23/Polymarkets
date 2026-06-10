import requests
import hashlib
from config import MAILCHIMP_API_KEY, MAILCHIMP_SERVER, MAILCHIMP_LIST_ID

BASE = f"https://{MAILCHIMP_SERVER}.api.mailchimp.com/3.0"
AUTH = ("anystring", MAILCHIMP_API_KEY)


def _subscriber_hash(email: str) -> str:
    return hashlib.md5(email.lower().encode()).hexdigest()


def add_or_update_subscriber(lead: dict, tags: list[str] = None):
    """Add lead to Mailchimp audience with tags."""
    email = lead.get("email")
    if not email:
        return None

    url = f"{BASE}/lists/{MAILCHIMP_LIST_ID}/members/{_subscriber_hash(email)}"
    payload = {
        "email_address": email,
        "status_if_new": "subscribed",
        "merge_fields": {
            "FNAME": lead.get("first_name", ""),
            "LNAME": lead.get("last_name", ""),
            "COMPANY": lead.get("company", ""),
            "TITLE": lead.get("title", ""),
        },
    }
    if tags:
        payload["tags"] = [{"name": t, "status": "active"} for t in tags]

    resp = requests.put(url, json=payload, auth=AUTH)
    resp.raise_for_status()
    return resp.json()


def create_campaign(subject: str, body_html: str, from_name: str, reply_to: str,
                    segment_tag: str = None) -> str:
    """Create and schedule a Mailchimp campaign. Returns campaign ID."""

    # 1. Create campaign
    campaign_payload = {
        "type": "regular",
        "recipients": {"list_id": MAILCHIMP_LIST_ID},
        "settings": {
            "subject_line": subject,
            "from_name": from_name,
            "reply_to": reply_to,
            "auto_footer": False,
            "inline_css": True,
        },
    }
    if segment_tag:
        campaign_payload["recipients"]["segment_opts"] = {
            "match": "all",
            "conditions": [{"condition_type": "StaticSegment", "op": "static_is",
                            "field": "static_segment", "value": segment_tag}],
        }

    resp = requests.post(f"{BASE}/campaigns", json=campaign_payload, auth=AUTH)
    resp.raise_for_status()
    campaign_id = resp.json()["id"]

    # 2. Set content
    content_payload = {"html": body_html}
    resp = requests.put(f"{BASE}/campaigns/{campaign_id}/content",
                        json=content_payload, auth=AUTH)
    resp.raise_for_status()

    return campaign_id


def send_campaign(campaign_id: str):
    resp = requests.post(f"{BASE}/campaigns/{campaign_id}/actions/send", auth=AUTH)
    resp.raise_for_status()
    return resp.status_code == 204


def get_campaign_stats(campaign_id: str) -> dict:
    resp = requests.get(f"{BASE}/reports/{campaign_id}", auth=AUTH)
    resp.raise_for_status()
    r = resp.json()
    return {
        "sends": r.get("emails_sent", 0),
        "opens": r.get("opens", {}).get("unique_opens", 0),
        "open_rate": r.get("opens", {}).get("open_rate", 0),
        "clicks": r.get("clicks", {}).get("unique_clicks", 0),
        "click_rate": r.get("clicks", {}).get("click_rate", 0),
        "unsubscribes": r.get("unsubscribes", {}).get("unsubscribes", 0),
    }


def plain_text_to_html(text: str) -> str:
    """Wrap plain text email body in minimal HTML."""
    paragraphs = text.strip().split("\n\n")
    html_parts = ["<html><body style='font-family:Arial,sans-serif;font-size:15px;line-height:1.6;color:#222;max-width:600px;'>"]
    for p in paragraphs:
        html_parts.append(f"<p>{p.replace(chr(10), '<br>')}</p>")
    html_parts.append("</body></html>")
    return "".join(html_parts)
