import visa
import numpy
import threading
import time
import Queue
from matplotlib import pyplot as plot
import os.path
import sys
sys.path.append("T:\python programs\modules")
import Instruments
import pyNIDAQ



class data_plots(object):
    def __init__(self,path):
        self.plot_number = 1
        self.path = path

    def add_plot(self,a,name,samp_per_sec,x_units,y_units,y_scale=-1):
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
            dt = 1.0 / float(samp_per_sec)
            time_graphed = len(a) * dt
            t = numpy.arange(0,time_graphed,dt,dtype="float")

            plot.subplot(1,1,1)
            plot.plot(t,a,'.',markersize=3)
            plot.xlim(0, time_graphed)
            if y_scale != -1: plot.ylim(y_scale)
            plot.xlabel(x_units)
            plot.ylabel(y_units)
            plot.title(name)
            plot.grid(True)

            fig_name = self.path + "\%02d_"%self.plot_number + name + ".png"
            self.plot_number += 1
            plot.savefig(fig_name,dpi=200)
            plot.clf()
        except Exception as e:
            print "Exception in add_plot: " + repr(e)
            raise e

    def plot_currents(self,measured_currents,sourced_currents,y_scale=-1):
        """
        """
        try:
            plot.subplot(1,1,1)
            plot.plot(sourced_currents,measured_currents,'bo',
                      sourced_currents,measured_currents,'k--',label='data',markersize=3)
            if y_scale != -1: plot.ylim(y_scale)
            plot.xlabel("measured current (Amps)")
            plot.ylabel("sourced current (Amps)")
            plot.title("Measured Current vs. Sourced Current")
            plot.grid(True)

            #calculate the trendline
            z = numpy.polyfit(measured_currents,sourced_currents,1)
            eq = numpy.poly1d(z)
            eq_str = "y = %.5fx + (%.5f)"%(z[0],z[1])
##            plot.plot(measured_currents,eq(measured_currents),'r--',label=)
##            plot.text(1.0,4.0,eq_str)

            fig_name = self.path + "\%02d_"%self.plot_number + "Input_vs_Measured.png"
            self.plot_number += 1
            plot.savefig(fig_name,dpi=200)
            plot.clf()

##            print "\n  Best fit equation for measured current data: %s"%(eq_str)
##            test_report.write("\n  Best fit equation for measured current data: %s\n"%(eq_str))

            return (eq,eq_str)

        except Exception as e:
            print "Exception in plot_currents(): " + repr(e)
            raise e




def array_to_csv(csv_file,array,test_name,samp_per_sec,x_units,y_units,y_scale=-1,make_plot=True):
    try:
        csv_file.write("%s,%f,%s,%s,"%(test_name,samp_per_sec,x_units,y_units))
        for i in range(len(array)):
            csv_file.write("%f,"%float(array[i]))
        csv_file.write("\n")
        if make_plot: graphs.add_plot(array,test_name,samp_per_sec,x_units,y_units,y_scale)
    except Exception as e:
        print "Exception writing array data to csv file: " + repr(e)
        raise e

def measure_Ibat(I_load):
    try:

        print "\n  Isource of %.3f"%I_load

        meas = Ibat_meas.Take_Voltage_Measurement()
        Vfixture_arr = meas[0]
        Vcircuit_arr = meas[1]

        print "    average voltage ch0(fixture): %.6fV, adjusted: %.6fV"\
              %(numpy.average(Vfixture_arr),numpy.average(Vfixture_arr)-fixture_Imeas_Voffset)
        print "    average voltage ch2(circuit): %.6fV, adjusted: %.6fV"\
              %(numpy.average(Vcircuit_arr),numpy.average(Vcircuit_arr)-I_sourced_offset)

        Ibat_sourced_arr = (Vcircuit_arr - I_sourced_offset) / tot_resistance
        Ibat_fixture_arr = abs(Vfixture_arr - fixture_Imeas_Voffset)

        Ibat_sourced_avg = numpy.average(Ibat_sourced_arr)
        Ibat_fixture_avg = numpy.average(Ibat_fixture_arr)

        test_name = "Isourced of %.5f Amps"%(Ibat_sourced_avg)
        array_to_csv(test_data,Ibat_sourced_arr,test_name,Ibat_meas_sampleRate,"time(sec)","volts",(0.0,6.0))

        test_name = "Ibat from fixture of %.5f Amps"%(Ibat_fixture_avg)
        array_to_csv(test_data,Ibat_fixture_arr,test_name,Ibat_meas_sampleRate,"time(sec)","volts",(0.0,6.0))

        pct_err = ( (Ibat_fixture_avg-Ibat_sourced_avg) / Ibat_sourced_avg ) * 100.0

        print "  Measured source current: %0.5fA, measured fixture current: %.5fA, %6.3f%% error"\
              %(Ibat_sourced_avg,Ibat_fixture_avg,pct_err)
        test_report.write("  Measured source current: %0.5fA, measured fixture current: %.5fA, %6.3f%% error\n"\
                          %(Ibat_sourced_avg,Ibat_fixture_avg,pct_err))

        return (Ibat_sourced_avg,Ibat_fixture_avg)

    except Exception as e:
        print "Exception in measure_Ibat(): " + repr(e)
        raise e



