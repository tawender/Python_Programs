import time
import math
import optparse
import os, fnmatch
import sys
import numpy
from matplotlib import pyplot as plot
from shutil import copy
from scipy.optimize import curve_fit




def discharge_function(x, a, b):
    return a*numpy.e**(-x*b)

class file_checker(object):
    def __init__(self,output_report=None):
        self.debug = True
        self.num_files_processed = 0
        self.output_report = output_report

    def find_files(self,pattern,search_dir,results_dir,show_plots):
        """Locate all files matching supplied filename pattern in and below
           supplied root directory.
        """
        try:
            self.num_files_processed += 1
            self.results_dir = results_dir
            self.show_plots = show_plots
            files_to_search = []
            dirs_to_search = []

            #create a list of files to search through later
            for root,dirs,files in os.walk(search_dir):
                for file in files:
                    if file.endswith('.csv') and (file.find('processed') == -1):
                        files_to_search.append(file)
                        dirs_to_search.append(root)
            print "found %d files to process..."%(len(files_to_search))

            #open and write heading to results table txt file
            filename = results_dir + "/results_table.txt"
            self.data_table = open(filename,'w')
            self.data_table.write("Data from file processing\n\n")
            self.data_table.write("cap sn,Rload (ohms),BSC esr(ohms),BSC cap(uF),")
            self.data_table.write("CHI esr(ohms),CHI cap(uF),CHI 75% tilt energy(J)\n")

            #process each file in the list of names
            for i in range(len(files_to_search)):
                self.process_file(dirs_to_search[i],files_to_search[i])

            print "\nFinished processing %d files.\nScript done."%len(files_to_search)
            self.output_report.write("processed %d files\n"%len(files_to_search))

        except Exception as e:
            print "Exception found in find_files(): " + repr(e)
            raise e



    def process_file(self,path,f_name):
        try:
            col_1 = []
            col_2 = []
            col_3 = []

            #******************************************************************
            #open file and put data into lists
            filename = os.path.join(path, f_name)
            print "\nAnalyzing %s ..."%(f_name)
            self.output_report.write("\n%s:\n"%(f_name))
            infile = open(filename,'r')
            self.num_files_processed += 1

            for line in infile:
                if line != '\n': #throw out blank lines
                    samples_list = line.split(",")
                    col_1.append(samples_list[0])   #time
                    col_2.append(samples_list[2])   #trigger
                    col_3.append(samples_list[1])   #load voltage

            infile.close()
            #******************************************************************



            #******************************************************************
            #get the necessary parameters from each file
            (self.sn,self.Rload,self.conversion_factor,self.scope_offset)=self.find_test_conditions(path,f_name)
            #******************************************************************



            #******************************************************************
            #run only the ideal data through the low pass filter to add effects of scope
            if 'IdealData' in f_name:
                self.Vcap_array = self.scope_low_pass(self.Vcap_array)
                print 'ideal data ran through filter'
            #******************************************************************




            #******************************************************************
            #change lists(waveform data) to numpy arrays
            data_beginning = 2

            self.time_array = numpy.zeros(len(col_1)-data_beginning,dtype=float)
            for i in range(len(self.time_array)):
                self.time_array[i] = float(col_1[i+data_beginning]) / 1000.0 #msec -> sec

            self.Vcap_array = numpy.zeros(len(col_2)-data_beginning,dtype=float)
            for i in range(len(self.Vcap_array)):
                self.Vcap_array[i] = float(col_2[i+data_beginning]) * self.conversion_factor - (self.scope_offset*self.conversion_factor)

            self.discharge_trigger_array = numpy.zeros(len(col_3)-data_beginning,dtype=float)
            for i in range(len(self.discharge_trigger_array)):
                self.discharge_trigger_array[i] = float(col_3[i+data_beginning])
            #******************************************************************





            #******************************************************************
            #this section will find certain waveform characteristics to be used below

            #find the pre-trigger average voltage - total cap was charged to
            self.pretrigger_Vavg = numpy.average(self.Vcap_array[:500])
            if self.debug: print '  pretrigger average voltage is %.3fV'%self.pretrigger_Vavg

            #find the time between samples (delta t) from the array of timestamps
            self.sample_time_delta = -(self.time_array[1] - self.time_array[11]) / 10.0
            if self.debug: print '  delta t between samples: %.10fsec'%(self.sample_time_delta)

            #find the sample number where the discharge trigger happens
            for i in range(len(self.time_array)):
                if self.time_array[i] >= 0.0:
                    self.trigger_sample_number = i
                    break
            if self.debug: print '  found discharge trigger at sample number %d'%(self.trigger_sample_number)

            #find sample number where t=250usec
            for i in range(len(self.time_array)):
                if self.time_array[i] >= .000250:
                    self._250usec_sample_number = i
                    break
            if self.debug: print '  found %.3fV at sample number %d (t=250usec)'%(self.Vcap_array[self._250usec_sample_number],
                                                                                self._250usec_sample_number)

            #find voltage at the 250usec mark and 40% of that voltage
            self.Vcap_at_250usec = self.Vcap_array[self._250usec_sample_number]
            if self.debug: print '  Vcap at 250usec is %.3fV'%self.Vcap_array[self._250usec_sample_number]
            self._40pct_of_250usec_Vcap = self.Vcap_array[self._250usec_sample_number] * 0.4
            if self.debug: print '  discharge to 40%% voltage is %.3fV'%self._40pct_of_250usec_Vcap,

            #find sample number where cap voltage has dropped to 40% of voltage found
            #on the caps at 250usec after discharge begins
            for i in range(self._250usec_sample_number,len(self.Vcap_array)):
                if self.Vcap_array[i] <= self._40pct_of_250usec_Vcap:
                    self._40pct_of_250usec_sample_number = i
                    break
            if self.debug: print '  found at sample number %d'%(self._40pct_of_250usec_sample_number)

            #find the amount of time it took to discharge cap to 40%
            self._40pct_discharge_time = self.time_array[self._40pct_of_250usec_sample_number] - \
                                        self.time_array[self._250usec_sample_number]
            if self.debug: print '  it took %.2fmsec to discharge to 40%%'%(self._40pct_discharge_time*1000.0)

            #find the voltage level that is 25% of initial cap voltage
            self._25pct_discharge_voltage = self.pretrigger_Vavg * 0.25
            if self.debug: print '  discharge to 25%% voltage is %.3fV'%(self._25pct_discharge_voltage),

            #find sample number where cap voltage has dropped to 25% of initial cap charge voltage
            for i in range(self.trigger_sample_number,len(self.Vcap_array)):
                if self.Vcap_array[i] <= self._25pct_discharge_voltage:
                    self._25pct_sample_number = i
                    break
            if self.debug: print '  found at sample number %d'%(self._25pct_sample_number)

            #find the amount of time it took to discharge cap to 25% of initial voltage
            self._25pct_discharge_time = self.time_array[self._25pct_sample_number] - \
                                        self.time_array[self.trigger_sample_number]
            if self.debug: print '  it took %.2fmsec to discharge to 25%%'%(self._25pct_discharge_time*1000.0)
            #******************************************************************





            #******************************************************************
            #BSC calculations
            self.calculated_BSC_energy_out = self.BSC_energy_out()
            self.calculated_BSC_pulsed_cap = self.BSC_DC_cap()
            self.calculated_BSC_pulsed_ESR = self.BSC_pulsed_ESR()
            #******************************************************************




            #******************************************************************
            #CHI calculations
            #
            #find trendline coefficients
            enhanced_weighted_coeff = self.find_trendline_coefficients()
            self.enhanced_weighted_coeff_a = enhanced_weighted_coeff[0]
            self.enhanced_weighted_coeff_b = enhanced_weighted_coeff[1]

            #find the trendline data using samples back to time t=0
            self.enhanced_weighted_trendline_data = discharge_function(self.time_array[self.trigger_sample_number:],
                                                    self.enhanced_weighted_coeff_a,self.enhanced_weighted_coeff_b)
            self.CHI_esr = self.CHI_find_ESR()
