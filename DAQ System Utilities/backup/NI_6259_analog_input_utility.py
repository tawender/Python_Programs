import time
import wx
import wx.gizmos as gizmos
import threading
import numpy
import sys
import os.path
sys.path.append("T:\python programs\modules")
import pyNIDAQ


class DAQ_utility_frame(wx.Frame):
    """
    create frame with the necessary controls and display
    """
    def __init__(self, parent, id):
        self.debug = False
        pos = wx.DefaultPosition
        wx.Frame.__init__(self, None, -1, title='NI DAQ Utility USB-6259',
                          size=(810,600))
        panel = wx.Panel(self,-1)

        self.led = gizmos.LEDNumberCtrl(panel, -1, pos=(50,200),
                                        size=(550,120))
        self.led.SetBackgroundColour("black")
        self.led.SetForegroundColour("red")
        if self.debug: print "7-segment display done"


        device_buttons_list = ['PCI-6251M', 'PCI-6025E', 'USB-6259']
        self.devices_RadioBox = wx.RadioBox(panel, -1, "DAQ Device", (218, 350), wx.DefaultSize,
                        device_buttons_list, 2, wx.RA_SPECIFY_COLS)
        self.Bind(wx.EVT_RADIOBOX, self.on_device_change, self.devices_RadioBox)
        if self.debug: print "DAQ card buttons done"

        channel_buttons_list = ['0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15']
        self.channels_RadioBox = wx.RadioBox(panel, -1, "Channel", (400, 350), wx.DefaultSize,
                        channel_buttons_list, 2, wx.RA_SPECIFY_COLS)
        self.Bind(wx.EVT_RADIOBOX, self.on_channel_change, self.channels_RadioBox)
        if self.debug: print "channel select buttons done"


        gain_buttons_list = ['+/- 10V','+/- 5V','+/- 2V','+/- 1V','+/- 0.5V','+/- 0.2V','+/- 0.1V','+/- 0.05V']
        self.gains_RadioBox = wx.RadioBox(panel, -1, "Channel Gain", (518, 350), wx.DefaultSize,
                        gain_buttons_list, 1, wx.RA_SPECIFY_COLS)
        self.Bind(wx.EVT_RADIOBOX, self.on_gain_change, self.gains_RadioBox)
        if self.debug: print "gain select buttons done"


        t1 = wx.StaticText(panel, -1, "Analog Input Voltage", pos=(180,150))
        font = wx.Font(25,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        t1.SetFont(font)
        t2 = wx.StaticText(panel, -1, "Volts", pos=(610,250))
        font = wx.Font(50,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        t2.SetFont(font)
        t3 = wx.StaticText(panel, -1, "Data Acquisition Card Measurement Utility", pos=(22,20))
        font = wx.Font(31,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        t3.SetFont(font)
        if self.debug: print "window text done"

        #disable +/-.05V selection for initial 6251 card selection
        self.gains_RadioBox.EnableItem(7,False)

        self.OnTimer(None)
        self.timer = wx.Timer(self, -1)
        # update clock digits every second (1000ms)
        self.timer.Start(1000)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

        self.setup_for_only_6259_installed()

        if self.debug: print "__init__ done"

    def setup_for_only_6259_installed(self):
        """
        this is the code change that will allow the program to run on a system
        that only has a USB-6259 installed
        """
        #grey out uninstalled choices
        self.devices_RadioBox.EnableItem(0,False)
        self.devices_RadioBox.EnableItem(1,False)

        #select the 6259 choice
        self.devices_RadioBox.SetSelection(2)

        self.update_channel_labels_to_6259()

        global measurement_type
        measurement_type = 'DIFF'


    def on_device_change(self,event):
        global measurement_type
        button_index = event.GetInt()

        if button_index in [0,2]:      #6251 or 6259 selected

            #selected gain invalid for 6251, disable and change selection to +/-10V
            if self.gains_RadioBox.GetSelection() == 7:
                self.gains_RadioBox.SetSelection(0)

            self.gains_RadioBox.EnableItem(7,False)
            self.gains_RadioBox.EnableItem(2,True)
            self.gains_RadioBox.EnableItem(3,True)
            self.gains_RadioBox.EnableItem(5,True)
            self.gains_RadioBox.EnableItem(6,True)

            if button_index == 2:   #6259 selected
                measurement_type = 'DIFF'
                self.update_channel_labels_to_6259()
            else:
                measurement_type = 'NRSE'
                self.update_channel_labels_from_6259()

        if button_index == 1:      #6025 selected

            #selected gain invalid for 6025, disable and change selection to +/-10V
            if self.gains_RadioBox.GetSelection() in [2,3,5,6]:
                self.gains_RadioBox.SetSelection(0)

            self.gains_RadioBox.EnableItem(2,False)
            self.gains_RadioBox.EnableItem(3,False)
            self.gains_RadioBox.EnableItem(5,False)
            self.gains_RadioBox.EnableItem(6,False)
            self.gains_RadioBox.EnableItem(7,True)

            measurement_type = 'NRSE'

            self.update_channel_labels_from_6259()

        self.update_channel_settings()


    def on_channel_change(self,event):
        self.update_channel_settings()

    def on_gain_change(self,event):
        self.update_channel_settings()

    def update_channel_settings(self):

        devices_list = ['Dev1','Dev2','Dev3']
        global device
        device = 'Dev1'

        global channel
        #the USB-6259('Dev3') numbers its 16 differential channels 0-7,16-23 instead of 0-16
        if (self.channels_RadioBox.GetSelection() > 7):
            channel = 'ai' + "%s"%(self.channels_RadioBox.GetSelection()+8)
        else:
            channel = 'ai' + "%s"%(self.channels_RadioBox.GetSelection())

##        device = devices_list[self.devices_RadioBox.GetSelection()]
##
##        global channel
##        #the USB-6259('Dev3') numbers its 16 differential channels 0-7,16-23 instead of 0-16
##        if (device is 'Dev3') and (self.channels_RadioBox.GetSelection() > 7):
##            channel = 'ai' + "%s"%(self.channels_RadioBox.GetSelection()+8)
##        else:
##            channel = 'ai' + "%s"%(self.channels_RadioBox.GetSelection())

        minV_list = [-10.0,-5.0,-2.0,-1.0,-0.5,-0.2,-0.1,-0.05]
        maxV_list = [10.0,5.0,2.0,1.0,0.5,0.2,0.1,0.05]
        gain_index = self.gains_RadioBox.GetSelection()
        global minV
        minV = minV_list[gain_index]
        global maxV
        maxV = maxV_list[gain_index]

        global reconfigure_channel
        reconfigure_channel = True

    def update_channel_labels_to_6259(self):
        for i in range(8,16):
            self.channels_RadioBox.SetItemLabel(i,"%s"%(i+8))

    def update_channel_labels_from_6259(self):
        for i in range(8,16):
            self.channels_RadioBox.SetItemLabel(i,"%s"%i)


    def OnTimer(self, event):

        self.led.SetValue("%9.6f"%measured_value)



class AI_Thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.debug = False

    def configure_measurement_channel(self):
        if self.debug:
            print "configuring channel"
            print "device: " + repr(device)
            print "channel: " + repr(channel)
            print "minV: " + repr(minV)
            print "maxV: " + repr(maxV)
            print "measurement type: " + repr(measurement_type)

        sampleRate = 10000.0
        num_samples_to_acquire = 10000
        readTimeout = 2.0

        self.measurement = pyNIDAQ.AI_Voltage_Channel()
        self.measurement.Config_Finite_Voltage_Measurement(device,channel,minV,maxV,
                                                     sampleRate,num_samples_to_acquire,
                                                     meas_type=measurement_type)

        global reconfigure_channel
        reconfigure_channel = False

    def run(self):
        """this main loop is running all the time
        """
        if self.debug: print "thread started"
        while(True):

            if reconfigure_channel:
                self.configure_measurement_channel()

            global measured_value
            measured_value = numpy.average(self.measurement.Take_Voltage_Measurement())
            if self.debug: print measured_value




if __name__ == '__main__':
    #******************************************************
    #*****GLOBAL VARIABLES*********************************
    global counter
    counter = 0.0001
    global minV
    minV = -10.0
    global maxV
    maxV = 10.0
    global device
    device = "Dev1"
    global measurement_type
    measurement_type = 'NRSE'
    global channel
    channel = "ai0"
    global reconfigure_channel
    reconfigure_channel = True
    global measured_value
    measured_value = 0.0
    #********************************************************


    app = wx.App()
    frame = DAQ_utility_frame(None, -1)
    frame.Show(True)
    app.SetTopWindow(frame)

    ai_thread = AI_Thread()
    ai_thread.start()

    app.MainLoop()