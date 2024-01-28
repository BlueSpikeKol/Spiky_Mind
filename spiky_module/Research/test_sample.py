import os
import json
from pathlib import Path

import openai

import utils.openai_api.gpt_calling as gpt

"""
TODO:
    - Supprimer la fonction `create_partial_context` et la remplacer dans toutes les fonctions qui l'utilisaient
    - Ajouter toutes les docstrings
    - Supprimer le fait de devoir choisir après chaque message de rester dans la sous discussion.
    - Implémenter les logs pour tous les tokens utilisé par les models pour la génération de la discussion.
    - Ajouter une fonction générale pour sauvegarder les données.
"""


class TestSpiky:
    def __init__(self, format_fn, num_scenario: int = 0, custom_scenario: dict = None, auto_test: bool = True,
                 test_model: str = "gpt-3.5-turbo", form_model: str = "gpt-3.5-turbo",
                 main_discussion_model: str = "gpt-4", summary_model: str = "gpt-3.5-turbo",
                 sub_discussion_model: str = "gpt-3.5-turbo", openai_key: str = "auto",
                 encoding: str = "utf-8", path_logs: Path = None, discussion_started: bool = False):

        # If you want to test your program on a custom scenario
        if custom_scenario:
            self.scenario_input = custom_scenario["input_scenario"]
            self.full_scenario = custom_scenario["full_scenario"]

        else:
            ls_input_scenario = [
                f"The High School Coding Club in Anytown, USA, aims to bridge this knowledge gap with a "
                f"unique project targeted at elementary school children. The goal? To create an interactive,"
                f" web-based platform that introduces basic coding concepts through gamified experiences,"
                f" making technology accessible and enjoyable for the youngest learners.",
                f"The Boston-based startup 'MindSage' aims to redefine mental health management by "
                f"harnessing machine learning algorithms for real-time monitoring and intervention.",
                f"While e-commerce has revolutionized the way we shop, it has also contributed significantly"
                f" to environmental pollution and waste. Our venture aims to challenge the status quo by "
                f"creating a global e-commerce platform committed solely to eco-friendly and sustainable"
                f" products.", f"To create a global renewable energy grid that can redistribute solar, wind, and"
                               f" hydroelectric power across continents, balancing out energy deficits and surpluses."]

            self.scenario_input = ls_input_scenario[num_scenario]

            # Get the full scenario from txt file
            with open(f"scenario_{num_scenario}.txt", "r", encoding="utf-8") as fic:
                ls_data = fic.readlines()

            self.full_scenario = ""

            for i in ls_data:
                self.full_scenario += i + "\n"

        # Initialize general variable
        self.auto_test: bool = auto_test
        self.format_fn = format_fn
        self.data: dict = {}
        self.encoding: str = encoding
        self.discussion_started: bool = discussion_started

        self.logs = {"form": {"input_tokens": 0, "output_tokens": 0, "total": 0},
                     "main_discussion": {"ls_inputs": [], "ls_outputs": [], "total_inputs": 0, "total_outputs": 0,
                                         "total": 0},
                     "sub_discussion": {"ls_usages": [], "total_inputs": 0, "total_outputs": 0, "total": 0},
                     "summary_discussion": {"ls_inputs": [], "ls_outputs": [], "total_inputs": 0, "total_outputs": 0,
                                            "total": 0}, "total_inputs": 0, "total_outputs": 0, "total": 0}

        # Select if the tester is a model or a human
        self.main_discussion_model: str = main_discussion_model
        self.summary_model: str = summary_model
        self.form_model: str = form_model
        self.sub_discussion_model: str = sub_discussion_model

        if self.auto_test:
            self.test_model: str = test_model
        else:
            self.test_model: str = "human"

        # Create the AI agents
        self.gpt_main_discussion = gpt.GPTAgent(self.main_discussion_model)
        self.gpt_summary = gpt.GPTAgent(self.summary_model)
        self.gpt_form = gpt.GPTAgent(self.form_model)
        self.gpt_sub_discussion = gpt.GPTAgent(self.sub_discussion_model)

        if self.auto_test:
            self.gpt_test = gpt.GPTAgent(self.test_model)

        # Set the key for the openai API
        if openai_key == "auto":
            openai.api_key = os.environ.get("OPENAI_API_KEY")
        else:
            openai.api_key = openai_key

        # Get the path to save the logs
        if path_logs:
            self.path_logs = Path(path_logs)
        else:
            self.path_logs = Path(os.getcwd())

    def create_form(self) -> dict:
        """
        Generate a form which aim to gather general quantitative information only.
        The form is generated using the specified format for the context and the specified model

        :return: The form
        """
        messages = [{"role": "user", "content": self.format_fn(self.scenario_input)}]

        self.gpt_form.messages = messages

        all_data = self.gpt_form.run_agent()
        print("Creation of the form:", all_data)

        self.update_logs(["form", "input"], value=all_data["usage"]["prompt_tokens"], is_appending=False)
        self.update_logs(["form", "output"], value=all_data["usage"]["completion_tokens"], is_appending=False)

        response_message = {"content": all_data["choices"][0]["message"]["content"]}

        return response_message

    def update_logs(self, ls_index: list = [], value: int = 0, is_dict: bool = False, dict_value: dict = None,
                    is_appending: bool = True) -> None:
        if is_dict:
            self.logs["sub_discussion"]["ls_usages"].append(dict_value)
            self.logs["sub_discussion"]["total_inputs"] += dict_value["total_inputs"]
            self.logs["sub_discussion"]["total_outputs"] += dict_value["total_outputs"]
            self.logs["sub_discussion"]["total"] += dict_value["total"]
            self.logs["total_inputs"] += dict_value["total_inputs"]
            self.logs["total_outputs"] += dict_value["total_outputs"]
            self.logs["total"] += dict_value["total"]

        elif len(ls_index) == 1:
            pass

        elif len(ls_index) == 2:
            i, k = ls_index
            if is_appending:
                if "input" in k:
                    self.logs[i]["ls_inputs"].append(value)
                    self.logs[i]["total_inputs"] += value
                    self.logs[i]["total"] += value
                    self.logs["total_inputs"] += value
                    self.logs["total"] += value

                elif "output" in k:
                    self.logs[i]["ls_outputs"].append(value)
                    self.logs[i]["total_outputs"] += value
                    self.logs[i]["total"] += value
                    self.logs["total_outputs"] += value
                    self.logs["total"] += value

                else:
                    raise KeyError("Invalid key for the logs. Choose either 'input' or 'output'")
            else:
                if "input" in k:
                    self.logs[i]["input_tokens"] += value
                    self.logs[i]["total"] += value
                    self.logs["total_inputs"] += value
                    self.logs["total"] += value

                elif "output" in k:
                    self.logs[i]["output_tokens"] += value
                    self.logs[i]["total"] += value
                    self.logs["total_outputs"] += value
                    self.logs["total"] += value


        else:
            raise Exception(f"Invalid input parameter to update the logs.\nls_index: {ls_index}\nvalue: {value}"
                            f"\ndict_value: {dict_value}")

    def fill_form(self, form: dict) -> dict:
        """
        Complete the form using the specified model

        :param form: The form
        :return: The answers
        """
        ls_question = []
        temp = form["content"].split("\n")
        ls_answers = []
        msg = ""
        messages = [{"role": "user", "content": msg}]

        # Extract all the questions in a list
        for i in temp:
            if len(i) == 0:
                continue
            else:
                ls_question.append(i)

        # Answer the questions from the form
        for i in ls_question:
            msg = (f"Answer the following question with a short sentence. "
                   f"If you think a long sentence or a discussion is needed in order to answer correctly "
                   f"the question put 'discussion needed'. You can create information at will."
                   f"The context you will use to answer the "
                   f"question: \n{self.full_scenario}\nThe question you need to answer:\n{i}")

            messages[0]["content"] = msg
            self.gpt_test.messages = messages
            ls_answers.append(self.gpt_test.run_agent()["choices"][0]["message"]["content"])

        # Use a discussion to answer the more complex questions.
        ls_discussion = []
        for i in range(len(ls_answers)):
            if ls_answers[i][:17].upper() == "discussion needed".upper():
                ls_discussion.append(self.create_specified_conversation(ls_question[i]))

        summary_discussions = [i[0][list(i[0].keys())[0]] for i in ls_discussion]
        sub_discussions = [i[1][list(i[1].keys())[0]] for i in ls_discussion]

        return {"content": "\n".join(ls_answers),
                "summary_discussions": summary_discussions, "sub_discussions": sub_discussions}

    def fill_form_human(self, form: dict) -> dict:
        """
        Ask a human tester to complete the form
        :param form: dict all the questions
        :return: dict all the answers to the questions
        """
        ls_question = []
        temp = form["content"].split("\n")
        ls_answers = []

        for i in temp:
            if len(i) == 0:
                continue
            else:
                ls_question.append(i)

        print("Answer the following question with the shortest sentences possible. If you don't have the answer "
              "put 'N/A'. If you think a discussion is needed for this specific question put 'discussion needed'.")

        for i in ls_question:
            ls_answers.append(input(i + " "))

        ls_discussion = []
        for i in range(len(ls_answers)):
            if ls_answers[i][:17].upper() == "discussion needed".upper():
                ls_discussion.append(self.create_specified_conversation(ls_question[i]))

        summary_discussions = [i[0][list(i[0].keys())[0]] for i in ls_discussion]
        sub_discussions = [i[1][list(i[1].keys())[0]] for i in ls_discussion]

        return {"usage": None, "content": "\n".join(ls_answers),
                "summary_discussions": summary_discussions, "sub_discussions": sub_discussions}

    def create_specified_conversation(self, subject: str, nb_max_msg: int = 3) -> tuple:
        """
        Gather information about a specific subject related to the project.

        :param nb_max_msg: The maximum number of message of the subdiscussion when being in auto
        :param subject: str the subject
        :return: All the information gathered
        """
        all_information_gathered = False
        question = f"Answer the following question with the information you have for now.\n {subject}"

        ls_questions_answers = []
        answer = ""
        messages = [{"role": "user"}]

        # Save the logs of the entire subdiscussion before updating the general logs.
        local_logs = {"ls_inputs": [], "ls_outputs": [], "total_inputs": 0, "total_outputs": 0,
                      "total": 0}

        # Only used when the test is on auto. Allow the conversation to end after a fixed number of messages
        index = 0

        # Keep asking questions on the subject until all the information are gathered
        while not all_information_gathered:
            ls_questions_answers.append(question)

            if self.auto_test:
                self.gpt_test.messages = [{"role": "user", "content": f"Answer the following question to the best "
                                                                      f"of your ability with the following context. "
                                                                      f"If the context lack information, create it but "
                                                                      f"make it logical with regards to the context."
                                                                      f"The context:\n {self.full_scenario}\n"
                                                                      f"The question:\n {question}"}]
                answer = self.gpt_test.run_agent()["choices"][0]["message"]["content"]

            else:
                answer = input(question + " ")

            ls_questions_answers.append(answer)
            msg = ("With the following context: " + self.scenario_input +
                   "\nContinue the following conversation by asking a question.\n the conversation: " +
                   "\n".join(ls_questions_answers))

            if self.auto_test and index >= nb_max_msg:
                print("subdiscussion ended by max number of message reached")
                all_information_gathered = True

            elif not self.auto_test:
                if self.evaluate_enough_information(
                        self.create_partial_context(ls_questions_answers)) or index >= nb_max_msg:
                    print("subdiscussion ended by max number of message reached")
                    all_information_gathered = True

            else:
                messages[0]["content"] = msg
                self.gpt_sub_discussion.messages = messages

                all_data = self.gpt_sub_discussion.run_agent()
                question = all_data["choices"][0]["message"]["content"]

                # Update the local logs
                local_logs["ls_inputs"].append(all_data["usage"]["prompt_tokens"])
                local_logs["total_inputs"] += all_data["usage"]["prompt_tokens"]

                local_logs["ls_outputs"].append(all_data["usage"]["completion_tokens"])
                local_logs["total_outputs"] += all_data["usage"]["completion_tokens"]

                local_logs["total"] += all_data["usage"]["completion_tokens"] + all_data["usage"]["prompt_tokens"]

                index += 1

        self.update_logs(is_dict=True, dict_value=local_logs)

        summary_data = self.summarize_information(ls_questions_answers)

        self.update_logs(["summary_discussion", "input"], value=summary_data["usage"]["prompt_tokens"])
        self.update_logs(["summary_discussion", "output"], value=summary_data["usage"]["completion_tokens"])

        result = ({"summary: " + subject: summary_data["choices"][0]["message"]["content"]},
                  {"sub_discussion": ls_questions_answers})

        return result

    def create_partial_context(self, ls_msg) -> str:
        """
        Return a context for a GPT agent depending on the input scenario and the questions and answers already gathered

        :param ls_msg: list of all the questions/answers
        :return: str the context generated
        """
        if len(ls_msg) == 0:
            return ""

        all_questions = "\n".join(ls_msg)

        context = self.scenario_input + "\nTake also in account the following question and answer.\n" + all_questions

        return context

    def evaluate_enough_information(self, context) -> bool:
        """
        Return if there is enough information or not. Note that if the model think that there is enough
        information it will ask the user before closing this conversation.
        :param context: The actual context with all the information gathered through Q&A
        :return: bool If all the information are gathered or not.
        """

        # Isn't implemented yet but will ask the user for test purposes
        if self.auto_test:
            is_enough = False

            messages = [{"role": "user", "content": f"From the following context, evaluate if, for the person asking "
                                                    f"questions, it is needed to ask more questions in order to have "
                                                    f"a complete answer about the first question asked.\n"
                                                    f"The context:\n{context}"}]
            self.gpt_summary.update_agent(messages=messages, max_tokens=3, temperature=0.1,
                                          logit_bias={9891: 10, 2201: 10})

            result = self.gpt_summary.run_agent()["choices"][0]["message"]["content"]
            print(result)
            return True
        else:
            return input("Is there enough information? (y or n) ").upper() == "Y"

    def summarize_information(self, ls_qa: list) -> dict:
        """
        Summarize the information gained through a discussion. The summarized information will be around 100 tokens long
        :param ls_qa: list of questions and answers
        :return: str summarized information
        """
        msg = ("Summarize the information in the following questions and answers in a short text of "
               "around 100 tokens.\n The questions and answers:\n") + "\n".join(ls_qa)

        messages = [{"role": "user", "content": msg}]

        self.gpt_summary.messages = messages

        return self.gpt_summary.run_agent()

    def have_conversation(self, form: dict, answers: dict, previous_discussion: dict = None,
                          nb_max_discussion: int = 3) -> dict:
        # Format all the questions and answers form the form in one string
        ls_questions_form = form["content"].split("\n")
        ls_answers_form = answers["content"].split("\n")

        corpus_qa = ""
        index = 0

        for q, a in zip(ls_questions_form, ls_answers_form):

            corpus_qa += q + "\n"

            if a[:17].upper() == "discussion needed".upper():
                corpus_qa += answers["summary_discussions"][index] + "\n"
                index += 1

            else:
                corpus_qa += a + "\n"

        if previous_discussion is not None:
            print("The discussion had already been started previously.")
            for i in previous_discussion["questions"].keys():
                corpus_qa += previous_discussion["questions"][i] + "\n"
                corpus_qa += previous_discussion["answers"][i] + "\n"

        # Initialize all the useful variables
        discussion: bool = True
        index = 0
        msg = ""
        messages = [{"role": "user", "content": msg}]
        data_discussion = {"questions": {}, "answers": {}, "sub_discussions": []}

        while discussion:
            msg = (f"Ask a question to continue the on going conversation. This is the project your are talking about: "
                   f"{self.scenario_input}\n And this is the conversation until now: {corpus_qa}")
            messages[0]["content"] = msg
            self.gpt_main_discussion.messages = messages

            # Create a sub_discussion based on the question generated by the main model
            all_data = self.gpt_main_discussion.run_agent()
            question = all_data["choices"][0]["message"]["content"]

            # Update the logs before creating a new subdiscussion
            self.update_logs(["main_discussion", "input"], value=all_data["usage"]["prompt_tokens"])
            self.update_logs(["main_discussion", "output"], value=all_data["usage"]["completion_tokens"])

            result = self.create_specified_conversation(question, nb_max_msg=5)

            # Save all the information
            data_discussion["questions"][f"Q{index}"] = question
            data_discussion["answers"][f"Q{index}"] = result[0][f"summary: {question}"]
            data_discussion["sub_discussions"].append(result[1]["sub_discussion"])

            # update the Q&A corpus
            corpus_qa += question + "\n" + result[0][f"summary: {question}"] + "\n"

            index += 1

            # check if the user want to terminate the discussion
            if self.auto_test:
                discussion = index < nb_max_discussion
            else:
                discussion = not input("Do you want to stop the discussion? ").upper()[:3] == "yes".upper()

        return data_discussion

    def save_conversation(self, form: dict, answers_form: dict, discussions: dict,
                          filename_conv: str = "logs_test_conversation.json") -> None:
        """
        Save all the data from a discussion including the form pre-discussion in a JSON file.

        :param filename_conv:
        :param form:
        :param answers_form:
        :param discussions:
        :return: None
        """
        data = {"form": {"function": self.format_fn.__name__, "model": self.main_discussion_model,
                         "project_brief": self.scenario_input,
                         "questions": {}, "answers": {},
                         "summary_discussions": answers_form["summary_discussions"],
                         "sub_discussions": answers_form["sub_discussions"]},
                "conversation": {"questions": {}, "answers": {}, "sub_discussions": discussions["sub_discussions"]},
                "token_used": self.logs,
                "models": {"main_discussion_model": self.main_discussion_model, "summary_model": self.summary_model,
                           "test_model": self.test_model, "form_model": self.form_model,
                           "sub_discussion_model": self.sub_discussion_model}}

        ls_question_form = form["content"].split("\n")
        ls_answers_form = answers_form["content"].split("\n")
        index = 0

        for i, j in zip(ls_question_form, ls_answers_form):
            if len(i) == 0:
                continue
            else:
                data["form"]["questions"][f"Q{index}"] = i
                data["form"]["answers"][f"Q{index}"] = j
                index += 1

        for i in discussions["questions"].keys():
            data["conversation"]["questions"][i] = discussions["questions"][i]
            data["conversation"]["answers"][i] = discussions["answers"][i]

        with open(self.path_logs / filename_conv, "w", encoding=self.encoding) as fic:
            json.dump(data, fic, indent=4, ensure_ascii=False)

    def save_form(self, form: dict, answer_form: dict, filename_form: str = "logs_test_form.json") -> None:
        """
        Save the form and the answers to the form in a JSON file.
        It will also save other useful information such as the number of tokens used ect..

        :param filename_form:
        :param form: All the information available about the form
        :param answer_form: The answers of the form
        :return: None
        """
        data = {"function": self.format_fn.__name__, "model": self.main_discussion_model,
                "prompt": self.format_fn(self.scenario_input),
                "questions": {"usage": form["usage"]}, "answers": {},
                "summary_discussions": answer_form["summary_discussions"],
                "sub_discussions": answer_form["sub_discussions"]}

        ls_question_form = form["content"].split("\n")
        ls_answers_form = answer_form["content"].split("\n")
        index = 0

        for i, j in zip(ls_question_form, ls_answers_form):
            if len(i) == 0:
                continue
            else:
                data["questions"][f"Q{index}"] = i
                data["answers"][f"Q{index}"] = j
                index += 1

        with open(self.path_logs / filename_form, "w", encoding=self.encoding) as fic:
            json.dump(data, fic, indent=4, ensure_ascii=False)

    @staticmethod
    def extract_data_form(data: dict) -> dict:

        usage_q = data["questions"]["usage"]
        del data["questions"]["usage"]
        ls_question = list(data["questions"].values())

        ls_answers = list(data["answers"].values())

        q_form = {"content": "\n".join(ls_question), "usage": usage_q}
        a_form = {"content": "\n".join(ls_answers),
                  "summary_discussions": data["summary_discussions"], "sub_discussions": data["sub_discussions"]}

        return q_form, a_form

    def load_information(self, filename_form: str = "logs_test_form.json",
                         filename_conv: str = "logs_test_conversation.json") -> tuple:

        path_form = self.path_logs / filename_form
        path_conv = self.path_logs / filename_conv

        if path_conv.is_file():
            with open(path_conv, "r") as fic:
                data = json.load(fic)

            data_form = data["form"]
            data_conv = data["conversation"]

            q_form, a_form = self.extract_data_form(data_form)

            return a_form, q_form, data_conv

        elif path_form.is_file():
            with open(path_form, "r") as fic:
                data = json.load(fic)

            q_form, a_form = self.extract_data_form()

            return a_form, q_form

        else:
            print(f"No available data. If you have already started a conversation, "
                  f"make sure that the logs are in the following directory:\n{self.path_logs}")
            return (-1,)

    def test_form(self) -> None:
        """
        Test and save the result of the creation of forms.
        :return: None
        """
        form = self.create_form()

        if self.auto_test:
            answer_form = self.fill_form(form)
        else:
            answer_form = self.fill_form_human(form)

        self.save_form(form, answer_form)

    def test_conversation(self) -> None:
        form = self.create_form()

        if self.auto_test:
            answer_form = self.fill_form(form)
        else:
            answer_form = self.fill_form_human(form)

        all_data = self.have_conversation(form, answer_form, nb_max_discussion=10)

        self.save_conversation(form, answer_form, all_data, filename_conv="logs_test_long_conversation_gpt4.json")

    def run(self) -> None:

        if self.discussion_started:
            all_data = self.load_information()

            # In the case where there is no available data to load
            if all_data[0] == -1:
                self.test_conversation()
            else:
                self.have_conversation(all_data[1], all_data[0], all_data[2])

        else:
            # Execute the entire code
            self.test_conversation()


if __name__ == "__main__":
    import test_querry_gpt as test

    p = Path(os.getcwd()) / "logs"

    t = TestSpiky(test_model="gpt-3.5-turbo-16k-0613", main_discussion_model="gpt-4",
                  summary_model="gpt-3.5-turbo-16k-0613", form_model="gpt-4",
                  sub_discussion_model="gpt-3.5-turbo-16k-0613", auto_test=True,
                  format_fn=test.format_msg_9, num_scenario=0, path_logs=p)

    # print(t.full_scenario)
    print(t.path_logs)

    # t.run()
    t.test_conversation()
