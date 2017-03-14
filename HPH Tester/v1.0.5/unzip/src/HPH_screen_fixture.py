import os
import sys
import optparse
import wx
import time
import Queue
import threading
import logging
import cv2
from cv2 import cv as cv

import HPH_vbat_caps_contact_resistance as testscript

TEXTBOX_SIZE = (45,-1)

myEVT_meas_ready = wx.NewEventType()
EVT_MEAS_READY = wx.PyEventBinder(myEVT_meas_ready, 1)

myEVT_meas_done = wx.NewEventType()
EVT_MEAS_DONE = wx.PyEventBinder(myEVT_meas_done, 1)

myEVT_test_started = wx.NewEventType()
EVT_TEST_STARTED = wx.PyEventBinder(myEVT_test_started, 1)

myEVT_all_tests_completed = wx.NewEventType()
EVT_ALL_TESTS_COMPLETED = wx.PyEventBinder(myEVT_all_tests_completed, 1)

myEVT_abort_looptesting = wx.NewEventType()
EVT_ABORT_LOOPTESTING = wx.PyEventBinder(myEVT_abort_looptesting, 1)

myEVT_invalid_test = wx.NewEventType()
EVT_INVALID_TEST = wx.PyEventBinder(myEVT_invalid_test, 1)

myEVT_probe_check = wx.NewEventType()
EVT_PROBE_CHECK = wx.PyEventBinder(myEVT_probe_check, 1)


class ProbeCheckEvent(wx.PyCommandEvent):
    """Event to signal that the pre-test probe check is starting"""
    def __init__(self, etype, eid):
        wx.PyCommandEvent.__init__(self, etype, eid)

    def get_value(self):
        pass

class MeasurementReadyEvent(wx.PyCommandEvent):
    """Event to signal that a measurement is ready"""
    def __init__(self, etype, eid, value):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def get_value(self):
        """Returns the value from the event"""
        return self._value

class MeasurementsDoneEvent(wx.PyCommandEvent):
    """Event to signal that all measurements have been completed"""
    def __init__(self, etype, eid):
        wx.PyCommandEvent.__init__(self, etype, eid)

    def get_value(self):
        pass

class MeasurementsStartedEvent(wx.PyCommandEvent):
    """Event to signal that a test has been requested and started"""
    def __init__(self, etype, eid):
        wx.PyCommandEvent.__init__(self, etype, eid)

    def get_value(self):
        pass

class AllMeasurementsCompletedEvent(wx.PyCommandEvent):
    """Event to signal that all requested measurements have been completed"""
    def __init__(self, etype, eid):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self.message = None

    def get_value(self):
        return self.message

    def set_message(self,m):
        self.message = m

class AbortLooptestingEvent(wx.PyCommandEvent):
    """Event to signal that current looptesting in progress is being aborted"""
    def __init__(self, etype, eid):
        wx.PyCommandEvent.__init__(self, etype, eid)

    def get_value(self):
        pass

class InvalidTestEvent(wx.PyCommandEvent):
    """Event to signal that in invalid reading has occurred during resistance test"""
    def __init__(self, etype, eid):
        wx.PyCommandEvent.__init__(self, etype, eid)

    def get_value(self):
        pass

##class SendSensePogoTestCommandThread(threading.Thread):
##    """thread to send the run_sense_pogo_test() command to module responsible
##       for operating test equipment"""
##    def __init__(self,HPH_tester,sense_pogo_check_q):
##        try:
##            threading.Thread.__init__(self)
##            self.daemon = True
##            self.HPH_tester = HPH_tester
##            self.sense_pogo_check_q = sense_pogo_check_q
##
##        except Exception as e:
##            print "Exception in SendSensePogoTestcommandThread.init(): " + repr(e)
##            raise e
##
##    def run(self):
##        try:
##            self.HPH_tester.run_sense_pogo_test(self.sense_pogo_check_q)
##
##
##        except Exception as e:
##            print "Exception in RunSensePogoCheckThread.run(): " + repr(e)
##            raise e

class RunTestsCommandThread(threading.Thread):
    """thread to send the run_tests command to the module responsible for operating test equipment"""
    def __init__(self,HPH_tester,sn,meas_q,pf_results_q,test_started_q,abort_q):
        try:
            threading.Thread.__init__(self)
            self.daemon = True
            self.HPH_tester = HPH_tester
            self.sn = sn
            self.meas_q = meas_q
            self.pf_results_q = pf_results_q
            self.test_started_q = test_started_q
            self.abort_q = abort_q

        except Exception as e:
            print "Exception in RunTestsCommandThread.init(): " + repr(e)
            raise e

    def run(self):
        try:
            self.HPH_tester.run_tests(self.sn,self.meas_q,self.pf_results_q,
                                        self.test_started_q,self.abort_q)

        except Exception as e:
            print "Exception in RunTestsCommandThread.run(): " + repr(e)
            raise e

class MeasurementThread(threading.Thread):
    """Thread to keep the GUI responsive to user input, respond to measurement results, and
       post events when the script running tests populates the appropriate queues"""
    def __init__(self,parent,sn,HPH_tester,pass_fail_results_q,debug,GUI_frame):
        try:
            threading.Thread.__init__(self)
            self.daemon = True
            self.parent = parent
            self.GUI_frame = GUI_frame
            self.sn = sn
            self.HPH_tester = HPH_tester
            self.pass_fail_results_q  = pass_fail_results_q
            self.debug = debug
            self.measurement_q = Queue.Queue()
            self.test_started_q = Queue.Queue()
            self.abort_looptesting_q = Queue.Queue()

        except Exception as e:
            print "Exception in __init__ of MeasurementThread(): " + repr(e)
            raise e

    def run(self):
        try:
            if self.HPH_tester.get_run_sense_check():

                #post a ProbeCheckEvent so that the screen is cleared out of previous results
                evt = ProbeCheckEvent(myEVT_probe_check,-1)
                wx.PostEvent(self.parent,evt)

                ret = self.HPH_tester.run_sense_pogo_test(self.sn)
                if ret[0] is 'FAIL':

                    if self.debug: print "sense pogo test FAIL"
                    msgbox = wx.MessageDialog(self.parent, "DUT failed continuity test of sense pogo pins.\n" \
                                    + "%s measures %.2fohms"%(ret[1],ret[2]),
                                    "Test Fixture Error",style=wx.OK)
                    msgbox.ShowModal()
                    evt = AllMeasurementsCompletedEvent(myEVT_all_tests_completed,-1)
                    evt.set_message("Failed test probe continuity test(%s = %.2fohms)"%(ret[1],ret[2]))
                    wx.PostEvent(self.parent,evt)
                    return

                elif ret[0] is 'ERROR':
                    if self.debug: print "sense pogo test ERROR"
                    evt = MeasurementsDoneEvent(myEVT_meas_done,-1)
                    wx.PostEvent(self.parent,evt)
                    raise RuntimeError("Error measuring sense pogo pin contact resistance. Refer to test log for details.")

                else:
                    if self.debug: print "sense pogo test PASSED"


            if self.HPH_tester.get_looptesting():
                num_loops = self.HPH_tester.get_num_loops()
            else:
                num_loops = 1

            t = RunTestsCommandThread(self.HPH_tester,self.sn,
                                            self.measurement_q,
                                            self.pass_fail_results_q,
                                            self.test_started_q,
                                            self.abort_looptesting_q)
            t.start()

            for i in range(num_loops):


###****************************
###see if this can be deleted
##                if self.debug and self.HPH_tester.get_looptesting():
##                    current_loopnum = self.HPH_tester.get_current_loop_num()
###****************************

                #monitor queue for indication that test has started
                while self.test_started_q.empty() and self.abort_looptesting_q.empty():
                    time.sleep(0.1)

                #see if above loop was exited because of abort
                if not self.abort_looptesting_q.empty():
                    #post event, empty queue and exit if while loop exited because of user abort
                    evt = AbortLooptestingEvent(myEVT_abort_looptesting,-1)
                    wx.PostEvent(self.parent,evt)
                    self.abort_looptesting_q.get()
                    return

                #while loop exited so post that event
                evt = MeasurementsStartedEvent(myEVT_test_started,-1)
                wx.PostEvent(self.parent,evt)
                self.test_started_q.get()


                #get all 6 joint resistance results as they are placed in the queue
                num_results = 0
                while num_results < 6:

                    while self.measurement_q.empty():
                        time.sleep(0.2)

                    num_results += 1
                    evt = MeasurementReadyEvent(myEVT_meas_ready,-1,self.measurement_q.get())
                    wx.PostEvent(self.parent,evt)


                #wait for the pass/fail result to be ready on the queue
                while self.pass_fail_results_q.empty():
                    time.sleep(0.2)
                ret = self.pass_fail_results_q.get()

                #queue will contain 'INVALID' if checking for resistance measurements
                #indicative of test fixture probe contact problems
                if ret == 'INVALID':
                    evt = InvalidTestEvent(myEVT_invalid_test,-1)
                    wx.PostEvent(self.parent,evt)

                    #on an invalid result during looptesting only halt on first iteration
                    if self.HPH_tester.get_looptesting():
                        loop_number = self.GUI_frame.get_loop_number()
                        print '(Inside measurement thread run() )current test loop number: %d'%(loop_number)
                        if loop_number is 1:
                            if self.debug: print "MEASUREMENT THREAD: invalid measurement on first loop iteration"
                            return
                        else:
                            if self.debug: print "MEASUREMENT THREAD: invalid measurement after first loop iteration"
                else:
                    evt = MeasurementsDoneEvent(myEVT_meas_done,-1)
                    wx.PostEvent(self.parent,evt)

            evt = AllMeasurementsCompletedEvent(myEVT_all_tests_completed,-1)
            wx.PostEvent(self.parent,evt)

        except Exception as e:
            print "Exception in MeasurementThread run(): " + repr(e)
            raise e



