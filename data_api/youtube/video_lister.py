# System imports
import os
from typing import List

# Third party imports
import json
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

def obtain_google_oauth_credentials():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Set the scope to be youtube readonly
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

    # Retrieve oauth credetials from the stored file
    client_secrets_file = os.path.join("assets", "google_oauth_token.json")

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    return flow.run_local_server()

api_service_name = "youtube"
api_version = "v3"
credentials = obtain_google_oauth_credentials()

def getAllVideos(channel_id: str) -> List:
    """
    Retrieves a list of video metadata items for a given channel_id

    To get the channel_id for a youtube channel:
    1. Go to the channel's homepage.
    2. Right click and choose "View Page Source"
    3. Search for "externalId"
    4. Use the corresponding string as the input string to this function

    params:
        channel_id: The channel_id for which video items are required

    returns:
        A list of video metadata items, one per video on the channel
    """

    # Create the youtube data API client
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    # Find all playlist IDs for the provided channel ID
    request = youtube.channels().list(
        part="snippet,contentDetails",
        id=channel_id,
    )
    response = request.execute()

    playlist_ids = []
    for item in response["items"]:
        if item["kind"] != "youtube#channel":
            continue

        playlist_ids.append(item["contentDetails"]["relatedPlaylists"]["uploads"])


    # Extract all videos from each playlist ID
    page_token = None
    all_videos = []
    for playlist_id in playlist_ids:
        while True:
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token,
            )

            response = request.execute()
            all_videos.extend(response["items"])


            if "nextPageToken" in response:
                page_token = response["nextPageToken"]
            else:
                break


    return all_videos

def main():
    podcast_channel_ids = {
        "hubermanlab": "UC2D2CMWXMOVWx7giW1n3LIg",
        "PeterAttiaMD": "UC8kGsMa0LygSX9nkBcBH1Sg",
    }

    for k, v in podcast_channel_ids.items():
        print("Retrieving videos for {}".format(k))

        curr_videos = getAllVideos(v)
        folder_path = os.path.join("data", k)
        os.makedirs(folder_path, exist_ok=True)

        metadata_file = os.path.join(folder_path, "metadata.json")
        with open(metadata_file, "w") as f:
            json.dump(curr_videos, f)


if __name__ == "__main__":
    main()