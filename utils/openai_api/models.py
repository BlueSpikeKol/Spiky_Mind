import tiktoken
from typing import Optional


class ModelType:
    """
    Defines constants for the supported model types.
    """
    # Embedding Models
    TEXT_EMBEDDING_ADA = "text-embedding-ada-002"

    # Chat Models
    GPT_3_5_TURBO = "gpt-3.5-turbo-16k-0613"
    CHAT_GPT4 = "gpt-4"
    FUNCTION_CALLING_GPT4 = "gpt-4-0613"

    # Text Models
    TEXT_DAVINCI_COMMON_3 = "text-davinci-003"
    GPT_4_32k = "gpt-4-32k"

    # Categories
    EMBEDDING_MODELS = [TEXT_EMBEDDING_ADA]
    CHAT_MODELS = [GPT_3_5_TURBO, CHAT_GPT4, FUNCTION_CALLING_GPT4]
    TEXT_MODELS = [TEXT_DAVINCI_COMMON_3, GPT_4_32k]

    # Prices per token for each model
    MODEL_PRICES = {
        TEXT_DAVINCI_COMMON_3: {'input': 0.02, 'output': 0.02},
        GPT_3_5_TURBO: {'input': 0.003, 'output': 0.004},
        CHAT_GPT4: {'input': 0.03, 'output': 0.06},
        GPT_4_32k: {'input': 0.06, 'output': 0.12},
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
    TEXT_DAVINCI_COMMON_3 = 4096
    GPT_3_5_TURBO = 16384
    CHAT_GPT4 = 8192
    GPT_4_32k = 32768
    FUNCTION_CALLING_GPT4 = 8192
    TEXT_EMBEDDING_ADA = 8192



class ModelManager:
    def check_agent_model(self, model: str) -> bool:
        supported_models = ModelType.get_supported_models()
        if model not in supported_models:
            raise ValueError(f"The model '{model}' is not supported.")
        return True

    def num_tokens_from_string(self, string: str, model_name: str) -> int:
        encoding = tiktoken.encoding_for_model(model_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def check_agent_token_limit(self, model: str, prompt: str, max_tokens: Optional[int] = None) -> bool:
        model_token_limit = getattr(ModelsTokenLimits, model, None)
        if model_token_limit is None:
            raise ValueError(f"Token limit for model '{model}' is not defined.")
        prompt_token_count = self.num_tokens_from_string(prompt, model)
        total_tokens = prompt_token_count + (max_tokens if max_tokens else 0)
        if total_tokens > model_token_limit:
            raise ValueError(
                f"The total token count ({total_tokens}) exceeds the model's limit ({model_token_limit}).")
        return True