##            self.CHI_esr_new = self.CHI_find_ESR_new()
##            self.CHI_esr_newer = self.CHI_find_ESR_newer()
            self.CHI_capacitance = self.CHI_find_capacitance()
##            self.CHI_capacitance_new = self.CHI_find_capacitance_new()
##            self.CHI_capacitance_newer = self.CHI_find_capacitance_newer()
            self.CHI_75pct_tilt_energy = self.CHI_find_75pct_tilt_energy()
            #******************************************************************




            #******************************************************************
            #do things with the calculations
            self.make_new_csv(f_name,self.enhanced_weighted_coeff_a,self.enhanced_weighted_coeff_b)

            if self.show_plots:
                self.plot_data(f_name)

            self.write_calculations_to_csv()
            #******************************************************************





            # use recorded scope offset and adjust (subtract if positivce offset) and save corrected attenuated voltage,
            # offset should be parameter entered in the command line

            #rescale data back to the cap stack voltages using the attenuation Vdiv which should be parameter entered in the command line

            #******************************************************************
            #find and save avergae of first 500 sample to use as pretrigger value

            #Vpreavg = numpy.average(Vcap_array[:500])
            #trig_val = -2E-08
            #time_above = 0.0
            #rolling_avg = 0.0


            #BSC ESR/Cap calcuation methods:
            # calculate & save  energy out using  piece wise intergration of voltage over R load from discharge trigger to end of discharge
            # calculate & save cap. based on Vpeak and Eout from above
            # save discharge array data from 250us after trigger for further processing
            # Calculate & save Pulsed ESR  using Cdc and Vinitial(at250us after trigger) and Vf(at 40% of Vinitial) => see BSC formula (will
            #need to input Rload as a paramaeter from command line for this calculation)
            # Output and Save above data BSC : Eout/Cap/ESR for each .csv file processed

            # CHI ESR/Cap calculations:
            # Use discharge array data from 250us after trigger
            # use trenadline curve fit to get equation of exponential discharge decay
            # Solve equaiton for t = 0 to get initial Vdrop due to ESR
            # Calculate Vesr = Vpreavg - Vdrop
            # Calculate and save ESR = Vesr/Idrop => Idrop =Vdrop/Rload
            # Calculate and Save Cap from trenadline curve fit  equation using coefficient and equate to = -t/RC => sloce for C in uF
            #  save BSC and CHI ESR/CAP measurements to log file similar to Ipeak/I2T ec.and
        except Exception as e:
            print "Exception in process_file(): " + repr(e)
            raise e


    def BSC_energy_out(self):
        """this function uses the Boston Scientific method for calculating the energy out of
           a charged capacitor
        """
        energy_out = 0.0

        for i in range(self.trigger_sample_number,len(self.Vcap_array)-1):
            energy_out += self.sample_time_delta * (self.Vcap_array[i]**2 / self.Rload)

        print "   BSC method energy out: %.2fJoules"%(energy_out)
        self.output_report.write("   BSC method energy out: %.2fJoules\n"%(energy_out))

        return energy_out

    def BSC_DC_cap(self):
        """calculate the DC capacitance from the energy formula solved for capacitance
        """
        DC_cap = 2.0 * self.calculated_BSC_energy_out / (self.pretrigger_Vavg**2)

        print "   BSC method DC capacitance: %.2fuF"%(DC_cap*1000000.0)
        self.output_report.write("   BSC method DC capacitance: %.2fuF\n"%(DC_cap*1000000.0))

        return DC_cap

    def BSC_pulsed_ESR(self):
        """
        """
        esr = -( self._40pct_discharge_time / (self.calculated_BSC_pulsed_cap * \
                math.log(self._40pct_of_250usec_Vcap/self.Vcap_at_250usec))) - self.Rload

        print "   BSC method pulsed ESR: %.2f ohms"%(esr)
        self.output_report.write("   BSC method pulsed ESR: %.2f ohms\n"%(esr))

        return esr

    def find_trendline_coefficients(self):
        """use the curve_fit function to find the trendline coefficients for the cap discharge equation
        """
        #create new arrays using only the samples gathered 250usec after trigger
        post_250usec_time_array = self.time_array[self._250usec_sample_number:]
        post_250usec_Vcap_array = self.Vcap_array[self._250usec_sample_number:]

        #using weighting in the function to find the equation coefficients
        VCapArrayWeighting = numpy.reciprocal(post_250usec_Vcap_array)
        popt2, pcov2 = curve_fit(discharge_function,post_250usec_time_array,post_250usec_Vcap_array, sigma=VCapArrayWeighting)
        EnhancedWeighting = numpy.reciprocal(popt2[0]*numpy.exp(post_250usec_time_array*(-popt2[1])))
        coeff,pcov3 = curve_fit(discharge_function,post_250usec_time_array,post_250usec_Vcap_array, sigma=EnhancedWeighting )

        print "   **********"
        print "   trendline coefficients: %.2f, %.2f"%(coeff[0],coeff[1])
        self.output_report.write("   **********\n")
        self.output_report.write("   trendline coefficients: %.2f, %.2f\n"%(coeff[0],coeff[1]))

        return coeff

