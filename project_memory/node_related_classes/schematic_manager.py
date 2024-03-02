import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Union, Type

from project_memory.persistance_access import MemoryStreamAccess
from project_memory.node_related_classes.schematics.node_schematics_parent import NodeSchematic, ConceptNodeSchematic, \
    FactNodeSchematic, RelationshipNodeSchematic
from utils.openai_api.gpt_calling import GPTManager, GPTAgent
from utils.openai_api.models import ModelType


class SchematicManager:
    def __init__(self, gpt_manager: GPTManager, memory_stream: MemoryStreamAccess):
        self.gpt_manager = gpt_manager
        self.memory_stream = memory_stream

    def get_text_embedding(self, input_text: str):  # TODO put into the gpt manager, its a reoccuring pattern
        """
        Retrieves the text embedding for the input text.

        :param input_text: The input text to process.
        :return: The text embedding.
        """
        embedding_agent = self.gpt_manager.create_agent(model=ModelType.TEXT_EMBEDDING_ADA, messages=input_text)
        embedding_agent.run_agent()
        vector = embedding_agent.get_vector()
        return vector

    def load_schematics(self, schematic_type: Type[Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]]) -> Dict:
        """Loads the schematic definitions from a JSON file."""
        schema_path = self.get_schema_or_python_path(schematic_type)
        if schema_path.exists():
            with open(schema_path, 'r') as file:
                return json.load(file)
        else:
            return {}

    def save_schematics(self, schematic_type: Type[Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]], schematics_to_save) -> None:
        """Saves the current schematics back to the JSON file."""
        schema_path = self.get_schema_or_python_path(schematic_type)
        with open(schema_path, 'w') as file:
            json.dump(schematics_to_save, file, indent=4)

    def add_schematic(self, schematic_name: str, description: str, class_name: str, code_reference: str,
                      schematic_general_type: str, schematic_specific_type: str,
                      schematic_type: Type[Union[
                          ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]]) -> None:
        """
        Adds a new schematic to the system.

        :param schematic_name: The name of the new schematic.
        :param description: A natural language description of the schematic.
        :param class_name: The Python class name that defines the dataclass for the schematic.
        :param code_reference: A copy of the Python code that defines the schematic.
        :param schematic_general_type: The general type of the schematic (Concept, Fact, or Relationship).
        :param schematic_specific_type: The most specific type that describes this schematic.
        :param schematic_type: The Python class type of the schematic for loading and saving.
        """
        schematics = self.load_schematics(schematic_type)
        # Step 1: Generate the vector for the description
        vector_id = self.memory_stream.add_to_pinecone(vector_name=schematic_name, vector_text=description,
                                                       return_id=True)
        # Step 2: Add the new schematic to the JSON storage
        if schematic_general_type is None:
            if schematic_type == ConceptNodeSchematic:
                schematic_general_type = "Concept"
            elif schematic_type == FactNodeSchematic:
                schematic_general_type = "Fact"
            elif schematic_type == RelationshipNodeSchematic:
                schematic_general_type = "Relationship"

        schematics[schematic_name] = {
            "description": description,
            "description_vector_id": vector_id,
            "class_name": class_name,  # this code snippet represents the dataclass for the schematic
            "schematic_general_type": schematic_general_type,
            "schematic_specific_type": schematic_specific_type,
            "code_reference": code_reference  # TODO may be useless
        }
        self.save_schematics(schematic_type, schematics)

        # Step 3: Optionally, print a warning if the Python code needs to be updated manually
        print(
            f"WARNING: Please manually add the following code to your project for the '{schematic_name}' schematic."
            f"\nclass name:{class_name}.code:\n{code_reference}")

    def check_for_updates(self) -> None:  # TODO
        """Checks if there are discrepancies between the JSON and the actual Python code."""
        # This would involve a more complex logic to introspect the Python code and compare it with JSON data.
        pass

    def calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        # TODO we do not have a way to reduce the number of vectors being compared in the db,
        # TODO so we need to drag them out and compare it locally. When we can change that,
        # TODO this function will no longer be necessary
        """
        Calculates cosine similarity between two vectors.
        """
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def get_schemas_vectors(self,
                            schematic_type: Type[
                                Union[ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]]):
        """
        Retrieves the vectors for all node schematics.

        Returns:
            A list of dictionaries with schematic information.
        """
        # Load the vector IDs from the external JSON document
        schematics_info = self.load_schematics(schematic_type)

        vector_ids = [info['vector_id'] for info in schematics_info.values()]
        all_vectors, missing_ids = self.memory_stream.get_vectors_whitelist(vector_ids)

        if missing_ids:
            print(f"Warning: Missing vectors for IDs: {missing_ids}. Some schematics may not have been updated."
                  f" Check file for discrepancies.")

        # Prepare the list of schematic dictionaries
        vector_schematic_list = []
        for schematic_name, info in schematics_info.items():
            vector_id = info['vector_id']
            if vector_id in all_vectors:
                vector_schematic_list.append({
                    'name': schematic_name,
                    'vector_id': vector_id,
                    'vector': all_vectors[vector_id]
                })

        return vector_schematic_list

    def choose_schematic(self, input_text: str, schematic_type: Type[Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]]) -> str:
        """
        Chooses the node schematic based on the similarity between input text vector and schematic vectors.

        :return: Chosen_schematic. This is the name of the schematic in the json, not the class name(see add_schematic)
        """
        input_vector = self.get_text_embedding(input_text)
        highest_similarity = -np.inf
        chosen_schematic = None
        vector_schema_list = self.get_schemas_vectors(schematic_type)

        for schematic in vector_schema_list:
            schematic_name = schematic['name']  # probably id
            schematic_vector = np.array(schematic['vector']).flatten()
            np_vector = np.array(input_vector).flatten()
            similarity = self.calculate_similarity(np_vector, schematic_vector)
            if similarity > highest_similarity:
                highest_similarity = similarity
                chosen_schematic = schematic_name

        return chosen_schematic  # this is the name of the schematic in the json, not the class name(see add_schematic)

    def get_schema_params(self, schematic_id: str) -> List[str]:
        """
        Retrieves the parameters for a given schematic ID.

        :param schematic_id: The ID of the schematic.
        :return: A list of parameters for the schematic.
        """
        return self.schematics[schematic_id]["params"]  # TODO deprecated, update to avoid using self.schematics

    def get_schema_or_python_path(self, schematic_type: Type[Union[
        ConceptNodeSchematic, FactNodeSchematic, RelationshipNodeSchematic]], return_python_file_path: bool = False):
        if return_python_file_path:
            # Paths to Python files
            if schematic_type == ConceptNodeSchematic:
                path = Path("schematics/concept_nodes/concept_nodes.py")
            elif schematic_type == FactNodeSchematic:
                path = Path("schematics/fact_nodes/fact_nodes.py")
            elif schematic_type == RelationshipNodeSchematic:
                path = Path("schematics/meta_relationship_nodes/meta_relationship_nodes.py")
            else:
                raise ValueError("Invalid schematic type")
        else:
            # Paths to JSON schematics
            if schematic_type == ConceptNodeSchematic:
                path = Path("schematics/concept_nodes/concept_schematics.json")
            elif schematic_type == FactNodeSchematic:
                path = Path("schematics/fact_nodes/fact_schematics.json")
            elif schematic_type == RelationshipNodeSchematic:
                path = Path("schematics/meta_relationship_nodes/relationships_schematics.json")
            else:
                raise ValueError("Invalid schematic type")

        return path

# Example usage
# schematic_manager = SchematicManager(
#     json_path=Path("./schematics.json"),
#     gpt_manager=GPTManager(),
#     memory_stream=MemoryStreamAccess()
# )
#
# # Adding a new schematic
# schematic_manager.add_schematic(
#     schematic_name="NewSchematic",
#     description="This is a description of what the new schematic represents.",
#     code_snippet="""
# @dataclass
# class NewSchematic(NodeSchematic):
#     # Define the attributes for the new schematic here
# """
# )
