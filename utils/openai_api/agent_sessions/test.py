import spacy

nlp = spacy.load('en_core_web_lg')

text = "Given the recent changes in tax legislation, reviewing our budget allocations is crucial, especially for our R&D department. This department will see the new law, effective from next quarter, imposing stricter regulations on capital expenditure. It will significantly impact the team, which consists of more than 25 people. How do you think this affects our planned investment in new technology and personnel over the next fiscal year?"
test_text = "Despite the heavy rain that was falling intermittently, she has, after much deliberation, decided to embark on the journey, knowing well that it could, without warning, turn more perilous."
test_2 = "The flowers smell fragrant in the garden. The orchids were responsible for this pleasant fragrance."

complete_text = """Given the recent changes in tax legislation, reviewing our budget allocations is crucial,
especially for our R&D department. This department will see the new law, effective from next quarter,
imposing stricter regulations on capital expenditure. It will significantly impact the team,
which consists of more than 25 people. How do you think this affects our planned investment in 
new technology and personnel over the next fiscal year?"""

response_to_legislation_changes = """
As head of R&D, I recognize the impact of recent tax legislation on our strategy.
The new law introduces strict regulations on capital expenditure effective next quarter, directly affecting 
our advanced robotics initiative and lab expansion. This necessitates a shift towards software innovation and remote 
collaboration tools, less affected by these constraints. To support our team of over 25, we're seeking grants and 
partnerships to sustain our technology and personnel investments. Our department's agility will be key in leveraging 
these changes to continue leading in innovation.
"""


def print_tokens_with_head(text):
    doc = nlp(text)
    important_dict = {}
    for token in doc:
        print(f"{token.text} ({token.pos_})--({token.dep_})", end="")
        print(f" -----> Head: {token.head.text} ({token.head.pos_})", end="")

        if token.pos_ == "NOUN" or token.pos_ == "VERB" or token.pos_ == "ADJ" or token.pos_ == "DET":
            important_dict[token.text] = token.pos_
            # important_list.append(token.text)
            # important_list.append(token.pos_)
            print()
        else:
            print()
    print("Important words: ")
    print(important_dict.keys())


#
# Text to process

def create_object_clusters(doc):
    object_clusters = {}
    for i, token in enumerate(doc):
        if token.pos_ == 'NOUN':
            if i > 0 and doc[i - 1].pos_ == 'NOUN':
                # Add the current token object to the cluster of the previous noun
                object_clusters.setdefault(i - 1, []).append(token)
            else:
                # Create a new cluster with the current token object
                object_clusters.setdefault(i, []).append(token)

    for token in doc:
        if token.pos_ == 'ADJ' or token.pos_ == 'DET':
            head = token.head
            if head.pos_ == 'NOUN':
                # Iterate over cluster IDs to find the head token's index and add the modifier
                for cluster_id in object_clusters:
                    if head in object_clusters[cluster_id]:
                        object_clusters[cluster_id].append(token)
                        break

    return object_clusters


def create_action_modifier_clusters(doc):
    action_modifier_clusters = {}
    aux_without_verbs = {}

    for i, token in enumerate(doc):
        if token.pos_ == 'VERB':
            action_modifier_clusters[i] = [token]
        elif token.pos_ == 'AUX':
            # Temporarily store AUX tokens that might not have a verb parent
            aux_without_verbs[i] = token

    # Adding modifiers to their respective verb clusters
    for token in doc:
        if token.pos_ in ['ADJ', 'DET']:
            head = token.head
            if head.pos_ == 'VERB':
                # Find the verb's cluster and add the modifier
                for cluster_id in action_modifier_clusters:
                    if head in action_modifier_clusters[cluster_id]:
                        action_modifier_clusters[cluster_id].append(token)
                        break

    # Process AUX tokens with respect to their parent verb or as standalone clusters
    for i, token in aux_without_verbs.items():
        head = token.head
        if head.pos_ == 'VERB':
            # If AUX modifies a verb, add it to that verb's cluster
            for cluster_id in action_modifier_clusters:
                if head in action_modifier_clusters[cluster_id]:
                    action_modifier_clusters[cluster_id].append(token)
                    break
        else:
            # If the AUX token does not modify a verb, it becomes its own cluster
            action_modifier_clusters[i] = [token]

    return action_modifier_clusters


