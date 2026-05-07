"""pytest-bdd step definitions for orchestrator.feature (end-to-end)."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import patch, MagicMock
import json

from tests.fixtures.mock_rss_feeds import (
    LEFT_FEED_ENTRIES,
    RIGHT_FEED_ENTRIES,
    MOCK_SUMMARIES_LEFT,
    MOCK_SUMMARIES_RIGHT,
    MOCK_BIAS_SCORES,
)

scenarios("../../specs/orchestrator.feature")


@pytest.fixture
def ctx():
    return {}


# ── given ─────────────────────────────────────────────────────────────────────

@given("the LangGraph news pipeline is initialized")
def pipeline_available():
    pass


@given("the LLM client is available")
def llm_ok():
    pass


@given("the RSS reader tool is available")
def rss_ok():
    pass


@given(parsers.parse('the topic is "{topic}"'), target_fixture="ctx")
def topic(ctx, topic):
    ctx["topic"] = topic
    return ctx


@given("the pipeline produces at least 1 StoryPair", target_fixture="ctx")
def force_pair(ctx):
    ctx["force_pairs"] = True
    return ctx


@given(parsers.parse("{n_left:d} left articles have no matching right article"), target_fixture="ctx")
def unmatched_left_count(ctx, n_left):
    ctx["expected_unmatched_left"] = n_left
    ctx["topic"] = None  # No topic filter so all mock articles pass through
    return ctx


@given(parsers.parse("{n_right:d} right article has no matching left article"), target_fixture="ctx")
def unmatched_right_count(ctx, n_right):
    ctx["expected_unmatched_right"] = n_right
    return ctx


@given(parsers.parse("the pipeline produces 3 StoryPairs with match_confidence values {vals}"), target_fixture="ctx")
def pipeline_three_pairs(ctx, vals):
    import ast
    ctx["expected_confidence_order"] = sorted(ast.literal_eval(vals), reverse=True)
    return ctx


@given("the pipeline has completed Moderator stage", target_fixture="ctx")
def after_moderator(ctx):
    ctx["skip_to_output"] = True
    return ctx


@given("all RSS feeds return connection errors", target_fixture="ctx")
def all_feeds_fail(ctx):
    ctx["all_feeds_fail"] = True
    return ctx


# ── when ──────────────────────────────────────────────────────────────────────

@when("the full news pipeline runs", target_fixture="ctx")
def run_full_pipeline(ctx):
    from src.graph.news_graph import build_graph

    all_fail = ctx.get("all_feeds_fail", False)

    def mock_fetch(url):
        if all_fail:
            raise ConnectionError("All feeds mocked to fail")
        if any(s in url for s in ["cnn", "guardian", "npr", "msnbc"]):
            return LEFT_FEED_ENTRIES
        return RIGHT_FEED_ENTRIES

    mock_llm_responses = [
        # summarizer calls
        *[MagicMock(content="Sentence one. Sentence two. Sentence three.") for _ in range(10)],
        # bias analyzer calls
        *[MagicMock(content=json.dumps({
            "lean_score": -0.4, "key_claims": ["claim"], "framing_notes": "notes", "named_entities": ["entity"]
        })) for _ in range(10)],
        # moderator calls
        *[MagicMock(content=json.dumps({
            "agreements": ["both agree on X"], "disagreements": ["differ on Y"]
        })) for _ in range(10)],
    ]
    call_count = [0]

    def mock_llm(messages):
        idx = call_count[0]
        call_count[0] += 1
        if idx < len(mock_llm_responses):
            return mock_llm_responses[idx]
        resp = MagicMock()
        resp.content = "Fallback mock response."
        return resp

    ctx["llm_call_log"] = []

    def tracked_llm(messages):
        ctx["llm_call_log"].append(messages)
        return mock_llm(messages)

    with patch("src.tools.rss_reader.fetch_feed", side_effect=mock_fetch):
        with patch("src.agents.summarizer.llm", side_effect=tracked_llm):
            with patch("src.agents.bias_analyzer.llm", side_effect=tracked_llm):
                with patch("src.agents.moderator.llm", side_effect=tracked_llm):
                    # balanced_output now uses an LLM; provide a mock that returns article JSON
                    article_json = json.dumps({
                        "headline": "Test Balanced Headline",
                        "lead": "A factual lead sentence.",
                        "left_perspective": "Left-leaning sources emphasise impact.",
                        "right_perspective": "Right-leaning sources stress economic concerns.",
                        "common_ground": ["both agree on X"],
                        "diverging_points": ["differ on Y"],
                    })
                    article_resp = MagicMock()
                    article_resp.content = article_json
                    with patch("src.agents.balanced_output.llm", return_value=article_resp):
                        graph = build_graph()
                        initial_state = {"topic": ctx.get("topic")}
                        final_state = graph.invoke(initial_state)

    ctx["final_state"] = final_state
    ctx["balanced_digest"] = final_state.get("balanced_digest")
    ctx["llm_calls_during_output"] = 0  # tracked separately in BalancedOutputAgent
    return ctx


@when("the BalancedOutputAgent runs", target_fixture="ctx")
def run_balanced_output(ctx):
    from src.agents.balanced_output import BalancedOutputAgent

    article_json = json.dumps({
        "headline": "Test Balanced Headline",
        "lead": "A factual lead sentence about the story.",
        "left_perspective": "Left-leaning sources emphasise policy impact.",
        "right_perspective": "Right-leaning sources stress economic concerns.",
        "common_ground": ["both agree on X"],
        "diverging_points": ["differ on Y"],
    })
    article_resp = MagicMock()
    article_resp.content = article_json

    # Provide at least one matched pair so the agent can write an article
    matched_stories = ctx.get("matched_stories") or [
        {
            "pair_id": "pair-1",
            "topic_label": "Test Topic",
            "left_article_id": MOCK_SUMMARIES_LEFT[0]["article_id"],
            "right_article_id": MOCK_SUMMARIES_RIGHT[0]["article_id"],
            "shared_entities": ["entity"],
            "agreements": ["both agree on X"],
            "disagreements": ["differ on Y"],
            "match_confidence": 0.85,
        }
    ]

    with patch("src.agents.balanced_output.llm", return_value=article_resp):
        state = {
            "topic": ctx.get("topic"),
            "matched_stories": matched_stories,
            "unmatched_left": ctx.get("unmatched_left", []),
            "unmatched_right": ctx.get("unmatched_right", []),
            "summaries": MOCK_SUMMARIES_LEFT + MOCK_SUMMARIES_RIGHT,
            "bias_scores": MOCK_BIAS_SCORES,
        }
        result = BalancedOutputAgent(state)
    ctx["balanced_digest"] = result["balanced_digest"]
    return ctx


# ── then ──────────────────────────────────────────────────────────────────────

@then("balanced_digest is not None")
def digest_exists(ctx):
    assert ctx["balanced_digest"] is not None


@then(parsers.parse('balanced_digest.topic is "{topic}"'))
def digest_topic(ctx, topic):
    assert ctx["balanced_digest"]["topic"] == topic


@then("balanced_digest.generated_at is a valid ISO 8601 datetime string")
def digest_datetime(ctx):
    from datetime import datetime
    ts = ctx["balanced_digest"]["generated_at"]
    assert ts.endswith("Z") or "T" in ts
    datetime.fromisoformat(ts.replace("Z", "+00:00"))


@then("balanced_digest.paired_stories is a list")
def digest_pairs_list(ctx):
    assert isinstance(ctx["balanced_digest"]["paired_stories"], list)


@then("balanced_digest.left_only_stories is a list")
def digest_left_only_list(ctx):
    assert isinstance(ctx["balanced_digest"]["left_only_stories"], list)


@then("balanced_digest.right_only_stories is a list")
def digest_right_only_list(ctx):
    assert isinstance(ctx["balanced_digest"]["right_only_stories"], list)


@then("each entry in balanced_digest.paired_stories has a non-empty left story")
def paired_has_left(ctx):
    for p in ctx["balanced_digest"]["paired_stories"]:
        assert p["left"]["title"] or p["left"]["summary_text"]


@then("each entry in balanced_digest.paired_stories has a non-empty right story")
def paired_has_right(ctx):
    for p in ctx["balanced_digest"]["paired_stories"]:
        assert p["right"]["title"] or p["right"]["summary_text"]


@then("each entry in balanced_digest.paired_stories has a topic_label")
def paired_has_topic_label(ctx):
    for p in ctx["balanced_digest"]["paired_stories"]:
        assert p["topic_label"]


@then(parsers.parse("balanced_digest.left_only_stories contains {n:d} entries"))
def left_only_count(ctx, n):
    assert len(ctx["balanced_digest"]["left_only_stories"]) == n


@then(parsers.parse("balanced_digest.right_only_stories contains {n:d} entries"))
def right_only_count(ctx, n):
    assert len(ctx["balanced_digest"]["right_only_stories"]) == n


@then(parsers.parse("balanced_digest.paired_stories are ordered {expected}"))
def pairs_sorted(ctx, expected):
    import ast
    order = ast.literal_eval(expected)
    confidences = [p.get("match_confidence", 0) for p in ctx["balanced_digest"]["paired_stories"]]
    assert confidences == sorted(confidences, reverse=True)


@then("balanced_digest.articles is a list")
def digest_articles_list(ctx):
    assert isinstance(ctx["balanced_digest"]["articles"], list)


@then("each article in balanced_digest.articles has a non-empty headline")
def articles_have_headline(ctx):
    for article in ctx["balanced_digest"]["articles"]:
        assert article.get("headline"), f"Missing headline in {article}"


@then("each article in balanced_digest.articles has a non-empty lead")
def articles_have_lead(ctx):
    for article in ctx["balanced_digest"]["articles"]:
        assert article.get("lead"), f"Missing lead in {article}"


@then("each article in balanced_digest.articles has a non-empty left_perspective")
def articles_have_left_perspective(ctx):
    for article in ctx["balanced_digest"]["articles"]:
        assert article.get("left_perspective"), f"Missing left_perspective in {article}"


@then("each article in balanced_digest.articles has a non-empty right_perspective")
def articles_have_right_perspective(ctx):
    for article in ctx["balanced_digest"]["articles"]:
        assert article.get("right_perspective"), f"Missing right_perspective in {article}"


@then("balanced_digest.paired_stories is an empty list")
def pairs_empty(ctx):
    assert ctx["balanced_digest"]["paired_stories"] == []


@then("balanced_digest.left_only_stories is an empty list")
def left_only_empty(ctx):
    assert ctx["balanced_digest"]["left_only_stories"] == []


@then("balanced_digest.right_only_stories is an empty list")
def right_only_empty(ctx):
    assert ctx["balanced_digest"]["right_only_stories"] == []


@then("no exception propagates to the caller")
def no_exception_propagates(ctx):
    pass  # Reaching this step proves no exception was raised


@then(parsers.parse("the pipeline state contains {field}"))
def state_has_field(ctx, field):
    assert field in ctx["final_state"]
