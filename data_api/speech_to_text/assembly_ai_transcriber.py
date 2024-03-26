# System Imports
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
import json
import os
import requests
from typing import List

# Third Party Imports
import assemblyai as aai

# Package Imports
from data_api.utils.file_utils import create_temp_local_directory, delete_temp_local_directory
from data_api.utils.gcs_utils import (
    download_file_gcs,
    file_exists_gcs,
    list_files_gcs,
    upload_string_as_textfile_gcs,
    upload_to_gcs,
)
from data_api.utils.paths import Paths
from google_client_provider import GoogleClientProvider

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

@dataclass
class AudioToTranscribe:
    """Encapsulates input and output paths for the audio to transcribe"""

    # Audio file input
    audio_path: str

    # Raw transcript output
    raw_transcript_path: str

    # Speaker transcript output
    speaker_transcript_path: str

    # Assembly AI json output
    aai_transcript_path: str


class AudioTranscriber:

    def __init__(self, gc_provider: GoogleClientProvider, podcast_name: str, extension: str):
        self.gc_provider = gc_provider
        self.podcast_name = podcast_name
        self.extension = extension

    def find_untranscribed_audio_files(self) -> List[AudioToTranscribe]:
        """
        Looks for audio files that have not been transcribed for this podcast

        returns:
            A list of audio files to transcribe 
        """

        print("Looking for untranscribed_files for {} ...".format(self.podcast_name))
        untranscribed_files = []

        audio_folder = Paths.get_audio_data_folder(self.podcast_name)
        audio_files = list_files_gcs(self.gc_provider, audio_folder, self.extension)
        raw_transcript_folder = Paths.get_raw_transcript_folder(self.podcast_name)
        raw_transcript_files = set(list_files_gcs(self.gc_provider, raw_transcript_folder, Paths.TXT_EXT))
        speaker_transcript_folder = Paths.get_speaker_transcript_folder(self.podcast_name)
        speaker_transcript_files = set(list_files_gcs(self.gc_provider, speaker_transcript_folder, Paths.TXT_EXT))
        aai_transcript_folder = Paths.get_aai_transcript_folder(self.podcast_name)
        aai_transcript_files = set(list_files_gcs(self.gc_provider, aai_transcript_folder, Paths.JSON_EXT))
        
        ext_len = len(self.extension)
        for audio_file in audio_files:
            title = Paths.get_title_from_path(audio_file)
            raw_transcript_file = Paths.get_raw_transcript_path(self.podcast_name, title)
            speaker_transcript_file = Paths.get_speaker_transcript_path(self.podcast_name, title)
            aai_transcript_file = Paths.get_aai_transcript_path(self.podcast_name, title)

            if (
                raw_transcript_file not in raw_transcript_files or 
                speaker_transcript_file not in speaker_transcript_files or
                aai_transcript_file not in aai_transcript_files
            ):
                untranscribed_files.append(
                    AudioToTranscribe(
                        audio_path=audio_file,
                        raw_transcript_path=raw_transcript_file,
                        speaker_transcript_path=speaker_transcript_file,
                        aai_transcript_path=aai_transcript_file,
                    )
                )

        return untranscribed_files

    def transcribe_audio(self, audio_to_transcribe: AudioToTranscribe) -> None:
        print("Transcribing {}".format(os.path.basename(audio_to_transcribe.audio_path)))

        # Download the audio
        download_file_gcs(self.gc_provider, audio_to_transcribe.audio_path)

        # Transcribe with AAI
        transcript = transcriber.transcribe(
            audio_to_transcribe.audio_path,
            config=config,
        )

        # Save raw transcript locally
        with open(audio_to_transcribe.raw_transcript_path, "w") as f:
            f.writelines([
                utterance.text + " \n" for utterance in transcript.utterances
            ])
            f.close()

        # Upload raw transcript to GCS
        upload_to_gcs(self.gc_provider, audio_to_transcribe.raw_transcript_path)

        # Save speaker transcript locally
        with open(audio_to_transcribe.speaker_transcript_path, "w") as f:
            for utterance in transcript.utterances:
                f.write("Speaker {}: \n".format(utterance.speaker))
                f.write(utterance.text)
                f.write("\n\n")

            f.close()

        # Upload speaker transcript to GCS
        upload_to_gcs(self.gc_provider, audio_to_transcribe.speaker_transcript_path)

        # Upload AAI json transcript to GCS
        upload_string_as_textfile_gcs(
            self.gc_provider, 
            audio_to_transcribe.aai_transcript_path, 
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
        untranscribed_files = self.find_untranscribed_audio_files()

        if len(untranscribed_files) > 0:
            print("Transcribing {} files for {}".format(len(untranscribed_files), self.podcast_name))
            
            # Transcribe the untranscribed files in parallel
            with ProcessPoolExecutor() as executor:
                executor.map(self.transcribe_audio, untranscribed_files)
        else:
            print("All audio files already transcribed for {}".format(self.podcast_name))

        # Delete local directories
        delete_temp_local_directory(self.podcast_name)
