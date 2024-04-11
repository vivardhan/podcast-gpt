# System Imports
from dataclasses import dataclass
from typing import List, Union

# Package Imports
from data_api.audio_download.chapter_extractor import (
    ChapterExtractor,
    HubermanChapterExtractor,
    LexFridmanChapterExtractor,
    PeterAttiaChapterExtractor,
)

@dataclass
class YoutubeFeedConfig:
    # Config for a podcast with a Youtube Feed

    """
    Unique Identifer for the Youtube Channel

    To get the channel_id for a youtube channel:
    1. Go to the channel's homepage.
    2. Right click and choose "View Page Source"
    3. Search for "externalId"
    4. Use the corresponding string as the input string to this function
    """
    channel_id: str

    # Audio extension for downloaded audio files
    audio_extension: str

    # The chapter extractor instance
    chapter_extractor: ChapterExtractor


hubermanlab_config = YoutubeFeedConfig(
    channel_id="UC2D2CMWXMOVWx7giW1n3LIg",
    audio_extension="mp4",
    chapter_extractor=HubermanChapterExtractor(),
)

lexfridman_config = YoutubeFeedConfig(
    channel_id="UCSHZKyawb77ixDdsGog4iWA",
    audio_extension="mp4",
    chapter_extractor=LexFridmanChapterExtractor(),
)

@dataclass
class RSSFeedConfig:
    # Config for a podcast with an RSS Feed

    # RSS Feed URL
    url: str

    # Audio extension for downloaded audio files
    audio_extension: str

    # A list of strings to prevent certain file names from being downloaded
    filter_out: List[str]

    # The chapter extractor instance
    chapter_extractor: ChapterExtractor

peterattia_config = RSSFeedConfig(
    url="https://peterattiadrive.libsyn.com/rss",
    audio_extension="mp3",
    filter_out=["rebroadcast", "Rebroadcast", "re-release", "Qualy"],
    chapter_extractor=PeterAttiaChapterExtractor(),
)
