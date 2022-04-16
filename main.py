import pickle

import midtide.cal as cal
from midtide.core import *


def main():
    # set forecast parameters
    forecast_spot = "5842041f4e65fad6a7708841"  # pb baby
    forecast_days = 3
    forecast_interval = 1
    hit_api = True
    create_cal_events = True

    if hit_api:
        forecast = surf_check(forecast_spot, forecast_days, forecast_interval)
        with open('data/forecast.pkl', 'wb') as handle:
            pickle.dump(forecast, handle, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        with open('data/forecast.pkl', 'rb') as handle:
            forecast = pickle.load(handle)

    # print(forecast.get_dataframe("wave"))

    # set mid tide optimization parameters
    opt_start_time_rel = datetime.datetime(2022, 3, 6, 0, 15, 0)  # how long after sunrise
    opt_start_time_abs = datetime.datetime(2022, 3, 6, 7, 0, 0)  # or no later than
    opt_end_time_rel = datetime.datetime(2022, 3, 6, 0, 45, 0)  # how long before sunset
    opt_end_time_abs = datetime.datetime(2022, 3, 6, 19, 00, 0)  # or no later than

    params = OptimizationParams(opt_start_time_rel, opt_start_time_abs,
                                opt_end_time_rel, opt_end_time_abs)

    sessions = get_surf_sessions(forecast, params)

    # set credentials to access calendar
    creds = cal.set_credentials()

    # create calendar events
    for session in sessions:
        surf_event_json = cal.create_event_json(session)

        # create calendar events or print to screen if debugging / testing        
        if create_cal_events:
            cal.create_event(surf_event_json, creds)
        else:
            print(surf_event_json)


if __name__ == '__main__':
    main()
