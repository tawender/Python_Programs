#-------------------------------------------------------------------------------
# Name:        sicdCalScript.py
# Purpose:     Verify the S-ICD VCO tuning range and calibration.
#
#
# Author:      T. Guerena
#
# 1. is the /usr/bin/env python line appropriate?
# 2. need to add a mechnanism to add the device to link to at runtime.
# 3. need to add code to download the patch firmware; otherwise, device must be preconditioned.
# 4. need to group all classes and procedures into a common file and import into test classes.
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import sys
import time
from ConfigParser import ConfigParser

sys.path.append(r'..\..\PyTES')
from PyTES import *

sys.path.append(r'c:\Program Files\Python 2.7.5\Lib\site-packages')

# path to common files
sys.path.append(r'c:\python_programs\mics2')

import watlowF4ipy 

import clr
clr.AddReference("System")
from System import *

clr.AddReferenceToFile("Config.dll")
import Config

class WaitForDisconnectedEventState(IScriptExecState):
    def __init__(self, key, data):
        self.key = key
        self.data = data

    def doEntryAction(self, sm):
        sm.ICD.breakLink()
        return

    def processEvent(self, sm, ev):
        return type(ev)==DisconnectedEvent

class sicdCalScript(PyScript):
    def __init__(self, optionsPath, configPath):
        # Read configuration
        config = ConfigParser()
        config.read(configPath)

        logDir = config.get('Location', 'log_dir')
        logName = 'sicdCalScriptLog ' + DateTime.Now.ToString('yyyy.MM.dd HH.mm.ss') + '.log'
        buildNumber = int(config.get('Firmware', 'build_num'), 0)

        super(sicdCalScript, self).__init__(optionsPath, buildNumber, Path.Combine(logDir, logName))

        self.loop_count = int(config.get('Sampling', 'loop_count'))

    def script(self):
        #self.TestProcedure.ICD.writePrbFpga(0x1002, 0x12)
        ##d.	Read FPGA address 0x3000 and verify the response is 0x12.
        val = self.TestProcedure.ICD.readPrbFpga(0x3000)
        self.verify("FPGA 0x3000", 0x12, val)
        if val != 0x12:
            self.verify("ERROR", 0x12, val)

        inv_flag = 0x01
        chn_sel = 0x00
        self.TestProcedure.ICD.writePrbFpga(0x3012, inv_flag)
        self.TestProcedure.ICD.writePrbFpga(0x1026, chn_sel)
        val = self.TestProcedure.ICD.readPrbFpga(0x1026)
        print "  Channel Selection = ",val
        val = self.TestProcedure.ICD.readPrbFpga(0x3012)
        print "  Data inversion = ",val

        #32-42 1 degree steps, 27-17 5 degree steps
        temperatures = [33,34,35,36,37,38,39,40,41,42,27,22,17] 
        stabilization_mins = 10
        chamber = watlowF4ipy.WatlowF4_temp_window(3,debug=True)

        for temperature in temperatures:

            chamber.set_temperature_and_time(temperature,temperature-0.3,
                                            temperature+0.3,stabilization_mins)

            while chamber.dwelltime_endpoint_reached() == False:
                #pause before checking the flag again
                time.sleep(2)

            # calibrate once on channel 0
            self.TestProcedure.ICD.calibrateCc1020()
            self.DumpCalResult()

            DoCalFlag = 0x01
            MaxCalTries = 0x03
            ExitDelaySecs = 0x01

            # Scan and link on Channel 0, with data inversion active
            # Initialize the CC1000 Calibration Config Table
            devList = self.icdcmd.scan(17, 2)
            print "type(devList):",type(devList)
            self.icdcmd.connect((UInt32) (2100146))
            time.sleep(1)
            # Initialize the Cal config table
            self.initCalConfigTable()
            self.writeCalConfigTable(0)
            # Write the test control table
            self.writeCalControlTable(DoCalFlag, MaxCalTries, ExitDelaySecs)
            # Load the CCTestPatch firmware image to S-ICD RAM
     #       self.writeCCTestPatch()
            val = self.icdcmd.readByte((UInt32)(0x0201))
            print "  S-ICD CC1000 FREQ_2A = ",val
            val = self.icdcmd.readByte((UInt32)(0x0202))
            print "  S-ICD CC1000 FREQ_1A = ",val
            val = self.icdcmd.readByte((UInt32)(0x0203))
            print "  S-ICD CC1000 FREQ_0A = ",val
            val = self.icdcmd.readByte((UInt32)(0x0204))
            print "  S-ICD CC1000 FREQ_2B = ",val
            val = self.icdcmd.readByte((UInt32)(0x0205))
            print "  S-ICD CC1000 FREQ_1B = ",val
            val = self.icdcmd.readByte((UInt32)(0x0206))
            print "  S-ICD CC1000 FREQ_0B = ",val

            # Start the test, the test patch will wait 10 seconds to allow for a break link
            self.icdcmd.writeUint16(Key.INT_VEC_TCMP0, 0x6A08)

            # break link with the S-ICD
            wfdeState = WaitForDisconnectedEventState(Key.DONT_CARE, 0x0)
            try:
                self.icdcmd.EventWaiter.execState(wfdeState, TimeSpan.FromSeconds(2))
            except Exception, ex:
                print str(ex)

            time.sleep(20.0)

            # Loop through all candidate frequencies and calibrate
            for index in range(0, self.loop_count):
                test_time = time.clock()
                print "Loop Index = ", index
    	        print "Test time = %.2d:%06.3f"%(test_time/60,test_time%60.0)
                if index%8 == 0:
                    print "Candidate Frequency = 402.8183MHz, LSI"
                elif index%8 == 1:
                    print "Candidate Frequency = 403.5108MHz, HSI"
                elif index%8 == 2:
                    print "Candi4ate Frequency = 402.4942MHz, LSI"
                elif index%8 == 3:
                    print "Candidate Frequency = 404.6167MHz, HSI"
                elif index%8 == 4:
                    print "Candidate Frequency = 402.7209MHz, HSI"
                elif index%8 == 5:
                    print "Candidate Frequency = 402.4049MHz, HSI"
                elif index%8 == 6:
                    print "Candidate Frequency = 404.5197MHz, LSI"
                elif index%8 == 7:
                    print "Candidate Frequency = 402.7049MHz, LSI"

                # get initial frequency values for channel 0
                val_2 = 0x35 #self.TestProcedure.ICD.readPrbFpga(0x305E)
                val_1 = 0xF0 #self.TestProcedure.ICD.readPrbFpga(0x3060)
                val_0 = 0x21 #self.TestProcedure.ICD.readPrbFpga(0x3062)
                freq_a_init = val_2*65536 + val_1*256 + val_0
                print "  PRB FREQ_A = ",freq_a_init

                val_2 = 0x35 #self.TestProcedure.ICD.readPrbFpga(0x3066)
                val_1 = 0xFA #self.TestProcedure.ICD.readPrbFpga(0x3068)
                val_0 = 0xCB #self.TestProcedure.ICD.readPrbFpga(0x306A)
                freq_b_init = val_2*65536 + val_1*256 + val_0
                print "  PRB FREQ_B = ",freq_b_init

                # Scan and link on Channel 0, with data inversion active
                self.TestProcedure.ICD.writePrbFpga(0x1026, 0x00)
                devList = self.icdcmd.scan(17, 2)
                print "  type(devList):",type(devList)
                print "  devList ",devList

                self.TestProcedure.ICD.writePrbFpga(0x3012, inv_flag)
                val = self.TestProcedure.ICD.readPrbFpga(0x1026)
                print "  Channel Selection = ",val
                val = self.TestProcedure.ICD.readPrbFpga(0x3012)
                print "  Data inversion = ",val

                self.icdcmd.connect((UInt32) (2100146))
                time.sleep(1)

                # Read CC1020 AFC register and verify correction logic
                val_0 = 0
                val_1 = 0
                for iter in range(0, 10):
                    val_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.AFC))
                    if val_0 > 127:
                        val_0 = val_0 - 256
                    print "  PRB AFC = ",val_0
                    val_1 = val_1 + val_0
                print "  PRB Average AFC = ",val_1/10.0

                #
                val_2 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_2A))
                val_1 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_1A))
                val_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_0A))
                freq_a = val_2*65536 + val_1*256 + val_0
                print "  PRB FREQ_A = ",freq_a

                val_2 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_2B))
                val_1 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_1B))
                val_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_0B))
                freq_b = val_2*65536 + val_1*256 + val_0
                print "  PRB FREQ_B = ",freq_b

                # compute frequency offset
                val = (freq_a -1)/2 - (freq_a_init-1)/2
                print "  PRB AFC_A = ",val
                val = (freq_b -1)/2 - (freq_b_init-1)/2
                print "  PRB AFC_B = ",val

                # set the filter to widest bandwidth to get an unsaturated RSSI
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FILTER))
                print "  PRB CC1020 FILTER = ", val
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FILTER), 0x80)
                time.sleep(0.080)

                # read RSSI 10 times and compute the average
                val_0 = 0
                val_1 = 0
                for iter in range(0, 10):
                    val_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                    print "  PRB RSSI = ",val_0
                    val_1 = val_1 + val_0
                print "  PRB Average RSSI = ",val_1/10.0

                # restore the filter setting
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FILTER), 0x22)
                time.sleep(0.080)

                # Dump the Tx/Rx cal results
                self.DumpSicdCalResults()

                # Write the calibration configuration table for a specific frequency
                self.writeCalConfigTable(index+1)
                self.icdcmd.ping()

                # Start the test, the test patch will wait 10 seconds to allow for a break link
                self.icdcmd.writeUint16(Key.INT_VEC_TCMP0, 0x6A08)

                # break link with the S-ICD
                wfdeState = WaitForDisconnectedEventState(Key.DONT_CARE, 0x0)
                try:
                    self.icdcmd.EventWaiter.execState(wfdeState, TimeSpan.FromSeconds(2))
                except Exception, ex:
                    print str(ex)

                time.sleep(20.0)

        self.passed = True

    def verify(self, parameter, expVal, actVal):
        self.TestProcedure.Log.addResult(parameter + " Expected: " + str(expVal) + " Actual: " + str(actVal))

    def writeCalControlTable(self, DoCalFlag, MaxCalTries, ExitDelaySecs):
        self.icdcmd.writeByte((UInt32)(0x0220), DoCalFlag)
        self.icdcmd.writeByte((UInt32)(0x0221), MaxCalTries)
        self.icdcmd.writeByte((UInt32)(0x0222), ExitDelaySecs)

    def initCalConfigTable(self):
        self.icdcmd.writeByte((UInt32)(0x0200), 0x11)
        self.icdcmd.writeByte((UInt32)(0x0201), 0x52)
        self.icdcmd.writeByte((UInt32)(0x0202), 0x00)
        self.icdcmd.writeByte((UInt32)(0x0203), 0x00)
        self.icdcmd.writeByte((UInt32)(0x0204), 0x51)
        self.icdcmd.writeByte((UInt32)(0x0205), 0xF6)
        self.icdcmd.writeByte((UInt32)(0x0206), 0x85)
        self.icdcmd.writeByte((UInt32)(0x0207), 0x03)
        self.icdcmd.writeByte((UInt32)(0x0208), 0x55)
        self.icdcmd.writeByte((UInt32)(0x0209), 0x40)
        self.icdcmd.writeByte((UInt32)(0x020A), 0x02)
        self.icdcmd.writeByte((UInt32)(0x020B), 0x0F)
        self.icdcmd.writeByte((UInt32)(0x020C), 0x60)
        self.icdcmd.writeByte((UInt32)(0x020D), 0x10)
        self.icdcmd.writeByte((UInt32)(0x020E), 0x26)
        self.icdcmd.writeByte((UInt32)(0x020F), 0xB7)
        self.icdcmd.writeByte((UInt32)(0x0210), 0x69)
        self.icdcmd.writeByte((UInt32)(0x0211), 0x50)
        self.icdcmd.writeByte((UInt32)(0x0212), 0x70)
        self.icdcmd.writeByte((UInt32)(0x0213), 0x01)
        self.icdcmd.writeByte((UInt32)(0x0214), 0x1C)
        self.icdcmd.writeByte((UInt32)(0x0215), 0x16)
        self.icdcmd.writeByte((UInt32)(0x0216), 0x10)
        self.icdcmd.writeByte((UInt32)(0x0217), 0x0A)
        self.icdcmd.writeByte((UInt32)(0x0218), 0x06)
        self.icdcmd.writeByte((UInt32)(0x0219), 0x03)
        self.icdcmd.writeByte((UInt32)(0x021A), 0x01)
        self.icdcmd.writeByte((UInt32)(0x021B), 0x03)
        self.icdcmd.writeByte((UInt32)(0x021C), 0x00)
        self.icdcmd.writeByte((UInt32)(0x021D), 0x08)
        self.icdcmd.writeByte((UInt32)(0x021E), 0x3F)
        self.icdcmd.writeByte((UInt32)(0x021F), 0x04)

    def writeCalConfigTable(self, index):
        if index%8 == 0:
            #Candidate Frequency = 402.8183MHz settings
            # S-ICD
            self.icdcmd.writeByte((UInt32)(0x0201), 0x58)
            self.icdcmd.writeByte((UInt32)(0x0202), 0xA0)
            self.icdcmd.writeByte((UInt32)(0x0203), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0204), 0x58)
            self.icdcmd.writeByte((UInt32)(0x0205), 0xA6)
            self.icdcmd.writeByte((UInt32)(0x0206), 0xA8)
            self.icdcmd.writeByte((UInt32)(0x0207), 0x03)
            self.icdcmd.writeByte((UInt32)(0x0208), 0x9C)
            self.icdcmd.writeByte((UInt32)(0x020C), 0x68)

        elif index%8 == 1:
            #Candidate Frequency = 403.5108MHz settings
            # S-ICD
            self.icdcmd.writeByte((UInt32)(0x0201), 0x52)
            self.icdcmd.writeByte((UInt32)(0x0202), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0203), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0204), 0x51)
            self.icdcmd.writeByte((UInt32)(0x0205), 0xF6)
            self.icdcmd.writeByte((UInt32)(0x0206), 0x85)
            self.icdcmd.writeByte((UInt32)(0x0207), 0x03)
            self.icdcmd.writeByte((UInt32)(0x0208), 0x55)
            self.icdcmd.writeByte((UInt32)(0x020C), 0x60)

        elif index%8 == 2:
            #Candidate Frequency = 402.4942MHz settings
            # S-ICD
            self.icdcmd.writeByte((UInt32)(0x0201), 0x5F)
            self.icdcmd.writeByte((UInt32)(0x0202), 0x60)
            self.icdcmd.writeByte((UInt32)(0x0203), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0204), 0x5F)
            self.icdcmd.writeByte((UInt32)(0x0205), 0x67)
            self.icdcmd.writeByte((UInt32)(0x0206), 0x2C)
            self.icdcmd.writeByte((UInt32)(0x0207), 0x03)
            self.icdcmd.writeByte((UInt32)(0x0208), 0xE4)
            self.icdcmd.writeByte((UInt32)(0x020C), 0x70)

        elif index%8 == 3:
            #Candidate Frequency = 404.6167MHz settings
            # S-ICD
            self.icdcmd.writeByte((UInt32)(0x0201), 0x44)
            self.icdcmd.writeByte((UInt32)(0x0202), 0x80)
            self.icdcmd.writeByte((UInt32)(0x0203), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0204), 0x44)
            self.icdcmd.writeByte((UInt32)(0x0205), 0x78)
            self.icdcmd.writeByte((UInt32)(0x0206), 0x1A)
            self.icdcmd.writeByte((UInt32)(0x0207), 0x02)
            self.icdcmd.writeByte((UInt32)(0x0208), 0xC7)
            self.icdcmd.writeByte((UInt32)(0x020C), 0x50)

        elif index%8 == 4:
            #Candidate Frequency = 402.7209MHz, settings
            # S-ICD
            self.icdcmd.writeByte((UInt32)(0x0201), 0x5F)
            self.icdcmd.writeByte((UInt32)(0x0202), 0x80)
            self.icdcmd.writeByte((UInt32)(0x0203), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0204), 0x5F)
            self.icdcmd.writeByte((UInt32)(0x0205), 0x74)
            self.icdcmd.writeByte((UInt32)(0x0206), 0xF1)
            self.icdcmd.writeByte((UInt32)(0x0207), 0x03)
            self.icdcmd.writeByte((UInt32)(0x0208), 0xE4)
            self.icdcmd.writeByte((UInt32)(0x020C), 0x70)

        elif index%8 == 5:
            #Candidate Frequency = 402.4049MHz settings
            # S-ICD
            self.icdcmd.writeByte((UInt32)(0x0201), 0x44)
            self.icdcmd.writeByte((UInt32)(0x0202), 0x20)
            self.icdcmd.writeByte((UInt32)(0x0203), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0204), 0x44)
            self.icdcmd.writeByte((UInt32)(0x0205), 0x18)
            self.icdcmd.writeByte((UInt32)(0x0206), 0x1A)
            self.icdcmd.writeByte((UInt32)(0x0207), 0x02)
            self.icdcmd.writeByte((UInt32)(0x0208), 0xC7)
            self.icdcmd.writeByte((UInt32)(0x020C), 0x50)

        elif index%8 == 6:
            #Candidate Frequency = 404.5197MHz settings
            # S-ICD
            self.icdcmd.writeByte((UInt32)(0x0201), 0x59)
            self.icdcmd.writeByte((UInt32)(0x0202), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0203), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0204), 0x59)
            self.icdcmd.writeByte((UInt32)(0x0205), 0x06)
            self.icdcmd.writeByte((UInt32)(0x0206), 0xA8)
            self.icdcmd.writeByte((UInt32)(0x0207), 0x03)
            self.icdcmd.writeByte((UInt32)(0x0208), 0x9C)
            self.icdcmd.writeByte((UInt32)(0x020C), 0x68)

        elif index%8 == 7:
            #Candidate Frequency = 402.7049MHz settings
            # S-ICD
            self.icdcmd.writeByte((UInt32)(0x0201), 0x44)
            self.icdcmd.writeByte((UInt32)(0x0202), 0x20)
            self.icdcmd.writeByte((UInt32)(0x0203), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0204), 0x44)
            self.icdcmd.writeByte((UInt32)(0x0205), 0x25)
            self.icdcmd.writeByte((UInt32)(0x0206), 0x1F)
            self.icdcmd.writeByte((UInt32)(0x0207), 0x02)
            self.icdcmd.writeByte((UInt32)(0x0208), 0xC7)
            self.icdcmd.writeByte((UInt32)(0x020C), 0x50)

	else:
            #Candidate Frequency = 403.5108MHz settings
            # S-ICD
            self.icdcmd.writeByte((UInt32)(0x0201), 0x52)
            self.icdcmd.writeByte((UInt32)(0x0202), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0203), 0x00)
            self.icdcmd.writeByte((UInt32)(0x0204), 0x51)
            self.icdcmd.writeByte((UInt32)(0x0205), 0xF6)
            self.icdcmd.writeByte((UInt32)(0x0206), 0x85)
            self.icdcmd.writeByte((UInt32)(0x0207), 0x03)
            self.icdcmd.writeByte((UInt32)(0x0208), 0x55)
            self.icdcmd.writeByte((UInt32)(0x020C), 0x60)

    def DumpSicdCalResults(self):
        val = self.icdcmd.readByte((UInt32)(0x0201))
        print "  S-ICD CC1000 FREQ_2A = ",val
        val = self.icdcmd.readByte((UInt32)(0x0202))
        print "  S-ICD CC1000 FREQ_1A = ",val
        val = self.icdcmd.readByte((UInt32)(0x0203))
        print "  S-ICD CC1000 FREQ_0A = ",val
        val = self.icdcmd.readByte((UInt32)(0x0204))
        print "  S-ICD CC1000 FREQ_2B = ",val
        val = self.icdcmd.readByte((UInt32)(0x0205))
        print "  S-ICD CC1000 FREQ_1B = ",val
        val = self.icdcmd.readByte((UInt32)(0x0206))
        print "  S-ICD CC1000 FREQ_0B = ",val
        val = self.icdcmd.readByte((UInt32)(0x0230))
        print "  S-ICD CC1000 Tx Test6 = ",val
        val = self.icdcmd.readByte((UInt32)(0x0231))
        print "  S-ICD CC1000 Tx Test5 = ",val
        val = self.icdcmd.readByte((UInt32)(0x0232))
        print "  S-ICD CC1000 Tx Test4 = ",val
        val = self.icdcmd.readByte((UInt32)(0x0233))
        print "  S-ICD CC1000 Tx Test3 = ",val
        val = self.icdcmd.readByte((UInt32)(0x0234))
        print "  S-ICD CC1000 Tx Test2 = ",val
        val = self.icdcmd.readByte((UInt32)(0x0235))
        print "  S-ICD CC1000 Tx Test1 = ",val
        val = self.icdcmd.readByte((UInt32)(0x0236))
        print "  S-ICD CC1000 Tx Test0 = ",val
        val = self.icdcmd.readByte((UInt32)(0x0237))
        print "  S-ICD CC1000 Rx Test6 = ",val
        val = self.icdcmd.readByte((UInt32)(0x0238))
        print "  S-ICD CC1000 Rx Test5 = ",val
        val = self.icdcmd.readByte((UInt32)(0x0239))
        print "  S-ICD CC1000 Rx Test4 = ",val
        val = self.icdcmd.readByte((UInt32)(0x023A))
        print "  S-ICD CC1000 Rx Test3 = ",val
        val = self.icdcmd.readByte((UInt32)(0x023B))
        print "  S-ICD CC1000 Rx Test2 = ",val
        val = self.icdcmd.readByte((UInt32)(0x023C))
        print "  S-ICD CC1000 Rx Test1 = ",val
        val = self.icdcmd.readByte((UInt32)(0x023D))
        print "  S-ICD CC1000 Rx Test0 = ",val
        val = self.icdcmd.readByte((UInt32)(0x023E))
        print "  S-ICD CC1000 Tx Cal Failure Count = ",val
        val = self.icdcmd.readByte((UInt32)(0x023F))
        print "  S-ICD CC1000 Tx Lock Failure Count = ",val
        val = self.icdcmd.readByte((UInt32)(0x0240))
        print "  S-ICD CC1000 Rx Cal Failure Count = ",val
        val = self.icdcmd.readByte((UInt32)(0x0241))
        print "  S-ICD CC1000 Rx Lock Failure Count = ",val

    def DumpCalResult(self):
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_2A))
        print "  PRB CC1020 FREQ_2A = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_1A))
        print "  PRB CC1020 FREQ_1A = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_0A))
        print "  PRB CC1020 FREQ_0A = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.CLOCK_A))
        print "  PRB CC1020 CLOCK_A = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_2B))
        print "  PRB CC1020 FREQ_2B = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_1B))
        print "  PRB CC1020 FREQ_1B = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_0B))
        print "  PRB CC1020 FREQ_0B = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.CLOCK_B))
        print "  PRB CC1020 CLOCK_B = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.MATCH))
        print "  PRB CC1020 MATCH = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS1))
        print "  PRB CC1020 STATUS1 = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS2))
        print "  PRB CC1020 STATUS2 = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS3))
        print "  PRB CC1020 STATUS3 = ",val

def main():
    optionsPath = ".\options.xml"
    configPath = ".\settings.cfg"
    psScript = sicdCalScript(optionsPath, configPath)
    psScript.run()

if __name__ == '__main__':
    main()
