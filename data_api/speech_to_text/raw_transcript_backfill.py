# System Imports
import json
import os
import requests
from typing import Dict

# Third Party Imports
import assemblyai as aai

# Package Imports
from data_api.utils.file_utils import create_temp_local_directory
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.paths import Paths

base_url = "https://api.assemblyai.com/v2/transcript/"

# Replace with your API key
aai.settings.api_key = "9b22f02582ac4fdf892ba609d1080da0"
headers = {'authorization': aai.settings.api_key}

def download_all_raw_transcript_texts() -> Dict[str, str]:
    ret = {}
    for podcast_name in ["hubermanlab", "PeterAttiaMD"]:
        print("Downloading all raw transcripts from gcs for {}".format(podcast_name))
        raw_text_folder = os.path.join(podcast_name, Paths.TEXT_DATA_FOLDER, Paths.RAW_TRANSCRIPT_FOLDER)
        create_temp_local_directory(raw_text_folder)
        for file_name in GCSClient.list_files(raw_text_folder, Paths.TXT_EXT):
            if not os.path.exists(file_name):
                GCSClient.download_file(file_name)
            
            curr_text = ""
            with open(file_name, "r") as f:
                for line in f.readlines():
                    curr_text += line.rstrip() + " "

                ret[file_name] = curr_text.rstrip()
                
    return ret

def get_aai_transcript(aai_transcript_id: str) -> str:
    try:
        return requests.get(url=base_url + aai_transcript_id, headers=headers).json()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

def match_aai_transcript_to_gcs_transcript(aai_transcript_text: str, gcs_transcripts: Dict[str, str]) -> str:
    """
    Matches a transcript from Assembly AI to the correct transcript on GCS and returns the filename

    params:
        aai_transcript_text:
            The transcript from Assembly AI transcript
        gcs_transcripts:
            A dictionary mapping filenames to raw transcript texts on GCS

    returns:
        A file name string for the matched GCS transcript
    """ 
    for file_name, gcs_text in gcs_transcripts.items():
        if aai_transcript_text == gcs_text:
            return file_name

    return None

def save_assembly_ai_transcript(transcript: json, file_name: str) -> None:
    transcript_file_name = file_name.replace(
        Paths.RAW_TRANSCRIPT_FOLDER, 
        Paths.ASSEMBLY_AI_FOLDER
    ).replace(
        Paths.TXT_EXT, 
        Paths.JSON_EXT
    )
    if GCSClient.file_exists(transcript_file_name):
        print("File already exists, skipping!")
        return

    GCSClient.upload_string_as_textfile(transcript_file_name, json.dumps(transcript))

def process_aai_transcripts(gcs_transcripts: Dict[str, str]) -> None:
    curr_url = "https://api.assemblyai.com/v2/transcript?limit=200&status=completed"
    urls = set()
    while curr_url:
        try:
            r = requests.get(url=curr_url, headers=headers).json()
            if "transcripts" in r:
                for t in r["transcripts"]:
                    aai_transcript = get_aai_transcript(t["id"])
                    file_name = match_aai_transcript_to_gcs_transcript(aai_transcript["text"], gcs_transcripts)
                    if file_name:
                        print("Matched transcript id: {} to file: {}".format(t["id"], file_name))
                        save_assembly_ai_transcript(aai_transcript, file_name)
                    else:
                        print("Failed to match transcript id: {} to any gcs file".format(t["id"]))

            if "prev_url" in r["page_details"]:
                curr_url = r["page_details"]["prev_url"]
            else:
                curr_url = None
                print("no more urls")

        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

def main():
    gcs_transcripts = download_all_raw_transcript_texts()
    print("Downloaded {} raw transcripts from GCS".format(len(gcs_transcripts)))
    process_aai_transcripts(gcs_transcripts)

if __name__ == "__main__":
    main()