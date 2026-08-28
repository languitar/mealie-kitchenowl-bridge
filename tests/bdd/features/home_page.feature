Feature: Home page
  As a visitor
  I want to load the bridge's home page in a browser
  So that I know the web UI is served correctly

  Scenario: The home page loads
    Given the bridge is running as a logged-in user
    When I open the home page
    Then I see the bridge's title
