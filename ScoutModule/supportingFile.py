def split_text(text, separator):
    # Step 1: Find the indices of the first and second characters of the separator
    split_indices_first_char = [i for i, char in enumerate(text) if char == separator[0]]
    split_indices_second_char = [i for i, char in enumerate(text) if char == separator[1]]

    # Combine and sort the indices
    split_indices = sorted(split_indices_first_char + split_indices_second_char)

    # Step 2: Determine which parts were inside the separators
    parts = []
    prev_idx = 0
    for idx in split_indices:
        parts.append(text[prev_idx: idx])
        prev_idx = idx + 1
    parts.append(text[prev_idx:])

    # Step 3: Create lists of inside and outside parts, replacing empty strings with "unavailable"
    inside_separators = [part if part else 'unavailable text' for part in parts[1::2]]
    outside_separators = [part if part else 'unavailable text' for part in parts[::2]]

    # Step 4: Return the final list
    return [inside_separators, outside_separators]

# Test the function
print(split_text("This is some<text> and some more<> and even more<text>", "<>"))
