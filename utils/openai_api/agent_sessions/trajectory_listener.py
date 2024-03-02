import re
from pathlib import Path
from typing import List
import numpy as np

from utils.openai_api.agent_sessions.message_types import UserMessage, AIMessage
from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType
from utils.openai_api.agent_sessions.agent_presets import PresetAgents
from utils.openai_api.agent_sessions.trajectory import UserAIRound
from project_memory.persistance_access import MemoryStreamAccess

""" Here are the ways to detect, using nlp techniques, if a decision is being made, which would trigger the addition of information to the project using DRF technique.
1. Anticipating Consequences
Technique: Sentiment Analysis and Predictive Modeling
Implementation: Train a model to recognize phrases that indicate speculation about future outcomes, such as "What if" scenarios or discussions about potential problems ("if custom development exceeds the budget"). The program can use sentiment analysis to detect concern or caution, coupled with a predictive model that identifies when these concerns signal a decision-making process related to planning for potential outcomes.
2. Goal Alignment
Technique: Text Classification and Keyword Extraction
Implementation: Implement text classification to distinguish parts of the conversation that relate to setting objectives or targets ("the goal is to have the design all wrapped up by Week 3"). Use keyword extraction to identify specific goals and timelines, allowing the program to detect when discussions align with these identified objectives, indicating a decision-making process focused on achieving set goals.
3. Change or Disruption
Technique: Topic Modeling and Change Detection Algorithms
Implementation: Use topic modeling to understand the general themes of the conversation and detect when a shift in these themes indicates a significant change or disruption. Change detection algorithms can identify sudden deviations in the conversation's direction, such as introducing a new problem or challenge, signaling the need for a decision to adapt or respond.
4. Conflict or Dissatisfaction
Technique: Sentiment Analysis and Conflict Detection
Implementation: Apply sentiment analysis to detect negative emotions or expressions of dissatisfaction ("the design getting too fancy for our skills"). Implement conflict detection algorithms to identify disagreements or problems within the conversation, signaling a decision point related to resolving these issues.
5. Opportunity Recognition
Technique: Named Entity Recognition (NER) and Relation Extraction
Implementation: Use NER to identify mentions of resources, tools, or opportunities ("set aside some cash, like 50 bucks, just for design stuff"). Relation extraction can then identify connections between these entities and actions or plans, indicating a decision-making process aimed at seizing these opportunities.
"""

"""
User
what would you recommend, even if far-fetched, to avoid some of the user interactions in the process
ChatGPT
Reducing user interaction in the process, while still ensuring the relevance and accuracy of the knowledge captured, requires leveraging more advanced AI and machine learning techniques. Here are some far-fetched yet potentially impactful recommendations:

1. Advanced Contextual Understanding and Prediction
Approach: Utilize deep learning models that can understand the context of a conversation at a much deeper level than current NER systems. These models could predict the relevance and categorization of information based on the entire conversation history, rather than isolated entities.
Implementation: Transformer-based models, like GPT-3 or newer versions, trained on domain-specific datasets could offer nuanced understanding and prediction capabilities. They could automatically suggest when information seems relevant to the database without explicit user prompts.
2. Automated Schematic Generation and Refinement
Approach: Develop AI systems capable of automatically generating new schematics based on the entities and context identified. These systems could also refine existing schematics by learning from each interaction and user feedback, even without direct user involvement.
Implementation: Machine learning models that learn the structure and relationships of schematics over time, possibly through reinforcement learning, where the model is rewarded for successful categorizations and linkages.
3. Self-organizing Knowledge Graphs
Approach: Create a self-organizing knowledge graph that dynamically adjusts its structure, creates new schematics, and forms links based on the evolving nature of the stored information and inferred relationships.
Implementation: Utilize graph neural networks (GNNs) and unsupervised learning techniques to allow the knowledge graph to identify patterns, similarities, and potential relationships autonomously.
4. Predictive Linking and Parent Node Creation
Approach: Instead of relying on user input for linking nodes and creating parent nodes, employ predictive models that can suggest these links by understanding the underlying patterns and relationships within the knowledge graph.
Implementation: Implement models that can analyze the graph's topology, node attributes, and vector similarities to predict where new information fits within the existing structure, potentially suggesting new parent nodes or direct linkages.
5. Crowdsourcing and Collaborative Filtering
Approach: While not eliminating user interaction, this approach reduces the burden on individual users by leveraging the collective actions of many users. By analyzing patterns in how multiple users interact with similar types of information, the system can learn to automate certain decisions.
Implementation: Techniques similar to those used in collaborative filtering for recommendation systems could be adapted to suggest schematics, linkages, and even new parent nodes based on the aggregated behaviors and choices of many users.
6. Interactive Learning Agents
Approach: Develop AI agents that learn from each interaction to better anticipate user needs and the relevance of information. These agents could become more autonomous over time, requiring less user input for routine decisions.
Implementation: Combining interactive learning with natural language processing and user feedback loops, these agents could gradually take on more responsibility for categorizing and linking information, asking for user input only in ambiguous situations.
Conclusion
While these approaches are ambitious and require significant advancements in AI, machine learning, and user interface design, they represent a direction towards more autonomous and intelligent systems for knowledge management. Balancing the reduction of user interactions with the maintenance of high-quality, relevant knowledge capture will be key to the success of such systems.
"""