def measure_Vbat(V_level):
    try:
        dmm_reading = dmm.measure_voltage(dmm_range)
        print "  Measurement with Vbat of %8.5fV(dmm) = "%(dmm_reading),

        readings = Vbat_meas.Take_Voltage_Measurement()
        if readings == 'error':
            print "\nError measuring Ibat"
            test_report.write("Error measuring Ibat")
            return 'error'

        avg = numpy.average(readings - fixture_Vbat_Voffset)
        pct_err = (dmm_reading-avg) / dmm_reading * 100.0

        print "%7.5fV(daq offset adjusted), %6.3f%% error"%(avg,pct_err)
        test_report.write("  measured voltage with input of %8.5fV(dmm) = %7.5fV(daq), %6.3f%% error\n"\
                          %(dmm_reading,avg,pct_err))

        test_name = "Vsource=%.2f__measurement avg=%.4f"%(V_level,avg)
        array_to_csv(test_data,readings,test_name,Vbat_meas_sampleRate,"time(sec)","volts",(3.0,10.0))

        return avg
    except Exception as e:
        print "Exception in measure_Vbat(): " + repr(e)
        raise e


def use_equation(eq,I_measurements,I_sourced_list):
    try:
        print "\nUsing best fit equation on measured data:"
        test_report.write("\nUsing best fit equation on measured data:\n")

        for j in range(len(I_measurements)):
            print "  measured value of %.4fA converted to %.4fA, %5.2f%% error"\
                  %(I_measurements[j],eq(I_measurements[j]),I_sourced_list[j])
            test_report.write("  measured value of %.4fA converted to %.4fA, %5.2f%% error\n"\
                              %(I_measurements[j],eq(I_measurements[j]),I_sourced_list[j]))

    except Exception as e:
        print "Exception in use_equation(): " + repr(e)

