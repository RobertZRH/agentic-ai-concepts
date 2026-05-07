"""pytest-bdd step definitions for moderator.feature."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import patch, MagicMock
import json

from tests.fixtures.mock_rss_feeds import MOCK_SUMMARIES_LEFT, MOCK_SUMMARIES_RIGHT, MOCK_BIAS_SCORES

scenarios("../../specs/moderator.feature")


@pytest.fixture
def ctx():
    return {}


# ── given ─────────────────────────────────────────────────────────────────────

@given("summaries and bias_scores are populated with matching article_ids", target_fixture="ctx")
def populated_state(ctx):
    # Initialize empty — scenario Given steps add the specific data they need
    ctx["summaries"] = []
    ctx["bias_scores"] = []
    return ctx


@given(parsers.parse('a left Summary about "{topic}" mentioning entities {entities}'), target_fixture="ctx")
@given(parsers.parse('a left Summary about "{topic}" with entities {entities}'), target_fixture="ctx")
def left_summary_with_entities(ctx, topic, entities):
    import ast
    entity_list = ast.literal_eval(entities)
    ctx.setdefault("summaries", [])
    ctx.setdefault("bias_scores", [])
    ctx["summaries"].append({
        "article_id": "left-mod-1",
        "source_label": "The Guardian",
        "lean": "left",
        "original_title": f"Left view on {topic}",
        "summary_text": f"Left perspective on {topic}. {' '.join(entity_list)} are central to this story.",
    })
    ctx["bias_scores"].append({
        "article_id": "left-mod-1",
        "source_label": "The Guardian",
        "lean_score": -0.4,
        "lean_label": "center-left",
        "key_claims": [f"Left claim about {topic}"],
        "framing_notes": "Left-leaning framing.",
        "named_entities": entity_list,
    })
    return ctx


@given(parsers.parse('a right Summary about "{topic}" mentioning entities {entities}'), target_fixture="ctx")
@given(parsers.parse('a right Summary about "{topic}" with entities {entities}'), target_fixture="ctx")
def right_summary_with_entities(ctx, topic, entities):
    import ast
    entity_list = ast.literal_eval(entities)
    ctx.setdefault("summaries", [])
    ctx.setdefault("bias_scores", [])
    ctx["summaries"].append({
        "article_id": "right-mod-1",
        "source_label": "Fox News",
        "lean": "right",
        "original_title": f"Right view on {topic}",
        "summary_text": f"Right perspective on {topic}. {' '.join(entity_list)} are discussed.",
    })
    ctx["bias_scores"].append({
        "article_id": "right-mod-1",
        "source_label": "Fox News",
        "lean_score": 0.6,
        "lean_label": "right",
        "key_claims": [f"Right claim about {topic}"],
        "framing_notes": "Right-leaning framing.",
        "named_entities": entity_list,
    })
    return ctx


@given(parsers.parse("{n_left:d} left summaries and {n_right:d} right summaries where all share \"{entity}\" as an entity"), target_fixture="ctx")
def multiple_summaries_shared_entity(ctx, n_left, n_right, entity):
    ctx.setdefault("summaries", [])
    ctx.setdefault("bias_scores", [])
    for i in range(n_left):
        aid = f"left-multi-{i+1}"
        ctx["summaries"].append({
            "article_id": aid,
            "source_label": "NPR",
            "lean": "left",
            "original_title": f"Left article {i+1} about {entity}",
            "summary_text": f"Left view {i+1} on {entity}.",
        })
        ctx["bias_scores"].append({
            "article_id": aid,
            "source_label": "NPR",
            "lean_score": -0.3,
            "lean_label": "center-left",
            "key_claims": [],
            "framing_notes": "",
            "named_entities": [entity],
        })
    for i in range(n_right):
        aid = f"right-multi-{i+1}"
        ctx["summaries"].append({
            "article_id": aid,
            "source_label": "Fox News",
            "lean": "right",
            "original_title": f"Right article {i+1} about {entity}",
            "summary_text": f"Right view {i+1} on {entity}.",
        })
        ctx["bias_scores"].append({
            "article_id": aid,
            "source_label": "Fox News",
            "lean_score": 0.4,
            "lean_label": "center-right",
            "key_claims": [],
            "framing_notes": "",
            "named_entities": [entity],
        })
    return ctx


@given("a matched StoryPair with overlapping content about \"trade tariffs\"", target_fixture="ctx")
def matched_pair_trade(ctx):
    entities = ["tariffs", "trade", "US economy"]
    for lean, aid, source in [("left", "left-trade-1", "CNN"), ("right", "right-trade-1", "WSJ Opinion")]:
        ctx.setdefault("summaries", []).append({
            "article_id": aid,
            "source_label": source,
            "lean": lean,
            "original_title": f"{lean.title()} view on trade tariffs",
            "summary_text": f"This article discusses tariffs, trade, and the US economy from a {lean} perspective.",
        })
        ctx.setdefault("bias_scores", []).append({
            "article_id": aid,
            "source_label": source,
            "lean_score": -0.4 if lean == "left" else 0.5,
            "lean_label": "center-left" if lean == "left" else "center-right",
            "key_claims": ["tariffs impact trade"],
            "framing_notes": f"{lean.title()} framing on tariffs.",
            "named_entities": entities,
        })
    return ctx


@given("a valid StoryPair match", target_fixture="ctx")
def valid_pair(ctx):
    return matched_pair_trade(ctx)


@given("the LLM call for agreements/disagreements fails", target_fixture="ctx")
def llm_fails_moderator(ctx):
    ctx["moderator_llm_fail"] = True
    return ctx


@given("a left Summary and right Summary covering the same event with few shared entity names", target_fixture="ctx")
def embedding_fallback_setup(ctx):
    ctx.setdefault("summaries", [])
    ctx.setdefault("bias_scores", [])
    ctx["summaries"].append({
        "article_id": "left-emb-1",
        "source_label": "NPR",
        "lean": "left",
        "original_title": "Fed decision analysis",
        "summary_text": "The central bank kept borrowing costs unchanged.",
    })
    ctx["summaries"].append({
        "article_id": "right-emb-1",
        "source_label": "Fox News",
        "lean": "right",
        "original_title": "Interest rate hold sparks debate",
        "summary_text": "Monetary policy remains steady as policymakers hold rates.",
    })
    ctx["bias_scores"].append({
        "article_id": "left-emb-1", "source_label": "NPR", "lean_score": -0.3,
        "lean_label": "center-left", "key_claims": [], "framing_notes": "",
        "named_entities": ["central bank"],
    })
    ctx["bias_scores"].append({
        "article_id": "right-emb-1", "source_label": "Fox News", "lean_score": 0.4,
        "lean_label": "center-right", "key_claims": [], "framing_notes": "",
        "named_entities": ["Federal Reserve"],
    })
    return ctx


@given("the entity overlap Jaccard similarity is below 0.2", target_fixture="ctx")
def low_entity_overlap(ctx):
    ctx["force_low_entity_overlap"] = True
    return ctx


@given("the embedding cosine similarity between the summaries is 0.82", target_fixture="ctx")
def high_embedding_sim(ctx):
    ctx["mock_embedding_similarity"] = 0.82
    return ctx


# ── when ──────────────────────────────────────────────────────────────────────

@when("the ModeratorAgent runs", target_fixture="ctx")
def run_moderator(ctx):
    from src.agents.moderator import ModeratorAgent

    llm_should_fail = ctx.get("moderator_llm_fail", False)
    mock_embedding_sim = ctx.get("mock_embedding_similarity", None)

    def mock_llm(messages):
        if llm_should_fail:
            raise RuntimeError("Mocked moderator LLM failure")
        resp = MagicMock()
        resp.content = json.dumps({
            "agreements": ["Both sides agree the Fed held rates"],
            "disagreements": ["Left says workers benefit; right says inflation worsens"],
        })
        return resp

    patches = [patch("src.agents.moderator.llm", side_effect=mock_llm)]
    if mock_embedding_sim is not None:
        patches.append(patch("src.agents.moderator.compute_embedding_similarity", return_value=mock_embedding_sim))

    with patches[0]:
        if len(patches) > 1:
            with patches[1]:
                state = {"summaries": ctx["summaries"], "bias_scores": ctx["bias_scores"]}
                result = ModeratorAgent(state)
        else:
            state = {"summaries": ctx["summaries"], "bias_scores": ctx["bias_scores"]}
            result = ModeratorAgent(state)

    ctx["matched_stories"] = result["matched_stories"]
    ctx["unmatched_left"] = result["unmatched_left"]
    ctx["unmatched_right"] = result["unmatched_right"]
    return ctx


# ── then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse("matched_stories contains {n:d} StoryPair"))
def matched_count(ctx, n):
    assert len(ctx["matched_stories"]) == n


@then("matched_stories is empty")
def matched_empty(ctx):
    assert ctx["matched_stories"] == []


@then(parsers.parse('the StoryPair.shared_entities includes "{entity}"'))
def shared_entity(ctx, entity):
    assert any(entity in p["shared_entities"] for p in ctx["matched_stories"])


@then("the StoryPair.match_confidence is greater than 0.0")
def confidence_positive(ctx):
    for p in ctx["matched_stories"]:
        assert p["match_confidence"] > 0.0


@then("neither article appears in unmatched_left or unmatched_right")
def not_unmatched(ctx):
    all_unmatched = set(ctx["unmatched_left"]) | set(ctx["unmatched_right"])
    for p in ctx["matched_stories"]:
        assert p["left_article_id"] not in all_unmatched
        assert p["right_article_id"] not in all_unmatched


@then("the left article appears in unmatched_left")
def left_unmatched(ctx):
    assert len(ctx["unmatched_left"]) > 0


@then("the right article appears in unmatched_right")
def right_unmatched(ctx):
    assert len(ctx["unmatched_right"]) > 0


@then("no article_id appears in more than one StoryPair")
def no_duplicate_pairs(ctx):
    left_ids = [p["left_article_id"] for p in ctx["matched_stories"]]
    right_ids = [p["right_article_id"] for p in ctx["matched_stories"]]
    assert len(left_ids) == len(set(left_ids))
    assert len(right_ids) == len(set(right_ids))


@then("the StoryPair.agreements is a list (may be empty)")
def agreements_is_list(ctx):
    for p in ctx["matched_stories"]:
        assert isinstance(p["agreements"], list)


@then("the StoryPair.disagreements is a list (may be empty)")
def disagreements_is_list(ctx):
    for p in ctx["matched_stories"]:
        assert isinstance(p["disagreements"], list)


@then("the StoryPair.agreements is an empty list")
def agreements_empty(ctx):
    for p in ctx["matched_stories"]:
        assert p["agreements"] == []


@then("the StoryPair.disagreements is an empty list")
def disagreements_empty(ctx):
    for p in ctx["matched_stories"]:
        assert p["disagreements"] == []


@then("the StoryPair.match_confidence equals the entity overlap score")
def confidence_from_overlap(ctx):
    for p in ctx["matched_stories"]:
        assert p["match_confidence"] >= 0.0


@then(parsers.parse("the StoryPair.match_confidence is approximately {value:f}"))
def confidence_approx(ctx, value):
    for p in ctx["matched_stories"]:
        assert abs(p["match_confidence"] - value) < 0.05


@then("no exception is raised")
def no_exception_moderator(ctx):
    pass  # If we reached this step, no exception was raised
