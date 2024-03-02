import re
import json
from pathlib import Path
import random
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass

from utils.openai_api.agent_sessions.agent_presets import PresetAgents
from utils.openai_api.agent_sessions.trajectory import UserAITrajectory
from utils.openai_api.agent_sessions.message_types import UserMessage, AIMessage, SystemMessage, Message, \
    DebaterMessage, PresidentMessage
from utils.openai_api.models import ModelType
from utils.openai_api.gpt_calling import GPTAgent, GPTManager
from utils.openai_api.agent_sessions.convo_types import ConversationType, ConversationEndType
from utils.openai_api.agent_sessions.memory_types import MemoryType
from utils.openai_api.agent_sessions.trajectory_listener import TrajectoryListenerCategorizer


class DiscussionSession:
    def __init__(self, discussion_name=None, subject=None, agent: GPTAgent = None,
                 conversation_type: ConversationType = ConversationType.FREESTYLE,
                 memory_type: MemoryType = MemoryType.LAST_X_MESSAGES, last_x_messages: int = 3,
                 summarize_result=False, conversation_end_type: ConversationEndType = ConversationEndType.USER_ENDED,
                 end_info=None, end_controlled_by_user=True, save_conversation: bool = False, save_path: str = None):
        """
        :param subject: the subject of a conversation is very important if the agent is asking questions and leading
        the discussion. Here is an example of a good subject to lead a discussion: "We need to determine what are the
        materials needed to build my DC motor".
        :param agent: only necessary when preset agents do not work. Especially with Freestyle conversations.
        :param conversation_type:
        :param memory_type:
        :param last_x_messages: only necessary when memory_type is LAST_X_MESSAGES
        :param summarize_result: if True, the result of the discussion will be summarized and returned as a string along.
        :param conversation_end_type: the type of end of discussion. Will determine the mechanism to end the discussion.
        :param end_info: additional information to end the discussion. For example, if conversation_end_type is set to
        ConversationEndType.X_MESSAGES_EXCHANGED, end_info will be the number of messages exchanged before ending the
        discussion.
        TODO: standardize the end_info parameter
        """
        self.discussion_name = discussion_name
        self.agent = agent
        self.subject = subject
        self.conversation_type = conversation_type
        self.memory_type = memory_type
        self.summarize_result = summarize_result
        self.trajectory = UserAITrajectory(self.subject, self.conversation_type, self.memory_type)
        self.last_x_messages = last_x_messages
        self.gpt_manager = GPTManager()
        self.conversation_end_type = conversation_end_type
        self.end_info = end_info
        self.end_controlled_by_user = end_controlled_by_user
        self.save_conversation = save_conversation
        self.save_path = save_path
        self.listeners = []

    def start_session(self, testing=True):
        all_information_gathered = False
        next_message = None
        AI_debaters = None
        while not all_information_gathered:
            end_of_discussion, next_message, AI_debaters = self.handle_single_round_convo(AI_message=next_message,
                                                                                          AI_debaters=AI_debaters)
            if end_of_discussion:
                break
        if self.save_conversation:
            self.save_conversation_to_json()
        if testing:
            final_output = self.trajectory.display_trajectory(display_directly=False)
            return final_output
        self.end_session()

    def end_session(self):
        for listener in self.listeners:
            listener.on_session_end(self.trajectory)

    def on_user_message(self, user_message):
        context = ""
        for listener in self.listeners:
            context = listener.on_new_user_msg(user_message)
        return context

    def register_listener(self, listener):
        self.listeners.append(listener)

    # TODO make sure that listeners can be tested here
    def process_message_pair(self, message_pair: List[Tuple[str, str]]) -> Tuple[
        Optional[UserMessage], Optional[AIMessage]]:
        user_message, ai_message = None, None
        for speaker, message in message_pair:
            if speaker == "Project Manager":  # Assuming "Project Manager" represents the user
                user_message = UserMessage(message)
            elif speaker == "AI Assistant":
                ai_message = AIMessage(message)
        return user_message, ai_message

    # Use the adjusted function in insert_premade_conversation
    def insert_premade_conversation(self, premade_conversation: List[Tuple[str, str]],
                                    premade_categories: Optional[List[str]] = None) -> None:
        if premade_conversation and premade_conversation[0][0] == "AI Assistant":
            self.trajectory.initial_question = premade_conversation[0][1]

        for i in range(0, len(premade_conversation), 2):
            message_pair = premade_conversation[i:i + 2]
            user_message, ai_message = self.process_message_pair(message_pair)

            # Ensure both messages are present before adding the round
            if user_message and ai_message:
                self.trajectory.add_round(user_message, ai_message, {})

                if premade_categories and i // 2 < len(premade_categories):
                    category = premade_categories[i // 2]
                    self.trajectory.rounds[-1].set_category(category)
                else:
                    last_round = self.trajectory.rounds[-1]
                    for listener in self.listeners:
                        listener.on_new_round(last_round, self.subject)

        # Optionally print categorization results for testing
        for listener in self.listeners:
            if isinstance(listener, TrajectoryListenerCategorizer):
                print("Categorization results:\n", listener.get_categorization_results())

    def handle_single_round_convo(self, AI_debaters=None, AI_message=None):
        # Retrieve messages for the round
        user_message, ai_message, president_message, debater_message, AI_debaters = self.retrieve_messages(AI_debaters,
                                                                                                           AI_message)

        # Update memory and save the messages into the trajectory
        end_of_discussion = self.update_and_save(
            user_message=user_message,
            ai_message=ai_message,
            president_message=president_message,
            debater_message=debater_message
        )

        return end_of_discussion, ai_message, AI_debaters

    def retrieve_messages(self, AI_debaters=None, AI_message=None):
        user_message, ai_message = None, None
        president_message, debater_message = None, None

        if self.conversation_type == ConversationType.USER_ANSWERS:
            # Handling AI-User interactions
            user_answer = input("\nYour turn: " if not self.trajectory.rounds else AI_message + "\nYour turn: ")
            ai_message = AIMessage(AI_message if self.trajectory.rounds else self.trajectory.initial_question)
            user_message = UserMessage(user_answer)

        elif self.conversation_type == ConversationType.BOT_ANSWERS:
            # Placeholder for BOT_ANSWERS logic
            pass

        elif self.conversation_type == ConversationType.FREESTYLE:
            # Placeholder for FREESTYLE logic
            pass

        elif self.conversation_type == ConversationType.AI_DEBATE:
            # Handling Session President-Debater interactions
            if not AI_debaters:
                AI_debaters = self.recruit_AI_debaters()

            if self.agent.agent_name != "Session President":
                for debater in AI_debaters:
                    if debater.agent_name != "Session President":
                        self.agent = debater

            self.agent.run_agent()
            president_message = PresidentMessage(self.agent.get_text())
            responding_agent = self.agent_answer_chooser(AI_debaters, president_message)

            if responding_agent:
                responding_agent.update_agent(messages=president_message.content)
                responding_agent.run()
                debater_message = DebaterMessage(responding_agent.get_text())
            else:
                debater_message = DebaterMessage(
                    "Cannot Process Directives: No available debaters or no debaters interested in responding.")

        return user_message, ai_message, president_message, debater_message, AI_debaters

    def update_and_save(self, user_message=None, ai_message=None, president_message=None, debater_message=None,
                        metrics=None, category=None):
        # Update context and memory based on the messages
        context = self.on_user_message(user_message or president_message)
        memory = self.update_memory(user_message or president_message, bonus_info=context)

        # Determine the type of round and add it to the trajectory
        if self.conversation_type == ConversationType.USER_ANSWERS:
            self.trajectory.add_round(user_message, ai_message, metrics, category)
        elif self.conversation_type == ConversationType.AI_DEBATE:
            self.trajectory.add_round(president_message, debater_message, metrics, category)

        # Handle post-round logic
        last_round = self.trajectory.rounds[-1]
        for listener in self.listeners:
            listener.on_new_round(last_round, self.subject)

        end_of_discussion = self.check_end_of_discussion(ai_message or debater_message, memory)
        return end_of_discussion

    def recruit_AI_debaters(self):
        def recruit_AI_debaters() -> List[GPTAgent]:
            chosen_agents = []
            current_script_path = Path(__file__).resolve()
            parent_folder = current_script_path.parent
            file_path = parent_folder.joinpath('agent_roles_permanent.json')
            agent_roles, agent_context = get_roles(file_path)
            president_description = """You are the president of a debate circle whose goal is to discuss a 
            project and you must explore the project organically. Your job is never to propose solutions, but to expose 
            problems, logic fallacies, and explore the subject in order to avoid blind spots. Never flip roles 
            with the debaters! You share a common interest with the debaters to solve issues and advance the 
            project. Never forget that the main task is to lead the other debaters so they can solve problems in 
            the project. If the debaters cannot answer or find your directives unclear they will answer with [
            Cannot Process Directives: <Reason for incompletion>]. Use open-ended questions to avoid forcing specific
            participants to answer.

            When presented with a numbered list of items to discuss, you are to address each item sequentially, 
            focusing on one issue at a time without introducing multiple items simultaneously. Only talk about the
            next item when the words [NEXT ITEM] are displayed.

            The debaters have a very short memory, so reminders of prior conclusions are necessary for continuity."""
            president_name = "Session President"
            president_agent = self.gpt_manager.create_agent(
                model=ModelType.GPT_3_5_TURBO, messages="", system_prompt=president_description,
                agent_name=president_name, temperature=0.4)
            chosen_agents.append(president_agent)

            # Randomly select roles for the debate, ensuring at least 3 agents are selected
            num_agents_to_recruit = max(3, len(agent_roles))
            chosen_roles = random.sample(agent_roles, num_agents_to_recruit)

            for role in chosen_roles:
                if role in agent_context:
                    additional_instructions = "If you find that the question you have been asked is unclear and need" \
                                              "further information, simply write [Cannot Process Directives:" \
                                              " <Reason for incompletion>]"
                    agent = self.gpt_manager.create_agent(
                        model=ModelType.GPT_3_5_TURBO, messages="",
                        system_prompt=agent_context[role] + additional_instructions, agent_name=role,
                        temperature=0.65)
                    chosen_agents.append(agent)
                else:
                    print(f"Failed to add agent: {role} due to no matching context.")

            return chosen_agents

        def get_roles(file_path: Path) -> (List[str], Dict[str, str]):
            with open(file_path, 'r') as f:
                agent_context = json.load(f)

            # Convert keys to lowercase for uniformity
            agent_context = {k.lower(): v for k, v in agent_context.items()}
            agent_roles = list(agent_context.keys())

            return agent_roles, agent_context

        return recruit_AI_debaters()

    def agent_answer_chooser(self, debater_agents, president_message=None):
        # Example: Randomly choose a debater agent to respond
        return random.choice(debater_agents)

    def mark_round_messages(self, user_message, ai_message, criteria=None):
        """
        Temporarily marks a round of messages (user and AI) based on given criteria.
        For now, the criteria parameter will not be used, and messages will be marked unconditionally.

        :param user_message: The user message to be marked.
        :param ai_message: The AI message to be marked.
        :param criteria: Optional criteria for marking messages (unused for now).
        """
        user_message.is_marked = True
        ai_message.is_marked = True

    def check_end_of_discussion(self, answer, memory: Message):
        # Dispatcher logic
        if self.conversation_end_type == ConversationEndType.INFORMATION_GATHERED:
            end_decision, explanation = self.end_by_information_gathered(answer, memory)
        elif self.conversation_end_type == ConversationEndType.X_MESSAGES_EXCHANGED:
            end_decision, explanation = self.end_by_message_count()
        elif self.conversation_end_type == ConversationEndType.USER_ENDED:
            end_decision, explanation = self.final_user_confirmation(memory, explanation=None)
            return end_decision, explanation
        else:
            raise NotImplementedError("The specified end type is not implemented.")

        # Final user confirmation if end_controlled_by_user is True
        if self.end_controlled_by_user:
            return self.final_user_confirmation(memory, explanation=explanation)
        else:
            return end_decision, explanation

    def final_user_confirmation(self, memory: Message, explanation=None):
        # Final user confirmation logic
        if explanation is not None:
            print(explanation)
        print(memory.content)
        user_confirmation = input(
            "Do you still wish to continue the discussion considering the information above? (yes/no): ").strip().lower()
        if user_confirmation == 'yes':

            return False, "The user has chosen to continue the discussion. While having this information:" + explanation
        else:
            return True, "The user has chosen to end the discussion. While having this information:" + explanation

    def end_by_information_gathered(self, answer, memory: Message):
        # Logic to determine if enough information has been gathered
        logic_agent = PresetAgents().get_agent(PresetAgents.LOGIC_GATE)
        logic_prompt = f"From the following context, evaluate if, for the person asking questions, it is needed to ask more questions to have a complete understanding of the subject.\nContext:\n{memory.content}\nLast Answer:\n{answer}"
        logic_agent.update_agent(messages=logic_prompt)
        logic_agent.run_agent()
        logic_result = logic_agent.get_text()

        if "yes" in logic_result.lower():
            return True, "The discussion seems to have covered all necessary information."
        else:
            information_prompt = f"From the following context, evaluate, for the person asking questions, what other questions to ask in order to have a complete understanding of the subject.\nContext:\n{memory.content}\nLast Answer:\n{answer}"
            information_agent = self.gpt_manager.create_agent(ModelType.GPT_3_5_TURBO, messages=information_prompt,
                                                              max_tokens=300)
            information_agent.run_agent()
            information_result = information_agent.get_text()
            return False, "Here are bonus questions to gather more information for the proper understanding of the discussion:\n\n" + information_result

    def end_by_message_count(self):
        rounds_left = self.end_info - len(self.trajectory.rounds)
        if rounds_left <= 0:
            return True, f"The message exchange limit of {self.end_info} has been reached."
        else:
            return False, f"There are {rounds_left} rounds left before reaching the message limit."

    def generate_initial_question(self, subject):
        # self.get_context_on_subject(subject) TODO: Implement logic for getting context on subject
        prompt = f'Give me an opening question that would quickstart any discussion of any subject. This is the subject of this particular session: <{subject}>. Your opening question must be 1-2 sentences long. Give that question between quotes ""'
        create_question_agent = self.gpt_manager.create_agent(ModelType.GPT_3_5_TURBO, messages=prompt, max_tokens=100)
        create_question_agent.run_agent()
        question_text = create_question_agent.get_text()

        # Extracting text between double quotes
        extracted_question = re.findall(r'"([^"]*)"', question_text)
        if extracted_question:
            formatted_question = f"Spiky wants to talk about {subject}, he is missing information and will ask you questions in order to fill in the missing knowledge: {extracted_question[0]}"
        else:
            formatted_question = "No valid question found."

        return formatted_question

    def get_context_on_subject(self, subject):
        # TODO will search in the database the appropriate context on the subject
        pass

    def extract_completion_data(self):
        # Extract data from agent's completion
        return {
            "finish_reason": self.agent.get_finish_reason(),
            "created_time": self.agent.get_created_time(),
            "completion_time": self.agent.get_completion_time(),
            "model": self.agent.get_model_used(),
            "usage": self.agent.get_usage(),
            "response_id": self.agent.get_id(),
            "completion_cost": self.get_completion_cost()
        }

    def get_completion_cost(self):
        # Retrieve prices for input and output tokens
        model_prices = ModelType.MODEL_PRICES.get(self.agent.model, {'input': 0.0, 'output': 0.0})
        usage = self.agent.get_usage()

        # Calculate cost for input and output tokens separately
        input_cost = usage['prompt_tokens'] * model_prices['input']
        output_cost = usage['completion_tokens'] * model_prices['output']
        total_cost = input_cost + output_cost

        return {'total_cost': total_cost, 'input_cost': input_cost, 'output_cost': output_cost}

    def update_memory(self, main_agent_answer, bonus_info=None):
        messages_to_update = []
        # Get previous conversation rounds based on memory type
        if self.memory_type == MemoryType.LAST_X_MESSAGES:
            messages_to_update = self.trajectory.trim_return_rounds(self.last_x_messages)
        elif self.memory_type == MemoryType.ALL_MESSAGES:
            messages_to_update = self.trajectory.rounds
        elif self.memory_type == MemoryType.MARKED_MESSAGES:
            messages_to_update = self.trajectory.get_marked_messages(self.last_x_messages)

        elif self.memory_type == MemoryType.DB_RETRIEVAL:
            # Implement logic for database retrieval
            pass

        elif self.memory_type == MemoryType.SIMILARITY_SEARCH:
            # Implement logic for similarity search
            pass

        else:
            raise ValueError("Unsupported memory type")

        if main_agent_answer is not None:
            messages_to_update.append(UserMessage(main_agent_answer))

        # Check if the initial question is already in the system prompt
        initial_question_prompt = f"This is the initial question of this discussion: {self.trajectory.initial_question}"
        if self.trajectory.initial_question and not self.is_initial_question_in_system_prompt(initial_question_prompt):
            if isinstance(self.agent.system_prompt, SystemMessage):
                self.agent.system_prompt.content += "\n" + initial_question_prompt
            elif isinstance(self.agent.system_prompt, str):
                self.agent.system_prompt += "\n" + initial_question_prompt
            else:
                self.agent.system_prompt = initial_question_prompt

        # Update agent with the accumulated messages
        self.agent.update_agent(messages=messages_to_update)
        return messages_to_update

    def is_initial_question_in_system_prompt(self, initial_question_prompt):
        """
        Check if the initial question is already in the system prompt.
        """
        if isinstance(self.agent.system_prompt, SystemMessage):
            return initial_question_prompt in self.agent.system_prompt.content
        elif isinstance(self.agent.system_prompt, str):
            return initial_question_prompt in self.agent.system_prompt
        return False

    def summarize_discussion(self, conversation):
        # TODO: Implement logic for summarizing the discussion, there will be multiple, like round by round, or the
        # whole discussion in one go etc.
        pass

    def save_conversation_to_json(self):
        if self.save_path is not None:
            with open(self.save_path, 'w') as file:
                json.dump(self.trajectory.to_dict(), file, indent=4)
        else:
            print("Save path not provided. Conversation not saved.")


if __name__ == "__main__":
    # Testing the DiscussionSession and related classes

    # Creating an instance of DiscussionSession with a specified subject, agent, and conversation type
    subject = "Testing the DiscussionSession class"
    session = DiscussionSession(subject=subject, conversation_type=ConversationType.USER_ANSWERS,
                                memory_type=MemoryType.LAST_X_MESSAGES, last_x_messages=3)

    # Starting the discussion session
    print("Starting Discussion Session...")
    final_output = session.start_session()

    # Printing the final output of the discussion
    print("\nFinal Output of Discussion:")
    print(final_output)
