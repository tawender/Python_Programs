import logging
import visa
import numpy

_logger = logging.getLogger('inst')

class InstrumentError(Exception):
    pass

class Instrument(object):
    def __init__(self, id, name):
        self.name = name
        self.ins = visa.instrument(id)

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
        error_result = self.get_errors()        
        code = error_result[0]
        if code == 0:
            return
        num_errors = len(error_result)/2
        _logger.error("ERROR COUNT: %s"%(num_errors))
        for i in range(num_errors):
            _logger.error("error code %s, %s"%(error_result[i*2],error_result[(i*2)+1]))
        raise InstrumentError("VISA command failed %d Errors encountered."%(num_errors));

    def reset(self):
        self._write("*RST")

    def get_error(self):
        error_text = self.ins.ask("SYSTEM:ERROR?")
        error_list = error_text.split(",")
        code = int(error_list[0])
        message = error_list[1]
        return code,message

    def get_errors(self):
        errors = []
        while True:
            code, message = self.get_error()
            errors.append(code)
            errors.append(message)
            if code == 0:
                break
        return errors

class sourcemeter_2400(Instrument):
    def __init__(self, id, name):
        Instrument.__init__(self, id, name)
        self.source_type = 'VOLTAGE'
        self.compliance_type = 'CURRENT'
        self.meas_func = 'CURRENT'
        self.reset()

    def set_Isource(self):
        self.source_type = 'CURRENT'
        self.compliance_type = 'VOLTAGE'
        self._write("SOURCE:FUNCTION:MODE %s"%self.source_type)

    def set_Vsource(self):
        self.source_type = 'VOLTAGE'
        self.compliance_type = 'CURRENT'
        self._write("SOURCE:FUNCTION:MODE %s"%self.source_type)

    def set_source_mode(self,mode):
        #mode should be FIXED, SWEEP, or LIST
        self._write("SOURCE:%s:MODE %s"%(self.source_type,mode))

    def set_source_range(self,range):
        self._write("SOURCE:%s:RANGE %s"%(self.source_type,repr(range)))

    def set_source_level(self,level):
        self._write("SOURCE:%s:LEVEL %s"%(self.source_type,repr(level)))

    def set_measurement_function(self,meas):
        self.meas_func = meas
        self._write("SENS:FUNC '%s'"%meas)

    def set_compliance_level(self,level):
        self._write("SENS:%s:PROT %s"%(self.compliance_type,repr(level)))

    def set_output_terminals(self,outp):
        #set the meter's output terminals to the FRONT or the REAR
        self._write("ROUT:TERM %s"%outp)

    def output_on(self):
        self._write("OUTPUT ON")

    def output_off(self):
        self._write("OUTPUT OFF")

    def set_meas_speed(self,speed):
        """sets the speed of the measurement(integration time of the A/D converter)
           The speed is set in terms of number of power line cycles (NPLC)
           Higher speed means lower accuracy and more noise in measurement
        """
        self._write("SENSE:%s:NPLC %s"%(self.meas_func,repr(speed)))
            
    def format_readings(self,format_string):
        """specifies the elements that are read during in instrument query
           argument can contain any of the following items:
           VOLTAGE, CURRENT, RESISTANCE, TIME, STATUS
        """
        self._write("FORM:ELEM %s"%format_string)

    def local_mode(self):
        """place the meter in local mode
        """
        self.ins.write("SYSTEM:KEY 23")

    def take_measurement(self,num_readings):
        """initiates a measurement and returns the raw data from the buffer in the
           form of a numpy array or 'error' if incorrect number of readings returned 
        """
        self._write("DATA:CLEAR")                       #clear the data buffer
        self._write("DATA:FEED SENSE")                  #store raw readins in buffer
        self._write("DATA:POINTS %s"%num_readings)      #data points to store
        self._write("DATA:FEED:CONTROL NEXT")           #buffer control mode = NEXT
        self._write("TRIGGER:COUNT %s"%num_readings)
        self._write("INIT")
        raw_data = self._ask("DATA:DATA?")
        lst = raw_data.split(",")
        if len(lst) != num_readings:
            return 'error'
        a=numpy.zeros(num_readings,dtype=numpy.float32)
        index = 0
        for l in lst:
            a[index] = float(l)
            index+=1
        return a