##    def CHI_find_ESR(self):
##        """find the cap ESR using the CHI method using a trendline evaluated at t=0 and using the
##           voltage drop to find the ESR
##        """
##        Vdrop = discharge_function(0.0,self.enhanced_weighted_coeff_a,self.enhanced_weighted_coeff_b)
##        Vesr = self.pretrigger_Vavg - Vdrop
##        Idrop = Vdrop / self.Rload
##        CHI_esr = Vesr / Idrop
##
##        print "   Vcap pretrigger average: %.2fV"%(self.pretrigger_Vavg)
##        self.output_report.write("   Vcap pretrigger average: %.2fV\n"%(self.pretrigger_Vavg))
##        print "   Vdrop from trendline at t=0: %.2fV"%(Vdrop)
##        self.output_report.write("   Vdrop from trendline at t=0: %.2fV\n"%(Vdrop))
##        print "   Vesr: %.2fV"%(Vesr)
##        self.output_report.write("   Vesr: %.2fV\n"%(Vesr))
##        print "   Idrop: %.2fAmps"%(Idrop)
##        self.output_report.write("   Idrop: %.2fAmps\n"%(Idrop))
##        print "   CHI method cap ESR: %.3f"%(CHI_esr)
##        self.output_report.write("   CHI method cap ESR: %.3f\n"%(CHI_esr))
##
##        return CHI_esr
##
##    def CHI_find_ESR_new(self):
##        """use quadradic equation and measured values to find the capacitor esr
##            *see pdf in subversion for derivation of the terms used in the quadratic
##        """
##        integrated_I2 = 0.0
##        for i in range(self.trigger_sample_number,len(self.Vcap_array)-1):
##            integrated_I2 += self.sample_time_delta * ((self.Vcap_array[i] / self.Rload)**2)
##
##        tao = 1.0 / self.enhanced_weighted_coeff_b
##
##        a = integrated_I2 * (2.0/self.pretrigger_Vavg**2)
##        b = ( 2.0/(self.pretrigger_Vavg**2) ) * (self.calculated_BSC_energy_out + self.Rload + integrated_I2)
##        c = ( ( 2.0/(self.pretrigger_Vavg**2) ) * self.Rload * self.calculated_BSC_energy_out ) - tao
##
##        esr = (-b + math.sqrt(b**2 - (4*a*c)))/(2*a)
##
##        print "   CHI method cap ESR new: %.3f"%(esr)
##        self.output_report.write("   CHI method cap ESR new: %.3f\n"%(esr))
##
##        return esr

    def CHI_find_ESR(self):
        """
        """
        tao = 1.0 / self.enhanced_weighted_coeff_b

        integrated_V = 0.0
        for i in range(self.trigger_sample_number,len(self.Vcap_array)-1):
            integrated_V += self.sample_time_delta * (self.Vcap_array[i]**2)

        esr = self.Rload * ( self.pretrigger_Vavg*math.sqrt(tao/( 2.0*integrated_V)) -1 )

        print "   CHI method cap ESR: %.3fohms"%(esr)
        self.output_report.write("   CHI method cap ESR: %.3fohms\n"%(esr))

        return esr

