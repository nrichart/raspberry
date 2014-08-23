#!/usr/bin/env python

# Copyright (c) 2012-2013 Limor Fried, Kevin Townsend and Mikey Sklar
# for Adafruit Industries. All rights reserved.
  
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# * Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the following
#   disclaimer.
# * Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials provided with
#   the distribution.
# * Neither the name of the nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
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

# https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code

# modified by netWorms to be integrated in Raspberry Pi tools


__all__ = [ "I2C" ]

import smbus

# ===========================================================================
# Adafruit_I2C Class
# ===========================================================================

class I2C :
  @staticmethod
  def getPiRevision():
    "Gets the version number of the Raspberry Pi board"
    # Courtesy quick2wire-python-api
    # https://github.com/quick2wire/quick2wire-python-api
    try:
      with open('/proc/cpuinfo','r') as f:
        for line in f:
          if line.startswith('Revision'):
            return 1 if line.rstrip()[-1] in ['1','2'] else 2
    except:
      return 0

  @staticmethod
  def getPiI2CBusNumber():
    # Gets the I2C bus number /dev/i2c#
    return 1 if I2C.getPiRevision() > 1 else 0
 
  def __init__(self, address, busnum = -1):
    self.__address = address
    # By default, the correct I2C bus is auto-detected using /proc/cpuinfo
    # Alternatively, you can hard-code the bus version below:
    # self.__smbus = smbus.SMBus(0); # Force I2C0 (early 256MB Pi's)
    # self.__smbus = smbus.SMBus(1); # Force I2C1 (512MB Pi's)
    print("Connecting to I2C{0}".format(busnum if busnum >= 0 else I2C.getPiI2CBusNumber()))
    self.__smbus = smbus.SMBus(busnum if busnum >= 0 else I2C.getPiI2CBusNumber())

  def reverseByteOrder(self, data):
    """Reverses the byte order of an int (16-bit) or long (32-bit) value"""
    # Courtesy Vishal Sapre
    byteCount = len(hex(data)[2:].replace('L','')[::2])
    val       = 0
    for i in range(byteCount):
      val    = (val << 8) | (data & 0xff)
      data >>= 8
    return val

  def errMsg(self):
    print("Error accessing {0:#X}: Check your I2C address".format(self.__address))
    return -1

  def write_byte(self, reg, value):
    """Writes an 8-bit value to the specified register"""
    try:
      self.__smbus.write_byte_data(self.__address, reg, value)
    except IOError, err:
      return self.errMsg()

  def write_short(self, reg, value):
    """Writes a 16-bit value to the specified register"""
    try:
      self.__smbus.write_word_data(self.__address, reg, value)
    except IOError, err:
      return self.errMsg()

  def write_block(self, reg, list):
    """Writes an array of bytes using I2C format"""
    try:
      self.__smbus.write_i2c_block_data(self.__address, reg, list)
    except IOError, err:
      return self.errMsg()

  def read_block(self, reg, length):
    """Read a list of bytes from the I2C device"""
    try:
      results = self.__smbus.read_i2c_block_data(self.__address, reg, length)
      return results
    except IOError, err:
      return self.errMsg()

  def read_byte(self, reg):
    """Read an byte from the I2C device"""
    try:
      return self.__smbus.read_byte_data(self.__address, reg)
    except IOError, err:
      return self.errMsg()

  def read_signed_byte(self, reg):
    """Reads a signed byte from the I2C device"""

    result = self.read_byte(reg)
    return result - (1 << 8) * (result >> 7)


  def read_short(self, reg):
    """Reads an unsigned 16-bit value from the I2C device"""

    msb, lsb = self.read_block(reg, 2)
    return ((msb << 8) + lsb)


  def read_signed_short(self, reg):
    "Reads a signed 16-bit value from the I2C device"

    result = self.read_short(reg)
    return result - (1 << 16) * (result >> 15)


