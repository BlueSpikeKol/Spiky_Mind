import json
import random

from neo4j import GraphDatabase

from utils import config_retrieval
from Task import Task


class ProgrammationTask(Task):
    def __init__(self, parent_id: str = "", name: str = "", description: str = "", children_id: list = [],
                 database_id: str = None, language: str = "", atomic: bool = False):
        super().__init__(parent_id, name, description, children_id, database_id)

        self.type = "Programming"

        if database_id is None:
            self.language = language
            self.atomic = atomic

        else:
            self.language = self.metadata["language"]
            self.atomic = self.metadata["atomic"] == "True"

    def get_libraries(self) -> str:
        pass

    def get_code(self) -> str:
        if not self.done:
            return None

        # print(text.find("```python"))
        start_code = self.solution.find("```python") + 9
        end_code = self.solution[start_code:].find("```") + start_code

        code = self.solution[start_code: end_code]

        return code

    def get_description_solution(self):
        if not self.done:
            return None

        code = self.get_code()
        # code = self.solution
        # print(code)

        name = ""
        index = code.find("def") + 4
        done = False
        while not done:
            if code[index] == ":":
                done = True
            else:
                name += code[index]
                index += 1

        # print(name)

        start_desc = code.find("'''") + 3
        end_desc = code[start_desc:].find("'''") + start_desc

        desc = code[start_desc:end_desc]

        # print(desc)

        result = "Function: "
        result += name + desc

        return result

    def _generate_cypher(self) -> str:
        cypher = super()._generate_cypher()
        # print(cypher)

        ls_query = cypher.split(";")
        # print(ls_query)

        ls_query[0] += f', n.language = "{self.language}", n.atomic = "{self.atomic}"'

        print(";\n".join(ls_query))

        return ";\n".join(ls_query)

    def save_into_db(self):
        url = self.config.neo4j.host_url
        user = self.config.neo4j.user
        password = self.config.neo4j.password
        driver = GraphDatabase.driver(url, auth=(user, password))

        with driver.session() as session:
            for cypher in self._generate_cypher().split(";\n"):
                print(cypher)
                print(self.name)

                if cypher == "":
                    continue

                session.run(cypher)

        driver.close()

    def update_solution(self, sol: str):
        self.done = True
        self.solution = sol
        code = self.solution.replace('"', "'")

        cypher = f'MERGE (n:Task {{id: "{self.id}"}}) SET n.solution = "{code}", n.done = "{self.done}";'

        # print()
        # print("Cypher\n")
        # print(cypher)
        url = self.config.neo4j.host_url
        user = self.config.neo4j.user
        password = self.config.neo4j.password
        driver = GraphDatabase.driver(url, auth=(user, password))

        with driver.session() as session:
            session.run(cypher)

        driver.close()

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

