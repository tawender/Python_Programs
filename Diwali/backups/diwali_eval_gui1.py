import os
import wx
import Diwali_com1

ver = "0.0.1"




class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(600,800))
        self.statusbar = self.CreateStatusBar() # A StatusBar in the bottom of the window
        self.statusbar.SetStatusText("Status: Idle")

        # Setting up the menu
        filemenu= wx.Menu()

        # wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets
        menuAbout = filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        menuExit = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content

        # Timer for updating display
        self.timer = wx.Timer(self)

        # Main panel to place objects
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Create labels for panel objects
        lbl_vmeas = wx.StaticText(panel, -1, "Measured Voltages")
        lbl_vRed = wx.StaticText(panel, -1, "Red:",size=(28,-1))
        lbl_vGreen = wx.StaticText(panel, -1, "Green:",size=(32,-1))
        lbl_vBlue = wx.StaticText(panel, -1, "Blue:",size=(30,-1))
        lbl_tri = wx.StaticText(panel, -1, "Tristimulus Values")
        lbl_X = wx.StaticText(panel, -1, "X:",size=(-1,28))
        lbl_X.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        lbl_Y = wx.StaticText(panel, -1, "Y:",size=(-1,28))
        lbl_Y.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        lbl_Z = wx.StaticText(panel, -1, "Z:",size=(-1,28))
        lbl_Z.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        lbl_cc = wx.StaticText(panel, -1, "Chromaticity Coordinates")
        lbl_x = wx.StaticText(panel, -1, "x:",size=(-1,30))
        lbl_x.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        lbl_y = wx.StaticText(panel, -1, "y:",size=(-1,30))
        lbl_y.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        lbl_cct = wx.StaticText(panel, -1, "Correlated Color Temperature")
        lbl_lightLevel = wx.StaticText(panel,-1,"Light Level")
        lbl_HTU21Dtemp = wx.StaticText(panel, -1, "        Temperature         ")
        lbl_HTU21Dhum = wx.StaticText(panel, -1, "          Relative Humidity")
        lbl_MS5637temp = wx.StaticText(panel, -1, " Temperature               ")
        lbl_MS5637pres = wx.StaticText(panel, -1, "             Pressure")
        lbl_MS8607temp = wx.StaticText(panel, -1, "Temperature                ")
        lbl_MS8607hum = wx.StaticText(panel, -1, " Humidity                    ")
        lbl_MS8607pres = wx.StaticText(panel, -1, "  Pressure            ")

        # Create text boxes for displaying data
        self.txtb_vRed = wx.StaticText(panel, -1,size=(45,-1))
        self.txtb_vRed.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL , wx.BOLD))
        self.txtb_vGreen = wx.StaticText(panel, -1,size=(55,-1))
        self.txtb_vGreen.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL , wx.BOLD))
        self.txtb_vBlue = wx.StaticText(panel, -1,size=(50,-1))
        self.txtb_vBlue.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL , wx.BOLD))
        self.txtb_X = wx.StaticText(panel, -1, size=(80,30))
        self.txtb_X.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_Y = wx.StaticText(panel, -1, size=(80,30))
        self.txtb_Y.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_Z = wx.StaticText(panel, -1, size=(80,30))
        self.txtb_Z.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_x = wx.StaticText(panel, -1, size=(80,30))
        self.txtb_x.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_y = wx.StaticText(panel, -1, size=(80,30))
        self.txtb_y.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_CCT = wx.StaticText(panel, -1, size=(120,60))
        self.txtb_CCT.SetFont(wx.Font(30, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_HTU21Dtemp = wx.StaticText(panel, -1,"00.00*C")
        self.txtb_HTU21Dtemp.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_HTU21Dhum = wx.StaticText(panel, -1,"00.00%")
        self.txtb_HTU21Dhum.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_MS5637temp = wx.StaticText(panel, -1,"00.00*C")
        self.txtb_MS5637temp.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_MS5637pres = wx.StaticText(panel, -1,"0000.00mbar")
        self.txtb_MS5637pres.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_lightLevel = wx.StaticText(panel,-1,"00.00fcd")
        self.txtb_lightLevel.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_MS8607temp = wx.StaticText(panel,-1,"00.00*C")
        self.txtb_MS8607temp.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_MS8607hum = wx.StaticText(panel,-1,"00.00%")
        self.txtb_MS8607hum.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_MS8607pres = wx.StaticText(panel,-1,"00.00mbar")
        self.txtb_MS8607pres.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))

        self.btn_dataControl = wx.Button(panel, -1, "Pause")


        # Arrange CCT objects
        row0 = wx.BoxSizer(wx.HORIZONTAL)
        row0.Add(lbl_vRed, 0, wx.RIGHT|wx.LEFT, 2)
        row0.Add(self.txtb_vRed, 0, wx.RIGHT|wx.LEFT, 2)
        row0.AddSpacer(20)
        row0.Add(lbl_vGreen, 0, wx.RIGHT|wx.LEFT, 2)
        row0.Add(self.txtb_vGreen, 0, wx.RIGHT|wx.LEFT, 2)
        row0.AddSpacer(20)
        row0.Add(lbl_vBlue, 0, wx.RIGHT|wx.LEFT, 2)
        row0.Add(self.txtb_vBlue, 0, wx.RIGHT|wx.LEFT, 2)

        row1 = wx.BoxSizer(wx.HORIZONTAL)
        row1.Add(lbl_X, 0, wx.ALL, 2)
        row1.Add(self.txtb_X, 0, wx.ALL, 2)
        row1.Add(lbl_Y, 0, wx.ALL, 2)
        row1.Add(self.txtb_Y, 0, wx.ALL, 2)
        row1.Add(lbl_Z, 0, wx.ALL, 2)
        row1.Add(self.txtb_Z, 0, wx.ALL, 2)

        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row2.Add(lbl_x, 0, wx.ALL, 2)
        row2.Add(self.txtb_x, 0, wx.ALL, 2)
        row2.AddSpacer(20)
        row2.Add(lbl_y, 0, wx.ALL, 2)
        row2.Add(self.txtb_y, 0, wx.ALL, 2)

        cct_box = wx.StaticBox(panel,-1,"Hamamatsu S9702 RGB sensor")
        cct_box_sizer = wx.StaticBoxSizer(cct_box,wx.VERTICAL)
        cct_box_sizer.Add(lbl_vmeas,flag=wx.CENTER)
        cct_box_sizer.Add(row0, 0, wx.TOP|wx.BOTTOM|wx.CENTER, 2)
        cct_box_sizer.AddSpacer(10)
        cct_box_sizer.Add(lbl_tri,flag=wx.CENTER)
        cct_box_sizer.Add(row1, 0, wx.TOP|wx.BOTTOM|wx.CENTER, 2)
        cct_box_sizer.AddSpacer(10)
        cct_box_sizer.Add(lbl_cc,flag=wx.CENTER)
        cct_box_sizer.Add(row2, 0, wx.TOP|wx.BOTTOM|wx.CENTER, 2)
        cct_box_sizer.AddSpacer(10)
        cct_box_sizer.Add(lbl_cct,flag=wx.CENTER)
        cct_box_sizer.Add(self.txtb_CCT, 0, wx.TOP|wx.BOTTOM|wx.CENTER, 2)

        # Arrange HTU21D temperature/humidity display
        HTU21D_box = wx.StaticBox(panel,-1,"HTU21D Sensor",size=(340,-1))
        HTU21D_box_sizer = wx.StaticBoxSizer(HTU21D_box,wx.VERTICAL)
        HTU21D_row1 = wx.BoxSizer(wx.HORIZONTAL)
        HTU21D_row1.Add(lbl_HTU21Dtemp, 0, wx.RIGHT|wx.LEFT, 2)
        HTU21D_row1.Add(lbl_HTU21Dhum, 0, wx.RIGHT|wx.LEFT, 2)
        HTU21D_row2 = wx.BoxSizer(wx.HORIZONTAL)
        HTU21D_row2.AddSpacer(10,0)
        HTU21D_row2.Add(self.txtb_HTU21Dtemp, 0, wx.RIGHT|wx.LEFT, 2)
        HTU21D_row2.AddSpacer(40,0)
        HTU21D_row2.Add(self.txtb_HTU21Dhum, 0, wx.RIGHT|wx.LEFT, 2)
        HTU21D_box_sizer.Add(HTU21D_row1, 0, wx.CENTER, 2)
        HTU21D_box_sizer.Add(HTU21D_row2, 0, wx.CENTER, 2)

        # Arrange MS5637 temperature/pressure display
        MS5637_box = wx.StaticBox(panel,-1,"MS5637 Sensor",size=(340,-1))
        MS5637_box_sizer = wx.StaticBoxSizer(MS5637_box,wx.VERTICAL)
        MS5637_row1 = wx.BoxSizer(wx.HORIZONTAL)
        MS5637_row1.Add(lbl_MS5637temp, 0, wx.ALL, 2)
        MS5637_row1.Add(lbl_MS5637pres, 0, wx.ALL, 2)
        MS5637_row2 = wx.BoxSizer(wx.HORIZONTAL)
        MS5637_row2.AddSpacer(40,0)
        MS5637_row2.Add(self.txtb_MS5637temp, 0, wx.ALL, 2)
        MS5637_row2.AddSpacer(20,0)
        MS5637_row2.Add(self.txtb_MS5637pres, 0, wx.ALL, 2)
        MS5637_box_sizer.Add(MS5637_row1, 0, wx.CENTER, 2)
        MS5637_box_sizer.Add(MS5637_row2, 0, wx.CENTER, 2)

        # Arrange MS8607 temperature/humidity/pressure display
        MS8607_box = wx.StaticBox(panel,-1,"MS8607 Sensor",size=(380,-1))
        MS8607_box_sizer = wx.StaticBoxSizer(MS8607_box,wx.VERTICAL)
        MS8607_row1 = wx.BoxSizer(wx.HORIZONTAL)
        MS8607_row1.Add(lbl_MS8607temp, 0, wx.ALL, 2)
        MS8607_row1.Add(lbl_MS8607hum, 0, wx.ALL, 2)
        MS8607_row1.Add(lbl_MS8607pres, 0, wx.ALL, 2)
        MS8607_row2 = wx.BoxSizer(wx.HORIZONTAL)
        #MS8607_row2.AddSpacer(20,0)
        MS8607_row2.Add(self.txtb_MS8607temp, 0, wx.ALL, 2)
        MS8607_row2.AddSpacer(20,0)
        MS8607_row2.Add(self.txtb_MS8607hum, 0, wx.ALL, 2)
        MS8607_row2.AddSpacer(20,0)
        MS8607_row2.Add(self.txtb_MS8607pres, 0, wx.ALL, 2)
        MS8607_box_sizer.Add(MS8607_row1, 0, wx.CENTER, 2)
        MS8607_box_sizer.Add(MS8607_row2, 0, wx.CENTER, 2)

        # Arrange light level objects
        light_lev_box = wx.StaticBox(panel,-1,"OP980 Photodiode",size=(340,-1))
        light_lev_box_sizer = wx.StaticBoxSizer(light_lev_box,wx.VERTICAL)
        light_lev_box_sizer.Add(lbl_lightLevel, 0, wx.ALL|wx.CENTER, 2)
        light_lev_box_sizer.Add(self.txtb_lightLevel, 0, wx.ALL|wx.CENTER, 10)

        # Add groups to the main vertical boxSizer on the panel
        vbox.Add(cct_box_sizer, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(HTU21D_box_sizer, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(MS5637_box_sizer, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(MS8607_box_sizer, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(light_lev_box_sizer, 0, wx.ALL|wx.CENTER, 5)
        vbox.Add(self.btn_dataControl, 0, wx.ALL|wx.CENTER, 5)



        panel.SetSizer(vbox)
        panel.Layout()


        # Set events.
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_BUTTON, self.OnDataControl, self.btn_dataControl)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        self.Show(True)

        # create the com object for serial communication
        self.com = Diwali_com.UART_com()

        self.timer.Start(self.com.get_interval()*1000.0)
        self.readingSensors = True


    def OnDataControl(self, e):
        if self.readingSensors:
            self.timer.Stop()
            self.readingSensors = False
            self.btn_dataControl.SetLabel("Continue")
        else:
            self.timer.Start(self.com.get_interval()*1000.0)
            self.readingSensors = True
            self.btn_dataControl.SetLabel("Pause")


    def readSensors(self):
        self.statusbar.SetStatusText("Status: Requesting Data...")
        ret = self.com.measure_and_read_data()
        if ret is not None:
            (v_red,v_green,v_blue,X, Y, Z, x, y, CCT,
             HTU_temp,HTU_rh,MS5637_temp,MS5637_press,light_level,
             MS8607_temp,MS8607_rh,MS8607_press) = ret

            self.txtb_vRed.SetLabel("%.3f V"%(v_red))
            self.txtb_vGreen.SetLabel("%.3f V"%(v_green))
            self.txtb_vBlue.SetLabel("%.3f V"%(v_blue))
            self.txtb_X.SetLabel("%.2f"%(X))
            self.txtb_Y.SetLabel("%.2f"%(Y))
            self.txtb_Z.SetLabel("%.2f"%(Z))
            if type(x) is float:
                self.txtb_x.SetLabel("%.5f"%(x))
            else:
                self.txtb_x.SetLabel("%s"%(x))
            if type(y) is float:
                self.txtb_y.SetLabel("%.5f"%(y))
            else:
                self.txtb_y.SetLabel("%s"%(y))
            if type(CCT) is float:
                self.txtb_CCT.SetLabel("%.0f K"%(CCT))
            else:
                self.txtb_CCT.SetLabel("%s"%(CCT))
            self.txtb_HTU21Dtemp.SetLabel("%.2f*C"%(HTU_temp))
            self.txtb_HTU21Dhum.SetLabel("%.2f%%"%(HTU_rh))
            self.txtb_MS5637temp.SetLabel("%.2f*C"%(MS5637_temp))
            if type(MS5637_press) is float:
                self.txtb_MS5637pres.SetLabel("%.2fmbar"%(MS5637_press))
            else:
                self.txtb_MS5637pres.SetLabel("%smbar"%(MS5637_press))
            self.txtb_lightLevel.SetLabel("%sfcd"%(light_level))

            self.statusbar.SetStatusText("Status: Idle")
            self.txtb_MS8607temp.SetLabel("%.2f*C"%(MS8607_temp))
            self.txtb_MS8607hum.SetLabel("%.2f%%"%(MS8607_rh))
            if type(MS8607_press) is float:
                self.txtb_MS8607pres.SetLabel("%.2fmbar"%(MS8607_press))
            else:
                self.txtb_MS8607pres.SetLabel("%smbar"%(MS8607_press))

        else:
            self.txtb_X.SetLabel("Err")
            self.txtb_Y.SetLabel("Err")
            self.txtb_Z.SetLabel("Err")
            self.txtb_x.SetLabel("Err")
            self.txtb_y.SetLabel("Err")
            self.txtb_CCT.SetLabel("Err")

            self.statusbar.SetStatusText("Status: Error Reading Data")

    def OnTimer(self, e):
        self.readSensors()


    def OnAbout(self,e):
        dlg = wx.MessageDialog( self, "Version: %s"%(ver), "About Diwali Demo", wx.OK)
        dlg.ShowModal() # Show it
        dlg.Destroy() # finally destroy it when finished.

    def OnExit(self,e):
        self.Close(True)  # Close the frame

app = wx.App(False)
frame = MainWindow(None, "Diwali Sensor Evaluation")
app.MainLoop()