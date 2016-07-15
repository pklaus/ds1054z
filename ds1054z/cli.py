#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CLI for the DS1054Z scope by Rigol

This tool can be used in very versatile ways.
Ask it for --help on the individual actions
and it will tell you how to use them.
"""

import argparse
import textwrap
import logging
import time
import io
import pkg_resources
import sys
import os
import itertools
import errno

from ds1054z import DS1054Z

# Py2 fix for input()
try: input = raw_input
except NameError: pass

# Py2 fix for itertools.zip_longest()
try:
    zip_longest = itertools.zip_longest
except AttributeError:
    zip_longest = itertools.izip_longest

SHELL_HOWTO = """
Enter a command. It will be sent to the DS1054Z.
If the command contains a question mark ('?'), the answer
will be read from the device.
Quit the shell with  'quit'  or by pressing Ctrl-C
"""

def comma_sep(s):
    return s.split(',')

def late_parents(self, parents):
    """
    Hack to add a positional argument before the parents[]
    https://hg.python.org/cpython/file/3.4/Lib/argparse.py#l1649
    """
    for parent in parents:
        self._add_container_actions(parent)
        try:
            defaults = parent._defaults
        except AttributeError:
            pass
        else:
            self._defaults.update(defaults)

def main():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(__doc__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        )
    parser.add_argument('-v', '--verbose', action='store_true',
        help='More verbose output')
    parser.add_argument('--version', action='store_true',
        #'Display the version of the tool/package and exit.'
        help=argparse.SUPPRESS)
    parser.add_argument('--debug', action='store_true',
        #help='Enable debugging output',
        help=argparse.SUPPRESS,
        )

    device_parser = argparse.ArgumentParser(add_help=False)
    device_parser.add_argument('device', nargs='?',
        help='The device string. Typically the IP address of the oscilloscope. '
             'Will try to discover a single (!) scope on the network if you leave it out.')

    subparsers = parser.add_subparsers(dest='action', metavar='<action>',
        help="Action to perform on the scope:")

    # ds1054z discover
    action_desc = 'Discover and list scopes on your network and exit'
    discover_parser = subparsers.add_parser('discover',
        description=action_desc, help=action_desc)
    # ds1054z info
    action_desc = 'Print information about your oscilloscope'
    cmd_parser = subparsers.add_parser('info', parents=[device_parser],
        description=action_desc, help=action_desc)
    # ds1054z cmd
    action_desc = 'Send an SCPI command to the oscilloscope'
    cmd_parser = subparsers.add_parser('cmd',
        description=action_desc, help=action_desc)
    cmd_parser.add_argument('command', metavar=':SCPI:CMD',
        help="The command to execute. If the command contains a '?' the answer "
             "will be read from the device and printed to stdout.")
    late_parents(cmd_parser, parents=[device_parser])
    # ds1054z save-screen
    action_desc = 'Save an image of the screen'
    save_screen_parser = subparsers.add_parser('save-screen', parents=[device_parser],
        description=action_desc, help=action_desc)
    save_screen_parser.add_argument('--filename', '-f', metavar='IMG_FILENAME',
        help='The filename template for the image')
    save_screen_parser.add_argument('--overlay', '-o', metavar='RATIO', type=float, default=0.5,
        help='Dim on-screen controls in --save-screen with a mask (default ratio: 0.5)')
    save_screen_parser.add_argument('--printable', '-p', action='store_true',
        help='Make the screenshot more printer-friendly')
    # ds1054z save-data
    action_desc = 'Save the waveform data to a file'
    save_data_parser = subparsers.add_parser('save-data', parents=[device_parser],
        description=action_desc, help=action_desc)
    save_data_parser.add_argument('--filename', '-f',
        metavar='FILENAME', default='ds1054z-scope-values_{ts}.csv',
        help='The filename template for the data file. '
             'The kind of file is determined by its filename extension. '
             'Defaults to: ds1054z-scope-values_{ts}.csv')
    save_data_parser.add_argument('--mode', default='NORMal', choices=('NORMal', 'MAXimum', 'RAW'),
        help='The mode determins whether you will be reading the 1200 displayed samples (NORMal) '
             'or stopping the scope and reading out the full memory (RAW). '
             'MAXimum either reads the full memory if the scope is already stopped '
             'or the 1200 displayed samples otherwise.'
             'Defaults to NORMal.')
    save_data_parser.add_argument('--without-time', action='store_false', dest='with_time',
        help="If specified, it will save the data without the extra column "
             "of time values that's being added by default")
    # ds1054z settings
    action_desc = 'View and change settings of the oscilloscope'
    settings_parser = subparsers.add_parser('settings', parents=[device_parser],
        description=action_desc, help=action_desc)
    settings_parser.add_argument('--timebase', type=float,
        help="Change the timebase of the oscilloscope to this value (in seconds/div).")
    settings_parser.add_argument('--timebase-offset', type=float,
        help="Change the timebase offset of the oscilloscope to this value (in seconds).")
    # ds1054z properties
    action_desc = 'Query properties of the DS1054Z instance'
    properties_parser = subparsers.add_parser('properties', description=action_desc, help=action_desc)
    properties_parser.add_argument('properties', metavar='PROPERTIES', type=comma_sep,
        help="The properties to query separated by a comma, like: 'idn,memory_depth_internal_total'. "
             "Asking for a single one will also work, off course.")
    late_parents(properties_parser, parents=[device_parser])
    # ds1054z run
    action_desc = 'Start the oscilloscope data acquisition'
    run_parser = subparsers.add_parser('run', parents=[device_parser],
        description=action_desc, help=action_desc)
    # ds1054z stop
    action_desc = 'Stop the oscilloscope data acquisition'
    stop_parser = subparsers.add_parser('stop', parents=[device_parser],
        description=action_desc, help=action_desc)
    # ds1054z single
    action_desc = 'Set the oscilloscope to the single trigger mode.'
    single_parser = subparsers.add_parser('single', parents=[device_parser],
        description=action_desc, help=action_desc)
    # ds1054z tforce
    action_desc = 'Generate a trigger signal forcefully.'
    tforce_parser = subparsers.add_parser('tforce', parents=[device_parser],
        description=action_desc, help=action_desc)
    # ds1054z shell
    action_desc = 'Start an interactive shell to control your scope.'
    tforce_parser = subparsers.add_parser('shell', parents=[device_parser],
        description=action_desc, help=action_desc)
    # ds1054z measure
    action_desc = 'Measure a value on a channel'
    measure_parser = subparsers.add_parser('measure', parents=[device_parser],
        description=action_desc, help=action_desc)
    measure_parser.add_argument('--channel', '-c', choices=(1, 2, 3, 4), type=int, required=True,
        help='Channel from which to take the measurement')
    measure_parser.add_argument('--type', '-t', choices=('CURRent', 'MAXimum', 'MINimum', 'AVERages', 'DEViation'), default='CURRent')
    measure_parser.add_argument('item', choices=('vmax', 'vmin', 'vpp', 'vtop', 'vbase', 'vamp', 'vavg', 'vrms', 'overshoot', 'preshoot', 'marea', 'mparea', 'period', 'frequency', 'rtime', 'ftime', 'pwidth', 'nwidth', 'pduty', 'nduty', 'rdelay', 'fdelay', 'rphase', 'fphase', 'tvmax', 'tvmin', 'pslewrate', 'nslewrate', 'vupper', 'vmid', 'vlower', 'variance', 'pvrms'),
        help='Value to measure')
    args = parser.parse_args()

    if args.version:
        print(pkg_resources.get_distribution("ds1054z").version)
        sys.exit(0)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if not args.action:
        parser.print_help(sys.stderr)
        sys.stderr.write('\nERROR: Please choose an action.\n\n')
        sys.exit(2)

    if args.action == 'discover':
        try:
            from ds1054z.discovery import discover_devices
        except:
            print('Discovery depends on the zeroconf Python package which is missing.')
            sys.exit(1)
        devices = discover_devices()
        for device in devices:
            if args.verbose:
                print("Found a {model} with the IP Address {ip}.".format(**device))
            else:
                print("{ip}".format(**device))
        sys.exit(0)

    if not args.device:
        try:
            from ds1054z.discovery import discover_devices
        except:
            print("Please specify a device to connect to. Auto-discovery doesn't "
                  "work because the zeroconf Python package is missing.")
            sys.exit(1)
        devices = discover_devices()
        if len(devices) < 1:
            print("Couln't discover any device on the network. Exiting.")
            sys.exit(1)
        elif len(devices) > 1:
            print("Discovered multiple devices on the network:")
            print("\n".join("{model} {ip}".format(**dev) for dev in devices))
            print("Please specify the device you would like to connect to.")
            sys.exit(1)
        else: # len(devices) == 0
            if args.verbose: print("Found a scope: {model} @ {ip}".format(**devices[0]))
            args.device = devices[0]['ip']
    ds = DS1054Z(args.device)

    if args.action == 'info':
        fmt = "\nVendor:   {0}\nProduct:  {1}\nSerial:   {2}\nFirmware: {3}\n"
        print(fmt.format(ds.vendor, ds.product, ds.serial, ds.firmware))

    if args.action == 'cmd':
        if '?' in args.command:
            print(ds.query(args.command))
        else:
            ds.write(args.command)

    if args.action in ('run', 'stop', 'single', 'tforce'):
        getattr(ds, args.action)()

    if args.action == 'settings':
        if args.timebase:
            ds.timebase_scale = args.timebase
        if args.timebase_offset:
            ds.timebase_offset = args.timebase_offset
        wp = ds.waveform_preamble_dict
        if args.verbose:
            displayed_channels = ds.displayed_channels
            print("Sample Rate: {0}Sa/s".format(DS1054Z.format_si_prefix(ds.sample_rate)))
            print("Timebase: {0}s/div".format(DS1054Z.format_si_prefix(ds.timebase_scale)))
            print("Timebase Offset: {0}s".format(DS1054Z.format_si_prefix(ds.timebase_offset)))
            ds.set_waveform_mode('NORMal')
            tv = ds.waveform_time_values
            t_from = DS1054Z.format_si_prefix(tv[0],  unit='s')
            t_to =   DS1054Z.format_si_prefix(tv[-1], unit='s')
            print("The time axis goes from {0} to {1}".format(t_from, t_to))
            print("Displayed Channels: {0}".format(' '.join(displayed_channels)))
            for channel in displayed_channels:
                print("  Channel {0}:".format(channel))
                print("    Scale: {0}V/div".format(DS1054Z.format_si_prefix(ds.get_channel_scale(channel))))
                print("    Offset: {0}V".format(ds.get_channel_offset(channel)))
                print("    Probe Ratio: {}".format(ds.get_probe_ratio(channel)))
                print("    ---".format(DS1054Z.format_si_prefix(ds.get_channel_scale(channel))))
        else:
            print('sample_rate={}'.format(ds.sample_rate))
            print('timebase_scale={}'.format(ds.timebase_scale))
            print('timebase_offset={}'.format(ds.timebase_offset))
            print('displayed_channels={}'.format(','.join(ds.displayed_channels)))

    if args.action == 'properties':
        for prop in args.properties:
            val = getattr(ds, prop)
            if args.verbose:
                print('{0}: {1}'.format(prop, val))
            else:
                if type(val) in (list, tuple):
                    print(' '.join(str(v) for v in val))
                else:
                    print(val)

    if args.action == 'save-screen':
        try:
            from PIL import Image, ImageOps, ImageEnhance
        except ImportError:
            parser.error('Please install Pillow (or the older PIL) to use --save-screen')
        # formatting the filename
        if args.filename: fmt = args.filename
        else: fmt = 'ds1054z-scope-display_{ts}.png'
        ts = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        filename = fmt.format(ts=ts)
        # need to find out file extension for Pillow on Windows...
        ext = os.path.splitext(filename)[1]
        if not ext: parser.error('could not detect the image file type extension from the filename')
        # getting and saving the image
        im = Image.open(io.BytesIO(ds.display_data))
        overlay_filename = pkg_resources.resource_filename("ds1054z","resources/overlay.png")
        overlay = Image.open(overlay_filename)
        alpha_100_percent =  Image.new(overlay.mode, overlay.size, color=(0,0,0,0))
        overlay = Image.blend(alpha_100_percent, overlay, args.overlay)
        im.putalpha(255)
        im = Image.alpha_composite(im, overlay)
        if args.printable:
            im = Image.merge("RGB", im.split()[0:3])
            im = ImageOps.invert(im)
            im = ImageEnhance.Color(im).enhance(0)
            im = ImageEnhance.Brightness(im).enhance(0.95)
            im = ImageEnhance.Contrast(im).enhance(2)
            im = im.convert('L')
            im = im.point(lambda x: x if x<252 else 255)
        else:
            im = im.convert('RGB')
        im.save(filename, format=ext[1:])
        if not args.verbose: print(filename)
        else: print("Saved file: " + filename)

    if args.action == 'save-data':
        ts = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        filename = args.filename.format(ts=ts)
        ext = os.path.splitext(filename)[1]
        if not ext: parser.error('could not detect the file type extension from the filename')
        kind = ext[1:]
        if kind in ('csv', 'txt'):
            import csv
            data = []
            channels = ds.displayed_channels
            for channel in channels:
                data.append(ds.get_waveform_samples(channel, mode=args.mode))
            if args.with_time:
                data.insert(0, ds.waveform_time_values_decimal)
            lengths = [len(samples) for samples in data]
            if len(set(lengths)) != 1:
                logger.error('Different number of samples read for different channels!')
                sys.exit(1)
            zip_longest
            def csv_open(filename):
                if sys.version_info >= (3, 0):
                    return open(filename, 'w', newline='')
                else:
                    return open(filename, 'wb')
            with csv_open(filename) as csv_file:
                delimiter = ',' if kind == 'csv' else '\t'
                csv_writer = csv.writer(csv_file, delimiter=delimiter)
                if args.with_time:
                    csv_writer.writerow(['TIME'] + channels)
                else:
                    csv_writer.writerow(channels)
                for vals in zip_longest(*data):
                    if args.with_time:
                        vals = [vals[0]] + ['{:.2e}'.format(val) for val in vals[1:]]
                    else:
                        vals = ['{:.2e}'.format(val) for val in vals]
                    csv_writer.writerow(vals)
        else:
            parser.error('This tool cannot handle the requested --type')
        if not args.verbose: print(filename)
        else: print("Saved file: " + filename)

    if args.action == 'shell':
        try:
            import atexit
            import readline
            histfile = os.path.join(os.path.expanduser("~"), ".ds1054z_history")
            try:
                readline.read_history_file(histfile)
            except IOError as e:
                if e.errno != errno.ENOENT:
                    raise e
            atexit.register(readline.write_history_file, histfile)
        except ImportError:
            pass
        run_shell(ds)

    if args.action == 'measure':
        v = ds.get_channel_measurement(args.channel, args.item, type=args.type)
        if v is not None:
            print(v)

def run_shell(ds):
    """ ds : DS1054Z instance """
    from vxi11.vxi11 import Vxi11Exception
    print(SHELL_HOWTO)
    print('> *IDN?')
    print(ds.query("*IDN?"))
    try:
        while True:
            cmd = input('> ')
            cmd = cmd.strip()
            if cmd in ('quit', 'exit'):
                break
            if '?' in cmd:
                try:
                    ret = ds.query_raw(cmd)
                    try:
                        print(ret.decode('utf-8').strip())
                    except UnicodeDecodeError:
                        print('binary message:', ret)
                except Vxi11Exception:
                    print("No response from the scope. Bad cmd?")
            else:
                ds.write(cmd)
    except KeyboardInterrupt as e:
        print('\nCtrl-C pressed.')
    except EOFError:
        pass
    print('Exiting...')

if __name__ == "__main__":
    main()

