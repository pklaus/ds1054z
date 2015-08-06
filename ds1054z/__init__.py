
import logging
import re

import vxi11

logger = logging.getLogger(__name__)

class DS1054Z(vxi11.Instrument):

    IDN_PATTERN = r'^RIGOL TECHNOLOGIES,DS1\d\d\dZ,'
    ENCODING = 'utf-8'
    H_GRID = 12
    TMC_HEADER_BYTES = 11
    TERMINATOR_BYTES = 3
    DISPLAY_DATA_BYTES = 1152068

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        idn = self.idn
        assert re.match(self.IDN_PATTERN, idn)
        idn = idn.split(',')
        self.vendor = idn[0]
        self.product = idn[1]
        self.serial = idn[2]
        self.firmware = idn[3]

    def write_raw(self, cmd, *args, **kwargs):
        logger.debug('sending: ' + repr(cmd))
        super().write_raw(cmd, *args, **kwargs)

    def read_raw(self, *args, **kwargs):
        data = super().read_raw(*args, **kwargs)
        logger.debug('received: ' + repr(data))
        return data

    def query(self, *args, **kwargs):
        return self.ask(*args, **kwargs)

    def query_raw(self, cmd, *args, **kwargs):
        cmd = cmd.encode(self.ENCODING)
        return self.ask_raw(cmd, *args, **kwargs)

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
        return buff[self.TMC_HEADER_BYTES:-self.TERMINATOR_BYTES]

    @property
    def displayed_channels(self):
        ''' returns the list of channels currently displayed on the scope '''
        channel_list = []
        for channel in ["CHAN1", "CHAN2", "CHAN3", "CHAN4", "MATH"]:
            if self.query(channel + ":DISPlay?") == '1':
                channel_list.append(channel)
        return channel_list
