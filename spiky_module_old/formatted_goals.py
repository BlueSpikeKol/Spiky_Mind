import os
from gpt_api_old import AI_entities as AI
import spacy
import traceback
from transformers import BertTokenizer, BertModel
import torch

"""
This module is designed to process a series of text-based exchanges between a user and an AI entity.
The goal is to integrate these exchanges into a structured text document, organized into various sections.
Each section contains bullet points that summarize the key points of the exchanges.

The module uses Natural Language Processing (NLP) to determine the most appropriate section and bullet point
to integrate the new information. If no suitable section or bullet point is found, new ones are created.

External AI functions are used for goal formation and confirmation.
"""

nlp = spacy.load("en_core_web_lg")  # Using the large spaCy model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

def get_bert_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1)
def string_to_formatted_list(conversation_text):
    try:
        if isinstance(conversation_text, str):
            conversation_lines = conversation_text.splitlines()
        elif isinstance(conversation_text, list):
            conversation_lines = conversation_text
        else:
            raise ValueError("Input must be either a string or a list of strings.")

        # Filter out empty lines or lines that are just whitespace
        conversation_lines = [line for line in conversation_lines if line.strip()]

        formatted_conversation = []

        for i in range(0, len(conversation_lines), 2):
            ai_split = conversation_lines[i].split(": ", 1)
            ai_line = ai_split[1] if len(ai_split) > 1 else "N/A"

            if i + 1 < len(conversation_lines):
                user_split = conversation_lines[i + 1].split(": ", 1)
                user_line = user_split[1] if len(user_split) > 1 else "N/A"
            else:
                user_line = "N/A"

            exchange = {
                "Spiky": ai_line,
                "User": user_line
            }
            formatted_conversation.append(exchange)

        return formatted_conversation
    except Exception as e:
        print(f"An error occurred in string_to_formatted_list: {e}")
        return []

def goal_creation_AI_call(exchange):
    formatted_string = ""
    for key, value in exchange.items():
        formatted_string += f"{key}: {value}\n"
    formatted_string = AI.goal_creation_AI(formatted_string)
    return formatted_string


# Function for goal confirmation
def goal_confirmation(exchange):
    formatted_string = ""
    for key, value in exchange.items():
        formatted_string += f"{key}: {value}\n"
    approval = AI.goal_approval_AI(formatted_string)
    return approval

def get_section_names_from_file(file_path, comment_file_path):
    sections, _ = read_txt_to_dict(file_path, comment_file_path)
    return list(sections.keys())

def choose_section(formatted_text, file_path, comment_file_path):
    section_names = get_section_names_from_file(file_path, comment_file_path)
    section_name_temp = AI.create_new_section_AI(formatted_text)
    section_name_temp_embedding = get_bert_embedding(section_name_temp)
    max_similarity = 0
    chosen_section = None

    for section in section_names:
        section_embedding = get_bert_embedding(section)
        similarity = torch.cosine_similarity(section_name_temp_embedding, section_embedding, dim=-1)
        if similarity > max_similarity:
            max_similarity = similarity
            chosen_section = section

    if chosen_section:
        approval = AI.similarity_approval_AI(formatted_text, chosen_section)
        if approval:
            return chosen_section
        else:
            return section_name_temp


def choose_or_add_line(section, formatted_text, file_path, comment_file_path):
    sections, _ = read_txt_to_dict(file_path, comment_file_path)
    formatted_embedding = get_bert_embedding(formatted_text)

    if section in sections:
        max_similarity = 0
        line_index = None

        for i, existing_line in enumerate(sections[section]):
            existing_embedding = get_bert_embedding(existing_line)
            similarity = torch.cosine_similarity(formatted_embedding, existing_embedding, dim=-1)

            if similarity > max_similarity:
                max_similarity = similarity
                line_index = i

        if max_similarity > 0.7:  # Threshold for considering lines as similar
            approval = AI.similarity_approval_AI(formatted_text, sections[section][line_index])
            if approval:
                print(section + formatted_text + "will be replaceing"+line_index)
                return line_index  # Replace the existing line


    return None  # Indicates a new line should be added



