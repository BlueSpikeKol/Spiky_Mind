import spacy

nlp = spacy.load('en_core_web_lg')

text = "Given the recent changes in tax legislation, reviewing our budget allocations is crucial, especially for our R&D department. This department will see the new law, effective from next quarter, imposing stricter regulations on capital expenditure. It will significantly impact the team, which consists of more than 25 people. How do you think this affects our planned investment in new technology and personnel over the next fiscal year?"


def print_tokens_with_head(text):
    doc = nlp(text)
    important_list = []
    for token in doc:
        print(f"{token.text} ({token.pos_})--({token.dep_})", end="")
        print(f" -----> Head: {token.head.text} ({token.head.pos_})", end="")
        if token.pos_ == "NOUN" or token.pos_ == "VERB" or token.pos_ == "ADJ" or token.pos_ == "DET":
            important_list.append(token.text)
            important_list.append(token.pos_)
            print()
        else:
            print()
    print("Important words: ")
    print(important_list)


#
test_text = "Despite the heavy rain that was falling intermittently, she has, after much deliberation, decided to embark on the journey, knowing well that it could, without warning, turn more perilous."
print("Test 1:")
# print_tokens_with_head(test_text)
# print()

test_2 = "The flowers smell fragrant in the garden. The orchids were responsible for this pleasant fragrance."
print("Test 2:")
# print_tokens_with_head(test_2)
print()
#
# test_3="He found the book on the top shelf interesting."
# print("Test 3:")
# print_tokens_with_head(test_3)
# print()

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
print("Test 4:")
# print_tokens_with_head(complete_text)
# print_tokens_with_head(response_to_legislation_changes)
print()

# Text to process


# Process the text with spaCy
# doc = nlp(complete_text+response_to_legislation_changes)
monopoly_text = "What happens if you land on an unowned property in Monopoly, is there a disatvantage? Why would I want to avoid such places and through what process does that put me in a bad position, do i have to lose something or is it just a matter of not gaining anything?"
print_tokens_with_head(monopoly_text)
doc = nlp(monopoly_text)


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

    return object_clusters



def create_action_modifier_clusters(doc):
    action_modifier_clusters = {}
    aux_without_verbs = {}

    for i, token in enumerate(doc):
        if token.pos_ == 'VERB':
            action_modifier_clusters[i] = [token]
        elif token.pos_ == 'AUX':
            aux_without_verbs[i] = token

    # Adding pronouns to their respective verb clusters
    for token in doc:
        if token.pos_ == 'PRON':
            head = token.head
            if head.pos_ == 'VERB':
                for cluster_id in action_modifier_clusters:
                    if head in action_modifier_clusters[cluster_id]:
                        action_modifier_clusters[cluster_id].append(token)
                        break
                else:
                    # If the verb is not yet in any cluster, create a new cluster for it
                    action_modifier_clusters[i] = [head, token]

    # Adding modifiers to their respective verb clusters
    for token in doc:
        if token.pos_ in ['ADJ', 'DET']:
            head = token.head
            if head.pos_ == 'VERB':
                for cluster_id in action_modifier_clusters:
                    if head in action_modifier_clusters[cluster_id]:
                        action_modifier_clusters[cluster_id].append(token)
                        break

    # Process AUX tokens with respect to their parent verb or as standalone clusters
    for i, token in aux_without_verbs.items():
        head = token.head
        if head.pos_ == 'VERB':
            for cluster_id in action_modifier_clusters:
                if head in action_modifier_clusters[cluster_id]:
                    action_modifier_clusters[cluster_id].append(token)
                    break
        else:
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

def create_composed_cluster_with_advcl(doc, object_clusters, action_modifier_clusters):
    for token in doc:
        if token.dep_ == 'advcl' and token.head.pos_ == 'VERB':
            advcl_cluster = None
            head_cluster = None

            # Find the cluster containing the advcl token
            for cluster_id, cluster in action_modifier_clusters.items():
                if token in cluster:
                    advcl_cluster = cluster
                    break

            # Find the cluster containing the head of the advcl token
            for cluster_id, cluster in action_modifier_clusters.items():
                if token.head in cluster:
                    head_cluster = cluster
                    break

            # Merge the two clusters if they exist
            if advcl_cluster is not None and head_cluster is not None:
                # Add all tokens from the advcl cluster to the head cluster
                for t in advcl_cluster:
                    if t not in head_cluster:
                        head_cluster.append(t)

                # Remove the old advcl cluster
                action_modifier_clusters = {k: v for k, v in action_modifier_clusters.items() if v != advcl_cluster}

    return action_modifier_clusters