class TransparentText(wx.StaticText):
    def __init__(self, parent, id=wx.ID_ANY, label='',
               pos=wx.DefaultPosition, size=wx.DefaultSize,
               style=wx.TRANSPARENT_WINDOW, name='transparenttext'):
        wx.StaticText.__init__(self, parent, id, label, pos, size, style, name)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_paint(self, event):
        bdc = wx.PaintDC(self)
        dc = wx.GCDC(bdc)

        font_face = self.GetFont()
        font_color = self.GetForegroundColour()

        dc.SetFont(font_face)
        dc.SetTextForeground(font_color)
        dc.DrawText(self.GetLabel(), 0, 0)

    def on_size(self, event):
        self.Refresh()
        event.Skip()



class WebcamCapture(wx.Panel):
    def __init__(self, parent, ID,debug=False, fps=30):
        try:
            wx.Panel.__init__(self, parent)

            self.debug = debug

            self.capture = cv2.VideoCapture(0)
            self.capture2 = cv2.VideoCapture(1)

            if self.debug: print 'cam1: ',self.capture,'  type:',type(self.capture)
            if self.debug: print 'cam2: ',self.capture2,'  type:',type(self.capture2)


            wid = self.capture.get(cv.CV_CAP_PROP_FRAME_WIDTH)
            ht = self.capture.get(cv.CV_CAP_PROP_FRAME_HEIGHT)

            if self.debug: print 'initial image width: ',wid
            if self.debug: print 'initial image height: ',ht

            scale = 0.86
            self.cam_border = 10

            if self.debug:
                print "scale factor is %.2f"%(scale)
                print "image width set to scaled size of %d"%(scale*wid)
                print "image height set to scaled size of %d"%(scale*ht)

            self.capture.set(cv.CV_CAP_PROP_FRAME_WIDTH, scale*wid)
            self.capture.set(cv.CV_CAP_PROP_FRAME_HEIGHT, scale*ht)
            self.capture2.set(cv.CV_CAP_PROP_FRAME_WIDTH, scale*wid)
            self.capture2.set(cv.CV_CAP_PROP_FRAME_HEIGHT, scale*ht)

            wid = self.capture.get(cv.CV_CAP_PROP_FRAME_WIDTH)
            ht = self.capture.get(cv.CV_CAP_PROP_FRAME_HEIGHT)

            if self.debug:
                print 'actual image width: ',wid
                print 'actual image height: ',ht
                print "cam border size: %d"%(self.cam_border)
                print "frame size should be set to width:%d, height:%d"%(
                                wid+(2*self.cam_border),(2*ht)+(3*self.cam_border))

            self.frame_size = (wid+(2*self.cam_border),(2*ht)+(3*self.cam_border))


            ret, frame = self.capture.read()
            ret2, frame2 = self.capture2.read()

            if self.debug: print 'frame1 type: ',type(frame)
            if self.debug: print 'frame2 type: ',type(frame2)

            if self.debug: print "frame background color: ",self.GetBackgroundColour()
            if self.debug: print "frame size: ",self.GetSize()
            self.SetSize(self.frame_size)
            if self.debug: print "frame size: ",self.GetSize()

            if (frame is None) and (frame2 is None):
                if self.debug: print 'Invalid frame captures from both cams... not using cams in GUI'

            else:
                if self.debug: print 'Valid frames captured from both cams... using images in GUI'

                self.height, self.width = frame.shape[:2]
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)

                self.bmp = wx.BitmapFromBuffer(self.width, self.height, frame)
                self.bmp2 = wx.BitmapFromBuffer(self.width, self.height, frame2)

                self.timer = wx.Timer(self)
                self.timer.Start(1000./fps)

                self.Bind(wx.EVT_PAINT, self.OnPaint)
                self.Bind(wx.EVT_TIMER, self.NextFrame)


        except Exception as e:
            print "Exception in ShowCapture.__init__(): " + repr(e)
            raise e


    def OnPaint(self, evt):
        try:
            dc = wx.BufferedPaintDC(self)
            r=dc.DrawRectangle(x=0, y=0, width=self.width+self.cam_border*2, height=2*self.height+3*self.cam_border)
            dc.DrawBitmap(self.bmp, self.cam_border, self.cam_border)
            dc.DrawBitmap(self.bmp2, self.cam_border, self.height+(2*self.cam_border))

        except Exception as e:
            print "Exception in OnPaint(): " + repr(e)
            raise e

    def NextFrame(self, event):
        try:
            #get image from first cam
            ret, frame = self.capture.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.bmp.CopyFromBuffer(frame)

            #get image from second cam
            ret2, frame = self.capture2.read()
            if ret2:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.bmp2.CopyFromBuffer(frame)

            #if image from first and second cams were good refresh screen
            if ret and ret2:
                self.Refresh(False)

        except Exception as e:
            print "Exception in NextFrame(): " + repr(e)
            raise e

    def get_frame_size(self):
        return self.frame_size

