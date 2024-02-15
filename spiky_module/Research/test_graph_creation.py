import os
import json
import random
from typing import Union, List, Any
from pathlib import Path
from utils import config_retrieval

from langchain.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate
from langchain.chat_models.openai import ChatOpenAI

from neo4j import GraphDatabase

from utils.openai_api.gpt_calling import GPTManager
from utils.openai_api.models import ModelType
from utils.persistance_access import MemoryStreamAccess

"""
TODO:
    - Use less tokens. Possible solutions: after generating every goals filter the ones that are important. 
    Generate labels for multiple goals at the same time.
    - Problem type labels wrong spelling
"""

PROJECT_PROMPT_TEMPLATE_1 = """
From the Project Survey below, extract the following Entities & relationships described in the mentioned format 
0. ALWAYS FINISH THE OUTPUT. Never send partial responses
1. First, look for these Entity types in the text and generate as comma-separated format similar to entity type.
   `id` property of each entity must be alphanumeric and must be unique among the entities. You will be referring this property to define the relationship between entities. Do not create new entity types that aren't mentioned below. Document must be summarized and stored inside Project entity under `summary` property. You will have to generate as many entities as needed as per the types below:
    Entity Types:
    label:'Project',id:string,name:string;summary:string //Project that is the subject of the survey; `id` property is the full name of the project, in lowercase, with no capital letters, special characters, spaces or hyphens; Contents of original document must be summarized inside 'summary' property
    label:'Goal',id:string,name:string;summary:string //Goal of the project that is the subject of the survey; `id` property is the full name of the goal, in lowercase, with no capital letters, special characters, spaces or hyphens; Contents of original document must be summarized inside 'summary' property
    label:'Technology',id:string,name:string //Technology Entity; `id` property is the name of the technology, in camel-case. Identify as many of the technologies used as possible
    label:'Restriction',id:string,name:string;//Restriction upon the completion of the project; `id` property is the name of the restriction, in camel-case; Identify as many of the restrictions as possible
    label:'Ressource',id:string,name:string;//Ressource available to the project; `id` property is the name of the ressource, in camel-case; Identify as many of the ressources as possible
    
2. Next generate each relationships as triples of head, relationship and tail. To refer the head and tail entity, use their respective `id` property. Relationship property should be mentioned within brackets as comma-separated. They should follow these relationship types below. You will have to generate as many relationships as needed as defined below:
    Relationship types:
    goal|USES_TECH|technology 
    goal|RESTRICTED|restriction
    project|HAS_RESSOURCES|ressource
    technology|RESTRICTED|restriction
    


3. The output should look like :
{
    "entities": [{"label":"Project","id":string,"name":string,"summary":string}],
    "relationships": ["goalid|USES_TECH|technologyid"]
}

Case Sheet:
$ctext
"""

PROJECT_PROMPT_TEMPLATE_2 = """
From the Project Survey below, extract the following Entities & relationships described in the mentioned format 
0. ALWAYS FINISH THE OUTPUT. Never send partial responses
1. First, look for these Entity types in the text and generate as comma-separated format similar to entity type.
   `id` property of each entity must be alphanumeric and must be unique among the entities. You will be referring this property to define the relationship between entities. Do not create new entity types that aren't mentioned below. Document must be summarized and stored inside Project entity under `summary` property. You will have to generate as many entities as needed as per the types below:
    Entity Types:
    label:'Project',id:string,name:string;summary:string //Project that is the subject of the survey; `id` property is the full name of the project, in lowercase, with no capital letters, special characters, spaces or hyphens; Contents of original document must be summarized inside 'summary' property
    label:'Goal',id:string,name:string;summary:string //Goal of the project that is the subject of the survey; `id` property is the full name of the goal, in lowercase, with no capital letters, special characters, spaces or hyphens; Contents of original document must be summarized inside 'summary' property
    label:'Technology',id:string,name:string //Technology Entity; `id` property is the name of the technology, in camel-case. Identify as many of the technologies used as possible
    label:'Restriction',id:string,name:string, value:string;//Restriction upon the completion of the project; `id` property is the name of the restriction, in camel-case; `value` property is the quantifier of the restriction or the specific restriction; Identify as many of the restrictions as possible
    label:'Ressource',id:string,name:string;//Every ressources available to the project. It can be of any type; `id` property is the name of the ressource, in camel-case; Identify as many of the ressources as possible

2. Next generate each relationships as triples of head, relationship and tail. To refer the head and tail entity, use their respective `id` property. Relationship property should be mentioned within brackets as comma-separated. They should follow these relationship types below. You will have to generate as many relationships as needed as defined below:
    Relationship types:
    goal|USES_TECH|technology 
    goal|RESTRICTED|restriction
    goal|HAS_RESSOURCES|ressource
    project|HAS_RESSOURCES|ressource
    technology|RESTRICTED|restriction



3. The output should look like :
{
    "entities": [{"label":"Project","id":string,"name":string,"summary":string}],
    "relationships": ["goalid|USES_TECH|technologyid"]
}

Case Sheet:
$ctext
"""

