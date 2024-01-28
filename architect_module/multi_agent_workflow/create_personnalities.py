my_message_list = [{'role': 'user', 'content': 'Blogger'}, {'role': 'user', 'content': 'Farmer'}, {'role': 'user', 'content': 'Fashion designer'}, {'role': 'user', 'content': 'Filmmaker'}, {'role': 'user', 'content': 'Gamer'}, {'role': 'user', 'content': 'Homemaker'}, {'role': 'user', 'content': 'Influencer'}, {'role': 'user', 'content': 'Nutritionist'}, {'role': 'user', 'content': 'Photographer'}, {'role': 'user', 'content': 'Salesperson'}, {'role': 'user', 'content': 'Student'}, {'role': 'user', 'content': 'Translator'}, {'role': 'user', 'content': 'Tutor'}, {'role': 'user', 'content': 'Veterinarian'}, {'role': 'user', 'content': 'Writer'}, {'role': 'user', 'content': 'Yoga instructor'}, {'role': 'user', 'content': 'YouTuber'}, {'role': 'user', 'content': 'Zoologist'}, {'role': 'user', 'content': 'Accountant'}, {'role': 'user', 'content': 'Actor'}, {'role': 'user', 'content': 'Administrator'}, {'role': 'user', 'content': 'Analyst'}, {'role': 'user', 'content': 'Artist'}, {'role': 'user', 'content': 'Athlete'}, {'role': 'user', 'content': 'Author'}, {'role': 'user', 'content': 'Chef'}, {'role': 'user', 'content': 'Coach'}, {'role': 'user', 'content': 'Consultant'}, {'role': 'user', 'content': 'Counselor'}, {'role': 'user', 'content': 'Designer'}, {'role': 'user', 'content': 'Developer'}, {'role': 'user', 'content': 'Doctor'}, {'role': 'user', 'content': 'Editor'}, {'role': 'user', 'content': 'Engineer'}, {'role': 'user', 'content': 'Entrepreneur'}, {'role': 'user', 'content': 'Event Planner'}, {'role': 'user', 'content': 'Financial Advisor'}, {'role': 'user', 'content': 'Fitness Trainer'}, {'role': 'user', 'content': 'Graphic Designer'}, {'role': 'user', 'content': 'Human Resources Manager'}, {'role': 'user', 'content': 'Interpreter'}, {'role': 'user', 'content': 'Journalist'}, {'role': 'user', 'content': 'Lawyer'}, {'role': 'user', 'content': 'Marketer'}, {'role': 'user', 'content': 'Musician'}, {'role': 'user', 'content': 'Nutritionist'}, {'role': 'user', 'content': 'Personal Assistant'}, {'role': 'user', 'content': 'Photographer'}, {'role': 'user', 'content': 'Physical Therapist'}, {'role': 'user', 'content': 'Programmer'}, {'role': 'user', 'content': 'Project Manager'}, {'role': 'user', 'content': 'Psychologist'}, {'role': 'user', 'content': 'Public Relations Specialist'}, {'role': 'user', 'content': 'Real Estate Agent'}, {'role': 'user', 'content': 'Researcher'}, {'role': 'user', 'content': 'Sales Representative'}, {'role': 'user', 'content': 'Scientist'}, {'role': 'user', 'content': 'Social Media Manager'}, {'role': 'user', 'content': 'Software Developer'}, {'role': 'user', 'content': 'Teacher'}, {'role': 'user', 'content': 'Technical Writer'}, {'role': 'user', 'content': 'Translator'}, {'role': 'user', 'content': 'Travel Agent'}, {'role': 'user', 'content': 'Video Editor'}, {'role': 'user', 'content': 'Virtual Assistant'}, {'role': 'user', 'content': 'Web Developer'}, {'role': 'user', 'content': 'Writer'}, {'role': 'user', 'content': 'Zoologist'}]
try_message_list = [{'role': 'user', 'content': 'Blockchain Developer'}, {'role': 'user', 'content': 'Cybersecurity Expert'}]

import json
from utils.openai_api import gpt_calling
from utils.openai_api.models import ModelType

message = """
can you create a short introduction(two small sentences) for the following characters.Do not give them a name. the most important part is to highlight their profession in a broad sense, not too specific and do not add too much information to theirbackground(specialized in a specific branch of their work for example). Not only that but you must ALWAYS start with 'you are [person_name]' and end with the sentence 'you share a common interest in collaborating with others to explore a topic given by the debate president who will be leading the discussion. you must be honnest and propose high level solutions to advance the discussion'. if possible gear their personnality to have at least one trait that would help in the project described here, which will be part of the discussion:
In an era where climate change looms as an existential threat, the Global Renewable Energy Grid (GREG) aims to be a groundbreaking initiative, reimagining the very fabric of how the world consumes energy. Anchored in Geneva, Switzerland, but with a reach that spans continents, GREG envisions a future where energy is abundant, clean, and universally accessible, irrespective of geographic or economic barriers."""
def create_personnality(item):
    gpt = gpt_calling.GPTManager()
    agent = gpt.create_agent(ModelType.CHAT_GPT4_old, messages=item, system_prompt=message, temperature= 0.2, max_tokens=125)
    agent.run_agent()
    personnality = agent.get_text()
    return personnality


def main():
    # Dictionary to hold the processed results
    result_dict = {}

    # Iterate through the list of items
    for item in try_message_list:
        # Process the item using the function and store the return value
        processed_value = create_personnality(item)

        # Extract content from the item dictionary to use as key
        item_key = item['content']

        # Append the return value to the dictionary, with the item as the key
        result_dict[item_key] = processed_value

    # Save the dictionary to a JSON file
    with open('agent_roles_permanent.json', 'w') as json_file:
        json.dump(result_dict, json_file, indent=4)



# Entry point of the script
if __name__ == '__main__':
    main()
