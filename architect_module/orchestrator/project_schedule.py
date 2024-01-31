import subprocess
from pathlib import Path

import json
import re
from collections import Counter

from front_end.tree_visualisation import DataVisualizer
from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType
from utils import persistance_access


class ProjectSchedule:
    current_script_path = Path(__file__).resolve()
    parent_folder = current_script_path.parent
    AGENT_SCHEDULE_FILE_PATH = parent_folder.joinpath('project_planning_files\agent_made_schedule.json')

    def __init__(self):
        self.data_visualizer = None
        self.gpt_manager = GPTManager()
        # self.memory_access = persistance_access.MemoryStreamAccess()
        self.mindmap = None
        self.project_schedule = None
        self.domain_file_text = None
        self.problem_file_text = None
        self.initialize_schedule()

    def visualize_schedule(self):
        if self.mindmap is None:
            self.mindmap = self.read_mindmap(self.AGENT_SCHEDULE_FILE_PATH)
        self.visualizer = DataVisualizer(self.mindmap)
        self.visualizer.visualize_data()

    def initialize_schedule(self):
        message = self.explore_goal_convo()
        self.save_final_convo(message)
        self.expand_schedule()
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

    def build_mindmap_from_user_knowledge(self):
        """
        Creates the initial message based on the user's project context.
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
  root((Web-based Platform Project))
    Project Scope
      Web Platform Creation
        Technology Stack
          HTML
          CSS
          JavaScript
          React.js
        Team Composition
          High School Coding Club Members
        Financial Resources
          Donations
          Partnerships
    Project Constraints
      Limited Budget
      Fixed Timeframe
    User Experience
      User Feedback
        Collection
        Analysis
        Integration
    Platform Maintenance
      Regular Updates
      Bug Fixes
      New Features
      Performance Optimization
```
          Do not forget that the nodes of this mindmap should not be verbs that describe direct actions(cook the potatoes) but rather verbs that describe higher level steps(prepare meal).
        """
        testing = True
        natural_l_query = "Can you list all the types of relationships present in my graph database." + "Could you provide a list of all the node types, or labels, that are used in my graph database?" + "Can you show me how all the nodes are connected to my 'Goal' nodes, including the names and IDs of these nodes and their relationships?"
        if testing:
            project_context = "The goal node in your graph database, specifically the one with the goal of 'Create an interactive, web-based platform', is connected to several other nodes. These connected nodes include various technologies like HTML, CSS, JavaScript, and React.js, which are used to achieve this goal. There are also restrictions in place, such as a limited budget and a fixed timeframe. The resources available for this goal include High School Coding Club Members and Donations and Partnerships. User Feedback and Platform Maintenance are also concerns related to this goal. Each of these nodes and their relationships contribute to the overall structure and function of your graph database."
        else:
            project_context = self.memory_access.neo4j_handler.direct_query_graph(
                query=["CALL db.relationshipTypes()", "CALL db.labels()", """MATCH (g:Goal)-[r]-(n)
            RETURN g.name AS GoalName, g.id AS GoalID, r.name AS RelationshipName, r.id AS RelationshipID, n.name AS ConnectedNodeName, n.id AS ConnectedNodeID"""],
                natural_l_query=natural_l_query, is_interpreted=True)

        message_creation_template = "Above is the information relative to a project you need to assist with, big or small, led by a human." \
                                    "Your goal is to give an order to the ai project manager that encapsulates the information you were given" \
                                    "and frames it into the context of a mermaid map. Do not use the information above directly in your text.  here is what you must do:\n" \
                                    "1. Briefly explain that he is a competent project manager.\n" \
                                    "2. Give him context for each element in the information above so he can accurately manage the project, cover all the goals and the challenges, strategies, or ressources available to him. You can paraphrase given data.\n" \
                                    "3. Explain that he has to create a process(reference this term in your message multiple times) that will help the human with the completion of his project " \
                                    "in a mermaid format where nodes represent high level steps that he infers from the information you give him(He is not supposed to simply copy paste your information, but reflect on it).\n" \
                                    "4. Explain that the structure of that mermaid mindmap is made to show that every node(representing a part of the process) is a compound task that can be broken down into other subaltern tasks to accomplish the goal a bit like in HDDL (HTN) format.\n"
        message_creator = self.gpt_manager.create_agent(
            system_prompt=project_context,
            model=ModelType.CHAT_GPT4_old,
            temperature=0.7,
            max_tokens=1000,
            messages=message_creation_template
        )
        if testing:
            message = """Dear AI Project Manager,

            You have been selected for your demonstrated competence in handling complex projects. We have an exciting new assignment for you that will utilize your skills in project management, strategic planning, and process creation.

            The project comprises building an engaging, web-based platform. This will involve the use of technologies such as HTML, CSS, JavaScript, and React.js. Your process should encapsulate the steps required to master these technologies and identify the points where they intersect to create the final product.

            You will need to consider constraints, such as budget limitations and tight deadlines. The existing resources at your disposal include a group of eager High School Coding Club members, along with funds from Donations and Partnerships. Your process should account for efficient use of these resources and include strategies to overcome constraints.

            A significant aspect of the project is ensuring user satisfaction and maintaining the platform. Your process should therefore include steps to gather and incorporate user feedback and outline a plan for regular maintenance of the platform.

            Remember, your role is not to merely parrot this information but to reflect on it and create a comprehensive process. This process will serve as a roadmap in the form of a mermaid diagram, where each node represents a high-level task derived from the information provided. 

            The structure of this mermaid diagram is akin to an HDDL (HTN) format where each node can be broken down into sub-tasks. This will provide a clear and detailed representation of the entire project, making it easier for the human team to follow and implement.

            We trust in your capabilities to manage this project efficiently and anticipate a detailed and well-structured process plan.

            Best of luck on your endeavor.

            Sincerely,
            [Your Name]"""
        else:
            message_creator.run_agent()
            message = message_creator.get_text()
        initial_diagram_creator = self.gpt_manager.create_agent(
            system_prompt=system_prompt,
            model=ModelType.CHAT_GPT4_old,
            temperature=0.7,
            max_tokens=700,
            messages=message
        )
        if testing:
            initial_diagram = """```mermaid
            mindmap
              root((Web-based Platform Project))
                Project Scope
                  Create an interactive, web-based platform
                  Web Platform Creation
                    Technology Stack
                      HTML
                      CSS
                      JavaScript
                      React.js
                    Team Composition
                      High School Coding Club Members
                    Financial Resources
                      Donations
                      Partnerships
                Project Constraints
                  Limited Budget
                  Fixed Timeframe
                User Experience
                  User Feedback
                    Collection
                    Analysis
                    Integration
                Platform Maintenance
                  Regular Updates
                  Bug Fixes
                  New Features
                  Performance Optimization
            ```"""
        else:
            initial_diagram_creator.run_agent()
            initial_diagram = initial_diagram_creator.get_text()

        message_review_template = 'Above is the data relative to a project you need to assist with, big or small, led by a human' \
                                  'Below is the mindmap that resulted from it. do you think that information that was intended to be in the mindmap is missing?' \
                                  'If so, make a list of elements that were not included in the mindmap, but that were in the information given above. do not mention an element if its not missing or if its unclear or if they are synonyms (like restriction and constraints). ' \
                                  'Only mention elements that are MISSING.' \
                                  'Use this format, consistency is key:\n' \
                                  '{1.itemdescription, where to put them and the original data you reference}\n' \
                                  '{2.itemdescription, where to put them and the original data you reference}\n' \
                                  'etc\n' \
                                  'or\n' \
                                  'There are no missing elements.' \
                                  'Below is the mindmap:'
        confirmation_agent = self.gpt_manager.create_agent(
            messages=project_context + '\n\n' + message_review_template + initial_diagram,
            model=ModelType.GPT_4_TURBO, temperature=0.1, max_tokens=300)
        if testing:
            missing_items_found = False
        else:
            confirmation_agent.run_agent()
            confirmation_message = confirmation_agent.get_text()
            missing_items_pattern = r'\{\d+\..+?\}'
            missing_items_found = re.search(missing_items_pattern, confirmation_message)

        if missing_items_found:
            missing_items_message = missing_items_found.group()
            initial_diagram_creator.update_agent(
                messages=initial_diagram + '. Add the following items:' + missing_items_message)
            initial_diagram_creator.run_agent()
            updated_diagram = initial_diagram_creator.get_text()
            return updated_diagram
        else:
            return initial_diagram

    def user_convo_to_expand_knowledge(self, base_mindmap):
        """
        Iteratively builds on the user's knowledge to create a mermaid diagram.
        """
        recursive_content = """Do you think that the root of the organization map above lacks any steps to reach its objective?
        For each addition of a step you would make, dont forget to add small description(30-50 words) that explains your reasoning. 
        please give your answer in markdown. Do not think of more than 4 additions at a time. Do not rewrite the whole mindmap, give a snippet of the new elements.
        Follow this format for your suggestions: 
        1. Add "RECOMMENDATION" under "EXISTING PARENT OF NEW NODE"

    REASONING(30-50 words)
    SNIPPET:
   ```mermaid
   mindmap
       EXISTING PARENT OF NEW NODE
         RECOMMENDATION
           RECOMMENDATION SUBSTEPS#1
           RECOMMENDATION SUBSTEPS#2
           ETC
   ```"""
        enhanced_versions = []
        current_mindmap = base_mindmap

        while True:
            mindmap_agent = self.gpt_manager.create_agent(
                model=ModelType.GPT_4_TURBO,
                temperature=0.7,
                max_tokens=600,
                messages=current_mindmap + recursive_content
            )
            mindmap_agent.run_agent()
            agent_response = mindmap_agent.get_text()
            snippets = re.findall(r"```.*?```", agent_response, re.DOTALL)

            user_approvals = self.discuss_with_user(snippets, agent_response)
            for snippet, approval in zip(snippets, user_approvals):
                if approval:
                    try:
                        current_mindmap = self.update_mindmap_with_snippet(current_mindmap, snippet)
                    except ValueError as error:
                        print(f"Mindmap update error: {error}")

            enhanced_versions.append(current_mindmap)
            print(f"Current mindmap update:\n{current_mindmap}")

            continue_discussion = input("Do you want more suggestions? (yes/no): ")
            if continue_discussion.lower() != 'yes':
                break

        return enhanced_versions[-1] if enhanced_versions else None

    def discuss_with_user(self, snippets, full_text):
        user_approvals = []
        print(full_text)
        for snippet in snippets:
            print(f"Proposed addition:\n{snippet}\n")
            while True:
                approval = input("Do you approve this addition? (yes/no): ").strip().lower()
                if approval == 'yes':
                    user_approvals.append(True)
                    break
                elif approval == 'no':
                    user_approvals.append(False)
                    break
                else:
                    self.discussion_session(snippet)
        return user_approvals

    def discussion_session(self, snippet):
        # TODO: Implement the logic for a discussion session
        pass

    @staticmethod
    def update_mindmap_with_snippet(original_diagram: str, new_snippet: str) -> str:
        def preprocess_diagram(diagram):
            # Split the diagram into lines
            lines = diagram.split('\n')

            # Replace leading spaces with tabs
            processed_lines = []
            for line in lines:
                # Count leading spaces
                leading_spaces = len(line) - len(line.lstrip(' '))
                # Convert every 4 spaces to a tab (assuming 4 spaces per tab, adjust if different)
                tabs = '\t' * (leading_spaces // 2)
                processed_line = tabs + line.lstrip(' ')
                processed_lines.append(processed_line)

            return '\n'.join(processed_lines)

        def normalize_indentation(text, parent_indentation, next_node_indentation):
            lines = text.split("\n")
            normalized_lines = []

            # Determine the tab count based on actual tabs if they are present, otherwise default to space calculation
            parent_tabs_count = parent_indentation.count("\t") if "\t" in parent_indentation else len(
                parent_indentation) // 2
            next_node_tabs_count = next_node_indentation.count("\t") if "\t" in next_node_indentation else len(
                next_node_indentation) // 2

            for i, line in enumerate(lines):
                normalized_line = line.lstrip()  # Remove leading whitespace
                if i == 0:
                    # For the first node (direct child of parent), add one extra tab than the parent
                    normalized_line = ("\t" * (parent_tabs_count + 1)) + normalized_line
                else:
                    # For the children of the first node, add two extra tabs than the parent
                    normalized_line = ("\t" * (parent_tabs_count + 2)) + normalized_line
                normalized_lines.append(normalized_line)

            indented_finish = "\n".join(normalized_lines)
            indented_finish += "\n" + ("\t" * next_node_tabs_count)
            return indented_finish

        # Extract the parent node and its indentation
        parent_node_pattern = r"(mindmap\n)(\s*)([^\n]+)"
        parent_node_match = re.search(parent_node_pattern, new_snippet)
        if not parent_node_match:
            raise ValueError("Parent node not found in the snippet.")
        # Preprocess the original diagram to convert spaces to tabs
        processed_original_diagram = preprocess_diagram(original_diagram)

        # Extract the parent node name from new_snippet
        parent_node_name_pattern = r"(mindmap\n)(\s*)([^\n]+)"
        parent_node_name_match = re.search(parent_node_name_pattern, new_snippet)
        if not parent_node_name_match:
            raise ValueError("Parent node not found in the snippet.")
        parent_node = parent_node_name_match.group(3).strip()

        # Find the parent node in the processed_original_diagram to get its indentation as a string of tabs
        parent_node_in_processed_pattern = r'(\t*)' + re.escape(parent_node) + r'\n'
        parent_node_in_processed_match = re.search(parent_node_in_processed_pattern, processed_original_diagram)
        if not parent_node_in_processed_match:
            raise ValueError("Parent node not found in the processed original diagram.")
        parent_indentation = parent_node_in_processed_match.group(1)

        # Find the indentation of the next node after the parent node
        next_node_pattern = re.escape(parent_node) + r"\n(\t*)([^\n]*)"
        next_node_match = re.search(next_node_pattern, processed_original_diagram)
        if next_node_match:
            next_node_indentation = next_node_match.group(1)
        else:
            next_node_indentation = ""

        # Extract the content to be added
        content_pattern = re.escape(parent_node) + r"\n\s*(.+?)```"
        content_match = re.search(content_pattern, new_snippet, re.DOTALL)
        if content_match:
            content = content_match.group(1).strip()
        else:
            raise ValueError("No valid content format found in the snippet.")

        # Normalize indentation of the new content
        indented_content = normalize_indentation(content, parent_indentation, next_node_indentation)

        # Insert the indented content under the parent node in the original mindmap
        insertion_pattern = re.escape(parent_node) + r"(\n\s*)"
        match = re.search(insertion_pattern, original_diagram)
        if not match:
            raise ValueError(f"Node '{parent_node}' not found in the mindmap.")

        parent_to_next_node_tabs_pattern = re.escape(parent_node) + r"\n(\t*)"
        updated_processed_diagram = re.sub(parent_to_next_node_tabs_pattern, parent_node + "\n",
                                           processed_original_diagram)

        # Then insert the indented content under the parent node
        insertion_pattern = re.escape(parent_node) + r"(\n)"
        updated_diagram = re.sub(insertion_pattern, match.group(0) + indented_content, updated_processed_diagram, 1)

        # Remove spaces between words
        updated_diagram_cleaned = re.sub(r'(?<!\w) | (?!\w)', '', updated_diagram)
        expected_tab_counts = [line.count("\t") for line in indented_content.split("\n")]

        # Split the updated_diagram_cleaned to get the actual lines
        actual_lines = updated_diagram_cleaned.split('\n')

        # Create a regex pattern to find the parent node with any number of leading tabs
        parent_node_regex_pattern = r'\t*' + re.escape(parent_node)

        # Find the index of the parent node in actual_lines using the regex pattern
        for i, line in enumerate(actual_lines):
            if re.match(parent_node_regex_pattern, line):
                start_index = i + 1
                break
        else:
            raise ValueError("Parent node not found in the updated diagram.")

        end_index = start_index + len(expected_tab_counts)

        # Adjust the tab counts in the actual lines
        for i, expected_count in enumerate(expected_tab_counts, start=start_index):
            if i < end_index:
                actual_tabs_count = actual_lines[i].count("\t")
                if actual_tabs_count < expected_count:
                    actual_lines[i] = ("\t" * (expected_count - actual_tabs_count)) + actual_lines[i]
                elif actual_tabs_count > expected_count:
                    actual_lines[i] = actual_lines[i][actual_tabs_count - expected_count:]

        final_updated_diagram = '\n'.join(actual_lines)

        return final_updated_diagram

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


class TemporarySchedule:
    def __init__(self):
        pass


if __name__ == "__main__":
    my_schedule = ProjectSchedule()
