# System Imports
from bisect import bisect
from dataclasses import dataclass
import json
import os
from typing import Dict, List, Optional

# Package Imports
from data_api.audio_download.audio_downloader import MetadataKeys
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.paths import Paths

SENTENCE_END_PUNCTUATIONS = ['.', '?', '!']

@dataclass
class Boundary:
	"""
	Encapsulates information about a boundary in a transcript
	"""

	# The timestamp of a word
	timestamp: int

	# The index of a word
	index: int

def determine_sentence_boundaries(words_list: json) -> List[Boundary]:
	"""
	Determines timestamps at which there are sentence boundaries in a transcript, given its words_list

	params:
		words_list:
			The list of words, each element is formatted as follows:
			{"text": "something", "start": 10345, "end": 10350, "confidence": 0.99, "speaker": "A"},
			where "start" and "end" are in milliseconds

	returns:
		The list of boundaries at which there are sentence changes.
	"""

	boundaries = [Boundary(timestamp=0, index=0)]
	previous_word = None
	for index, w in enumerate(words_list):
		if previous_word and previous_word["text"][-1] in SENTENCE_END_PUNCTUATIONS:
			boundaries.append(
				Boundary(
					timestamp=previous_word["end"],
					index=index,
				)
			)

		previous_word = w

	return boundaries

def determine_speaker_change_boundaries(words_list: json) -> List[Boundary]:
	"""
	Determines timestamps at which the speaker changes in a transcript, given its words_list

	params:
		words_list:
			The list of words, each element is formatted as follows:
			{"text": "something", "start": 10345, "end": 10350, "confidence": 0.99, "speaker": "A"},
			where "start" and "end" are in milliseconds

	returns:
		The list of boundaries at which there are speaker changes.
	"""

	boundaries = [Boundary(timestamp=0, index=0)]
	curr_speaker = words_list[0]["speaker"]
	for index, w in enumerate(words_list):
		if w["speaker"] != curr_speaker:
			boundaries.append(Boundary(timestamp=w["end"], index=index))

		curr_speaker = w["speaker"]

	return boundaries

def determine_break_boundaries(words_list: json, num_speakers: int) -> List[Boundary]:
	"""
	Determines boundaries at which to split a transcript, given its words_list

	If there is only one speaker, the timestamps correspond to sentence boundaries.
	If there are more than one speaker, the timestamps correspond to speaker change boundaries.

	params:
		words_list:
			The list of words, each element is formatted as follows:
			{"text": "something", "start": 10345, "end": 10350, "confidence": 0.99, "speaker": "A"},
			where "start" and "end" are in milliseconds
		num_speakers:
			The number of speakers in the transcipt

	returns:
		The list of boundaries at which the transcript can be split
	"""
	if num_speakers == 1:
		return determine_sentence_boundaries(words_list)
	else:
		return determine_speaker_change_boundaries(words_list)

def count_num_speakers(words_list: json) -> int:
	"""
	Determines the number of speakers in a transcript, given its words_list

	params:
		words_list:
			The list of words, each element is formatted as follows:
			{"text": "something", "start": 10345, "end": 10350, "confidence": 0.99, "speaker": "A"},
			where "start" and "end" are in milliseconds

	returns:
		The no. of speakers.
	"""

	speakers = set()
	for w in words_list:
		speakers.add(w["speaker"])

	return len(speakers)


def map_aai_speaker_to_name(aai_speaker: str, podcast_host: str, podcast_guest: Optional[str]) -> str:
	"""
	Maps the assembly AI speaker identifier (A, B, etc.) to the speaker's name

	params:
		podcast_host:
			The podcast host name
		pocast_guest:
			The guest on the podcast episode
	"""
	if aai_speaker == 'A':
		return podcast_host
	else:
		return podcast_guest


def construct_chapter_text(words_list: json, start_index: int, end_index: int, num_speakers: int, podcast_host: str, podcast_guest: Optional[str]) -> str:
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
		podcast_host:
			The podcast host's name
		podcast_guest:
			The podcast guest name, if there was a guest

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
		if num_speakers > 1:
			if not prev_speaker or prev_speaker != curr_speaker:
				text = text.strip() + "\n\n{}:\n".format(map_aai_speaker_to_name(curr_speaker, podcast_host, podcast_guest))

		text += curr_word["text"] + " "
		prev_speaker = curr_speaker

	return text.strip()

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
	if (len(parts) > 3):
		print(timestamp)
	assert len(parts) <= 3

	conversion_factor = 1000
	milliseconds = 0
	for part in reversed(parts):
		milliseconds += conversion_factor * int(part)
		conversion_factor *= 60

	return milliseconds

