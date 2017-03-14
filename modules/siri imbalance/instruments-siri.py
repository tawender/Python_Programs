import logging
import visa

_logger = logging.getLogger('inst')

class InstrumentError(Exception):
    pass

class VisaInstrument(object):
    def __init__(self, id, name):
        self.name = name
        self.ins = visa.instrument(id)

    def reset(self):
        self._write("*CLS")
        identity = self._ask("*IDN?")
        self._write("*RST")
        self._ask("*ESE?")
        self._ask("*ESR?")
        self._ask("*SRE?")

    def _ask(self, command):
        _logger.info("VISA-ASK %s: %s"%(self.name, command))
        result = self.ins.ask(command)
        _logger.info("VISA-RSP %s: %s"%(self.name, repr(result)))
        self._check_error_status()
        return result

    def _write(self, command):
        _logger.info("VISA-WR  %s: %s"%(self.name, command))
        self.ins.write(command)
        self._check_error_status()

    def _check_error_status(self):
        result = self.ins.ask("*ESR?")
        result_num = int(result)
        if result_num != 0:
            _logger.error("VISA-ESR %s: %s"%(self.name, result))
            self.get_errors()
            raise InstrumentError("VISA command failed (ESR=0x%x)"%(result_num));

    def get_error(self):
        error_text = self._ask("SYSTEM:ERROR?")
        (code_text, message) = error_text.split(',')
        code = int(code_text)
        return (code, message)

    def get_errors(self):
        errors = []
        while True:
            (code, message) = self.get_error()
            if code == 0:
                break
            errors.append((code, message))
        return errors



class Multimeter(VisaInstrument):

    def reset(self):
        VisaInstrument.reset(self)
        self._write("VOLT:DC:NPLC 0.2")

    def measure_voltage(self, volt_range):
        result = self._ask("MEASURE:VOLTAGE:DC? "+str(volt_range)+",0.0001")
        return float(result)

    def self_test(self):
        if self._ask("*TST?") not in ("+0", "0"):
            raise InstrumentError("Self test failed", self.get_errors());

class Multiplexer(VisaInstrument):

    def close(self, slot, channel):
        self._write("CLOSE (@ %d!%d)"%(slot, channel))

    def open_all(self):
        self._write("OPEN ALL")

class Oscilloscope(VisaInstrument):

    def reset(self):
        VisaInstrument.reset(self)
        self._write("autoset execute")
        self._write("horizontal:main:scale 20E-3")
        self._write("horizontal:trigger:position 10")
        self._write("horizontal:recordlength 10000")
        self._write("horizontal:delay:state OFF")

        self._write("CH1:yunit \"V\"")
        self._write("CH1:position 0")
        self._write("CH1:probe 10")
        self._write("CH1:scale 1")
        self._write("CH1:impedance FIFTY")
        self._write("CH1:bandwidth TWENTY")

        self._write("trigger:a:mode NORMAL")
        self._write("trigger:a:type EDGE")
        self._write("trigger:a:level 0.6")
        self._write("trigger:a:edge:source CH1")
        self._write("trigger:a:edge:slope RISE")

    def single_seq_trigger(self):
        self._ask("*OPC?")
        self._write("SELECT:CH1 ON")
        self._write("ACQUIRE:MODE SAMPLE")
        self._write("ACQUIRE:STOPAFTER SEQUENCE")
        self._write("ACQUIRE:STATE ON")

    def read_waveform_data(self):
        self._write("DATA:SOURCE CH1")
        self._write("DATA:ENCDG ASCII")
        self._write("DATA:WIDTH 1")
        self._ask("*OPC?")
        result = self._ask("WAVFRM?")
        return result

class PowerSupply(VisaInstrument):

    def reset(self):
        VisaInstrument.reset(self)
        self._write("ILIM 0.002")
        self._write("VLIM 1350")
        self._ask("ILIM?")
        self._ask("VLIM?")

    def set_voltage(self, voltage):
        self._write("VSET "+str(voltage))

    def get_voltage(self):
        result = self._ask("VOUT?")
        return float(result)

    def turn_voltage_on(self):
        self._write("HVON")

    def turn_voltage_off(self):
        self._write("HVOF")