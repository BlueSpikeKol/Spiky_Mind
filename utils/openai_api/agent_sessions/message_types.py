from dataclasses import dataclass


@dataclass
class Message:
    content: str
    role: str
    is_marked: bool = False


class SystemMessage(Message):
    def __init__(self, content: str):
        super().__init__(content, 'system')


class UserMessage(Message):
    def __init__(self, content: str):
        super().__init__(content, 'user')


class AIMessage(Message):
    def __init__(self, content: str):
        super().__init__(content, 'assistant')


class DebaterMessage(Message):
    def __init__(self, content: str):
        super().__init__(content, 'debater')


class PresidentMessage(Message):
    def __init__(self, content: str):
        super().__init__(content, 'president')
