from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType
from utils import config_retrieval


def execute_querry_gpt_4_turbo(query):
    gpt_manager = GPTManager()
    model = ModelType.GPT_4_TURBO
    agent = gpt_manager.create_agent(model=model, temperature=0.5, messages=query)

    agent.run_agent()
    print(agent.get_text())


def locate_desc_func():
    text = '''
Here is a Python function that fulfills the task described:

```python
def is_index_out_of_bounds(letters, index):
    """
    Determines if the provided index is out of bounds for the given list of letters.
    
    Parameters:
    letters (list): A list of characters.
    index (int): The index to check.
    
    Returns:
    bool: True if the index is out of bounds or negative, False otherwise.
    """
    # Check if the index is negative or beyond the length of the letters list
    return index < 0 or index >= len(letters)

# Libraries used:
Library: NA
```

This function does not require any external libraries, so the answer to the library used is "NA".
    '''

    # print(text.find("```python"))
    start_code = text.find("```python") + 9
    end_code = text[start_code:].find("```") + start_code

    code = text[start_code: end_code]
    # print(code)

    name = ""
    index = code.find("def") + 4
    done = False
    while not done:
        if code[index] == ":":
            done = True
        else:
            name += code[index]
            index += 1

    # print(name)

    start_desc = code.find('"""') + 3
    end_desc = code[start_desc:].find('"""') + start_desc

    desc = code[start_desc:end_desc]

    # print(desc)

    result = "Function: "
    result += name + desc

    return result

if __name__ == "__main__":
    query = "I'm a French citizen studying in Montreal. I went to Montreal 3 years ago. Now I have a private health insurance but I would like to get the quebec one. I don't have the franch health insurance since I'm not currently living in France. How can I get the Quebec health insurance (RamQ) ?"
    query2 = "I'm a French citizen studying in Montreal. I need to complete a mandatory internship. I got accepted at the Herzberg Astronomy and Astrophysics (HAA). But then I will work for the NRC. What document do I need to complete and what procedures should I follow ?"
    #execute_querry_gpt_4_turbo(query2)
    locate_desc_func()