##    def CHI_find_capacitance(self):
##        """use the CHI method of finding the capacitance by solving the exponential
##           decay formula for capacitance and using Rload, Vcap at 250usec after trigger,
##           Vcap at discharge to 40%, and time of discharge to 40% in equation
##        """
##        c = 1.0 / ((self.Rload + self.CHI_esr) * self.enhanced_weighted_coeff_b)
##        print "   CHI method capacitance: %.2fuF"%(c*1000000.0)
##        self.output_report.write("   CHI method capacitance: %.2fuF\n"%(c*1000000.0))
##
##        return c
##
##    def CHI_find_capacitance_new(self):
##        """use the CHI method of finding the capacitance by solving the exponential
##           decay formula for capacitance and using Rload, Vcap at 250usec after trigger,
##           Vcap at discharge to 40%, and time of discharge to 40% in equation
##        """
##        c = 1.0 / ((self.Rload + self.CHI_esr_new) * self.enhanced_weighted_coeff_b)
##        print "   CHI method capacitance new: %.2fuF"%(c*1000000.0)
##        self.output_report.write("   CHI method capacitance new: %.2fuF\n"%(c*1000000.0))
##
##        return c

    def CHI_find_capacitance(self):
        """use the CHI method of finding the capacitance by solving the exponential
           decay formula for capacitance and using Rload, Vcap at 250usec after trigger,
           Vcap at discharge to 40%, and time of discharge to 40% in equation
        """
        c = 1.0 / ((self.Rload + self.CHI_esr) * self.enhanced_weighted_coeff_b)
        print "   CHI method capacitance: %.2fuF"%(c*1000000.0)
        self.output_report.write("   CHI method capacitance: %.2fuF\n"%(c*1000000.0))

        return c

    def CHI_find_75pct_tilt_energy(self):
        """find the energy discharged from the capacitors from the initial voltage to the point
           where the caps have been discharged to 25% of the initial voltage - (2) 50% tilt reductions in voltage
        """
        energy = 0.0
        for i in range(self.trigger_sample_number,self._25pct_sample_number+1):
            energy += (self.Vcap_array[i]**2 / self.Rload) * self.sample_time_delta

        print "   75%% tilt energy (integrated) %.3fJoules"%energy
        self.output_report.write("   75%% tilt energy (integrated) %.3fJoules\n"%energy)

        return energy

    def echo_parameters(self):
        """print the parameters used for file analysis to the screen and the output report
        """
        print "Parameters used for analysis:"
        self.output_report.write("\nParameters used for analysis:\n")
        print "    Rload: %.2fohms, Vcap conversion factor: %.2f, scope offset: %.3fV"%( \
                self.Rload,self.conversion_factor,self.scope_offset)
        self.output_report.write("    Rload: %.2fohms, Vcap conversion factor: %.2f, scope offset: %.3fV\n\n"%( \
                self.Rload,self.conversion_factor,self.scope_offset))

    def make_new_csv(self,f,a,b):
        outfile = open(self.results_dir + '/' + f[:len(f)-4] + '_processed.csv','w')
        outfile.write("time,Vtrigger,Vcap,trendline\n")

        for i in range(len(self.time_array)):
            outfile.write("%f,%f,%f"%(self.time_array[i],
                                        self.discharge_trigger_array[i],
                                        self.Vcap_array[i]))
            if self.time_array[i] >= 0.0:
                outfile.write(",%f"%(discharge_function(self.time_array[i],a,b)))

            outfile.write("\n")
        outfile.close()

    def find_test_conditions(self,path,f_name):
        print 'attempting to unmayhem test conditions - give me a second...'
        print "path: %s"%path
        dir = path.split('\\')[len(path.split('\\'))-1]
        print "dir: %s"%dir
        print "f_name: %s"%f_name

        cap_sn = f_name.split("_")[0].split("-")[1]
        print "cap s/n: %s"%cap_sn
        offset = float(dir.split(" ")[len(dir.split(" "))-1].replace("mV",""))/1000.0
        print "offset: %fV"%offset
        conversion = float(dir.split(" ")[len(dir.split(" "))-2])
        print "conversion: %f"%conversion
        load_resistance = float(f_name.split("_")[1])
        print "load resistance: %fohms"%load_resistance

        return (cap_sn,load_resistance,conversion,offset)

    def write_calculations_to_csv(self):
        """write stuff
        """
        self.data_table.write("%s,%.3f,%.3f,%.2f,%.3f,%.2f,%.1f\n"%(self.sn,self.Rload,self.calculated_BSC_pulsed_ESR,
                                            self.calculated_BSC_pulsed_cap*1000000.0,
                                            self.CHI_esr,self.CHI_capacitance*1000000.0,self.CHI_75pct_tilt_energy))
        self.data_table.flush()

    def plot_data(self,name):
        try:
            x=self.time_array

            fig = plot.figure()

            #plot calculated data
            plot.plot(x*1000.0,self.Vcap_array,'b-',label='Vcap')
            plot.plot(x*1000.0,self.discharge_trigger_array,'r-',label='trigger')
            plot.plot(x[self._250usec_sample_number:]*1000.0,self.Vcap_array[self._250usec_sample_number:],'c-')
