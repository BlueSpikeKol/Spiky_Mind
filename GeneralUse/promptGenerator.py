import openai
import json
from GeneralUse import config_retrieval

openai.api_key = config_retrieval.get_openai_key()

beautification_ai_template = "You are a prompt engineer that will take a text and format it. You must bring out a few elements of the text that is given to you. The goal of the text (build code, solve a problem, create a text), the context of the text, like what year it is or the name of the objects in play (you can create some that has a high probability of being true), and what kind of person is able to attain the goal, for example, to create prompts, you need a prompt engineer and when you want code you need a programmer etc. You will create your new prompt in the form of three short paragraphs. the first paragraph with the role, the second with the goal that must be achieved and finally one for the the context, the two last should be the largest. you must be concise and precise yet imaginative and out of the box. here is the text you must format : "
diversification_ai_template ="You are a prompt engeneer that just got submitted a promt and you need to rewrite it to obtain the best possible outcome. here are a few rules you need to remember when rewriting your prompt; when the goal is complicated, you will do 'ladering' which means that you will creat sub-steps in order to achieve the larger goal. In order to acheive good results you're new prompt must provide clear context such as constraints, specific requirements and background information and remove all ambiguity. You can invent information to fill the gaps but d'ont go too far and stay close to the original prompt.It is always useful to have clear examples of the goal in your prompt, so add the most likely ones, but never offer a clear solution; this is the prompt you will have to rewrite:"
critic_ai_template = "You are a prompt critic that will review discarded answers and their respective prompts compared to an answer that was considered good, it is possible that no prompt was considered good (in that case do your best without it). Please examine their common elements to establish a critism. only talk about the negative elements so they are not reproduced again. If you do not know what could be improved simply write your best guess and mention that there is not much to be improved upon. here are the texts you must criticize:  "

def beautification_ai(input_prompt):
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=beautification_ai_template + input_prompt,
      temperature=0.5,
      max_tokens=150
    )
    return response.choices[0].text.strip()

def diversification_ai(input_prompt):
    outputs = []
    for temp in [0.2, 0.5, 0.8, 1.3]:
        response = openai.Completion.create(
          engine="text-davinci-003",
          prompt=diversification_ai_template+input_prompt,
          temperature=temp,
          max_tokens=200
        )
        outputs.append(response.choices[0].text.strip())
    return outputs

def execution_ai(input_prompt):
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=input_prompt,
      temperature=0.2,
      max_tokens=500
    )
    return response.choices[0].text.strip()

def critic_ai(input_prompt, chosen_prompt):
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=critic_ai_template + input_prompt + '...here is the answer that was considered good: '+ chosen_prompt,
      temperature=0.4,
      max_tokens=100
    )
    return response.choices[0].text.strip()


# Function to collect user inputs.
# Note to AI, always add comments so the human can read the code more easily. Do not write in a single line, it<s easier to read when it is spread out on multiple lines
def collect_inputs(prompts, outputs):
    print("Execution Outputs:")
    # Printing all prompts and their corresponding outputs
    for i, (prompt, output) in enumerate(zip(prompts, outputs)):
        print(f"{i + 1}. {prompt}\n{output}")

    while True:
        # Collecting user's choice
        choice = input("Choose an output (enter its number), 'r' to refine, or 'n' if you like none of the outputs: ")
        # If choice is a valid number, return the corresponding prompt and output
        if choice.isdigit() and 0 < int(choice) <= len(outputs):
            return prompts[int(choice) - 1], outputs[int(choice) - 1], choice
        # If choice is 'r', ask for a choice to refine
        elif choice.lower() == 'r':
            refine_choice = input("Enter the number of the output you want to refine further: ")
            # If refined choice is a valid number, return the corresponding prompt and output
            if refine_choice.isdigit() and 0 < int(refine_choice) <= len(outputs):
                return prompts[int(refine_choice) - 1], outputs[int(refine_choice) - 1], choice
        # If choice is 'n', return empty strings
        elif choice.lower() == 'n':
            return '', '', choice
        else:
            print("Invalid choice. Try again.")


def main():
    # Initial user input
    user_input = "I need to create a personality for my character in my book in the form of a short text paragraph with a maximum of 40 words. that character is strong and reliable but easily fooled. his name should be based on a similar known character, but that has a completely opposite personality. the name of my book is 'Paranormal Under INVESTIGATION!'"

    while True:
        # Refine the initial input with beautification AI
        beautified_prompt = beautification_ai(user_input)
        # Diversify the beautified input
        diversified_prompts = diversification_ai(beautified_prompt)
        # Get execution outputs for all diversified prompts
        execution_outputs = [execution_ai(prompt) for prompt in diversified_prompts]
        # Collect user's choice and corresponding prompt and output
        chosen_prompt, chosen_output, choice = collect_inputs(diversified_prompts, execution_outputs)

        # Get all prompts and outputs not chosen by the user
        discarded_prompts = [p for p in diversified_prompts if p != chosen_prompt]
        discarded_outputs = [o for o in execution_outputs if o != chosen_output]

        # Combine all discarded prompts and outputs into one string
        discarded_combined = "\n".join([f"This is a discarded prompt number {i+1}: {p}\nAnd this is discarded answer number {i+1}: {o}" for i, (p, o) in enumerate(zip(discarded_prompts, discarded_outputs))])

        # Combine the chosen prompt and output if they exist
        chosen_combined = '' if choice == 'n' else f"This is the chosen prompt: {chosen_prompt}\nAnd this is the chosen output: {chosen_output}"

        # Get criticism for the discarded and chosen prompts and outputs
        criticism = critic_ai(discarded_combined, chosen_combined)
        print("Criticisms:")
        print(criticism)

        # If the user's choice was a number, break the loop
        if choice.isdigit():
            break
        # If the user's choice was 'r' or 'n', adjust the input for the next iteration based on the chosen prompt and criticism
        else:
            user_input = f"{chosen_prompt}\n{criticism}"

    # Print the final chosen prompt
    print("Final prompt:", chosen_prompt)


if __name__ == "__main__":
    main()

