# System Imports
from dataclasses import dataclass, field
import os
from typing import List, Tuple, Union

# Package Imports
from data_api.audio_download.audio_downloader import (
	AudioDownloader,
	DownloadStream,
)
from data_api.audio_download.factory import DownloaderFactory
from data_api.audio_download.feed_config import (
	hubermanlab_config,
	peterattia_config,
	RSSFeedConfig,
	YoutubeFeedConfig,
)
from data_api.speech_to_text.assembly_ai_transcriber import AudioTranscriber
from data_api.qa_generator.transcript_chapterizer import TranscriptChapterizer
from google_client_provider import GoogleClientProvider

@dataclass
class Episode:
	"""Encapsulates information about a single podcast episode"""

	# The name of the podcast that this episode belongs to
	podcast_name: str

	# Episode title
	title: str

	# List of chapters in pairs of timestamp and chapter heading
	chapters: List[Tuple[str, str]]

def remove_extension(path: str) -> str:
	# Removes the extension of a file path
	dot_pos = path.rfind('.')
	return path[:dot_pos]

@dataclass
class Podcast:
	"""Encapsulates information about a podcast"""

	# Name of the podcast
	name: str

	# The feed configuration for this podcast's data source
	feed_config: Union[YoutubeFeedConfig, RSSFeedConfig]

	# Google Client Provider
	gc_provider: GoogleClientProvider

	# The audio downloader instance
	audio_downloader: AudioDownloader = field(init=False)

	# The audio transcriber instance
	audio_transcriber: AudioTranscriber = field(init=False)

	# The transcript chapterizer instance
	transcript_chapterizer: TranscriptChapterizer = field(init=False)

	# The episodes in this podcast
	episodes: List[Episode] = field(init=False)

	def __post_init__(self):
		self.audio_downloader = DownloaderFactory(self.name, self.feed_config, self.gc_provider)
		self.audio_transcriber = AudioTranscriber(self.gc_provider, self.name, self.feed_config.audio_extension)
		self.transcript_chapterizer = TranscriptChapterizer(self.gc_provider, self.name)

	def run_data_extraction_pipeline(self):
		print("Extracting data for: {}".format(self.name))

		# Download all audios
		downloaded_files = self.audio_downloader.download_all_audios()

		self.episodes = [
			Episode(
				podcast_name=self.name,
				title=remove_extension(os.path.basename(f.downloaded_name)),
				chapters=f.chapters,
			)
			for f in downloaded_files
		]

		titles = [e.title for e in self.episodes]

		# Transcribe all episodes
		self.audio_transcriber.transcribe_all_audio_files(titles)

		# Chapterize transcripts
		self.transcript_chapterizer.chapterize_all_transcripts(titles)

gc_provider = GoogleClientProvider()
huberman_lab = Podcast(
	name="hubermanlab",
	feed_config=hubermanlab_config,
	gc_provider=gc_provider,
)
peterattia_md = Podcast(
	name="PeterAttiaMD",
	feed_config=peterattia_config,
	gc_provider=gc_provider,
)

PODCASTS = [
	huberman_lab,
	peterattia_md,
]
