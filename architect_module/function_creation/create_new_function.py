import ast
import textwrap
import inspect
import os
from pathlib import Path

import json
import unittest
import importlib
import re

from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType


class FunctionCreator:
    def __init__(self, task: str, gpt_manager: GPTManager):
        self.task = task
        self.agent_manager = gpt_manager
        self.advice = ""
        self.lessons = ""
        self.code = None
        self.programmer = None
        self.programmer_output =None
        self.evaluator = None
        self.evaluator_output = None

    def run_workflow(self):
        self.programmer = Programmer(self.agent_manager, self.task)
        self.evaluator = Evaluator(self.agent_manager, self.task)

        while True:

            self.programmer_output = self.programmer.create_code()

            self.evaluator_output = self.evaluator.evaluate_and_advise(self.programmer_output)

            if self.evaluator_output['evaluation_result']:
                # If the CodeAssessor is satisfied, break the loop
                print("CodeAssessor is satisfied. Exiting loop.")

                # Parse and implement the function
                self.code = self.programmer_output['code']

                break
            else:
                # Update advice and lessons for the next iteration
                self.advice = self.evaluator_output['advice']
                self.lessons = ""

    def implement_function(self):
        # TODO: Properly implement this function later to incorporate the logic for actual function implementation.
        self.save_function_to_json()

    def save_function_to_json(self):
        helper_functions = list(self.evaluator.allowed_functions.keys())

        # Extract the function_info_dict from programmer_output
        function_data = self.programmer_output['function_info_dict']
        print(self.programmer_output['function_info_dict'])

        # Update helper functions field
        function_data["helper_functions"] = helper_functions

        # Determine path to save the JSON
        current_script_path = Path(__file__).resolve()
        parent_folder = current_script_path.parent
        file_path = parent_folder.joinpath('saved_code.json')

        # Check if file exists to append data
        if file_path.exists():
            with open(file_path, 'r') as json_file:
                existing_data = json.load(json_file)
                existing_data.append(function_data)
        else:
            existing_data = [function_data]

        # Save to JSON
        with open(file_path, 'w') as json_file:
            json.dump(existing_data, json_file)


class Programmer:
    def __init__(self, agent_manager: GPTManager, task: str, additional_context: str = ''):
        self.agent_manager = agent_manager
        self.task = task
        self.additional_context = additional_context

    def create_code(self, advice: str = "") -> dict:
        programmer_system_prompt = ("You are a Python programmer, currently writing code. "
                                    "You follow instructions and do your best to present high quality code. "
                                    "Make sure to add the types of the inputs. "
                                    "Before showing me your code, you must briefly explain the logic, step by step, "
                                    "of the actions you are about to take, a bit like pseudocode. Then write the code. "
                                    "No need to explain the code after you wrote it, if you have comments to make, "
                                    "make them before you create the code. "
                                    "Be mindful of the fact that the function you are creating might go into an exec function, "
                                    "so avoid code injection and infinite loops. "
                                    "Never doubt your instructions, but if additional context is needed "
                                    "(missing logic, unclear variables, imports, etc), or the task is unclear, "
                                    "you MUST ask for more precision in this format: (CONTEXT_NEEDED:<missing_context_between_20_and_75_words>)")

        programmer_agent = self.agent_manager.create_agent(model=ModelType.CHAT_GPT4_old, max_tokens=600,
                                                           messages=advice + self.task + self.additional_context,
                                                           temperature=0.3,
                                                           system_prompt=programmer_system_prompt)
        programmer_agent.run_agent()
        programmer_output = programmer_agent.get_text()

        unit_test_programmer_system_prompt = ("You must create unit test(s) that can be used to verify the "
                                              "proper functioning of this code as per the instructions. "
                                              "Do not forget to import unittest. Instructions :")
        unit_test_agent = self.agent_manager.create_agent(model=ModelType.GPT_3_5_TURBO, max_tokens=700,
                                                          messages=programmer_output, temperature=0.1,
                                                          system_prompt=unit_test_programmer_system_prompt)
        unit_test_agent.run_agent()
        unit_test_code = unit_test_agent.get_text()

        function_info_system_prompt = """Given the code you've just generated, can you fill in the details 
        for the function_data dictionary below? only fill where there is a # to be modified.
        function_data = {
            "function_name": <function_name>,  # to be modified
            "code": <leave_empty_even_if_you_have_code>,
            "input_types": <input_types_dict>,  # to be modified
            "output_type": <output_type>, # to be modified
            "unit_test": <leave_empty>,
            "description": <function_description>, # to be modified
            "helper_functions": <leave_empty>
        }"""

        function_info_agent = self.agent_manager.create_agent(model=ModelType.GPT_3_5_TURBO, max_tokens=250,
                                                              messages=programmer_output, temperature=0.1,
                                                              system_prompt=function_info_system_prompt)
        function_info_agent.run_agent()
        function_info_text = function_info_agent.get_text()

        # Extracting the dictionary from the string representation
        function_info_dict = ast.literal_eval(function_info_text.split('=')[1].strip())

        code_content = self.extract_code_from_output(programmer_output)
        unit_test_content = self.extract_code_from_output(unit_test_code)

        code = {
            'code': code_content,
            'unit_test_code': unit_test_content,
            'function_info_dict': {
                "function_name": function_info_dict["function_name"],
                "code": code_content,
                "input_types": function_info_dict["input_types"],
                "output_type": function_info_dict["output_type"],
                "unit_test": unit_test_content,
                "description": function_info_dict["description"],
                "helper_functions": []  # Placeholder for now
            }
        }

        return code
    @staticmethod
    def extract_code_from_output(output: str) -> str:
        # Define the start and end markers for the code block
        start_marker = "```"
        end_marker = "```"

        # Find the position of the start marker
        start_pos = output.find(start_marker)
        if start_pos == -1:
            return "Start marker not found."

        # Find the position of the end marker after the start marker
        end_pos = output.find(end_marker, start_pos + len(start_marker))
        if end_pos == -1:
            return "End marker not found."

        # Extract the code block
        code_block = output[start_pos + len(start_marker):end_pos].strip()

        # Remove the language specification (if present)
        first_newline_pos = code_block.find("\n")
        if first_newline_pos != -1:
            code_block = code_block[first_newline_pos + 1:].strip()

        return code_block


