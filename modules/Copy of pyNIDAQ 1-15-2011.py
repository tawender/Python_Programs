import ctypes
import numpy
import threading
import time
from Queue import Queue

nidaq = ctypes.windll.nicaiu 
##############################
# Setup some typedefs,constants,variables
# to correspond with values in
# C:\Program Files\National Instruments\NI-DAQ\DAQmx ANSI C Dev\include\NIDAQmx.h
# the typedefs
int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
void_ptr = ctypes.c_void_p
TaskHandle = uInt32
EveryNSamplesEventCallbackType = ctypes.CFUNCTYPE(int32,TaskHandle,int32,uInt32,void_ptr)
# the constants
DAQmx_Val_Cfg_Default = int32(-1)
DAQmx_Val_Volts = 10348

DAQmx_Val_NRSE = 10078
DAQmx_Val_RSE = 10083
DAQmx_Val_Diff = 10106
DAQmx_Val_Rising = 10280
DAQmx_Val_Falling = 10171
DAQmx_Val_FiniteSamps = 10178
DAQmx_Val_WaitInfinitely = -1.0
DAQmx_Val_ContSamps = 10123
DAQmx_Val_Seconds = 10364
DAQmx_Val_Ticks = 10304
DAQmx_Val_GroupByChannel = 0
DAQmx_Val_GroupByScanNumber = 1
DAQmx_Val_Acquired_Into_Buffer = 1
DAQmx_Val_Transferred_From_Buffer = 2
Internal_Clock = None
No_Custom_Scale = None
Onboard_Clock = None
No_Autostart = 0
##############################
class NIDAQ(object):
    def _CHK(self,err):
        """a simple error checking routine"""
        if err < 0:
            buf_size = 100
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(err,ctypes.byref(buf),buf_size)
            raise RuntimeError("nidaq call failed with error %d: %s"%(err,repr(buf.value)))
        if err > 0:
            buf_size = 100
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(err,ctypes.byref(buf),buf_size)
            raise RuntimeError("nidaq generated warning %d: %s"%(err,repr(buf.value)))

class AI_Voltage_Channel(NIDAQ):
    def __init__(self):
        self.task_handle = TaskHandle(0)
        self.min_volts = -10.0
        self.max_volts = 5.0
        self.sample_rate = 10000.0
        self.num_samples = 5000
        self.timeout = 10.0
        self.Create_Task()
    def __del__(self):
        nidaq.DAQmxClearTask(self.task_handle)

    def Create_Task(self):
        self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.task_handle)))

    def Config_Finite_Voltage_Measurement(self,device,AIchan,min_volts,max_volts,sample_rate,num_samples):
        """configure an analog input channel to measure voltage
           Parameters:  device - DAQ card device (string)
                        AIchan - Analog input channel for measurement (string)
                        min_volts - minimum voltage level expected (float)
                        max_volts - maximum voltage level expected (float)
                        sample_rate - number of samples to be taken per second (float)
                        num_samples - maximum number of samples to be taken (integer)
            Returns:    nothing
        """
        self.min_volts = min_volts
        self.max_volts = max_volts
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.channel = device + "/" + AIchan
        self._CHK(nidaq.DAQmxCreateAIVoltageChan(self.task_handle,self.channel,"",
                                           DAQmx_Val_NRSE,
                                           float64(self.min_volts),float64(self.max_volts),
                                           DAQmx_Val_Volts,None))
        self._CHK(nidaq.DAQmxCfgSampClkTiming(self.task_handle,Internal_Clock,float64(self.sample_rate),
                                        DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,
                                        uInt64(self.num_samples)))

    def Take_Voltage_Measurement(self,timeout=10.0):
        """take a voltage measurement from a defined voltage channel
           Parameters:  num_samples - maximum number of samples to be taken (integer)
                        timeout - maximum time in seconds before voltage reading fails (float)
                        outfile - a .csv file object to write the results to
           Returns:     data - a numpy array of floats containing the voltage readings or
                               'error' upon incorrect number of samples taken
        """
        self.timeout = timeout
        self._CHK(nidaq.DAQmxStartTask(self.task_handle))
        samples_read = int32()
        data = numpy.zeros((self.num_samples,),dtype=numpy.float64)
        self._CHK(nidaq.DAQmxReadAnalogF64(self.task_handle,uInt32(self.num_samples),float64(self.timeout),
                                     DAQmx_Val_GroupByChannel,data.ctypes.data,
                                     self.num_samples,ctypes.byref(samples_read),None))
        if self.task_handle.value != 0:
            nidaq.DAQmxStopTask(self.task_handle)
        if samples_read.value != self.num_samples:
            return 'error'
        else:
            return data