PROJECT_PROMPT_TEMPLATE_3 = """
From the Project Survey below, extract the following Entities & relationships described in the mentioned format 
0. ALWAYS FINISH THE OUTPUT. Never send partial responses
1. First, look for these Entity types in the text and generate as comma-separated format similar to entity type.
   `id` property of each entity must be alphanumeric and must be unique among the entities. You will be referring this property to define the relationship between entities. Do not create new entity types that aren't mentioned below. Document must be summarized and stored inside Project entity under `summary` property. You will have to generate as many entities as needed as per the types below:
    Entity Types:
    label:'Project',id:string,name:string;summary:string //Project that is the subject of the survey; `id` property is the full name of the project, in lowercase, with no capital letters, special characters, spaces or hyphens; Contents of original document must be summarized inside 'summary' property
    label:'Goal',id:string,name:string;summary:string //Goal of the project that is the subject of the survey; `id` property is the full name of the goal, in lowercase, with no capital letters, special characters, spaces or hyphens; Contents of original document must be summarized inside 'summary' property
    label:'Technology',id:string,name:string //Technology Entity; `id` property is the name of the technology, in camel-case. Identify as many of the technologies used as possible
    label:'Restriction',id:string,name:string, value:string;//Absolute restriction upon the completion of the project. Cannot have common entity with 'Concern'; `id` property is the name of the restriction, in camel-case; `value` property is the quantifier of the restriction or the specific restriction; Identify as many of the restrictions as possible
    label:'Concern',id:string,name:string, value:string;//Every non-absolute restriction that need to be taken into account while completing the project. Cannot have common entity with 'Restriction'; `id` property is the name of the concern, in camel-case; `value` property is the quantifier of the restriction or the specific concern; Identify as many of the concerns as possible
    label:'Ressource',id:string,name:string;//Every ressources available to the project. It can be of any type; `id` property is the name of the ressource, in camel-case; Identify as many of the ressources as possible

2. Next generate each relationships as triples of head, relationship and tail. To refer the head and tail entity, use their respective `id` property. Relationship property should be mentioned within brackets as comma-separated. They should follow these relationship types below. You will have to generate as many relationships as needed as defined below:
    Relationship types:
    goal|USES_TECH|technology 
    goal|RESTRICTED|restriction
    goal|CONCERNED|concern
    goal|HAS_RESSOURCES|ressource
    project|HAS_RESSOURCES|ressource
    technology|RESTRICTED|restriction
    tehnology|CONCERNED|concern



3. The output should look like :
{
    "entities": [{"label":"Project","id":string,"name":string,"summary":string}],
    "relationships": ["goalid|USES_TECH|technologyid"]
}

Case Sheet:
$ctext
"""

QUERY_PROMPT_TEMPLATE_1 = """
You are an expert Neo4j Cypher translator who converts English to Cypher based on the Neo4j Schema provided, following the instructions below:
1. Generate Cypher query compatible ONLY for Neo4j Version 5
2. Do not use EXISTS, SIZE, HAVING keywords in the cypher. Use alias when using the WITH keyword
3. Use only Nodes and relationships mentioned in the schema
4. Always do a case-insensitive and fuzzy search for any properties related search. Eg: to search for a Client, use `toLower(client.id) contains 'neo4j'`. To search for Slack Messages, use 'toLower(SlackMessage.text) contains 'neo4j'`. To search for a project, use `toLower(project.summary) contains 'logistics platform' OR toLower(project.name) contains 'logistics platform'`.)
5. Never use relationships that are not mentioned in the given schema
6. When asked about projects, Match the properties using case-insensitive matching and the OR-operator, E.g, to find a logistics platform -project, use `toLower(project.summary) contains 'logistics platform' OR toLower(project.name) contains 'logistics platform'`.

schema: {schema}

Examples:
Question: Which tech's goal has the greatest number of restriction?
Answer: ```MATCH (tech:Technology)<-[:USES_TECH]-(g:Goal)-[:RESTRICTED]->(restriction:Restriction)
RETURN tech.name AS Tech, COUNT(DISTINCT restriction) AS NumberOfRestriction
ORDER BY NumberOfRestriction DESC```
Question: Which goal uses the largest number of different technologies?
Answer: ```MATCH (goal:Goal)-[:USES_TECH]->(tech:Technology)
RETURN goal.name AS GoalName, COUNT(DISTINCT tech) AS NumberOfTechnologies
ORDER BY NumberOfTechnologies DESC```

Question: {question}
$ctext
"""

