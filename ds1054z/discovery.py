#!/usr/bin/env python

"""
Zeroconf Discovery for Rigol DS1000Z-series scopes
--------------------------------------------------

Derived from https://gist.github.com/pklaus/0a799921217bc9a7d86f

"""

from zeroconf import *
import socket
import time
import re

try:
    clock = time.perf_counter
except AttributeError:
    clock = time.time


class Listener(object):
    def __init__(self, filter_func=None):
        self.results = []
        self.filter_func = filter_func

    def remove_service(self, zeroconf, zc_type, zc_name):
        #print('Service "{0}" removed'.format(zc_name))
        pass

    def add_service(self, zeroconf, zc_type, zc_name):
        zc_info = zeroconf.get_service_info(zc_type, zc_name)
        zc_info._properties = {k: v for k, v in zc_info.properties.items() if v is not None}

        result = {
          'zc_name' : zc_name,
          'zc_type' : zc_type,
          'zc_info' : zc_info,
        }
        if self.filter_func:
            if self.filter_func(result):
                self.results.append(result)
        else:
            self.results.append(result)


def get_ds1000z_results(if_any_return_after=0.8, timeout=2.5):
    """
    Zeroconf service discovery of "_scpi-raw._tcp.local."
    The results are filtered for entries matching the Rigol DS1000Z scope series.
    """
    zc = Zeroconf()

    def ds1000z_filter(result):
        check_results = [
          re.match(b'DS1\d\d\dZ', result['zc_info'].properties[b'Model']),
          re.match(b'RIGOL TECHNOLOGIES', result['zc_info'].properties[b'Manufacturer']),
        ]
        if not all(check_results):
            return False
        return True

    listener = Listener(filter_func=ds1000z_filter)
    browser = ServiceBrowser(zc, '_scpi-raw._tcp.local.', listener=listener)

    start = clock()
    while True:
        # Because multithreading sucks.
        et = clock() - start # elapsed time
        if len(listener.results) and et >= if_any_return_after:
            break
        if et >= timeout:
            break
        time.sleep(0.005)

    zc.close()

    return listener.results

def discover_devices(*args, **kwargs):
    """
    A wrapper for get_ds1000z_results()
    returning a reduced dictionary of the results.
    """
    devices = []
    for result in get_ds1000z_results(*args, **kwargs):
        device = {
          'model': result['zc_info'].properties[b'Model'],
          'ip': socket.inet_ntoa(result['zc_info'].address),
        }
        devices.append(device)
    return devices

