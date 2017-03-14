import ctypes
import numpy
import threading
import time
from Queue import Queue
from string import upper

nidaq = ctypes.windll.nicaiu
##############################
# Setup some typedefs,constants,variables
# to correspond with values in
# C:\Program Files\National Instruments\NI-DAQ\DAQmx ANSI C Dev\include\NIDAQmx.h
# the typedefs
uint8 = ctypes.c_uint8
int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
void_ptr = ctypes.c_void_p
TaskHandle = uInt32
EveryNSamplesEventCallbackType = ctypes.CFUNCTYPE(int32,TaskHandle,int32,uInt32,void_ptr)
DoneEventCallbackType = ctypes.CFUNCTYPE(int32,TaskHandle,int32,void_ptr)
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
DAQmx_Val_GroupByChannel = 0 #noninterleaved
DAQmx_Val_GroupByScanNumber = 1 #interleaved
DAQmx_Val_Acquired_Into_Buffer = 1
DAQmx_Val_Transferred_From_Buffer = 2
DAQmx_Val_ChanPerLine = 0
DAQmx_Val_ChanForAllLines = 1
Internal_Clock = None
No_Custom_Scale = None
Onboard_Clock = None
No_Autostart = 0
Autostart = 1
##############################
class NIDAQ(object):
    def _CHK(self,_err):
        """a simple error checking routine"""
        if _err < 0:
            buf_size = 100
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(_err,ctypes.byref(buf),buf_size)
            raise RuntimeError("nidaq call failed with error %d: %s"%(_err,repr(buf.value)))
        if _err > 0:
            buf_size = 100
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(_err,ctypes.byref(buf),buf_size)
            raise RuntimeError("nidaq generated warning %d: %s"%(_err,repr(buf.value)))

