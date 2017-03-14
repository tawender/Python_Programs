#-------------------------------------------------------------------------------
# Name:        
# Purpose:     
#	       
#
# Author:      
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import sys
import time
from ConfigParser import ConfigParser

sys.path.append(r'..\..\PyTES')
from PyTES import *

# a modified pyvisa
sys.path.append(r'c:\Program Files\Python 2.7.5\Lib\site-packages\pyvisa')
#import visa

from Instruments import HP_8648_sig_gen as sig_gen

import clr
clr.AddReference("System")
from System import *

clr.AddReferenceToFile("Config.dll")
import Config


class plotter(object):
    """this class will use a system call to py
    """
    def __init__(self,sa,plot_path):
        self.sa = sa        #spectrum analyzer instance
        self.path = plot_path

        self.conv_fact = 1000000.0 #work in MHz not Hz
        self.plot_num = 1   #increment plot number

    def set_conversion_factor(self,c):
        self.freq_conversion_factor = c

    def make_plot(self,title,y_data,x_units,y_units):

        plotname = "%d_"%(self.plot_num)+title
        self.plot_num += 1

        self.make_temp_file('tmp_data.txt',y_data)

        x_scale_min = self.sa.get_startf()
        x_scale_max = self.sa.get_stopf()

        y_scale= self.sa.get_y_scale()
        y_scale_min = y_scale[0]
        y_scale_max = y_scale[1]

        os.system('python plot_spec_an.py' + \
                    ' "%s"'%self.path + \
                    ' "%s"'%plotname + \
                    ' tmp_data.txt' + \
                    ' "%s" "%s"'%(x_units,y_units) + \
                    " %f %f"%(x_scale_min,x_scale_max) + \
                    " %f %f"%(y_scale_min,y_scale_max))

        os.remove('tmp_data.txt')
        print 'temporary files deleted'

    def make_temp_file(self,f_name,data):
        f = open(f_name,'w')
        for item in data:
            f.write("%f\n"%item)
        f.close()


class WaitForDisconnectedEventState(IScriptExecState):
    def __init__(self, key, data):
        self.key = key
        self.data = data

    def doEntryAction(self, sm):
        sm.ICD.breakLink()
        return

    def processEvent(self, sm, ev):
        return type(ev)==DisconnectedEvent

class prbIqiCalScript(PyScript):
    def __init__(self, optionsPath, configPath):
        # Read configuration
        config = ConfigParser()
        config.read(configPath)

        logDir = config.get('Location', 'log_dir')
        logName = 'prbIqiCalScriptLog ' + DateTime.Now.ToString('yyyy.MM.dd HH.mm.ss') + '.log'
        buildNumber = int(config.get('Firmware', 'build_num'), 0)

        super(prbIqiCalScript, self).__init__(optionsPath, buildNumber, Path.Combine(logDir, logName))

        self.loop_count = int(config.get('Sampling', 'loop_count'))

    def script(self):
        # Read FPGA address 0x3000 and verify the response is 0x12.
        val = self.TestProcedure.ICD.readPrbFpga(0x3000)
        self.verify("FPGA 0x3000", 0x12, val)
        if val != 0x12:
            self.verify("ERROR", 0x12, val)

        sg=sig_gen("GPIB::18",'SIG_GEN')

        # read the MATCH value from EEPROM and write to the PRB