CYPHER_QA_TEMPLATE = """You are an assistant that helps to form nice and human understandable answers.
The information part contains the provided information that you must use to construct an answer.
The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
Make the answer sound as a response to the question. Do not mention that you based the result on the given information, especially if it comes from a query.
If the provided information is empty, say that you don't know the answer.
Final answer should be easily readable and structured.
Information:
{context}

Question: {question}
Do not give back the raw data, interpret it in a small paragraph.
Helpful Answer:"""

QUERY_GOALS_TEMPLATE_1 = """
From the Q&A session below, extract the objectives that need to be achieved in order to complete the specified project.
ALWAYS FINISH THE OUTPUT. Never send partial responses.
Your output must be a comma-separated format similar to the following example:
name:name of the objective; description:description of the objective;
            
The project:
$project

The Q&A session:
$ctext
"""

QUERY_GOALS_TEMPLATE_2 = """
From the Q&A session below, extract the objectives that need to be achieved in order to complete the specified project.
The objectives needs to be clear and attainable. Do not return similar objectives.
ALWAYS FINISH THE OUTPUT. Never send partial responses.
Your output must have the same format than the following example:
name:name of the objective; description:description of the objective;

The project:
$project

The Q&A session:
$ctext
"""

QUERY_GOALS_TEMPLATE_3 = """
From the Q&A session below, extract the objectives that are mentioned to achieve the project.
The objectives needs to be clear and attainable. Do not return similar objectives.
ALWAYS FINISH THE OUTPUT. Never send partial responses.
Do not jump a line between two objectives in your output. 
Put the name and the description of an objective on the same line.
Your output must have the same format than the following example:
name:name of the objective; description:description of the objective;

The project:
$project

The Q&A session:
$ctext
"""

QUERY_GOALS_TEMPLATE_4 = """
Extract the objectives that are mentioned in the Q&A session. DO NOT CREATE INFORMATION.
Do not return similar objectives. Do not return restrictions.
ALWAYS FINISH THE OUTPUT. Never send partial responses.
Do not jump a line between two objectives in your output. 
Put the name and the description of an objective on the same line.
Your output must have the same format than the following example:
name:name of the objective; description:description of the objective;

The abstract of the project:
$project

The Q&A session:
$ctext
"""

QUERY_GOALS_TEMPLATE_5 = """
Extract the steps mentioned in the Q&A session that need to be completed in order to finish the project. 
DO NOT CREATE INFORMATION.
Do not return similar steps.
ALWAYS FINISH THE OUTPUT. Never send partial responses.
Do not jump a line between two steps in your output. 
Put the name and the description of a step on the same line.
Your output must have the same format than the following example:
name:name of the step; description:description of the step;

The abstract of the project:
$project

The Q&A session:
$ctext
"""

# Works only with gpt 4
QUERY_GOALS_TEMPLATE_6 = """
Extract the objectives that are mentioned in the Q&A session. DO NOT CREATE INFORMATION.
Do not return similar objectives. 
Don't include following a restriction as an objectives in your output. For example, don't include 'Complete the project within a set timeframe' or 'Respect the allocated budget'.
ALWAYS FINISH THE OUTPUT. Never send partial responses.
Do not jump a line between two objectives in your output. 
Put the name and the description of an objective on the same line.
Your output must have the same format than the following example:
name:name of the objective; description:description of the objective;

The abstract of the project:
$project

The Q&A session:
$ctext
"""

QUERY_RELATION_GOALS_TEMPLATE_1 = """
From the list of goals below add a property `type` to each goal.
The `type` property can be either 'main' which mean that the goal isn't a subgoal of any other goal.
Or 'subgoal_nameOfGoal' which means that the goal is in reality a smaller goal that is needed in order to complete a bigger goal.
You need to replace 'nameOfGoal' by the name of the bigger goal.
Do not change any information about the goals.

See below an example of how every lines of the output should looks like:
name:some goal; description:the description of the goal; type:type of the goal;


The goals:
$goals
"""

