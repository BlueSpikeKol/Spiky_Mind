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

import owlready2

from project_memory.persistance_access import MemoryStreamAccess
from project_memory.ontology_manager import OntologyManager
from project_memory.protocol_research.query_solver import QuerySolver
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
        if self.ontology_manager.get_ontology_owlready2() is None:
            self.ontology_manager.load_ontology(MAIN_ONTOLOGY_TESTING_PATH)
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

    # not useful for now since we use owlready2 instead of queries
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
        """ Check if owl_class is the same as or a subclass of any class in property_class_list. """
        if not property_class_list:  # Handle None or empty scenarios
            return False

        # Ensure property_class_list is a list, even if it's a single class or set
        if not isinstance(property_class_list, list):
            property_class_list = [property_class_list]

        # Create a set for efficient membership checks
        class_set = set(property_class_list)

        # Check if the class itself or any of its ancestors is in the class set
        return owl_class in class_set or any(
            superclass in class_set for superclass in owl_class.ancestors(include_self=True))

    def handle_triples(self, triple_parts, original_question, use_dummy_data=False):
        if use_dummy_data:
            return self.get_dummy_corrections()
        else:
            triple = ' '.join(triple_parts) if isinstance(triple_parts, tuple) else triple_parts
            corrections_for_triple = []
            subject, predicate, object = self.extract_triple_parts(triple)

            class_corrections = self.resolve_classes([subject, object], triple, original_question)
            if class_corrections:
                corrections_for_triple.extend(self.resolve_properties(subject, object, class_corrections, predicate))
                corrections_for_triple.extend(self.format_class_corrections(class_corrections))

            return corrections_for_triple

    def extract_triple_parts(self, triple):
        triple_pattern = re.compile(r"(\?\w+|:\w+)\s+(\w+:\w+|a)\s+(\?\w+|:\w+|\w+)")
        match = triple_pattern.match(triple)
        if match:
            return match.groups()
        return None, None, None

    def resolve_classes(self, components, triple, original_question):
        class_corrections = {}
        for component in components:
            semantic_description = self.generate_class_description(component, triple, original_question)
            part_vector = self.generate_vector(semantic_description)
            class_corrections[component] = self.get_similar_classes(part_vector)
        return class_corrections

    def generate_class_description(self, component, triple, original_question):
        description_generator = self.gpt_manager.create_agent(
            model=ModelType.GPT_3_5_TURBO,
            system_prompt="Describe the class in the context of the ontology.",
            messages=f"Ontologic class: {component}. Context: {triple} + {original_question}.",
            temperature=0.3,
            max_tokens=100
        )
        description_generator.run_agent()
        return description_generator.get_text()

    def generate_vector(self, semantic_description):
        vectorizer_agent = self.gpt_manager.create_agent(
            model=ModelType.TEXT_EMBEDDING_ADA,
            messages=semantic_description
        )
        vectorizer_agent.run_agent()
        return vectorizer_agent.get_vector()

    def get_similar_classes(self, part_vector):
        most_similar_vector_list = self.memory_stream.query_similar_vectors(vector=part_vector, k=3,
                                                                            strip_UUID=True, return_metadata=True)
        return [self.ontology_manager.get_class_by_iri(metadata['iri']) for _, _, metadata in most_similar_vector_list]

    def resolve_properties(self, subject, object, class_corrections, predicate):
        corrections = []
        if subject in class_corrections and object in class_corrections:
            updated_subject = class_corrections[subject][0]
            updated_object = class_corrections[object][0]
            onto = self.ontology_manager.get_ontology_owlready2()
            applicable_properties = self.find_applicable_properties(updated_subject, updated_object, onto)
            corrections.append({
                'original': predicate,
                'suggested_corrections': applicable_properties,
                'reason': f"Object properties fitting the domain of {updated_subject.label.first()} and range of {updated_object.label.first()}."
            })
        return corrections

    def find_applicable_properties(self, updated_subject, updated_object, onto):
        applicable_properties = []
        for prop in onto.object_properties():
            if self.is_applicable_property(updated_subject, prop.domain) and \
                    self.is_applicable_property(updated_object, prop.range):
                domain_info, range_info = self.get_property_details(prop)
                applicable_properties.append({
                    'iri': prop.iri,
                    'label': prop.label[0] if prop.label else prop.name,
                    'domain': domain_info,
                    'range': range_info
                })
        return applicable_properties

    def get_property_details(self, prop):
        domain_info = {'iri': prop.domain[0].iri, 'label': prop.domain[0].label.first() if prop.domain else "No Label"}
        range_info = {'iri': prop.range[0].iri, 'label': prop.range[0].label.first() if prop.range else "No Label"}
        return domain_info, range_info

    def format_class_corrections(self, class_corrections):
        formatted_corrections = []
        for key, corrections in class_corrections.items():
            formatted_corrections.append({
                'original': key,
                'suggested_correction': {
                    'iri': corrections[0].iri,
                    'label': corrections[0].label.first() if corrections[0].label else "No Label"
                },
                'reason': 'Class correction based on semantic similarity.'
            })
        return formatted_corrections

    def get_dummy_corrections(self):
        return {
            'predicate_corrections': [
                {
                    'original': ':hasType',
                    'suggested_corrections': [
                        {
                            'iri': 'http://purl.obolibrary.org/obo/FOODON_00002420',
                            'label': 'has ingredient',
                            'domain': {
                                'iri': 'http://purl.obolibrary.org/obo/FOODON_00002403',
                                'label': 'food material'
                            },
                            'range': {
                                'iri': 'http://purl.obolibrary.org/obo/FOODON_00001002',
                                'label': 'food product'
                            }
                        },
                        {
                            'iri': 'http://purl.obolibrary.org/obo/RO_0002434',
                            'label': 'interacts with',
                            'domain': {
                                'iri': 'http://purl.obolibrary.org/obo/BFO_0000040',
                                'label': 'material entity'
                            },
                            'range': {
                                'iri': 'http://purl.obolibrary.org/obo/BFO_0000040',
                                'label': 'material entity'
                            }
                        },
                        {
                            'iri': 'http://purl.obolibrary.org/obo/RO_0002448',
                            'label': 'directly regulates activity of',
                            'domain': {
                                'iri': 'http://purl.obolibrary.org/obo/BFO_0000040',
                                'label': 'material entity'
                            },
                            'range': {
                                'iri': 'http://purl.obolibrary.org/obo/BFO_0000040',
                                'label': 'material entity'
                            }
                        },
                        {
                            'iri': 'http://purl.obolibrary.org/obo/RO_0011002',
                            'label': 'regulates activity of',
                            'domain': {
                                'iri': 'http://purl.obolibrary.org/obo/BFO_0000040',
                                'label': 'material entity'
                            },
                            'range': {
                                'iri': 'http://purl.obolibrary.org/obo/BFO_0000040',
                                'label': 'material entity'
                            }
                        },
                        {
                            'iri': 'http://purl.obolibrary.org/obo/RO_0002449',
                            'label': 'directly negatively regulates activity of',
                            'domain': {
                                'iri': 'http://purl.obolibrary.org/obo/BFO_0000040',
                                'label': 'material entity'
                            },
                            'range': {
                                'iri': 'http://purl.obolibrary.org/obo/BFO_0000040',
                                'label': 'material entity'
                            }
                        },
                        {
                            'iri': 'http://purl.obolibrary.org/obo/RO_0002450',
                            'label': 'directly positively regulates activity of',
                            'domain': {
                                'iri': 'http://purl.obolibrary.org/obo/BFO_0000040',
                                'label': 'material entity'
                            },
                            'range': {
                                'iri': 'http://purl.obolibrary.org/obo/BFO_0000040',
                                'label': 'material entity'
                            }
                        }
                    ],
                    'reason': "Object properties fitting the domain of spice or herb and range of spice food product."
                }
            ],
            'class_corrections': [
                {
                    'original': ':Garlic',
                    'suggested_correction': {
                        'iri': 'http://purl.obolibrary.org/obo/FOODON_00001242',
                        'label': 'spice or herb'
                    },
                    'reason': 'Class correction based on semantic similarity.'
                },
                {
                    'original': '?garlicType',
                    'suggested_correction': {
                        'iri': 'http://purl.obolibrary.org/obo/FOODON_03303380',
                        'label': 'spice food product'
                    },
                    'reason': 'Class correction based on semantic similarity.'
                }
            ]
        }

    def correlate_to_ontology(self, isolated_parts: dict) -> list:
        corrections = []

        for problem_type, details in isolated_parts['problems'].items():
            found_parts = details['found']
            for part in found_parts:
                if problem_type == 'triples':
                    triple_corrections = self.handle_triples(part, isolated_parts['nlq'], use_dummy_data=True)
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
