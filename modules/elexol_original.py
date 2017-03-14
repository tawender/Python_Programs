

class Elexol(object):
    def __init__(self, usb_ser):
        self._usb_ser = usb_ser

    def get_name(self):
        """ returns the name of the device.
        """
        self._usb_ser.write("?")
        str = self._usb_ser.read(12)
        return str

    def configure_output_port(self, port):
        self._usb_ser.write("!%s\x00"%(port))

    def configure_output_ports(self, *ports):
        for port in ports:
            self.configure_output_port(port)




    def write_byte_to_port(self, port, value):
        self._usb_ser.write(port)
        self._usb_ser.write(chr(value))

    def read_byte_from_port(self, port):
        data = self._usb_ser.write(port)
        return data

    def set_bit(self, bit):
        self._usb_ser.write('H')
        self._usb_ser.write(chr(bit))

    def clear_bit(self, bit):
        self._usb_ser.write('L')
        self._usb_ser.write(chr(bit))




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





    #***** SPI data ************************
    def write_SPI_byte_to_portA(self, byte):
        """send a byte in SPI format out at port A
        byte - the byte of data to be written
        """
        self.write_byte_to_port('S', byte)

    def write_SPI_bytes_to_portA(self, bytes):
        """send a string of bytes out in SPI format at port A
        bytes - a list of bytes to be sent out
        """
        for byte in bytes:
            self.write_SPI_byte_to_portA(byte)
    #****************************************




