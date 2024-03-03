# Third Party Imports
import googleapiclient.discovery
import googleapiclient.errors
from google.cloud import storage

# Package imports
from google_oauth_credentials import obtain_google_oauth_credentials

# Set the scopes for authentication
SCOPES = [
    # For google cloud storage read write on the podcast-gpt project
    "https://www.googleapis.com/auth/devstorage.read_write",
    # For reading youtube data using the Youtube Data API v3
    "https://www.googleapis.com/auth/youtube.readonly",
]
PROJECT_ID = "podcast-gpt-415000"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

class GoogleClientProvider:
    """
     This is an instance class so that a given binary only has one copy
     Clients are expected to instantiate it once in their main() method
     and pass the instance to objects that need to access google APIs.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GoogleClientProvider, cls).__new__(cls)
            
            cls.CREDENTIALS = obtain_google_oauth_credentials(scopes=SCOPES)

            cls.STORAGE_CLIENT = storage.Client(project=PROJECT_ID, credentials=cls.CREDENTIALS)
            cls.DATA_BUCKET = cls.STORAGE_CLIENT.get_bucket("podcast_gpt_data")

            # Create the youtube data API client
            cls.youtube_client = googleapiclient.discovery.build(
                YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=cls.CREDENTIALS)

        return cls._instance
