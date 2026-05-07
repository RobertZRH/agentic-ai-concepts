"""RSS feed fetch and parse utilities."""
import logging
import uuid
from typing import Optional

import feedparser

logger = logging.getLogger(__name__)


def fetch_feed(url: str) -> list[dict]:
    """Fetch and parse an RSS feed URL. Returns a list of raw entry dicts."""
    feed = feedparser.parse(url)
    if feed.bozo:
        raise ConnectionError(f"Failed to parse feed at {url}: {feed.bozo_exception}")
    return feed.entries


def parse_entry(entry: dict, source_label: str, lean: str) -> dict:
    """Convert a feedparser entry dict into an Article TypedDict."""
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, entry.get("link", str(uuid.uuid4())))),
        "title": entry.get("title", "").strip(),
        "summary": entry.get("summary", entry.get("description", "")).strip(),
        "link": entry.get("link", ""),
        "published_at": entry.get("published", ""),
        "source_label": source_label,
        "lean": lean,
    }


def fetch_articles(
    sources: list[tuple[str, str]],
    lean: str,
    topic: Optional[str] = None,
    max_per_source: int = 10,
) -> list[dict]:
    """
    Fetch articles from multiple RSS sources.

    Args:
        sources: List of (source_label, feed_url) tuples.
        lean: "left" or "right" — applied to all articles from these sources.
        topic: Optional keyword filter applied to title + summary.
        max_per_source: Maximum articles to return per feed.

    Returns:
        List of Article dicts. Never raises — failed feeds are skipped with a warning.
    """
    articles: list[dict] = []
    for source_label, url in sources:
        try:
            entries = fetch_feed(url)
        except Exception as exc:
            logger.warning("Skipping feed %s (%s): %s", source_label, url, exc)
            continue

        count = 0
        for entry in entries:
            if count >= max_per_source:
                break
            article = parse_entry(entry, source_label, lean)
            if topic:
                haystack = (article["title"] + " " + article["summary"]).lower()
                if topic.lower() not in haystack:
                    continue
            articles.append(article)
            count += 1

    return articles
