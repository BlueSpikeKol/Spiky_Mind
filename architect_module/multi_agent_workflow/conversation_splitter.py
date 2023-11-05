import re

from utils.openai_api.models import ModelType


class ConversationSplitter:
    def __init__(self, parent_convo, agent_manager):
        self.split_conversations = []
        self.parent_convo = parent_convo
        self.agent_manager = agent_manager

    def split_conversation(self, conversation_summary: str):
        side_topics = self.extract_side_topics(conversation_summary)

        self.split_conversations.clear()

        self.split_conversations = side_topics

    import re

    def extract_side_topics(self, conversation_summary):
        topic_extractor_system_prompt = (
            "You will be given a debate transcript. "
            "The debate will probably be technical and will probably come up with decisions concerning code. "
            "Your goal is to extract a list of Final Solutions. Final solutions are features that the debaters have chosen to implement. "
            "Your goal is to basically to either detect potential small conversations in the main debate to spark smaller debates or to find ready solutions to be implemented "
            "(mainly the creation of python code in the source code of a project). "
            "If a problem is still being discussed, you cannot add it to the list. You cannot have more than 6 FinalSolutions to present at a time. "
            "You must give your list with the following template: "
            "Final Solution List:[<FinalSolution1>,<why is it worthy of being a FinalSolution(50 words max)>],"
            "[<FinalSolution2>,<why is it worthy of being a FinalSolution(50 words max)>],"
            "[<etc>]"
            "\n\n"
            "For instance, here are three Final Solutions extracted from a recent debate:"
            "[1. \"Incorporate Docker for environment management\", "
            "This solution merits implementation because it ensures consistent environments across development, staging, and production, preventing the 'it works on my machine' syndrome.],"
            "[2. \"Utilize WebSockets for real-time data communication\", "
            "Crucial for its ability to provide live, two-way interaction between users and servers, which is essential for responsive user experiences.],"
            "[3. \"Enforce code linting and formatting standards\", "
            "Imperative for maintaining a uniform codebase, significantly easing collaboration, maintenance, and reducing the likelihood of syntax-related bugs.]"
        )

        topic_extractor = self.agent_manager.create_agent(model=ModelType.CHAT_GPT4, max_tokens=600,
                                                          temperature=0.2, system_prompt=topic_extractor_system_prompt,
                                                          messages=conversation_summary)
        topic_extractor.run_agent()
        topics_str = topic_extractor.get_text()
        print(topics_str)

        # Adjusted pattern to capture only the final solution part before the comma
        topics = re.findall(r'\[([^,]*),', topics_str)

        side_topics = self.determine_convo_type_and_append(topics, conversation_summary)
        return side_topics

    def determine_convo_type_and_append(self, topics, conversation_summary) -> list:
        side_topics = []
        for topic in topics:
            # Ask for user input to determine the type
            print(f"Topic: {topic}")
            convo_type = input("Type 'c' for high-level debate, 'f' for low-level coding, or 'd' to drop the topic: ")

            # Validate user input
            while convo_type not in ['c', 'f', 'd']:
                print("Invalid input. Enter 'c' for conversation, 'f' for function creator, or 'd' to drop the topic.")
                convo_type = input(
                    "Type 'c' for high-level debate, 'f' for low-level coding, or 'd' to drop the topic: ")

            if convo_type == 'd':
                print(f"Topic '{topic}' dropped and will not be used.")
                continue  # Skip this topic and continue with the next one

            if convo_type == 'c':
                content_extractor_system_prompt = f"You will be given a debate transcript and a corresponding topic." \
                                                  f"Your goal is to regroup all the information that has been said on the topic in a short and direct way, under 75 words."

                context_extractor = self.agent_manager.create_agent(model=ModelType.FUNCTION_CALLING_GPT_3_5, max_tokens=150,
                                                                    temperature=0.5,
                                                                    system_prompt=content_extractor_system_prompt,
                                                                    messages="random filler")

                context_extractor.update_agent(
                    messages=conversation_summary + "this is the topic you must extract" + topic)
                context_extractor.run_agent()
                side_topic_context = context_extractor.get_text()

                # Create the side_topic dictionary
                side_topic = {'side_topic_name': topic, 'side_topic_context': side_topic_context,
                              'side_topic_type': 'side'}

            else:  # convo_type == 'f'
                function_creator_system_prompt = (
                    "You are given a coding task that is associated with a specific topic. "
                    "Your goal is to dissect and understand the coding task in the following dimensions:\n"
                    "- Objective: What is the main goal or functionality that the code must achieve?\n"
                    "- Input: What kind of data will the code receive? Please specify the data type and constraints, if any.\n"
                    "- Output: What should the code return? Again, specify the data type and any constraints.\n"
                    "- Constraints: Are there any limitations or rules that the code must adhere to? For example, are certain libraries or functions disallowed?\n"
                    "- Existing Functions to Utilize: Are there any existing functions that should be used in the code?\n"
                    "Please extract this information in a readable format.")

                function_creator_extractor_agent = self.agent_manager.create_agent(model=ModelType.GPT_3_5_TURBO, max_tokens=150,
                                                                         temperature=0.2,
                                                                         system_prompt=function_creator_system_prompt,
                                                                         messages="random filler")

                function_creator_extractor_agent.update_agent(
                    messages=conversation_summary + "this is the topic you must extract" + topic)
                function_creator_extractor_agent.run_agent()
                side_topic_context = function_creator_extractor_agent.get_text()

                # Create the side_topic dictionary
                side_topic = {'side_topic_name': topic, 'side_topic_context': side_topic_context,
                              'side_topic_type': 'function_creator'}

            # Append to the list
            side_topics.append(side_topic)

        return side_topics

    def get_split_conversations(self):
        return self.split_conversations
