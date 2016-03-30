from flask_apscheduler import APScheduler
import datetime
# from myapp import models_database


class Config(object):
    JOBS = [
        {
            'id': 'request_realtime_weather_data',
            'func': 'myapp.models_database:request_realtime_weather_data',
            'args': (),
            'trigger': 'interval',
            'seconds': 300
        },
        {
            'id': 'request_realtime_traffic_data',
            'func': 'myapp.models_database:request_realtime_traffic_data',
            'args': (),
            'trigger': 'interval',
            'seconds': 10
        },
        # {
        #     'id': 'request_static_gtfs_data',
        #     'func': 'myapp.models_database:request_static_gtfs_data',
        #     'args': (),
        #     'trigger': 'cron',
        #     'hour': '1'
        # },
        # {
        #     'id': 'request_realtime_gtfs_data',
        #     'func': 'myapp.models_database:request_realtime_gtfs_data',
        #     'args': (),
        #     'trigger': 'interval',
        #     'seconds': 15
        # }
    ]

    SCHEDULER_VIEWS_ENABLED = True


# def request_realtime_weather_data():
#     weather = Weather()
#     weather.requestWeatherForAllCounty()

# def request_realtime_traffic_data():
#     traffic = Traffic()
#     traffic.requestTrafficForAllRoutes()

def job1(a, b):
    print(str(a) + ' ' + str(b))+' | '+str(datetime.datetime.now())
