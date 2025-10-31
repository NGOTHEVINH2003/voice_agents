import os.path
import datetime as dt

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# IF YOU MODIFY THE SCOPE DELETE THE TOKEN.TXT FILE

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_credentials_google():
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())
    
    return creds

def get_calendar_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = get_credentials_google()
    
    service = build("calendar", "v3", credentials=creds)
    return service
