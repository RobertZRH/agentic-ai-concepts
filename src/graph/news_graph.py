"""LangGraph news pipeline — wires all agents into a state machine."""
from langgraph.graph import StateGraph, START, END
from src.models.state import PipelineState
from src.agents.left_fetcher import LeftSourceFetcherAgent
from src.agents.right_fetcher import RightSourceFetcherAgent
from src.agents.summarizer import SummarizerAgent
from src.agents.bias_analyzer import BiasAnalyzerAgent
from src.agents.moderator import ModeratorAgent
from src.agents.balanced_output import BalancedOutputAgent


def _merge_fetcher_outputs(state: PipelineState) -> PipelineState:
    """No-op fan-in node — LangGraph requires a node after parallel branches."""
    return {}


def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    # Nodes
    graph.add_node("left_fetcher", LeftSourceFetcherAgent)
    graph.add_node("right_fetcher", RightSourceFetcherAgent)
    graph.add_node("summarizer", SummarizerAgent)
    graph.add_node("bias_analyzer", BiasAnalyzerAgent)
    graph.add_node("moderator", ModeratorAgent)
    graph.add_node("balanced_output", BalancedOutputAgent)

    # Parallel fetch from START
    graph.add_edge(START, "left_fetcher")
    graph.add_edge(START, "right_fetcher")

    # Both fetchers feed into summarizer (LangGraph merges state automatically)
    graph.add_edge("left_fetcher", "summarizer")
    graph.add_edge("right_fetcher", "summarizer")

    # Sequential pipeline
    graph.add_edge("summarizer", "bias_analyzer")
    graph.add_edge("bias_analyzer", "moderator")
    graph.add_edge("moderator", "balanced_output")
    graph.add_edge("balanced_output", END)

    return graph.compile()


if __name__ == "__main__":
    import json

    pipeline = build_graph()
    result = pipeline.invoke({"topic": "economy"})
    digest = result.get("balanced_digest", {})
    print(json.dumps(digest, indent=2))
