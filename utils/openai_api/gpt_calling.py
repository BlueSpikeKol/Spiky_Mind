import openai
from utils import config_retrieval
import templates
import models
from models import ModelType
import inspect
import token_pools
from dataclasses import dataclass
from typing import Optional, Union, List

EXAMPLE_CHAT_COMPLETION= """
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo-0613",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "\n\nHello there, how may I assist you today?",
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
"""
EXAMPLE_TEXT_COMPLETION = """
{
  "id": "cmpl-uqkvlQyYK7bGYrRHQ0eXlWi7",
  "object": "text_completion",
  "created": 1589478378,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "text": "\n\nThis is indeed a test",
      "index": 0,
      "logprobs": null,
      "finish_reason": "length"
    }
  ],
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 7,
    "total_tokens": 12
  }
}
"""

@dataclass
class AgentConfig:
    """
    Configuration options for creating a GPTAgent.

    Attributes:
        echo (bool): Whether to echo the prompt in the response.
        frequency_penalty (float): Controls the frequency of token occurrence in the output.
        logit_bias (dict): Bias logits before sampling. Pass {"50256": -100} to prevent a specific token from being generated.
        logprobs (int): Number of logprobs to return. Max value is 5.
        max_tokens (int): Maximum number of tokens for the output. Default is 50.
        n (int): Number of completions to generate. Default is 1.
        presence_penalty (float): Controls the presence of tokens in the output.
        stop (Union[str, List[str]]): Token(s) that indicate the end of the generated content.
        stream (bool): Whether to stream the output.
        suffix (str): Suffix to attach after the prompt.
        temperature (float): Controls randomness. Lower value makes output more focused.
        top_p (float): Controls diversity via nucleus sampling. Default is 1.0.
        user (str): Identifier for the user. Default is "developer1".
    """
    echo: Optional[bool] = False
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[dict] = None
    logprobs: Optional[int] = None
    max_tokens: Optional[int] = 50
    n: Optional[int] = 1
    presence_penalty: Optional[float] = 0.0
    stop: Optional[Union[str, List[str]]] = None
    stream: Optional[bool] = False
    suffix: Optional[str] = None
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    user: Optional[str] = "developer1"

