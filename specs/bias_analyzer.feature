Feature: Bias analysis

  Background:
    Given the LLM client is available
    And summaries contains at least 1 Summary

  Scenario: Bias score produced for every summary
    Given summaries contains 4 Summary objects
    When the BiasAnalyzerAgent runs
    Then bias_scores contains exactly 4 BiasScore objects
    And each BiasScore.article_id matches a Summary.article_id

  Scenario: Lean score is within valid range
    Given summaries contains 3 Summary objects
    When the BiasAnalyzerAgent runs
    Then each BiasScore.lean_score is between -1.0 and 1.0 inclusive

  Scenario: Lean label matches lean score range
    Given a Summary with a lean_score of -0.8 after analysis
    When the BiasAnalyzerAgent runs
    Then the BiasScore.lean_label is "left"

  Scenario: Lean label for center score
    Given a Summary expected to score near 0.0
    When the BiasAnalyzerAgent runs
    Then the BiasScore.lean_label is "center"

  Scenario: Key claims are extracted
    Given a Summary about "tariff policy" with multiple factual claims
    When the BiasAnalyzerAgent runs
    Then the BiasScore.key_claims has at most 5 entries
    And each entry in key_claims is a non-empty string

  Scenario: LLM fails for one summary
    Given summaries contains 4 Summary objects
    And the LLM call fails for the third summary
    When the BiasAnalyzerAgent runs
    Then bias_scores contains exactly 4 BiasScore objects
    And the failed article's BiasScore.lean_score is 0.0
    And the failed article's BiasScore.lean_label is "center"
    And no exception is raised
