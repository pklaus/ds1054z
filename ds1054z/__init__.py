# -*- coding: utf-8 -*-

"""
The class :py:mod:`ds1054z.DS1054Z` - Easy communication with your scope
========================================================================
"""

import logging
import re
import time
import sys
import struct
import decimal

import vxi11

logger = logging.getLogger(__name__)

try:
    clock = time.perf_counter
except AttributeError:
    clock = time.time

class DS1054Z(vxi11.Instrument):
    """
    This class represents the oscilloscope.

    :ivar product: like ``'DS1054Z'`` (depending on your device)
    :ivar vendor:  should be ``'RIGOL TECHNOLOGIES'``
    :ivar serial:  e.g. ``'DS1ZA118171631'``
    :ivar firmware: e.g. ``'00.04.03.SP1'``
    """

    IDN_PATTERN = r'^RIGOL TECHNOLOGIES,DS1\d\d\dZ( Plus)?,'
    ENCODING = 'utf-8'
    H_GRID = 12
    SAMPLES_ON_DISPLAY = 1200
    DISPLAY_DATA_BYTES = 1152068
    SCALE_MANTISSAE = (1, 2, 5)
    MIN_TIMEBASE_SCALE = 5E-9
    MAX_TIMEBASE_SCALE = 50E0
    MIN_CHANNEL_SCALE = 1E-3
    MAX_CHANNEL_SCALE = 1E1
    MIN_PROBE_RATIO = 0.01
    MAX_PROBE_RATIO = 1000

    def __init__(self, host, *args, **kwargs):
        self.start = clock()
        super(DS1054Z, self).__init__(host, *args, **kwargs)
        idn = self.idn
        match = re.match(self.IDN_PATTERN, idn)
        if not match:
            msg = "Unknown device identification:\n%s\n" \
                  "If you believe this device should be supported " \
                  "by this package, feel free to contact " \
                  "the maintainer with this information." % idn
            raise NameError(msg)
        idn = idn.split(',')
        self.vendor = idn[0]
        self.product = idn[1]
        self.serial = idn[2]
        self.firmware = idn[3]
        self.mask_begin_num = None
        self.possible_probe_ratio_values = self._populate_possible_values('PROBE_RATIO')
        self.possible_timebase_scale_values = self._populate_possible_values('TIMEBASE_SCALE')
        self.possible_channel_scale_values = self._populate_possible_values('CHANNEL_SCALE')

    def clock(self):
        return clock() - self.start

    def log_timing(self, msg):
        logger.info('{0:.3f} - {1}'.format(self.clock(), msg))

    def write_raw(self, cmd, *args, **kwargs):
        self.log_timing('starting write')
        logger.debug('sending: ' + repr(cmd))
        super(DS1054Z, self).write_raw(cmd, *args, **kwargs)
        self.log_timing('finishing write')

    def read_raw(self, *args, **kwargs):
        self.log_timing('starting read')
        data = super(DS1054Z, self).read_raw(*args, **kwargs)
        self.log_timing('finished reading {0} bytes'.format(len(data)))
        if len(data) > 200:
            logger.debug('received a long answer: {0} ... {1}'.format(format_hex(data[0:10]), format_hex(data[-10:])))
        else:
            logger.debug('received: ' + repr(data))
        return data

    def query(self, message, *args, **kwargs):
        """
        Write a message to the scope and read back the answer.
        See :py:meth:`vxi11.Instrument.ask()` for optional parameters.
        """
        return self.ask(message, *args, **kwargs)

    def query_raw(self, message, *args, **kwargs):
        """
        Write a message to the scope and read a (binary) answer.

        This is the slightly modified version of :py:meth:`vxi11.Instrument.ask_raw()`.
        It takes a command message string and returns the answer as bytes.

        :param str message: The SCPI command to send to the scope.
        :return: Data read from the device
        :rtype: bytes
        """
        data = message.encode(self.ENCODING)
        return self.ask_raw(data, *args, **kwargs)

    def _interpret_channel(self, channel):
        """ wrapper to allow specifying channels by their name (str) or by their number (int) """
        if type(channel) == int:
            channel = 'CHAN' + str(channel)
        return channel

    @property
    def running(self):
        return self.query(':TRIGger:STATus?') in ('TD', 'WAIT', 'RUN', 'AUTO')

    @property
    def waveform_preamble(self):
        """
        Provides the values returned by the command ``:WAVeform:PREamble?``.
        They will be converted to float and int as appropriate.

        Those values are essential if you want to convert BYTE data from the scope
        to voltage readings or if you want to recreate the scope's
        display content programmatically.

        This property is also accessible via the wrapper property :py:attr:`waveform_preamble_dict`
        where it returns a :py:obj:`dict` instead of a :py:obj:`tuple`.

        This property will be fetched from the scope every time you access it.

        :return: (fmt, typ, pnts, cnt, xinc, xorig, xref, yinc, yorig, yref)
        :rtype: tuple of float and int values
        """
        values = self.query(":WAVeform:PREamble?")
        #
        # From the Programming Guide:
        # format: <format>,<type>,<points>,<count>,<xincrement>,<xorigin>,<xreference>,<yincrement>,<yorigin>,<yreference>
        #
        # for example: 0,0,1200,1,2.000000e-05,-1.456000e-02,0,4.000000e-02,-75,127
        #
        #             0   format      0 (BYTE), 1 (WORD) or 2 (ASC)
        #             0   type        0 (NORMal), 1 (MAXimum) or 2 (RAW)
        #          1200   points      an integer between 1 and 12000000
        #             1   count       number of averages
        #  2.000000e-05   xincrement  time delta between subsequent data points
        # -1.456000e-02   xorigin     start time
        #             0   xreference  reference time (always zero?)
        #  4.000000e-02   yincrement
        #           -75   yorigin
        #           127   yreference
        #
        values = values.split(',')
        assert len(values) == 10
        fmt, typ, pnts, cnt, xref, yorig, yref  = (int(val) for val in values[:4] + values[6:7] + values[8:10])
        xinc, xorig, yinc = (float(val) for val in values[4:6] + values[7:8])
        return (fmt, typ, pnts, cnt, xinc, xorig, xref, yinc, yorig, yref)

    @property
    def waveform_preamble_dict(self):
        """
        Provides a dictionary with 10 entries corresponding to the
        tuple items of the property :py:attr:`waveform_preamble`.

        This property will be fetched from the scope every time you access it.

        :return: {'fmt', 'typ', 'pnts', 'cnt', 'xinc', 'xorig', 'xref', 'yinc', 'yorig', 'yref'}
        :rtype: dict
        """
        keys = 'fmt, typ, pnts, cnt, xinc, xorig, xref, yinc, yorig, yref'.split(', ')
        return dict(zip(keys, self.waveform_preamble))

    def get_waveform_samples(self, channel, mode='NORMal'):
        """
        Returns the waveform voltage samples of the specified channel.

        The mode argument translates into a call to ``:WAVeform:MODE``
        setting up how many samples you want to read back. If you set it
        to normal mode, only the screen content samples will be returned.
        In raw mode, the whole scope memory will be read out, which can
        take many seconds depending on the current memory depth.

        If you set mode to RAW, the scope will be stopped first.
        Please start it again yourself, if you need to, afterwards.

        If you set mode to NORMal you will always get 1200 samples back.
        Those 1200 points represent the waveform over the full screen width.
        This can happend when you stop the acquisition and move the waveform
        horizontally so that it starts or ends inside the screen area,
        the missing data points are being set to float('nan') in the list.

        :param channel: The channel name (like 'CHAN1' or 1).
        :type channel: int or str
        :param str mode: can be 'NORMal', 'MAX', or 'RAW'
        :return: voltage samples
        :rtype: list of float values
        """

        buff = self.get_waveform_bytes(channel, mode=mode)
        fmt, typ, pnts, cnt, xinc, xorig, xref, yinc, yorig, yref = self.waveform_preamble
        samples = list(struct.unpack(str(len(buff))+'B', buff))
        samples = [(val - yorig - yref)*yinc for val in samples]
        if self.mask_begin_num:
            at_begin = self.mask_begin_num[0]
            num = self.mask_begin_num[1]
            if at_begin:
                samples = [float('nan')] * num + samples[num:]
            else:
                samples = samples[:-num] + [float('nan')] * num
        return samples

    def get_waveform_bytes(self, channel, mode='NORMal'):
        """
        Get the waveform data for a specific channel as :py:obj:`bytes`.
        (In most cases you would want to use the higher level
        function :py:meth:`get_waveform_samples()` instead.)

        This function distinguishes between requests for reading
        the waveform data currently being displayed on the screen
        or if you will be reading the internal memory.
        If you set mode to RAW, the scope will be stopped first and
        you will get the bytes from internal memory.
        (Please start it again yourself, if you need to, afterwards.)
        If you set the mode to MAXimum this function will return the
        internal memory if the scope is stopped, and the screen
        memory otherwise.

        In case the internal memory will be read, the data request will
        automatically be split into chunks if it's impossible to read
        all bytes at once.

        :param channel: The channel name (like CHAN1, ...). Alternatively specify the channel by its number (as integer).
        :type channel: int or str
        :param str mode: can be NORMal, MAXimum, or RAW
        :return: The waveform data
        :rtype: bytes
        """
        channel = self._interpret_channel(channel)
        if mode.upper().startswith('NORM') or (self.running and mode.upper().startswith('MAX')):
            return self._get_waveform_bytes_screen(channel, mode=mode)
        else:
            return self._get_waveform_bytes_internal(channel, mode=mode)

    def _get_waveform_bytes_screen(self, channel, mode='NORMal'):
        """
        This function returns the waveform bytes from the scope if you desire
        to read the bytes corresponding to the screen content.
        """
        channel = self._interpret_channel(channel)
        assert mode.upper().startswith('NOR') or mode.upper().startswith('MAX')
        self.write(":WAVeform:SOURce " + channel)
        self.write(":WAVeform:FORMat BYTE")
        self.write(":WAVeform:MODE " + mode)
        wp = self.waveform_preamble_dict
        pnts = wp['pnts']
        starting_at = 1
        stopping_at = self.SAMPLES_ON_DISPLAY
        if pnts < self.SAMPLES_ON_DISPLAY:
            """
            The oscilloscope seems to be stopped and in addition
            the waveform is not going all the way from the left to the
            right end of the screen (due to horizontal scrolling).
            We will not get back the expected 1200 samples in this case.
            Thus, a fix is needed to determine at which side the samples are missing.
            """
            self.write(":WAVeform:STARt {0}".format(self.SAMPLES_ON_DISPLAY))
            self.write(":WAVeform:STARt 1")
            if int(self.query(":WAVeform:STARt?")) != 1:
                starting_at = self.SAMPLES_ON_DISPLAY - pnts + 1
            else:
                stopping_at = pnts
        self.write(":WAVeform:STARt {0}".format(starting_at))
        self.write(":WAVeform:STOP {0}".format(stopping_at))
        tmp_buff = self.query_raw(":WAVeform:DATA?")
        buff = DS1054Z.decode_ieee_block(tmp_buff)
        assert len(buff) == pnts
        if pnts < self.SAMPLES_ON_DISPLAY:
            logger.info('Accessing screen values when the waveform is not entirely ')
            logger.info('filling the screen - padding missing bytes with 0x00!')
            num = self.SAMPLES_ON_DISPLAY - pnts
            zero_bytes = b"\x00" * num
            if starting_at == 1:
                buff += zero_bytes
                self.mask_begin_num = (0, num)
            else:
                buff = zero_bytes + buff
                self.mask_begin_num = (1, num)
        else:
            self.mask_begin_num = None
        return buff

    def _get_waveform_bytes_internal(self, channel, mode='RAW'):
        """
        This function returns the waveform bytes from the scope if you desire
        to read the bytes corresponding to the internal (deep) memory.
        """
        channel = self._interpret_channel(channel)
        assert mode.upper().startswith('MAX') or mode.upper().startswith('RAW')
        if self.running:
            self.stop()
        self.write(":WAVeform:SOURce " + channel)
        self.write(":WAVeform:FORMat BYTE")
        self.write(":WAVeform:MODE " + mode)
        wp = self.waveform_preamble_dict
        pnts = wp['pnts']
        buff = b""
        max_byte_len = 250000
        pos = 1
        while len(buff) < pnts:
            self.write(":WAVeform:STARt {0}".format(pos))
            end_pos = min(pnts, pos+max_byte_len-1)
            self.write(":WAVeform:STOP {0}".format(end_pos))
            tmp_buff = self.query_raw(":WAVeform:DATA?")
            buff += DS1054Z.decode_ieee_block(tmp_buff)
            pos += max_byte_len
        return buff

    def _populate_possible_values(self, which):
        """
        Populates list of possible values.

        Uses MIN_which, MAX_which, and SCALE_MANTISSAE attributes.
        """
        min_val = getattr(self, 'MIN_' + which.upper())
        max_val = getattr(self, 'MAX_' + which.upper())
        mantissae = self.SCALE_MANTISSAE
        possible_values = []
        # initialize with the decimal mantissa and exponent for min_val
        mantissa_idx = mantissae.index(int('{0:e}'.format(min_val)[0]))
        exponent = int('{0:e}'.format(min_val).split('e')[1])
        value = min_val
        while value <= max_val:
            # add the value to the list of possible values
            possible_values.append(value)
            # construct the next value:
            mantissa_idx += 1
            mantissa_idx %= len(mantissae)
            if mantissa_idx == 0: exponent += 1
            value = '{0}e{1}'.format(mantissae[mantissa_idx], exponent)
            value = decimal.Decimal(value)
            value = float(value)
        return possible_values

    @property
    def timebase_offset(self):
        """
        The timebase offset of the scope in seconds.

        You can change the timebase offset by assigning to this property:

        >>> scope.timebase_offset = 200e-6

        The possible values according to the programming manual:

        * -Screen/2 to 1s or -Screen/2 to 5000s.
        """
        return float(self.query(':TIMebase:MAIN:OFFSet?'))

    @timebase_offset.setter
    def timebase_offset(self, new_offset):
        self.write(":TIMebase:MAIN:OFFSet {0}".format(new_offset))

    @property
    def timebase_scale(self):
        """
        The timebase scale of the scope in seconds.

        The possible values according to the programming guide:

        * Normal mode:  5 ns  to  50 s  in 1-2-5 steps
        * Roll mode:  200 ms  to  50 s  in 1-2-5 steps

        You can change the timebase like this:

        >>> scope.timebase_scale = 200E-9

        The nearest possible value will be set.
        """
        return float(self.query(':TIMebase:MAIN:SCALe?'))

    @timebase_scale.setter
    def timebase_scale(self, new_timebase):
        new_timebase = min(self.possible_timebase_scale_values, key=lambda x:abs(x-new_timebase))
        self.write(":TIMebase:MAIN:SCALe {0}".format(new_timebase))

    @property
    def sample_rate(self):
        return float(self.query(':ACQuire:SRATe?'))

    @property
    def waveform_time_values(self):
        """
        The timestamps that belong to the waveform samples accessed to
        to be accessed beforehand.

        Access this property only after fetching your waveform data,
        otherwise the values will not be correct.

        Will be fetched every time you access this property.

        :return: sample timestamps (in seconds)
        :rtype: list of float
        """
        wp = self.waveform_preamble_dict
        tv = []
        for i in range(self.memory_depth_curr_waveform):
            tv.append(wp['xinc'] * i + wp['xorig'])
        return tv

    @property
    def waveform_time_values_decimal(self):
        """
        This is a wrapper for :py:attr:`waveform_time_values`.
        It returns the time samples as :py:obj:`Decimal` values instead
        of float which can be convenient for writing with an appropriate
        precision to a human readable file format.

        Access this property only after fetching your waveform data,
        otherwise the values will not be correct.

        Will be fetched every time you access this property.

        :return: sample timestamps (in seconds)
        :rtype: list of :py:obj:`Decimal`
        """
        wp = self.waveform_preamble_dict
        xinc_fmt = list('{0:.6e}'.format(wp['xinc']).partition('e'))
        xinc_fmt[0] = xinc_fmt[0].rstrip('0')
        xinc_fmt = ''.join(xinc_fmt)
        xinc_dec = decimal.Decimal(xinc_fmt)
        return [decimal.Decimal(t).quantize(xinc_dec) for t in self.waveform_time_values]

    @staticmethod
    def format_si_prefix(number, unit=None, as_unicode=True, number_format='{0:.6f}'):
        """
        Formats the given number by choosing an appropriate metric prefix
        and stripping the formatted number of its zero-digits
        giving a nice human readable form.

        If you provide a unit, it will be appended to the resulting string.

        Example:

        >>> DS1054Z.format_si_prefix(2E-9, unit='s')
        '2 ns'
        """
        prefixes  = [( 1e9, 'G'), ( 1e6, 'M'), ( 1e3, 'k'), (  1e0, '' )]
        prefixes += [(1e-3, 'm'), (1e-6, 'u'), (1e-9, 'n'), (1e-12, 'p')]
        formatted_number = None
        for prefix in prefixes:
            if abs(number) < prefix[0]:
                continue
            formatted_number = [number_format.format(number / prefix[0]), prefix[1]]
            break
        if not formatted_number:
            formatted_number = ['{0}'.format(number / prefixes[-1][0]), prefixes[-1][1]]
        formatted_number[0] = formatted_number[0].rstrip('0').rstrip('.')
        formatted_number = ' '.join(formatted_number)
        if as_unicode:
            formatted_number = formatted_number.replace('u', 'µ')
        if unit:
            formatted_number += unit
        return formatted_number

    @staticmethod
    def decode_ieee_block(ieee_bytes):
        """
        Strips headers (and trailing bytes) from a IEEE binary data block off.

        This is the block format commands like ``:WAVeform:DATA?``, ``:DISPlay:DATA?``,
        ``:SYSTem:SETup?``, and ``:ETABle<n>:DATA?`` return their data in.

        Named after ``decode_ieee_block()`` in python-ivi
        """
        if sys.version_info >= (3, 0):
            n_header_bytes = int(chr(ieee_bytes[1]))+2
        else:
            n_header_bytes = int(ieee_bytes[1])+2
        n_data_bytes = int(ieee_bytes[2:n_header_bytes].decode('ascii'))
        return ieee_bytes[n_header_bytes:n_header_bytes + n_data_bytes]

    @property
    def idn(self):
        """
        The ``*IDN?`` string of the device.
        Will be fetched every time you access this property.
        """
        return self.query("*IDN?")

    def stop(self):
        """ Stop acquisition """
        self.write(":STOP")

    def run(self):
        """ Start acquisition """
        self.write(":RUN")

    def single(self):
        """ Set the oscilloscope to the single trigger mode. """
        self.write(":SINGle")

    def tforce(self):
        """ Generate a trigger signal forcefully. """
        self.write(":TFORce")

    def set_waveform_mode(self, mode='NORMal'):
        """ Changing the waveform mode """
        self.write('WAVeform:MODE ' + mode)

    @property
    def memory_depth_curr_waveform(self):
        """
        The current memory depth of the oscilloscope.
        This value is the number of samples to expect when reading the
        waveform data and depends on the status of the scope (running / stopped).

        Needed by :py:attr:`waveform_time_values`.

        This property will be updated every time you access it.
        """
        if self.query(':WAVeform:MODE?').startswith('NORM') or self.running:
            return self.SAMPLES_ON_DISPLAY
        else:
            return self.memory_depth_internal_total

    @property
    def memory_depth_internal_currently_shown(self):
        """
        The number of samples in the **raw (=deep) memory** of the oscilloscope
        which are **currently being displayed on the screen**.

        This property will be updated every time you access it.
        """
        mdep = self.query(":ACQuire:MDEPth?")
        if mdep == "AUTO":
            srate = self.sample_rate
            scal = self.timebase_scale
            mdep = srate * scal * self.H_GRID
        return int(float(mdep))

    @property
    def memory_depth_internal_total(self):
        """
        The total number of samples in the **raw (=deep) memory** of the oscilloscope.
        If it's running, the scope will be stopped temporarily when accessing this value.

        This property will be updated every time you access it.
        """
        mdep = self.query(":ACQuire:MDEPth?")
        if mdep == "AUTO":
            curr_running = self.running
            curr_mode = self.query(':WAVeform:MODE?')
            if curr_running:
                self.stop()
            if curr_mode.startswith('NORM'):
                # in this case we need to switch to RAW mode to find out the memory depth
                self.write(':WAVeform:MODE RAW')
                mdep = self.waveform_preamble_dict['pnts']
                self.write(':WAVeform:MODE ' + curr_mode)
            else:
                mdep = self.waveform_preamble_dict['pnts']
            if curr_running:
                self.run()
        return int(float(mdep))

    @property
    def display_data(self):
        """
        The bitmap bytes of the current screen content.
        This property will be updated every time you access it.
        """
        self.write(":DISPlay:DATA?")
        logger.info("Receiving screen capture...")
        buff = self.read_raw(self.DISPLAY_DATA_BYTES)
        logger.info("read {0} bytes in .display_data".format(len(buff)))
        if len(buff) != self.DISPLAY_DATA_BYTES:
            raise NameError("display_data: didn't receive the right number of bytes")
        return DS1054Z.decode_ieee_block(buff)

    @property
    def displayed_channels(self):
        """
        The list of channels currently displayed on the scope.
        This property will be updated every time you access it.
        """
        channel_list = []
        for channel in ["CHAN1", "CHAN2", "CHAN3", "CHAN4", "MATH"]:
            if self.query(channel + ":DISPlay?") == '1':
                channel_list.append(channel)
        return channel_list

    def get_probe_ratio(self, channel):
        """
        Returns the probe ratio for a specific channel
        """
        channel = self._interpret_channel(channel)
        return float(self.query(':{0}:PROBe?'.format(channel)))

    def set_probe_ratio(self, channel, ratio):
        """
        Set the probe ratio of a specific channel.

        The possible ratio values are: 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1,
        2, 5, 10, 20, 50, 100, 200, 500, and 1000.

        :param channel: The channel name (like CHAN1, ...). Alternatively specify the channel by its number (as integer).
        :type channel: int or str
        :param float ratio: Ratio of the probe connected to the channel
        """
        ratio = float(ratio)
        ratio = min(self.possible_probe_ratio_values, key=lambda x:abs(x-ratio))
        channel = self._interpret_channel(channel)
        self.write(":{0}:PROBe {1}".format(channel, ratio))


    def get_channel_offset(self, channel):
        """
        Returns the channel offset in volts.
        """
        channel = self._interpret_channel(channel)
        return float(self.query(':{0}:OFFSet?'.format(channel)))

    def set_channel_offset(self, channel, volts):
        """
        Set the (vertical) offset of a specific channel in Volt.

        The range of possible offset values depends on the current vertical scale and on
        the probe ratio. With the probe ratio set to 1x the offset can be set between:

        * -100V and +100V (if vertical scale ≥ 500mV/div), or
        * -2V and +2V (if vertical scale < 500mV/div).

        The range scales with the probe ratio. Thus, when the probe ratio is set to 10x,
        for example, the offset could be set between:

        * -1000V and +1000V (if vertical scale ≥ 5V/div), or
        * -20V and +20V (if vertical scale < 5V/div).

        :param channel: The channel name (like CHAN1, ...). Alternatively specify the channel by its number (as integer).
        :type channel: int or str
        :param float volts: the new vertical scale offset in volts
        """
        channel = self._interpret_channel(channel)
        self.write(":{0}:OFFSet {1}".format(channel, volts))

    def get_channel_scale(self, channel):
        """
        Returns the channel scale in volts.

        :return: channel scale
        :rtype: float
        """
        channel = self._interpret_channel(channel)
        return float(self.query(':{0}:SCALe?'.format(channel)))

    def set_channel_scale(self, channel, volts, use_closest_match=False):
        """
        The default steps according to the programming guide:

        * 1mV, 2mV, 5mV, 10mV...10V (for a 1x probe),
        * 10mV, 20mV, 50mV, 100mV...100V (for a 10x probe).

        You can also set the scale to values in between those steps
        (as with using the fine adjustment mode on the scope).

        :param channel: The channel name (like CHAN1, ...). Alternatively specify the channel by its number (as integer).
        :type channel: int or str
        :param float volts: the new value for the vertical channel scaling
        :param bool use_closest_match: round new scale value to closest match from the default steps
        """
        channel = self._interpret_channel(channel)
        if use_closest_match:
            probe_ratio = self.get_probe_ratio(channel)
            possible_channel_scale_values = [val * probe_ratio for val in self.possible_channel_scale_values]
            volts = min(possible_channel_scale_values, key=lambda x:abs(x-volts))
        self.write(":{0}:SCALe {1}".format(channel, volts))

    def get_channel_measurement(self, channel, item, type="CURRent"):
        """
        Measures value on a channel

        :param channel: The channel name (like CHAN1, ...). Alternatively specify the channel by its number (as integer).
        :type channel: int or str
        :param str item: Item to measure, can be vmax, vmin, vpp, vtop, vbase, vamp, vavg, vrms, overshoot, preshoot, marea, mparea, period, frequency, rtime, ftime, pwidth, nwidth, pduty, nduty, rdelay, fdelay, rphase, fphase, tvmax, tvmin, pslewrate, nslewrate, vupper, vmid, vlower, variance, pvrms
        :param str type: Type of measurement, can be CURRent, MAXimum, MINimum, AVERages, DEViation
        """
        channel = self._interpret_channel(channel)
        ret = float(self.query(":MEASure:STATistic:item? {0},{1},{2}".format(type, item, channel)))
        if ret == 9.9e37: # This is a value which means that the measurement cannot be taken for some reason (channel disconnected/no edge in the trace etc.)
            return None
        return ret

def format_hex(byte_str):
    if sys.version_info >= (3, 0):
        return ' '.join( [ "{:02X}".format(x)  for x in byte_str ] )
    else:
        return ' '.join( [ "{:02X}".format(ord(x))  for x in byte_str ] )
