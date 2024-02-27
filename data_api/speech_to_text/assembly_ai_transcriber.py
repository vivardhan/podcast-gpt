# System Imports
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
from functools import partial
import os
from typing import List

# Third Party Imports
import assemblyai as aai

# Package Imports
from configs import (
    AUDIO_DATA_FOLDER, 
    podcast_configs, 
    RAW_TRANSCRIPT_FOLDER,
    SPEAKER_TRANSCRIPT_FOLDER,
    TEXT_DATA_FOLDER,
    TXT_EXT,
)

from data_api.utils.file_utils import create_temp_local_directory, delete_temp_local_directory
from data_api.utils.gcs_utils import (
    download_file_gcs,
    file_exists_gcs, 
    list_files_gcs, 
    upload_to_gcs,
)
from google_client_provider import GoogleClientProvider

# Replace with your API key
aai.settings.api_key = "9b22f02582ac4fdf892ba609d1080da0"

config = aai.TranscriptionConfig(speaker_labels=True, speakers_expected=2)
transcriber = aai.Transcriber()

@dataclass
class AudioToTranscribe:
    audio_path: str

    raw_transcript_path: str

    speaker_transcript_path: str

def transcribe_audio(audio_to_transcribe: AudioToTranscribe) -> None:
    print("Transcribing {}".format(os.path.basename(audio_to_transcribe.audio_path)))
    transcript = transcriber.transcribe(
        audio_to_transcribe.audio_path,
        config=config,
    )

    with open(audio_to_transcribe.raw_transcript_path, "w") as f:
        f.writelines([
            utterance.text + " \n" for utterance in transcript.utterances
        ])
        f.close()

    with open(audio_to_transcribe.speaker_transcript_path, "w") as f:
        for utterance in transcript.utterances:
            f.write("Speaker {}: \n".format(utterance.speaker))
            f.write(utterance.text)
            f.write("\n\n")

        f.close()

class AudioTranscriber:

    def __init__(self, gc_provider: GoogleClientProvider, podcast_name: str, extension: str):
        self.gc_provider = gc_provider
        self.podcast_name = podcast_name
        self.extension = extension
        self.audio_folder = os.path.join(self.podcast_name, AUDIO_DATA_FOLDER)
        self.text_folder = os.path.join(self.podcast_name, TEXT_DATA_FOLDER)
        self.raw_transcript_prefix = os.path.join(self.text_folder, RAW_TRANSCRIPT_FOLDER)
        self.speaker_transcript_prefix = os.path.join(self.text_folder, SPEAKER_TRANSCRIPT_FOLDER)

    def find_untranscribed_audio_files(self, audio_files: List[str]) -> List[AudioToTranscribe]:
        print("Looking for untranscribed_files for {} ...".format(self.podcast_name))
        untranscribed_files = []
        
        ext_len = len(self.extension)
        for f in audio_files:
            base_filename = os.path.basename(f)[:-ext_len] + TXT_EXT
            raw_transcript_file = os.path.join(self.raw_transcript_prefix, base_filename)
            speaker_transcript_file = os.path.join(self.speaker_transcript_prefix, base_filename)

            if not file_exists_gcs(self.gc_provider, raw_transcript_file) or not file_exists_gcs(self.gc_provider, speaker_transcript_file):
                untranscribed_files.append(
                    AudioToTranscribe(
                        audio_path=f,
                        raw_transcript_path=raw_transcript_file,
                        speaker_transcript_path=speaker_transcript_file,
                    )
                )

        return untranscribed_files


    def transcribe_all_audio_files(self) -> None:
        temp_folders = [self.audio_folder, self.raw_transcript_prefix, self.speaker_transcript_prefix]
        for tf in temp_folders:
            create_temp_local_directory(tf)

        audio_files = list_files_gcs(self.gc_provider, os.path.join(self.podcast_name, AUDIO_DATA_FOLDER), self.extension)
        untranscribed_files = self.find_untranscribed_audio_files(audio_files)

        if len(untranscribed_files) > 0:
            print("Transcribing {} files for {}".format(len(untranscribed_files), self.podcast_name))

            for f in untranscribed_files:
                download_file_gcs(self.gc_provider, f.audio_path)
            
            with ProcessPoolExecutor() as executor:
                executor.map(transcribe_audio, untranscribed_files)

            for f in untranscribed_files:
                upload_to_gcs(self.gc_provider, f.raw_transcript_path)
                upload_to_gcs(self.gc_provider, f.speaker_transcript_path)
        else:
            print("All audio files already transcribed for {}".format(self.podcast_name))

        delete_temp_local_directory(self.podcast_name)


def main():
    gc_provider = GoogleClientProvider()
    for podcast_name, config in podcast_configs.items():
        transcriber = AudioTranscriber(gc_provider, podcast_name, config.audio_extension)
        transcriber.transcribe_all_audio_files()

if __name__ == "__main__":
    main()
