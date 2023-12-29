import subprocess

import json
import re
from collections import Counter

from front_end.tree_visualisation import DataVisualizer
from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType
from utils import persistance_access


class ProjectSchedule:
    AGENT_SCHEDULE_FILE_PATH = r"C:\Users\philippe\PycharmProjects\Spiky_Mind\architect_module\orchestrator\project_planning_files\agent_made_schedule.json"

    def __init__(self):
        self.data_visualizer = None
        self.gpt_manager = GPTManager()
        self.memory_access = persistance_access.MemoryStreamAccess()
        self.mindmap = None
        self.project_schedule = None
        self.domain_file_text = None
        self.problem_file_text = None
        self.initialize_schedule()

    def visualize_schedule(self):
        if self.mindmap is None:
            self.mindmap = self.read_mindmap(self.AGENT_SCHEDULE_FILE_PATH)
        visualizer = DataVisualizer(self.mindmap)
        visualizer.visualize_data()

    def initialize_schedule(self):
        # message = self.explore_goal_convo()
        # self.save_final_convo(message)
        # self.expand_schedule()
        #self.save_to_pinecone()
        #self.regroup_nodes_pinecone()
        # self.create_fastdownward_solution()
        pass

    def save_to_pinecone(self):
        if self.mindmap is None:
            self.mindmap = self.read_mindmap(self.AGENT_SCHEDULE_FILE_PATH)
        """
        Traverses the mindmap and saves each node into the Pinecone database.

        The mindmap is expected to be a nested dictionary with each node containing a name (key),
        and a dictionary (value) which may have 'children' and 'metadata'. An example input:

        {
            "Node1": {
                "children": {
                    "Child1": {
                        "children": {},
                        "metadata": "Description of Child1"
                    },
                    "Child2": {
                        "children": {},
                        "metadata": "Description of Child2"
                    }
                },
                "metadata": "Description of Node1"
            },
            "Node2": {
                "children": {},
                "metadata": ""
            }
        }
        """

        def traverse_and_save(node, path=None):
            """
            Recursively traverse the mindmap tree and save each node to Pinecone.

            Parameters:
                node (dict): Current node in the mindmap.
                path (list): List of ancestor names leading to the current node.
            """
            if path is None:
                path = []
            for node_name, node_data in node.items():
                current_path = path + [node_name]
                vector_name = ">".join(current_path)  # Creating a unique identifier for the node
                vector_text = node_name  # Assuming vector_text is the node name

                if 'metadata' in node_data and node_data['metadata']:
                    vector_text += "-" + node_data['metadata']  # Adding metadata to the vector text

                self.memory_access.add_to_pinecone(vector_name, vector_text)

                if 'children' in node_data and node_data['children']:
                    traverse_and_save(node_data['children'], current_path)

        # Assuming mindmap is stored in self.mindmap
        traverse_and_save(self.mindmap)



    def regroup_nodes_pinecone(self):
        if self.mindmap is None:
            self.mindmap = self.read_mindmap(self.AGENT_SCHEDULE_FILE_PATH)
        #whitelist = self.get_all_nodes_IDs()
        #k_groups = self.memory_access.group_vectors(whitelist=whitelist, k=5)
        #groups_counts = self.extract_and_count(k_groups)
        self.data_visualizer = DataVisualizer(self.mindmap)
        self.data_visualizer.visualize_data(use_list=False)
        #print(groups_counts)
    @staticmethod
    def extract_and_count(words_list, base_term='Engineering_a_DC_Motor'):
        unimportant_words = {'a', 'the', 'my', 'is', 'and', 'in', 'to', 'of'}

        def clean_and_extract(words):
            words = words.replace(base_term + '>', '').split('>')
            return [word for word in words if word.lower() not in unimportant_words]

        top_counts_per_group = []
        for group in words_list:
            all_words = []
            for phrase in group:
                all_words.extend(clean_and_extract(phrase))

            # Get the top 25 most common words in this group
            top_counts = Counter(all_words).most_common(5)
            top_counts_per_group.append(dict(top_counts))

        return top_counts_per_group

    def get_all_nodes_IDs(self):
        """
        Traverse the mindmap tree, retrieve all the node names, and then fetch their corresponding IDs from MySQL.

        Returns:
            A list of all node IDs in the mindmap.
        """
        if self.mindmap is None:
            self.mindmap = self.read_mindmap(self.AGENT_SCHEDULE_FILE_PATH)

        def traverse(node, path=None):
            """
            Recursively traverse the mindmap tree and collect node names.

            Parameters:
                node (dict): Current node in the mindmap.
                path (list): List of ancestor names leading to the current node.

            Returns:
                A list of all traversed node names.
            """
            if path is None:
                path = []
            node_names = []
            for node_name, node_data in node.items():
                current_path = path + [node_name]
                vector_name = ">".join(current_path)  # Unique identifier for the node
                node_names.append(vector_name)

                if 'children' in node_data and node_data['children']:
                    node_names.extend(traverse(node_data['children'], current_path))

            return node_names

        node_names = traverse(self.mindmap)

        node_ids = []
        for name in node_names:
            node_id = self.memory_access.get_id_by_column(value=name.replace(" ", "_"))
            if node_id:
                node_ids.append(node_id)

        return node_ids

    def explore_goal_convo(self, max_iterations=10):
        """
        Iteratively explores and updates a conversation about creating a mermaid diagram for engineering a DC motor.
        :param max_iterations: Maximum number of iterations for the conversation.
        :return: The final goal string (the last message).
        """
        system_prompt = """
- Mindmap Hierarchy: Use indentation to define hierarchy levels.
- No Arrows: Connections are made through indents, not arrows.
- Bracket Usage: Avoid using different bracket types in text, except for defining node shapes. Replace unwanted brackets with |.
- Root Node:
  - Only one root allowed.
  - Use a descriptive title.
  - Syntax: root((title)), e.g., root((Main Topic))
- Markdown Strings:
  - Text automatically wraps; use newline characters for line breaks.
- Example:
  ```mermaid
  mindmap
    root((mindmap))
      Origins
        Long history
        Popularisation
          Author Tony Buzan
      Research
        Effectiveness
        Automatic creation
          Uses
            Creative techniques
            Strategic planning
            Argument mapping
      Tools
        Pen and paper
        Mermaid
  ```
"""
        # Initialize the message
        message = "Make me a mermaid diagram that shows the process of engineering a dc motor. Organize it to show the " \
                  "named compound tasks that can split into other subaltern tasks to accomplish the goal a bit like " \
                  "in HDDL (HTN) format."
        recursive_content = """Do you think that this organization map above lacks any steps to reach the end goal of 
        building a dc motor? If so, add new parts to the diagram after identifying 
        what could be improved parts from the original map. In the diagram, always surround new elements with ** no 
        matter their emplacement. Remove ** from the original before proceeding. Be sure to not forget to write any 
        old parts of the original mindmap. dont forget to add small description of the changes and why you think 
        those changes are important."""
        all_messages = []

        initial_diagram_creation_agent = self.gpt_manager.create_agent(system_prompt=system_prompt,
                                                                       model=ModelType.CHAT_GPT4,
                                                                       temperature=0.4, max_tokens=700,
                                                                       messages="empty")

        for count in range(1, max_iterations + 1):
            # Check if 'message' is None
            if message is None:
                print("error_messages")
                # Attempt to use the last valid message if available
                if all_messages:
                    message = all_messages[-1]
                else:
                    break

            # Update the agent with the current message
            if count == 1:
                initial_diagram_creation_agent.update_agent(messages=message)
            else:
                # Check if 'recursive_content' is None
                if recursive_content is None:
                    print("error_recursive_content")
                    break
                initial_diagram_creation_agent.update_agent(messages=message + recursive_content)

            # Run the agent
            initial_diagram_creation_agent.run_agent()
            new_message = initial_diagram_creation_agent.get_text()

            # Extract the mermaid diagram from the message
            pattern = r"```.*?```"
            match = re.search(pattern, new_message, re.DOTALL)

            if match:
                message = match.group(0)
                all_messages.append(message)  # Store the valid message
            else:
                message = None
                print(new_message)

            print("NEW ENTRY:\n" + new_message)

        # Return the last valid message from the list
        return all_messages[-1] if all_messages else None

    def save_final_convo(self, mindmap_text):
        mindmap_dict = self.parse_mindmap(mindmap_text)

        # Save to the original location
        with open(self.AGENT_SCHEDULE_FILE_PATH, 'w') as file:
            json.dump(mindmap_dict, file, indent=4)
        print(f"Mindmap saved at {self.AGENT_SCHEDULE_FILE_PATH}")

        # Save to the new location
        new_file_path = r'C:\Users\philippe\PycharmProjects\Spiky_Mind_Electron\data.json'
        with open(new_file_path, 'w') as file:
            json.dump(mindmap_dict, file, indent=4)
        print(f"Mindmap also saved at {new_file_path}")

    def parse_mindmap(self, text):
        lines = text.split('\n')
        root = {}
        stack = [(root, -1)]  # Stack to keep track of (node, depth)

        for line in lines:
            if not line.strip() or line.strip() in ['```mermaid', 'mindmap']:
                continue

            depth = line.count('  ')  # Count leading spaces (2 spaces per indent)
            node_name = line.strip()

            # Special handling for the root node
            if node_name.startswith('root(('):
                node_name = node_name[6:-2]  # Extract the root node name

            # Pop from stack until the current node's parent is found
            while stack and stack[-1][1] >= depth:
                stack.pop()

            # Create new node
            new_node = {node_name: {"children": {}, "metadata": None}}

            # Add new node to its parent
            stack[-1][0].update(new_node)

            # Push new node onto stack
            stack.append((new_node[node_name]["children"], depth))

        return root

    def expand_schedule(self):
        self.mindmap = self.read_mindmap(self.AGENT_SCHEDULE_FILE_PATH)
        self.mindmap = self.recursive_expansion(self.mindmap)
        self.write_mindmap(self.AGENT_SCHEDULE_FILE_PATH, self.mindmap)

    def read_mindmap(self, file_path):
        """Reads and parses the mindmap from a JSON file."""
        try:
            with open(file_path, 'r') as file:
                mindmap = json.load(file)
        except IOError as e:
            print(f"Error reading file: {e}")
            return {}
        return mindmap

    def recursive_expansion(self, mindmap, depth=2):
        """Recursively expands each leaf node in the mindmap."""
        if depth == 0:
            return mindmap

        leaf_nodes = self.find_leaf_nodes(mindmap)
        for leaf in leaf_nodes:
            new_branch = self.knowledge_expansion(leaf)
            mindmap = self.update_mindmap(mindmap, leaf, new_branch)

        return self.recursive_expansion(mindmap, depth - 1)

    @staticmethod
    def get_branch(mindmap, path):
        """Retrieves a specific branch from the mindmap."""
        if len(path) < 2:
            return {}  # Return an empty dict if the path is too short

        branch = mindmap
        for node in path[:-2]:  # Navigate to the parent of the leaf node
            branch = branch.get(node, {})

        parent_node = path[-2]
        return branch.get(parent_node, {})

    @staticmethod
    def update_mindmap(mindmap, path, new_branch):
        """Updates the mindmap by adding a new branch under a specified node."""
        parent = mindmap
        for node in path[:-1]:
            if node in parent:
                # Navigate to the 'children' of the current node
                parent = parent[node]['children']
            else:
                raise KeyError(f"Node '{node}' not found in the current branch of the mindmap.")

        # Add the new branch to the last node in the path
        leaf_node = path[-1]
        if leaf_node in parent:
            # Here, we add the new branch as a child of the leaf node, rather than replacing it
            parent[leaf_node]['children'].update(new_branch)
        else:
            raise KeyError(f"Leaf node '{leaf_node}' not found in the parent branch of the mindmap.")

        return mindmap

    def find_leaf_nodes(self, node, path=None, leaves=None):
        if leaves is None:
            leaves = []
        if path is None:
            path = []

        for child_name, child_node in node.items():
            try:
                new_path = path + [child_name]
                if "children" not in child_node:
                    raise KeyError(f"'children' key not found in node: {child_name}")

                if not child_node["children"]:
                    leaves.append(new_path)
                else:
                    self.find_leaf_nodes(child_node["children"], new_path, leaves)
            except KeyError as e:
                print(f"KeyError encountered: {e}")
            except Exception as e:
                print(f"Unexpected error encountered while processing node '{child_name}': {e}")

        return leaves

    def write_mindmap(self, file_path, mindmap):
        """Writes the updated mindmap back to a JSON file."""
        try:
            with open(file_path, 'w') as file:
                json.dump(mindmap, file, indent=4)
        except IOError as e:
            print(f"Error writing file: {e}")

    def _write_node(self, file, node, depth):
        """Helper method for writing a node to the file."""
        for name, children in node.items():
            file.write('  ' * depth + name + '\n')
            self._write_node(file, children, depth + 1)

    def knowledge_expansion(self, leaf):
        goal = "to engineer a dc motor for the goal of mass production"
        context = ""
        leaf_node = leaf[-1]  # The actual leaf node is the last element in the leaf path

        # Traverse the mindmap to build the context
        current_branch = self.mindmap
        for i, node in enumerate(leaf):
            if node in current_branch:
                # Update the current branch to the children of the current node
                current_branch = current_branch[node]["children"]

                if i == len(leaf) - 2:
                    # Add the parent node and its children (siblings of the leaf)
                    context += f"{'-' * i} {node}\n"
                    for sibling in current_branch:
                        indent = '-' * (i + 1)
                        if sibling == leaf_node:
                            # Mark the leaf node distinctly
                            context += f"{indent} {sibling}(This is the task to divide)\n"
                        else:
                            context += f"{indent} {sibling}\n"
                # Exclude higher-level context above the parent node
            else:
                raise KeyError(f"Node '{node}' not found in the current branch of the mindmap.")

        knowledge_system_prompt = f"You are a task planner and your goal is to divide this task <{leaf[-1]}> into " \
                                  f"subordinate tasks. Never create multiple steps as a single step and the name of " \
                                  f"each step should be no more than 4 words. The overall goal is {goal}. Here are " \
                                  f"the surrounding tasks and " \
                                  f"your position within them: \n{context}"
        message = "Please be creative but concise in the creation of new steps in this large task. Please make a " \
                  "incremented list (max 7) of the subordinate tasks and provide a small explanation for each of them (two " \
                  "sentence. eg: <new_step>:<explanation>)."
        knowledge_creation_agent = self.gpt_manager.create_agent(system_prompt=knowledge_system_prompt,
                                                                 model=ModelType.GPT_3_5_TURBO, messages=message,
                                                                 max_tokens=700, temperature=0.5)
        knowledge_creation_agent.run_agent()
        new_step_text = knowledge_creation_agent.get_text()
        return self.parse_new_steps(new_step_text)

    @staticmethod
    def parse_new_steps(text):
        # Regular expression to match the pattern "number. "
        steps = re.split(r'\d+\.\s', text)
        new_branch = {}

        # The first split is usually an empty string, so we skip it
        for step in steps[1:]:
            # Check if the step contains the expected ':' separator
            if ': ' in step:
                # Splitting each step into a title and its explanation
                title, explanation = step.split(': ', 1)
            else:
                # Fallback values if the expected format is not found
                title = "Unnamed Step"
                explanation = "No detailed explanation provided."

            # The title becomes the key, and the explanation is stored in metadata
            new_branch[title.strip()] = {"children": {}, "metadata": explanation.strip()}

        return new_branch

    def create_problem_and_domain_text(self):  # currently unused
        try:
            with open(self.AGENT_SCHEDULE_FILE_PATH, 'r') as file:
                problem_description = file.read()

            pddl_generation_system_prompt = "Can you try to make a working domain and problem file in PDDL from the information you have right now?"
            pddl_generator_agent = self.gpt_manager.create_agent(system_prompt=pddl_generation_system_prompt,
                                                                 messages=problem_description,
                                                                 model=ModelType.CHAT_GPT4,
                                                                 max_tokens=1000, temperature=0.3)
            pddl_generator_agent.run_agent()
            agent_output = pddl_generator_agent.get_text()
            self.parse_pddl_output(agent_output)
        except FileNotFoundError:
            print(f"File not found: {self.AGENT_SCHEDULE_FILE_PATH}")

    def parse_pddl_output(self, agent_output):  # currently unused
        # Regular expression to find all texts enclosed within ```
        pattern = r"```(.*?)```"
        matches = re.findall(pattern, agent_output, re.DOTALL)

        for text in matches:
            cleaned_text = text.strip()

            # Check for domain file characteristics
            if "(:domain" in cleaned_text:
                self.domain_file_text = cleaned_text
            # Check for problem file characteristics
            elif "(:problem" in cleaned_text:
                self.problem_file_text = cleaned_text

    def update_pddl_files(self):  # currently unused
        # Define file paths
        domain_file_path = "C:\\Users\\philippe\\PycharmProjects\\Spiky_Mind\\architect_module\\orchestrator\\project_planning_files\\project_domain_file.pddl"
        problem_file_path = "C:\\Users\\philippe\\PycharmProjects\\Spiky_Mind\\architect_module\\orchestrator\\project_planning_files\\project_problem_file.pddl"

        # Save domain file
        if self.domain_file_text is not None:
            with open(domain_file_path, 'w') as file:
                file.write(self.domain_file_text)
            print(f"Domain file saved at {domain_file_path}")

        # Save problem file
        if self.problem_file_text is not None:
            with open(problem_file_path, 'w') as file:
                file.write(self.problem_file_text)
            print(f"Problem file saved at {problem_file_path}")

    def create_fastdownward_solution(self):
        docker_command = (
            "docker run -v C:\\Users\\philippe\\PycharmProjects\\Spiky_Mind\\architect_module\\orchestrator\\project_planning_files:/mnt/files "
            "aibasel/downward --alias seq-sat-lama-2011 /mnt/files/project_domain_file.pddl /mnt/files/project_problem_file.pddl"
        )

        result = subprocess.run(docker_command, shell=True, text=True, capture_output=True)
        solution_file_path = "C:\\Users\\philippe\\PycharmProjects\\Spiky_Mind\\architect_module\\orchestrator\\project_planning_files\\domain_full_solution_process.txt"
        with open(
                solution_file_path,
                "w") as file:
            file.write(result.stdout)

        if result.stderr:
            print("Error:", result.stderr)
        else:
            print('Done')
        solution_steps = self.parse_fast_downward_solution(solution_file_path)

    def parse_fast_downward_solution(self, file_path) -> list:
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()

            solution_found = False
            actions_list = []

            for line in lines:
                if "Solution found!" in line:
                    solution_found = True
                    continue

                if solution_found:
                    # Check if the line represents an action
                    if line.strip() and not line.startswith("[t="):
                        actions_list.append(line.strip())
                    else:
                        # End of action list
                        break

            # Process each action as needed
            for action in actions_list:
                print("Action:", action)
            return actions_list

        except FileNotFoundError:
            print(f"File not found: {file_path}")


class TemporarySchedule:
    def __init__(self):
        pass


if __name__ == "__main__":
    my_schedule = ProjectSchedule()
