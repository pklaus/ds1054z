"""
The class :py:mod:`ds1054z.DS1054Z` - Easy communication with your scope
========================================================================
"""

import logging
import re
import time
import sys
import struct

import vxi11

logger = logging.getLogger(__name__)

try:
    clock = time.perf_counter
except:
    clock = time.time

class DS1054Z(vxi11.Instrument):
    """
    This class represents the oscilloscope.

    :ivar product: like ``'DS1054Z'`` (depending on your device)
    :ivar vendor:  should be ``'RIGOL TECHNOLOGIES'``
    :ivar serial:  e.g. ``'DS1ZA118171631'``
    :ivar firmware: e.g. ``'00.04.03.SP1'``
    """

    IDN_PATTERN = r'^RIGOL TECHNOLOGIES,DS1\d\d\dZ,'
    ENCODING = 'utf-8'
    H_GRID = 12
    DISPLAY_DATA_BYTES = 1152068

    def __init__(self, host, *args, **kwargs):
        self.start = clock()
        super(DS1054Z, self).__init__(host, *args, **kwargs)
        idn = self.idn
        assert re.match(self.IDN_PATTERN, idn)
        idn = idn.split(',')
        self.vendor = idn[0]
        self.product = idn[1]
        self.serial = idn[2]
        self.firmware = idn[3]

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
        self.log_timing('finished reading {} bytes'.format(len(data)))
        if len(data) > 200:
            logger.debug('received a long answer: {} ... {}'.format(format_hex(data[0:10]), format_hex(data[-10:])))
        else:
            logger.debug('received: ' + repr(data))
        return data

    def query(self, message, *args, **kwargs):
        """
        Write a message to the scope and read back the answer.
        See vxi11.Instrument.ask() for optional parameters.
        """
        return self.ask(message, *args, **kwargs)

    def query_raw(self, message, *args, **kwargs):
        """
        Write a message to the scope and read a (binary) answer.

        This is the slightly modified version of vxi11.Instrument.ask_raw().
        It takes a command message string and returns the answer as bytes.
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
        return self.ask(':TRIGger:STATus?') in ('TD', 'WAIT', 'RUN', 'AUTO')

    @property
    def waveform_preamble(self):
        """
        Returns a tuple of length 10 with the values returned by the command
        ``:WAVeform:PREamble?`` parsed as floats and ints.

        They are essential values if you want to convert BYTE data from the scope
        to voltage readings or if you want to recreate the scope's
        display content programmatically.

        This property will be fetched from the scope every time you access it.

        :return: (fmt, typ, pnts, cnt, xinc, xorig, xref, yinc, yorig, yref)
        :rtype: tuple
        """
        values = self.query(":WAVeform:PREamble?")
        # format: <format>,<type>,<points>,<count>,<xincrement>,<xorigin>,<xreference>,<yincrement>,<yorigin>,<yreference>
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
        values = values.split(',')
        assert len(values) == 10
        fmt, typ, pnts, cnt, xref, yorig, yref  = (int(val) for val in values[:4] + values[6:7] + values[8:10])
        xinc, xorig, yinc = (float(val) for val in values[4:6] + values[7:8])
        return (fmt, typ, pnts, cnt, xinc, xorig, xref, yinc, yorig, yref)

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

        :param channel: The channel name (like 'CHAN1' or 1).
        :type channel: int or str
        :param str mode: can be 'NORMal', 'MAX', or 'RAW'
        :return: voltage samples
        :rtype: list of float values
        """

        buff = self.get_waveform_bytes(channel, mode)
        fmt, typ, pnts, cnt, xinc, xorig, xref, yinc, yorig, yref = self.waveform_preamble
        data = struct.unpack(str(len(buff))+'B', buff)
        data = list(data)
        data = [(val - yorig - yref)*yinc for val in data]
        return data

    def get_waveform_bytes(self, channel, mode='NORMal'):
        """
        Get the waveform data for a specific channel as :py:obj:`bytes`.
        (In most cases you would want to use the higher level
        function :py:meth:`get_waveform_values()` instead.)

        This function automatically splits the data request into chunks
        if it cannot read all data in a single request.

        If you set mode to RAW, the scope will be stopped first.
        Please start it again yourself, if you need to, afterwards.

        :param channel: The channel name (like CHAN1, ...). Alternatively specify the channel by its number (as integer).
        :type channel: int or str
        :param str mode: can be NORMal, MAX, or RAW
        :return: The waveform data
        :rtype: bytes
        """
        channel = self._interpret_channel(channel)
        if mode == 'RAW':
            if self.running:
                self.stop()
        self.write(":WAVeform:SOURce " + channel)
        self.write(":WAVeform:FORMat BYTE")
        self.write(":WAVeform:MODE " + mode)
        if mode.upper().startswith('NORM') or self.running:
            total = 1200
        else:
            total = self.memory_depth
        buff = b""
        max_byte_len = 250000
        pos = 1
        while len(buff) < total:
            remaining =  total - len(buff)
            self.write(":WAVeform:STARt {}".format(pos))
            end_pos = min(total, pos+max_byte_len-1)
            self.write(":WAVeform:STOP {}".format(end_pos))
            tmp_buff = self.query_raw(":WAVeform:DATA?")
            buff += DS1054Z._clean_tmc_header(tmp_buff)
            pos += max_byte_len
        return buff

    @staticmethod
    def _clean_tmc_header(tmc_data):
        if sys.version_info >= (3, 0):
            n_header_bytes = int(chr(tmc_data[1]))+2
        else:
            n_header_bytes = int(tmc_data[1])+2
        n_data_bytes = int(tmc_data[2:n_header_bytes].decode('ascii'))
        return tmc_data[n_header_bytes:n_header_bytes + n_data_bytes]

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

    @property
    def memory_depth(self):
        """
        The current memory depth of the oscilloscope as float.
        This property will be updated every time you access it.
        """
        mdep = self.query(":ACQuire:MDEPth?")
        if mdep == "AUTO":
            srate = self.query(":ACQuire:SRATe?")
            scal = self.query(":TIMebase:MAIN:SCALe?")
            mdep = self.H_GRID * float(scal) * float(srate)
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
        logger.info("read {} bytes in .display_data".format(len(buff)))
        if len(buff) != self.DISPLAY_DATA_BYTES:
            raise NameError("display_data: didn't receive the right number of bytes")
        return DS1054Z._clean_tmc_header(buff)

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


def format_hex(byte_str):
    if sys.version_info >= (3, 0):
        return ''.join( [ "%02X " % x  for x in byte_str ] ).strip()
    else:
        return ''.join( [ "%02X " % ord(x)  for x in byte_str ] ).strip()
