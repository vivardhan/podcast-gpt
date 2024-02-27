# System Imports
from typing import Union

# Package Imports
from audio_downloader import AudioDownloader
from configs import podcast_configs, RSSFeedConfig, YoutubeFeedConfig
from google_client_provider import GoogleClientProvider
from rss.rss_audio_downloader import RSSAudioDownloader
from youtube.youtube_audio_downloader import YoutubeAudioDownloader

def DownloaderFactory(name: str, config: Union[YoutubeFeedConfig, RSSFeedConfig], gc_provider: GoogleClientProvider) -> AudioDownloader:
	if type(config) == YoutubeFeedConfig:
		return YoutubeAudioDownloader(name, gc_provider)
	elif type(config) == RSSFeedConfig:
		return RSSAudioDownloader(name, gc_provider)
	else:
		raise ValueError("Unknown config type!")


def main():
	gc_provider = GoogleClientProvider()
	for name, config in podcast_configs.items():
		downloader = DownloaderFactory(name, config, gc_provider)
		downloader.download_all_audios(config)

if __name__ == "__main__":
    main()