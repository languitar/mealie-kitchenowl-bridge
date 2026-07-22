Feature: Health check
  As an operator running the bridge
  I want a health endpoint
  So that I can verify the service is up

  Scenario: The service reports healthy
    Given the bridge is running
    When I request the health endpoint
    Then the response indicates the service is healthy
