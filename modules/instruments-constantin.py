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
        self._ask("SYSTEM:VERSION?")
        self._write("*RST")        
        self.get_errors()
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

    def measure_voltage(self):
        result = self._ask("MEASURE:VOLTAGE:DC? 5,0.00001")
        return float(result)

    def self_test(self):
        if self._ask("*TST?") not in ("+0", "0"):
            raise InstrumentError("Self test failed", self.get_errors());

class Multiplexer(VisaInstrument):

    def close(self, slot, channel):
        self._write("CLOSE (@ %d!%d)"%(slot, channel))
        
    def open_all(self):
        self._write("OPEN ALL")
