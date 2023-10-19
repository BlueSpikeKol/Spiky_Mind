import models


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
                # Your validation code here
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
                # Your validation code here
                return True
            except TypeError as e:
                print(f"Error: {e}")
                return False

        if validate_prompt(prompt):
            self.prompt = prompt


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
                # Your validation code here
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

    def transform_into_messages(self, messages=None):
        """
        Transforms and validates chat messages.

        Parameters:
            messages (list): List of message dictionaries.

        Returns:
            ChatTypeMessages: Validated chat messages.
        """
        return ChatTypeMessages(messages)

    def transform_into_prompt(self, prompt):
        """
        Transforms and validates a prompt.

        Parameters:
            prompt (str or list): The prompt string or list.

        Returns:
            PromptTypeMessages: Validated prompt.
        """
        return PromptTypeMessages(prompt)

    def transform_into_embedding(self, text_to_embed):
        """
        Transforms and validates text to be embedded.

        Parameters:
            text_to_embed (str or list): The text to be embedded.

        Returns:
            AdaTypeEmbedding: Validated text embedding.
        """
        return AdaTypeEmbedding(text_to_embed)
