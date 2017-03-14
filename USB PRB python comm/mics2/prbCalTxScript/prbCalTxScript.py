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
import os
from ConfigParser import ConfigParser

sys.path.append(r'..\..\PyTES')
from PyTES import *

sys.path.append(r'c:\Program Files\Python 2.7.5\Lib\site-packages')

# a modified pyvisa
sys.path.append(r'c:\Program Files\Python 2.7.5\Lib\site-packages\pyvisa')

# path to common files
sys.path.append(r'c:\python_programs\mics2')

from Instruments import Advantest_R3465 as spec_anal

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

#        os.system('python ..\plot_spec_an.py' + \
        os.system('python c:\python_programs\mics2\plot_spec_an.py' + \
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

class prbCalTxScript(PyScript):
    def __init__(self, optionsPath, configPath):
        # Read configuration
        config = ConfigParser()
        config.read(configPath)

        logDir = config.get('Location', 'log_dir')
        logName = 'prbCalTxScriptLog ' + DateTime.Now.ToString('yyyy.MM.dd HH.mm.ss') + '.log'
        buildNumber = int(config.get('Firmware', 'build_num'), 0)

        super(prbCalTxScript, self).__init__(optionsPath, buildNumber, Path.Combine(logDir, logName))

        self.loop_count = int(config.get('Sampling', 'loop_count'))

        global test_dir
        dir_name = "Results"
        cwd = os.getcwd()
        test_dir = cwd + "/" + dir_name
        os.mkdir(test_dir)

    def script(self):
        # Read FPGA address 0x3000 and verify the response is 0x12.
        val = self.TestProcedure.ICD.readPrbFpga(0x3000)
        self.verify("FPGA 0x3000", 0x12, val)
        if val != 0x12:
            self.verify("ERROR", 0x12, val)

        #*********instrument setup***************************************
        print "Creating instrument..."
        sa=spec_anal("GPIB::8",'SPEC_ANAL')
        #****************************************************************

        #*********plotter setup******************************************
        plots = plotter(sa,test_dir)
        #****************************************************************

        # read the MATCH value from EEPROM and write to the PRB
#need to add read here...
        # calibrate once on channel 0
        self.TestProcedure.ICD.calibrateCc1020()
        val = self.TestProcedure.ICD.readPrbFpga(0x2012)
        print "  PRB badCal = ", val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS))
        print "  PRB STATUS register = ", val
        self.DumpCalResult()
        channel = 0

        #5-45 5 degree steps
        temperatures = range(5,46,5)
        stabilization_mins = 10
        chamber = watlowF4ipy.WatlowF4_temp_window(3,debug=True)

        for temperature in temperatures:

            chamber.set_temperature_and_time(temperature,temperature-0.3,
                                            temperature+0.3,stabilization_mins)

            while chamber.dwelltime_endpoint_reached() == False:
                #pause before checking the flag again
                time.sleep(2)

            sa.set_ref_level_dB(0)
            sa.set_span_kHz(400)
            sa.set_resolutionBW_kHz(3)
            sa.set_sweep_time_milliseconds(200)

            for index in range(0, self.loop_count):
                test_time = time.clock() 
                print "Loop Index = ", index
	        print "Test time = %.2d:%06.3f"%(test_time/60,test_time%60.0)

