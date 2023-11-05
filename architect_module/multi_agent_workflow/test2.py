from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType

messages = "Debate President: Welcome, software developer and project manager. It's great to have both of you here. " \
           "As we start the discussion, let's begin with the first challenge: the extraction process. We need to " \
           "determine the most efficient method to extract information from the user's Python project. What are your " \
           "thoughts on this challenge?\n\nRemember, the goal is to extract both machine-readable and human-readable " \
           "data or metadata and structure it in a clear and easy-to-understand manner."
differentiate_system_prompt = """Using the provided text by a debate president, determine whether it reflects a 'main' or 'side' 
conversation in the context of a structured debate. For 'main' conversations, identify elements that suggest a broad, 
strategic dialogue, such as overarching issues, project-wide implications, or high-level problem identification. Look 
for indicators of conceptual discussion over technical specifics. For 'side' conversations, identify signs of a more 
detailed, tactical discourse, such as specific task-oriented details, granular steps towards problem-solving, 
or actionable solutions. Classify the text accordingly and provide justification for your classification based on the 
content and focus of the discussion. Provide your answer with this format:
[<Conversation Classification 'main' or 'side'>]
<Justification of classification>"""

gpt_manager = GPTManager()
differentiate_agent = gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=messages,
                                               system_prompt=differentiate_system_prompt, max_tokens=75)
differentiate_agent.run_agent()
print(differentiate_agent.get_text())
