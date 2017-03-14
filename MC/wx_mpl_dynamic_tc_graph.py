import os
import pprint
import random
import sys
import wx
import datetime

# The recommended way to use wx with mpl is with the WXAgg
# backend.
#
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np
import pylab

sys.path.append("C:/docs/python programs/modules")
import MCC_devices

class BoundControlBox(wx.Panel):
    """ A static box with a couple of radio buttons and a text
        box. Allows to switch between an automatic mode and a
        manual mode with an associated value.
    """
    def __init__(self, parent, ID, label, initval):
        wx.Panel.__init__(self, parent, ID)

        self.value = initval

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.radio_auto = wx.RadioButton(self, -1,
            label="Auto", style=wx.RB_GROUP)
        self.radio_manual = wx.RadioButton(self, -1,
            label="Manual")
        self.manual_text = wx.TextCtrl(self, -1,
            size=(35,-1),
            value=str(initval),
            style=wx.TE_PROCESS_ENTER)

        self.Bind(wx.EVT_UPDATE_UI, self.on_update_manual_text, self.manual_text)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter, self.manual_text)

        manual_box = wx.BoxSizer(wx.HORIZONTAL)
        manual_box.Add(self.radio_manual, flag=wx.ALIGN_CENTER_VERTICAL)
        manual_box.Add(self.manual_text, flag=wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(self.radio_auto, 0, wx.ALL, 10)
        sizer.Add(manual_box, 0, wx.ALL, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_update_manual_text(self, event):
        self.manual_text.Enable(self.radio_manual.GetValue())

    def on_text_enter(self, event):
        self.value = self.manual_text.GetValue()

    def is_auto(self):
        return self.radio_auto.GetValue()

    def manual_value(self):
        return self.value

class LogDataBox(wx.Panel):
    """ A static box that contains controlls to allow the user to capture
        acquired data as a csv file.
    """
    def __init__(self, parent, ID, label,  log_interval_sec=5):
        wx.Panel.__init__(self, parent, ID)

        self.box = wx.StaticBox(self, -1, label,size=(150,150))
        sizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)

        self.log_button = wx.Button(self, -1, "On/Off")
        self.Bind(wx.EVT_BUTTON, self.on_log_button, self.log_button)
        #self.Bind(wx.EVT_UPDATE_UI, self.on_log_button, self.log_button)

        self.logto_button = wx.Button(self, -1, "Log Dir")
        self.Bind(wx.EVT_BUTTON, self.on_logto_button, self.logto_button)
        #self.Bind(wx.EVT_UPDATE_UI, self.on_logto_button, self.logto_button)

        self.logging_active = False

        sizer.Add(self.log_button, 0, wx.ALL, 7)
        sizer.Add(self.logto_button, 0, wx.ALL, 7)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.log_dir = "C:/MC temperature logs"

    def on_log_button(self, event):
        self.logging_active = not self.logging_active

        if self.logging_active:
            self.box.SetLabel("Logging=Active")
            self.start_logging()

        else:
            self.box.SetLabel("Logging=Inactive")
            self.end_logging()

    def on_logto_button(self, event):
        print'pressed too'

    def start_logging(self):
        start_time = datetime.datetime.now().strftime("%Y_%m_%d - %H_%M_%S")
        filename = self.log_dir + "/temperature log - %s"%start_time + ".csv"
        self.logfile = open(filename,'w')
        self.logfile.write("Temperature Log - started:%s\n\nTimestamp,degrees(C)\n"%(start_time))

        self.logging_active = True

    def end_logging(self):
        self.logging_active = False
        self.logfile.close()

    def on_log_timer(self):
        pass

    def is_logging_active(self):
        return self.logging_active

    def get_logfile(self):
        return self.logfile

class GraphFrame(wx.Frame):
    """ The main frame of the application
    """
    title = 'Demo: dynamic matplotlib graph'
    INITIAL_REDRAW_TIMER_MSEC = 2000

    def __init__(self,device_sn=None):
        wx.Frame.__init__(self, None, -1, self.title)
        print 'calling mcc module'
        self.thermocouple = MCC_devices.USB_2001_TC("USB-2001-TC::016f24e0","T","F")
        self.data = [self.thermocouple.read_temp()]
        self.paused = False

        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        self.redraw_timer.Start(self.INITIAL_REDRAW_TIMER_MSEC)

    def create_menu(self):
        self.menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)

        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
        self.panel = wx.Panel(self)

        self.init_plot()
        self.canvas = FigCanvas(self.panel, -1, self.fig)

        self.xmin_control = BoundControlBox(self.panel, -1, "X min", 0)
        self.xmax_control = BoundControlBox(self.panel, -1, "X max", 50)
        self.ymin_control = BoundControlBox(self.panel, -1, "Y min", 0)
        self.ymax_control = BoundControlBox(self.panel, -1, "Y max", 100)
        self.log_control = LogDataBox(self.panel, -1,"Logging=Inactive")

        self.pause_button = wx.Button(self.panel, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)

        self.cb_grid = wx.CheckBox(self.panel, -1,
            "Show Grid",
            style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)
        self.cb_grid.SetValue(True)

        self.cb_xlab = wx.CheckBox(self.panel, -1,
            "Show X labels",
            style=wx.ALIGN_RIGHT)
        self.Bind(wx.EVT_CHECKBOX, self.on_cb_xlab, self.cb_xlab)
        self.cb_xlab.SetValue(True)

        self.reset_button = wx.Button(self.panel, -1, "Reset")
        self.Bind(wx.EVT_BUTTON, self.on_reset_button, self.reset_button)

        self.txt_sample_interval = wx.StaticText(self.panel, -1, "sample interval(sec)")
        self.tcntrl_sample_interval = wx.TextCtrl(self.panel, -1, "%s"%(self.INITIAL_REDRAW_TIMER_MSEC/1000),
                                                    size=(50,20),style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_sample_interval_changed, self.tcntrl_sample_interval)
        self.sample_interval_sec = self.INITIAL_REDRAW_TIMER_MSEC/1000

        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.cb_grid, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(10)
        self.hbox1.Add(self.cb_xlab, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.reset_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(25)
        self.hbox1.Add(self.txt_sample_interval, border=1, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.Add(self.tcntrl_sample_interval, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.xmin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.xmax_control, border=5, flag=wx.ALL)
        self.hbox2.AddSpacer(24)
        self.hbox2.Add(self.ymin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.ymax_control, border=5, flag=wx.ALL)
        self.hbox2.AddSpacer(24)
        self.hbox2.Add(self.log_control, border=5, flag=wx.ALL)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP)
        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_LEFT | wx.TOP)

        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)

    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()

    def init_plot(self):
        self.dpi = 100
        self.fig = Figure((3.0, 3.0), dpi=self.dpi)

        self.axes = self.fig.add_subplot(111)
        self.axes.set_axis_bgcolor('black')
        self.axes.set_title('Very important temperature data', size=12)

        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)

        # plot the data as a line series, and save the reference
        # to the plotted line series
        #
        self.plot_data = self.axes.plot(self.data,
                                        linewidth=1,
                                        color=(1, 1, 0),)[0]

    def draw_plot(self):
        """ Redraws the plot
        """
        # when xmin is on auto, it "follows" xmax to produce a
        # sliding window effect. therefore, xmin is assigned after
        # xmax.
        #
        if self.xmax_control.is_auto():
            xmax = len(self.data) if len(self.data) > 50 else 50
        else:
            xmax = int(self.xmax_control.manual_value())

        if self.xmin_control.is_auto():
            xmin = xmax - 50
        else:
            xmin = int(self.xmin_control.manual_value())

        # for ymin and ymax, find the minimal and maximal values
        # in the data set and add a mininal margin.
        #
        # note that it's easy to change this scheme to the
        # minimal/maximal value in the current display, and not
        # the whole data set.
        #
        if self.ymin_control.is_auto():
            ymin = round(min(self.data), 0) - 1
        else:
            ymin = int(self.ymin_control.manual_value())

        if self.ymax_control.is_auto():
            ymax = round(max(self.data), 0) + 1
        else:
            ymax = int(self.ymax_control.manual_value())

        self.axes.set_xbound(lower=xmin, upper=xmax)
        self.axes.set_ybound(lower=ymin, upper=ymax)

        # anecdote: axes.grid assumes b=True if any other flag is
        # given even if b is set to False.
        # so just passing the flag into the first statement won't
        # work.
        #
        if self.cb_grid.IsChecked():
            self.axes.grid(True, color='gray')
        else:
            self.axes.grid(False)

        # Using setp here is convenient, because get_xticklabels
        # returns a list over which one needs to explicitly
        # iterate, and setp already handles this.
        #
        pylab.setp(self.axes.get_xticklabels(),
            visible=self.cb_xlab.IsChecked())

        self.plot_data.set_xdata(np.arange(len(self.data)))
        self.plot_data.set_ydata(np.array(self.data))

        self.canvas.draw()

    def on_pause_button(self, event):
        self.paused = not self.paused

    def on_update_pause_button(self, event):
        label = "Resume" if self.paused else "Pause"
        self.pause_button.SetLabel(label)

    def on_reset_button(self, event):
        self.data = [self.thermocouple.read_temp()]

    def on_cb_grid(self, event):
        self.draw_plot()

    def on_cb_xlab(self, event):
        self.draw_plot()

    def on_save_plot(self, event):
        file_choices = "PNG (*.png)|*.png"

        dlg = wx.FileDialog(
            self,
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)

    def on_redraw_timer(self, event):
        # if paused do not add data, but still redraw the plot
        # (to respond to scale modifications, grid change, etc.)
        #
        if not self.paused:
            reading = self.thermocouple.read_temp()
            self.data.append(reading)

            if self.log_control.is_logging_active():
                self.log_control.get_logfile().write("%s,%.2f\n"%(datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S.%f")[0:24],
                                                                                reading))
                self.flash_status_message("logging data point: %.2f"%(reading),flash_len_ms=1000)

        self.draw_plot()

    def on_exit(self, event):
        self.Destroy()

    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(
            wx.EVT_TIMER,
            self.on_flash_status_off,
            self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)

    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('')

    def on_sample_interval_changed(self, event):
        try:
            entered_value = float(self.tcntrl_sample_interval.GetValue())
        except:
            print 'unable to convert sample interval to float'
            self.tcntrl_sample_interval.SetValue('%s'%(self.sample_interval_sec))
            return

        if (entered_value <= 0):
            # for negative values don't allow a change
            self.tcntrl_sample_interval.SetValue('%s'%(self.sample_interval_sec))

        else:
            self.sample_interval_sec = entered_value
            self.update_sample_timer()

    def update_sample_timer(self):
        self.redraw_timer.Start(self.sample_interval_sec*1000.0)


if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = GraphFrame()
    app.frame.Show()
    app.MainLoop()