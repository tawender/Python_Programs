from contextlib import closing
import sys
import time
import visa
import threading
import logging
import os.path
import chtelemetry
import math
import numpy
import tkMessageBox
import ecg_data_to_file as ecg
import scipy.fftpack
import FFTonECG
import binascii

def write_byte_to_implant_and_verify(_session,_address,_data):
    """writes data to the implant address specified, then reads the address to verify
       data was written correctly

        _session:   telemetry session
        _address_:  address to write the byte to, can be a key or address value
        _data:      the data to be written, type is an integer from 0 to 255

        returns:    1 if the data was written and verified correctly
                    'fail' if an error occurred
    """

    #turn the number "_data" into a string in the form '\x07'    
    _session.write_memory(_address,bytes(chr(_data)))
    _session.read_uint8(_address)
    if session.read_uint8(_address) == _data:
        return 1
    else:
        results_outfile.write("error writing %#x to address %#x, readback verification failed\n"%(_data,_address))
        return 'fail'


def calculate_CMRR_results(_array,_sense_vector):
    """calculates the CMRR and outputs results
       expects array of magnitude values in the correct order
    """
    
    print "Results for input vector %s:"%_sense_vector
    print"16.6Hz input, 50Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f"%(_array[0],_array[6],20*math.log10( (_array[0]/cm_sig_level)/(_array[6]/dm_sig_level)))
    print"16.6Hz input, 60Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f"%(_array[1],_array[7],20*math.log10( (_array[1]/cm_sig_level)/(_array[7]/dm_sig_level)))
    print"50Hz input, 50Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f"%(_array[2],_array[8],20*math.log10( (_array[2]/cm_sig_level)/(_array[8]/dm_sig_level)))
    print"50Hz input, 60Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f"%(_array[3],_array[9],20*math.log10( (_array[3]/cm_sig_level)/(_array[9]/dm_sig_level)))
    print"60Hz input, 50Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f"%(_array[4],_array[10],20*math.log10( (_array[4]/cm_sig_level)/(_array[10]/dm_sig_level)))
    print"60Hz input, 60Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f"%(_array[5],_array[11],20*math.log10( (_array[5]/cm_sig_level)/(_array[11]/dm_sig_level)))
    print""

    results_outfile.write("Results for input vector %s:\n"%_sense_vector)
    results_outfile.write("16.6Hz input, 50Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f\n"%(_array[0],_array[6],20*math.log10( (_array[0]/cm_sig_level)/(_array[6]/dm_sig_level))))
    results_outfile.write("16.6Hz input, 60Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f\n"%(_array[1],_array[7],20*math.log10( (_array[1]/cm_sig_level)/(_array[7]/dm_sig_level))))
    results_outfile.write("50Hz input, 50Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f\n"%(_array[2],_array[8],20*math.log10( (_array[2]/cm_sig_level)/(_array[8]/dm_sig_level))))
    results_outfile.write("50Hz input, 60Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f\n"%(_array[3],_array[9],20*math.log10( (_array[3]/cm_sig_level)/(_array[9]/dm_sig_level))))
    results_outfile.write("60Hz input, 50Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f\n"%(_array[4],_array[10],20*math.log10( (_array[4]/cm_sig_level)/(_array[10]/dm_sig_level))))
    results_outfile.write("60Hz input, 60Hz notch: CM magnitude is %.2f, DM magnitude is %.2f, CMRR is %.2f\n\n"%(_array[5],_array[11],20*math.log10( (_array[5]/cm_sig_level)/(_array[11]/dm_sig_level))))
    results_outfile.flush()

def scan_for_devices(_max_scan_attempts = 5):
    """Will scan for device ids _max_scan_attempts times before returning 'fail'
       only fails on no devices found after max_scan_attempts tries

       returns:
                   ids -        a list of ids found in the scan
                   serials -    a list of the serial numbers extracted from the list of ids found
    """
    serials = []
    attempt_num = 1
    while True:
        test_log.info("scanning for devices...%s attempt"%(ordinal_text[attempt_num]))
        ids = radio.scan(9, 2)
        if not ids:
            test_log.error("no devices found")
            if attempt_num == _max_scan_attempts:
                return 'fail'
        else:
            for i in range(0,len(ids)):
                serial = "%x"%(ids[i])
                serial = "0x" + serial[5:]
                serials.append(int(serial,0))
                print"  device#%d:  id:%x  s/n:%d"%(i,ids[i],int(serial,0))
            return ids,serials
        attempt_num+=1

def link_to_device(_id,_max_link_attempts):
    """link to a specific device id specified in the _id parameter
        returns a 'link fail' error if unable to establish a link to the correct id

    Parameters: _id - the target id to establish a link to
                _max_link_attempts - maximum number of times the link will be attempted
    Returns:    the telemetry session if linked, 'link fail' on failure
    """
    attempt_num = 1
    while True:
        test_log.info("linking to %#0x..%s attempt"%(_id,ordinal_text[attempt_num]))
        _session = radio.link(_id)
        if (not _session):
            test_log.error("link attempt failed")
            if attempt_num == _max_link_attempts:
                return 'link fail'
            else:
                attempt_num+=1
        else:
            return _session

