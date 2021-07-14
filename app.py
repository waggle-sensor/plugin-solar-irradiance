import numpy as np
import argparse
import datetime

import time

import waggle.plugin as plugin

TOPIC_CLOUDCOVER = "env.coverage.cloud"
TOPIC_SOLARCLOUD = "env.irradiance.cloud"

plugin.init()
plugin.subscribe(TOPIC_CLOUDCOVER)


class cal_max_irr:
    def __init__(self):
        self.maxirrs = {}
        with open('maxirr_june2020.txt', 'r') as f:
            for line in f:
                a = line.strip().split(' ')
                self.maxirrs[datetime.datetime.strptime(a[0], '%H:%M:%S')] = float(a[1])

    def cal(self, timestamp, args):
        timestamp_low = datetime.datetime.fromtimestamp(timestamp).time()
        timestamp_high = (datetime.datetime.fromtimestamp(timestamp)+datetime.timedelta(seconds=args.interval)).time()
        for k, v in self.maxirrs.items():
            if k.time() > timestamp_low and k.time() < timestamp_high:
                return v

def run(args):
    maxirr = cal_max_irr()
    while True:
        ratio = plugin.get()
        timestamp = ratio.timestamp
        current_max_irr = maxirr.cal(timestamp, args)

        irr = (1-ratio) * current_max_irr
        plugin.publish(TOPIC_SOLARCLOUD, irr, timestamp=timestamp)
        if args.debug:
            print(f"Measures published: Solar irradiance = {irr}")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', dest='interval', action='store', default=15, type=int, help='Inference interval in seconds')
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='Debug flag')
    args = parser.parse_args()

    run(args)
