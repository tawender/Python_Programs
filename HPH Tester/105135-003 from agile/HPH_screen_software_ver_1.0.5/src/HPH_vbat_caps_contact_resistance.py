import os
import time
from ConfigParser import ConfigParser
import optparse
import datetime
import threading
import logging
import msvcrt

cwd = os.getcwd()
import sys
Instruments_path = cwd + "/../lib"
sys.path.append(Instruments_path)
import Instruments

SW_PART_NUMBER = "105135-003"
SW_AGILE_REV = "A"
SW_VERSION = "1.0.5"
SW_RELEASE_TYPE = "Production"

class Keyboard_input_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self._terminate_thread = False
        self._thread_ended = False

    def kbfunc(self):
        return ord(msvcrt.getch()) if msvcrt.kbhit() else 0

    def run(self):
        #terminate when a 'q' is pressed or done flag is set
        while (self._terminate_thread is not True) and (self.kbfunc() != 113):
            time.sleep(0.1)

        self._thread_ended = True

    def terminate_thread(self):
        self._terminate_thread = True

    def thread_ended(self):
        return self._thread_ended



class spst_relay(object):
    def __init__(self,slot,channel,switch_system):
        self.slot = slot
        self.channel = channel
        self.switch_system = switch_system

    def close(self):
        self.switch_system.close(self.slot,self.channel)

    def open(self):
        self.switch_system.open(self.slot,self.channel)

class measurement_config(object):
    def __init__(self,switch_list,name):
        self.switch_list = switch_list
        self.name = name

    def config_switches(self):
        #close the desired switches
        for switch in self.switch_list:
            switch.close()

    def get_name(self):
        return self.name

