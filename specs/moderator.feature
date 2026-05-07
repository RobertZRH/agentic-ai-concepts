Feature: Story moderation and cross-perspective matching

  Background:
    Given summaries and bias_scores are populated with matching article_ids

  Scenario: Matching stories from both sides are paired
    Given a left Summary about "Federal Reserve" mentioning entities ["Federal Reserve", "Jerome Powell", "interest rates"]
    And a right Summary about "Federal Reserve" mentioning entities ["Federal Reserve", "Jerome Powell", "inflation"]
    When the ModeratorAgent runs
    Then matched_stories contains 1 StoryPair
    And the StoryPair.shared_entities includes "Federal Reserve"
    And the StoryPair.match_confidence is greater than 0.0
    And neither article appears in unmatched_left or unmatched_right

  Scenario: Unrelated articles are not paired
    Given a left Summary about "climate policy" with entities ["EPA", "carbon emissions"]
    And a right Summary about "immigration" with entities ["border patrol", "asylum seekers"]
    When the ModeratorAgent runs
    Then matched_stories is empty
    And the left article appears in unmatched_left
    And the right article appears in unmatched_right

  Scenario: Each article appears in at most one pair
    Given 3 left summaries and 3 right summaries where all share "NATO" as an entity
    When the ModeratorAgent runs
    Then no article_id appears in more than one StoryPair

  Scenario: Agreements and disagreements are extracted for paired stories
    Given a matched StoryPair with overlapping content about "trade tariffs"
    When the ModeratorAgent runs
    Then the StoryPair.agreements is a list (may be empty)
    And the StoryPair.disagreements is a list (may be empty)

  Scenario: LLM failure during agreement extraction
    Given a valid StoryPair match
    And the LLM call for agreements/disagreements fails
    When the ModeratorAgent runs
    Then the StoryPair.agreements is an empty list
    And the StoryPair.disagreements is an empty list
    And the StoryPair.match_confidence equals the entity overlap score
    And no exception is raised

  Scenario: Fallback to embedding similarity when entity overlap is below threshold
    Given a left Summary and right Summary covering the same event with few shared entity names
    And the entity overlap Jaccard similarity is below 0.2
    And the embedding cosine similarity between the summaries is 0.82
    When the ModeratorAgent runs
    Then matched_stories contains 1 StoryPair
    And the StoryPair.match_confidence is approximately 0.82