class Analog_Input_Thread(threading.Thread,NIDAQ):
    """this class uses threading to set up an analog voltage measurement and return control
       to the calling program while the measurement is taking place
    """
    def __init__(self,device,channel,q,min=-10.0,max=10.0,sample_rate=1000.0,num_samples=1000):
        threading.Thread.__init__(self)
        self.daemon = True
        self.task_handle = TaskHandle(0)
        self.device = device
        self.channel = channel
        self.min_volts = min
        self.max_volts = max
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.timeout = int(self.num_samples / self.sample_rate ) + 5
        self.result_queue = q
        self.Create_Task()
        self.Config_Finite_Voltage_Measurement(self.device,self.channel,
                                               self.min_volts,self.max_volts,
                                               self.sample_rate,self.num_samples)

    def run(self):
        """this function will start the voltage measurement and, when completed put the result onto
           a result queue for retrieval by the calling function"""
        result = self.Take_Voltage_Measurement()
        self.result_queue.put(result)

    def Create_Task(self):
        self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.task_handle)))

    def Config_Finite_Voltage_Measurement(self,device,AIchan,min_volts,max_volts,sample_rate,num_samples):
        """configure an analog input channel to measure voltage
           Parameters:  device - DAQ card device (string)
                        AIchan - Analog input channel for measurement (string)
                        min_volts - minimum voltage level expected (float)
                        max_volts - maximum voltage level expected (float)
                        sample_rate - number of samples to be taken per second (float)
                        num_samples - maximum number of samples to be taken (integer)
            Returns:    nothing
        """
        self.min_volts = min_volts
        self.max_volts = max_volts
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.channel = device + "/" + AIchan
        self._CHK(nidaq.DAQmxCreateAIVoltageChan(self.task_handle,self.channel,"",
                                           DAQmx_Val_NRSE,
                                           float64(self.min_volts),float64(self.max_volts),
                                           DAQmx_Val_Volts,None))
        self._CHK(nidaq.DAQmxCfgSampClkTiming(self.task_handle,Internal_Clock,float64(self.sample_rate),
                                        DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,
                                        uInt64(self.num_samples)))

    def Take_Voltage_Measurement(self):
        """take a voltage measurement from a defined voltage channel
        
           Returns:     data - a numpy array of floats containing the voltage readings or
                               'error' upon incorrect number of samples taken
        """
        self._CHK(nidaq.DAQmxStartTask(self.task_handle))
        samples_read = int32()
        data = numpy.zeros((self.num_samples,),dtype=numpy.float64)
        self._CHK(nidaq.DAQmxReadAnalogF64(self.task_handle,uInt32(self.num_samples),float64(self.timeout),
                                     DAQmx_Val_GroupByChannel,data.ctypes.data,
                                     self.num_samples,ctypes.byref(samples_read),None))
        if self.task_handle.value != 0:
            nidaq.DAQmxStopTask(self.task_handle)
        nidaq.DAQmxClearTask(self.task_handle)
        if samples_read.value != self.num_samples:
            return 'error'
        else:
            return data

