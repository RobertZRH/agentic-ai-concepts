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


class BalancedDigest(TypedDict):
    topic: Optional[str]
    generated_at: str
    paired_stories: list[PairedStoryOutput]
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
