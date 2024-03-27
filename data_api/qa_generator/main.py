# System Imports
import json
import os

# Third Party Imports
from matplotlib import pyplot as plt
import numpy as np
import tiktoken
from tqdm import tqdm

# Package Imports
from data_api.utils.gcs_utils import (
	download_textfile_as_string_gcs,
    list_files_gcs,
    upload_string_as_textfile_gcs,
)
from data_api.utils.paths import Paths
from data_api.qa_generator.llm_qa_generator import LLMQAGenerator
from data_api.qa_generator.gpt4 import GPT4QAGenerator
from data_api.utils.paths import Paths
from google_client_provider import GoogleClientProvider
from podcasts import PODCASTS


# Specify a mapping between model names to concrete implementations of LLMQAGenerator subclesses here:
qa_generator_models = {
	"gpt4": GPT4QAGenerator,
}

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def main():
	gc_provider = GoogleClientProvider()

	# Uncomment the following once qa_generator_models above is setup
	for model_name, model_class in qa_generator_models.items():
		model = model_class(model_name)
		all_token_counts = []
		all_large_counts = {}
		for podcast in PODCASTS:
			chapterized_data_folder = Paths.get_chapterized_data_folder(podcast.name)
			qa_pairs_folder = Paths.get_qa_pairs_folder(podcast.name)
			chapterized_files = list_files_gcs(gc_provider, chapterized_data_folder, Paths.JSON_EXT)
			
			print("Counting tokens for {}".format(podcast.name))
			for t in tqdm(chapterized_files):
				text = download_textfile_as_string_gcs(gc_provider, t)
				chapters_json = json.loads(text)
				episode_title = Paths.get_title_from_path(t)

				curr_counts = {
					chapter_title: num_tokens_from_string(chapter_transcript, "cl100k_base")
					for chapter_title, chapter_transcript in chapters_json.items()
				}

				large_counts = {
					chapter_title: count
					for chapter_title, count in curr_counts.items()
					if count > 8191
				}

				if len(large_counts) > 0:
					all_large_counts[episode_title] = large_counts

				all_token_counts.extend(curr_counts.values())





	counts, bins = np.histogram(all_token_counts)
	plt.figure()
	plt.hist(bins[:-1], bins, weights=counts)
	plt.xlabel("Num Tokens")
	plt.ylabel("Num chapters")
	plt.savefig('/Users/vkanoria/Desktop/counts.png')

	all_large = []
	for k, v in all_large_counts.items():
		print("Episode: {}: \nLong Chapters:".format(k))
		all_large.extend(v.values())
		for chapter_name, count in v.items():
			print("{}: {}".format(chapter_name, count))

	print("Num large files: {}".format(len(all_large)))
	plt.figure()
	counts, bins = np.histogram(all_large)
	plt.hist(bins[:-1], bins, weights=counts)
	plt.xlabel("Num Tokens")
	plt.ylabel("Num chapters")
	plt.savefig('/Users/vkanoria/Desktop/counts_large.png')

				# print("Generating QA pairs for {}".format(episode_title))
				# chapters_qa_pairs = {
				# 	chapter: model.generate_question_answer_pairs(podcast.host_name, episode_title, chapter, transcript)
				# 	for chapter, transcript in chapters_json.items()
				# }

				# print(chapters_qa_pairs)
				# break
					
				# output_file_path = os.path.join(qa_pairs_prefix, model_name, t)
				# upload_string_as_textfile_gcs(output_file_path, json.dumps(qa_pairs))

if __name__ == "__main__":
    main()