class Vbat_caps_test(object):
    def __init__(self,verify_configurations=False,
                    pause=False,print_to_console=True,
                    debug=False,substrate=False):


        self.pause = pause
        self.resume = False
        self.print_to_console = print_to_console
        self.debug = debug
        self.use_substrate_pins = substrate


        self.cwd = os.getcwd()
        self.read_config_file()
        self.config_logging()
        self.init_instruments()
        self.define_switch_configurations()
        self.setup_sourcemeter()
        self.voltage_measurement_offset = 0
        self.current_measurement_offset = 0

        if verify_configurations:
            self.verify_switch_configurations()



    def read_config_file(self):
        """   """
        try:
            self.software_version = SW_VERSION
            self.software_pn = SW_PART_NUMBER
            self.software_agile_rev = SW_AGILE_REV
            self.software_release_type = SW_RELEASE_TYPE

            self.config_file_name = "settings.cfg"
            self.c_file = open(self.config_file_name, 'r')
            self.config_file = ConfigParser()
            self.config_file.readfp(self.c_file)

            self.sm_gpib_addr = int(self.config_file.get('instruments','sm_gpib'))
            self.sm_model = self.config_file.get('instruments','sm_model')
            self.sw_gpib_addr = int(self.config_file.get('instruments','sw_gpib'))
            self.sw_model = self.config_file.get('instruments','sw_model')
            self.mux_card_slot = int(self.config_file.get('instruments','mux_card_slot'))

            self.test_current = float(self.config_file.get('test conditions','test current'))
            self.compliance_voltage = float(self.config_file.get('test conditions','compliance voltage'))
            self.settle_sec = float(self.config_file.get('test conditions','settle seconds before measurement'))
            self.NPLC = float(self.config_file.get('test conditions','measurement speed NPLC'))

            #test operator
            self.operator_name = self.config_file.get('test info','operator')

            #test system part number and instance
            self.test_system_pn = self.config_file.get('test info','test system instance')

            #information
            self.reference_entry = self.config_file.get('test info','reference entry')

            #individual DUT test report generation
            self.create_DUT_report = self.config_file.getboolean('execution control','create DUT report')
            self.DUT_pn = self.config_file.get('DUT info','DUT part number')
            self.DUT_rev = self.config_file.get('DUT info','DUT revision')
            self.DUT_ln = self.config_file.get('DUT info','DUT lot number')
            self.test_reason = self.config_file.get('test info','test reason')
            self.test_location = self.config_file.get('test info','test location')

            #test loop control
            self.looptesting = self.config_file.getboolean('execution control','looptesting')
            self.num_testloops = int(self.config_file.get('execution control','num testloops'))
            self.loop_interval_sec = float(self.config_file.get('execution control','loop interval seconds'))

            #test execution
            self.run_sense_pogo_contact_check = self.config_file.get('execution control','run sense pogo contact check')
            self.sense_pogo_contact_resistance_ohms_high_limit = self.config_file.getfloat('execution control','sense pogo resistance ohms high limit')
            self.sense_pogo_contact_resistance_ohms_low_limit = self.config_file.getfloat('execution control','sense pogo resistance ohms low limit')
            self.sense_pogo_test_current = self.config_file.getfloat('execution control','sense pogo test current')
            self.sense_pogo_compliance_voltage = self.config_file.getfloat('execution control','sense pogo compliance voltage')
            self.use_criteria_parallel_R = self.config_file.getboolean('execution control','use criteria parallel R')
            self.use_criteria_bad_caps = self.config_file.getboolean('execution control','use criteria bad caps')
            self.use_criteria_absolute_R = self.config_file.getboolean('execution control','use criteria absolute R')
            self.validate_resistance_results = self.config_file.getboolean('execution control','validate resistance results')
            self.valid_resistance_limit = float(self.config_file.get('execution control','valid resistance limit ohms'))

            #test criteria
            self.absolute_resistance_limit = self.config_file.getfloat('test criteria','absolute resistance limit')
            self.cap_ESR = self.config_file.getfloat('test criteria','cap ESR')
            self.max_Rp = self.config_file.getfloat('test criteria','max parallel resistance')
            self.compromised_cap_Rthreshold = self.config_file.getfloat('test criteria','compromised cap Rthreshold')
            self.max_compromised_caps = self.config_file.getfloat('test criteria','max compromised caps')

            #if using a GUI, should the user be able to make changes to the test configurations
            self.allow_config_changes = self.config_file.getboolean('GUI access','allow parameter changes')

            #leakage testing parameters
            self.run_leakage_test = self.config_file.getboolean('leakage testing','run leakage test')
            self.leakage_test_voltage = self.config_file.getfloat('leakage testing','test voltage')
            self.leakage_conditioning_voltage = self.config_file.getfloat('leakage testing','conditioning voltage')
            self.leakage_compliance_current = self.config_file.getfloat('leakage testing','compliance current')
            self.leakage_conditioning_sec = self.config_file.getfloat('leakage testing','conditioning hold seconds')
            self.num_leakage_measurements = self.config_file.getint('leakage testing','num leakage measurements')
            self.leakage_measurement_range = self.config_file.get('leakage testing','leakage measurement range')
            self.max_leakage_limit = self.config_file.getfloat('leakage testing','max leakage limit')
            self.leakage_ramp_up_seconds = self.config_file.getfloat('leakage testing','ramp up seconds')
            self.leakage_ramp_up_voltage_step = self.config_file.getfloat('leakage testing','ramp up voltage step')
            self.leakage_ramp_down_seconds = self.config_file.getfloat('leakage testing','ramp down seconds')
            self.leakage_ramp_down_voltage_step = self.config_file.getfloat('leakage testing','ramp down voltage step')

            #test results logging
            self.record_results = self.config_file.getboolean('output','record all results to csv')
            self.results_file_error = False
            self.logfilename = self.config_file.get('output','filename')

            #close configuration file
            self.c_file.close()

            #open results file
            try:
                self.results_file = open(self.logfilename,'a')
            except IOError as e:
                if __name__ is not '__main__':
                    self.results_file = None
                    self.results_file_error = True
                else:
                    raise e

        except Exception as e:
            print "Exception in read_config_file(): " + repr(e)
            raise e

    def config_logging(self):
        try:
            if not os.path.exists(cwd + "/../logs"):
                os.mkdir(cwd + "/../logs")
            log_dir = cwd + "/../logs"

            t = datetime.datetime.now()
            logdate = t.strftime("%Y-%m-%d %H_%M_%S.%f")[:19]
            self.log_name = "HPHscreen %s.log"%(logdate)
            log_date_format = "%Y/%m/%d %H:%M:%S"
            log_entry_format = "%(asctime)s.%(msecs)03d %(name)-16s %(levelname)-5s: %(message)s"
            logging.basicConfig(level=logging.DEBUG,
                    format = log_entry_format,
                    datefmt = log_date_format,
                    filename = log_dir + "/" + self.log_name)
            self.test_log = logging.getLogger(self.log_name)

            self.test_log.info("*******************************************************************")
            self.test_log.info("Running HPH screen software %s Rev.%s",SW_PART_NUMBER,SW_AGILE_REV)
            self.test_log.info("Version %s",SW_VERSION)
            self.test_log.info("Release type: %s",SW_RELEASE_TYPE)
            self.test_log.info("*******************************************************************")

        except Exception as e:
            print "Exception in config_logging(): " + repr(e)
            raise e

    def init_instruments(self):
        #initialize sourcemeter and verify model number
        try:
            self.sm = Instruments.sourcemeter_2400("GPIB::%d"%(self.sm_gpib_addr),"sourcemeter",
                                                    timeout=30,logname=self.log_name)
            sm_model = self.sm.get_ID().split(",")[1]
            if  sm_model != self.sm_model:
                raise RuntimeError("Incorrect sourcemeter model number... Got %s, expected %s"%(
                                        sm_model,self.sm_model))
        except Exception as e:
            print "Error initializing sourcemeter..." + repr(e)
            raise e

        try:
            #initialize switch system and verify model number
            self.sw = Instruments.switch_system_7001("GPIB::%d"%(self.sw_gpib_addr),"switch matrix",
                                                        logname=self.log_name)
            sw_model = self.sw.get_ID().split(",")[1]
            if  sw_model != self.sw_model:
                raise RuntimeError("Incorrect switch system model number... Got %s, expected %s"%(
                                        sw_model,self.sw_model))
        except Exception as e:
            print "Error initializing switch system..." + repr(e)
            raise e



    def define_switch_configurations(self):

        #************************************************************
        #side contact pogo pins
        #
        #for silver epoxy joint testing
        self.VBAT2_curr_neg = spst_relay(self.mux_card_slot,18,self.sw)
        self.VBAT3_meas_neg = spst_relay(self.mux_card_slot,38,self.sw)
        self.VSS4_curr_neg = spst_relay(self.mux_card_slot,19,self.sw)
        self.VSS5_meas_neg = spst_relay(self.mux_card_slot,39,self.sw)
        #
        #for leakage testing(to apply V+ to pins 2,3 and V- to pins 4,5)
        self.VBAT2_curr_pos = spst_relay(self.mux_card_slot,8,self.sw)
        self.VBAT3_curr_pos = spst_relay(self.mux_card_slot,9,self.sw)
        self.VSS5_curr_neg = spst_relay(self.mux_card_slot,20,self.sw)
        #*************************************************************


        #measure CCHRG1 VBAT connection
        self.pogo1_curr_pos = spst_relay(self.mux_card_slot,1,self.sw)
        self.pogo2_meas_pos = spst_relay(self.mux_card_slot,21,self.sw)

        #measure CCHRG1 VSS connection
        self.pogo10_curr_pos = spst_relay(self.mux_card_slot,2,self.sw)
        self.pogo11_meas_pos = spst_relay(self.mux_card_slot,22,self.sw)

        #measure CCHRG2 VBAT connection
        self.pogo3_curr_pos = spst_relay(self.mux_card_slot,3,self.sw)
        self.pogo4_meas_pos = spst_relay(self.mux_card_slot,23,self.sw)

        #measure CCHRG2 VSS connection
        self.pogo12_curr_pos = spst_relay(self.mux_card_slot,4,self.sw)
        self.pogo13_meas_pos = spst_relay(self.mux_card_slot,24,self.sw)

        #measure CCHRG3 VBAT connection
        self.pogo5_curr_pos = spst_relay(self.mux_card_slot,5,self.sw)
        self.pogo6_meas_pos = spst_relay(self.mux_card_slot,25,self.sw)

        #measure CCHRG3 VSS connection
        self.pogo14_curr_pos = spst_relay(self.mux_card_slot,6,self.sw)
        self.pogo15_meas_pos = spst_relay(self.mux_card_slot,26,self.sw)

        #switch configuration used to find voltage measurement offset
        #  this will short the sense and output connections to find the
        #  sourcemeter measurement offset
        self.relay_offset_pos = spst_relay(self.mux_card_slot,27,self.sw)
        self.relay_offset_neg = spst_relay(self.mux_card_slot,37,self.sw)
        self.jumper_wire_A = spst_relay(self.mux_card_slot,7,self.sw)
        self.jumper_wire_B = spst_relay(self.mux_card_slot,17,self.sw)

        #relays for sense pin contact resistance checks
        self.pogo2_curr_neg = spst_relay(self.mux_card_slot,11,self.sw)
        self.pogo11_curr_neg = spst_relay(self.mux_card_slot,12,self.sw)
        self.pogo4_curr_neg = spst_relay(self.mux_card_slot,13,self.sw)
        self.pogo13_curr_neg = spst_relay(self.mux_card_slot,14,self.sw)
        self.pogo6_curr_neg = spst_relay(self.mux_card_slot,15,self.sw)
        self.pogo15_curr_neg = spst_relay(self.mux_card_slot,16,self.sw)
        self.VSS5_curr_pos = spst_relay(self.mux_card_slot,10,self.sw)


        if self.use_substrate_pins:

            #**********************************************************************
            # test configurations if using the original 18 pogo pins that contact top
            # of the cap and the substrate (pads that caps connect to)
            #
            #measure CCHRG1 VBAT connection
            self.pogo8_curr_neg = spst_relay(self.mux_card_slot,11,self.sw)
            self.pogo7_meas_neg = spst_relay(self.mux_card_slot,31,self.sw)
            #
            #measure CCHRG1 VSS connection
            self.pogo17_curr_neg = spst_relay(self.mux_card_slot,12,self.sw)
            self.pogo16_meas_neg = spst_relay(self.mux_card_slot,32,self.sw)
            #
            #measure CCHRG2 VBAT connection
            self.pogo9_curr_neg = spst_relay(self.mux_card_slot,13,self.sw)
            self.pogo8_meas_neg = spst_relay(self.mux_card_slot,33,self.sw)
            #
            #measure CCHRG2 VSS connection
            self.pogo18_curr_neg = spst_relay(self.mux_card_slot,14,self.sw)
            self.pogo17_meas_neg = spst_relay(self.mux_card_slot,34,self.sw)
            #
            #measure CCHRG3 VBAT connection
            """pogo8_curr_neg already exists"""
            self.pogo9_meas_neg = spst_relay(self.mux_card_slot,35,self.sw)
            #
            #measure CCHRG3 VSS connection
            """pogo17_curr_neg already exists"""
            self.pogo18_meas_neg = spst_relay(self.mux_card_slot,36,self.sw)
            #**********************************************************************

            self.CCHRG1_VBAT_measurement_config = measurement_config([self.pogo1_curr_pos,
                                                                self.pogo8_curr_neg,
                                                                self.pogo2_meas_pos,
                                                                self.pogo7_meas_neg],
                                                                "CCHRG1 VBAT side")

            self.CCHRG1_VSS_measurement_config = measurement_config([self.pogo10_curr_pos,
                                                                self.pogo17_curr_neg,
                                                                self.pogo11_meas_pos,
                                                                self.pogo16_meas_neg],
                                                                "CCHRG1 VSS side")

            self.CCHRG2_VBAT_measurement_config = measurement_config([self.pogo3_curr_pos,
                                                                self.pogo9_curr_neg,
                                                                self.pogo4_meas_pos,
                                                                self.pogo8_meas_neg],
                                                                "CCHRG2 VBAT side")

            self.CCHRG2_VSS_measurement_config = measurement_config([self.pogo12_curr_pos,
                                                                self.pogo18_curr_neg,
                                                                self.pogo13_meas_pos,
                                                                self.pogo17_meas_neg],
                                                                "CCHRG2 VSS side")

            self.CCHRG3_VBAT_measurement_config = measurement_config([self.pogo5_curr_pos,
                                                                self.pogo8_curr_neg,
                                                                self.pogo6_meas_pos,
                                                                self.pogo9_meas_neg],
                                                                "CCHRG3 VBAT side")

            self.CCHRG3_VSS_measurement_config = measurement_config([self.pogo14_curr_pos,
                                                                self.pogo17_curr_neg,
                                                                self.pogo15_meas_pos,
                                                                self.pogo18_meas_neg],
                                                                "CCHRG3 VSS side")

            self.cap_leakage_measurement_config = measurement_config([self.pogo3_curr_pos,
                                                                self.pogo17_curr_neg],
                                                                "Cap Leakage:")

        else:

            #**********************************************************************
            # test configurations if using 6 pogo pins that contact top
            # of the cap and pogo pins that contact HPH side pins for VBAT and VSS
            self.CCHRG1_VBAT_measurement_config = measurement_config([self.pogo1_curr_pos,
                                                                self.VBAT2_curr_neg,
                                                                self.pogo2_meas_pos,
                                                                self.VBAT3_meas_neg],
                                                                "CCHRG1 VBAT side")

            self.CCHRG1_VSS_measurement_config = measurement_config([self.pogo10_curr_pos,
                                                                self.VSS4_curr_neg,
                                                                self.pogo11_meas_pos,
                                                                self.VSS5_meas_neg],
                                                                "CCHRG1 VSS side")

            self.CCHRG2_VBAT_measurement_config = measurement_config([self.pogo3_curr_pos,
                                                                self.VBAT2_curr_neg,
                                                                self.pogo4_meas_pos,
                                                                self.VBAT3_meas_neg],
                                                                "CCHRG2 VBAT side")

            self.CCHRG2_VSS_measurement_config = measurement_config([self.pogo12_curr_pos,
                                                                self.VSS4_curr_neg,
                                                                self.pogo13_meas_pos,
                                                                self.VSS5_meas_neg],
                                                                "CCHRG2 VSS side")

            self.CCHRG3_VBAT_measurement_config = measurement_config([self.pogo5_curr_pos,
                                                                self.VBAT2_curr_neg,
                                                                self.pogo6_meas_pos,
                                                                self.VBAT3_meas_neg],
                                                                "CCHRG3 VBAT side")

            self.CCHRG3_VSS_measurement_config = measurement_config([self.pogo14_curr_pos,
                                                                self.VSS4_curr_neg,
                                                                self.pogo15_meas_pos,
                                                                self.VSS5_meas_neg],
                                                                "CCHRG3 VSS side")

            self.cap_leakage_measurement_config = measurement_config([self.VBAT2_curr_pos,
                                                                    self.VBAT3_curr_pos,
                                                                    self.VSS4_curr_neg,
                                                                    self.VSS5_curr_neg],
                                                                    "Cap Leakage:")

            self.pogo2_check_config = measurement_config([self.pogo1_curr_pos,self.pogo2_curr_neg],
                                                                "Pogo 1-2 check")
            self.pogo11_check_config = measurement_config([self.pogo10_curr_pos,self.pogo11_curr_neg],
                                                                "Pogo 10-11 check")
            self.pogo4_check_config = measurement_config([self.pogo3_curr_pos,self.pogo4_curr_neg],
                                                                "Pogo 3-4 check")
            self.pogo13_check_config = measurement_config([self.pogo12_curr_pos,self.pogo13_curr_neg],
                                                                "Pogo 12-13 check")
            self.pogo6_check_config = measurement_config([self.pogo5_curr_pos,self.pogo6_curr_neg],
                                                                "Pogo 5-6 check")
            self.pogo15_check_config = measurement_config([self.pogo14_curr_pos,self.pogo15_curr_neg],
                                                                "Pogo 14-15 check")
            self.pogoP3_check_config = measurement_config([self.VBAT3_curr_pos,self.VBAT2_curr_neg],
                                                                "Pogo P2-P3 check")
            self.pogoP5_check_config = measurement_config([self.VSS5_curr_pos,self.VSS4_curr_neg],
                                                                "Pogo P4-P5 check")



        self.offset_measurement_config = measurement_config([self.relay_offset_pos,
                                                                self.relay_offset_neg,
                                                                self.jumper_wire_A,
                                                                self.jumper_wire_B],
                                                                "Offset Measurement")

        self.test_configurations = [self.CCHRG1_VBAT_measurement_config,
                                    self.CCHRG1_VSS_measurement_config,
                                    self.CCHRG2_VBAT_measurement_config,
                                    self.CCHRG2_VSS_measurement_config,
                                    self.CCHRG3_VBAT_measurement_config,
                                    self.CCHRG3_VSS_measurement_config]

        self.pogo_check_configs = [self.pogo2_check_config,self.pogo11_check_config,
                                    self.pogo4_check_config,self.pogo13_check_config,
                                    self.pogo6_check_config,self.pogo15_check_config,
                                    self.pogoP3_check_config,self.pogoP5_check_config]


    def sm_2wire_resistance_setup(self):
        if self.sm.get_output_state():
            self.sm.output_off()


    def setup_sourcemeter(self):
        if self.sm.get_output_state():
            self.sm.output_off()
        self.sm.set_Isource()
        self.sm.remote_sense("ON")
        self.sm.set_source_level(0)
        self.sm.set_compliance_level(self.compliance_voltage)
        self.sm.set_measurement_function("VOLT")
        self.sm.format_readings("VOLTAGE,CURRENT")
        self.sm.set_meas_speed(self.NPLC)
        self.sm.set_output_terminals("REAR")
        self.sm.output_on()


    def sense_pogo_test_setup(self):
        """run a resistance check to verify that the sense pogo pins are
           making contact with the DUT in the fixture"""
        if self.sm.get_output_state():
            self.sm.output_off()
