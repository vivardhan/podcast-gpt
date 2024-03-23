# System Imports
from dataclasses import dataclass
from typing import List, Union

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

hubermanlab_config = YoutubeFeedConfig(
    channel_id="UC2D2CMWXMOVWx7giW1n3LIg",
    audio_extension="mp4",
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

peterattia_config = RSSFeedConfig(
    url="https://peterattiadrive.libsyn.com/rss",
    audio_extension="mp3",
    filter_out=["rebroadcast", "Rebroadcast", "re-release", "Qualy"],
)
