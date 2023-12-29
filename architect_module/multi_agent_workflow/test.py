import role_playing_session
# from architect_module.multi_agent_workflow.conversation_splitter import ConversationSplitter
# from architect_module.function_creation.create_new_function import FunctionCreator
from architect_module.multi_agent_workflow.role_playing_session import ConversationManager
from utils.openai_api.gpt_calling import GPTManager
import textwrap
from utils.openai_api.models import ModelType

# convo_summary = "Environmental Scientist's Viewpoint:\n- Types of energy managed must be understood to determine efficiency of the Energy Redistribution Algorithm (ERA).\n- ERA needs to adapt to the unpredictability of renewable energy sources like solar and wind power.\n- Environmental impact of energy redistribution and required infrastructure should be assessed.\n- The social equity implications of energy distribution must also be accounted for.\n\nCybersecurity Expert's Viewpoint:\n- Potential risk of ERA manipulation by cyber attackers could lead to inaccurate prediction and mismanagement of energy.\n- Recommendations for safeguarding ERA include:\n  - Regular Penetration Testing to identify and fix vulnerabilities.\n  - Usage of strong Encryption to prevent interception of data.\n  - Implementing Multi-factor Authentication for controlling access to ERA.\n  - Regular Security Audits of ERA and its associated infrastructure to ensure compliance with security protocols.\n  - An effective Incident Response Plan in case of a security breach.\n  - Security Awareness Training for all involved personnel to keep them updated about potential threats and mitigation methods."

# convo_splitter = ConversationSplitter(agent_manager=GPTManager(), parent_convo="random name")
# convo_splitter.split_conversation(convo_summary)

