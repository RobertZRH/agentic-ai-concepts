"""BalancedOutputAgent — formats the final balanced news digest. No LLM calls."""
from datetime import datetime, timezone

# No LLM is used in this agent. This attribute exists only so tests can assert
# it is never called (they patch it and verify call_count == 0).
llm = None


def BalancedOutputAgent(state: dict) -> dict:
    """LangGraph node. Pure data transformation — no LLM calls."""
    matched_stories = state.get("matched_stories", [])
    unmatched_left = state.get("unmatched_left", [])
    unmatched_right = state.get("unmatched_right", [])
    summaries = state.get("summaries", [])
    bias_scores = state.get("bias_scores", [])
    topic = state.get("topic")

    summary_by_id = {s["article_id"]: s for s in summaries}
    bias_by_id = {b["article_id"]: b for b in bias_scores}

    def make_snippet(article_id: str) -> dict:
        s = summary_by_id.get(article_id, {})
        b = bias_by_id.get(article_id, {})
        return {
            "source_label": s.get("source_label", "[data unavailable]"),
            "lean_label": b.get("lean_label", "[data unavailable]"),
            "title": s.get("original_title", "[data unavailable]"),
            "summary_text": s.get("summary_text", "[data unavailable]"),
            "link": "",  # link not stored in Summary; enriched if needed downstream
            "key_claims": b.get("key_claims", []),
        }

    # Sort paired stories by match_confidence descending
    sorted_pairs = sorted(matched_stories, key=lambda p: p.get("match_confidence", 0), reverse=True)

    paired_stories = [
        {
            "topic_label": pair["topic_label"],
            "left": make_snippet(pair["left_article_id"]),
            "right": make_snippet(pair["right_article_id"]),
            "agreements": pair.get("agreements", []),
            "disagreements": pair.get("disagreements", []),
            "match_confidence": pair.get("match_confidence", 0.0),
        }
        for pair in sorted_pairs
    ]

    left_only = [make_snippet(aid) for aid in unmatched_left]
    right_only = [make_snippet(aid) for aid in unmatched_right]

    balanced_digest = {
        "topic": topic,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "paired_stories": paired_stories,
        "left_only_stories": left_only,
        "right_only_stories": right_only,
    }

    return {"balanced_digest": balanced_digest}
