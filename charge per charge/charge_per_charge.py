from contextlib import closing
import chtelemetry
import sys
sys.path.append("C:/Python27/Lib/site-packages/chtelemetry")
import fwdata
import threading
import logging
import time
import struct
import visa
import numpy
import os.path
from Queue import Queue
from matplotlib import pyplot as plot
from ConfigParser import ConfigParser
import pylab
import csv

##sys.path.append(os.getcwd() + "\modules")
sys.path.append("T:/python programs/modules")
import Instruments
import pyNIDAQ
import count
import csv_ops


MAX_COMMAND_ATTEMPTS = 5
MAX_SHOCK_VOLTAGE = 225


class TelemetryError(Exception):
    pass

class TelemetryCommandError(Exception):
    pass

class TimeoutError(Exception):
    pass

class GPIBError(Exception):
    pass

class data_plots(object):
    def __init__(self,path,dut_sn):
        self.plot_number = 1
        self.path = path
        self.dut_sn = dut_sn

    def make_patch_spines_invisible(self,ax):
            ax.set_frame_on(True)
            ax.patch.set_visible(False)
            for sp in ax.spines.itervalues():
                sp.set_visible(False)

    def add_Ibat_Vbat_charging_plot(self,Vbat,Ibat,chrg,dut_powr,dut_enrg,
                                    name,samp_per_sec,charge_begin,charge_end):
        try:
            dt = 1.0 / samp_per_sec
            time_graphed = len(Vbat) * dt
            t = numpy.arange(0,time_graphed,dt,dtype="float")
            fig = plot.figure(figsize=(10,5))
            plot.title(name + "\n")
            fig.subplots_adjust(right=0.70)

            #make sure that the arrays are all same length
            if len(t) != len(Vbat): Vbat = Vbat[0:len(t)]
            if len(t) != len(Ibat): Ibat = Ibat[0:len(t)]
            if len(t) != len(chrg): chrg = chrg[0:len(t)]
            if len(t) != len(dut_powr): dut_powr = dut_powr[0:len(t)]
            if len(t) != len(dut_enrg): dut_enrg = dut_enrg[0:len(t)]

            #convert sample numbers to time
            cb = charge_begin / samp_per_sec
            ce = charge_end / samp_per_sec

            volts = fig.add_subplot(111)
            current = volts.twinx()
            charge = volts.twinx()
            power = volts.twinx()
            energy = volts.twinx()

            # Offset the right spine of current.  The ticks and label have already been
            # placed on the right by twinx above.
            charge.spines["right"].set_position(("axes", 1.11))
            power.spines["right"].set_position(("axes", 1.20))
            energy.spines["right"].set_position(("axes", 1.30))
            # Having been created by twinx, current has its frame off, so the line of its
            # detached spine is invisible.  First, activate the frame but make the patch
            # and spines invisible.
            self.make_patch_spines_invisible(charge)
            self.make_patch_spines_invisible(power)
            self.make_patch_spines_invisible(energy)
            # Second, show the right spine.
            charge.spines["right"].set_visible(True)
            power.spines["right"].set_visible(True)
            energy.spines["right"].set_visible(True)

            p1, = volts.plot(t,Vbat,"b-")
            #plot vertical lines to indicate charge time measurement
            volts.plot([cb,cb],[2,10],'r-')
            volts.plot([ce,ce],[2,10],'r-')

            p2, = current.plot(t,Ibat,"m-")
            p3, = charge.plot(t,chrg,"g-")
            p4, = power.plot(t,dut_powr,"c-")
            p5, = energy.plot(t,dut_enrg,"r-")



            volts.set_xlabel("time(sec)")
            volts.set_ylabel("Vbat(volts)")
            current.set_ylabel("Ibat(amps)")
            charge.set_ylabel("Battery Capacity Drawn(mA*hr)")
            power.set_ylabel("Power Delivered to DUT(watts)")
            energy.set_ylabel("Energy Delivered to DUT(Joules)")

            volts.yaxis.label.set_color(p1.get_color())
            current.yaxis.label.set_color(p2.get_color())
            charge.yaxis.label.set_color(p3.get_color())
            power.yaxis.label.set_color(p4.get_color())
            energy.yaxis.label.set_color(p5.get_color())



            tkw = dict(size=4, width=1.5)
            volts.tick_params(axis='y', colors=p1.get_color(), **tkw)
            volts.tick_params(axis='x', **tkw)
            current.tick_params(axis='y', colors=p2.get_color(), **tkw)
            charge.tick_params(axis='y', colors=p3.get_color(), **tkw)
            power.tick_params(axis='y', colors=p4.get_color(), **tkw)
            energy.tick_params(axis='y', colors=p5.get_color(), **tkw)

            plot.grid(True)

            fig_name = self.path + "\%02d_E1#%d "%(self.plot_number,self.dut_sn) + name + ".png"
            self.plot_number += 1
            plot.savefig(fig_name,dpi=200)
            #plot.show()
            plot.clf()

        except Exception as e:
            print "Exception in add_Ibat_Vbat_charging_plot(): " + repr(e)
            raise e

