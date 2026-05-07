"""ModeratorAgent — matches related stories from both sides and surfaces agreements/disagreements."""
import json
import logging
import uuid
from typing import Optional

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
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
                temperature=0,
            )
        else:
            _llm_instance = AzureChatOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_API_KEY,
                azure_deployment=AZURE_OPENAI_DEPLOYMENT,
                api_version=AZURE_OPENAI_API_VERSION,
                temperature=0,
            )
    return _llm_instance


llm = None  # tests patch this directly; production uses _get_llm()


def _call_llm(messages: list) -> object:
    """Call the LLM — direct call for test mocks, .invoke() for real LangChain clients."""
    _llm = llm if llm is not None else _get_llm()
    try:
        return _llm(messages)
    except TypeError:
        return _llm.invoke(messages)

_AGREEMENT_PROMPT = (
    "You are a news moderation assistant. Given two news summaries on the same topic — "
    "one from a left-leaning source and one from a right-leaning source — identify:\n"
    "  agreements: list of factual claims both articles share\n"
    "  disagreements: list of claims or framings that differ between the articles\n"
    "Respond with valid JSON only, using exactly the keys 'agreements' and 'disagreements'."
)

ENTITY_OVERLAP_THRESHOLD = 0.2
EMBEDDING_SIMILARITY_THRESHOLD = 0.75


def _jaccard(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def compute_embedding_similarity(text_a: str, text_b: str) -> float:
    """Compute cosine similarity between two text embeddings via Azure OpenAI."""
    from langchain_openai import AzureOpenAIEmbeddings
    import numpy as np

    embedder = AzureOpenAIEmbeddings(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        azure_deployment="text-embedding-3-large",
        api_version=AZURE_OPENAI_API_VERSION,
    )
    vecs = embedder.embed_documents([text_a, text_b])
    a, b = vecs[0], vecs[1]
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x ** 2 for x in a) ** 0.5
    norm_b = sum(x ** 2 for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _extract_agreements(left_summary: str, right_summary: str) -> tuple[list[str], list[str]]:
    try:
        response = _call_llm([
            SystemMessage(content=_AGREEMENT_PROMPT),
            HumanMessage(content=f"LEFT:\n{left_summary}\n\nRIGHT:\n{right_summary}"),
        ])
        data = json.loads(response.content)
        return data.get("agreements", []), data.get("disagreements", [])
    except Exception as exc:
        logger.warning("ModeratorAgent agreement extraction failed: %s", exc)
        return [], []


def ModeratorAgent(state: dict) -> dict:
    """LangGraph node. Reads summaries + bias_scores, writes matched_stories, unmatched_left, unmatched_right."""
    summaries = state.get("summaries", [])
    bias_scores = state.get("bias_scores", [])

    # Build lookup maps
    bias_by_id = {b["article_id"]: b for b in bias_scores}
    summary_by_id = {s["article_id"]: s for s in summaries}

    left_ids = [s["article_id"] for s in summaries if s["lean"] == "left"]
    right_ids = [s["article_id"] for s in summaries if s["lean"] == "right"]

    matched_stories = []
    used_left: set[str] = set()
    used_right: set[str] = set()

    for l_id in left_ids:
        left_entities = set(bias_by_id.get(l_id, {}).get("named_entities", []))
        best_right_id: Optional[str] = None
        best_confidence = 0.0

        for r_id in right_ids:
            if r_id in used_right:
                continue
            right_entities = set(bias_by_id.get(r_id, {}).get("named_entities", []))
            overlap = _jaccard(left_entities, right_entities)
            if overlap > best_confidence:
                best_confidence = overlap
                best_right_id = r_id

        # Fall back to embedding similarity if entity overlap is below threshold
        if best_confidence < ENTITY_OVERLAP_THRESHOLD and best_right_id is None:
            left_text = summary_by_id.get(l_id, {}).get("summary_text", "")
            best_embed_id: Optional[str] = None
            best_embed_sim = 0.0
            for r_id in right_ids:
                if r_id in used_right:
                    continue
                right_text = summary_by_id.get(r_id, {}).get("summary_text", "")
                try:
                    sim = compute_embedding_similarity(left_text, right_text)
                except Exception:
                    sim = 0.0
                if sim > best_embed_sim:
                    best_embed_sim = sim
                    best_embed_id = r_id
            if best_embed_sim >= EMBEDDING_SIMILARITY_THRESHOLD:
                best_right_id = best_embed_id
                best_confidence = best_embed_sim

        if best_right_id and best_confidence >= ENTITY_OVERLAP_THRESHOLD:
            left_entities = set(bias_by_id.get(l_id, {}).get("named_entities", []))
            right_entities = set(bias_by_id.get(best_right_id, {}).get("named_entities", []))
            shared = sorted(left_entities & right_entities)

            left_text = summary_by_id.get(l_id, {}).get("summary_text", "")
            right_text = summary_by_id.get(best_right_id, {}).get("summary_text", "")
            agreements, disagreements = _extract_agreements(left_text, right_text)

            left_title = summary_by_id.get(l_id, {}).get("original_title", "")
            right_title = summary_by_id.get(best_right_id, {}).get("original_title", "")
            topic_label = shared[0] if shared else left_title[:40]

            matched_stories.append({
                "pair_id": str(uuid.uuid4()),
                "topic_label": topic_label,
                "left_article_id": l_id,
                "right_article_id": best_right_id,
                "shared_entities": shared,
                "agreements": agreements,
                "disagreements": disagreements,
                "match_confidence": round(best_confidence, 4),
            })
            used_left.add(l_id)
            used_right.add(best_right_id)

    unmatched_left = [i for i in left_ids if i not in used_left]
    unmatched_right = [i for i in right_ids if i not in used_right]

    return {
        "matched_stories": matched_stories,
        "unmatched_left": unmatched_left,
        "unmatched_right": unmatched_right,
    }
