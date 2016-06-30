@manager @slow
Feature: testing_nodecellar_on_a_manager

    Background:
        Given I have a manager
        And I create inputs file 'inputs.yaml' with inputs
            """
            vpc_id: vpc-1a31137e
            image: ami-c80b0aa2
            vpc_subnet_id: subnet-1a825830
            agent_user: ubuntu
            size: m3.medium
            """
        And I clone the repo 'https://github.com/geokala/cloudify-nodecellar-example.git' into 'nodecellar'
        And I check out the branch 'CFY-5048-aws-vpc-nodecellar'
        And I upload the nodecellar blueprint
        And I create a 'nodecellar' deployment with the ID 'nodecellar-1'
        And I run the 'install' workflow

    Scenario: Check the monitoring data
        When I look up the monitoring data for the deployment
        Then monitoring data is present

    Scenario: Check the nodecellar is available
        When I retrieve the host and port from the deployment
        And I visit the nodecellar URL
        Then I see the nodecellar front page
