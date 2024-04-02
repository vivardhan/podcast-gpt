# System Imports
import json
import os

# Package Imports
from data_api.utils.file_utils import create_temp_local_directory, delete_temp_local_directory
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.paths import Paths

def process_aai_transcript(transcript_path: str) -> None:
    filename = os.path.basename(transcript_path)
    print(filename)
    speaker_count = int(input("Enter speaker count:"))
    if speaker_count == 1:
        print("Modifying json and saving!")
        js = json.loads(GCSClient.download_textfile_as_string(transcript_path))
        for w in js["words"]:
            w["speaker"] = "A"

        for u in js["utterances"]:
            u["speaker"] = "A"
            for w in u["words"]:
                w["speaker"] = "A"

        GCSClient.upload_string_as_textfile(transcript_path, json.dumps(js))
    else:
        return

def process_all_transcripts(podcast_name: str) -> None:
    aai_folder = Paths.get_aai_transcript_folder(podcast_name)
    create_temp_local_directory(aai_folder)

    aai_transcript_files = GCSClient.list_files(aai_folder, Paths.JSON_EXT)
    for transcript_file in aai_transcript_files:
        process_aai_transcript(gc_provider, transcript_file)

    delete_temp_local_directory(podcast_name)


def main():
    podcast_name = "PeterAttiaMD"
    process_all_transcripts(podcast_name)

if __name__ == "__main__":
    main()
