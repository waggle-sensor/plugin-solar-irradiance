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
    def __init__(self):
        self.maxirrs = {}
        self.lastupdate = '2020-06-20'

    def cal(self, timestamp):
        if datetime.datetime.fromtimestamp(timestamp).date() != self.lastupdate:
            self.solarpy(datetime.datetime.fromtimestamp(timestamp).date())

        timestamp_low = datetime.datetime.fromtimestamp(timestamp).time()
        timestamp_high = (datetime.datetime.fromtimestamp(timestamp)+datetime.timedelta(seconds=args.interval)).time()

        for k, v in self.maxirrs['GHI'].items():
            dt = datetime.datetime.strptime(k, '%Y-%m-%dT%H:%M:%S').time()
            if dt > timestamp_low and dt < timestamp_high:
                return v

    def solarpy(self, date):
        self.lastupdate = date
        # Lamont, Oklahoma
        tz = 'MST'
        lat, lon = 36.691959, -97.565965
        site = location.Location(lat, lon, tz=tz)

        def get_irradiance(site_location, date, tilt, surface_azimuth):
            times = pd.date_range(date, freq='1min', periods=60*24, tz=site_location.tz)
            clearsky = site_location.get_clearsky(times)
            solar_position = site_location.get_solarposition(times=times)
            return pd.DataFrame({'GHI': clearsky['ghi']})

        self.maxirrs = get_irradiance(site, date, 25, 180)
        self.maxirrs.index = self.maxirrs.index.strftime('%Y-%m-%dT%H:%M:%S')
        self.maxirrs = self.maxirrs.to_dict('dict')

        

def run():
    maxirr = cal_max_irr()
    maxirr.solarpy(datetime.datetime.fromtimestamp(time.time()).date())

    while True:
        ratio = plugin.get()
        rvalue = ratio.value
        timestamp = ratio.timestamp
        current_max_irr = maxirr.cal(timestamp)

        irr = (1-rvalue) * current_max_irr
        plugin.publish(TOPIC_SOLARCLOUD, irr, timestamp=timestamp)
        if args.debug:
            print(f"Measures published: Solar irradiance = {irr}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
        parser.add_argument(
        '-debug', dest='debug',
        action='store_true', default=False,
        help='Debug flag')
    parser.add_argument(
        '-interval', dest='interval',
        action='store', default=0, type=int,
        help='Inference interval in seconds')
    run(parser.parse_args())
