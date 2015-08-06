
import vxi11

class DS1054Z(vxi11.Instrument):

    ENCODING = 'utf-8'

    def query(self, *args, **kwargs):
        return self.ask(*args, **kwargs)

    def query_raw(self, cmd, *args, **kwargs):
        cmd = cmd.encode(self.ENCODING)
        return self.ask_raw(cmd, *args, **kwargs)