def add_acomp_to_clusters(doc, object_clusters, action_modifier_clusters):
    for token in doc:
        if token.dep_ == 'acomp':
            head = token.head
            # Check if the head is a verb and belongs to an action modifier cluster
            added = False
            for cluster_id, cluster in action_modifier_clusters.items():
                if head in cluster:
                    action_modifier_clusters[cluster_id].append(token)
                    added = True
                    break
            # If not added to an action cluster, check if it belongs to an object cluster
            if not added:
                for cluster_id, cluster in object_clusters.items():
                    if head in cluster:
                        object_clusters[cluster_id].append(token)
                        break

    # Return the updated clusters
    return object_clusters, action_modifier_clusters


def create_linking_clusters(doc, object_clusters, action_modifier_clusters):
    linking_cluster = []

    for token in doc:
        if token.pos_ == 'ADP' or token.dep_ == 'prep':
            sender_cluster = None
            target_cluster = None

            # Find the sender_cluster by comparing token objects directly
            for cluster_id, cluster in object_clusters.items():
                if token.head in cluster:
                    sender_cluster = cluster
                    break

            if sender_cluster is None:
                for cluster_id, cluster in action_modifier_clusters.items():
                    if token.head in cluster:
                        sender_cluster = cluster
                        break

            # Find the target_cluster by comparing token objects directly
            for other_token in doc:
                if other_token != token and other_token.head == token:
                    for cluster_id, cluster in object_clusters.items():
                        if other_token in cluster:
                            target_cluster = cluster
                            break

                    if target_cluster is None:
                        for cluster_id, cluster in action_modifier_clusters.items():
                            if other_token in cluster:
                                target_cluster = cluster
                                break

            if sender_cluster is not None and target_cluster is not None:
                linking_cluster.append({
                    'link_token': token,
                    'sender_cluster': sender_cluster,
                    'target_cluster': target_cluster
                })

    return linking_cluster


if __name__ == "__main__":
    print("Test 1:")
    print_tokens_with_head(test_text)
    # print()

    # print("Test 2:")
    # print_tokens_with_head(test_2)
    # print()
    #
    # test_3="He found the book on the top shelf interesting."
    # print("Test 3:")
    # print_tokens_with_head(test_3)
    # print()

    # print("Test 4:")
    # print_tokens_with_head(complete_text)
    # print_tokens_with_head(response_to_legislation_changes)
    # print()

    # Process the text with spaCy
    """
    doc = nlp(complete_text + response_to_legislation_changes)
    # Assuming 'doc' is already processed by spaCy

    object_clusters = create_object_clusters(doc)
    action_modifier_clusters = create_action_modifier_clusters(doc)
    object_clusters, action_modifier_clusters = add_acomp_to_clusters(doc, object_clusters, action_modifier_clusters)
    linking_clusters = create_linking_clusters(doc, object_clusters, action_modifier_clusters)

    # Now you have all three types of clusters ready for further analysis or processing.
    for link in linking_clusters:
        print(link)
    # Print the clusters
    print("Object Clusters:")
    for cluster in object_clusters.values():
        print(cluster)

    print("\nAction Modifier Clusters:")
    for cluster in action_modifier_clusters.values():
        print(cluster)

    print()
    """

# from utils.openai_api.agent_sessions.trajectory_listener import TrajectoryListenerOntologyTermDetector
# from project_memory import persistance_access, ontology_manager
# from utils.openai_api.agent_sessions.trajectory import UserAIRound, UserMessage, AIMessage
# from utils.openai_api.gpt_calling import GPTManager
#
# memory_stream = persistance_access.MemoryStreamAccess()
# gpt_manager = GPTManager()
# my_ontology_manager = ontology_manager.OntologyManager(memory_stream=memory_stream, gpt_manager=gpt_manager)
# term_detector = TrajectoryListenerOntologyTermDetector(memory_stream, my_ontology_manager)
# user_message_content = (
#     "Given the recent changes in tax legislation, it's crucial we review our budget allocations, "
#     "especially concerning our R&D department. The new law, effective from next quarter, "
#     "imposes stricter regulations on capital expenditure and will impact our R&D team of more than 25 people. "
#     "How do you think this affects our planned investment in new technology and personnel over the next fiscal year?"
# )
#
# ai_message_content = (
#     "The tax legislation changes indeed present a significant challenge, particularly with the tightened regulations "
#     "on capital expenditure. It's imperative we reassess our financial strategy with our finance department to ensure "
#     "compliance while still pushing forward with our R&D initiatives. Regarding our technology investments and hiring plans, "
#     "we might need to explore more cost-effective solutions or seek external funding sources. Additionally, "
#     "it's worth consulting with lawyers to navigate these new laws effectively. Time is of the essence, "
#     "as these changes will impact us starting next quarter, so immediate action is required for the sake of stakeholders."
# )
#
# round = UserAIRound(UserMessage(user_message_content), AIMessage(ai_message_content))
#
# term_detector.on_new_round(last_round=round)
