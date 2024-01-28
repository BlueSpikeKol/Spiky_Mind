import utils.openai_api.models as models


class ChatTypeMessages:
    """
    Class to handle and validate chat messages.
    """

    def __init__(self, messages):
        """
        Initializes the ChatTypeMessages object and validates the messages.

        Parameters:
            messages (list): List of message dictionaries.
        """

        def validate_messages(messages):
            """
            Validates the structure and content of messages.

            Parameters:
                messages (list): List of message dictionaries.

            Returns:
                bool: True if messages are valid, False otherwise.
            """
            try:
                if not isinstance(messages, list):
                    raise TypeError("messages must be a list.")

                for message in messages:
                    if not isinstance(message, dict):
                        raise TypeError("Each message must be a dictionary.")

                    required_keys = ["role", "content"]
                    for key in required_keys:
                        if key not in message:
                            raise KeyError(f"Message is missing required key: {key}")

                    if message["role"] not in ["system", "user", "assistant"]:
                        raise ValueError("Invalid role in message.")

                    if not isinstance(message["content"], str):
                        raise TypeError("Content must be a string.")

                return True
            except (TypeError, KeyError, ValueError) as e:
                print(f"Error: {e}")
                return False

        if validate_messages(messages):
            self.messages = messages


class PromptTypeMessages:
    """
    Class to handle and validate prompt messages.
    """

    def __init__(self, prompt):
        """
        Initializes the PromptTypeMessages object and validates the prompt.

        Parameters:
            prompt (str or list): The prompt string or list.
        """

        def validate_prompt(prompt):
            """
            Validates the structure and content of the prompt.

            Parameters:
                prompt (str or list): The prompt string or list.

            Returns:
                bool: True if the prompt is valid, False otherwise.
            """
            try:
                if not isinstance(prompt, (str, list)):
                    raise TypeError("Prompt must be a string or a list.")

                return True
            except TypeError as e:
                print(f"Error: {e}")
                return False

        if validate_prompt(prompt):
            self.prompt_str = prompt


class AdaTypeEmbedding:
    """
    Class to handle and validate text embeddings.
    """

    def __init__(self, text_to_embed):
        """
        Initializes the AdaTypeEmbedding object and validates the text to embed.

        Parameters:
            text_to_embed (str or list): The text to be embedded.
        """

        def validate_embedding_input(input_text):
            """
            Validates the structure and content of the text to be embedded.

            Parameters:
                input_text (str or list): The text to be embedded.

            Returns:
                bool: True if the text is valid, False otherwise.
            """
            try:
                if not isinstance(input_text, (str, list)):
                    raise TypeError("Input text must be a string or a list.")

                return True
            except (TypeError, ValueError) as e:
                print(f"Error: {e}")
                return False

        if validate_embedding_input(text_to_embed):
            self.embedding_str = text_to_embed
            self.model = "text-embedding-ada-002"


class TemplateManager:
    """
    Manages the transformation of various types of inputs into their respective validated forms.
    """
    @staticmethod
    def transform_into_messages(messages=None):
        """
        Transforms and validates chat messages.

        Parameters:
            messages (list): List of message dictionaries.

        Returns:
            ChatTypeMessages: Validated chat messages.
        """
        return ChatTypeMessages(messages)

    @staticmethod
    def transform_into_prompt(prompt):
        """
        Transforms and validates a prompt.

        Parameters:
            prompt (str or list): The prompt string or list.

        Returns:
            PromptTypeMessages: Validated prompt.
        """
        return PromptTypeMessages(prompt)

    @staticmethod
    def transform_into_embedding(text_to_embed):
        """
        Transforms and validates text to be embedded.

        Parameters:
            text_to_embed (str or list): The text to be embedded.

        Returns:
            AdaTypeEmbedding: Validated text embedding.
        """
        return AdaTypeEmbedding(text_to_embed)