def power_cycle(supply):
    level = supply.read_voltage_limit()
    supply.set_voltage_limit(0)
    time.sleep(2)
    supply.set_voltage_limit(level)

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

def read_failed_fw_page(page_num,write_attempt_num,len):
    """read the firmware page from the flash chip to a file to see where
       the errors are
    """
    try:
        name = test_dir + "/failed_firmware_write,page%d_attempt%d.bin"%(page_num,write_attempt_num)
        _outfile = open(name,'w')
        print "reading page to file for diagnosis..."
        if page_num == 1:
            address = 0x10000
        else:
            address = 0x20000

        byte_index = 0
        byte_list = []

        while byte_index < len:
            byte_list.append(session.read_memory(address,256))
            byte_index += 256

        print "writing"
        byte_string = ""
        byte_string = byte_string.join(byte_list)
        _outfile.write(byte_string)
        _outfile.close()

    except Exception as e:
        print "Exception in read_failed_fw_page(): " + repr(e)

def write_firmware_blocks(address,data):
    """writes data to memory in 256 byte blocks
       address - The address in flash to write to, should be 0x10000 or 0x20000
       data - The string of bytes to write to flash
    """
    retry_num = 10
    byte_count = 0
    block_size = 256
    block_count = 0
    write_string = ""

    try:
        for byte in data:
            if byte_count<=block_size:
                write_string += byte
                byte_count += 1
            if byte_count == block_size:
                session.write_memory( (address + block_size*block_count),write_string,retry_num)
                byte_count = 0
                block_count += 1
                write_string = ""
                if block_count == 1:
                    session.write_memory(address,data[0],retry_num)
        if len(write_string) > 0:
            session.write_memory( (address + block_size*block_count),write_string,retry_num)
    except Exception as e:
        print "Exception writing firmware blocks: " + repr(e)
        raise e

def write_firmware_version_to_flash(fw_build_num, max_write_attempts=5):
    """
    """
    try:
        name = "IMAGE" + str(fw_build_num) + ".BIN"
        f_path = fw_dir + name

        bytes_list = []
        with open(f_path, 'rb') as f:
            byte = f.read(1)
            while byte:
                bytes_list.append(byte)
                byte = f.read(1)

        bytes_str = ''
        bytes_str = bytes_str.join(bytes_list)

        #write the flash pages
        addr = 0x10000
        for i in [2,1]:
            write_attempts = 1
            while (write_attempts <= max_write_attempts):
                print "erasing flash page %d..."%i
                session.erase_flash_sector(addr*i)
                print "erase completed. Writing firmware to page %d..."%i
                write_firmware_blocks(addr*i,bytes_str)
                print "write completed. Calculating page %d crc... "%i,
                res = session.calculate_block_32_bit_crc(addr*i)
                if res.crc_is_valid():
                    print "page %d crc passed.\n"%i
                    break
                else:
                    print "page %d crc is invalid"%i
                    read_failed_fw_page(i,write_attempts,len(bytes_str))
                    write_attempts += 1
                    if write_attempts <= max_write_attempts:
                        print "write attempt #%d for page %d"%(write_attempts,i)
                    else:
                        print "write failed after %d attempts"%max_write_attempts
                        if (i==1):  #failed on page 1 write, continue since reboot checks page 2 first
                            print "  ...test will continue with successful write to page 2 only"
                        else:
                            raise RuntimeError("Failed to update firmware sector %d in flash")%(i)
    except Exception as e:
        print "Exception found in write_firmware_version_to_flash() " + repr(e)
        raise e

