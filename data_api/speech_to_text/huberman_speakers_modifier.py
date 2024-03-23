# System Imports
import json
import os

# Package Imports
from data_api.utils.file_utils import create_temp_local_directory, delete_temp_local_directory
from data_api.utils.gcs_utils import (
    download_file_gcs,
    file_exists_gcs, 
    list_files_gcs, 
    upload_string_as_textfile_gcs,
)
from google_client_provider import GoogleClientProvider
from data_api.utils.paths import Paths

def read_transcript(transcript_path: str) -> json:
    with open(transcript_path) as f:
        js = json.load(f)
        f.close()
        return js

def process_aai_transcript(gc_provider: GoogleClientProvider, transcript_path: str) -> None:
    filename = os.path.basename(transcript_path)
    print(filename)
    speaker_count = int(input("Enter speaker count:"))
    if speaker_count == 1:
        print("Modifying json and saving!")
        download_file_gcs(gc_provider, transcript_path)
        js = read_transcript(transcript_path)
        for w in js["words"]:
            w["speaker"] = "A"

        for u in js["utterances"]:
            u["speaker"] = "A"
            for w in u["words"]:
                w["speaker"] = "A"

        upload_string_as_textfile_gcs(gc_provider, transcript_path, json.dumps(js))
    else:
        return

def process_all_transcripts(gc_provider: GoogleClientProvider, podcast_name: str) -> None:
    aai_folder = Paths.get_aai_transcript_folder(podcast_name)
    create_temp_local_directory(aai_folder)

    aai_transcript_files = list_files_gcs(gc_provider, aai_folder, JSON_EXT)
    for transcript_file in aai_transcript_files:
        process_aai_transcript(gc_provider, transcript_file)

    delete_temp_local_directory(podcast_name)


def main():
    huberman_podcast_name = "hubermanlab"
    gc_provider = GoogleClientProvider()
    process_all_transcripts(gc_provider, huberman_podcast_name)

if __name__ == "__main__":
    main()