# Helper function to read the text file into a dictionary
def read_txt_to_dict(file_path,comment_file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    sections = {}
    current_section = None

    for line in lines:
        line = line.strip()
        if line.startswith('Section Start:'):  # Custom section start
            current_section = line[len('Section Start:'):].strip()
            sections[current_section] = []
        elif line.startswith('Section End:'):  # Custom section end
            current_section = None
        elif current_section is not None:
            sections[current_section].append(line)
    comments = {}
    with open(comment_file_path, 'r') as f:
        lines = f.readlines()

    current_key = None
    for line in lines:
        line = line.strip()
        if line.startswith('Key:'):
            current_key = line[len('Key:'):].strip()
        elif current_key is not None:
            comments[current_key] = line

    return sections, comments



# Helper function to write the dictionary back to the text file
def write_dict_to_txt(sections,comments,file_path,comment_file_path):
    with open(file_path, 'w') as f:
        for section, bullet_points in sections.items():
            f.write(f'Section Start:{section}\n')  # Custom section start
            print(f'Section Start:{section}\n')
            for point in bullet_points:
                f.write(f'{point}\n')
                print(f'{point}\n')
            f.write(f'Section End:{section}\n')  # Custom section end
            print(f'Section End:{section}\n')
    with open(comment_file_path, 'w') as f:
        for key, comment in comments.items():
            f.write(f'Key:{key}\n')
            f.write(f'{comment}\n')



# Helper function to integrate line into file
def integrate_line_to_file(section, line_index, formatted_text, file_path, comment_file_path):
    sections, comments = read_txt_to_dict(file_path, comment_file_path)

    if section in sections:
        if line_index is not None:
            sections[section][line_index] = formatted_text  # Modify existing line
        else:
            sections[section].append(formatted_text)  # Add new line
    else:
        sections[section] = [formatted_text]  # Add new section and line
    comment = AI.conversation_comment_AI(formatted_text)
    if line_index is not None:
        key = f"{section}_{line_index}"
    else:
        key = section
    comments[key] = comment

    write_dict_to_txt(sections, comments, file_path, comment_file_path)


# Function for integrating to formatted goals
def integrate_to_formatted_goals(exchange, file_path, comment_file_path):
    # Formatting the text using external function
    integration_text = goal_creation_AI_call(exchange)

    # Logic for choosing the section
    section = choose_section(integration_text, file_path, comment_file_path)

    # Logic for choosing the line or adding a new line
    line_index = choose_or_add_line(section, integration_text, file_path,comment_file_path)

    # Integrate the line into the text file
    integrate_line_to_file(section, line_index, integration_text, file_path, comment_file_path)


# Main function to process the list of exchanges or a single exchange
def process_exchanges(exchanges, file_path):
    comment_file_path = file_path.replace("conversation_goals.txt", "conversation_comments.txt")
    if isinstance(exchanges, list):
        for exchange in exchanges:
            if goal_confirmation(exchange):
                integrate_to_formatted_goals(exchange, file_path, comment_file_path)
    elif isinstance(exchanges, dict):
        if goal_confirmation(exchanges):
            integrate_to_formatted_goals(exchanges, file_path, comment_file_path)
    else:
        raise ValueError("Input must be either a list of exchanges or a single exchange.")




if __name__ == "__main__":
    try:
        convo_dir_path = r"C:\Users\philippe\Documents\pdf to txt files\test\stubs"

        with open(os.path.join(convo_dir_path, "stub_conversation.txt"), 'r', encoding='utf-8', errors='ignore') as file:
            formatted_convo = string_to_formatted_list(file.read())

        file_path = r"C:\Users\philippe\Documents\pdf to txt files\test\test_conversation_goals.txt"
        process_exchanges(formatted_convo, file_path)
    except Exception as e:
        print(f"A critical error occurred: {e}")
        traceback.print_exc()


