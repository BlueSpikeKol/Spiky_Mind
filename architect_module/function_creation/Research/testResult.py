def group_false_letters(letters, booleans):
    """
    Groups all letters from the input list where their corresponding boolean value is False.
    
    :param letters: A list of single-character strings (letters).
    :param booleans: A list of boolean values.
    :return: A string containing all letters from the 'letters' list where the corresponding
             value in the 'booleans' list is False.
    
    :raises ValueError: If the input lists are not of the same size.
    """

    if len(letters) != len(booleans):
        raise ValueError("The 'letters' and 'booleans' lists must have the same size.")

    result = ''.join(letter for letter, boolean in zip(letters, booleans) if not boolean)
    return result


# Example usage:
# letters_list = ['a', 'b', 'c', 'd', 'e']
# booleans_list = [True, False, True, False, True]
# print(group_false_letters(letters_list, booleans_list))  # Output would be 'bd'


def reveal_word_in_boolean_list(boolean_list, word_size, start_index, direction):
    """
    This function takes a list of booleans and modifies it by setting the values to True
    at the positions where the letters of a word are located, based on the given word size,
    start index, and direction.

    Parameters:
    - boolean_list (list of bool): The list of booleans to modify.
    - word_size (int): The size of the word to reveal.
    - start_index (int): The index of the first letter of the word in the list.
    - direction (int): The direction in which the word is found (1 for forward, -1 for backward).

    Returns:
    - None: The function modifies the input list in place.
    
    Raises:
    - ValueError: If the start_index is out of the bounds of the list or if the word goes out of bounds.
    - TypeError: If the input types are not as expected.
    """

    # Validate inputs
    if not isinstance(boolean_list, list) or not all(isinstance(b, bool) for b in boolean_list):
        raise TypeError("boolean_list must be a list of booleans.")
    if not isinstance(word_size, int) or word_size < 1:
        raise ValueError("word_size must be a positive integer.")
    if not isinstance(start_index, int) or not (0 <= start_index < len(boolean_list)):
        raise ValueError("start_index must be a valid index in boolean_list.")
    if direction not in [1, -1]:
        raise ValueError("direction must be either 1 (forward) or -1 (backward).")

    # Calculate the end index based on direction and word size
    end_index = start_index + direction * word_size

    # Validate if the word goes out of bounds
    if direction == 1 and end_index > len(boolean_list):
        raise ValueError("The word exceeds the list bounds.")
    if direction == -1 and end_index < -1:
        raise ValueError("The word exceeds the list bounds.")

    # Set the values to True where the letters of the word are
    for i in range(word_size):
        boolean_list[start_index + i * direction] = True


def highlight_word_positions(letter_list, word_size, positions_directions):
    """
    This function takes a list of letters, the size of a word, and a nested list of positions
    and directions. It returns a list of booleans where each boolean corresponds to a position
    in the letter list. The function sets the boolean value to True for the positions where
    the letters of the word are located based on the provided positions and directions.
    
    Parameters:
    letter_list (list of str): A one-dimensional list of single-character strings.
    word_size (int): The size of the word to highlight in the list.
    positions_directions (list of tuples): A nested list of tuples, where each tuple contains
        a position (int) and a direction (1 or -1) indicating the sense in which the word was written.
    
    Returns:
    list of bool: A list of boolean values where True indicates the presence of a word letter.
    """

    # Initialize the list of booleans with False
    bool_list = [False] * len(letter_list)

    # Iterate over each position and direction pair
    for position, direction in positions_directions:
        # Calculate the indices of the word's letters based on the current position and direction
        indices = [position + i * direction for i in range(word_size)]

        # Set the corresponding boolean values to True
        for idx in indices:
            if 0 <= idx < len(letter_list):  # Ensure index is within the bounds of the list
                bool_list[idx] = True

    return bool_list


def is_index_out_of_bounds(letter_list, index):
    """
    Check if the given index is out of bounds for the provided one-dimensional list of letters.
    
    Parameters:
    letter_list (list): A one-dimensional list of letters.
    index (int): The index to check.
    
    Returns:
    bool: True if the index is out of bounds or negative, False otherwise.
    """
    # Check if the index is negative or greater than or equal to the length of the list
    return index < 0 or index >= len(letter_list)


