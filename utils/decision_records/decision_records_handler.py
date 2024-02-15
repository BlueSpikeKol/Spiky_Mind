import json
from pathlib import Path
from typing import List, Dict, Optional
import re

from utils.decision_records.decision_records import DecisionRecord, RecordType
from utils.persistance_access import MemoryStreamAccess
from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType

MOCK_DRF_DATA = {
    "previous_record": "N/A",
    "context": "Decision on choosing a cloud provider for hosting our new web application.",
    "decision_drivers": "Cost, scalability, reliability, and support.",
    "options_considered": "AWS, Google Cloud, Azure",
    "decision": "Chose AWS for its scalability and extensive support.",
    "consequences": "Higher initial cost but better long-term scalability.",
    "lessons_learned": "In-depth comparison and trial are crucial before making a decision.",
    "next_record": "N/A",
    "implementation_plan": "Start with AWS's free tier and scale as needed.",
    "validation_and_monitoring": "Monthly review of costs and performance metrics.",
    "feedback_loop": "Quarterly feedback sessions with the development team."
}


class DecisionRecordHandler:
    def __init__(self):
        self.decision_record = None
        self.memory_access = MemoryStreamAccess()
        self.gpt_manager = GPTManager()
        self.filepath = Path(__file__).parent / "saved_records"

    def create_drfs_for_given_nodes(self, node_ids):
        """
        Creates and links a new Decision Record Form (DRF) for each specified node ID.

        Parameters:
        - node_ids (list of str): A list of node IDs to create DRFs for.
        """
        for node_id in node_ids:
            drf_id = self.fetch_drf_id_for_node(node_id)
            if not drf_id:
                self.create_and_link_new_drf(node_id)
            else:
                print(f"Node {node_id} already has a linked DRF with ID {drf_id}.")

    def pair_nodes_without_drf(self):
        """
        Identifies nodes without a Decision Record Form (DRF) and pairs each with a new DRF, considering their labels.
        """
        nodes_without_drf = self.fetch_nodes_without_drf()

        for node_info in nodes_without_drf:
            self.create_and_link_new_drf(node_info['nodeId'], node_info['labels'])

    def fetch_nodes_without_drf(self):
        """
        Fetches nodes without a Decision Record Form (DRF), including their labels for accurate query construction.
        """
        query = """
        MATCH (n)
        WHERE NOT EXISTS ((n)-[:HAS_DRF]->(:DRF))
        AND (n:Objective OR n:Project)
        RETURN labels(n) AS labels, n.name_id AS nodeId
        """
        # Execute the query using the modified execute_queries function
        result = self.memory_access.neo4j_handler.execute_queries(query)

        # Check if result is not None and not empty before processing
        if result is None or len(result) == 0:
            return []

        # Process and return the result if nodes are found
        return [{"labels": record['labels'], "nodeId": record['nodeId']} for record in result]

    def fetch_drf_id_for_node(self, node_id):
        query = f"""
        MATCH (n {{id: '{node_id}'}})-[:HAS_DRF]->(drf:DRF)
        RETURN drf.name_id AS drfId
        """
        result = self.memory_access.neo4j_handler.execute_queries(query)
        return result[0]['drfId'] if result else None

    def create_and_link_new_drf(self, node_id, node_label):
        record_type = self.determine_record_type(node_id)  # This method's logic remains unchanged
        new_drf = self.build_record(record_type, auto_fill=True, node_id=node_id)
        self.add_to_db(new_drf)
        self.link_drf_to_node(node_id, new_drf.id, node_label)

    def create_from_existing_drf(self, drf_id, modified_data=None):
        """
        Modifies an existing DRF by either prompting for new data or using provided data.

        Parameters:
        - drf_id (str): The ID of the DRF to modify.
        - modified_data (dict, optional): New data to replace in the DRF. If None, the user will be prompted.
        """
        # Fetch existing data to determine the record type and to use as default values
        existing_data = self.fetch_drf_data(drf_id)
        record_type = existing_data['type']

        if modified_data is None:
            # Collect new data from the user, using existing data as defaults
            new_data = self.collect_data_from_user(record_type, previous_record_id=drf_id,
                                                   existing_data=existing_data['content'])
        else:
            # Merge provided modified data with existing data to ensure all fields are covered
            new_data = {**existing_data['content'], **modified_data}

        # Create a new DRF with the merged new data
        new_drf = self.build_record(record_type, new_data, drf_id)
        # Add the new DRF to the database, replacing the old one
        self.add_to_db(new_drf)

    def link_drf_to_node(self, node_id, drf_id, node_labels):
        # Ensure node_labels is a list to handle both single and multiple labels
        if not isinstance(node_labels, list):
            node_labels = [node_labels]

        # Construct the label part for the query
        labels_str = ":".join(node_labels)

        # Adjust the queries to use the dynamic node labels
        has_drf_query = f"MATCH (n:{labels_str} {{name_id: $node_id}}), (drf:DRF {{name_id: $drf_id}}) MERGE (n)-[:HAS_DRF]->(drf) RETURN n, drf"
        helped_decide_query = f"MATCH (n:{labels_str} {{name_id: $node_id}}), (drf:DRF {{name_id: $drf_id}}) MERGE (drf)-[:HELPED_DECIDE]->(n) RETURN n, drf"

        try:
            # Execute relationship creation queries with parameters
            has_drf_result = self.memory_access.neo4j_handler.execute_queries(
                [(has_drf_query, {'node_id': node_id, 'drf_id': drf_id})])
            helped_decide_result = self.memory_access.neo4j_handler.execute_queries(
                [(helped_decide_query, {'node_id': node_id, 'drf_id': drf_id})])

            # Check if relationships were created
            if not has_drf_result or not helped_decide_result:
                print(
                    f"No relationship was created between DRF {drf_id} and Node {node_id}. Please check the IDs and labels.")
            else:
                print(f"Relationships successfully created between DRF {drf_id} and Node {node_id}.")
        except Exception as e:
            print(f"Failed to link DRF {drf_id} with Node {node_id}: {e}")

    def determine_record_type(self, node_id):
        # TODO: Implement logic to fetch the node and determine the record type
        query = f"""
        MATCH (n) WHERE n.name_id = '{node_id}'
        RETURN labels(n) AS labels
        """
        result = self.memory_access.neo4j_handler.execute_queries(query)
        if result and 'labels' in result:
            labels = result['labels']
            if 'Project' in labels:
                return RecordType.CDR
            elif 'Objective' in labels:
                return RecordType.SDR  # Assuming SDR for Objectives, adjust as needed
            else:
                # Handle other types or throw an error
                raise ValueError("Unable to determine record type for given labels.")
        else:
            raise ValueError("Node not found or unable to determine record type.")

    def fetch_drf_data(self, drf_id):
        query = f"""
        MATCH (drf:DRF) WHERE drf.id = '{drf_id}'
        RETURN drf.content AS content, drf.type AS type
        """
        result = self.memory_access.neo4j_handler.execute_queries(query)
        if result:
            # Assuming the content is stored as a stringified JSON and type as a string
            content = json.loads(result[0]['content']) if 'content' in result[0] else {}  # might not be json
            record_type = RecordType[result[0]['type']] if 'type' in result[0] else None
            return {"content": content, "type": record_type}
        else:
            raise ValueError("DRF not found.")

    def replace_drf(self, drf_id, modified_data):
        """
        Updates an existing decision record form in the database with new data by creating a new DRF.

        Parameters:
        - drf_id (str): The unique identifier of the decision record form to update.
        - modified_data (dict): The new data to update the decision record form with.
        """
        # Fetch existing DRF data to get the full picture
        existing_data = self.fetch_drf_data(drf_id)
        record_type = existing_data['type']

        # Prepare the data for creating a new DRF
        updated_data = {**existing_data['content'], **modified_data}

        # Use build_record to create the updated DRF
        updated_drf = self.build_record(record_type, modified_data=updated_data, previous_record_id=drf_id)

        # Delete the old DRF entry from the database
        self.delete_drf_from_db(drf_id)

        # Add the updated DRF to the database
        self.add_to_db(updated_drf)
    def sanitize_name(self, name):
        # Regular expression pattern to match a UUID
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        # Extract the name without UUID
        return re.sub(uuid_pattern, '', name).strip("_").strip()

    def build_record(self, record_type: RecordType, data=None, previous_record_id=None, modified_data=None,
                     auto_fill=False, node_id=None):
        """
        Builds a DecisionRecord object based on the provided data. Handles four cases:
        1. Creating a DRF from scratch by filling every field, with the option to skip fields.
        2. Creating a DRF by filling in fields that are empty in the provided data.
        3. Creating a DecisionRecord directly from an already formed dict.
        4. Automatically filling a DRF based on the properties linked to a specific node_id.

        Parameters:
        - record_type (RecordType): The type of the decision record.
        - data (dict, optional): Initial data for the DRF. If None, data will be collected from the user.
        - previous_record_id (str, optional): ID of the previous record, if any.
        - modified_data (dict, optional): Data to modify an existing DRF. If provided, `data` is updated with this.
        - auto_fill (bool, optional): If True, automatically fills the DRF based on the node_id's linked properties.
        - node_id (str, optional): The ID of the node from which to auto-fill the DRF.

        Returns:
        - DecisionRecord: The newly created DecisionRecord object.
        """
        record_name = None
        if auto_fill and node_id:
            # Case 4: Automatically fill a DRF based on the properties linked to a specific node_id
            linked_properties = self.retrieve_linked_properties_and_node(node_id)
            final_data = self.auto_fill_data_from_properties(linked_properties, record_type)
            record_name = self.sanitize_name(node_id)
        elif modified_data:
            # Case 3: Directly create a DecisionRecord from a fully formed dict
            final_data = {**data, **modified_data} if data else modified_data
        elif data:
            # Case 2: Fill in missing fields in the provided data
            final_data = self.complete_data_from_user(data, record_type, previous_record_id)
            record_name = previous_record_id or final_data.get('name')
        else:
            # Case 1: Create a DRF from scratch
            final_data = self.collect_data_from_user(record_type, previous_record_id)
            record_name = previous_record_id or final_data.get('name')

        return DecisionRecord(record_type, final_data, record_name=record_name)

    def retrieve_linked_properties_and_node(self, node_id):
        """
        Retrieves properties linked to a specific node_id from the Neo4j database, along with the node itself.

        Parameters:
        - node_id (str): The ID of the node from which to retrieve properties and the node data.

        Returns:
        - List[Dict[str, str]]: A list of dictionaries, each representing a property linked to the node.
        - Dict[str, str]: A dictionary representing the node itself.
        """
        query = f"""
        MATCH (n {{name_id: '{node_id}'}})-[:HAS_PROPERTY]->(p)
        RETURN n.name_id AS node_name_id, n.name AS node_name, n.label AS node_label, n.information AS node_information,
               collect({{name_id: p.name_id, name: p.name, information: p.information}}) AS properties
        """
        try:
            results = self.memory_access.neo4j_handler.execute_queries(query)
            if results:
                node_data = results['properties']
                properties = [{'name_id': prop['name_id'], 'name': prop['name'], 'information': prop['information']} for
                              prop in node_data]
                return properties
            else:
                return []
        except Exception as e:
            print(f"Failed to retrieve linked properties and node for node_id {node_id}: {e}")
            return []

    def auto_fill_data_from_properties(self, properties, record_type):
        # Define ignorable fields that cannot be automatically filled
        IGNORABLE_FIELDS = ["previous_record", "next_record", "review_date"]

        # Initialize DRF data with default values for required fields, excluding ignorable fields
        drf_data = {field: "" for field in self.get_required_fields(record_type) if field not in IGNORABLE_FIELDS}

        # Iterate over each required field to fill it based on properties and linked Rounds
        for field in drf_data.keys():
            question = self.formulate_question_for_field(field)
            relevant_properties = self.query_relevant_information(properties, question)
            rounds_info_by_property = self.retrieve_linked_rounds_info(relevant_properties)

            # New: Extract round IDs for each field and store them alongside the information
            drf_data[field] = {
                "information": self.extract_information_for_field(rounds_info_by_property, question),
                "round_ids": [round_info["id"] for round_info_list in rounds_info_by_property.values() for round_info in
                              round_info_list]
            }

        return drf_data

    def formulate_question_for_field(self, field):
        # Comprehensive mapping of fields to questions for SDR, CDR, and IFR.
        questions_map = {
            # Shared fields across SDR, CDR, and IFR
            "previous_record": "What is the previous decision or step related to this objective or implementation?",
            "summary": "Can you provide a brief overview of the decision or summary of the implementation?",
            "decision": "What option was chosen, what was rejected, and which option was implemented?",
            "rationale": "Why was this option or approach chosen?",
            "impact": "What are the expected outcomes or impacts of this decision or implementation?",
            "lessons_learned": "What key insights or takeaways were learned from this decision process or implementation?",
            "next_record": "What is the next decision, step, or record related to this objective or implementation?",
            "review_date": "When should this decision or implementation be revisited?",

            # Comprehensive Decision Record (CDR) specific fields
            "context": "What is the detailed background leading to this decision?",
            "decision_drivers": "What are the key factors influencing this decision?",
            "options_considered": "What options were considered for this decision?",
            "consequences": "What are the anticipated positive and negative outcomes?",
            "implementation_plan": "What steps will be taken to execute this decision?",
            "validation_and_monitoring": "How will the effectiveness of this decision be assessed?",
            "feedback_loop": "What mechanism is in place for continuous improvement?",

            # Implementation Follow-up Record (IFR) specific fields
            "decision_summary": "Can you summarize the decision that led to this implementation?",
            "implementation_steps": "What were the key steps taken in the implementation?",
            "metrics_for_success": "How is success being measured for this implementation?",
            "iterations": "What plan is there for iterative development and review?",
            "feedback_collection": "How is feedback being collected from users or stakeholders?",
            "pivot_or_persevere": "Under what criteria will adjustments be made or the current approach continued?"
        }

        return questions_map.get(field, "Could you provide more details on this aspect?")

    def query_relevant_information(self, properties: List[Dict[str, str]], question: str) -> List[str]:
        """
        Queries for the most relevant properties to a given question by analyzing the properties linked to a specific node.

        Parameters:
        - properties (List[Dict[str, str]]): A list of dictionaries, each representing a property linked to the node.
        - question (str): The question for which relevant information is being sought.

        Returns:
        - List[str]: A list of name_ids for the properties deemed most relevant to the question.
        """
        properties_description = "\nNEXT PROPERTY:\n".join(
            [f"{prop['name']}: {prop['information']}" for prop in properties])
        prompt = f"In order to answer the question '{question}', what are the top most interesting properties to look more deeply into," \
                 f" do not talk about all properties, just the most relevent ones?\n" \
                 f"Here are the properties and a short description of their content:\n{properties_description}\n" \
                 f"Please give your answer in this format:" \
                 f" Property1, \nreason1(30 words max); Property2, \nreason2(30 words max) etc."

        # Initialize GPT agent and get the relevant properties string
        property_chooser = self.gpt_manager.create_agent(messages=prompt, model=ModelType.GPT_3_5_TURBO, max_tokens=400,
                                                         temperature=0.2)
        property_chooser.run_agent()
        relevant_properties_string = property_chooser.get_text()

        # Generate cleaned names list
        cleaned_names = [prop['name'].split(':')[0].strip() for prop in properties]

        # Match cleaned names against the agent's output
        relevant_properties_names = [name for name in cleaned_names if name in relevant_properties_string]

        # Extract IDs based on the matched names
        relevant_properties_ids = [prop['name_id'] for prop in properties if
                                   prop['name'].split(':')[0].strip() in relevant_properties_names]

        return relevant_properties_ids

    def retrieve_linked_rounds_info(self, relevant_properties_ids: List[str]) -> Dict[str, List[Dict[str, str]]]:
        """
        Retrieves information for rounds linked to the specified property IDs.

        Parameters:
        - relevant_properties_ids (List[str]): A list of IDs for the properties deemed most relevant.

        Returns:
        - Dict[str, List[Dict[str, str]]]: A dictionary where each key is a property ID, and each value is a list of dictionaries. Each dictionary in the list contains 'name', 'information', and 'id' keys for a round linked to the property.

        Example output:
        {
            "property1_id": [
                {"name": "Round 1", "information": "Round 1 information", "id": "round1_id"},
                {"name": "Round 2", "information": "Round 2 information", "id": "round2_id"}
            ],
            "property2_id": [
                {"name": "Round 3", "information": "Round 3 information", "id": "round3_id"}
            ]
        }
        """
        rounds_info_by_property = {}

        for prop_id in relevant_properties_ids:
            primary_query = f"""
            MATCH (p {{name_id: '{prop_id}'}})-[:HAS_ROUND]->(r:Round)
            RETURN r.name AS round_name, r.information AS round_information, r.name_id AS round_id
            """
            inverse_query = f"""
            MATCH (r:Round)-[:CONTRIBUTES_TO]->(p {{name_id: '{prop_id}'}})
            RETURN r.name AS round_name, r.information AS round_information, r.name_id AS round_id
            """
            try:
                results = self.memory_access.neo4j_handler.execute_queries(primary_query)
                if not results:  # If no results from the primary query, try the inverse query
                    results = self.memory_access.neo4j_handler.execute_queries(inverse_query)

                # Normalize results to always be a list of dicts
                results = results if isinstance(results, list) else [results] if results else []

                # Storing round information and IDs
                rounds_info = [
                    {"name": result['round_name'], "information": result['round_information'], "id": result['round_id']}
                    for result in results]
                rounds_info_by_property[prop_id] = rounds_info
            except Exception as e:
                print(
                    f"Failed to retrieve Rounds linked to property {prop_id} with both direct and inverse methods: {e}")
                rounds_info_by_property[prop_id] = []

        return rounds_info_by_property

    def extract_information_for_field(self, rounds_info_by_property: Dict[str, List[Dict[str, str]]],
                                      question: str, is_fast: bool = True) -> str:
        """
        Extracts specific information for a DRF field from the combined information of relevant Rounds,
        using either a fast or slow extraction method.

        Parameters:
        - rounds_info_by_property (Dict[str, List[Dict[str, str]]]): A dictionary where each key is the name of a property
          and the value is a list of dictionaries, each containing information of a round linked to it.
        - question (str): The specific question for which information is being extracted.
        - is_fast (bool, optional): Determines whether to use the fast extraction method. Defaults to True.

        Returns:
        - str: The extracted information for the specified question.
        """
        if is_fast:
            return self.fast_extraction(rounds_info_by_property, question)
        else:
            return self.slow_extraction(rounds_info_by_property, question)

    def fast_extraction(self, rounds_info_by_property: Dict[str, List[Dict[str, str]]], question: str) -> str:
        """
        A fast method for extracting specific information for a DRF field from the combined information of relevant Rounds.

        This is the current implementation, directly extracting information based on the rounds' details without user intervention.

        Parameters and returns are identical to extract_information_for_field.
        """
        combined_rounds_info_list = []

        # Iterate over each property's rounds information
        for rounds_info in rounds_info_by_property.values():
            for round_info in rounds_info:
                # Combine name, information, and possibly ID of the round into a string
                combined_info = f"Round Name: {round_info['name']}, Information: {round_info['information']}"
                combined_rounds_info_list.append(combined_info)

        # Combine all rounds' information into a single string for analysis
        combined_rounds_info = "\n".join(combined_rounds_info_list)

        # Prepare the prompt for the AI model
        prompt = f"Based on the following details (Details might be out of order, try to pick out facts to answer the question), extract information relevant to: '{question}'.\n\nDetails:\n{combined_rounds_info}\n\nAnswer:"

        # Create and run the agent to extract information
        extraction_agent = self.gpt_manager.create_agent(messages=prompt, model=ModelType.GPT_3_5_TURBO, max_tokens=300,
                                                         temperature=0.7)
        extraction_agent.run_agent()
        extracted_info = extraction_agent.get_text().strip()
        return extracted_info

    def slow_extraction(self, rounds_info_by_property: Dict[str, List[Dict[str, str]]], question: str) -> str:
        """
        A slow method for extracting specific information for a DRF field from the combined information of relevant Rounds.

        TODO: Implement this function using the information intelligently to fill the decision record with the help of the user.

        Parameters and returns are identical to extract_information_for_field.
        """
        return ""

    def complete_data_from_user(self, data, record_type, previous_record_id=None):
        """
        Completes missing fields in the provided data based on the required fields for the record type.

        Parameters:
        - data (dict): The initial data for the DRF.
        - record_type (RecordType): The type of the decision record.
        - previous_record_id (str, optional): ID of the previous record, if any, to pre-fill the "previous_record" field.

        Returns:
        - dict: The completed data with all required fields filled.
        """
        required_fields = self.get_required_fields(record_type)
        for field in required_fields:
            if field not in data or data[field] is None or data[field].strip() == "":
                if field == "previous_record" and previous_record_id:
                    data[field] = previous_record_id  # Pre-fill with the previous record ID if available
                else:
                    user_input = input(f"Enter {field} (press Enter to skip): ")
                    data[field] = user_input if user_input.strip() != "" else "N/A"  # Allow skipping fields

        return data

    def collect_data_from_user(self, record_type, previous_record_id=None, existing_data=None):
        """
        Collects data from the user for a decision record, allowing fields to be skipped.
        Skipped fields will retain their current value if existing data is provided.

        Parameters:
        - record_type (RecordType): The type of the decision record.
        - previous_record_id (str, optional): ID of the previous record for linking.
        - existing_data (dict, optional): Existing data for the DRF being modified. If provided, skipping a field will retain its current value.

        Returns:
        - dict: The collected or modified data for the decision record.
        """
        data = {}
        required_fields = self.get_required_fields(record_type)

        for field in required_fields:
            if previous_record_id and field == "previous_record":
                data[field] = previous_record_id
            else:
                prompt = self.get_prompt_for_field(field, record_type.name_id)
                user_input = input(f"{prompt} (Press enter to skip): ")

                if user_input.strip() == "" and existing_data and field in existing_data:
                    # If the user skips and there's existing data, retain the current value
                    data[field] = existing_data[field]
                elif user_input.strip() != "":
                    # If the user provides input, use the new value
                    data[field] = user_input
                else:
                    # If there's no existing data and the user skips, leave the field empty
                    data[field] = None

        return data

    @staticmethod
    def get_prompt_for_field(field, record_type_name):
        prompts = {
            "SDR": {
                "previous_record": "Enter the link to the previous decision record, if any: ",
                "summary": "Enter a brief overview of the decision: ",
                "decision": "Enter the option chosen (short description): ",
                "rationale": "Enter why this option was chosen (1-2 sentences): ",
                "impact": "Enter the expected outcomes (brief): ",
                "lessons_learned": "Enter key takeaways from this decision process: ",
                "next_record": "Enter the link to the next decision record, if any: ",
                "review_date": "Enter the date when to revisit this decision: "
            },
            "CDR": {
                "previous_record": "Enter the link to the previous decision record, if any: ",
                "context": "Enter detailed background and current situation: ",
                "decision_drivers": "Enter key factors influencing the decision: ",
                "options_considered": "Enter the options considered (description): ",
                "decision": "Enter the chosen option (detailed description): ",
                "consequences": "Enter the consequences (positive and negative): ",
                "lessons_learned": "Enter insights gained from this decision: ",
                "next_record": "Enter the link to the next decision record, if any: ",
                "implementation_plan": "Enter steps for executing the decision: ",
                "validation_and_monitoring": "Enter how the decision will be assessed: ",
                "feedback_loop": "Enter the mechanism for continuous improvement: "
            },
            "IFR": {
                "previous_record": "Enter the link to the previous decision record, if any: ",
                "decision_summary": "Enter a quick recap of the decision made: ",
                "implementation_steps": "Enter the implementation steps (brief description): ",
                "metrics_for_success": "Enter key indicators to measure progress: ",
                "iterations": "Enter the plan for iterative development and review: ",
                "lessons_learned": "Enter valuable insights from implementation: ",
                "next_record": "Enter the link to the next decision record, if any: ",
                "feedback_collection": "Enter methods for gathering user/stakeholder feedback: ",
                "pivot_or_persevere": "Enter criteria for deciding to adjust or continue with the current approach: "
            }
        }

        return prompts[record_type_name].get(field, f"Enter {field}: ")

    @staticmethod
    def get_required_fields(record_type):
        # Return a list of required fields based on the record type
        if record_type == RecordType.SDR:
            return ["previous_record", "summary", "decision", "rationale", "impact", "lessons_learned", "next_record",
                    "review_date"]
        elif record_type == RecordType.CDR:
            return ["previous_record", "context", "decision_drivers", "options_considered", "decision", "consequences",
                    "lessons_learned", "next_record", "implementation_plan", "validation_and_monitoring",
                    "feedback_loop"]
        elif record_type == RecordType.IFR:
            return ["previous_record", "decision_summary", "implementation_steps", "metrics_for_success", "iterations",
                    "lessons_learned", "next_record", "feedback_collection", "pivot_or_persevere"]
        else:
            raise ValueError("Invalid record type")

    def add_to_db(self, decision_record: DecisionRecord):
        """
        Adds a DecisionRecord to the Neo4j database using parameters in the Cypher query.

        Parameters:
        - decision_record: An instance of DecisionRecord to be added to the database.
        """
        # Serialize the decision record data as a JSON string
        content_str = json.dumps(decision_record.data)

        # Use parameters to pass data safely
        query = """
        MERGE (dr:DRF {name_id: $name_id})
        ON CREATE SET dr.type = $type, dr.content = $content, dr.name = $name
        ON MATCH SET dr.type = $type, dr.content = $content, dr.name = $name
        """
        params = {
            "name_id": decision_record.id,
            "type": decision_record.record_type.value,
            "content": content_str,
            "name": decision_record.name
        }

        # Execute the query with parameters
        self.memory_access.neo4j_handler.execute_queries((query, params))

    def delete_drf_from_db(self, drf_id):
        """
        Deletes a decision record form from the database.

        Parameters:
        - drf_id (str): The unique identifier of the decision record form to delete.
        """
        delete_query = f"""
        MATCH (drf:DRF {{id: '{drf_id}'}})
        DETACH DELETE drf
        """
        self.memory_access.neo4j_handler.execute_queries(delete_query)

    def create_drf_from_db(self, drf_id: str) -> Optional[DecisionRecord]:
        """
        Fetches a Decision Record Form (DRF) from the database using its ID and creates a DecisionRecord object.

        Parameters:
        - drf_id (str): The unique identifier of the DRF in the database.

        Returns:
        - DecisionRecord: The constructed DecisionRecord object based on the fetched data, or None if not found.
        """
        query = f"""
        MATCH (drf:DRF {{id: '{drf_id}'}})
        RETURN drf.type AS type, drf.content AS content, drf.name AS name
        """
        try:
            result = self.memory_access.neo4j_handler.execute_queries(query)
            if result:
                drf_data = result['content']
                drf_data_clean = drf_data.replace('\n', '\\n').replace('\r', '\\r')
                drf_type = None
                temp_type = result['type']
                if temp_type == "Comprehensive Decision Record":
                    drf_type = RecordType.CDR
                elif temp_type == "Implementation Follow-up Record":
                    drf_type = RecordType.IFR
                elif temp_type == "Small Decision Record":
                    drf_type = RecordType.SDR
                drf_name = result['name']

                drf_data_dict = json.loads(drf_data_clean)

                return DecisionRecord(record_type=drf_type, data=drf_data_dict, record_name=drf_name)
            else:
                print(f"No DRF found with ID {drf_id}")
                return None
        except Exception as e:
            print(f"Error fetching DRF from the database: {e}")
            return None


if __name__ == "__main__":
    # Initialize the DecisionRecordCreator
    decision_record_creator = DecisionRecordHandler()

    decision_record_creator.pair_nodes_without_drf()

    # Use the mock data to build a record
    # drf = decision_record_creator.create_drf_from_db("489539c1-89e7-4861-80cc-5100392f0622Designing the interactive platformRecordType.SDR")
    # if drf:
    #     decision_record_creator.link_drf_to_node("Designing the interactive platform_f349c5e4-c009-405c-8557-be6b5b57d176", drf.id, "Objective")
    # print("Mock DRF has been created and saved to db successfully.")