def erase_flash_fw_pages():
    addr = 0x10000
    for i in [2,1]:
        print "\nerasing flash page %d..."%i
        session.erase_flash_sector(addr*i)
        print "erase completed."

def charge_MaxV(max_command_attempts=5):
    """commands the implant to perform a max energy charge without shock
    """

    try:
        ps = session.read_permanent_parameters()
        print "programmable parameters read from device..."
        print ps
        if ps.HVShockVoltage != MAX_SHOCK_VOLTAGE:
            ps.HVShockVoltage = MAX_SHOCK_VOLTAGE
            ps.update_crc()
            test_log.info("HVShockVoltage is not 225. Setting HVShockVoltage to 225")

        marker = None
        markerList = [chtelemetry.ChargeEndMarker]
        cmd_attempt = 1
        while cmd_attempt <= max_command_attempts:
            try:
                with session.wait_for_event_context(*markerList) as waiter:
                    session.hv_charge(ps, retry_num=4)
                    marker = waiter.wait(60*1000)
                return marker
            except TelemetryCommandError, err:
                print "#TelemetryCommandError#"
                test_log.error("Temetry command error " + str(err))
            except TimeoutError, err:
                print "#TimeoutError#"
                test_log.error("Timeout error " + str(err))
                return marker
            cmd_attempt += 1
        raise RuntimeError("HV charge max retries failed")

    except Exception as e:
        print "Exception in charge_MaxV(): " + repr(e)
        raise e

def charge_and_shock_MaxV(max_command_attempts=5):
    """commands the implant to perform a max energy charge and shock sequence
    """

    try:
        ps = session.read_permanent_parameters()
        print "programmable parameters read from device..."
        print ps
        if ps.HVShockVoltage != MAX_SHOCK_VOLTAGE:
            ps.HVShockVoltage = MAX_SHOCK_VOLTAGE
            ps.update_crc()
            test_log.info("HVShockVoltage is not 225. Setting HVShockVoltage to 225")

        marker = None
        markerList = [chtelemetry.ShockMarker]
        cmd_attempt = 1
        while cmd_attempt <= max_command_attempts:
            try:
                with session.wait_for_event_context(*markerList) as waiter:
                    print "Sending max voltage charge/shock command.."
                    session.hv_charge_and_shock(ps)
                    marker = waiter.wait(60*1000)
                return marker
            except TelemetryCommandError:
                print "#error# TelemetryCommandError"
                test_log.error("Temetry command error " + str(err))
            except TimeoutError:
                print "#error# TimeoutError"
                test_log.error("Timeout error " + str(err))
                return marker
            cmd_attempt += 1
        raise RuntimeError("HV charge and shock max retries failed")

    except Exception as e:
        print "Exception in charge_and_shock_MaxV(): " + repr(e)
        raise e

def measure_leadZ(max_command_attempts=5):
    """commands the implant to perform a lead impedance measurement
    """

    try:
        marker = None
        markerList = [chtelemetry.LeadImpedanceMarker]
        cmd_attempt = 1
        while cmd_attempt <= max_command_attempts:
            try:
                with session.wait_for_event_context(*markerList) as waiter:
                    session.measure_lead_impedance()
                    marker = waiter.wait(60*1000)
                return marker
            except TelemetryCommandError, err:
                test_log.error("Temetry command error " + str(err))
            except TimeoutError, err:
                test_log.error("Timeout error " + str(err))
                return marker
            cmd_attempt += 1
        raise RuntimeError("measure lead impedance max retries failed")

    except Exception as e:
        print "Exception in measure_leadZ(): " + repr(e)
        raise e

