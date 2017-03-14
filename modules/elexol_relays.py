#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      tawender
#
# Created:     07/09/2012
# Copyright:   (c) tawender 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import serial
import sys

sys.path.append("..\modules")
import elexol


class elexol_board(object):
    def __init__(self,port=1):
        #******************************************************
        #****** set up elexol serial port *********************
        self.USB_ser = serial.Serial(timeout = 3, writeTimeout = 3)
        self.USB_ser.port = int(port)-1
        self.USB_ser.open()
        #******************************************************


        #******************************************************
        #***** create and initialize the serial port device ***
        self.relays = elexol.Elexol(self.USB_ser)
        self.relays.configure_output_ports('A','B','C')
        self.relays.write_byte_to_portA(0)
        self.relays.write_byte_to_portB(0)
        self.relays.write_byte_to_portC(0)
        #******************************************************

    def all_NC(self):
        """switch all relays to normally closed state)
        """
        self.port_NC(port='A')
        self.port_NC(port='B')
        self.port_NC(port='C')

    def all_NO(self):
        """switch all relays to normally open state)
        """
        self.port_NO(port='A')
        self.port_NO(port='B')
        self.port_NO(port='C')

    def port_NC(self,port='A'):
        """switch all relays on the given port to normally closed state)
        """
        if port in ['a','A']:
            self.relays.write_byte_to_portA(0)
        if port in ['b','B']:
            self.relays.write_byte_to_portB(0)
        if port in ['c','C']:
            self.relays.write_byte_to_portC(0)

    def port_NO(self,port='A'):
        """switch all relays on the given port to normally open state)
        """
        if port in ['a','A']:
            self.relays.write_byte_to_portA(0xFF)
        if port in ['b','B']:
            self.relays.write_byte_to_portB(0xFF)
        if port in ['c','C']:
            self.relays.write_byte_to_portC(0xFF)

    def close_serial_port(self):
        self.USB_ser.close()


class relay(object):
    def __init__(self,board,port='A',relay_num=1):
        """find the desired relay from the port number(A,B,or C) and relay number(1-8)
        """
        self.elexol_DIO = board

        if port not in['a','A','b','B','c','C']:
            raise RuntimeError("invalid port number given (A-C only)")
        elif relay_num not in range(1,9):
            raise RuntimeError("invalid relay number given (0-23 only)")

        self.relay_id = self.find_relay_id(port,relay_num)

    def find_relay_id(self,port, relay_num):
        """get the I/O pin number (0-23) for the desired relay
        """
        if port in ['a','A']:
            return relay_num - 1

        elif port in ['b','B']:
            return relay_num + 7

        elif port in ['c','C']:
            return relay_num + 15

    def select_NC(self):
        """select the normally closed relay position
        """
        self.elexol_DIO.relays.clear_bit(self.relay_id)

    def select_NO(self):
        """select the normally open relay position
        """
        self.elexol_DIO.relays.set_bit(self.relay_id)

class ecg_mux(object):
    def __init__(self,board,port='A'):
        """
        """
        self.elexol_DIO = board

        if port not in['a','A','b','B','c','C']:
            raise RuntimeError("invalid port number given (A-C only)")
        else:
            self.port = port

        #define all of the relays
        self.DAC_0_SA = relay(self.elexol_DIO,self.port,8)
        self.DAC_1_SA = relay(self.elexol_DIO,self.port,7)
        self.DAC_0_SB = relay(self.elexol_DIO,self.port,6)
        self.DAC_1_SB = relay(self.elexol_DIO,self.port,5)
        self.DAC_0_HVA = relay(self.elexol_DIO,self.port,4)
        self.DAC_1_HVA = relay(self.elexol_DIO,self.port,3)
        self.DAC_0_HVB = relay(self.elexol_DIO,self.port,2)
        self.DAC_1_HVB = relay(self.elexol_DIO,self.port,1)

    def SB_SA(self):
        """connect the NI analog output DAC0OUT to SENSEB, DAC1OUT to SENSEA
        """
        self.elexol_DIO.port_NC(self.port)
        self.DAC_0_SB.select_NO()
        self.DAC_1_SA.select_NO()

    def SA_SB(self):
        """connect the NI analog output DAC0OUT to SENSEA, DAC1OUT to SENSEB
        """
        self.elexol_DIO.port_NC(self.port)
        self.DAC_0_SA.select_NO()
        self.DAC_1_SB.select_NO()

    def HVB_SA(self):
        """connect the NI analog output DAC0OUT to HVB, DAC1OUT to SENSEA
        """
        self.elexol_DIO.port_NC(self.port)
        self.DAC_0_HVB.select_NO()
        self.DAC_1_SA.select_NO()

    def SA_HVB(self):
        """connect the NI analog output DAC0OUT to SENSEA, DAC1OUT to HVB
        """
        self.elexol_DIO.port_NC(self.port)
        self.DAC_0_SA.select_NO()
        self.DAC_1_HVB.select_NO()

    def HVB_SB(self):
        """connect the NI analog output DAC0OUT to HVB, DAC1OUT to SENSEB
        """
        self.elexol_DIO.port_NC(self.port)
        self.DAC_0_HVB.select_NO()
        self.DAC_1_SB.select_NO()

    def SB_HVB(self):
        """connect the NI analog output DAC0OUT to SENSEB, DAC1OUT to HVB
        """
        self.elexol_DIO.port_NC(self.port)
        self.DAC_0_SB.select_NO()
        self.DAC_1_HVB.select_NO()

    def D0_to_HVB_and_SB_common_mode(self):
        """connect both HVB and SB to DAC0OUT in common mode configuration
        """
        self.elexol_DIO.port_NC(self.port)
        self.DAC_0_HVB.select_NO()
        self.DAC_0_SB.select_NO()

    def D1_to_HVB_and_SB_common_mode(self):
        """connect both HVB and SB to DAC0OUT in common mode configuration
        """
        self.elexol_DIO.port_NC(self.port)
        self.DAC_1_HVB.select_NO()
        self.DAC_1_SB.select_NO()

    def all_open(self):
        """open all relays in the mux
        """
        self.elexol_DIO.port_NC(self.port)




