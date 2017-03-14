import serial
import time
import copy
from numpy import average
import sys
sys.path.append("..\libs")
import elexol
import Instruments

class fixture(object):
    def __init__(self,usb_ser_port_num,sm_gpib_addr,dmm_gpib_addr):
        """create an instance of the test fixture and
           initialize all of the detected shift registers
           to the 'off'(normally closed) relay state

           Parameters:
           usb_ser_port_num - the serial port number elexol is installed in
           sm_gpib_addr - the gpib address of the sourcemeter
           dmm_gpib_addr - the gpib address of the multimeter
        """
        self.initialize_elexol(usb_ser_port_num)

        #find the number of shift registers installed in test system
        print "Counting number of shift registers connected to fixture..."
        num_shift_reg_found = self.count_shift_reg()

        if num_shift_reg_found < 1:
            print "No shift registers present... Exiting program."
            exit()
        else:
            print "found %d shift registers"%self.num_registers

        #initialize all of the relays to the normally closed state
        print "\nInitializing %d shift registers"%self.num_registers
        self.initialize_relays()
        print "initialization done."

        #create instances of the sourcemeter and dmm for communication
        self.dmm = Instruments.DMM_34401A("GPIB::22","meter")
        self.sm = Instruments.sourcemeter_2400("GPIB::4","sourcemeter")

    def initialize_elexol(self,port_num):
        USB_ser = serial.Serial(timeout = 2, writeTimeout = 3)
        USB_ser.port = port_num-1
        print "\n\nUSB port opened is:",
        print USB_ser.portstr

        USB_ser.open()
        USB_ser

        USB_ser_settings = USB_ser.getSettingsDict()
        print "Port settings are:"
        print USB_ser_settings

        self.e = elexol.Elexol(USB_ser)

        str = self.e.get_name()
        print "Device name: ",
        print str

        #set all bits low
        self.e.write_byte_to_portA(0)
        self.e.write_byte_to_portB(0)
        self.e.write_byte_to_portC(0)

        self.e.configure_output_ports('A', 'B', 'C')

        #configure the SPI return bit as input
        self.e.write_portA_dir_reg(0x04)

    def initialize_relays(self):
        """configures ports A,B,C on the elexol board to outputs
           with a low state, con
        """
        #create list of bytes to clear out relays
        zeroed_bytes = []
        for i in range(self.num_registers):
            zeroed_bytes.append(0x00)

        #clear out any data in the shift registers
        ret = self.e.write_SPI_bytes_to_portA(zeroed_bytes)
        self.strobe_relays()
        print "read from SPI: ",
        print ret

        #enable the relays
        self.enable_relays()

    def count_shift_reg(self):
        """count the number of shift registers in the chain,
           returns an int with the number found
        """
        #first clear out the shift registers by shifting a ton of
        #zeros through, save the data read while shifting zeros in
        max_registers = 5
        self.num_registers = 0
        all_zeros = []
        for i in range(max_registers):
            all_zeros.append(0x00)
        data_read = self.e.write_SPI_bytes_to_portA(all_zeros)

        #shift a 1 into the first shift register
        self.e.write_SPI_bytes_to_portA([0x01])

        for i in range(1,max_registers+1):
            byte_returned = self.e.write_SPI_bytes_to_portA([0x00])
            if byte_returned == [0x01]:
                self.num_registers = i

        #write the original data back into the registers
        self.e.write_SPI_bytes_to_portA(data_read[0:self.num_registers+1])

        return self.num_registers

    def get_num_shift_reg(self):
        """returns the number of shift registers found during initialization
        """
        return self.num_registers

    def dmm_measure_voltage(self,range=None,res=None):
        """take a voltage measurement with the dmm and return the result
        """
        if range is None:
            return self.dmm.measure_voltage()
        elif res is None:
            return self.dmm.measure_voltage(volt_range=range)
        else:
            return self.dmm.measure_voltage(volt_range=range,resolution=res)

    def dmm_measure_resistance(self,range=None,res=None):
        """take a resistance measurement with the dmm and return the result
        """
        if range is None:
            return self.dmm.measure_resistance()
        elif res is None:
            return self.dmm.measure_resistance(res_range=range)
        else:
            return self.dmm.measure_resistance(res_range=range,resolution=res)

    def sm_measure_current(self,num_readings=1):
        """read the current being supplied by the sourcemter and return the result
        """
        self.sm.set_measurement_function("CURRENT")
        self.sm.format_readings("CURRENT")
        ret = average(self.sm.take_measurement(num_readings))
        return ret

    def sm_measure_voltage(self,num_readings=1):
        """read the voltage being supplied by the sourcemter and return the result
        """
        self.sm.set_measurement_function("VOLTAGE")
        self.sm.format_readings("VOLTAGE")
        return average(self.sm.take_measurement(num_readings))

    def sm_set_Isource(self,level,compliance):
        """set the sourcemeter as a current source with output current specified
           in 'level' and compliance voltage specified in 'compliance'
        """
        self.sm.set_Isource()
        self.sm.set_source_level(level)
        self.sm.set_compliance_level(compliance)
        self.sm_output_on()

    def sm_set_Vsource(self,level,compliance):
        """set the sourcemeter as a voltage source with output voltage specified
           in 'level' and compliance current specified in 'compliance'
        """
        self.sm.set_Vsource()
        self.sm.set_source_level(level)
        self.sm.set_compliance_level(compliance)
        self.sm_output_on()

    def sm_output_on(self):
        """turn the sourcemeter output on
        """
        self.sm.output_on()
        #self.sm_restore_display()

    def sm_output_off(self):
        """turn the sourcemeter output off
        """
        self.sm.output_off()

    def remove_cell_from_locations_list(self,cell):
        """remove the specified cell from the list of cell locations
        """
        if type(cell) is int:
            if cell in self.cell_locations:
                self.cell_locations.remove(cell)
            else:
                print "Cell location %d not found, unable to remove."%cell

        elif type(cell) is list:
            for c in cells:
                if c in self.cell_locations:
                    self.cell_locations.remove(c)
                else:
                    print "Cell location %d not found, unable to remove."%c

    def get_cell_locations_list(self):
        return self.cell_locations

    def shift_bytes(self,bytes):
        """sends bytes out through the shift registers and reads the bytes
           that are shifted out of the shift registers back into the elexol board

            Parameters:
                bytes - a list of bytes to send

            Returns:
                a list of bytes read (one byte read for each shifted out)
        """
        data_read = self.e.write_SPI_bytes_to_portA(bytes)
        return data_read

    def I_enable(self):
        self.e.set_bit(6)

    def I_disable(self):
        self.e.clear_bit(6)

    def enable_relays(self):
        """will clock a low into the flip-flop driving Output_Enable*
            bit 7 is the clock and bit 5 is the data
        """
        #ensure clock and data are low
        self.e.clear_bit(7)
        self.e.clear_bit(5)
        time.sleep(0.01)

        #pulse the clock line
        self.e.set_bit(7)
        time.sleep(0.01)
        self.e.clear_bit(7)

    def disable_relays(self):
        """will clock a high into the flip-flop driving Output_Enable*
            bit 7 is the clock and bit 5 is the data
        """
        #ensure clock low and data high
        self.e.clear_bit(7)
        self.e.set_bit(5)
        time.sleep(0.01)

        #pulse the clock line
        self.e.set_bit(7)
        time.sleep(0.01)
        self.e.clear_bit(7)

        #clear the data line
        self.e.clear_bit(5)

    def read_state(self):
        """read the current state of shift register data and returns a list
           of data bytes
           data returned for x number of shift registers: [reg1,reg2,reg3,...regx]

           Important to note that bytes sent back into the shift registers
           must be reversed since the last byte in the shift register chain
           needs to be sent first
        """
        #build a list of 0x00 bytes to send through shift registers
        #existing data will be read as zeros are shifted in
        all_zeros = []
        for i in range(self.num_registers):
            all_zeros.append(0x00)

        #shift in the 0x00 data in order to read current data
        shift_reg_bytes = self.e.write_SPI_bytes_to_portA(all_zeros)

        #write the current data back into the shift registers
        self.e.write_SPI_bytes_to_portA(shift_reg_bytes)

        shift_reg_bytes.reverse()
        return shift_reg_bytes

    def strobe_relays(self):
        self.e.set_bit(3)
        time.sleep(0.01)
        self.e.clear_bit(3)

    def shift_1_through(self):
        initial_state = self.read_state()

        bytes_list = []
        all_zeros = []

        #build the list of bytes
        for i in range(self.num_registers):
            bytes_list.append(0x00)
            all_zeros.append(0x00)

        #loop through each byte in the list
        for i in range(self.num_registers):

            #for each bit in the byte
            for j in range(8):

                #set each byte in the list before writing
                for k in range(len(bytes_list)):
                    if k == i:
                        bytes_list[k] = 2**j
                    else:
                        bytes_list[k] = 0

                self.e.write_SPI_bytes_to_portA(all_zeros)
                self.strobe_relays()
                time.sleep(0.5)
                self.e.write_SPI_bytes_to_portA(bytes_list)
                self.strobe_relays()
                time.sleep(0.5)

        #return all zeros to clear the relays
        initial_state.reverse()
        return initial_state

    def open_all_meas_relays(self):
        """will open all measurement relays that connect
           each battery cell to the measurement DMM
        """
        byte_list = []
        for byte in self.read_state():
            byte_list.append(byte&0x55)

        byte_list.reverse()
        self.shift_bytes(byte_list)
        time.sleep(0.01)
        self.strobe_relays()
        time.sleep(0.001)

    def find_measurement_relay_bit(self,cell_num):
        """uses the cell number to find which byte number the cell is found
           in and the bit in that byte that controls the measurement relay
           Parameters:
            cell_num - an integer specifying cell to be measured
           Returns:
            a tuple containing two integers (byte_number,bit_number)
        """
        #find the byte number
        byte_index = (cell_num - 1) / 4

        #find the bit number
        if cell_num%4 == 0:
            bit = 128
        else:
            bit = 2**( (cell_num%4*2)-1 )

        return (byte_index,bit)

    def find_load_relay_bit(self,cell_num):
        """uses the cell number to find which byte number the cell is found
           in and the bit in that byte that controls the load relay
           Parameters:
            cell_num - an integer specifying cell to be measured
           Returns:
            a tuple containing two integers (byte_number,bit_number)
        """
        #find the byte number
        byte_index = (cell_num - 1) / 4

        #find the bit number
        if cell_num%4 == 0:
            bit = 64
        else:
            bit = 2**( (cell_num%4*2)-2 )

        return (byte_index,bit)

    def measure_relay_close(self,location):
        """will first open all measurement relays, then
           close the measurement relay at the specified location
        """
        #create the list of bytes to send to close the correct measurement relay
        initial_bytes_list = self.read_state()
        bytes_to_send = copy.deepcopy(initial_bytes_list)
        (index,bit)=self.find_measurement_relay_bit(location)
        bytes_to_send[index] = bytes_to_send[index] | bit

        #close the correct measurement relay
        self.open_all_meas_relays()
        time.sleep(0.01)
        bytes_to_send.reverse()
        self.shift_bytes(bytes_to_send)
        self.strobe_relays()
        time.sleep(0.1)

    def measure_cell_location(self,location='all',
                                meas_function='volts',
                                range=None,res=None):
        """will cycle through each specified cell location and take the
           measurement specified in the meas_function parameter

           Parameters:
           location - (int) the cell location to be measured
           meas_function - either 'volts' or 'resistance' for measurement function
           range - (float)measurement range for dmm measurement
           res - (float)measurement resolution for dmm measurement

           returns - (float)dmm measurement
        """
        #create the list of bytes to send to close the correct measurement relay
        initial_bytes_list = self.read_state()
        bytes_to_send = copy.deepcopy(initial_bytes_list)
        (index,bit)=self.find_measurement_relay_bit(location)
        bytes_to_send[index] = bytes_to_send[index] | bit

        #close the correct measurement relay
        self.open_all_meas_relays()
        time.sleep(0.01)
        bytes_to_send.reverse()
        self.shift_bytes(bytes_to_send)
        self.strobe_relays()
        time.sleep(0.1)

        #take the measurement
        if meas_function is 'volts':
            result = self.dmm_measure_voltage(range,res)
        elif meas_function is 'resistance':
            result = self.dmm_measure_resistance(range,res)
        else:
            raise RuntimeError("Invalid measurement function")

        self.open_all_meas_relays()

        return result

    def measure_cell_locations(self,cell_loc_lst='all',
                                meas_function='volts',
                                range=None,res=None):
        """will cycle through each specified cell location and take the
           measurement specified in the meas_function parameter

           Parameters:
           cell_loc_lst - a list of the cell locations(integers) to measure
           meas_function - either 'volts' or 'resistance' for measurement function
           range - (float)measurement range for dmm measurement
           res - (float)measurement resolution for dmm measurement

           returns - a list of 2-element lists:[ [cell location,measurement],... ]
        """
        results_list = []
        initial_bytes_list = self.read_state()

        if cell_loc_lst == 'all':
            cells = [1,2,3,4,5,6]
        else:
            cells = cell_loc_lst

        for cell in cells:

            #create the list of bytes to send to close the correct measurement relay
            bytes_to_send = copy.deepcopy(initial_bytes_list)
            (index,bit)=self.find_measurement_relay_bit(cell)
            bytes_to_send[index] = bytes_to_send[index] | bit

            #close the correct measurement relay
            self.open_all_meas_relays()
            time.sleep(0.01)
            bytes_to_send.reverse()
            self.shift_bytes(bytes_to_send)
            self.strobe_relays()
            time.sleep(0.1)

            #take the measurement
            if meas_function is 'volts':
                result = self.dmm_measure_voltage(range,res)
            elif meas_function is 'resistance':
                result = self.dmm_measure_resistance(range,res)
            else:
                raise RuntimeError("Invalid measurement function")
            results_list.append([cell,result])

        self.open_all_meas_relays()
        return results_list

    def bypass_cell_locations(self,cell_loc_lst='all'):
        """will set the load relays for cells from list to 'bypass'
           all other relay locations are unchanged

           Parameters:
           cell_loc_lst - a list of the cell locations(integers) bypass

           returns - nothing
        """
        initial_bytes_list = self.read_state()

        if cell_loc_lst == 'all':
            cells = [1,2,3,4,5,6,7,8]
        else:
            cells = cell_loc_lst

        for cell in cells:

            #find the location of the desired bit
            (index,bit)=self.find_load_relay_bit(cell)

            #clear the desired bit
            initial_bytes_list[index] = initial_bytes_list[index] & (0xff-bit)

        #reverse to send last byte in the list first
        initial_bytes_list.reverse()
        self.shift_bytes(initial_bytes_list)
        self.strobe_relays()

    def load_cell_locations(self,cell_loc_lst='all'):
        """will set the load relays for cells from list to 'not-bypassed' or 'loaded'
           all other relay locations are unchanged

           Parameters:
           cell_loc_lst - a list of the cell locations(integers) bypass

           returns - nothing
        """
        initial_bytes_list = self.read_state()

        if cell_loc_lst == 'all':
            cells = [1,2,3,4,5,6,7,8]
        else:
            cells = cell_loc_lst

        for cell in cells:

            #find the location of the desired bit
            (index,bit)=self.find_load_relay_bit(cell)

            #set the desired bit
            initial_bytes_list[index] = initial_bytes_list[index] | bit

        #reverse to send last byte in the list first
        initial_bytes_list.reverse()
        self.shift_bytes(initial_bytes_list)
        self.strobe_relays()