class digital_output_channel(NIDAQ):
        def __init__(self,device,port,line,timeout=10.0):
            self.timeout = timeout
            self.task_handle = TaskHandle(0)
            self.Create_Task()
            self.Create_DO_Channel(device,port,line)

        def __del__(self):
            self.stop_task()

        def Create_Task(self):
            self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.task_handle)))

        def Create_DO_Channel(self,device,port,line):
            self.chans = '%s'%device + '/' + 'port%s'%port + '/' + 'line%s'%line
            temp = nidaq.DAQmxCreateDOChan(self.task_handle,self.chans,"",1)
            self._CHK(nidaq.DAQmxStartTask(self.task_handle))

        def write_state(self,data):
            if data not in [0,1]:
                raise RuntimeError("data must be binary (0 or 1)")

            a=(ctypes.c_uint8*1)()
            a[0]=data

            self._CHK(nidaq.DAQmxWriteDigitalLines(self.task_handle,1,1,float64(self.timeout),
                                    DAQmx_Val_GroupByChannel,a,None,None))

        def stop_task(self):
            self.write_state(0)
            nidaq.DAQmxStopTask(self.task_handle)
            nidaq.DAQmxClearTask(self.task_handle)

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

    def Config_Finite_Voltage_Measurement(self,device,AIchan,min_volts,max_volts,sample_rate,num_samples,
                                        meas_type='NRSE'):
        """configure an analog input channel to measure voltage
           Parameters:  device - DAQ card device (string)
                        AIchan - Analog input channel for measurement (string)
                        min_volts - minimum voltage level expected (float)
                        max_volts - maximum voltage level expected (float)
                        sample_rate - number of samples to be taken per second (float)
                        num_samples - maximum number of samples to be taken (integer)
                        meas_type - type of measurement to perform (string):RSE,NRSE,DIFF
            Returns:    nothing
        """
        self.min_volts = min_volts
        self.max_volts = max_volts
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.channel = device + "/" + AIchan

        if upper(meas_type) == 'DIFF':
            meas_type = DAQmx_Val_Diff
        elif upper(meas_type) == 'RSE':
            meas_type = DAQmx_Val_RSE
        elif upper(meas_type) == 'NRSE':
            meas_type = DAQmx_Val_NRSE

        self._CHK(nidaq.DAQmxCreateAIVoltageChan(self.task_handle,self.channel,"",
                                           meas_type,
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

class AI_Voltage_Channels(NIDAQ):
    def __init__(self):
        self.task_handle = TaskHandle(0)
        self.timeout = 10.0
        self.Create_Task()
    def __del__(self):
        nidaq.DAQmxClearTask(self.task_handle)

    def Create_Task(self):
        self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.task_handle)))

    def Config_Finite_Voltage_Measurement(self,AIchans,min_volts,max_volts,sample_rate,num_samples,
                                            meas_type='NRSE'):
        """configure an analog input channel to measure voltage
           Parameters:  AIchan - Analog input channel for measurement (string)
                        min_volts - minimum voltage level expected (float)
                        max_volts - maximum voltage level expected (float)
                        sample_rate - number of samples to be taken per second (float)
                        num_samples - number of samples to be taken per channel (integer)
                        meas_type - 'DIFF','RSE','NRSE'
            Returns:    nothing
        """
        if upper(meas_type) == 'DIFF':
            meas_type = DAQmx_Val_Diff
        elif upper(meas_type) == 'RSE':
            meas_type = DAQmx_Val_RSE
        elif upper(meas_type) == 'NRSE':
            meas_type = DAQmx_Val_NRSE

        self.num_channels = len(AIchans.split(','))
        self.num_samples = num_samples
        self._CHK(nidaq.DAQmxCreateAIVoltageChan(self.task_handle,AIchans,"",
                                           meas_type,
                                           float64(min_volts),float64(max_volts),
                                           DAQmx_Val_Volts,None))
        self._CHK(nidaq.DAQmxCfgSampClkTiming(self.task_handle,Internal_Clock,float64(sample_rate),
                                        DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,
                                        uInt64(self.num_samples)))

    def Take_Voltage_Measurement(self,timeout=10.0):
        """take a voltage measurement from a defined voltage channel
           Parameters:  num_samples - maximum number of samples to be taken (integer)
                        timeout - maximum time in seconds before voltage reading fails (float)
           Returns:     a numpy array of floats containing the voltage readings or
                               'error' upon incorrect number of samples taken
        """
        self.timeout = timeout
        self._CHK(nidaq.DAQmxStartTask(self.task_handle))
        samples_per_chan_read = int32()
        data = numpy.zeros((self.num_samples*self.num_channels),dtype=numpy.float64)

        self._CHK(nidaq.DAQmxReadAnalogF64(self.task_handle,uInt32(self.num_samples),float64(self.timeout),
                                     DAQmx_Val_GroupByChannel,data.ctypes.data,
                                     self.num_samples*self.num_channels,ctypes.byref(samples_per_chan_read),None))

        if self.task_handle.value != 0:
            nidaq.DAQmxStopTask(self.task_handle)

        if (samples_per_chan_read.value *self.num_channels) != (self.num_samples*self.num_channels):
            raise RuntimeError("Measurement Error: incorrect number of samples taken")
        else:
            data_list = []
            start_index = 0
            end_index = self.num_samples

            for i in range(self.num_channels):
                data_list.append(data[start_index:end_index])
                start_index += self.num_samples
                end_index += self.num_samples

            return data_list