class switch_system_7001(Instrument):
    def __init__(self, id, name):
        Instrument.__init__(self, id, name)
        self.reset()
        self.open_all()

    def close(self, slot, channel):
        self._write("CLOSE (@ %d!%d)"%(slot, channel))

    def open(self, slot, channel):
        self._write("OPEN (@ %d!%d)"%(slot, channel))
        
    def open_all(self):
        self._write("OPEN ALL")

class picoammeter_6485(Instrument):
    def __init__(self, id, name):
        Instrument.__init__(self, id, name)
        self.reset()

    def write(self,string):
        self._write(string)

    def read(self,string):
        self._ask(string)

    def config_zero(self, range):
        """enable the zero check feature and find the zero correct value to apply
           to readings
           range: 2nA,20nA,200nA,2uA,20uA,200uA,2mA,20mA
        """
        range_str1 = ['2n','20n','200n','2u','20u','200u','2m','20m']
        range_str2 = ['2nA','20nA','200nA','2uA','20uA','200uA','2mA','20mA']
        range_num = [2E-9,2E-8,2E-7,2E-6,2E-5,2E-4,2E-3,2E-2]
        range_sci = ['2E-9','2E-8','2E-7','2E-6','2E-5','2E-4','2E-3','2E-2']
        if range in range_str1:
            _range = range_sci[range_str1.index(range)]
        elif range in range_str2:
            _range = range_sci[range_str2.index(range)]
        elif range in range_num:
            _range = range_sci[range_num.index(range)]
        elif range in range_sci:
            _range = range
        else:
            raise InstrumentError("Invalid Range parameter given")

        self._write("*rst")
        self._write("SYST:ZCH ON")          #turn on zero check
        self._write("CURR:RANG %s"%_range)  #set the range to zero
        self._write("INIT")                 #trigger a reading
        self._write("SYST:ZCOR:ACQ")        #acquire zero correct value
        self._write("SYST:ZCH OFF")         #turn off zero check
        self._write("SYST:ZCOR ON")         #perform zero correction on subsequent readings

    def format_readings(self, format_string):
        """specifies the elements that are read during in instrument query
           argument can contain any of the following items:
           'READING', 'UNITS', 'TIME', 'STATUS' in a single string
           Ex. "READING,UNITS"
        """
        self._write(":FORMAT:ELEMENTS %s"%format_string)

    def take_measurement(self,num_readings):
        """initiates a measurement and returns the raw data from the buffer in the
           form of a numpy array or 'error' if incorrect number of readings returned 
        """
        self._write("DATA:CLEAR")                       #clear the data buffer
        self._write("DATA:FEED SENSE")                  #store raw readins in buffer
        self._write("TRIGGER:COUNT %s"%num_readings)    #set trigger to take readings
        self._write("DATA:POINTS %s"%num_readings)      #set buffer size
        self._write("DATA:FEED:CONTROL NEXT")           #buffer control mode = NEXT
        self.ins.write("INIT")                          #start storing readings

    def get_data_format(self):
        """will read the elements that the picoammeter will return when data is requested
           Returns: 'reading only' if the reading is the only element returned
                    num_elements - a list of the elements returned upon request
        """
        elem = self._ask("FORMAT:ELEMENTS?")
        elements = elem.split(',')
        return elements        

    def read_data(self, num_readings):
        """retrieve the readings stored in the picoammeter memory buffer
           returns - a numpy array of float32 values containing measurements
                     or 'error' on fail
        """
        restore_data_formatting = False
        elements = self._ask("FORMAT:ELEMENTS?")
        if elements != 'READ':
            restore_data_formatting = True
            self.format_readings("READ")
        raw_data = self._ask("DATA:DATA?")
 
        lst = raw_data.split(",")
        if len(lst) != num_readings:
            return 'error'
        a=numpy.zeros(num_readings,dtype=numpy.float32)
        for i in range(len(lst)):
            a[i] = float(lst[i])
        if restore_data_formatting == True:
            self.format_readings(elements)
        return a

    def local_mode(self):
        """place the meter in local mode
        """
        self.ins.write("SYSTEM:KEY 1")