from memory_stream_old import MemoryObject
from utils import persistance_access
from gpt_api_old import AI_entities as AI


def retrieve_recent_memories(num_memories): #not useful for reflection anymore
    memory_stream = MemoryStreamAccess.MemoryStreamAccess()
    recent_memories = memory_stream.select_memories("spiky_memory", num_memories, "most recent creation")
    return recent_memories, memory_stream

def extract_memory_content(recent_memories):
    recent_memories_str = "\n".join([memory.processed_content for memory in recent_memories if memory.processed_content is not None])
    return recent_memories_str

def create_questions(recent_memories_str):
    questions = AI.create_question_AI(recent_memories_str)
    return questions

def create_and_store_reflections(questions, max_level_of_abstraction, memory_stream):
    reflections = []
    for question in questions:
        retrieved_context_id = memory_retrieval(question, number_of_retrievals_multiplier=20)
        retrieved_context_memory_objects = memory_stream.select_memories("spiky_memory",
                                                                         type_select="fetch rows",
                                                                         corresponding_IDs=retrieved_context_id)
        parsed_context = "\n".join([f"id: {single_memory.memoryID} text: {single_memory.reflection if single_memory.processed_content == '' else single_memory.processed_content}" for single_memory in retrieved_context_memory_objects])
        reflection_object = AI.reflection_AI(parsed_context)

        #reflection object is a list with the first object being the text and the second the ids of the memories that each insight is inspired by

        reflection_text = reflection_object[0] # "Klaus Mueller is deeply committed to his research; Klaus Mueller shows a keen interest in the topic of gentrification
        reflection_sources = reflection_object[1] # example :"insight 1: [id:1], [id:2], [id:8], [id:15]; insight 2: [id:1], [id:2], [id:3]
        reflection = MemoryObject.MemoryObject()
        reflections.append(reflection)
        memory_stream.add_memory(reflection,"spiky_memory")
    return reflections

def generate_reflections():
    num_memories_for_context = 30
    recent_memories, memory_stream = retrieve_recent_memories(num_memories_for_context)

    max_level_of_abstraction = max([memory.level_of_abstraction for memory in recent_memories])

    recent_memories_str = extract_memory_content(recent_memories)
    questions = create_questions(recent_memories_str)
    create_and_store_reflections(questions, max_level_of_abstraction, memory_stream)

#returns a list of IDs in the database
def memory_retrieval(situation, conditions="", number_of_retrievals_multiplier=1):
    approved = False
    top_recent_rows = []
    excluded_ids = []
    situation_embedding = AI.get_embedding(situation)
    num_cycles=0
    print("situation:"+situation)
    while not approved:
        num_cycles += 1
        print("cycle number :" + str(num_cycles))
        mydb = {"host": "localhost", "user": "root", "password": "Q144bughL0?Y@JFYxPA0", "database": "externalmemorydb"}
        index_name = "spiky-testing"
        memory_stream = MemoryStreamAccess.MemoryStreamAccess(mydb, index_name)

        top_k = max(40, number_of_retrievals_multiplier * 3)
        query_results = memory_stream.index.query(queries=[situation_embedding], top_k=top_k)

        # Exclude the bottom half of similar embeddings based on their scores
        half_point = len(query_results['results'][0]['matches']) // 2
        low_score_ids = [match['id'] for match in query_results['results'][0]['matches'][half_point:]]
        excluded_ids.extend(low_score_ids)

        # Filter out any results that are in the excluded_ids list
        similar_embeddings_IDs = [match['id'] for result in query_results['results'] for match in result['matches'] if
                                  match['id'] not in excluded_ids]

        query = "SELECT * FROM spiky_memory WHERE memory_id IN (%s)" % ', '.join(
            ['%s'] * len(similar_embeddings_IDs))
        memory_stream.mycursor.execute(query, tuple(similar_embeddings_IDs))
        rows = memory_stream.mycursor.fetchall()

        num_important_rows = max(10, number_of_retrievals_multiplier * 2)
        rows.sort(key=lambda row: row[5] if row[5] is not None else 1.0, reverse=True)
        top_important_rows = rows[:num_important_rows]
        top_important_rows.sort(key=lambda row: row[6], reverse=True)
        top_recent_rows = top_important_rows[:number_of_retrievals_multiplier]

        if conditions == "":
            approved = True
        elif conditions == "similarity":
            number_no_similarity=0
            for id in top_recent_rows:
                parsed_context_list = []
                retrieved_memory_objects = memory_stream.select_memories("spiky_memory",type_select="fetch rows",corresponding_IDs=[id[0]])  # Use the first element of 'id' as the ID
                for single_memory in retrieved_memory_objects:
                    formatted_string = f"text: {single_memory.reflection if single_memory.processed_content == '' else single_memory.processed_content}"
                    parsed_context_list.append(formatted_string)
                    print(formatted_string)
                is_similar = AI.similarity_approval_AI(situation, parsed_context_list)

                print(is_similar)
                if is_similar is False:
                    excluded_ids.append(id)
                    number_no_similarity+=1
            if number_no_similarity == 0:
                approved = True
        if num_cycles == 5:
            approved = True

    return [row[0] for row in top_recent_rows]



