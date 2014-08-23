#!/usr/bin/env python

from raspberry.sensors import *

# ===========================================================================
# Example Code
# ===========================================================================

# Initialise the BMP085 and use STANDARD mode (default value)
# bmp = BMP085(0x77, debug=True)
bmp = BMP085(0x77, BMP085.ULTRAHIGHRES)

# Read the current barometric pressure level
pressure, temp = bmp.read()

# To calculate altitude based on an estimated mean sea level pressure
# (1013.25 hPa) call the function as follows, but this won't be very accurate
altitude = bmp.readAltitude()

# To specify a more accurate altitude, enter the correct mean sea level
# pressure level.  For example, if the current pressure level is 1023.50 hPa
# enter 102350 since we include two decimal places in the integer value
# altitude = bmp.readAltitude(102350)

print """Temperature: {0:.2f} C
Pressure:    {1:.2f} hPa
Altitude:    {2:.2f} m""".format(temp, (pressure / 100.0), altitude)
