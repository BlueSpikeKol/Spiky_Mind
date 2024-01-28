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

    def extract_side_topics(self, conversation_summary):
        topic_extractor_system_prompt = (
            "You will be given a debate transcript summary. "
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

        topic_extractor = self.agent_manager.create_agent(model=ModelType.CHAT_GPT4_old, max_tokens=600,
                                                          temperature=0.2, system_prompt=topic_extractor_system_prompt,
                                                          messages=conversation_summary)
        topic_extractor.run_agent()
        topics_str = topic_extractor.get_text()
        print(topics_str)

        topics = re.findall(r'"([^"]*)"', topics_str)

        side_topics = self.get_side_topics(topics, conversation_summary)
        return side_topics

    def get_side_topics(self, topics, conversation_summary) -> list:
        """
        This function appends conversation information to the side topics
        based on the conversation type determined by the user input.

        Parameters:
        - topics (list): A list of debate topics.
        - conversation_summary (str): The summary of the conversation.

        Returns:
        - side_topics (list): A list of dictionaries containing the side topics information.
        """
        # First, classify all topics and separate them based on type
        classified_topics = {
            'c': [],  # Conversation topics
            'f': [],  # Function creator topics
        }

        for topic in topics:
            convo_type = self.determine_convo_type(topic)
            if convo_type == 'd':
                continue  # Skip 'd' type topics
            elif convo_type in ['c', 'f']:
                classified_topics[convo_type].append(topic)

        # Now, prepare the string for 'c' type topics
        c_type_topics_string = ', '.join(classified_topics['c'])  # Join all 'c' type topics in a single string

        # Extract contexts for each type after all topics have been classified
        side_topics = []
        if classified_topics['c']:
            # Extract the conversation context for all 'c' type topics at once
            side_topic_context = self.extract_conversation_context(conversation_summary, c_type_topics_string)
            side_topics.append({
                'side_topic_name': None,
                'side_topic_context': side_topic_context,
                'side_topic_type': 'side'
            })

        for topic in classified_topics['f']:
            # 'f' type topics are processed individually
            side_topic_context = self.extract_function_context(conversation_summary, topic)
            side_topics.append({
                'side_topic_name': topic,
                'side_topic_context': side_topic_context,
                'side_topic_type': 'function_creator'
            })

        return side_topics

    def determine_convo_type(self, topic):
        """
        This function determines the type of conversation for a given topic
        based on user input.

        Parameters:
        - topic (str): The debate topic for which the conversation type is to be determined.

        Returns:
        - convo_type (str): A string representing the conversation type ('c', 'f', or 'd').
        """
        print(f"Topic: {topic}")
        convo_type = input("Type 'c' for high-level debate, 'f' for low-level coding, or 'd' to drop the topic: ")

        # Validate user input
        while convo_type not in ['c', 'f', 'd']:
            print("Invalid input. Enter 'c' for conversation, 'f' for function creator, or 'd' to drop the topic.")
            convo_type = input(
                "Type 'c' for high-level debate, 'f' for low-level coding, or 'd' to drop the topic: ")

        if convo_type == 'd':
            print(f"Topic '{topic}' dropped and will not be used.")

        return convo_type

    def extract_conversation_context(self, conversation_summary, all_topics):
        """
        Extracts the conversation context for debate topics.

        Parameters:
        - conversation_summary (str): The summary of the conversation.
        - topic (str): The topic to extract conversation context for.

        Returns:
        - str: Extracted conversation context.
        """
        content_extractor_system_prompt = (
            f"**Main Topics List :[{all_topics}].**"
            "Engage in a thorough examination of a debate transcript, with the mission of extracting "
            "and encapsulating pivotal arguments and data tied to a predetermined list of main topics, "
            "adhering to a stringent 500-word total limit. The goal is to achieve great "
            "identification and categorization of the main subjects at hand. Crystallize "
            "these discussions into a lucid, comprehensive narrative, meticulously sifting out any "
            "irrelevant to avoid retrieving information from irrelevant tics. Intertwine related thematic "
            "elements to achieve a seamless and cogent storyline. You must identify the features that are related to "
            "the main topic list and produce an answer in this format:\n"
            "<75 word to describe general goal, what is the expected input and output>\n"
            "1.<feature1>:<up to 100 words to explain this feature>\n"
            "2.<feature2>:<up to 100 words to explain this feature>\n"
            "etc, max 5 features\n"
            "<How features interact with each other>"
        )

        # Assume self.agent_manager and other required methods are already defined.
        context_extractor = self.agent_manager.create_agent(
            model=ModelType.CHAT_GPT4_old,
            max_tokens=700,
            temperature=0.4,
            system_prompt=content_extractor_system_prompt,
            messages=conversation_summary
        )
        context_extractor.run_agent()
        return context_extractor.get_text()

    def extract_function_context(self, conversation_summary, topic):
        """
        Extracts the function context for coding task topics.

        Parameters:
        - conversation_summary (str): The summary of the conversation.
        - topic (str): The topic to extract function context for.

        Returns:
        - str: Extracted function context.
        """
        function_creator_system_prompt = (
            "You are given a coding task that is associated with a specific topic. "
            "Your goal is to dissect and understand the coding task in the following dimensions:\n"
            "- Objective: What is the main goal or functionality that the code must achieve?\n"
            "- Input: What kind of data will the code receive? Please specify the data type and constraints, if any.\n"
            "- Output: What should the code return? Again, specify the data type and any constraints.\n"
            "- Constraints: Are there any limitations or rules that the code must adhere to? For example, are certain libraries or functions disallowed?\n"
            "- Existing Functions to Utilize: Are there any existing functions that should be used in the code?\n"
            "Please extract this information in a readable format.")

        # Assume self.agent_manager and other required methods are already defined.
        function_creator_extractor_agent = self.agent_manager.create_agent(
            model=ModelType.GPT_3_5_TURBO,
            max_tokens=500,
            temperature=0.2,
            system_prompt=function_creator_system_prompt,
            messages=conversation_summary + " this is the topic you must extract: " + topic
        )
        function_creator_extractor_agent.run_agent()
        return function_creator_extractor_agent.get_text()

    def get_split_conversations(self):
        return self.split_conversations