#        for index in range(0, 2):
                if index%9 == 0:
                    print "Candidate Frequency = 402.8183MHz, LSI"
                    sa.set_center_frequency_MHz(402.8183)
                elif index%9 == 1:
                    print "Candidate Frequency = 403.5108MHz, HSI"
                    sa.set_center_frequency_MHz(403.5108)
                elif index%9 == 2:
                    print "Candidate Frequency = 402.4942MHz, LSI"
                    sa.set_center_frequency_MHz(402.4942)
                elif index%9 == 3:
                    print "Candidate Frequency = 404.6167MHz, HSI"
                    sa.set_center_frequency_MHz(404.6167)
                elif index%9 == 4:
                    print "Candidate Frequency = 402.7209MHz, HSI"
                    sa.set_center_frequency_MHz(402.7209)
                elif index%9 == 5:
                    print "Candidate Frequency = 402.4049MHz, HSI"
                    sa.set_center_frequency_MHz(402.4049)
                elif index%9 == 6:
                    print "Candidate Frequency = 404.5197MHz, LSI"
                    sa.set_center_frequency_MHz(404.5197)
                elif index%9 == 7:
                    print "Candidate Frequency = 402.7049MHz, LSI"
                    sa.set_center_frequency_MHz(402.7049)
                else:
                    print "Candidate Frequency = 403.5108MHz, HSI"
                    sa.set_center_frequency_MHz(403.5108)

                time.sleep(1)

                # write the candidate frequency to PRB channel 0 registers
                self.writeFreqToPRB(index, 0)
                # write the candidate frequency to PRB channel 1 registers
                self.writeFreqToPRB(index, 1)

                # perform calibration and dump results
                self.TestProcedure.ICD.calibrateCc1020()
# is badcal checked and reported? is there a wait until the cal interrupt?
                time.sleep(0.300)
                val = self.TestProcedure.ICD.readPrbFpga(0x2012)
                print "  PRB badCal = ", val
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS))
                print "  PRB STATUS register = ", val
                self.DumpCalResult()

                # write the legacy frequency to PRB channel 0 registers
                self.writeFreqToPRB(1, channel)
                # perform calibration and dump results
                self.TestProcedure.ICD.calibrateCc1020()
# is badcal checked and reported? is there a wait until the cal interrupt?
                time.sleep(0.300)
                val = self.TestProcedure.ICD.readPrbFpga(0x2012)
                print "  PRB badCal = ", val
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS))
                print "  PRB STATUS register = ", val
                self.DumpCalResult()

                # perform an LBT instruction and log results 
# how do we issue an LBT and capture the interrupt packet? 
                self.TestProcedure.ICD.writePrbFpga(0x1008, 0x10)
                time.sleep(0.400)
                val = self.TestProcedure.ICD.readPrbFpga(0x1020)
                print "  PRB LIC = ", val
                val = self.TestProcedure.ICD.readPrbFpga(0x1026)
                print "  PRB Channel Selection = ", val
                val = self.TestProcedure.ICD.readPrbFpga(0x1022)
                print "  PRB Channel 0 RSSI = ", val
                val = self.TestProcedure.ICD.readPrbFpga(0x1024)
                print "  PRB Channel 1 RSSI = ", val

#note, after LBT the CC1020 registers contain the channel 1 values
                val_2 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_2A))
                val_1 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_1A))
                val_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_0A))
                freq_a = val_2*65536 + val_1*256 + val_0 
                print "  CC1020 FREQ_A = ",freq_a

                val_2 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_2B))
                val_1 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_1B))
                val_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_0B))
                freq_b = val_2*65536 + val_1*256 + val_0 
                print "  CC1020 FREQ_B = ",freq_b

                # place CC1020 into receive mode
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.MAIN), 0x01)
#does the write/read routines wait until cc1020 not busy?
                time.sleep(0.080)
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS))
                print "  PRB STATUS register = ", val

                # log the filter setting 
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FILTER))
                print "  CC1020 FILTER = ", val
                time.sleep(0.080)

                # read RSSI 10 times and compute the average
                val_0 = 0
                val_1 = 0
                for iter in range(0, 10):
                    val_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.RSSI))
                    print "  CC1020 RSSI = ",val_0
                    val_1 = val_1 + val_0
                print "  CC1020 Average RSSI = ",val_1/10.0

                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.MAIN), 0x1F)
                time.sleep(0.080)

                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.MODEM))
                print "  CC1020 MODEM = ", val
                time.sleep(0.080)
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.DEVIATION))
                print "  CC1020 DEVIATION = ", val
                time.sleep(0.080)

                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.MAIN), 0xC1)
                time.sleep(0.080)
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS))
                print "  PRB STATUS register = ", val
                time.sleep(1)
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.MAIN))
                print "  CC1020 MAIN = ", val

