from dataclasses import dataclass
from typing import List, Dict
import json
import re
from pathlib import Path

from utils.openai_api import gpt_calling
from utils.openai_api.models import ModelType


@dataclass
class Role:
    name: str
    description: str


def recruit_agents(convo_prompt: str) -> List[Dict[str, str]]:
    current_script_path = Path(__file__).resolve()
    parent_folder = current_script_path.parent
    file_path = parent_folder.joinpath('agent_roles_permanent.json')
    agent_roles, agent_context = get_roles(file_path)

    chosen_roles = select_roles(agent_roles, convo_prompt)

    chosen_agents = []
    for role in chosen_roles:
        if role in agent_context:
            chosen_agents.append({"role": role, "context": agent_context[role]})
        else:
            #TODO make it retry to add it with a small correction in prompt
            print(f"Failed to add agent: {role} due to no matching context.")

    return chosen_agents


def get_roles(file_path: Path) -> (List[str], Dict[str, str]):
    with open(file_path, 'r') as f:
        agent_context = json.load(f)

    # Convert keys to lowercase
    agent_context = {k.lower(): v for k, v in agent_context.items()}
    agent_roles = list(agent_context.keys())

    return agent_roles, agent_context


def select_roles(agent_roles: List[str], convo_prompt: str) -> List[str]:
    agent_manager = gpt_calling.GPTManager()
    agent_roles_str = '\n'.join(map(str, agent_roles))
    system_prompt = f"""Roles:{agent_roles_str}. Given the project or task description below and the available roles displayed here, choose 2 roles that could bring important points of view and contribute to the project.
     You are not allowed to invent roles that are not in the list above. Bear in mind that in any coding task, there should be a Software Developer and a Project Manager, if possible.
     Display your answer like this:
1.[<role1>]
2.[<role2>]
<reason to choose each>"""
    recruitment_agent = agent_manager.create_agent(model=ModelType.GPT_3_5_TURBO, messages=convo_prompt,
                                                   system_prompt=system_prompt, max_tokens=150)
    recruitment_agent.run_agent()
    chosen_roles = recruitment_agent.get_text()

    pattern = r'\[(.*?)\]'
    chosen_roles_parsed = re.findall(pattern, chosen_roles)

    # Convert to lowercase
    chosen_roles_parsed = [role.lower() for role in chosen_roles_parsed]

    return chosen_roles_parsed


if __name__ == "__main__":
    convo_prompt = "This is a fake project description for a test, give me a random result"
    chosen_agents = recruit_agents(convo_prompt)
    print(chosen_agents)
