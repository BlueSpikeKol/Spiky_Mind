import json
import os
from pathlib import Path
import utils.openai_api.models as models

class TokenPool:
    """
    Class to manage and track token usage in various pools.
    """

    def __init__(self):
        """
        Initialize the TokenPool object.

        Parameters:
            file_path (str): The path to the JSON file where token pool data is stored.
        """
        current_script_path = Path(__file__).resolve()
        parent_folder = current_script_path.parent
        self.file_path = parent_folder.joinpath('token_pools.json')
        self.pools = {}
        self.load_data()

    def load_data(self):
        """
        Load token pool data from a JSON file.
        """
        try:
            with open(self.file_path, "r") as f:
                data = f.read()
                if data:
                    self.pools = json.loads(data)

                    # Ensure 'total_pool_cost' is a float
                    for pool, pool_data in self.pools.items():
                        pool_data['total_pool_cost'] = float(pool_data['total_pool_cost'])

                        # Ensure 'cost' for each model is a float
                        for model, model_data in pool_data['models'].items():
                            model_data['cost'] = float(model_data['cost'])

                else:
                    self.pools = {}
        except FileNotFoundError:
            pass

    def save_data(self):
        """
        Save token pool data to a JSON file.
        """
        with open(self.file_path, "w") as f:
            json.dump(self.pools, f)

    def create_pool(self, user_friendly_name):
        """
        Create a new token pool.

        Parameters:
            user_friendly_name (str): A readable name for the pool.

        Returns:
            str: The name for the new pool or an error message.
        """
        if user_friendly_name in self.pools:
            existing_pools = ", ".join(self.pools.keys())
            return f"The name needs to be unique. Existing pools: {existing_pools}"

        self.pools[user_friendly_name] = {'total_pool_tokens': 0, 'total_pool_cost': 0.0, 'models': {}}
        self.save_data()
        return user_friendly_name

    def update_pool_counters(self, pool, tokens_used, total_cost, model, prompt_tokens, output_tokens):
        """
        Update the token and cost counters for a specific pool and model.

        Parameters:
            pool (str): The name of the pool to update.
            tokens_used (int): The number of tokens used in the latest completion.
            total_cost (float): The total cost of the latest completion.
            model (str): The model used for the latest completion.
            prompt_tokens (int): The number of tokens used for the prompt in the latest completion.
            output_tokens (int): The number of tokens used for the output in the latest completion.
        """
        self.pools[pool]['total_pool_tokens'] += tokens_used
        self.pools[pool]['total_pool_cost'] += float(total_cost)

        if model not in self.pools[pool]['models']:
            self.pools[pool]['models'][model] = {'tokens': 0, 'cost': 0.0, 'prompt_tokens': 0, 'output_tokens': 0}

        self.pools[pool]['models'][model]['tokens'] += tokens_used
        self.pools[pool]['models'][model]['cost'] += float(total_cost)
        self.pools[pool]['models'][model]['prompt_tokens'] += prompt_tokens
        self.pools[pool]['models'][model]['output_tokens'] += output_tokens

    def add_completion_to_pool(self, completion: dict, token_pools_list: list):
        """
        Add a completion to the token pools.

        Parameters:
            completion (dict): The completion data.
            token_pools_list (list): The list of token pools to update.
        """
        if completion is None:
            print("Completion data is None, skipping.")
            return
        model = completion.get('model', 'unknown')
        usage = completion.get('usage', {})
        tokens_used = usage.get('total_tokens', 0)
        prompt_tokens = usage.get('prompt_tokens', 0)
        output_tokens = usage.get('completion_tokens', 0)

        choices = completion.get('choices', [])
        if len(choices) > 0:
            first_choice = choices[0]
            message = first_choice.get('message', {})
            content = message.get('content', 'N/A')

        model_prices = models.ModelType.MODEL_PRICES.get(model, {'input': 0, 'output': 0})
        total_cost = (model_prices['input'] * prompt_tokens + model_prices['output'] * output_tokens) / 1000

        if "TotalCountPool" not in token_pools_list:
            token_pools_list.append("TotalCountPool")

        for pool in token_pools_list:
            if pool not in self.pools:
                self.pools[pool] = {'total_pool_tokens': 0, 'total_pool_cost': 0.0, 'models': {}}

            self.update_pool_counters(pool, tokens_used, total_cost, model, prompt_tokens, output_tokens)

        self.save_data()

    def get_token_count(self, pool_name):
        """
        Retrieve the token count for a specified pool.

        Parameters:
            pool_name (str): The name for the pool.

        Returns:
            int: The current token count for the pool, or None if the pool is not found.
        """
        pool = self.pools.get(pool_name)
        if pool is not None:
            return pool['total_pool_tokens']
        else:
            return None

    def view_pool(self, pool_name=None):
        """
        View the current state of a specific pool or all pools.

        Parameters:
            pool_name (str, optional): The name of the pool to view. If None, all pools are displayed.

        Returns:
            dict: The current state of the specified pool or all pools.
        """
        if pool_name:
            return self.pools.get(pool_name, "Pool not found.")
        else:
            return self.pools
