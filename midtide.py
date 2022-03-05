from __future__ import print_function

import datetime
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
# set_credentials()
# create_event()
# update_event()
# delete_event()

# surfline api
# ###############
# surf_check()


def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # test calendar insert
    try:
        service = build('calendar', 'v3', credentials=creds)

        # create sarf event
        sarf_event = {
            'summary': 'gnar sesh',
            'start': {
                'dateTime': '2022-03-15T07:00:00-07:00',
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': '2022-03-15T08:00:00-07:00',
                'timeZone': 'America/Los_Angeles',
            },
            'reminders': {
                'useDefault': False
            }
        }

        event = service.events().insert(calendarId='primary', body=sarf_event).execute()

        print("Event created:", event.get('htmlLink'))

    except HttpError as error:
        print('An error occurred: %s' % error)


if __name__ == '__main__':
    main()