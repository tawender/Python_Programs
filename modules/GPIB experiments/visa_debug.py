import visa

sm = visa.instrument("GPIB::22")
sm.write("*RST")