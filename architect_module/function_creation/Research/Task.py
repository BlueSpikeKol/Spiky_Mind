import json
import random

from neo4j import GraphDatabase

from utils import config_retrieval


class Task:
    def __init__(self, parent_id: str = "", name: str = "", description: str = "", children_id: list = [],
                 database_id: str = None, metadata: dict = {}):
        """
        Use metadata for any additional information
        """
        self.config = config_retrieval.ConfigManager()
        self.metadata = metadata
        self.solution = ""

        if database_id is None:
            self.parent_id = parent_id
            self.name = name
            self.description = description
            self.children = children_id

            self.id: str = self._generate_id()

            self.type = None
            self.done = False

        else:
            data = self._get_data_db(database_id)

            self.name = data["name"]
            self.description = data["description"]
            self.children = self._convert_str_to_ls(data["children"])
            self.parent_id = data["parent_id"]

            self.id = database_id

            self.type = data["type"]
            self.done = data["done"] == "True"

            if self.done:
                self.solution = data["solution"]

            self.metadata = data

    @staticmethod
    def _convert_str_to_ls(data: str):
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

    def _get_data_db(self, id_task: str) -> dict:
        url = self.config.neo4j.host_url
        user = self.config.neo4j.user
        password = self.config.neo4j.password
        driver = GraphDatabase.driver(url, auth=(user, password))

        cypher = f'MATCH (n:Task {{id: "{id_task}"}}) RETURN n;'

        with driver.session() as session:
            d = session.run(cypher).data()
            data = d[0]["n"]

        driver.close()
        return data

    def _generate_id(self) -> str:
        if self.parent_id != "":
            return self.parent_id + self.name[0].upper() + self.name[1:].lower()
        else:
            return hex(random.randint(1_000_000_000, 100_000_000_000))[2:] + self.name[0].upper() + self.name[
                                                                                                    1:].lower()

    def _generate_cypher(self) -> str:
        cypher = (f'MERGE (n:Task {{id: "{self.id}"}}) ON CREATE SET n.name = "{self.name}", '
                  f'n.description =  "{self.description}", n.type = "{self.type}", n.children = "{self.children}", '
                  f'n.done = "{self.done}", n.parent_id = "{self.parent_id}";')

        for i in self.children:
            cypher += f'\nMERGE (a:Task {{id: "{self.id}"}}) MERGE (b:Task {{id: "{i}"}}) MERGE (a)-[:CHILDREN]->(b);'

        return cypher

    def _get_parent_information(self) -> str:
        pass

    def save_into_db(self):
        url = self.config.neo4j.host_url
        user = self.config.neo4j.user
        password = self.config.neo4j.password
        driver = GraphDatabase.driver(url, auth=(user, password))

        with driver.session() as session:
            for cypher in self._generate_cypher().split(";\n"):
                print(cypher)
                session.run(cypher)

        driver.close()

    def update_parent_id(self):
        cypher = f'MERGE (n:Task {{id: "{self.id}"}}) SET n.parent_id = "{self.parent_id}";'
        url = self.config.neo4j.host_url
        user = self.config.neo4j.user
        password = self.config.neo4j.password
        driver = GraphDatabase.driver(url, auth=(user, password))

        with driver.session() as session:
            session.run(cypher)

        driver.close()

    def save_json(self, filename: str):
        data = {"name": self.name, "type": self.type, "done": self.done, "children_id": self.children,
                "description": self.description, "parent_id": self.parent_id}

        with open(filename, "r") as f:
            json.dump(data, f)


if __name__ == "__main__":
    task = Task(parent_id="14090c9529",
                name="testTask1",
                description="Une instance de la call Task pour tester les fonctions relié à la database",
                children_id=["child1", "child2"])
    task.save_into_db()
