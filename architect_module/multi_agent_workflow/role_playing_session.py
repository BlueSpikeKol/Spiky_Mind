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
    def __init__(self, convo_manager, agent_manager: GPTManager, session_president: GPTAgent, agents: list[GPTAgent],
                 session_type,
                 convo_name,
                 main_convo_name=None):
        self.agent_manager = agent_manager
        self.convo_manager = convo_manager
        self.session_president = session_president
        self.agents = agents
        self.rounds = []
        self.summaries = []
        self.convo_name = convo_name
        self.session_type = session_type
        self.main_convo_name = main_convo_name
        self.convo_item_count = 0
        self.conversation_ended = False

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
            agent_introduction = "Debater introduction: " + agent.get_text()

            # Add the introduction to the list
            introductions.append({agent.agent_name: agent_introduction})

        # Append the introductions to the rounds list
        self.rounds.append(introductions)

    def play_regular_round(self):
        """
        Play a regular round where the Debate President asks a question and agents may interject.
        """
        if self.conversation_ended:
            print("The conversation has already ended. No further action taken.")
            return
        guidance = self.format_prior_conversations()
        president_output = ""
        exchange_type = ""
        # Check if the round should be skipped
        if guidance in ["wrap-up", "atomic_step"]:
            if guidance == "wrap-up":
                self.wrap_up_round()
            elif guidance == "atomic_step":
                self.atomic_step_gathering()
            # Skip the round and note completion
            self.convo_item_count = 1  # Reset the conversation item count
            skip_message = 'Completion Noted No Need For Further Summarizing Or Exploration: [Solution Found]'
            this_round_output = [{agent.agent_name: skip_message} for agent in self.agents]
        else:
            print(guidance)
            self.convo_item_count += 1
            president_message = self.summaries[-1]['content'] + guidance
            self.session_president.update_agent(messages=president_message, max_tokens=400, temperature=0.3)
            self.session_president.run_agent()
            president_output = self.session_president.get_text()
            if "[CONVO_END]" in president_output:
                self.conversation_ended = True
                print("The Debate President has ended the conversation.")
                return

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
                    fused_conversation = self.extract_conversation_context(self.convo_item_count, max_rounds=1)
                    fused_conversation = fused_conversation.strip() + "\n\n" + president_output

                    if exchange_type == 'main':
                        personnality = agent.system_prompt
                        agent.update_agent(messages=fused_conversation, max_tokens=600, temperature=1.1,
                                           system_prompt=personnality + main_vs_side.MAIN_CONVO_SYSTEM_PROMPT)
                    elif exchange_type == 'side':
                        personnality = agent.system_prompt
                        agent.update_agent(messages=fused_conversation, max_tokens=600, temperature=0.4,
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

    def wrap_up_round(self):
        context = self.extract_conversation_context(self.convo_item_count)
        summary_of_debate_item = self.summarize_round_debaters("", context=context, wrap_up=True)
        self.process_split_conversations(summary_of_debate_item, 'side')

    def atomic_step_gathering(self):
        context = self.extract_conversation_context(self.convo_item_count)
        atomic_steps_summary = self.summarize_round_debaters("", context=context, atomic_steps=True)
        self.process_split_conversations(atomic_steps_summary, 'function_creator')

    def process_split_conversations(self, summary, session_type):
        convo_splitter = conversation_splitter.ConversationSplitter(self.convo_name, self.agent_manager)
        convo_splitter.split_conversation(summary)

        for split_convo in convo_splitter.get_split_conversations():
            try:
                new_session = self.convo_manager.create_session(
                    session_type=session_type,
                    main_convo_name=self.main_convo_name,
                    side_convo_prompt=split_convo['side_topic_context'] if session_type == 'side' else None,
                    task=split_convo['side_topic_context'] if session_type == 'function_creator' else None
                )
                new_session.start_role_playing_session()
            except Exception as e:
                print(f"Failed to create or initialize session for {session_type}: {e}")

    def classify_exchange(self, president_message):
        differentiate_system_prompt = """Using the provided text by a debate president, determine whether it reflects 
        a 'main' or 'side' conversation in the context of a structured debate. For 'main' conversations, 
        identify elements that suggest a broad, strategic dialogue, such as overarching issues, project-wide 
        implications, or high-level problem identification. Look for indicators of conceptual discussion over 
        technical specifics. For 'side' conversations, identify signs of a more detailed, specific discourse, 
        such as specific task-oriented details, granular steps towards problem-solving, or actionable solutions. 
        Classify the text accordingly and provide justification for your classification based on the content and 
        focus of the discussion. Provide your answer with this format: [<Conversation Classification 'main' or 
        'side'>] <Justification of classification>"""
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

    def summarize_round_debaters(self, user_content, context="", wrap_up=False, atomic_steps=False):
        """
        Summarize the content provided by agents during a round.

        Parameters:
            user_content: The content to be summarized.
            context: The context of previous summaries to be included in the system prompt.

        Returns:
            A string containing the summarized content.
        """
        summarizing_agent = None
        if wrap_up:
            summarizing_system_prompt = context + (
                "Above are the previous rounds."
                "\nFrom the new round's inputs, create your own summary highlighting:\n\n"
                "1. **Distinct Solutions:** List specific solutions from each participant "
                "(e.g., 'Use library X for parsing').\n"
                "2. **Key Challenges:** Note any difficulties or concerns raised "
                "(e.g., 'Scalability issues with solution Y').\n"
                "3. **Consensus/Differences:** Indicate any agreements or debates "
                "(e.g., 'Agreed on framework Z, debated on in-house vs. open-source tools').\n"
                "4. **Categorized Actions:**\n"
                "- **Immediate Steps:** Actions to implement now. only applicable if long-term plans are impossible "
                "without them"
                "(e.g., 'Refactor code for readability').\n"
                "   - **Strategic Recommendations:** Long-term plans "
                "(e.g., 'Overhaul module architecture').\n"
                "5. **Further Exploration/Resolutions:** Mention topics needing more discussion "
                "or those resolved (e.g., 'AI integration needs exploring, Agile methodology adopted').\n"
                "6. **Complex Ideas:** Provide a brief text for complex proposals "
                "(e.g., 'Hybrid cloud merits detailed analysis').\n"
                "Note: Focus on the new information only. Focus on the high quality structure of your summary."
                " Your summary cannot exceed 1000 words. write None when there is nothing to say"
            )
            summarizing_agent = self.agent_manager.create_agent(model=ModelType.FUNCTION_CALLING_GPT_3_5,
                                                                messages="now create the summary:",
                                                                system_prompt=summarizing_system_prompt,
                                                                max_tokens=1100,
                                                                temperature=0.5)
        elif atomic_steps:
            summarizing_system_prompt = (
                "When delineating atomic steps for any task, it's critical to elucidate the micro-objective of each "
                "step, capped at 150 words to ensure brevity and clarity. For each step, the input should be "
                "specified in detail—it could encompass resources like time allocation, budgetary limits, "
                "or information prerequisites such as data formats, expected knowledge, or preparatory work. The "
                "output is equally vital, marking the completion of the step with a deliverable, which might be a "
                "tangible artifact like a document, a code module, or an intangible result such as enhanced knowledge "
                "or a decision point."
                "Moreover, any existing tools, processes, or functions that are to be leveraged must be identified to "
                "facilitate the step. This may involve predefined frameworks, established methodologies, or specific "
                "pieces of code. Articulating these elements ensures each "
                "atomic step is not just a task, but a cog in a larger mechanism. This precise breakdown into atomic "
                "steps equips even a novice with a clear, actionable path forward"
            )
            summarizing_agent = self.agent_manager.create_agent(model=ModelType.FUNCTION_CALLING_GPT_3_5,
                                                                messages="now create the atomic steps:",
                                                                system_prompt=summarizing_system_prompt + context,
                                                                max_tokens=1100,
                                                                temperature=0.2)
        else:
            summarizing_system_prompt = "cut in half the content given by creating an unstructured summary of it."

            summarizing_agent = self.agent_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=user_content,
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
        guidance = self.guide_next_round()
        return guidance

    def guide_next_round(self):
        if len(self.rounds) < 2:
            return ""  # Return an empty string if not enough context

        fused_conversation = self.extract_conversation_context(3)
        guide_system_prompt = "You are the advisor of a debate president. You are listening to the debate as it is happening" \
                              "and your goal is to propose to the president what his next action should be. The point " \
                              "of view of the debate president is that he has a objects on his list he MUST go " \
                              "through, but he doesnt need to lead them to completion. So when enough " \
                              "information on the item has been said, you must tell him to either wrap up and talk " \
                              "about the next item on the list or create atomic steps." \
                              "When an item is wrapped up, it will be given to another" \
                              "debate president in order to reduce the load on himself. Each item on the list should " \
                              "have roughly the same amount of rounds attributed to them (1 min, 3 rounds max). Sometimes the " \
                              "president will ask debaters to create the specific actions that will lead to the " \
                              "resolution of the item on his list. This is the 'atomic step creation' and should only " \
                              "happen when the granularity is high. when granularity is high that means that you " \
                              "cannot think of any way for the tasks to be broken down further. An atomic task should " \
                              "be able to be handled by a novice. Never forget that atomic task creation is rather " \
                              "rare and can only happen when all high level solutions have been explored. before " \
                              "suggesting the creation of atomic steps, always ask yourself if these requirements are " \
                              "fulfilled." \
                              "You have a few actions to choose from:" \
                              "1. Suggest to talk more deeply about a subject on the list.(same as 2 but more general, to gather more information on the subject)" \
                              "2. Suggest to ask the debaters for <specific information> that will help understand a subject on the list.(same as 1 but you have in mind what is the information missing)" \
                              "3. Suggest to wrap up on this subject.(never suggest the next topic, simply state that this topic should be wrapped up)" \
                              "4. Suggest to ask the debaters to create atomic steps.(remember the special requirements to suggest atomic steps!)" \
                              "remember that your <suggestion> will be given out of context to the president, " \
                              "so be thoughtful of your <suggestion>." \
                              "Offer you answer in the order provided by this format(first the reason and then the suggestion):\n" \
                              "<Reason why you chose this option and not the other options>\n" \
                              "[Suggestion: <suggestion, ALWAYS START WITH: 'I think you should...'>]"

        conversation_guide_agent = self.agent_manager.create_agent(model=ModelType.FUNCTION_CALLING_GPT_3_5,
                                                                   messages=fused_conversation + 'dont forget to put your suggestion between []',
                                                                   system_prompt=guide_system_prompt, temperature=0.1,
                                                                   max_tokens=250)
        conversation_guide_agent.run_agent()
        agent_output = conversation_guide_agent.get_text()

        # Regular expression pattern to match text inside the first pair of square brackets
        pattern = r"\[(.*?)\]"

        # Use the search method to find the first match
        match = re.search(pattern, agent_output)

        # If there's a match, extract the 'suggestion' group
        if match:
            suggestion = match.group(1).strip()
            analysis_agent = self.agent_manager.create_agent(
                model=ModelType.GPT_3_5_TURBO,
                messages=suggestion,
                system_prompt="Analyze the following text and determine which of the four options has been chosen by the agent."
                              "1. Suggest to talk more deeply about a subject on the list.(same as 2 but more general, to gather more information on the subject)" \
                              "2. Suggest to ask the debaters for <specific information> that will help understand a subject on the list.(same as 1 but you have in mind what is the information missing)" \
                              "3. Suggest to wrap up on this subject.(never suggest the next topic, simply state that this topic should be wrapped up)"
                              "4. Suggest to ask the debaters to create atomic steps.(remember the special requirements to suggest atomic steps!)"
                              "give your answer like this: Option Chosen:[<Number1 or Number2 or Number3 or Number4>]",
                temperature=0.1,
                max_tokens=100
            )
            analysis_agent.run_agent()
            agent_choice = analysis_agent.get_text()
            option_match = re.search(r"(\b1\b|\b2\b|\b3\b|\b4\b)", agent_choice)
            if option_match and option_match.group(1) == "3":
                return "wrap-up"
            elif option_match and option_match.group(1) == "4":
                return "atomic_steps"
            else:
                return suggestion
        else:
            return ""

    def extract_conversation_context(self, number_of_rounds_to_extract=1, target_extraction=None, max_rounds=None):
        """
        Extracts the context of the conversation from the specified number of recent rounds.

        :param number_of_rounds_to_extract: The number of rounds to extract from the end of the rounds list.
        :param target_extraction: The target list of rounds from which to extract the conversation context.
                                  Defaults to self.rounds if not specified.
        :param max_rounds: The maximum number of rounds to consider for extraction.
        :return: A string that fuses the conversation context with markers.
        """
        if target_extraction is None:
            target_extraction = self.rounds

        # If max_rounds is specified, limit the target_extraction to the last max_rounds entries
        if max_rounds is not None:
            target_extraction = target_extraction[-max_rounds:]

        # Determine the number of rounds to extract
        rounds_to_extract = min(number_of_rounds_to_extract, len(target_extraction))
        context_messages = target_extraction[-rounds_to_extract:]

        round_start_marker = "\n--- START OF ROUND ---\n"
        round_end_marker = "\n--- END OF ROUND ---\n"

        # Pattern to match the role at the beginning of the text, accounting for any number of spaces
        role_pattern = re.compile(r"^\w+\s*:")

        fused_conversation = ""
        for round_ in context_messages:
            fused_conversation += round_start_marker
            for speech in round_:
                for role, text in speech.items():
                    # Check if the text starts with the role name followed by a colon (and optional spaces)
                    if role_pattern.match(text):
                        # Remove the role prefix if it's already there
                        text = role_pattern.sub("", text).strip()
                    # Now prepend the role name to ensure consistent formatting
                    fused_conversation += f"{role}:\n{text}\n\n"
            fused_conversation += round_end_marker

        return fused_conversation.strip()

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
            let them choose weather they have something to say by giving context that might help them share their 
            specialized opinion on the subject.

            When presented with a numbered list of items to discuss, you are to address each item sequentially, 
            focusing on one issue at a time without introducing multiple items simultaneously. Listen to the debaters 
            if they want to add more information to an item in the list. Upon completion of an item, 
            this will clearly be stated :'Completion Noted: [Solution Found]'. When the discussion is finished write 
            [CONVO_END] to end the debate. Always add 'Debate President: ' when you start to talk and never talk for 
            more than 300 words. Maintain a vigilant watch for unbiased facilitation, steering clear of influencing 
            the direction of solutions or asking specific participants for input. The debaters have a very short 
            memory, so reminders of prior conclusions are necessary for continuity. Now, here is the context of the 
            project:"""


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
            problem at a time, never bring up multiple problems or items at a time. The completion of an item in the 
            list occurs when either a step-by-step solution is found, described in atomic steps that are detailed and 
            explicit to the point where further division would be inefficient, or when the item is too complex to 
            articulate in atomic steps and requires a more in-depth exploration. In the latter case, it should be 
            exported for further discussion.

            When complexity escalates beyond the scope of debate it means that creating atomic steps is impossible 
            because of the complexity.

            Upon completion of an item or if the item is deemed to complex to handle in this discussion, this will 
            clearly be stated :'Completion Noted: [Solution Found]'. This procedural closure signals the readiness 
            for a transition to a new debate or a different stage of project development. Always add 'Debate 
            President: ' when you start to talk and never talk for more than 300 words. When the discussion is 
            finished, write [CONVO_END] to end the debate.

            The debaters have a very short memory, so you must provide them with the conclusions from the previous 
            rounds to deepen the discussion.You must never create summaries of the discussion, unless an item is 
            completed! Now, here is the context of the project:"""

            self.session_president = self.agent_manager.create_agent(model=ModelType.FUNCTION_CALLING_GPT_3_5,
                                                                     messages='empty',
                                                                     system_prompt=president_system_prompt + self.convo_prompt + "never forget to address only one point at a time and let the debaters propose solutions! Your job is to lead not work!",
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

    def start_role_playing_session(self, num_rounds=8):
        if self.session_president is None:
            self.appoint_session_president()
        self.appoint_session_agents()
        count = 0  # should be 0
        self.round_manager = RoundManager(self.convo_manager, self.agent_manager, self.session_president, self.agents,
                                          self.session_type,
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