# add SA commands to measure frequency and power for the peak output- read ten times and record the average
                sa.set_marker_findpeak()
                time.sleep(2.000)
                # read peak 10 times and compute the average
                freq_0 = 0
                freq_1 = 0
                pwr_0 = 0
                pwr_1 = 0
                for iter in range(0, 10):
                    freq_0 = sa.get_marker_frequency()
                    print "  PRB Tx frequency = ", freq_0
                    pwr_0 = sa.get_marker_power_level()
                    print "  PRB Tx power = ", pwr_0
                    freq_1 = freq_1 + freq_0
                    pwr_1 = pwr_1 + pwr_0
                print "  PRB Ave Frequency = ",freq_1/10.0
                print "  PRB Ave Power = ",pwr_1/10.0
            
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.DEVIATION), 0xD9)
                time.sleep(0.080)

                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.MODEM))
                print "  CC1020 MODEM = ", val
                time.sleep(0.080)
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.DEVIATION))
                print "  CC1020 DEVIATION = ", val
                time.sleep(1)

                # read peak 10 times and compute the average
                sa.set_marker_findpeak()
                time.sleep(2.000)
                freq_0 = 0
                freq_1 = 0
                pwr_0 = 0
                pwr_1 = 0
                for iter in range(0, 10):
                    freq_0 = sa.get_marker_frequency()
                    print "  PRB Tx frequency = ", freq_0
                    pwr_0 = sa.get_marker_power_level()
                    print "  PRB Tx power = ", pwr_0
                    freq_1 = freq_1 + freq_0
                    pwr_1 = pwr_1 + pwr_0
                print "  PRB Ave Frequency = ",freq_1/10.0
                print "  PRB Ave Power = ",pwr_1/10.0
            
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.DEVIATION), 0x59)
                time.sleep(0.080)

                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.MODEM))
                print "  CC1020 MODEM = ", val
                time.sleep(0.080)
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.DEVIATION))
                print "  CC1020 DEVIATION = ", val
                time.sleep(0.500)

                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.MAIN), 0x1F)
                time.sleep(0.080)

            for index in range(0, self.loop_count):
                if index%9 == 0:
                    print "Candidate Frequency = 402.8183MHz, LSI"
                    sa.set_center_frequency_MHz(402.8183)
                elif index%9 == 1:
                    print "Candidate Frequency = 403.5108MHz, HSI"
                    sa.set_center_frequency_MHz(403.5108)
                elif index%9 == 2:
                    print "Candidate Frequency = 402.4942MHz, LSI"
                    sa.set_center_frequency_MHz(402.4942)
                elif index%9 == 3:
                    print "Candidate Frequency = 404.6167MHz, HSI"
                    sa.set_center_frequency_MHz(404.6167)
                elif index%9 == 4:
                    print "Candidate Frequency = 402.7209MHz, HSI"
                    sa.set_center_frequency_MHz(402.7209)
                elif index%9 == 5:
                    print "Candidate Frequency = 402.4049MHz, HSI"
                    sa.set_center_frequency_MHz(402.4049)
                elif index%9 == 6:
                    print "Candidate Frequency = 404.5197MHz, LSI"
                    sa.set_center_frequency_MHz(404.5197)
                elif index%9 == 7:
                    print "Candidate Frequency = 402.7049MHz, LSI"
                    sa.set_center_frequency_MHz(402.7049)
                else:
                    print "Candidate Frequency = 403.5108MHz, HSI"
                    sa.set_center_frequency_MHz(403.5108)

                # write the legacy frequency to PRB channel 0 registers
                self.writeFreqToPRB(1, 0)
                # write the candidate frequency to PRB channel 1 registers
                self.writeFreqToPRB(index, 1)
                # perform calibration and dump results
                self.TestProcedure.ICD.calibrateCc1020()
