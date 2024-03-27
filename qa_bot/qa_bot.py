# System Imports
import json
from typing import List

# Third Party Imports
from openai import OpenAI

# Package Imports
from data_api.utils.gcs_utils import (
	download_textfile_as_string_gcs,
	list_files_gcs,
)
from data_api.utils.file_utils import create_temp_local_directory
from data_api.utils.paths import Paths
from google_client_provider import GoogleClientProvider
from podcasts import PODCASTS
from qa_bot.vector_db import DatabaseMatch, VectorDB

class QABot:

	client = OpenAI()
	GPT_MODEL = "gpt-4-0125-preview"

	def __init__(self, gc_provider: GoogleClientProvider):
		self.gc_provider = gc_provider
		self.system_prompt = 'You answer the user\'s questions based on the provided context.'
		self.k = 4

		print("Loading vector database.")
		self.vector_db = VectorDB(self.gc_provider)
		
		print("Loading context database.")
		self.context_db = {
			# Podcast Title is outermost key
			podcast.name : {
				# Episode Title is middle key
				Paths.get_title_from_path(chapterized_file) :
				# Chapter Title is inner most key, Chapter transcript is value
				json.loads(
					download_textfile_as_string_gcs(
						self.gc_provider, 
						chapterized_file,
					)
				)
				for chapterized_file in list_files_gcs(
					self.gc_provider, 
					Paths.get_chapterized_data_folder(podcast.name), 
					Paths.JSON_EXT,
				)
			}
			for podcast in PODCASTS
		}

		self.base_prompt = """
		The following is a set of chapters from transcribed podcasts.
		Answer the question that follows them using the information in the chapters.
		Provide detailed, factually accurate and thorough answers.
		Quote the speakers of the podcast liberally when it helps answer the question better.
		Refer to speakers in the podcast in the third person.
		"""

		self.quit_string = 'q'

		self.podcast_name_to_title = {
			"hubermanlab": "Huberman Lab Podcast",
			"PeterAttiaMD": "The Peter Attia Drive Podcast",
		}


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
				self.podcast_name_to_title[match.podcast_title], 
				match.episode_title, 
				match.chapter_title, 
				self.context_db[match.podcast_title][match.episode_title][match.chapter_title],
			)
			for match in database_matches
		] + [question])

	def answer_question(self, question: str) -> str:
		db_matches = self.vector_db.get_topk_matches(question, self.k)
		print("matches: {}".format(db_matches))
		return self.client.chat.completions.create(
		    messages=[
		        {'role': 'system', 'content': self.system_prompt},
		        {'role': 'user', 'content': self.construct_prompt(question, db_matches)},
		    ],
		    model=self.GPT_MODEL,
		    temperature=0,
		).choices[0].message.content

	def answer_questions(self):
		print("Hello, I answer questions based on 'The Huberman Lab Podcast' and 'The Drive Podcast'.")
		print("When prompted, type your question and hit enter and I'll attempt to answer it.")
		print("Once you're done, just type '{}' and hit enter.".format(self.quit_string))

		while True:
			curr_question = input("Enter your question:")
			if curr_question == self.quit_string:
				print("Thanks, bye!")
				break

			print(self.answer_question(curr_question))