class Analog_Group_Input_Thread(threading.Thread,NIDAQ):
    """this class uses threading to set up an analog voltage measurement of a group of channels
       and return control to the calling program while the measurement is taking place
    """
    def __init__(self,q,sample_rate=100.0,test_time_sec=10,fillmode='channel',buffer_flush_sec=2):
        threading.Thread.__init__(self)
        if type(sample_rate) is float:
            self.sample_rate = sample_rate
        else:
            raise RuntimeError("sample rate type must be float")

        if type(test_time_sec) is float or int:
            self.test_time_sec = float(test_time_sec)
        else:
            raise RuntimeError("test time must be float or integer")

        if fillmode is 'channel':
            self.fillmode = DAQmx_Val_GroupByChannel
        elif fillmode is 'scan':
            self.fillmode = DAQmx_Val_GroupByScanNumber
        else:
            raise RuntimeError("fillmode must be 'channel' or 'scan'")

        if buffer_flush_sec is float or int:
            self.buffer_flush_sec = buffer_flush_sec
        else:
            raise RuntimeError("buffer_flush_sec must be float or integer")
        
        self.daemon = True
        self.num_channels = 0
        self.data_array_index = 0
        self.max_samples_per_channel = sample_rate * test_time_sec
        self.result_queue = q
        self.task_handle = TaskHandle(0)
        self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.task_handle)))
        print "__init__ completed"

    def run(self):
        try:
            """this function will start the voltage measurement and when completed, put the result onto
               a result queue for retrieval by the calling function"""
            if ( (self.test_time_sec*self.sample_rate) - int(self.test_time_sec*self.sample_rate) ) > 0.0:
                self.total_num_samples = ( int(self.test_time_sec*self.sample_rate) + 1 ) * self.num_channels
            else:
                self.total_num_samples = int(self.test_time_sec*self.sample_rate)

            if ( (self.buffer_flush_sec*self.sample_rate) - int(self.buffer_flush_sec*self.sample_rate) ) > 0.0:
                self.num_event_samples = ( int(self.buffer_flush_sec * self.sample_rate) + 1 ) * self.num_channels
            else:
                self.num_event_samples = int(self.buffer_flush_sec * self.sample_rate) * self.num_channels


    ##        self.buffer_size = self.total_num_samples * sample_rate + 500
    ##        self.num_samples = int(self.sample_rate * self.test_time_sec * self.num_channels)
            self.data_array = numpy.zeros((self.total_num_samples),dtype=numpy.float64)
            print "data array created"

            self.Take_Voltage_Measurement()
            #if buffer fills (and measurement ends) then call Stop_Measuring() from within class I guess...
            #I really don't know what the fuck I am doing but this might work...
            print "Stop_Measuring() call from inside the run() function"
            self.Stop_Measuring()
        except Exception as e:
            print "Exception in Analog_Group_Input_Thread run: " + repr(e)

    def Add_Analog_Voltage_Channel(self,device,channel,min=-10.0,max=10.0):
        """configure analog input channel and add to the task
        """
        self.num_channels += 1
        self.channel = device + "/" + channel
        self._CHK(nidaq.DAQmxCreateAIVoltageChan(self.task_handle,self.channel,"",
                                                 DAQmx_Val_NRSE,
                                                 float64(min),float64(max),
                                                 DAQmx_Val_Volts,None))

    def Take_Voltage_Measurement(self):
        try:
            """take a voltage measurement from the defined voltage channels
            
               Returns:     data - a numpy array of floats containing the voltage readings or
                                   'error' upon incorrect number of samples taken
            """
            print "\nTake_Voltage_Measurement() function entered"
            print "self.sample_rate: " + repr(self.sample_rate)
            print "self.num_channels: " + repr(self.num_channels)
            print "self.buffer_flush_sec: " + repr(self.buffer_flush_sec)
            print "self.total_num_samples: " + repr(self.total_num_samples)
            print "self.num_event_samples: " + repr(self.num_event_samples)
            print
            self._CHK(nidaq.DAQmxCfgSampClkTiming(self.task_handle,Internal_Clock,float64(self.sample_rate),
                                            DAQmx_Val_Rising,DAQmx_Val_ContSamps,
                                            uInt64(self.num_event_samples*2)))
            print "sample clock has been set up"
            self._CHK(nidaq.DAQmxRegisterEveryNSamplesEvent(self.task_handle,DAQmx_Val_Acquired_Into_Buffer,self.num_event_samples,0,
                                                            EveryNSamplesEventCallbackType(self.EveryNcallback),None))
            print "Every N Samples Event has been registered"
            self._CHK(nidaq.DAQmxStartTask(self.task_handle))
            print "task started"
##            for i in range(10):
##                time.sleep(1)
##                print "task counter %d"%i
        except Exception as e:
            print "Exception in Take_voltage_Measurement(): " + repr(e)
            
    def EveryNcallback(self,handle,everyNsamplesEventType,num_event_samples,callbackData):
        try:
            """executes every time buffer reaches specified amount of samples contained in num_event_samples
            """
            print "************************"
            print "entered callback function"
            print "************************"
            timeout = 10.0
            num_samples_read = int32()
            temp_array = numpy.zeros((num_event_samples),dtype=numpy.float64)
            self._CHK(nidaq.DAQmxReadAnalogF64(handle,uInt32(num_samples),float64(timeout),
                                               self.fillmode,temp_array.ctypes.data,
                                               len(temp_array),ctypes.byref(num_samples_read),None))
            print "number of samples read from buffer: %d"%num_samples_read
            start_element = self.data_array_index
            end_element = self.data_array_index + num_samples
            self.data_array[start_element:end_element]
            self.data_array_index += num_event_samples
        except Exception as e:
            print "Exception in EveryNcallback(): " + repr(e)
        

    #def Done_Callback(self,self.task_handle)
    def Stop_Measuring(self):
        try:
            print "Entered Stop_Measuring() function"
            nidaq.DAQmxStopTask(self.task_handle)
            print "After StopTask"
            nidaq.DAQmxClearTask(self.task_handle)
            print "After ClearTask"
            self.result_queue.put(self.data_array)
        except Exception as e:
            print "Exception in Stop_Measuring(): " + repr(e)

