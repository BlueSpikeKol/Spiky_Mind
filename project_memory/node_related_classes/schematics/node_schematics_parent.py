from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import json

from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType
from project_memory.persistance_access import MemoryStreamAccess


@dataclass
class NodeSchematic:
    description: str
    description_vector_id: str
    creation_context: str
    name: str
    name_id: str
    label: str
    sub_label: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)
    # Each dict contains 'label', 'class_type', and 'relationship' keys
    parent_relationship_map: List[Dict[str, str]] = field(default_factory=list)
    """
    parent_relationship_map=[
        {"label": "ParentLabel1", "class_type": "ParentClass1", "relationship": "RELATIONSHIP_TYPE1"},
        {"label": "ParentLabel2", "class_type": "ParentClass2", "relationship": "RELATIONSHIP_TYPE2"}]"""

    def __post_init__(self):
        if isinstance(self, ConceptNodeSchematic):
            self.label = "Concept"  # Enforcing the label for Concept nodes

    def fill_attributes(self, schematic_info: str, gpt_manager: GPTManager) -> None:
        """
        Uses GPT-3 to generate attributes for the node based on provided schematic information.

        :param schematic_info: The input text to generate attributes from, describing the node.
        :param gpt_manager: An instance capable of handling GPT model requests.
        """
        prompt = self.build_prompt(schematic_info)
        assigning_agent = gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=prompt, temperature=0.2,
                                                   max_tokens=500)
        assigning_agent.run_agent()
        response = assigning_agent.get_text()
        attributes = json.loads(response)  # Assuming the LLM response is JSON-formatted
        for key, value in attributes.items():
            setattr(self, key, value)

    def build_prompt(self, schematic_info: str) -> str:
        """
        Constructs a prompt for the LLM to generate node attributes based on schematic information.

        :param schematic_info: Descriptive information about the node.
        :return: A string prompt for the LLM.
        """
        return (f"Given the following information about a node: '{schematic_info}', "
                "please generate a JSON object with attributes that best describe this node. "
                "Include any relevant properties and their values.")

    def upload_as_cypher_query(self, memory_stream: MemoryStreamAccess):
        """
        Constructs and executes a Cypher query string for uploading the node to a Neo4J database,
        treating sub_label as additional labels.
        """
        # Convert all relevant dataclass fields to a dictionary for Cypher query
        properties = {k: v for k, v in asdict(self).items() if
                      v is not None and k not in ['sub_label', 'relationships']}

        # Handle dynamic labels (main label + sub_labels)
        labels = self.label  # Main label
        if hasattr(self, 'sub_label') and self.sub_label:  # Check if sub_labels exist and are not empty
            sub_labels = ":" + ":".join(self.sub_label) if isinstance(self.sub_label, list) else ":" + self.sub_label
        else:
            sub_labels = ""

        # Prepare properties string for Cypher query
        properties_str = ', '.join([f"{k}: ${k}" for k in properties.keys()])
        query = f"MERGE (n:{labels}{sub_labels} {{name_id: $name_id}}) SET n += {{{properties_str}}}"

        # Execute the query using the provided Neo4jDatabaseManager instance
        result = memory_stream.neo4j_handler.execute_queries((query, properties))
        return result


@dataclass
class ConceptNodeSchematic(NodeSchematic):
    """
    Schematic for Concept nodes.
    """
    label: str = "Concept"

    def __post_init__(self):
        super().__post_init__()
        self.label = "Concept"  # Ensures the label is always "Concept" for instances of this class


@dataclass
class FactNodeSchematic(NodeSchematic):
    """
    Schematic for Fact nodes.
    """

    def __post_init__(self):
        super().__post_init__()
        self.label = "Fact"  # Ensures the label is always "Fact" for instances of this class


@dataclass
class RelationshipNodeSchematic(NodeSchematic):
    """
    Schematic for Relationship meta-nodes.
    To avoid putting properties in the relationships, we use a meta-node to have greater control.
    """

    def __post_init__(self):
        super().__post_init__()
        self.label = "Relationship"  # Ensures the label is always "Relationship" for instances of this class
