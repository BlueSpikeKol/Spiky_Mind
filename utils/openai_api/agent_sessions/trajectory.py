from typing import Optional

from utils.openai_api.agent_sessions.message_types import UserMessage, AIMessage, SystemMessage, DebaterMessage, \
    PresidentMessage
from utils.openai_api.agent_sessions.convo_types import ConversationType
from utils.openai_api.agent_sessions.memory_types import MemoryType


class ConversationRound:
    def __init__(self, initiator_message, responder_message, metrics: dict = None, category=None,
                 information_detected=None):
        self.initiator_message = initiator_message
        self.responder_message = responder_message
        self.metrics = metrics if metrics is not None else {}
        self.category = category
        self.information_detected = information_detected  # New attribute

    def set_information_detected(self, information_detected):
        """Sets detected information from decision-making detection."""
        self.information_detected = information_detected

    def to_dict(self):
        return {
            "initiator_message": self.initiator_message.content,
            "responder_message": self.responder_message.content,
            "metrics": self.metrics,
            "is_marked": getattr(self, 'is_marked', False),
            "category": self.category
        }

    def set_category(self, category):
        # Method to set the category of the round
        self.category = category


class UserAIRound(ConversationRound):
    def __init__(self, user_message: UserMessage, ai_message: AIMessage, metrics: dict = None, category=None,
                 information_detected=None):
        super().__init__(user_message, ai_message, metrics, category, information_detected)


class SessionPresidentDebaterRound(ConversationRound):
    def __init__(self, president_message: PresidentMessage, debater_message: DebaterMessage, metrics: dict = None,
                 category=None, information_detected=None):
        super().__init__(president_message, debater_message, metrics, category, information_detected)


class GeneralConversationTrajectory:
    def __init__(self, subject, conversation_type, memory_type):
        self.subject = subject
        self.conversation_type = conversation_type
        self.initial_question = None
        self.memory_type = memory_type
        self.system_prompt = None
        self.rounds = []

    def add_round(self, *args, **kwargs):
        """Placeholder for adding a round. To be implemented in subclasses."""
        pass

    def set_information_detected_for_round(self, round_index, information_detected):
        """Sets information detected for a specific round by its index."""
        if round_index < len(self.rounds):
            self.rounds[round_index].set_information_detected(information_detected)
        else:
            print(f"Error: Round index {round_index} out of bounds.")

    def trim_return_rounds(self, nb_max_msg):
        """Placeholder for trimming rounds. To be implemented in subclasses."""
        pass

    def set_system_prompt(self, prompt):
        """Placeholder for setting the system prompt. To be implemented in subclasses."""
        pass

    def get_marked_messages(self, last_x_messages):
        """Placeholder for getting marked messages. To be implemented in subclasses."""
        pass

    def display_trajectory(self, display_directly=False):
        """Placeholder for displaying the trajectory. To be implemented in subclasses."""
        pass

    def to_dict(self):
        """Placeholder for converting to dictionary. To be implemented in subclasses."""
        pass


class UserAITrajectory(GeneralConversationTrajectory):
    def __init__(self, subject, conversation_type, memory_type):
        super().__init__(subject, conversation_type, memory_type)

    def add_round(self, user_message: UserMessage, ai_message: AIMessage, metrics: dict, category: Optional[str] = None,
                  information_detected: Optional[dict] = None):
        round = UserAIRound(user_message, ai_message, metrics, category, information_detected)
        if self.memory_type == MemoryType.MARKED_MESSAGES:
            if user_message.is_marked or ai_message.is_marked:
                round.is_marked = True
        self.rounds.append(round)

    def trim_return_rounds(self, nb_max_msg):
        return self.rounds[-nb_max_msg:]

    def set_system_prompt(self, prompt):
        self.system_prompt = prompt

    def get_marked_messages(self, last_x_messages):
        marked_messages = [round for round in self.rounds if getattr(round, 'is_marked', False)]
        return marked_messages[-last_x_messages:]

    def display_trajectory(self, display_directly=False):
        output = f"\033[32mSystem Prompt: {self.system_prompt}\033[0m\n\n"
        for round in self.rounds:
            output += f"User: {round.user_message.content}\n"
            output += f"AI: {round.ai_message.content}\n"
            output += "----\n"
        output += "Discussion concluded.\n"
        if display_directly:
            print(output)
        else:
            return output

    def to_dict(self):
        return {
            "subject": self.subject,
            "conversation_type": self.conversation_type.name,
            "initial_question": self.initial_question,
            "memory_type": self.memory_type.name,
            "system_prompt": self.system_prompt,
            "rounds": [round.to_dict() for round in self.rounds]
        }


class PresidentDebaterTrajectory(GeneralConversationTrajectory):
    def __init__(self, subject, memory_type):
        super().__init__(subject, ConversationType.AI_DEBATE, memory_type)

    def add_round(self, president_message: PresidentMessage, debater_message: DebaterMessage, metrics: dict = None,
                  category: Optional[str] = None, information_detected: Optional[dict] = None):
        round = SessionPresidentDebaterRound(president_message, debater_message, metrics, category,
                                             information_detected)
        self.rounds.append(round)

    def format_rounds(self):
        round_output = ""
        for round in self.rounds:
            round_output += f"Session President ({round.session_president.name}): {round.president_message.content}\n"
            round_output += f"Debater ({round.debater.name}): {round.debater_message.content}\n"
            round_output += "----\n"  # Separator line
        return round_output
