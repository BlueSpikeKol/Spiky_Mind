from project_memory.persistance_access import MemoryStreamAccess
vector_name = 'test'
vector_text = "This is a test, please do not consider important"
vector_id = vector_name + 'Engineering a DC Motor > Documentation > User Guide > Maintenance > Belt/Chain Tensioning-830511a7-2605-4abd-93e1-77b770d07365'
mem = MemoryStreamAccess()
print()
#mem.add_to_pinecone(vector_name=vector_name,vector_text=vector_text)
#thing = mem.get_vectors_whitelist(whitelist=[vector_id])

mem.delete_from_pinecone(delete_all=True)
print('this is important test')
#print(thing)

#mem.delete_from_pinecone(vector_ids=vector_id)