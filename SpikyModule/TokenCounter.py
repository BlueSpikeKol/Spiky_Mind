
class TokenCounter:
    def __init__(self):
        self.token_costs = {
            "gpt-4_8k_input": 0.03,
            "gpt-4_8k_output": 0.06,
            "gpt-4_32k_input": 0.06,
            "gpt-4_32k_output": 0.12,
            "gpt-3.5-turbo-16k_input": 0.003,
            "gpt-3.5-turbo-16k_output": 0.004,
            "text-davinci-003_input": 0.0120,
            "text-davinci-003_output": 0.0120,
            "text-embedding-ada-002": 0.0001
        }
        self.total_cost = 0

    def add_tokens(self, model, tokens, direction="input"):
        key = f"{model}_{direction}"
        cost_per_token = self.token_costs.get(key, 0)
        cost = cost_per_token * tokens / 1000  # Convert to per 1K tokens
        self.total_cost += cost

    def get_total_cost(self):
        return self.total_cost

    def check_budget(self, budget=30):
        if self.total_cost > budget:
            remaining = self.total_cost - budget
            return False, remaining
        return True, 0

token_counter = TokenCounter()
token_counter.add_tokens("gpt-4_8k", 5000, "input")
token_counter.add_tokens("gpt-4_8k", 5000, "output")
print(token_counter.get_total_cost())
is_within_budget, remaining = token_counter.check_budget()
print(is_within_budget, remaining)
