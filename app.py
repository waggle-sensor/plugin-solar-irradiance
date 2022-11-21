import os
import logging
import argparse
import datetime
import time

import numpy as np

from pvlib import location
from pvlib import irradiance
import pandas as pd
from gpsdclient import GPSDClient

from waggle.plugin import Plugin

TOPIC_CLOUDCOVER = "env.coverage.cloud"
TOPIC_SOLARCLOUD = "env.irradiance.solar"

def get_gpolocation(host, port, retry=5):
    gpsclient = GPSDClient(host=host, port=port)
    for i in range(retry):
        for result in gpsclient.dict_stream(convert_datetime=False):
            # look for a GPS report
            if result["class"] == "TPV":
                lat = result.get("lat", None)
                lon = result.get("lon", None)
                if all([lat, lon]):
                    return (lat, lon)
                logging.error("Failed to find lat, lon")
        logging.debug(f'Failed to find GPS report from {host}. Retry in 1 second.')
        time.sleep(1)

class cal_max_irr:
    def __init__(self, geo_location):
        self.maxirrs = {}
        self.lastupdate = '2020-06-20'
        self.geo_location = geo_location

    def cal(self, timestamp):
        timestamp_low = datetime.datetime.fromtimestamp(timestamp).time()
        timestamp_high = (datetime.datetime.fromtimestamp(timestamp)+datetime.timedelta(seconds=60)).time()

        for k, v in self.maxirrs['GHI'].items():
            dt = datetime.datetime.strptime(k, '%Y-%m-%dT%H:%M:%S').time()
            if dt > timestamp_low and dt < timestamp_high:
                return v

    def is_updated(self, date):
        return self.lastupdate == date

    def update_solarpy(self, date):
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
    logging.info('Generating solar irradiance table...')
    geolocation = (0,0)
    if all([args.node_latitude is None, args.node_longitude is None]):
        logging.info("No GPS coordinates is given.")
        host = os.getenv("WAGGLE_GPS_SERVER", "")
        port = os.getenv("WAGGLE_GPS_SERVER_PORT", 2947)
        if host == "":
            logging.error("WAGGLE_GPS_SERVER is not set. Failed to get GPS coordinates.")
            return 2
        logging.info(f'Attempting to get the coordinates from {host}:{port}.')
        geolocation = get_gpolocation(host, port)
    elif any([args.node_latitude is None, args.node_longitude is None]):
        logging.error(f'node latitude ({args.node_latitude}) and longitude ({args.node_longitude}) information is incomplete')
        return 2
    else:
        logging.info(f'GPS location is given as ({args.node_latitude}, {args.node_longitude})')
        geolocation = (args.node_latitude, args.node_longitude)


    maxirr = cal_max_irr(geo_location=geolocation)
    logging.info("Solar Irradiance estimator starts.")
    with Plugin() as plugin:
        logging.info(f'Subscribing {TOPIC_CLOUDCOVER}')
        plugin.subscribe(TOPIC_CLOUDCOVER)
        while True:
            ratio = plugin.get()
            rvalue = ratio.value
            logging.info(f'Received cloud cover: {rvalue}')
            timestamp_ns = ratio.timestamp
            date = datetime.datetime.fromtimestamp(timestamp_ns / 1e9).date()
            if not maxirr.is_updated(date):
                logging.info(f'SolarPy\'s is outdated. Updating it with {date}')
                maxirr.update_solarpy(date)
            current_max_irr = maxirr.cal(timestamp_ns / 1e9)
            irr = (1-rvalue) * current_max_irr
            plugin.publish(TOPIC_SOLARCLOUD, irr, timestamp=timestamp_ns)
            logging.info(f'Measures published: Solar irradiance = {irr}')
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-debug', dest='debug',
        action='store_true', default=False,
        help='Debug flag')
    parser.add_argument(
        '-node-latitude', dest='node_latitude',
        action='store', type=float,
        help='latitude of the node location')
    parser.add_argument(
        '-node-longitude', dest='node_longitude',
        action='store', type=float,
        help='longitude of the node location')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')
    
    exit(run(args))