##        self.sm._write(":CONF:RES")
##        self.sm._write(":RES:MODE MANUAL")
##        self.sm._write("SOURCE:CURRENT:LEVEL 0.000")
##        self.sm._write("FORMAT:ELEMENTS RES")
        self.sm.set_Isource()
        self.sm.set_measurement_function("RES")
        self.sm.set_sense_resistance_mode("MANUAL")
        self.sm.remote_sense("OFF")
        self.sm.format_readings("RESISTANCE")
        self.sm.set_source_level(0)
        self.sm.set_compliance_level(self.sense_pogo_compliance_voltage)
        self.sm.output_on()

    def run_sense_pogo_test(self,HPH_sn):
        """Veryfy that pogo pins used for voltage sensing during silver epoxy joint resistance testing
           are making good contact with the part in the test fixture by running a simple 2-wire
           resistance test
           will return a 3 item tuple containing either ('PASS',0,0), ('ERROR',name,0) or ('FAIL',location,resistance)
           """
        try:
            if self.debug: print"  Running sense pogo pin contact resistance check:"
            self.test_log.info("Running sense pogo pin contact resistance check...")
            self.sense_pogo_test_setup()
            self.sense_check_results = []

            for config in self.pogo_check_configs:
                self.test_log.info("%s..."%config.get_name() )
                config.config_switches()
                self.sm.set_source_level(self.sense_pogo_test_current)

                ret = self.sm.take_measurement(1)
                self.sm.set_source_level(0)
                self.sw.open_all()

                if ret == 'error':
                    if __name__ == '__main__':
                        #if running from console raise error here
                        raise RuntimeError("Error measuring sense pogo pin continuity (%s)"%(config.get_name()) )
                    else:
                        return('ERROR',config.get_name(),0)
                else:
                    resistance = ret[0]
                    self.sense_check_results.append(resistance)
                    self.test_log.info("Measured Resistance: %.2fohms"%(resistance))

                if self.debug: print"    %-17s: %.3f ohms"%(config.get_name(),resistance)

                if (resistance > self.sense_pogo_contact_resistance_ohms_high_limit) or \
                   (resistance < self.sense_pogo_contact_resistance_ohms_low_limit):
                    if __name__ == '__main__':
                        #if running from console raise error here
                        print("*%s contact resistance outside limit of %.2fohms"%(
                                                config.get_name(),resistance))
                    else:
                        t = datetime.datetime.now()
                        timestamp = t.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
                        self.write_sense_pin_fail_to_csv(self.sense_check_results,timestamp,HPH_sn)
                        return('FAIL',config.get_name(),resistance)

            self.sm.reset()
            #change sourcemeter back to silver epoxy joint measurement configuration
            self.setup_sourcemeter()
            return('PASS',0,0)

        except Exception as e:
            print "Exception in run_sense_pogo_test(): " + repr(e)
            raise e

    def leakage_setup(self):
        if self.sm.get_output_state():
            self.sm.output_off()
        self.sm.set_Vsource()
        self.sm.remote_sense("OFF")
        self.sm.set_source_level(0)
        self.sm.set_compliance_level(self.leakage_compliance_current)
        self.sm.set_measurement_function("CURRENT")

        #set a high measurement range so that the compliance current is not restricted
        self.sm.set_measurement_range("10E-3")

        self.sm.output_on()


    def capacitor_leakage_current_test(self):
        #change sourcemeter configuration for leakage measurements
        self.leakage_setup()

        if self.print_to_console: print "  Measuring leakage current after %.1f seconds..." \
                            %(self.leakage_conditioning_sec)
        self.cap_leakage_measurement_config.config_switches()
        time.sleep(0.1)


        #***************************************************
        # ramp up the voltage slowly to avoid surge current
        x = 0
        voltages = [x]
        while x < self.leakage_conditioning_voltage:
            x += self.leakage_ramp_up_voltage_step
            voltages.append(x)

        for v in voltages:
            self.sm.set_source_level(v)
            time.sleep(self.leakage_ramp_up_seconds / len(voltages))
        #***************************************************

        time.sleep(self.leakage_conditioning_sec)
        self.sm.set_source_level(self.leakage_test_voltage)
        time.sleep(1)
        self.sm.set_measurement_range(self.leakage_measurement_range)

        if self.debug: print '  measuring leakage current and voltage...'
        measurements = self.sm.take_measurements(self.num_leakage_measurements)

        if self.debug:
            for i in range(len(measurements[0])):
                print "  measurement# %02d:  V:%.6f    I:%.9f"%(i+1,measurements[0][i],measurements[1][i])

        #short out the caps to discharge test voltage
        self.sm.set_compliance_level(1)
        self.sm.set_measurement_range(1)

        #***************************************************
        # ramp down slowly to discharge test voltage
        x = self.leakage_test_voltage
        voltages = [x]
        while x > 0:
            x -= self.leakage_ramp_down_voltage_step
            voltages.append(x)

        for v in voltages:
            self.sm.set_source_level(v)
            time.sleep(self.leakage_ramp_down_seconds / len(voltages))
        #***************************************************

        time.sleep(0.2)
        self.sw.open_all()

        measured_voltage = measurements[0][self.num_leakage_measurements-1]
        measured_current = measurements[1][self.num_leakage_measurements-1]

        if self.print_to_console: print "  %s  measured voltage: %.2fV   measured current: %.0fuA" \
                    %(self.cap_leakage_measurement_config.get_name(),
                    measured_voltage,measured_current*1E6)

        #change sourcemeter back to silver epoxy joint measurement configuration
        self.setup_sourcemeter()

        return measured_current

    def find_voltage_measurement_offset(self):
        self.test_log.info("Finding voltage measurement offset...")
        self.sw.open_all()
        self.offset_measurement_config.config_switches()
        time.sleep(self.settle_sec)
        self.sm.set_source_level(0)

        if self.debug:
            print '\t*******************************************'
            print '\tfinding voltage measurement offset...'
        offsets = self.sm.take_measurements(1)
        self.voltage_measurement_offset = offsets[0][0]
        self.current_measurement_offset = offsets[1][0]
        if self.debug: print '\tvoltage measurement offset: %.6f volts'%(self.voltage_measurement_offset)
        if self.debug: print '\tcurrent measurement offset: %.9f amps'%(self.current_measurement_offset)
        if self.debug: print '\t*******************************************'
        self.sw.open_all()

        if abs(self.voltage_measurement_offset) > 0.001:
            raise RuntimeError("Voltage offset measurement of %.6fvolts above " \
                    "allowed absolute value limit of 1mV"%self.voltage_measurement_offset)

        if abs(self.current_measurement_offset) > 0.001:
            raise RuntimeError("Current offset measurement of %.6famps above " \
                    "allowed absolute value limit of 1mA"%(self.current_measurement_offset))

        self.test_log.info("Voltage measurement offset completed")


    def take_measurement(self,config,result_queue=None):
        self.test_log.info("Testing %s",config.get_name())
        config.config_switches()
        time.sleep(self.settle_sec)
        self.sm.set_source_level(self.test_current)

        measured_voltage_and_current = self.sm.take_measurements(1)
        measured_voltage = measured_voltage_and_current[0][0] - self.voltage_measurement_offset
        measured_current = measured_voltage_and_current[1][0] - self.current_measurement_offset


        #handle an 'over limit' condition where the calculated resistance tops out when the
        # sourcemeter is at compliance voltage and still well below attempted source current
        if (measured_voltage > 0.95*self.compliance_voltage) and (measured_current < (.002*self.test_current) ):
            calculated_resistance = self.compliance_voltage / (0.002*self.test_current)

        else:
            calculated_resistance = measured_voltage / measured_current


        #upper limit for calculated resistance is 10K ohms
        if calculated_resistance > 10000.0:

            calculated_resistance = 10000.0

        if self.print_to_console: print "    %-17s: %.2fmilliohms"%(config.get_name(),calculated_resistance*1000.0)

        if result_queue:
            #convert resistance reading to milliohms and put on the queue
            result_queue.put(calculated_resistance*1000.0)

        if self.pause:
            if __name__ == '__main__':
                self.test_log.info("Test Paused... waiting for user input to resume")
                #if running from command prompt wait for enter key pressed
                raw_input()
                self.test_log.info("Test resumed")
            else:
                self.test_log.info("Test Paused... waiting for user input to resume")
                self.resume = False
                while self.resume is False:
                    #wait for resume to be set to true
                    time.sleep(0.5)

                self.resume = False
                self.test_log.info("Test resumed")

        self.sm.set_source_level(0)
        self.sw.open_all()

        self.test_log.info("Testing for %s completed",config.get_name())

        return calculated_resistance



    def run_tests(self,HPH_sn,result_queue=None,pass_fail_queue=None,
                    test_started_q=None,abort_q=None):
        """this function will call run_test() as many times as required for loop testing"""

        try:
            if self.looptesting:

                self.user_abort = False
                start_time = time.clock()
                for self.current_loopnum in range(self.num_testloops):

                    if self.debug: print "*********HPH_vbat_caps_contact_resistance loop %d of %d*********"%(
                                            self.current_loopnum+1,self.num_testloops)

                    self.test_log.info("Looptesting SN:%04d... test %d of %d",int(HPH_sn),self.current_loopnum+1,self.num_testloops)

                    if abort_q is None:
                        """script is not being called by the GUI so use keyboard input as abort method"""

                        #start a thread to monitor keyboard input indicating user abort
                        keyboard_input_thread = Keyboard_input_thread()
                        keyboard_input_thread.start()

                        #delay until time interval is met or user decided to abort
                        while (time.clock()-start_time < self.current_loopnum*self.loop_interval_sec) and \
                                        (keyboard_input_thread.thread_ended() == False):
                            time.sleep(0.1)

                        #check for quit from user
                        if keyboard_input_thread.thread_ended():
                            return
                        else:
                            #end thread checking for user abort before continuing
                            keyboard_input_thread.terminate_thread()


                    else:
                        """script is being called by GUI so use flag as abort method"""

                        #delay until time interval is met or user decided to abort
                        while (time.clock()-start_time < self.current_loopnum*self.loop_interval_sec) and \
                                        (self.user_abort is False):
                            time.sleep(0.1)

                        if self.user_abort:
                            abort_q.put(1)
                            return



                    #print to the console if module was not called by GUI
                    if result_queue is None:
                        print " running test %d of %d:"%(self.current_loopnum+1,self.num_testloops)

                    self.run_test(HPH_sn,result_queue,pass_fail_queue,test_started_q)


            else:

                self.test_log.info("Testing SN:%04d"%(int(HPH_sn)))
                self.run_test(HPH_sn,result_queue,pass_fail_queue,test_started_q)

