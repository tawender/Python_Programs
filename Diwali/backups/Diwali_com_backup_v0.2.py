#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Asus
#
# Created:     10/12/2015
# Copyright:   (c) Asus 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import optparse
from ConfigParser import ConfigParser
import sys
import serial
from threading import Thread
import time
import msvcrt
import datetime
import os


class Com_thread(Thread):
    def __init__(self,uart,wait_time,debug=False):
        Thread.__init__(self)
        self.uart = uart
        self.wait_time = wait_time
        self.daemon = True
        self.stop_thread = False
        self.debug = debug

    def end_thread(self):
        self.stop_thread = True

    def run(self):

        if self.debug: print "Thread started..."
        while (self.stop_thread == False):

            self.uart.measure_and_read_data()
            time.sleep(self.wait_time)

        if self.debug: print "Thread stopped..."


class UART_com(object):
    """

    """
    def __init__(self, debug=False, print_statements=False):
        try:
            self.debug = debug
            self.printToConsole = print_statements
            self.response_timeout_sec = 5
            self.logging_enabled = False
            self.streaming_data_requests = False

            self.read_config_file()
            self.setup_serial_port()


        except Exception as e:
            if self.printToConsole: print "Exception in UART_com.init(): " + repr(e)
            raise e

    #-----------------------------
    def start_data_requests(self):
        """start requesting data from MSP430"""
        self.com_thread = Com_thread(self,self.data_interval_sec,self.debug)
        self.com_thread.start()
        self.streaming_data_requests = True

    def stop_data_requests(self):
        """stop requesting data from MSP430"""
        self.com_thread.end_thread()
        self.streaming_data_requests = False

    def get_streaming_data_requests_flag(self):
        return self.streaming_data_requests


    def read_config_file(self):
        """read parameters from the config file"""
        try:
            if self.debug: print "reading config file..."

            self.config_file_name = "settings.cfg"
            self.c_file = open(self.config_file_name, 'r')
            self.config_file = ConfigParser()
            self.config_file.readfp(self.c_file)

            self.port_num = int(self.config_file.get('COM Port','port number'))
            self.response_timeout_sec = int(self.config_file.get('COM Port','read timeout'))
            self.data_interval_sec = float(self.config_file.get('Program Execution','data interval seconds'))
            self.datapoints_expected = float(self.config_file.get('Program Execution','data points expected'))

            self.cal_X1 = float(self.config_file.get('Calibration Values','X1'))
            self.cal_Y1 = float(self.config_file.get('Calibration Values','Y1'))
            self.cal_Z1 = float(self.config_file.get('Calibration Values','Z1'))
            self.cal_X2 = float(self.config_file.get('Calibration Values','X2'))
            self.cal_Y2 = float(self.config_file.get('Calibration Values','Y2'))
            self.cal_Z2 = float(self.config_file.get('Calibration Values','Z2'))
            self.cal_X3 = float(self.config_file.get('Calibration Values','X3'))
            self.cal_Y3 = float(self.config_file.get('Calibration Values','Y3'))
            self.cal_Z3 = float(self.config_file.get('Calibration Values','Z3'))


            if self.debug: print "done reading config file"

        except Exception as e:
            print "Exception in UART_com.read_config_file(): " + repr(e)
            raise e

    def get_interval(self):
        return self.data_interval_sec


    def setup_serial_port(self):
        """setup serial port that the MSP430 is connected to"""
        try:
            if self.debug: print "setting up serial port..."

            self.ser = serial.Serial(self.port_num-1)
            self.ser.timeout = self.response_timeout_sec

            if self.debug: print "serial port opened: ",self.ser

        except Exception as e:
            print "Exception in UART_com.setup_serial_port(): " + repr(e)
            raise e


    def measure_and_read_data(self):
        """send request for data to the MSP430 and read data back"""
        try:
            if self.debug: print "sending request for data..."

            self.ser.write("^")
            time.sleep(.25)

            self.ser.flushInput()
            self.ser.write("?")

            resp = self.ser.readline()
            if self.debug: print "received:%s"%resp

            read_response = resp.strip().split(":")
            if len(read_response) == self.datapoints_expected:
                self.R_voltage = float(read_response[0]) / 1000.0
                self.G_voltage = float(read_response[1]) / 1000.0
                self.B_voltage = float(read_response[2]) / 1000.0
                self.OP980_lightLevel = float(read_response[7]) / 10.0          #light level in foot-candles
                self.HTU21Dtemperature = float(read_response[3]) / 100.0        #temperature in degrees C
                self.HTU21Dhumidity = float(read_response[4]) / 100.0           #humidity in %RH
                self.MS5637temperature = float(read_response[5]) / 100.0        #temperature in degrees C
                try:
                    self.MS5637pressure = float(read_response[6]) / 100.0           #pressure in mbar
                except:
                    self.MS5637pressure = "err"


            else:
                if self.printToConsole: print "UART error... expected %d data points returned and got %d"%(self.datapoints_expected,len(read_response))
                if resp != None:
                    if self.printToConsole: print "response: %s"%resp
                else:
                    if self.printToConsole: print "no response"
                return

            t = datetime.datetime.now()
            timestamp = t.strftime("%m/%d/%Y %H:%M:%S.%f")[:23]

            if self.printToConsole:
                print "%s, R: %5.3fV, G: %5.3fV, B: %5.3fV"%(timestamp,self.R_voltage,self.G_voltage,self.B_voltage)
                print "  Light Level: %4.1ffcd"%(self.OP980_lightLevel)

            self.run_calculations()

            if self.printToConsole:
                print "  HTU21Dtemperature: %s*C,   HTU21Dhumidity: %s%%RH\n" \
                      "  MS5637temperature: %s*C,   MS5637pressure: %smbar"%(self.HTU21Dtemperature,self.HTU21Dhumidity,
                                                                        self.MS5637temperature,self.MS5637pressure)
                print "*****************"

            return (self.R_voltage,self.G_voltage,self.B_voltage,
                    self.X,self.Y,self.Z,self.x,self.y,self.CCT,
                    self.HTU21Dtemperature,self.HTU21Dhumidity,
                    self.MS5637temperature,self.MS5637pressure,
                    self.OP980_lightLevel)


        except Exception as e:
            print "Exception in UART_com.measure_and_read_data(): " + repr(e)
            raise e

    def run_calculations(self):
        """calculate the tristimulus values XYZ, chromaticity coordinates (x,y), and CCT"""

        # calculate tristimulus values
        self.X = self.cal_X1*self.R_voltage + self.cal_Y1*self.G_voltage + self.cal_Z1*self.B_voltage
        self.Y = self.cal_X2*self.R_voltage + self.cal_Y2*self.G_voltage + self.cal_Z2*self.B_voltage
        self.Z = self.cal_X3*self.R_voltage + self.cal_Y3*self.G_voltage + self.cal_Z3*self.B_voltage
        if self.printToConsole: print "  X: %5.2f  Y: %5.2f  Z: %5.2f"%(self.X,self.Y,self.Z)


        #calculate chromaticity coordinates
        if (self.X + self.Y + self.Z) != 0:
            self.x = self.X / (self.X + self.Y + self.Z)
            self.y = self.Y / (self.X + self.Y + self.Z)
            if self.printToConsole: print "  (x,y):(%.5f,%.5f)"%(self.x,self.y)
        else:
            self.x = 'Err'
            self.y = 'Err'
            if self.printToConsole: print "  (x,y):(Err,Err)"


        #calculate correlated color temperature if valid readings taken
        if (self.X + self.Y + self.Z) != 0:
            n = (self.x - 0.3320) / (0.1858 - self.y)
            self.CCT = 449*n**3 + 3525*n**2 + 6823.3*n + 5520.33
            if self.printToConsole: print "  CCT: %.0f"%(self.CCT)
        else:
            self.CCT = 'Err'
            if self.printToConsole: print "  CCT: Err"

