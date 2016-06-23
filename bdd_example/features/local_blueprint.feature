Feature: Local blueprint

    Scenario: Deploy a local blueprint
        Given I have a local blueprint at cloudify_tester/suites/local/simple_blueprint/blueprint.yaml
        And I create inputs file test.yaml with inputs
            """
            target_path: path/ilikecake
            target_file_name: test.yaml
            """

        When I init a local env using the blueprint
        And I execute the local install workflow

        Then I see the file path/ilikecake/test.yaml exists
        And The file path/ilikecake/test.yaml contains the text 'Wow!'
