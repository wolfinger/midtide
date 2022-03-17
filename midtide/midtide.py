from __future__ import print_function

import datetime
import os.path
from pkgutil import get_data
from tabnanny import check
from webbrowser import get

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pysurfline import SpotForecast

import pandas as pd
import pickle

# set scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

class OptimizationParams:
    """
    optimization parameters object for easy passing into optimization function
    """
    def __init__(self, start_time_rel, start_time_abs, end_time_rel, end_time_abs, length=60):
        self.start_time_rel = start_time_rel
        self.start_time_abs = start_time_abs
        self.end_time_rel = end_time_rel
        self.end_time_abs = end_time_abs
        self.length = length

class OptimalWindow:
    """
    optimal window for a sarf sesh
    """
    def __init__(self, start_dt, end_dt):
        self.start_dt = start_dt
        self.end_dt = end_dt

# google cal api
# ###############
def cal_set_credentials():
    """
    set google calendar credentials
    """
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
    
    return creds

def cal_create_event(event, creds):
    # test calendar insert
    try:
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().insert(calendarId='primary', body=event).execute()

    except HttpError as error:
        print("An error occurred: %s" % error)

# surfline api
# ###############

def surf_check(spot_id, days, interval):
    """
    check a surf spot's surfline forecast
    """
    params = {
        "spotId": spot_id,
        "days": days,
        "intervalHours": interval,
    }
    return SpotForecast(params)

def get_optimal_windows(forecast, params):
    """
    iterate thru a forecast to get optimal surf windows for each day
    """ 
    # get datetime list for only the future and conver to local time ztone
    tides_df = forecast.get_dataframe("tides")
    
    # find the closest low/high tide to current time
    min_dt = tides_df[(tides_df['type'].isin(['LOW', 'HIGH'])) & (tides_df.index <= datetime.datetime.utcnow())].index.max()
    tides_df = tides_df[tides_df.index >= min_dt]
    #tides_df.index = tides_df.index + tides_df['utcOffset'].astype('timedelta64[h]')

    # get optimal window for each date
    optimal_windows = []
    last_low = None
    last_high = None
    for index, row in tides_df.iterrows():
        if row['type'] == 'LOW':
            last_low = index
            if last_high != None:
                mid = calc_mid(last_low, last_high)
                if mid >= datetime.datetime.now():
                    optimal_windows.append(OptimalWindow(mid - pd.DateOffset(minutes=params.length / 2), 
                        mid + pd.DateOffset(minutes=params.length / 2)))
        elif row['type'] == 'HIGH':
            last_high = index
            if last_low != None:
                mid = calc_mid(last_low, last_high)
                if mid >= datetime.datetime.now():
                    optimal_windows.append(OptimalWindow(mid - pd.DateOffset(minutes=params.length / 2), 
                        mid + pd.DateOffset(minutes=params.length / 2)))

    #
    # drop gnar sesh's when the sun's down
    # TODO: refactor as function
    sunlight_df = forecast.get_dataframe("sunlightTimes")

    # convert timestamps to local time
    #for time_pd in ['midnight', 'dawn', 'dusk']:
    #    sunlight_df[time_pd] = sunlight_df[time_pd] + sunlight_df[time_pd + 'UTCOffset'].astype('timedelta64[h]')

    sunlight_df['date'] = sunlight_df['dawn'].dt.date
    sunlight_df = sunlight_df.set_index('date')

    daytime_windows = []

    for window in optimal_windows:
         window_dt = window.start_dt.to_pydatetime().date()

         if not sunlight_df[sunlight_df.index == window_dt].empty and \
         sunlight_df[sunlight_df.index == window_dt]['dawn'].values[0] < window.start_dt.to_numpy() and \
         sunlight_df[sunlight_df.index == window_dt]['dusk'].values[0] > window.end_dt.to_numpy():
            daytime_windows.append(window)
    
    return daytime_windows

def calc_mid(start, end):
    return start + (end - start) / 2

def main():
    # set forecast parameters
    forecast_spot = "5842041f4e65fad6a7708841" # pb baby
    forecast_days = 3
    forecast_interval = 3
    hit_api = False

    if hit_api:
        forecast = surf_check(forecast_spot, forecast_days, forecast_interval)
        with open('forecast.pkl', 'wb') as handle:
            pickle.dump(forecast, handle, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        with open('forecast.pkl', 'rb') as handle:
            forecast = pickle.load(handle)

    # set mid tide optimization parameters
    opt_start_time_rel = datetime.datetime(2022, 3, 6, 0, 15, 0) # how long after sunrise
    opt_start_time_abs = datetime.datetime(2022, 3, 6, 7, 0, 0) # or no later than
    opt_end_time_rel = datetime.datetime(2022, 3, 6, 0, 45, 0) # how long before sunset
    opt_end_time_abs = datetime.datetime(2022, 3, 6, 19, 00, 0) # or no later than
    
    params = OptimizationParams(opt_start_time_rel, opt_start_time_abs, 
        opt_end_time_rel, opt_end_time_abs)
    
    windows = get_optimal_windows(forecast, params)

    # set credentials to access calendar
    creds = cal_set_credentials()

    # create calendar events
    for window in windows:
        sarf_event = {
            'summary': 'gnar sesh',
            'start': {
                'dateTime': window.start_dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                #'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': window.end_dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                #'timeZone': 'America/Los_Angeles',
            },
            'reminders': {
                'useDefault': False
            }
        }
        #print(sarf_event)
        cal_create_event(sarf_event, creds)

if __name__ == '__main__':
    main()