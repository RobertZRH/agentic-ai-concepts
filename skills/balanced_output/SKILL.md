# SKILL: BalancedOutputAgent

## name
`balanced_output`

## description
Writes a fully-formed **balanced news article** for each matched story pair using an LLM, then assembles the complete balanced digest. Each article presents a neutral headline, a factual lead, and two distinct perspective sections — one for the left-leaning source and one for the right-leaning source — drawn from the upstream summaries, bias scores, and moderator analysis. Unmatched articles are still included in the digest as raw snippets.

## domain
LLM-powered article synthesis and report assembly. This is the final publishing agent — it produces the human-readable output delivered to the consumer.

## inputs
| Field | Type | Description |
|---|---|---|
| `matched_stories` | `list[StoryPair]` | Paired left+right articles |
| `unmatched_left` | `list[str]` | article_ids with no right-side match |
| `unmatched_right` | `list[str]` | article_ids with no left-side match |
| `summaries` | `list[Summary]` | All summaries (needed to look up unmatched articles) |
| `bias_scores` | `list[BiasScore]` | All bias scores (for lean_label display) |
| `topic` | `str \| None` | The topic filter used, for digest header |

## outputs
| Field | Type | Description |
|---|---|---|
| `balanced_digest` | `BalancedDigest` | The final structured digest containing written articles |

## BalancedDigest schema
```python
class BalancedArticle(TypedDict):
    article_id: str             # uuid
    headline: str               # neutral headline written by the LLM (max 15 words)
    topic_label: str            # short topic label from the matched pair
    lead: str                   # 1-2 sentence factual lead paragraph
    left_perspective: str       # 2-3 sentences: what left-leaning sources say
    right_perspective: str      # 2-3 sentences: what right-leaning sources say
    common_ground: list[str]    # claims both sides agree on
    diverging_points: list[str] # where the perspectives differ
    left_source_label: str
    right_source_label: str
    left_lean_label: str
    right_lean_label: str
    match_confidence: float

class BalancedDigest(TypedDict):
    topic: str | None
    generated_at: str                    # ISO 8601 datetime
    articles: list[BalancedArticle]      # LLM-written balanced articles
    paired_stories: list[PairedStoryOutput]  # raw pair data (kept for API consumers)
    left_only_stories: list[StorySnippet]
    right_only_stories: list[StorySnippet]
```

## article_writing_prompt
System: *"You are a neutral journalist writing a balanced news article that presents both
left-leaning and right-leaning perspectives on the same story. Return ONLY a JSON object
with keys: headline, lead, left_perspective, right_perspective, common_ground (list),
diverging_points (list)."*

Human message includes:
- `TOPIC`, `LEFT SOURCE` (source_label, lean_label, title, summary_text, key_claims)
- `RIGHT SOURCE` (same fields)
- Agreements and disagreements already identified by the ModeratorAgent

## formatting_rules
1. `articles` and `paired_stories` are sorted by `match_confidence` descending
2. `left_only_stories` and `right_only_stories` are included in full
3. `generated_at` uses `datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")`
4. One LLM call is made per matched pair

## tools_used
- `llm` — GitHub Models / Azure OpenAI (same lazy `_get_llm()` pattern as other agents)

## must_never
- Never omit an article for a StoryPair
- Never omit unmatched articles from `left_only_stories` / `right_only_stories`
- Never fabricate facts not present in upstream summaries or bias scores
- Never raise an exception — fall back to snippet data if LLM call fails

## error_behavior
If the LLM call fails for a pair, produce a fallback `BalancedArticle` using the existing
snippet data (topic_label as headline, summary_text as lead/perspectives, moderator
agreements/disagreements). If a `Summary` or `BiasScore` lookup fails, use `"[data unavailable]"`.

## example_invocation
```
Given matched_stories has 1 StoryPair with left_article_id and right_article_id
When BalancedOutputAgent runs
Then balanced_digest.articles has 1 entry
 And balanced_digest.articles[0].headline is non-empty
 And balanced_digest.articles[0].left_perspective is non-empty
 And balanced_digest.articles[0].right_perspective is non-empty
 And balanced_digest.generated_at is a valid ISO 8601 string
```

## related_spec
`specs/orchestrator.feature` — Scenario: BalancedOutputAgent writes a balanced article per story pair
