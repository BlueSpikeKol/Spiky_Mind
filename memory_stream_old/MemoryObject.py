import uuid
from datetime import datetime


class MemoryObject:
    def __init__(self, memory_id=None ,content="", child_list_ID=None, parent_ID=None, access_level=0, level_of_abstraction=0, retrieved_memory=False):

        if not retrieved_memory:
            if memory_id == None:
                self.memory_id = str(uuid.uuid4())
            else:
                self.memory_id = memory_id
            self.content = content
            self.child_ids = child_list_ID
            self.parent_id = parent_ID
            self.access_level = access_level
            self.created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.modified_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.last_visited_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.nb_of_visits = 0
            self.level_of_abstraction=level_of_abstraction

        else:

            self.memory_id = ""
            self.content = None
            self.child_ids = None
            self.parent_id = None
            self.subject = None
            self.access_level = None
            self.created_date = None
            self.modified_date = None
            self.last_visited_date = None
            self.nb_of_visits = None
            self.level_of_abstraction = None