#need to add read here...
        # write the legacy frequency to PRB channel 0 registers
        self.TestProcedure.ICD.writePrbFpga(0x3024, 0x35)
        self.TestProcedure.ICD.writePrbFpga(0x3026, 0xF0)
        self.TestProcedure.ICD.writePrbFpga(0x3028, 0x21)
        self.TestProcedure.ICD.writePrbFpga(0x302C, 0x35)
        self.TestProcedure.ICD.writePrbFpga(0x302E, 0xFA)
        self.TestProcedure.ICD.writePrbFpga(0x3030, 0xCB)
        # calibrate once on channel 0
        self.TestProcedure.ICD.calibrateCc1020()
        self.DumpCalResult()

        XP = 0
        XG = 0
        DX = 64
         
        for idx in range(0, self.loop_count):
            if idx != 0:
                DX = DX/2
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.GAIN_COMP), XG)

            if (XP+2*DX) < 127:
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.PHASE_COMP), XP+2*DX)
            else:
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.PHASE_COMP), 127)
            time.sleep(0.006)

            # read RSSI 10 times and compute the average
            Y4_0 = 0
            Y4_1 = 0
            for idx_i in range(0, 10):
                Y4_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                print "  CC1020 RSSI = ",Y4_0
                Y4_1 = Y4_1 + Y4_0
                time.sleep(0.001)
            Y4_1 = Y4_1/10.0
            print "  CC1020 Average RSSI = ",Y4_1

            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.PHASE_COMP), XP+DX)
            time.sleep(0.006)

            # read RSSI 10 times and compute the average
            Y3_0 = 0
            Y3_1 = 0
            for idx_i in range(0, 10):
                Y3_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                print "  CC1020 RSSI = ",Y3_0
                Y3_1 = Y3_1 + Y3_0
                time.sleep(0.001)
            Y3_1 = Y3_1/10.0
            print "  CC1020 Average RSSI = ",Y3_1

            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.PHASE_COMP), XP)
            time.sleep(0.006)

            # read RSSI 10 times and compute the average
            Y2_0 = 0
            Y2_1 = 0
            for idx_i in range(0, 10):
                Y2_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                print "  CC1020 RSSI = ",Y2_0
                Y2_1 = Y2_1 + Y2_0
                time.sleep(0.001)
            Y2_1 = Y2_1/10.0
            print "  CC1020 Average RSSI = ",Y2_1

            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.PHASE_COMP), XP-DX)
            time.sleep(0.006)

            # read RSSI 10 times and compute the average
            Y1_0 = 0
            Y1_1 = 0
            for idx_i in range(0, 10):
                Y1_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                print "  CC1020 RSSI = ",Y1_0
                Y1_1 = Y1_1 + Y1_0
                time.sleep(0.001)
            Y1_1 = Y1_1/10.0
            print "  CC1020 Average RSSI = ",Y1_1

