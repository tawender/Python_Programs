#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      tawender
#
# Created:     05/12/2012
# Copyright:   (c) tawender 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import pyPicoscope


def main():
    def print_averages(d):
        for ch in result:
            print "average of %s: %.3fV"%(ch,numpy.average(result[ch]))

    #set up the picoscope
##    ps = pyPicoscope.picoscope()
    picoscope_handle = ps.get_handle()
    x=numpy.zeros(10)

    #set up the normal measurement
    print "setting up standard measurement"
    measurement = pyPicoscope.picoscope_measurement(picoscope_handle,timeout_sec=5.0)
    print "picoscope measurement created..."
    measurement.set_channel('ChannelA',enabled=True,dc_coupling=True,_range='Range_5V')
    print "channel A set..."
    measurement.set_channel('ChannelB',enabled=True,dc_coupling=True,_range='Range_10V')
    print "channel B set..."
    measurement.set_triggering(triggered_measurement=False,trig_source='ChannelB',
                        trigger_voltage=1.0,trig_slope='Rising',trigger_delay=0,trig_timeout=0)
    print "triggering set..."
    measurement.set_sampling(seconds_to_acquire=0.0002,desired_sample_interval=.000005,
                        seconds_pretrigger=0.00006)
    print "sampling set..."
    result = measurement.run_measurement()
    print "measurement completed."
    print_averages(result)
    print " done with standard measurement\n"


if __name__ == '__main__':
    main()
