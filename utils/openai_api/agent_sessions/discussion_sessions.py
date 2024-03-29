import re

from utils.openai_api.agent_sessions.agent_presets import PresetAgents
from utils.openai_api.agent_sessions.trajectory import ConversationTrajectory
from utils.openai_api.agent_sessions.message_types import UserMessage, AIMessage, SystemMessage, Message
from utils.openai_api.models import ModelType
from utils.openai_api.gpt_calling import GPTAgent, GPTManager
from utils.openai_api.agent_sessions.convo_types import ConversationType, ConversationEndType
from utils.openai_api.agent_sessions.memory_types import MemoryType


class DiscussionSession:
    def __init__(self, subject=None, agent: GPTAgent = None,
                 conversation_type: ConversationType = ConversationType.FREESTYLE,
                 memory_type: MemoryType = MemoryType.LAST_X_MESSAGES, last_x_messages: int = 3,
                 summarize_result=False, conversation_end_type: ConversationEndType = ConversationEndType.USER_ENDED,
                 end_info=None, end_controlled_by_user=True):
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
        self.agent = agent
        self.subject = subject
        self.conversation_type = conversation_type
        self.memory_type = memory_type
        self.summarize_result = summarize_result
        self.trajectory = ConversationTrajectory(self.subject, self.conversation_type, self.memory_type)
        self.last_x_messages = last_x_messages
        self.gpt_manager = GPTManager()
        self.conversation_end_type = conversation_end_type
        self.end_info = end_info
        self.end_controlled_by_user = end_controlled_by_user

    def start_session(self, testing=True):
        all_information_gathered = False

        while not all_information_gathered:
            end_of_discussion = self.handle_single_round_convo()
            if end_of_discussion:
                break
        if testing:
            final_output = self.trajectory.display_trajectory(display_directly=False)
            return final_output
        else:
            return self.trajectory

    def handle_single_round_convo(self):
        user_answer = None
        if not self.agent:
            self.agent = PresetAgents().get_agent(self.conversation_type)

        if self.conversation_type == ConversationType.USER_ANSWERS:
            # Generate initial question and get user's answer
            if not self.trajectory.rounds:  # Only if it's the first round
                ai_question = self.generate_initial_question(self.subject)
                #ai_question = 'testing'
                self.trajectory.initial_question = ai_question
                user_answer = input(ai_question)
            else:
                user_answer = input(self.trajectory.rounds[-1].ai_message.content)

        elif self.conversation_type == ConversationType.BOT_ANSWERS:
            # TODO: Implement logic for bot answering user's questions
            pass

        elif self.conversation_type == ConversationType.FREESTYLE:
            # TODO: Implement freestyle conversation logic
            pass

        # Update agent with the trajectory and get AI's response
        memory = self.update_memory(user_answer)
        self.agent.run_agent()
        ai_answer = self.agent.get_text()

        user_message = UserMessage(user_answer)
        ai_message = AIMessage(ai_answer)

        # Mark messages if memory type is MARKED_MESSAGES
        if self.memory_type == MemoryType.MARKED_MESSAGES:
            self.mark_round_messages(user_message, ai_message)

        completion_data = self.extract_completion_data()
        self.trajectory.add_round(user_message, ai_message, completion_data)
        end_of_discussion = self.check_end_of_discussion(ai_answer, memory)
        return end_of_discussion

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
        #self.get_context_on_subject(subject) TODO: Implement logic for getting context on subject
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

    def update_memory(self, user_answer):
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

        if user_answer is not None:
            messages_to_update.append(UserMessage(user_answer))

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
