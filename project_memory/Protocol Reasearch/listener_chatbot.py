"""
the listener bot will be more complex. He will have to look at the question from the explorer bot
(Natural Language Query or NLQ) and transform it into a SPARQL query that is applicable to the ontology
(Accurate Sparql Query or ASQ). to do this he will have to:
parse the NLQ(the goal is to use clusters to separate different subjects, testing will be required) vectorize the
relevent clusters of information into multiple NLQs, vectorize the parsed NLQs, compare them to the ontology using
vector comparison, find a match, either directly or with a traversal algorithm and finally transform the NLQS with the
information matched to transform them into ASQs.
"""


class ListenerChatbot:
    def __init__(self):
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

    def parse_NLQ_into_clusters(self):
        # parse the NLQ into clusters
        pass

    def vectorize_clusters(self):
        # vectorize the clusters
        pass

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

    def create_low_quality_sparql_queries(self) -> list:
        # Generate initial SPARQL queries from clusters
        pass

    def refine_query(self, query) -> str:
        # Refine the query until it's accurate
        pass

    def test_query(self, query):
        # Test the query for accuracy
        pass

    def explore_ontology(self, query) -> str:
        # Explore the ontology to refine the query further
        pass


