import spacy

temporary_text = "She sat on the chair.He walked into the room.They arrived after midnight.She looked at the painting.He is from Germany.He bought apples and oranges.She likes tea but prefers coffee.They neither drink nor smoke.She worked hard, so she succeeded.I am tired, yet I will continue working."

test_text1 = "What biological methods have been successful in eradicating invasive fish and mushroom species?"
test_text2 = "How would the global climate be affected if deforestation rates were reduced by 50% over the next 10 years?"
test_text3 = "What are the primary survival strategies of desert flora during prolonged drought conditions?"

test_text4 = test_text1 + " " + test_text2 + " " + test_text3

modified_test_text1 = "Invasive species like fish and mushrooms can disrupt local ecosystems. " \
                      "What methods have been successful in eradicating them? Have any biological approaches proven effective?"

modified_test_text2 = "Deforestation is a major environmental concern. " \
                      "How would the global climate change if the rates of deforestation were reduced by 50% over the next 10 years?" \
                      " Would this reduction have a significant impact?"

modified_test_text3 = "Desert flora face extreme conditions during droughts. " \
                      "What are their primary survival strategies during such prolonged periods?" \
                      " How do these plants manage to sustain themselves?"

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


def print_tokens_with_head(doc):
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
    """
    Analyze a spaCy document to identify linking relationships based on adpositions ('ADP') with
    prepositional dependencies ('prep'), and separate logic for coordinating conjunctions ('CCONJ')
    with dependency 'cc'. This function aims to link clusters of objects or action modifiers through
    connections indicated by prepositions and coordinating conjunctions, establishing semantic relationships.

    Parameters:
    - doc (spacy.tokens.Doc): The spaCy document to analyze, which should already be processed
      by a spaCy pipeline with annotated tokens for parts-of-speech and dependencies.
    - object_clusters (dict): A dictionary with identifiers for clusters of noun objects,
      and values as lists (or sets) of tokens representing these objects.
    - action_modifier_clusters (dict): A dictionary with identifiers for clusters of verbs
      or adjectives (action modifiers), and values as lists (or sets) of tokens that modify actions.

    Returns:
    - list: A list of dictionaries, where each dictionary represents a linking relationship identified
      in the document. Each dictionary includes:
        - 'link_token' (spacy.tokens.Token): The token that establishes the link (a preposition or conjunction).
        - 'sender_cluster' (list or set): The cluster from which the link originates.
        - 'target_cluster' (list or set): The cluster to which the link points.

    The function processes tokens with 'ADP'/'prep' for typical adpositional linking and 'CCONJ'/'cc' for
    conjunction-based linking, identifying associations within specified clusters.
    """
    linking_cluster = []

    # Process adpositions (ADP with prep)
    for token in doc:
        if token.pos_ == 'ADP' and token.dep_ == 'prep':
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
                if other_token.head == token:
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

    # Process coordinating conjunctions (CCONJ with cc)
    for token in doc:
        if token.pos_ == 'CCONJ' and token.dep_ == 'cc':
            sender_cluster = None
            target_cluster = None

            # Handling coordinating conjunctions
            conjuncts = [t for t in doc if t.dep_ == 'conj' and t.head == token.head]
            if conjuncts:
                sender_cluster = [token.head] + [t for t in conjuncts if t.i < token.i]
                target_cluster = [t for t in conjuncts if t.i > token.i]

                if sender_cluster and target_cluster:
                    linking_cluster.append({
                        'link_token': token,
                        'sender_cluster': sender_cluster,
                        'target_cluster': target_cluster
                    })

    return linking_cluster


if __name__ == "__main__":
    nlp = spacy.load("en_core_web_trf")
    nlp_coref = spacy.load("en_coreference_web_trf", vocab=nlp.vocab)

    doc = nlp(test_text4)
    doc = nlp_coref(doc)
    print_tokens_with_head(doc)
    for key in doc.spans:
        if key.startswith('coref_clusters'):
            print(f"Cluster ({key}):")
            for mention in doc.spans[key]:
                print(f" - Mention: {mention.text}, [Start: {mention.start}, End: {mention.end}]")

    print([(t.i, t.text, t.pos_, t.dep_) for t in doc])

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
