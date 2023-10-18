def fetch_user_names_from_db_to_dict(start_id, end_id):
    """
    Simulates fetching all names from the 'user' table in the database and returns them as a dictionary.
    The dictionary will have user IDs as keys and names as values.

    Parameters:
    start_id (int): The starting ID for the dictionary.
    end_id (int): The ending ID for the dictionary.

    Returns:
    dict: A dictionary containing user IDs as keys and names as values.
    """
    user_dict = {}
    for i in range(start_id, end_id + 1):
        user_dict[i] = f"Name_{i}"

    return user_dict


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b
