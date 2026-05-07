"""pytest-bdd step definitions for news_fetcher.feature."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import patch, MagicMock

from tests.fixtures.mock_rss_feeds import LEFT_FEED_ENTRIES, RIGHT_FEED_ENTRIES

scenarios("../../specs/news_fetcher.feature")

# ── shared state ──────────────────────────────────────────────────────────────

@pytest.fixture
def ctx():
    return {}


# ── given ─────────────────────────────────────────────────────────────────────

@given("the RSS reader tool is available")
def rss_reader_available():
    pass  # will be satisfied once src/tools/rss_reader.py exists


@given("no topic filter is set", target_fixture="ctx")
def no_topic(ctx):
    ctx["topic"] = None
    return ctx


@given(parsers.parse('the topic is "{topic}"'), target_fixture="ctx")
def with_topic(ctx, topic):
    ctx["topic"] = topic
    return ctx


@given("the CNN feed is configured to return a connection error", target_fixture="ctx")
def cnn_feed_error(ctx):
    ctx["fail_sources"] = ["CNN"]
    return ctx


# ── when ──────────────────────────────────────────────────────────────────────

@when("the LeftSourceFetcherAgent runs", target_fixture="ctx")
def run_left_fetcher(ctx):
    from src.agents.left_fetcher import LeftSourceFetcherAgent
    fail_sources = ctx.get("fail_sources", [])

    def mock_fetch(url):
        if "cnn" in url.lower() and "CNN" in fail_sources:
            raise ConnectionError("Mocked CNN feed failure")
        entries = [e for e in LEFT_FEED_ENTRIES if e["source_label"] not in fail_sources]
        return entries

    with patch("src.tools.rss_reader.fetch_feed", side_effect=mock_fetch):
        state = {"topic": ctx.get("topic")}
        result = LeftSourceFetcherAgent(state)
    ctx["left_articles"] = result["left_articles"]
    return ctx


@when("the RightSourceFetcherAgent runs", target_fixture="ctx")
def run_right_fetcher(ctx):
    from src.agents.right_fetcher import RightSourceFetcherAgent
    with patch("src.tools.rss_reader.fetch_feed", return_value=RIGHT_FEED_ENTRIES):
        state = {"topic": ctx.get("topic")}
        result = RightSourceFetcherAgent(state)
    ctx["right_articles"] = result["right_articles"]
    return ctx


# ── then ──────────────────────────────────────────────────────────────────────

@then("left_articles is a list")
def left_is_list(ctx):
    assert isinstance(ctx["left_articles"], list)


@then("each article in left_articles has a non-empty title")
def left_titles(ctx):
    for a in ctx["left_articles"]:
        assert a["title"]


@then("each article in left_articles has a non-empty link")
def left_links(ctx):
    for a in ctx["left_articles"]:
        assert a["link"]


@then(parsers.parse('each article in left_articles has a source_label in {labels}'))
def left_source_labels(ctx, labels):
    import ast
    valid = ast.literal_eval(labels)
    for a in ctx["left_articles"]:
        assert a["source_label"] in valid


@then(parsers.parse('each article in left_articles has a lean of "{lean}"'))
def left_lean(ctx, lean):
    for a in ctx["left_articles"]:
        assert a["lean"] == lean


@then(parsers.parse('every article in left_articles mentions "{keyword}" in its title or summary'))
def left_topic_filter(ctx, keyword):
    for a in ctx["left_articles"]:
        text = (a["title"] + " " + a.get("summary", "")).lower()
        assert keyword.lower() in text


@then("right_articles is a list")
def right_is_list(ctx):
    assert isinstance(ctx["right_articles"], list)


@then("each article in right_articles has a non-empty title")
def right_titles(ctx):
    for a in ctx["right_articles"]:
        assert a["title"]


@then("each article in right_articles has a non-empty link")
def right_links(ctx):
    for a in ctx["right_articles"]:
        assert a["link"]


@then(parsers.parse('each article in right_articles has a source_label in {labels}'))
def right_source_labels(ctx, labels):
    import ast
    valid = ast.literal_eval(labels)
    for a in ctx["right_articles"]:
        assert a["source_label"] in valid


@then(parsers.parse('each article in right_articles has a lean of "{lean}"'))
def right_lean(ctx, lean):
    for a in ctx["right_articles"]:
        assert a["lean"] == lean


@then(parsers.parse('every article in right_articles mentions "{keyword}" in its title or summary'))
def right_topic_filter(ctx, keyword):
    for a in ctx["right_articles"]:
        text = (a["title"] + " " + a.get("summary", "")).lower()
        assert keyword.lower() in text


@then("left_articles still contains articles from other left-leaning sources")
def left_partial_results(ctx):
    assert len(ctx["left_articles"]) > 0
    labels = {a["source_label"] for a in ctx["left_articles"]}
    assert "CNN" not in labels


@then("no exception is raised")
def no_exception():
    pass  # exceptions would have already propagated


@then("left_articles is an empty list")
def left_empty(ctx):
    assert ctx["left_articles"] == []