class AI_Voltage_Measurement(NIDAQ):
    """this class gives a way to add channels to a task in multiple calls to
       Config_Finite_Voltage_Measurement, allowing different channel scales to be used.
    """
    def __init__(self,timeout=10.0):
        self.task_handle = TaskHandle(0)
        self.timeout = timeout
        self.samples_per_sec = 1000.0
        self.num_samples_per_ch = 1000
        self.num_channels = 0
        self.Create_Task()

    def __del__(self):
        nidaq.DAQmxClearTask(self.task_handle)

    def Create_Task(self):
        self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.task_handle)))

    def Add_Channels(self,AIchans,min_volts=-10.0,max_volts=10.0):
        """configure an analog input channel to measure voltage
           Parameters:  AIchan - Analog input channel for measurement (string)
                        min_volts - minimum voltage level expected (float)
                        max_volts - maximum voltage level expected (float)
            Returns:    nothing
        """
        self.num_channels += len(AIchans.split(','))
        self._CHK(nidaq.DAQmxCreateAIVoltageChan(self.task_handle,AIchans,"",
                                           DAQmx_Val_NRSE,
                                           float64(min_volts),float64(max_volts),
                                           DAQmx_Val_Volts,None))

    def Config_Sample_Clock(self,samples_per_sec=1000.0,num_samps_per_ch=1000):
        """configure the DAQ card sample clock
           Parameters:  samples_per_sec - number of samples to be taken per second (float)
                        num_samps_per_ch - number of samples to be taken per channel (integer)
            Returns:    nothing
        """
        self.samples_per_sec = samples_per_sec
        self.num_samples_per_ch = num_samps_per_ch

    def Take_Voltage_Measurement(self,timeout=10.0):
        """take a voltage measurement from a defined voltage channel
           Parameters:  timeout - maximum time in seconds before voltage reading fails (float)
           Returns:     a numpy array of floats containing the voltage readings or
                               'error' upon incorrect number of samples taken
        """
        self.timeout = timeout
        self._CHK(nidaq.DAQmxCfgSampClkTiming(self.task_handle,Internal_Clock,float64(self.samples_per_sec),
                                        DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,
                                        uInt64(self.num_samples_per_ch)))
        self._CHK(nidaq.DAQmxStartTask(self.task_handle))
        samples_per_chan_read_by_DAQ = int32()
        data = numpy.zeros((self.num_samples_per_ch*self.num_channels),dtype=numpy.float64)

        self._CHK(nidaq.DAQmxReadAnalogF64(self.task_handle,uInt32(self.num_samples_per_ch),float64(self.timeout),
                                     DAQmx_Val_GroupByChannel,data.ctypes.data,
                                     self.num_samples_per_ch*self.num_channels,ctypes.byref(samples_per_chan_read_by_DAQ),None))

        if self.task_handle.value != 0:
            nidaq.DAQmxStopTask(self.task_handle)

        if (samples_per_chan_read_by_DAQ.value *self.num_channels) != (self.num_samples_per_ch*self.num_channels):
            raise RuntimeError("Measurement Error: incorrect number of samples taken")
        else:
            data_list = []
            start_index = 0
            end_index = self.num_samples_per_ch

            for i in range(self.num_channels):
                data_list.append(data[start_index:end_index])
                start_index += self.num_samples_per_ch
                end_index += self.num_samples_per_ch

            return data_list


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

class Analog_Input_Thread_Continuous(threading.Thread,NIDAQ):
    """this class uses threading to set up an analog voltage measurement of a group of channels
       and return control to the calling program while the measurement is taking place
    """
    def __init__(self,q,daq_card,samps_per_chan_per_sec=100.0,event_time_sec=2.0,
                        fillmode='channel',meas_type='NRSE'):
        self.debug = False
        threading.Thread.__init__(self)
        self.keep_measuring = True
        if type(samps_per_chan_per_sec) is float or int:
            self.samps_per_chan_per_sec = float(samps_per_chan_per_sec)
        else:
            raise RuntimeError("sample rate type must be int or float")

        if fillmode is 'channel':
            self.fillmode = DAQmx_Val_GroupByChannel
        elif fillmode is 'scan':
            self.fillmode = DAQmx_Val_GroupByScanNumber
        else:
            raise RuntimeError("fillmode must be 'channel' or 'scan'")

        if event_time_sec is float or int:
            self.event_time_sec = float(event_time_sec)
        else:
            raise RuntimeError("event_time_sec must be int or float")

        if upper(meas_type) == 'DIFF':
            self.meas_type = DAQmx_Val_Diff
        elif upper(meas_type) == 'RSE':
            self.meas_type = DAQmx_Val_RSE
        elif upper(meas_type) == 'NRSE':
            self.meas_type = DAQmx_Val_NRSE
        else:
            raise RuntimeError("unknown measurement type: %s"%meas_type)

        self.event_samples = self.event_time_sec * self.samps_per_chan_per_sec
        self.daemon = True
        self.num_channels = 0
        self.device = daq_card
        self.result_queue = q
        self.all_samples_list = []
        self.task_handle = TaskHandle(0)
        self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.task_handle)))
        if self.debug is True: print "__init__ completed"

    def Add_Analog_Voltage_Channel(self,channel,min=-10.0,max=10.0):
        """configure analog input channel and add to the task
        """
        self.num_channels += 1
        self.channel = self.device + "/" + channel
        self._CHK(nidaq.DAQmxCreateAIVoltageChan(self.task_handle,self.channel,"",
                                                 self.meas_type,
                                                 float64(min),float64(max),
                                                 DAQmx_Val_Volts,None))
    def run(self):
        try:
            """this function will start the voltage measurement and when completed, put the result onto
               a result queue for retrieval by the calling function
            """
            if self.debug is True: print "run entered"
            if ( (self.event_time_sec*self.samps_per_chan_per_sec) - int(self.event_time_sec*self.samps_per_chan_per_sec) ) > 0.0:
                self.num_event_samples = ( int(self.event_time_sec * self.samps_per_chan_per_sec) + 1 )
            else:
                self.num_event_samples = int(self.event_time_sec * self.samps_per_chan_per_sec)

            self.buffer_size = self.num_event_samples * self.num_channels
            self.Take_Voltage_Measurement()

            self._group_samples_by_channel()

        except Exception as e:
            print "Exception in Analog_Input_Thread_Continuous run: " + repr(e)
            raise e

    def Take_Voltage_Measurement(self):
        try:
            """take a voltage measurement from the defined voltage channels

               Returns:     data - a numpy array of floats containing the voltage readings or
                                   'error' upon incorrect number of samples taken
            """
            if self.debug is True: print "\nTake_Voltage_Measurement() function entered"
            if self.debug is True: print "self.samps_per_chan_per_sec: " + repr(self.samps_per_chan_per_sec)
            if self.debug is True: print "self.num_channels: " + repr(self.num_channels)
            if self.debug is True: print "self.event_time_sec: " + repr(self.event_time_sec)
