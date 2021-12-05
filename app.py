import numpy as np
import argparse
import datetime

import time

#from pvlib import location
#from pvlib import irradiance
#import pandas as pd

from pysolar.solar import *

import waggle.plugin as plugin

TOPIC_CLOUDCOVER = "env.coverage.cloud"
TOPIC_SOLARCLOUD = "env.irradiance.solar"

plugin.init()
plugin.subscribe(TOPIC_CLOUDCOVER)

class cal_max_irr:
    def __init__(self, geo_location):
        self.maxirrs = {}
        self.lastupdate = '2020-06-20'
        self.geo_location = geo_location

    def cal(self, timestamp):
        if datetime.datetime.fromtimestamp(timestamp).date() != self.lastupdate:
            self.solarpy(datetime.datetime.fromtimestamp(timestamp).date())

        timestamp_low = datetime.datetime.fromtimestamp(timestamp).time()
        timestamp_high = (datetime.datetime.fromtimestamp(timestamp)+datetime.timedelta(seconds=60)).time()

        for k, v in self.maxirrs['GHI'].items():
            dt = datetime.datetime.strptime(k, '%Y-%m-%dT%H:%M:%S').time()
            if dt > timestamp_low and dt < timestamp_high:
                return v

    def solarpy(self, date):
        self.lastupdate = date
        tz = 'UTC'
        lat, lon = self.geo_location
        site = location.Location(lat, lon, tz=tz)

        def get_irradiance(site_location, date, tilt, surface_azimuth):
            times = pd.date_range(date, freq='1min', periods=60*24, tz=site_location.tz)
            clearsky = site_location.get_clearsky(times)
            solar_position = site_location.get_solarposition(times=times)
            return pd.DataFrame({'GHI': clearsky['ghi']})

        self.maxirrs = get_irradiance(site, date, 25, 180)
        self.maxirrs.index = self.maxirrs.index.strftime('%Y-%m-%dT%H:%M:%S')
        self.maxirrs = self.maxirrs.to_dict('dict')


def run(args):
    #print('Generating solar irradiance table...')
    # The default location (36.691959, -97.565965) is Lamont, Oklahoma
    #timestamp = time.time()
    #plugin.publish(TOPIC_SOLARCLOUD, 'Solar Irradiance Estimator: Generating Max Solar Irradiance Table', timestamp=timestamp)
    #print(f"Generating Max Solar irradiance at {timestamp}")
    #maxirr = cal_max_irr(geo_location=(args.node_latitude, args.node_longitude))
    #maxirr.solarpy(datetime.datetime.fromtimestamp(time.time()).date())


    latitude_deg = args.node_latitude # positive in the northern hemisphere
    longitude_deg = args.node_longitude # negative reckoning west from prime meridian in Greenwich, England
    date = datetime.datetime(2007, 2, 18, 15, 13, 1, 130320, tzinfo=datetime.timezone.utc)
    altitude_deg = get_altitude(latitude_deg, longitude_deg, date)
    irr = radiation.get_radiation_direct(date, altitude_deg)

    print('Solar Irradiance estimator starts...')
    while True:
        print('Getting cloud coverage ratio...')
        timestamp = time.time()
        plugin.publish(TOPIC_SOLARCLOUD, 'Solar Irradiance Estimator: Getting Cloud Cover Ratio', timestamp=timestamp)
        print(f"Getting Cloud Cover ratio at {timestamp}")
        ratio = plugin.get()
        rvalue = ratio.value
        imagetimestamp = ratio.timestamp
        timestamp = time.time()
        plugin.publish(TOPIC_SOLARCLOUD, 'Solar Irradiance Estimator: Getting Current Max Irradiance', timestamp=timestamp)
        print(f"Getting Current Max Irradiance at {timestamp}")
        #current_max_irr = maxirr.cal(imagetimestamp)


        date = datetime.datetime.fromtimestamp(imagetimestamp).replace(year=2018).replace(tzinfo=datetime.timezone.utc)
        current_max_irr = radiation.get_radiation_direct(date, altitude_deg)

        timestamp = time.time()
        plugin.publish(TOPIC_SOLARCLOUD, 'Solar Irradiance Estimator: Calculate Irradiance', timestamp=timestamp)
        print(f"Calculate Solar irradiance at {timestamp}")
        irr = (1-rvalue) * current_max_irr
        timestamp = time.time()
        plugin.publish(TOPIC_SOLARCLOUD, irr, timestamp=imagetimestamp)
        print(f"Measures published: Solar irradiance = {irr} at {timestamp}")
        exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-debug', dest='debug',
        action='store_true', default=False,
        help='Debug flag')
    parser.add_argument(
        '-node-latitude', dest='node_latitude', action='store',
        type=float, default=36.691959,
        help='latitude of the node location')
    parser.add_argument(
        '-node-longitude', dest='node_longitude', action='store',
        type=float, default=-97.565965,
        help='longitude of the node location')
    run(parser.parse_args())
