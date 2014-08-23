#!/usr/bin/env python

import raspberry as rpi
import time

if __name__ == "__main__":
    fm = rpi.radio.SI470x(debug = True)
    fm.setChannel(93.0)
#    time.sleep(2)
#    fm.seek()
#    while not fm.hasRDS():
#        fm.seek()
#        time.sleep(0.4)
    poll_time = 10

    print(fm.status())
    while 1:
        fm.pollRDS()

#    while 1:
#        st = time.time()
#        print(fm.status())
#        t = time.time() - st
#        while t < poll_time:
#            t = time.time() - st
#            fm.pollRDS()
#        print("")
#        fm.seek(seek_rssi_threshold = 0xC, seek_snr_threshold = 0x4, seek_fm_counts = 0x4, timeout = 5)
