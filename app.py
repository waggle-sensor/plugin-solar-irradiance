import numpy as np
import argparse
import datetime

import time

from pvlib import location
from pvlib import irradiance
import pandas as pd

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
    print('Generating solar irradiance table...')
    # The default location (36.691959, -97.565965) is Lamont, Oklahoma
    maxirr = cal_max_irr(geo_location=(args.node_latitude, args.node_longitude))
    maxirr.solarpy(datetime.datetime.fromtimestamp(time.time()).date())

    print('Solar Irradiance estimator starts...')
    while True:
        print('Getting cloud coverage ratio...')
        ratio = plugin.get()
        rvalue = ratio.value
        timestamp = ratio.timestamp
        current_max_irr = maxirr.cal(timestamp)

        irr = (1-rvalue) * current_max_irr
        plugin.publish(TOPIC_SOLARCLOUD, irr, timestamp=timestamp)
        print(f"Measures published: Solar irradiance = {irr}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-debug', dest='debug',
        action='store_true', default=False,
        help='Debug flag')
    parser.add_argument(
        '-node-latitude', dest='node_latitude', type=float,
        default=36.691959,
        help='latitude of the node location')
    parser.add_argument(
        '-node-longitude', dest='node_longitude', type=float,
        default=-97.565965,
        help='longitude of the node location')
    run(parser.parse_args())