def find_character_indices(char_list, character):
    """
    Finds all positive indices in a list where the given character is found.
    
    Parameters:
    char_list (list of str): The list of characters to search through.
    character (str): The character to find in the list.
    
    Returns:
    list: A list of positive indices where the character is found. 
          Returns an empty list if the character is not found.
    """
    # Initialize an empty list to store the indices
    indices = []

    # Loop through the list and check if the character matches
    # the current element. If it does, append the index to indices.
    for index, char in enumerate(char_list):
        if char == character:
            indices.append(index + 1)  # +1 to convert to positive index

    return indices


def find_word_in_list(letters, word, index, direction):
    """
    This function checks if a word is present in a one-dimensional list of letters starting
    from a specified index and in a given direction.
    
    Parameters:
    letters (list): A one-dimensional list of single-character strings.
    word (str): The word to search for within the list.
    index (int): The index in the list from which to start the search.
    direction (str): The direction of search, can be 'forward' or 'backward'.
    
    Returns:
    bool: True if the word is found in the specified direction starting from the index, False otherwise.
    """

    word_length = len(word)

    # Check if the index is within the bounds of the list
    if index < 0 or index >= len(letters):
        return False

    # Search forward
    if direction == 'forward':
        if index + word_length > len(letters):
            return False
        return letters[index:index + word_length] == list(word)

    # Search backward
    elif direction == 'backward':
        if index - word_length < -1:
            return False
        return letters[index - word_length + 1:index + 1] == list(word[::-1])

    # If direction is not recognized
    else:
        raise ValueError("Direction must be 'forward' or 'backward'")


def find_word_directions(letter_list, word, index):
    """
    Searches for occurrences of a word in a one-dimensional list of letters starting from a given index.
    The function returns a list of directions in which the word has been found.
    
    Parameters:
    letter_list (list of str): The one-dimensional list of single-letter strings.
    word (str): The word to search for within the letter list.
    index (int): The starting index from which to search for the word.
    
    Returns:
    list: A list of directions ('left', 'right') where the word has been found.
          Returns an empty list if the word is not found.
    """
    directions = []
    word_length = len(word)

    # Check to the right
    if index + word_length <= len(letter_list):
        if letter_list[index:index + word_length] == list(word):
            directions.append('right')

    # Check to the left
    if index - word_length >= -1:  # -1 because slicing is inclusive at the start index
        if letter_list[index - word_length + 1:index + 1] == list(word):
            directions.append('left')

    return directions


def find_word_positions(letter_list, word):
    """
    Searches for occurrences of a word within a list of letters and returns a nested list of indices
    representing the starting and ending positions of the word within the list.

    Parameters:
    letter_list (list of str): A one-dimensional list of single-letter strings.
    word (str): The word to search for within the list of letters.

    Returns:
    list of lists: A nested list where each inner list contains two integers, the start and end index of the word found.
    """
    positions = []
    word_length = len(word)
    for i in range(len(letter_list) - word_length + 1):
        # Extract a substring of the same length as the word from the current position
        substring = ''.join(letter_list[i:i + word_length])
        # If the substring matches the word, store the start and end indices
        if substring == word:
            positions.append([i, i + word_length - 1])
    return positions


# Example usage:
letters = ['h', 'e', 'l', 'l', 'o', 'w', 'o', 'r', 'l', 'd']
word = 'hello'
print(find_word_positions(letters, word))  # Output: [[0, 4]]


def find_remaining_letters(letters, words):
    """
    Creates a list of booleans indicating whether each letter in the input list
    is part of any word in the list of words, and returns a string composed of
    the letters not forming any of the words.
    
    Parameters:
    letters (list of str): A list of single-letter strings.
    words (list of str): A list of words.
    
    Returns:
    str: A string composed of the letters from the input list that do not
         contribute to any of the words in the words list.
    """

    # Initialize the boolean list with False values
    letter_used = [False] * len(letters)

    # Check each word in the list of words
    for word in words:
        # Keep track of letters found for the current word
        found_indices = []
        # Go through each letter in the word
        for letter in word:
            # Check if the letter is in the letters list and not used yet
            if letter in letters:
                index = letters.index(letter)
                if not letter_used[index]:
                    found_indices.append(index)
            else:
                # If any letter of the word is not found, break and don't mark
                break
        else:
            # If all letters were found, mark them as used
            for index in found_indices:
                letter_used[index] = True

    # Create the string of unused letters
    remaining_letters = ''.join([letters[i] for i in range(len(letters)) if not letter_used[i]])

    return remaining_letters


if __name__ == "__main__":
    ls = [i for i in "CBIRDAMBCAGBCEBDNIRDUDRSDR"]

    print(ls)

    a = find_remaining_letters(ls, ["CB", "DR"])
    print(a)
