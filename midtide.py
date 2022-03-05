from __future__ import print_function

import datetime
import os.path
from pkgutil import get_data
from webbrowser import get

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pysurfline import SpotForecast


# set scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# google cal api
# ###############
# set_credentials()
# create_event()
# update_event()
# delete_event()

def gcal():
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
        print("An error occurred: %s" % error)


# surfline api
# ###############
# surf_check()
def surf_check(spot_id):
    params = {
        "spotId": spot_id,
        "days": 1,
        "intervalHours": 3,
    }
    forecast = SpotForecast(params)
    print(forecast.get_dataframe('wave'))

def main():
    surf_check("5842041f4e65fad6a7708841")

if __name__ == '__main__':
    main()