# TODO implement the Function Registry along with function calling

# Uncomment for Function Registry (Deactivated)
# FUNCTION_REGISTRY = {}

# Uncomment for Function Registry (Deactivated)
# def register_function(name, func):
#     FUNCTION_REGISTRY[name] = func
class Evaluator:
    def __init__(self, agent_manager: GPTManager, task):
        self.agent_manager = agent_manager
        self.task = task
        self.allowed_function_names = self.extract_allowed_functions()
        self.allowed_functions = self.get_allowed_functions()
        self.advice = None

    def extract_allowed_functions(self) -> list:
        function_extractor_system_prompt = """You will be given a text in which someone is describing how to create a python function.
        in this text he might also mention that this function will access other helper functions that already exist.
        Your goal is to extract the names of these helper functions in this format:
        [<helper function 1>]
        <reason for choosing helper function 1>
        [<helper function 2>]
        <reason for choosing helper function 2>
        [<helper function etc>]
        <reason for choosing helper function etc>
        here is an example:
        [add]
        I chose the add function because they mentioned it was a pre-existing function that was essential to the functioning of the function to-be-created.
        [get_user_data]
        I chose the get_user_data function because the function to-be-created planned to leverage this function."""

        allowed_function_extractor = self.agent_manager.create_agent(model=ModelType.GPT_3_5_TURBO, max_tokens=300,
                                                                     temperature=0.1,
                                                                     system_prompt=function_extractor_system_prompt,
                                                                     messages=self.task)
        allowed_function_extractor.run_agent()
        extracted_functions_text = allowed_function_extractor.get_text()

        # Use regex to extract function names enclosed in square brackets
        extracted_functions_list = re.findall(r'\[([\w_]+)]', extracted_functions_text)

        return extracted_functions_list

    def create_exec_environment(self):
        # Create an environment containing only the allowed functions
        environment = {}
        for func_name, func_object in self.allowed_functions.items():
            environment[func_name] = func_object

        # Generate the helper functions string from allowed functions
        self.helper_functions = ""
        for func_name, func_obj in self.allowed_functions.items():
            source_code = inspect.getsource(func_obj)
            self.helper_functions += source_code + "\n"

        return environment

    def evaluate_and_advise(self, programmer_output: dict) -> dict:
        try:
            parsed_code = ast.parse(programmer_output['code'])
        except SyntaxError:
            return {"evaluation_result": False,
                    "advice": "The code has syntax errors. could not be analyzed by ast.parse."}

        # Check for unsafe constructs (omitted for clarity)

        cleaning_agent_advice = self.run_cleaning_agent(programmer_output['code'])
        if not cleaning_agent_advice['is_safe']:
            return {"evaluation_result": False, "advice": cleaning_agent_advice['advice']}

        NewTestCase = type("NewTestCase", (unittest.TestCase,), {})

        # Combine the helper functions, main function, and the unit test method
        code_to_exec = self.helper_functions + "\n" + programmer_output['code'] + "\n\n" + \
                       "def new_test_method(self):\n" + \
                       textwrap.indent(programmer_output['unit_test_code'], '    ')

        # Assign the test method to NewTestCase outside the exec to ensure correct assignment
        try:
            exec(code_to_exec, globals(), locals())
            NewTestCase.new_test_method = locals()["new_test_method"]
        except Exception as e:
            agent_advice = self.run_advice_agent(str(e), programmer_output['unit_test_code'])
            return {"evaluation_result": False, "advice": agent_advice}

        suite = unittest.TestLoader().loadTestsFromTestCase(NewTestCase)  # type: ignore

        test_results = unittest.TextTestRunner().run(suite)

        # Check if the tests passed
        if test_results.wasSuccessful():
            return {"evaluation_result": True, "advice": "The code and unit tests are correct."}
        else:
            agent_advice = self.run_advice_agent("Unit tests failed", programmer_output['unit_test_code'])
            return {"evaluation_result": False, "advice": agent_advice}

    def is_code_safe(self, parsed_code):
        for node in ast.walk(parsed_code):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for n in node.names:
                    if n.name not in self.allowed_functions:
                        self.advice = n.name
                        return False
        return True

    def run_cleaning_agent(self, code):
        cleaning_system_prompt = (
            "You are tasked with examining Python code snippets to ensure they are safe for execution (through exec)."
            "Please indicate if you identify constructs that could lead to code injection vulnerabilities,"
            " infinite loops, or the use of unsafe libraries. Assume that the use of pre-existing functions is safe."
            "Your answer must follow this format:\n"
            "Code Safety: <code is safe, true or false>\n"
            "Comments: <what part of the code is unsafe, if unsafe>")

        cleaning_agent = self.agent_manager.create_agent(model=ModelType.GPT_3_5_TURBO, max_tokens=75,
                                                         messages=code,
                                                         system_prompt=cleaning_system_prompt,
                                                         temperature=0.1)
        cleaning_agent.run_agent()
        answer = cleaning_agent.get_text()

        parsed_answer = {}
        lines = answer.split('\n')
        for line in lines:
            key_value = line.split(':')
            if len(key_value) == 2:
                key, value = key_value
                value = value.strip().lower()  # Convert to lowercase for consistent matching
                if key == "Code Safety":
                    # Use regex to search for words indicating safety
                    if re.search(r'\b(true|yes|safe|correct)\b', value):
                        parsed_answer["is_safe"] = True
                    else:
                        parsed_answer["is_safe"] = False
                elif key == "Comments":
                    parsed_answer["advice"] = value

        return parsed_answer

    def run_advice_agent(self, error_message, code_created):
        advice_system_prompt = "The code encountered a runtime error. How can this be resolved?"

        advice_agent = self.agent_manager.create_agent(model=ModelType.GPT_3_5_TURBO, max_tokens=250,
                                                       messages=error_message + "this is the code that cause the error" + code_created,
                                                       system_prompt=advice_system_prompt)
        advice_agent.run_agent()
        return advice_agent.get_text

    def get_allowed_functions(self):
        # Dynamically get function objects based on their names
        module = importlib.import_module('utils.function_calling.function_repositery')
        allowed_functions = {}
        for func_name in self.allowed_function_names:
            func_object = getattr(module, func_name, None)
            if func_object:
                allowed_functions[func_name] = func_object

        # Uncomment for Function Registry (Deactivated)
        # allowed_functions = {}
        # for func_name in self.allowed_function_names:
        #     func_object = FUNCTION_REGISTRY.get(func_name, None)
        #     if func_object:
        #         allowed_functions[func_name] = func_object

        return allowed_functions
