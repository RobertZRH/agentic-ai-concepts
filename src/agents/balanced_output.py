"""BalancedOutputAgent — writes final balanced articles from matched story pairs."""
import json
import logging
import uuid
from datetime import datetime, timezone
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import (
    LLM_PROVIDER,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
    GITHUB_TOKEN,
    GITHUB_MODELS_ENDPOINT,
    GITHUB_MODELS_DEPLOYMENT,
)

logger = logging.getLogger(__name__)

_llm_instance = None


def _get_llm():
    global _llm_instance
    if _llm_instance is None:
        if LLM_PROVIDER == "github":
            _llm_instance = ChatOpenAI(
                base_url=GITHUB_MODELS_ENDPOINT,
                api_key=GITHUB_TOKEN,
                model=GITHUB_MODELS_DEPLOYMENT,
                temperature=0.3,
            )
        else:
            _llm_instance = AzureChatOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_API_KEY,
                azure_deployment=AZURE_OPENAI_DEPLOYMENT,
                api_version=AZURE_OPENAI_API_VERSION,
                temperature=0.3,
            )
    return _llm_instance


# Module-level alias used by tests for patching
llm = None  # tests patch this directly; production uses _get_llm()


def _call_llm(messages: list) -> object:
    """Call the LLM — direct call for test mocks, .invoke() for real LangChain clients."""
    _llm = llm if llm is not None else _get_llm()
    try:
        return _llm(messages)
    except TypeError:
        return _llm.invoke(messages)


_ARTICLE_SYSTEM_PROMPT = """\
You are a neutral journalist writing a balanced news article that presents both \
left-leaning and right-leaning perspectives on the same story. \
Your writing must be factual, fair, and free of editorial bias. \
Return ONLY a JSON object with these exact keys:
  "headline": a single neutral headline (max 15 words)
  "lead": 1-2 factual sentences summarising what happened (no opinion)
  "left_perspective": 2-3 sentences conveying what left-leaning sources say
  "right_perspective": 2-3 sentences conveying what right-leaning sources say
  "common_ground": list of 1-3 short strings — claims both sides agree on
  "diverging_points": list of 1-3 short strings — where perspectives differ
Output valid JSON only. No markdown fences, no extra text."""


def _write_balanced_article(
    pair: dict,
    left_snippet: dict,
    right_snippet: dict,
) -> dict:
    """Ask the LLM to synthesise a balanced article from a left+right story pair."""
    human_content = (
        f"TOPIC: {pair.get('topic_label', 'News story')}\n\n"
        f"LEFT SOURCE ({left_snippet.get('source_label', '')}, "
        f"lean: {left_snippet.get('lean_label', '')}):\n"
        f"Title: {left_snippet.get('title', '')}\n"
        f"Summary: {left_snippet.get('summary_text', '')}\n"
        f"Key claims: {'; '.join(left_snippet.get('key_claims', []))}\n\n"
        f"RIGHT SOURCE ({right_snippet.get('source_label', '')}, "
        f"lean: {right_snippet.get('lean_label', '')}):\n"
        f"Title: {right_snippet.get('title', '')}\n"
        f"Summary: {right_snippet.get('summary_text', '')}\n"
        f"Key claims: {'; '.join(right_snippet.get('key_claims', []))}\n\n"
        f"Agreements already identified: {'; '.join(pair.get('agreements', []))}\n"
        f"Disagreements already identified: {'; '.join(pair.get('disagreements', []))}"
    )
    try:
        response = _call_llm([
            SystemMessage(content=_ARTICLE_SYSTEM_PROMPT),
            HumanMessage(content=human_content),
        ])
        data = json.loads(response.content)
        return {
            "article_id": str(uuid.uuid4()),
            "headline": str(data.get("headline", pair.get("topic_label", ""))),
            "topic_label": pair.get("topic_label", ""),
            "lead": str(data.get("lead", "")),
            "left_perspective": str(data.get("left_perspective", "")),
            "right_perspective": str(data.get("right_perspective", "")),
            "common_ground": list(data.get("common_ground", pair.get("agreements", []))),
            "diverging_points": list(data.get("diverging_points", pair.get("disagreements", []))),
            "left_source_label": left_snippet.get("source_label", ""),
            "right_source_label": right_snippet.get("source_label", ""),
            "left_lean_label": left_snippet.get("lean_label", ""),
            "right_lean_label": right_snippet.get("lean_label", ""),
            "match_confidence": pair.get("match_confidence", 0.0),
        }
    except Exception as exc:
        logger.warning("BalancedOutputAgent article writing failed for pair %s: %s",
                       pair.get("topic_label"), exc)
        # Fallback: construct article from existing data without LLM
        return {
            "article_id": str(uuid.uuid4()),
            "headline": pair.get("topic_label", ""),
            "topic_label": pair.get("topic_label", ""),
            "lead": (left_snippet.get("summary_text") or right_snippet.get("summary_text") or "")[:200],
            "left_perspective": left_snippet.get("summary_text", ""),
            "right_perspective": right_snippet.get("summary_text", ""),
            "common_ground": pair.get("agreements", []),
            "diverging_points": pair.get("disagreements", []),
            "left_source_label": left_snippet.get("source_label", ""),
            "right_source_label": right_snippet.get("source_label", ""),
            "left_lean_label": left_snippet.get("lean_label", ""),
            "right_lean_label": right_snippet.get("lean_label", ""),
            "match_confidence": pair.get("match_confidence", 0.0),
        }


def BalancedOutputAgent(state: dict) -> dict:
    """LangGraph node. Writes balanced articles for paired stories; formats the digest."""
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
            "link": "",
            "key_claims": b.get("key_claims", []),
        }

    # Sort paired stories by match_confidence descending
    sorted_pairs = sorted(matched_stories, key=lambda p: p.get("match_confidence", 0), reverse=True)

    articles = []
    paired_stories = []

    for pair in sorted_pairs:
        left_snippet = make_snippet(pair["left_article_id"])
        right_snippet = make_snippet(pair["right_article_id"])

        # Write the balanced article using the LLM
        article = _write_balanced_article(pair, left_snippet, right_snippet)
        articles.append(article)

        paired_stories.append({
            "topic_label": pair["topic_label"],
            "left": left_snippet,
            "right": right_snippet,
            "agreements": pair.get("agreements", []),
            "disagreements": pair.get("disagreements", []),
            "match_confidence": pair.get("match_confidence", 0.0),
        })

    left_only = [make_snippet(aid) for aid in unmatched_left]
    right_only = [make_snippet(aid) for aid in unmatched_right]

    balanced_digest = {
        "topic": topic,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "articles": articles,
        "paired_stories": paired_stories,
        "left_only_stories": left_only,
        "right_only_stories": right_only,
    }

    return {"balanced_digest": balanced_digest}