def scan_for_devices(pri_scan_int,sec_scan_int=2,_max_scan_attempts=5):
    """Will scan for device ids _max_scan_attempts times before returning 'fail'
       only fails on no devices found after max_scan_attempts tries

       returns:
            ids -        a list of ids (long int) found during the scan
            serials -    a list of the serial numbers extracted from the list of ids found
    """
    try:
        if type(pri_scan_int) is not int:
            raise RuntimeError("primary scan interval parameter must be an integer")
        if type(sec_scan_int) is not int:
            raise RuntimeError("secondary scan interval parameter must be an integer")

        serials = []
        attempt_num = 1
        while True:
            test_log.info("scanning for devices... %s attempt"%(ordinal_text[attempt_num]))
            print "scanning for devices... %s attempt"%(ordinal_text[attempt_num])
            ids = radio.scan(pri_scan_int,sec_scan_int)
            if not ids:
                print "no devices found"
                test_log.error("no devices found")
                if attempt_num == _max_scan_attempts:
                    return 'fail'
            else:
                for i in range(0,len(ids)):
                    serial = ids[i]&0x3FFFF
                    serials.append(serial)
                    print"  device#%d:  id:0x%.8x  s/n:%d"%(i+1,ids[i],serial)
                return ids,serials
            attempt_num+=1
    except Exception as e:
        print "Exception found in scan_for_devices(): " + repr(e)
        raise e


def link_to_device(_id,_max_link_attempts=3):
    """link to a specific device id specified in the _id parameter
        returns a 'link fail' error if unable to establish a link to the correct id

    Parameters: _id - the target id to establish a link to
                _max_link_attempts - maximum number of times the link will be attempted
    Returns:    the telemetry session if linked, 'link fail' on failure
    """
    try:
        attempt_num = 1
        while True:
            test_log.info("linking to %#0x..%s attempt"%(_id,ordinal_text[attempt_num]))
            print "linking to %#0x..%s attempt"%(_id,ordinal_text[attempt_num])
            session = radio.link(_id,fw_dir)
            if (not session):
                test_log.error("link attempt failed")
                if attempt_num == _max_link_attempts:
                    return 'link fail'
                else:
                    attempt_num+=1
            else:
                return session
    except Exception as e:
        print "Exception found in link_to_device(): " + repr(e)
        raise e

def scan_and_link(target_sn,prim_scan_interval,max_scans=5,max_links=5):
    try:
        num_scans = 0
        while (num_scans < max_scans):
            ids,serials = scan_for_devices(prim_scan_interval)
            if target_sn in serials:
                selection = serials.index(target_sn)
                break
            else:
                num_scans += 1

        if num_scans == 5:
            test_report.write("Unable to find device %d in %d scans\n"%(target_sn,max_scans))
            raise RuntimeError("Unable for find device %d in %d scans\n"%(target_sn,max_scans))

        id = ids[selection]
        global session
        session = link_to_device(id,max_links)
        if session == 'link fail':
            raise RuntimeError("Telemetry link unsuccessful")
        try:
            device_sn = serials[selection]

            if (id == 0xFFFFFFFF) | (id == 0xFFFFFFFE):
                print "running in bootloader\n"
            else:
                print "device is running firmware."
                fw_build_number = session.read_firmware_build_number()
                print "firmware build number %d detected"%fw_build_number
            session.set_firmware_symbols_dir(fw_dir)
            return (session,id,device_sn)
        except Exception as e:
            print "Exception in scan_and_link(): " + repr(e)
            raise e
    except Exception as e:
        print "Exception found in scan_and_link(): " + repr(e)
        raise e




