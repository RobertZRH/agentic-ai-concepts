# SKILL: ModeratorAgent

## name
`moderator`

## description
Groups related stories from left and right sources into matched pairs by finding articles that cover the same event or topic. Surfaces factual agreements and framing disagreements between the two perspectives. The `agreements`, `disagreements`, and `shared_entities` it produces are the primary inputs for the downstream `BalancedOutputAgent`, which uses them to write balanced published articles. Never suppresses or edits any article.

## domain
Story deduplication, named-entity overlap matching, cross-perspective comparison. Uses named-entity overlap as primary matching signal; falls back to embedding cosine similarity for ambiguous matches.

## inputs
| Field | Type | Description |
|---|---|---|
| `summaries` | `list[Summary]` | All summaries from both sides |
| `bias_scores` | `list[BiasScore]` | Bias analysis for each summary |

## outputs
| Field | Type | Description |
|---|---|---|
| `matched_stories` | `list[StoryPair]` | Paired left+right articles covering the same event |
| `unmatched_left` | `list[str]` | article_ids with no right-side match |
| `unmatched_right` | `list[str]` | article_ids with no left-side match |

## StoryPair schema
```python
class StoryPair(TypedDict):
    pair_id: str                  # uuid
    topic_label: str              # short topic description, e.g. "US-China Trade Tariffs"
    left_article_id: str
    right_article_id: str
    shared_entities: list[str]    # named entities present in both articles
    agreements: list[str]         # factual claims both sides share
    disagreements: list[str]      # claims or framing that differ
    match_confidence: float       # 0.0 to 1.0
```

## matching_algorithm
1. For each left article, compute named-entity overlap with all right articles using `BiasScore.named_entities`
2. Pair the left article with the right article that has the highest overlap score (Jaccard similarity ≥ 0.2)
3. If no pair meets the threshold, attempt embedding cosine similarity ≥ 0.75 as fallback
4. Articles with no match above either threshold go into `unmatched_left` / `unmatched_right`
5. Each article may appear in at most one StoryPair

## tools_used
- `llm` — Azure OpenAI GPT-5.5 (for `agreements` and `disagreements` extraction)
- Named-entity lists from `BiasScore.named_entities` (no additional NLP calls)
- Optional: `langchain_openai.AzureOpenAIEmbeddings` for fallback cosine similarity

## must_never
- Never suppress or exclude an article because of its political lean
- Never merge two left-side or two right-side articles into a pair
- Never fabricate `agreements` or `disagreements` not supported by the summaries
- Never assign `match_confidence > 1.0` or `< 0.0`
- Never modify the content of any Summary or BiasScore

## error_behavior
If LLM fails during agreements/disagreements extraction, set both fields to `[]` and `match_confidence` to the entity-overlap score only.

## example_invocation
```
Given summaries contains a CNN article and a Fox News article both mentioning "Federal Reserve" and "interest rates"
When ModeratorAgent runs
Then matched_stories contains a StoryPair linking those two articles
 And StoryPair.shared_entities includes "Federal Reserve"
 And StoryPair.match_confidence >= 0.2
 And neither article appears in unmatched_left or unmatched_right
```

## related_spec
`specs/moderator.feature`
