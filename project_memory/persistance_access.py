import uuid
import numpy as np
from pinecone import Pinecone, PodSpec
from pinecone import ServerlessSpec
import mysql.connector
from typing import Tuple, List
import re
import tempfile
import os
import json

import requests
from requests.auth import HTTPDigestAuth
from SPARQLWrapper import SPARQLWrapper, JSON, POST, GET, DIGEST
from owlready2 import *
import rdflib
from mysql.connector import Error as MySQLError
from mysql.connector import InterfaceError, DatabaseError
from collections import Counter
from sklearn.cluster import KMeans
from neo4j import GraphDatabase

from utils import config_retrieval
from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType

config_manager = config_retrieval.ConfigManager()


class Neo4jDatabaseManager:
    def __init__(self):
        self.uri = config_manager.neo4j.host_url
        self.user = config_manager.neo4j.user
        self.password = config_manager.neo4j.password
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        """Closes the database connection."""
        self.driver.close()

    def execute_queries(self, queries):
        results = []
        with self.driver.session() as session:
            # Ensure queries is a list for uniform processing
            if not isinstance(queries, list):
                queries = [queries]

            for query in queries:
                # Check if query is a tuple of (query_string, params)
                if isinstance(query, tuple) and len(query) == 2:
                    query_string, params = query
                    query_string = self.escape_special_characters(query_string)
                    # Use parameters to safely pass data
                    result = session.run(query_string, parameters=params).data()
                elif isinstance(query, str):
                    query = self.escape_special_characters(query)
                    # For simple string queries without parameters (not recommended for data insertion)
                    result = session.run(query).data()
                else:
                    raise TypeError("query must be a string or a tuple of (query_string, params)")
                results.extend(result)

        # Return logic remains unchanged
        if not results:
            return None
        return results[0] if len(results) == 1 else results

    def escape_special_characters(self, query):
        """
        Escapes special characters in a query string, avoiding double-escaping.
        """
        # Define patterns and their replacements
        patterns = {
            # Match a double quote not preceded by a backslash or preceded by an even number of backslashes
            r'(?<!\\)(?:\\\\)*"': r'\\"',
            # Match newline characters
            '\n': '\\n',
            # Add more patterns as needed
        }

        for pattern, replacement in patterns.items():
            query = re.sub(pattern, replacement, query)

        # Handle the specific case of '\\\\"' being transformed to '\\\"'
        # This reverses the transformation if it incorrectly escaped '\\\\"' (an already correctly escaped quote in JSON within the string)
        query = re.sub(r'\\\\\\"', r'\\"', query)

        return query

    def prepare_query(self, query_string, params):
        """
        Prepares a Cypher query string by embedding parameters directly into the query.

        Parameters:
        - query_string: The Cypher query string with placeholders for parameters.
        - params: A dictionary of parameters to embed into the query string.

        Returns:
        - A prepared query string with parameters embedded.
        """
        # Example implementation, adjust based on your parameter placeholders and escaping needs
        for key, value in params.items():
            safe_value = str(value).replace("'", "\\'")  # Simple escaping, adjust as necessary
            query_string = query_string.replace(f"${key}", safe_value)
        return query_string


