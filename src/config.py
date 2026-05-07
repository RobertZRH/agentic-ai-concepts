"""Configuration: RSS sources and Azure OpenAI client."""
import os
from dotenv import load_dotenv

load_dotenv()

# ── RSS sources ────────────────────────────────────────────────────────────────

LEFT_SOURCES: list[tuple[str, str]] = [
    ("CNN", "http://rss.cnn.com/rss/edition.rss"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
    ("NPR", "https://feeds.npr.org/1001/rss.xml"),
    ("MSNBC", "http://www.msnbc.com/feeds/latest"),
]

RIGHT_SOURCES: list[tuple[str, str]] = [
    ("Fox News", "https://moxie.foxnews.com/google-publisher/latest.xml"),
    ("WSJ Opinion", "https://feeds.a.dj.com/rss/RSSOpinion.xml"),
    ("NY Post", "https://nypost.com/feed/"),
    ("Breitbart", "http://feeds.feedburner.com/breitbart"),
]

# ── Azure OpenAI ───────────────────────────────────────────────────────────────

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-55")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
