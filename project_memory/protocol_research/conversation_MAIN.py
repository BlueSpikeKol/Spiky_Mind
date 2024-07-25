"""The goal of this test is to create the explorer AI and simulate the human that knows thing, that i will now call
the listener, since he simply answers the questions of the explorer"""

"""
The explorer bot will very simply be given a goal(the subject of the ontology) 
and be asked to be curious about the subject ad_infinitum while using the logit bias
(or whatver it is that makes him avoid specific subjects, we simply have to update it from time to time) 
to make sure he doesnt repeat the same questions over and over.
"""

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

from listener_chatbot import ListenerChatbot
from explorer_chatbot import ExplorerChatbot


def build_ontology(explorer_bot: ExplorerChatbot):
    """
    This function will read the information that the explorer bot has gotten from the listener bot and attempt to
    build an ontology from it. the goal is to ressemble the original ontology as much as possible.
    :param explorer_bot:
    :return:
    """
    pass

def main(ontology_subject: str):
    listener = ListenerChatbot()
    explorer = ExplorerChatbot(ontology_subject=ontology_subject)

    while True:
        explorer.ask_question()
        if explorer.question == "exit":
            break
        if explorer.question == "reset":
            explorer.reset()
            continue
        answer = listener.answer_question(explorer.question)
        explorer.update_explorer_memory(answer)
        build_ontology(explorer)

main("test")