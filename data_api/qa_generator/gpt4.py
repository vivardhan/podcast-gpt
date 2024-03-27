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
		self.model_version = "gpt-4-0125-preview"

	def create_qa_prompt(self, podcast_host: str, episode_title: str, chapter_title: str, chapter_transcript: str) -> str:
		"""
		Given an episode title, chapter title and chapter transcript, creates a prompt to run inference with.

		params:
			podcast_host:
				The name of the podcast host
			episode_title: 
				The title of the episode
			chapter_title: 
				The title of the current chapter from the episode
			chapter_transcript: 
				The transcript of current chapter

		returns:
			The prompt text
		"""
		return  """
        The following is an excerpt from a podcast hosted by {}. 
        The title of the current episode of the podcast is {}.
        The topic being discussed in the current excerpt from this episode is {}.
        
        Extract question answer pairs from the excerpt, covering the following areas, if possible:
        1. Facts in the discussion.
        2. Advice for resolving an issue.
        3. Strategies for optimizing for specific personal goals.
        4. Explanations of nuanced or complex ideas and topics.

        When framing the questions, follow these rules as far as possible:
        1. Ensure that the question makes sense to a reader who is unfamiliar with the content of the excerpt.
        2. Avoid references to the podcast, speakers, episode title or chapter title.
        3. Do not assume any knowledge of the provided excerpt by the reader of the question. 
        4. Ask questions from the point of view of a person who has never read the excerpt. In particular do not use 
        using phrases such "from the discussion", "was discussed", "in the excerpt", "as described", etc.


        If a question or answer refers to the podcast host or other speakers, it should do so in the third person. 
        Provide detailed, well explained answers and thorough answers. 
        Except for fact based questions, answers should typically be much longer than the questions.
        """.format(podcast_host, episode_title, chapter_title) + \
        'Return the question-answer pairs in json format: [\{question: "Question here.", answer:"answer here."\}]' + \
        "Excerpt: {}\nQuestion Answer Pairs:\n".format(chapter_transcript)

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