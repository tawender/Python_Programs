import logging
import visa
import numpy
import time
from struct import unpack_from

_logger = logging.getLogger('inst')

class InstrumentError(Exception):
    pass


class Instrument(object):
    def __init__(self, id, name, _timeout=None):
        self.name = name
        if _timeout is not None:
            self.ins = visa.instrument(id,timeout=_timeout)
        else:
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
            print ("error code %s, %s"%(error_result[i*2],error_result[(i*2)+1]))
        raise InstrumentError("VISA command failed %d Errors encountered."%(num_errors));

    def reset(self):
        print 'resetting'
        self._write("*RST")
        print 'done resetting'

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

class Advantest_R3465(Instrument):
    """spectrum analyzer commands"""
    def __init__(self,id,name):
        Instrument.__init__(self, id, name)
        self.reset()
        self.OBW_use_averaging = False
        self.num_data_points = 1001

    def _write(self, command):
        """this instrument does not seem to report errors like other instruments.
           The _write function is redefined to eliminate error checking since sending
           commands is not possible with standard error checking after command is sent.
        """
        _logger.info("VISA-WR  %s: %s"%(self.name, command))
        self.ins.write(command)

    def _ask(self, command):
        """this instrument does not seem to report errors like other instruments.
           The _ask function is redefined to eliminate error checking since sending
           commands is not possible with standard error checking after command is sent.
        """
        _logger.info("VISA-ASK %s: %s"%(self.name, command))
        result = self.ins.ask(command)
        _logger.info("VISA-RSP %s: %s"%(self.name, repr(result)))
        return result

    def get_id(self):
        return self._ask("*IDN?")

    def get_sweep_time(self):
        return float(self._ask("SW?"))

    def set_ref_level_dB(self,level):
        self._write("RL %sDB"%level)

    def get_ref_level(self):
        return float(self._ask("RL?"))

    def get_y_scale(self):
        return (self.get_ref_level() - self.get_dB_per_div()*10,
                                self.get_ref_level())

    def get_y_range(self):
        scale = self.get_y_scale()
        return scale[1]-scale[0]

    def get_dB_per_div(self):
        levels = [10,5,2,1,0.5]
        return levels[int(self._ask("DD?"))]

    def set_span_kHz(self,span):
        self._write("SP %sKZ"%span)

    def get_span(self):
        return float("SP?")

    def set_resolutionBW_kHz(self,r):
        self._write("RB %sKZ"%r)

    def set_sweep_time_milliseconds(self,t):
        self._write("SW %sMS"%t)

    def set_center_frequency_MHz(self,f):
        self._write("CF %sMZ"%f)

    def get_center_frequency(self):
        return float(self._ask("CF?"))

    def get_startf(self):
        return float(self._ask("FA?"))

    def get_stopf(self):
        return float(self._ask("FB?"))

    def set_marker_findpeak(self):
        self._write("MKPK")

    def get_marker_frequency(self):
        return float(self._ask("MK?"))

    def get_marker_power_level(self):
        return float(self._ask("ML?"))

    def set_occupied_bandwidth_pct(self,pct):
        if pct<10.0 or pct>99.8:
            raise RuntimeError("Occupied bandwidth percentage setpoint is out of range")
        self._write("OBW %s"%pct)

    def set_OBW_times_to_average(self,times):
        self._write("AVGOBW %s"%times)

    def get_OBW_num_averages(self):
        return float(self._ask("AVGOBW?"))

    def turn_OBW_averages_on(self):
        self._write("AVGOBW ON")
        self.OBW_use_averaging = True

    def turn_OBW_averages_off(self):
        self._write("AVGOBW OFF")
        self.OBW_use_averaging = False

    def measure_occupied_bandwidth(self):
        """will start a measurement and return a tuple of floats:
            (occupied_bandwidth_percent,occupied_bandwidth,center_frequency)
        """
        sleep_time=1.0
        self._write("OBW")
        if self.OBW_use_averaging:
            sleep_time += (self.get_OBW_num_averages() * (self.get_sweep_time()+.1))
        time.sleep(sleep_time)
        result = self._ask("OBW?").split(',')
        return (float(result[0]),float(result[1]),float(result[2]))

    def set_data_points_high(self):
        """set the number of data points on frequency axis to 1001
        """
        self._write("TPS")
        self.num_data_points = 1001

    def set_data_points_low(self):
        """set the number of data points on frequency axis to 501
        """
        self._write("TPL")
        self.num_data_points = 501

    def get_data_points(self):
        """returns a list of integers for data points representing screen data.
           The screen data is stored internally by integer values ranging from 1792 to 14592.
        """
        return list( unpack_from(">%dH"%self.num_data_points,
                                        self._ask("TBA?")))

    def get_data(self):
        """returns a list of data points converted into the correct units.
           The key for the dictionary item is the data units."""
        data_points = self.get_data_points()
        for i in range( len(data_points) ): data_points[i] -= 1792  #offset data for 0 min 12800 max

        y_scale = self.get_y_scale()
        y_range = self.get_y_range()

        for i in range(len(data_points)):   #convert screen point value to measured units
            data_points[i] = data_points[i] * y_range / 12800

        for i in range(len(data_points)):   #shift each point to match y-axis scale
            data_points[i] += y_scale[0]

        return data_points


    def get_units(self):
        units = ['dBm','dBmV','dBuV','dBuVemf','dBpW','V','W']
        return units[int(self._ask("UNIT?"))]

        """commands P.283 in manual"""

        """x dB down width P.278 in manual"""