# Todo: Implement the above techniques to detect decision making in the conversation and add the information to the project using DRF technique.
class TrajectoryListener:
    def __init__(self):
        self.round_history = []  # Stores all rounds observed by the listener
        self.gpt_manager = GPTManager()
        self.memory_stream = MemoryStreamAccess()

    def on_new_round(self, last_round: UserAIRound, objective):
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

    def on_new_round(self, last_round: UserAIRound, objective: str) -> None:
        categories_string = ", ".join(self.categories)
        system_prompt = (f"Please categorize the following conversation round(s), centered around [{objective}], "
                         f"into one of the following categories: {categories_string}.")

        # Accessing the messages via initiator_message and responder_message
        round_string = f"User: {last_round.initiator_message.content}\nAI: {last_round.responder_message.content}"

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
        self.categorization_results.append(found_category)

    def set_round_category(self, last_round: UserAIRound, category: str) -> None:
        if category in self.categories:
            last_round.set_category(category)
        else:
            print(f"Warning: Category '{category}' not recognized. Setting to 'Uncategorized'.")
            last_round.set_category("Uncategorized")

    def get_categorization_results(self) -> List[str]:
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


class TrajectoryListenerFactDetector(TrajectoryListener):
    def __init__(self):
        super().__init__()

    def on_new_round(self, last_round: UserAIRound, objective: str) -> None:
        # Check if the round contains a decision-making context
        information_detected_list = self.detect_decision_making(last_round)
        last_round.set_information_detected(information_detected_list)

    def detect_decision_making(self, last_round: UserAIRound) -> dict:
        round_as_text = f"{last_round.responder_message.content}"

        # Step 1: Vectorize the conversation round
        vectorization_agent = self.gpt_manager.create_agent(model=ModelType.TEXT_EMBEDDING_ADA, messages=round_as_text)
        vectorization_agent.run_agent()
        round_vector = vectorization_agent.get_vector()

        # Step 2: Retrieve technique vectors (this function needs to be implemented)
        technique_vectors = self.get_techniques_vectors()

        # Find the most similar technique
        similarity_scores = {
            technique: np.dot(round_vector, tech_vector) / (np.linalg.norm(round_vector) * np.linalg.norm(tech_vector))
            for technique, tech_vector in technique_vectors.items()}
        most_similar_technique = max(similarity_scores, key=similarity_scores.get)

        # Verify the technique with a logic-gate agent
        verification = self.verify_technique_with_logic_gate(round_as_text, most_similar_technique)

        if not verification:
            # User selects the correct technique if verification fails
            print("The automated detection might not be accurate. Please confirm or select the correct technique:")
            for idx, technique in enumerate(technique_vectors.keys(), 1):
                print(f"{idx}. {technique}")
            user_choice = int(input("Enter the number of the correct technique: ")) - 1
            chosen_technique = list(technique_vectors.keys())[user_choice]
            most_similar_technique = chosen_technique
            # Update similarity score based on user's choice
            highest_similarity = similarity_scores[most_similar_technique]
        else:
            highest_similarity = similarity_scores[most_similar_technique]

        parsed_decision_data = self.get_decision_text(round_as_text, most_similar_technique)

        decision_making_data = {
            "decision_text": round_as_text,
            "detected_technique": most_similar_technique,
            "bot_verification": "Correct" if verification else "User Corrected",
            "similarity_score": highest_similarity,  # Adjust this based on actual implementation
            "phrase_detected": parsed_decision_data["phrase_detected"],
            "decision_indicated": parsed_decision_data["decision_indicated"],
            "type": parsed_decision_data["type"]
        }

        return decision_making_data

    def get_decision_text(self, round_text, technique) -> dict:
        # Define technique descriptions
        technique_descriptions = {
            "Anticipating Consequences": "<Identify sentences speculating on future scenarios or discussing 'what if' possibilities and potential problems. Look for signs of caution or speculation about future steps.>",
            "Goal Alignment": "<Spot mentions of goals, objectives, deadlines, or milestones. Focus on parts of the conversation where targets are being set or alignment with objectives is discussed.>",
            "Change or Disruption": "<Notice any sudden shifts in the topic that indicate a significant change or disruption. Look for new challenges or deviations in plans being introduced.>",
            "Conflict or Dissatisfaction": "<Detect expressions of dissatisfaction, disagreement, or conflict. These might be complaints, expressions of concern, or disagreements.>",
            "Opportunity Recognition": "<Look for mentions of resources, tools, opportunities, or innovations being considered. Pay attention to how these are linked to actions or plans.>"
        }

        # Extract the base name of the technique from the identifier
        base_technique_name = technique.split("-")[0].replace("_", " ")

        # Adjust for cases where the technique name might not directly map due to spaces or case differences
        base_technique_name = base_technique_name.replace("Anticipating Consequences", "Anticipating Consequences") \
            .replace("Goal Alignment", "Goal Alignment") \
            .replace("Change or Disruption", "Change or Disruption") \
            .replace("Conflict or Dissatisfaction", "Conflict or Dissatisfaction") \
            .replace("Opportunity Recognition", "Opportunity Recognition")

        # Ensure the technique name matches the keys in technique_descriptions
        if base_technique_name in technique_descriptions:
            technique_description = technique_descriptions[base_technique_name]
        else:
            print(f"Technique description for '{base_technique_name}' not found.")
            return {}

        # Generate the prompt for decision-making insight
        prompt = f"Given the conversation snippet above and the decision-making technique '{technique_description}', " \
                 f"provide a human-understandable summary that includes:" \
                 f"1. Phrase Detected\n2. Decision Indicated\n3. Type of Decision" \
                 f"Separate each of the three parts with a new line"
        extractor_agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=round_text + prompt)
        extractor_agent.run_agent()
        decision_text = extractor_agent.get_text()
        decision_data = self.parse_decision_data(decision_text)
        return decision_data

    def parse_decision_data(self, decision_data: str) -> dict:
        # First attempt with newline characters
        decision_parts = decision_data.split("\n")
        if len(decision_parts) == 3:
            return self.extract_decision_parts(decision_parts)

        # Second attempt with splitting by "1. ", "2. ", "3. "
        decision_parts = self.split_by_list_numbers(decision_data)
        if len(decision_parts) == 3:
            return self.extract_decision_parts(decision_parts)

        # Fourth method: Directly look for the markers within the text
        decision_parts = self.split_by_markers(decision_data)
        if len(decision_parts) == 3:
            return self.extract_decision_parts(decision_parts)

        return self.prompt_user_for_decision_data()

    def prompt_user_for_decision_data(self):
        print("Unable to automatically parse the decision data from the conversation.")
        print("Please provide the necessary information based on the conversation snippet.")
        print("\nExample of successful parsing:")
        print("\tPhrase Detected: 'The budget constraints limit our options.'")
        print("\tDecision Indicated: 'Adjust the project scope to fit within the budget.'")
        print("\tType of Decision: 'Strategic decision related to project management.'\n")

        # Prompting user for each piece of information
        phrase_detected = input("1. Phrase Detected: ").strip()
        decision_indicated = input("2. Decision Indicated: ").strip()
        decision_type = input("3. Type of Decision: ").strip()

        # Constructing and returning the dictionary with user-provided data
        decision_data = {
            "phrase_detected": phrase_detected,
            "decision_indicated": decision_indicated,
            "type": decision_type
        }

        return decision_data

    def split_by_list_numbers(self, decision_data: str) -> list:
        decision_parts = []
        current_part = ""
        for line in decision_data.split("\n"):
            if line.startswith("1. ") or line.startswith("2. ") or line.startswith("3. "):
                if current_part:  # Save the previous part if it exists
                    decision_parts.append(current_part.strip())
                current_part = line  # Start a new part
            else:
                current_part += " " + line  # Continue building the current part
        if current_part:  # Don't forget to add the last part
            decision_parts.append(current_part.strip())
        return decision_parts

    def split_by_markers(self, decision_data: str) -> list:
        markers = ["Phrase Detected:", "Decision Indicated:", "Type of Decision:"]
        decision_parts = []
        for marker in markers:
            start_idx = decision_data.find(marker)
            if start_idx != -1:
                end_idx = len(decision_data)
                for next_marker in markers:
                    next_idx = decision_data.find(next_marker, start_idx + len(marker))
                    if next_idx != -1 and next_idx < end_idx:
                        end_idx = next_idx
                part_text = decision_data[start_idx + len(marker):end_idx].strip()
                decision_parts.append(part_text)
        return decision_parts

    def extract_decision_parts(self, decision_parts: list) -> dict:
        # Assuming decision_parts are correctly split and only contain relevant parts
        phrase_detected, decision_indicated, type_detected = decision_parts
        return {
            "phrase_detected": phrase_detected.split(":", 1)[-1].strip(),
            "decision_indicated": decision_indicated.split(":", 1)[-1].strip(),
            "type": type_detected.split(":", 1)[-1].strip()
        }

    def verify_technique_with_logic_gate(self, round_text, technique):
        logic_gate_agent = PresetAgents.get_agent(PresetAgents.LOGIC_GATE)
        logic_prompt = f"tell me, yes or no, if that technique '{technique}' was used to detect a decision with the following conversation round:{round_text}"
        logic_gate_agent.update_agent(messages=round_text + logic_prompt)
        logic_gate_agent.run_agent()
        logic_gate_agent_output = logic_gate_agent.get_text().strip()
        if "yes" in logic_gate_agent_output:
            return True
        else:
            return False

    def get_techniques_vectors(self):
        # goes into the db to retrieve the vectors of the known techniques to detect decision making in the conversation.
        technique_ids = ["Anticipating_Consequences-d55d3921-983b-4a8d-be6f-3c8d8fed362e",
                         "Goal_Alignment-d2d2ed56-39a7-4bd5-a7f7-0f412242650e",
                         "Change_or_Disruption-9fdfce2c-15d4-4b9b-8498-d37565de6d53",
                         "Conflict_or_Dissatisfaction-dd705b89-b3a0-4162-a3c9-c49f5fe906ab",
                         "Opportunity_Recognition-88f37932-eaf2-4d5c-98a7-020433055916"]
        technique_dict = self.memory_stream.get_vectors_whitelist(technique_ids)
        return technique_dict


