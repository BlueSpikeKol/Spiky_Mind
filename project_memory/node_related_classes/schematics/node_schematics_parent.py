from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import json

from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType
from project_memory.persistance_access import MemoryStreamAccess


@dataclass
class NodeSchematic:
    # Consolidating related attributes into lists of dictionaries
    descriptions: List[Dict[str, str]] = field(default_factory=lambda: [
        {"description": "", "vector_id": ""}
    ])
    names: List[Dict[str, str]] = field(default_factory=lambda: [
        {"name": "", "name_id": ""}
    ])
    labels: List[Dict[str, Optional[str]]] = field(default_factory=lambda: [
        {"label": "", "sub_label": None}
    ])
    properties: Dict[str, str] = field(default_factory=dict)  # Properties are typed as Facts
    Domain: List[Dict[str, str]] = field(default_factory=list)
    Range: List[Dict[str, str]] = field(default_factory=list)
    """
    Example for Domain and Range:
    Domain=[
        {"label": "ParentLabel1", "class_type": "ParentClass1", "relationship": "RELATIONSHIP_TYPE1"},
        {"label": "ParentLabel2", "class_type": "ParentClass2", "relationship": "RELATIONSHIP_TYPE2"}
    ],
    Range=[
        {"label": "ChildLabel1", "class_type": "ChildClass1", "relationship": "RELATIONSHIP_TYPE1"},
        {"label": "ChildLabel2", "class_type": "ChildClass2", "relationship": "RELATIONSHIP_TYPE2"}
    ]
    """

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
        taking into account the specific structure of properties for different node types.
        """
        # Initial setup for labels
        label_str = ":".join([d['label'] for d in self.labels])  # Construct label string from labels list

        # Prepare properties for Cypher query
        properties_cypher = {}
        for key, value in self.properties.items():
            # For FactNodeSchematic, directly use the value
            if isinstance(self, FactNodeSchematic):
                properties_cypher[key] = value
            # For ConceptNodeSchematic and RelationshipNodeSchematic, handle references to FactNodeSchematic
            elif isinstance(self, (ConceptNodeSchematic, RelationshipNodeSchematic)) and isinstance(value,
                                                                                                    FactNodeSchematic):
                # Assuming the value to be the name or another simple identifier from FactNodeSchematic
                properties_cypher[key] = f"'{value.names[0]['name']}'"

        # Convert properties to Cypher string format
        properties_str = ', '.join([f"{k}: {v}" for k, v in properties_cypher.items()])

        # Construct the Cypher query
        query = f"MERGE (n:{label_str} {{name_id: $name_id}}) SET n += {{{properties_str}}}"

        # Execute the query
        result = memory_stream.neo4j_handler.execute_queries(
            (query, {"name_id": self.names[0]['name_id'], **properties_cypher}))
        return result


@dataclass
class FactNodeSchematic(NodeSchematic):
    """
    Schematic for Fact nodes.
    """

    def __post_init__(self):
        super().__post_init__()
        self.label = "Fact"  # Ensures the label is always "Fact" for instances of this class


@dataclass
class ConceptNodeSchematic(NodeSchematic):
    """
    Schematic for Concept nodes.
    """
    properties: Dict[str, FactNodeSchematic] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.label = "Concept"

@dataclass
class RelationshipNodeSchematic(NodeSchematic):
    """
    Schematic for Relationship meta-nodes.
    """
    properties: Dict[str, FactNodeSchematic] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.label = "Relationship"

