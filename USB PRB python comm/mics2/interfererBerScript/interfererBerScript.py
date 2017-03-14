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
#sys.path.append(r'c:\Program Files\IronPython 2.7\Lib\site-packages')
#import visa

# path to common files
sys.path.append(r'c:\python_programs\mics2')

# a modified pyvisa
sys.path.append(r'c:\Program Files\Python 2.7.5\Lib\site-packages\pyvisa')

from Instruments import HP_8648_sig_gen as sig_gen

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

class interfererBerScript(PyScript):
    def __init__(self, optionsPath, configPath):
        # Read configuration
        config = ConfigParser()
        config.read(configPath)

        logDir = config.get('Location', 'log_dir')
        logName = 'interfererBerScriptLog ' + DateTime.Now.ToString('yyyy.MM.dd HH.mm.ss') + '.log'
        buildNumber = int(config.get('Firmware', 'build_num'), 0)

        super(interfererBerScript, self).__init__(optionsPath, buildNumber, Path.Combine(logDir, logName))

        self.loop_count = int(config.get('Sampling', 'loop_count'))

    def script(self):
        # Read FPGA address 0x3000 and verify the response is 0x12.
        val = self.TestProcedure.ICD.readPrbFpga(0x3000)
        self.verify("FPGA 0x3000", 0x12, val)
        if val != 0x12:
            self.verify("ERROR", 0x12, val)

        # calibrate once on channel 0
        self.TestProcedure.ICD.calibrateCc1020()
        self.DumpCalResult()
        inv_flag = 0x00
#read the MATCH register from eeprom and the CC1020....

        # set the allowed errors to 64 to minimize listening mode 
        self.TestProcedure.ICD.writePrbFpga(0x1006, 0x40)

        #
        sg=sig_gen("GPIB::18",'SIG_GEN')
        sg.set_output_power_dBm(-17)
        sg.set_fm_source_internal()
        sg.set_fm_deviation_Hz(32000)
        sg.fm_on()

        for idx in range(0, self.loop_count):
            test_time = time.clock() 
            print "Loop Index = ", idx
	    print "Test time = %.2d:%06.3f"%(test_time/60,test_time%60.0)

            sg.output_off()
            # get initial frequency values
            val_2 = self.TestProcedure.ICD.readPrbFpga(0x305E)
            val_1 = self.TestProcedure.ICD.readPrbFpga(0x3060)
            val_0 = self.TestProcedure.ICD.readPrbFpga(0x3062)
            freq_a_init = val_2*65536 + val_1*256 + val_0 
            print "PRB FREQ_A = ",freq_a_init

            val_2 = self.TestProcedure.ICD.readPrbFpga(0x3066)
            val_1 = self.TestProcedure.ICD.readPrbFpga(0x3068)
            val_0 = self.TestProcedure.ICD.readPrbFpga(0x306A)
            freq_b_init = val_2*65536 + val_1*256 + val_0 
            print "PRB FREQ_B = ",freq_b_init

            # Scan and link on Channel 1, with data inversion disabled
            self.TestProcedure.ICD.writePrbFpga(0x1026, 0x01)
            devList = self.icdcmd.scan(17, 2)
 #           if devList == NULL:
 #             devList = self.icdcmd.scan(17, 2)
            print "type(devList):",type(devList)
            print "devList ",devList

            self.TestProcedure.ICD.writePrbFpga(0x3012, inv_flag)             
            val = self.TestProcedure.ICD.readPrbFpga(0x1026)
            print "Channel Selection = ",val
            val = self.TestProcedure.ICD.readPrbFpga(0x3012)             
            print "Data inversion = ",val

            self.icdcmd.connect((UInt32) (2149582066))
            time.sleep(1)

            self.TestProcedure.ICD.writePrbFpga(0x301C, 0x00)
            val = self.TestProcedure.ICD.readPrbFpga(0x301C)
            print "PRB Init Frame Error Count = ", val

            if idx%9 == 0:
                print "Candidate Frequency = 402.8183MHz, LSI"
            elif idx%9 == 1:
                print "Candidate Frequency = 403.5108MHz, HSI"
            elif idx%9 == 2:
                print "Candidate Frequency = 402.4942MHz, LSI"
            elif idx%9 == 3:
                print "Candidate Frequency = 404.6167MHz, HSI"
            elif idx%9 == 4:
                print "Candidate Frequency = 402.7209MHz, HSI"
            elif idx%9 == 5:
                print "Candidate Frequency = 402.4049MHz, HSI"
            elif idx%9 == 6:
                print "Candidate Frequency = 404.5197MHz, LSI"
            elif idx%9 == 7:
                print "Candidate Frequency = 402.7049MHz, LSI"
            else:
                print "Candidate Frequency = 403.5108MHz, HSI"

            val = self.TestProcedure.ICD.readPrbFpga(0x1026)
            print "  PRB Channel Selection = ",val
            val = self.TestProcedure.ICD.readPrbFpga(0x3012)             
            print "  PRB Data inversion = ",val

            # Disable firmware CRC checks
            self.icdcmd.writeByte((UInt32)(0x410D), 0x39)
            val = self.icdcmd.readByte(Key.TELEM_CC1K_PA_POW)
            print "  S-ICD PA_POW = ",val

