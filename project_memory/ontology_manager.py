import os
import re

from owlready2 import *

from project_memory.persistance_access import MemoryStreamAccess
from utils.openai_api.models import ModelType
from utils.openai_api.gpt_calling import GPTManager


class OntologyManager:
    def __init__(self, memory_stream: MemoryStreamAccess, gpt_manager: GPTManager):
        self.ontology = None
        self.gpt_manager = gpt_manager
        self.memory_stream = memory_stream

    def load_ontology(self, ontology_path):
        self.ontology = ontology_path

    def get_ontology(self):
        return self.ontology
    def process_conversation_analysis(self, round_analysis):
        """
        Process the analysis of a conversation round that was done through en_core_web_lg and
        update the ontology accordingly. then call add_new_rule_to_ontology() to add the new rule to the ontology with
        the suggested rule type.

        Parameters:
        - round_analysis: The analysis of a conversation round done with en_core_web_lg nlp.
        """
        # Step 1: Chunking Potential Project Objects
        potential_objects = self.chunk_potential_objects(round_analysis)

        # Step 2: Vectorization and Comparison
        object_matches = self.vectorize_and_compare(potential_objects)

        # Step 3: Display Analysis and Matches
        for obj, match in object_matches.items():
            print(f"Object: {obj}, Match: {match['rule_name']}, Probability: {match['probability']}")

        # Step 4: User Selection and Rule Addition
        selections = input("Enter the numbers of the objects you want to add rules for, separated by commas: ")
        selected_indices = [int(idx.strip()) for idx in selections.split(",")]

        for idx in selected_indices:
            obj = list(object_matches.keys())[idx]
            suggested_rule_type = object_matches[obj]['rule_name']
            self.add_new_rule_to_ontology(suggested_rule_type=suggested_rule_type)
    def chunk_potential_objects(self, round_analysis):
        """
        Chunk potential project objects from the conversation analysis.

        Parameters:
        - round_analysis: The analysis of a conversation round done with en_core_web_lg nlp.
        """
        # each entity is a potential object and its surrounding context should be included.
        # to detect surrounding context, use the tokens before and after the entity and the tokens that are related to
        # the entity using Parser and Tagger labels on the analysis. ex: ('the', 'det', 'DT') ('department', 'dobj', 'NN')



        return ["Project A", "Project B", "Project C"]

    def add_new_rule_to_ontology(self, suggested_rule_type=None):
        print("Welcome to the Ontology Rule Addition Helper.")
        print("Let's add a new rule to our knowledge base. What would you like to do?")
        rule_types = {
            "1": {
                "type": "Class Declaration",
                "explanation": "Create a new category or group of things.",
                "example": "For example, 'Fruit' could be a new category."
            },
            "2": {
                "type": "Subclass",
                "explanation": "Specify that one category is a more specific type of another category.",
                "example": "For instance, 'Apple' is a specific type of 'Fruit'."
            },
            "3": {
                "type": "Equivalent Classes",
                "explanation": "Say that two categories are essentially the same.",
                "example": "For example, 'Car' and 'Automobile' mean the same thing."
            },
            "4": {
                "type": "Disjoint Classes",
                "explanation": "Declare that two categories can never overlap.",
                "example": "For instance, no 'Fruit' can be a 'Vehicle'."
            },
            "5": {
                "type": "Property Declaration",
                "explanation": "Define a new relationship or characteristic that can exist between things.",
                "example": "For example, 'isColorOf' could describe the relationship between 'Red' and 'Apple'."
            },
            "6": {
                "type": "Domain and Range",
                "explanation": "Specify what categories or types of things a relationship can connect.",
                "example": "For 'isColorOf', the domain might be 'Color', and the range might be 'Fruit'."
            },
            "7": {
                "type": "Functional Property",
                "explanation": "Say that a thing can have only one of this kind of relationship.",
                "example": "For instance, a 'Person' can have only one 'BirthDate'."
            },
            "8": {
                "type": "Inverse Properties",
                "explanation": "Define two ways of looking at the same relationship.",
                "example": "If 'John isParentOf Jane', then 'Jane isChildOf John'."
            },
            "9": {
                "type": "Transitive Property",
                "explanation": "If A is related to B, and B is related to C, then A is also related to C.",
                "example": "If 'Paris isPartOf France' and 'France isPartOf Europe', then 'Paris isPartOf Europe'."
            },
            "10": {
                "type": "Symmetric Property",
                "explanation": "If A is related to B, then B is also related to A.",
                "example": "If 'John isMarriedTo Jane', then 'Jane isMarriedTo John'."
            },
            "11": {
                "type": "Asymmetric Property",
                "explanation": "If A is related to B, then B cannot be related to A in the same way.",
                "example": "If 'John isParentOf Jane', then 'Jane cannot beParentOf John'."
            }
        }

        for key, value in rule_types.items():
            print(f"{key}. {value['type']}: {value['explanation']} (e.g., {value['example']})")
        if suggested_rule_type:
            print(f"Based on the information provided, we suggest adding a rule of type: {suggested_rule_type}")
        choice = input("Enter the number of the rule type you wish to add: ")

        if choice not in rule_types:
            print("Invalid choice. Please try again.")
            return
        # TODO if the user does not see the choice he needs, he might want to start a conversation with gpt learn more about the choices or add a new choice

        sparql_insertion_query = self.prepare_rule_for_insertion(choice, rule_types)

        success = self.memory_stream.execute_sparql_query(query=sparql_insertion_query)
        if success is False:
            print("Rule addition process failed. Will try to upload the query as a file using owlready2.")
        self.upload_query_as_file(sparql_insertion_query)
        print("Rule addition process completed. The rule has been prepared for insertion into the ontology.")

    def upload_query_as_file(self, sparql_query):
        current_script_path = os.path.abspath(__file__)
        spiky_mind_dir = current_script_path.split('Spiky_Mind', 1)[0] + 'Spiky_Mind'
        save_path = os.path.join(spiky_mind_dir, 'project_memory', 'ontologies', 'temporary_file_for_upload.rdf')
        self.memory_stream.download_ontology_from_graph(save_path=save_path)
        onto = get_ontology(f"file://{save_path}").load()
        modified_onto_saved_path = save_path.replace('.rdf', '_modified.rdf')
        self.use_agent_to_modify_onto(onto, modification_input=sparql_query, save_path=save_path)
        self.memory_stream.upload_ontology_to_virtuoso(file_path=modified_onto_saved_path)

    def use_agent_to_modify_onto(self, onto, modification_input=None, save_path=None):
        if modification_input:
            prompt = f"""listen to the user query and create python code to modify the ontology using owlready2 library.
            Never perform reasoning on the ontology. Always assume that the imports are already done. 
            Always assume that onto is already defined(no need to use load_ontology()).
        Example:
        Query: "Add a class named 'MyClass' as a subclass of Thing."
        Code:
        ```
        with onto:
            class MyClass(Thing):
                pass
        ```"""
            agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=modification_input,
                                                  system_prompt=prompt,
                                                  temperature=0.1, max_tokens=500)
            agent.run_agent()
            code_response = agent.get_text()
            start = code_response.find("```") + 3
            end = code_response.rfind("```")
            code_to_exec = code_response[start:end].strip()

            # Prepare the namespace for exec, explicitly including 'onto' and necessary Owlready2 classes
            namespace = {
                'onto': onto,
                'Thing': Thing,
                'ObjectProperty': ObjectProperty,
                'DataProperty': DataProperty,
                'AnnotationProperty': AnnotationProperty,
                'Class': onto.classes,
                'Individual': onto.individuals,
                'AsymmetricProperty': AsymmetricProperty,
                'SymmetricProperty': SymmetricProperty,
                'TransitiveProperty': TransitiveProperty,
                'InverseFunctionalProperty': InverseFunctionalProperty,
                'FunctionalProperty': FunctionalProperty,
                'AllDisjoint': AllDisjoint,
                'OneOf': OneOf,
                'AllDifferent': AllDifferent,
                'get_ontology': get_ontology,
                'default_world': default_world
            }
            # Make existing classes available in the namespace
            for cls in onto.classes():
                namespace[cls.name] = cls

            try:
                code_to_exec_clean = re.sub(r"python\n", "", code_to_exec, flags=re.MULTILINE)
                exec(code_to_exec_clean, namespace)
                print("Ontology(onto variable) modified successfully.")

                # Dynamically construct expected elements dictionary
                expected_elements = self.construct_expected_elements_dict(code_to_exec)

                # Verify modifications
                self.verify_ontology_modifications(onto, expected_elements)

            except Exception as e:
                print(f"Failed to modify ontology: {e}")

            # Save modifications to the specified path
            if save_path:
                onto.save(file=save_path)
                print(f"Ontology saved to {save_path}.")
            else:
                print("No save path provided. Ontology not saved.")
        else:
            print("No modification input provided. Skipping ontology modification.")

    def construct_expected_elements_dict(self, code_to_exec):
        """
        Extracts expected elements from the agent-generated code using regular expressions.
        This version tries to capture all occurrences of each element type.
        """
        expected_elements = {
            'class': re.findall(r"class (\w+)\(", code_to_exec),
            'individual': re.findall(r"(\w+) = (\w+)\(", code_to_exec),
            'object_property': re.findall(r"class (\w+)\(ObjectProperty\):", code_to_exec),
            'data_property': re.findall(r"class (\w+)\(DataProperty\):", code_to_exec),
            'annotation_property': re.findall(r"class (\w+)\(AnnotationProperty\):", code_to_exec),
            # Datatypes are typically not defined with class syntax in Owlready2, so this remains empty
            'datatype': [],
            # Additional property types
            'functional_property': re.findall(r"class (\w+)\(FunctionalProperty\):", code_to_exec),
            'inverse_functional_property': re.findall(r"class (\w+)\(InverseFunctionalProperty\):", code_to_exec),
            'transitive_property': re.findall(r"class (\w+)\(TransitiveProperty\):", code_to_exec),
            'symmetric_property': re.findall(r"class (\w+)\(SymmetricProperty\):", code_to_exec),
            'asymmetric_property': re.findall(r"class (\w+)\(AsymmetricProperty\):", code_to_exec),
        }
        return expected_elements

    def verify_ontology_modifications(self, onto, expected_elements):
        """
        Verifies various modifications made to an ontology.

        :param onto: The ontology to verify.
        :param expected_elements: A dictionary with keys as element types (e.g., 'class', 'individual') and values as lists of names to check.
        """
        # Verify classes
        for cls_name in expected_elements.get('class', []):
            if not onto.search(iri="*" + cls_name):
                print(f"Error: Class '{cls_name}' not found in the ontology.")
            else:
                print(f"Class '{cls_name}' successfully verified.")

        # Verify individuals
        for ind_name in expected_elements.get('individual', []):
            if not onto.search(iri="*" + ind_name):
                print(f"Error: Individual '{ind_name}' not found in the ontology.")
            else:
                print(f"Individual '{ind_name}' successfully verified.")

        # Verify object properties
        for prop_name in expected_elements.get('object_property', []):
            if not onto.search(iri="*" + prop_name):
                print(f"Error: Object property '{prop_name}' not found in the ontology.")
            else:
                print(f"Object property '{prop_name}' successfully verified.")

        # Verify data properties
        for prop_name in expected_elements.get('data_property', []):
            if not onto.search(iri="*" + prop_name):
                print(f"Error: Data property '{prop_name}' not found in the ontology.")
            else:
                print(f"Data property '{prop_name}' successfully verified.")

        # Add more verification for other types like annotation properties
        for prop_name in expected_elements.get('annotation_property', []):
            if not onto.search(iri="*" + prop_name):
                print(f"Error: Annotation property '{prop_name}' not found in the ontology.")
            else:
                print(f"Annotation property '{prop_name}' successfully verified.")
        for prop_name in expected_elements.get('datatype', []):
            if not onto.search(iri="*" + prop_name):
                print(f"Error: Datatype '{prop_name}' not found in the ontology.")
            else:
                print(f"Datatype '{prop_name}' successfully verified.")

    def prepare_rule_for_insertion(self, rule_type, rule_types):
        """
        Collects specific information based on the rule type and prepares it for insertion as a SPARQL query.

        Parameters:
        - rule_type: The type of rule selected by the user.
        - rule_types: A dictionary of rule types with explanations and examples.
        """
        rule_info = rule_types.get(rule_type)
        if not rule_info:
            print("Invalid rule type selected.")
            return

        print(f"You have selected to add a rule of type: {rule_info['type']}")
        print(f"Explanation: {rule_info['explanation']}")
        print(f"Example: {rule_info['example']}")

        if rule_type == "1":  # Class Declaration
            print("example:INSERT DATA { :Fruit rdf:type owl:Class. }")
            class_name = input("Enter the name of the new class you want to add: ")
            sparql_query = f"INSERT DATA {{ :{class_name} rdf:type owl:Class. }}"

        elif rule_type == "2":  # Subclass
            print("example:INSERT DATA { :Apple rdfs:subClassOf :Fruit. }")
            subclass_name = input("Enter the name of the subclass: ")
            parent_class_name = input("Enter the name of its parent class: ")
            sparql_query = f"INSERT DATA {{ :{subclass_name} rdfs:subClassOf :{parent_class_name}. }}"

        elif rule_type == "3":  # Equivalent Classes
            print("example:INSERT DATA { :Car owl:equivalentClass :Automobile. }")
            class_name1 = input("Enter the name of the first class: ")
            class_name2 = input("Enter the name of the second class: ")
            sparql_query = f"INSERT DATA {{ :{class_name1} owl:equivalentClass :{class_name2}. }}"

        elif rule_type == "4":  # Disjoint Classes
            print("example:INSERT DATA { :Fruit owl:disjointWith :Vehicle. }")
            class_name1 = input("Enter the name of the first class: ")
            class_name2 = input("Enter the name of the second class: ")
            sparql_query = f"INSERT DATA {{ :{class_name1} owl:disjointWith :{class_name2}. }}"

        elif rule_type == "5":  # Property Declaration
            print("example:INSERT DATA { :isColorOf rdf:type owl:ObjectProperty. }")
            property_name = input("Enter the name of the new property: ")
            sparql_query = f"INSERT DATA {{ :{property_name} rdf:type owl:ObjectProperty. }}"

        elif rule_type == "6":  # Domain and Range
            print("""example:INSERT DATA { 
  :isColorOf rdfs:domain :Color; 
             rdfs:range :Fruit.}""")
            property_name = input("Enter the name of the property: ")
            domain = input("Enter the domain class: ")
            range = input("Enter the range class: ")
            sparql_query = f"INSERT DATA {{ :{property_name} rdfs:domain :{domain}; rdfs:range :{range}. }}"

        elif rule_type == "7":  # Functional Property
            print("example:INSERT DATA { :hasBirthDate rdf:type owl:FunctionalProperty. }")
            property_name = input("Enter the name of the functional property: ")
            sparql_query = f"INSERT DATA {{ :{property_name} rdf:type owl:FunctionalProperty. }}"

        elif rule_type == "8":  # Inverse Properties
            print("example:INSERT DATA { :isParentOf owl:inverseOf :isChildOf. }")
            property1 = input("Enter the name of the first property: ")
            property2 = input("Enter the name of the inverse property: ")
            sparql_query = f"INSERT DATA {{ :{property1} owl:inverseOf :{property2}. }}"

        elif rule_type == "9":  # Transitive Property
            print("example:INSERT DATA { :isPartOf rdf:type owl:TransitiveProperty. }")
            property_name = input("Enter the name of the transitive property: ")
            sparql_query = f"INSERT DATA {{ :{property_name} rdf:type owl:TransitiveProperty. }}"

        elif rule_type == "10":  # Symmetric Property
            print("example:INSERT DATA { :isMarriedTo rdf:type owl:SymmetricProperty. }")
            property_name = input("Enter the name of the symmetric property: ")
            sparql_query = f"INSERT DATA {{ :{property_name} rdf:type owl:SymmetricProperty. }}"

        elif rule_type == "11":  # Asymmetric Property
            print("example:INSERT DATA { :isParentOf rdf:type owl:AsymmetricProperty. }")
            property_name = input("Enter the name of the asymmetric property: ")
            sparql_query = f"INSERT DATA {{ :{property_name} rdf:type owl:AsymmetricProperty. }}"

        # elif rule_type == "12":  # Individual Assertion
        #     individual_name = input("Enter the name of the individual: ")
        #     class_name = input("Enter the class of the individual: ")
        #     sparql_query = f"INSERT DATA {{ :{individual_name} rdf:type :{class_name}. }}"
        #
        # elif rule_type == "13":  # Property Assertion
        #     subject_name = input("Enter the name of the subject individual: ")
        #     property_name = input("Enter the name of the property: ")
        #     object_name = input("Enter the name of the object individual or literal value: ")
        #     sparql_query = f"INSERT DATA {{ :{subject_name} :{property_name} :{object_name}. }}"

        else:
            print("Unsupported rule type selected.")
            return

        print("The following SPARQL query has been prepared for insertion:" + sparql_query)
        return sparql_query


if __name__ == "__main__":
    # Assuming MemoryStreamAccess and GPTManager are properly initialized elsewhere
    memory_stream = MemoryStreamAccess()
    gpt_manager = GPTManager()

    # Initialize the OntologyManager with the required components
    ontology_manager = OntologyManager(memory_stream, gpt_manager)

    # Load the ontology (assuming the ontology file path is known)
    ontology_path = "path/to/your/ontology/file.owl"
    ontology_manager.load_ontology(ontology_path)

    # Example usage: Add a new rule to the ontology
    # This will invoke the interactive process to select and define a new rule
    ontology_manager.add_new_rule_to_ontology()
