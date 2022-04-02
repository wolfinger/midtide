import datetime
import pandas as pd

from pysurfline import SpotForecast


class OptimizationParams:
    """
    optimization parameters object for easy passing into optimization function
    """

    def __init__(self, start_time_rel, start_time_abs, end_time_rel, end_time_abs,
                 length_min=30, length_def=60, length_max=120, wave_height_min=2, wave_height_max=12,
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

    def __init__(self, start_dt, end_dt, surf_min=None, surf_max=None):
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.surf_min = surf_min
        self.surf_max = surf_max


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
    # get datetime list for only the future and convert to local time zone
    tides_df = forecast.get_dataframe("tides")

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
            if last_high is not None:
                mid = calc_mid(last_low, last_high)
                if mid >= datetime.datetime.now():
                    surf_sessions.append(SurfSession(mid - pd.DateOffset(minutes=params.length_def / 2),
                                                     mid + pd.DateOffset(minutes=params.length_def / 2)))
        elif row['type'] == 'HIGH':
            last_high = index
            if last_low is not None:
                mid = calc_mid(last_low, last_high)
                if mid >= datetime.datetime.now():
                    surf_sessions.append(SurfSession(mid - pd.DateOffset(minutes=params.length_def / 2),
                                                     mid + pd.DateOffset(minutes=params.length_def / 2)))

    #
    # drop gnar sesh's when the sun's down
    # TODO: refactor as function
    sunlight_df = forecast.get_dataframe("sunlightTimes")

    # convert timestamps to local time
    # for time_pd in ['midnight', 'dawn', 'dusk']:
    #    sunlight_df[time_pd] = sunlight_df[time_pd] + sunlight_df[time_pd + 'UTCOffset'].astype('timedelta64[h]')

    sunlight_df['date'] = sunlight_df['dawn'].dt.date
    sunlight_df = sunlight_df.set_index('date')

    daytime_windows = []

    for session in surf_sessions:
        session_dt = session.start_dt.to_pydatetime().date()

        if not sunlight_df[sunlight_df.index == session_dt].empty and \
                sunlight_df[sunlight_df.index == session_dt]['dawn'].values[0] < session.start_dt.to_numpy() and \
                sunlight_df[sunlight_df.index == session_dt]['dusk'].values[0] > session.end_dt.to_numpy():
            daytime_windows.append(session)

    return daytime_windows


def calc_mid(start, end):
    """
    helper function to calc the mid tide time
    """
    return start + (end - start) / 2
