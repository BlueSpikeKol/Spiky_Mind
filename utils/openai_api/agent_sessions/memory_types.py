from enum import Enum

class MemoryType(Enum):
    LAST_X_MESSAGES = 1
    ALL_MESSAGES = 2
    MARKED_MESSAGES = 3
    DB_RETRIEVAL = 4
    SIMILARITY_SEARCH = 5