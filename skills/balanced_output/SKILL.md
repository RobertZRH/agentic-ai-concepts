# SKILL: BalancedOutputAgent

## name
`balanced_output`

## description
Formats the matched story pairs and unmatched articles into a structured, human-readable balanced news digest. Presents both perspectives side-by-side with no editorial preference. The output is the final artifact delivered to the consumer.

## domain
Report formatting, structured output generation. Has no analysis or judgment responsibilities — it only formats what the upstream agents produced.

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
| `balanced_digest` | `BalancedDigest` | The final structured digest |

## BalancedDigest schema
```python
class BalancedDigest(TypedDict):
    topic: str | None
    generated_at: str            # ISO 8601 datetime
    paired_stories: list[PairedStoryOutput]
    left_only_stories: list[StorySnippet]
    right_only_stories: list[StorySnippet]

class PairedStoryOutput(TypedDict):
    topic_label: str
    left: StorySnippet
    right: StorySnippet
    agreements: list[str]
    disagreements: list[str]

class StorySnippet(TypedDict):
    source_label: str            # e.g. "CNN"
    lean_label: str              # e.g. "center-left"
    title: str
    summary_text: str
    link: str
    key_claims: list[str]
```

## formatting_rules
1. `paired_stories` are sorted by `match_confidence` descending
2. Within each pair, left-source is always listed before right-source (alphabetical by lean)
3. `left_only_stories` and `right_only_stories` are included in full — not hidden or summarized further
4. `generated_at` uses `datetime.utcnow().isoformat() + "Z"`
5. No LLM calls — this agent is pure data transformation

## tools_used
None — pure Python data transformation only. No LLM calls.

## must_never
- Never omit a StoryPair from `paired_stories`
- Never omit unmatched articles — they must appear in `left_only_stories` or `right_only_stories`
- Never editorialize, annotate, or add text not present in upstream agent outputs
- Never reorder `agreements` or `disagreements` in a way that changes meaning
- Never make LLM calls

## error_behavior
If a `Summary` or `BiasScore` lookup by `article_id` fails, use `"[data unavailable]"` for the missing field. Never raise an exception.

## example_invocation
```
Given matched_stories has 4 StoryPairs and 2 unmatched_left and 1 unmatched_right
When BalancedOutputAgent runs
Then balanced_digest.paired_stories has 4 entries
 And balanced_digest.left_only_stories has 2 entries
 And balanced_digest.right_only_stories has 1 entry
 And balanced_digest.generated_at is a valid ISO 8601 string
 And no LLM calls are made
```

## related_spec
`specs/orchestrator.feature` — Scenario: Full pipeline produces balanced digest
