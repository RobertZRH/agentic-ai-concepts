# SKILL: RightSourceFetcherAgent

## name
`right_fetcher`

## description
Fetches and parses news articles from RSS feeds of right-leaning and center-right publications. Produces a list of structured Article objects ready for downstream processing.

## domain
RSS feed retrieval, XML parsing, article metadata extraction. Operates only on publicly available RSS endpoints. Has no knowledge of article content beyond what is in the feed (title, summary, link, published date, source).

## inputs
| Field | Type | Description |
|---|---|---|
| `topic` | `str \| None` | Optional keyword filter. If provided, only articles whose title or summary contain this keyword are included. If `None`, all recent articles are returned. |

## outputs
| Field | Type | Description |
|---|---|---|
| `right_articles` | `list[Article]` | Parsed articles from right-leaning sources, max 10 per source. |

## tools_used
- `rss_reader.fetch_feed(url: str) -> list[RawEntry]`
- `rss_reader.parse_entry(entry: RawEntry, source_label: str) -> Article`

## rss_sources
| Label | Feed URL |
|---|---|
| Fox News | `https://moxie.foxnews.com/google-publisher/latest.xml` |
| WSJ Opinion | `https://feeds.a.dj.com/rss/RSSOpinion.xml` |
| NY Post | `https://nypost.com/feed/` |
| Breitbart | `http://feeds.feedburner.com/breitbart` |

## must_never
- Never filter out articles based on political content or tone
- Never modify article text, title, or summary
- Never fabricate articles or fill gaps with LLM-generated content
- Never use sources not listed in `rss_sources`
- Never raise an unhandled exception — return partial results if one feed fails

## error_behavior
If a feed is unreachable or returns malformed XML, log a warning and continue with the remaining feeds. The `right_articles` list must always be returned (may be empty).

## example_invocation
```
Given topic = "immigration"
When RightSourceFetcherAgent runs
Then right_articles contains articles from Fox News, WSJ, NY Post, and/or Breitbart
 And each article has title, summary, link, published_at, source_label
 And articles not mentioning "immigration" in title or summary are excluded
```

## related_spec
`specs/news_fetcher.feature` — Scenario: Fetch articles from right-leaning sources