QUERY_LABELS_TEMPLATE_1 = """
From the Q&A session, extract the following Entities described in the mentioned format 
0. ALWAYS FINISH THE OUTPUT. Never send partial responses
1. First, look for these Entity types in the text and generate as comma-separated format similar to entity type.
    Do not create new entity types that aren't mentioned below. You will have to generate as many entities as needed as per the types below:
    Entity Types:
    label:'Requirements',name:string;summary:string; //What is required to complete the specified goal. Contents of original document must be summarized inside 'summary' property
    label:'Ressources',name:string; value:string; //What is available in order to complete the specified goal.
    label:'Risks',name:string; description:string; impact:string; severity:string; lk_happen:string; //What are the risks when completing the specified goal; `lk_happen` property is the likelihood that the risk happen.
    label:'Schedule', value:string; //Timeframe to complete the specified goal.
    label:'Constraints',name:string; type:string; description:string; //Constraints upon the completion of the specified goal. `type` property is one of the following: 'Internal controls', 'Approvals', 'Regulatory', Ressource constraints', 'Dependencies'.

2. The output should look like :
    {"label":"Requirements","name":string,"summary":string},
    {"label":"Ressources","name":string,"value":string},
    {"label":"Risks","name":string,"description":string,"impact":string,"severity":string,"lk_happen":string},
    {"label":"Schedule","value":string},
    {"label":"Constraints","name":string,"type":string,"description":string},

The goal:
$goal

Q&A Session:
$ctext
"""

QUERY_LABELS_TEMPLATE_2 = """
From the Q&A session, extract the following Entities described in the mentioned format 
0. ALWAYS FINISH THE OUTPUT. Never send partial responses
1. First, look for these Entity types in the text and generate as comma-separated format similar to entity type.
    Do not create new entity types that aren't mentioned below. Do not generate entity with the same name.
    Do not generate entity without a name except for the `Schedule` entities. 
    You will have to generate as many entities as needed as per the types below:
    Entity Types:
    label:'Requirements',name:string;summary:string; //What is required to complete the specified goal. Contents of original document must be summarized inside 'summary' property
    label:'Ressources',name:string; value:string; //What is available in order to complete the specified goal.
    label:'Risks',name:string; description:string; impact:string; severity:string; lk_happen:string; //What are the risks when completing the specified goal; `lk_happen` property is the likelihood that the risk happen.
    label:'Schedule', value:string; //Timeframe to complete the specified goal.
    label:'Constraints',name:string; type:string; description:string; //Constraints upon the completion of the specified goal. `type` property is one of the following: 'Internal controls', 'Approvals', 'Regulatory', Ressource constraints', 'Dependencies'.

2. The output should look like :
    {"label":"Requirements","name":string,"summary":string},
    {"label":"Ressources","name":string,"value":string},
    {"label":"Risks","name":string,"description":string,"impact":string,"severity":string,"lk_happen":string},
    {"label":"Schedule","value":string},
    {"label":"Constraints","name":string,"type":string,"description":string},

The goal:
$goal

Q&A Session:
$ctext
"""

QUERY_SUBGOALS_TEMPLATE_1 = """
From the Q&A session below, extract the sub objectives of the main specified of the project.
ALWAYS FINISH THE OUTPUT. Never send partial responses.
Your output should have the following format:
name of the objective; description of the objective
            
The project:
$project

The main goal:
$nameGoal
$textGoal

The Q&A session:
$ctext
"""


