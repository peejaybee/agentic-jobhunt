Feature: Remote Job Matching and Resume Scoring
  As a job seeker
  I want to parse my resume, crawl multiple remote job boards, and filter out low-paying listings
  So that I can evaluate the best matching jobs on a dashboard ranked by ATS match score.

  Background:
    Given my local Ollama instance is running
    And I have a valid PDF resume file at "resume.pdf"
    And I have configured a JSearch API key in ".env"

  Scenario: Crawling, filtering by salary, and rating jobs with custom parameters
    Given the remote job feeds have listings:
      | Title             | Company     | Source            | Salary Range        |
      | Python Developer  | Tech Corp   | We Work Remotely  | $160,000 - $180,000 |
      | QA Engineer       | Test Labs   | Remotive          | $110,000 - $130,000 |
      | Software Engineer | Dev Shop    | Arbeitnow         | Not Specified       |
      | ML Engineer       | AI Labs     | The Muse          | $130,000 - $145,000 |
    When I run the matching agent with query "Python, ML", max eval 2, min salary 120000, concurrency 2, and description limit 4000
    Then the agent should crawl jobs from We Work Remotely, Remotive, Arbeitnow, The Muse, and JSearch
    And the agent should query search APIs using the query "Python, ML"
    And the agent should evaluate matching listings against the $120k salary threshold with a concurrency cap of 2
    And only the "Python Developer" and "ML Engineer" jobs should pass the salary filter
    And the agent should evaluate those 2 passed jobs against my resume using the ATS scorer with descriptions truncated to 4000 characters
    And a date-stamped HTML dashboard should be generated
    And the dashboard should display the matching jobs sorted by score

  Scenario: Handling empty matches gracefully
    Given the remote job feeds do not contain any listings matching "Golang Developer"
    When I run the matching agent with query "Golang Developer"
    Then the agent should skip the salary evaluation and ATS scoring phases
    And a dashboard should be generated showing no job matches found

  Scenario: Excluding employers listed in excluded_employers.txt
    Given my exclusion file "excluded_employers.txt" contains "lemon.io"
    And the remote job feeds have listings:
      | Title             | Company     | Source            | Salary Range        |
      | Python Developer  | Lemon.io    | We Work Remotely  | $160,000 - $180,000 |
      | Python Developer  | Tech Corp   | We Work Remotely  | $160,000 - $180,000 |
    When I run the matching agent with query "Python"
    Then the agent should ignore the listing from "Lemon.io"
    And only the listing from "Tech Corp" should be evaluated against the salary and ATS criteria

  Scenario: Self-correcting malformed LLM JSON output
    Given the local LLM returns a malformed JSON block on the first attempt
    When the agent evaluates a job listing
    Then the agent should detect the JSON parsing error
    And the agent should query the LLM again with the syntax error and corrective instructions under the same session ID
    And the agent should successfully extract the valid JSON results on a subsequent retry attempt

