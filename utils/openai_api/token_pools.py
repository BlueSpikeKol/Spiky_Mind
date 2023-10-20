import json
import models
from decimal import Decimal

class TokenPool:
    """
    Class to manage and track token usage in various pools.
    """

    def __init__(self, file_path="token_pools.json"):
        self.pools = {}
        self.file_path = file_path
        self.load_data()

    def load_data(self):
        try:
            with open(self.file_path, "r") as f:
                data = f.read()
                if data:
                    self.pools = json.loads(data)
                else:
                    self.pools = {}
        except FileNotFoundError:
            pass

    def save_data(self):
        with open(self.file_path, "w") as f:
            json.dump(self.pools, f)

    def create_pool(self, user_friendly_name):
        """
        Creates a new token pool.

        Parameters:
            user_friendly_name (str): A readable name for the pool.

        Returns:
            str: The name for the new pool or an error message.
        """
        if user_friendly_name in self.pools:
            existing_pools = ", ".join(self.pools.keys())
            return f"The name needs to be unique. Existing pools: {existing_pools}"

        # Initialize the pool with a dictionary structure
        self.pools[user_friendly_name] = {'total_pool_tokens': 0, 'total_pool_cost': 0.0, 'models': {}}

        # Save the data
        self.save_data()

        return user_friendly_name

    def update_pool_counters(self, pool, tokens_used, total_cost, model, prompt_tokens, output_tokens):
        self.pools[pool]['total_pool_tokens'] += tokens_used
        self.pools[pool]['total_pool_cost'] += total_cost

        if model not in self.pools[pool]['models']:
            self.pools[pool]['models'][model] = {'tokens': 0, 'cost': 0.0, 'prompt_tokens': 0, 'output_tokens': 0}

        self.pools[pool]['models'][model]['tokens'] += tokens_used
        self.pools[pool]['models'][model]['cost'] += total_cost
        self.pools[pool]['models'][model]['prompt_tokens'] += prompt_tokens
        self.pools[pool]['models'][model]['output_tokens'] += output_tokens

    def add_completion_to_pool(self, completion, pool_names):
        model = completion['model']
        tokens_used = completion['usage']['total_tokens']
        prompt_tokens = completion['usage']['prompt_tokens']
        output_tokens = completion['usage']['output_tokens']

        model_prices = models.ModelType.MODEL_PRICES[model]
        total_cost = Decimal(model_prices['input']) * Decimal(prompt_tokens) + Decimal(model_prices['output']) * Decimal(output_tokens)
        total_cost /= Decimal(1000)

        if "TotalCountPool" not in pool_names:
            pool_names.append("TotalCountPool")

        for pool in pool_names:
            if pool not in self.pools:
                self.pools[pool] = {'total_pool_tokens': 0, 'total_pool_cost': 0.0, 'models': {}}

            self.update_pool_counters(pool, tokens_used, total_cost, model, prompt_tokens, output_tokens)

        self.save_data()
    def get_token_count(self, pool_name):
        """
        Retrieves the token count for a specified pool.

        Parameters:
            pool_name (str): The name for the pool.

        Returns:
            int: The current token count for the pool.
        """
        pool = self.pools.get(pool_name)
        if pool is not None:
            return pool['total_pool_tokens']
        else:
            return None  # Return None if pool not found

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

# uncomment to add a new pool
#token_pool_manager = TokenPool()
#new_pool = token_pool_manager.create_pool("TotalCountPool")

#uncomment to view pools
#token_pool_manager = TokenPool()
#print(token_pool_manager.view_pool("TotalCountPool"))  # View a specific pool
#print(token_pool_manager.view_pool())  # View all pools