class Analog_Triggered_Input_Thread(threading.Thread,NIDAQ):
    """this class uses threading to set up an analog voltage measurement and return control
       to the calling program while the measurement is taking place
    """
    def __init__(self,device,channel,q,min=-10.0,max=10.0,trig=0.0,slope=DAQmx_Val_Rising,
                 sample_rate=1000.0,num_samples=1000,num_pre_trig_samples=100,timeout=30.0):
        """ Parameters: device -    DAQ card device (string)
                        channel -   Analog input channel for measurement (string)
                        q -         the queue to contain the results array (queue)
                        min -       minimum voltage level expected (float)
                        max -       maximum voltage level expected (float)
                        trig -      the analog voltage trigger level (float)
                        sample_rate - number of samples to be taken per second (float)
                        num_samples - total number of samples to be taken (integer)
                        num_pre_trig_samples - number of pre-trigger samples to save (integer)
                        timeout -   time in seconds (float)
        """
        threading.Thread.__init__(self)
        self.daemon = True
        self.task_handle = TaskHandle(0)
        self.device = device
        self.channel = channel
        self.device_and_channel = device + "/" + channel
        self.min_volts = min
        self.max_volts = max
        self.trig_level = trig
        if slope == 'rising': self.slope = DAQmx_Val_Rising
        elif slope == 'falling': self.slope = DAQmx_Val_Falling
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.num_pre_trig_samples = num_pre_trig_samples
        self.timeout = timeout
        self.result_queue = q
        self.Create_Task()
        self.Config_Finite_Voltage_Measurement(self.device,self.channel,
                                               self.min_volts,self.max_volts,
                                               self.sample_rate,self.num_samples)

    def run(self):
        """this function will start the voltage measurement and, when completed put the result onto
           a result queue for retrieval by the calling function"""
        result = self.Take_Voltage_Measurement()
        self.result_queue.put(result)

    def Create_Task(self):
        self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.task_handle)))

    def Config_Finite_Voltage_Measurement(self,device,AIchan,min_volts,max_volts,sample_rate,num_samples):
        """configure an analog input channel to measure voltage
        """        
        self._CHK(nidaq.DAQmxCreateAIVoltageChan(self.task_handle,self.device_and_channel,"",
                                           DAQmx_Val_NRSE,
                                           float64(self.min_volts),float64(self.max_volts),
                                           DAQmx_Val_Volts,None))
        self._CHK(nidaq.DAQmxCfgSampClkTiming(self.task_handle,Internal_Clock,float64(self.sample_rate),
                                        DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,
                                        uInt64(self.num_samples)))
        self._CHK(nidaq.DAQmxCfgAnlgEdgeRefTrig(self.task_handle,self.device_and_channel,self.slope,
                                                  float64(self.trig_level),self.num_pre_trig_samples))

    def Take_Voltage_Measurement(self):
        """take a voltage measurement from a defined voltage channel
           Parameters:  num_samples - maximum number of samples to be taken (integer)
                        timeout - maximum time in seconds before voltage reading fails (float)
                        outfile - a .csv file object to write the results to
           Returns:     data - a numpy array of floats containing the voltage readings or
                               'error' upon incorrect number of samples taken
        """
        self._CHK(nidaq.DAQmxStartTask(self.task_handle))
        samples_read = int32()
        data = numpy.zeros((self.num_samples,),dtype=numpy.float64)
        self._CHK(nidaq.DAQmxReadAnalogF64(self.task_handle,uInt32(self.num_samples),float64(self.timeout),
                                     DAQmx_Val_GroupByChannel,data.ctypes.data,
                                     self.num_samples,ctypes.byref(samples_read),None))
        if self.task_handle.value != 0:
            nidaq.DAQmxStopTask(self.task_handle)
        nidaq.DAQmxClearTask(self.task_handle)
        if samples_read.value != self.num_samples:
            return 'error'
        else:
            return data

    def Take_Voltage_Measurement_old(self,timeout):
        """take a voltage measurement from a defined voltage channel
           Parameters:  num_samples - maximum number of samples to be taken (integer)
                        timeout - maximum time in seconds before voltage reading fails (float)
                        outfile - a .csv file object to write the results to
           Returns:     data - a numpy array of floats containing the voltage readings or
                               'error' upon incorrect number of samples taken
        """
        self._CHK(nidaq.DAQmxStartTask(self.task_handle))
        samples_read = int32()
        data = numpy.zeros((self.num_samples,),dtype=numpy.float64)
        self._CHK(nidaq.DAQmxReadAnalogF64(self.task_handle,uInt32(self.num_samples),float64(timeout),
                                     DAQmx_Val_GroupByChannel,data.ctypes.data,
                                     self.num_samples,ctypes.byref(samples_read),None))
        if self.task_handle.value != 0:
            nidaq.DAQmxStopTask(self.task_handle)
        nidaq.DAQmxClearTask(self.task_handle)
        if samples_read.value != self.num_samples:
            return 'error'
        else:
            return data



