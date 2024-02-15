import re
from pathlib import Path
from typing import List

from utils.openai_api.gpt_calling import GPTAgent, GPTManager
from utils.openai_api.models import ModelType
from utils.openai_api.agent_sessions.trajectory import ConversationTrajectory, ConversationRound
from utils.persistance_access import MemoryStreamAccess


class TrajectoryListener:
    def __init__(self):
        self.round_history = []  # Stores all rounds observed by the listener
        self.gpt_manager = GPTManager()
        self.memory_stream = MemoryStreamAccess()

    def on_new_round(self, last_round: ConversationRound, objective):
        """
        Called when a new round is added to the session.
        :param last_round: The last round that was added to the trajectory.
        :param objective: The current objective of the discussion session.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def on_new_user_msg(self, user_message: str) -> str:
        """
        Processes a new user message and returns context or an answer.
        :param user_message: The message from the user.
        :return: The context to answer to the user message.
        """
        return ""


class TrajectoryListenerCategorizer(TrajectoryListener):
    def __init__(self, categories: List[str]):
        super().__init__()
        self.categories: List[str] = categories
        self.categorization_results: List[str] = []
        # Stores the category of each round for future reference or premade conversations.

    def on_new_round(self, last_round: ConversationRound,
                     objective: str) -> None:  # TODO better categorization needs to be found, make it editable by user
        categories_string = ", ".join(self.categories)
        system_prompt = (f"Please categorize the following conversation round(s), centered around [{objective}], "
                         f"into one of the following categories: {categories_string}.")
        round_string = f"User: {last_round.user_message.content}\nAI: {last_round.ai_message.content}"

        categorizer_agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO,
                                                          system_prompt=system_prompt,
                                                          messages=round_string, temperature=0.1, max_tokens=10)
        categorizer_agent.run_agent()
        categorizer_output = categorizer_agent.get_text().strip()

        found_category = "Uncategorized"  # Default category if no match is found
        for category in self.categories:
            if category.lower() in categorizer_output.lower():  # Case-insensitive match
                found_category = category
                break

        last_round.set_category(found_category)
        self.categorization_results.append(found_category)  # Save the result

    def set_round_category(self, last_round: ConversationRound, category: str) -> None:
        if category in self.categories:
            last_round.set_category(category)
        else:
            print(f"Warning: Category '{category}' not recognized. Setting to 'Uncategorized'.")
            last_round.set_category("Uncategorized")

    def get_categorization_results(self) -> List[str]:
        # Returns the list of categories assigned to rounds, useful for creating premade conversations(premade_categories)
        return self.categorization_results


class TrajectoryListenerVectorSearch(TrajectoryListener):
    def __init__(self):
        super().__init__()

    def on_new_user_msg(self, user_message: str) -> str:
        """
        Processes a new user message for vector database search queries enclosed in $v$...$v$.

        Parameters:
        - user_message (str): The message from the user.
        - objective (str): The current objective of the discussion session.

        Returns:
        - str: A concatenated string of all vector search results or an empty string if no matches.
        """
        pattern = r"\$v\$(.*?)\$v\$"
        matches = re.findall(pattern, user_message)

        if not matches:
            return ""

        search_results: List[str] = []
        for match in matches:
            search_result = self.perform_vector_search(match)
            search_results.append(f"Vector search result for '{match}': {search_result}")

        return "\n".join(search_results)

    def perform_vector_search(self, query: str, simplified: bool = False) -> str:
        """
        Performs a vector search based on the given query and returns either simplified results or the original context.

        Parameters:
        - query (str): The query extracted from the user message.
        - simplified (bool): Whether to simplify the search results.

        Returns:
        - str: Search results for the query, optionally simplified.
        """
        # Convert the query text to a vector
        vector_converter = self.gpt_manager.create_agent(model=ModelType.TEXT_EMBEDDING_ADA, messages=query)
        vector_converter.run_agent()
        vector = vector_converter.get_vector()

        # Perform the vector search and retrieve the top k similar messages with their text
        topk_results = self.memory_stream.query_similar_vectors_with_text(vector, k=3)

        # Extract just the text from the search results
        topk_messages = [result[2] for result in topk_results]  # result[2] is the text part of each tuple

        if simplified:
            # Simplify the messages if requested
            simplifying_agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO,
                                                              system_prompt="Simplify the following messages:",
                                                              messages="\n".join(topk_messages), temperature=0.1)
            simplifying_agent.run_agent()
            simplified_text = simplifying_agent.get_text()
            return simplified_text
        else:
            # Return the original messages joined by new lines
            context = "\n".join(topk_messages)
            return context


class TrajectoryListenerGraphSearch(TrajectoryListener):
    def __init__(self):
        super().__init__()
        # the path is in the  same folder under the name cypher_labels_relationships.md
        self.markdown_file_path = "cypher_labels_relationships.md"
        self.system_prompt = self.generate_system_prompt_from_md()

    def generate_system_prompt_from_md(self) -> str:
        # Read the markdown file
        md_content = Path(self.markdown_file_path).read_text()

        # Extract labels and relationships sections
        labels_section = re.search(r"## Node Labels\n(.*?)\n\n##", md_content, re.DOTALL)
        relationships_section = re.search(r"## Relationships\n(.*?)\n\n##", md_content, re.DOTALL)

        # Combine extracted sections into a system prompt
        system_prompt = "Node Labels:\n"
        if labels_section:
            system_prompt += labels_section.group(1) + "\n"
        system_prompt += "Relationships:\n"
        if relationships_section:
            system_prompt += relationships_section.group(1)

        return system_prompt

    def perform_graph_search(self, query: str, simplified: bool = False) -> str:
        """
        Translates a natural language query into a Cypher query, executes it, and optionally simplifies the results.

        Parameters:
        - query (str): The query extracted from the user message.
        - simplified (bool): Whether to simplify the search results.

        Returns:
        - str: The results of executing the Cypher query, optionally simplified.
        """
        # Format the query for the translator
        query_prompt = f"Create a cypher query from the natural language query '{query}'. Format it between ` ```cypher ` and ` ``` `"
        cypher_translator = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=query_prompt,
                                                          system_prompt=self.system_prompt)
        cypher_translator.run_agent()
        cypher_query_text = cypher_translator.get_text()

        # Extract Cypher queries from the formatted text
        cypher_queries = re.findall(r"```cypher(.*?)```", cypher_query_text, re.DOTALL)

        # Clean up and prepare the queries for execution
        cleaned_queries = [query.strip() for query in cypher_queries]

        # Execute the queries
        query_result = self.memory_stream.neo4j_handler.execute_queries(cleaned_queries)

        # Format the query result for output
        formatted_result = "\n".join([str(result) for result in query_result]) if isinstance(query_result,
                                                                                             list) else str(
            query_result)

        if simplified:
            # Simplify the results if requested
            simplifying_agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO,
                                                              system_prompt="Simplify the following results:",
                                                              messages=formatted_result, temperature=0.1)
            simplifying_agent.run_agent()
            simplified_result = simplifying_agent.get_text()
            return simplified_result
        else:
            # Return the original results
            return formatted_result
