#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      tawender
#
# Created:     16/05/2012
# Copyright:   (c) tawender 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import numpy
from matplotlib import pyplot as plot

def make_plot(a,name=None,samp_per_sec=None,x_units=None,y_units=None,y_scale=-1):
    """add the plot to the directory containing all plots
       a            (numpy array) array of data to graph
       name         (string)the name of the test
       result       (string)the result of the test data
       samp_per_sec (float)sample rate of the acquired data
       x_units      (string)units along the x-axis
       y_units      (string)units along the y-axis
       y_scale      (tuple)min and max for the y scale
    """
    try:
        if samp_per_sec is not None:
            dt = 1.0 / float(samp_per_sec)
            time_graphed = len(a) * dt
            t = numpy.arange(0,time_graphed,dt,dtype="float")
        else:
            t = numpy.arange(0,len(a))

        plot.subplot(1,1,1)
        plot.plot(t,a,'ko',markersize=3)
        plot.plot(t,a,'b-',markersize=3)

        if samp_per_sec is not None:
            plot.xlim(0, time_graphed)

        if y_scale != -1:
            plot.ylim(y_scale)

        if x_units is not None:
            plot.xlabel(x_units)

        if y_units is not None:
            plot.ylabel(y_units)

        if name is not None:
            plot.title(name)

        plot.grid(True)

        plot.show()

    except Exception as e:
        print "Exception in make_plot: " + repr(e)
        raise e


def main():
    pass

if __name__ == '__main__':
    main()
