#!/usr/bin/env python

# https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code

#Copyright (c) 2012-2013 Limor Fried, Kevin Townsend and Mikey Sklar
#for Adafruit Industries. All rights reserved.

#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions
#are met: * Redistributions of source code must retain the above
#copyright notice, this list of conditions and the following
#disclaimer. * Redistributions in binary form must reproduce the above
#copyright notice, this list of conditions and the following
#disclaimer in the documentation and/or other materials provided with
#the distribution. * Neither the name of the nor the names of its
#contributors may be used to endorse or promote products derived from
#this software without specific prior written permission.

#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# modified by netWorms to be integrated in Raspberry Pi tools

__all__ = [ "BMP085" ]

import time
from ..i2c import I2C

# ===========================================================================
# BMP085 Class
# ===========================================================================

class BMP085 :
  __i2c = None

  # Operating Modes
  ULTRALOWPOWER     = 0
  STANDARD          = 1
  HIGHRES           = 2
  ULTRAHIGHRES      = 3

  # BMP085 Registers
  __BMP085_CAL_AC1           = 0xAA  # R   Calibration data (16 bits)
  __BMP085_CAL_AC2           = 0xAC  # R   Calibration data (16 bits)
  __BMP085_CAL_AC3           = 0xAE  # R   Calibration data (16 bits)
  __BMP085_CAL_AC4           = 0xB0  # R   Calibration data (16 bits)
  __BMP085_CAL_AC5           = 0xB2  # R   Calibration data (16 bits)
  __BMP085_CAL_AC6           = 0xB4  # R   Calibration data (16 bits)
  __BMP085_CAL_B1            = 0xB6  # R   Calibration data (16 bits)
  __BMP085_CAL_B2            = 0xB8  # R   Calibration data (16 bits)
  __BMP085_CAL_MB            = 0xBA  # R   Calibration data (16 bits)
  __BMP085_CAL_MC            = 0xBC  # R   Calibration data (16 bits)
  __BMP085_CAL_MD            = 0xBE  # R   Calibration data (16 bits)
  __BMP085_CONTROL           = 0xF4
  __BMP085_TEMPDATA          = 0xF6
  __BMP085_PRESSUREDATA      = 0xF6
  __BMP085_READTEMPCMD       = 0x2E
  __BMP085_READPRESSURECMD   = 0x34

  # Private Fields
  __cal_AC1 = 0
  __cal_AC2 = 0
  __cal_AC3 = 0
  __cal_AC4 = 0
  __cal_AC5 = 0
  __cal_AC6 = 0
  __cal_B1  = 0
  __cal_B2  = 0
  __cal_MB  = 0
  __cal_MC  = 0
  __cal_MD  = 0

  __conversion_time = { ULTRALOWPOWER: 0.0045,
                        STANDARD:      0.007,
                        HIGHRES:       0.0135,
                        ULTRAHIGHRES:  0.0255 }


  # Constructor
  def __init__(self, address=0x77, mode = STANDARD, debug=False):
    self.__i2c = I2C(address)

    self.debug = debug

    # Make sure the specified mode is in the appropriate range
    if ((mode < 0) | (mode > 3)):
      if (self.debug):
        print "Invalid Mode: Using STANDARD by default"
      self.mode = self.__BMP085_STANDARD
    else:
      self.mode = mode

    # Read the calibration data
    self.readCalibrationData()


  def readCalibrationData(self):
    """Reads the calibration data from the IC"""

    self.__cal_AC1 = self.__i2c.read_signed_short(self.__BMP085_CAL_AC1)
    self.__cal_AC2 = self.__i2c.read_signed_short(self.__BMP085_CAL_AC2)
    self.__cal_AC3 = self.__i2c.read_signed_short(self.__BMP085_CAL_AC3)
    self.__cal_AC4 = self.__i2c.read_short       (self.__BMP085_CAL_AC4)
    self.__cal_AC5 = self.__i2c.read_short       (self.__BMP085_CAL_AC5)
    self.__cal_AC6 = self.__i2c.read_short       (self.__BMP085_CAL_AC6)
    self.__cal_B1  = self.__i2c.read_signed_short(self.__BMP085_CAL_B1) 
    self.__cal_B2  = self.__i2c.read_signed_short(self.__BMP085_CAL_B2) 
    self.__cal_MB  = self.__i2c.read_signed_short(self.__BMP085_CAL_MB) 
    self.__cal_MC  = self.__i2c.read_signed_short(self.__BMP085_CAL_MC) 
    self.__cal_MD  = self.__i2c.read_signed_short(self.__BMP085_CAL_MD) 


  def showCalibrationData(self):
      """Displays the calibration values for debugging purposes"""
      print "AC1 = {0}".format(self.__cal_AC1)
      print "AC2 = {0}".format(self.__cal_AC2)
      print "AC3 = {0}".format(self.__cal_AC3)
      print "AC4 = {0}".format(self.__cal_AC4)
      print "AC5 = {0}".format(self.__cal_AC5)
      print "AC6 = {0}".format(self.__cal_AC6)
      print "B1  = {0}".format(self.__cal_B1)
      print "B2  = {0}".format(self.__cal_B2)
      print "MB  = {0}".format(self.__cal_MB)
      print "MC  = {0}".format(self.__cal_MC)
      print "MD  = {0}".format(self.__cal_MD)


  def readRawTemp(self):
    """Reads the raw (uncompensated) temperature from the sensor"""
    self.__i2c.write_byte(self.__BMP085_CONTROL, self.__BMP085_READTEMPCMD)
    time.sleep(0.0045)  # Wait 4.5ms

    raw = self.__i2c.read_short(self.__BMP085_TEMPDATA)
    return raw


  def readRawPressure(self):
    """Reads the raw (uncompensated) pressure level from the sensor"""
    
    self.__i2c.write_byte(self.__BMP085_CONTROL,
                          self.__BMP085_READPRESSURECMD + (self.mode << 6))

    time.sleep(self.__conversion_time[self.mode])

    msb  = self.__i2c.read_byte(self.__BMP085_PRESSUREDATA)
    lsb  = self.__i2c.read_byte(self.__BMP085_PRESSUREDATA+1)
    xlsb = self.__i2c.read_byte(self.__BMP085_PRESSUREDATA+2)

    raw = ((msb << 16) + (lsb << 8) + xlsb) >> (8 - self.mode)

    return raw


  def readTemperature(self):
    """Gets the compensated temperature in degrees celcius"""

    # Read raw temp before aligning it with the calibration values
    UT = self.readRawTemp()
    X1 = ((UT - self.__cal_AC6) * self.__cal_AC5) >> 15
    X2 = (self.__cal_MC << 11) / (X1 + self.__cal_MD)
    B5 = X1 + X2
    temp = ((B5 + 8) >> 4) / 10.0

    return temp


  def read(self):
    """Gets the compensated pressure in pascal and the temperature"""

    UT = self.readRawTemp()
    UP = self.readRawPressure()

    # True Temperature Calculations
    X1 = ((UT - self.__cal_AC6) * self.__cal_AC5) >> 15
    X2 = (self.__cal_MC << 11) / (X1 + self.__cal_MD)
    B5 = X1 + X2
    temp = ((B5 + 8) >> 4) / 10.0

    # Pressure Calculations
    B6 = B5 - 4000
    X1 = (self.__cal_B2 * (B6 * B6) >> 12) >> 11
    X2 = (self.__cal_AC2 * B6) >> 11
    X3 = X1 + X2
    B3 = (((self.__cal_AC1 * 4 + X3) << self.mode) + 2) / 4
    X1 = (self.__cal_AC3 * B6) >> 13
    X2 = (self.__cal_B1 * ((B6 * B6) >> 12)) >> 16
    X3 = ((X1 + X2) + 2) >> 2
    B4 = (self.__cal_AC4 * (X3 + 32768)) >> 15
    B7 = (UP - B3) * (50000 >> self.mode)
    if (B7 < 0x80000000):
      p = (B7 * 2) / B4
    else:
      p = (B7 / B4) * 2
      
    X1 = (p >> 8) * (p >> 8)
    X1 = (X1 * 3038) >> 16
    X2 = (-7357 * p) >> 16

    p = p + ((X1 + X2 + 3791) >> 4)

    return (1. * p, temp)

  def readAltitude(self, seaLevelPressure=101325):
    "Calculates the altitude in meters"
    altitude = 0.0
    pressure = float(self.read()[0])
    altitude = 44330.0 * (1.0 - pow(pressure / seaLevelPressure, 1./5.255))
    return altitude
