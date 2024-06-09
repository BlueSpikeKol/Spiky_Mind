"""
in order to enable the next step, we will load an already made ontology and sow inside of it metadata that will be
vectorized for the listener bot to be able to match it with the questions of the explorer bot.
"""

"""
the listener bot will be more complex. He will have to look at the question from the explorer bot
(Natural Language Query or NLQ) and transform it into a SPARQL query that is applicable to the ontology
(Accurate Sparql Query or ASQ). to do this he will have to:
parse the NLQ(the goal is to use clusters to separate different subjects, testing will be required) vectorize the 
relevent clusters of information into multiple NLQs, vectorize the parsed NLQs, compare them to the ontology using
vector comparison, find a match, either directly or with a traversal algorithm and finally transform the NLQS with the 
information matched to transform them into ASQs.
"""