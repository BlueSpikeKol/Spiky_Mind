from enum import Enum

class ConversationType(Enum):
    USER_ANSWERS = 1
    BOT_ANSWERS = 2
    FREESTYLE = 3


class ConversationEndType(Enum):
    INFORMATION_GATHERED = 1
    X_MESSAGES_EXCHANGED = 2
    USER_ENDED = 3
    BOT_ENDED = 4
    TIMEOUT = 5

