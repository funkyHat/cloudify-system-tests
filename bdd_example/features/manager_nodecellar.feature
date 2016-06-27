@manager @slow
Feature: testing_nodecellar_on_a_manager

    Background:
        Given I have a manager
        And I clone the repo 'https://github.com/geokala/cloudify-nodecellar-example.git' into 'nodecellar'
        And I check out the branch 'CFY-5048-aws-vpc-nodecellar'
        And I deploy a 'nodecellar' blueprint with the ID 'nodecellar-1'

    Scenario: Check the monitoring data
        When I look up the monitoring data for the deployment
        Then monitoring data is present

    Scenario: Check the nodecellar is available
        When I retrieve the host and IP from the deployment
        And I visit the nodecellar URL
        Then I see the nodecellar front page
