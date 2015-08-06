
import vxi11

class DS1054Z(vxi11.Instrument):

    ENCODING = 'utf-8'
    H_GRID = 12

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

