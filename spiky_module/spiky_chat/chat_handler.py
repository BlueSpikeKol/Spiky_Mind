import queue
import threading
import time
from typing import Union, List

from utils.openai_api.gpt_calling import GPTAgent
from utils.openai_api.models import ModelType
from front_end.chat_interface_old import ChatInterface


class SpikyChatHandler:
    def __init__(self, chat_agent: GPTAgent):
        self.chat_agent = chat_agent
        self.interface = ChatInterface(self.handle_input)
        self.word_limiter = WordLimiter(self.interface)
        self.tool_handler = ToolHandler()
        self.memory_handler = MemoryHandler()

    def open_chat(self):
        self.word_limiter.start()
        self.interface.show()  # Show the PyQt interface

    def close_chat(self):
        self.word_limiter.stop()
        self.interface.close()  # Close the PyQt interface

    def handle_input(self, input_text):
        # Process the input with the chat agent
        self.chat_agent.update_agent(messages = input_text)  # Assuming there's a method to set input
        self.display_model_output()

    def display_model_output(self):
        self.chat_agent.run_agent()
        if self.chat_agent.stream:
            # return self.stream_output() TODO: implement streaming
            pass
        else:
            self.word_limiter.enqueue_words(self.chat_agent.get_text())

    def stream_output(self):
        for output in self.chat_agent.get_stream():
            self.word_limiter.enqueue_words(output)

class WordLimiter:
    def __init__(self, display_interface: ChatInterface):
        self.display_interface = display_interface
        self.word_queue = queue.Queue()
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self.process_words, daemon=True).start()

    def stop(self):
        self.running = False

    # def process_words(self):
    #     while self.running:
    #         if not self.word_queue.empty():
    #             word = self.word_queue.get()
    #             self.display_interface.display_message(word, is_user=False)
    #             time.sleep(0.25)  # Adjust as needed for real-time effect

    def process_words(self):
        while self.running:
            # Check if there are words in the queue
            if not self.word_queue.empty():
                # Accumulate all words in the queue
                words = []
                while not self.word_queue.empty():
                    words.append(self.word_queue.get())

                # Join all words into a single string
                full_message = ' '.join(words)

                # Display the full message using the display interface
                self.display_interface.display_message(full_message, is_user=False)
            else:
                # If the queue is empty, wait a bit before checking again
                time.sleep(0.25)  # Adjust as needed

    def enqueue_words(self, words: Union[str, List[str]]):
        if isinstance(words, str):
            words = words.split()
        for word in words:
            self.word_queue.put(word)



class ToolHandler:
    def __init__(self):
        self.current_tool = None

    def update_tool(self, tool):
        self.current_tool = tool


class MemoryHandler:
    def __init__(self):
        self.memory = None

    def update_memory(self, memory):
        self.memory = memory

    def get_memory(self):
        return self.memory