##            plot.plot(x[self.trigger_sample_number:]*1000.0,self.trendline_data,'m-',label='trendline')
            plot.plot(x[self.trigger_sample_number:]*1000.0,self.enhanced_weighted_trendline_data,
                                                            'HotPink',label='enhanced weighted')
##            plot.plot(x[self.trigger_sample_number:]*1000.0,self.weighted_trendline_data,'DarkGoldenRod',label='weighted')

            #plot vertical lines on graph for significant times
            plot.plot([x[self.trigger_sample_number]*1000.0,x[self.trigger_sample_number]*1000.0],
                        [0.0,500.0],'k-')
            plot.plot([x[self._250usec_sample_number]*1000.0,x[self._250usec_sample_number]*1000.0],
                        [0.0,500.0],'k-')
            plot.plot([x[self._40pct_of_250usec_sample_number]*1000.0,x[self._40pct_of_250usec_sample_number]*1000.0],
                        [0.0,500.0],'k-')
            plot.plot([x[self._25pct_sample_number]*1000.0,x[self._25pct_sample_number]*1000.0],
                        [0.0,500.0],'k-')

            plot.xlabel('time(msec)')
            plot.ylabel('Cap Voltage(volts)')
            plot.title(name,fontsize=10)
            plot.legend()
            plot.show()
            plot.close(fig)


        except Exception as e:
            print "Exception in plot_data(): " + repr(e)
            raise e

    def scope_low_pass(self,input):
        """a function to emulate the RC time constant of the front end of an oscilloscope.
           The ideal capacitor data is run through this function to show the effects of the scope
           on the end results.
        """
        last_output = input[0]
        R = 700000
        C = 16e-12
        a = self.sample_time_delta / (self.sample_time_delta + R*C)
        b = 1- a
        output = []
        for point in input:
            last_output = a*point + b*last_output
            output.append(last_output)
        return output




