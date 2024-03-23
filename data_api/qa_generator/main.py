# System Imports
import json
import os

# Package Imports
from data_api.utils.gcs_utils import (
	download_textfile_as_string_gcs,
    list_files_gcs,
    upload_string_as_textfile_gcs,
)
from data_api.utils.paths import Paths
from data_api.qa_generator.llm_qa_generator import LLMQAGenerator
from data_api.qa_generator.gpt4 import GPT4QAGenerator
from google_client_provider import GoogleClientProvider


# Specify a mapping between model names to concrete implementations of LLMQAGenerator subclesses here:
qa_generator_models = {
	"gpt4": GPT4QAGenerator,
}

def main():
	gc_provider = GoogleClientProvider()


	# Uncomment the following once qa_generator_models above is setup
	for model_name, model_class in qa_generator_models.items():
		model = model_class(model_name)
		for podcast_name, config in podcast_configs.items():
			chapterized_transcript_prefix = os.path.join(podcast_name, TEXT_DATA_FOLDER, CHAPTERIZED_DATA_FOLDER)
			qa_pairs_prefix = os.path.join(podcast_name, TEXT_DATA_FOLDER, QA_PAIRS_FOLDER)
			chapterized_files = list_files_gcs(gc_provider, chapterized_transcript_prefix, JSON_EXT)
			for t in chapterized_files:
				text = download_textfile_as_string_gcs(gc_provider, t)
				chapters_json = json.loads(text)
				chapters_qa_pairs = {
					chapter: model.generate_question_answer_pairs(transcript)
					for chapter, transcript in chapters_json.items()
				}

				print(chapters_qa_pairs)
				break
					
				# output_file_path = os.path.join(qa_pairs_prefix, model_name, t)
				# upload_string_as_textfile_gcs(output_file_path, json.dumps(qa_pairs))

if __name__ == "__main__":
    main()