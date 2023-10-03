
spiky_task_template = """You will receive a request from the user. You must try to fill a task element that has this format:
<task_type = add task type
task_goal = add task goal
task_context = add context
task_max_tokens = add max tokens>
if you cannot fill one of the elements because the user did not specify, write NONE in capital letters instead. here are examples of task types, if the task of the user is outside of these task types, write NONE : web scrapping with specific website, web scrapping with free exploration, web scrapping with specific goal. 
here are examples of goals: 'I want to know what the following page talks about, https://elevenlabs.io/blog/','I want you to get all the information online you can get that might be usefull for my project','I want to know all the usefull information about voice mods for discord'
here are a few examples of context :'I need to know this information to use it in my code', 'this web scrapping task is to test the limit of web scrapping', 'I want to learn everything i can about sports fast, because i need to do a presentation soon'
you are now ready to fill the task element. here is what the user wants.
USER :"""

def check_task_fields(task):
    lines = task.split('\n')
    missing_fields = []

    for line in lines:
        field, value = line.split(' = ')
        if value.strip() == 'NONE':
            missing_fields.append(field.strip('<>'))

    if missing_fields:
        return "The following fields are empty: " + ", ".join(missing_fields) + " please rewrite the missing fields"
    else:
        return "All fields are filled."

class Spiky_Task:
    def __init__(self, task_string):
        lines = task_string.split('\n')
        self.fields = {}

        for line in lines:
            if line.strip():
                field, value = line.split(' = ')
                field_name = field.strip('<>')
                self.fields[field_name] = value.strip()
