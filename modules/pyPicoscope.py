#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      tawender
#
# Created:     01/11/2012
# Copyright:   (c) tawender 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import time
import math
import numpy
import ctypes
psdll = ctypes.windll.ps4000
from collections import OrderedDict
import datetime
import threading
from Queue import Queue

import sys
sys.path.append("picoscopeLib")
import PicoStatusConstants as psConstants
import PicoTypes as psTypes




short = ctypes.c_short
ref = ctypes.byref
void_ptr = ctypes.c_void_p
no_oversample = ctypes.c_short(1)
BlockReadyCallbackType = ctypes.CFUNCTYPE(short,ctypes.c_ulong,void_ptr,short)

active = 1
inactive = 0
dc_coupling = 1
ac_coupling = 0
disable_trigger = 0
enable_trigger = 1
u = 10**-6

max_ADC = 32764
maxV = [.01,.02,.05,.1,.2,.5,1.0,2.0,5.0,10.0,20.0,50.0,100.0]
input_channels = ['ChannelA','ChannelB']


def calculate_seconds_passed(start_time):
    seconds_passed = 0
    if (start_time != None):
        now = datetime.datetime.now()
        seconds_passed = (now - start_time).seconds
    return seconds_passed

class TimeoutError(Exception):
    pass

class PS(object):
    """main picoscope object that contains common functions which can be inherited by
       other more specific picoscope objects
    """
    def CHK(self,code):
        """this function checks the return value of all dll function calls
        """
        if code == 0:
            return 0
        elif code in psConstants.constants.values():
            print "ERROR. Function returned value of %d - %s"%(code,
                            psConstants.constants.keys()[psConstants.constants.values().index(code)])
            return code

    def find_timebase(self,sample_interval):
        """will find the closest allowed sample interval that can be used by the picoscope. If the desired
           sample interval is not possible the next shortest one will be used.
           Returns a tuple containing: (interval_code,actual_sample_interval)
        """
        if sample_interval < 64 * (10**-9): #<64nsec
            n = int( math.log(sample_interval * 250000000) / math.log(2) )
            actual_interval = 2**n / 250000000.0
        else:
            n = int( 2+(31250000*sample_interval) )
            actual_interval = (n-2) / 31250000.0
        return (n,actual_interval)

    def convert_ADC_reading(self,reading,_range=None,conversion_factor=None):
        """converts a single ADC reading to a voltage.
           If converting a single reading specify _range, if converting an array
           speed up execution by finding the conversion factor first and sending it instead.
        """
        if (_range is None) and (conversion_factor is None):
            raise RuntimeError("Must specify range or conversion factor to convert ADC reading")

        #conversion factor was sent
        if (conversion_factor is not None):
            return reading * conversion_factor

        #range was sent
        elif _range in psTypes.Range.keys():
            index = psTypes.Range[_range]
            return reading * maxV[index] / max_ADC

        else:
            raise RuntimeError("Error converting ADC readings. Range not found")

    def convert_ADC_readings(self,buffer_dict):
        """Takes a dictionary where each item contains an array of ADC readings.
           Returns an ordered dictionary of numpy arrays keyed by channel name.
        """
        #container for the conversions
        converted_dict = OrderedDict()

        #convert each buffer in the dictionary and add to the return dictionary
        for key in buffer_dict.keys():

            readings = buffer_dict[key]
            _range = self.channel_ranges[key]
            conv_fac = maxV[ psTypes.Range[_range] ] / max_ADC

            #create numpy array and add to the dictionary
            converted_readings = numpy.zeros(len(readings),dtype=numpy.float64)
            for i in range(len(readings)):
                converted_readings[i] = self.convert_ADC_reading(readings[i],conversion_factor=conv_fac)
            converted_dict[key] = converted_readings

        return converted_dict

    def voltage_to_ADC_count(self,voltage,_range):
        """converts a voltage to ADC counts given the range of the ADC
        """
        if _range in psTypes.Range.keys():
            index = psTypes.Range[_range]
            return int(voltage * max_ADC / maxV[index])
        else:
            raise RuntimeError("Range not found: %s"%_range)

    def block_ready_callback(self,_handle,void_ptr,status_code):
        """callback function sent to the RunBlock function
            PARAMETERS:
                _handle:        the handle of the device returning the samples
                status_code:    indicates whether an error occurred during collection of the data
                void_ptr:       passes from ps4000RunBlock
        """
        if self.debug:
            print "type of _handle: ",type(_handle)
            print "value of _handle: ",_handle
            print "type of status_code: ",type(status_code)
            print "value of status_code: ",status_code
            print "type of void_ptr: ",type(void_ptr)
            print "value of void_ptr: ",void_ptr
        if status_code == 0:
            self.data_ready = True
            return 0
        else:
            ret = self.CHK(status_code)
            print ("Error found in block_ready_callback()")
            return 1