class Analog_Output_Thread(threading.Thread,NIDAQ):
    """
    This class performs the necessary initialization of the DAQ hardware and
    spawns a thread to handle playback of the signal.
    It takes as input arguments the waveform to play and the sample rate at which
    to play it.
    This will play an arbitrary-length waveform file.
    """
    def __init__(self, device, channel, waveform, sampleRate):
        threading.Thread.__init__(self)
        self.daemon = True
        self.channel = device + "/" + channel
        self.sampleRate = float64(sampleRate)
        self.periodLength = len(waveform)
        self.taskHandle = TaskHandle(0)
        self.min_output = float64(-10.0)
        self.max_output = float64(10.0)
        if type(waveform) != 'numpy.ndarray':
            self.data = numpy.zeros( ( self.periodLength, ), dtype=numpy.float64 )
            for i in range(self.periodLength):
                self.data[i] = waveform[i]
        else:
            self.data = waveform
        additional_seconds = 5.0
        self.timeout = float64( len(self.data) / sampleRate )

        self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref( self.taskHandle )))
        self._CHK(nidaq.DAQmxCreateAOVoltageChan( self.taskHandle,
                                                 self.channel,"",
                                                 self.min_output,
                                                 self.max_output,
                                                 DAQmx_Val_Volts,
                                                 No_Custom_Scale))
        self._CHK(nidaq.DAQmxCfgSampClkTiming( self.taskHandle,
                                              Onboard_Clock,
                                              self.sampleRate,
                                              DAQmx_Val_Rising,
                                              DAQmx_Val_FiniteSamps,
                                              uInt64(self.periodLength)))
        self._CHK(nidaq.DAQmxWriteAnalogF64( self.taskHandle,
                                            int32(self.periodLength),
                                            No_Autostart,
                                            self.timeout,
                                            DAQmx_Val_GroupByChannel,
                                            self.data.ctypes.data,
                                            None,
                                            None))

    def run(self):
        self._CHK(nidaq.DAQmxStartTask(self.taskHandle))

    def stop(self):
        nidaq.DAQmxStopTask(self.taskHandle)
        nidaq.DAQmxClearTask(self.taskHandle)

class Pulse_Width_Measurement_Thread(threading.Thread,NIDAQ):
    """
    This class performs the necessary initialization of the DAQ hardware and
    spawns a thread to handle pulse width measurement of a signal.
    
    
    """
    def __init__(self, device, channel, q, minT, maxT, slope='rising', timeout=10.0):
        threading.Thread.__init__(self)
        self.daemon = True
        self.result_queue = q
        self.channel = device + "/" + channel
        self.minT = float64(minT)
        self.maxT = float64(maxT)
        self.timeout = float64(timeout)
        if slope == 'rising': self.slope = DAQmx_Val_Rising
        elif slope == 'falling': self.slope = DAQmx_Val_Falling
        else: raise RuntimeError("invalid slope value passed")
        
        self.taskHandle = TaskHandle(0)
        self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.taskHandle)))
        self._CHK(nidaq.DAQmxCreateCIPulseWidthChan( self.taskHandle,self.channel,"",
                                                     self.minT,self.maxT,
                                                     DAQmx_Val_Seconds,
                                                     self.slope,None))

    def run(self):
        """this function will start the pulse width measurement thread and, when completed put the result onto
           a result queue for retrieval by the calling function"""
        result = self.measure_pulse_width()
        self.result_queue.put(result)

    def measure_pulse_width(self):
        self._CHK(nidaq.DAQmxStartTask(self.taskHandle))
        reading = float64(0.0)
        self._CHK(nidaq.DAQmxReadCounterScalarF64(self.taskHandle,self.timeout,ctypes.byref(reading),None))
        nidaq.DAQmxStopTask(self.taskHandle)
        nidaq.DAQmxClearTask(self.taskHandle)
        return reading.value
