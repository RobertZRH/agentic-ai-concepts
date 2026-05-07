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

# ── LLM provider ──────────────────────────────────────────────────────────────
# Set LLM_PROVIDER=github to use GitHub Models instead of Azure OpenAI.
# GitHub Models endpoint: https://models.inference.ai.azure.com
# Requires: GITHUB_TOKEN with models:read permission.

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "azure").lower()  # "azure" | "github"

# Azure OpenAI
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-55")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

# GitHub Models
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"
GITHUB_MODELS_DEPLOYMENT = os.getenv("GITHUB_MODELS_DEPLOYMENT", "openai/gpt-4.1")