# need to add the proper BER data location in S-ICD RAM
            self.icdcmd.writeByte((UInt32)(0x0200), 0xA5)
            val = self.icdcmd.readByte((UInt32)(0x0200))
            print "  S-ICD RAM = ",val

            # Read CC1020 AFC register and verify correction logic 
# need to add specific range checks
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
#            print "  PRB FREQ_A = ",freq_a

            val_2 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_2B))
            val_1 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_1B))
            val_0 = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FREQ_0B))
            freq_b = val_2*65536 + val_1*256 + val_0 
#            print "  PRB FREQ_B = ",freq_b

            # compute frequency offset 
            val = (freq_a -1)/2 - (freq_a_init-1)/2
            print "  PRB AFC_A = ",val
            val = (freq_b -1)/2 - (freq_b_init-1)/2
            print "  PRB AFC_B = ",val

            # set the filter to widest bandwidth to get an unsaturated RSSI
            self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FILTER), 0x80)
            val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FILTER))
            print "  PRB CC1020 FILTER = ", val

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
            val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FILTER))
            print "  PRB CC1020 FILTER = ", val
            time.sleep(0.080)


            # Loop through 32 times to check no interferer, channel interferer, and non-channel interferers
#	    for idx_i in range(0, 33):
            for idx_i in range(0, 11):
                self.TestProcedure.ICD.writePrbFpga(0x301C, 0x00)
                val = self.TestProcedure.ICD.readPrbFpga(0x301C)
                print "  PRB Init Frame Error Count = ", val

                if idx_i == 0:
                    print "  No interferer "
                elif idx_i == 1:
                    print "  402.150MHz interferer "
                    sg.set_output_frequency(402150000)
                    sg.output_on()
                elif idx_i == 2:
                    print "  402.450MHz interferer "
                    sg.set_output_frequency(402450000)
                elif idx_i == 3:
                    print "  402.750MHz interferer "
                    sg.set_output_frequency(402750000)
                elif idx_i == 4:
                    print "  403.050MHz interferer "
                    sg.set_output_frequency(403050000)
                elif idx_i == 5:
                    print "  403.350MHz interferer "
                    sg.set_output_frequency(403350000)
                elif idx_i == 6:
                    print "  403.650MHz interferer "
                    sg.set_output_frequency(403650000)
                elif idx_i == 7:
                    print "  403.950MHz interferer "
                    sg.set_output_frequency(403950000)
                elif idx_i == 8:
                    print "  404.250MHz interferer "
                    sg.set_output_frequency(404250000)
                elif idx_i == 9:
                    print "  404.550MHz interferer "
                    sg.set_output_frequency(404550000)
                elif idx_i == 10:
                    print "  404.850MHz interferer "
                    sg.set_output_frequency(404850000)
                elif idx_i == 11:
                    print "  -1000kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 12:
                    print "  -900kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 13:
                    print "  -800kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 14:
                    print "  -700kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 15:
                    print "  -600kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 16:
                    print "  -500kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 17:
                    print "  -400kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 18:
                    print "  -300kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 19:
                    print "  -200kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 20:
                    print "  -100kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 21:
                    print "  co-channel interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 22:
                    print "  +100kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 23:
                    print "  +200kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 24:
                    print "  +300kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 25:
                    print "  +400kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 26:
                    print "  +500kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 27:
                    print "  +600kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 28:
                    print "  +700kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 29:
                    print "  +800kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 30:
                    print "  +900kHz interferer "
#                    sg.set_output_frequency(402818300)
                elif idx_i == 31:
                    print "  +1000kHz interferer "
#                    sg.set_output_frequency(402818300)
                else:
                    print "  No interferer "
                    sg.output_off()

                # set the filter to widest bandwidth to get an unsaturated RSSI
                self.TestProcedure.ICD.writeCC1020(int(CC1020Register.FILTER), 0x80)
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FILTER))
                print "  PRB CC1020 FILTER = ", val

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
                val = self.TestProcedure.ICD.readCC1020(int(CC1020Register.FILTER))
                print "  PRB CC1020 FILTER = ", val
                time.sleep(0.080)

# need to the BER procedure here, needs to include the logic to write the 0xA5A5 value to RAM
#                self.icdcmd.ping()
                # sleep to let supplies settle after a ping
                time.sleep(2)
                self.TestProcedure.ICD.resetCommunicationSystemStatusCounters()
                cmdFailures = 0