class MemoryStreamAccess:  # TODO find a way to reduce the times this class is initialized, there could be too many connections and time lost
    def __init__(self):
        self.mysql_config = config_manager.mysql.as_dict()
        self.pinecone_controller = Pinecone(api_key=config_manager.pinecone.api_key)
        self.pinecone_index = config_manager.pinecone.index_name
        self.gpt_manager = GPTManager()
        self.virtuoso_auth = HTTPDigestAuth(config_manager.virtuoso.user, config_manager.virtuoso.password)
        self.virtuoso_endpoint = config_manager.virtuoso.sparql_endpoint
        try:
            self.mydb = mysql.connector.connect(**self.mysql_config)
            self.mycursor = self.mydb.cursor()
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            self.mydb = None
            self.mycursor = None

        print(self.pinecone_controller.list_indexes())
        try:
            if self.pinecone_index not in self.pinecone_controller.list_indexes().names():
                self.pinecone_controller.create_index(name=self.pinecone_index, dimension=1536, metric="cosine",
                                                      spec=PodSpec(environment='us-east-1'))
            self.index = self.pinecone_controller.Index(self.pinecone_index)
        except Exception as e:
            print(f"Error with Pinecone: {e}")
            self.index = None
        print(self.index.describe_index_stats())

    def query_sparql_endpoint(self, query, auth=None, update=False):
        endpoint = "http://localhost:8890/sparql-auth"

        # Setup for digest authentication
        if auth is None:
            auth = HTTPDigestAuth('dba', 'hhggRSe6DFZPcqze')

        # Ensure the endpoint returns JSON
        headers = {"Accept": "application/sparql-results+json"}  # This line is crucial
        if update:
            headers["Content-Type"] = "application/sparql-update"
        else:
            headers["Content-Type"] = "application/sparql-query"

        try:
            response = requests.post(endpoint, auth=auth, headers=headers, data=query)
            response.raise_for_status()

            # Parse the JSON response
            results = json.loads(response.text)  # This line converts the response text to a Python dictionary

            print(response.status_code, results)  # Adjust logging as needed

            return results  # Now this returns a dictionary as expected

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error performing SPARQL operation: {e.response.status_code} {e.response.text}")
        except Exception as e:
            print(f"Error performing SPARQL operation: {e}")

    def upload_ontology_to_virtuoso(self, graph_uri=None, auth=None, replace=True, file_path=None, file_contents=None):
        # Hardcoded endpoint for Virtuoso SPARQL Graph CRUD operations
        endpoint = self.virtuoso_endpoint + "/sparql-graph-crud"
        headers = {"Content-Type": "application/rdf+xml"}
        if auth is None:
            auth = HTTPDigestAuth('dba', 'hhggRSe6DFZPcqze')
        if graph_uri is None:
            graph_uri = "http://spikymind.org/data/myprojectontology"
        if file_path:
            with open(file_path, 'rb') as file:
                file_contents = file.read()
        else:
            if file_contents is None:
                print("No file path or contents provided.")
                return
        if replace:
            # Use PUT request to replace the target completely
            response = requests.put(f"{endpoint}?graph-uri={graph_uri}", data=file_contents, headers=headers, auth=auth)
        else:
            # Use POST request to append new information
            response = requests.post(f"{endpoint}?graph-uri={graph_uri}", data=file_contents, headers=headers,
                                     auth=auth)

        if response.status_code in [200, 201]:
            print("Ontology uploaded successfully.")
        else:
            print(f"Failed to upload ontology: {response.status_code} - {response.reason}")
            print(f"Response body: {response.text}")
            print(f"File contents: {file_contents}")

    def download_ontology_from_graph(self, graph_uri=None, save_path=None, auth=None):
        headers = {
            "Accept": "application/rdf+xml",  # Request RDF/XML response
            "Content-Type": "application/sparql-query"  # Indicate SPARQL query in the request body
        }
        # SPARQL CONSTRUCT query to retrieve all triples from the specified graph
        if graph_uri is None:
            graph_uri = "http://spikymind.org/data/myprojectontology"
        sparql_query = f"""
        CONSTRUCT {{
            ?s ?p ?o .
        }} WHERE {{
            GRAPH <{graph_uri}> {{
                ?s ?p ?o .
            }}
        }}
        """
        sparql_query_endpoint = self.virtuoso_endpoint + "/sparql-auth"
        if save_path is None:
            current_script_path = os.path.abspath(__file__)
            spiky_mind_dir = current_script_path.split('Spiky_Mind', 1)[0] + 'Spiky_Mind'

            # Now construct the path to the ontology file
            save_path = os.path.join(spiky_mind_dir, 'project_memory', 'ontologies', 'basic_ontology.rdf')
        try:
            response = requests.post(sparql_query_endpoint, data=sparql_query, headers=headers, auth=auth)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    file.write(response.content)
                print(f"Ontology data successfully downloaded and saved to {save_path}.")
            else:
                print(f"Failed to download ontology data: {response.status_code} - {response.reason}")
        except Exception as e:
            print(f"Error downloading ontology data: {e}")

    def execute_sparql_query(self, query, graph_uri=None, auth=None):
        """
        Executes a SPARQL query against a Virtuoso endpoint with fallback to CRUD endpoint for complex operations.

        Parameters:
        - query: The SPARQL query string.
        - graph_uri: The URI of the graph for CRUD operations. Defaults to a predefined graph URI if not specified.
        - auth: Authentication credentials, if required (default: None).

        Returns:
        A requests.Response object containing the query result or operation status, or None if the operation fails.

        Examples:
        - SELECT query:
          execute_sparql_query("SELECT * WHERE {?s ?p ?o} LIMIT 10")

        - INSERT query with fallback:
          execute_sparql_query("INSERT DATA { GRAPH <http://example.org> { <http://example.org/subject> <http://example.org/predicate> <http://example.org/object> . } }", "http://example.org")

        - DELETE query with fallback:
          execute_sparql_query("DELETE DATA { GRAPH <http://example.org> { <http://example.org/subject> <http://example.org/predicate> <http://example.org/object> . } }", "http://example.org")

        Note: For INSERT and DELETE operations, ensure your endpoint URL points to an update-capable URL if it is different.
        Note: Complex Insertion and Deletion operations may require the use of the Virtuoso SPARQL Graph CRUD endpoint.
        """
        if auth is None:
            auth = self.virtuoso_auth
        if graph_uri is None:
            graph_uri = "http://spikymind.org/data/myprojectontology"
        endpoint = self.virtuoso_endpoint + "/sparql-auth"
        # crud_endpoint = self.virtuoso_endpoint + "/sparql-graph-crud"
        headers = {"Accept": "application/sparql-results+json"} if query.strip().upper().startswith(
            ("SELECT", "ASK")) else {"Content-Type": "application/sparql-update"}

        method = requests.get if query.strip().upper().startswith(("SELECT", "ASK")) else requests.post
        response = method(endpoint, params={"query": query} if method == requests.get else None,
                          data=query if method == requests.post else None, headers=headers, auth=auth)

        # If the operation fails, return None
        if response.status_code not in range(200, 300):
            print("Operation failed. Status code:", response.status_code)
            print(" Response Error:", response.reason)
            success = False
            return success

        return response

    def perform_reasoning(self, graph_uri=None, save_path=None):
        # Download the ontology from the graph URI if not already available locally
        if save_path is None:
            current_script_path = os.path.abspath(__file__)
            spiky_mind_dir = current_script_path.split('Spiky_Mind', 1)[0] + 'Spiky_Mind'

            # Now construct the path to the ontology file
            save_path = os.path.join(spiky_mind_dir, 'project_memory', 'ontologies', 'reasoning_ontology.rdf')

        if not os.path.exists(save_path):
            self.download_ontology_from_graph(graph_uri=graph_uri, save_path=save_path, auth=self.virtuoso_auth)

        # Load the ontology into Owlready2
        onto = get_ontology(f"file://{save_path}").load()

        # Perform reasoning
        with onto:
            sync_reasoner_hermit(infer_property_values=True)

        # Save the reasoned ontology back to the same file or a new file
        reasoned_save_path = save_path.replace('.rdf', '_is_reasoned.rdf')
        onto.save(file=reasoned_save_path)

        print(f"Reasoning completed. Reasoned ontology saved to {reasoned_save_path}.")

    def similarity_comparison(self, comparison_list_id: List[str], single_id: str, top_k: int = 5) -> List[
        Tuple[str, float]]:
        """
        Compares a list of parent IDs against a single ID to find the top k most similar parents.

        :param parent_ids: List of parent IDs to compare.
        :param single_id: The single ID to compare against the list.
        :param top_k: The number of top similar items to return.
        :return: A list of tuples containing the parent ID and its similarity score, sorted by similarity.
        """
        # Retrieve vectors for all IDs using the whitelist function
        all_ids = comparison_list_id + [single_id]
        vectors, missing_ids = self.get_vectors_whitelist(all_ids)

        if missing_ids:
            print(f"Missing vectors for IDs: {missing_ids}")

        # Extract the vector for the single ID
        single_vector = np.array(vectors[single_id])

        # Calculate similarity scores
        similarities = []
        for parent_id in comparison_list_id:
            parent_vector = np.array(vectors[parent_id])
            similarity_score = np.dot(single_vector, parent_vector) / (
                    np.linalg.norm(single_vector) * np.linalg.norm(parent_vector))  # Cosine similarity
            similarities.append((parent_id, similarity_score))

        # Sort by similarity score in descending order and return top k results
        top_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]

        return top_similarities

    def text_similarity(self, text1: str, text2: str) -> float:
        """
        Computes the similarity score between two pieces of text by vectorizing them and calculating the cosine similarity.

        :param text1: The first piece of text to compare.
        :param text2: The second piece of text to compare.
        :return: A float representing the similarity score between the two texts.
        """
        # Vectorize the first piece of text
        vectorizer_agent = self.gpt_manager.create_agent(model=ModelType.TEXT_EMBEDDING_ADA, messages="")
        vectorizer_agent.update_agent(messages=text1)
        vectorizer_agent.run_agent()
        vector1 = vectorizer_agent.get_vector()

        # Vectorize the second piece of text
        vectorizer_agent.update_agent(messages=text2)
        vectorizer_agent.run_agent()
        vector2 = vectorizer_agent.get_vector()

        # Calculate cosine similarity between the two vectors
        similarity_score = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))

        return similarity_score

    def stream_close(self):
        if self.mycursor:
            self.mycursor.close()
        if self.mydb:
            self.mydb.close()

    def query_similar_vectors_with_text(self, vector: List[float], k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Queries the Pinecone database for the top k most similar vectors to the given vector and retrieves their associated text from MySQL.

        Parameters:
            vector (List[float]): The query vector.
            k (int): The number of similar vectors to retrieve.

        Returns:
            List[Tuple[str, float, str]]: A list of tuples, where each tuple contains the ID of a similar vector, its similarity score, and its associated text.
        """
        similar_vectors = self.query_similar_vectors(vector, k)
        if not similar_vectors:
            return []

        # Extract vector IDs from the query results
        vector_ids = [vector_id for vector_id, _ in similar_vectors]

        # Fetch the associated text for each vector ID from MySQL
        vector_texts = self.fetch_vector_texts_by_ids(vector_ids)

        # Combine the IDs, scores, and texts into a single list of tuples
        combined_results = []
        for vector_id, score in similar_vectors:
            text = vector_texts.get(vector_id, "Text not found.")
            combined_results.append((vector_id, score, text))

        return combined_results

    def query_similar_vectors(self, vector: List[float], k: int = 5, strip_UUID: bool = False) -> List[
        Tuple[str, float]]:
        """
        Queries the Pinecone database for the top k most similar vectors to the given vector.

        Parameters:
            vector (List[float]): The query vector.
            k (int): The number of similar vectors to retrieve.
            strip_UUID (bool): Whether to strip UUIDs from the returned vector IDs.

        Returns:
            List[Tuple[str, float]]: A list of tuples, where each tuple contains the ID of a similar vector and its similarity score.
        """
        if not self.index:
            print("Pinecone index is not initialized.")
            return []

        try:
            # Query Pinecone for the top k most similar vectors
            query_result = self.index.query(vector=vector, top_k=k)
            matches = query_result['matches']

            # Extract and process the IDs and scores of the top k matches
            if strip_UUID:
                similar_vectors = [(self.strip_uuid(match['id']), match['score']) for match in matches]
            else:
                similar_vectors = [(match['id'], match['score']) for match in matches]
            return similar_vectors

        except Exception as e:
            print(f"Error querying Pinecone for similar vectors: {e}")
            return []

    def strip_uuid(self, identifier: str) -> str:
        """
        Strips the UUID from the identifier using a regex pattern, if present.

        Parameters:
            identifier (str): The identifier potentially containing a UUID.

        Returns:
            str: The identifier with the UUID stripped if it was present.
        """
        # Regex to identify a UUID appended at the end of the identifier
        # UUIDs typically look like: 123e4567-e89b-12d3-a456-426614174000
        # The pattern assumes the UUID is at the end and possibly preceded by an underscore or other separator
        pattern = r'(.*)_[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        match = re.match(pattern, identifier)
        if match:
            # Return the part before the UUID
            return match.group(1)
        else:
            # Return the original identifier if no UUID is found
            return identifier

    def get_vectors_whitelist(self, whitelist):
        """
        Retrieve vectors from the Pinecone database based on a whitelist of IDs.

        Parameters:
            whitelist (list): List of vector IDs to include in retrieval.

        Returns:
            A tuple containing a dictionary with vector names as keys and vectors as values,
            and a list of IDs that did not return any data.
        """
        if not self.index:
            print("Pinecone index is not initialized.")
            return {}, []

        batch_size = 250
        all_vectors = {}
        missing_ids = []

        for i in range(0, len(whitelist), batch_size):
            batch = whitelist[i:i + batch_size]
            id_counts = Counter(batch)
            duplicates = [id for id, count in id_counts.items() if count > 1]

            if duplicates:
                print(f"Duplicate IDs in batch {i // batch_size + 1}: {duplicates}")

            try:
                response = self.index.fetch(ids=batch)
                returned_vectors = response.get('vectors', {})

                for id in batch:
                    if id not in returned_vectors:
                        missing_ids.append(id)

                for vector_id, vector_data in returned_vectors.items():
                    vector_values = vector_data.get('values', [])
                    all_vectors[vector_id] = vector_values
                    print(f"Retrieved vector ID: {vector_id}")

            except Exception as e:
                print(f"Error retrieving batch from Pinecone: {e}")

        return all_vectors, missing_ids

    def group_vectors(self, whitelist, k=5):
        """
        Retrieves vectors based on a whitelist and groups them into k clusters.

        Parameters:
            whitelist (list): List of vector names to include in retrieval.
            k (int): The number of groups to create.

        Returns:
            List of lists, where each sublist contains the names of vectors in that group.
        """
        vectors = self.get_vectors_whitelist(whitelist)

        if len(vectors) < k:
            print("Number of vectors is less than the number of groups.")
            return []

        # Extract the vector names and vectors
        names, vectors = zip(*vectors.items())
        vectors_matrix = np.array(vectors)

        # Perform K-Means clustering
        kmeans = KMeans(n_clusters=k, random_state=0).fit(vectors_matrix)
        labels = kmeans.labels_

        # Group vector names based on cluster labels
        grouped_vectors = [[] for _ in range(k)]
        for name, label in zip(names, labels):
            grouped_vectors[label].append(name)

        return grouped_vectors

    def add_to_pinecone(self, vector_name, vector_text, return_id=False):
        """
        Adds or updates a single entry in the Pinecone database and MySQL.

        Parameters:
            vector_name (str): The name of the vector.
            vector_text (str): The description of the vector.
            return_id (bool): If True, returns the ID of the vector added to Pinecone.

        Returns:
            The ID of the vector added to Pinecone if return_id is True. Otherwise, returns None.
        """
        if not self.index:
            print("Pinecone index is not initialized.")
            return None

        # Replace spaces with underscores in vector_name
        vector_name = vector_name.replace(" ", "_")

        # Generate a UUID for the vector and combine it with the vector_name
        vector_id = vector_name + "-" + str(uuid.uuid4())

        # Replace spaces with underscores in combined_text
        combined_text = (vector_name + "." + vector_text).replace(" ", "_")

        # Generate the vector using the embedding agent
        embedding_agent = self.gpt_manager.create_agent(model=ModelType.TEXT_EMBEDDING_ADA, messages=combined_text)
        embedding_agent.run_agent()
        vector = embedding_agent.get_vector()

        # Insert into MySQL
        try:
            self.add_to_mysql("vector_storage", {'id': vector_id, 'name': vector_name, 'content': vector_text})
            print(f"Vector with ID '{vector_id}' added to MySQL. content:{combined_text}")

            # Proceed with Pinecone insertion only if MySQL insertion is successful
            try:
                self.index.upsert(vectors=[(vector_id, vector)])
                print(f"Vector with ID '{vector_id}' added or updated in Pinecone.")
                if return_id:
                    return vector_id
            except Exception as e:
                print(f"Error inserting into Pinecone: {e}")

        except Exception as e:
            print(f"Error inserting into MySQL: {e}")

        return None if not return_id else vector_id

    def delete_from_pinecone(self, vector_ids=None, delete_all=False):
        """
        Deletes entries from the Pinecone database using their IDs or deletes all entries if delete_all is True,
        processing in batches of 500 entries at a time.

        Parameters:
            vector_ids (str or list, optional): The ID or list of IDs of the vectors to be deleted.
            delete_all (bool): If True, deletes all entries based on IDs fetched from the MySQL database.
        """
        if not self.index:
            print("Pinecone index is not initialized.")
            return

        def delete_batch(ids):
            """Deletes a batch of vectors from Pinecone."""
            try:
                self.index.delete(ids=ids)
                print(f"Vectors with IDs {ids} have been deleted from Pinecone.")
            except Exception as e:
                print(f"Error deleting from Pinecone: {e}")

        if delete_all:
            # Fetch all IDs from MySQL and delete corresponding vectors from Pinecone
            if self.mydb and self.mycursor:
                try:
                    self.mycursor.execute("SELECT id FROM vector_storage")
                    all_ids = [item[0] for item in self.mycursor.fetchall()]
                    for i in range(0, len(all_ids), 500):
                        batch_ids = all_ids[i:i + 500]
                        delete_batch(batch_ids)
                        self.delete_from_mysql(table_name="vector_storage", delete_all=True)
                    else:
                        print("No vectors found to delete in Pinecone.")
                except mysql.connector.Error as err:
                    print(f"Error fetching IDs from MySQL: {err}")
            else:
                print("MySQL database is not initialized.")
            return

        if vector_ids:
            if isinstance(vector_ids, str):
                vector_ids = [vector_ids]  # Convert to list if a single ID is provided
            for i in range(0, len(vector_ids), 500):
                batch_ids = vector_ids[i:i + 500]
                delete_batch(batch_ids)

    def delete_from_mysql(self, table_name, where_clause=None, delete_all=False):
        """
        Deletes entries from a specified MySQL table based on a given condition or deletes all entries if delete_all is True.

        Parameters:
            table_name (str): The name of the MySQL table.
            where_clause (str, optional): The SQL WHERE clause specifying the condition for deletion.
            delete_all (bool): If True, deletes all entries in the specified MySQL table.
        """
        if not self.mydb or not self.mycursor:
            print("MySQL database is not initialized.")
            return

        if delete_all:
            try:
                query = f"DELETE FROM {table_name}"
                self.mycursor.execute(query)
                self.mydb.commit()
                print(f"All records have been deleted from {table_name}.")
            except mysql.connector.Error as err:
                print(f"Error deleting all records from {table_name}: {err}")
            return

        if where_clause:
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            try:
                self.mycursor.execute(query)
                self.mydb.commit()
                print(f"Records satisfying the condition '{where_clause}' have been deleted from {table_name}.")
            except mysql.connector.Error as err:
                print(f"Error deleting records from {table_name}: {err}")

    def add_to_mysql(self, table_name, data):
        """
        Adds or updates data in a specified MySQL table.

        Parameters:
            table_name (str): The name of the MySQL table.
            data (dict): Dictionary containing data to be inserted or updated. Keys should match column names.
        """
        if not self.mydb or not self.mycursor:
            print("MySQL database is not initialized.")
            return

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        update_assignments = ', '.join([f"{col} = VALUES({col})" for col in data.keys()])
        values = tuple(data.values())

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_assignments}"

        try:
            self.mycursor.execute(query, values)
            self.mydb.commit()
            print(f"Data added or updated in MySQL table '{table_name}'.")
        except mysql.connector.Error as err:
            print(f"Error inserting into MySQL: {err}")

    def get_id_by_column(self, value, column_name="name"):
        """
        Retrieves the ID from the MySQL database based on a specified column's value.

        Parameters:
            value (str): The value to search for in the database.
            column_name (str): The name of the column to search in. Defaults to 'name'.

        Returns:
            The ID associated with the value in the specified column, or None if not found.
        """
        if not self.mydb:
            print("MySQL database is not initialized.")
            return None

        try:
            with self.mydb.cursor() as cursor:
                query = f"SELECT id FROM vector_storage WHERE {column_name} LIKE %s"
                cursor.execute(query, (f"%{value}%",))
                results = cursor.fetchall()
                return results[0][0] if results else None

        except InterfaceError as ie:
            print(f"MySQL Interface Error: {ie}")
        except DatabaseError as de:
            print(f"MySQL Database Error: {de}")
        except MySQLError as err:
            print(f"MySQL Error: {err}")
        except Exception as e:
            print(f"General Error: {e}")

        return None

    def fetch_vector_texts_by_ids(self, vector_ids: List[str]) -> dict:
        """
        Fetches the associated text for a list of vector IDs from MySQL.

        Parameters:
            vector_ids (List[str]): The list of vector IDs.

        Returns:
            dict: A dictionary mapping vector IDs to their associated text.
        """
        if not self.mydb or not self.mycursor:
            print("MySQL database is not initialized.")
            return {}

        vector_texts = {}
        try:
            # Construct a query to fetch the text for each vector ID
            format_strings = ','.join(['%s'] * len(vector_ids))
            query = f"SELECT id, content FROM vector_storage WHERE id IN ({format_strings})"
            self.mycursor.execute(query, tuple(vector_ids))
            for vector_id, text in self.mycursor.fetchall():
                vector_texts[vector_id] = text
        except Exception as e:
            print(f"Error fetching vector texts from MySQL: {e}")

        return vector_texts


"""
    def add_memory(self, memory_object, embedding, memory_table="spiky_memory"):
        # If child_ids is not None, convert it to a comma-separated string
        if memory_object.child_ids is not None:
            child_ids_str = ','.join(map(str, memory_object.child_ids))
        else:
            child_ids_str = None

        # Add memory to MySQL database
        add_memory = (f"INSERT INTO {memory_table} "
                      "(memory_id, content, child_ids, parent_id, access_level, created_date, modified_date, last_visited_date, nb_of_visits,level_of_abstraction) "
                      "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
        data_memory = (
            memory_object.memory_id, memory_object.content, child_ids_str, memory_object.parent_id,
            memory_object.access_level, memory_object.created_date, memory_object.modified_date,
            memory_object.last_visited_date, memory_object.nb_of_visits, memory_object.level_of_abstraction)

        try:
            self.mycursor.execute(add_memory, data_memory)
            self.mydb.commit()
            self.index.upsert([(memory_object.memory_id, embedding)])
        except Exception as e:
            error_msg = f"Error occurred while adding memory to {memory_table}. Details: {str(e)}"
            raise Exception(error_msg)

    def select_memories(self, table_name, num_select=1, type_select="most recent creation", corresponding_IDs=None,
                        level_of_abstraction=None):
        if corresponding_IDs is None:
            corresponding_IDs = []
        mydb = {"host": "localhost", "user": "root", "password": "Q144bughL0?Y@JFYxPA0",
                "database": "externalmemorydb"}
        index_name = "spiky-testing"
        memory_stream = MemoryStreamAccess(mydb, index_name)
        # If you want to select from multiple tables, you would need to modify the SQL query.
        # For example, if you have two tables `table1` and `table2` with the same columns, and you want to select the most recent rows from both tables, you could use a query like this:
        # self.mycursor.execute(f"SELECT * FROM (SELECT * FROM table1 UNION ALL SELECT * FROM table2) AS combined_table ORDER BY created_date DESC LIMIT {X}")
        memory_objects = []
        if type_select == "most recent creation":
            # Execute the SQL query
            query = f"SELECT * FROM {table_name} ORDER BY created_date DESC LIMIT {num_select}"
            self.mycursor.execute(query)
            rows = self.mycursor.fetchall()

            for row in rows:
                memory_object = MemoryObject.MemoryObject(retrieved_memory=True)
                memory_object.memory_id = row[0]
                memory_object.content = row[1]
                memory_object.child_ids = row[2]
                memory_object.parent_id = row[3]
                memory_object.access_level = row[4]
                memory_object.created_date = row[5]
                memory_object.modified_date = row[6]
                memory_object.last_visited_date = row[7]
                memory_object.nb_of_visits = row[8]
                memory_object.level_of_abstraction = row[9]
                memory_objects.append(memory_object)


        elif type_select == "most recent visited":
            # Execute the SQL query
            self.mycursor.execute(f"SELECT * FROM {table_name} ORDER BY last_visited_date DESC LIMIT {num_select}")
            rows = self.mycursor.fetchall()

            for row in rows:
                memory_object = MemoryObject.MemoryObject(retrieved_memory=True)
                memory_object.memory_id = row[0]
                memory_object.content = row[1]
                memory_object.child_ids = row[2]
                memory_object.parent_id = row[3]
                memory_object.access_level = row[4]
                memory_object.created_date = row[5]
                memory_object.modified_date = row[6]
                memory_object.last_visited_date = row[7]
                memory_object.nb_of_visits = row[8]
                memory_object.level_of_abstraction = row[9]
                memory_objects.append(memory_object)


        elif type_select == "fetch rows":
            # Convert UUIDs to strings
            corresponding_IDs_str = [str(uuid) for uuid in corresponding_IDs]

            # Create the query string with placeholders
            placeholders = ', '.join(['%s'] * len(corresponding_IDs_str))
            query = f"SELECT * FROM {table_name} WHERE memory_id IN ({placeholders})"

            # Execute the query
            memory_stream.mycursor.execute(query, tuple(corresponding_IDs_str))
            rows = memory_stream.mycursor.fetchall()

            for row in rows:
                memory_object = MemoryObject.MemoryObject(retrieved_memory=True)
                memory_object.memory_id = row[0]
                memory_object.content = row[1]
                memory_object.child_ids = row[2]
                memory_object.parent_id = row[3]
                memory_object.access_level = row[4]
                memory_object.created_date = row[5]
                memory_object.modified_date = row[6]
                memory_object.last_visited_date = row[7]
                memory_object.nb_of_visits = row[8]
                memory_object.level_of_abstraction = row[9]
                memory_objects.append(memory_object)

        elif type_select == "unlinked_at_level":
            if level_of_abstraction is None:
                raise ValueError("For unlinked_at_level type, level_of_abstraction must be provided.")
            query = f"SELECT * FROM {table_name} WHERE level_of_abstraction = %s AND parent_id IS NOT NULL"
            self.mycursor.execute(query, (level_of_abstraction,))
            rows = self.mycursor.fetchall()
            for row in rows:
                memory_object = MemoryObject.MemoryObject(retrieved_memory=True)
                memory_object.memory_id = row[0]
                memory_object.content = row[1]
                memory_object.child_ids = row[2]
                memory_object.parent_id = row[3]
                memory_object.access_level = row[4]
                memory_object.created_date = row[5]
                memory_object.modified_date = row[6]
                memory_object.last_visited_date = row[7]
                memory_object.nb_of_visits = row[8]
                memory_object.level_of_abstraction = row[9]
                memory_objects.append(memory_object)

        return memory_objects

    def modify_memory(self, memory_id, new_memory):
        # Update the action_memory table
        update_query = """
"""
        UPDATE spiky_memory
        SET content = %s,
            child_ids = %s,
            parent_id = %s,
            subject = %s,
            memory_type = %s,
            access_level = %s,
            created_date = %s,
            modified_date = %s,
            last_visited_date = %s,
            nb_of_visits = %s
        WHERE memory_id = %s
        """
"""
        data_memory = (
            new_memory.content,
            new_memory.child_ids,
            new_memory.parent_id,
            new_memory.subject,
            new_memory.memory_type,
            new_memory.access_level,
            new_memory.created_date,
            new_memory.modified_date,
            new_memory.last_visited_date,
            new_memory.nb_of_visits,
            memory_id
        )

        self.mycursor.execute(update_query, data_memory)
        self.mydb.commit()

    def delete_memory(self, memory_IDs, table_name):
        # Delete from MySQL
        for memory_ID in memory_IDs:
            sql = f"DELETE FROM {table_name} WHERE memory_id = %s"
            val = (memory_ID,)
            self.mycursor.execute(sql, val)
        self.mydb.commit()

        # Delete from Pinecone
        self.index.delete(ids=memory_IDs)

        print(f"Memories {memory_IDs} deleted from MySQL and Pinecone.")
"""