project_description = """The Global Renewable Energy Grid: A Manifesto for a Sustainably Powered Future
Introduction
In an era where climate change looms as an existential threat, the Global Renewable Energy Grid (GREG) aims to be a groundbreaking initiative, reimagining the very fabric of how the world consumes energy. Anchored in Geneva, Switzerland, but with a reach that spans continents, GREG envisions a future where energy is abundant, clean, and universally accessible, irrespective of geographic or economic barriers.

Business Model
To achieve this herculean task, GREG relies on a diversified business model involving government partnerships, private investments, and energy trading. The estimated budget stands at $25 billion, which is expected to grow as the project scales. A cadre of 500 engineers from various disciplines, 100 environmental scientists, and 50 cybersecurity experts forms the backbone of this ambitious project.

Funding Structure
Government Partnerships: 40% of the budget
Private Investments: 35% of the budget
Energy Trading Revenues: 25% of the budget, expected to increase over time
Key Features
Smart Grid Technology
The crux of GREG lies in its Smart Grid Technology. Unlike conventional grids that are passive conduits for energy transmission, GREG’s Smart Grid uses AI algorithms and Internet of Things (IoT) devices to dynamically manage energy flow.

Energy Redistribution Algorithm (ERA)
ERA is an AI algorithm that constantly analyzes real-time data from solar, wind, and hydroelectric installations. It identifies energy surpluses and deficits across continents and redistributes energy accordingly.

Real-time Energy Monitoring
GREG will employ a dense network of IoT sensors and SCADA systems to monitor energy production, consumption, and transmission in real-time. This data is relayed to the central command, where AI algorithms make predictive models for demand and possible energy bottlenecks.

Emergency Backup Systems
Redundancy is built into the system in the form of battery storage units, capacitor banks, and emergency fossil fuel generators to ensure uninterrupted supply during unforeseen circumstances like natural disasters.

Security Measures
Given the global nature of GREG, cybersecurity is paramount. The system will employ multi-layered security protocols, including advanced firewalls, intrusion detection systems, and end-to-end encryption to protect against cyber-attacks.

Resources & Location
The project will be coordinated from a state-of-the-art facility in Geneva, Switzerland, which houses the central command and data centers. The project will also have multiple offices worldwide for local operations and monitoring.

Milestones
Feasibility Studies and International Agreements: Year 1-2

Conducting comprehensive environmental and technical studies
Drafting and ratifying international agreements for energy sharing and tariffs
Detailed Project Planning and Resource Allocation: Year 2-3

Finalizing the technology stack
Identifying locations for renewable installations and grid infrastructure
Initial Prototypes and Testing: Year 3-4

Setting up prototype smart grids in select regions
Extensive simulation and real-world testing
Phase-wise Implementation by Continent: Year 4-10

Rolling out the grid infrastructure continent by continent
Synchronization of regional grids with the central command
Real-world Testing and Adjustments: Year 10-12

Ongoing analysis and improvements
Scaling of energy production capabilities
Final Global Synchronization: Year 12-15

Linking all continental grids into a single, seamless global grid
Continuous Monitoring and Upgrades: Year 15 Onwards

Constant data analysis for predictive maintenance
Incremental upgrades to technology and infrastructure
Philosophy & Conclusion
The Global Renewable Energy Grid is not just a project; it’s a movement towards a sustainable future. We aim to democratize energy, making it abundant, clean, and accessible to all. The scale is vast, and the challenges are many, but the potential rewards—both environmental and economic—are incalculable. In breaking down geographic and economic barriers, we also break down social barriers, uniting humanity in the pursuit of a common goal: a sustainably powered world.

Decentralized Energy Nodes (DENs)
In addition to centralized hubs, GREG will employ decentralized energy nodes using blockchain technology to facilitate peer-to-peer energy trading at the local level. These DENs empower consumers to become prosumers, enabling them to sell excess energy back to the grid or directly to neighbors. By reducing the distance energy has to travel, we also minimize transmission losses and increase efficiency.

Adaptive Energy Storage System (AESS)
Traditional energy storage solutions like batteries have limitations in terms of capacity and lifespan. The Adaptive Energy Storage System will use advanced flow batteries and flywheel storage mechanisms to adapt to the variable nature of renewable energy production. These systems can be scaled up or down depending on demand and are more environmentally friendly than traditional lithium-ion batteries.

Autonomous Repair Drones
To ensure the integrity and reliability of the grid, GREG will deploy fleets of drones equipped with advanced diagnostic tools and repair capabilities. These drones will be dispatched regularly to inspect and maintain the energy installations and transmission lines. In the event of an emergency or malfunction, the drones can execute minor repairs autonomously or provide real-time data to human operators for more complex issues.

Multi-Modal Renewable Energy Installations (MMREIs)
Rather than standalone wind, solar, or hydro installations, GREG aims to develop Multi-Modal Renewable Energy Installations. These MMREIs will combine multiple forms of renewable energy production into a single location. For instance, a solar farm could have wind turbines integrated into its structure and a small-scale hydroelectric dam nearby. This ensures that energy production continues even if one source is not optimal due to weather conditions.

Global Energy Highway (GEH)
The most audacious and futuristic feature is the Global Energy Highway—a network of superconductive transmission lines that connect the continents via undersea cables and ground installations. The GEH would use cryogenic coolers to keep the superconducting material at temperatures where resistance is negligible. At this scale, the logistical, environmental, and geopolitical challenges are immense, but the benefits are equally staggering: near-lossless energy transmission across thousands of miles.

This "highway" would be the pinnacle of GREG's ambition to break down geographical barriers, capable of transferring colossal amounts of energy from regions of surplus to those in deficit. If the Sahara Desert is abundant in solar energy, GEH could transmit it to power-hungry cities in Europe or Asia, balancing the global energy equation.

Conclusion
With these additional features, the Global Renewable Energy Grid doesn't just aim to redefine energy consumption; it sets out to revolutionize the way humanity thinks about and interacts with energy as a whole. From empowering local communities with decentralized nodes to establishing a near-lossless global energy superhighway, GREG is not just a technological marvel but a beacon for a sustainable, unified future."""

# conversation_manager = role_playing_session.ConversationManager(project_description)

# main_convo_session = conversation_manager.create_session('side',main_convo_name="\"Powering the Future: GREG's Mission Debate\"")

# main_convo_session.start_role_playing_session()

