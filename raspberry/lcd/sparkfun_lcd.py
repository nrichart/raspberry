#!/usr/bin/env python

__all__ = [ "SparkfunLCD" ]

import serial

class SparkfunLCD:
    def __sendCommand(self, command):
        self.__serial.write(self.__escape_chr)
        self.__serial.write(self.__command_list[command])

    def __sendValue(self, value):
        self.__serial.write(chr(value))

    def __init__(self, serial_port = "/dev/ttyAMA0", baudrate = 115200, width = 128, height = 64):
        self.__width  = width
        self.__height = height
 
        self.__serial = serial.Serial(serial_port, baudrate)

        self.__escape_chr = "\x7C"
        self.__command_list = { "clearScreen":   "\x00", # C-@
                                "setBacklight":  "\x02", # C-b
                                "drawCircle":    "\x03", # C-c
                                "demo":          "\x04", # C-d
                                "eraseBox":      "\x05", # C-e
                                "setBaudrate":   "\x07", # C-g
                                "drawLine":      "\x0C", # C-l
                                "drawBox":       "\x0F", # C-o
                                "setPixel":      "\x10", # C-p
                                "toggleReverse": "\x12", # C-r
                                "toggleSplash":  "\x13", # C-s
                                "setX":          "\x18", # C-x
                                "setY":          "\x19"  # C-y
                                }

        self.__baudrate = { 4800:   "1",
                            9600:   "2",
                            19200:  "3",
                            38400:  "4",
                            57600:  "5",
                            115200: "6"
                            }

        self.__sendCommand("clearScreen")


    def width(self):
        return self.__width

    def height(self):
        return self.__height

    def demo(self):
        self.__sendCommand("demo")

    def clearScreen(self):
        self.__sendCommand("clearScreen")

    def changeBauderate(self, baudrate):
        self.__sendCommand("changeBauderate")
        self.__sendValue(self.__baudrate[baudrate])
        self.__serial.close()
        self.__serial.baudrate = baudrate
        self.__serial.open()

    def setBacklight(self, backlight):
        self.__sendCommand("setBacklight")
        self.__sendValue(backlight)

    def write(self, txt):
        self.__serial.write(txt)

    def setX(self, x):
        self.__sendCommand("setX")
        self.__sendValue(x)

    def setY(self, y):
        self.__sendCommand("setY")
        self.__sendValue(y)

    def setCharX(self, x):
        self.__sendCommand("setX")
        self.__sendValue(x * 6)

    def setCharY(self, y):
        self.__sendCommand("setY")
        self.__sendValue(self.__height - y * 8)

    def setPosition(self, x, y):
        self.setX(x)
        self.setY(y)


    def setCharPosition(self, x, y):
        self.setCharX(x)
        self.setCharY(y)

    def setPixel(self, x, y, val = 0x01):
        self.__sendCommand("setPixel")
        self.__sendValue(x)
        self.__sendValue(y)
        self.__sendValue(val)

    def drawLine(self, x1, y1, x2, y2, val = 0x01):
        self.__sendCommand("drawLine")
        self.__sendValue(x1)
        self.__sendValue(y1)
        self.__sendValue(x2)
        self.__sendValue(y2)
        self.__sendValue(val)

    def drawBox(self, x1, y1, x2, y2, val = 0x01):
        self.__sendCommand("drawBox")
        self.__sendValue(x1)
        self.__sendValue(y1)
        self.__sendValue(x2)
        self.__sendValue(y2)
        self.__sendValue(val)

    def eraseBox(self, x1, y1, x2, y2):
        self.__sendCommand("eraseBox")
        self.__sendValue(x1)
        self.__sendValue(y1)
        self.__sendValue(x2)
        self.__sendValue(y2)

    def drawCircle(self, x, y, r, val = 0x01):
        self.__sendCommand("drawCircle")
        self.__sendValue(x)
        self.__sendValue(y)
        self.__sendValue(r)
        self.__sendValue(val)

    def toggleReverse(self):
        self.__sendCommand("toggleReverse")

    def toggleSplash(self):
        self.__sendCommand("toggleSplash")
