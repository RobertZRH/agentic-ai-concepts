"""LeftSourceFetcherAgent — fetches articles from left-leaning RSS sources."""
from src.config import LEFT_SOURCES
from src.tools.rss_reader import fetch_articles


def LeftSourceFetcherAgent(state: dict) -> dict:
    """LangGraph node. Reads `topic` from state, writes `left_articles`."""
    articles = fetch_articles(
        sources=LEFT_SOURCES,
        lean="left",
        topic=state.get("topic"),
    )
    return {"left_articles": articles}
