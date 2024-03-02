from pathlib import Path

import json
import re
from collections import Counter

from front_end.tree_visualisation import DataVisualizer
from utils.openai_api.gpt_calling import GPTManager, GPTAgent
from utils.openai_api.models import ModelType
from utils.openai_api.agent_sessions.convo_types import ConversationType, ConversationEndType
from utils.openai_api.agent_sessions.memory_types import MemoryType
from project_memory import persistance_access


class ProjectSchedule:
    current_script_path = Path(__file__).resolve()
    parent_folder = current_script_path.parent
    AGENT_SCHEDULE_FILE_PATH = parent_folder.joinpath('project_planning_files\agent_made_schedule.json')

    def __init__(self):
        self.data_visualizer = None
        self.gpt_manager = GPTManager()
        self.memory_access = persistance_access.MemoryStreamAccess()
        self.mindmap = None
        self.domain_file_text = None
        self.problem_file_text = None

    def visualize_schedule(self):
        if self.mindmap is None:
            self.mindmap = self.read_mindmap(self.AGENT_SCHEDULE_FILE_PATH)
        self.visualizer = DataVisualizer(self.mindmap)
        self.visualizer.visualize_data()

    def initialize_schedule(self):
        message = self.explore_goal_convo()
        self.save_final_convo(message)
        # self.expand_schedule()
        self.save_to_pinecone()
        self.save_to_neo4j()

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

    def save_to_neo4j(self):
        pass

    def regroup_nodes_pinecone(self):
        # if self.mindmap is None:
        #     self.mindmap = self.read_mindmap(self.AGENT_SCHEDULE_FILE_PATH)
        # whitelist = self.get_all_nodes_IDs()
        # k_groups = self.memory_access.group_vectors(whitelist=whitelist, k=5)
        # groups_counts = self.extract_and_count(k_groups)
        # self.data_visualizer = DataVisualizer(self.mindmap)
        # self.data_visualizer.visualize_data()
        # print(groups_counts)
        pass

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

    def create_mindmap_node_dict(self, name_id, labels, metadata=None):
        """
        Creates a dictionary for a node with the given details.

        Args:
        - name_id (str): The unique identifier of the node.
        - labels (list): A list of labels associated with the node.
        - metadata (dict, optional): Additional metadata for the node.

        Returns:
        - dict: A dictionary representing the node.
        """
        return {
            "children": {},
            "name_id": name_id,
            "label": '; '.join(labels),  # Concatenate labels with semicolon
            "metadata": metadata
        }

    def build_mindmap_from_user_knowledge(self):
        # Assuming 'query' is defined and executed elsewhere to fetch the required data
        query = """
        MATCH (p:Project)-[:HAS_OBJECTIVE]->(o:Objective)
        OPTIONAL MATCH (o)-[:HAS_SUBOBJECTIVE]->(sub:Objective)
        WITH p, o, collect(sub) AS subs
        RETURN p.name AS projectName, p.name_id AS projectID, labels(p) AS projectLabels, 
               collect({objectiveName: o.name, objectiveID: o.name_id, objectiveLabels: labels(o), subObjectives: subs}) AS objectives
        """
        result = self.memory_access.neo4j_handler.execute_queries(query)

        # Initialize the mindmap dictionary
        mindmap_dict = {}

        # Assuming 'result' provides a single project's structure
        project_name = result['projectName']

        # Initialize the project entry in the mindmap
        mindmap_dict[project_name] = self.create_mindmap_node_dict(result['projectID'], result['projectLabels'])

        # Process objectives and sub-objectives
        for obj in result['objectives']:
            if obj:  # Ensure objective is not None
                objective_dict = self.create_mindmap_node_dict(obj['objectiveID'], obj['objectiveLabels'])

                # Process sub-objectives
                for sub_obj in obj['subObjectives']:
                    if sub_obj:  # Ensure sub-objective is not None
                        sub_objective_dict = self.create_mindmap_node_dict(sub_obj['name_id'], sub_obj['labels'])
                        objective_dict["children"][sub_obj['name']] = sub_objective_dict

                # Add the objective (with its sub-objectives) under the project
                mindmap_dict[project_name]["children"][obj['objectiveName']] = objective_dict

        return mindmap_dict

    def user_convo_to_expand_knowledge(self, base_mindmap):
        high_level_objective_session = self.create_discussion_session(
            discussion_name="High Level Objectives exploration", subject=)

        return base_mindmap

    def create_discussion_session(self, discussion_name=None, subject=None, agent: GPTAgent = None,
                                  conversation_type: ConversationType = ConversationType.AI_DEBATE,
                                  memory_type: MemoryType = MemoryType.LAST_X_MESSAGES, last_x_messages: int = 3,
                                  summarize_result=False,
                                  conversation_end_type: ConversationEndType = ConversationEndType.USER_ENDED,
                                  end_info=None, end_controlled_by_user=True, save_conversation: bool = False,
                                  save_path: str = None):
        # TODO: Implement the logic for a discussion session
        pass

    def explore_goal_convo(self):
        """
        Iteratively explores and updates a conversation about creating a mermaid diagram for engineering a DC motor.
        """
        initial_mindmap = self.build_mindmap_from_user_knowledge()

        final_mindmap = self.user_convo_to_expand_knowledge(initial_mindmap)
        final_mindmap = """```mermaid
mindmap
	root((Web-based Platform Project))
		Project Scope
			Project Planning
				Establish Objectives
				Define Milestones
				Assign Responsibilities
			Market Research
				Target Audience Analysis
				Competitor Analysis
				Feature Benchmarking
			Create an interactive,web-based platform
			Web Platform Creation
				Security Measures
					Data Encryption
					Secure Authentication
					Regular Security Audits
					Compliance with Security Standards
				User Interface Design
					Wireframing
					Prototyping
					User Testing
					Accessibility Standards Implementation
				Technical Documentation
					API Documentation
					Codebase Documentation
					Deployment Procedures
				Marketing and Outreach
					Promotional Campaigns
					Community Engagement
					Stakeholder Communication
				Technology Stack
					HTML
					CSS
					JavaScript
					React.js
				Team Composition
					Training and Development
						Skill Assessments
						Workshops and Webinars
						Code Reviews
					High School Coding Club Members
				Financial Resources
					Funding Strategies
						Crowdfunding Campaigns
						Membership Fees
						Grant Applications
						Sponsorship Deals
					Donations
					Partnerships
		Project Constraints
			Sustainability Planning
				Resource Optimization
				Scaling Strategies
				Long-term Funding Models
			Legal Compliance
				Data Protection Laws
				Accessibility Standards
				Copyright and Licensing
			Risk Assessment
				Identification
				Mitigation Planning
				Contingency Plans
			Limited Budget
			Fixed Timeframe
		User Experience
			User Feedback
				Collection
				Analysis
				Integration
		Platform Maintenance
			Monitoring and Analytics
				User Engagement Tracking
				Performance Metrics Analysis
				SEO Monitoring
				Feedback Loop Implementation
			Regular Updates
			Bug Fixes
			New Features
			Performance Optimization
```"""

        return final_mindmap

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


class TemporarySchedule:
    def __init__(self):
        pass


if __name__ == "__main__":
    my_schedule = ProjectSchedule()
