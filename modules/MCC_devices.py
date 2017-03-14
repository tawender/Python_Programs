#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      tawender
#
# Created:     13/06/2012
# Copyright:   (c) tawender 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import string

##import sys
##sys.path.append(r'C:\apps\Python27\Lib')
##sys.path.append(r'C:\Program Files\Measurement Computing\DAQFlex')

import clr
clr.AddReference("DAQFlex")
import MeasurementComputing.DAQFlex as daqflex

device_names_format = daqflex.DeviceNameFormat.NameAndSerno



class USB_2001_TC(object):
    """measurement computing thermocouple reader
    """
    def __init__(self,id,tc_type,units):
        print 'target id:',id
        devices = self._get_device_names()
        print 'type(devices):',type(devices)
        print 'devices:',devices
        print "devices found: " + repr(devices)
        print 'first device: ',devices[0]
        for device in devices:
            print device
            if device == id:
                print "found match"
                self.deviceName = device
                self.device = daqflex.DaqDeviceManager.CreateDevice(self.deviceName)
                print "created tc device"

        if id not in devices:
            raise RuntimeError("device not found")

        self.set_tc_type(tc_type)
        self.set_units(units)


    def _get_device_names(self,format='Name_and_sn'):
        """scan the computer for connected measurement computing devices
           and return a list of devices in NameAndSerno format
           Ex. USB-2001-TC::00000000
        """
        return daqflex.DaqDeviceManager.GetDeviceNames(device_names_format)

    def set_tc_type(self,tc_type):
        """set the thermocouple type
           tc_type: 'J','K','S','R','B','E','T',or 'N'
        """
        print 'setting the thermocouple type'
        if tc_type in ['j','k','s','r','b','e','t','n']:
            tctype = string.upper(tc_type)
        elif tc_type not in ['J','K','S','R','B','E','T','N']:
            raise RuntimeError("Invalid thermocouple type: ") + repr(tc_type)

        str = r'AI{0}:SENSOR=TC/%s'%tc_type
        self.device.SendMessage(str)

        resp = self.device.SendMessage(r'?AI{0}:SENSOR').ToString()
        print 'tc type set to %s'%(resp[len(resp)-1:len(resp)])

    def set_units(self,units):
        """set the units that the temerature is returned in C or F
           Parameter: units (string)'F' or 'C'
        """
        if units in ['f','c']:
            units = string.upper(units)
        elif units not in ['F','C']:
            raise RuntimeError("Invalid temperature units: ") + repr(tc_type)
        self.units = units

    def read_temp(self,units=None):
        """read the temperature from the thermocouple device.
           Returns the temperature as a float
        """
        if units is not None:
            self.set_units(units)

        resp = self.device.SendMessage(r'?AI{0}:VALUE/DEG%s'%string.upper(self.units))
        s = str(resp).strip().split('=')

        return float(s[1])

    def release_device(self):
        """release this instance of the daq device
        """
        daqflex.DaqDeviceManager.ReleaseDevice(self.device)



def main():
    tc = USB_2001_TC("USB-2001-TC::16f24e0",'T','C')

    import time

    for i in range(100):
        t = tc.read_temp()
        print "%2d. "%i+1,
        print "temperature: %.3f C"%t
        time.sleep(2)

if __name__ == '__main__':
    main()