##            #wait here until the test has completed
##            self.test_in_progress = True
##            while self.test_in_progress:
##                time.sleep(0.2)

        except Exception as e:
            print "Exception in run_tests(): " + repr(e)
            raise e


    def run_test(self,HPH_sn,result_queue=None,pass_fail_queue=None,
                    test_started_q=None):
        """this function calls any required tests(resistance or leakage), checks results against limits,
           writes to the csv file if required, and generates a test report if required.
           Queues are used to indicate to the calling script that operations have completed."""

        try:

            if test_started_q is not None:
                test_started_q.put(1)

            t = datetime.datetime.now()
            timestamp = t.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
            timestamp_for_fname = t.strftime("%Y-%m-%d %H_%M_%S.%f")[:23]

            results = []
            failed_test = False

            if self.debug: print"  Testing silver epoxy contact resistance:"

            for config in self.test_configurations:
                results.append(self.take_measurement(config,result_queue))

            if self.validate_resistance_results:

                #check for a resistance value indicating tester contact problems
                for r in results:
                    if (r > self.valid_resistance_limit) or (r < 0):

                        #invalid value found so write line to csv indicating invalid result
                        self.main_pass_fail_result = 'INVALID'
                        self.write_results_to_csv(results,timestamp,HPH_sn,found_invalid_reading=True)

                        if self.looptesting:

                            #only stop the looptesting on the first iteration, allow subsequent failures
                            #to be logged as invalid but looptesting continues
                            if self.current_loopnum is 0:
                                self.user_abort = True

                        #determine whether this test script was called by GUI
                        if pass_fail_queue is not None:
                            pass_fail_queue.put('INVALID')

                        #must be running this script from command line so use print statements
                        else:
                            print "    *****Invalid Contact Resistance Found*****"
                            print "       Possible test fixture probe contact issue..."
                            print "       Try reseating part and running again."
                        return


            self.pass_fail_result_dict = dict()

            if self.use_criteria_parallel_R:
                self.pass_fail_parallel_resistance(results)
            else:
                self.pass_fail_parallel_resistance()


            if self.use_criteria_bad_caps:
                self.pass_fail_number_of_bad_caps(results)
            else:
                self.pass_fail_number_of_bad_caps()


            if self.use_criteria_absolute_R:
                self.pass_fail_absolute_resistance(results)
            else:
                self.pass_fail_absolute_resistance()


            if self.print_to_console:

                if self.use_criteria_parallel_R:
                    print "    ***** parallel resistance: %sohms %s ***** "%(
                                self.pass_fail_result_dict['parallel resistance'][1],
                                self.pass_fail_result_dict['parallel resistance'][0])

                if self.use_criteria_bad_caps:
                    print "    ***** number of compromised caps: %s %s ***** "%(
                                    self.pass_fail_result_dict['number of compromised caps'][1],
                                    self.pass_fail_result_dict['number of compromised caps'][0])

                if self.use_criteria_absolute_R:
                    print "    ***** # joints with resistance <%.3fohms: %s %s ***** "%(
                                    self.absolute_resistance_limit,
                                    self.pass_fail_result_dict['absolute resistance'][1],
                                    self.pass_fail_result_dict['absolute resistance'][0])


            if self.run_leakage_test:
                self.pass_fail_cap_leakage(self.capacitor_leakage_current_test())

                if self.print_to_console:
                    print "    ***** capacitor leakage: %suA %s ***** "%(
                                self.pass_fail_result_dict['leakage current'][1],
                                self.pass_fail_result_dict['leakage current'][0])
            else:
                self.pass_fail_cap_leakage()



            #find overall PASS/FAIL result for the HPH
            self.main_pass_fail_result = 'NA'
            for entry in self.pass_fail_result_dict:

                #any failure of a test makes the overall result a failure
                if self.pass_fail_result_dict[entry][0] == 'FAIL':
                    self.main_pass_fail_result = 'FAIL'
                    break

                #any test that passes changes the overall result from 'N/A' to PASS
                elif self.pass_fail_result_dict[entry][0] == 'PASS':
                    self.main_pass_fail_result = 'PASS'


            #putting the result on the queue indicates to calling program that result is ready
            if pass_fail_queue is not None:
                pass_fail_queue.put(self.pass_fail_result_dict)


            #write results to csv file
            if self.record_results:
                self.write_results_to_csv(results,timestamp,HPH_sn)


            if self.create_DUT_report:

                name = "HPH sn%04d - %s %s.txt"%(int(HPH_sn),timestamp_for_fname,self.main_pass_fail_result)
                DUT_report = open(self.cwd + "/../output/"+name,'w')
                if self.debug: print "  Writing DUT test report to %s"%(self.cwd + "/../output/"+name)

                DUT_report.write("**************************************************************************************\n")
                DUT_report.write("Cameron Health Inc.   /   HPH Silver Epoxy Screen Test\n")
                DUT_report.write("**************************************************************************************\n")
                DUT_report.write("Test System P/N:%s\n"%(self.test_system_pn))
                DUT_report.write("Test System SW P/N:%s    Test SW Agile REV:%s    Test SW Version:%s\n" \
                                    %(self.software_pn,self.software_agile_rev,self.software_version))
                DUT_report.write("Test Location: %s\n"%(self.test_location))
                DUT_report.write("**************************************************************************************\n")

                DUT_report.write("Test Start Date/Time: %s\n"%(timestamp))
                DUT_report.write("DUT P/N:%s    DUT REV:%s\n"%(self.DUT_pn,self.DUT_rev))
                DUT_report.write("DUT L/N:%s\n"%(self.DUT_ln))
                DUT_report.write("DUT S/N:%04d\n"%(int(HPH_sn)))
                DUT_report.write("**************************************************************************************\n\n")

                DUT_report.write("Test Reason: %s\n"%(self.test_reason))
                DUT_report.write("Test Operator: %s\n"%(self.operator_name))
                DUT_report.write("Reference Entry: %s\n\n"%(self.reference_entry))
                DUT_report.write("Test Overall Status: %s\n\n"%(self.main_pass_fail_result))

                DUT_report.write("1. Contact Resistance Test:\n")
                DUT_report.write("     CCHRG1 Anode Resistance  \t\tTest Data: %s\n" \
                                                %self.measurement_string_for_report(results[0]))
                DUT_report.write("     CCHRG1 Cathode Resistance\t\tTest Data: %s\n" \
                                                %self.measurement_string_for_report(results[1]))
                DUT_report.write("     CCHRG2 Anode Resistance  \t\tTest Data: %s\n" \
                                                %self.measurement_string_for_report(results[2]))
                DUT_report.write("     CCHRG2 Cathode Resistance\t\tTest Data: %s\n" \
                                                %self.measurement_string_for_report(results[3]))
                DUT_report.write("     CCHRG3 Anode Resistance  \t\tTest Data: %s\n" \
                                                %self.measurement_string_for_report(results[4]))
                DUT_report.write("     CCHRG3 Cathode Resistance\t\tTest Data: %s\n\n" \
                                                %self.measurement_string_for_report(results[5]))

                if self.use_criteria_parallel_R:
                    DUT_report.write("   Overall Capacitor Resistance Criteria:\n")
                    DUT_report.write("     Parallel Resistance:%s\t\t\t\tTest Data:%.0fmOhm(High Limit:%.0fmOhm)\n\n" \
                                %(self.pass_fail_result_dict['parallel resistance'][0],
                                  float(self.pass_fail_result_dict['parallel resistance'][1])*1000.0,self.max_Rp*1000.0))

                if self.use_criteria_bad_caps:
                    DUT_report.write("   High Resistance Caps Criteria:\n")
                    DUT_report.write("     Number of high resistance caps:%s\tTest Data:%d(High Limit:%.1f)\n\n" \
                                %(self.pass_fail_result_dict['number of compromised caps'][0],
                                  self.pass_fail_result_dict['number of compromised caps'][1],
                                  self.max_compromised_caps+0.1))

                if self.use_criteria_absolute_R:
                    DUT_report.write("   Joint Resistance Criteria:\n")
                    DUT_report.write("     Number of joints at or above %.0fmOhm:%s"%(self.absolute_resistance_limit*1000.0,
                                                self.pass_fail_result_dict['absolute resistance'][0]) +
                                "         Test Data:%d(High Limit:0.1)\n\n" \
                                %(self.pass_fail_result_dict['absolute resistance'][1]))

                DUT_report.write("2. Capacitor Leakage Current Test: \n")
                if self.run_leakage_test:
                    DUT_report.write("     Leakage at %.1f Volts:%s                   " \
                            %(self.leakage_test_voltage,
                            self.pass_fail_result_dict['leakage current'][0]))
                    DUT_report.write("Test Data:%.2fuA(High Limit:%.1fuA)\n\n" \
                            %(float(self.pass_fail_result_dict['leakage current'][1]),
                            self.max_leakage_limit*1E6))

                duration = datetime.datetime.now()-t
                (mins,sec) = divmod(duration.total_seconds(),60)
                (hrs,mins) = divmod(mins,60)

                DUT_report.write("\nTest Duration: %02d:%02d:%05.2f\n\n"%(hrs,mins,sec))
                DUT_report.write("Report End")

                DUT_report.close()

                if self.debug: print"Test Duration: %02d:%02d:%05.2f"%(hrs,mins,sec)

            self.test_in_progress = False

        except Exception as e:
            print "Exception in run_test(): " + repr(e)
            raise e


    def write_sense_pin_fail_to_csv(self,results,timestamp,HPH_sn):
        try:
            if self.debug: print "writing sense pin fail results to csv file..."
            self.results_file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,INVALID"%(self.test_system_pn,
                                                            self.test_location,
                                                            self.test_reason,
                                                            self.DUT_pn,self.DUT_rev,self.DUT_ln,
                                                            self.reference_entry,
                                                            self.operator_name,
                                                            timestamp))
            for r in results:
                self.results_file.write(",%.2f"%(r))

            #write the DUT serial number 5 spaces from the P4-P5 sense pogo pin resistance result
            #so add 'NA' for any blank cells
            for i in range(8-len(results)):
                self.results_file.write(",NA")

            #write NA for tests that did not run
            for i in range(4):
                self.results_file.write(",NA")

            #write the serial number
            self.results_file.write(",%04d"%(int(HPH_sn)))

            #write NA for test current and silver epoxy resistance tests that did not run
            for i in range(7):
                self.results_file.write(",NA")

            self.results_file.write("\n")
            self.results_file.flush()
            if self.debug: print "finished writing sense pin fail results to csv file"

        except Exception as e:
            print "Exception in write_sense_pin_fail_to_csv(): " + repr(e)
            raise e

    def write_results_to_csv(self,results,timestamp,HPH_sn,found_invalid_reading=False):
        try:
            if self.debug: print"  Writing results to csv file"
            self.results_file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%(self.test_system_pn,
                                                            self.test_location,
                                                            self.test_reason,
                                                            self.DUT_pn,self.DUT_rev,self.DUT_ln,
                                                            self.reference_entry,
                                                            self.operator_name,
                                                            timestamp,self.main_pass_fail_result))
            if self.get_run_sense_check:
                for result in self.sense_check_results:
                    self.results_file.write(",%.2f"%(result))
            else:
                self.results_file.write(",,,,,,,,")

            if self.main_pass_fail_result is 'INVALID':
                self.results_file.write(",,,,")

            else:
                self.results_file.write(",%s,%s,%s,%s"%(self.pass_fail_result_dict['parallel resistance'][1],
                                                        self.pass_fail_result_dict['number of compromised caps'][1],
                                                        self.pass_fail_result_dict['absolute resistance'][1],
                                                        self.pass_fail_result_dict['leakage current'][1]))

            self.results_file.write(",%04d,%.3f"%(int(HPH_sn),self.test_current))

            for result in results:
                #convert resistance readings to milliohms for csv file
                self.results_file.write(",%.2f"%(result*1000.0))
            self.results_file.write("\n")
            self.results_file.flush()
            if self.debug: print"  Done writing results to file"

        except Exception as e:
            print "Exception in write_results_to_csv(): " + repr(e)
            raise e


    def measurement_string_for_report(self,measurement):
        """this is a way to format the resistance reading so that the appropriate precision is used and
           the readings all line up to make the test report more presentable
        """
        if measurement < 0.01:
            return "%-4.2f mOhm"%(measurement*1000.0)
        if measurement < 0.1:
            return "%-4.1f mOhm"%(measurement*1000.0)
        elif measurement < 1.0:
            return "%-4.0f mOhm"%(measurement*1000.0)
        elif measurement < 10.0:
            return "%-4.2f Ohm"%(measurement)
        elif measurement < 100.0:
            return "%-4.1f Ohm"%(measurement)
        elif measurement < 10000.0:
            return "%-4.0f Ohm"%(measurement)
        else:
            return ">10K Ohm"


    def pass_fail_parallel_resistance(self,results=None):

        if results is None:
            self.pass_fail_result_dict['parallel resistance'] = ['NA','NA']
            return

        Rp = 1.0 / ( 1/(results[0]+results[1]+self.cap_ESR) + 1/(results[2]+results[3]+self.cap_ESR) + \
                                            1/(results[4]+results[5]+self.cap_ESR) )

        if Rp <= self.max_Rp:
            self.pass_fail_result_dict['parallel resistance'] = ['PASS',"%.3f"%Rp]
        else:
            self.pass_fail_result_dict['parallel resistance'] = ['FAIL',"%.3f"%Rp]

    def pass_fail_number_of_bad_caps(self,results=None):

        if results is None:
            self.pass_fail_result_dict['number of compromised caps'] = ['NA','NA']
            return

        num_compromised_caps = 0

        if (results[0] >= self.compromised_cap_Rthreshold) or (results[1] >= self.compromised_cap_Rthreshold):
            num_compromised_caps += 1

        if (results[2] >= self.compromised_cap_Rthreshold) or (results[3] >= self.compromised_cap_Rthreshold):
            num_compromised_caps += 1

        if (results[4] >= self.compromised_cap_Rthreshold) or (results[5] >= self.compromised_cap_Rthreshold):
            num_compromised_caps += 1

        if num_compromised_caps > self.max_compromised_caps:
            self.pass_fail_result_dict['number of compromised caps'] = ['FAIL',num_compromised_caps]
        else:
            self.pass_fail_result_dict['number of compromised caps'] = ['PASS',num_compromised_caps]


    def pass_fail_absolute_resistance(self,results=None):

        if results is None:
            self.pass_fail_result_dict['absolute resistance'] = ['NA','NA']
            return

        num_above_limit = 0
        self.pass_fail_result_dict['absolute resistance'] = ['PASS',num_above_limit]#"%d"%num_above_limit]
        for result in results:
            if result >= self.absolute_resistance_limit:
                num_above_limit += 1
                self.pass_fail_result_dict['absolute resistance'] = ['FAIL',num_above_limit]#"%d"%num_above_limit]


    def pass_fail_cap_leakage(self,leakage=None):

        if leakage is None:
            self.pass_fail_result_dict['leakage current'] = ['NA','NA']

        else:
            if leakage <= self.max_leakage_limit:
                self.pass_fail_result_dict['leakage current'] = ['PASS',"%.3f"%(leakage*1E6)]
            else:
                self.pass_fail_result_dict['leakage current'] = ['FAIL',"%.3f"%(leakage*1E6)]



    def verify_switch_configurations(self):
        for config in self.test_configurations:
            config.config_switches()
            raw_input(config.get_name() + "... enter to continue")
        self.sw.open_all()


    def modify_config_file(self,section,parameter,value):
        try:
            with open(self.config_file_name,'r') as cfg_file:
                data = cfg_file.readlines()

            search_lines = False
            linenum = 0
            for line in data:

                #look for section to start
                if line.find("[%s]"%section) != -1:

                    search_lines = True
                    linenum += 1
                    continue

                #look for section to end
                elif (search_lines is True) and (line.find("[") != -1) and (line.find("]") != -1):
                    break

                if search_lines:

                    #remove all whitespace from line and parameter name, then search for parameter to change
                    if "".join(line.split()).find("".join(parameter.split())+"=") != -1:
                        data[linenum] = "%s = %s\n"%(parameter,value)
                        break

                linenum += 1

            if linenum == len(data):
                raise RuntimeError("parameter not found in config file")

            with open(self.config_file_name,'w') as cfg_file:
                cfg_file.writelines(data)

        except Exception as e:
            print "Exception in modify_config_file(): " + repr(e)
            raise e

    def get_current_loop_num(self):
        return self.current_loopnum

    def set_pause(self,b):
        self.pause = b
        self.test_log.info("User set pause_each_test flag to %s",b)


    def get_pause(self):
        return self.pause

    def set_perform_verifications(self,b):
        self.perform_verifications = b
        self.test_log.info("User set perform_verifications flag to %s",b)

    def get_perform_verifications(self):
        return self.perform_verifications


    def set_test_current(self,current):
        if (current > 0) and (current <= 2.0):
            self.test_current = current
            self.test_log.info("User changed test current to %s Amps",current)

    def set_compliance_voltage(self,voltage):
        self.compliance_voltage = voltage
        self.sm.set_compliance_level(self.compliance_voltage)
        self.test_log.info("User changed compliance voltage to %s Volts",self.compliance_voltage)


    def set_looptesting(self,x):
        self.looptesting = x
        self.test_log.info("User set Loop Testing flag to %s",x)

    def get_looptesting(self):
        return self.looptesting

    def set_num_loops(self,n):
        self.num_testloops = n
        self.modify_config_file(section='execution control',
                                parameter='num testloops',
                                value=n)
        self.test_log.info("User set number of test loops to %s",n)

    def get_num_loops(self):
        return self.num_testloops

    def set_loop_interval_sec(self,n):
        self.loop_interval_sec = n
        self.modify_config_file(section='execution control',
                                parameter='loop interval seconds',
                                value=n)
        self.test_log.info("User set loop interval seconds to %s",n)

    def get_loop_interval_sec(self):
        return self.loop_interval_sec


    def get_run_sense_check(self):
        return self.run_sense_pogo_contact_check


    def set_results_file_path(self,fname):
        if self.results_file is not None:
            self.results_file.close()
        self.results_file = open(fname,'a')
        self.modify_config_file(section='output',parameter='filename',value=fname)
        self.test_log.info("User changed results file to %s",fname)

    def get_results_file_path(self):
        return self.logfilename

    def get_results_file_error(self):
        return self.results_file_error

    def get_test_current(self):
        return self.test_current

    def get_compliance_voltage(self):
        return self.compliance_voltage

    def resume_measurements(self):
        self.resume = True

    def set_record_results(self,f):
        self.record_results = f
        self.test_log.info("User changed set_record_results flag to %s",f)

    def get_record_results(self):
        return self.record_results

    def get_pass_fail_result(self):
        return self.pass_fail_result_dict

    def get_allow_config_changes(self):
        return self.allow_config_changes


    def set_operator_name(self,name):
        self.operator_name = name
        self.test_log.info("User changed operator name to %s",name)

    def get_operator_name(self):
        return self.operator_name

    def get_test_system_instance(self):
        return self.test_system_pn


    def set_create_DUT_report(self,_flag):
        self.create_DUT_report = _flag
        self.test_log.info("User set create_DUT_report to %s",_flag)

    def get_create_DUT_report(self):
        return self.create_DUT_report

    def set_test_location(self,loc):
        self.test_location = loc
        self.test_log.info("User set Test Location field to %s",loc)

    def get_test_location(self):
        return self.test_location

    def set_DUT_pn(self,pn):
        self.DUT_pn = pn
        self.test_log.info("User set DUT part number field to %s",pn)

    def get_DUT_pn(self):
        return self.DUT_pn

    def set_DUT_rev(self,rev):
        self.DUT_rev = rev
        self.test_log.info("User set DUT revision field to %s",rev)

    def get_DUT_rev(self):
        return self.DUT_rev

    def set_DUT_ln(self,ln):
        self.DUT_ln = ln
        self.test_log.info("User set DUT lot number field to %s",ln)

    def get_DUT_ln(self):
        return self.DUT_ln

    def set_test_reason(self,reason):
        self.test_reason = reason
        self.test_log.info("User set Test Reason field to %s",reason)

    def get_test_reason(self):
        return self.test_reason


    def get_leakage_test(self):
        return self.run_leakage_test

    def set_leakage_test(self,b):
        self.run_leakage_test = b
        self.test_log.info("User set run_leakage_test flag to %s",b)


    def using_criteria_parallel_R(self):
        return self.use_criteria_parallel_R

    def using_criteria_bad_caps(self):
        return self.use_criteria_bad_caps

    def using_criteria_absolute_R(self):
        return self.use_criteria_absolute_R


    def get_absolute_resistance_limit(self):
        return self.absolute_resistance_limit


    def get_reference_entry(self):
        return self.reference_entry

    def set_reference_entry(self,entry):
        self.reference_entry = entry
        self.test_log.info("User changed reference entry to %s",entry)



    def abort_looptesting(self):
        self.user_abort = True

    def program_terminated(self):
        self.test_log.info("Closing Program")


    def get_overall_pass_fail_result(self):
        return self.main_pass_fail_result


    def get_software_pn(self):
        return SW_PART_NUMBER

    def get_software_agile_rev(self):
        return SW_AGILE_REV

    def get_software_version(self):
        return SW_VERSION

    def get_software_release_type(self):
        return SW_RELEASE_TYPE