# this seems wrong, potentially writing a negative number?
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.PHASE_COMP), XP-2*DX)
            time.sleep(0.006)

            # read RSSI 10 times and compute the average
            Y0_0 = 0
            Y0_1 = 0
            for idx_i in range(0, 10):
                Y0_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                print "  CC1020 RSSI = ",Y0_0
                Y0_1 = Y0_1 + Y0_0
                time.sleep(0.001)
            Y0_1 = Y0_1/10.0
            print "  CC1020 Average RSSI = ",Y0_1

            AP = 2*(Y0_1-Y2_1+Y4_1) - (Y1_1+Y3_1)
            if AP > 0:
                DP = round(7*DX*(2*(Y0_1-Y4_1)+Y1_1-Y3_1)/(10*AP),0)
            elif (Y0_1+Y1_1) > (Y3_1+Y4_1):
                DP = DX
            else:
                DP = -DX

            if DP > DX:
                DP = DX
            elif DP < -DX: 
                DP = -DX

            XP = XP + DP

            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.PHASE_COMP), XP)
            time.sleep(0.006)

	    if (XG+2*DX) < 127:
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.GAIN_COMP), XG+2*DX)
            else:
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.GAIN_COMP), 0x7F)
            time.sleep(0.006)

            # read RSSI 10 times and compute the average
            Y4_0 = 0
            Y4_1 = 0
            for idx_i in range(0, 10):
                Y4_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                print "  CC1020 RSSI = ",Y4_0
                Y4_1 = Y4_1 + Y4_0
                time.sleep(0.001)
            Y4_1 = Y4_1/10.0
            print "  CC1020 Average RSSI = ",Y4_1

            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.GAIN_COMP), XG+DX)
            time.sleep(0.006)

            # read RSSI 10 times and compute the average
            Y3_0 = 0
            Y3_1 = 0
            for idx_i in range(0, 10):
                Y3_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                print "  CC1020 RSSI = ",Y3_0
                Y3_1 = Y3_1 + Y3_0
                time.sleep(0.001)
            Y3_1 = Y3_1/10.0
            print "  CC1020 Average RSSI = ",Y3_1

            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.GAIN_COMP), XG)
            time.sleep(0.006)

            # read RSSI 10 times and compute the average
            Y2_0 = 0
            Y2_1 = 0
            for idx_i in range(0, 10):
                Y2_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                print "  CC1020 RSSI = ",Y2_0
                Y2_1 = Y2_1 + Y2_0
                time.sleep(0.001)
            Y2_1 = Y2_1/10.0
            print "  CC1020 Average RSSI = ",Y2_1

            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.GAIN_COMP), XG-DX)
            time.sleep(0.006)

            # read RSSI 10 times and compute the average
            Y1_0 = 0
            Y1_1 = 0
            for idx_i in range(0, 10):
                Y1_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                print "  CC1020 RSSI = ",Y1_0
                Y1_1 = Y1_1 + Y1_0
                time.sleep(0.001)
            Y1_1 = Y1_1/10.0
            print "  CC1020 Average RSSI = ",Y1_1

            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.GAIN_COMP), XG-2*DX)
            time.sleep(0.006)
	    
            # read RSSI 10 times and compute the average
            Y0_0 = 0
            Y0_1 = 0
            for idx_i in range(0, 10):
                Y0_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                print "  CC1020 RSSI = ",Y0_0
                Y0_1 = Y0_1 + Y0_0
                time.sleep(0.001)
            Y0_1 = Y0_1/10.0
            print "  CC1020 Average RSSI = ",Y0_1

            AG = 2*(Y0_1-Y2_1+Y4_1) - (Y1_1+Y3_1)
            if AG > 0:
                DG = round(7*DX*(2*(Y0_1-Y4_1)+Y1_1-Y3_1)/(10*AG),0)
            elif (Y0_1+Y1_1) > (Y3_1+Y4_1):
                DG = DX
            else:
                DG = -DX

            if DG > DX:
                DG = DX
            elif DG < -DX: 
                DG = -DX

            XG = XG + DG
            if DX > 1:
                print "  REPEAT!!!!!"
            else:
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.PHASE_COMP), XP)
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.GAIN_COMP), XG)

            sg.output_off()

        self.passed = True

    def verify(self, parameter, expVal, actVal):
        self.TestProcedure.Log.addResult(parameter + " Expected: " + str(expVal) + " Actual: " + str(actVal))

    def DumpCalResult(self):
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_2A))
        print "  CC1020 FREQ_2A = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_1A))
        print "  CC1020 FREQ_1A = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_0A))
        print "  CC1020 FREQ_0A = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.CLOCK_A))
        print "  CC1020 CLOCK_A = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_2B))
        print "  CC1020 FREQ_2B = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_1B))
        print "  CC1020 FREQ_1B = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_0B))
        print "  CC1020 FREQ_0B = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.CLOCK_B))
        print "  CC1020 CLOCK_B = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.MATCH))
        print "  CC1020 MATCH = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS1))
        print "  CC1020 STATUS1 = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS2))
        print "  CC1020 STATUS2 = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS3))
        print "  CC1020 STATUS3 = ", val

    def writeFreqToCC1020(self, index):
        # Write the frequency update locations in S-ICD RAM and the PRB 
        if index%9 == 0:
            #Candidate Frequency = 402.8183MHz settings
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2A), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1A), 0xD8)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0A), 0x15)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2B), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1B), 0xE2)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0B), 0xBF)

        elif index%9 == 1:
            #Candidate Frequency = 403.5108MHz settings
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2A), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1A), 0xF0)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0A), 0x21)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2B), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1B), 0xFA)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0B), 0xCB)

        elif index%9 == 2:
            #Candidate Frequency = 402.4942MHz settings
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2A), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1A), 0xCC)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0A), 0xD3)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2B), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1B), 0xD7)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0B), 0x7F)

        elif index%9 == 3:
            #Candidate Frequency = 404.6167MHz settings
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2A), 0x36)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1A), 0x16)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0A), 0x87)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2B), 0x36)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1B), 0x21)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0B), 0x31)

        elif index%9 == 4:
            #Candidate Frequency = 402.7209MHz, settings
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2A), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1A), 0xD4)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0A), 0xB3)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2B), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1B), 0xDF)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0B), 0x5D)

        elif index%9 == 5:
            #Candidate Frequency = 402.4049MHz settings
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2A), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1A), 0xC9)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0A), 0xB9)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2B), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1B), 0xD4)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0B), 0x65)

        elif index%9 == 6:
            #Candidate Frequency = 404.5197MHz settings
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2A), 0x36)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1A), 0x13)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0A), 0x29)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2B), 0x36)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1B), 0x1D)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0B), 0xD3)

        elif index%9 == 7:
            #Candidate Frequency = 402.7049MHz settings
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2A), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1A), 0xD4)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0A), 0x25)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2B), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1B), 0xDE)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0B), 0xCF)

	else:
            #Candidate Frequency = 403.5108MHz settings
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2A), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1A), 0xF0)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0A), 0x21)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_2B), 0x35)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_1B), 0xFA)
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FREQ_0B), 0xCB)

def main():
    optionsPath = ".\options.xml"
    configPath = ".\settings.cfg"
    psScript = prbIqiCalScript(optionsPath, configPath)
    psScript.run()

if __name__ == '__main__':
    main()
