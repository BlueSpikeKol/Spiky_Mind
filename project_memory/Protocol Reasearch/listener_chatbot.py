"""
the listener bot will be more complex. He will have to look at the question from the explorer bot
(Natural Language Query or NLQ) and transform it into a SPARQL query that is applicable to the ontology
(Accurate Sparql Query or ASQ). to do this he will have to:
parse the NLQ(the goal is to use clusters to separate different subjects, testing will be required) vectorize the
relevent clusters of information into multiple NLQs, vectorize the parsed NLQs, compare them to the ontology using
vector comparison, find a match, either directly or with a traversal algorithm and finally transform the NLQS with the
information matched to transform them into ASQs.
"""
import re

from project_memory.persistance_access import MemoryStreamAccess
from project_memory.ontology_manager import OntologyManager
from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType

MAIN_ONTOLOGY_TESTING_PATH = r"C:\Users\philippe\PycharmProjects\Spiky_Mind\project_memory\ontologies\foodon_ontology.rdf"


class ListenerChatbot:
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
        self.NLQ = ""
        self.NLQ_clusters = []
        self.NLQ_clusters_vectorized = []
        self.ASQs = []
        self.answer = ""

    def answer_question(self, question: str):
        # parse the NLQ into clusters
        self.NLQ = question
        self.parse_NLQ_into_clusters()
        self.vectorize_clusters()
        self.create_ASQs()
        return self.answer

    def parse_NLQ_into_clusters(self):  # will use the smart parsing tool. for now its a stub
        # parse the NLQ into clusters
        self.NLQ_clusters = ["Is garlic a spice or an herb?", "What are all ways you know to use garlic in dishes?"]

    def vectorize_clusters(self):
        self.NLQ_clusters_vectorized = []
        for cluster in self.NLQ_clusters:
            vectorizer_agent = self.gpt_manager.create_agent(model=ModelType.TEXT_EMBEDDING_ADA, messages=cluster)
            vectorizer_agent.run_agent()
            vectorized_cluster = vectorizer_agent.get_vector()
            self.NLQ_clusters_vectorized.append(vectorized_cluster)

    def create_ASQs(self):
        # Generate initial SPARQL queries from clusters
        initial_queries = self.create_low_quality_sparql_queries()

        for query in initial_queries:
            is_accurate = False
            refined_query = ""
            # Try refining the query until it's accurate
            while not is_accurate:
                refined_query = self.refine_query(query)
                is_accurate = self.test_query(refined_query)

                if not is_accurate:
                    # If still not accurate, explore ontology to refine it further
                    refined_query = self.explore_ontology(refined_query)
                    is_accurate = self.test_query(refined_query)

            # If query is accurate, add to the list of Accurate SPARQL Queries (ASQs)
            if is_accurate:
                self.ASQs.append(refined_query)
            else:
                # If not accurate after exploration, append an error message
                self.ASQs.append("I'm sorry, I could not find an answer to your question")

    def create_low_quality_sparql_queries(self, test=True) -> list:
        low_quality_queries = []
        predefined_sparql_queries = [{'nlq': 'Is garlic a spice or an herb?',
                                      'sparql': 'SELECT ?garlicType\nWHERE {\n  :Garlic a ?garlicType .\n}'},
                                     {'nlq': 'What are all ways you know to use garlic in dishes?',
                                      'sparql': 'SELECT ?way \nWHERE {\n  :Garlic :canBeUsedIn ?way .\n}'}]

        if test and predefined_sparql_queries:
            # Populate the list with dictionaries containing NLQ and SPARQL from predefined queries
            low_quality_queries = predefined_sparql_queries
        else:
            system_prompt = "transform this NLQ(natural language query) into a spaql query that explores my local personalized ontology(no outside data, such as wikidata)" \
                            "if it is not possible, still create something but add comments as to why it might be incorrect(very short comments).put your query between ```"
            NLQ_to_sparql_agent = self.gpt_manager.create_agent(
                model=ModelType.GPT_3_5_TURBO,
                messages="placeholder message",
                temperature=0.3,
                system_prompt=system_prompt
            )

            for cluster in self.NLQ_clusters:
                NLQ_to_sparql_agent.update_agent(messages=cluster)
                NLQ_to_sparql_agent.run_agent()

                low_quality_query = NLQ_to_sparql_agent.get_text()
                low_quality_query_cleaned = self.extract_sparql_query(low_quality_query)

                # Append a dictionary for each cluster containing both the NLQ and SPARQL
                low_quality_queries.append({'nlq': cluster, 'sparql': low_quality_query_cleaned})

        return low_quality_queries

    def extract_sparql_query(self, text):
        # Regex to find content enclosed in triple backticks
        pattern = r"```(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def refine_query(self, query: dict) -> str:
        isolated_parts = self.isolate_problematic_query_parts(query)
        refined_parts = self.correlate_to_ontology(isolated_parts)
        refined_query = self.recombine_query_parts(refined_parts)
        return refined_query

    def isolate_problematic_query_parts(self, query_dict: dict) -> dict:
        """The goal of this function is to identify where the SPARQL part of the query could be misaligned with the ontology
        and reason of the misalignment, which will then be used to correct the misalignment."""

        # Normalize the SPARQL query part of the dictionary
        sparql_query = self.precise_normalize_shorthand(query_dict['sparql'])

        # Initialize dictionary to collect problems with corresponding messages
        problems_with_messages = {}

        # Extract PREFIX lines to check for declared but unused or undeclared but used prefixes
        prefix_pattern = r"(PREFIX\s+\w+:\s+<[^>]+>)"
        # Example captured: PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        prefixes = re.findall(prefix_pattern, sparql_query)
        if prefixes:
            problems_with_messages['prefixes'] = {
                'found': prefixes,
                'message': "Check if all prefixes are used in the query or if any undeclared prefixes are used."
            }

        # Extract triple patterns, accounting for normalized and direct predicate references
        triple_pattern = r"(\?\w+|:\w+)\s+(rdf:type|\w+:\w+)\s+(\?\w+|:\w+|\w+)"
        # Example captured: ?person rdf:type foaf:Person
        triples = re.findall(triple_pattern, sparql_query)
        if triples:
            problems_with_messages['triples'] = {
                'found': triples,
                'message': "Ensure predicates align with the ontology and that class and properties also align with the ontology."
            }

        # Extract FILTER conditions
        filter_pattern = r"(FILTER\s+\([^)]+\))"
        # Example captured: FILTER (LANG(?label) = "en")
        filters = re.findall(filter_pattern, sparql_query)
        if filters:
            problems_with_messages['filters'] = {
                'found': filters,
                'message': "Verify correctness of FILTER expressions, especially language tags and logical operators."
            }

        # Check for potential literal and datatype issues
        literal_pattern = r"\"([^\"]+)\"(?:\^\^<([^>]+)>|@(\w+))"
        # Example captured: "example"@en or "42"^^xsd:int
        literals = re.findall(literal_pattern, sparql_query)
        if literals:
            problems_with_messages['literals'] = {
                'found': literals,
                'message': "Check for correct datatype usage and language tags for literals."
            }

        # Detect complex constructs like OPTIONAL, UNION
        complex_constructs_pattern = r"(OPTIONAL\s*{[^}]+})|(UNION\s*{[^}]+})"
        # Example captured: OPTIONAL { ?person foaf:age ?age }
        complex_constructs = re.findall(complex_constructs_pattern, sparql_query)
        if complex_constructs:
            problems_with_messages['complex_constructs'] = {
                'found': complex_constructs,
                'message': "Ensure proper use of OPTIONAL and UNION constructs for intended logical query flow."
            }

        # Detect misuse of aggregation functions without GROUP BY
        aggregation_pattern = r"(SELECT\s+(?:(?!GROUP BY).)*?((SUM|AVG|COUNT|MIN|MAX)\(\?\w+\))[^;]+)"
        # Example captured: SELECT (COUNT(?person) AS ?personCount) WHERE { ... }
        aggregations = re.findall(aggregation_pattern, sparql_query, re.IGNORECASE)
        if aggregations:
            problems_with_messages['aggregations'] = {
                'found': aggregations,
                'message': "Aggregation functions detected. Ensure a GROUP BY clause is used when necessary."
            }

        # Add detected problems with their messages to the original query dictionary
        query_dict['problems'] = problems_with_messages

        return query_dict

    def precise_normalize_shorthand(self, query: str) -> str:
        # Replace ' a ' when used as a predicate with spaces around to ensure it is the shorthand for rdf:type
        query = re.sub(r'\b(?<!\.)a\b', ' rdf:type ', query)  # improved to handle edge cases and avoid dots
        return query

    @staticmethod
    def is_applicable_property(owl_class, property_class_list):
        """ Check if owl_class is the same as or a subclass of any class in property_class_list """
        if owl_class in property_class_list:
            return True
        for superclass in owl_class.ancestors():
            if superclass in property_class_list:
                return True
        return False

    def handle_triples(self, triple_parts, problem_type, original_question):
        if isinstance(triple_parts, tuple):
            triple = ' '.join(triple_parts)  # Converts tuple to a space-separated string
        else:
            triple = triple_parts  # It's already a string, proceed as normal

        triple_pattern = re.compile(r"(\?\w+|:\w+)\s+(\w+:\w+|a)\s+(\?\w+|:\w+|\w+)")
        corrections_for_triple = []
        match = triple_pattern.match(triple)

        if match:
            subject, predicate, object = match.groups()
            components = [subject, object]  # Handle class components first

            # Resolve classes
            class_corrections = {}
            for component in components:
                # Generate and process descriptions for classes
                description_generator = self.gpt_manager.create_agent(
                    model=ModelType.GPT_3_5_TURBO,
                    system_prompt="Describe the class in the context of the ontology.",
                    messages=f"Ontologic class: {component}. Context: {triple} + {original_question}.",
                    temperature=0.3,
                    max_tokens=100
                )
                description_generator.run_agent()
                semantic_description = description_generator.get_text()

                vectorizer_agent = self.gpt_manager.create_agent(
                    model=ModelType.TEXT_EMBEDDING_ADA,
                    messages=semantic_description
                )
                vectorizer_agent.run_agent()
                part_vector = vectorizer_agent.get_vector()

                most_similar_vector_list = self.memory_stream.query_similar_vectors(vector=part_vector, k=3,
                                                                                    scope="classes")
                class_corrections[component] = most_similar_vector_list

            # Resolve property based on updated classes
            if all(k in class_corrections for k in [subject, object]):
                updated_subject = class_corrections[subject][0][0]  # Assuming the first result is the best match
                updated_object = class_corrections[object][0][0]
                onto = None
                if self.ontology_manager.get_ontology_owlready2():
                    onto= self.ontology_manager.get_ontology_owlready2()
                else:
                    self.ontology_manager.load_ontology(MAIN_ONTOLOGY_TESTING_PATH)
                    onto = self.ontology_manager.get_ontology_owlready2()
                applicable_properties = [
                    prop for prop in onto.object_properties()
                    if self.is_applicable_property(updated_subject, prop.domain) and self.is_applicable_property(
                        updated_object,
                        prop.range)
                ]

                corrections_for_triple.append({
                    'original': predicate,
                    'suggested_corrections': [prop.name for prop in applicable_properties],
                    'reason': f"Object properties fitting the domain of {updated_subject} and range of {updated_object}."
                })

            corrections_for_triple.extend([
                {'original': subject, 'suggested_correction': class_corrections[subject][0],
                 'reason': 'Class correction based on semantic similarity.'},
                {'original': object, 'suggested_correction': class_corrections[object][0],
                 'reason': 'Class correction based on semantic similarity.'}
            ])

        return corrections_for_triple

    def correlate_to_ontology(self, isolated_parts: dict) -> list:
        corrections = []

        for problem_type, details in isolated_parts['problems'].items():
            found_parts = details['found']
            for part in found_parts:
                if problem_type == 'triples':
                    triple_corrections = self.handle_triples(part, problem_type, isolated_parts['nlq'])
                    corrections.append({
                        'original': part,
                        'corrections': triple_corrections
                    })
                else:
                    # Handle other problem types with generic description, vectorization, and matching
                    description_generator = self.gpt_manager.create_agent(
                        model=ModelType.GPT_3_5_TURBO,
                        messages=f"Ontologic object: {part}. Problem type: {problem_type}",
                        temperature=0.3,
                        max_tokens=100
                    )
                    description_generator.run_agent()
                    semantic_description = description_generator.get_text()

                    vectorizer_agent = self.gpt_manager.create_agent(
                        model=ModelType.TEXT_EMBEDDING_ADA,
                        messages=semantic_description
                    )
                    vectorizer_agent.run_agent()
                    part_vector = vectorizer_agent.get_vector()

                    most_similar_vector_list = self.memory_stream.query_similar_vectors(vector=part_vector, k=3)

                    correction = {
                        'original': part,
                        'suggested_correction': most_similar_vector_list[0],
                        'reason': f"Based on semantic similarity to '{semantic_description}'."
                    }
                    corrections.append(correction)

        return corrections

    def recombine_query_parts(self, refined_parts) -> str:
        # Recombine the refined parts into a single query
        pass

    def test_query(self, query):
        # Test the query for accuracy
        pass

    def explore_ontology(self, query) -> str:
        # Explore the ontology to refine the query further
        pass
