import configparser
from pathlib import Path
from dataclasses import dataclass, asdict
import os

current_script_path = Path(__file__).resolve()
parent_folder = current_script_path.parent.parent
CONFIG_FILE = parent_folder.joinpath('config.ini')


# Define the individual data classes for each section of the configuration.
# Each field in the data classes serves as a hint for both types and the structure of the config.
# The `frozen=True` attribute ensures the instances are immutable after creation.

@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str


@dataclass(frozen=True)
class MySQLConfig:
    host: str
    user: str
    password: str
    database: str

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Neo4jConfig:
    host_url: str
    user: str
    password: str

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class PineconeConfig:
    index_name: str
    api_key: str
    environment: str

@dataclass(frozen=True)
class VirtuosoConfig:
    sparql_endpoint: str
    user: str
    password: str


class ConfigManager:
    def __init__(self, config_path=CONFIG_FILE):
        config = configparser.ConfigParser()

        # Check if the file was read successfully
        if not config.read(config_path):
            print(f"Error: Could not read {config_path}")
            return

        if 'openai' in config:
            self.openai = OpenAIConfig(
                api_key=os.environ.get("OPENAI_API_KEY")
            )

        if 'mysql' in config:
            mysql_config = config['mysql']
            self.mysql = MySQLConfig(
                host=mysql_config['host'],
                user=mysql_config['user'],
                password=mysql_config['password'],
                database=mysql_config['database']
            )

        if 'pinecone' in config:
            self.pinecone = PineconeConfig(
                index_name=config['pinecone']['index_name'],
                api_key=config['pinecone']['api_key'],
                environment=config['pinecone']['environment']
            )

        if 'neo4j' in config:
            self.neo4j = Neo4jConfig(
                host_url=config['neo4j']['host_url'],
                user=config['neo4j']['user'],
                password=config['neo4j']['password']
            )
        if 'virtuoso' in config:
            self.virtuoso = VirtuosoConfig(
                sparql_endpoint=config['virtuoso'].get('sparql_endpoint', ''),
                user=config['virtuoso'].get('user', ''),
                password=config['virtuoso'].get('password', '')
            )

# To add a new config section:
# 1. Define a new dataclass above, annotating all fields with their expected types.
# 2. Make sure the dataclass has the attribute `frozen=True` to ensure immutability.
# 3. In this ConfigManager's `__init__` method, add a condition to check for the section's presence:
#    if 'your_new_section_name' in config:
#        self.your_new_section_variable = YourNewDataClass(
#            attribute1=config['your_new_section_name']['attribute1'],
#            attribute2=config['your_new_section_name']['attribute2'],
#            ...
#        )
# 4. The instance variable `self.your_new_section_variable` will now hold the config for that section.
