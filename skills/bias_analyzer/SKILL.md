# SKILL: BiasAnalyzerAgent

## name
`bias_analyzer`

## description
Analyzes each article summary to detect political framing, extract key claims, and assign a numeric political lean score. Operates analytically — it identifies framing patterns without endorsing or suppressing any perspective.

## domain
Political framing analysis, named-entity recognition, claim extraction. Uses GPT-5.5 to detect linguistic signals of political lean (e.g. word choice, framing of issues, which entities are cast as protagonists vs antagonists).

## inputs
| Field | Type | Description |
|---|---|---|
| `summaries` | `list[Summary]` | Summarized articles from both sides |

## outputs
| Field | Type | Description |
|---|---|---|
| `bias_scores` | `list[BiasScore]` | One `BiasScore` per Summary |

## BiasScore schema
```python
class BiasScore(TypedDict):
    article_id: str            # matches Summary.article_id
    source_label: str
    lean_score: float          # -1.0 (far left) to +1.0 (far right), 0.0 = neutral
    lean_label: Literal["left", "center-left", "center", "center-right", "right"]
    key_claims: list[str]      # up to 5 factual or interpretive claims extracted
    framing_notes: str         # 1-2 sentences describing framing signals detected
    named_entities: list[str]  # people, orgs, places mentioned
```

## lean_label mapping
| lean_score range | lean_label |
|---|---|
| -1.0 to -0.6 | `left` |
| -0.6 to -0.2 | `center-left` |
| -0.2 to +0.2 | `center` |
| +0.2 to +0.6 | `center-right` |
| +0.6 to +1.0 | `right` |

## tools_used
- `llm` — Azure OpenAI GPT-5.5
- System prompt: *"You are a political framing analyst. Given a news summary, output: (1) a lean_score from -1.0 (strongly left) to +1.0 (strongly right), (2) up to 5 key claims, (3) a framing_notes sentence, (4) named entities. Be analytical and consistent. Do not advocate for any political position."*

## must_never
- Never assign a score with the intent to discredit or favor any source
- Never fabricate key_claims not present in the summary
- Never produce a lean_score outside the range [-1.0, +1.0]
- Never omit a BiasScore for any input Summary
- Never use lean_score to filter or suppress articles downstream

## error_behavior
If LLM fails for a specific summary, return a BiasScore with `lean_score=0.0`, `lean_label="center"`, `key_claims=[]`, `framing_notes="Analysis unavailable."`.

## example_invocation
```
Given summaries contains a CNN article about "border policy"
When BiasAnalyzerAgent runs
Then bias_scores contains a BiasScore for that article
 And BiasScore.lean_score is between -1.0 and +1.0
 And BiasScore.key_claims has at most 5 entries
 And BiasScore.lean_label matches the lean_score range
```

## related_spec
`specs/bias_analyzer.feature`
