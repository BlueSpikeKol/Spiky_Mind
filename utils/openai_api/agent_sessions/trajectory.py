from utils.openai_api.agent_sessions.message_types import UserMessage, AIMessage, SystemMessage
from utils.openai_api.agent_sessions.convo_types import ConversationType
from utils.openai_api.agent_sessions.memory_types import MemoryType


class ConversationRound:
    def __init__(self, user_message: UserMessage, ai_message: AIMessage, metrics: dict, category=None):
        self.user_message = user_message
        self.ai_message = ai_message
        self.metrics = metrics
        self.category = category  # New attribute for storing the round's category

    def to_dict(self):
        # Include the category in the dictionary representation of the round
        return {
            "user_message": self.user_message.content,
            "ai_message": self.ai_message.content,
            "metrics": self.metrics,
            "is_marked": getattr(self, 'is_marked', False),  # Default to False if not set
            "category": self.category
        }

    def set_category(self, category):
        # Method to set the category of the round
        self.category = category



class ConversationTrajectory:
    def __init__(self, subject, conversation_type, memory_type):
        self.subject = subject
        self.conversation_type = conversation_type
        self.initial_question = None
        self.memory_type = memory_type
        self.system_prompt = None
        self.rounds = []

    def add_round(self, user_message, ai_message, completion_metrics):
        round = ConversationRound(user_message, ai_message, completion_metrics)

        # Mark the entire round if any message in the round is marked
        if self.memory_type == MemoryType.MARKED_MESSAGES:
            if user_message.is_marked or ai_message.is_marked:
                round.is_marked = True  # Assuming ConversationRound has an is_marked attribute

        self.rounds.append(round)

    def trim_return_rounds(self, nb_max_msg):
        # Trim the trajectory to the last nb_max_msg rounds and return it
        trimmed_trajectory = self.rounds[-nb_max_msg:]
        return trimmed_trajectory

    def set_system_prompt(self, prompt):
        self.system_prompt = prompt

    def get_marked_messages(self, last_x_messages):
        marked_messages = []
        for round in self.rounds:
            if round.is_marked:  # Check if the round is marked
                marked_messages.append(round.user_message)
                marked_messages.append(round.ai_message)

        # Apply FIFO if memory exceeds limit
        if len(marked_messages) > last_x_messages:
            marked_messages = marked_messages[-last_x_messages:]

        return marked_messages

    def display_trajectory(self, display_directly=False):
        output = "\033[32mSystem Prompt: {}\033[0m\n\n".format(self.system_prompt)  # Green text for system prompt

        if self.conversation_type == ConversationType.USER_ANSWERS:
            # AI starts the conversation
            output += self.format_rounds(ai_starts=True)
        elif self.conversation_type in [ConversationType.BOT_ANSWERS, ConversationType.FREESTYLE]:
            # User starts the conversation
            output += self.format_rounds(ai_starts=False)
        else:
            # Default to user talking first
            output += self.format_rounds(ai_starts=False)

        output += "Discussion concluded.\n"
        if display_directly:
            print(output)
        else:
            return output

    def format_rounds(self, ai_starts):
        round_output = ""
        for round in self.rounds:
            if ai_starts:
                round_output += "AI: {}\n".format(round.ai_message.content)
                round_output += "User: {}\n".format(round.user_message.content)
            else:
                round_output += "User: {}\n".format(round.user_message.content)
                round_output += "AI: {}\n".format(round.ai_message.content)
            round_output += "----\n"  # Separator line
        return round_output

    def to_dict(self):
        trajectory_dict = {
            "subject": self.subject,
            "conversation_type": self.conversation_type.name_id,
            "initial_question": self.initial_question,
            "memory_type": self.memory_type.name_id,
            "system_prompt": self.system_prompt,
            "rounds": [round.to_dict() for round in self.rounds]
        }
        return trajectory_dict
