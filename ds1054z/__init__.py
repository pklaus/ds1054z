
import logging
import re
import time
import sys

import vxi11

logger = logging.getLogger(__name__)

try:
    clock = time.perf_counter
except:
    clock = time.time

class DS1054Z(vxi11.Instrument):

    IDN_PATTERN = r'^RIGOL TECHNOLOGIES,DS1\d\d\dZ,'
    ENCODING = 'utf-8'
    H_GRID = 12
    DISPLAY_DATA_BYTES = 1152068

    def __init__(self, *args, **kwargs):
        self.start = clock()
        super(DS1054Z, self).__init__(*args, **kwargs)
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

    def query(self, *args, **kwargs):
        return self.ask(*args, **kwargs)

    def query_raw(self, cmd, *args, **kwargs):
        '''
        this is the slightly modified version of query_raw() / ask_raw():
        it takes a command string and returns bytes
        '''
        cmd = cmd.encode(self.ENCODING)
        return self.ask_raw(cmd, *args, **kwargs)

    def get_waveform(self, channel, mode='NORMal'):
        ''' mode can also be MAX or RAW '''
        if type(channel) == int: channel = 'CHAN' + str(channel)
        self.write(":WAVeform:SOURce " + channel)
        self.write(":WAVeform:FORMat BYTE")
        self.write(":WAVeform:MODE " + mode)
        self.query(":WAVeform:STARt?")
        self.query(":WAVeform:STOP?")
        buff = self.query_raw(":WAVeform:DATA?")
        return DS1054Z._clean_tmc_header(buff)

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
        return self.query("*IDN?")

    def stop(self):
        self.write(":STOP")

    def run(self):
        self.write(":RUN")

    def single(self):
        self.write(":SINGle")

    def tforce(self):
        self.write(":TFORce")

    @property
    def memory_depth(self):
        mdep = self.query(":ACQuire:MDEPth?")
        if mdep == "AUTO":
            srate = self.query(":ACQuire:SRATe?")
            scal = self.query(":TIMebase:MAIN:SCALe?")
            mdep = self.H_GRID * float(scal) * float(srate)
        return float(mdep)

    @property
    def display_data(self):
        # Ask for an oscilloscope display print screen
        self.write(":DISPlay:DATA?")
        logger.info("Receiving screen capture...")
        buff = self.read_raw(self.DISPLAY_DATA_BYTES)
        logger.info("read {} bytes in .display_data".format(len(buff)))
        if len(buff) != self.DISPLAY_DATA_BYTES:
            raise NameError("display_data: didn't receive the right number of bytes")
        return DS1054Z._clean_tmc_header(buff)

    @property
    def displayed_channels(self):
        ''' returns the list of channels currently displayed on the scope '''
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
