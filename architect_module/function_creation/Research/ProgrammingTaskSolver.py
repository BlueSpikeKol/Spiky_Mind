import json

from neo4j import GraphDatabase

from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType
from utils import config_retrieval
from TaskProgramming import ProgrammationTask

"""
TODO:
    - Add the verification of the programing task in the `create_list_task` function.
    - Add the integration of the libraries in the `reorder_code` function.
    - Add the possibility to handle class and object oriented programming.
    - Add a parallel execution of the task that are not directly related. 

Problem
    - Sometimes at the end of the code there is `Library:` and `NA` which are errors in python.
"""

queryPython1Atomic = """
You are a professional python programmer.
Write a function in python that compete the following task. 

$ctask

Also you should specify which library you have used to complete the task and and brief description of your function.
The description of the function should look like this:
nameOfTheFunction: 
argument1- Type: descriptionArgument1
argument2- Type: descriptionArgument2
...
"""

queryPython2Atomic = """
You are a professional python programmer.
Write a function in python that complete the following task. Don't forget to write the docstring of your function.

$ctask

After writing the function, you need to write all the library used, if you haven't used any write NA. The library must be written like this:
Library:
numpy, pandas, ...
"""

queryPython1 = """
You are a professional python programmer.
Write a function in python that complete the following task. Don't forget to write the docstring of your function.

$ctask

In order to write this function, you can use the following functions:

$cfunctions

After writing the function, you need to write all the library used, if you haven't used any write NA. The library must be written like this:
Library:
numpy, pandas, ...
"""


def testSimpleQuery(query: str, task: ProgrammationTask, model) -> str:
    query = query.replace("ctask", task.description)

    gpt_manager = GPTManager()

    agent = gpt_manager.create_agent(model=model, temperature=0.5, messages=query)

    agent.run_agent()
    # print(agent.get_text())

    return agent.get_text()


def testQueryNonAtomic(query: str, task: ProgrammationTask, model) -> str:
    current_tasks = task.children
    # print(current_tasks)
    fn = ""

    while len(current_tasks) > 0:
        t = ProgrammationTask(database_id=current_tasks[0])

        fn += t.get_description_solution() + "\n"

        for index in t.children:
            current_tasks.append(index)

        del current_tasks[0]

    query = query.replace("$ctask", task.description).replace("$cfuntions", fn)
    gpt_manager = GPTManager()

    agent = gpt_manager.create_agent(model=model, temperature=0.5, messages=query)

    agent.run_agent()
    # print(agent.get_text())

    return agent.get_text()


def create_list_task(id_task: str, ls_task: list):
    t = ProgrammationTask(database_id=id_task)

    if t.children:
        for id_children in t.children:
            create_list_task(id_children, ls_task)

        ls_task.append(t)

    else:
        ls_task.append(t)


def create_nested_list_task(id_task: str, ls_task: list):
    t = ProgrammationTask(database_id=id_task)

    if len(t.children) > 1:

        for id_children in t.children:
            new_list = []
            create_list_task(id_children, new_list)
            ls_task.append(new_list)

        ls_task.append(t)

    elif len(t.children) == 1:
        create_list_task(t.children[0], ls_task)

        ls_task.append(t)

    else:
        ls_task.append(t)


def reorder_code(ls_tasks: list, path_file: str):
    python_file = ""

    for task in ls_tasks:
        python_file += f"# {task.name}" + task.get_code() + "\n\n"

    with open(path_file, "w") as f:
        f.write(python_file)


def main_solver(id_first_task: str, path_file: str):
    ls_task = []
    create_list_task(id_first_task, ls_task)

    for task in ls_task:
        print(task.name)
        if task.atomic:
            task.update_solution(testSimpleQuery(queryPython2Atomic, task, ModelType.GPT_4_TURBO))
        else:
            task.update_solution(testQueryNonAtomic(queryPython1, task, ModelType.GPT_4_TURBO))

    reorder_code(ls_task, path_file)


if __name__ == "__main__":
    desc = """
This function takes a list of boolean, the size of a word, the index of the first letter of the word in the list and the direction (either 1 or -1 depending in which sense the word was written) in which the word is find in the list.
It will set to true all the value of the list of boolean where a letter of the word is. 
    """

    # t = ProgrammationTask("b", "testPythonAtomic", desc, [])

    # testSimpleQuery(queryPython2Atomic, t, ModelType.GPT_4_TURBO)

    id_firstQuestion = "7d04fbcf5Question 1"
    id_secondQuestion = "10d898b214Question 2"

    # task1 = ProgrammationTask(database_id=id_firstQuestion)
    # task2 = ProgrammationTask(database_id=id_secondQuestion)

    # task1.update_solution(testSimpleQuery(queryPython2Atomic, task1, ModelType.GPT_4_TURBO))
    # task2.update_solution(testQueryNonAtomic(queryPython1, task2, ModelType.GPT_4_TURBO))

    ls = []

    id_main_task = "1badc15c0Question 9"

    """
    create_list_task(id_main_task, ls)

    for i in ls:
        print(i.name)
    # """
    create_nested_list_task(id_main_task, ls)
    print(ls)

    filename = "testResult.py"

    # main_solver(id_main_task, filename)
