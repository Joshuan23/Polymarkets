import os
from dotenv import load_dotenv

load_dotenv()

# API Keys - loaded from .env (copy .env.example → .env and fill in values)
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
YELP_API_KEY = os.getenv("YELP_API_KEY", "")
MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY", "")
MAILCHIMP_SERVER = os.getenv("MAILCHIMP_SERVER", "")  # e.g. "us1"
MAILCHIMP_LIST_ID = os.getenv("MAILCHIMP_LIST_ID", "")
CALENDLY_LINK = os.getenv("CALENDLY_LINK", "https://calendly.com/yourname/30min")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
YOUR_NAME = os.getenv("YOUR_NAME", "Josh")
YOUR_EMAIL = os.getenv("YOUR_EMAIL", "joshuan.sandoval@gmail.com")
YOUR_SERVICE = os.getenv("YOUR_SERVICE", "AI automation for small businesses")
YOUR_PRICE = os.getenv("YOUR_PRICE", "$3,000")

DB_PATH = "leads.db"
