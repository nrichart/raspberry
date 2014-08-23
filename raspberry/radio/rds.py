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

__all__ = [ "RDS" ]

import array
from sets import Set

class RDS:
    __pty = 0
    __tp = 0
    __pi = 0
    __reg = ['']*8
    __radio_text = ['']*64

    __text_ab = -1;

    __static_pty = True
    __compressed = False
    __stereo     = True
    __artificial_head = False

    __seen_groups = Set()

    UNKNOWN = 0
    EUROPE  = 1
    USA     = 2

    def __init__(self, pi, region = UNKNOWN):
        self.__pi = pi
        self.__region = region

    def __str__(self):
        msg = ["RDS: "]
        msg += [ " - PI : {0:X}{1}".format(self.__pi,
                                           " ({0})".format(self.__stations[self.__pi] if self.__pi in self.__stations else "")) ]
        msg += [ " - pty: {0}".format(self.__pty,
                                      " ({0})".format(self.__ptys[self.__region][self.__pty])) ]
        msg += [ " - reg: {0}".format("".join(self.__reg)) ]
        msg += [ " - text: {0}".format("".join(self.__radio_text)) ]
        msg += [ " - d3: {0}".format("static" if self.__static_pty else "not static") ]
        msg += [ " - d2: {0}".format("compressed" if self.__compressed else "uncompressed" ) ]
        msg += [ " - d0: {0}".format("stereo" if self.__stereo else "mono") ]
        msg += [ " - seen groups: {0}".format(self.__seen_groups) ]

        return "\n".join(msg)

    def decode(self, b, c, chwc, d, chwd):
        self.__pty = (b >>  5) & 0xF
        self.__tp  = (b >> 10) & 0x1

        group_type = (b >> 12) & 0xF
        b0         = (b >> 11) & 0x1
        
        if chwd < 3:
            if b0 == 0: # Version A
                if chwc < 3:
                    self.__decodeBlock34(group_type, b & 0x1F, c, d)
            else: # Verison B
                self.__decodeBlock4(group_type, b & 0x1F, d)

        self.__seen_groups.add(group_type)

    def __decodeBlock4(self, group, b, d):
        if group == 0:
            self.__decode0(b, d)
        if group == 2:
            self.__decode2(b, [d >> 4, d & 0xF])

    def __decodeBlock34(self, group, b, c, d):
        if group == 0:
            self.__decode0(b, d)
        if group == 2:
            self.__decode2(b, [c >> 8, c & 0xFF, d >> 8, d & 0xFF])

    def __decode0(self, b, d):
        di = (b >> 3) & 0x1
        c  = b & 0x3
        self.__decodeDI(di, c)
        self.__reg[2*c    ] = chr((d >> 8) & 0xFF)
        self.__reg[2*c + 1] = chr(d & 0xFF)

    def __decode2(self, b, chars):
        c = b & 0xF
        t_ab = b >> 4

        if not self.__text_ab == t_ab:
            self.__radio_text = [''] * 64
            self.__text_ab = t_ab

        for i, ch in enumerate(chars):
            self.__radio_text[len(chars) * c + i] = chr(ch)


    def __decodeDI(self, di, c):
        if c == 0:   # d3
            self.__static_pty = (di == 0)
        elif c == 1: # d2
            self.__compressed = (di == 1)
        elif c == 2: # d1
            self.__artificial_head = (di == 1)
        else:        # d0
            self.__stereo = (di == 1)

    __stations = { 0xF832: "La Radio Plus" }

    # Program types
    __ptys = { UNKNOWN: [""]*32,
               EUROPE:  [""        , "News"    , "Affairs" , "Info"    ,
                         "Sport"   , "Educate" , "Drama"   , "Culture" ,
                         "Science" , "Varied"  , "Pop M"   , "Rock M"  ,
                         "Easy M"  , "Light M" , "Classics", "Other M" ,
                         "Weather" , "Finance" , "Children", "Social"  ,
                         "Religion", "Phone In", "Travel"  , "Leisure" ,
                         "Jazz"    , "Country" , "Nation M", "Oldies"  ,
                         "Folk M"  , "Document", "TEST"    , "Alarm"   ],
               USA:     [""        , "News"    , "Inform"  , "Sports"  ,
                         "Talk"    , "Rock"    , "Cls_Rock", "Adlt_Hit",
                         "Soft_Rck", "Top_40"  , "Country" , "Oldies"  ,
                         "Soft"    , "Nostalga", "Jazz"    , "Classicl",
                         "R_&_B"   , "Soft_R&B", "Language", "Rel_Musc",
                         "Rel_Talk", "Persnlty", "Public"  , "College" ,
                         ""        , "Weather" , "Test"    , "ALERT !" ] }
