Feature: Remote Job Matching and Resume Scoring
  As a job seeker
  I want to parse my resume, crawl multiple remote job boards, and filter out low-paying listings
  So that I can evaluate the best matching jobs on a dashboard ranked by ATS match score.

  Background:
    Given my local Ollama instance is running
    And I have a valid PDF resume file at "resume.pdf"
    And I have configured a JSearch API key in ".env"

  Scenario: Crawling, filtering by salary, and rating jobs
    Given the remote job feeds have listings:
      | Title             | Company     | Source            | Salary Range        |
      | Python Developer  | Tech Corp   | We Work Remotely  | $160,000 - $180,000 |
      | QA Engineer       | Test Labs   | Remotive          | $110,000 - $130,000 |
      | Software Engineer | Dev Shop    | Arbeitnow         | Not Specified       |
      | ML Engineer       | AI Labs     | The Muse          | $170,000 - $220,000 |
    When I run the matching agent with query "Python, ML" and max evaluation limit of 2
    Then the agent should crawl jobs from We Work Remotely, Remotive, Arbeitnow, The Muse, and JSearch
    And the agent should filter listings by title matching "Python" or "ML"
    And the agent should evaluate matching listings against the $150k salary threshold
    And only the "Python Developer" and "ML Engineer" jobs should pass the salary filter
    And the agent should evaluate those 2 passed jobs against my resume using the ATS scorer
    And a date-stamped HTML dashboard should be generated
    And the dashboard should display the matching jobs sorted by score

  Scenario: Handling empty matches gracefully
    Given the remote job feeds do not contain any listings matching "Golang Developer"
    When I run the matching agent with query "Golang Developer"
    Then the agent should skip the salary evaluation and ATS scoring phases
    And a dashboard should be generated showing no job matches found
