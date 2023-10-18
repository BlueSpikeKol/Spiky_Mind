import os
import traceback
from gpt_api_old import AI_entities as AI
import spacy
from transformers import BertTokenizer, BertModel
import torch

nlp = spacy.load("en_core_web_lg")
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


class ConvoProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.comment_file_path = file_path.replace("conversation_goals.txt", "conversation_comments.txt")
        self.sections, self.comments = self.read_txt_to_dict()

    def read_txt_to_dict(self):
        sections = {}
        with open(self.file_path, 'r') as f:
            lines = f.readlines()

        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith('Section Start:'):
                current_section = line[len('Section Start:'):].strip()
                sections[current_section] = []
            elif line.startswith('Section End:'):
                current_section = None
            elif current_section is not None:
                sections[current_section].append(line)

        comments = {}
        with open(self.comment_file_path, 'r') as f:
            lines = f.readlines()

        current_key = None
        for line in lines:
            line = line.strip()
            if line.startswith('Key:'):
                current_key = line[len('Key:'):].strip()
            elif current_key is not None:
                comments[current_key] = line

        return sections, comments

    def write_dict_to_txt(self):
        with open(self.file_path, 'w') as f:
            for section, bullet_points in self.sections.items():
                f.write(f'Section Start:{section}\n')
                for point in bullet_points:
                    f.write(f'{point}\n')
                f.write(f'Section End:{section}\n')

        with open(self.comment_file_path, 'w') as f:
            for key, comment in self.comments.items():
                f.write(f'Key:{key}\n')
                f.write(f'{comment}\n')

    def goal_creation_AI_call(self, exchange):
        formatted_string = ""
        for key, value in exchange.items():
            formatted_string += f"{key}: {value}\n"
        return AI.goal_creation_AI(formatted_string)

    def goal_confirmation(self, exchange):
        formatted_string = ""
        for key, value in exchange.items():
            formatted_string += f"{key}: {value}\n"
        return AI.goal_approval_AI(formatted_string)

    def get_section_names_from_file(self):
        sections, _ = self.read_txt_to_dict()
        return list(sections.keys())

    def calculate_similarity(self, text1, text2):
        embedding1 = get_bert_embedding(text1)
        embedding2 = get_bert_embedding(text2)
        return torch.cosine_similarity(embedding1, embedding2, dim=-1).item()

    def find_most_similar_section(self, candidate_section, section_names):
        max_similarity = 0
        chosen_section = None
        for section in section_names:
            similarity = self.calculate_similarity(candidate_section, section)
            if similarity > max_similarity:
                max_similarity = similarity
                chosen_section = section
        return chosen_section, max_similarity

    def choose_section(self, formatted_text):
        section_names = self.get_section_names_from_file()
        candidate_section = AI.create_new_section_AI(formatted_text)
        chosen_section, max_similarity = self.find_most_similar_section(candidate_section, section_names)

        if chosen_section:
            approval = AI.similarity_approval_AI(formatted_text, chosen_section)
            if approval:
                return chosen_section
        return candidate_section

    def choose_or_add_line(self,section, formatted_text):
        sections, _ = self.read_txt_to_dict()
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
                    print(f"{section}{formatted_text} will be replacing {line_index}")
                    return line_index  # Replace the existing line

        return None  # Indicates a new line should be added

    def integrate_line_to_file(self, section, line_index, formatted_text):
        if section in self.sections:
            if line_index is not None:
                self.sections[section][line_index] = formatted_text  # Modify existing line
            else:
                self.sections[section].append(formatted_text)  # Add new line
        else:
            self.sections[section] = [formatted_text]  # Add new section and line

        comment = AI.conversation_comment_AI(formatted_text)  # Get comment for the line
        key = f"{section}_{line_index}" if line_index is not None else section
        self.comments[key] = comment  # Update the comment

        self.write_dict_to_txt()  # Write the updates to the text files

        # Refresh the in-memory state to be consistent with the files
        self.sections, self.comments = self.read_txt_to_dict()

    def process_single_exchange(self, exchange):
        if self.goal_confirmation(exchange):
            formatted_text = self.goal_creation_AI_call(exchange)
            section = self.choose_section(formatted_text)
            line_index = self.choose_or_add_line(section, formatted_text)
            self.integrate_line_to_file(section, line_index, formatted_text)

    def process_exchanges(self, exchanges):
        if isinstance(exchanges, list):
            for exchange in exchanges:
                self.process_single_exchange(exchange)
        elif isinstance(exchanges, dict):
            self.process_single_exchange(exchanges)
        else:
            raise ValueError("Input must be either a list of exchanges or a single exchange.")


# Usage
if __name__ == "__main__":
    try:
        file_path = r"C:\Users\philippe\Documents\pdf to txt files\test\test_conversation_goals.txt"
        processor = ConvoProcessor(file_path)
        with open(r"C:\Users\philippe\Documents\pdf to txt files\test\stub_conversation.txt", 'r', encoding='utf-8',
                  errors='ignore') as file:
            formatted_convo = string_to_formatted_list(file.read())
        processor.process_exchanges(formatted_convo)
    except Exception as e:
        print(f"A critical error occurred: {e}")
        traceback.print_exc()