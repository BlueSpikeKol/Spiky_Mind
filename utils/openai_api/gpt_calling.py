import openai
from typing import Optional, Union, List
from utils import config_retrieval
import templates
import models
import inspect
import token_pools

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

class GPTAgent:
    """
    Class to handle GPT-based agents for both chat and completion tasks.
    """
    def __init__(self,
                 is_chat_agent: bool,
                 model,
                 prompt: str = None,
                 messages: list = None,
                 echo: Optional[bool] = False,
                 frequency_penalty: Optional[float] = 0.0,
                 function_call: Optional[Union[str, dict]] = "none",
                 functions: Optional[list] = None,
                 logit_bias: Optional[dict] = None,
                 # As an example, you can pass {"50256": -100} to prevent the <|endoftext|> token from being generated.
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

        self.chat_agent = is_chat_agent
        self.model = model
        self.prompt = prompt
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
        return {
            'model': self.model,
            'frequency_penalty': self.frequency_penalty,
            'logit_bias': self.logit_bias,
            'logprobs': self.logprobs,
            'max_tokens': self.max_tokens,
            'n': self.n,
            'presence_penalty': self.presence_penalty,
            'stop': self.stop,
            'stream': self.stream,
            'suffix': self.suffix,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'user': self.user
        }

    def run_chat_agent(self, common_params):
        chat_params = {
            'messages': self.messages,
            'function_call': self.function_call,
            'functions': self.functions
        }
        return openai.ChatCompletion.create(**{**common_params, **chat_params})

    def run_completion_agent(self, common_params):
        completion_params = {
            'prompt': self.prompt,
            'echo': self.echo # also returns prompt True or False
        }
        return openai.Completion.create(**{**common_params, **completion_params})

    def update_token_pools(self, usage, token_pools_list):
        token_pool_manager = token_pools.TokenPool()
        if "TotalCountPool" not in token_pools_list:
            token_pools_list.append("TotalCountPool")
        for pool in token_pools_list:
            token_pool_manager.add_tokens(pool, usage)

    def run_agent(self, token_pools_list=None):
        """
        Executes the GPT agent based on the provided configurations.

        Parameters:
            token_pools_list (list, optional): List of token pool names to which the token usage will be added.

        Returns:
            completion openai object: The response from the GPT model.
        """
        common_params = self.set_common_params()

        if self.chat_agent:
            self.completion = self.run_chat_agent(common_params)
        else:
            self.completion = self.run_completion_agent(common_params)

        if self.completion:
            usage = self.completion["usage"]["total_tokens"]
            if token_pools_list is None:
                token_pools_list = []
            self.update_token_pools(usage, token_pools_list)

        if inspect.currentframe().f_back.f_lineno in inspect.getouterframes(inspect.currentframe())[1].frame.f_lineno:
            return self.completion

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
            if self.chat_agent:
                if isinstance(index, list):
                    return [self.completion["choices"][i]["message"]["content"] for i in index]
                return self.completion["choices"][index]["message"]["content"]
            else:
                if isinstance(index, list):
                    return [self.completion["choices"][i]["text"] for i in index]
                return self.completion["choices"][index]["text"]
        return "No completion data available."


class GPTManager:
    """
        Manages the creation of GPT agents into all the types of agent (prompt, message, embedding, function).
    """
    def __init__(self):
        """
                Initializes the GPTManager with necessary configurations.
        """
        config = config_retrieval.ConfigManager()
        openai.api_key = config.openai.api_key
        self.template_manager = templates.TemplateManager()
        self.models_manager = models.ModelManager()
    def get_agent(self,
                  model,
                  prompt,
                  echo: Optional[bool] = False,
                  frequency_penalty: Optional[float] = 0.0,
                  logit_bias: Optional[dict] = None,
                  # As an example, you can pass {"50256": -100} to prevent the <|endoftext|> token from being generated.
                  logprobs: Optional[int] = None,  # max value is 5. returns x most likely tokens with prompt.
                  max_tokens: Optional[int] = 50,
                  n: Optional[int] = 1,
                  presence_penalty: Optional[float] = 0.0,
                  stop: Optional[Union[str, list]] = None,
                  stream: Optional[bool] = False,
                  suffix: Optional[str] = None,
                  temperature: Optional[float] = 1.0,
                  top_p: Optional[float] = 1.0,
                  user: Optional[str] = "developper1"
                  ) -> GPTAgent:
        """
                Creates and returns a GPTAgent for completion tasks.

                args: all the variables possibly involved in the communication with the api

                Returns:
                    GPTAgent: The GPTAgent object.
                """
        prompt_message = self.template_manager.transform_into_prompt(prompt)
        prompt = prompt_message.prompt_str
        #TODO check if there is a better way to hand le the tranformation of messagaes to MessageTypes and back to messages
        if self.models_manager.check_agent_model(model):
            pass
        if self.models_manager.check_agent_token_limit(model, prompt, max_tokens):
            pass
            raise ValueError("Either the prompt or the max_tokens parameter is problematic.")
        gpt_agent = GPTAgent(is_chat_agent=False,
                             model=model,
                             prompt=prompt,
                             echo=echo,
                             frequency_penalty=frequency_penalty,
                             logit_bias=logit_bias,
                             logprobs=logprobs,
                             max_tokens=max_tokens,
                             n=n,
                             presence_penalty=presence_penalty,
                             stop=stop,
                             stream=stream,
                             suffix=suffix,
                             temperature=temperature,
                             top_p=top_p,
                             user=user)
        return gpt_agent

    def get_chat_agent(self,
                       model,
                       messages: list,
                       frequency_penalty: Optional[float] = 0.0,
                       function_call: Optional[Union[str, dict]] = "none",
                       functions: Optional[list] = None,
                       logit_bias: Optional[dict] = None,
                       # As an example, you can pass {"50256": -100} to prevent the <|endoftext|> token from being generated.
                       logprobs: Optional[int] = None,  # max value is 5. returns x most likely tokens with prompt.
                       max_tokens: Optional[int] = 50,
                       n: Optional[int] = 1,
                       presence_penalty: Optional[float] = 0.0,
                       stop: Optional[Union[str, list]] = None,
                       stream: Optional[bool] = False,
                       suffix: Optional[str] = None,
                       temperature: Optional[float] = 1.0,
                       top_p: Optional[float] = 1.0,
                       user: Optional[str] = "developper1"
                       ) -> GPTAgent:
        """
                Creates and returns a GPTAgent for chat tasks.

                Returns:
                    GPTAgent: The GPTAgent object.
        """
        #TODO same as above
        messages = self.template_manager.transform_into_messages(messages)
        gpt_agent = GPTAgent(
            is_chat_agent=True,
            model=model,
            messages=messages.messages,
            frequency_penalty=frequency_penalty,
            function_call=function_call,
            functions=functions,
            logit_bias=logit_bias,
            logprobs=logprobs,
            max_tokens=max_tokens,
            n=n,
            presence_penalty=presence_penalty,
            stop=stop,
            stream=stream,
            suffix=suffix,
            temperature=temperature,
            top_p=top_p,
            user=user)
        return gpt_agent

    def create_embedding(self,embedding_str:str=None):
        """
               Creates an embedding using the provided string.

               Returns:
                   dict: The embedding data.
        """
        ada_embedding = self.template_manager.transform_into_embedding(embedding_str)
        return openai.Embedding.create(input=[ada_embedding.embedding_str], model=ada_embedding.model)['data'][0]['embedding']
    def set_agent(self, agent):
        """
                Sets the GPTAgent object. (This method is currently empty and can be implemented as needed)

                Parameters:
                    agent (GPTAgent): The GPTAgent object to set.
        """
        pass