def print_menu():
    print "\n Type characters 0-4 to change heater modes,\n" \
        " 'q' for quit, 's' for single data request,\n" \
        " 'c' to read the configuration file,\n" \
        " 'd' to toggle looping data requests, or\n" \
        " '?' for this command menu\n\n"


def main(argv=None):
    try:
        #********************************************
        # Parse command line options
        if argv is None:
            argv = sys.argv
        p = optparse.OptionParser()
        p.add_option("-d","--debug", action="store_true", dest="debug", help="enable debug statements")

        # Set default values for options:
        p.set_defaults(debug=False)
        opts, args = p.parse_args()

        # Retrieve the option settings:
        _debug = opts.debug
        #********************************************

        if _debug: print 'Debugging Statements Enabled...'

        UART = UART_com(_debug,True)

        print_menu()
        s = msvcrt.getch()
        while(s != 'q'):

            #-----------------------------------------
            if (s == 's'):      #single data request
                UART.measure_and_read_data()



            #-----------------------------------------
            elif (s == 'd'):       #toggle looping data requests
                if UART.get_streaming_data_requests_flag():
                    UART.stop_data_requests()

                else:
                    UART.start_data_requests()


            #-----------------------------------------
            elif (s == 'c'):      #read configuration data
                UART.read_config_file()


            #-----------------------------------------
            elif (s == '?'):
                print_menu()


            else:
                print "Invalid character"



            time.sleep(0.1)
            s = msvcrt.getch()

    except Exception as e:
        print "Exception in main(): " + repr(e)
        raise e

if __name__ == '__main__':
    main()