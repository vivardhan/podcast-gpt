# System imports
import os
from typing import List

# Third Party Imports
import google_auth_oauthlib.flow

def obtain_google_oauth_credentials(scopes: List[str]):
    """
    Obtain google oauth2 credentials for the provided scopes

    params:
        scopes: A list of scopes to request credentials for

    returns:
        A credentials object that can be used to authenticate clients
    """
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Retrieve oauth credetials from the stored file
    client_secrets_file = os.path.join("assets", "google_oauth_token.json")

    # Get credentials
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    return flow.run_local_server()