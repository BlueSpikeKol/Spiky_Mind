from architect_module.multi_agent_workflow.role_playing_session import RoundManager

convo_manager = RoundManager("",'','','',
                                      '','')

# List of conversation names to be removed
names_to_remove = [
    "Python_Project_Control_and_Navigation",
    "Controlling_Python_Project_via_Application",
    "Python_Project_Control_and_Readability",
    "Controlled_Python_Project_via_Application",
    "Controlling_Python_Projects_with_App"
]

# Removing each name from the conversation rounds
for name in names_to_remove:
    convo_manager.remove_content(name_to_remove=name)