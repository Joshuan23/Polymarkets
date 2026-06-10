import anthropic
from config import ANTHROPIC_API_KEY, YOUR_NAME, CALENDLY_LINK, YOUR_PRICE

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SEQUENCE = ["initial", "followup_1", "followup_2", "breakup"]


def generate_email(lead: dict, niche_profile: dict, touch: str = "initial") -> dict:
    """Generate a personalized cold email for a lead using Claude."""

    first = lead.get("first_name", "there")
    company = lead.get("company", "your company")
    title = lead.get("title", "")
    pain = niche_profile["pain_point"]
    result = niche_profile["result"]

    prompts = {
        "initial": f"""Write a cold outreach email with these exact constraints:
- Subject line: max 7 words, no spam triggers, no ALL CAPS
- Body: max 5 sentences, no bullet points
- Tone: direct peer-to-peer, NOT salesy or corporate
- End with ONE clear CTA linking to: {CALENDLY_LINK}
- Sign off as {YOUR_NAME}

Lead context:
- Name: {first}
- Title: {title}
- Company: {company}
- Their pain: {pain}
- Result we deliver: {result}
- Price: {YOUR_PRICE} one-time project

Do NOT mention AI in the subject. Do NOT use words like "synergy", "leverage", "game-changer".
Return ONLY valid JSON: {{"subject": "...", "body": "..."}}""",

        "followup_1": f"""Write a 3-sentence follow-up to a cold email that got no reply.
- Assume they're busy, not uninterested
- Add ONE new piece of social proof or result (make it specific and believable)
- End with an easy yes/no question
- Sign off as {YOUR_NAME}

Lead: {first} at {company} ({title})
Original pain addressed: {pain}

Return ONLY valid JSON: {{"subject": "Re: [original subject]", "body": "..."}}""",

        "followup_2": f"""Write a 3-sentence second follow-up. Try a different angle — focus on a specific outcome or quick win, not the full service.
- Offer something low-commitment (a free audit, a quick loom video, a template)
- Keep it short
- Sign off as {YOUR_NAME}

Lead: {first} at {company}

Return ONLY valid JSON: {{"subject": "...", "body": "..."}}""",

        "breakup": f"""Write a short "breakup" email — last attempt, no hard feelings.
- 2 sentences max
- Leave the door open
- No guilt-tripping
- Sign off as {YOUR_NAME}

Lead: {first} at {company}

Return ONLY valid JSON: {{"subject": "Closing the loop", "body": "..."}}""",
    }

    prompt = prompts.get(touch, prompts["initial"])

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    import json
    text = msg.content[0].text.strip()
    # Strip markdown code block if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def personalize_subject(subject: str, first_name: str) -> str:
    """Add first name to subject for higher open rates."""
    if first_name and first_name.lower() not in subject.lower():
        return f"{first_name}, {subject[0].lower()}{subject[1:]}"
    return subject
