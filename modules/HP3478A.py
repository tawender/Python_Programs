

class commands(object):
    def __init__(self,instr):
        self._instr = instr

    def home(self):
        """sends the 'home' command to the instrument
        """
        self._instr.write("H0")

    def set30mRng(self):
        """sets the 30mV DC range for voltage measurement
        """
        self._instr.write("R-2")

    def set300mRng(self):
        """sets the 300m AC or DC range for voltage or current measurements
        """
        self._instr.write("R-1")

    def set3Rng(self):
        """sets the 3.0V AC or DC range for voltage or current measurements
        """
        self._instr.write("R0")

    def set3kRng(self):
        """sets the 3Kohm range for resistance measurements
        """
        self._instr.write("R3")

    def set30Rng(self):
        """sets the 30V AC or DC range for voltage or current measurements
        or the 30ohm range for resistance measurements
        """
        self._instr.write("R1")

    def set3MegRng(self):
        """sets the 3Meg ohm range for resistance measurements
        """
        self._instr.write("R6")

    def func2WireOhms(self):
        """sets the meter function to 2-wire resistance measurement
        """
        self._instr.write("F3")

    def func4WireOhms(self):
        """sets the meter function to 4-wire resistance measurement
        """
        self._instr.write("F4")

    def funcDCvolts(self):
        """sets the meter function to measure DC voltage
        """
        self._instr.write("F1")

    def meas2WireOhms(self):
        """sets the meter function to 2-wire resistance measurement
        """
        self._instr.write("H3")

    def meas4WireOhms(self):
        """sets the meter function to 4-wire resistance measurement
        """
        self._instr.write("H4")

    def write_text(self,text):
        """writes the text to the meter front panel
        """
        self._instr.write("D2%s"%text)

    def send_trigger(self):
        """sends a single trigger to the meter to take a measurement
        and returns the measured value
        """
        reading = self._instr.ask("T3")
        return reading