def begin_Ibat_Vbat_measurement():
    try:
        global results_queue
        results_queue = Queue()
        global Ibat_Vbat_samples_per_sec
        Ibat_Vbat_samples_per_sec = 10000.0
        event_time_seconds = 1.0
        fillmode = 'scan'

        global Ibat_Vbat_meas_thread
        Ibat_Vbat_meas_thread = pyNIDAQ.Analog_Input_Thread_Continuous(results_queue,
                                                                     NI_device,
                                                                     Ibat_Vbat_samples_per_sec,
                                                                     event_time_seconds,
                                                                     fillmode,
                                                                     meas_type='DIFF')
        Ibat_Vbat_meas_thread.Add_Analog_Voltage_Channel("ai0",-10.0,10.0)  #Ibat
        Ibat_Vbat_meas_thread.Add_Analog_Voltage_Channel("ai1",-10.0,10.0)  #Vbat

        Ibat_Vbat_meas_thread.start()

    except Exception as e:
        print "Exception in begin_Ibat_Vbat_measurement(): " + repr(e)
        raise e

def handle_Ibat_Vbat_measurements(dut_sn,batt_cond,chrg_num):
    try:
        debug = True

        if debug: print "ending measurement"
        Ibat_Vbat_meas_thread.End_Measurement()
        if debug: print "getting results from queue"
        data = results_queue.get()

        #convert the measured Ibat voltage to current
        if debug: print "converting data"
        Ibat = -data[0]
        Vbat = data[1]
        if debug: print "Ibat samples: %d, Vbat samples: %d"%(len(Ibat),len(Vbat))

        if debug: print "sending Ibat,Vbat measurements to csv"
        name = "%s charge#%d Ibat"%(batt_cond,chrg_num)
        array_to_csv(test_data,Ibat,name,Ibat_Vbat_samples_per_sec,"time(sec)","current(Amps)",make_plot=False)
        name = "%s charge#%d Vbat"%(batt_cond,chrg_num)
        array_to_csv(test_data,Vbat,name,Ibat_Vbat_samples_per_sec,"time(sec)","Vbat(Volts)",make_plot=False)

        if debug: print "performing calculations on data"
        (begin_samp,end_samp,chrg_time) = find_charge_window(Ibat,Ibat_Vbat_samples_per_sec)
        (chrg,DUT_powr,DUT_enrg) = calculate_HV_charge_params(Ibat,Vbat,Ibat_Vbat_samples_per_sec,
                                                              begin_samp,end_samp)

        if debug: print "sending calculated charge,power,energy to csv"
        name = "%s charge#%d (charge)"%(batt_cond,chrg_num)
        array_to_csv(test_data,chrg,name,Ibat_Vbat_samples_per_sec,"time(sec)","charge(mA hr)",make_plot=False)
        name = "%s charge#%d power delivered to DUT"%(batt_cond,chrg_num)
        array_to_csv(test_data,DUT_powr,name,Ibat_Vbat_samples_per_sec,"time(sec)","Vbat(Volts)",make_plot=False)
        name = "%s charge#%d energy"%(batt_cond,chrg_num)
        array_to_csv(test_data,DUT_enrg,name,Ibat_Vbat_samples_per_sec,"time(sec)","Vbat(Volts)",make_plot=False)
        test_data.flush()

        test_report.write("Charge number %d:\n"%(chrg_num) + \
        "   charge time: %.2f sec, batt capacity used: %.2f mA*hr, energy delivered to DUT: %.2f Joules\n" \
        %(chrg_time,numpy.max(chrg),numpy.max(DUT_enrg)))
        test_report.flush()

        print "Charge number %d:"%(chrg_num)
        print "**********************************************************************************************"
        print "charge time: %.2f sec, batt capacity used: %.2f mA*hr, energy delivered to DUT: %.2f Joules" \
        %(chrg_time,numpy.max(chrg),numpy.max(DUT_enrg))
        print "**********************************************************************************************"


        if debug: print "plotting results"
        graphs.add_Ibat_Vbat_charging_plot(Vbat,Ibat,chrg,DUT_powr,DUT_enrg,
                                           "E1#%d %s charge time - %.2f sec, batt capacity used - %.2f mA-hr" \
                                           %(dut_sn,batt_cond,chrg_time,numpy.max(chrg)),
                                           Ibat_Vbat_samples_per_sec,begin_samp,end_samp)
        if debug: print "done handling Ibat and Vbat measurements"

    except Exception as e:
        print "Exception found in handle_Ibat_Vbat_measurements(): " + repr(e)
        raise e