class HP_8648_sig_gen(Instrument):
    """commands P.135 in manual"""
    def __init__(self, id, name):
        Instrument.__init__(self, id, name)
        self.ins.write('SYST:LANG "SCPI"')
        time.sleep(1)
        self.reset()

    def _write(self, command):
        """had to define local _write() to add a delay before checking error
           status for this instrument"""
        _logger.info("VISA-WR  %s: %s"%(self.name, command))
        self.ins.write(command)
        time.sleep(1)
        self._check_error_status()

    def get_error(self):
        """this instrument appears not to take full commands,
           must define local ger_error() to use the abbreviated forms"""
        error_text = self.ins.ask("SYST:ERR?")
        error_list = error_text.split(",")
        code = int(error_list[0])
        message = error_list[1]
        return code,message

    def set_output_frequency(self,f):
        if f<9000.0 or f>2E9:
            raise RuntimeError("CW frequency outside range of signal generator")
        self._write("FREQ:CW %s HZ"%f)

    def set_output_power_dBm(self,level):
        if level<-136 or level>22:
            raise RuntimeError("RF output power level out of range")
        self._write("POW:AMPL %s DBM"%level)

    def set_fm_source_internal(self):
        self._write("FM:SOUR INT")

    def set_fm_source_external(self):
        self._write("FM:SOUR EXT")

    def set_fm_ext_coup_ac(self):
        self._write("FM:EXT:COUP AC")

    def set_fm_ext_coup_dc(self):
        self._write("FM:EXT:COUP DC")

    def set_fm_deviation_Hz(self,dev):
        if dev<0.0 or dev>200000.0:
            raise RuntimeError("FM modulation exceeds deviation range")
        self._write("FM:DEV %s HZ"%dev)

    def fm_on(self):
        self._write("AM:STAT OFF;:PM:STAT OFF;:FM:STAT ON")

    def output_on(self):
        self._write("OUTP:STAT ON")

    def output_off(self):
        self._write("OUTP:STAT OFF")