#                self.icdcmd.writeByte(address and data)
                for idx_i in range(0, 100):
                    try:                
                        self.icdcmd.readByte((UInt32)(0x0200))
#                        self.icdcmd.readmemory(0x0200)
                    except Exception, ex0:
#                        self.TestProcedure.ICD.communicationSystemStatusCounters()                
                        cmdFailures+=1
                        print str(ex0)
                self.passed = True
                print "  S-ICD command failures = ",cmdFailures
#                    self.returnlastcommand()

                val = self.TestProcedure.ICD.readPrbFpga(0x301C)
                print "  PRB Final Frame Error Count = ", val
            self.passed = True


            # Write the frequency update locations in S-ICD RAM and the PRB 
            if idx%9 == 0:
                #Candidate Frequency = 403.5108MHz settings
                # S-ICD
                self.icdcmd.writeByte((UInt32)(0x5A61), 0x52)
                self.icdcmd.writeByte((UInt32)(0x5A62), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A63), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A64), 0x51)
                self.icdcmd.writeByte((UInt32)(0x5A65), 0xF6)
                self.icdcmd.writeByte((UInt32)(0x5A66), 0x85)
                self.icdcmd.writeByte((UInt32)(0x5A67), 0x03)
                self.icdcmd.writeByte((UInt32)(0x5A68), 0x55)
                self.icdcmd.writeByte((UInt32)(0x5A69), 0x60)
                inv_flag = 0x01
                # PRB
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xF0)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x21)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xFA)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0xCB)

            elif idx%9 == 1:
                #Candidate Frequency = 402.4942MHz settings
                # S-ICD
                self.icdcmd.writeByte((UInt32)(0x5A61), 0x5F)
                self.icdcmd.writeByte((UInt32)(0x5A62), 0x60)
                self.icdcmd.writeByte((UInt32)(0x5A63), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A64), 0x5F)
                self.icdcmd.writeByte((UInt32)(0x5A65), 0x67)
                self.icdcmd.writeByte((UInt32)(0x5A66), 0x2C)
                self.icdcmd.writeByte((UInt32)(0x5A67), 0x03)
                self.icdcmd.writeByte((UInt32)(0x5A68), 0xE4)
                self.icdcmd.writeByte((UInt32)(0x5A69), 0x70)
                inv_flag = 0x00
                # PRB
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xCC)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0xD3)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xD7)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0x7F)

            elif idx%9 == 2:
                #Candidate Frequency = 404.6167MHz settings
                # S-ICD
                self.icdcmd.writeByte((UInt32)(0x5A61), 0x44)
                self.icdcmd.writeByte((UInt32)(0x5A62), 0x80)
                self.icdcmd.writeByte((UInt32)(0x5A63), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A64), 0x44)
                self.icdcmd.writeByte((UInt32)(0x5A65), 0x78)
                self.icdcmd.writeByte((UInt32)(0x5A66), 0x1A)
                self.icdcmd.writeByte((UInt32)(0x5A67), 0x02)
                self.icdcmd.writeByte((UInt32)(0x5A68), 0xC7)
                self.icdcmd.writeByte((UInt32)(0x5A69), 0x50)
                inv_flag = 0x01
                # PRB
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0x16)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x87)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0x21)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0x31)

            elif idx%9 == 3:
                #Candidate Frequency = 402.7209MHz, settings
                # S-ICD
                self.icdcmd.writeByte((UInt32)(0x5A61), 0x5F)
                self.icdcmd.writeByte((UInt32)(0x5A62), 0x80)
                self.icdcmd.writeByte((UInt32)(0x5A63), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A64), 0x5F)
                self.icdcmd.writeByte((UInt32)(0x5A65), 0x74)
                self.icdcmd.writeByte((UInt32)(0x5A66), 0xF1)
                self.icdcmd.writeByte((UInt32)(0x5A67), 0x03)
                self.icdcmd.writeByte((UInt32)(0x5A68), 0xE4)
                self.icdcmd.writeByte((UInt32)(0x5A69), 0x70)
                inv_flag = 0x01
                # PRB
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xD4)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0xB3)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xDF)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0x5D)

            elif idx%9 == 4:
                #Candidate Frequency = 402.4049MHz settings
                # S-ICD
                self.icdcmd.writeByte((UInt32)(0x5A61), 0x44)
                self.icdcmd.writeByte((UInt32)(0x5A62), 0x20)
                self.icdcmd.writeByte((UInt32)(0x5A63), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A64), 0x44)
                self.icdcmd.writeByte((UInt32)(0x5A65), 0x18)
                self.icdcmd.writeByte((UInt32)(0x5A66), 0x1A)
                self.icdcmd.writeByte((UInt32)(0x5A67), 0x02)
                self.icdcmd.writeByte((UInt32)(0x5A68), 0xC7)
                self.icdcmd.writeByte((UInt32)(0x5A69), 0x50)
                inv_flag = 0x01
                # PRB
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xC9)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0xB9)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xD4)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0x65)

            elif idx%9 == 5:
                #Candidate Frequency = 404.5197MHz settings
                # S-ICD
                self.icdcmd.writeByte((UInt32)(0x5A61), 0x59)
                self.icdcmd.writeByte((UInt32)(0x5A62), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A63), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A64), 0x59)
                self.icdcmd.writeByte((UInt32)(0x5A65), 0x06)
                self.icdcmd.writeByte((UInt32)(0x5A66), 0xA8)
                self.icdcmd.writeByte((UInt32)(0x5A67), 0x03)
                self.icdcmd.writeByte((UInt32)(0x5A68), 0x9C)
                self.icdcmd.writeByte((UInt32)(0x5A69), 0x68)
                inv_flag = 0x00
                # PRB
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0x13)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x29)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x36)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0x1D)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0xD3)

            elif idx%9 == 6:
                #Candidate Frequency = 402.7049MHz settings
                # S-ICD
                self.icdcmd.writeByte((UInt32)(0x5A61), 0x44)
                self.icdcmd.writeByte((UInt32)(0x5A62), 0x20)
                self.icdcmd.writeByte((UInt32)(0x5A63), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A64), 0x44)
                self.icdcmd.writeByte((UInt32)(0x5A65), 0x25)
                self.icdcmd.writeByte((UInt32)(0x5A66), 0x1F)
                self.icdcmd.writeByte((UInt32)(0x5A67), 0x02)
                self.icdcmd.writeByte((UInt32)(0x5A68), 0xC7)
                self.icdcmd.writeByte((UInt32)(0x5A69), 0x50)
                inv_flag = 0x00
                # PRB
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xD4)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x25)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xDE)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0xCF)

            elif idx%9 == 7:
                #Candidate Frequency = 403.5108MHz settings
                # S-ICD
                self.icdcmd.writeByte((UInt32)(0x5A61), 0x52)
                self.icdcmd.writeByte((UInt32)(0x5A62), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A63), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A64), 0x51)
                self.icdcmd.writeByte((UInt32)(0x5A65), 0xF6)
                self.icdcmd.writeByte((UInt32)(0x5A66), 0x85)
                self.icdcmd.writeByte((UInt32)(0x5A67), 0x03)
                self.icdcmd.writeByte((UInt32)(0x5A68), 0x55)
                self.icdcmd.writeByte((UInt32)(0x5A69), 0x60)
                inv_flag = 0x01
                # PRB
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xF0)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x21)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xFA)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0xCB)

            else:
                # Must revert to 402.8183MHz without data inversion 
                # after last iteration
                #Candidate Frequency = 402.8183MHz settings
                # S-ICD
                self.icdcmd.writeByte((UInt32)(0x5A61), 0x58)
                self.icdcmd.writeByte((UInt32)(0x5A62), 0xA0)
                self.icdcmd.writeByte((UInt32)(0x5A63), 0x00)
                self.icdcmd.writeByte((UInt32)(0x5A64), 0x58)
                self.icdcmd.writeByte((UInt32)(0x5A65), 0xA6)
                self.icdcmd.writeByte((UInt32)(0x5A66), 0xA8)
                self.icdcmd.writeByte((UInt32)(0x5A67), 0x03)
                self.icdcmd.writeByte((UInt32)(0x5A68), 0x9C)
                self.icdcmd.writeByte((UInt32)(0x5A69), 0x68)
                inv_flag = 0x00
                # PRB
                self.TestProcedure.ICD.writePrbFpga(0x305E, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3060, 0xD8)
                self.TestProcedure.ICD.writePrbFpga(0x3062, 0x15)
                self.TestProcedure.ICD.writePrbFpga(0x3066, 0x35)
                self.TestProcedure.ICD.writePrbFpga(0x3068, 0xE2)
                self.TestProcedure.ICD.writePrbFpga(0x306A, 0xBF)

            # break link with the S-ICD
            wfdeState = WaitForDisconnectedEventState(Key.DONT_CARE, 0x0)
            try:
                self.icdcmd.EventWaiter.execState(wfdeState, TimeSpan.FromSeconds(2))
            except Exception, ex:
                print str(ex)

            time.sleep(4)
        sg.output_off()
        self.passed = True

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

def main():
    optionsPath = ".\options.xml"
    configPath = ".\settings.cfg"
    psScript = interfererBerScript(optionsPath, configPath)
    psScript.run()

if __name__ == '__main__':
    main()
