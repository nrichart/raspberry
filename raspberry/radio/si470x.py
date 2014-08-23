#!/usr/bin/env python

# Copyright (c) 2014, netWorms 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__all__ = [ "SI470x" ]

import RPi.GPIO as gpio 
import time
from ..i2c import I2C

import array

class SI470x:
    # De-Emphasis[3:0] Space[3:0] Band[3:0]
    EUROPE     = 0x110
    USA        = 0x000
    JAPAN_Wide = 0x111
    JAPAN      = 0x112

    # Seek direction
    UP   = 1
    DOWN = 0

    # Seek mode
    LIMIT = 1
    WRAP  = 0

    __i2c = None

    __registers = None
    __properties = None

    # configuration values given in Mhz
    __spacing  = { 0x000: 0.2 , 0x010: 0.1, 0x020: 0.050  }
    __band_min = { 0x000: 87.5, 0x001: 76 , 0x002: 76 }
    __band_max = { 0x000: 108 , 0x001: 108, 0x002: 90 }

    def __init__(self, address=0x10, rst_pin = 23,
                 region = EUROPE, volume = 16, debug=False):
        '''
        This initialize the Si470x module according to the datasheet
        rev 1.1 and the document AN230 rev0.9
        can be found here:
        http://www.sparkfun.com/datasheets/BreakoutBoards/Si4702-03-C19-1.pdf
        '''

        self.__debug = debug
        self.__i2c = I2C(address)
        self.__registers = SI470x.Registers(self.__i2c)
        self.__properties = SI470x.Properties(self.__i2c)

        self.__rst_pin = rst_pin

        gpio.setwarnings(False)
        gpio.setmode(gpio.BCM)  # We will use board numbering instead of pin numbering. 
        gpio.setup(self.__rst_pin, gpio.OUT)

        gpio.output(self.__rst_pin, gpio.LOW)
        time.sleep(.1)
        gpio.output(self.__rst_pin ,gpio.HIGH)
        time.sleep(0.5)

        # initial read
        self.__registers.read()
        
        # enable the oscilator and wait a least 500ms
        self.__registers.set("xoscen")
        self.__registers.write()
        time.sleep(.5)

        # enable the IC
        self.__registers.set("enable")
        self.__registers.write();
        time.sleep(1)

        self.__registers.read() # read the current registers

        #self.__properties.get(0x0700)

        self.__registers.set("rds")
        self.__registers.set("rdsml")
        self.mute(direct_update = False)
        self.setSoftMute(direct_update = False)
        self.setRegion(region, direct_update = False)
        self.setVolume(volume, direct_update = False)
        self.setChannel(self.__band_min[region & 0x0F], direct_update = False )

        self.__registers.write();
        if self.__debug == True: print(self.__registers)

    def __str__(self):
        s = self.status()
        if self.__debug == True: s += "\n" + self.__registers.__str__()
        return s

    def __update_registers(self, direct_update = True, **kwargs):
        if direct_update == True:
            self.__registers.write()

    def status(self): 
        freq = self.getChannel()
        __rds_errors = ["0 errors", "1-2 errors", "3-5 errors", "6+ errors"]
        return ("Status:\n" + 
                " - freq: {0}MHz\n" +
                " - RDS status: {1} (Block A:{4} - B:{5} - C:{6} - C:{7})\n" +
                " - Stereo indicator: {2}\n" +
                " - RSSI: {3}/75dBuV").format(freq,
                                              "ready" if self.__registers.get("rdsr") == 1 else "none",
                                              "stereo" if self.__registers.get("st") == 1 else "mono",
                                              self.__registers.get("rssi"),
                                              __rds_errors[self.__registers.get("blera")],
                                              __rds_errors[self.__registers.get("blerb")],
                                              __rds_errors[self.__registers.get("blerc")],
                                              __rds_errors[self.__registers.get("blerd")])


    def hasRDS(self):
        self.__registers.read(end = "statusrssi")
        return self.__registers.get("rdsr") == 1

    __rdbs_text = ['.','.','.','.','.','.','.','.']
    __rdbs_id = ['.','.','.','.','.','.','.','.']

    def pollRDS(self):
        '''
        The RDS part is experimental and not yet finished Reference is
        AN243 rev0.2 and RDBS Standard that is basically the same info
        '''
        start = time.time();
        self.__registers.read(end = "rdsd")

        rdbs = ""
        if self.__registers.get("rdsr"):
            if self.__registers.get("blera") < 3:
                pi = self.__registers.get("rdsa")
                rdbs = "PI: {0:#x}".format(pi)
                if self.__registers.get("blerb") < 2:
                    rdsb = self.__registers.get("rdsb")
                    group_type = rdsb >> 11
                    pty = (rdsb >> 5) & 0xF
                    b0 = (rdsb >> 9) & 0x1
                    tp = (rdsb >> 10) & 0x1
                    rdbs  += " - Group: {1} B0: {2} TP: {3} PTY:{4}".format(pi, group_type, b0, tp, pty)

                    rdsc = self.__registers.get("rdsc")
                    rdsd = self.__registers.get("rdsd")
                    t = [ rdsc >> 8, rdsc & 0xFF, rdsd >> 8, rdsd & 0xFF ]
                    if group_type == 4: # radio text
                        pos = rdsb & 0x4
                        for i in range(4):
                            self.__rdbs_text[pos + i] = chr(t[i])

                    if group_type == 0:
                        c = (rdsb >> 0) & 3
                        self.__rdbs_id[c    ] = chr(t[2])
                        self.__rdbs_id[c + 1] = chr(t[3])

                    rdbs += " - rds_id: {0}".format(self.__rdbs_id)
                    rdbs += " - text \"" + self.__rdbs_text.__str__() + "\""
        if not rdbs == "":
            print("\r"+rdbs),
                    
        dur = 0.086 - (time.time() - start)
        if(dur > 0):
            time.sleep(dur)

    def rssi(self):
        self.__registers.read(end = "statusrssi")
        return self.__registers.get("rssi")

    def setSoftMute(self, mute = True, attenuation = 16, speed = "fastest", **kwargs):
        __softmute_speed = { "fastest": 0x0,
                             "fast"   : 0x1,
                             "slow"   : 0x2,
                             "slowest": 0x3 }
        __softmute_attenuation = {16: 0, 14: 1, 12: 2, 10: 3} # in dB

        speed = speed if speed in __softmute_speed else "fastest"
        attenuation = attenuation if attenuation in __softmute_attenuation else 16
        
        self.__registers.set("dsmute", 0x0 if mute == True else 0x1)
        self.__registers.set("smutea", __softmute_attenuation[attenuation])
        self.__registers.set("smuter", __softmute_speed[speed])
        self.__update_registers(**kwargs)

    def __wait_stc(self, value, timeout = 1):
        start = time.time()
        timeouted = False

        while(self.__registers.get("stc") != value and not timeouted):
            timeouted = (time.time() - start > timeout)
            self.__registers.read(end = "statusrssi")

        return timeouted


    def setChannel(self, frequence, tune = True, timeout = 0.5, **kwargs):
        '''
        Set the channel according to Datasheet Rev 1.1 page 25
        Freq (MHz) = Spacing (MHz) x Channel + 87.5 MHz
        By default the station is tuned
        '''
        if frequence > self.__band_max[self.__region & 0x0F]: frequence = self.__band_max[self.__region & 0x0F]
        channel = int((frequence - self.__band_min[self.__region & 0x0F]) / self.__spacing[self.__region & 0xF0])
        self.__registers.set("channel", channel)

        if self.__debug == True:
            print(("Setting frequency: {0}MHz translated in:\n" +
                   " - CHANNEL[9:0] = 0x{1:X}").format(frequence, channel))
        
        if tune:
            self.__registers.set("tune")
            self.__registers.write(end = "channel")
            time.sleep(.060) # wait 60ms

            # wait that station is tuned
            self.__wait_stc(1, timeout)

            self.__registers.set("tune", 0x0)
            self.__registers.write(end = "channel")

            # clear the STC bit
            self.__wait_stc(0, timeout)
            self.__registers.read(end = "readchan")

            if self.__debug == True:
                frequence = self.getChannel()
                channel = self.__registers.get("readchan")
                print(("Frequency tuned to {0}MHz\n" +
                       " - READCHAN[9:0] = 0x{1:X}").format(frequence, channel))
        else:
            self.__update_registers(**kwargs)


    def getChannel(self, **kwargs):
        '''
        Return the current frequency
        '''
        self.__registers.read(end = "readchan")
        return (self.__band_min[self.__region & 0x0F] +  self.__spacing[self.__region & 0xF0] * self.__registers.get("readchan"))

    def seek(self, direction = UP, mode = WRAP, timeout = 1, seek_rssi_threshold = 0x19, seek_snr_threshold = 0x4, seek_fm_counts = 0x8, **kwargs):
        # the defaults values are the one recommanded in AN284
        self.__registers.set("seekth", seek_rssi_threshold)
        self.__registers.set("sksnr", seek_snr_threshold)
        self.__registers.set("skcnt", seek_fm_counts)

        self.__registers.set("skmode", mode)
        self.__registers.set("seekup", direction)
        self.__registers.set("seek", 1)

        self.__registers.write(end = "powercfg")
        self.__wait_stc(1, timeout)

        if self.__registers.get("sfbl"):
            print("Seek fail or reached the and of the band!")

        self.__registers.set("seek", 0)
        self.__registers.write(end = "powercfg")
        self.__wait_stc(0, timeout)

        if self.__debug == True:
            frequence = self.getChannel()
            channel = self.__registers.get("readchan")
            print(("Frequency seeked to {0}MHz\n" +
                   " - READCHAN[9:0] = 0x{1:X}").format(frequence, channel))


    def setRegion(self, region, **kwargs):
        '''
        Set the region parameters
        '''

        self.__region = region

        self.__registers.set("de"   , (region >> 8) & 0xF)
        self.__registers.set("space", (region >> 4) & 0xF)
        self.__registers.set("band" ,  region       & 0xF)

        if self.__debug == True:
            region_str = { self.EUROPE: "Europe",
                           self.USA: "USA",
                           self.JAPAN_Wide: "Japan (wide)",
                           self.JAPAN: "Japan"}
            print(("Setting region: {0} translated in:\n" +
                   " - DE[0] = {1}\n" +
                   " - BAND[1:0] = {2}\n" +
                   " - SPACE[1:0] = {3}").format(region_str[region],
                                               self.__registers.get("de"),
                                               self.__registers.get("space"),
                                               self.__registers.get("band")))

        self.__update_registers(**kwargs)

    def setVolume(self, volume, **kwargs):
        '''
        Set the volume between 0 and 31
        00: mute
        01: -58 dBFS
        0F: -30 dBFS
        10: -28 dBFS
        1E:   0 dBFS
        '''

        self.__volume = volume

        if volume > 0x1E:
            volume = 0x1E

        volext = (~volume >> 4) & 0x01
        volume = (volume & 0xF) + ((volume >> 4) & 0x1)

        if self.__debug == True:
            print(("Volume command: {0} ({1} dBFS) translated in\n" +
                   " - VOLUME[3:0] = {2}\n" +
                   " - VOLEXT[0] = {3}").format(self.__volume,
                                                range(-58, 0, 2)[self.__volume - 1],
                                                volume,
                                                volext))

        self.__registers.set("volume", volume)
        self.__registers.set("volext", volext)

        self.__update_registers(**kwargs)

    def mute(self, **kwargs):
        '''
        Mute/unmute the radio
        '''
        self.__registers.set("dmute", ~(self.__registers.get("dmute")))
        self.__update_registers(**kwargs)


    # --------------------------------------------------------------------------
    class Registers:
        __update_regs = 0x08
        class BitsInfo:
            def __init__(self, reg, pos, mask):
                self.reg  = reg
                self.pos  = pos
                self.mask = mask

        def __init__(self, i2c):
            self.__i2c = i2c

        def set(self, bit, value = 0x1):
            info_bit = self.__bits[bit]
            reg = self.__reg_addr[info_bit.reg]
            self.__update_regs = max(reg, self.__update_regs)

            wiped_bits = self.__registers[reg] & (~(info_bit.mask << info_bit.pos))
            self.__registers[reg] = wiped_bits | ((value & info_bit.mask) << info_bit.pos)


        def get(self, bit):
            info_bit = self.__bits[bit]
            reg = self.__reg_addr[info_bit.reg]
            return (self.__registers[reg] >> info_bit.pos) & info_bit.mask

        def set_reg(self, reg, value):
            '''
            This method write the register
            '''
            reg_addr = self.__reg_addr[reg]
            self.__update_regs = max(reg_addr, self.__update_regs)
            self.__registers[reg_addr] = value

        def read(self, end = "bootconfig"):
            '''
            This command read all 16 registers bytes by bytes starting by
            the registers 0x0Ah
            '''
            end = self.__reg_addr[end]
            pos_end = [pos for pos, reg in enumerate(self.__read_order) if  reg == end][0] + 1

            regs_values = self.__i2c.read_block((self.__registers[0x02] >> 8), pos_end * 2)
            for i, r in enumerate(self.__read_order[:pos_end]):
                self.__registers[r] = (regs_values[2*i] << 8) + regs_values[2*i+1]

               
        def write(self, end = "all"):
            '''
            This method write the registers 0x02 to addr(end), if end
            is not defined it goes to the addr of the highest register
            modified since the lase write
            '''
            end = self.__update_regs if end == "all" else self.__reg_addr[end]

            pos_end = [pos for pos, reg in enumerate(self.__read_order) if  reg == end][0] + 1
        
            regs_values = [0]*len(self.__write_order[:pos_end])*2

            for i, r in enumerate(self.__write_order[:pos_end]):
                regs_values[2*i    ] = self.__registers[r] >> 8
                regs_values[2*i + 1] = self.__registers[r] & 0x00FF
            self.__i2c.write_block(regs_values[0], regs_values[1:])
            self.__update_regs = 0x02


       
        def __str__(self):
            pn    = self.get("pn")
            mfgid = self.get("mfgid")
            dev_str = "Device: {0} by {1}".format("Si4702/03" if pn == 0x01 else "unknow",
                                                  "Silicon Laboratories" if mfgid == 0x242 else "unknow")
            rev      = self.get("rev")
            dev      = self.get("dev")
            firmware = self.get("firmware")
            chip_str = "Chip: {0}{1}{2} ({3})".format("Si4703" if dev & 0x8 else "Si4702",
                                                      "C" if rev == 0x04 else "A/B",
                                                      firmware,
                                                      "off" if firmware == 0 else "on")
            registers_str = "\n".join(["Registers:"] + [" - {0:<11}(0x{1:02X}) = 0x{2:04X}".format(self.__get_name(a+2), a+2, v)
                                       for a, v in enumerate(self.__registers[2:])])

            return "\n".join([dev_str, chip_str, registers_str])

        def __get_name(self, reg_addr):
            return [name for name, reg in self.__reg_addr.iteritems() if  reg == reg_addr][0]

        __registers = array.array('H', [0] * 16)

        __read_order  =  range(10, 16) + range(0, 10)
        __write_order =  range(2, 9)

        # Registers
        __reg_addr = { "deviceid"  : 0x00,
                       "chipid"    : 0x01,
                       "powercfg"  : 0x02,
                       "channel"   : 0x03,
                       "sysconfig1": 0x04,
                       "sysconfig2": 0x05,
                       "sysconfig3": 0x06,
                       "test1"     : 0x07,
                       "test2"     : 0x08,
                       "bootconfig": 0x09,
                       "statusrssi": 0x0A,
                       "readchan"  : 0x0B,
                       "rdsa"      : 0x0C,
                       "rdsb"      : 0x0D,
                       "rdsc"      : 0x0E,
                       "rdsd"      : 0x0F, }

        # http://www.sparkfun.com/datasheets/BreakoutBoards/Si4702-03-C19-1.pdf page 22
        __bits = { 
            # Register 0x00 Device ID
            "pn"      : BitsInfo("deviceid"  , 12, 0x000F),
            "mfgid"   : BitsInfo("deviceid"  ,  0, 0x0FFF),
            "rev"     : BitsInfo("chipid"    , 10, 0x003F),
            # Register 0x01 Chip ID
            "dev"     : BitsInfo("chipid"    ,  6, 0x000F),
            "firmware": BitsInfo("chipid"    ,  0, 0x003F),
            # Register 0x02 Power Configuration
            "dsmute"  : BitsInfo("powercfg"  , 15, 0x0001),
            "dmute"   : BitsInfo("powercfg"  , 14, 0x0001),
            "mono"    : BitsInfo("powercfg"  , 13, 0x0001),
            "rdsml"   : BitsInfo("powercfg"  , 11, 0x0001),
            "skmode"  : BitsInfo("powercfg"  , 10, 0x0001),
            "seekup"  : BitsInfo("powercfg"  ,  9, 0x0001),
            "seek"    : BitsInfo("powercfg"  ,  8, 0x0001),
            "disable" : BitsInfo("powercfg"  ,  6, 0x0001), 
            "enable"  : BitsInfo("powercfg"  ,  0, 0x0001),
            # Register 0x03 Channel
            "tune"    : BitsInfo("channel"   , 15, 0x0001),
            "channel" : BitsInfo("channel"   ,  0, 0x03FF),
            # Register 0x04 System configuration 1
            "rdsien"  : BitsInfo("sysconfig1", 15, 0x0001),
            "stcien"  : BitsInfo("sysconfig1", 14, 0x0001),
            "rds"     : BitsInfo("sysconfig1", 12, 0x0001),
            "de"      : BitsInfo("sysconfig1", 11, 0x0001),
            "abcd"    : BitsInfo("sysconfig1", 10, 0x0001),
            "blndadj" : BitsInfo("sysconfig1",  6, 0x0003),
            "gpio1"   : BitsInfo("sysconfig1",  4, 0x0003),
            "gpio2"   : BitsInfo("sysconfig1",  2, 0x0003),
            "gpio3"   : BitsInfo("sysconfig1",  0, 0x0003),
            # Register 0x05 System configuration 2
            "seekth"  : BitsInfo("sysconfig2",  8, 0x00FF),
            "band"    : BitsInfo("sysconfig2",  6, 0x0003),
            "space"   : BitsInfo("sysconfig2",  4, 0x0003),
            "volume"  : BitsInfo("sysconfig2",  0, 0x000F),
            # Register 0x06 System configuration 2
            "smuter"  : BitsInfo("sysconfig3", 14, 0x0003),
            "smutea"  : BitsInfo("sysconfig3", 12, 0x0003),
            "volext"  : BitsInfo("sysconfig3",  8, 0x0001),
            "sksnr"   : BitsInfo("sysconfig3",  4, 0x000F),
            "skcnt"   : BitsInfo("sysconfig3",  0, 0x000F),
            # Register 0x07 Test 1
            "xoscen"  : BitsInfo("test1"     , 15, 0x0001),
            "ahizen"  : BitsInfo("test1"     , 14, 0x0001),
            # Register 0x08 Test 2
            # --- Reserved ----
            # Register 0x09 Boot configuration
            # --- Reserved ----
            # Register 0x0A Status RSSI
            "rdsr"    : BitsInfo("statusrssi", 15, 0x0001),
            "stc"     : BitsInfo("statusrssi", 14, 0x0001),
            "sfbl"    : BitsInfo("statusrssi", 13, 0x0001),
            "afcrl"   : BitsInfo("statusrssi", 12, 0x0001),
            "rdss"    : BitsInfo("statusrssi", 11, 0x0001),
            "blera"   : BitsInfo("statusrssi",  9, 0x0003),
            "st"      : BitsInfo("statusrssi",  8, 0x0001),
            "rssi"    : BitsInfo("statusrssi",  0, 0x00FF),
            # Register 0x0B Status Read channel
            "blerb"   : BitsInfo("readchan"  , 14, 0x0003),
            "blerc"   : BitsInfo("readchan"  , 12, 0x0003),
            "blerd"   : BitsInfo("readchan"  , 10, 0x0003),
            "readchan": BitsInfo("readchan"  ,  0, 0x03FF),
            # Register 0x0C RDSA
            "rdsa"    : BitsInfo("rdsa"      ,  0, 0xFFFF),
            # Register 0x0D RDSB
            "rdsb"    : BitsInfo("rdsb"      ,  0, 0xFFFF),
            # Register 0x0E RDSC
            "rdsc"    : BitsInfo("rdsc"      ,  0, 0xFFFF),
            # Register 0x0F RDSD
            "rdsd"    : BitsInfo("rdsd"      ,  0, 0xFFFF),
            }

    # --------------------------------------------------------------------------
    class Properties:
        def __init__(self, i2c):
            self.__i2c = i2c
            
        def get(self, prop):
            self.__i2c.write_block(0x08, [0,0,0,0, prop >> 8, prop & 0xF])
            val = self.__i2c.read_block(0x00, 3)
            print("0x{0:02X}{1:02X}{2:02X}".format(val[0], val[1], val[2]))
