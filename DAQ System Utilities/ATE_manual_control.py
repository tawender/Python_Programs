import time
import wx
import threading
import numpy
import sys
import os.path
sys.path.append("T:\python programs\modules")
import pyNIDAQ

#background colors for buttons
GREEN = (0,255,0,255)
STANDARD = (236,233,216,255)

#DAQ card sampling
ANALOG_INPUT_SAMPLES_PER_SEC = 10.0
ANALOG_INPUT_SAMPLES_PER_CHANNEL = 10
ANALOG_OUTPUT_SAMPLES_PER_SEC = 1000.0



class ATE_manual_control_frame(wx.Frame):
    """
    create frame with the necessary controls and display
    """
    def __init__(self, parent, id, DO_lines):
        self.debug = True
        (self.DO_lines_6251,self.DO_lines_6025) = DO_lines

        wx.Frame.__init__(self, None, -1, title='ATE Manual Control',
                          pos=(10,10),size=(600,800))
        panel = wx.Panel(self,-1)

        #main label for the window
        window_label = wx.StaticText(panel, -1, "ATE Manual Control Utility", pos=(50,10))
        font = wx.Font(31,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        window_label.SetFont(font)



        #*****************************************************************
        #********Analog input voltage controls****************************
        #create labels for 6251 analog voltage display
        voltage_labels = ['VREF','2V2','1V8','Ibat','15V','2V2 ripple','1V8 ripple','15V ripple','TPECG',
                            'ISRC','VREF ripple','VBAT','HV CAPS']
        voltage_labels_x_pos = 20
        voltage_labels_y_pos = 100
        voltage_labels_spacing = 25
        column_label_font = wx.Font(12,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        voltage_display_font = wx.Font(10,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        num_voltage_measurement_labels = 13
        self.voltage_measurement_labels = []
        for i in range(num_voltage_measurement_labels):
            self.voltage_measurement_labels.append(wx.StaticText(panel,-1,voltage_labels[i],
                    pos=(voltage_labels_x_pos,voltage_labels_y_pos+(i*voltage_labels_spacing)),
                    size=(20,70),style=wx.ALIGN_RIGHT))
            self.voltage_measurement_labels[i].SetFont(column_label_font)

        #create the controls to place 6251 analog voltage measurements into
        num_6251_displays = 13
        voltage_measurements_6251_x_pos = 110
        self.voltage_measurements_6251 = []
        for i in range(num_6251_displays):
            self.voltage_measurements_6251.append(wx.TextCtrl(panel,-1,"",size=(67,20),
                    pos=(voltage_measurements_6251_x_pos,voltage_labels_y_pos+(i*voltage_labels_spacing))))
            self.voltage_measurements_6251[i].SetFont(voltage_display_font)
            self.voltage_measurements_6251[i].SetValue("%.4fV"%(1.2345))
        label_6251 = wx.StaticText(panel,-1,'   6251',
                        pos=(voltage_measurements_6251_x_pos,voltage_labels_y_pos-25))
        label_6251.SetFont(column_label_font)


        #create labels for 6025 analog voltage display
        voltage_labels_6025 = ['VREF','2V2','1V8','15V','VBAT','Ibat']
        voltage_labels_6025_x_pos = 260
        self.voltage_measurement_labels_6025 = []
        for i in range(len(voltage_labels_6025)):
            self.voltage_measurement_labels_6025.append(wx.StaticText(panel,-1,voltage_labels_6025[i],
                    pos=(voltage_labels_6025_x_pos,voltage_labels_y_pos+(i*voltage_labels_spacing))))
            self.voltage_measurement_labels_6025[i].SetFont(column_label_font)

        #create the controls to place 6025 analog voltage measurements into
        num_6025_displays = 6
        voltage_measurements_6025_x_pos = 190
        self.voltage_measurements_6025 = []
        for i in range(num_6025_displays):
            self.voltage_measurements_6025.append(wx.TextCtrl(panel,-1,"",size=(67,20),
                    pos=(voltage_measurements_6025_x_pos,voltage_labels_y_pos+(i*voltage_labels_spacing))))
            self.voltage_measurements_6025[i].SetFont(voltage_display_font)
            self.voltage_measurements_6025[i].SetValue("%.4fV"%(1.2345))

        label_6025 = wx.StaticText(panel,-1,'   6025',
                        pos=(voltage_measurements_6025_x_pos,voltage_labels_y_pos-25))
        label_6025.SetFont(column_label_font)

        #create a timer for updating voltage displays
        self.timer = wx.Timer(self, -1)
        self.timer.Start(1000)      # update clock digits every second (1000ms)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        #*****************************************************************




        #*****************************************************************
        #**********Digital Controls***************************************
        DIO_6251_port_numbers = ["P0_0","P0_1"]
        DIO_portnums_6251 = []
        DIO_6251_port_descriptions = ["short TZ","BOL(off)/EOL(on)"]
        DIO_portnames_6251 = []
        self.DIO_buttons_6251 = []

        digital_ports_6251_x_pos = 350
        digital_ports_6251_y_pos = 710
        digital_y_pos = 100
        digital_y_spacing = 18
        num_digital_controls_6251 = len(DIO_6251_port_numbers)

        DIO_label_font = wx.Font(10,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        DIO_description_font = wx.Font(10,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        DIO_button_font = wx.Font(8,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        DIO_button_size = (35,18)

        #labels for port numbers on 6251 DIO card
        for i in range(num_digital_controls_6251):
            DIO_portnums_6251.append(wx.StaticText(panel,-1,DIO_6251_port_numbers[i],
                pos=(digital_ports_6251_x_pos,digital_ports_6251_y_pos+(i*digital_y_spacing))))
            DIO_portnums_6251[i].SetFont(DIO_label_font)

        #buttons for controlling 6251 ports
        for i in range(num_digital_controls_6251):
            self.DIO_buttons_6251.append(wx.Button(panel,-1,'OFF',
                pos=(digital_ports_6251_x_pos+40,digital_ports_6251_y_pos+(i*digital_y_spacing)-2),
                size=DIO_button_size))
            self.DIO_buttons_6251[i].name = "6251_%d"%i
            self.DIO_buttons_6251[i].SetFont(DIO_button_font)
            self.DIO_buttons_6251[i].SetBackgroundColour(STANDARD)
            self.Bind(wx.EVT_BUTTON,self.on_DIO_click,self.DIO_buttons_6251[i])

        #labels for 6251 port descriptions
        for i in range(num_digital_controls_6251):
            DIO_portnames_6251.append(wx.StaticText(panel,-1,DIO_6251_port_descriptions[i],
                pos=(digital_ports_6251_x_pos+80,digital_ports_6251_y_pos+(i*digital_y_spacing))))
            DIO_portnames_6251[i].SetFont(DIO_description_font)

        #label 6251 column
        label_6251_DO = wx.StaticText(panel,-1,'  6251 Digital Output',
                        pos=(digital_ports_6251_x_pos,digital_ports_6251_y_pos-25))
        label_6251_DO.SetFont(column_label_font)


        #variables for the 6025 digital ports
        DIO_6025_port_numbers = ["DIO_0","DIO_1","DIO_2","DIO_3","DIO_4","DIO_5","DIO_6","DIO_7",
                                    "PA_0","PA_1","PA_2","PA_3","PA_4","PA_5","PA_6","PA_7",
                                    "PB_0","PB_1","PB_2","PB_3","PB_4","PB_5","PB_6","PB_7",
                                    "PC_0","PC_1","PC_2","PC_3","PC_4","PC_5","PC_6","PC_7"]
        DIO_portnums_6025 = []
        DIO_6025_port_descriptions = ["shock load 1","shock load 2","shock load 3","shock load 4",
                    "75ohm shock load","","","HVcaps 10K load","ECG SA-A0","ECG SA-A1",
                    "ECG SB-A0","ECG SB-A1","ECG HVA-A0","ECG HVA-A1","ECG HVB-A0","ECG HVB-A1",
                    "SMU_CH1-2V2","SMU_CH2-1V8","SMU_CH3-15V","GPIP0-1V8","FDATA0-GND","ADCIN-2V2",
                    "","","PicoscopeA-shock","PicoscopeB-ECGDATA","PicoscopeB-CEN","PicoscopeA-DATA0",
                    "","","",""]
        DIO_portnames_6025 = []
        self.DIO_buttons_6025 = []
        digital_ports_6025_x_pos = 350
        num_digital_controls_6025 = len(DIO_6025_port_numbers)
        DIO_portnums_6025 = []

        #labels for port numbers on 6025 DIO card
        for i in range(num_digital_controls_6025):
            DIO_portnums_6025.append(wx.StaticText(panel,-1,DIO_6025_port_numbers[i],
                pos=(digital_ports_6025_x_pos,digital_y_pos+(i*digital_y_spacing))))
            DIO_portnums_6025[i].SetFont(DIO_label_font)

        #buttons for controlling 6025 ports
        for i in range(num_digital_controls_6025):
            self.DIO_buttons_6025.append(wx.Button(panel,-1,'OFF',
                pos=(digital_ports_6025_x_pos+40,digital_y_pos+(i*digital_y_spacing)-2),
                size=DIO_button_size))
            self.DIO_buttons_6025[i].name="6025_%d"%i
            self.DIO_buttons_6025[i].SetFont(DIO_button_font)
            self.DIO_buttons_6025[i].SetBackgroundColour(STANDARD)
            self.Bind(wx.EVT_BUTTON,self.on_DIO_click,self.DIO_buttons_6025[i])

        #labels for 6025 port descriptions
        for i in range(len(DIO_6025_port_descriptions)):
            DIO_portnames_6025.append(wx.StaticText(panel,-1,DIO_6025_port_descriptions[i],
                pos=(digital_ports_6025_x_pos+80,digital_y_pos+(i*digital_y_spacing))))
            DIO_portnames_6025[i].SetFont(DIO_description_font)

        #label 6025 column
        label_6025_DO = wx.StaticText(panel,-1,'  6025 Digital Output',
                        pos=(digital_ports_6025_x_pos,digital_y_pos-25))
        label_6025_DO.SetFont(column_label_font)
        #*****************************************************************





        #*****************************************************************
        #***********Analog Output Controls********************************
        AO_x_pos = 100
        AO_y_pos = 450
        #section label
        label_AO = wx.StaticText(panel,-1,' 6251 Analog Output',
                        pos=(AO_x_pos,AO_y_pos))
        label_AO.SetFont(column_label_font)

        #radio buttons for selecting output type
        output_types_list = ['Sinewave', 'ECG']
        self.output_types = wx.RadioBox(panel, -1, "", (AO_x_pos,AO_y_pos+20), wx.DefaultSize,
                        output_types_list, 2, wx.RA_SPECIFY_COLS)
        self.Bind(wx.EVT_RADIOBOX, self.on_AO_change, self.output_types)

        #numeric control for selecting sinewave amplitude
        self.amplitude_label = wx.StaticText(panel,-1,'amplitude(Vpp)',
                        pos=(AO_x_pos-20,AO_y_pos+76))
        self.amplitude_label.SetFont(DIO_label_font)
        self.amplitude_entry = wx.TextCtrl(panel,-1,'0.05',
                    pos=(AO_x_pos+70,AO_y_pos+75),size=(50,20),
                    style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER,self.on_amplitude_entered,self.amplitude_entry)

        self.amplitude_spin = wx.SpinButton(panel,-1,pos=(AO_x_pos+120,AO_y_pos+75))
        self.Bind(wx.EVT_SPIN_UP,self.on_amplitude_spin_increase,self.amplitude_spin)
        self.Bind(wx.EVT_SPIN_DOWN,self.on_amplitude_spin_decrease,self.amplitude_spin)

        #numeric control for selecting sinewave frequency
        self.frequency_label = wx.StaticText(panel,-1,'frequency(Hz)',
                        pos=(AO_x_pos-20,AO_y_pos+101))
        self.frequency_label.SetFont(DIO_label_font)
        self.frequency_entry = wx.TextCtrl(panel,-1,'11.0',
                    pos=(AO_x_pos+70,AO_y_pos+100),size=(50,20),
                    style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER,self.on_frequency_entered,self.frequency_entry)

        self.frequency_spin = wx.SpinButton(panel,-1,pos=(AO_x_pos+120,AO_y_pos+100))
        self.Bind(wx.EVT_SPIN_UP,self.on_frequency_spin_increase,self.frequency_spin)
        self.Bind(wx.EVT_SPIN_DOWN,self.on_frequency_spin_decrease,self.frequency_spin)

        #container for all controls related to sinewave output adjustment
        self.sinewave_controls = [self.amplitude_label,self.amplitude_entry,self.amplitude_spin,
                                    self.frequency_label,self.frequency_entry,self.frequency_spin]

        #slider for selecting ECG beats-per-minute
        self.ecg_bpm = 60
        self.min_bpm = 40
        self.max_bpm = 300
        self.ecg_bpm_slider = wx.Slider(panel,-1,value=self.ecg_bpm,
                    minValue=self.min_bpm, maxValue=self.max_bpm,
                    pos=(AO_x_pos-50,AO_y_pos+130), size=(260,50),
                    style=wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS)
        self.ecg_bpm_slider.SetTickFreq(10,1)
        self.Bind(wx.EVT_SCROLL_THUMBRELEASE,self.on_bpm_slider_change,self.ecg_bpm_slider)

        #container for all controls related to ecg output
        self.ecg_controls = [self.ecg_bpm_slider]

        #turn ecg bpm slider off as default selection is sinewave output
        for control in self.ecg_controls:
            control.Hide()

        #buttons for selecting which channel the selected signal is applied to
        AO_button_y_pos = 640
        self.AO_buttons_label = wx.StaticText(panel,-1,'Output Channel Enable',
                        pos=(AO_x_pos,AO_button_y_pos))
        self.AO_buttons_label.SetFont(wx.Font(10,wx.DEFAULT,wx.NORMAL,wx.NORMAL))

        self.AO_CH0_button = wx.Button(panel,-1,'OFF',
                        pos=(AO_x_pos,AO_button_y_pos+20),size=(50,20))
        self.AO_CH0_button.SetBackgroundColour(STANDARD)
        self.AO_CH0_button.name = 'CH0'
        self.Bind(wx.EVT_BUTTON,self.on_AO_enable_click,self.AO_CH0_button)
        self.AO_CH0_button_label = wx.StaticText(panel,-1,'CH_0',
                        pos=(AO_x_pos+10,AO_button_y_pos+40))
        self.AO_CH0_button_label.SetFont(wx.Font(10,wx.DEFAULT,wx.NORMAL,wx.NORMAL))
        self.AO_CH0_running = False

        self.AO_CH1_button = wx.Button(panel,-1,'OFF',
                        pos=(AO_x_pos+100,AO_button_y_pos+20),size=(50,20))
        self.AO_CH1_button.SetBackgroundColour(STANDARD)
        self.AO_CH1_button.name = 'CH1'
        self.Bind(wx.EVT_BUTTON,self.on_AO_enable_click,self.AO_CH1_button)
        self.AO_CH1_button_label = wx.StaticText(panel,-1,'CH_1',
                        pos=(AO_x_pos+110,AO_button_y_pos+40))
        self.AO_CH1_button_label.SetFont(wx.Font(10,wx.DEFAULT,wx.NORMAL,wx.NORMAL))
        self.AO_CH1_running = False
        self.analog_output_thread_started = False

        self.AO_buttons = [self.AO_CH0_button,self.AO_CH1_button]
        #*****************************************************************


    def on_amplitude_spin_increase(self,event):
        new_value = float(self.amplitude_entry.GetValue())+.01
        if new_value > 10.0:
            new_value = 10.0
        self.amplitude_entry.SetValue('%s'%new_value)
        self.crappy_analog_output_method()

    def on_amplitude_spin_decrease(self,event):
        new_value = float(self.amplitude_entry.GetValue())-.01
        if new_value < 0.0:
            new_value = 0.0
        self.amplitude_entry.SetValue('%s'%new_value)
        self.crappy_analog_output_method()

    def on_amplitude_entered(self,event):
        new_value = float(self.amplitude_entry.GetValue())
        if new_value > 10.0:
            new_value = 10.0
        elif new_value < 0.0:
            new_value = 0.0
        self.amplitude_entry.SetValue('%.3f'%new_value)
        self.crappy_analog_output_method()

    def on_frequency_spin_increase(self,event):

        new_value = float(self.frequency_entry.GetValue())+1.0

        #if ecg(triangle wave) is selected ensure within upper limit
        if self.output_types.GetSelection() == 1:
            if new_value < self.max_bpm:
                self.frequency_entry.SetValue('%.1f'%new_value)
                self.ecg_bpm_slider.SetValue(new_value)
            else:
                self.frequency_entry.SetValue('%.1f'%self.max_bpm)
                self.ecg_bpm_slider.SetValue(max_bpm)

        #sinewave output was selected
        else:
            self.frequency_entry.SetValue('%.1f'%(float(self.frequency_entry.GetValue())+1.0))
            self.ecg_bpm_slider.SetValue('%.1f'%(float(self.frequency_entry.GetValue())+1.0))

        self.crappy_analog_output_method()

    def on_frequency_spin_decrease(self,event):
        new_value = float(self.frequency_entry.GetValue())-1.0
        if new_value < 0.0:
            new_value = 0.0
        self.frequency_entry.SetValue('%.1f'%new_value)
        self.ecg_bpm_slider.SetValue(new_value)
        self.crappy_analog_output_method()

    def on_frequency_entered(self,event):

        new_value = float(self.frequency_entry.GetValue())
        if new_value < 0.0:
            new_value = 0.0

            #ecg selected
            if new_value > self.max_bpm:
                self.frequency_entry.SetValue(".1f"%(self.max_bpm / 60.0))
            else:
                self.frequency_entry.SetValue(".1f"%(self.new_value / 60.0))
        else:
            #sinewave selected
            self.frequency_entry.SetValue('%.1f'%new_value)

        self.crappy_analog_output_method()


    def crappy_analog_output_method(self,event=None):
        try:
            if self.analog_output_thread_started == True:
                if self.debug: print "ending the previously started thread"
                self.analog_output_thread.End_Output()
                time.sleep(1) #pause for thread to end
                self.analog_output_thread_started = False

            if self.AO_CH0_button.GetLabel() == 'OFF':  #channel turned off
                if self.debug: print 'channel 0 detected off'
                a1 = self.generate_zeros_array()

            else:
                if self.output_types.GetSelection() == 0: #channel turned on and sinewave selected
                    if self.debug: print 'channel 0 sinewave'
                    a1 = self.generate_sinewave_array()
                else:
                    if self.debug: print 'channel 0 ecg'
                    a1 = self.generate_triangle_array()      #channel turned on and ecg selected

            if self.AO_CH1_button.GetLabel() == 'OFF':  #channel turned off
                if self.debug: print 'channel 1 detected off'
                a2 = self.generate_zeros_array()

            else:
                if self.output_types.GetSelection() == 0: #channel turned on and sinewave selected
                    if self.debug: print 'channel 1 sinewave'
                    a2 = self.generate_sinewave_array()
                else:
                    if self.debug: print 'channel 1 ecg'
                    a2 = self.generate_triangle_array()      #channel turned on and ecg selected

            if self.debug: print 'size of a1: ',len(a1)
            if self.debug: print 'size of a2: ',len(a2)
            _2D_array = numpy.array([a1,a2])
            self.analog_output_thread = pyNIDAQ.Analog_Output_Thread_Continuous('Dev1/ao0,Dev1/ao1',
                                        _2D_array,ANALOG_OUTPUT_SAMPLES_PER_SEC)
            self.analog_output_thread.start()
            self.analog_output_thread_started = True
            if self.debug: print 'analog output thread started'

        except Exception as e:
            print "Exception found in crappy_analog_output_method(): " + repr(e)
            raise e

    def generate_zeros_array(self):
        if self.output_types.GetSelection() == 0:
            #sinewave selected, use sinewave method to create an array, then zero out

            if self.debug: print 'creating zero array (sine method)'
            frequency = float(self.frequency_entry.GetValue())
            if self.debug: print 'sine frequency: ',frequency
            pk_amplitude = float(self.amplitude_entry.GetValue())
            if self.debug: print 'sine peak amplitude: ',pk_amplitude

            cycle_time = 2.0 * numpy.pi             #2*pi seconds, time for one complete sine wave cycle
            period = 1.0 / frequency        #store one period's worth of samples

            t = numpy.arange(0,period,1.0/float(ANALOG_OUTPUT_SAMPLES_PER_SEC)) #evenly spaced time intervals

            #zero out all array values
            for i in range(len(t)):
                t[i] = 0.0

            return t

        else:
            #ecg selected, use ecg method to create a zeroed out array

            if self.debug: print 'creating zero array (ecg method)'
            frequency = float(self.frequency_entry.GetValue()) / 60.0
            if self.debug: print 'ecg frequency: ',frequency
            pk_amplitude = float(self.amplitude_entry.GetValue())
            if self.debug: print 'ecg peak amplitude: ',pk_amplitude
            period = 1.0 / frequency

            array_size = int(round(period * ANALOG_OUTPUT_SAMPLES_PER_SEC))
            return numpy.zeros(array_size,dtype=numpy.float)

    def generate_sinewave_array(self):

        frequency = float(self.frequency_entry.GetValue())
        pk_amplitude = float(self.amplitude_entry.GetValue())

        cycle_time = 2.0 * numpy.pi             #2*pi seconds, time for one complete sine wave cycle
        period = 1.0 / frequency        #store one period's worth of samples
        t=numpy.arange(0,period,1.0/float(ANALOG_OUTPUT_SAMPLES_PER_SEC)) #evenly spaced time intervals

        if self.debug: print 'sinewave array size: ',len(t)

        return numpy.sin(frequency * cycle_time * t) * pk_amplitude

    def generate_triangle_array(self):
        frequency = float(self.frequency_entry.GetValue()) / 60.0
        if self.debug: print 'frequency: ',frequency
        pk_amplitude = float(self.amplitude_entry.GetValue())
        if self.debug: print 'peak amplitude: ',pk_amplitude
        period = 1.0 / frequency

        array_size = int(round(period * ANALOG_OUTPUT_SAMPLES_PER_SEC))
        if self.debug: print 'triangle array size: ',array_size
        a = numpy.zeros(array_size,dtype=numpy.float)

        num_rising_samples = int(round(0.04 * ANALOG_OUTPUT_SAMPLES_PER_SEC))
        if self.debug: print 'num rising samples: ',num_rising_samples
        step_volts = pk_amplitude / float(num_rising_samples)
        if self.debug: print 'step volts',step_volts

        #rising edge of triangle wave
        for i in range(1,num_rising_samples+1):
            a[i] = a[i-1]+step_volts

        #falling edge of triangle wave
        for i in range(num_rising_samples+1,(2*num_rising_samples)+1):
            a[i] = a[i-1]-step_volts

        return a

    def zero_AO_channel(self,channel):

        ao = pyNIDAQ.Analog_Output_Level(channel)
        ao.end()


    def on_AO_enable_click(self,event):
        button_name = event.GetEventObject().name
        if button_name == 'CH0':
            prev_state = self.AO_CH0_button.GetLabel()
            if prev_state == 'OFF':
                self.AO_CH0_button.SetLabel('ON')
                self.AO_CH0_button.SetBackgroundColour(GREEN)
            else:
                self.AO_CH0_button.SetLabel('OFF')
                self.AO_CH0_button.SetBackgroundColour(STANDARD)

        elif button_name == 'CH1':
            prev_state = self.AO_CH1_button.GetLabel()
            if prev_state == 'OFF':
                self.AO_CH1_button.SetLabel('ON')
                self.AO_CH1_button.SetBackgroundColour(GREEN)
            else:
                self.AO_CH1_button.SetLabel('OFF')
                self.AO_CH1_button.SetBackgroundColour(STANDARD)
        else:
            raise RuntimeError("Unknown button name found on AO button click: %s"%button_name)

        self.crappy_analog_output_method()

    def on_bpm_slider_change(self,event):
        self.frequency_entry.SetValue("%.1f"%(self.ecg_bpm_slider.GetValue()))
        self.crappy_analog_output_method()

    def on_AO_change(self,event):
        button_index = event.GetInt()

        if button_index == 0:
                    #sinewave selected

            #change frequency to Hz instead of bpm
            self.frequency_label.SetLabel("frequency(Hz)")
            self.frequency_entry.SetValue("%.1f"%(float(self.frequency_entry.GetValue()) / 60.0))

            for control in self.sinewave_controls:
                control.Show()
            for control in self.ecg_controls:
                control.Hide()

        else:
                    #ECG selected

            self.frequency_label.SetLabel("ecg bpm")
            frequency = float(self.frequency_entry.GetValue())

            #change frequency to bpm instead of Hz
            if frequency > (self.max_bpm / 60.0):
                self.frequency_entry.SetValue("%.1f"%self.max_bpm)
                self.ecg_bpm_slider.SetValue(self.max_bpm)
            else:
                self.frequency_entry.SetValue("%.1f"%(frequency * 60.0))
                self.ecg_bpm_slider.SetValue(frequency * 60.0)

            for control in self.ecg_controls:
                control.Show()

        self.crappy_analog_output_method()




    def on_DIO_click(self,event):

        button_name = event.GetEventObject().name.split("_")
        card = button_name[0]
        index = int(button_name[1])

        if card == '6251':
            if self.DIO_buttons_6251[index].GetBackgroundColour() == STANDARD:
                self.DIO_buttons_6251[index].SetBackgroundColour(GREEN)
                self.DIO_buttons_6251[index].SetLabel("ON")
                self.DO_lines_6251[index].write_state(1)
            else:
                self.DIO_buttons_6251[index].SetBackgroundColour(STANDARD)
                self.DIO_buttons_6251[index].SetLabel("OFF")
                self.DO_lines_6251[index].write_state(0)

        elif card == '6025':
            if self.DIO_buttons_6025[index].GetBackgroundColour() == STANDARD:
                self.DIO_buttons_6025[index].SetBackgroundColour(GREEN)
                self.DIO_buttons_6025[index].SetLabel("ON")
                self.DO_lines_6025[index].write_state(1)
            else:
                self.DIO_buttons_6025[index].SetBackgroundColour(STANDARD)
                self.DIO_buttons_6025[index].SetLabel("OFF")
                self.DO_lines_6025[index].write_state(0)

        else:
            raise RuntimeError("Unknown card number found on DIO button click: %s"%card)

    def OnTimer(self, event):
        #display of 6251 measurements
        for i in range(13):
            if i == 12:             #HVCAPS
                self.voltage_measurements_6251[i].SetValue("%4.0fV"%(displayed_values[i]))
            elif i in [5,6,7,10]:   #ripple measurements
                self.voltage_measurements_6251[i].SetValue("%5.0fmV"%(displayed_values[i]*1000.0))
            elif i == 3:            #Ibat
                self.voltage_measurements_6251[i].SetValue("%2.2fuA"%(displayed_values[i] / .025))
            elif i == 9:            #ISRC voltage converted to nA
                self.voltage_measurements_6251[i].SetValue("%.1fnA"%(displayed_values[i] * 100.0))
##                print 'measured: %.2f, calculated: %.2f'%(displayed_values[i],displayed_values[i]*100.0)
            elif i == 4:            #15V
                self.voltage_measurements_6251[i].SetValue("%.3fV"%(displayed_values[i]))
            else:                   #all others
                self.voltage_measurements_6251[i].SetValue("%.4fV"%(displayed_values[i]))

        #display of 6025 measurements
        for i in range(6):
            if i == 4:              #15V
                self.voltage_measurements_6025[i].SetValue("%.3fV"%(displayed_values[13+i]))
            elif i == 5:            #Ibat
                self.voltage_measurements_6025[i].SetValue("%2.2fuA"%(displayed_values[13+i] / 0.025))
            else:                   #all others
                self.voltage_measurements_6025[i].SetValue("%.4fV"%(displayed_values[13+i]))



class AI_Thread(threading.Thread):
    def __init__(self,start_index,DAQ_card=None,debug=False):
        threading.Thread.__init__(self)
        self.daemon = True
        self.DAQ_card = DAQ_card
        self.debug = debug
        self.start_index = start_index  #starting index in the main list of values to display
                                        #where the measurements being taken by this thread will
                                        #be placed... starts with all 6251 measurements, then 6025

        self.measurement = pyNIDAQ.AI_Voltage_Measurement()

    def add_measurement_channels(self,channels,minV=-10.0,maxV=10.0):
        if self.debug: print "adding channels"
        self.measurement.Add_Channels(channels,minV,maxV)

    def configure_sample_timing(self,sampleRate=1000.0,samples_per_channel=1000):
        if self.debug: print "configuring sample timing"
        self.measurement.Config_Sample_Clock(sampleRate,samples_per_channel)

    def run(self):
        """this main loop is running all the time
        """
        if self.debug: print "thread started"
        global displayed_values
        # displayed_values is the global list that contains all of the values to be displayed
        # on the user interface for analog voltage measurements. It consists of first the measurements
        # from the NI6251, then the measurements from the NI6025

        while(True):

            measured_samples = self.measurement.Take_Voltage_Measurement()

            #for each channel measured find the value for display

            if self.DAQ_card == '6251':

                for i in range(len(measured_samples)):
                    if i == 4:
                        #multiply 15V measurement by 10 since 10:1 divider is used on board
                        displayed_values[self.start_index+i] = numpy.average(measured_samples[i] * 10.0)

                    elif i in [5,6,7,10]:
                        #ripple measurements are mVpp
                        if self.debug: print '%d, max: %.4f min: %.4f, dif: %.4f'%(i,numpy.max(measured_samples[i]),
                                        numpy.min(measured_samples[i]),
                                        numpy.max(measured_samples[i])-numpy.min(measured_samples[i]))
                        displayed_values[self.start_index+i] = \
                            numpy.max(measured_samples[i]) - numpy.min(measured_samples[i])

                    elif i == 9:
                        #convert ISRC measurement to current
                        displayed_values[self.start_index+i] = numpy.average(measured_samples[i])

                    elif i == 12:
                        #multiply HVCAPS measurement by 1000 since 1000:1 divider used on board
                        displayed_values[self.start_index+i] = numpy.average(measured_samples[i] * 1000.0)

                    else:
                        #all other measurements from 6251 handled like this
                        displayed_values[self.start_index+i] = numpy.average(measured_samples[i])

            elif self.DAQ_card == '6025':

                for i in range(len(measured_samples)):
                    if i == 3:
                        #multiply 15V measurement by 10 since 10:1 divider is used on board
                        displayed_values[self.start_index+i] = numpy.average(measured_samples[i] * 10.0)

                    else:
                        #all other measurements from 6025 handled like this
                        displayed_values[self.start_index+i] = numpy.average(measured_samples[i])

def config_6251_AI_channels(ai):

    #VREF
    channels = "Dev1/ai0"
    ai.add_measurement_channels(channels,minV=-2.0,maxV=2.0)

    #2V2,1V8,Ibat
    channels = "Dev1/ai1,Dev1/ai2,Dev1/ai3"
    ai.add_measurement_channels(channels,minV=-5.0,maxV=5.0)

    #15V
    channels = "Dev1/ai4"
    ai.add_measurement_channels(channels,minV=-2.0,maxV=2.0)

    #ripple measurements for 2V2,1V8,15V
    channels = "Dev1/ai5,Dev1/ai6,Dev1/ai7"
    ai.add_measurement_channels(channels,minV=-0.5,maxV=0.5)

    #TPECG,ISRC
    channels = "Dev1/ai8,Dev1/ai9"
    ai.add_measurement_channels(channels,minV=-2.0,maxV=2.0)

##    #ISRC
##    channels = "Dev1/ai9"
##    ai.add_measurement_channels(channels,minV=-5.0,maxV=5.0)

    #ripple measurement for VREF
    channels = "Dev1/ai10"
    ai.add_measurement_channels(channels,minV=-0.5,maxV=0.5)

    #VBAT
    channels = "Dev1/ai11"
    ai.add_measurement_channels(channels,minV=-10.0,maxV=10.0)

    #HVDIV
    channels = "Dev1/ai12"
    ai.add_measurement_channels(channels,minV=-2.0,maxV=2.0)



def config_6025_AI_channels(ai):

    #VREF
    channels = "Dev2/ai0"
    ai.add_measurement_channels(channels,minV=-2.0,maxV=2.0)

    #2V2,1V8
    channels = "Dev2/ai1,Dev2/ai2"
    ai.add_measurement_channels(channels,minV=-5.0,maxV=5.0)

    #15V
    channels = "Dev2/ai3"
    ai.add_measurement_channels(channels,minV=-2.0,maxV=2.0)

    #channels in +/- 10V range
    channels = "Dev2/ai4"
    ai.add_measurement_channels(channels,minV=-10.0,maxV=10.0)

    #Ibat
    channels = "Dev2/ai5"
    ai.add_measurement_channels(channels,minV=-5.0,maxV=5.0)



def create_DO_channels():
    digital_lines_6251 = []
    digital_lines_6025 = []

    for line in range(8):
        ch = pyNIDAQ.digital_output_channel('Dev1','0',line)
        ch.write_state(0)
        digital_lines_6251.append(ch)

    for port in range(4):
        for line in range(8):
            ch = pyNIDAQ.digital_output_channel('Dev2',port,line)
            ch.write_state(0)
            digital_lines_6025.append(ch)

    return (digital_lines_6251,digital_lines_6025)







if __name__ == '__main__':
    #******************************************************
    #*****GLOBAL VARIABLES*********************************
    global displayed_values
    displayed_values = list()
    for i in range(13+6): displayed_values.append(0.0)
    R_ISRC = 1E7
    #********************************************************

    ai_thread_6251 = AI_Thread(0,DAQ_card='6251')
    ai_thread_6025 = AI_Thread(13,DAQ_card='6025')
    digital_output_lines = create_DO_channels()

    config_6251_AI_channels(ai_thread_6251)
    ai_thread_6251.configure_sample_timing(sampleRate=ANALOG_INPUT_SAMPLES_PER_SEC,
                                samples_per_channel=ANALOG_INPUT_SAMPLES_PER_CHANNEL)
    ai_thread_6251.start()

    config_6025_AI_channels(ai_thread_6025)
    ai_thread_6025.configure_sample_timing(sampleRate=ANALOG_INPUT_SAMPLES_PER_SEC,
                                samples_per_channel=ANALOG_INPUT_SAMPLES_PER_CHANNEL)
    ai_thread_6025.start()

    app = wx.App()
    frame = ATE_manual_control_frame(None, -1, digital_output_lines)
    frame.Show(True)
    app.SetTopWindow(frame)


    app.MainLoop()