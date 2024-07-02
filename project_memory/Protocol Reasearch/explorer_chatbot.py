"""
The explorer bot will very simply be given a goal(the subject of the ontology)
and be asked to be curious about the subject ad_infinitum while using the logit bias
(or whatver it is that makes him avoid specific subjects, we simply have to update it from time to time)
to make sure he doesnt repeat the same questions over and over.
"""

"""
def main():
    listener = ListenerChatbot()
    explorer = ExplorerChatbot()

    while True:
        if explorer.ask_question() == "exit":
            break
        if explorer.ask_question() == "reset":
            explorer.reset()
            continue
        explorer.ask_question()
        listener.answer_question(explorer.question)
        explorer.list_of_anwers.append(listener.answer)
        explorer.update_logit_bias()
        build_ontology(explorer)
"""

from utils.openai_api.gpt_calling import GPTManager, GPTAgent
from utils.openai_api.models import ModelType
import re


class ExplorerChatbot:
    def __init__(self, ontology_subject: str):
        exploration_system_prompt = f"You are a very curious chatbot whose goal is to understand everything about" \
                                    f" a specific subject. Sadly you know very little about the subject but luckily all the questions you ask" \
                                    f" will be answered by a very intelligent computer that never makes mistakes. Here is the" \
                                    f" subject you must explore in creative ways: [{ontology_subject}]"
        base_message = "Ask a new question to explore the subject please"
        self.gpt_manager = GPTManager()
        self.explorer_agent = self.gpt_manager.create_agent(model=ModelType.GPT_4_TURBO, temperature=1.2,
                                                            max_tokens=400, system_prompt=exploration_system_prompt,
                                                            messages=base_message, frequency_penalty=0.5,
                                                            presence_penalty=0.9, logit_bias={})
        self.explorer_direct_memory = []
        self.ontology_subject = ontology_subject
        self.question = ""
        self.list_of_anwers = []
        self.logit_bias = {}

    def ask_question(self):
        test = True
        user_input = "test"
        if test:
            self.question = "Is garlic a spice or an herb? What are all ways you know to use garlic in dishes?"
        else:
            self.explorer_agent.run_agent()
            self.question = self.explorer_agent.get_text()
            self.explorer_direct_memory.append(self.question)
            # print all the answers that are part of the explorer as well as the last exchange
            print(f"Explorer list of answers:\n{self.list_of_anwers}\n")
            print(f"Explorer last question:\n{self.question}\n")
            user_input = input("Type exit to exit or reset to reset the explorer\n")
        if user_input == "exit":
            return "exit"
        if user_input == "reset":
            return "reset"

    def reset(self):
        self.list_of_anwers = []

    def update_explorer_memory(self, listener_answer):
        self.list_of_anwers.append(listener_answer)
        self.explorer_direct_memory.append(listener_answer)
        if len(self.explorer_direct_memory) > 5:
            self.transfer_to_long_term_memory()

    def transfer_to_long_term_memory(self):
        system_prompt = "Choose a few words to represent(summarize) each topic that has been discussed in the text given. " \
                        "No more than 5 words per topic. there may be multiple topics. Put each cluster in between[]." \
                        "ex:[chicken nuggets][oxygen removal][copper wires][electromagnetism][soda]"
        message = f"Here is the text to summarize:{self.explorer_direct_memory}"
        memory_agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, temperature=0.3,
                                                     system_prompt=system_prompt,
                                                     messages=message, max_tokens=150)
        memory_agent.run_agent()
        memory_update = memory_agent.get_text()
        self.explorer_direct_memory = []
        # use a regex pattern to extract the clusters from the memory_update
        pattern = re.compile(r'\[(.*?)\]')
        clustered_memory_update = pattern.findall(memory_update)
        # logit bias only accepts a dictionary of the words and a value between -100 and 100
        for cluster in clustered_memory_update:
            self.logit_bias[cluster] = -50
        self.explorer_agent.update_agent(logit_bias=self.logit_bias)

    def reset_explorer(self):
        self.logit_bias = {}
        self.explorer_direct_memory = []
        self.list_of_anwers = []