user_message_content = """
Given our tight budget constraints, I've been thinking we might need to explore alternative technologies. 
What if we can't secure the necessary resources for our preferred stack? We should have a backup plan.
"""

ai_message_content = """
You're right about preparing for potential budget issues. However, it's crucial we don't compromise on quality. 
Let's consider open-source tools as a backup. Also, aligning with the marketing team could open up additional 
funding opportunities. We need to ensure any changes don't disrupt our current timeline or team dynamics.
Conflict could arise if the team isn't on board with the backup technologies.
"""
# TODO: this message above is complex and could create multiple information detected, we will need to handle more than a single object in the future.

# Assuming UserMessage and AIMessage are initialized properly elsewhere
user_message = UserMessage(content=user_message_content)
ai_message = AIMessage(content=ai_message_content)

# Creating a UserAIRound instance with the simulated conversation
last_round = UserAIRound(user_message=user_message, ai_message=ai_message, metrics={}, category="Project Discussion")

# Assuming the trajectory listener is initialized properly
trajectory_listener = TrajectoryListenerFactDetector()

# Injecting the round into the trajectory listener's detection process
trajectory_listener.on_new_round(last_round=last_round, objective="Enhancing User Experience")
print()

# At this point, the trajectory listener would process the conversation,
# detect decision-making contexts, and potentially ask for user confirmation if automated detection is unsure.
