import uuid
from collections import Counter
import numpy as np
from sklearn.cluster import KMeans
import mysql.connector
from mysql.connector import Error as MySQLError
from mysql.connector import InterfaceError, DatabaseError
import pinecone

from utils import config_retrieval
from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType
from spiky_module.Research.test_graph_creation import Neo4jGraphHandler

config_manager = config_retrieval.ConfigManager()


class MemoryStreamAccess:
    def __init__(self):
        self.mysql_config = config_manager.mysql.as_dict()
        self.pinecone_index = config_manager.pinecone.index_name
        self.neo4j_handler = Neo4jGraphHandler()
        self.gpt_manager = GPTManager()
        try:
            self.mydb = mysql.connector.connect(**self.mysql_config)
            self.mycursor = self.mydb.cursor()
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            self.mydb = None
            self.mycursor = None

        pinecone.init(api_key=config_manager.pinecone.api_key, environment=config_manager.pinecone.environment)
        print(pinecone.list_indexes())
        try:
            if self.pinecone_index not in pinecone.list_indexes():
                pinecone.create_index(name=self.pinecone_index, dimension=1536, metric="cosine")
            self.index = pinecone.Index(index_name=self.pinecone_index)
        except Exception as e:
            print(f"Error with Pinecone: {e}")
            self.index = None
        print(self.index.describe_index_stats())

    def stream_close(self):
        if self.mycursor:
            self.mycursor.close()
        if self.mydb:
            self.mydb.close()



    def get_vectors_whitelist(self, whitelist):
        """
        Retrieve vectors from the Pinecone database based on a whitelist of IDs.

        Parameters:
            whitelist (list): List of vector IDs to include in retrieval.

        Returns:
            A dictionary with vector names as keys and vectors as values,
            and a list of IDs that did not return any data.
        """
        if not self.index:
            print("Pinecone index is not initialized.")
            return {}

        batch_size = 250
        all_vectors = {}
        missing_ids = []

        for i in range(0, len(whitelist), batch_size):
            batch = whitelist[i:i + batch_size]

            # Count occurrences of each ID
            id_counts = Counter(batch)
            duplicates = [id for id, count in id_counts.items() if count > 1]

            # Print duplicate IDs if any
            if duplicates:
                print(f"Duplicate IDs in batch {i // batch_size + 1}: {duplicates}")

            try:
                response = self.index.fetch(ids=batch)
                returned_vectors = response.get('vectors', {})

                # Check for missing IDs in this batch
                for id in batch:
                    if id not in returned_vectors:
                        missing_ids.append(id)

                for vector_id, vector_data in returned_vectors.items():
                    vector_values = vector_data.get('values', [])
                    all_vectors[vector_id] = vector_values
                    print(f"Retrieved vector ID: {vector_id}")

            except Exception as e:
                print(f"Error retrieving batch from Pinecone: {e}")

        return all_vectors

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

    def add_to_pinecone(self, vector_name, vector_text):
        """
        Adds or updates a single entry in the Pinecone database and MySQL.

        Parameters:
            vector_name (str): The name of the vector.
            vector_text (str): The description of the vector.
        """
        if not self.index:
            print("Pinecone index is not initialized.")
            return

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
            except Exception as e:
                print(f"Error inserting into Pinecone: {e}")

        except Exception as e:
            print(f"Error inserting into MySQL: {e}")

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
