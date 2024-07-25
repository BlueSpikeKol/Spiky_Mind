from project_memory.ontology_manager import OntologyManager


class QueryFunctionStorage:
    def __init__(self, onotology_manager: OntologyManager):
        # This setup assumes that the functions are dynamically identified by a unique key including a UUID.
        self.query_functions = {}
        self.ontology_manager = onotology_manager
        self.ontology_object = self.ontology_manager.get_ontology_owlready2()
        self.setup_query_functions()

    def setup_query_functions(self):
        # Manually specified keys mapping directly to functions
        self.query_functions = {
            'unique_key_for_is_a_query': self.is_a_query,
            'unique_key_for_superclass_query': self.superclass_query,
            'unique_key_for_subclass_query': self.subclass_query,
            'unique_key_for_attribute_query': self.attribute_query,
            'unique_key_for_relationship_query': self.relationship_query,
            'unique_key_for_specific_instance_query': self.specific_instance_query,
            'unique_key_for_instance_counting_query': self.instance_counting_query,
            'unique_key_for_pathfinding_query': self.pathfinding_query,
            'unique_key_for_role_exploration_query': self.role_exploration_query,
            'unique_key_for_behavioral_query': self.behavioral_query,
            'unique_key_for_causal_query': self.causal_query,
            'unique_key_for_comparison_query': self.comparison_query,
            'unique_key_for_evaluation_query': self.evaluation_query,
            'unique_key_for_definition_query': self.definition_query,
            'unique_key_for_category_identification_query': self.category_identification_query,
            'unique_key_for_contextual_query': self.contextual_query,
            'unique_key_for_hypothetical_scenarios_query': self.hypothetical_scenarios_query,
            'unique_key_for_metadata_query': self.metadata_query,
            'unique_key_for_ontology_structure_query': self.ontology_structure_query
        }

    def get_query_function(self, query_function_key, nlq, rationale=None):
        query_function = self.query_functions.get(query_function_key)
        if not query_function:
            print(f"No query function found for key {query_function_key}")
            return None
        return query_function(nlq=nlq, rationale=rationale)

    # Example query function implementations
    def is_a_query(self, nlq, rationale=None):
        print("Executing an Is-A query.")
        return {}

    def superclass_query(self, nlq, rationale=None):
        print("Executing a Superclass query.")
        return {}

    def subclass_query(self, nlq, rationale=None):
        print("Executing a Subclass query.")
        return {}

    def attribute_query(self, nlq, rationale=None):
        print("Executing an Attribute query.")
        return {}

    def relationship_query(self, nlq, rationale=None):
        print("Executing a Relationship query.")
        return {}

    def specific_instance_query(self, nlq, rationale=None):
        print("Executing a Specific Instance query.")
        return {}

    def instance_counting_query(self, nlq, rationale=None):
        print("Executing an Instance Counting query.")
        return {}

    def pathfinding_query(self, nlq, rationale=None):
        print("Executing a Pathfinding query.")
        return {}

    def role_exploration_query(self, nlq, rationale=None):
        print("Executing a Role Exploration query.")
        return {}

    def behavioral_query(self, nlq, rationale=None):
        print("Executing a Behavioral query.")
        return {}

    def causal_query(self, nlq, rationale=None):
        print("Executing a Causal query.")
        return {}

    def comparison_query(self, nlq, rationale=None):
        print("Executing a Comparison query.")
        return {}

    def evaluation_query(self, nlq, rationale=None):
        print("Executing an Evaluation query.")
        return {}

    def definition_query(self, nlq, rationale=None):
        print("Executing a Definition query.")
        return {}

    def category_identification_query(self, nlq, rationale=None):
        print("Executing a Category Identification query.")
        return {}

    def contextual_query(self, nlq, rationale=None):
        print("Executing a Contextual query.")
        return {}

    def hypothetical_scenarios_query(self, nlq, rationale=None):
        print("Executing a Hypothetical Scenarios query.")
        return {}

    def metadata_query(self, nlq, rationale=None):
        print("Executing a Metadata query.")
        return {}

    def ontology_structure_query(self, nlq, rationale=None):
        print("Executing an Ontology Structure query.")
        return {}


