"""RightSourceFetcherAgent — fetches articles from right-leaning RSS sources."""
from src.config import RIGHT_SOURCES
from src.tools.rss_reader import fetch_articles


def RightSourceFetcherAgent(state: dict) -> dict:
    """LangGraph node. Reads `topic` from state, writes `right_articles`."""
    articles = fetch_articles(
        sources=RIGHT_SOURCES,
        lean="right",
        topic=state.get("topic"),
    )
    return {"right_articles": articles}
