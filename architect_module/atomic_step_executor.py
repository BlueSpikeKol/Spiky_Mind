from architect_module.orchestrator import project_schedule
from gpt_api_old import AI_entities as AI
import json
from transformers import BertTokenizer, BertModel
import torch

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')
JSON_FILEPATH = r"../../utils/function_calling/JSON_function_calling.txt"
JSON_INPUT_EXAMPLE = """{
  "id": "TaskID_91011",
  "links": ["TaskID_1234", "TaskID_5678"],
  "estimated_time": "2 hours",
  "level_of_priority": "High",
  "comments": "This task is foundational for several other tasks. Make sure to validate the dictionary against a schema.",
  "task_description": "The task is to create a Python dictionary that holds all the names from the 'user' table in the database. This task requires that a database connection be established and that the program has read access to the user table. The dictionary should have user IDs as keys and names as values."
}
"""


class AtomicStepExecutor:
    def __init__(self, json_input):
        self.data_input = self.parse_json(
            json_input)  # this is what the atomic step content will look like. it does not come from the user, but from the orchestrator generator

        self.function_obj = None  # this does not come from a speculation made by the orchestrator generator, but from the function calling manager. not speculative, it is confirmed
        self.function_json = None
        self.function_name = None
        self.function_args = None

    def parse_json(self, json_input):
        # Parse JSON and return the data
        return json.loads(json_input)

    def get_bert_embedding(self, text):
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1)

    def physical_or_computer_task(self):
        physical_task_string = "it's a physical task that needs to be performed"
        computer_task_string = "This is a computer or informatics task that needs to be performed"

        physical_task_embedding = self.get_bert_embedding(physical_task_string)
        computer_task_embedding = self.get_bert_embedding(computer_task_string)

        data_comparison_embedding = self.get_bert_embedding(self.data_input["task_description"])

        all_task_types = {
            'physical_task': physical_task_embedding,
            'computer_task': computer_task_embedding
        }

        task_scores = {}

        for task_name, task_embedding in all_task_types.items():
            task_scores[task_name] = torch.cosine_similarity(task_embedding, data_comparison_embedding, dim=-1).item()

        # Find the task with the highest score
        highest_score_task = max(task_scores, key=task_scores.get)

        # Return as an int (assuming you have a mapping for this)
        task_mapping = {'physical_task': 0, 'computer_task': 1}

        return task_mapping[highest_score_task]

    def search_and_execute_existing_function(self):
        messages = \
            [
                {
                    "role": "user",
                    "content": self.data_input["task_description"]
                }
            ]
        function_manager = function_call_manager.FunctionCallManager(function_repositery, JSON_FILEPATH)
        self.function_obj, self.function_json, self.function_name, self.function_args = AI.function_calling(messages,
                                                                                                            function_manager)

    def create_new_function(self):
        # Create a new function based on self.description, self.parameters, and self.data
        pass  # Placeholder

    def announce_atomic_step_to_user(self):
        print(self.data_input)
        pass

    def execute_atomic_step(self):
        is_computer_task = self.physical_or_computer_task()
        if is_computer_task == 1:
            self.search_and_execute_existing_function()
            if not self.function_obj:
                self.create_new_function()
        else:
            # Call the function to announce the atomic step to the user
            print(self.announce_atomic_step_to_user())  # Placeholder function


atomic_executor = AtomicStepExecutor("""{
  "id": "TaskID_91011",
  "links": ["TaskID_1234", "TaskID_5678"],
  "estimated_time": "2 hours",
  "level_of_priority": "High",
  "comments": "This task is foundational for several other tasks. Make sure to validate the dictionary against a schema.",
  "task_description": "The task is to create a Python dictionary that holds all the names from the 'user' table in the database. This task requires that a database connection be established and that the program has read access to the user table. The dictionary should have user IDs as keys and names as values."
}""")
atomic_executor.execute_atomic_step()
