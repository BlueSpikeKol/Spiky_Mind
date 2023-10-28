# Import the GPTManager class
from utils.openai_api.gpt_calling import GPTManager  # Replace 'your_module' with the actual module name
from models import ModelType

# Initialize the GPTManager
gpt_manager = GPTManager()
valid_messages = [
    {"role": "user", "content": "Tell me a joke."},
    {"role": "assistant", "content": "Why did the chicken cross the road?"}
]
# Test get_agent method
print("Testing get_agent:")
agent1 = gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=valid_messages)
print(f"Agent1 Result: {agent1.run_agent()}")  # Assuming GPTAgent has a run() method to execute the agent and get the result

# Test get_chat_agent method with valid messages
print("Testing get_chat_agent:")

agent2 = gpt_manager.create_agent(model=ModelType.TEXT_DAVINCI_COMMON_3, messages="valid_messages")
print(f"Agent2 Chat Result: {agent2.run_agent()}")  # Assuming GPTAgent has a run_chat() method

# Test get_embedding_agent method
print("Testing get_embedding_agent:")
agent3 = gpt_manager.create_agent(model=ModelType.TEXT_EMBEDDING_ADA, messages="Embed this text.")
print(f"Agent3 Embedding Result: {agent3.run_agent()}")  # Assuming GPTAgent has a run_embedding() method