def main(argv=None):

    #********************************************
    # Parse command line options
    if argv is None:
        argv = sys.argv
    p = optparse.OptionParser()
    p.add_option("-d", action="store", type='string',  dest="search_dir")
    p.add_option("--dir", action="store", dest="search_dir")
    p.add_option("-p", action="store_true", dest="plots")
    p.add_option("--plots", action="store_true", dest="plots")

    # Set default values for options:
    p.set_defaults(search_dir=os.getcwd(),show_plots=False)
    opts, args = p.parse_args()
    # Retrieve the option settings:
    search_dir = opts.search_dir.replace('"','')
    show_plots = opts.plots
    #********************************************



    #********************************************
    # create a directory and report to keep track of results
    now_text = time.strftime("%Y_%m_%d - %H_%M_%S")
    results_dir = search_dir + "/Analysis Results - %s"%(now_text)
    os.mkdir(results_dir)
    report_path = results_dir + "/analysis_results_" + now_text + ".txt"
    output_report = open(report_path,'w')
    output_report.write("Output report - %s\n"%(now_text))
    #********************************************


    #********************************************
    #find files and search each one
    f = file_checker(output_report)
    f.find_files("*.csv",search_dir,results_dir,show_plots)
    #********************************************


if __name__ == '__main__':
    sys.exit(main())

