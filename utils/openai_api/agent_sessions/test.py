# import spacy
#
# # Load the spaCy model
# nlp = spacy.load("en_core_web_lg")
#
# # Sample text
# text = "Set aside some cash, like 50 bucks, just for design stuff."
#
# # Process the text
# doc = nlp(text)
#
# print("Named Entities:")
# # Extract and display entities
# for ent in doc.ents:
#     print(f" - {ent.text} ({ent.label_})")
#
# print("\nDependency Parsing and Part-of-Speech Tagging:")
# # Display token-level details: text, dependency relation, POS tag
# for token in doc:
#     print(f" - {token.text}: Dependency: {token.dep_}, POS Tag: {token.tag_}")
#
# print("Done")

import spacy

# Load the spaCy model
nlp = spacy.load("en_core_web_lg")

def process_text_and_present_chunks(text):
    doc = nlp(text)
    modified_text = text
    chunk_counter = 1
    chunk_mappings = {}

    # Process entities
    for ent in doc.ents:
        chunk_description = f"{ent.label_} related to '{ent.text}'"
        chunk_mappings[chunk_counter] = chunk_description
        modified_text = modified_text.replace(ent.text, f"<{chunk_counter}:{ent.text}>", 1)
        chunk_counter += 1

    # Process subjects
    for sent in doc.sents:
        for token in sent:
            if token.dep_ == "nsubj" or token.dep_ == "nsubjpass":
                # Collect immediate context (verb and direct object)
                verb = token.head
                object_ = [child for child in verb.children if child.dep_ in ["dobj", "attr", "prep"]]
                context = ' '.join([token.text for token in [token] + [verb] + object_])
                chunk_description = f"Subject '{token.text}' involved in '{context}'"
                chunk_mappings[chunk_counter] = chunk_description
                modified_text = modified_text.replace(token.text, f"<{chunk_counter}:{token.text}>", 1)
                chunk_counter += 1

    # Present the modified text with identified chunks
    print("Modified Text with Identified Chunks:")
    print(modified_text)

    # Present the chunks with references for user selection
    print("\nIdentified Chunks:")
    for i, desc in chunk_mappings.items():
        print(f"{i}. {desc}")

    # Example of user selection based on chunk numbers
    user_selection = input("Select chunks to use (e.g., 1, 2, 3): ")
    selected_chunks = user_selection.split(", ")

    # Process user selection
    selected_descriptions = [chunk_mappings[int(index)] for index in selected_chunks]

    print("\nSelected Chunks:")
    for desc in selected_descriptions:
        print(desc)

# Example text
text = """
Given the recent changes in tax legislation, it's crucial we review our budget allocations, 
especially concerning our R&D department. The new law, effective from next quarter, 
imposes stricter regulations on capital expenditure and will impact our R&D team of more than 25 people. 
How do you think this affects our planned investment in new technology and personnel over the next fiscal year?
"""

process_text_and_present_chunks(text)


from utils.openai_api.agent_sessions.trajectory_listener import TrajectoryListenerOntologyTermDetector
from project_memory import persistance_access, ontology_manager
from utils.openai_api.agent_sessions.trajectory import UserAIRound, UserMessage, AIMessage
from utils.openai_api.gpt_calling import GPTManager

memory_stream = persistance_access.MemoryStreamAccess()
gpt_manager = GPTManager()
my_ontology_manager = ontology_manager.OntologyManager(memory_stream=memory_stream, gpt_manager=gpt_manager)
term_detector = TrajectoryListenerOntologyTermDetector(memory_stream, my_ontology_manager)
user_message_content = (
    "Given the recent changes in tax legislation, it's crucial we review our budget allocations, "
    "especially concerning our R&D department. The new law, effective from next quarter, "
    "imposes stricter regulations on capital expenditure and will impact our R&D team of more than 25 people. "
    "How do you think this affects our planned investment in new technology and personnel over the next fiscal year?"
)

ai_message_content = (
    "The tax legislation changes indeed present a significant challenge, particularly with the tightened regulations "
    "on capital expenditure. It's imperative we reassess our financial strategy with our finance department to ensure "
    "compliance while still pushing forward with our R&D initiatives. Regarding our technology investments and hiring plans, "
    "we might need to explore more cost-effective solutions or seek external funding sources. Additionally, "
    "it's worth consulting with lawyers to navigate these new laws effectively. Time is of the essence, "
    "as these changes will impact us starting next quarter, so immediate action is required for the sake of stakeholders."
)

round = UserAIRound(UserMessage(user_message_content), AIMessage(ai_message_content))

term_detector.on_new_round(last_round=round)
