"""SummarizerAgent — condenses each article to a neutral 3-5 sentence summary."""
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


# Module-level alias used by tests for patching
llm = None  # tests patch this directly; production uses _get_llm()

_SYSTEM_PROMPT = (
    "You are a neutral summarizer. Summarize the following news article in 3-5 sentences. "
    "Preserve all factual claims, named entities, and dates. "
    "Do not add interpretation, opinion, or first-person language."
)


def SummarizerAgent(state: dict) -> dict:
    """LangGraph node. Reads left_articles + right_articles, writes summaries."""
    all_articles = state.get("left_articles", []) + state.get("right_articles", [])
    summaries = []

    for article in all_articles:
        text = f"Title: {article['title']}\n\n{article['summary']}"
        try:
            _llm = llm if llm is not None else _get_llm()
            response = _llm([SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=text)])
            summary_text = response.content.strip()
        except Exception as exc:
            logger.warning("Summarizer LLM failed for article %s: %s", article["id"], exc)
            summary_text = ""

        summaries.append({
            "article_id": article["id"],
            "source_label": article["source_label"],
            "lean": article["lean"],
            "original_title": article["title"],
            "summary_text": summary_text,
        })

    return {"summaries": summaries}
