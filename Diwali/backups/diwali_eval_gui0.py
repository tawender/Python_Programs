import os
import wx
import Diwali_com

ver = "0.0.1"




class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(600,700))
        self.CreateStatusBar() # A StatusBar in the bottom of the window

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
        cct_border = wx.StaticBox(panel,-1,"Correlated Color Temperature",size=(500,400))
        box = wx.StaticBoxSizer(cct_border,wx.VERTICAL)
        box.SetMinSize((500,500))

        # Create panel objects
        lbl_vRed = wx.StaticText(panel, -1, "Red Voltage:",size=(80,-1))
        lbl_vGreen = wx.StaticText(panel, -1, "Green Voltage:",size=(80,-1))
        lbl_vBlue = wx.StaticText(panel, -1, "Blue Voltage:",size=(80,-1))
        lbl_X = wx.StaticText(panel, -1, "X:",size=(-1,28))
        lbl_X.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
        lbl_Y = wx.StaticText(panel, -1, "Y:",size=(-1,28))
        lbl_Y.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
        lbl_Z = wx.StaticText(panel, -1, "Z:",size=(-1,28))
        lbl_Z.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
        lbl_x = wx.StaticText(panel, -1, "x:",size=(-1,30))
        lbl_x.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        lbl_y = wx.StaticText(panel, -1, "y:",size=(-1,30))
        lbl_y.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        lbl_CCT = wx.StaticText(panel, -1, "CCT:",size=(-1,50))
        lbl_CCT.SetFont(wx.Font(30, wx.SWISS, wx.NORMAL, wx.BOLD))

        self.txtb_vRed = wx.StaticText(panel, -1,size=(50,-1))
        self.txtb_vGreen = wx.StaticText(panel, -1,size=(50,-1))
        self.txtb_vBlue = wx.StaticText(panel, -1,size=(50,-1))
        self.txtb_X = wx.StaticText(panel, -1, size=(80,50))
        self.txtb_X.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_Y = wx.StaticText(panel, -1, size=(80,50))
        self.txtb_Y.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_Z = wx.StaticText(panel, -1, size=(80,50))
        self.txtb_Z.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_x = wx.StaticText(panel, -1, size=(80,30))
        self.txtb_x.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_y = wx.StaticText(panel, -1, size=(80,30))
        self.txtb_y.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.txtb_CCT = wx.StaticText(panel, -1, size=(120,60))
        self.txtb_CCT.SetFont(wx.Font(30, wx.SWISS, wx.NORMAL, wx.BOLD))

        self.btn_dataControl = wx.Button(panel, -1, "Pause")


        # Arrange the objects on the panel
        row0 = wx.BoxSizer(wx.HORIZONTAL)
        row0.Add(lbl_vRed, 0, wx.ALL, 2)
        row0.Add(self.txtb_vRed, 0, wx.ALL, 2)
        row0.Add(lbl_vGreen, 0, wx.ALL, 2)
        row0.Add(self.txtb_vGreen, 0, wx.ALL, 2)
        row0.Add(lbl_vBlue, 0, wx.ALL, 2)
        row0.Add(self.txtb_vBlue, 0, wx.ALL, 2)

        row1 = wx.BoxSizer(wx.HORIZONTAL)
        row1.Add(lbl_X, 0, wx.ALL, 10)
        row1.Add(self.txtb_X, 0, wx.ALL, 10)
        row1.Add(lbl_Y, 0, wx.ALL, 10)
        row1.Add(self.txtb_Y, 0, wx.ALL, 10)
        row1.Add(lbl_Z, 0, wx.ALL, 10)
        row1.Add(self.txtb_Z, 0, wx.ALL, 10)

        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row2.Add(lbl_x, 0, wx.ALL, 10)
        row2.Add(self.txtb_x, 0, wx.ALL, 10)
        row2.Add(lbl_y, 0, wx.ALL, 10)
        row2.Add(self.txtb_y, 0, wx.ALL, 10)

        row3 = wx.BoxSizer(wx.HORIZONTAL)
        row3.Add(lbl_CCT, 0, wx.ALL, 10)
        row3.Add(self.txtb_CCT, 0, wx.ALL, 10)

        box.Add(row0, 0, wx.ALL, 10)
        box.Add(row1, 0, wx.ALL, 10)
        box.Add(row2, 0, wx.ALL, 10)
        box.Add(row3, 0, wx.ALL, 10)
        box.Add(self.btn_dataControl, 0, wx.ALL, 10)



        panel.SetSizer(box)
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
        ret = self.com.measure_and_read_data()
        if ret is not None:
            (v_red,v_green,v_blue,X, Y, Z, x, y, CCT) = ret

            self.txtb_vRed.SetLabel("%.3f"%(v_red))
            self.txtb_vGreen.SetLabel("%.3f"%(v_green))
            self.txtb_vBlue.SetLabel("%.3f"%(v_blue))
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
                self.txtb_CCT.SetLabel("%.0f"%(CCT))
            else:
                self.txtb_CCT.SetLabel("%s"%(CCT))

        else:
            self.txtb_X.SetLabel("Err")
            self.txtb_Y.SetLabel("Err")
            self.txtb_Z.SetLabel("Err")
            self.txtb_x.SetLabel("Err")
            self.txtb_y.SetLabel("Err")
            self.txtb_CCT.SetLabel("Err")

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