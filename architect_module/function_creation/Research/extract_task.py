import json
import time
from pathlib import Path

from neo4j import GraphDatabase

from utils import config_retrieval
from Task import Task
from TaskProgramming import ProgrammationTask


def load_data(pathfile: str):
    with open(pathfile, "r") as f:
        data = json.load(f)

    return data


def create_task(project_id: str, data: dict, ls_children_id) -> Task:
    for i in data.keys():
        if data[i]["children"] != {}:
            own_children_id = []
            create_task(project_id, data[i]["children"], own_children_id)

            task = Task(name=i, description=data[i]["metadata"], children_id=own_children_id)

            ls_children_id.append(task.id)
            task.save_into_db()

        else:
            task = Task(name=i, description=data[i]["metadata"])
            ls_children_id.append(task.id)
            task.save_into_db()


def create_task_programmation(project_id: str, data: dict, ls_children_id) -> Task:
    for i in data.keys():
        if data[i]["children"] != {}:
            own_children_id = []
            create_task_programmation(project_id, data[i]["children"], own_children_id)

            task = ProgrammationTask(name=i, description=data[i]["metadata"], children_id=own_children_id,
                                     language="Python")

            ls_children_id.append(task.id)
            task.save_into_db()

        else:
            task = ProgrammationTask(name=i, description=data[i]["metadata"], language="Python", atomic=True)
            ls_children_id.append(task.id)
            task.save_into_db()


def convert_str_to_ls(data: str):
    result = []
    if data == "[]":
        return result

    while data.find("'") != -1:
        start = data.find("'")
        data = data[start + 1:]
        end = data.find("'")
        result.append(data[:end])
        data = data[end + 1:]

    return result


def update_parent_id():
    config = config_retrieval.ConfigManager()

    cypher = "MATCH (n:Task) RETURN n;"

    url = config.neo4j.host_url
    user = config.neo4j.user
    password = config.neo4j.password
    driver = GraphDatabase.driver(url, auth=(user, password))

    with driver.session() as session:
        data = session.run(cypher).data()

    for task_dict in data:
        if task_dict["n"]["children"] != "[]":
            parent_task = Task(database_id=task_dict["n"]["id"])

            for child in convert_str_to_ls(task_dict["n"]["children"]):
                child_task = Task(database_id=child)

                child_task.parent_id = parent_task.id
                child_task.update_parent_id()

    driver.close()


def test_recursion(n=4):
    if n > 0:
        own_list = []

        while n > 0:
            own_list.append(n)
            n -= 1
            test_recursion(n)

        print(own_list)


def test_querry_neo4j():
    config = config_retrieval.ConfigManager()

    cypher = "MATCH (n:Task) RETURN n LIMIT 25;"

    url = config.neo4j.host_url
    user = config.neo4j.user
    password = config.neo4j.password
    driver = GraphDatabase.driver(url, auth=(user, password))

    with driver.session() as session:
        d = session.run(cypher).data()
        print(type(d))
        print(len(d))
        print(d[2])

    driver.close()


def test_queery_speed_1():
    config = config_retrieval.ConfigManager()

    url = config.neo4j.host_url
    user = config.neo4j.user
    password = config.neo4j.password
    driver = GraphDatabase.driver(url, auth=(user, password))

    with driver.session() as session:
        for i in range(100):
            cypher = f'MERGE (Task{i}:Task {{id: "Task{i}"}}) ON CREATE SET Task{i}.name="Task{i}", Task{i}.description="Task{i}";'
            session.run(cypher)

    driver.close()


def test_queery_speed_2():
    config = config_retrieval.ConfigManager()

    url = config.neo4j.host_url
    user = config.neo4j.user
    password = config.neo4j.password
    driver = GraphDatabase.driver(url, auth=(user, password))

    main_cypher = []

    with driver.session() as session:
        for i in range(100):
            main_cypher.append(
                f'CREATE (Task{i}:Task {{id: "Task{i}", name: "Task{i}", description: "Task{i}"}});')

        session.run("\n".join(main_cypher))

    driver.close()


def test_queery_speed_3():
    config = config_retrieval.ConfigManager()

    url = config.neo4j.host_url
    user = config.neo4j.user
    password = config.neo4j.password
    driver = GraphDatabase.driver(url, auth=(user, password))

    for i in range(100):
        with driver.session() as session:
            cypher = f'MERGE (n:Task {{id: "Task{i}"}}) ON CREATE SET n.name="Task{i}", n.description="Task{i}";'
            session.run(cypher)

    driver.close()


def delete_task():
    cypher = "MATCH (n:Task) DETACH DELETE n;"
    config = config_retrieval.ConfigManager()

    url = config.neo4j.host_url
    user = config.neo4j.user
    password = config.neo4j.password
    driver = GraphDatabase.driver(url, auth=(user, password))

    with driver.session() as session:
        session.run(cypher)

    driver.close()


def delete_test_index():
    config = config_retrieval.ConfigManager()

    url = config.neo4j.host_url
    user = config.neo4j.user
    password = config.neo4j.password
    driver = GraphDatabase.driver(url, auth=(user, password))

    with driver.session() as session:
        for i in range(100):
            cypher = f'MATCH (n: Task{i}) DELETE n;'
            session.run(cypher)

    driver.close()



if __name__ == "__main__":
    # p = "C:/Users/emile/OneDrive/Bureau/programme/Spiky_Mind/architect_module/orchestrator/project_planning_files/agent_made_schedule.json"
    p = "taskAssignment3.json"
    create_task_programmation("", load_data(p), [])
    # test_querry_neo4j()
    # update_parent_id()

    # print(convert_str_to_ls("['Task4', 'Task5']"))

    # print(load_data(p))
    # test_recursion()

    """
    func = [test_queery_speed_1, test_queery_speed_3]
    for i in func:
        start = time.time()
        i()
        end = time.time()
        print(end - start)
        delete_task()
    """
    # delete_test_index()