# is badcal checked and reported? is there a wait until the cal interrupt?
                time.sleep(0.300)
                val = self.TestProcedure.ICD.readPrbFpga(0x2012)
                print "  PRB badCal = ", val
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS))
                print "  PRB STATUS register = ", val
                self.DumpCalResult()

                # perform an LBT to place channel 1 frequency into CC1020
                self.TestProcedure.ICD.writePrbFpga(0x1008, 0x10)
                time.sleep(1)

                # turn off the CC1020 and place into PN9 mode
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.MAIN), 0x1F)
                time.sleep(0.080)
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.MODEM), 0x54)
                time.sleep(0.080)
                # turn on CC1020 in transmit mode
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.MAIN), 0xC1)
                time.sleep(0.080)
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS))
                print "  PRB STATUS register = ", val

                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.MODEM))
                print "  CC1020 MODEM = ", val
                time.sleep(0.080)
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.DEVIATION))
                print "  CC1020 DEVIATION = ", val
                time.sleep(0.500)

                time.sleep(2)
                sa.set_OBW_times_to_average(30)
                sa.set_occupied_bandwidth_pct(99)
                sa.turn_OBW_averages_on()
                (a,obw,c)=sa.measure_occupied_bandwidth()
                print "  PRB OBW = ", obw
                d = sa.get_data()
                name='Occupied Bandwidth (PN9 pattern)'
                x_units = 'frequency(MHz)'
                y_units = 'signal power('+sa.get_units()+')'
                plots.make_plot(name,d,x_units,y_units)

                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.DEVIATION), 0xD9)
                time.sleep(0.080)

                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.MODEM))
                print "  CC1020 MODEM = ", val
                time.sleep(0.080)
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.DEVIATION))
                print "  CC1020 DEVIATION = ", val
                time.sleep(0.500)

                time.sleep(2)
                (a,obw,c)=sa.measure_occupied_bandwidth()
                print "  PRB OBW = ", obw
                d = sa.get_data()
                name='Occupied Bandwidth (PN9 pattern)'
                x_units = 'frequency(MHz)'
                y_units = 'signal power('+sa.get_units()+')'
                plots.make_plot(name,d,x_units,y_units)

                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.DEVIATION), 0x59)
                time.sleep(0.080)

            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.MAIN), 0x1F)
            sa.reset()

        self.passed = True
        self.TestProcedure.ICD.writeCC1020(int(CC1020Register.MAIN), 0x1F)
        print "Test complete, run prbRssiScript"

    def verify(self, parameter, expVal, actVal):
        self.TestProcedure.Log.addResult(parameter + " Expected: " + str(expVal) + " Actual: " + str(actVal))

    def DumpCalResult(self):
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_2A))
        print "PRB CC1020 FREQ_2A = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_1A))
        print "PRB CC1020 FREQ_1A = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_0A))
        print "PRB CC1020 FREQ_0A = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.CLOCK_A))
        print "PRB CC1020 CLOCK_A = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_2B))
        print "PRB CC1020 FREQ_2B = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_1B))
        print "PRB CC1020 FREQ_1B = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_0B))
        print "PRB CC1020 FREQ_0B = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.CLOCK_B))
        print "PRB CC1020 CLOCK_B = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.MATCH))
        print "PRB CC1020 MATCH = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS1))
        print "PRB CC1020 STATUS1 = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS2))
        print "PRB CC1020 STATUS2 = ",val
        val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.STATUS3))
        print "PRB CC1020 STATUS3 = ",val

    def writeFreqToPRB(self, index, channel):
        # Write the frequency update locations in S-ICD RAM and the PRB 
        if index%9 == 0:
            #Candidate Frequency = 402.8183MHz settings
            if channel == 0:
                self.TestProcedure.ICD.writePrbFpga(0x3024, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3026, 0xD8)
                self.TestProcedure.ICD.writePrbFpga(0x3028, 0x15)
                self.TestProcedure.ICD.writePrbFpga(0x302C, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x302E, 0xE2)
                self.TestProcedure.ICD.writePrbFpga(0x3030, 0xBF)
            else:
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xD8)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x15)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xE2)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0xBF)

        elif index%9 == 1:
            #Candidate Frequency = 403.5108MHz settings
            if channel == 0:
                self.TestProcedure.ICD.writePrbFpga(0x3024, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3026, 0xF0)
                self.TestProcedure.ICD.writePrbFpga(0x3028, 0x21)
                self.TestProcedure.ICD.writePrbFpga(0x302C, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x302E, 0xFA)
                self.TestProcedure.ICD.writePrbFpga(0x3030, 0xCB)
            else:
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xF0)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x21)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xFA)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0xCB)

        elif index%9 == 2:
            #Candidate Frequency = 402.4942MHz settings
            if channel == 0:
                self.TestProcedure.ICD.writePrbFpga(0x3024, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3026, 0xCC)
                self.TestProcedure.ICD.writePrbFpga(0x3028, 0xD3)
                self.TestProcedure.ICD.writePrbFpga(0x302C, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x302E, 0xD7)
                self.TestProcedure.ICD.writePrbFpga(0x3030, 0x7F)
            else:
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xCC)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0xD3)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xD7)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0x7F)

        elif index%9 == 3:
            #Candidate Frequency = 404.6167MHz settings
            if channel == 0:
                self.TestProcedure.ICD.writePrbFpga(0x3024, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x3026, 0x16)
                self.TestProcedure.ICD.writePrbFpga(0x3028, 0x87)
                self.TestProcedure.ICD.writePrbFpga(0x302C, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x302E, 0x21)
                self.TestProcedure.ICD.writePrbFpga(0x3030, 0x31)
            else:
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0x16)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x87)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0x21)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0x31)

        elif index%9 == 4:
            #Candidate Frequency = 402.7209MHz, settings
            if channel == 0:
                self.TestProcedure.ICD.writePrbFpga(0x3024, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3026, 0xD4)
                self.TestProcedure.ICD.writePrbFpga(0x3028, 0xB3)
                self.TestProcedure.ICD.writePrbFpga(0x302C, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x302E, 0xDF)
                self.TestProcedure.ICD.writePrbFpga(0x3030, 0x5D)
            else:
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xD4)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0xB3)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xDF)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0x5D)

        elif index%9 == 5:
            #Candidate Frequency = 402.4049MHz settings
            if channel == 0:
                self.TestProcedure.ICD.writePrbFpga(0x3024, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3026, 0xC9)
                self.TestProcedure.ICD.writePrbFpga(0x3028, 0xB9)
                self.TestProcedure.ICD.writePrbFpga(0x302C, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x302E, 0xD4)
                self.TestProcedure.ICD.writePrbFpga(0x3030, 0x65)
            else:
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xC9)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0xB9)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xD4)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0x65)

        elif index%9 == 6:
            #Candidate Frequency = 404.5197MHz settings
            if channel == 0:
                self.TestProcedure.ICD.writePrbFpga(0x3024, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x3026, 0x13)
                self.TestProcedure.ICD.writePrbFpga(0x3028, 0x29)
                self.TestProcedure.ICD.writePrbFpga(0x302C, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x302E, 0x1D)
                self.TestProcedure.ICD.writePrbFpga(0x3030, 0xD3)
            else:
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0x13)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x29)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0x1D)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0xD3)

        elif index%9 == 7:
            #Candidate Frequency = 402.7049MHz settings
            if channel == 0:
                self.TestProcedure.ICD.writePrbFpga(0x3024, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3026, 0xD4)
                self.TestProcedure.ICD.writePrbFpga(0x3028, 0x25)
                self.TestProcedure.ICD.writePrbFpga(0x302C, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x302E, 0xDE)
                self.TestProcedure.ICD.writePrbFpga(0x3030, 0xCF)
            else:
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xD4)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x25)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xDE)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0xCF)

	else:
            #Candidate Frequency = 403.5108MHz settings
            if channel == 0:
                self.TestProcedure.ICD.writePrbFpga(0x3024, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3026, 0xF0)
                self.TestProcedure.ICD.writePrbFpga(0x3028, 0x21)
                self.TestProcedure.ICD.writePrbFpga(0x302C, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x302E, 0xFA)
                self.TestProcedure.ICD.writePrbFpga(0x3030, 0xCB)
            else:
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xF0)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x21)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xFA)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0xCB)

def main():
    optionsPath = ".\options.xml"
    configPath = ".\settings.cfg"
    psScript = prbCalTxScript(optionsPath, configPath)
    psScript.run()

if __name__ == '__main__':
    main()
