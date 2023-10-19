import openai
from typing import Optional, Union
from utils import config_retrieval
import templates
import models


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
        self.agent = None

    def run_agent(self):
        """
                Executes the GPT agent based on the provided configurations.

                Returns:
                    str: The response from the GPT model.
                """
        if self.chat_agent:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=self.messages,
                frequency_penalty=self.frequency_penalty,
                function_call=self.function_call,
                functions=self.functions,
                logit_bias=self.logit_bias,
                logprobs=self.logprobs,
                max_tokens=self.max_tokens,
                n=self.n,
                presence_penalty=self.presence_penalty,
                stop=self.stop,
                stream=self.stream,
                suffix=self.suffix,
                temperature=self.temperature,
                top_p=self.top_p,
                user=self.user
            )
            str_response = response["choices"][0]["message"].strip()
            return str_response

        else:
            response = openai.Completion.create(
                model=self.model,
                prompt=self.prompt,
                echo=self.echo,
                frequency_penalty=self.frequency_penalty,
                logit_bias=self.logit_bias,
                logprobs=self.logprobs,
                max_tokens=self.max_tokens,
                n=self.n,
                presence_penalty=self.presence_penalty,
                stop=self.stop,
                stream=self.stream,
                suffix=self.suffix,
                temperature=self.temperature,
                top_p=self.top_p,
                user=self.user
            ).choices[0].text.strip()
            str_response = response["choices"][0]["text"].strip()
            return str_response


class GPTManager:
    """
        Manages the creation and execution of GPT agents.
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
        prompt = self.template_manager.transform_into_prompt(prompt)
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
        messages = self.template_manager.transform_into_messages(messages)
        gpt_agent = GPTAgent(
            is_chat_agent=True,
            model=model,
            messages=messages,
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
