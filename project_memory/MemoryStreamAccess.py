import mysql.connector
import pinecone
from memory_stream_old import MemoryObject
from utils import config_retrieval

config_manager = config_retrieval.ConfigManager()


class MemoryStreamAccess:
    def __init__(self):
        self.mysql_config = config_manager.mysql.as_dict()
        self.pinecone_index = config_manager.pinecone.index_name
        try:
            self.mydb = mysql.connector.connect(**self.mysql_config)
            self.mycursor = self.mydb.cursor()
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            self.mydb = None
            self.mycursor = None

        pinecone.init(api_key=config_manager.pinecone.api_key, environment=config_manager.pinecone.environment)
        try:
            if self.pinecone_index not in pinecone.list_indexes():
                pinecone.create_index(name=self.pinecone_index, dimension=1536, metric="cosine")
            self.index = pinecone.Index(index_name=self.pinecone_index)
        except Exception as e:
            print(f"Error with Pinecone: {e}")
            self.index = None

    def stream_close(self):
        if self.mycursor:
            self.mycursor.close()
        if self.mydb:
            self.mydb.close()

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
            self.mycursor.execute(query, tuple(corresponding_IDs_str))
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
