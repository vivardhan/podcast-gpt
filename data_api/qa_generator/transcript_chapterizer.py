# System Imports
from bisect import bisect
import json
import os
from typing import Dict

# Package Imports
from configs import (
	ASSEMBLY_AI_FOLDER,
	AUDIO_DATA_FOLDER,
	CHAPTERS_SUFFIX,
	JSON_EXT,
	podcast_configs,
	TEXT_DATA_FOLDER,
	TXT_EXT,
)
from google_client_provider import GoogleClientProvider
from data_api.utils.file_utils import (
	create_temp_local_directory,
	delete_temp_local_directory,
)
from data_api.utils.gcs_utils import (
	download_file_gcs,
	file_exists_gcs,
	list_files_gcs,
)

def construct_chapter_text(words_list: json, start_index: int, end_index: int, num_speakers: int) -> str:
	"""
	Given the words list of an assembly AI transcript and the start and end index element
	of a chapter, construct text transcript for the chapter
	
	params:
		words_list:
			The list of words, each element is formatted as follows:
			{"text": "something", "start": 10345, "end": 10350, "confidence": 0.99, "speaker": "A"},
			where "start" and "end" are in milliseconds
		start_index:
			The index in words_list where the returned text should start
		end_index:
			The index in words_list where the returned text should end
			Note that this is a suggested end index. The logic followed in this function is: 
				- if there are multiple speakers, continue until the speaker changes
				- if there is only one speaker, stop at the end of the current sentence
		num_speakers:
			The number of speakers in this transcipt

	returns:
		A text transcript, eg.

		Speaker A:
		Hi, good to have you on the show!

		Speaker B:
		Glad to be here.

		Speaker A:
		Let's get started ...
	"""

	text = ""
	prev_speaker = None
	for index in range(start_index, end_index):
		curr_word = words_list[index]
		curr_speaker = curr_word["speaker"]
		if not prev_speaker or prev_speaker != curr_speaker:
			text = text.strip() + "\n\nSpeaker {}:\n".format(curr_speaker)

		text += curr_word["text"] + " "
		prev_speaker = curr_speaker

	text = text.strip()

	assert num_speakers >= 1
	
	if num_speakers == 1:
		while text[-1] not in ['.', '?', '!']:
			index += 1
			if index >= len(words_list):
				break

			curr_word = words_list[index]
			text += " " + curr_word["text"]
	else:
		while True:
			index += 1
			if index >= len(words_list):
				break

			curr_speaker = curr_word["speaker"]
			if curr_speaker != prev_speaker:
				break

			curr_word = words_list[index]
			text += " " + curr_word["text"]

	return text

def convert_timestamp_string_to_milliseconds(timestamp_string: str) -> int:
	"""
	Converts a timestamp string to milliseconds

	params:
		timestamp_str:
			The timestamp in hh:mm:ss format, possibly truncated, eg:
			02:34:27,
			00:23:17,
			2:45,
			3:23:51.

	returns:
		The timestamp in milliseconds
	"""
	parts = timestamp_string.split(':')
	assert len(parts) <= 3

	conversion_factor = 1000
	milliseconds = 0
	for part in reversed(parts):
		milliseconds += conversion_factor * int(part)
		conversion_factor *= 60

	return milliseconds


def split_transcript_into_chapters(assembly_ai_transcript: json, chapters: json) -> Dict[str, str]:
	"""
	Given a transcript and chapter timestamps and titles, returns a list of chapter transcripts
	
	params:
		assembly_ai_transcript: The raw transcript from assembly AI in json format
		chapters: json formated list of (timestamp, title) pairs describing chapters

	returns:
		Dictionary that maps chapter titles to transcript text for the chapter

	"""
	print(chapters)
	chapter_transcripts = {}
	words_list = assembly_ai_transcript["words"]
	curr_index = 0
	for index, c in enumerate(chapters):
		start_time_str = c[0]
		title = c[1]

		start_time_ms = convert_timestamp_string_to_milliseconds(start_time_str)
		start_elem = bisect(words_list, start_time_ms, lo=curr_index, key=lambda elem : elem['start'])

		if index < len(chapters) - 1:
			end_time_ms = convert_timestamp_string_to_milliseconds(chapters[index + 1][0])
			end_elem = bisect(words_list, end_time_ms, lo=start_elem, key=lambda elem : elem['end'])
		else:
			end_elem = len(words_list)

		chapter_transcripts[title] = construct_chapter_text(words_list, start_elem, end_elem, 2)
		curr_index = end_elem

	return chapter_transcripts


def main():
	gc_provider = GoogleClientProvider()
	for podcast_name, config in podcast_configs.items():
		assembly_transcripts_folder = os.path.join(podcast_name, TEXT_DATA_FOLDER, ASSEMBLY_AI_FOLDER)
		assembly_transcript_files = list_files_gcs(gc_provider, assembly_transcripts_folder, JSON_EXT)
		audio_folder = os.path.join(podcast_name, AUDIO_DATA_FOLDER)

		create_temp_local_directory(assembly_transcripts_folder)
		create_temp_local_directory(audio_folder)

		for transcript_file in assembly_transcript_files:
			print(transcript_file)
			chapters_filename = os.path.basename(transcript_file)[:-(len(JSON_EXT) + 1)] + "_{}.{}".format(CHAPTERS_SUFFIX, JSON_EXT)
			chapters_file = os.path.join(audio_folder, chapters_filename)

			if file_exists_gcs(gc_provider, chapters_file):
				download_file_gcs(gc_provider, chapters_file)
			else:
				continue

			download_file_gcs(gc_provider, transcript_file)

			transcript = open(transcript_file, "r")
			chapters = open(chapters_file, "r")

			chapter_transcripts = split_transcript_into_chapters(json.load(transcript), json.load(chapters))

			transcript.close()
			chapters.close()

			for title, chapter_text in chapter_transcripts.items():
				print("************************")
				print(title)
				print("************************")
				print(chapter_text)

			break

		delete_temp_local_directory(podcast_name)


if __name__ == "__main__":
    main()