##            if self.debug is True: print "self.total_num_samples: " + repr(self.total_num_samples)
            if self.debug is True: print "self.num_event_samples: " + repr(self.num_event_samples)
            if self.debug is True: print

            self._CHK(nidaq.DAQmxCfgSampClkTiming(self.task_handle,Internal_Clock,float64(self.samps_per_chan_per_sec),
                                            DAQmx_Val_Rising,DAQmx_Val_ContSamps,
                                            uInt64(self.buffer_size)))
            if self.debug is True: print "sample clock has been set up"

            n_event_callback = EveryNSamplesEventCallbackType(self.EveryN_callback)
            self._CHK(nidaq.DAQmxRegisterEveryNSamplesEvent(self.task_handle,DAQmx_Val_Acquired_Into_Buffer,
                                                            self.num_event_samples,0,n_event_callback,None))
            if self.debug is True: print "Every N Samples Event has been registered"

            done_callback = DoneEventCallbackType(self.Done_Callback)
            self._CHK(nidaq.DAQmxRegisterDoneEvent(self.task_handle,0,done_callback,None))
            if self.debug is True: print "Done Callback function registered"

            self._CHK(nidaq.DAQmxStartTask(self.task_handle))
            if self.debug is True: print "task started"

            while (self.keep_measuring is True):
                if self.debug is True: print "measuring..."
                time.sleep(.5)

            if self.debug is True: print "finished measuring now"
            nidaq.DAQmxStopTask(self.task_handle)
            if self.debug is True: print "After StopTask"
            nidaq.DAQmxClearTask(self.task_handle)
            if self.debug is True: print "After ClearTask"

        except Exception as e:
            print "Exception in Take_voltage_Measurement(): " + repr(e)
            raise e

    def _group_samples_by_channel(self):
        """take the list of samples (gathered by scan) and put
           into numpy arrays to place on the queue for return.
           If there was only one channel measured put the numpy array on the queue
           If there was more than one channel measured put a list of the numpy arrays on the queue
        """
        print "total number of samples acquired:",len(self.all_samples_list)
        samples_acquired_per_channel = len(self.all_samples_list) / self.num_channels
        print "total number of samples acquired:",len(self.all_samples_list)
        print "number of channels:",self.num_channels
        print "calculated samples acquired per channel:",samples_acquired_per_channel

        #make a list with each element being a numpy array for the results from each channel
        channel_data = []
        for i in range(self.num_channels):
            channel_data.append(numpy.zeros(samples_acquired_per_channel,dtype=float))

        scan_num = 0
        channel_index = 0
        for sample in range(len(self.all_samples_list)):    #each sample in interleaved list
            channel_data[channel_index][scan_num] = self.all_samples_list[sample]
            if channel_index < self.num_channels-1:
                channel_index += 1
            else:
                channel_index = 0
                scan_num += 1

        if self.num_channels == 1:  #if only one channel put the numpy array on the queue
            self.result_queue.put(channel_data[0])
        else:                       #if more than one channel put the list of arrays on the queue
            self.result_queue.put(channel_data)

    def EveryN_callback(self,handle,everyNsamplesEventType,num_event_samples,callbackData):
        try:
            """executes every time buffer reaches specified amount of samples contained in num_event_samples
            """
            if self.debug is True: print "*********************************"
            if self.debug is True: print "entered every N callback function"
            if self.debug is True: print "*********************************"

            timeout = 10.0
            num_samples_read = int32()
            temp_array = numpy.zeros((self.buffer_size),dtype=numpy.float64)
            self._CHK(nidaq.DAQmxReadAnalogF64(handle,uInt32(num_event_samples),float64(timeout),
                                               self.fillmode,temp_array.ctypes.data,
                                               len(temp_array),ctypes.byref(num_samples_read),None))
            if self.debug is True: print temp_array
            for i in range(len(temp_array)):
                self.all_samples_list.append(temp_array[i])

            return 0
        except Exception as e:
            print "Exception in EveryNcallback(): " + repr(e)
            raise e

    def Done_Callback(self,param1,param2,param3):
        try:
            if self.debug is True: print "*******************************"
            if self.debug is True: print "entered done callback function"
            if self.debug is True: print "*******************************"

        except exception as e:
            print "Exception in done callback function: " + repr(e)
            raise e

    def End_Measurement(self):
        try:
            self.keep_measuring = False
        except Exception as e:
            print "Exception found in End_Measurement(): " + repr(e)
            raise e

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