class Agilent_sourcemeter_U2722A(Instrument):
    def __init__(self, id, name):
        Instrument.__init__(self, id, name)
        self.reset()

    def reset(self):
        self._write("*RST")
        self._write("SYST:LFREQUENCY F60HZ")
        self.set_NPLC_for_all(num_cycles=5)

    def set_NPLC_for_all(self,num_cycles=5):
        """set the number of power line cycles that an individual measurement
           is taken over. Sets all channels and both voltage and current meaurements.
        """
        for function in ['VOLT','CURR']:
            for channel in [1,2,3]:
                self.set_NPLC(function,num_cycles,channel)

    def set_NPLC(self,function,num_cycles,channel):
        """set the number of power line cycles that an individual measurement
           is taken over for a single channel and function (voltage or current measurement)
        """
        self._write("SENS:%s:NPLC %d, (@%d)"%(function,num_cycles,channel))

    def get_NPLC(self,function,channel):
        """returns the number of power line cycles that an individual measurement
           is taken over for a single channel and function (voltage or current measurement)
        """
        return float(self._ask("SENS:%s:NPLC? (@%d)"%(function,channel)))

    def _set_voltage_range(self,V_range,channel):
        if V_range in [2.0,'2','2.0','2v','2V','2.0v','2.0V',
                        -2.0,'-2','-2.0','-2v','-2V','-2.0v','-2.0V']:
            V_range = '2V'
        elif V_range in [20.0,'20.0','20.0v','20.0V','20','20v','20.0V',
                        -20.0,'-20.0','-20.0v','-20.0V','-20','-20v','-20.0V']:
            V_range = '20V'
        else:
            raise InstrumentError("Agilent U2722 error, invalid voltage range" + repr(V_range))

        self._write("SOURCE:VOLT:RANGE R%s, (@%d)"%(V_range,channel))

    def _set_current_range(self,I_range,channel):
        if I_range in [0.000001,'1uA','1.0uA',-0.000001,'-1uA','-1.0uA']:
            I_range = '1uA'
        elif I_range in [0.00001,'10uA','10.0uA',-0.00001,'-10uA','-10.0uA']:
            I_range = '10uA'
        elif I_range in [0.0001,'100uA','100.0uA',-0.0001,'-100uA','-100.0uA']:
            I_range = '100uA'
        elif I_range in [0.001,'1mA','1.0mA',-0.001,'-1mA','-1.0mA']:
            I_range = '1mA'
        elif I_range in [0.01,'10mA','10.0mA',-0.01,'-10mA','-10.0mA']:
            I_range = '10mA'
        elif I_range in [0.12,'120mA','120.0mA',-0.12,'-120mA','-120.0mA']:
            I_range = '120mA'
        else:
            raise InstrumentError("Agilent U2722 error, invalid current range" + repr(I_range))

        self._write("SOURCE:CURR:RANGE R%s, (@%d)"%(I_range,channel))

    def _set_current_limit(self,level,channel):
        self._write("SOURCE:CURRENT:LIMIT %s, (@%d)"%(level,channel))

    def _set_voltage_limit(self,level,channel):
        self._write("SOURCE:VOLTAGE:LIMIT %s, (@%d)"%(level,channel))

    def _set_current_level(self,level,channel):
        self._write("SOURCE:CURRENT %s, (@%d)"%(level,channel))

    def _set_voltage_level(self,level,channel):
        self._write("SOURCE:VOLTAGE %s, (@%d)"%(level,channel))


    def config_voltage_source(self,volt_rng=20,volt_lev=1.0,
                                curr_rng=.12,curr_lim=.001,channel=1):
        """configure the sourcemeter channel as a constant voltage source
        """
        if channel not in [1,2,3]:
            raise InstrumentError("Agilent U2722 error, invalid channel number")

        self._set_voltage_range(volt_rng,channel)
        self._set_current_range(curr_rng,channel)
        self._set_current_limit(curr_lim,channel)
        self._set_voltage_level(volt_lev,channel)

    def config_current_source(self,curr_rng=.12,curr_lev=.001,
                                volt_rng=20,volt_lim=1.0,channel=1):
        """configure the sourcemeter channel as a constant current source
        """
        if channel not in [1,2,3]:
            raise InstrumentError("Agilent U2722 error, invalid channel number")

        self._set_voltage_range(volt_rng,channel)
        self._set_current_range(curr_rng,channel)
        self._set_voltage_limit(volt_lim,channel)
        self._set_current_level(curr_lev,channel)

    def auto_select_voltage_range(self,level):
        """select the appropriate range from the desired voltage level
        """
        if (level <= 2.0) and (level >= -2.0):
            return '2V'
        elif (level <= 20.0) and (level >= -20.0):
            return '20V'
        else:
            raise InstrumentError("Agilent U2722 error, invalid voltage level for autorange" + repr(level))

    def auto_select_current_range(self,level):
        """select the appropriate range from the desired current level
        """
        if (level <= 0.000001) and (level >= -0.000001):
            return '1uA'
        elif (level <= 0.00001) and (level >= -0.00001):
            return '10uA'
        elif (level <= 0.0001) and (level >= -0.0001):
            return '100uA'
        elif (level <= 0.001) and (level >= -0.001):
            return '1mA'
        elif (level <= 0.01) and (level >= -0.01):
            return '10mA'
        elif (level <= 0.120) and (level >= -0.120):
            return '120mA'
        else:
            raise InstrumentError("Agilent U2722 error, invalid current level for autorange" + repr(level))

    def measure_current(self,channel):
        """measure the current at the specified channel
        """
        if channel not in [1,2,3]:
            raise InstrumentError("Agilent U2722 error, invalid channel number")
        return float(self._ask("MEAS:CURR? (@%d)"%channel))

    def measure_voltage(self,channel):
        """measure the voltage at the specified channel
        """
        if channel not in [1,2,3]:
            raise InstrumentError("Agilent U2722 error, invalid channel number")
        return float(self._ask("MEAS:VOLT? (@%d)"%channel))

    def _set_output_state(self,channel,state):
        """turns the output on or off
        """
        self._write("OUTPUT %s, (@%d)"%(state,channel))

    def output_on(self,channel):
        """turn the specified channel(s) output on
        """
        if type(channel) is list:
            for item in channel:
                if item not in [1,2,3]:
                    raise InstrumentError("Agilent U2722 error, invalid channel number")
                self._set_output_state(item,'on')
        elif channel not in [1,2,3]:
            raise InstrumentError("Agilent U2722 error, invalid channel number")
        else:
            self._set_output_state(channel,'on')

    def output_off(self,channel):
        """turn the specified channel(s) output off
        """
        if type(channel) is list:
            for item in channel:
                if item not in [1,2,3]:
                    raise InstrumentError("Agilent U2722 error, invalid channel number")
                self._set_output_state(item,'off')
        elif channel not in [1,2,3]:
            raise InstrumentError("Agilent U2722 error, invalid channel number")
        else:
            self._set_output_state(channel,'off')

    def get_output_state(self,channel):
        """read the current output state of the specified channel
        """
        if channel not in [1,2,3]:
            raise InstrumentError("Agilent U2722 error, invalid channel number")

        result = self._ask("OUTPUT? (@%d)"%(channel))
        if result == '1':
            return 1
        elif result == '0':
            return 0
        else:
            print "returned unexpected " + repr(result)


