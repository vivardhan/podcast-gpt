# System Imports
from dataclasses import dataclass, field
from typing import Union

# Package Imports
from data_api.audio_download.audio_downloader import AudioDownloader
from data_api.audio_download.factory import DownloaderFactory
from data_api.audio_download.feed_config import (
	hubermanlab_config,
	lexfridman_config,
	peterattia_config,
	RSSFeedConfig,
	YoutubeFeedConfig,
)
from data_api.speech_to_text.assembly_ai_transcriber import AudioTranscriber
from data_api.chapterizer.transcript_chapterizer import TranscriptChapterizer

@dataclass
class Podcast:
	"""Encapsulates information about a podcast"""

	# Name of the podcast
	name: str

	# Name of the podcast host
	host_name: str

	# The feed configuration for this podcast's data source
	feed_config: Union[YoutubeFeedConfig, RSSFeedConfig]

	# The audio downloader instance
	audio_downloader: AudioDownloader = field(init=False)

	# The audio transcriber instance
	audio_transcriber: AudioTranscriber = field(init=False)

	# The transcript chapterizer instance
	transcript_chapterizer: TranscriptChapterizer = field(init=False)

	def __post_init__(self):
		self.audio_downloader = DownloaderFactory(self.name, self.feed_config)
		self.audio_transcriber = AudioTranscriber(self.name, self.feed_config.audio_extension)
		self.transcript_chapterizer = TranscriptChapterizer(self.name, self.host_name)

	def run_data_extraction_pipeline(self):
		print("Extracting data for: {}".format(self.name))

		# Download all audios
		self.audio_downloader.download_all_audios()

		# Transcribe all episodes
		self.audio_transcriber.transcribe_all_audio_files()

		# Chapterize transcripts
		self.transcript_chapterizer.chapterize_all_transcripts()

huberman_lab = Podcast(
	name="hubermanlab",
	host_name="Dr. Andrew Huberman",
	feed_config=hubermanlab_config,
)
peterattia_md = Podcast(
	name="PeterAttiaMD",
	host_name="Dr. Peter Attia",
	feed_config=peterattia_config,
)
lex_fridman = Podcast(
	name="lexfridman",
	host_name="Lex Fridman",
	feed_config=lexfridman_config,
)

PODCASTS = [
	huberman_lab,
	peterattia_md,
	# lex_fridman,
]
