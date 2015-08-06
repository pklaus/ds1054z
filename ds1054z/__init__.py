
import logging

import vxi11

logger = logging.getLogger(__name__)

class DS1054Z(vxi11.Instrument):

    ENCODING = 'utf-8'
    H_GRID = 12
    TMC_HEADER_BYTES = 11
    TERMINATOR_BYTES = 3
    DISPLAY_DATA_BYTES = 1152068

    def query(self, *args, **kwargs):
        return self.ask(*args, **kwargs)

    def query_raw(self, cmd, *args, **kwargs):
        cmd = cmd.encode(self.ENCODING)
        return self.ask_raw(cmd, *args, **kwargs)

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
        buff = b""
        while len(buff) < self.DISPLAY_DATA_BYTES:
            tmp = self.read_raw(self.DISPLAY_DATA_BYTES)
            logger.info("read {} bytes in .display_data".format(len(tmp)))
            if len(tmp) == 0:
                break
            buff += tmp

        return buff[self.TMC_HEADER_BYTES:-self.TERMINATOR_BYTES]

