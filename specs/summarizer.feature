Feature: Article summarization

  Background:
    Given the LLM client is available

  Scenario: Summarize a batch of mixed articles
    Given left_articles contains 5 articles
    And right_articles contains 4 articles
    When the SummarizerAgent runs
    Then summaries contains exactly 9 Summary objects
    And each Summary has a non-empty summary_text
    And each Summary.article_id matches an article in left_articles or right_articles
    And each Summary.source_label matches the source of its article

  Scenario: Summary length is within bounds
    Given left_articles contains 1 article
    And right_articles contains 0 articles
    When the SummarizerAgent runs
    Then summaries contains exactly 1 Summary
    And the Summary.summary_text contains between 1 and 5 sentences

  Scenario: Summary does not introduce new named entities
    Given a left article about "Federal Reserve interest rate decision" from "NPR"
    When the SummarizerAgent runs
    Then the resulting Summary.summary_text does not contain first-person language
    And the resulting Summary.summary_text does not contain phrases like "I think" or "in my opinion"

  Scenario: LLM fails for one article
    Given left_articles contains 3 articles
    And right_articles contains 2 articles
    And the LLM call fails for the second left article
    When the SummarizerAgent runs
    Then summaries contains exactly 5 Summary objects
    And the failed article's Summary.summary_text is an empty string
    And no exception is raised
