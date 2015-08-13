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
    SAMPLES_ON_DISPLAY = 1200
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
        self.mask_begin_num = None

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
        Provides the values returned by the command ``:WAVeform:PREamble?``.
        They will be converted to floats and ints as appropriate.

        They are essential values if you want to convert BYTE data from the scope
        to voltage readings or if you want to recreate the scope's
        display content programmatically.

        This property is also accessible via the wrapper property :py:attr:`waveform_preamble_dict`
        where it returns a :py:obj:`dict` instead of a :py:obj:`tuple`.

        This property will be fetched from the scope every time you access it.

        :return: (fmt, typ, pnts, cnt, xinc, xorig, xref, yinc, yorig, yref)
        :rtype: tuple
        """
        values = self.query(":WAVeform:PREamble?")
        # from the Programming Guide:
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

    @property
    def waveform_preamble_dict(self):
        """
        Provides a dictionary with 10 entries corresponding to the
        tuple items of the property :py:attr:`waveform_preamble`.

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
            self.write(":WAVeform:STARt {}".format(self.SAMPLES_ON_DISPLAY))
            self.write(":WAVeform:STARt 1")
            if int(self.query(":WAVeform:STARt?")) != 1:
                starting_at = self.SAMPLES_ON_DISPLAY - pnts + 1
            else:
                stopping_at = pnts
        self.write(":WAVeform:STARt {}".format(starting_at))
        self.write(":WAVeform:STOP {}".format(stopping_at))
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
            self.write(":WAVeform:STARt {}".format(pos))
            end_pos = min(pnts, pos+max_byte_len-1)
            self.write(":WAVeform:STOP {}".format(end_pos))
            tmp_buff = self.query_raw(":WAVeform:DATA?")
            buff += DS1054Z.decode_ieee_block(tmp_buff)
            pos += max_byte_len
        return buff

    @staticmethod
    def decode_ieee_block(ieee_bytes):
        """
        Strips headers (and trailing bytes) from a IEEE binary data block off.

        Named after :any:`decode_ieee_block` in python-ivi
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


def format_hex(byte_str):
    if sys.version_info >= (3, 0):
        return ''.join( [ "%02X " % x  for x in byte_str ] ).strip()
    else:
        return ''.join( [ "%02X " % ord(x)  for x in byte_str ] ).strip()
