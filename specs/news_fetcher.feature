Feature: News fetching from left and right RSS sources

  Background:
    Given the RSS reader tool is available

  Scenario: Fetch articles from left-leaning sources without a topic filter
    Given no topic filter is set
    When the LeftSourceFetcherAgent runs
    Then left_articles is a list
    And each article in left_articles has a non-empty title
    And each article in left_articles has a non-empty link
    And each article in left_articles has a source_label in ["CNN", "The Guardian", "NPR", "MSNBC"]
    And each article in left_articles has a lean of "left"

  Scenario: Fetch articles from left-leaning sources with a topic filter
    Given the topic is "climate"
    When the LeftSourceFetcherAgent runs
    Then every article in left_articles mentions "climate" in its title or summary

  Scenario: Fetch articles from right-leaning sources without a topic filter
    Given no topic filter is set
    When the RightSourceFetcherAgent runs
    Then right_articles is a list
    And each article in right_articles has a non-empty title
    And each article in right_articles has a non-empty link
    And each article in right_articles has a source_label in ["Fox News", "WSJ Opinion", "NY Post", "Breitbart"]
    And each article in right_articles has a lean of "right"

  Scenario: Fetch articles from right-leaning sources with a topic filter
    Given the topic is "immigration"
    When the RightSourceFetcherAgent runs
    Then every article in right_articles mentions "immigration" in its title or summary

  Scenario: One RSS feed is unreachable
    Given the topic is "economy"
    And the CNN feed is configured to return a connection error
    When the LeftSourceFetcherAgent runs
    Then left_articles still contains articles from other left-leaning sources
    And no exception is raised

  Scenario: No articles match the topic filter
    Given the topic is "xyzzy_nonexistent_topic_12345"
    When the LeftSourceFetcherAgent runs
    Then left_articles is an empty list
    And no exception is raised