class ProjectDataHandler:
    def __init__(self):
        current_script_path = Path(__file__).resolve()
        parent_folder = current_script_path.parent
        path_folder = parent_folder.joinpath('logs')
        path_graph = parent_folder.joinpath('graphs')
        self.config = config_retrieval.ConfigManager()
        self.path_folder = Path(path_folder)
        self.path_graph = Path(path_graph)
        self.llm = ChatOpenAI(
            temperature=0,
            openai_api_key=self.config.openai.api_key,
            model="gpt-4"
        )
        self.gpt_manager = GPTManager()
        self.memory_access = MemoryStreamAccess()

    def gen_all_data(self, filename: str):
        with open(self.path_folder / filename, "r") as f:
            data = json.load(f)

        # Return the data from the form
        result_txt = ""
        index = 0
        for i in range(len(data["form"]["questions"].keys())):
            result_txt += data["form"]["questions"]["Q" + str(i)] + "\n"

            if "discussion needed" in data["form"]["answers"]["Q" + str(i)].lower():
                result_txt += data["form"]["summary_discussions"][index] + "\n"
                index += 1
            else:
                result_txt += data["form"]["answers"]["Q" + str(i)] + "\n"

        yield result_txt

        # Return the data from the subdiscussions
        for i in range(len(data["conversation"]["questions"].keys())):
            # Get the first question of the subdiscussion without the rules.
            result_txt = data["conversation"]["sub_discussions"][i][0].split("\n")[1][1:]

            result_txt += "\n".join(data["conversation"]["sub_discussions"][i][1:])

            yield result_txt

    def gen_token_new_project(self):
        return hex(random.randint(1_000_000_000, 100_000_000_000))[2:]

    def generate_labels(self, filename: str, model: ModelType = ModelType.GPT_3_5_TURBO, debug: bool = False) -> dict:
        """
        Generate all the labels for a specified goal of the project.
        :param debug:
        :param model:
        :param filename:
        :return:
        """
        with open(self.path_folder / filename, "r") as f:
            data = json.load(f)

        project_brief = data['form']['project_brief']

        graph = {"Goals": {}, "Project": {"description": project_brief}}
        data = ""
        ls_nb_txt = []

        tokens = {"input": 0, "output": 0, "total": 0}
        gen = self.gen_all_data(filename)

        for n_txt, txt in enumerate(gen):
            # Get the goals from each part of the data
            query = QUERY_GOALS_TEMPLATE_6.replace("$project", project_brief).replace("$ctext", txt)
            agent = self.gpt_manager.create_agent(model=model, temperature=0.5, messages=query)

            agent.run_agent()
            graph_info = agent.get_text()

            for i, j in enumerate(agent.get_usage().values()):
                tokens[list(tokens.keys())[i]] += j

            data += graph_info + "\n"
            for i in graph_info.split("\n"):
                if i != "":
                    ls_nb_txt.append(n_txt)

        # Add the property `type` to each goals to identify if they are subgoals or not
        query = QUERY_RELATION_GOALS_TEMPLATE_1.replace("$goals", data)
        agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=query)
        agent.run_agent()
        data_new = agent.get_text()

        # Assign the part of the text that the goal came from
        temp = [i for i in data_new.split("\n") if len(i) != 0]
        if len(temp) != len(ls_nb_txt):
            print(
                f"something is wrong with the number of goals and their index's text.\nThe number of goals: {len(temp)}\nThe number of index: {len(ls_nb_txt)}")
            print("old data:\n" + data)
            print("\n\n\nNew data:\n" + data_new)
            exit(1)
        else:
            for i in range(len(temp)):
                if temp[i][-1] == ";":
                    temp[i] += f" index_text:{ls_nb_txt[i]};"
                elif temp[i][-2:] == "; ":
                    temp[i] += f"index_text:{ls_nb_txt};"
                else:
                    temp[i] += f"; index_text:{ls_nb_txt[i]};"

            data_new = "\n".join(temp)

        if debug:
            print(data_new)

        # Save the data in a dictionary
        for goal in data_new.split("\n"):
            if goal[goal.find("type:") - 2] != ";":
                goal = goal[:goal.find("type:") - 2] + ";" + goal[goal.find("type:") - 2:]

            if debug:
                print(goal.split(";"))

            graph["Goals"][goal.split(";")[0][5:]] = {}
            graph["Goals"][goal.split(";")[0][5:]]["description"] = goal.split(";")[1][13:]
            graph["Goals"][goal.split(";")[0][5:]]["type"] = goal.split(";")[2][6:]
            graph["Goals"][goal.split(";")[0][5:]]["index_text"] = int(goal.split(";")[3][12:])

        # Generate the labels for each goal and subgoal.
        # """
        gen = self.gen_all_data(filename)
        for n_txt, txt in enumerate(gen):
            for goal in graph["Goals"]:

                if debug:
                    print(f"Generating the labels for the goal\n{goal}\nWith the text {n_txt}")

                if n_txt == graph["Goals"][goal]["index_text"]:
                    temp = goal + "\nDescription: " + graph["Goals"][goal]["description"]

                    query = QUERY_LABELS_TEMPLATE_2.replace("$goal", temp).replace("$ctext", txt)

                    agent = self.gpt_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=query)
                    agent.run_agent()

                    result_labels = agent.get_text()
                    for i, j in enumerate(agent.get_usage().values()):
                        tokens[list(tokens.keys())[i]] += j

                    # Save the logs of the labels in case of debug
                    if debug:
                        with open(self.path_graph / f"Labels/{goal.replace(' ', '_').replace('/', '-')}.txt", "w") as f:
                            f.write(result_labels)

                    # Save the labels into the dict
                    graph["Goals"][goal]["Labels"] = []
                    for label in result_labels.split("\n"):
                        if label != "":
                            if label[-1] == ",":
                                label = label[:-1]

                            # Potentiel faille de sécurité
                            print(label)
                            t = eval(label)
                            if type(t) is list or type(t) is tuple:
                                for dicti in t:
                                    graph["Goals"][goal]["Labels"].append(dicti)
                            else:
                                graph["Goals"][goal]["Labels"].append(t)

        # """

        if debug:
            print(graph)
            print(tokens)

            with open(self.path_graph / "goals_6_gpt_4.txt", "w") as f:
                f.write(data)

            with open(self.path_graph / "dict_all_data.json", "w") as f:
                json.dump(graph, f)

        return graph

    def convert_dict_to_file(self, graph: dict, filename: str) -> dict:
        result = {"entities": [], "relationships": []}
        token_project = self.gen_token_new_project()

        result["entities"].append({"label": "Project", "name": "Project", "id": token_project,
                                   "description": graph["Project"]["description"]})

        for goal in graph["Goals"]:
            # Add the goal to the list of relationship
            if graph["Goals"][goal]["type"] == "main":
                id_goal = token_project + f"_{goal.lower().replace(' ', '')}"
                result["relationships"].append(f"{token_project}|HAS_GOAL|{id_goal}")

            else:
                id_goal = token_project + f"_{graph['Goals'][goal]['type'][8:].lower().replace(' ', '')}_{goal.lower().replace(' ', '')}"
                result["relationships"].append(
                    f"{token_project}_{graph['Goals'][goal]['type'][8:].lower().replace(' ', '')}|HAS_GOAL|{id_goal}")

            # Add the goal to the list of entities
            temp = {"label": "Goal", "id": id_goal,
                    "name": goal, "summary": graph["Goals"][goal]["description"]}
            result["entities"].append(temp)

            print()
            print()
            print(goal)
            # Add each label of a goal to the entities and relationship
            for label in graph["Goals"][goal]["Labels"]:
                if "name" in label.keys():
                    if label["name"] == "" or label["name"] == "-" or label["name"] == "None":
                        continue

                if label["label"] == "Schedule":
                    if label["value"] == "" or label["value"] == "-" or label["value"] == "None":
                        continue

                print(type(label))
                print(label)

                if label["label"] == "Schedule":
                    label["id"] = f"{temp['id']}_schedule"
                elif label["name"] == "":
                    label["id"] = f"{temp['id']}_{self.gen_token_new_project()}"
                else:
                    label["id"] = f"{temp['id']}_{label['label'].lower()}{label['name'].lower().replace(' ', '')}"

                result["entities"].append(label)

                result["relationships"].append(f"{temp['id']}|HAS_{label['label'].upper()}|{label['id']}")

        with open(self.path_graph / filename, "w") as f:
            json.dump(result, f)

        return result

    def load_data_form_main_discussion(self, filename: str) -> str:
        with open(self.path_folder / filename, "r") as f:
            data = json.load(f)

        result_txt = f"Project brief description: {data['form']['project_brief']}\n"

        # Get the data from the form
        index = 0
        for i in range(len(data["form"]["questions"].keys())):
            result_txt += data["form"]["questions"]["Q" + str(i)] + "\n"

            if "discussion needed" in data["form"]["answers"]["Q" + str(i)].lower():
                result_txt += data["form"]["summary_discussions"][index] + "\n"
                index += 1
            else:
                result_txt += data["form"]["answers"]["Q" + str(i)] + "\n"

        # Get the data from the main discussion
        for i in data["conversation"]["questions"].keys():
            result_txt += data["conversation"]["questions"][i] + "\n"
            result_txt += data["conversation"]["answers"][i] + "\n"

        return result_txt

    def create_graph(self, query: str, data: str, model: ModelType) -> str:
        complete_query = query.replace("$ctext", data)

        agent = self.gpt_manager.create_agent(model=model, temperature=0.5, max_tokens=400, messages=complete_query)

        agent.run_agent()

        graph_info = agent.get_text()

        return graph_info

    def save_graph(self, path: Path, data: str) -> None:
        with open(path, "w") as f:
            f.write(data)

    def generate_cypher(self, json_obj):
        e_statements = []
        r_statements = []

        e_label_map = {}

        # loop through our json object
        for i, obj in enumerate(json_obj):
            print(f"Generating cypher for file {i + 1} of {len(json_obj)}")

            # Process entities if they exist in this part of the json_obj
            if "entities" in obj:
                for entity in obj["entities"]:
                    label = entity["label"]
                    id = entity["id"]
                    id = id.replace("-", "").replace("_", "")
                    properties = {k: v for k, v in entity.items() if k not in ["label", "id"]}

                    cypher = f'MERGE (n:{label} {{id: "{id}"}})'
                    if properties:
                        props_str = ", ".join(
                            [f'n.{key} = "{val}"' for key, val in properties.items()]
                        )
                        cypher += f" ON CREATE SET {props_str}"
                    e_statements.append(cypher)
                    e_label_map[id] = label

            # Process relationships if they exist in this part of the json_obj
            if "relationships" in obj:
                for rs in obj["relationships"]:
                    src_id, rs_type, tgt_id = rs.split("|")
                    src_id = src_id.replace("-", "").replace("_", "")
                    tgt_id = tgt_id.replace("-", "").replace("_", "")

                    src_label = e_label_map.get(src_id, "UnknownLabel")
                    tgt_label = e_label_map.get(tgt_id, "UnknownLabel")

                    cypher = f'MERGE (a:{src_label} {{id: "{src_id}"}}) MERGE (b:{tgt_label} {{id: "{tgt_id}"}}) MERGE (a)-[:{rs_type}]->(b)'
                    r_statements.append(cypher)

        with open("cyphers.txt", "w") as outfile:
            outfile.write("\n".join(e_statements + r_statements))

        return e_statements + r_statements

    def create_db(self, data: list) -> None: #TODO: use the persistance access
        url = self.config.neo4j.host_url
        user = self.config.neo4j.user
        password = self.config.neo4j.password
        gdb = GraphDatabase.driver(url, auth=(user, password))

        for i, stmt in enumerate(data):
            print(f"Executing cypher statement {i + 1} of {len(data)}")
            try:
                gdb.execute_query(stmt)
            except Exception as e:
                with open("failed_statements.txt", "a") as f:
                    f.write(f"{stmt} - Exception: {e}\n")

    def query_graph(self, query: Union[str, List[str]], full_result: bool = False) -> Union[Any, List[Any]]:
        """
        Processes a query or a list of queries against the Neo4j graph database using a GraphCypherQAChain.

        If a single query string is provided, it processes the query and returns the result. If a list of query strings is provided, it processes each query in the list and returns a list of results.

        Parameters:
        query (Union[str, List[str]]): A single query string or a list of query strings to be processed.
        full_result (bool): If True, returns the full result object; if False, returns only the answer.

        Returns:
        Union[Any, List[Any]]: The full result object or just the answer, depending on the full_result flag.
        """
        url = self.config.neo4j.host_url
        user = self.config.neo4j.user
        password = self.config.neo4j.password
        graph = Neo4jGraph(url=url, username=user, password=password)
        qa_prompt = PromptTemplate(
            input_variables=["context", "question"], template=CYPHER_QA_TEMPLATE
        )
        cypher_prompt = PromptTemplate(
            template=QUERY_PROMPT_TEMPLATE_1,
            input_variables=["schema", "question"]
        )

        if isinstance(query, str):
            return self._process_query(graph, qa_prompt, cypher_prompt, query, full_result)
        elif isinstance(query, list):
            return [self._process_query(graph, qa_prompt, cypher_prompt, q, full_result) for q in query]
        else:
            raise ValueError("Query must be a string or a list of strings")

    def _process_query(self, graph: Neo4jGraph, qa_prompt: PromptTemplate, cypher_prompt: PromptTemplate, query: str,
                       full_result: bool) -> Any:
        """
        Processes a single query string using the provided GraphCypherQAChain.

        This method is intended to be used internally by the query_graph method for processing individual queries.

        Parameters:
        graph (Neo4jGraph): The Neo4j graph object for database interaction.
        qa_prompt (PromptTemplate): The template for the question-answering prompt.
        cypher_prompt (PromptTemplate): The template for the Cypher query prompt.
        query (str): The query string to be processed.
        full_result (bool): If True, returns the full result object; if False, returns only the answer.

        Returns:
        Any: The full result object or just the answer, depending on the full_result flag.
        """
        chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=graph,
            verbose=True,
            return_intermediate_steps=True,
            cypher_prompt=cypher_prompt,
            qa_prompt=qa_prompt
        )
        result = chain(query)
        return result if full_result else result["result"]

    def direct_query_graph(self, query: Union[str, List[str]], natural_l_query='', is_interpreted: bool = False,
                           use_chat_gpt4: bool = False):
        """
        Executes a query or a list of queries directly against the Neo4j graph database.

        If a single query string is provided, it executes the query and returns the result. If a list of query strings is provided, it executes each query in the list and returns a list of results.

        If is_interpreted is True and a list of queries is provided, the results of each query are concatenated into a single string, separated by ".\n".

        Parameters:
        query (Union[str, List[str]]): A single query string or a list of query strings to be executed.
        is_interpreted (bool): If True and a list of queries is provided, concatenates the results into a single string.
        use_chat_gpt4 (bool): If True, uses the CHAT_GPT4 model for interpretation; otherwise, uses GPT-3.5_TURBO.

        Returns:
        Union[str, List[str]]: The result of the query or queries. If is_interpreted is True and a list of queries is provided, returns a single concatenated string.
        """
        if isinstance(query, str):
            return self.memory_access.neo4j_handler.query_graph(query)
        elif isinstance(query, list):
            results = [self.memory_access.neo4j_handler.query_graph(q) for q in query]
            if is_interpreted:
                db_results_concatenated = ".\n".join(str(result) for result in results)
                db_query = " ".join(query)
                system_prompt = CYPHER_QA_TEMPLATE.format(context=db_results_concatenated,
                                                          question=db_query + natural_l_query)
                model_type = ModelType.GPT_4_TURBO if use_chat_gpt4 else ModelType.GPT_3_5_TURBO
                interpretation_agent = self.gpt_manager.create_agent(model=model_type, max_tokens=500, temperature=0.4,
                                                                     messages=system_prompt)
                interpretation_agent.run_agent()

                return interpretation_agent.get_text()
            else:
                return results
        else:
            raise ValueError("Query must be a string or a list of strings")

    def create_json_from_conversation(self, ls_filename_model: list[str]) -> str:
        graph_name = None
        for filename, model, graph_name in ls_filename_model:
            d = self.load_data_form_main_discussion(self.path_folder / filename)
            # graph = self.create_graph(PROJECT_PROMPT_TEMPLATE_3, d, model)
            # self.save_graph(self.path_graph / graph_name, graph)
        return graph_name

    def pipeline(self, ls_filename_model):  # ls_filename_model is a list that allows testing
        filename = self.create_json_from_conversation(ls_filename_model)

        json_path = self.path_graph / filename
        with open(json_path, 'r') as file:
            json_data = json.load(file)

        # Splitting the json_data into two separate dictionaries
        json_list = [
            {"entities": json_data.get("entities", [])},
            {"relationships": json_data.get("relationships", [])}
        ]

        d = self.generate_cypher(json_list)

        self.create_db(d)
        # test the db, no need to do previous steps if there is already a db
        query_result = self.query_graph("Which tech's goal has the greatest number of restriction?")
        intermediate_steps = query_result["intermediate_steps"]
        cypher_query = intermediate_steps[0]["query"]
        database_results = intermediate_steps[1]["context"]

        answer = query_result["result"]
        print(answer)
        print(intermediate_steps)
        print(cypher_query)
        print(database_results)

    def new_pipeline(self, ls_filename_model: list):
        data = self.generate_labels(ls_filename_model[0], ls_filename_model[1], debug=True)
        graph = self.convert_dict_to_file(data, ls_filename_model[2])

        d = self.generate_cypher([graph])

        self.create_db(d)


