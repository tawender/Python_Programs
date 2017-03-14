#-------------------------------------------------------------------------------
# Name:        find_ni_hardware
# Purpose:     Search computer for NI hardware installed
#
# Author:      awendet
#
# Created:     30/05/2013
# Copyright:   (c) awendet 2013
# Licence:     <your licence>
#
# This script is to be run using IronPython.
# IronPython is needed to use the .net DLL from NationalInstruments which is
# used to check the system to see what NI hardware is installed.
#-------------------------------------------------------------------------------
import clr
clr.AddReference("NationalInstruments.DAQmx")
import NationalInstruments.DAQmx as DAQmx

import sys
import optparse


class find_hardware(object):

    def __init__(self,display_info=False,outfile=None):
        self.hardware_list = None
        self.display_info = display_info

        hw = self.find_installed_hardware()

        if hw is not None:
            self.read_hardware_info(hw)

        if self.display_info and hw is not None:
            self.display_hardware_info()

        if outfile is not None:
            self.write_results_to_file(outfile)

    def find_installed_hardware(self):
        """this function will search the machine for installed NI hardware
           and return a list of device identifiers Ex.'Dev1','Dev2'
        """
        found_devices = DAQmx.DaqSystem.Local.Devices

        if len(found_devices) == 0:
            if self.display_info:
                print "No National Instruments Hardware Detected"
            return None

        else:
            if self.display_info:
                print "found %d device(s) installed in the system"%(len(found_devices))
            return found_devices


    def read_hardware_info(self,devices_list):
        """will run through a list of device identifiers Ex.'Dev1','Dev2' and read and store
           the hardware information available for each device
        """

        self.hardware_list = []

        for device in devices_list:

            device_info = dict()

            device_info['name'] = device
            device_info['model'] = DAQmx.DaqSystem.Local.LoadDevice(device).ProductType
            device_info['serial'] = "%x"%(DAQmx.DaqSystem.Local.LoadDevice(device).SerialNumber)
            device_info['simulated'] = DAQmx.DaqSystem.Local.LoadDevice(device).IsSimulated

            self.hardware_list.append(device_info)

    def display_hardware_info(self):
        """displays the information for hardware previously found installed in the system
        """
        for device in self.hardware_list:
            print '\nDevice: ',device['name']
            print '       model number: ',device['model']
            print '      serial number: ',device['serial']
            print '   simulated device: ',device['simulated']

    def get_hardware_list(self):
        """will search for hardware devices installed in the system, find detailed information on all
           hardware devices detected.

           RETURNS: A list of dictionaries (dictioary for each hardware device detected)
                    dictionary keys:    'name':     device name Ex.Dev1
                                        'model':    device model number
                                        'serial':   device serial number
                                        'simulated':boolean for whether or not device is simulated
        """
        hw = self.find_installed_hardware()
        self.read_hardware_info(hw)

        return self.hardware_list

    def write_results_to_file(self,outfile):
        """writes the results of the hardware check to an external file specified during
           class instance creation
           No hardware found is indicated by a file containing only '0'
        """
        f = open(outfile,'w')

        if self.hardware_list is None:
            f.write("0")

        else:
            linecount = 0
            for device in self.hardware_list:
                linecount += 1
                f.write("%s,%s,%s,%s"%(device['name'],
                                        device['model'],
                                        device['serial'],
                                        device['simulated']))

                if linecount < len(self.hardware_list):
                    f.write("\n")

        f.close()




def main(argv=None):

    #********************************************
    # Parse command line options
    if argv is None:
        argv = sys.argv
    p = optparse.OptionParser()
    p.add_option("-f", action="store", dest="outfile")
    p.add_option("-d", action="store_true", dest="display")

    # Set default values for options:
    p.set_defaults(outfile=None,display=False)
    opts, args = p.parse_args()
    # Retrieve the option settings:
    if opts.outfile is None:
        _outfile = None
    else:
        _outfile = opts.outfile.replace('"','')
    _display = opts.display
    #********************************************


    if _display:
        print "Checking system for installed NI hardware..."
    hardware = find_hardware(display_info=_display,outfile=_outfile)


if __name__ == '__main__':
    sys.exit(main())





