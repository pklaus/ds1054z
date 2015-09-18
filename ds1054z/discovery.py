#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The submodule :py:mod:`ds1054z.discovery` - Zeroconf Discovery for Rigol DS1000Z-series scopes
==============================================================================================

This submodule depends on the Python package :py:mod:`zeroconf`. Thus,

>>> import ds1054z.discovery

raises an ImportError in case, the zeroconf package is not installed.

"""

# Derived from https://gist.github.com/pklaus/0a799921217bc9a7d86f

from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser
import socket
import time
import re

try:
    clock = time.perf_counter
except AttributeError:
    clock = time.time

class DS1000ZServiceInfo(ServiceInfo):
    """ Patched version of zeroconf.ServiceInfo for DS1000Z devices."""
    @property
    def properties(self):
        properties = {k: v for k, v in self._properties.items() if v is not None}
        return properties

class Listener(object):
    def __init__(self, filter_func=None, cast_service_info=None):
        self.results = []
        self.filter_func = filter_func
        self.cast_service_info = cast_service_info

    def remove_service(self, zc, zc_type, zc_name):
        #print('Service "{0}" removed'.format(zc_name))
        pass

    def add_service(self, zc, zc_type, zc_name):
        zc_info = zc.get_service_info(zc_type, zc_name)
        if self.cast_service_info:
            zc_info.__class__ = self.cast_service_info

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


def _get_ds1000z_results(if_any_return_after=1.0, timeout=2.5):
    """
    Zeroconf service discovery of ``_scpi-raw._tcp.local.``
    The results are filtered for entries matching the Rigol DS1000Z scope series.

    :return: The filtered results list created by the Listener():
             A list of dictionaries, each containing the entries ``zc_name``,
             ``zc_type``, and ``zc_info``.
    :rtype: list of dict
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

    listener = Listener(filter_func=ds1000z_filter, cast_service_info=DS1000ZServiceInfo)
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

def discover_devices(if_any_return_after=0.8, timeout=2.5):
    # This is effectively a wrapper for _get_ds1000z_results()
    # returning a reduced dictionary of the results.
    """
    Discovers Rigol DS1000Z series oscilloscopes on the local networks.

    :param float if_any_return_after: Return after this amount of time in seconds, if at least one device was discovered.
    :param float timeout: Return after at most this amount of time in seconds whether devices were discovered or not.
    :return: The list of discovered devices. Each entry is a dictionary containing a 'model' and 'ip' entry.
    :rtype: list of dict
    """
    devices = []
    for result in _get_ds1000z_results(if_any_return_after=0.8, timeout=2.5):
        device = {
          'model': result['zc_info'].properties[b'Model'].decode('utf-8'),
          'ip': socket.inet_ntoa(result['zc_info'].address),
        }
        devices.append(device)
    return devices

