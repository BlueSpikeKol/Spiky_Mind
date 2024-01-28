import re
import uuid
from utils import persistance_access
from gpt_api_old import AI_entities as AI

memory_stream = MemoryStreamAccess.MemoryStreamAccess()

def get_relevent_memories(user_input):
    pass

def parse_uuid(input_string):
    # Regular expression pattern to find UUIDs
    pattern = r'[a-fA-F0-9]{8}-(?:[a-fA-F0-9]{4}-){3}[a-fA-F0-9]{12}'
    # Find all matches of the pattern in the input string
    uuids = re.findall(pattern, input_string)

    # Validate the UUIDs and return only valid ones
    valid_uuids = []
    for u in uuids:
        try:
            # Attempt to create a UUID object from the string
            parsed_uuid = uuid.UUID(u.strip())
            # If no exception occurs, add it to the list of valid UUIDs
            valid_uuids.append(parsed_uuid)
        except ValueError:
            # If an exception occurs, it means the UUID is invalid
            print(f"Invalid UUID: {u}")

    return valid_uuids # is a list

print("I am Spiky, this is a test to see if the conversation is interesting")
exchanges = []
number_of_exchanges = 1
mode = "automatic"  # Start with automatic mode

while True:
    """
    The main conversation loop. Alternates between "automatic" and "guided" modes.
    In "automatic" mode, the conversation is built upon previous exchanges.
    In "guided" mode, the conversation is enriched with data fetched from a database.
    """
    user_input = input()

    if mode == "automatic":
        # Use the previous exchange to build the next one
        exchanges_str = "\n".join(exchanges)
        spiky_input = exchanges_str + "This is a new input from the user. User: " + user_input
        result = AI.spiky_AI(spiky_input)
        print("Spiky (Automatic): ", result)
        mode = "guided"  # Switch to guided mode for the next exchange

    elif mode == "guided":
        # Fetch additional information from the database
        relevent_memories = get_relevent_memories(user_input)
        relevent_memories_str = '. '.join(relevent_memories)
        spiky_input = "This is a new input from the user. User: " + user_input + ". Relevant memories: " + relevent_memories_str
        result = AI.spiky_AI(spiky_input)
        print("Spiky (Guided): ", result)
        mode = "automatic"  # Switch to automatic mode for the next exchange

    exchange_string = "User: " + user_input + "\nSpiky: " + result
    exchanges.append(exchange_string)
    number_of_exchanges += 1