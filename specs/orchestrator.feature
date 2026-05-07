Feature: End-to-end orchestration and balanced digest output

  Background:
    Given the LangGraph news pipeline is initialized
    And the LLM client is available
    And the RSS reader tool is available

  Scenario: Full pipeline produces a balanced digest
    Given the topic is "economy"
    When the full news pipeline runs
    Then balanced_digest is not None
    And balanced_digest.topic is "economy"
    And balanced_digest.generated_at is a valid ISO 8601 datetime string
    And balanced_digest.paired_stories is a list
    And balanced_digest.left_only_stories is a list
    And balanced_digest.right_only_stories is a list

  Scenario: Paired stories appear in digest with both perspectives
    Given the topic is "trade"
    And the pipeline produces at least 1 StoryPair
    When the full news pipeline runs
    Then each entry in balanced_digest.paired_stories has a non-empty left story
    And each entry in balanced_digest.paired_stories has a non-empty right story
    And each entry in balanced_digest.paired_stories has a topic_label

  Scenario: Unmatched articles are not lost
    Given the topic is "local elections"
    And 2 left articles have no matching right article
    And 1 right article has no matching left article
    When the full news pipeline runs
    Then balanced_digest.left_only_stories is a list
    And balanced_digest.right_only_stories is a list

  Scenario: Paired stories are sorted by match confidence descending
    Given the pipeline produces 3 StoryPairs with match_confidence values [0.3, 0.9, 0.6]
    When the full news pipeline runs
    Then balanced_digest.paired_stories are ordered [0.9, 0.6, 0.3]

  Scenario: No LLM calls are made in the BalancedOutputAgent
    Given the pipeline has completed Moderator stage
    When the BalancedOutputAgent runs
    Then no LLM API calls are recorded during BalancedOutputAgent execution

  Scenario: Pipeline handles all feeds being unreachable
    Given all RSS feeds return connection errors
    When the full news pipeline runs
    Then balanced_digest.paired_stories is an empty list
    And balanced_digest.left_only_stories is an empty list
    And balanced_digest.right_only_stories is an empty list
    And no exception propagates to the caller

  Scenario: Pipeline state fields are all populated after completion
    Given the topic is "healthcare"
    When the full news pipeline runs
    Then the pipeline state contains left_articles
    And the pipeline state contains right_articles
    And the pipeline state contains summaries
    And the pipeline state contains bias_scores
    And the pipeline state contains matched_stories
    And the pipeline state contains balanced_digest
