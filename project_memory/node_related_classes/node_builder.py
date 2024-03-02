from dataclasses import is_dataclass
from typing import Dict, List, Union, Type
import importlib
from pathlib import Path

from project_memory.persistance_access import MemoryStreamAccess
from project_memory.node_related_classes.schematic_manager import SchematicManager
from project_memory.node_related_classes.schematics.node_schematics_parent import NodeSchematic, ConceptNodeSchematic, \
    FactNodeSchematic, RelationshipNodeSchematic
from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType
from utils.openai_api.agent_sessions.agent_presets import PresetAgents


class NodeBuilder:
    def __init__(self, memory_stream: MemoryStreamAccess, gpt_manager: GPTManager = None):
        """
        Initializes the NodeBuilder.

        :param gpt_manager: An instance capable of handling GPT model requests.
        :param vector_storage: A storage system for vector representations of node schematics.
        :param neo4j_handler: Handler for interacting with the Neo4J database.
        """
        self.memory_stream = memory_stream
        if gpt_manager:
            self.gpt_manager = gpt_manager
        else:
            self.gpt_manager = GPTManager()
        self.schematic_manager = SchematicManager(self.gpt_manager, self.memory_stream)

    def build_node(self, input_text: str,
                   schematic_type: Type[Union[ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]],
                   parent_id=None) -> None:
        """
        Builds a node based on the input text.

        :param input_text: The input text to process.
        """
        # Step 1: Choose schematic based on input
        chosen_schematic = self.schematic_manager.choose_schematic(input_text, schematic_type=schematic_type)

        # Step 2: Fill the node content based on the chosen schematic
        node_schematic_object = self.create_node_from_schematic(chosen_schematic, input_text, schematic_type)

        # Step 3: Create all the parents until a parent already exists
        bonus_nodes_schematics = self.build_all_parents(node_schematic_object, parent_id=parent_id)

        # Step 4: Create the nodes in Neo4J
        node_schematic_object.upload_as_cypher_query(self.memory_stream)

    def build_all_parents(self, node_schematic_object: Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic], parent_id=None) -> List[NodeSchematic]:
        bonus_nodes_schematics = []
        parent_node = None
        parent_relationship_map = node_schematic_object.parent_relationship_map

        # Retrieve all potential parent nodes across all parent types
        potential_parents = self.get_nodes_with_empty_field(node_schematic_object)

        # If multiple potential parents are found, perform a similarity search
        if len(potential_parents) > 1:
            parent_ids = [parent['id'] for parent in potential_parents]
            vectors, missing_ids = self.memory_stream.get_vectors_whitelist(parent_ids)
            if missing_ids:
                print(f"Missing vectors for IDs: {missing_ids}")

            # Retrieve the vector for the node_schematic_object using its vector_id
            context_vector, _ = self.memory_stream.get_vectors_whitelist([node_schematic_object.description_vector_id])

            # Perform similarity search (this step may need to be adapted based on your implementation)
            top_parents = self.memory_stream.similarity_comparison(vectors, context_vector[
                node_schematic_object.description_vector_id], top_k=5)

            # Check belonging of top results
            for parent_id, similarity_score in top_parents:
                if self.check_belonging(parent_id, node_schematic_object):
                    parent_node, _ = self.memory_stream.get_vectors_whitelist([parent_id])
                    break
        elif potential_parents:
            parent_node, _ = self.memory_stream.get_vectors_whitelist([potential_parents[0]['id']])
        else:
            parent_node = None

        # If a parent is identified, create the relationship
        if parent_node:
            # Assuming parent_node['label'] or another attribute gives us the parent's label
            parent_label = parent_node['label']
            # Find the relationship type for this parent label in the parent_relationship_map
            for parent_info in parent_relationship_map:
                if parent_info['label'] == parent_label:
                    relationship_type = parent_info['relationship']
                    self.create_relationship(node_schematic_object.name_id, parent_node['id'], relationship_type)
                    bonus_nodes_schematics.append(parent_node)
                    break  # Assuming each parent label only appears once in the map

        return bonus_nodes_schematics

    def check_belonging(self, parent_id: str, child_schematic: NodeSchematic) -> bool:
        # Retrieve parent node details from Neo4j
        parent_node = self.memory_stream.neo4j_handler.get_node_details(parent_id)
        THRESHOLD = 0.8
        if not parent_node:
            return False

        # Compare vectors (assuming a function to calculate similarity)
        similarity = self.memory_stream.text_similarity(parent_node["creation_context"],
                                                        child_schematic.creation_context)

        # Consult logic gate agent if similarity is above a certain threshold
        if similarity > THRESHOLD:
            decision = self.consult_logic_gate_agent(child_schematic.creation_context, parent_node["creation_context"])
            if decision:
                # Prompt user for confirmation
                return self.prompt_user_for_confirmation(child_schematic, parent_node)
        return False

    def consult_logic_gate_agent(self, child_context: str,
                                 parent_context: str) -> bool:  # TODO we could make this more general to avoid complexities in the logic_gate  agent usage
        logic_gate_agent = PresetAgents.get_agent(PresetAgents.LOGIC_GATE)
        logic_gate_agent.update_agent(
            messages=f"Compare the context of the child and parent nodes in a db."
                     f"If they are similar, do you think that yes or no they should be linked together by a parent-child relationship?"
                     f"\nContext of the child: {child_context}\n"
                     f"Context of the parent: {parent_context})")
        logic_gate_agent.run_agent()
        decision_text = logic_gate_agent.get_text()
        return decision_text.strip().lower() == "yes"

    def prompt_user_for_confirmation(self, child_schematic: NodeSchematic, parent_node: dict) -> bool:
        user_prompt = f"currently the {type(child_schematic).__name__} is getting linked to its parent of type {parent_node['label']}. " \
                      f"Here is the context of the child {child_schematic.creation_context} and here is the parent node: " \
                      f"context:{parent_node['creation_context']}/nparent name:{parent_node['name']}/nlabels:{parent_node['labels']}"
        user_confirmation = input(user_prompt + "\nConfirm (yes/no): ")
        return user_confirmation.strip().lower() == "yes"

    def get_nodes_with_empty_field(self, node_schematic_object: Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]) -> List[dict]:
        potential_parents = []

        # Iterate over each entry in the parent_relationship_map to find matching nodes
        for parent_info in node_schematic_object.parent_relationship_map:
            label = parent_info['label']
            class_name = parent_info['class_type']
            relationship = parent_info['relationship']

            # Dynamically determine the parent type based on the class_name
            parent_type = self.determine_parent_type(node_schematic_object)

            # Use get_schematic_object to dynamically import the schematic for each parent type and class name
            try:
                parent_schematic = self.get_schematic_object(schematic_name=class_name, schematic_type=parent_type)
            except ValueError as e:
                print(e)
                continue

            # Determine the field in the parent schematic that matches the type of node_schematic_object
            matching_field = None
            for field_name, field_type in parent_schematic.properties.items():
                # Assuming the properties dict contains types as values, and we're looking for a match with node_schematic_object's type
                if field_type == type(node_schematic_object).__name__:
                    matching_field = field_name
                    break

            if matching_field:
                # Query the database for nodes of this label with the matching field empty
                query_result = self.query_for_empty_field_nodes(label, matching_field)
                potential_parents.extend(query_result)

        return potential_parents

    def determine_parent_type(self, node_schematic_class: Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]) -> Type[Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]]:
        """
        Determines the expected parent type based on the class type of the node_schematic_object.

        :param node_schematic_class: The class type of the node schematic object to determine the parent type for.
        :return: The class type of the expected parent.
        """

        # Check the class type of node_schematic_object and return the corresponding parent type
        if node_schematic_class is ConceptNodeSchematic or node_schematic_class is FactNodeSchematic:
            # If it's a ConceptNodeSchematic or FactNodeSchematic, the parent should be a RelationshipNodeSchematic
            return RelationshipNodeSchematic
        elif node_schematic_class is RelationshipNodeSchematic:
            # If it's a RelationshipNodeSchematic, the parent should be a ConceptNodeSchematic
            return ConceptNodeSchematic
        else:
            raise ValueError("Unsupported node schematic class type.")

    def query_for_empty_field_nodes(self, label: str, field_name: str) -> List[dict]:
        """
            Placeholder function to query the database for nodes with a specific label
            where a given field is empty. This function needs to be implemented based on
            your database access layer and query language (e.g., Cypher for Neo4j).
        """
        # Example Cypher query for Neo4j (this is just a placeholder and needs to be adapted)
        query = f"""
                MATCH (n:{label})
                WHERE NOT EXISTS(n.{field_name})
                RETURN n
                """
        # Execute the query and return the results
        results = self.memory_stream.neo4j_handler.execute_queries(query)
        return results

    def create_relationship(self, child_id: str, parent_id: str, relationship_type: str):
        """
        Creates a relationship of a given type between two nodes identified by their IDs.
        """
        query = f"""
                    MATCH (child {{id: $child_id}}), (parent {{id: $parent_id}})
                    MERGE (child)-[r:{relationship_type}]->(parent)
                    RETURN r
                    """
        # Adjusted to pass query and parameters as a tuple
        self.memory_stream.neo4j_handler.execute_queries((query, {'child_id': child_id, 'parent_id': parent_id}))

    def create_node_from_schematic(self, schematic_name: str, input_text: str, schematic_type: Type[Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]]) -> Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]:
        schema = self.get_schematic_object(schematic_name, schematic_type)
        schema.fill_attributes(input_text, self.gpt_manager)  # needs testing

        return schema

    def get_schematic_object(self, schematic_name: str, schematic_type: Type[Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]]) -> Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]:
        # Step 1: Load all schematics of the same type
        schematics = self.schematic_manager.load_schematics(schematic_type)

        # Step 2: Check if the schematic name exists
        schematic_details = schematics.get(schematic_name)
        if not schematic_details:
            raise ValueError(f"Schematic with name {schematic_name} not found.")

        # Step 3: Dynamically import the class
        class_name = schematic_details['class_name']
        class_path = self.schematic_manager.get_schema_or_python_path(class_name, return_python_file_path=True)
        module_path, class_name = class_path.rsplit('.', 1)  # Assuming class_path includes the full path to the class
        module = importlib.import_module(module_path)
        schematic_class = getattr(module, class_name)

        # Step 4: Create an object of the imported class
        schematic_object = schematic_class()

        return schematic_object

    @staticmethod
    def extract_json_from_response(response: str) -> str:
        # Extracts JSON text from the response, assuming it is enclosed in triple backticks
        start = response.find("```json") + len("```json")
        end = response.find("```", start)
        json_text = response[start:end].strip()
        return json_text

    def add_schematic_to_json(self, schematic_name: str, description: str, code_snippet: str) -> None:
        # will need to be updated depending on how the input will change
        self.schematic_manager.add_schematic(schematic_name, description, code_snippet)
