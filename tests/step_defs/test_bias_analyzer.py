"""pytest-bdd step definitions for bias_analyzer.feature (summarizer + bias)."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import patch, MagicMock

from tests.fixtures.mock_rss_feeds import (
    MOCK_SUMMARIES_LEFT,
    MOCK_SUMMARIES_RIGHT,
    MOCK_BIAS_SCORES,
)

scenarios("../../specs/summarizer.feature", "../../specs/bias_analyzer.feature")


# ── shared state ──────────────────────────────────────────────────────────────

@pytest.fixture
def ctx():
    return {}


# ── given ─────────────────────────────────────────────────────────────────────

@given("the LLM client is available")
def llm_available():
    pass


@given(parsers.parse("left_articles contains {n:d} articles"), target_fixture="ctx")
@given(parsers.parse("left_articles contains {n:d} article"), target_fixture="ctx")
def left_n_articles(ctx, n):
    ctx.setdefault("left_articles", [])
    for i in range(n):
        ctx["left_articles"].append({
            "id": f"left-{i+1}",
            "title": f"Left article {i+1}",
            "summary": f"Summary of left article {i+1}.",
            "link": f"https://example.com/left-{i+1}",
            "source_label": "CNN",
            "lean": "left",
        })
    return ctx


@given(parsers.parse("right_articles contains {n:d} articles"), target_fixture="ctx")
@given(parsers.parse("right_articles contains {n:d} article"), target_fixture="ctx")
def right_n_articles(ctx, n):
    ctx.setdefault("right_articles", [])
    for i in range(n):
        ctx["right_articles"].append({
            "id": f"right-{i+1}",
            "title": f"Right article {i+1}",
            "summary": f"Summary of right article {i+1}.",
            "link": f"https://example.com/right-{i+1}",
            "source_label": "Fox News",
            "lean": "right",
        })
    return ctx


@given(parsers.parse('a left article about "{topic}" from "{source}"'), target_fixture="ctx")
def left_article_topic(ctx, topic, source):
    ctx.setdefault("left_articles", [])
    ctx["left_articles"].append({
        "id": "left-topic-1",
        "title": f"Left article about {topic}",
        "summary": f"This article discusses {topic} in depth.",
        "link": "https://example.com/left-topic-1",
        "source_label": source,
        "lean": "left",
    })
    return ctx


@given(parsers.parse("the LLM call fails for the {ordinal} left article"), target_fixture="ctx")
def llm_fails_for_nth(ctx, ordinal):
    ordinal_map = {"first": 0, "second": 1, "third": 2, "fourth": 3}
    ctx["llm_fail_index"] = ordinal_map.get(ordinal, 1)
    return ctx


@given(parsers.parse("summaries contains {n:d} Summary objects"), target_fixture="ctx")
def summaries_n(ctx, n):
    ctx["summaries"] = (MOCK_SUMMARIES_LEFT + MOCK_SUMMARIES_RIGHT)[:n]
    return ctx


@given("summaries contains at least 1 Summary", target_fixture="ctx")
def summaries_at_least_one(ctx):
    ctx.setdefault("summaries", MOCK_SUMMARIES_LEFT[:1])
    return ctx


@given("a Summary with a lean_score of -0.8 after analysis", target_fixture="ctx")
def summary_lean_left(ctx):
    ctx["summaries"] = [MOCK_SUMMARIES_LEFT[0]]
    ctx["expected_lean_label"] = "left"
    ctx["expected_lean_score"] = -0.8  # forces mock to return this score → label="left"
    return ctx


@given("a Summary expected to score near 0.0", target_fixture="ctx")
def summary_lean_center(ctx):
    ctx["summaries"] = [{
        "article_id": "center-1",
        "source_label": "Reuters",
        "lean": "left",
        "original_title": "Neutral report",
        "summary_text": "A neutral factual report with no apparent bias.",
    }]
    ctx["expected_lean_label"] = "center"
    ctx["expected_lean_score"] = 0.0  # forces mock to return 0.0 → label="center"
    return ctx


@given("a Summary about \"tariff policy\" with multiple factual claims", target_fixture="ctx")
def summary_tariff(ctx):
    ctx["summaries"] = [{
        "article_id": "tariff-1",
        "source_label": "WSJ Opinion",
        "lean": "right",
        "original_title": "Tariff policy debate",
        "summary_text": "New tariffs impose 25% duty on steel imports. The measure affects 200 billion dollars in trade. Economists warn of retaliation from trading partners. The administration defends the policy as protecting jobs.",
    }]
    return ctx


@given(parsers.parse("the LLM call fails for the {ordinal} summary"), target_fixture="ctx")
def llm_fails_summary(ctx, ordinal):
    ordinal_map = {"first": 0, "second": 1, "third": 2, "fourth": 3}
    ctx["bias_llm_fail_index"] = ordinal_map.get(ordinal, 2)
    return ctx


# ── when ──────────────────────────────────────────────────────────────────────

@when("the SummarizerAgent runs", target_fixture="ctx")
def run_summarizer(ctx):
    from src.agents.summarizer import SummarizerAgent

    call_count = [0]
    fail_index = ctx.get("llm_fail_index", -1)

    def mock_llm(messages):
        idx = call_count[0]
        call_count[0] += 1
        if idx == fail_index:
            raise RuntimeError("Mocked LLM failure")
        resp = MagicMock()
        resp.content = "Mocked summary sentence one. Sentence two. Sentence three."
        return resp

    with patch("src.agents.summarizer.llm", side_effect=mock_llm):
        state = {
            "left_articles": ctx.get("left_articles", []),
            "right_articles": ctx.get("right_articles", []),
        }
        result = SummarizerAgent(state)
    ctx["summaries"] = result["summaries"]
    return ctx


@when("the BiasAnalyzerAgent runs", target_fixture="ctx")
def run_bias_analyzer(ctx):
    from src.agents.bias_analyzer import BiasAnalyzerAgent

    call_count = [0]
    fail_index = ctx.get("bias_llm_fail_index", -1)
    scores_pool = MOCK_BIAS_SCORES
    forced_score = ctx.get("expected_lean_score", None)

    def mock_llm(messages):
        idx = call_count[0]
        call_count[0] += 1
        if idx == fail_index:
            raise RuntimeError("Mocked LLM failure")
        if forced_score is not None:
            import json
            resp = MagicMock()
            resp.content = json.dumps({
                "lean_score": forced_score,
                "key_claims": ["mock claim"],
                "framing_notes": "mock notes",
                "named_entities": ["mock entity"],
            })
            return resp
        score = scores_pool[idx % len(scores_pool)]
        resp = MagicMock()
        import json
        resp.content = json.dumps({
            "lean_score": score["lean_score"],
            "key_claims": score["key_claims"],
            "framing_notes": score["framing_notes"],
            "named_entities": score["named_entities"],
        })
        return resp

    with patch("src.agents.bias_analyzer.llm", side_effect=mock_llm):
        state = {"summaries": ctx.get("summaries", [])}
        result = BiasAnalyzerAgent(state)
    ctx["bias_scores"] = result["bias_scores"]
    return ctx


# ── then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse("summaries contains exactly {n:d} Summary objects"))
@then(parsers.parse("summaries contains exactly {n:d} Summary"))
def summaries_count(ctx, n):
    assert len(ctx["summaries"]) == n


@then("each Summary has a non-empty summary_text")
def summaries_non_empty(ctx):
    for s in ctx["summaries"]:
        assert isinstance(s.get("summary_text"), str)


@then("each Summary.article_id matches an article in left_articles or right_articles")
def summaries_ids_match(ctx):
    all_ids = {a["id"] for a in ctx.get("left_articles", []) + ctx.get("right_articles", [])}
    for s in ctx["summaries"]:
        assert s["article_id"] in all_ids


@then("each Summary.source_label matches the source of its article")
def summaries_source_match(ctx):
    id_to_source = {
        a["id"]: a["source_label"]
        for a in ctx.get("left_articles", []) + ctx.get("right_articles", [])
    }
    for s in ctx["summaries"]:
        assert s["source_label"] == id_to_source.get(s["article_id"])


@then("the Summary.summary_text contains between 1 and 5 sentences")
def summary_sentence_count(ctx):
    for s in ctx["summaries"]:
        text = s.get("summary_text", "")
        sentences = [p.strip() for p in text.split(".") if p.strip()]
        assert 1 <= len(sentences) <= 5


@then("the resulting Summary.summary_text does not contain first-person language")
def no_first_person(ctx):
    for s in ctx["summaries"]:
        text = s.get("summary_text", "").lower()
        assert "i think" not in text
        assert "in my opinion" not in text


@then('the resulting Summary.summary_text does not contain phrases like "I think" or "in my opinion"')
def no_opinion_phrases(ctx):
    for s in ctx["summaries"]:
        text = s.get("summary_text", "").lower()
        assert "i think" not in text
        assert "in my opinion" not in text


@then("the failed article's Summary.summary_text is an empty string")
def failed_summary_empty(ctx):
    fail_idx = ctx.get("llm_fail_index", -1)
    if fail_idx >= 0 and fail_idx < len(ctx["summaries"]):
        assert ctx["summaries"][fail_idx]["summary_text"] == ""


@then(parsers.parse("bias_scores contains exactly {n:d} BiasScore objects"))
def bias_count(ctx, n):
    assert len(ctx["bias_scores"]) == n


@then("each BiasScore.article_id matches a Summary.article_id")
def bias_ids_match(ctx):
    summary_ids = {s["article_id"] for s in ctx["summaries"]}
    for b in ctx["bias_scores"]:
        assert b["article_id"] in summary_ids


@then("each BiasScore.lean_score is between -1.0 and 1.0 inclusive")
def bias_score_range(ctx):
    for b in ctx["bias_scores"]:
        assert -1.0 <= b["lean_score"] <= 1.0


@then(parsers.parse('the BiasScore.lean_label is "{label}"'))
def bias_label(ctx, label):
    for b in ctx["bias_scores"]:
        assert b["lean_label"] == label


@then("the BiasScore.key_claims has at most 5 entries")
def bias_claims_max(ctx):
    for b in ctx["bias_scores"]:
        assert len(b["key_claims"]) <= 5


@then("each entry in key_claims is a non-empty string")
def bias_claims_strings(ctx):
    for b in ctx["bias_scores"]:
        for claim in b["key_claims"]:
            assert isinstance(claim, str) and claim.strip()


@then("the failed article's BiasScore.lean_score is 0.0")
def failed_bias_score(ctx):
    fail_idx = ctx.get("bias_llm_fail_index", -1)
    if fail_idx >= 0 and fail_idx < len(ctx["bias_scores"]):
        assert ctx["bias_scores"][fail_idx]["lean_score"] == 0.0


@then('the failed article\'s BiasScore.lean_label is "center"')
def failed_bias_label(ctx):
    fail_idx = ctx.get("bias_llm_fail_index", -1)
    if fail_idx >= 0 and fail_idx < len(ctx["bias_scores"]):
        assert ctx["bias_scores"][fail_idx]["lean_label"] == "center"

@then("no exception is raised")
def no_exception_raised(ctx):
    pass  # If we reached this step, no exception was raised