def calculate_HV_charge_params(Ibat,Vbat,samp_per_sec,begin_samp,end_samp):
    try:
        dt = 1.0/samp_per_sec
        q_from_batt = numpy.zeros(len(Ibat),dtype=float)
        dutP = numpy.zeros(len(Ibat),dtype=float)
        dutE = numpy.zeros(len(Ibat),dtype=float)
        Qsum = 0.0
        Esum_dut = 0.0

        for i in range(len(Ibat)):

            if (i>=begin_samp):

                #charge calculation (integration)
                Qsum += Ibat[i]*1000*dt/3600 #find charge in mA*hr
                q_from_batt[i] = Qsum

                #power to DUT
                dutP[i] = Ibat[i] * Vbat[i]

                #energy to DUT
                Esum_dut += dutP[i]*dt
                dutE[i] = Esum_dut

        return (q_from_batt,dutP,dutE)

    except Exception as e:
        print "Exception found in calculate_batt_charge_power_energy(): " + repr(e)
        raise e

def find_charge_window(a,samp_per_sec):
    """will find the window of samples where the charge was taking place
       and return the begin and end sample numbers and charge time in a tuple
    """
    try:
        trig_level = 0.05
        begin_found = False
        end_sample = None

        num_half_sec_samples = samp_per_sec / 0.5
        num_low_samples = 0

        for i in range(len(a)):

            #find the rising edge of current waveform
            if begin_found == False and a[i] > trig_level:
                begin_sample = i
                begin_found = True

            #after beginning of current waveform has been found
            if begin_found == True:

                if a[i] < trig_level*5:

                    #check for low going edge
                    if end_sample is None:
                        end_sample = i

                    num_low_samples += 1

                    #check if has been low for half second
                    if num_low_samples >= num_half_sec_samples:
                        break

                #sample found was not below trigger level
                else:
                    end_sample = None
                    num_low_sample = 0

        charge_time = (end_sample - begin_sample) / samp_per_sec


        return (begin_sample,end_sample,charge_time)
    except Exception as e:
        print "Exception found in find_charge_window(): " + repr(e)
        raise e

def end_AO_pulse(AO_voltage):
    AO_voltage.end()

def create_AO_pulse(pulse_sec):
    try:
        Vout_channel = pyNIDAQ.Analog_Output_Level(NI_device+"/ao0")
        arg = [Vout_channel]

        #create a timer to turn off the voltage pulse
        AO_pulse_timer = threading.Timer(pulse_sec,end_AO_pulse,arg)
        return (Vout_channel,AO_pulse_timer)

    except Exception as e:
        print "Exception in start_AO_pulse(): " + repr(e)
        raise e

