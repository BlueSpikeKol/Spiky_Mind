import json
from pathlib import Path
import traceback

import re

from utils.openai_api import gpt_calling
from utils.openai_api.models import ModelType
from architect_module.multi_agent_workflow import agent_recruitment

class RoundManager:
    def __init__(self, agent_manager, session_president, agents):
        """
        Initialize the RoundManager class.

        Parameters:
            agent_manager: The manager for GPT agents.
            session_president: The agent serving as the president of the debate.
            agents: The agents participating in the debate.
        """
        self.agent_manager = agent_manager
        self.session_president = session_president
        self.agents = agents
        self.rounds = []
        self.summaries = []
    def play_introduction_round(self):
        """
        Play the introduction round where each agent presents themselves.
        """
        introductions = []

        for agent in self.agents:  # Loop through each agent except the president
            # Update the message for the agent
            agent.update_agent(messages = 'present yourself in under 25 words to the debate circle. They need to know what you are capable of. example:"I am a public relations specialist, i will help you handle the public side of this projecct with my experiencce in the field. I am happy to collaborate to this discussion"',temperature = 0.2)
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

        self.session_president.update_agent(messages=prior_conversations)
        self.session_president.run_agent()
        president_output = self.session_president.get_text()

        # Initialize a list to hold the output of this round
        this_round_output = [{self.session_president.agent_name: president_output}]

        # Step 2: Each agent decides whether to interject
        for agent in self.agents:
            query = 'Would you like to interject on this issue given by the debate president? Only interject if you think you can bring useful information and explore the subject according to your profession (a farmer should only talk about the implementation of a certain feature in the context that he is a farmer). Answer with YES or NO and no other choice in between.'
            agent.update_agent(messages=president_output + query, max_tokens=3, temperature=0.1, logit_bias={9891: 10, 2201: 10} )
            for i in range(3):  # Initial run + 2 additional tries
                agent.run_agent()
                interject_response = agent.get_text().strip().lower()

                # Step 3: If agent chooses to interject
                if re.search(r'\byes\b', interject_response):
                    agent.update_agent(messages=president_output, max_tokens=300, temperature=0.7)
                    agent.run_agent()
                    agent_output = agent.get_text()
                    this_round_output.append({agent.agent_name: agent_output})
                    break  # Break out of the loop

                # Step 4: If agent chooses not to interject
                elif re.search(r'\bno\b', interject_response):
                    print(interject_response + ' this was the agent response to the interjection choice')
                    this_round_output.append({agent.agent_name: 'did not talk this round'})
                    break
                else:
                    print(f"Invalid response received on attempt {i + 1}. Rerunning the agent.")

        # Append this round's output to the list of rounds
        self.rounds.append(this_round_output)
    def format_single_round(self, round_, summary=False):
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
                    user_content += content

        # Process user_content through the summarize_round_debaters function only if summary is True
        if summary:
            user_content = self.summarize_round_debaters(user_content)

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
    def summarize_round_debaters(self, user_content):
        """
        Summarize the content provided by agents during a round.

        Parameters:
            user_content: The content to be summarized.

        Returns:
            A string containing the summarized content.
        """
        summarizing_system_prompt = "All of the parties involved are trying to answer a single question from their point of view. Could you put all of their suggestions and important points into a single, easily readable, bullet-point text? If bullet points cannot capture the idea, you can write a short text to accompany it."
        summarizing_agent = self.agent_manager.create_agent(model=ModelType.CHAT_GPT4, messages=user_content,
                                                            system_prompt=summarizing_system_prompt)
        summarizing_agent.run_agent()
        summary = summarizing_agent.get_text()
        return summary

    def format_prior_conversations(self):
        """
        Format prior conversations to prepare for the next round.

        Returns:
            A list containing formatted content of all prior rounds.
        """
        formatted_rounds = []
        summary_rounds = []  # Initialize an empty list to store summary rounds

        for round_ in self.rounds:
            single_round = self.format_single_round(round_)
            formatted_rounds.append(single_round)

            # Create the summary version of this round
            summary_round = self.format_single_round(round_, summary=True)
            summary_rounds.append(summary_round)

        # Save the summary rounds to self.summaries
        self.summaries = self.flatten_rounds(summary_rounds)

        return self.flatten_rounds(formatted_rounds)

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
    def save_rounds_and_summaries(self, count):
        """
        Save the rounds and their summaries to disk.

        Parameters:
            count: The current round number.
        """
        try:
            with open('conversation_rounds.json', 'w') as json_file:
                json.dump(self.rounds, json_file, indent=4)
            with open('conversation_summaries.json', 'w') as json_file:
                json.dump(self.summaries, json_file, indent=4)
            print(f"Rounds and summaries saved up to round {count}.")
        except Exception as e:
            print(f"Failed to save rounds and summaries due to: {e}")


class ConversationManager:
    def __init__(self, input_prompt: str):
        self.agent_manager = gpt_calling.GPTManager()
        self.convo_prompt = input_prompt
        self.session_president = None
        self.agents = None
        self.round_manager = None

    def start_role_playing_session(self, num_rounds=10):
        self.appoint_session_president()
        self.appoint_session_agents()
        count = 0
        self.round_manager = RoundManager(self.agent_manager, self.session_president, self.agents)

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
            self.round_manager.save_rounds_and_summaries(count)

    def appoint_session_president(self):
        pre_president_system_prompt = "You will receive a task or project description and your job is to make a summary of it. make sure that no key points are omited, it's better to have more than not enough. No need for a conclusion of your own, focus entirely on the task or project given"
        pre_president_agent = self.agent_manager.create_agent(model=ModelType.CHAT_GPT4, messages=self.convo_prompt, system_prompt=pre_president_system_prompt)
        pre_president_agent.run_agent()
        president_directives = pre_president_agent.get_text()
        president_system_prompt = """You are the president of a debate circle who's goal is to discuss a project and, unless asked otherwise in this format (TALK ABOUT SPECIFIC SUBJECT:<SPECIFIC_SUBJECT>), you must explore the project organically.
        Your job is never to propose solutions, but to expose problems, logic fallacies and explore the subject in order to avoid blindspots.Never flip roles with the debaters! you share a common interest with the debaters to solve issues and advance the project.
        Never forget that the main task is to lead the other debaters so they can solve problems in the project.If the debaters cannot answer or find your directives unclear they will answer with [Cannot Process Directives: <Reason for incompletion>].
        You must lead them clearly with only one problem at a time, you must avoid bringing multiple issues at the same time. Always add 'Debate President: ' when you start to talk. Avoid calling out to any specific participant, let them choose wether they have something to say by giving context that might help them share their specialized opinion on the subject.
        Here is the context of the project:"""
        self.session_president = self.agent_manager.create_agent(model=ModelType.FUNCTION_CALLING_GPT4, messages='empty', system_prompt=president_system_prompt+president_directives, agent_name= "Debate President")
    def appoint_session_agents(self):
        agents = agent_recruitment.recruit_agents(self.convo_prompt)
        self.agents = []  # Initialize an empty list to store agent objects
        for agent_info in agents:
            bonus_context = f"whenever you are asked to tackle issues that are not very similar to your domain, do not try to act outside of your role as a {agent_info['role']}, but instead view the issues from the point of view of a {agent_info['role']}."
            role_context = agent_info['role'] +': '+ agent_info['context'] + bonus_context
            agent = self.agent_manager.create_agent(
                model=ModelType.FUNCTION_CALLING_GPT_3_5,
                messages="empty",
                system_prompt=role_context,
                agent_name=agent_info['role']
            )
            self.agents.append(agent)  # Append the created agent to self.agents list

