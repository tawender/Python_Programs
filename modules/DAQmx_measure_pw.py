import sys
sys.path.append("Z:\python programs\modules")
import pyNIDAQ
import numpy


try:
    samples = 100
    a=numpy.zeros(samples,dtype=numpy.float64)
    device = "Dev2"
    channel  = "ctr1"
    minT = 0.000001
    maxT = 0.002
    slope = 'falling'

    sum = 0
    num_averaged = 0

    for i in range(samples):
        pw = pyNIDAQ.Pulse_Width_Measurement_Thread(device,channel,minT,maxT,slope)
        print "measuring %2d: "%(i+1),
        width = pw.measure_pulse_width()
        print "pulse width was: %.9f"%width
        a[i] = width

    mean = numpy.mean(a)
    print "mean of results is: %.9f"%mean
    
    stdev=numpy.std(a)
    print "standard deviation is: %.9f"%stdev
    
    for i in range(samples):
        if abs(a[i]-mean) > stdev:
            print "sample %d thrown out of averaging"%i
        else:
            sum += a[i]
            num_averaged += 1
            
    result = sum / num_averaged
    print "result is: %.9f"%result

except Exception as e:
    print "Exception found: " + repr(e)