class picoscope(PS):
    """the main picoscope hardware instance
    """
    def __init__(self):
        self.handle = short(0)
        string_buf_size = 25
        string_buf = ctypes.create_string_buffer(string_buf_size)
        reqd_size = short(0)

        ret = self.CHK(psdll.ps4000OpenUnit(ctypes.byref(self.handle)))
        if ret == 0:
            print "Picoscope Opened"
        else:
            raise RuntimeError("Error Opening Picoscope... Exiting")

        print "Retrieving device info..."
        for i in range(7):
            key = psConstants.unit_info.keys()[psConstants.unit_info.values().index(i)]
            ret = self.CHK(psdll.ps4000GetUnitInfo(self.handle,ref(string_buf),short(string_buf_size),
                                        ref(reqd_size),i))
            print "  %-30s  "%(key),
            if ret == 0:
                print "%s"%(string_buf.value)
                if key is 'PICO_VARIANT_INFO':
                    self.model = int(string_buf.value)
            else:
                raise RuntimeError("Error retrieving device info")
        print

    def get_handle(self):
        return self.handle

    def model_num(self):
        """returns the model number of the picoscope
        """
        return self.model

    def close(self):
        """close the picoscope device
        """
        ret = self.CHK(psdll.ps4000CloseUnit(self.handle))


class picoscope_measurement_thread(threading.Thread,PS):
    """A thread for taking an analog measurement with the picoscope - creates an  instance
       of the picoscope_measurement class defined below
    """
    def __init__(self,handle,queue,timeout_sec=10.0,debug=False):
        threading.Thread.__init__(self)
        self.daemon = True
        self.handle = handle
        self.result_queue = queue
        self.timeout_sec = timeout_sec
        self.m = picoscope_measurement(self.handle,self.timeout_sec,debug=debug)

    def set_channel(self,ch,enabled=False,dc_coupling=True,_range='Range_10V'):
        """set the channel properties
        """
        self.m.set_channel(ch,enabled,dc_coupling,_range)

    def set_triggering(self,triggered_measurement=False,trig_source='ChannelA',trigger_voltage=1.0,
                        trig_slope='Rising',trigger_delay=0,trig_timeout=0):
        """Set the triggering properties for the measurement.
           Channel setup for the trigger should be set up prior to using this
           function so that the channel range is known (needed to convert trigger
           voltage to ADC counts in this function)
        """
        self.m.set_triggering(triggered_measurement,trig_source,trigger_voltage,
                        trig_slope,trigger_delay,trig_timeout)

    def set_sampling(self,seconds_to_acquire=1.0,desired_sample_interval=.001,
                        seconds_pretrigger=0.0):
        """set up the buffers and the timebase for the acquisition
        """
        self.m.set_sampling(seconds_to_acquire,desired_sample_interval,seconds_pretrigger)

    def run(self):
        """this function will start the measurement and, when completed put the result onto
           a result queue for retrieval by the calling function
        """
        try:
            result = self.m.run_measurement()
        except TimeoutError:
            self.result_queue.put(None)
            return

        self.result_queue.put(result)


