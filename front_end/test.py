# from architect_module.orchestrator.project_schedule import ProjectSchedule
#
# schedule = ProjectSchedule()
# schedule.visualize_schedule()

import sys
from PyQt6.QtWidgets import QApplication
from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType
from spiky_module.spiky_chat.chat_handler import SpikyChatHandler

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gpt_manager = GPTManager()
    gpt_agent = gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, stream=False, messages="test", max_tokens=1000)
    gpt_agent.update_agent(add_to_previous_chat_messages=True, messages="test2")

    # Initialize SpikyChatHandler with the GPTAgent
    chat_handler = SpikyChatHandler(gpt_agent)
    chat_handler.open_chat()

    sys.exit(app.exec())
