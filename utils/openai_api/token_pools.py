import json


class TokenPool:
    """
    Class to manage and track token usage in various pools.

    Attributes:
        pools (dict): Dictionary to store token counts for each pool.
        file_path (str): Path to the JSON file for data persistence.
    """

    def __init__(self, file_path="token_pools.json"):
        """
        Initializes the TokenPool object and loads existing data from a JSON file.

        Parameters:
            file_path (str): Path to the JSON file for data persistence. Defaults to "token_pools.json".
        """
        self.pools = {}
        self.file_path = file_path
        self.load_data()

    def load_data(self):
        """Loads existing token pool data from a JSON file."""
        try:
            with open(self.file_path, "r") as f:
                data = f.read()
                if data:
                    self.pools = json.loads(data)
                else:
                    self.pools = {}
        except FileNotFoundError:
            pass  # File will be created when saving data

    def save_data(self):
        """Saves the current token pool data to a JSON file."""
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

        # Initialize the pool with 0 tokens
        self.pools[user_friendly_name] = 0

        # Save the data
        self.save_data()

        return user_friendly_name

    def add_tokens(self, pool_name, tokens):
        """Adds tokens to the specified pool. Creates the pool if it doesn't exist."""
        if pool_name not in self.pools:
            confirm = input(f"The pool {pool_name} does not exist. Do you want to create it? (y/n): ")
            if confirm.lower() == 'y':
                self.pools[pool_name] = 0
            else:
                print("Operation cancelled.")
                return
        self.pools[pool_name] += tokens
        self.save_data()
    def get_token_count(self, pool_name):
        """
        Retrieves the token count for a specified pool.

        Parameters:
            pool_name (str): The name for the pool.

        Returns:
            int: The current token count for the pool.
        """
        return self.pools.get(pool_name, "Pool not found.")

# uncomment to add a new pool
#token_pool_manager = TokenPool()
#new_pool = token_pool_manager.create_pool("TotalCountPool")
