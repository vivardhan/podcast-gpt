# System Imports
from typing import List

# Third Party Imports
from openai import OpenAI

# Package Imports
from data_api.embeddings.vector_db.vector_search import DatabaseMatch, VectorSearch

class QABot:

	client = OpenAI()
	GPT_MODEL = "gpt-4-0125-preview"
	I_DONT_KNOW = "Sorry, the podcasts do not cover this topic."

	def __init__(self):
		self.system_prompt = 'You answer the user\'s questions based on the provided context.'
		self.k = 4

		self.base_prompt = f"""
		The following is a set of discussions from podcasts that may be helpful in answering a question.
		If none of the discussions are relevant to the question that follows, answer exactly as follows:
		{self.I_DONT_KNOW}
		Otherwise, answer the question using the discussion in the podcasts.
		Provide detailed, factually accurate and thorough answers.
		Quote the speakers of the podcast liberally when it helps answer the question better.
		Refer to speakers in the podcast in the third person.
		"""

		self.quit_string = 'q'


	def construct_prompt(self, question: str, database_matches: List[DatabaseMatch]) -> str:
		return  "\n".join([
			"""
			{}
			Podcast Name: {}
			Episode Title: {}
			Chapter Title: {}
			Transcript: 
			{}
			""".format(
				self.base_prompt,
				VectorSearch.podcast_name_to_title[match.podcast_title], 
				match.episode_title, 
				match.chapter_title, 
				match.chapter_transcript,
			)
			for match in database_matches
		] + [question])

	def answer_question(self, question: str) -> None:
		db_matches = VectorSearch.get_topk_matches(question, self.k)
		return db_matches, self.client.chat.completions.create(
		    messages=[
		        {'role': 'system', 'content': self.system_prompt},
		        {'role': 'user', 'content': self.construct_prompt(question, db_matches)},
		    ],
		    model=self.GPT_MODEL,
		    temperature=0,
		    stream=True,
		)


	def answer_questions(self):
		print("Hello, I answer questions based on 'The Huberman Lab Podcast' and 'The Peter Attia Drive Podcast'.")
		print("When prompted, type your question and hit enter and I'll attempt to answer it.")
		print("Once you're done, just type '{}' and hit enter.".format(self.quit_string))

		while True:
			curr_question = input("Enter your question:\n")
			if curr_question == self.quit_string:
				print("Thanks, bye!")
				break

			_, response = self.answer_question(curr_question)
			for chunk in response:
				content = chunk.choices[0].delta.content
				if content:
					print(content, end='')
				else:
					print('')