if __name__ == '__main__':
    handler = ProjectDataHandler()

    # handler.generate_labels("logs_test_short_conversation_gpt4.json", ModelType.GPT_4_TURBO, debug=True)

    ls_filename_model = ("logs_test_short_conversation_gpt4.json", ModelType.GPT_4_TURBO, "new_pipeline_test.json")
    handler.new_pipeline(ls_filename_model)

    # with open(handler.path_graph / "dict_all_data.json", "r") as f:
    #    d = json.load(f)

    # graph = handler.convert_dict_to_file(d, "new_pipeline_test.json")
    # cypher = handler.generate_cypher([graph])
    # handler.create_db(cypher)

    # ls_filename_model = [("logs_test_short_conversation_gpt4.json", ModelType.CHAT_GPT4_old, "pipeline_test.json")]
    # handler.pipeline(ls_filename_model)

    # ls_filename_model = [("logs_test_short_conversation_gpt4.json", "gpt-3.5-turbo-16k-0613", "d2_q3_short_gpt3.json"),
    #                      ("logs_test_long_conversation_gpt4.json", "gpt-3.5-turbo-16k-0613", "d2_q3_long_gpt3.json"),
    #                      ("logs_test_short_conversation_gpt4.json", "gpt-4", "d2_q3_short_gpt4.json"),
    #                      ("logs_test_long_conversation_gpt4.json", "gpt-4", "d2_q3_long_gpt4.json"), ]
