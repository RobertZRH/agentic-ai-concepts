# SKILL: SummarizerAgent

## name
`summarizer`

## description
Condenses each raw article into a concise, neutral 3-5 sentence summary using GPT-5.5. Preserves factual claims and key named entities. Does not interpret or editorialize.

## domain
Natural language summarization. Processes articles from both left and right sources identically — source political lean is never considered during summarization.

## inputs
| Field | Type | Description |
|---|---|---|
| `left_articles` | `list[Article]` | Articles from left-leaning sources |
| `right_articles` | `list[Article]` | Articles from right-leaning sources |

## outputs
| Field | Type | Description |
|---|---|---|
| `summaries` | `list[Summary]` | One `Summary` per input article, preserving `article_id` and `source_label` |

## tools_used
- `llm` — Azure OpenAI GPT-5.5 (`AzureChatOpenAI`)
- System prompt: *"You are a neutral summarizer. Summarize the following news article in 3-5 sentences. Preserve all factual claims, named entities, and dates. Do not add interpretation or opinion."*

## Summary schema
```python
class Summary(TypedDict):
    article_id: str       # matches Article.id
    source_label: str     # e.g. "CNN", "Fox News"
    lean: Literal["left", "right"]
    original_title: str
    summary_text: str     # 3-5 sentences
```

## must_never
- Never alter named entities, dates, or quoted figures in the summary
- Never add opinions, predictions, or context not present in the original article
- Never skip an article — every input article must produce exactly one Summary
- Never apply different summarization behavior based on source political lean
- Never exceed 5 sentences in `summary_text`

## error_behavior
If the LLM call fails for a specific article, produce a Summary with `summary_text = ""` and log a warning. Do not abort the entire batch.

## example_invocation
```
Given left_articles has 8 articles and right_articles has 7 articles
When SummarizerAgent runs
Then summaries contains exactly 15 Summary objects
 And each Summary.article_id matches an Article.id from the input
 And each Summary.summary_text is between 1 and 5 sentences
 And no Summary.summary_text contains first-person opinion language
```

## related_spec
`specs/summarizer.feature`
