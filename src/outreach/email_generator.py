from config import YOUR_NAME, CALENDLY_LINK, YOUR_PRICE

SEQUENCE = ["initial", "followup_1", "followup_2", "breakup"]

# Rotating subject lines — autopilot picks one per lead to avoid pattern detection
SUBJECTS = [
    "{company} — quick question",
    "missed calls at {company}?",
    "question for {company}",
    "saw {company} on Google Maps",
]

TEMPLATES = {
    "initial": {
        "subject": "{company} — quick question",
        "body": (
            "Hi {first},\n\n"
            "When someone calls {company} and nobody picks up — do they get a text back?\n\n"
            "I set up a system that automatically texts missed callers within 60 seconds, "
            "books the job, and follows up for a Google review. "
            "Most owners recover 3–5 jobs they were already losing every week.\n\n"
            "Would it even be worth a quick chat?\n\n"
            "{name}"
        ),
    },
    "followup_1": {
        "subject": "Re: {company} — quick question",
        "body": (
            "Hi {first},\n\n"
            "Wanted to follow up — I know things get busy.\n\n"
            "Quick version: missed calls are the #1 silent revenue killer for local service businesses. "
            "When someone calls and gets voicemail, 80% of them call a competitor instead.\n\n"
            "I fix that with an automatic text-back. Takes 48 hours to set up.\n\n"
            "Does {company} deal with missed calls at all?\n\n"
            "{name}"
        ),
    },
    "followup_2": {
        "subject": "free audit for {company}",
        "body": (
            "Hi {first},\n\n"
            "Last follow-up — I promise.\n\n"
            "I'll do a free 10-minute audit and tell you exactly how many calls "
            "{company} is losing per week and what that's costing you. "
            "No pitch. Just the number.\n\n"
            "Interested? Reply 'yes' and I'll send you the details.\n\n"
            "{name}"
        ),
    },
    "breakup": {
        "subject": "closing the loop — {company}",
        "body": (
            "Hi {first},\n\n"
            "I won't keep following up.\n\n"
            "If you ever want to know what missed calls are costing {company}, "
            "I'm one message away.\n\n"
            "{name}"
        ),
    },
}

NICHE_OVERRIDES = {
    "real_estate": {
        "initial": {
            "subject": "{company} — quick question",
            "body": (
                "Hi {first},\n\n"
                "Do you have anything that automatically follows up with leads "
                "who never booked a showing?\n\n"
                "I set up automated follow-up for agents that re-engages cold leads "
                "and books showings on autopilot. Runs itself after setup.\n\n"
                "Worth a quick chat?\n\n"
                "{name}"
            ),
        }
    },
    "law_firm": {
        "initial": {
            "subject": "question about {company}'s intake",
            "body": (
                "Hi {first},\n\n"
                "How much time does your team spend on intake calls and chasing documents?\n\n"
                "I automate that for small firms — intake forms, reminders, e-signatures, "
                "all handled before the first real meeting. Most firms save 6–8 hours a week.\n\n"
                "Would that be useful for {company}?\n\n"
                "{name}"
            ),
        }
    },
}

import random

def generate_email(lead: dict, niche_profile: dict, touch: str = "initial") -> dict:
    """Return a personalized email from a template — no API, no cost."""
    first = lead.get("first_name") or "there"
    company = lead.get("company") or "your business"
    niche_key = niche_profile.get("niche_key", "")
    niche_type = niche_profile.get("niche_type", "business")

    override = NICHE_OVERRIDES.get(niche_key, {}).get(touch)
    template = override if override else TEMPLATES.get(touch, TEMPLATES["initial"])

    # Rotate subject lines on initial touch for variety
    if touch == "initial" and not override:
        subject_template = random.choice(SUBJECTS)
    else:
        subject_template = template["subject"]

    subject = subject_template.format(
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