class GPTAgent:
    """
    Class to handle GPT-based agents for both chat and completion tasks.
    """
    def __init__(self,
                 model,
                 messages: Union[list,str] = None,
                 echo: Optional[bool] = False,
                 frequency_penalty: Optional[float] = 0.0,
                 function_call: Optional[Union[str, dict]] = "none",
                 functions: Optional[list] = None,
                 logit_bias: Optional[dict] = None, # As an example, you can pass {"50256": -100} to prevent the <|endoftext|> token from being generated.
                 logprobs: Optional[int] = None,  # max value is 5. returns x most likely tokens with prompt.
                 max_tokens: Optional[int] = 50,
                 n: Optional[int] = 1,
                 presence_penalty: Optional[float] = 0.0,
                 stop: Optional[Union[str, list]] = None,
                 stream: Optional[bool] = False,
                 suffix: Optional[str] = None,
                 temperature: Optional[float] = 1.0,
                 top_p: Optional[float] = 1.0,
                 user: Optional[str] = "developper1"):
        self.model = model
        self.messages = messages
        self.echo = echo
        self.frequency_penalty = frequency_penalty
        self.function_call = function_call
        self.functions = functions
        self.logit_bias = logit_bias
        self.logprobs = logprobs
        self.max_tokens = max_tokens
        self.n = n
        self.presence_penalty = presence_penalty
        self.stop = stop
        self.stream = stream
        self.suffix = suffix
        self.temperature = temperature
        self.top_p = top_p
        self.user = user
        self.completion = None

    def run_agent(self, token_pools_list=None):
        """
        Executes the GPT agent based on the provided configurations.

        Parameters:
            token_pools_list (list, optional): List of token pool names to which the token usage will be added.

        Returns:
            dict: The response from the GPT model.
        """
        common_params = self.set_common_params()

        if self.model in ModelType.CHAT_MODELS:
            self.completion = self.run_chat_agent(common_params)
        elif self.model in ModelType.TEXT_MODELS:
            self.completion = self.run_text_agent(common_params)
        elif self.model in ModelType.EMBEDDING_MODELS:
            self.completion = self.run_embedding_agent()

        if self.completion:
            self.add_token_pools(self.completion, token_pools_list or [])

        return self.completion

    def update_agent(self, **kwargs):
        """
        Updates the attributes of the GPTAgent instance.

        Keyword Arguments:
            Any attribute of the GPTAgent class can be updated.

        Example:
            # Update specific fields of the agent
            agent.update_agent(model="text-davinci-002", max_tokens=100, temperature=0.7)

            # Update multiple fields at once
            agent.update_agent(prompt="Tell me a story.", max_tokens=500, temperature=0.5, stop=["\n"])
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_common_params(self):
        """
        Sets the common parameters for both chat and completion agents.

        Returns:
            dict: A dictionary containing the common parameters.
        """
        return {
            'model': self.model,
            'frequency_penalty': self.frequency_penalty,
            'logit_bias': self.logit_bias,
            'max_tokens': self.max_tokens,
            'n': self.n,
            'presence_penalty': self.presence_penalty,
            'stop': self.stop,
            'stream': self.stream,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'user': self.user
        }

    def filter_optional_params(self, params: dict) -> dict:
        """
        Filters out optional parameters that are set to their default values.

        Parameters:
            params (dict): Dictionary of parameters to filter.

        Returns:
            dict: Filtered dictionary of parameters.
        """
        default_values = {
            "frequency_penalty": 0.0,
            "function_call": "none",
            "functions": None,
            "logit_bias": None,
            "max_tokens": 50,
            "n": 1,
            "presence_penalty": 0.0,
            "stop": None,
            "stream": False,
            "temperature": 1.0,
            "top_p": 1.0,
        }

        return {k: v for k, v in params.items() if v != default_values.get(k, None)}

    def run_chat_agent(self, common_params):
        """
        Executes the chat agent with the provided common parameters.

        Parameters:
            common_params (dict): Dictionary of common parameters.

        Returns:
            dict: The response from the GPT model.
        """
        chat_params = {
            'messages': self.messages,
            'function_call': self.function_call,
            'functions': self.functions
        }
        filtered_params = self.filter_optional_params({**common_params, **chat_params})
        return openai.ChatCompletion.create(**filtered_params)

    def run_text_agent(self, common_params):
        """
        Executes the completion agent with the provided common parameters.

        Parameters:
            common_params (dict): Dictionary of common parameters.

        Returns:
            dict: The response from the GPT model.
        """
        completion_params = {
            'prompt': self.messages[-1] if self.messages else None,  # Use the last message as the prompt
            'echo': self.echo,
            'logprobs': self.logprobs,
            'suffix': self.suffix
        }
        filtered_params = self.filter_optional_params({**common_params, **completion_params})
        return openai.Completion.create(**filtered_params)

    def run_embedding_agent(self):
        """
        Executes the embedding agent with the provided string.

        Returns:
            dict: The response from the GPT model.
        """
        embedding_data = openai.Embedding.create(input=[self.messages], model=self.model)
        return embedding_data

    def add_token_pools(self, completion, token_pools_list):
        """
        Updates the token pools with the usage data from the completion.

        Parameters:
            completion (dict): The completion object returned by the GPT model.
            token_pools_list (list): List of token pool names to update.
        """
        token_pool_manager = token_pools.TokenPool()
        token_pool_manager.add_completion_to_pool(completion, token_pools_list)

    def get_finish_reason(self, index: Union[List[int], int] = 0):
        """
        Retrieves the finish reason(s) from the completion data.

        Parameters:
            index (Union[List[int], int]): Index or list of indices for which to retrieve the finish reason.

        Returns:
            str or List[str]: The finish reason(s) for the specified index/indices.

        Example Output:
            For chat: "length" OR "content_filter" OR "stop" OR "function_call"
            For text: "length" OR "content_filter" OR "stop"
        """
        if self.completion:
            if isinstance(index, list):
                return [self.completion["choices"][i]["finish_reason"] for i in index]
            return self.completion["choices"][index]["finish_reason"]
        return "No completion data available."

    def get_usage(self):
        """
        Retrieves the usage statistics from the completion data.

        Returns:
            dict: The usage statistics.

        Example Output:
            {'prompt_tokens': 9, 'completion_tokens': 12, 'total_tokens': 21}
        """
        if self.completion:
            return self.completion["usage"]
        return "No completion data available."

    def get_id(self):
        """
        Retrieves the ID from the completion object, created by openai.

        Returns:
            str: The ID of the completion.

        Example Output:
            "chatcmpl-123"
        """
        if self.completion:
            return self.completion["id"]
        return "No completion data available."

    def get_object(self):
        """
        Retrieves the object type from the completion data.

        Returns:
            str: The object type.

        Example Output:
            "chat.completion" OR "text_completion"
        """
        if self.completion:
            return self.completion["object"]
        return "No completion data available."

    def get_text(self, index: Union[List[int], int] = 0):
        """
        Retrieves the text content from the completion data.

        Parameters:
            index (Union[List[int], int]): Index or list of indices for which to retrieve the text content.

        Returns:
            str or List[str]: The text content for the specified index/indices.

        Example Output:
            For chat: "\n\nHello there, how may I assist you today?"
            For text: "\n\nThis is indeed a test"
        """
        if self.completion:
            if "message" in self.completion["choices"][0]:
                # This is a chat completion
                if isinstance(index, list):
                    return [self.completion["choices"][i]["message"]["content"] for i in index]
                return self.completion["choices"][index]["message"]["content"]
            else:
                # This is a text completion
                if isinstance(index, list):
                    return [self.completion["choices"][i]["text"] for i in index]
                return self.completion["choices"][index]["text"]
        return "No completion data available."

    def get_vector(self):
        """
        Retrieves the vector object from the completion data.

        Returns:
            list: The vector object if available, otherwise a message indicating it's not available.

        Example Output:
            [0.0023064255, -0.009327292, ...., -0.0028842222]
        """
        if self.completion and 'embedding' in self.completion:
            return self.completion['embedding']
        return "No vector data available."

    def get_model_used(self):
        """
        Retrieves the model used for the completion.

        Returns:
            str: The model used if available, otherwise a message indicating it's not available.

        Example Output:
            "text-embedding-ada-002"
        """
        if self.completion and 'model' in self.completion:
            return self.completion['model']
        return "No model data available."


class GPTManager:
    """
    Manages the creation of GPT agents for various tasks (prompt, chat, embedding, etc.).
    """

    def __init__(self):
        """
        Initializes the GPTManager with necessary configurations.
        """
        config = config_retrieval.ConfigManager()
        openai.api_key = config.openai.api_key
        self.template_manager = templates.TemplateManager()
        self.model_manager = models.ModelManager()

    def create_agent(self, model: str, **kwargs) -> 'GPTAgent':
        if not self.model_manager.check_agent_model(model):
            raise ValueError("Invalid model.")
        return GPTAgent(model=model, **kwargs)