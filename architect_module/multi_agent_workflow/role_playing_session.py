import json
from pathlib import Path
import traceback

import re

from utils.openai_api import gpt_calling
from utils.openai_api.gpt_calling import GPTAgent, GPTManager

from utils.openai_api.models import ModelType
from architect_module.multi_agent_workflow import agent_recruitment, conversation_splitter, main_vs_side
from architect_module.function_creation import create_new_function


class RoundManager:
    def __init__(self, agent_manager: GPTManager, session_president: GPTAgent, agents: list[GPTAgent], session_type,
                 convo_name,
                 main_convo_name=None):
        self.agent_manager = agent_manager
        self.session_president = session_president
        self.agents = agents
        self.rounds = []
        self.summaries = []
        self.convo_name = convo_name
        self.session_type = session_type
        self.main_convo_name = main_convo_name

    def play_introduction_round(self):
        """
        Play the introduction round where each agent presents themselves.
        """
        introductions = []

        for agent in self.agents:  # Loop through each agent except the president
            # Update the message for the agent
            agent.update_agent(
                messages='present yourself in under 25 words to the debate circle. They need to know what you are capable of. example:"I am a public relations specialist, i will help you handle the public side of this projecct with my experiencce in the field. I am happy to collaborate to this discussion"',
                temperature=0.2)
            # Run the agent to get the introduction
            agent.run_agent()
            agent_introduction = agent.get_text()

            # Add the introduction to the list
            introductions.append({agent.agent_name: agent_introduction})

        # Append the introductions to the rounds list
        self.rounds.append(introductions)

    def play_regular_round(self):
        """
        Play a regular round where the Debate President asks a question and agents may interject.
        """
        # Step 1: President issues a question based on prior rounds
        prior_conversations = self.format_prior_conversations()

        self.session_president.update_agent(messages=prior_conversations, max_tokens=400)
        self.session_president.run_agent()
        president_output = self.session_president.get_text()

        # Initialize a list to hold the output of this round
        this_round_output = [{self.session_president.agent_name: president_output}]
        exchange_type = self.classify_exchange(president_output)
        # Step 2: Each agent decides whether to interject
        for agent in self.agents:
            query = 'Would you like to interject on this issue given by the debate president? Only interject if you think you can bring useful information and explore the subject according to your profession (a farmer should only talk about the implementation of a certain feature in the context that he is a farmer). Answer with YES or NO and no other choice in between.'
            agent.update_agent(messages=president_output + query, max_tokens=3, temperature=0.1,
                               logit_bias={9891: 10, 2201: 10})
            for i in range(3):  # Initial run + 2 additional tries
                personnality = None
                agent.run_agent()
                interject_response = agent.get_text().strip().lower()
                # Step 3: If agent chooses to interject
                if re.search(r'\byes\b', interject_response):

                    if exchange_type == 'main':
                        personnality = agent.system_prompt
                        agent.update_agent(messages=president_output, max_tokens=500, temperature=0.7,
                                           system_prompt=personnality + main_vs_side.MAIN_CONVO_SYSTEM_PROMPT)
                    elif exchange_type == 'side':
                        personnality = agent.system_prompt
                        agent.update_agent(messages=president_output, max_tokens=300, temperature=0.7,
                                           system_prompt=personnality + main_vs_side.SIDE_CONVO_SYSTEM_PROMPT)
                    else:
                        raise ValueError(f"Unexpected exchange type: {exchange_type}")
                    agent.run_agent()
                    agent_output = agent.get_text()
                    this_round_output.append({agent.agent_name: agent_output})
                    if personnality is not None:
                        agent.update_agent(system_prompt=personnality)
                    break  # Break out of the loop


                # Step 4: If agent chooses not to interject
                elif re.search(r'\bno\b', interject_response):
                    print(interject_response + ' this was the agent response to the interjection choice')
                    this_round_output.append({agent.agent_name: 'did not talk this round'})
                    break
                else:
                    print(f"Invalid response received on attempt {i + 1}. Rerunning the agent.")

        self.rounds.append(this_round_output)

    def classify_exchange(self, president_message):
        differentiate_system_prompt = """Using the provided text by a debate president, determine whether it reflects a 'main' or 'side' 
        conversation in the context of a structured debate. For 'main' conversations, identify elements that suggest a broad, 
        strategic dialogue, such as overarching issues, project-wide implications, or high-level problem identification. Look 
        for indicators of conceptual discussion over technical specifics. For 'side' conversations, identify signs of a more 
        detailed, tactical discourse, such as specific task-oriented details, granular steps towards problem-solving, 
        or actionable solutions. Classify the text accordingly and provide justification for your classification based on the 
        content and focus of the discussion. Provide your answer with this format:
        [<Conversation Classification 'main' or 'side'>]
        <Justification of classification>"""
        differentiate_agent = self.agent_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=president_message,
                                                              system_prompt=differentiate_system_prompt, max_tokens=75)
        differentiate_agent.run_agent()
        differentiate_text = differentiate_agent.get_text()
        # Regex to extract the context enclosed in square brackets
        context_match = re.search(r"\[(.*?)]", differentiate_text)

        # If the context is found, store it, otherwise raise an error
        if context_match:
            conversation_context = context_match.group(1).lower()
            # Use regex to check if 'main' or 'side' is mentioned
            if re.search(r"\bmain\b", conversation_context, re.IGNORECASE):
                return 'main'
            elif re.search(r"\bside\b", conversation_context, re.IGNORECASE):
                if self.session_type == 'main':
                    return 'main'
                else:
                    return 'side'
            else:
                # If neither 'main' nor 'side' is found, print an error message and fail the process
                print(f"Error: The context '{conversation_context}' is neither 'main' nor 'side'.")
                raise ValueError(f"Invalid context: {conversation_context}")
        else:
            # If no context is found, print an error message and fail the process
            print("Error: No context found in square brackets.")
            raise ValueError("No context in brackets")

    def format_single_round(self, round_, context, summary=False):
        """
        Format a single round's content.

        Parameters:
            round_: The round to be formatted.
            summary: A boolean flag indicating whether to summarize the round.

        Returns:
            A list containing formatted content of the round.
        """
        assistant_content = ""
        user_content = ""

        # Initialize a variable to keep track of whether the assistant has spoken at all
        assistant_spoken = False

        for intro in round_:
            for agent_name, content in intro.items():
                if agent_name == "Debate President":
                    assistant_content = content
                    assistant_spoken = True
                else:
                    if user_content:
                        user_content += "\n"
                    user_content += agent_name + ":" + content

        # Process user_content through the summarize_round_debaters function only if summary is True
        if summary:
            # Summarize the round by passing the user content and the existing context (previous summaries)
            user_content = self.summarize_round_debaters(user_content, context)

        single_round = []

        # Append a single dictionary entry for 'user' role, if any content is present
        if user_content:
            single_round.append({"role": "user", "content": user_content})

        # Append a single dictionary entry for 'assistant' role, if the assistant has spoken
        if assistant_spoken:
            single_round.append({"role": "assistant", "content": assistant_content})
        else:
            # If the assistant did not speak at all, insert a fake user message
            if not user_content:
                single_round.append({"role": "user", "content": "nothing happened this round"})

        # Ensure the last message is not from the assistant
        if single_round and single_round[-1]["role"] == "assistant":
            last_assistant_message = single_round.pop()
            single_round.insert(-1, last_assistant_message)

        return single_round

    def summarize_round_debaters(self, user_content, context):
        """
        Summarize the content provided by agents during a round.

        Parameters:
            user_content: The content to be summarized.
            context: The context of previous summaries to be included in the system prompt.

        Returns:
            A string containing the summarized content.
        """

        # Include context in the system prompt
        summarizing_system_prompt = "\n".join(context) + (
            "Above are the old rounds summaries."
            "\nFrom the new round's inputs, create your own summary highlighting:\n\n"
            "1. **Distinct Solutions:** List specific solutions from each participant "
            "(e.g., 'Use library X for parsing').\n"
            "2. **Key Challenges:** Note any difficulties or concerns raised "
            "(e.g., 'Scalability issues with solution Y').\n"
            "3. **Consensus/Differences:** Indicate any agreements or debates "
            "(e.g., 'Agreed on framework Z, debated on in-house vs. open-source tools').\n"
            "4. **Categorized Actions:**\n"
            "   - **Immediate Steps:** Actions to implement now "
            "(e.g., 'Refactor code for readability').\n"
            "   - **Strategic Recommendations:** Long-term plans "
            "(e.g., 'Overhaul module architecture').\n"
            "5. **Further Exploration/Resolutions:** Mention topics needing more discussion "
            "or those resolved (e.g., 'AI integration needs exploring, Agile methodology adopted').\n"
            "6. **Complex Ideas:** Provide a brief text for complex proposals "
            "(e.g., 'Hybrid cloud merits detailed analysis').\n"
            "Note: Focus on the new information only. Do not re-summarize previous rounds' content."
            " Your summary cannot exceed 400 words. Your summary should aim to halve the original content."
        )

        summarizing_agent = self.agent_manager.create_agent(model=ModelType.CHAT_GPT4, messages=user_content,
                                                            system_prompt=summarizing_system_prompt, max_tokens=500)
        summarizing_agent.run_agent()
        summary = summarizing_agent.get_text()
        return summary

    def format_prior_conversations(self):
        """
        Format prior conversations to prepare for the next round, summarizing only new rounds.

        Returns:
            A list containing formatted summaries of all rounds.
        """
        # Initialize an attribute to keep track of the last summarized round if it doesn't exist.
        if not hasattr(self, 'last_summarized_round_index'):
            self.last_summarized_round_index = -1

        # Fetch new rounds that haven't been summarized yet.
        new_rounds = self.rounds[self.last_summarized_round_index + 1:]

        # Fetch existing summaries to provide context for new summaries.
        existing_summaries = getattr(self, 'summaries', [])

        # Flatten existing summaries for use as context.
        context_for_summarization = self.flatten_rounds(existing_summaries)

        # Initialize an empty list to store summary rounds.
        summary_rounds = []

        # Iterate over new rounds to create their summaries.
        for round_index, round_ in enumerate(new_rounds, start=self.last_summarized_round_index + 1):
            # Create the summary version of this round using existing summaries as context.
            summary_round = self.format_single_round(round_, context=context_for_summarization, summary=True)
            summary_rounds.append(summary_round)

            # Update the last summarized round index.
            self.last_summarized_round_index = round_index

        # Save the summary rounds to self.summaries, if it doesn't exist, initialize it.
        if not hasattr(self, 'summaries'):
            self.summaries = []
        self.summaries.extend(self.flatten_rounds(summary_rounds))

        return self.summaries

    @staticmethod
    def flatten_rounds(formatted_rounds):
        """
        Flatten the list of rounds into a single list.

        Parameters:
            formatted_rounds: The list of formatted rounds.

        Returns:
            A flattened list.
        """
        flattened_list = []
        for single_round in formatted_rounds:
            for message in single_round:
                flattened_list.append(message)
        return flattened_list

    @staticmethod
    def clean_name(name):
        # Remove all special characters, double quotes, and single quotes
        cleaned_name = re.sub(r'[^\w\s]', '', name)
        return cleaned_name.strip().replace(" ", "_")

    def remove_content(self, name_to_remove=None, remove_all=False):
        file_path = Path(__file__).resolve().parent.joinpath('conversation_rounds.json')
        try:
            with open(file_path, 'r') as json_file:
                all_data = json.load(json_file)

            if remove_all:
                all_data = {"all_convos": [], "main_convo": {}, "side_convos": {}}
            elif name_to_remove:
                cleaned_name_to_remove = self.clean_name(name_to_remove)
                all_data['all_convos'].remove(cleaned_name_to_remove)
                all_data['main_convo'].pop(cleaned_name_to_remove, None)
                all_data['side_convos'].pop(cleaned_name_to_remove, None)

            with open(file_path, 'w') as json_file:
                json.dump(all_data, json_file, indent=4)

        except Exception as e:
            print(f"An error occurred: {e}")

    def get_summary(self, convo_name):
        cleaned_convo_name = self.clean_name(convo_name)
        file_path = Path(__file__).resolve().parent.joinpath('conversation_rounds.json')

        try:
            with open(file_path, 'r') as json_file:
                all_data = json.load(json_file)

            # Initialize the summary string
            summary_string = ""

            # Check if the conversation exists in 'main_convo'
            if cleaned_convo_name in all_data['main_convo']:
                summary_list = all_data['main_convo'][cleaned_convo_name].get('summaries', [])

            # Check if the conversation exists in 'side_convos'
            else:
                for main_convo in all_data['side_convos'].values():
                    for side_convo in main_convo:
                        if side_convo['name'] == cleaned_convo_name:
                            summary_list = side_convo.get('summaries', [])
                            break
                    else:
                        continue
                    break
                else:
                    return "Conversation not found."

            # Concatenate the content from each summary into the summary string
            for summary in summary_list:
                summary_string += f"{summary['role']}: {summary['content']} "  # Add a space for separation

            return summary_string.strip()  # Remove any leading/trailing whitespace

        except FileNotFoundError:
            return "File not found."
        except json.JSONDecodeError:
            return "Error decoding JSON file."
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    def save_rounds_and_summaries(self):
        cleaned_convo_name = self.clean_name(self.convo_name)
        cleaned_main_convo_name = self.clean_name(self.main_convo_name) if self.main_convo_name else None

        current_script_path = Path(__file__).resolve()
        parent_folder = current_script_path.parent
        file_path = parent_folder.joinpath('conversation_rounds.json')
        try:
            with open(file_path, 'r') as json_file:
                all_data = json.load(json_file)
        except FileNotFoundError:
            all_data = {"all_convos": [], "main_convo": {}, "side_convos": {}}
        except json.JSONDecodeError:
            print("Error decoding JSON file.")
            return
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return

        if cleaned_convo_name not in all_data['all_convos']:
            all_data['all_convos'].append(cleaned_convo_name)

        try:
            if self.session_type == 'main':
                all_data['main_convo'][cleaned_convo_name] = {'name': cleaned_convo_name, 'rounds': self.rounds,
                                                              'summaries': self.summaries}
            elif self.session_type == 'side':
                if cleaned_main_convo_name not in all_data['side_convos']:
                    all_data['side_convos'][cleaned_main_convo_name] = []
                all_data['side_convos'][cleaned_main_convo_name].append(
                    {'name': cleaned_convo_name, 'rounds': self.rounds, 'summaries': self.summaries})
        except Exception as e:
            print(f"An error occurred while updating the data: {e}")
            return

        try:
            with open(file_path, 'w') as json_file:
                json.dump(all_data, json_file, indent=4)
        except Exception as e:
            print(f"An error occurred while saving the data: {e}")


