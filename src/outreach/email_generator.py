from config import YOUR_NAME, CALENDLY_LINK, YOUR_PRICE

SEQUENCE = ["initial", "followup_1", "followup_2", "breakup"]

# Proven cold email templates — no AI API needed, zero cost.
# These are written to convert: short, specific, direct, one CTA.
TEMPLATES = {
    "initial": {
        "subject": "quick question about {company}",
        "body": (
            "Hi {first},\n\n"
            "Quick question — when someone calls {company} and nobody picks up, what happens?\n\n"
            "I help {niche_type} owners set up a system that texts missed callers back within 60 seconds, "
            "books the job automatically, and follows up for a Google review after. "
            "Most owners recover 3–5 jobs in the first week.\n\n"
            "Worth a 15-minute call to see if it makes sense for you? "
            "You can grab a time here: {calendly}\n\n"
            "{name}"
        ),
    },
    "followup_1": {
        "subject": "Re: quick question about {company}",
        "body": (
            "Hi {first},\n\n"
            "Just bumping this up — I know things get busy.\n\n"
            "One owner I worked with last month was losing roughly $2k/week to missed calls going to voicemail. "
            "Two weeks after setup, that stopped. Same phones, same team — just an automatic text-back handling it.\n\n"
            "Is this something {company} deals with at all? Even a yes or no helps. {calendly}\n\n"
            "{name}"
        ),
    },
    "followup_2": {
        "subject": "free audit for {company}",
        "body": (
            "Hi {first},\n\n"
            "I'll make this easy — I can do a free 10-minute audit of {company}'s current lead capture "
            "and tell you exactly how many calls are slipping through. No pitch, just the number.\n\n"
            "If the number is zero, great — nothing to fix. If it's not, you'll know what it's costing you. "
            "Book here if you want it: {calendly}\n\n"
            "{name}"
        ),
    },
    "breakup": {
        "subject": "Closing the loop",
        "body": (
            "Hi {first},\n\n"
            "I won't keep following up — I'll assume the timing isn't right.\n\n"
            "If that changes and you ever want to look at what's falling through the cracks at {company}, "
            "my link is always open: {calendly}\n\n"
            "{name}"
        ),
    },
}

# Niche-specific override for the initial email body when available.
NICHE_OVERRIDES = {
    "real_estate": {
        "initial": {
            "subject": "quick question about {company}",
            "body": (
                "Hi {first},\n\n"
                "Do you have a system that follows up with leads who never booked a showing — "
                "automatically, without you having to remember?\n\n"
                "I set up automated follow-up sequences for agents that keep cold leads warm and "
                "re-engage them when they're ready. Takes about a week to set up and runs on its own.\n\n"
                "Would it make sense to talk? {calendly}\n\n"
                "{name}"
            ),
        }
    },
    "law_firm": {
        "initial": {
            "subject": "question about {company}'s intake process",
            "body": (
                "Hi {first},\n\n"
                "How much time does your team spend on intake calls, conflict checks, and chasing "
                "documents that clients haven't sent yet?\n\n"
                "I automate that entire process for small firms — intake forms, document reminders, "
                "e-signatures, and case summaries all handled before the first real meeting. "
                "Most firms cut 6–8 hours of admin per week.\n\n"
                "15 minutes to show you how it works? {calendly}\n\n"
                "{name}"
            ),
        }
    },
}


def generate_email(lead: dict, niche_profile: dict, touch: str = "initial") -> dict:
    """Return a personalized email from a template — no API, no cost."""
    first = lead.get("first_name") or "there"
    company = lead.get("company") or "your business"
    niche_key = niche_profile.get("niche_key", "")
    niche_type = niche_profile.get("niche_type", "business")

    override = NICHE_OVERRIDES.get(niche_key, {}).get(touch)
    template = override if override else TEMPLATES.get(touch, TEMPLATES["initial"])

    subject = template["subject"].format(
        first=first, company=company, name=YOUR_NAME,
        calendly=CALENDLY_LINK, price=YOUR_PRICE, niche_type=niche_type,
    )
    body = template["body"].format(
        first=first, company=company, name=YOUR_NAME,
        calendly=CALENDLY_LINK, price=YOUR_PRICE, niche_type=niche_type,
    )
    return {"subject": subject, "body": body}


def personalize_subject(subject: str, first_name: str) -> str:
    """Prefix subject with first name for higher open rates."""
    if first_name and first_name.lower() not in subject.lower():
        return f"{first_name}, {subject[0].lower()}{subject[1:]}"
    return subject