class picoscope_measurement(PS):
    """used for setting up and acquiring analog measurements with the picoscope
    """
    def __init__(self,handle,timeout_sec=10.0,debug=False):
        self.debug = debug
        self.handle = handle
        self.timeout_sec = timeout_sec
        self.data_ready = False
        self.chA_enabled = False
        self.chB_enabled = False
        self.chA_dc_coupling = True
        self.chB_dc_coupling = True

        self.channel_ranges = OrderedDict()
        self.channel_ranges['ChannelA'] = 'Range_10V'
        self.channel_ranges['ChannelB'] = 'Range_10V'

        self.channels_enabled = OrderedDict()
        self.channels_enabled['ChannelA'] = False
        self.channels_enabled['ChannelB'] = False

        #initialize both channels to 'disabled'
        self.set_channel('ChannelA')
        self.set_channel('ChannelB')

    def check_data_ready(self):
        return self.data_ready

    def get_num_enabled_channels(self):
        num_enabled = 0
        for key in self.channels_enabled.keys():
            if self.channels_enabled[key] is True:
                num_enabled += 1
        return num_enabled

    def set_channel(self,ch,enabled=False,dc_coupling=True,_range='Range_10V'):
        """set the channel properties
        """
        #update the channel range variable
        self.channel_ranges[ch] = _range

        #keep track of the enabled channels for buffer allocation
        if enabled is True:
            if ch in self.channels_enabled.keys():
                self.channels_enabled[ch] = True

        #configure channel settings
        ret = self.CHK(psdll.ps4000SetChannel(self.handle,psTypes.Channel[ch],
                                    enabled,dc_coupling,psTypes.Range[_range]))
        if ret == 0:
            if self.debug: print "%s has been set"%ch
        else:
            raise RuntimeError("Error setting picoscope channel")

    def set_triggering(self,triggered_measurement=False,trig_source='ChannelA',trigger_voltage=1.0,
                        trig_slope='Rising',trigger_delay=0,trig_timeout=0):
        """Set the triggering properties for the measurement.
           Channel setup for the trigger should be set up prior to using this
           function so that the channel range is known (needed to convert trigger
           voltage to ADC counts in this function)
        """
        if triggered_measurement:
            trig_ADC = self.voltage_to_ADC_count(trigger_voltage,self.channel_ranges[trig_source])
        else:
            trig_ADC = 0
        ret = self.CHK(psdll.ps4000SetSimpleTrigger(self.handle,triggered_measurement,
                                                psTypes.Channel[trig_source],
                                                short(trig_ADC),
                                                psTypes.ThresholdDirection[trig_slope],
                                                ctypes.c_ulong(trigger_delay),
                                                ctypes.c_short(trig_timeout)))
        if ret == 0:
            if self.debug:
                if triggered_measurement:print "Trigger has been set to %.3fV (%d ADC counts)" \
                                                        %(trigger_voltage,trig_ADC)
                else:print "Triggering has been disabled (untriggered measurement)"
        else:
            raise RuntimeError("Error setting trigger")

    def set_sampling(self,seconds_to_acquire=1.0,desired_sample_interval=.001,
                        seconds_pretrigger=0.0):
        """set up the buffers and the timebase for the acquisition
        """
        (self.timebase_code,actual_sample_interval) = self.find_timebase(desired_sample_interval)
        #round up to the next highest integer
        self.channel_buffer_size = int(math.ceil(seconds_to_acquire / actual_sample_interval))
        self.num_pretrigger_samples = int(math.ceil(seconds_pretrigger / actual_sample_interval))
        if self.debug:
            print " desired sample interval of %.3fusec"%(desired_sample_interval/u)
            print " actual sample interval of %.3fusec using code %d"%(actual_sample_interval/u,self.timebase_code)
            print " acquiring %.3fusec of data at %.3fusec sample interval"%(
                                    seconds_to_acquire/u,actual_sample_interval/u)
            print " channel buffer size of: ",self.channel_buffer_size
            print " number of pretrigger samples: ",self.num_pretrigger_samples

        self.buffer_dict = OrderedDict()
        for channel in self.channels_enabled.keys():
            if self.channels_enabled[channel] is True:
                #create and set the data buffer
                self.buffer_dict[channel] = (ctypes.c_short*self.channel_buffer_size)()
                ret = self.CHK(psdll.ps4000SetDataBuffer(self.handle,psTypes.Channel[channel],
                                                ref(self.buffer_dict[channel]),
                                                ctypes.c_long(self.channel_buffer_size)))
                if ret == 0:
                    if self.debug: print "%s data buffer has been set"%channel
                else:
                    raise RuntimeError("Error setting %s data buffer"%channel)

    def stop_capture(self):
        ret = self.CHK(psdll.ps4000Stop(self.handle))
        if ret == 0:
            if self.debug: print "Capture Stopped"
        else:
            raise RuntimeError("Error stopping")

    def run_measurement(self):
        """Runs the measurement and returns a dictionary of numpy arrays keyed by the channel name.
        """
        #ps4000RunBlock
        num_pretrigger_samples = ctypes.c_long(self.num_pretrigger_samples)
        num_posttrigger_samples = ctypes.c_long(self.channel_buffer_size - self.num_pretrigger_samples + 1)

        if self.debug:
            print " number of pretrigger samples to collect: ",num_pretrigger_samples.value
            print " number of posttrigger samples to collect: ",num_posttrigger_samples.value

        callback = BlockReadyCallbackType(self.block_ready_callback)
        if self.debug: print " callback created"
        pParameter = void_ptr(None)
        measurement_begin_time = datetime.datetime.now()
        ret = self.CHK(psdll.ps4000RunBlock(self.handle,
                                        num_pretrigger_samples,
                                        num_posttrigger_samples,
                                        ctypes.c_ulong(self.timebase_code),
                                        no_oversample,
                                        None,
                                        0,
                                        callback,
                                        pParameter))
        if self.debug: print " waiting for measurement to complete"

        #check for timeout and if it happened raise error
        time_passed = 0
        while ( (not self.data_ready) and (time_passed < self.timeout_sec) ):
            time_passed = calculate_seconds_passed(measurement_begin_time)
            time.sleep(0.01)

        if time_passed >= self.timeout_sec:
            self.stop_capture()
            raise TimeoutError("Timeout waiting for Picoscope measurement result")


        if ret == 0:
            if self.debug: print "RunBlock completed"
        else:
            self.stop_capture()
            raise RuntimeError("Error running data capture block")


        #stop the data capture
        self.stop_capture()


        #get the values from the oscilloscope
        def print_buffer(buf_dict):
            for key in buf_dict.keys():
                buf = buf_dict[key]
                print "\n%s buffer (%d readings):"%(key,len(buf))
                for i in range(len(buf)):
                    print "  %2d: "%(i), buf[i]
                if type(buf[1]) is numpy.float64:
                    print "  average of values: %.3f"%numpy.average(buf)

        if self.debug:
            print "buffer before getting values:"
            print_buffer(self.buffer_dict)

        num_samples = ctypes.c_ulong( self.channel_buffer_size * self.get_num_enabled_channels() )
        overflow_flags = short(0)
        ret = self.CHK(psdll.ps4000GetValues(self.handle,0,ref(num_samples),
                                        ctypes.c_ulong(1),
                                        short(0),
                                        ctypes.c_ushort(0),
                                        ref(overflow_flags)))
        if ret == 0:
            if self.debug: print "GetValues function completed successfully"
        else:
            raise RuntimeError("Error getting values")

        #make sure expected number of samples returned


        #check overflow flags (bit 0 for chA, bit 1 for chB)



        if self.debug:
            print "buffer after getting values:"
            print_buffer(self.buffer_dict)

        converted_buf = self.convert_ADC_readings(self.buffer_dict)

        if self.debug:
            print "converted readings:"
            print_buffer(converted_buf)

        return converted_buf





