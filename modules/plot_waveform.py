#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys, optparse, math, numpy as np
from matplotlib import pyplot as plot

def spectrum_with_plots(array, freq, sample_rate):
    try:
        a = np.asarray(array, dtype="float")
        samples = len(a)
        sample_time = float(samples) / sample_rate    
        frequency_index = int(2.0*freq*sample_time + 0.5)
        bin_width = 1/(sample_time*2.0)
        dt = 1.0/sample_rate
        t = np.arange(0, sample_time, dt,dtype="float")
        b = np.abs(fft.rfft(a))/(samples/2.0)
        f = np.arange(0,  sample_rate/2.0,  bin_width)
        c = b**2

        # Make a little extra space between the subplots
        plot.subplots_adjust(hspace=.4)   
        plot.subplot(311)
        plot.plot(t, a, 'bo', t, a, 'k--')
        plot.xlim(0,sample_time)
        plot.xlabel('time(sec)')
        plot.ylabel('amplitude(V)')
        plot.grid(True)
        
        plot.show()
        
        return
    except Exception as e:
        print "exception in spectrum_with_plots: " + repr(e)
def main(infile,_freq):
    
    sample_rate = 256

    i_f = open(infile,  'r')
    a = []
    for line in i_f:
        a.append(int(line.strip()))
    spectrum_with_plots(a,_freq,sample_rate)
    return

if __name__ == "__main__":
    sys.exit(main())
