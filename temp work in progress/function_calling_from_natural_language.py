from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType

from AllFunctions import *

import openai
from openai import OpenAI

GPT_MODEL = "gpt-4o"
client = OpenAI()


def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


def test_gpt_4o(query):
    # gpt_manager = GPTManager()
    # model = ModelType.GPT_4_OMNI

    tool_use = {"type": "function", "function": {"name": "add"}}

    ls_func = [
        {
            "type": "function",
            "function": {
                "name": "regroup",
                "description": "Isolate from the rest of the query all the instructions that are connected",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "multiple instructions whose result are inter dependent"
                        }
                    },
                    "required": ["text"]
                }
            }
        }
    ]

    messages = []
    messages.append({"role": "system",
                     "content": "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."})
    messages.append({"role": "user", "content": query})
    chat_response = chat_completion_request(
        messages, tools=ls_func, tool_choice="required"
    )
    assistant_message = chat_response.choices[0].message
    messages.append(assistant_message)
    # print(messages)

    for lol in assistant_message.tool_calls:
        print(lol)

    """
    agent = gpt_manager.create_agent(model=model, temperature=0.5, messages=query, function_call=tool_use,
                                     functions=ls_func)

    agent.run_agent()
    print(agent.get_text())
    """


if __name__ == "__main__":
    query1 = "I want to go to Montreal from 12 to 15 August. If it's above 25°C, book a paddle. If not, book a visit to the Musée des Beaux Arts. What is the result of 1 + 2 and 3 + 4 - 5 + 6 + 7 and (1/pi) ^ e + ln(sqrt(pi^21)) ?"  # "What is the result of 1 + 2 and 3 + 4 - 5 + 6 + 7 and (1/pi) ^ e + ln(sqrt(pi^21)) ?" #
    test_gpt_4o(query1)

"""
La première fonction cherche à savoir la température dans un lieu spécifique à une date spécifique.
La seconde fonction cherche à réserver une activité en fonction de la température à une date spécifique dans un lieu spécifique.

ex: Je veux aller à Montreal du 12 au 15 aout. S'il fera plus que 25°C, réserve une sortie en paddle. Sinon réserve une visite au musée des beaux arts.
"""