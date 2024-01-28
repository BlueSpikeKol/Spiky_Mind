import tiktoken
from typing import Optional


class ModelType:
    """
    Defines constants for the supported model types.
    """
    # Embedding Models
    TEXT_EMBEDDING_ADA = "text-embedding-ada-002"

    # Chat Models
    FUNCTION_CALLING_GPT_3_5 = "gpt-3.5-turbo-16k-0613"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    CHAT_GPT4_old = "gpt-4"
    FUNCTION_CALLING_GPT4 = "gpt-4-0613"
    GPT_4_TURBO = "gpt-4-1106-preview"

    # Text Models
    TEXT_DAVINCI_COMMON_3 = "text-davinci-003"


    # Categories
    EMBEDDING_MODELS = [TEXT_EMBEDDING_ADA]
    CHAT_MODELS = [GPT_3_5_TURBO, CHAT_GPT4_old, FUNCTION_CALLING_GPT4, FUNCTION_CALLING_GPT_3_5, GPT_4_TURBO]
    TEXT_MODELS = [TEXT_DAVINCI_COMMON_3]

    # Prices per token for each model
    MODEL_PRICES = {
        TEXT_DAVINCI_COMMON_3: {'input': 0.02, 'output': 0.02},
        GPT_3_5_TURBO: {'input': 0.0015, 'output': 0.002},
        FUNCTION_CALLING_GPT_3_5: {'input': 0.003, 'output': 0.004},
        CHAT_GPT4_old: {'input': 0.03, 'output': 0.06},
        GPT_4_TURBO: {'input': 0.01, 'output': 0.3},
        FUNCTION_CALLING_GPT4: {'input': 0.03, 'output': 0.06},
        TEXT_EMBEDDING_ADA: {'input': 0.0001, 'output': 0.0001}
    }
    @classmethod
    def get_supported_models(cls) -> list[str]:
        """Returns a list of all supported models."""
        return list(cls.MODEL_PRICES.keys())

    @classmethod
    def get_price(cls, model: str) -> float:
        """
        Retrieves the price per token for a given model.

        Parameters:
            model (str): The model name.

        Returns:
            float: The price per token for the model.
        """
        return cls.MODEL_PRICES.get(model, 0.0)


class ModelsTokenLimits:
    """
    Defines token limits for each supported model type.
    """
    TOKEN_LIMITS = {
        "text-davinci-003": 4096,
        "gpt-3.5-turbo-16k-0613": 16384,
        "gpt-3.5-turbo": 4097,
        "gpt-4": 8192,
        "gpt-4-0613": 8192,
        "gpt-4-1106-preview": 128000,
        "text-embedding-ada-002": 8192
    }

    @classmethod
    def get_token_limit(cls, model: str) -> int:
        return cls.TOKEN_LIMITS.get(model, 0)  # Return 0 if the model is not found


class ModelManager:

    @staticmethod
    def check_agent_token_limit(model: ModelType, prompt: str, max_tokens: Optional[int] = None) -> bool:
        model_str = str(model)
        model_token_limit = ModelsTokenLimits.get_token_limit(model_str)

        if model_token_limit == 0:  # No token limit found for the model
            raise ValueError(f"Token limit for model '{model}' is not defined.")

        # Note the use of 'ModelManager.num_tokens_from_string' to call the static method
        prompt_token_count = ModelManager.num_tokens_from_string(prompt, model_str)

        total_tokens = prompt_token_count + (max_tokens if max_tokens else 0)
        if total_tokens > model_token_limit:
            raise ValueError(
                f"The total token count ({total_tokens}) exceeds the model's ({model}) limit ({model_token_limit}).")
        return True

    @staticmethod
    def check_agent_model(model: ModelType) -> bool:
        supported_models = ModelType.get_supported_models()
        if model not in supported_models:
            raise ValueError(f"The model '{model}' is not supported.")
        return True

    @staticmethod
    def num_tokens_from_string(string: str, model_name: str) -> int:
        encoding = tiktoken.encoding_for_model(model_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