try:
    print"\nRunning CMRR program..."
    log_date_format = "%Y/%m/%d %H:%M:%S"
    log_entry_format = "%(asctime)s.%(msecs)03d %(name)-16s %(levelname)-5s: %(message)s"
    logging.basicConfig(level=logging.DEBUG,
            format = log_entry_format,
            datefmt = log_date_format,
            filename = "test.log")
    #consoleHandler = logging.StreamHandler()
    #consoleHandler.setFormatter(logging.Formatter(log_entry_format, "%H:%M:%S"))
    #logging.getLogger().addHandler(consoleHandler)
    test_log = logging.getLogger("test")
    
    class TelemetryError(Exception):
        pass

    class GPIBError(Exception):
        pass

    sig_gen = visa.instrument("GPIB::19")

    sig_gen.write("OUTP OFF")
    sig_gen.write("*RST")
    sig_gen.write("OUTP:LOAD INF")
    sig_gen.write("FREQ 16.6")
    sig_gen.write("VOLT:UNIT VPP")
     
    #function generator output signal levels
    cm_sig_level = .200
    dm_sig_level = .002

    num_samples = 256 * 3

    ordinal_text = ['0','first','second','third','fourth','fifth',
                    'sixth','seventh','eighth','ninth','tenth']
    
    vectors = ['HVB_SA','HVB_SB','SB_SA']
    gain_modes = ['common_mode','diff_mode']
    freqs = ['16.6Hz','50Hz','60Hz']
    notch_settings = ['50Hz','60Hz']

    with closing(chtelemetry.Radio()) as radio:
        ids,serials = scan_for_devices(1)
        if ids == 'fail':
            test_log.info("Failed to find any devices.. exiting")
            raise RuntimeError("Telemetry scan unsuccessful")
        selection = input("Select the device # to link to...")
        session = link_to_device(ids[selection],2)
        device_sn = serials[selection]
        if session == 'link fail':
            raise RuntimeError("Telemetry link unsuccessful")
        try:
            now_text = time.strftime("%Y_%m_%d-%H_%M_%S")
            cwd = os.getcwd()
            print cwd
            dir_name = "SN_%04d  %s"%(device_sn,now_text)
            print dir_name
            os.mkdir(cwd + "/" + dir_name)
            os.chdir(cwd + "/" + dir_name)
            print "made directory"
            cwd = os.getcwd()
            print cwd
            results_outfile = open("Device#%04d %s CMRR testing results.txt"%(device_sn,now_text), 'w')

            #set the ecg gain select bit to 2x
            write_byte_to_implant_and_verify(session,0xF1CB,0x80)
   
            for vector in vectors:
                magnitudes_array = numpy.zeros(12,dtype=numpy.float)
                magnitudes_array_index = 0
                
                if vector == 'HVB_SA':
                    write_byte_to_implant_and_verify(session,0xF1C0,6)
                elif vector == 'HVB_SB':
                    write_byte_to_implant_and_verify(session,0xF1C0,7)
                else:
                    write_byte_to_implant_and_verify(session,0xF1C0,11)

                for gain_mode in gain_modes:
                    
                    sig_gen_output_state = sig_gen.ask("OUTP?")
                    if sig_gen_output_state == '1':
                        sig_gen.write("OUTP OFF")
                    #prompt user to change input vector and gain mode connections, wait for ok
                    input_str = "Connect the DUT in %s using %s input vector,\nthen click 'OK' to continue test...\n"%(gain_mode,vector)
                    tkMessageBox.showinfo(message=input_str)
                    test_num = 1

                    #change function generator settings for gain mode used
                    if gain_mode == 'common_mode':
                        sig_gen.write("VOLT %s"%cm_sig_level)
                    else:
                        sig_gen.write("VOLT %s"%dm_sig_level)

                    for freq in freqs:

                        if freq == '16.6Hz':
                            sig_gen.write("FREQ 16.6")
                            input_freq = 16.6
                            num_samples = 740
                        elif freq == '50Hz':
                            sig_gen.write("FREQ 50")
                            input_freq = 50
                            num_samples = 256*3
                        else:
                            sig_gen.write("FREQ 60")
                            input_freq = 60
                            num_samples = 256*3

                        sig_gen_output_state = sig_gen.ask("OUTP?")
                        if sig_gen_output_state == '0':
                            sig_gen.write("OUTP ON")

                        for notch_setting in notch_settings:

                            name = "Device#%04d %s - %s %s input %s notch %s "%(device_sn,now_text,vector,freq,notch_setting,gain_mode)
                            ecg_data_file_name = name + "ecg_data.csv"
                            ecg_data_file = open(ecg_data_file_name,'w')

                            if notch_setting == '50Hz':
                                write_byte_to_implant_and_verify(session,0xF088,0x0B)
                            else:
                                write_byte_to_implant_and_verify(session,0xF088,0x09)
                                                                 
                            time.sleep(15)
                            ecg.start_recording(session,ecg_data_file,num_samples)
                            magnitudes_array[magnitudes_array_index] = FFTonECG.main(ecg_data_file_name,input_freq,name)
                            print "*****************************"
                            print "results for %s, %s, %s input, %s notch (test %d of 6)"%(vector,gain_mode,freq,notch_setting,test_num)
                            print "magnitude measured is: %.3f"%(magnitudes_array[magnitudes_array_index])
                            print "*****************************"
                            test_num += 1
                            magnitudes_array_index += 1

                calculate_CMRR_results(magnitudes_array,vector)

            sig_gen.write("OUTP OFF")
            tkMessageBox.showinfo()

        except Exception as e:
            print "error inside nested for loops: " + repr(e)
            results_outfile.write("error inside nested for loops: " + repr(e))
        finally:
            session.close()
except Exception as e:
    print e
    
finally:
    ecg_data_file.close()