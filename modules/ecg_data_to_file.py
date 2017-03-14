
import logging
import msvcrt
import os.path
import sys
import time
import threading
import traceback
import numpy as array

from optparse import OptionParser

import chtelemetry
import chtelemetry.sm as sm

from chtelemetry import _chtelemetry
from chtelemetry._chtelemetry import eventid

python_version = "%d.%d"%(sys.version_info.major, sys.version_info.minor)

if hasattr(sys, 'gettotalrefcount'):
    output_dir_name = "Debug"
    sys.path.append('../../build/lib.win32-%s-pydebug'%(python_version))
    sys.path.append(os.path.abspath('../../build/lib.win32-%s-pydebug/chtelemetry'%(python_version)))
else:
    output_dir_name = "Release"
    sys.path.append('../../build/lib.win32-%s'%(python_version))
    sys.path.append(os.path.abspath('../../build/lib.win32-%s/chtelemetry'%(python_version)))

PRB_DLL = os.path.abspath(r"..\..\prb_da\%s\prb.dll"%(output_dir_name))
DA_PRB_DLL = os.path.abspath(r"..\..\prb_da\%s\prb.dll"%(output_dir_name))
sys.path.append(os.path.abspath("..\..\%s"%(output_dir_name)))

DEFAULT_ECG_FILE = 'ecg_data.txt'

##log_date_format = "%Y/%m/%d %H:%M:%S"
##log_entry_format = "%(asctime)s.%(msecs)03d %(name)-16s %(levelname)-5s: %(message)s"
##
##logging.basicConfig(level=logging.DEBUG,
##        format = log_entry_format,
##        datefmt = log_date_format)
##
###consoleHandler = logging.StreamHandler()
###consoleHandler.setFormatter(logging.Formatter(log_entry_format, log_date_format))
###logging.getLogger().addHandler(consoleHandler)
##
###fileHandler = logging.FileHandler("ecg_recorder.log")
###fileHandler.setFormatter(logging.Formatter(log_entry_format, log_date_format))
###logging.getLogger().addHandler(fileHandler)
##
##ecg_recorder_log = logging.getLogger("ecg_recorder")








#------------------------
#	@method	parse_args()
#	@param  None
#	@return testDirectory - directory that contains test directories
#           outputDirectory - directory in which to write the test results
#
#	@brief	Parses the arguements from the command line.
#
#	@detail
#-------------------------
def parse_args():
    # parse the options from the command line
    usage="usage: %prog --s <serial number> --o <ecg data output file and path>"
    version="%prog 0.010101"

    ecg_data_file_path = ""
    serial = 0

    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--serial", help="serial number of the device", dest="serial", default ="")
    parser.add_option("-o", "--output", help="output file for ecg data", dest="output", default ="")
    (options, args) = parser.parse_args()

    if options.serial:
        serial = options.serial
        print "Serial number %s." % options.serial
        ecg_recorder_log.info("Serial number %s." % options.serial)
    if options.output:
        ecg_data_file_path = options.output
        print "Output file: %s." % options.output
        ecg_recorder_log.info("Output file: %s." % options.output)
    if not options.output:
        ecg_data_file_path = DEFAULT_ECG_FILE
        print "WARN:  You did not provide the output directory.  Results will be written to %s." % DEFAULT_ECG_FILE
        ecg_recorder_log.info("WARN:  You did not provide the output directory.  Results will be written to %s." % DEFAULT_ECG_FILE)

    return ecg_data_file_path, serial

class EcgFinalState(sm.FinalState):
    def enter(self): pass
    def handle_event(self, EcgEvent): pass
    def exit(self): pass

class EcgStateMachine(sm.StateMachine):

    def __init__(self,_log):
        self.log = _log
        self.current_state = None
        self.initial_state = None
        self.next_state = None
        self.final_state = EcgFinalState()

    def enter(self):
        self.current_state = self.initial_state
        self.current_state.state_machine = self
        self.current_state.enter()

    def handle_event(self, event_id, EcgEvent):
        self.next_state = None
        self.current_state.handle_event(event_id, EcgEvent)
        if self.next_state is None:
            return

        self.current_state.exit()
        self.current_state.state_machine = None

        self.next_state.state_machine = self
        self.next_state.enter()

        self.current_state = self.next_state

    def exit(self):
        self.log.info("%s exit"%(self))
        self.current_state.exit()
        self.current_state.state_machine = None

    def transition_to_final_state(self):
        self.next_state = self.final_state

    def reeenter_current_state(self):
        self.next_state = self.current_state

def make_ecg_recording_state_machine(session, outfile, num_datapoints, _log):
    class EcgInitialState(object):

        def __init__(self, outfile, _log,debug=False):
            self.log = _log
            self.outfile = outfile
            self.points_collected = 0
            self.debug = debug

        def enter(self):
            pass

        def handle_event(self, event_id, event):
            try:
                if event_id == eventid.EV_ECG:
                    self.log.info("EcgRecorder received ECG event: %s", event)
                    temp_string = event.data_to_string()
                    temp_list = temp_string.split()
                    temp_list.reverse()
                    for item in temp_list:
                        if self.points_collected < num_datapoints:
                            self.outfile.write("%d\n"%int(item))
                            if self.debug: print "%d: %d"%(self.points_collected+1,int(item))
                            self.points_collected += 1
                        elif self.points_collected > num_datapoints:
                            if self.debug: print 'finished collecting ecg... %d points'%(self.points_collected)
                    self.outfile.flush()
                else:
                    self.log.info("EcgRecorder received non-ECG Event: %s", event)
                    self.state_machine.transition_to_final_state()
            except Exception as e:
                print "except inside handle_event: " + repr(e)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if output_dir_name == 'Debug':
                    traceback.print_exception(exc_type, exc_value, exc_traceback,
                          limit=8, file=sys.stdout)

        def exit(self):
            pass

    sm = EcgStateMachine(_log)
    sm.initial_state = EcgInitialState(outfile,_log)
    return sm

class MyEventHandler:

    def __init__(self, state_machine):
        self.state_machine = state_machine
        self.state_machine.enter()

    def __call__(self, *args):
        if (args[0] == eventid.EV_ECG):
            self.state_machine.handle_event(eventid.EV_ECG, chtelemetry.telemetry.EcgEvent(args[1:]))

def wait_for_exit(timeout):
    start_time = time.time()
    while True:
        if msvcrt.kbhit():
            chr = msvcrt.getche()
            if ord(chr) == 13: # enter_key
                break
        if (time.time() - start_time) > timeout:
            break

##    print ''  # needed to move to next line

def start_recording(session,ecg_data_file,num_datapoints,_log):
    _log.info("ecg_recorder.start_recording()")

    outfile = ecg_data_file

    registered = False
    try:
        handler = MyEventHandler(make_ecg_recording_state_machine(session,
                                                                    outfile,
                                                                    num_datapoints,
                                                                    _log))
    except Exception as e:
        print "exception registering handler: " + repr(e)
    try:
        #session.register_handler(handler)
        #registered = True
        _chtelemetry.set_event_handler(handler)

        recorder_timeout = num_datapoints / 256
        recorder_timeout += 1.5
        wait_for_exit(recorder_timeout)
        #session.unregister_handler(handler)
        _chtelemetry.set_event_handler(session._event_source)

    except Exception as e:
        print "except inside ecg main:" + repr(e)

    finally:
        _log.info("ecg recorder exit")
        return

if __name__ == "__main__":
    main()