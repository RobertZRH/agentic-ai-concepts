"""Shared TypedDict schemas for the news aggregation pipeline state."""
from typing import TypedDict, Literal
from typing import Optional


class Article(TypedDict):
    id: str
    title: str
    summary: str
    link: str
    published_at: str
    source_label: str
    lean: Literal["left", "right"]


class Summary(TypedDict):
    article_id: str
    source_label: str
    lean: Literal["left", "right"]
    original_title: str
    summary_text: str


class BiasScore(TypedDict):
    article_id: str
    source_label: str
    lean_score: float
    lean_label: Literal["left", "center-left", "center", "center-right", "right"]
    key_claims: list[str]
    framing_notes: str
    named_entities: list[str]


class StoryPair(TypedDict):
    pair_id: str
    topic_label: str
    left_article_id: str
    right_article_id: str
    shared_entities: list[str]
    agreements: list[str]
    disagreements: list[str]
    match_confidence: float


class StorySnippet(TypedDict):
    source_label: str
    lean_label: str
    title: str
    summary_text: str
    link: str
    key_claims: list[str]


class PairedStoryOutput(TypedDict):
    topic_label: str
    left: StorySnippet
    right: StorySnippet
    agreements: list[str]
    disagreements: list[str]
    match_confidence: float


class BalancedArticle(TypedDict):
    """A fully written balanced article synthesised from a left+right story pair."""
    article_id: str
    headline: str               # Neutral headline written by the LLM
    topic_label: str            # Short topic label from the matched pair
    lead: str                   # 1-2 sentence factual lead paragraph
    left_perspective: str       # 2-3 sentences representing the left-leaning view
    right_perspective: str      # 2-3 sentences representing the right-leaning view
    common_ground: list[str]    # Claims both sides share
    diverging_points: list[str] # Where the perspectives diverge
    left_source_label: str
    right_source_label: str
    left_lean_label: str
    right_lean_label: str
    match_confidence: float


class BalancedDigest(TypedDict):
    topic: Optional[str]
    generated_at: str
    articles: list[BalancedArticle]          # Written balanced articles for paired stories
    paired_stories: list[PairedStoryOutput]  # Raw pair data (kept for API consumers)
    left_only_stories: list[StorySnippet]
    right_only_stories: list[StorySnippet]


class PipelineState(TypedDict, total=False):
    topic: Optional[str]
    left_articles: list[Article]
    right_articles: list[Article]
    summaries: list[Summary]
    bias_scores: list[BiasScore]
    matched_stories: list[StoryPair]
    unmatched_left: list[str]
    unmatched_right: list[str]
    balanced_digest: BalancedDigest
