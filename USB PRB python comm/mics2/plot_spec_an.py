#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      awendet
#
# Created:     24/06/2013
# Copyright:   (c) awendet 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import visa
from matplotlib import pyplot
from matplotlib.ticker import FormatStrFormatter
from numpy import arange

import sys
sys.path.append("T:/python programs/modules")
import Instruments


class data_plots(object):
    def __init__(self,path=None):
        self.plot_number = 1
        if path is None:
            self.save_plots = False
        else:
            self.path = path
            self.save_plots = True


    def plot_data_OBW(self,f1,f2,levels,x_units,y_units,conv_factor=1.0,
                        vertlines=None,y_scale=None,name=None):

        freqs = [x/conv_factor for x in arange(f1,f2,(f2-f1)/len(levels))]

        fig = pyplot.figure()
        pyplot.plot(freqs,levels[0:len(freqs)],'b-')
        pyplot.gca().xaxis.set_major_formatter(FormatStrFormatter('%.2f'))

        #add vertical lines if specified
        if vertlines is not None:
            for line in vertlines:
                pyplot.plot( [line/conv_factor,line/conv_factor],[y_scale[0],y_scale[1]],'r-' )
                pyplot.text(line/conv_factor,y_scale[0]+2,'%.3f'%(line/conv_factor),color='r')


        pyplot.xlim(f1/conv_factor,f2/conv_factor)
        pyplot.ylim(y_scale)

        pyplot.xlabel(x_units)
        pyplot.ylabel(y_units)

        pyplot.grid(True)

        if name is not None:
            pyplot.title(name)

        if self.save_plots:
            fig_name = self.path + "\%02d_"%self.plot_number + name + ".png"
            self.plot_number += 1
            pyplot.savefig(fig_name,dpi=200)
            pyplot.clf()
            pyplot.close(fig)
        else:
            pyplot.show()

def read_file_data(f_name):
    f = open(f_name,'r')
    data = []
    for line in f:
        data.append(float(line.strip()))
    f.close()
    return data

def main(args):
    path = args[1]
    name = args[2]
    y_data = read_file_data(args[3])
    x_units = args[4]
    y_units = args[5]
    f1 = float(args[6])
    f2 = float(args[7])
    y1 = float(args[8])
    y2 = float(args[9])

    plots = data_plots(path)

    plots.plot_data_OBW(f1,f2,y_data,x_units,y_units,conv_factor=1E6,
                        vertlines=[403.510E6],y_scale=(y1,y2),name=name)

if __name__ == '__main__':
    #arguments:
        #[0] script name
        #[1] path
        #[2] plot name
        #[3] y values filename
        #[4] x-axis label
        #[5] y-axis label
        #[6] x scale minimum
        #[7] x scale maximum
        #[8] y scale minimum
        #[9] y scale maximum
        #[10] plot type(1=occupied bandwidth,
        #               2=

    main(sys.argv)
