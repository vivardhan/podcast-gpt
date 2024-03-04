# System imports
import os
from typing import List

# Third Party Imports
import google.oauth2.credentials
from google.oauth2 import service_account

def obtain_google_oauth_credentials(scopes: List[str]) -> google.oauth2.credentials.Credentials:
    """
    Obtain google oauth2 credentials for the provided scopes

    params:
        scopes: A list of scopes to request credentials for

    returns:
        A credentials object that can be used to authenticate clients
    """
    SERVICE_ACCOUNT_FILE = os.path.join("assets", "compute_engine_key.json")
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=scopes)
