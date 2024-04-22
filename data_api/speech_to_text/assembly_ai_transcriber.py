# System Imports
from concurrent.futures import ProcessPoolExecutor
import json
import requests
from typing import List

# Third Party Imports
import assemblyai as aai

# Package Imports
from data_api.utils.file_utils import (
    create_temp_local_directory,
    delete_temp_local_directory,
)
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.paths import Paths

# Replace with your API key
aai.settings.api_key = "9b22f02582ac4fdf892ba609d1080da0"

base_url = "https://api.assemblyai.com/v2/transcript/"
headers = {'authorization': aai.settings.api_key}

config = aai.TranscriptionConfig(speaker_labels=True)
transcriber = aai.Transcriber()

def get_aai_transcript(aai_transcript_id: str) -> str:
    try:
        return requests.get(url=base_url + aai_transcript_id, headers=headers).json()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

class AudioTranscriber:

    def __init__(self, podcast_name: str, extension: str):
        self.podcast_name = podcast_name
        self.extension = extension

    def find_untranscribed_episodes(self) -> List[str]:
        """
        Looks for episodes that have not been transcribed for this podcast

        returns:
            A list of episode titles to transcribe 
        """

        print("Looking for untranscribed_files for {} ...".format(self.podcast_name))
        untranscribed_files = []

        # Get a list of all audio files for this podcast
        audio_folder = Paths.get_audio_data_folder(self.podcast_name)
        audio_files = GCSClient.list_files(audio_folder, self.extension)

        # Create a set of the existing transcripts (raw, speaker labeled and original from Assembly AI)
        raw_transcript_folder = Paths.get_raw_transcript_folder(self.podcast_name)
        raw_transcript_files = set(GCSClient.list_files(raw_transcript_folder, Paths.TXT_EXT))
        speaker_transcript_folder = Paths.get_speaker_transcript_folder(self.podcast_name)
        speaker_transcript_files = set(GCSClient.list_files(speaker_transcript_folder, Paths.TXT_EXT))
        aai_transcript_folder = Paths.get_aai_transcript_folder(self.podcast_name)
        aai_transcript_files = set(GCSClient.list_files(aai_transcript_folder, Paths.JSON_EXT))
        
        for audio_file in audio_files:
            title = Paths.get_title_from_path(audio_file)
            raw_transcript_file = Paths.get_raw_transcript_path(self.podcast_name, title)
            speaker_transcript_file = Paths.get_speaker_transcript_path(self.podcast_name, title)
            aai_transcript_file = Paths.get_aai_transcript_path(self.podcast_name, title)

            # Check if any of the transcripts do not exist
            if (
                raw_transcript_file not in raw_transcript_files or 
                speaker_transcript_file not in speaker_transcript_files or
                aai_transcript_file not in aai_transcript_files
            ):
                untranscribed_files.append(Paths.get_title_from_path(audio_file))

        return untranscribed_files

    def transcribe_audio(self, episode_title: str) -> None:
        """
        Use Assembly AI to transcribe the audio and upload the transcripts to GCS

        params:
            episode_title:
                The episode title

        returns:
            None
        """
        print("Transcribing {}".format(episode_title))

        # Download the audio
        audio_path = Paths.get_audio_path(self.podcast_name, episode_title, self.extension)
        GCSClient.download_file(audio_path)

        # Transcribe with AAI
        transcript = transcriber.transcribe(audio_path, config=config)

        raw_transcript_path = Paths.get_raw_transcript_path(self.podcast_name, episode_title)

        # Save raw transcript locally
        with open(raw_transcript_path, "w") as f:
            f.writelines([
                utterance.text + " \n" for utterance in transcript.utterances
            ])
            f.close()

        # Upload raw transcript to GCS
        GCSClient.upload_file(raw_transcript_path)

        speaker_transcript_path = Paths.get_speaker_transcript_path(self.podcast_name, episode_title)

        # Save speaker transcript locally
        with open(speaker_transcript_path, "w") as f:
            for utterance in transcript.utterances:
                f.write("Speaker {}: \n".format(utterance.speaker))
                f.write(utterance.text)
                f.write("\n\n")

            f.close()

        # Upload speaker transcript to GCS
        GCSClient.upload_file(speaker_transcript_path)

        # Upload AAI json transcript to GCS
        GCSClient.upload_string_as_textfile(
            Paths.get_aai_transcript_path(self.podcast_name, episode_title), 
            json.dumps(get_aai_transcript(transcript.id)),
        )


    def transcribe_all_audio_files(self) -> None:
        """
        Transcribes the audio files corresponding to the podcast

        The resulting transcripts are saved to GCS
        """

        # Create temporary local directories
        temp_folders = [
            Paths.get_audio_data_folder(self.podcast_name), 
            Paths.get_raw_transcript_folder(self.podcast_name), 
            Paths.get_speaker_transcript_folder(self.podcast_name),
        ]
        for tf in temp_folders:
            create_temp_local_directory(tf)

        # Find untranscribed files among the titles
        untranscribed_files = self.find_untranscribed_episodes()

        if len(untranscribed_files) > 0:
            print("Transcribing {} files for {}".format(len(untranscribed_files), self.podcast_name))
            
            # Transcribe the untranscribed files in parallel
            with ProcessPoolExecutor() as executor:
                executor.map(self.transcribe_audio, untranscribed_files)
        else:
            print("All audio files already transcribed for {}".format(self.podcast_name))

        # Delete local directories
        delete_temp_local_directory(self.podcast_name)