def create_composed_clusters_with_mark(doc, object_clusters, action_modifier_clusters):
    for token in doc:
        if token.dep_ == 'mark':
            mark_head_cluster = None

            # Find the cluster containing the head of the mark token
            for cluster_id, cluster in object_clusters.items():
                if token.head in cluster:
                    mark_head_cluster = cluster
                    break

            if mark_head_cluster is None:
                for cluster_id, cluster in action_modifier_clusters.items():
                    if token.head in cluster:
                        mark_head_cluster = cluster
                        break

            # Integrate the mark token with its head cluster
            if mark_head_cluster is not None:
                mark_head_cluster.append(token)

    return object_clusters, action_modifier_clusters

def add_expl_to_clusters(doc, object_clusters, action_modifier_clusters):
    for token in doc:
        if token.dep_ == 'expl':
            head = token.head
            added = False

            # Find the head's cluster and add the expletive token to it
            for cluster_id, cluster in action_modifier_clusters.items():
                if head in cluster:
                    cluster.append(token)
                    added = True
                    break

            if not added:
                for cluster_id, cluster in object_clusters.items():
                    if head in cluster:
                        cluster.append(token)
                        break

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


def print_clusters_in_order(doc, object_clusters, action_modifier_clusters, linking_clusters):
    # Create a list of tuples (start_index, cluster_type, cluster) for sorting
    cluster_list = []

    # Add object clusters
    for cluster_id, cluster in object_clusters.items():
        start_index = min([token.i for token in cluster])
        cluster_list.append((start_index, 'Object Cluster', cluster))

    # Add action modifier clusters
    for cluster_id, cluster in action_modifier_clusters.items():
        start_index = min([token.i for token in cluster])
        cluster_list.append((start_index, 'Action Modifier Cluster', cluster))

    # Add linking clusters
    for link in linking_clusters:
        start_index = link['link_token'].i
        cluster_list.append((start_index, 'Linking Cluster', link))

    # Sort the list by start_index
    cluster_list.sort(key=lambda x: x[0])

    # Print the clusters in order
    for start_index, cluster_type, cluster in cluster_list:
        if cluster_type == 'Linking Cluster':
            link_token = cluster['link_token']
            link_token_index = link_token.i
            sender_start_index = min([token.i for token in cluster['sender_cluster']])
            target_start_index = min([token.i for token in cluster['target_cluster']])

            if link_token_index < target_start_index < sender_start_index:
                link_token_text = link_token.text
                target_text = ' '.join([token.text for token in sorted(cluster['target_cluster'], key=lambda t: t.i)])
                sender_text = ' '.join([token.text for token in sorted(cluster['sender_cluster'], key=lambda t: t.i)])
                print(f"{cluster_type}: [link_token: '{link_token_text}'], [target_cluster: {target_text}], [sender_cluster: {sender_text}]")
            elif sender_start_index < link_token_index < target_start_index:
                sender_text = ' '.join([token.text for token in sorted(cluster['sender_cluster'], key=lambda t: t.i)])
                link_token_text = link_token.text
                target_text = ' '.join([token.text for token in sorted(cluster['target_cluster'], key=lambda t: t.i)])
                print(f"{cluster_type}: [sender_cluster: {sender_text}], [link_token: '{link_token_text}'], [target_cluster: {target_text}]")
            else:
                sender_text = ' '.join([token.text for token in sorted(cluster['sender_cluster'], key=lambda t: t.i)])
                target_text = ' '.join([token.text for token in sorted(cluster['target_cluster'], key=lambda t: t.i)])
                link_token_text = link_token.text
                print(f"{cluster_type}: [sender_cluster: {sender_text}], [target_cluster: {target_text}], [link_token: '{link_token_text}']")
        else:
            cluster_text = ' '.join([token.text for token in sorted(cluster, key=lambda t: t.i)])
            print(f"{cluster_type}: [{cluster_text}]")
# Process the document and create clusters
object_clusters = create_object_clusters(doc)
action_modifier_clusters = create_action_modifier_clusters(doc)
object_clusters, action_modifier_clusters = add_acomp_to_clusters(doc, object_clusters, action_modifier_clusters)
action_modifier_clusters = create_composed_cluster_with_advcl(doc, object_clusters, action_modifier_clusters)
object_clusters, action_modifier_clusters = create_composed_clusters_with_mark(doc, object_clusters, action_modifier_clusters)
object_clusters, action_modifier_clusters = add_expl_to_clusters(doc, object_clusters, action_modifier_clusters)
linking_clusters = create_linking_clusters(doc, object_clusters, action_modifier_clusters)

# Print the clusters in order
print_clusters_in_order(doc, object_clusters, action_modifier_clusters, linking_clusters)

# for link in linking_clusters:
#     print(link)
# # Print the clusters
# print("Object Clusters:")
# for cluster in object_clusters.values():
#     print(cluster)
#
# print("\nAction Modifier Clusters:")
# for cluster in action_modifier_clusters.values():
#     print(cluster)



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