class sourcemeter_2400(Instrument):
    def __init__(self, id, name):
        Instrument.__init__(self, id, name)
        self.reset()

    def reset(self):
        self._write("*RST")
        self.source_type = 'VOLTAGE'
        self.limit_type = 'CURRENT'
        self.meas_func = 'CURRENT'

    def set_Isource(self):
        self.source_type = 'CURRENT'
        self.limit_type = 'VOLTAGE'
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

    def get_output_state(self):
        result = self._ask("OUTPUT?")
        if result == '1':
            return 1
        elif result == '0':
            return 0
        else:
            return 'unknown'

    def set_output_off_state(self,mode):
        """sets the output to the desired state
            mode: HIMPedance,NORMal,ZERO,or GAURd
        """
        self._write("OUTPUT:SMODE %s"%(mode))

    def set_meas_speed(self,speed):
        """sets the speed of the measurement(integration time of the A/D converter)
           The speed is set in terms of number of power line cycles (NPLC)
           Higher speed means lower accuracy and more noise in measurement
        """
        self._write("SENSE:%s:NPLC %s"%(self.meas_func,repr(speed)))

    def format_readings(self,format_string):
        """specifies the elements that are read during an instrument query
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


class PowerSupply_E3632A(Instrument):
    def __init__(self, id, name):
        Instrument.__init__(self, id, name)
        #self.reset()

    def set_voltage_limit(self,value):
        self._write("VOLTAGE %s"%value)
        self._write("DISP ON")

    def set_current_limit(self,value):
        self._write("CURRENT %s"%value)

    def read_voltage_limit(self):
        result = self._ask("VOLTAGE?")
        return float(result)

    def read_current_limit(self):
        result = self._ask("CURRENT?")
        return float(result)

    def measure_voltage(self):
        result = self._ask("MEASURE:VOLTAGE?")
        return float(result)

    def measure_current(self):
        result = self._ask("MEASURE:CURRENT?")
        return float(result)

    def output_on(self):
        self._write("OUTPUT ON")

    def output_off(self):
        self._write("OUTPUT OFF")

    def set_over_current_protect(self,value):
        self._write("CURR:PROT %s"%value)

    def set_over_voltage_protect(self,value):
        self._write("VOLT:PROTECT %s"%value)

    def enable_over_current_protect(self):
        self._write("CURR:PROT:STAT ON")

    def disable_over_current_protect(self):
        self._write("CURR:PROT:STAT OFF")

    def enable_over_voltage_protect(self):
        self._write("VOLT:PROT:STAT ON")

    def disable_over_voltage_protect(self):
        self._write("VOLT:PROT:STAT OFF")

    def beep(self):
        self._write("SYST:BEEP")


class DMM_34401A(Instrument):
    def __init__(self, id, name, timeout=10.0):
        Instrument.__init__(self, id, name, timeout)
        self.reset()

    def measure_voltage(self,volt_range=None,resolution=None):
        """issue a voltage measurement command and returns the result
        volt_range: the expected measured value, the multimeter then selects
                    the correct measurement range
        resolution: the resolution to use Ex. 0.0001

        Returns: the measurement as a float
        """
        if (resolution is None) and (volt_range is None):
            result = self._ask("MEASURE:VOLTAGE:DC?")
        elif resolution is None:
            result = self._ask("MEASURE:VOLTAGE:DC? " + str(volt_range) )
        else:
            result = self._ask("MEASURE:VOLTAGE:DC? " + str(volt_range) + "," + str(resolution))
        return float(result)

    def measure_resistance(self,res_range=None,resolution=None):
        """issue a resistance measurement command and returns the result
        res_range: the expected measured value, the multimeter then selects
                    the correct measurement range
        resolution: the resolution to use Ex. 0.0001

        Returns: the measurement as a float
        """
        if (resolution is None) and (res_range is None):
            result = self._ask("MEASURE:RESISTANCE?")
        elif resolution is None:
            result = self._ask("MEASURE:RESISTANCE? " + str(res_range) )
        else:
            result = self._ask("MEASURE:RESISTANCE? " + str(res_range) + ", " + str(resolution))
        return float(result)

    def set_integration_time(self,function,nplc):
        """sets the integration time (measurement speed)
            function: the measurement function Ex. VOLT:DC
            nplc: number of power line cycles (0.02,0.2,1,10,100)
        """
        self._write("SENS:%s:NPLC %s"%(function,nplc))

    def set_measurement_function(self,function,range=None,resolution=None):
        """sets the measurement function of the meter
            function: VOLTage:DC,VOLTage:DC:RATio,VOLTage:AC,
                        CURRent:DC,CURRent:AC,RESistance,FRESistance,
                        FREQency,PERiod,CONTinuity,DIODe
            range: measurement range or scale setting
            resolution: measurement resolution
        """
        if (range is None) and (resolution is None):
            self._write("CONF:%s"%(function))
        elif (resolution is None):
            self._write("CONF:%s %s"%(function,range))
        else:
            self._write("CONF:%s %s, %s'"%(function,range,resolution))

    def set_trigger_source(self,source):
        """sets the trigger source to take a measurement
            source: BUS,IMMediate,or EXTernal
        """
        self._write("TRIGGER:SOURCE " + source)

    def set_trigger_delay(self,delay):
        """time between the trigger and the measurement, also the time between
           measurements if more than one are to be taken after trigger
           delay: 0 to 3600 seconds
        """
        self._write("TRIG:DELAY " + str(delay) )

    def set_number_of_samples(self,num):
        self._write("SAMPLE:COUNT " + str(num) )

    def initiate_triggering(self):
        self._write("INIT")

    def initiate_triggering_and_return_result(self):
        readings = self._ask("READ?")
        print readings
        return readings

    def fetch_buffered_results(self):
        readings = self._ask("FETCH?")
        return readings

    def self_test(self):
        if self._ask("*TST?") not in ("+0", "0"):
            raise InstrumentError("Self test failed", self.get_errors());


class DMM_HP3478A(object):
    def __init__(self, id, name):
        self.name = name
        self._instr = visa.instrument(id)
        self.home()

    def _write(self,command):
        _logger.info("VISA-WR  %s: %s"%(self.name, command))
        self._instr.write(command)

    def _ask(self,command):
        _logger.info("VISA-ASK  %s: %s"%(self.name, command))
        return self._instr.ask(command)

    def home(self):
        """sends the 'home' command to the instrument (reset)
        """
        self._write("H0")

    def set30mRng(self):
        """sets the 30mV DC range for voltage measurement
        """
        self._write("R-2")

    def set300mRng(self):
        """sets the 300m AC or DC range for voltage or current measurements
        """
        self._write("R-1")

    def set3Rng(self):
        """sets the 3.0V AC or DC range for voltage or current measurements
        """
        self._write("R0")

    def set3kRng(self):
        """sets the 3Kohm range for resistance measurements
        """
        self._write("R3")

    def set30Rng(self):
        """sets the 30V AC or DC range for voltage or current measurements
        or the 30ohm range for resistance measurements
        """
        self._write("R1")

    def set3MegRng(self):
        """sets the 3Meg ohm range for resistance measurements
        """
        self._write("R6")

    def func2WireOhms(self):
        """sets the meter function to 2-wire resistance measurement
        """
        self._write("F3")

    def func4WireOhms(self):
        """sets the meter function to 4-wire resistance measurement
        """
        self._write("F4")

    def funcDCvolts(self):
        """sets the meter function to measure DC voltage
        """
        self._instr._write("F1")

    def meas2WireOhms(self):
        """sets the meter function to 2-wire resistance measurement
        """
        self._instr._write("H3")

    def meas4WireOhms(self):
        """sets the meter function to 4-wire resistance measurement
        """
        self._instr._write("H4")

    def write_text(self,text):
        """writes the text to the meter front panel
        """
        self._instr._write("D2%s"%text)

    def trig_and_read(self):
        """sends a single trigger to the meter to take a measurement
        and returns the measured value
        """
        reading = self._ask("T3")
        return float(reading)