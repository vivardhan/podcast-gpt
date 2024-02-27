# Third Party Imports
import googleapiclient.discovery
import googleapiclient.errors
from google.cloud import storage

# Package imports
from google_oauth_credentials import obtain_google_oauth_credentials

# Set the scope to be youtube readonly
SCOPES = [
    "https://www.googleapis.com/auth/devstorage.read_write",
    "https://www.googleapis.com/auth/youtube.readonly",
]
PROJECT_ID = "podcast-gpt-415000"

class GoogleClientProvider:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GoogleClientProvider, cls).__new__(cls)
            
            cls.CREDENTIALS = obtain_google_oauth_credentials(scopes=SCOPES)

            cls.STORAGE_CLIENT = storage.Client(project=PROJECT_ID, credentials=cls.CREDENTIALS)
            cls.DATA_BUCKET = cls.STORAGE_CLIENT.get_bucket("podcast_gpt_data")

            # Create the youtube data API client
            youtube_api_service_name = "youtube"
            youtube_api_version = "v3"
            
            cls.youtube_client = googleapiclient.discovery.build(
                youtube_api_service_name, youtube_api_version, credentials=cls.CREDENTIALS)

        return cls._instance