class Analog_Output_Thread(threading.Thread,NIDAQ):
    """
    This class performs the necessary initialization of the DAQ hardware and
    spawns a thread to handle playback of the signal.
    It takes as input arguments the waveform to play and the sample rate at which
    to play it.
    This will play an arbitrary-length waveform file.
    """
    try:
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
    except Exception as e:
        print "Exception found in Analog_Output_Thread(): " + repr(e)
        raise e

class Analog_Output_Thread_Continuous(threading.Thread,NIDAQ):
    """this class uses threading to set up analog output using a DAQ output channel
       and return control to the calling program while the output is taking place
       For multiple channels pass in a multi-dimensional array of samples. Each channel
       should contain the same number of array elements.
    """
    def __init__(self,channels_str,data_array,samps_per_sec,
                 minV=-10.0,maxV=10.0,debug=False):
        threading.Thread.__init__(self)
        try:
            self.debug = debug

            self.daemon = True
            self.continue_output = True
            self.timeout = 10.0
            self.channels = channels_str
            self.channels_list = self.channels.split(',')
            self.num_channels = len(self.channels_list)
            self.data_array = data_array
            self.buffer_size = numpy.size(data_array)
            self.samps_per_sec = float(samps_per_sec)
            self.task_handle = TaskHandle(0)
            self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.task_handle)))
            if self.debug: print "task created"

            self._CHK(nidaq.DAQmxCreateAOVoltageChan(self.task_handle,self.channels,"",
                                                     float64(minV),float64(maxV),DAQmx_Val_Volts,
                                                     None))
            if self.debug: print "channel created"
            self._CHK(nidaq.DAQmxCfgSampClkTiming(self.task_handle,Internal_Clock,float64(self.samps_per_sec),
                                                  DAQmx_Val_Rising,DAQmx_Val_ContSamps,
                                                  uInt64(self.buffer_size)))
            if self.debug: print "clock set up"
            if self.debug: print "buffer size: " + repr(self.buffer_size)
            if self.debug: print "number of channels: " + repr(self.num_channels)
            if self.debug: print "write size: " + repr(self.buffer_size/self.num_channels)
            self._CHK(nidaq.DAQmxWriteAnalogF64(self.task_handle,int32(self.buffer_size/self.num_channels),
                                                No_Autostart,float64(self.timeout),
                                                DAQmx_Val_GroupByChannel,
                                                self.data_array.ctypes.data,
                                                None,None))
            if self.debug: print "write done"
        except Exception as e:
            print "Exception found in Analog_Output_Thread_Continuous()__init__: " + repr(e)
            raise e

    def run(self):
        try:
            """this function will start the voltage measurement and when completed, put the result onto
               a result queue for retrieval by the calling function
            """
            self._CHK(nidaq.DAQmxStartTask(self.task_handle))
            while self.continue_output:
                time.sleep(0.3)

            self.data_array = numpy.zeros(3,dtype=numpy.float64)
            self._CHK(nidaq.DAQmxStopTask(self.task_handle))
            self._CHK(nidaq.DAQmxClearTask(self.task_handle))

            self.clear_output_channels()
        except Exception as e:
            print "Exception in run(): " + repr(e)
            raise e

    def clear_output_channels(self):
        try:
            for ch in self.channels_list:
                h = TaskHandle(0)
                self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(h)))
                self._CHK(nidaq.DAQmxCreateAOVoltageChan(h,ch,"",
                                                         float64(-10.0),float64(10.0),DAQmx_Val_Volts,
                                                         None))
                self._CHK(nidaq.DAQmxWriteAnalogScalarF64( h,Autostart,float64(10.0),
                                                           float64(0.0),None))
                self._CHK(nidaq.DAQmxStopTask(h))
                self._CHK(nidaq.DAQmxClearTask(h))

        except Exception as e:
            print "Exception in clear_output_channels(): " + repr(e)
            raise e

    def End_Output(self):
        try:
            self.continue_output = False
        except Exception as e:
            print "Exception found in End_Output(): " + repr(e)
            raise e


