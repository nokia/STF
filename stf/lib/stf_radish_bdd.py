radish_bdd_setup_py = '''
import os
import commands
from radish import given, when, then

@given("configure file {ini_file:S} and test case {case_path:S}")
def get_test_case(step, ini_file, case_path):
    step.context.ini_file = ini_file
    step.context.case_path = case_path

@when("Execute test case")
def execute_script(step):
    exec_string = 'stf test --no_report -i {} -c {}'.format(step.context.ini_file, step.context.case_path)
    print "STF RUN COMMAND: " + exec_string
    try:
        step.context.result, output = commands.getstatusoutput(exec_string)
        print output
    except:
        step.context.result = 1

@then("Check result {result:g}")
def expect_result(step, result):
    assert step.context.result == result
'''


radish_bdd_stf_feature = '''
Feature: STF generated BDD test cases
    Scenario Outline: case execution
        Given configure file <ini_file> and test case <case_path>
        When Execute test case
        Then Check result <result>

        Examples:
        | ini_file | case_path | result |

'''

