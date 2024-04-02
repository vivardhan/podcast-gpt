# System Imports
from typing import Union

# Package Imports
from data_api.audio_download.audio_downloader import AudioDownloader
from data_api.audio_download.feed_config import (
	RSSFeedConfig,
	YoutubeFeedConfig,
)
from data_api.audio_download.rss.rss_audio_downloader import RSSAudioDownloader
from data_api.audio_download.youtube.youtube_audio_downloader import YoutubeAudioDownloader

def DownloaderFactory(name: str, config: Union[YoutubeFeedConfig, RSSFeedConfig]) -> AudioDownloader:
	if type(config) == YoutubeFeedConfig:
		return YoutubeAudioDownloader(name, config)
	elif type(config) == RSSFeedConfig:
		return RSSAudioDownloader(name, config)
	else:
		raise ValueError("Unknown config type!")