import datetime
import pandas as pd

from pysurfline import SpotForecast
from pysurfline.utils import degToCompass


class OptimizationParams:
    """
    optimization parameters object for easy passing into optimization function
    """

    def __init__(self, start_time_rel, start_time_abs, end_time_rel, end_time_abs,
                 length_min=30, length_def=60, length_max=120, wave_height_min=3, wave_height_max=12,
                 swell_period_min=6, swell_period_max=15, swell_directions=None,
                 wind_max=8, water_temp_min=57, time_since_rain=72):
        self.start_time_rel = start_time_rel
        self.start_time_abs = start_time_abs
        self.end_time_rel = end_time_rel
        self.end_time_abs = end_time_abs
        self.length_min = length_min
        self.length_def = length_def
        self.length_max = length_max
        self.wave_height_min = wave_height_min
        self.wave_height_max = wave_height_max
        self.swell_period_min = swell_period_min
        self.swell_period_max = swell_period_max
        self.swell_period_directions = swell_directions
        self.wind_max = wind_max
        self.water_temp_min = water_temp_min
        self.time_since_rain = time_since_rain


class SurfSession:
    """
    sarf session
    """

    def __init__(self, start_dt, end_dt, surf_min=None, surf_max=None, wind_speed=None, wind_direction=None):
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.surf_min = surf_min
        self.surf_max = surf_max
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction


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


def get_surf_sessions(forecast, params):
    """
    iterate thru a forecast to get surf sessions for each day
    """
    # get dataframes for different forecast attributes
    tides_df = forecast.get_dataframe("tides")
    waves_df = forecast.get_dataframe("wave")
    wind_df = forecast.get_dataframe("wind")

    # find the closest low/high tide to current time
    min_dt = tides_df[
        (tides_df['type'].isin(['LOW', 'HIGH'])) & (tides_df.index <= datetime.datetime.utcnow())].index.max()
    tides_df = tides_df[tides_df.index >= min_dt]
    # tides_df.index = tides_df.index + tides_df['utcOffset'].astype('timedelta64[h]')

    # get sessions for each date
    surf_sessions = []
    last_low = None
    last_high = None
    for index, row in tides_df.iterrows():
        if row['type'] == 'LOW':
            last_low = index
        elif row['type'] == 'HIGH':
            last_high = index

        if (row['type'] == 'LOW' and last_high is not None) or (row['type'] == 'HIGH' and last_low is not None):
            mid = calc_mid(last_low, last_high)
            if mid >= datetime.datetime.utcnow():
                # get surf height
                surf_size = waves_df.iloc[waves_df.index.get_indexer([mid], method='nearest')][['surf_min', 'surf_max']]
                surf_min = round(surf_size.iloc[0]['surf_min'], 0)
                surf_max = round(surf_size.iloc[0]['surf_max'], 0)

                # get wind
                wind = wind_df.iloc[wind_df.index.get_indexer([mid], method='nearest')][['speed', 'direction']]
                wind_speed = wind.iloc[0]['speed']
                wind_direction = degToCompass(wind.iloc[0]['direction'])

                # create surf session
                surf_sessions.append(SurfSession(mid - pd.DateOffset(minutes=params.length_def / 2),
                                                 mid + pd.DateOffset(minutes=params.length_def / 2), surf_min,
                                     surf_max, wind_speed, wind_direction))

    # determine good gnar seshs
    good_surf_sessions = []

    # get sunlight info
    sunlight_df = forecast.get_dataframe("sunlightTimes")
    sunlight_df['date'] = sunlight_df['dawn'].dt.date
    sunlight_df = sunlight_df.set_index('date')

    for session in surf_sessions:
        good_session = True

        # check for daytime sessions
        session_dt = session.start_dt.to_pydatetime().date()

        if sunlight_df[sunlight_df.index == session_dt].empty or \
                sunlight_df[sunlight_df.index == session_dt]['dawn'].values[0] > session.start_dt.to_numpy() or \
                sunlight_df[sunlight_df.index == session_dt]['dusk'].values[0] < session.end_dt.to_numpy():
            good_session = False

        # check wave height
        if (session.surf_max < params.wave_height_min) or (session.surf_max > params.wave_height_max):
            good_session = False

        # check wind
        if session.wind_speed > params.wind_max:
            good_session = False

        if good_session:
            good_surf_sessions.append(session)

    return good_surf_sessions


def calc_mid(start, end):
    """
    helper function to calc the midtide time
    """
    return start + (end - start) / 2