class Analog_Output_Level(threading.Thread,NIDAQ):
    """this class will output a single voltage level on the specified channel
    """
    def __init__(self,channel,minV=-10.0,maxV=10.0):
        try:
            threading.Thread.__init__(self)
            self.task_handle = TaskHandle(0)
            self.buffer_size = 1
            self.timeout = 10.0
            self.sig_level = numpy.zeros(1,dtype=numpy.float64)
            self._CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.task_handle)))
            self._CHK(nidaq.DAQmxCreateAOVoltageChan(self.task_handle,channel,"",
                                                     float64(minV),float64(maxV),DAQmx_Val_Volts,
                                                     None))
            self._CHK(nidaq.DAQmxStartTask(self.task_handle))
            self.clear_channel()

        except Exception as e:
            print "Exception found in Analog_Output_Level()__init__: " + repr(e)
            raise e

    def clear_channel(self):
        try:
            self.sig_level[0] = 0.0
            self._CHK(nidaq.DAQmxWriteAnalogF64(self.task_handle,self.buffer_size,
                                                No_Autostart,float64(self.timeout),
                                                DAQmx_Val_GroupByChannel,
                                                self.sig_level.ctypes.data,
                                                None,None))
        except Exception as e:
            print "Exception in clear_channel(): " + repr(e)
            raise e

    def update(self,value):
        try:
            """this function will update the voltage level on the output channel
            """
            self.sig_level[0] = float(value)
            self._CHK(nidaq.DAQmxWriteAnalogF64(self.task_handle,self.buffer_size,
                                                No_Autostart,float64(self.timeout),
                                                DAQmx_Val_GroupByChannel,
                                                self.sig_level.ctypes.data,
                                                None,None))
        except Exception as e:
            print "Exception in update(): " + repr(e)
            raise e

    def end(self):
        try:
            """sets the voltage output to 0.0 and ends the task
            """
            self.clear_channel()
            self._CHK(nidaq.DAQmxStopTask(self.task_handle))
            self._CHK(nidaq.DAQmxClearTask(self.task_handle))

        except Exception as e:
            print "Exception in end(): " + repr(e)
            raise e



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
