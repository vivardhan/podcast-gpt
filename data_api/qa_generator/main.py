# System Imports
import json
import os

# Package Imports
from configs import (
	podcast_configs, 
	RAW_TRANSCRIPT_FOLDER,
	TEXT_DATA_FOLDER,
	TXT_EXT,
	QA_PAIRS_FOLDER,
)
from data_api.utils.gcs_utils import (
	download_textfile_as_string_gcs,
    list_files_gcs,
    upload_string_as_textfile_gcs,
)
from google_client_provider import GoogleClientProvider
from llm_qa_generator import LLMQAGenerator

# Instantiate your LLM QA generation models here:
"""
qa_generators = [
	Generator_1("model_name_1", seed=5),
	...
	Generator_n("model_name_n", seed=42),
]
"""

def main():
	gc_provider = GoogleClientProvider()
	for podcast_name, config in podcast_configs.items():
		raw_transcript_prefix = os.path.join(podcast_name, TEXT_DATA_FOLDER, RAW_TRANSCRIPT_FOLDER)
		qa_pairs_prefix = os.path.join(podcast_name, TEXT_DATA_FOLDER, QA_PAIRS_FOLDER)
		transcript_files = list_files_gcs(gc_provider, raw_transcript_prefix, TXT_EXT)

		for t in transcript_files:
			text = download_textfile_as_string_gcs(gc_provider, t)
			for g in generators:
				pass
				# Uncomment this section once qa_generators, above, is setup
				# qa_pairs = g.generate_question_answer_pairs(text)
				# output_file_path = os.path.join(qa_pairs_prefix, g.model_name, t)
				# upload_string_as_textfile_gcs(output_file_path, json.dumps(qa_pairs))