def main(argv=None):

    #********************************************
    # Parse command line options
    if argv is None:
        argv = sys.argv
    p = optparse.OptionParser()
    p.add_option("-d", action="store_true", dest="debug")
    p.add_option("--debug", action="store_true", dest="debug")
    p.add_option("-s", action="store_true", dest="substrate")
    p.add_option("--substrate", action="store_true", dest="substrate")

    # Set default values for options:
    p.set_defaults(debug=False,substrate=False)
    opts, args = p.parse_args()

    # Retrieve the option settings:
    _debug = opts.debug
    _substrate = opts.substrate
    #********************************************


    vbat_caps_test = Vbat_caps_test(print_to_console=True,debug=_debug,substrate=_substrate)

    HPH_sn = raw_input("Enter HPH sn('q' to quit): ")
    while HPH_sn != 'q':

        if vbat_caps_test.get_run_sense_check():
            vbat_caps_test.run_sense_pogo_test(HPH_sn)

        r = vbat_caps_test.run_tests(HPH_sn)
        if r == 'fail':
            HPH_sn = raw_input("reseat and press enter to try again, or enter new HPH sn('q' to quit):")
        else:
            HPH_sn = raw_input("Enter HPH sn('q' to quit): ")

    vbat_caps_test.program_terminated()

if __name__ == '__main__':
    main()
