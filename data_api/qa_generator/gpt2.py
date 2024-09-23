from transformers import pipeline, set_seed, AutoTokenizer, AutoModelForCausalLM
from typing import Any, List, Tuple
from llm_qa_generator import LLMQAGenerator


class GPT2QAGenerator(LLMQAGenerator):
    """docstring for ClassName"""

    def __init__(self):
        super().__init__(
            "gpt2"
        )  # Call the constructor of LLMQAGenerator with model_name = 'gpt2''
        # self.model_name = additional_value

    def load_llm(self, model_name):
        pipe = pipeline("text-generation", model=model_name)
        set_seed(seed=21)
        print(
            f"""New text generation pipeline of model: {model_name} is setup.
            The max token size is {pipe.tokenizer.model_max_length}"""
        )
        return pipe

    def create_qa_prompt(self, raw_prompt: str) -> str:
        """
        Embellishes a raw prompt to add the context of question answer generation.
        """

        return (
            """
        Given the conversation below from a podcast, extract a list of questions and answers for each salient point discussed. \
        The questions and answers should refer to the speakers in the third person. \
        Return the resulting question-answer pairs in a json format: [\{question: "", answer:""\}]
        """
            + raw_prompt
            + "\n\nQuestion Answer Pairs:\n"
        )

    def iterate_over_transcript(self, transcript: str, chunk_size: int):
        """
        Given a transcript file, create a prompt to run inference with.
        This function yields portions of the transcript with each portion being
        up to `chunk_size` in length.

        Params:
            transcript (str): The string from the transcript file.
            chunk_size (int): The maximum size of each chunk to yield.

        Yields:
            str: A portion of the transcript of length <= `chunk_size`.
        """

        start_idx = 0

        # Iterate over the transcript in increments of chunk_size
        while start_idx < len(transcript):
            # Calculate end index for the current chunk
            end_idx = start_idx + chunk_size

            # Yield the current chunk of the transcript
            yield self.create_qa_prompt(transcript[start_idx:end_idx])

            # Update the start index for the next chunk
            start_idx = end_idx

    def run_model_inference(self, prompt: str) -> str:
        """
        Runs inference on self.model using the provided prompt.

        params:
            prompt: The prompt text

        returns:
            The model output text
        """
        output = self.pipeline(prompt, max_length=1000, truncation=True)[0][
            "generated_text"
        ]
        print(f"\n" + output + "\n")
        # return output

    def parse_model_output(self, model_output: str) -> List[Tuple[str, str]]:
        """
        Parse the model output into a list of question answer pairs

        params:
            model_output: inference result

        returns
            a List of question answer tuples, i.e.:
            [
                (question_1, answer_1),
                ...
                (question_n), answer_n),
            ]
        """
        pass

    def generate_question_answer_pairs(
        self, transcript: str
    ):  # -> List[Tuple[str, str]]:
        """
        Generates QA pairs using self.model for a transcript

        You do not need to re-implement this function for a child class

        params:
            transcript: The text for a transcript

        returns:
            a List of question answer tuples, i.e.:
            [
                (question_1, answer_1),
                ...
                (question_n), answer_n),
            ]
        """
        for prompt in self.iterate_over_transcript(transcript, 400):
            output = self.run_model_inference(prompt)
        # prompt = self.create_transcript_prompt(transcript)

        # return self.parse_model_output(output)


if __name__ == "__main__":
    file = open("data_api/qa_generator/example_transcript_1.txt", "r")
    transcript = file.read()
    gpt2_instance = GPT2QAGenerator()
    gpt2_instance.generate_question_answer_pairs(transcript)

# output = gpt2_instance.pipeline(raw_prompt)
# print(output[0]['generated_text'])
