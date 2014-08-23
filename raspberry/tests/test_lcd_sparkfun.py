#!/usr/bin/env python

from raspberry.lcd import *

lcd = SparkfunLCD()

lcd.setBacklight(20)

lcd.setXChar(1)
lcd.setYChar(1)
lcd.write("Hello world!")
