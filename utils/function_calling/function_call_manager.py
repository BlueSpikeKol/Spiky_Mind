import inspect
import json

class FunctionCallManager:
    def __init__(self, functions_module, json_file_path):
        self.functions_dict = {}
        self.populate_functions_and_metadata(functions_module, json_file_path)

    def populate_functions_and_metadata(self, functions_module, json_file_path):
        # Load metadata from JSON file
        with open(json_file_path, 'r') as f:
            metadata_dict = json.load(f)

        # Populate functions and their metadata
        for name, obj in inspect.getmembers(functions_module, inspect.isfunction):
            if name in metadata_dict:  # Only add functions that have metadata
                self.functions_dict[name] = {
                    'function': obj,
                    'metadata': metadata_dict[name]
                }

    def update_function_and_metadata(self, function_name, new_function, new_metadata):
        self.functions_dict[function_name] = {
            'function': new_function,
            'metadata': new_metadata
        }

    def remove_function_and_metadata(self, function_name):
        if function_name in self.functions_dict:
            del self.functions_dict[function_name]

    def call_function(self, function_name, function_args_json):
        function_data = self.functions_dict.get(function_name)
        if function_data is None:
            return "Function not found"

        function_to_call = function_data['function']
        function_args = json.loads(function_args_json)
        return function_to_call(**function_args)

# Usage
# Assume my_functions is your module containing the functions
# manager = FunctionCallManager(my_functions,r"C:\Users\philippe\Documents\pdf to txt files\test\JSON_function_calling.txt")
