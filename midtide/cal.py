import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# set scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# google cal api
# ###############


def set_credentials():
    """
    set google calendar credentials, code snippet lifted from google cal api start docs
    """
    creds = None
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('data/token.json'):
        creds = Credentials.from_authorized_user_file('data/token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'data/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('data/token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds


def create_event(event, creds):
    """
    creat a google calendar event
    """
    # test calendar insert
    try:
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().insert(calendarId='primary', body=event).execute()

    except HttpError as error:
        print("An error occurred: %s" % error)


def create_event_json(session):
    """
    generate google calendar event api json from a SurfSession
    """
    event_json = {
            'summary': 'gnar sesh',
            'start': {
                'dateTime': session.start_dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                # 'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': session.end_dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                # 'timeZone': 'America/Los_Angeles',
            },
            'reminders': {
                'useDefault': False
            }
        }
    
    return event_json