class DUTControlBox(wx.Panel):
    """
    """

    def __init__(self, parent, ID, HPH_tester,DUT_reporting_info,debug,GUI_frame):
        wx.Panel.__init__(self, parent, ID)

        self.debug = debug
        self.GUI_frame = GUI_frame
        self.parent = parent
        self.HPH_tester = HPH_tester
        self.DUT_reporting_info_controls = DUT_reporting_info
        self.result_index = 0
        self.pass_fail_results_q = Queue.Queue()

        box = wx.StaticBox(self, -1, "Device Under Test")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.label1 = wx.StaticText(self, -1, "DUT s/n")
        self.sn_txtb = wx.TextCtrl(self, -1, size=TEXTBOX_SIZE,style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_sn_enter,self.sn_txtb)

        self.run_button = wx.Button(self, -1, "TEST HPH", size=(150,50))
        self.Bind(wx.EVT_BUTTON, self.on_run, self.run_button)

        self.label2 = wx.StaticText(self, -1, "Test Operator")
        self.operator_txtb = wx.TextCtrl(self, -1, size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.operator_name = ""#self.HPH_tester.get_operator_name()
        self.operator_txtb.SetValue(self.operator_name)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_operator_enter,self.operator_txtb)
        self.operator_txtb.Bind(wx.EVT_KILL_FOCUS, self.on_operator_enter)

        row1 = wx.BoxSizer(wx.HORIZONTAL)
        row1.Add(self.label1)
        row1.Add(self.sn_txtb)

        sizer.AddSpacer(5)
        sizer.Add(row1, 0, wx.LEFT|wx.RIGHT, 10)
        sizer.AddSpacer(5)
        sizer.Add(self.run_button, 0, wx.LEFT|wx.RIGHT, 10)
        sizer.AddSpacer(5)
        sizer.Add(self.label2, 0, wx.LEFT|wx.RIGHT, 10)
        sizer.AddSpacer(2)
        sizer.Add(self.operator_txtb, 0, wx.LEFT|wx.RIGHT, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.run_button_recently_disabled = False
        self.sn_txtb_recently_disabled = False
        self.operator_name_recently_disabled = False



    def get_sn(self):
        return self.sn_txtb.GetValue()

    def on_operator_enter(self, event):
        new_name = self.operator_txtb.GetValue().replace(","," ").replace("  "," ")

        #if the name has not changed exit
        if new_name == self.operator_name:
            return

        self.operator_name = new_name
        self.HPH_tester.set_operator_name(self.operator_name)

    def on_sn_enter(self, event):
        self.start_test()

    def on_run(self, event):
        self.start_test()


    def start_test(self):
        try:
            #no serial number entered
            if self.sn_txtb.GetValue() == "":
                msgbox = wx.MessageDialog(self, "Enter a device serial number","Incomplete Test Information",
                                    style=wx.OK)
                msgbox.ShowModal()
                self.sn_txtb.SetFocus()
                return

            #no operator entered
            if self.operator_txtb.GetValue() == "":
                msgbox = wx.MessageDialog(self, "Enter an operator name","Incomplete Test Information",
                                    style=wx.OK)
                msgbox.ShowModal()
                self.operator_txtb.SetFocus()
                return


            if self.DUT_reporting_info_controls.create_DUT_report():

                #no DUT part number entered
                if self.DUT_reporting_info_controls.get_DUT_pn() == "":
                    msgbox = wx.MessageDialog(self, "Enter a DUT part number in the\nDUT Reporting section","Incomplete Test Information",
                                        style=wx.OK)
                    msgbox.ShowModal()
                    self.DUT_reporting_info_controls.pn_SetFocus()
                    return

                #no DUT revision entered
                if self.DUT_reporting_info_controls.get_DUT_rev() == "":
                    msgbox = wx.MessageDialog(self, "Enter a DUT revision in the\nDUT Reporting section","Incomplete Test Information",
                                        style=wx.OK)
                    msgbox.ShowModal()
                    self.DUT_reporting_info_controls.rev_SetFocus()
                    return

                #no DUT lot number entered
                if self.DUT_reporting_info_controls.get_DUT_ln() == "":
                    msgbox = wx.MessageDialog(self, "Enter a DUT Lot number in the\nDUT Reporting section","Incomplete Test Information",
                                        style=wx.OK)
                    msgbox.ShowModal()
                    self.DUT_reporting_info_controls.ln_SetFocus()
                    return

                #no Reason Code selected
                if self.DUT_reporting_info_controls.get_reason() == "":
                    msgbox = wx.MessageDialog(self, "Select a Test Reason Code in the\nDUT Reporting section","Incomplete Test Information",
                                        style=wx.OK)
                    msgbox.ShowModal()
                    self.DUT_reporting_info_controls.reason_SetFocus()
                    return

                #no test location selected
                if self.DUT_reporting_info_controls.get_location() == "":
                    msgbox = wx.MessageDialog(self, "Select a Test Location in the\nDUT Reporting section","Incomplete Test Information",
                                        style=wx.OK)
                    msgbox.ShowModal()
                    self.DUT_reporting_info_controls.location_SetFocus()
                    return

            t=MeasurementThread(self,self.sn_txtb.GetValue(),
                                self.HPH_tester,self.pass_fail_results_q,
                                self.debug,self.GUI_frame)
            t.start()

        except Exception as e:
            print "Exception in start_test(): " + repr(e)
            raise e

    def get_loop_number(self):
        return self.parent.get_loop_number()

    def prep_for_next_test(self):
        self.sn_txtb.SetValue("")
        self.sn_txtb.SetFocus()

    def disable_controls_during_test(self):
        """disable controls while test is running to prevent changes"""
        if self.run_button.IsEnabled():
            self.run_button.Enable(False)
            self.run_button_recently_disabled = True

        if self.sn_txtb.IsEnabled():
            self.sn_txtb.Enable(False)
            self.sn_txtb_recently_disabled = True

        if self.operator_txtb.IsEnabled():
            self.operator_txtb.Enable(False)
            self.label2.Enable(False)
            self.operator_name_recently_disabled = True

    def enable_controls_after_test(self):
        """enable controls that were disabled during test"""
        if self.run_button_recently_disabled:
            self.run_button.Enable(True)
            self.run_button_recently_disabled = False

        if self.sn_txtb_recently_disabled:
            self.sn_txtb.Enable(True)
            self.sn_txtb_recently_disabled = False

        if self.operator_name_recently_disabled:
            self.operator_txtb.Enable(True)
            self.label2.Enable(True)
            self.operator_name_recently_disabled = False

class DUT_ReportControlBox(wx.Panel):
    """
    """
    def __init__(self, parent, ID, HPH_tester):
        wx.Panel.__init__(self, parent, ID)

        self.HPH_tester = HPH_tester

        box = wx.StaticBox(self, -1, "DUT Reporting")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.report_cb = wx.CheckBox(self, -1, "Create individual DUT Report")
        self.report_cb.SetValue(self.HPH_tester.get_create_DUT_report())

        self.label1 = wx.StaticText(self, -1, "     DUT P/N")
        self.DUT_pn_txtb = wx.TextCtrl(self, -1, size=(80,-1), style=wx.TE_PROCESS_ENTER)
        self.DUT_pn = ""

        self.label2 = wx.StaticText(self, -1, "            DUT REV")
        self.DUT_rev_txtb = wx.TextCtrl(self, -1, size=(25,-1), style=wx.TE_PROCESS_ENTER)
        self.DUT_rev = ""

        self.label3 = wx.StaticText(self, -1, "                DUT L/N")
        self.DUT_ln_txtb = wx.TextCtrl(self, -1, size=(140,-1), style=wx.TE_PROCESS_ENTER)
        self.DUT_ln = ""

        self.reason_label = wx.StaticText(self, -1, "Reason Code")
        self.reason_choices = ["Production","Eng Test","Golden Device","Retest Per MI","NCMR Retest"]
        self.reason_choice = wx.Choice(self, -1,size=(80,-1),choices=self.reason_choices)
        self.reason = ""

        self.loc_label = wx.StaticText(self, -1, "Test Location")
        self.loc_choices = ["SCL","STP","INT. RECTIFIER"]
        self.loc_choice = wx.Choice(self, -1,size=(80,-1),choices=self.loc_choices)
        self.location = ""

        self.Bind(wx.EVT_CHECKBOX, self.on_report_cb, self.report_cb)

        self.Bind(wx.EVT_TEXT_ENTER, self.on_pn_entered,self.DUT_pn_txtb)
        self.DUT_pn_txtb.Bind(wx.EVT_KILL_FOCUS, self.on_pn_entered)

        self.Bind(wx.EVT_TEXT_ENTER, self.on_rev_entered,self.DUT_rev_txtb)
        self.DUT_rev_txtb.Bind(wx.EVT_KILL_FOCUS, self.on_rev_entered)

        self.Bind(wx.EVT_TEXT_ENTER, self.on_ln_entered,self.DUT_ln_txtb)
        self.DUT_ln_txtb.Bind(wx.EVT_KILL_FOCUS, self.on_ln_entered)

        self.Bind(wx.EVT_CHOICE, self.on_reason, self.reason_choice)
        self.Bind(wx.EVT_CHOICE, self.on_location, self.loc_choice)


        label_row = wx.BoxSizer(wx.HORIZONTAL)
        label_row.Add(self.label1, flag=wx.ALIGN_CENTER_VERTICAL)
        label_row.Add(self.label2, flag=wx.ALIGN_CENTER_VERTICAL)

        txtb_row = wx.BoxSizer(wx.HORIZONTAL)
        txtb_row.Add(self.DUT_pn_txtb, flag=wx.ALIGN_CENTER_VERTICAL)
        txtb_row.AddSpacer(15)
        txtb_row.Add(self.DUT_rev_txtb, flag=wx.ALIGN_CENTER_VERTICAL)

        reason_row = wx.BoxSizer(wx.HORIZONTAL)
        reason_row.Add(self.reason_label, flag=wx.ALIGN_CENTER_VERTICAL)
        reason_row.AddSpacer(3)
        reason_row.Add(self.reason_choice, flag=wx.ALIGN_CENTER_VERTICAL)

        loc_row = wx.BoxSizer(wx.HORIZONTAL)
        loc_row.Add(self.loc_label, flag=wx.ALIGN_CENTER_VERTICAL)
        loc_row.AddSpacer(3)
        loc_row.Add(self.loc_choice, flag=wx.ALIGN_CENTER_VERTICAL)

        sizer.AddSpacer(2)
        sizer.Add(self.report_cb, 0, wx.RIGHT|wx.LEFT, 10)
        sizer.AddSpacer(10)
        sizer.Add(label_row, 0, wx.RIGHT|wx.LEFT, 10)
        sizer.AddSpacer(2)
        sizer.Add(txtb_row, 0, wx.RIGHT|wx.LEFT, 10)
        sizer.AddSpacer(10)
        sizer.Add(self.label3, 0, wx.RIGHT|wx.LEFT, 10)
        sizer.AddSpacer(2)
        sizer.Add(self.DUT_ln_txtb, 0, wx.RIGHT|wx.LEFT, 10)
        sizer.AddSpacer(10)
        sizer.Add(reason_row, 0, wx.RIGHT|wx.LEFT, 10)
        sizer.AddSpacer(5)
        sizer.Add(loc_row, 0, wx.RIGHT|wx.LEFT, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.checkbox_recently_disabled = False
        self.controls_recently_disabled = False

        self.refresh()


    def on_pn_entered(self, event):
        new_pn = self.DUT_pn_txtb.GetValue()

        #check for no change
        if self.DUT_pn == new_pn:
            return

        self.DUT_pn = new_pn
        self.HPH_tester.set_DUT_pn(self.DUT_pn)

    def on_rev_entered(self, event):
        new_rev = self.DUT_rev_txtb.GetValue()

        #check for no change
        if self.DUT_rev == new_rev:
            return

        self.DUT_rev = new_rev
        self.HPH_tester.set_DUT_rev(self.DUT_rev)

    def on_ln_entered(self, event):
        new_ln = self.DUT_ln_txtb.GetValue()

        #check for no change
        if self.DUT_ln == new_ln:
            return

        self.DUT_ln = new_ln
        self.HPH_tester.set_DUT_ln(self.DUT_ln)


    def on_reason(self, event):
        new_reason = self.reason_choices[self.reason_choice.GetSelection()]

        #check for no change
        if self.reason == new_reason:
            return

        self.reason = new_reason
        self.HPH_tester.set_test_reason(self.reason)

    def on_location(self, event):
        new_location = self.loc_choices[self.loc_choice.GetSelection()]

        #check for no change
        if self.location == new_location:
            return

        self.location = new_location
        self.HPH_tester.set_test_location(self.location)


    def on_report_cb(self, event):
        self.HPH_tester.set_create_DUT_report(self.report_cb.GetValue())
        self.refresh()

    def create_DUT_report(self):
        """returns whether or not an individual DUT report is to be created"""
        return self.report_cb.GetValue()

    def get_DUT_pn(self):
        return self.DUT_pn

    def get_DUT_rev(self):
        return self.DUT_rev

    def get_DUT_ln(self):
        return self.DUT_ln

    def get_reason(self):
        return self.reason

    def get_location(self):
        return self.location


    def pn_SetFocus(self):
        self.DUT_pn_txtb.SetFocus()

    def rev_SetFocus(self):
        self.DUT_rev_txtb.SetFocus()

    def ln_SetFocus(self):
        self.DUT_ln_txtb.SetFocus()

    def reason_SetFocus(self):
        self.reason_choice.SetFocus()

    def location_SetFocus(self):
        self.loc_choice.SetFocus()


    def disable_controls_during_test(self):
        """disable controls to prevent changes during test"""
        if self.report_cb.IsEnabled():
            self.report_cb.Enable(False)
            self.checkbox_recently_disabled = True

        #only need to check one of the controls in the group (group is enabled or disabled)
        if self.loc_label.IsEnabled():
            self.loc_label.Enable(False)
            self.loc_choice.Enable(False)
            self.reason_label.Enable(False)
            self.reason_choice.Enable(False)
            self.label1.Enable(False)
            self.DUT_pn_txtb.Enable(False)
            self.label2.Enable(False)
            self.DUT_rev_txtb.Enable(False)
            self.label3.Enable(False)
            self.DUT_ln_txtb.Enable(False)
            self.controls_recently_disabled = True

    def enable_controls_after_test(self):
        """enable controls that were disabled during test"""
        if self.checkbox_recently_disabled:
            self.report_cb.Enable(True)
            self.checkbox_recently_disabled = False

        if self.controls_recently_disabled:
            self.loc_label.Enable(True)
            self.loc_choice.Enable(True)
            self.reason_label.Enable(True)
            self.reason_choice.Enable(True)
            self.label1.Enable(True)
            self.DUT_pn_txtb.Enable(True)
            self.label2.Enable(True)
            self.DUT_rev_txtb.Enable(True)
            self.label3.Enable(True)
            self.DUT_ln_txtb.Enable(True)
            self.controls_recently_disabled = False

    def changes_not_allowed(self):
        """disable controls if the user should not be allowed to make changes
           to the test configuration"""
        self.report_cb.Enable(False)


    def refresh(self):
        if self.report_cb.GetValue():
            self.loc_label.Enable(True)
            self.loc_choice.Enable(True)
            self.reason_label.Enable(True)
            self.reason_choice.Enable(True)
            self.label1.Enable(True)
            self.DUT_pn_txtb.Enable(True)
            self.label2.Enable(True)
            self.DUT_rev_txtb.Enable(True)
            self.label3.Enable(True)
            self.DUT_ln_txtb.Enable(True)
        else:
            self.loc_label.Enable(False)
            self.loc_choice.Enable(False)
            self.reason_label.Enable(False)
            self.reason_choice.Enable(False)
            self.label1.Enable(False)
            self.DUT_pn_txtb.Enable(False)
            self.label2.Enable(False)
            self.DUT_rev_txtb.Enable(False)
            self.label3.Enable(False)
            self.DUT_ln_txtb.Enable(False)

class MasterResultsBox(wx.Panel):
    """
    """
    def __init__(self, parent, ID, HPH_tester):
        wx.Panel.__init__(self, parent, ID)

        self.HPH_tester = HPH_tester

        box = wx.StaticBox(self, -1, "Master Results CSV")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.results_cb = wx.CheckBox(self, -1, "Record results to file              ")
        self.label = wx.StaticText(self, -1, "Results file location      ")
        self.browse_but = wx.Button(self, -1, "Browse")
        self.resultsfile_txtb = wx.TextCtrl(self, -1, size=(190,-1), style=wx.TE_PROCESS_ENTER)

        self.Bind(wx.EVT_CHECKBOX, self.on_results_cb, self.results_cb)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_resultsfile_entered,self.resultsfile_txtb)
        self.resultsfile_txtb.Bind(wx.EVT_KILL_FOCUS, self.on_resultsfile_entered)
        self.Bind(wx.EVT_BUTTON, self.on_resultsfile_browse, self.browse_but)
        self.results_cb.SetValue(self.HPH_tester.get_record_results())
        self.resultsfile = self.HPH_tester.get_results_file_path()
        self.resultsfile_txtb.SetValue(self.resultsfile)

        row1 = wx.BoxSizer(wx.HORIZONTAL)
        row1.Add(self.label, flag=wx.ALIGN_CENTER_VERTICAL)
        row1.Add(self.browse_but, flag=wx.ALIGN_CENTER_VERTICAL)

        sizer.AddSpacer(2)
        sizer.Add(self.results_cb, 0, wx.RIGHT|wx.LEFT, 10)
        sizer.AddSpacer(5)
        sizer.Add(row1, 0, wx.RIGHT|wx.LEFT, 10)
        sizer.AddSpacer(2)
        sizer.Add(self.resultsfile_txtb, 0, wx.RIGHT|wx.LEFT, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)


        self.results_cb_recently_disabled = False
        self.label_recently_disabled = False
        self.resultsfile_txtb_recently_disabled = False
        self.browse_but_recently_disabled = False

    def on_results_cb(self, event):
        self.HPH_tester.set_record_results(self.results_cb.GetValue())
        self.refresh()


    def on_resultsfile_browse(self, event):
        """pops up a file selector box to choose the file to record results to
        """
        file_selected = wx.FileSelector("Select a resultsfile",wildcard="*.csv")
        self.change_resultsfile(file_selected,from_browse_button=True)

    def on_resultsfile_entered(self, event):
        """use the file specified in the text box for results recording
        """
        f = self.resultsfile_txtb.GetValue()
        self.change_resultsfile(f)

    def change_resultsfile(self,new_resultsfile,from_browse_button=False):
        """
        """
        #verify that the new resultsfile is different than the file currently used
        if new_resultsfile == self.resultsfile:
            return

        #attempt to open file
        try:
            f = open(new_resultsfile, 'a')
        except Exception as e:
            wx.MessageBox("ERROR","Unable to open file",wx.OK)
            self.resultsfile_txtb.SetValue(self.resultsfile)
            return

        self.resultsfile = new_resultsfile
        if from_browse_button:
            self.resultsfile_txtb.SetValue(self.resultsfile)

        self.HPH_tester.set_results_file_path(self.resultsfile)

    def disable_controls_during_test(self):
        """disable controls to prevent changes during test"""
        if self.results_cb.IsEnabled():
            self.results_cb.Enable(False)
            self.results_cb_recently_disabled = True
            self.label.Enable(False)
            self.label_recently_disabled = True

        if self.resultsfile_txtb.IsEnabled():
            self.resultsfile_txtb.Enable(False)
            self.resultsfile_txtb_recently_disabled = True

        if self.browse_but.IsEnabled():
            self.browse_but.Enable(False)
            self.browse_but_recently_disabled = True

    def enable_controls_after_test(self):
        """enable controls that were disabled during test"""
        if self.results_cb_recently_disabled:
            self.results_cb.Enable(True)
            self.results_cb_recently_disabled = False

        if self.resultsfile_txtb_recently_disabled:
            self.resultsfile_txtb.Enable(True)
            self.resultsfile_txtb_recently_disabled = False
            self.label.Enable(True)
            self.label_recently_disabled = False

        if self.browse_but_recently_disabled:
            self.browse_but.Enable(True)
            self.browse_but_recently_disabled = False

    def changes_not_allowed(self):
        """disable controls if the user should not be allowed to make changes
           to the test configuration"""
        self.results_cb.Enable(False)
        self.label.Enable(False)
        self.resultsfile_txtb.Enable(False)
        self.browse_but.Enable(False)

    def refresh(self):
        if self.results_cb.GetValue():
            self.label.Enable(True)
            self.resultsfile_txtb.Enable(True)
            self.browse_but.Enable(True)
        else:
            self.label.Enable(False)
            self.resultsfile_txtb.Enable(False)
            self.browse_but.Enable(False)

class ReferenceEntryBox(wx.Panel):
    """
    """

    def __init__(self, parent, ID, HPH_tester):
        wx.Panel.__init__(self, parent, ID)

        self.HPH_tester = HPH_tester

        box = wx.StaticBox(self, -1, "Reference Entry(optional)")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.ref_text_box = wx.TextCtrl(self, -1, size=(160,-1),style=wx.TE_PROCESS_ENTER)
        self.ref_text = str(self.HPH_tester.get_reference_entry())

        self.Bind(wx.EVT_TEXT_ENTER, self.on_ref_text_enter,self.ref_text_box)
        self.ref_text_box.Bind(wx.EVT_KILL_FOCUS, self.on_ref_text_enter)

        sizer.AddSpacer(5)
        sizer.Add(self.ref_text_box, 0, wx.LEFT|wx.RIGHT, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.ref_text_recently_disabled = False

    def on_ref_text_enter(self, event):
        new_text = self.ref_text_box.GetValue()

        #exit if no change was made
        if self.ref_text == new_text:
            return

        else:
            self.HPH_tester.set_reference_entry(new_text)
            self.ref_text = new_text

    def disable_controls_during_test(self):
        """during the test disable controls that are not already disabled"""
        if self.ref_text_box.IsEnabled():
            self.ref_text_box.Enable(False)
            self.ref_text_recently_disabled = True

    def enable_controls_after_test(self):
        """after the test enable controls that were disabled during the test"""
        if self.ref_text_recently_disabled:
            self.ref_text_box.Enable(True)
            self.ref_text_recently_disabled = False


class SourcemeterControlBox(wx.Panel):
    """
    """
    max_test_current = 1.0
    max_compliance_voltage = 20

    def __init__(self, parent, ID, HPH_tester):
        wx.Panel.__init__(self, parent, ID)

        self.HPH_tester = HPH_tester

        box = wx.StaticBox(self, -1, "Sourcemeter Parameters")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.sm_Ilabel = wx.StaticText(self, -1, "           test current(A)")
        self.sm_Itext = wx.TextCtrl(self, -1, size=TEXTBOX_SIZE,style=wx.TE_PROCESS_ENTER)
        self.sm_I = str(self.HPH_tester.get_test_current())
        self.sm_Itext.SetValue(str(self.sm_I))

        self.sm_Vlabel = wx.StaticText(self, -1, "compliance voltage(V)")
        self.sm_Vtext = wx.TextCtrl(self, -1, size=TEXTBOX_SIZE,style=wx.TE_PROCESS_ENTER)
        self.sm_V = str(self.HPH_tester.get_compliance_voltage())
        self.sm_Vtext.SetValue(str(self.sm_V))

        self.Bind(wx.EVT_TEXT_ENTER, self.on_Itext_enter,self.sm_Itext)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_Vtext_enter,self.sm_Vtext)
        self.sm_Itext.Bind(wx.EVT_KILL_FOCUS, self.on_Itext_enter)
        self.sm_Vtext.Bind(wx.EVT_KILL_FOCUS, self.on_Vtext_enter)

        row1 = wx.BoxSizer(wx.HORIZONTAL)
        row1.Add(self.sm_Ilabel, flag=wx.ALIGN_CENTER_VERTICAL)
        row1.Add(self.sm_Itext, flag=wx.ALIGN_CENTER_VERTICAL)

        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row2.Add(self.sm_Vlabel, flag=wx.ALIGN_CENTER_VERTICAL)
        row2.Add(self.sm_Vtext, flag=wx.ALIGN_CENTER_VERTICAL)

        sizer.AddSpacer(5)
        sizer.Add(row1, 0, wx.LEFT|wx.RIGHT, 10)
        sizer.AddSpacer(5)
        sizer.Add(row2, 0, wx.LEFT|wx.RIGHT, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.sm_Itext_recently_disabled = False
        self.sm_Vtext_recently_disabled = False

    def on_Itext_enter(self, event):
        current = float(self.sm_Itext.GetValue())

        #exit if no change was made
        if current == self.sm_I:
            return

        #check for acceptable current entered
        elif (current > 0) and (current <= self.max_test_current):
            self.sm_I = current
            self.HPH_tester.set_test_current(current)

        #unacceptable current entered, revert back to original
        else:
            self.sm_Itext.SetValue(self.sm_I)

    def on_Vtext_enter(self, event):
        voltage = float(self.sm_Vtext.GetValue())

        #exit if no change was made
        if voltage == self.sm_V:
            return

        #check for acceptable voltage entered
        elif (voltage > 0) and (voltage <= self.max_compliance_voltage):
            self.sm_V = voltage
            self.HPH_tester.set_compliance_voltage(self.sm_V)

        #unacceptable voltage entered, revert back to original
        else:
            self.sm_Vtext.SetValue(self.sm_V)

    def changes_not_allowed(self):
        """disable controls if the user should not be allowed to make changes
           to the test configuration"""
        self.sm_Itext.Enable(False)
        self.sm_Ilabel.Enable(False)
        self.sm_Vtext.Enable(False)
        self.sm_Vlabel.Enable(False)

    def disable_controls_during_test(self):
        """during the test disable controls that are not already disabled"""
        if self.sm_Itext.IsEnabled():
            self.sm_Itext.Enable(False)
            self.sm_Itext_recently_disabled = True
            self.sm_Ilabel.Enable(False)
            self.sm_Ilabel_recently_disabled = True

        if self.sm_Vtext.IsEnabled():
            self.sm_Vtext.Enable(False)
            self.sm_Vtext_recently_disabled = True
            self.sm_Vlabel.Enable(False)
            self.sm_Vlabel_recently_disabled = True

    def enable_controls_after_test(self):
        """after the test enable controls that were disabled during the test"""
        if self.sm_Itext_recently_disabled:
            self.sm_Itext.Enable(True)
            self.sm_Itext_recently_disabled = False
            self.sm_Ilabel.Enable(True)
            self.sm_Ilabel_recently_disabled = False

        if self.sm_Vtext_recently_disabled:
            self.sm_Vtext.Enable(True)
            self.sm_Vtext_recently_disabled = False
            self.sm_Vlabel.Enable(True)
            self.sm_Vlabel_recently_disabled = False



class ExecutionControlBox(wx.Panel):
    """
    """
    def __init__(self, parent, ID, HPH_tester):
        wx.Panel.__init__(self, parent, ID)

        self.HPH_tester = HPH_tester

        box = wx.StaticBox(self, -1, "Test Execution Control")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.cb_pause = wx.CheckBox(self, -1, "pause each test")
        pause_spaces = wx.StaticText(self, -1, "        ")
        self.Bind(wx.EVT_CHECKBOX, self.on_pause_each_test, self.cb_pause)
        self.cb_pause.SetValue(self.HPH_tester.get_pause())

        self.resume = wx.Button(self, -1, "Resume")
        self.Bind(wx.EVT_BUTTON, self.on_resume, self.resume)

        self.cb_run_loops = wx.CheckBox(self, -1, "Loop Testing")
        loop_spaces = wx.StaticText(self, -1, "             ")
        self.Bind(wx.EVT_CHECKBOX, self.on_loop_testing,self.cb_run_loops)
        self.cb_run_loops.SetValue(self.HPH_tester.get_looptesting())

        self.abort = wx.Button(self, -1, "Abort")
        self.Bind(wx.EVT_BUTTON, self.on_abort, self.abort)

        self.label3 = wx.StaticText(self, -1, "number of test loops")
        self.num_loops_txtb = wx.TextCtrl(self, -1, size=TEXTBOX_SIZE,style=wx.TE_PROCESS_ENTER)
        self.num_loops = self.HPH_tester.get_num_loops()
        self.num_loops_txtb.SetValue(str(self.num_loops))
        self.Bind(wx.EVT_TEXT_ENTER, self.on_num_loops_enter,self.num_loops_txtb)
        self.num_loops_txtb.Bind(wx.EVT_KILL_FOCUS, self.on_num_loops_enter)

        self.label4 = wx.StaticText(self, -1, "loop interval(seconds)")
        self.loop_interval_txtb = wx.TextCtrl(self, -1, size=TEXTBOX_SIZE,style=wx.TE_PROCESS_ENTER)
        self.loop_interval = self.HPH_tester.get_loop_interval_sec()
        self.loop_interval_txtb.SetValue(str(self.loop_interval))
        self.Bind(wx.EVT_TEXT_ENTER, self.on_loop_interval_enter,self.loop_interval_txtb)
        self.loop_interval_txtb.Bind(wx.EVT_KILL_FOCUS, self.on_loop_interval_enter)

        self.cb_run_leakage = wx.CheckBox(self, -1, "Run Cap Leakage Testing")
        self.Bind(wx.EVT_CHECKBOX, self.on_leakage_testing,self.cb_run_leakage)
        self.cb_run_leakage.SetValue(self.HPH_tester.get_leakage_test())

        pause_row = wx.BoxSizer(wx.HORIZONTAL)
        pause_row.Add(self.cb_pause)
        pause_row.Add(pause_spaces)
        pause_row.Add(self.resume)

        loop_ckbx_row = wx.BoxSizer(wx.HORIZONTAL)
        loop_ckbx_row.Add(self.cb_run_loops)
        loop_ckbx_row.Add(loop_spaces)
        loop_ckbx_row.Add(self.abort)

        loop_num_row = wx.BoxSizer(wx.HORIZONTAL)
        loop_num_row.AddSpacer(23)
        loop_num_row.Add(self.label3, flag=wx.ALIGN_CENTER_VERTICAL)
        loop_num_row.Add(self.num_loops_txtb, flag=wx.ALIGN_CENTER_VERTICAL)

        loop_int_row = wx.BoxSizer(wx.HORIZONTAL)
        loop_int_row.AddSpacer(17)
        loop_int_row.Add(self.label4, flag=wx.ALIGN_CENTER_VERTICAL)
        loop_int_row.Add(self.loop_interval_txtb, flag=wx.ALIGN_CENTER_VERTICAL)

        sizer.AddSpacer(2)
        sizer.Add(pause_row, 0, wx.RIGHT|wx.LEFT, 5)
        sizer.AddSpacer(5)
        sizer.Add(loop_ckbx_row, 0, wx.RIGHT|wx.LEFT, 5)
        sizer.AddSpacer(5)
        sizer.Add(loop_num_row, 0, wx.RIGHT|wx.LEFT, 10)
        sizer.AddSpacer(5)
        sizer.Add(loop_int_row, 0, wx.RIGHT|wx.LEFT, 10)
        sizer.AddSpacer(10)
        sizer.Add(self.cb_run_leakage, 0, wx.RIGHT|wx.LEFT, 10)
        sizer.AddSpacer(2)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.refresh()

        #variables used to control disabling of objects during measurement execution
        self.pause_ckb_recently_disabled = False
        self.resume_button_recently_disabled = False
        self.looptesting_ckb_recently_disabled = False
        self.num_loops_recently_disabled = False
        self.loop_interval_recently_disabled = False
        self.cb_run_leakage_recently_disabled = False
        self.abort_recently_disabled = False


    def on_leakage_testing(self, event):
        self.HPH_tester.set_leakage_test(self.cb_run_leakage.GetValue())

    def on_pause_each_test(self, event):
        self.HPH_tester.set_pause(self.cb_pause.GetValue())
        self.refresh()

    def on_abort(self, event):
        self.abort.Enable(False)
        self.HPH_tester.abort_looptesting()

    def on_resume(self, event):
        self.HPH_tester.resume_measurements()

    def on_loop_testing(self, event):
        self.HPH_tester.set_looptesting(self.cb_run_loops.GetValue())
        self.refresh()

    def on_num_loops_enter(self, event):
        new_val = int(self.num_loops_txtb.GetValue())

        #exit if no change was made
        if new_val == self.num_loops:
            return

        #check for acceptable number entered
        elif (new_val >= 2):
            self.num_loops = new_val
            self.HPH_tester.set_num_loops(new_val)

        #unacceptable limit entered, revert back to original
        else:
            self.num_loops_txtb.SetValue(str(self.num_loops))

    def on_loop_interval_enter(self, event):
        new_val = float(self.loop_interval_txtb.GetValue())

        #exit if no change was made
        if new_val == self.loop_interval:
            return

        #check for acceptable number entered
        elif (new_val >= 10):
            self.loop_interval = new_val
            self.HPH_tester.set_loop_interval_sec(self.loop_interval)

        #unacceptable limit entered, revert back to original
        else:
            self.loop_interval_txtb.SetValue(str(self.loop_interval))


    def refresh(self):
        if self.cb_pause.GetValue():
            self.resume.Enable(True)
        else:
            self.resume.Enable(False)

        if self.cb_run_loops.GetValue():
            self.label3.Enable(True)
            self.num_loops_txtb.Enable(True)
            self.label4.Enable(True)
            self.loop_interval_txtb.Enable(True)
            self.abort.Enable(True)
        else:
            self.label3.Enable(False)
            self.num_loops_txtb.Enable(False)
            self.label4.Enable(False)
            self.loop_interval_txtb.Enable(False)
            self.abort.Enable(False)



    def changes_not_allowed(self):
        """disable controls if the user should not be allowed to make changes
           to the test configuration"""
        self.cb_pause.Enable(False)
        self.cb_run_loops.Enable(False)
        self.num_loops_txtb.Enable(False)
        self.label3.Enable(False)
        self.loop_interval_txtb.Enable(False)
        self.label4.Enable(False)
        self.cb_run_leakage.Enable(False)

    def disable_controls_during_test(self):
        """disable controls during test execution"""
        if self.cb_pause.IsEnabled():
            self.cb_pause.Enable(False)
            self.pause_ckb_recently_disabled = True

        if self.cb_run_loops.IsEnabled():
            self.cb_run_loops.Enable(False)
            self.looptesting_ckb_recently_disabled = True

        if self.num_loops_txtb.IsEnabled():
            self.num_loops_txtb.Enable(False)
            self.label3.Enable(False)
            self.num_loops_recently_disabled = True

        if self.loop_interval_txtb.IsEnabled():
            self.loop_interval_txtb.Enable(False)
            self.label4.Enable(False)
            self.loop_interval_recently_disabled = True

        if self.cb_run_leakage.IsEnabled():
            self.cb_run_leakage.Enable(False)
            self.cb_run_leakage_recently_disabled = True


    def enable_controls_after_test(self):
        """enable the controls that were disabled during the test"""
        if self.pause_ckb_recently_disabled:
            self.cb_pause.Enable(True)
            self.pause_ckb_recently_disabled = False

        if self.resume_button_recently_disabled:
            self.resume.Enable(True)
            self.resume_button_recently_disabled = False

        if self.looptesting_ckb_recently_disabled:
            self.cb_run_loops.Enable(True)
            self.looptesting_ckb_recently_disabled = False

        if self.num_loops_recently_disabled:
            self.num_loops_txtb.Enable(True)
            self.label3.Enable(True)
            self.num_loops_recently_disabled = False

        if self.loop_interval_recently_disabled:
            self.loop_interval_txtb.Enable(True)
            self.label4.Enable(True)
            self.loop_interval_recently_disabled = False

        if self.cb_run_leakage_recently_disabled:
            self.cb_run_leakage.Enable(True)
            self.cb_run_leakage_recently_disabled = False


class GUI_frame(wx.Frame):
    title = 'HPH: Vbat capacitor silver epoxy contact resistance tester'

    def __init__(self,HPH_tester,debug):
        self.HPH_tester = HPH_tester
        self.debug = debug

        #create the frame, disable resizing, disable the maximize button
        wx.Frame.__init__(self, None, title=self.title, size=(700,700),pos=(3,3),
                            style=wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX ^ wx.RESIZE_BORDER)
        self.create_menu()
        self.create_status_bar()
        self.create_main_panel(self)
        self.disable_necessary_GUI_controls()
        self.DUT_control_box.prep_for_next_test()

    def create_menu(self):
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_exit = menu_file.Append(-1, "Exit", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)

        menu_help = wx.Menu()
        m_about = menu_help.Append(-1, "About...", "About")
        self.Bind(wx.EVT_MENU, self.on_about, m_about)

        self.menubar.Append(menu_file, "&File")
        self.menubar.Append(menu_help, "&Help")
        self.SetMenuBar(self.menubar)

    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()

    def create_main_panel(self,parent):
        try:
            self.panel = wx.Panel(self)

            pic = wx.StaticBitmap(self.panel)

            pic.SetBitmap(wx.Bitmap(os.getcwd() + "/HPH.bmp"))

            title = TransparentText(self.panel, -1, "HPH Silver Epoxy Contact Resistance Measurement",
                                            pos=(12,5),style=wx.TRANSPARENT_WINDOW)
            title.SetFont(wx.Font(20,wx.FONTFAMILY_DEFAULT,wx.NORMAL,wx.FONTWEIGHT_NORMAL))
            note = TransparentText(self.panel, -1, "resistance measurements below displayed in milliohms",
                                            pos=(135,35),style=wx.TRANSPARENT_WINDOW)
            note.SetFont(wx.Font(12,wx.FONTFAMILY_DEFAULT,wx.NORMAL,wx.FONTWEIGHT_NORMAL))
            pn = self.HPH_tester.get_test_system_instance()
            sys_pn = TransparentText(self.panel, -1, "Test System: %s"%pn,
                                            pos=(160,55),style=wx.TRANSPARENT_WINDOW)
            sys_pn.SetFont(wx.Font(25,wx.FONTFAMILY_DEFAULT,wx.NORMAL,wx.FONTWEIGHT_NORMAL))
            self.pass_fail = TransparentText(self.panel, -1, "", pos=(215,290),style=wx.TRANSPARENT_WINDOW)
            self.pass_fail.SetFont(wx.Font(50,wx.FONTFAMILY_DEFAULT,wx.NORMAL,wx.FONTWEIGHT_BOLD))

            self.create_measurement_textboxes()

            self.DUT_report_control_box = DUT_ReportControlBox(self.panel, -1, self.HPH_tester)
            self.DUT_control_box = DUTControlBox(self.panel, -1, self.HPH_tester,
                                                    self.DUT_report_control_box,self.debug,self)
            self.sm_control_box = SourcemeterControlBox(self.panel, -1, self.HPH_tester)
            self.reference_entry_box = ReferenceEntryBox(self.panel, -1, self.HPH_tester)
            self.data_recording_control_box = MasterResultsBox(self.panel, -1, self.HPH_tester)
            self.execution_controls_box = ExecutionControlBox(self.panel, -1, self.HPH_tester)
            self.webcams = WebcamCapture(self.panel, -1,self.debug)

            #fix tab order since items could not be created in desired order
            self.DUT_report_control_box.MoveAfterInTabOrder(self.sm_control_box)


            self.Bind(EVT_MEAS_DONE, self.on_measurements_done)
            self.Bind(EVT_MEAS_READY, self.on_measurement_ready)
            self.Bind(EVT_TEST_STARTED, self.on_test_started)
            self.Bind(EVT_ALL_TESTS_COMPLETED, self.on_all_tests_completed)
            self.Bind(EVT_ABORT_LOOPTESTING, self.on_looptesting_aborted)
            self.Bind(EVT_INVALID_TEST, self.on_invalid_result)
            self.Bind(EVT_PROBE_CHECK, self.on_probe_check)
            self.Bind(wx.EVT_CLOSE, self.on_exit)
            self.result_index = 0

            col1 = wx.BoxSizer(wx.VERTICAL)
            col1.Add(self.DUT_control_box, border=5, flag=wx.ALL)
            col1.Add(self.sm_control_box, border=5, flag=wx.ALL)

            col2 = wx.BoxSizer(wx.VERTICAL)
            col2.Add(self.DUT_report_control_box, border=5, flag=wx.ALL)
            col2.Add(self.reference_entry_box, border=5, flag=wx.ALL)

            col3 = wx.BoxSizer(wx.VERTICAL)
            col3.Add(self.data_recording_control_box, border=5, flag=wx.ALL)
            col3.Add(self.execution_controls_box, border=5, flag=wx.ALL)

            self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
            self.hbox1.Add(col1, border=1, flag=wx.RIGHT|wx.LEFT)
            self.hbox1.Add(col2, border=1, flag=wx.RIGHT|wx.LEFT)
            self.hbox1.Add(col3, border=1, flag=wx.RIGHT|wx.LEFT)

            self.fixture_col = wx.BoxSizer(wx.VERTICAL)
            self.fixture_col.Add(pic, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
            self.fixture_col.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)

            self.webcams_col = wx.BoxSizer(wx.VERTICAL)
            self.webcams_col.Add(self.webcams, border=5)

            main_hbox = wx.BoxSizer(wx.HORIZONTAL)
            main_hbox.Add(self.fixture_col,border=5)
            main_hbox.Add(self.webcams_col,border=5)

            self.panel.SetSizer(main_hbox)
            main_hbox.Fit(self)

            #check for valid csv file for recording results
            if self.HPH_tester.get_results_file_error():
                self.data_file_error()

        except Exception as e:
            print "Exception in create_main_panel(): " + repr(e)
            raise e

    def data_file_error(self):
        """error message encountered when output csv file containing all accumulated test
           results is not found
        """
        try:
            str = "Unable to find output file specified in settings.cfg\n\n" + \
                      "Please specify file location"
            msgbox = wx.MessageDialog(self, str,"Output File Error",style=wx.OK)
            msgbox.ShowModal()

            file_selected = wx.FileSelector("Select a resultsfile",wildcard="*.csv")
            self.data_recording_control_box.change_resultsfile(file_selected,from_browse_button=True)

        except Exception as e:
            print "Exception in data_file_error(): " + repr(e)
            raise e

    def create_measurement_textboxes(self):
        start_pos = (125,145)
        h_spacing = 130
        v_spacing = 22
        _size = (110,30)

        text_boxes = []
        for i in range(3):
            for j in range(2):
                if j==0:
                    #right justify textboxes for VSS connections
                    txtctrl = wx.TextCtrl(self.panel, -1,size=_size,style=wx.TE_RIGHT,
                                            pos = (start_pos[0]+j*_size[0]+j*h_spacing,
                                                   start_pos[1]+i*_size[1]+i*v_spacing))
                else:
                    #left justify textboxes for VBAT connections
                    txtctrl = wx.TextCtrl(self.panel, -1,size=_size,
                                            pos = (start_pos[0]+j*_size[0]+j*h_spacing,
                                                   start_pos[1]+i*_size[1]+i*v_spacing))
                txtctrl.SetFont(wx.Font(15,wx.MODERN,wx.NORMAL,wx.NORMAL))
                txtctrl.SetEditable(False)
                text_boxes.append(txtctrl)

        #put the text boxes in the correct order that the measurements will be taken
        self.measurement_displays = []
        self.measurement_displays.append(text_boxes[1])
        self.measurement_displays.append(text_boxes[0])
        self.measurement_displays.append(text_boxes[3])
        self.measurement_displays.append(text_boxes[2])
        self.measurement_displays.append(text_boxes[5])
        self.measurement_displays.append(text_boxes[4])

        #give more meaningful names to the displays
        self.txt_CCHRG1_vss = self.measurement_displays[0]
        self.txt_CCHRG1_vbat = self.measurement_displays[1]
        self.txt_CCHRG2_vss = self.measurement_displays[2]
        self.txt_CCHRG2_vbat = self.measurement_displays[3]
        self.txt_CCHRG3_vss = self.measurement_displays[4]
        self.txt_CCHRG3_vbat = self.measurement_displays[5]



    def on_about(self, event):
        try:
            str = "High Power Hybrid screening fixture software info...\n\n"
            str += "Part Number: %s Rev.%s\n"%(self.HPH_tester.get_software_pn(),
                                                        self.HPH_tester.get_software_agile_rev())
            str += "Version: %s\n"%(self.HPH_tester.get_software_version())
            str += "Release Type: %s"%(self.HPH_tester.get_software_release_type())
            msgbox = wx.MessageDialog(self, str,"About HPH Test Software",style=wx.OK)
            msgbox.ShowModal()

        except Exception as e:
            print "Exception in on_about(): " + repr(e)
            raise e

    def on_probe_check(self, event):
        try:
            if self.debug: print "Handling EVT_PROBE_CHECK Event"
            self.clear_displays()
            self.pass_fail.SetLabel("")
            self.disable_objects_during_test()

            str = "Running pre-test probe check..."
            self.set_status_message(str)

        except Exception as e:
            print "Exception in on_probe_check(): " + repr(e)
            raise e

    def on_all_tests_completed(self, event):
        try:
            if self.debug: print "Handling EVT_ALL_TESTS_COMPLETED Event"

            if event.get_value() is not None:
                self.set_status_message(event.get_value())

            self.enable_objects_after_test()
            self.DUT_control_box.prep_for_next_test()

        except Exception as e:
            print "Exception in on_all_tests_completed(): " + repr(e)
            raise e

    def on_measurements_done(self, event):
        try:
            if self.debug: print "Handling EVT_MEAS_DONE Event"

            if self.debug and self.HPH_tester.get_looptesting():
                print "loop number %d measurements finished"%self.current_loop_num

            result_dictionary = self.HPH_tester.get_pass_fail_result()

            #update the status box at bottom of GUI with results
            if self.HPH_tester.get_looptesting():
                loopstring = "(loop %d of %d) "%(self.current_loop_num,
                                                    self.HPH_tester.get_num_loops())
            else:
                loopstring = ""

            msg = "S/N:%s%s"%(self.sn,loopstring)

            if self.HPH_tester.using_criteria_parallel_R():
                msg += " - Rparallel: %sohms (%s)"%(result_dictionary['parallel resistance'][1],
                                                                result_dictionary['parallel resistance'][0])

            if self.HPH_tester.using_criteria_bad_caps():
                msg += " - #bad caps: %s (%s)"%(result_dictionary['number of compromised caps'][1],
                                                        result_dictionary['number of compromised caps'][0])

            if self.HPH_tester.using_criteria_absolute_R():
                msg += " - #joints at or above %.3fohms: %s (%s)"%(self.HPH_tester.get_absolute_resistance_limit(),
                                        result_dictionary['absolute resistance'][1],
                                        result_dictionary['absolute resistance'][0])

            if self.HPH_tester.get_leakage_test():
                msg += " - Cap Leakage: %suA (%s)"%(result_dictionary['leakage current'][1],
                                            result_dictionary['leakage current'][0])
            self.set_status_message(msg)


            result = self.HPH_tester.get_overall_pass_fail_result()

            #update the on-screen text to indicate pass or fail
            if result == 'PASS':
                self.pass_fail.SetForegroundColour("GREEN")
                self.pass_fail.SetLabel("PASS")
            elif result == 'FAIL':
                self.pass_fail.SetForegroundColour("RED")
                self.pass_fail.SetLabel("FAIL")
            elif result == 'NA':
                self.pass_fail.SetForegroundColour("BLACK")
                self.pass_fail.SetLabel("N/A")
                if self.debug: print "No pass/fail test criteria selected in config file"
            else:
                raise RuntimeError("Did not get the expected 'PASS' or 'FAIL' event")

        except Exception as e:
            print "Exception in on_measurements_done(): " + repr(e)
            raise e

    def on_measurement_ready(self, event):
        """value returned from the event will be the calculated resistance value in milliohms
        """
        try:
            if self.debug: print "Handling EVT_MEAS_READY Event"

            r = event.get_value()

            if r >= 10000000.0:
                self.measurement_displays[self.result_index].SetValue(">10Kohm")

            elif r >= 1000.0:
                self.measurement_displays[self.result_index].SetValue("%.0f"%event.get_value())

            else:
                self.measurement_displays[self.result_index].SetValue("%.2f"%event.get_value())

            if self.result_index == 5:
                self.result_index = 0
            else:
                self.result_index += 1

        except Exception as e:
            print "Exception in on_measurement_ready(): " + repr(e)
            raise e


    def on_test_started(self, event):
        try:
            if self.debug: print "Handling EVT_TEST_STARTED Event"

            self.clear_displays()
            self.pass_fail.SetLabel("")
            self.disable_objects_during_test()
            self.sn = self.DUT_control_box.get_sn()
            if self.debug: print "Test Started on SN: %s"%(self.sn)

            if self.HPH_tester.get_looptesting():
                self.current_loop_num = self.HPH_tester.get_current_loop_num()+1
                loopstring = "(loop %d of %d)"%(self.current_loop_num,
                                                self.HPH_tester.get_num_loops())
                if self.debug: "  ",loopstring
            else:
                loopstring = ""

            self.set_status_message("Testing device S/N:%s%s..."%(self.sn,loopstring))
            self.pass_fail.SetLabel("")

        except Exception as e:
            print "Exception found in on_test_started(): " + repr(e)
            raise e

    def on_looptesting_aborted(self, event):
        try:
            if self.debug: print "Handling EVT_ABORT_LOOPTESTING Event"

            self.set_status_message("S/N:%s loop testing aborted after %d of %d loops"%(self.sn,
                                    self.current_loop_num,self.HPH_tester.get_num_loops()))
            self.enable_objects_after_test()
            self.DUT_control_box.prep_for_next_test()
            self.execution_controls_box.refresh()
        except Exception as e:
            print "Exception in on_looptesting_aborted(): " + repr(e)
            raise e

    def on_invalid_result(self, event):
        try:
            if self.debug: print "Handling EVT_INVALID_TEST Event"

            self.set_status_message("%s  invalid resistance detected at test fixture"%(self.status_msg))

            # when an invalid measurement is encountered pop up a dialog box to inform the user that
            # action should be taken to fix the problem
            # In the case of loop testing only inform the user on the first loop iteration. After the first
            # loop has been successfully run invalid results will be written to the results file as 'INVALID'
            # but loop testing will continue without a user prompt dialog box
            if self.HPH_tester.get_looptesting():
                if self.debug: print "looptesting detected by on_invalid_result(), loop number %d"%(self.current_loop_num)
                if self.current_loop_num > 1:
                    if self.debug: print "Not going to launch pop-up dialog"
                    return
                else:
                    if self.debug: print "Going to launch pop-up dialog and abort testing"

            str="Warning:\nInvalid resistance measurement encountered. Test execution halted.\n\n" + \
                "Recommend verifying probe alignment and restarting test."
            msgbox = wx.MessageDialog(self, str,"Test Fixture Warning",style=wx.OK)
            msgbox.ShowModal()

            self.enable_objects_after_test()
            self.DUT_control_box.prep_for_next_test()
            self.execution_controls_box.refresh()

        except Exception as e:
            print "Exception in on_invalid_result(): " + repr(e)
            raise e

    def get_loop_number(self):
        return self.current_loop_num

    def disable_objects_during_test(self):
        self.sm_control_box.disable_controls_during_test()
        self.DUT_control_box.disable_controls_during_test()
        self.execution_controls_box.disable_controls_during_test()
        self.data_recording_control_box.disable_controls_during_test()
        self.DUT_report_control_box.disable_controls_during_test()
        self.reference_entry_box.disable_controls_during_test()

    def enable_objects_after_test(self):
        self.sm_control_box.enable_controls_after_test()
        self.DUT_control_box.enable_controls_after_test()
        self.execution_controls_box.enable_controls_after_test()
        self.data_recording_control_box.enable_controls_after_test()
        self.DUT_report_control_box.enable_controls_after_test()
        self.reference_entry_box.enable_controls_after_test()

    def disable_necessary_GUI_controls(self):
        """do not allow the operator to change any of the test controls"""
        if self.HPH_tester.get_allow_config_changes() == False:
            self.sm_control_box.changes_not_allowed()
            self.execution_controls_box.changes_not_allowed()
            self.data_recording_control_box.changes_not_allowed()
            self.DUT_report_control_box.changes_not_allowed()

    def clear_displays(self):
        for display in self.measurement_displays:
            display.SetValue("")

    def set_status_message(self, msg):
        self.status_msg = msg
        self.statusbar.SetStatusText(self.status_msg)

    def on_exit(self, event):
        self.HPH_tester.program_terminated()
        self.Destroy()


def main(argv=None):
    try:
        #********************************************
        # Parse command line options
        if argv is None:
            argv = sys.argv
        p = optparse.OptionParser()
        p.add_option("-d", action="store_true", dest="debug")
        p.add_option("--debug", action="store_true", dest="debug")
        p.add_option("-s", action="store_true", dest="substrate")
        p.add_option("--substrate", action="store_true", dest="substrate")

        # Set default values for options:
        p.set_defaults(debug=False,substrate=False)
        opts, args = p.parse_args()

        # Retrieve the option settings:
        _debug = opts.debug
        _substrate = opts.substrate
        #********************************************

        if _debug: print 'Debugging Statements Enabled...'
        HPH_tester = testscript.Vbat_caps_test(print_to_console=False,
                                                debug=_debug,
                                                substrate=_substrate)
        app = wx.App(False)
        frame = GUI_frame(HPH_tester,_debug)
        frame.Show()
        app.MainLoop()

    except Exception as e:
        print "Exception in main(): " + repr(e)
        raise e

if __name__ == '__main__':
    main()








