# System Imports
from typing import List, Tuple

# Third Party Imports
from openai import OpenAI

# Package Imports
from data_api.qa_generator.llm_qa_generator import LLMQAGenerator

class GPT4QAGenerator(LLMQAGenerator):
	"""
	Uses Open AI's GPT 4 model to generate QA pairs
	"""

	def __init__(self, model_name: str):
		super().__init__(model_name)

	def load_llm(self, model_name: str) -> any:
		"""
		Loads the LLM and returns it

		params:
			model_name: The string identifier for the model
		
		returns:
			The initialized model
		"""
		self.openai_client = OpenAI()
		self.model_version = "gpt-3.5-turbo-0125"

	def create_qa_prompt(self, transcript: str) -> str:
		"""
		Given a transcript file, creats a prompt to run inference with.

		params:
			transcript: The string from the transcript file

		returns:
			The prompt text
		"""
		return  """
        Given the conversation below from a podcast, extract a list of questions and answers for each salient point discussed. \
        The questions should be focussed on broad insights rather than on individual details. Questions and answers should \
        refer to the speakers in the third person. \
        Return the resulting question-answer pairs in a json format: [\{question: "First question here.", answer:"First answer here."\}]
        """ + transcript + '\nQuestion Answer Pairs:\n'

	def run_model_inference(self, prompt: str) -> str:
		"""
		Runs inference on self.model using the provided prompt.

		params:
			prompt: The prompt text

		returns:
			The model output text
		"""
		return self.openai_client.chat.completions.create(
			model = self.model_version,
  			response_format={ "type": "json_object" },
  			messages=[
  				{"role": "system", "content": "You are a helpful assistant designed to output JSON."},
  				{"role": "user", "content": prompt},
  			],
		).choices[0].message.content

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
		print(model_output)
		return model_output