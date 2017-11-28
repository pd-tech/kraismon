#!/usr/bin/env python

# (c) 2017 pd-tech

# Use of this source code is governed by a "GNU General Public License v2.0" license that can be
# found in the LICENSE file.
# (https://raw.githubusercontent.com/pd-tech/kraismon/master/LICENSE)

import asyncio
import time
import psutil
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from threading import Thread

async def pn_streamer(pubnub, channel_name, values):
    pubnub.publish().channel(channel_name).message(values).sync()

async def measurement_delayer(period):
    await asyncio.sleep(period)

def monitor_cpu(cpumon_interval, pubnub, publish_at_sleep):
    while True:
        cpu_usg = psutil.cpu_percent()
        values = {'eon': {'x': time.time(), 'cpu_usage': cpu_usg}}  # format gathered data for the PubNub service

        asyncio.set_event_loop(publish_at_sleep)
        tasks = [asyncio.ensure_future(pn_streamer(pubnub, 'CPU-usage', values)),
                 asyncio.ensure_future(measurement_delayer(cpumon_interval))]   # publish when sleeping to ensure static (1 second) delay because of various network response time
        publish_at_sleep.run_until_complete(asyncio.gather(*tasks))

def monitor_ram(rammon_interval, pubnub, publish_at_sleep):
    while True:
        ram_usg = psutil.virtual_memory()[2]    # we need just the third element of the tuple (=percentage)
        values = {'eon': {'x': time.time(), 'ram_usage': ram_usg}}  # format gathered data for the PubNub service

        asyncio.set_event_loop(publish_at_sleep)
        tasks = [asyncio.ensure_future(pn_streamer(pubnub, 'RAM-usage', values)), 
                         asyncio.ensure_future(measurement_delayer(rammon_interval))]   # publish when sleeping to ensure static (1 second) delay because of various network response time
        publish_at_sleep.run_until_complete(asyncio.gather(*tasks))

def main():
    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "sub-c-c2edf284-d235-11e7-aee1-6e8e9d2d00b1"
    pnconfig.publish_key = "pub-c-ab64c3fc-c6e8-4a92-bf32-df36b37b5d0b"
    pnconfig.ssl = True
    pubnub = PubNub(pnconfig)

    cpu = asyncio.new_event_loop()
    ram = asyncio.new_event_loop()

    cpumon = Thread(target=monitor_cpu, args=(1.0, pubnub, cpu))
    cpumon.start()
    rammon = Thread(target=monitor_ram, args=(1.0, pubnub, ram))
    rammon.start()


if __name__ == '__main__':
    main()