def main(dut_sn,battery_condition):
    try:

        print "\n\n\n*************************************************"
        print "Beginning Program ..."
        start_time = time.clock()



        #****************************************************************
        #*********directory and file setup*******************************
        global now_text
        now_text = time.strftime("%Y_%m_%d - %H_%M_%S")
        dir_name = "Test Results E1#%d - %s"%(dut_sn,now_text)
        cwd = os.getcwd()

        global test_dir
        test_dir = cwd + "/" + dir_name
        os.mkdir(test_dir)

        global fw_dir
        fw_dir = cwd + "/firmware_builds/"

        plot_dir = (cwd + "/" + dir_name + "/test_plots")
        os.mkdir(plot_dir)
        global graphs
        graphs = data_plots(plot_dir,dut_sn)

        global test_report
        test_report = open(test_dir + "/Test_Report_E1#%d "%dut_sn + now_text + ".txt",'w')
        test_report.write("Test report for E1# %d: "%(dut_sn))
        test_report.write(": %s\n\n"%(now_text))

        global test_data
        test_data = open(test_dir + "/Test_Data_E1#%d "%dut_sn + now_text + ".csv",'w')
        test_data.write("Test Name,samples per second,x-axis units,y-axis units,data\n")
        #*********************************************************************




        #****************************************************************
        #*********logging setup******************************************
        log_date_format = "%Y/%m/%d %H:%M:%S"
        log_entry_format = "%(asctime)s.%(msecs)03d %(name)-16s %(levelname)-5s: %(message)s"
        log_filename = test_dir + "/test.log"
        logging.basicConfig(level=logging.DEBUG,
                format = log_entry_format,
                datefmt = log_date_format,
                filename = log_filename)
        global test_log
        test_log = logging.getLogger("test")
        #*****************************************************************






        #*****************************************************************
        #********program variables****************************************
        global ordinal_text
        ordinal_text = ['0','first','second','third','fourth','fifth',
                        'sixth','seventh','eighth','ninth','tenth']
        global ps_voltage
        first_charge = True

        # Read configuration
        config = ConfigParser()
        config.read( os.getcwd() + "/HVcharge_q_settings.cfg" )

        source_type = config.get('power_source', 'source_type')
        BOL_voltage = float(config.get('Simulated_Battery_Conditions', 'BOL_voltage'))
        MOL_voltage = float(config.get('Simulated_Battery_Conditions', 'MOL_voltage'))
        ERI_voltage = float(config.get('Simulated_Battery_Conditions', 'ERI_voltage'))
        EOL_voltage = float(config.get('Simulated_Battery_Conditions', 'EOL_voltage'))

        BOL_esr = float(config.get('Simulated_Battery_Conditions', 'BOL_esr'))
        MOL_esr = float(config.get('Simulated_Battery_Conditions', 'MOL_esr'))
        ERI_esr = float(config.get('Simulated_Battery_Conditions', 'ERI_esr'))
        EOL_esr = float(config.get('Simulated_Battery_Conditions', 'EOL_esr'))

        fixture_Imeas_offset = float(config.get('measurements', 'fixture_Imeas_offset'))
        fixture_Vbat_offset = float(config.get('measurements', 'fixture_Vbat_offset'))

        HV_loopcount = int(config.get('test_control', 'HV_loopcount'))
        HV_loop_wait_sec = float(config.get('test_control', 'HV_loop_wait_sec'))
        HV_control = int(config.get('test_control', 'HV_control'))
        if HV_control:
            test_type = 'charge/shock(s)'
        else:
            test_type = 'charge(s)'

        global NI_device
        NI_device = config.get('hardware', 'device')
        #*****************************************************************




        #*****************************************************************
        #******instrument setup*******************************************
        if source_type == 'bench_supply':
            global ps
            ps=Instruments.PowerSupply_E3632A("GPIB::7","power_supply")

        #initialize voltage output channel to 0V
        Vout_channel = pyNIDAQ.Analog_Output_Level(NI_device+"/ao0")
        Vout_channel.end()
        #************************************************************************




        #*****************************************************************
        #********instrument control***************************************
        if source_type == 'bench_supply':
            print "controlling power supply"
            if battery_condition == 'BOL':
                ps_voltage = BOL_voltage
                ps_esr = BOL_esr
            elif battery_condition == 'MOL':
                ps_voltage = MOL_voltage
                ps_esr = MOL_esr
            elif battery_condition == 'ERI':
                ps_voltage = ERI_voltage
                ps_esr = ERI_esr
            elif battery_condition == 'EOL':
                ps_voltage = EOL_voltage
                ps_esr = EOL_esr
            else:
                test_report.write('Unknown cmd line argument for simulated battery condition')
                raise RuntimeError('Unknown cmd line argument for simulated battery condition')
            ps.set_voltage_limit(ps_voltage)

            print " supply voltage set to %.1fV"%ps.read_voltage_limit()
            ps.set_current_limit(5.0)
            ps.output_on()
            print " output turned on"

            test_report.write("Using power supply with simulated %s battery conditions"%(battery_condition))
            test_report.write(" of %.1f Volts, %.2f ohms esr.\n"%(ps_voltage,ps_esr))

        elif (source_type == 'battery'):
            if battery_condition is None:
                battery_condition = 'BAT'
            elif battery_condition != 'BAT':
                test_report.write('Unknown cmd line argument for simulated battery condition')
                raise RuntimeError('Unknown cmd line argument for simulated battery condition')
            elif battery_condition == ('BAT'):
                test_report.write("Using a battery to power DUT during tests.\n")
        #*****************************************************************

        print "Configuration: %d second delay between %d "%(HV_loop_wait_sec,HV_loopcount),
        test_report.write("%d second delay between %d "%(HV_loop_wait_sec,HV_loopcount))
        if HV_control:
            print "HV charge/shock commands.\n"
            test_report.write("HV charge/shock commands.\n\n")
        else:
            print "HV charge commands.\n"
            test_report.write("HV charge commands.\n\n")
        test_report.flush()



        #change location of current working directory before telemetry log creation
        #this allows control of where the CommunicationSystem.log file is stored
        os.chdir(test_dir)

        global radio,session,id,sn
        with closing(chtelemetry.Radio()) as radio:

            #reset location of current working directory after telemetry log creation
            os.chdir(cwd)
            session,id,sn = scan_and_link(dut_sn,9)

            for i in range(HV_loopcount):

                if first_charge:
                    print "\nRunning lead-Z measurement before first charge..."
                    measure_leadZ()
                    print "...lead Z done"
                    first_charge = False

                print "\nStarting Ibat and Vbat measurement..."
                begin_Ibat_Vbat_measurement()
                meas_strt = time.clock()
                time.sleep(1.0)

                pulse_time_sec = 8.0
                (Vout_channel,AO_pulse_timer) = create_AO_pulse(pulse_time_sec)
                Vout_channel.update(3.5)
                AO_pulse_timer.start()

                if HV_control:
                    print "\nRunning max voltage charge/shock..."
                    shock_cmd_time = time.clock()
                    charge_and_shock_MaxV()
                    print "HV shock completed"
                else:
                    print "\nRunning max voltage charge..."
                    shock_cmd_time = time.clock()
                    charge_MaxV()
                    print "HV charge completed"

                time.sleep(1)
                print "\nHandling Ibat and Vbat measurements..."
                handle_Ibat_Vbat_measurements(dut_sn,battery_condition,i+1)
                print "completed %d of %d high voltage charging events"%(i+1,HV_loopcount)

                print "\nRunning lead-Z measurement to dump caps..."
                measure_leadZ()
                print "...lead Z done"

                if i < HV_loopcount-1:

                    print "\nWaiting for %d second interval to perform HV charge #%d... "%(HV_loop_wait_sec,i+2),
                    count.seconds_from_start(shock_cmd_time,HV_loop_wait_sec)

            print "breaking telemetry link...",
            session.break_link()
            print "done"

            print "\nFinished with %d HV charge events"%(HV_loopcount)
            test_report.write("\nFinished with %d HV charge events\n"%(HV_loopcount))




    except Exception as e:
        print "Exception in main(): " + repr(e)
        test_report.write("\nException occurred: " + repr(e) + "\n")
        test_report.write("Test script terminated prematurely..\n\n")


    finally:
        print "\nCleanup..."

        et = time.clock() - start_time
        print "total elapsed test time: %.2d:%06.3f"%(et/60,et%60.0)
        test_report.write("total elapsed test time: %.2d:%06.3f\n"%(et/60,et%60.0))

        print "transposing csv file data to columns...",
        test_data.close()
        csv_ops.transpose_csv(test_data)
        print "done"

        if source_type == 'bench_supply':
            print "powering down supply...",
            ps.set_voltage_limit(0)
            time.sleep(1)
            ps.output_off()
            print "supply output turned off"

        print "...finished. Have a nice day."


if __name__ == '__main__':

    if (len(sys.argv) == 1):
        main(None)

    elif (len(sys.argv) == 2):
        main(int(sys.argv[1]),None)

    elif (len(sys.argv) == 3):
        main(int(sys.argv[1]),sys.argv[2])

    elif (len(sys.argv) < 2) or (len(sys.argv) > 3):
        sys.stderr.write("Usage: python %s DUT_serial_num [BOL,MOL,ERI,EOL, or BAT]\n"%sys.argv[0])
        raise SystemExit(1)