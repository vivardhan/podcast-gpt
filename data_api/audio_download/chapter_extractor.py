# System Imports
import abc
import re
from typing import List, Tuple


class ChapterExtractor(metaclass=abc.ABCMeta):

	FULL_TIMESTAMP_PATTERN = '(\n[0-9][0-9]:[0-5][0-9]:[0-5][0-9] )(.*?\n)'

	# See https://stackoverflow.com/questions/8318236/regex-pattern-for-hhmmss-time-string
	# timestamp_pattern = '?:(?:([01]?\d|2[0-3]):)?([0-5]?\d):)([0-5]?\d'
	# The minor modification from the Stackoverflow post is to remove the optionality of the minute block
	# i.e. at least one colon is required.
	PARTIAL_TIMESTAMP_PATTERN = '(?:(?:([01]?\d|2[0-3]):)?([0-5]?\d):)([0-5]?\d)'

	@abc.abstractmethod
	def __call__(self, description: str) -> List[Tuple[str, str]]:
		"""
		Given the description of video, extract a list of chapter timestamp and title pairs

		Params:
			description: The text description of the video

		Returns:
			A list of tuples. Each tuple contains a chapter timestamp and title pair, eg:
			[
				("00:00:00", "Introduction"),
				("00:02:40", "Sponsors"),
				...
			]
		"""
		pass

class HubermanChapterExtractor(ChapterExtractor):

	def __init__(self):
		self.chapters_header = '\n\nTimestamps'

	def __call__(self, description: str) -> List[Tuple[str, str]]:
		curr_pos = description.find(self.chapters_header)
		if curr_pos == -1:
			return None

		curr_pos += len(self.chapters_header)
		chapters = re.findall(ChapterExtractor.FULL_TIMESTAMP_PATTERN, description[curr_pos:])

		# Strip away the new line and space characters
		return [(c[0].strip(), c[1].strip()) for c in chapters]

class LexFridmanChapterExtractor(ChapterExtractor):

	def __init__(self):
		self.chapters_header = '\n\nOUTLINE:'

	def __call__(self, description: str) -> List[Tuple[str, str]]:
		curr_pos = description.find(self.chapters_header)
		if curr_pos == -1:
			return None

		curr_pos += len(self.chapters_header)
		pattern = ChapterExtractor.PARTIAL_TIMESTAMP_PATTERN + '( - )' + '(.*?\n)'
		matches = re.findall(pattern, description[curr_pos:])

		chapters = []
		for m in matches:
			timestamp = m[2] # seconds
			if not m[1] == '':
				timestamp = m[1] + ':' + timestamp

			if not m[0] == '':
				timestamp = m[0] + ':' + timestamp

			chapters.append(
				(
					timestamp,
					# The description is the last group
					# Strip whitespace
					m[4].strip(),
				)
			)

		return chapters


class PeterAttiaChapterExtractor(ChapterExtractor):

	def __call__(self, description: str) -> List[Tuple[str, str]]:
		# First clean the description by replacing all href tags with the contained text.
		# Eg. '<a href= "2021-05-11%2003:15:00%20EDT">3:15</a>' will be replaced by '3:15'
		href_pattern = '(\<a href\=.*?\>)(.*?)(\<\/a\>)'
		nohrefs = re.sub(href_pattern, r'\g<2>', description)

		# The pattern is expected to be a list of <li> </li> tags, with the contained text as follows:
		# "chapter title [hh:mm:ss]"
		# There are some exceptions to this, which are accounted for i.e.:
		# 1. The opening <li> tag might have some additional attributes
		# 2. The square brackets around the timestamp may be parentheses instead
		# 3. There may be some additional text within the brackets containing the timestamp (before or after hh:mm:ss)
		# 4. The timestamp may be truncated, eg. 1:45 or 3:24;17 or 00:1:30 - see the comment above for the pattern
		pattern = '(\<li.*?\>)(.*?[\[|\(].*?)' + ChapterExtractor.PARTIAL_TIMESTAMP_PATTERN + '(.*?[\]|\)].*?\<\/li\>)'

		matches = re.findall(pattern, nohrefs)

		chapters = []
		for m in matches:
			timestamp = m[4] # seconds
			if not m[3] == '':
				timestamp = m[3] + ':' + timestamp

			if not m[2] == '':
				timestamp = m[2] + ':' + timestamp

			chapters.append(
				(
					timestamp,
					# The description is the 1st group
					# Remove the open bracket and strip whitespace
					m[1][:-1].strip(),
				)
			)

		return chapters