def main():
    try:

        print "\n***************************************************************************"
        print "Beginning Program ..."


        #****************************************************************
        #*********directory setup****************************************
        now_text = time.strftime("%Y_%m_%d - %H_%M_%S")
        dir_name = "Test Results - %s"%(now_text)
        cwd = os.getcwd()

        global test_dir
        test_dir = cwd + "/" + dir_name
        os.mkdir(test_dir)

        plot_dir = (cwd + "/" + dir_name + "/test_plots")
        os.mkdir(plot_dir)
        global graphs
        graphs = data_plots(plot_dir)

        global test_report
        test_report = open(test_dir + "/Test_Report_" + now_text + ".txt",'w')
        test_report.write("Test report for Battery Current/Voltage Measurement Fixture: ")
        test_report.write(": %s\n\n"%(now_text))

        global test_data
        test_data = open(test_dir + "/Test_Data_" + now_text + ".csv",'w')
        test_data.write("Test Name,samples per second,x-axis units,y-axis units,data\n")
        #*********************************************************************



        #*********************************************************************
        #***********DAQ card setup********************************************
        BNC_6259 = 'Dev1'

        global Ibat_meas_sampleRate
        Ibat_meas_sampleRate = 100000.0
        Ibat_meas_time_sec = 0.5
        num_Ibat_meas_samples = int(Ibat_meas_sampleRate * Ibat_meas_time_sec)
        Ibat_meas_minV = -10.0
        Ibat_meas_maxV = 10.0
        global Ibat_meas
        Ibat_meas = pyNIDAQ.AI_Voltage_Channels()
        Ibat_meas.Config_Finite_Voltage_Measurement("Dev1/ai0,Dev1/ai2",Ibat_meas_minV,Ibat_meas_maxV,
                                                    Ibat_meas_sampleRate,num_Ibat_meas_samples,
                                                    meas_type='DIFF')
        global Ibat_source
        Ibat_source = pyNIDAQ.AI_Voltage_Channels()
        Ibat_source.Config_Finite_Voltage_Measurement("Dev1/ai2",Ibat_meas_minV,Ibat_meas_maxV,
                                                    Ibat_meas_sampleRate,num_Ibat_meas_samples,
                                                    meas_type='DIFF')
        global Vbat_meas_sampleRate
        Vbat_meas_sampleRate = 100000.0
        Vbat_meas_time_sec = 0.5
        num_Vbat_meas_samples = int(Vbat_meas_sampleRate * Vbat_meas_time_sec)
        Vbat_meas_minV = -10.0
        Vbat_meas_maxV = 10.0
        global Vbat_meas
        Vbat_meas = pyNIDAQ.AI_Voltage_Channel()
        Vbat_meas.Config_Finite_Voltage_Measurement(BNC_6259,"ai1",Vbat_meas_minV,Vbat_meas_maxV,
                                                    Vbat_meas_sampleRate,num_Vbat_meas_samples,
                                                    meas_type='DIFF')
        #*********************************************************************



        #*********************************************************************
        #**********instrument setup******************************************
        global ps
        ps=Instruments.PowerSupply_E3632A("GPIB::7","power_supply")
        ps.output_on()

        global sm_2400
        sm_2400 = Instruments.sourcemeter_2400("GPIB::4",'Voltage Source')
        sm_2400.reset()
        sm_2400.set_Vsource()
        sm_2400.set_source_level(9.5)
        sm_2400.set_compliance_level(.001)
        sm_2400.output_on()

        global dmm
        dmm = Instruments.DMM_34401A("GPIB::22",'Agilent 34401A DMM')
        global dmm_range
        dmm_range = 10
        #*********************************************************************



        #*********************************************************************
        #***********variables********************************************
        global tot_resistance
        tot_resistance = 1.017
        I_list = [0.5,1.0,1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0]
        V_list = [4.0,4.5,5.0,5.5,6.0,6.5,7.0,7.5,8.0,8.5,9.0,9.5,10.0]
        I_sourced_list = []
        I_fixture_list = []

        #stores the offset of the DAQ channel measuring the total circuit voltage
        global I_sourced_offset
        I_sourced_offset = -0.0001

        #stores the offset of the DAQ channel measuring the fixture output  'current measure'
        global fixture_Imeas_Voffset
        fixture_Imeas_Voffset = -0.0002

        #stores the offset of the DAQ channel measuring the fxture output 'Vbat measure'
        global fixture_Vbat_Voffset
        fixture_Vbat_Voffset = 0.0001
        #*********************************************************************



        #*********************************************************************
        #***********main test loop********************************************
        print "\nUsing total system resistance of %.4f ohms for calculation of actual current..."%(tot_resistance)
        print "Applying voltage offset correction of %.6fV on channel measuring total circuit..."%(I_sourced_offset)
        print "Applying voltage offset correction of %.6fV on channel measuring Imeas fixture output..."%(fixture_Imeas_Voffset)
        print "Applying voltage offset correction of %.6fV on channel measuring Vbat fixture output..."%(fixture_Vbat_Voffset)
        print "\nTesting current detection circuit(-1 gain expected):"

        test_report.write( "\nUsing total system resistance of %.4f ohms for calculation of actual current...\n"%(tot_resistance))
        test_report.write( "Applying voltage offset correction of %.6fV on channel measuring total circuit...\n"%(I_sourced_offset))
        test_report.write( "Applying voltage offset correction of %.6fV on channel measuring fixture Imeas output...\n"%(fixture_Imeas_Voffset))
        test_report.write( "Applying voltage offset correction of %.6fV on channel measuring fixture Vbat output...\n"%(fixture_Vbat_Voffset))
        test_report.write( "\nTesting current detection circuit(-1 gain expected):\n")

        for I in I_list:

            ps.set_voltage_limit(I)
            ps.output_on()
            time.sleep(.3)

            (Isource,Ifixture) = measure_Ibat(I)
            I_sourced_list.append(Isource)
            I_fixture_list.append(Ifixture)

            ps.output_off()
            time.sleep(5)

        ps.set_voltage_limit(0.0)
        ps.output_off()

        graphs.plot_currents(I_fixture_list,I_sourced_list,y_scale=-1)

        print "\nTesting Vbat monitoring circuit:"
        test_report.write("\nTesting Vbat monitoring circuit:\n")
        for V in V_list:

            sm_2400.set_source_level(V)
            time.sleep(0.2)
            measure_Vbat(V)

        sm_2400.set_source_level(0.0)
        sm_2400.output_off()
        #*********************************************************************





    except Exception as e:
        print "Exception in main(): " + repr(e)
        raise e

    finally:
        print "\n\n"



if __name__ == '__main__':
    main()