class TranscriptChapterizer:

	def __init__(self, podcast_name: str, podcast_host: str):
		self.podcast_name = podcast_name
		self.podcast_host = podcast_host

	def _split_transcript_into_chapters(self, assembly_ai_transcript: json, metadata: json) -> Dict[str, str]:
		"""
		Given a transcript and chapter timestamps and titles, returns a list of chapter transcripts
		
		params:
			assembly_ai_transcript: 
				The raw transcript from assembly AI in json format
			metadata: 
				json formated metadata. with the following information:
					guest: The name of the podcast guest (or None) if there is no guest
					chapters: list of (timestamp, title) pairs describing chapters
					

		returns:
			Dictionary that maps chapter titles to transcript text for the chapter

		"""
		podcast_guest = metadata[MetadataKeys.GUEST_KEY]
		chapters = metadata[MetadataKeys.CHAPTERS_KEY]
		chapter_transcripts = {}
		words_list = assembly_ai_transcript["words"]
		num_speakers = count_num_speakers(words_list)
		transcript_break_boundaries = determine_break_boundaries(words_list, num_speakers)

		curr_index = 0
		for index, c in enumerate(chapters):
			start_time_str = c[0]
			title = c[1]

			start_time_ms = convert_timestamp_string_to_milliseconds(start_time_str)
			start_boundary_index = bisect(transcript_break_boundaries, start_time_ms, lo=curr_index, key=lambda elem : elem.timestamp)
			start_elem = transcript_break_boundaries[max(0, start_boundary_index - 1)]

			if index < len(chapters) - 1:
				end_time_ms = convert_timestamp_string_to_milliseconds(chapters[index + 1][0])
				end_boundary_index = bisect(transcript_break_boundaries, end_time_ms, lo=start_boundary_index, key=lambda elem : elem.timestamp)
			else:
				end_boundary_index = len(transcript_break_boundaries) - 1

			end_elem = transcript_break_boundaries[end_boundary_index] if end_boundary_index < len(transcript_break_boundaries) else transcript_break_boundaries[-1]

			chapter_transcripts[title] = construct_chapter_text(words_list, start_elem.index, end_elem.index, num_speakers, self.podcast_host, podcast_guest)
			curr_index = end_boundary_index

		return chapter_transcripts


	def chapterize_all_transcripts(self) -> None:
		"""
		Creates transcripts for each chapter in each transcript for this podcast

		returns:
			None
			
			The resulting chapterized transcripts are saved to gcs, one file per podcast episode
			Each file contains a dictionary mapping chapter headings and their transcripts, i.e.

			filename: "episode_1.json", contents:
			{
				"chapter_1": {"transcript_1 - hi, welcome"},
				"chapter_2": {"topic_1 - bla bla"},
					...
			}

		"""
		print("Running chapterization for {}".format(self.podcast_name))

		aai_transcripts_folder = Paths.get_aai_transcript_folder(self.podcast_name)
		aai_transcripts = GCSClient.list_files(aai_transcripts_folder, Paths.JSON_EXT)

		chapterized_data_folder = Paths.get_chapterized_data_folder(self.podcast_name)
		chapterized_files = GCSClient.list_files(chapterized_data_folder, Paths.JSON_EXT)

		audio_data_folder = Paths.get_audio_data_folder(self.podcast_name)
		metadata_files = set(GCSClient.list_files(audio_data_folder, Paths.METADATA_SUFFIX + Paths.JSON_EXT))
		for aai_transcript in aai_transcripts:
			title = Paths.get_title_from_path(aai_transcript)

			metadata_file = Paths.get_metadata_file_path(self.podcast_name, title)
			if metadata_file not in metadata_files:
				continue

			chapterized_file = Paths.get_chapterized_transcript_path(self.podcast_name, title)
			if chapterized_file in chapterized_files:
				continue

			print("Chapterizing: {}".format(title))
			transcript_text = GCSClient.download_textfile_as_string(aai_transcript)
			metadata_text = GCSClient.download_textfile_as_string(metadata_file)

			chapterized_transcript = self._split_transcript_into_chapters(json.loads(transcript_text), json.loads(metadata_text))
			GCSClient.upload_string_as_textfile(chapterized_file, json.dumps(chapterized_transcript))