def main():
    def print_averages(d):
        for ch in result:
            print "average of %s: %.3fV"%(ch,numpy.average(result[ch]))

    #set up the picoscope
    ps = picoscope()
    picoscope_handle = ps.get_handle()

    #set up the unthreaded measurement
    print "setting up unthreaded measurement"
    measurement = picoscope_measurement(picoscope_handle,timeout_sec=5.0)
    print "picoscope measurement created..."
    measurement.set_channel('ChannelA',enabled=True,dc_coupling=True,_range='Range_5V')
    print "channel A set..."
    measurement.set_channel('ChannelB',enabled=True,dc_coupling=True,_range='Range_10V')
    print "channel B set..."
    measurement.set_triggering(triggered_measurement=False,trig_source='ChannelB',
                        trigger_voltage=1.0,trig_slope='Rising',trigger_delay=0,trig_timeout=0)
    print "triggering set..."
    measurement.set_sampling(seconds_to_acquire=0.0002,desired_sample_interval=.000005,
                        seconds_pretrigger=0.00006)
    print "sampling set..."
    result = measurement.run_measurement()
    print "measurement completed."
    print_averages(result)
    print " done with standard measurement\n"
    return

    #set up the threaded measurement
    print "setting up measurement using threading"
    q = Queue()
    measurement = picoscope_measurement_thread(picoscope_handle,q,timeout_sec=5.0)
    print "picoscope measurement created..."
    measurement.set_channel('ChannelA',enabled=True,dc_coupling=True,_range='Range_5V')
    print "channel A set..."
    measurement.set_channel('ChannelB',enabled=True,dc_coupling=True,_range='Range_10V')
    print "channel B set..."
    measurement.set_triggering(triggered_measurement=False,trig_source='ChannelB',
                        trigger_voltage=1.0,trig_slope='Rising',trigger_delay=0,trig_timeout=0)
    print "triggering set..."
    measurement.set_sampling(seconds_to_acquire=0.0002,desired_sample_interval=.000005,
                        seconds_pretrigger=0.00006)
    measurement.start()
    while q.empty():
        print "waiting for measurement..."
        time.sleep(1)
    measurement_result = q.get()

    if measurement_result is None:
        raise TimeoutError("Timeout getting measurement result from Picoscope")

    print_averages(measurement_result)

    print "done!"
    return

if __name__ == '__main__':
    main()
