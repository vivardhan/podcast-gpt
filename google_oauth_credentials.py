# System imports
import json
import os
from typing import List

# Third Party Imports
import google_auth_oauthlib
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
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    # os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    SERVICE_ACCOUNT_FILE = os.path.join("assets", "compute_engine_key.json")
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=scopes)

    # Retrieve oauth credetials from the stored file
    # client_secrets_file = os.path.join("assets", "google_oauth_token.json")
    # with open(client_secrets_file, "r") as f:
    #     js = json.load(f)
    #     client_id = js["web"]["client_id"]
    #     client_secret = js["web"]["client_secret"]

    #     f.close()

    # Get credentials
    # flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
    #     client_secrets_file, 
    #     scopes,
    # )
    # return flow.run_local_server(open_browser=False)

    # return google_auth_oauthlib.get_user_credentials(
    #     scopes=scopes, 
    #     client_id=client_id, 
    #     client_secret=client_secret,
    # )

    # Tell the user to go to the authorization URL.
    # auth_url, _ = flow.authorization_url(prompt='consent')

    # print('Please go to this URL: {}'.format(auth_url))

    # code = input('Enter the authorization code: ')
    # flow.fetch_token(code=code)
    # session = flow.authorized_session()

    # print(session.get('https://www.googleapis.com/userinfo/v2/me').json())