class SessionObject:
    def __init__(self, convo_manager, agent_manager, convo_prompt, session_type, main_convo_name):
        self.convo_manager = convo_manager
        self.agent_manager = agent_manager
        self.convo_prompt = convo_prompt
        self.session_type = session_type  # 'main', 'side', or 'function_creator'
        self.session_president = None
        self.agents = None
        self.round_manager = None
        self.main_convo_name = main_convo_name
        if session_type == 'main':
            self.convo_name = self.main_convo_name

    def appoint_session_president(self):
        if self.session_type in ['main', 'side']:
            president_system_prompt = ""
            # Differentiate between 'main' and 'side'
            if self.session_type == 'main':
                president_system_prompt = """You are the president of a debate circle whose goal is to discuss a 
            project and, unless asked otherwise in this format (TALK ABOUT SPECIFIC SUBJECT:<SPECIFIC_SUBJECT>), 
            you must explore the project organically. Your job is never to propose solutions, but to expose 
            problems, logic fallacies, and explore the subject in order to avoid blind spots. Never flip roles 
            with the debaters! You share a common interest with the debaters to solve issues and advance the 
            project. Never forget that the main task is to lead the other debaters so they can solve problems in 
            the project. If the debaters cannot answer or find your directives unclear they will answer with [
            Cannot Process Directives: <Reason for incompletion>]. Avoid calling out to any specific participant, 
            let them choose wether they have something to say by giving context that might help them share their 
            specialized opinion on the subject.

            When presented with a numbered list of items to discuss, you are to address each item sequentially, 
            focusing on one issue at a time without introducing multiple issues simultaneously. Upon concluding the 
            discussion of an item, you are to declare its completion with 'Completion Noted: [Item Exported to New 
            Session]'. This statement signifies that you have collected ample information for the feature's 
            development, which will then be passed on to the following debate president. You will then create a 
            summary, ensuring impartiality throughout the process. The debaters will not participate in this 
            summarization round, as it is reserved for you to encapsulate all key points and nuances of the debate 
            for that item to provide a solid foundation for the next phase. As the current debate president, 
            your findings and discussions will be the sole context provided to the next session's president. Always 
            add 'Debate President: ' when you start to talk, and maintain a vigilant watch for unbiased facilitation, 
            steering clear of influencing the direction of solutions. The debaters have a very short memory, 
            so reminders of prior conclusions are necessary for continuity. Now, here is the context of the project:"""


            elif self.session_type == 'side':
                president_system_prompt = """You are the president of a debate circle whose goal is to discuss a 
            specific task and how to resolve it, unless asked otherwise in this format (TALK ABOUT SPECIFIC 
            SUBJECT:<SPECIFIC_SUBJECT>). Your job is never to propose solutions yourself, but to expose problems, 
            logic fallacies, and explore the subject and the proposed solutions in order to avoid blind spots. 
            Never flip roles with the debaters! You share a common interest with the debaters to solve the task. 
            Never forget that your main objective as a debate president is to lead the other debaters so they can 
            propose solutions. If the debaters cannot answer or find your directives unclear, they will answer 
            with [Cannot Process Directives: <Reason for incompletion>].

            When dealing with a numbered list of items, address each point in order, ensuring to tackle only one 
            problem at a time, never bring up multiple problems at a time. The completion of an item in the list 
            occurs when either a step-by-step solution is found, described in atomic steps that are detailed and 
            explicit to the point where further division would be inefficient, or when the item is too complex to 
            articulate in atomic steps and requires a more in-depth exploration. In the latter case, it should be 
            exported for further discussion.

            When complexity escalates beyond the scope of debate it means that creating atomic steps is impossible 
            because of the complexity.

            Upon completion of an item, clearly state 'Completion Noted: [Full Solution Found]' along with the atomic 
            steps outlined, remember that wrapping up an item on the list means that debaters won't be involved while 
            you format the solution/export. If the item is too complex, state 'Completion Noted: [Item Exported to 
            New Session]'. This procedural closure signals the readiness for a transition to a new debate or a 
            different stage of project development. Ensure that the atomic steps are sufficiently granular; for 
            instance, rather than saying 'Implement the feature,' break it down into steps like '1. Define the 
            function parameters, 2. Write the loop structure, 3. Validate input data, etc.' These steps should be 
            formulated so that even a novice programmer could implement the solution without additional guidance. 
            Always add 'Debate President: ' when you start to talk.

            The debaters have a very short memory, so you must provide them with the conclusions from the previous 
            rounds to deepen the discussion.You must never create summaries of the discussion, unless an item is 
            completed! Now, here is the context of the project:"""

            self.session_president = self.agent_manager.create_agent(model=ModelType.FUNCTION_CALLING_GPT_3_5,
                                                                     messages='empty',
                                                                     system_prompt=president_system_prompt + self.convo_prompt,
                                                                     agent_name="Debate President",
                                                                     max_tokens=400)
        elif self.session_type == 'function_creator':
            pass

    def appoint_session_agents(self):
        if self.session_type in ['main', 'side']:
            agents = agent_recruitment.recruit_agents(self.convo_prompt)
            self.agents = []  # Initialize an empty list to store agent objects
            for agent_info in agents:
                role_context = agent_info['role'] + "personality" + ': ' + agent_info['context']
                # TODO the personnalities for side and main are not actually for side and main but rather for low-level and high level.
                # if at runtime the agent is able to choose which personnality is the best, then it could be more optimal. test to be done if an agent can choose the right personnality accurately.
                agent = self.agent_manager.create_agent(
                    model=ModelType.FUNCTION_CALLING_GPT_3_5,
                    messages="empty",
                    system_prompt=role_context,
                    agent_name=agent_info['role']
                )
                self.agents.append(agent)  # Append the created agent to self.agents list
        elif self.session_type == 'function_creator':
            pass

    def start_role_playing_session(self, num_rounds=4):
        if self.session_president is None:
            self.appoint_session_president()
        self.appoint_session_agents()
        count = 0  # should be 0
        self.round_manager = RoundManager(self.agent_manager, self.session_president, self.agents, self.session_type,
                                          self.convo_name, main_convo_name=self.main_convo_name)
        try:
            while num_rounds > count:
                if count == 0:
                    self.round_manager.play_introduction_round()
                else:
                    self.round_manager.play_regular_round()
                count += 1
        except Exception as e:
            print(f"An error occurred during round {count + 1}: {e}")
            print("Traceback details:")
            print(traceback.format_exc())
        finally:
            # if self.session_type == 'main':
            #    self.convo_name = "Backend_Python_Project_Processing"
            self.round_manager.save_rounds_and_summaries()
            try:
                convo_splitter = conversation_splitter.ConversationSplitter(self.convo_name, self.agent_manager)
                convo_splitter.split_conversation(self.round_manager.get_summary(self.convo_name))

                for split_convo in convo_splitter.get_split_conversations():
                    try:
                        if split_convo['side_topic_type'] == 'function_creator':
                            self.convo_manager.create_session(
                                session_type=split_convo['side_topic_type'],
                                main_convo_name=self.main_convo_name,
                                task=split_convo['side_topic_context']
                            )
                        new_session = self.convo_manager.create_session(
                            session_type=split_convo['side_topic_type'],
                            main_convo_name=self.main_convo_name,
                            side_convo_prompt=split_convo['side_topic_context']
                        )
                        new_session.start_role_playing_session()
                    except Exception as e:
                        print(f"Failed to create or initialize session for {split_convo['side_topic_type']}: {e}")

            except Exception as e:
                print(f"Failed to split conversation: {e}")

    def get_convo_name(self):
        if self.session_president is None:
            self.appoint_session_president()
        self.session_president.update_agent(messages="Please give a name to  this debate. "
                                                     "It must clearly highlight the goal and be extremely short."
                                                     "Between 3 to 7 words maximum",
                                            max_tokens=15)
        self.session_president.run_agent()
        self.convo_name = self.session_president.get_text()
        if self.session_type == 'main':
            self.main_convo_name = self.convo_name


class ConversationManager:
    def __init__(self, input_prompt: str):
        self.agent_manager = gpt_calling.GPTManager()
        self.main_convo_prompt = input_prompt
        self.side_convo_prompts = []
        self.sessions = {}

    # main_convo_name should only be filled if a side conversation is created
    def create_session(self, session_type, main_convo_name=None, task=None, side_convo_prompt=None):
        new_session = None
        if side_convo_prompt:
            self.side_convo_prompts.append(side_convo_prompt)
        if session_type == 'function_creator':
            function_creator = create_new_function.FunctionCreator(task=task, gpt_manager=self.agent_manager)
            function_creator.run_workflow()
            function_creator.implement_function()
            return None
        elif session_type == 'main':
            new_session = SessionObject(self, self.agent_manager, self.main_convo_prompt, session_type, main_convo_name)
        elif session_type == 'side':
            new_session = SessionObject(self, self.agent_manager, side_convo_prompt, session_type, main_convo_name)
        new_session.get_convo_name()
        session_name = new_session.convo_name
        self.sessions[session_name] = new_session
        return new_session

    def get_session(self, session_name):
        return self.sessions.get(session_name, None)
