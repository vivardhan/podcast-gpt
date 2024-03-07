# System Imports
import json
import os
import pdb
import requests
from typing import Dict

# Third Party Imports
import assemblyai as aai

# Package Imports
from configs import (
    ASSEMBLY_AI_FOLDER,
    JSON_EXT, 
    podcast_configs, 
    RAW_TRANSCRIPT_FOLDER,
    TEXT_DATA_FOLDER,
    TXT_EXT,
)

from data_api.utils.file_utils import create_temp_local_directory
from data_api.utils.gcs_utils import (
    download_file_gcs,
    file_exists_gcs, 
    list_files_gcs, 
    upload_string_as_textfile_gcs,
)
from google_client_provider import GoogleClientProvider

base_url = "https://api.assemblyai.com/v2/transcript/"

# Replace with your API key
aai.settings.api_key = "9b22f02582ac4fdf892ba609d1080da0"
headers = {'authorization': aai.settings.api_key}

def download_all_raw_transcript_texts(gc_provider: GoogleClientProvider) -> Dict[str, str]:
    ret = {}
    for podcast_name, config in podcast_configs.items():
        print("Downloading all raw transcripts from gcs for {}".format(podcast_name))
        raw_text_folder = os.path.join(podcast_name, TEXT_DATA_FOLDER, RAW_TRANSCRIPT_FOLDER)
        create_temp_local_directory(raw_text_folder)
        for file_name in list_files_gcs(gc_provider, raw_text_folder, TXT_EXT):
            if not os.path.exists(file_name):
                download_file_gcs(gc_provider, file_name)
            
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

def save_assembly_ai_transcript(gc_provider: GoogleClientProvider, transcript: json, file_name: str) -> None:
    transcript_file_name = file_name.replace(RAW_TRANSCRIPT_FOLDER, ASSEMBLY_AI_FOLDER).replace(TXT_EXT, JSON_EXT)
    if file_exists_gcs(gc_provider, transcript_file_name):
        print("File already exists, skipping!")
        return

    upload_string_as_textfile_gcs(gc_provider, transcript_file_name, json.dumps(transcript))

def process_aai_transcripts(gc_provider: GoogleClientProvider, gcs_transcripts: Dict[str, str]) -> None:
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
                        save_assembly_ai_transcript(gc_provider, aai_transcript, file_name)
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
    gc_provider = GoogleClientProvider()
    gcs_transcripts = download_all_raw_transcript_texts(gc_provider)
    print("Downloaded {} raw transcripts from GCS".format(len(gcs_transcripts)))
    process_aai_transcripts(gc_provider, gcs_transcripts)

if __name__ == "__main__":
    main()