task_old = """Objective:
The main goal of the function, named user_data_operations, is to perform a series of operations involving fetching user data from a simulated database and performing arithmetic calculations on numeric inputs. It utilizes existing utility functions for these tasks.

Input:

start_id (int): The starting user ID for fetching user names from the simulated database. No specific constraints.
end_id (int): The ending user ID for fetching user names from the simulated database. It should be greater than or equal to start_id.
num1 (int or float): A numeric value to be used in arithmetic operations. No specific constraints.
num2 (int or float): Another numeric value to be used in arithmetic operations. No specific constraints.
Output:

The function should return a dictionary (result_dict) containing:

'user_data': A dictionary of user IDs and names. (dict type)
'sum': The sum of num1 and num2. (Type will match the input numeric types)
'difference': The difference between num1 and num2. (Type will match the input numeric types)
'product': The product of num1 and num2. (Type will match the input numeric types)
Constraints:

The function must use the existing utility functions (fetch_user_names_from_db_to_dict, add, subtract, multiply) for performing its tasks.
end_id should be greater than or equal to start_id.
Existing Functions to Utilize:

fetch_user_names_from_db_to_dict(start_id: int, end_id: int) -> dict: To fetch user data.
add(a, b) -> int or float: To calculate the sum of two numbers.
subtract(a, b) -> int or float: To calculate the difference between two numbers.
multiply(a, b) -> int or float: To calculate the product of two numbers."""
task = """We need to create a process that allows our application to take control of a python project given by the 
user and be able to read and modify it. This process must have zero UI and only be done from the source code, 
where the entry needs to have the file_path of the python project. We must discuss the best way to extract it, 
knowing the fact that it will be read by machine and humans alike. As for modifications, as long as we have a 
function that takes the code to implement as well as its location, and the code to remove, it should do the trick, 
maybe as a dict or list of dicts, you decide. Keep in mind that the code that will be implemented is already deemed 
safe and code injection cannot be malicious, the only additional, its important that there is nothing else than this! 
form of code verification should be to remove code where the user is asked if they really want to remove code. It 
must be easy to navigate the extracted python project even without any UI. Remember that kwargs** are useful, 
but they are hard to navigate since its not descriptive."""

system_prompt = """Below is complex programming task that a debate president (that is not you) will have to resolve 
with the help of debaters, who specialize in programming. Please make the task more specific and easy to understand. 
each point needs to have enough context that the debate president can know the context. Be creative, imaginative and 
cover blind spots the original task description might have forgotten. Do not add anything else and do not answer any 
of the problems given. You are not part of the debate team, so do not use 'we' or 'our'. Do not doubt the original 
task. Submit your answer in small paragraph(75 words) followed by a listed bullet-point format of features(75 words 
per feature). If possible in a step by step format(1. 2. ,etc) where each step depends on the previous step for success and put 
the least important features of the task in last if it doesnt contradict the previous rule. Never talk about more 
than 5 features at a time, but never cut content, regroup multiple features under a single name if necessary, 
and make it explicit. Every time a feature interacts with another feature (feature one will create the input of 
feature 2 and 3 for example), it must be written down along with the feature to avoid cluttering the first main 
paragraph.
example:
<75 word general goal>
1.<feature1>:<up to 75 words to explain feature 1>
2.<feature2>:<up to 75 words to explain feature 2>
etc
<How Features Interact with each other>"""
#agent_manager = GPTManager()
#agent = agent_manager.create_agent(model=ModelType.CHAT_GPT4, system_prompt=system_prompt,
#                                   messages=f"here is the original task description: {task}", max_tokens=600, temperature=0.4)
#agent.run_agent()
#new_task2 = agent.get_text()
#print(new_task2)
new_task1 = """The task essentially involves establishing a process to control a designated Python project via an application. The system should be able to read, navigate, and modify the codebase with no user interface but only with instructions supplied via the source code. The entry point for this system would be the filepath of the Python project. The process needs to satisfy constraints of machine and human readability and safety against malicious code injections, with the help of a verification prompt for code deletion.
1.**File Access and Readability Feature**: Design a method that takes the filepath of the Python project as an input and allows the application to take control of the project. This method must be able to read the source code. It is useful to require a layout of the project's working structure (files, modules, and classes) for efficient navigation.
2.**Code Modification Feature**: Develop a function that receives a code block, the position for its implementation in the form of a dictionary (or list of dictionaries), and a separate code block for deletion. The feature should be capable of turning on/off code prompts for deletion.
3.**Code Navigability Feature**: The process should allow for easy navigation of the Python project. Implement a method to facilitate this, like generating a summary output of the project structure.
4.**Code Safety Verification Feature**: Even when the code to be implemented is known to be safe, there must be a safety feature that warns users before any code deletion. This feature would reconfirm if the user wishes to proceed with the deletion.
5.**Simplified Complex Structures Feature**: Handle complex python structures like kwargs** to be descriptive enough to aid navigability. Implement a feature that simplifies or organizes such unstructured data in a more human-readable format.
**Interdependencies and Interactions amongst these features**:
The _File Access and Readability Feature_ provides the base for other features, it indeed control the Python project and reads its structure for _Code Modification_ and _Code Navigability Features_. _Code Safety Verification Feature_ relies on the _Code Modification Feature_, to verify that the modifications do not delete any code unintentionally. The _Simplified Complex Structures Feature_ improves the _Code Navigability Feature_ by structuring unstructured python components.
"""
conversation_manager = role_playing_session.ConversationManager(new_task1)
coding_session = conversation_manager.create_session(session_type='main')

coding_session.start_role_playing_session(num_rounds=12)
