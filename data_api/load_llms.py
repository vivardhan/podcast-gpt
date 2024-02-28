from transformers import pipeline, set_seed

"""
Goal: Utilities for various LLM related calls.
1. Load LLM with a given model name
2. Craft various kinds of prompts for inference: 
	2a: 0-shot learning in an instruction format.
	2b: n-shot learning with input n and a pointer to examples.
3. Calling LLM on a given prompt
"""

# The function loads the LLM and returns the generator to play with.
def load_llm(model_name = 'gpt2', seed = 21):
    generator = pipeline('text-generation', model='gpt2')
    set_seed(seed)
    return generator

"""
Convert any incoming raw_prompt into a question answering setup and see if that makes a difference.
"""
def zero_shot_learning(raw_prompt):
    return f'Question: {raw_prompt}\nAnswer:'


"""
The function transforms an input prompt into an n shot learning prompt using existing examples.
"""
def create_n_shot_learning(raw_prompt: str, examples: dict, n: int) -> str:
    prompt = ''
    count = 0
    for ques, ans in examples.items(): 
        if count >= n: break
        prompt += f"Question: {ques}\nAnswer: {ans}"
        count += 1
    print("Created the following prompt: \n" + prompt)
    return prompt


if __name__ == '__main__':
    model = load_llm()
    raw_prompt = "Who is Huberman?"
    prompt_list = [raw_prompt, zero_shot_learning(raw_prompt)]
    for prompt in prompt_list:
    	print(prompt)
    	output = model("Who is Huberman?", max_length=180, truncation=True)
    	print(output[0]['generated_text'])