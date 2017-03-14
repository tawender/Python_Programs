

class Elexol(object):
    def __init__(self, usb_ser):
        self._usb_ser = usb_ser

    def get_name(self):
        """ returns the name of the device.
        """
        self._usb_ser.write("?")
        str = self._usb_ser.read(15)
        return str

    def configure_output_port(self, port):
        self._usb_ser.write("!%s\x00"%(port))

    def configure_output_ports(self, *ports):
        for port in ports:
            self.configure_output_port(port)




    def write_byte_to_port(self, port, value):
        self._usb_ser.write(port)
        self._usb_ser.write(chr(value))

    def write_SPI_byte_to_port(self, port, value):
        self._usb_ser.write(port)
        self._usb_ser.write(chr(value))
        bytes = self._usb_ser.read(2)

        #get rid of the 'S' and return the byte read as an int
        return int("%0#4x"%ord(bytes[1]),0)

    def read_byte_from_port(self, port):
        data = self._usb_ser.write(port)
        return data

    def set_bit(self, bit):
        self._usb_ser.write('H')
        self._usb_ser.write(chr(bit))

    def clear_bit(self, bit):
        self._usb_ser.write('L')
        self._usb_ser.write(chr(bit))

    def write_port_dir_reg(self,port,byte):
        self._usb_ser.write(port)
        self._usb_ser.write(chr(byte))




    def write_byte_to_portA(self, value):
        """ writes an integer value to port A
        value an integer value.
        """
        self.write_byte_to_port('A', value)

    def write_byte_to_portB(self, value):
        """ writes an integer value to port B
        value an integer value.
        """
        self.write_byte_to_port('B', value)

    def write_byte_to_portC(self, value):
        """ writes an integer value to port C
        value an integer value.
        """
        self.write_byte_to_port('C', value)

    def read_portA_byte(self):
        """ reads the current state of the bits at port A
        """
        port_byte = self.read_byte_from_port('a')
        return port_byte

    def read_portB_byte(self):
        """ reads the current state of the bits at port B
        """
        port_byte = self.read_byte_from_port('b')
        return port_byte

    def read_portC_byte(self):
        """ reads the current state of the bits at port C
        """
        port_byte = self.read_byte_from_port('c')
        return port_byte

    def set_bits(self,bits):
        """sets the specified list of bits(0-24) high
        """
        for bit in bits:
            self.set_bit(bit)

    def clear_bits(self,bits):
        """clears the specified list of bits(0-24) -writes low
        """
        for bit in bits:
            self.clear_bit(bit)

    def write_portA_dir_reg(self,byte):
        """writes the port A I/O direction register (1=input)
            byte - specify the bits to set as inputs
        """
        self.write_port_dir_reg('!A',byte)

    def write_portB_dir_reg(self,byte):
        """writes the port B I/O direction register (1=input)
            byte - specify the bits to set as inputs
        """
        self.write_port_dir_reg('!B',byte)

    def write_portC_dir_reg(self,byte):
        """writes the port C I/O direction register (1=input)
            byte - specify the bits to set as inputs
        """
        self.write_port_dir_reg('!C',byte)




    #***** SPI data ************************
    def write_SPI_byte_to_portA(self, byte):
        """send a byte in SPI format out at port A
        byte - the byte of data to be written
        returns - 1 byte of SPI data read from the port
        """
        ret_byte = self.write_SPI_byte_to_port('S', byte)
        return ret_byte

    def write_SPI_bytes_to_portA(self, bytes):
        """send a string of bytes out in SPI format at port A
        bytes - a list of bytes to be sent out
        returns - list of bytes of SPI data read from the port
        """
        ret_bytes_list = []
        for byte in bytes:
            ret_bytes_list.append(self.write_SPI_byte_to_portA(byte))
        return ret_bytes_list

    def write_SPI_byte_to_portB(self, byte):
        """send a byte in SPI format out at port B
        byte - the byte of data to be written
        returns - 1 byte of SPI data read from the port
        """
        ret_byte = self.write_SPI_byte_to_port('T', byte)
        return ret_byte

    def write_SPI_bytes_to_portB(self, bytes):
        """send a string of bytes out in SPI format at port B
        bytes - a list of bytes to be sent out
        returns - list of bytes of SPI data read from the port
        """
        ret_bytes_list = []
        for byte in bytes:
            ret_bytes_list.append(self.write_SPI_byte_to_portB(byte))
        return ret_bytes_list

    def write_SPI_byte_to_portC(self, byte):
        """send a byte in SPI format out at port C
        byte - the byte of data to be written
        returns - 1 byte of SPI data read from the port
        """
        ret_byte = self.write_SPI_byte_to_port('U', byte)
        return ret_byte

    def write_SPI_bytes_to_portC(self, bytes):
        """send a string of bytes out in SPI format at port C
        bytes - a list of bytes to be sent out
        returns - list of bytes of SPI data read from the port
        """
        ret_bytes_list = []
        for byte in bytes:
            ret_bytes_list.append(self.write_SPI_byte_to_portC(byte))
        return ret_bytes_list
    #****************************************




