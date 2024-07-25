from owlready2 import *

from project_memory.persistance_access import MemoryStreamAccess
from project_memory.ontology_manager import OntologyManager
from project_memory.protocol_research.query_function_storage import QueryFunctionStorage
from utils.openai_api.gpt_calling import GPTManager, GPTAgent
from utils.openai_api.models import ModelType

MAIN_ONTOLOGY_TESTING_PATH = r"C:\Users\philippe\PycharmProjects\Spiky_Mind\project_memory\ontologies\foodon_ontology.rdf"
ALL_FUNCTION_IDS = []


class QuerySolver:
    def __init__(self, ontology_manager: OntologyManager = None, memory_stream: MemoryStreamAccess = None):
        self.gpt_manager = GPTManager()
        if memory_stream is None:
            self.memory_stream = MemoryStreamAccess()
        else:
            self.memory_stream = memory_stream
        if ontology_manager is None:
            self.ontology_manager = OntologyManager(self.memory_stream, self.gpt_manager)
        else:
            self.ontology_manager = ontology_manager
        if self.ontology_manager.get_ontology_owlready2() is None:
            self.ontology_manager.load_ontology(MAIN_ONTOLOGY_TESTING_PATH)
        self.query_storage = QueryFunctionStorage(self.ontology_manager)
        self.ontology = self.ontology_manager.get_ontology_owlready2()
        self.parsing_tool = None

    def classify_query(self, original_question):
        self.original_NLQ = original_question
        self.parse_NLQ_into_clusters(self.original_NLQ)
        self.vectorize_clusters()
        queries_and_type_dict = self.find_query_types()
        return queries_and_type_dict

    def parse_NLQ_into_clusters(self, query):
        # Use parsing tool and llm to extract queries
        self.NLQ_clusters = ["Is garlic a spice or an herb?", "What are all ways you know to use garlic in dishes?"]

    def vectorize_clusters(self):
        self.NLQ_clusters_vectorized = {}
        for cluster in self.NLQ_clusters:
            vectorizer_agent = self.gpt_manager.create_agent(model=ModelType.TEXT_EMBEDDING_ADA, messages=cluster)
            vectorizer_agent.run_agent()
            vectorized_cluster = vectorizer_agent.get_vector()
            self.NLQ_clusters_vectorized[cluster] = vectorized_cluster

    def find_query_types(self):
        """
        Analyzes clusters of natural language queries (NLQs) and determines the most appropriate query handling function for each cluster based on similarity and metadata analysis using a large language model (LLM).

        This method iterates through each cluster of NLQs, retrieves metadata associated with top candidate query functions, and uses an LLM to decide which function best fits the cluster's needs. The decision is based on a combination of metadata descriptions and LLM inference.

        Steps:
        1. For each cluster, vector representations of the cluster's queries are compared to all available functions using the 'similarity_comparison' method, which returns the top three closest matches with their metadata.
        2. Metadata from these top matches is concatenated and fed to an LLM to determine the most appropriate query function.
        3. The LLM response is parsed to select the chosen function, which is then stored with its rationale.

        Returns:
            dict: A dictionary where each key is a cluster identifier and each value is another dictionary containing:
                  - 'chosen_function_id': The ID of the chosen function based on LLM analysis.
                  - 'chosen_function_name': The name of the function as extracted from the LLM's response.
                  - 'rationale': The LLM's textual rationale for why this function was chosen.

        Raises:
            ValueError: If an invalid function choice number is received from the LLM's response.
            Exception: If no valid function choice is found in the LLM's response.

        Example Usage:
            result_dict = self.find_query_types()
            for cluster, info in result_dict.items():
                print(f"Cluster: {cluster}, Function ID: {info['chosen_function_id']}, Rationale: {info['rationale']}")
        """
        queries_and_type_dict = {}
        for cluster in self.NLQ_clusters:
            vectorized_cluster = self.NLQ_clusters_vectorized[cluster]
            # Call similarity_comparison with return_metadata=True to fetch metadata
            top_k_result = self.memory_stream.similarity_comparison(
                comparison_list_id=ALL_FUNCTION_IDS,
                single_vector_or_id=vectorized_cluster, top_k=3,
                return_metadata=True
            )

            # Collect metadata from each result in top_k_result
            metadata_descriptions = []
            for func_id, _, func_metadata in top_k_result:
                metadata_description = func_metadata.get('function_restriction_str', 'No metadata available')
                metadata_descriptions.append(metadata_description)

            # Concatenate all metadata into a single string
            combined_metadata = " ".join(metadata_descriptions)

            # Use an LLM to analyze the combined metadata and make a decision
            chosen_function_response = self.llm_determine_best_choice(combined_metadata, cluster)

            # Parse the response to extract the choice number and name
            match = re.search(r"\[(\d+)(?:\s*-\s*)([^\]]+)\]", chosen_function_response)
            if match:
                choice_number = int(match.group(1)) - 1  # Convert to zero-based index
                choice_name = match.group(2)
                if 0 <= choice_number < len(top_k_result):
                    chosen_function_id, _, _ = top_k_result[choice_number]
                    # Store the chosen function ID and its name with a rationale into the dictionary
                    queries_and_type_dict[cluster] = {
                        'chosen_function_id': chosen_function_id,
                        'chosen_function_name': choice_name,
                        'rationale': chosen_function_response
                    }
                else:
                    print(f"Invalid choice number received: {choice_number + 1}")
            else:
                print(f"No valid function choice found in response: {chosen_function_response}")

        return queries_and_type_dict

    def llm_determine_best_choice(self, combined_metadata, accompanying_NLQ):
        """
        Uses a large language model to interpret the combined metadata and selects the most appropriate query type.

        :param combined_metadata: A string containing concatenated metadata descriptions.
        :return: The selected query type as a string.
        """
        llm_message = f"Given the metadata for the query types: {combined_metadata}, and the accompanying NLQ(natural language query): {accompanying_NLQ}, " \
                      f"what is the best query type to use?"
        system_prompt = "Choose the best query type to use for the given metadata and NLQ. You must return your answer" \
                        "in two parts: the first part should be the chosen query type(give the number of the chosen and its title between [])," \
                        " and the second part should be the reasoning behind your choice."
        selector_agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=llm_message,
                                                       max_tokens=50,
                                                       system_prompt=system_prompt, temperature=0.3)
        selector_agent.run_agent()
        best_choice = selector_agent.get_text()
        return best_choice

    def construct_query_and_execute(self, query_type, accompanying_NLQ, rationale):
        function_to_execute = self.query_storage.get_query_function(query_function_key=query_type, nlq=accompanying_NLQ,
                                                                    rationale=rationale)
        if function_to_execute is None:
            return "No function found for query type"
        result = function_to_execute()
        return result

    def solve_query(self, query):
        queries_and_type_dict = self.classify_query(query)
        results = {}
        for cluster, query_type in queries_and_type_dict.items():
            cluster_str = str(cluster)
            query_type_id = query_type['chosen_function_id']
            rationale = query_type['rationale']
            single_result = self.construct_query_and_execute(query_type=query_type_id, accompanying_NLQ=cluster_str,
                                                             rationale=rationale)
            results[cluster] = {single_result}
        return results
