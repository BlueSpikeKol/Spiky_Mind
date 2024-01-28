from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.agent_sessions.message_types import SystemMessage
from utils.openai_api.models import ModelType
from utils.openai_api.agent_sessions.convo_types import ConversationType


class PresetAgents:
    # Class attribute for the agent manager
    agent_manager = GPTManager()

    # Predefined types for agents
    LOGIC_GATE = 'logic_gate'
    USER_ANSWERS = ConversationType.USER_ANSWERS
    BOT_ANSWERS = ConversationType.BOT_ANSWERS
    FREESTYLE = ConversationType.FREESTYLE

    @classmethod
    def _create_logic_gate_agent(cls):
        system_prompt = SystemMessage(
            "You are an AI designed to logically evaluate if yes or no an objective was fullfiled."
            " You will be given context and the objective. Follow the instructions closely."
            " You must answer yes or no. you cannot answer anything else.")
        return cls.agent_manager.create_agent(
            model=ModelType.GPT_3_5_TURBO,
            agent_name="Logic Gate",
            system_prompt=system_prompt,
            max_tokens=3,  # Restricting to very few tokens
            temperature=0.1,
            logit_bias={9891: 10, 2201: 10},  # Specific logit biases to guide responses
            messages="empty"  # Starting with no predefined messages
        )

    @classmethod
    def _create_questions_agent(cls):
        system_prompt = SystemMessage(
            "You are an AI assistant that engages with an expert in the field to answer the question above,"
            " always bringing fresh opinions and pushing the discussion with constructive observations. "
            "Try framing your opinions as questions to push the conversation further.")
        return cls.agent_manager.create_agent(agent_name="question creator", model=ModelType.GPT_3_5_TURBO,
                                              system_prompt=system_prompt,
                                              max_tokens=600, temperature=0.7, messages="empty")

    @classmethod
    def _create_answers_agent(cls):
        system_prompt = SystemMessage(
            "You are a conversational AI that answers user's queries, encouraging a two-way dialogue.")
        return cls.agent_manager.create_agent(agent_name="answer creator", model=ModelType.GPT_3_5_TURBO,
                                              system_prompt=system_prompt,
                                              max_tokens=600, temperature=0.5, messages="empty")

    @classmethod
    def _create_freestyle_agent(cls):
        system_prompt = SystemMessage(
            "You are an AI designed for open-ended, creative and engaging conversations with users.")
        return cls.agent_manager.create_agent(agent_name="freestyle", model=ModelType.GPT_3_5_TURBO,
                                              system_prompt=system_prompt,
                                              max_tokens=600, temperature=0.4, messages="empty")

    @classmethod
    def get_agent(cls, agent_type):
        if agent_type == cls.LOGIC_GATE:
            return cls._create_logic_gate_agent()
        elif agent_type == cls.USER_ANSWERS:
            return cls._create_questions_agent()
        elif agent_type == cls.BOT_ANSWERS:
            return cls._create_answers_agent()
        elif agent_type == cls.FREESTYLE:
            return cls._create_freestyle_agent()
        else:
            raise ValueError("Unsupported conversation type")
