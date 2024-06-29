import json
import random
import datetime

from neo4j import GraphDatabase

from utils import config_retrieval
from Task import Task


class AdminTask(Task):
    def __init__(self, parent_id: str = "", name: str = "", description: str = "", children_id: list = [],
                 database_id: str = None, country: str = ""):
        super().__init__(parent_id, name, description, children_id, database_id)

        self.country = country
        self.type = "Admin"
        self.time = datetime.now().strftime("%Y/%m/%d, %H:%M:%S")

    def _generate_cypher(self) -> str:
        pass

    def save_into_db(self):
        pass


if __name__ == "__main__":
    pass
