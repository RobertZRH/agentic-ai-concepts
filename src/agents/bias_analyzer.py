"""BiasAnalyzerAgent — scores political lean and extracts key claims per article."""
import json
import logging
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

_SYSTEM_PROMPT = (
    "You are a political framing analyst. Given a news summary, respond with a JSON object "
    "containing exactly these fields:\n"
    "  lean_score: float from -1.0 (strongly left) to +1.0 (strongly right)\n"
    "  key_claims: list of up to 5 factual or interpretive claims (strings)\n"
    "  framing_notes: 1-2 sentences describing framing signals detected\n"
    "  named_entities: list of people, organisations, and places mentioned\n"
    "Be analytical and consistent. Do not advocate for any political position. "
    "Respond with valid JSON only."
)

_LEAN_THRESHOLDS = [
    (-1.0, -0.6, "left"),
    (-0.6, -0.2, "center-left"),
    (-0.2, 0.2, "center"),
    (0.2, 0.6, "center-right"),
    (0.6, 1.01, "right"),
]

_FALLBACK_SCORE = {
    "lean_score": 0.0,
    "lean_label": "center",
    "key_claims": [],
    "framing_notes": "Analysis unavailable.",
    "named_entities": [],
}


def _score_to_label(score: float) -> str:
    for low, high, label in _LEAN_THRESHOLDS:
        if low <= score < high:
            return label
    return "center"


def BiasAnalyzerAgent(state: dict) -> dict:
    """LangGraph node. Reads summaries, writes bias_scores."""
    bias_scores = []

    for summary in state.get("summaries", []):
        try:
            response = _call_llm([
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=summary["summary_text"] or summary["original_title"]),
            ])
            data = json.loads(response.content)
            lean_score = float(data.get("lean_score", 0.0))
            lean_score = max(-1.0, min(1.0, lean_score))
            bias_scores.append({
                "article_id": summary["article_id"],
                "source_label": summary["source_label"],
                "lean_score": lean_score,
                "lean_label": _score_to_label(lean_score),
                "key_claims": data.get("key_claims", [])[:5],
                "framing_notes": data.get("framing_notes", ""),
                "named_entities": data.get("named_entities", []),
            })
        except Exception as exc:
            logger.warning("BiasAnalyzer failed for article %s: %s", summary["article_id"], exc)
            bias_scores.append({
                "article_id": summary["article_id"],
                "source_label": summary["source_label"],
                **_FALLBACK_SCORE,
            })

    return {"bias_scores": bias_scores}
