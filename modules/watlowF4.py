#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      tawender
#
# Created:     01/07/2013
# Copyright:   (c) tawender 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import time
import threading
import sys
sys.path.append(r'C:\python27\lib\site-packages')
import minimalmodbus


class WatlowF4(object):
    """basic commands sent to the Watlow F4 temperature controller via modbus protocol"""
    TEMPERATURE_MINIMUM = -70
    TEMPERATURE_MAXIMUM = 175
    PROCESS_VALUE_REG = 100
    SETPOINT_VALUE_REG = 300

    def __init__(self,portnum,controller_id=1,timeout=0.1,
                    baud=9600,echo_settings=False):
        self.ins = minimalmodbusipy.Instrument(portnum-1,controller_id)
        self.ins.serial.timeout = timeout
        self.ins.serial.baudrate = baud
        if echo_settings:
            print self.ins

    def read_temperature(self,num_decimals=1):
        return self.ins.read_register(self.PROCESS_VALUE_REG,num_decimals)

    def read_temp_setpoint(self,num_decimals=1):
        return self.ins.read_register(self.SETPOINT_VALUE_REG,num_decimals)

    def write_temp_setpoint(self,setpoint,num_decimals=1):
        self.ins.write_register(self.SETPOINT_VALUE_REG,setpoint,num_decimals)

    def close_port(self):
        self.ins.serial.close()

class WatlowF4_temp_window(WatlowF4):
    """Will change the setpoint of the temperature controller and set a flag when the
       chamber temperature has maintined its measured temperature within the min and max
       window for the specified amount of time
    """
    def __init__(self,portnum,controller_id=1,timeout=0.1,
                    baud=9600,echo_settings=False,debug=False):
        WatlowF4.__init__(self,portnum,controller_id=1,timeout=0.1,
                    baud=9600,echo_settings=False)
        self.debug = debug
        self._within_temperature_window = False
        self._dwelltime_endpoint_reached = False
        self.monitor_temperature_thread = threading.Thread(target=self.monitor)
        self.monitor_temperature_thread.daemon = True
        self.terminate_monitoring_thread = False

    def set_temperature_and_time(self,setpoint,
                                temp_window_min,temp_window_max,
                                dwelltime_mins,monitoring_interval_sec=5):
        """begin the process of setting the temperature setpoint, temperature window
           and time to remain within the temperature window before the flag
           dwelltime_endpoint_reached is set to True
        """
        if setpoint<self.TEMPERATURE_MINIMUM or setpoint>self.TEMPERATURE_MAXIMUM:
            raise RuntimeError("Attempted temperature setpoint outside allowed range")
        if temp_window_min > setpoint:
            raise RuntimeError("Window minimum temperature must be less than setpoint")
        if temp_window_max < setpoint:
            raise RuntimeError("Window maximum temperature must be greater than setpoint")

        self.monitoring_interval_sec = monitoring_interval_sec

        if self.monitor_temperature_thread.is_alive():
            if self.debug: print "Terminating previous thread..."
            self.terminate_monitoring_thread = True
            time.sleep(self.monitoring_interval_sec+1)
            if self.debug: print "monitoring thread is_alive():",self.monitor_temperature_thread.is_alive()

        self.monitor_temperature_thread = threading.Thread(target=self.monitor)
        self.monitor_temperature_thread.daemon = True
        self.temp_window_min = temp_window_min
        self.temp_window_max = temp_window_max
        self.dwelltime_sec = dwelltime_mins * 60.0

        self._within_temperature_window = False
        self._dwelltime_endpoint_reached = False

        self.write_temp_setpoint(setpoint)
        if self.debug: print "Setpoint changed to %.1fC"%(setpoint)

        self.monitor_temperature_thread.start()

    def monitor(self):
        """check the temperature and set the dwelltime_endpoint_reached flag when time reached
        """
        self._within_temperature_window = False
        self._dwelltime_endpoint_reached = False
        self.start_time = time.clock()

        while not self._dwelltime_endpoint_reached:
            measured_temp = self.read_temperature()

            if measured_temp>=self.temp_window_min and measured_temp<=self.temp_window_max:
                if self.debug:
                    print "Inside temperature window. Dwell time = %.1fsec (%.1fC)"%(
                                time.clock()-self.start_time,self.read_temperature())
                self._within_temperature_window = True
                if (time.clock()-self.start_time) >= self.dwelltime_sec:
                    if self.debug: print "Dwell time within temperature window achieved"
                    self._dwelltime_endpoint_reached = True
            else:
                self.start_time = time.clock()
                if self.debug:
                    print "Outside temperature window. Dwell time = %.1fsec (%.1fC)"%(
                                time.clock()-self.start_time,self.read_temperature())

            time.sleep(self.monitoring_interval_sec)

    def within_temperature_window(self):
        """return the flag status"""
        return self._within_temperature_window

    def dwelltime_endpoint_reached(self):
        """return the flag status"""
        return self._dwelltime_endpoint_reached
