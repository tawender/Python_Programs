#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys, optparse, math, numpy as np
from scipy import fftpack as fft
from matplotlib import pyplot as plot

def spectrum_with_plots(array, freq, sample_rate,pic_name):
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
        
        # Sum energy in bins +/- 2.5%  the calculated value
        index_offset = int(freq* 0.025 *sample_time*2.0 + 0.5)
        signal_power = 0.0
        for i in range(frequency_index - index_offset, frequency_index + index_offset + 1):
            signal_power += c[i]
        signal_magnitude = math.sqrt(signal_power)

        # Make a little extra space between the subplots
        plot.subplots_adjust(hspace=.4)   
        plot.subplot(311)
        plot.plot(t, a, 'bo', t, a, 'k--')
        plot.xlim(0,sample_time)
        plot.xlabel('time(sec)')
        plot.ylabel('amplitude(V)')
        plot.grid(True)

        plot.subplot(312)
        plot.plot( f,  b, 'ro')
        plot.xlim(0, sample_rate/2.0)
        plot.xlabel('frequency(Hz)')
        mag_str = "magnitude \n%.3f"%(signal_magnitude)
        plot.ylabel(mag_str)
        plot.grid(True)

        plot.subplot(313)
        plot.plot( f,  c, 'go')
        plot.xlim(0, sample_rate/2.0)
        plot.xlabel('frequency(Hz)')
        plot.ylabel('power')
        plot.grid(True)
        
        #plot.show()
        plot.savefig(pic_name,dpi=200)
        plot.clf()
        
        return(signal_magnitude,b)
    except Exception as e:
        print "exception in spectrum_with_plots: " + repr(e)
def main(infile,_freq,name):
    
    outfile = name + "fft_data.csv"
    pic_name = name + "fft_graphs.png"
    sample_rate = 256

    i_f = open(infile,  'r')
    a = []
    for line in i_f:
        a.append(int(line.strip())-128)
    signal_magnitude,magnitude_spectrum = spectrum_with_plots(a,_freq,sample_rate,pic_name)
    o_f = open(outfile,  'w')
    for bin in magnitude_spectrum:
        o_f.write(repr(bin) + '\n')
    return signal_magnitude

if __name__ == "__main__":
    sys.exit(main())
