#!/usr/bin/env python

import raspberry as rpi
import time
import curses

from curses.textpad import Textbox, rectangle
from raspberry.radio import SI470x
from curses import wrapper

fm = SI470x()
fm.setChannel(93.0)

def main(stdscr):

    stdscr.clear()
    win_f = curses.newwin(3, 24,  1, 1)
    win_r = curses.newwin(3, 24,  1, 45)
    win_rds = curses.newwin(3, 68,  4, 1)
    win_rds_pn = curses.newwin(3, 18,  1, 26)

    win_s = curses.newwin(1, 1, 0, 0)

    freq = fm.getChannel()
    new_freq = freq

    win_f.clear()
    curses.textpad.rectangle(win_f, 0, 0, 2, 22)
    win_f.addstr(1, 2, "Frequency: {0:.1f}MHz".format(freq))
    win_f.refresh()

    win_rds_pn.clear()
    curses.textpad.rectangle(win_rds_pn, 0,  0, 2, 16)
    win_rds_pn.addstr(1, 4, "12345678")
    win_rds_pn.refresh()


    win_s.nodelay(True)

    start = 0
    volume = 15

    while True:
        rds = fm.pollRDS()

        c = win_s.getch()
        if c == ord('q'):
            break
        elif c == ord('+'):
            fm.seek(direction = SI470x.UP)
            new_freq = fm.getChannel()
        elif c == ord('-'):
            fm.seek(direction = SI470x.DOWN)
            new_freq = fm.getChannel()
        elif c == ord('2'):
            volume += 1
            fm.setVolume(volume)
        elif c == ord('8'):
            volume -= 1
            fm.setVolume(volume)
        elif c == ord('5'):
            fm.mute()


        if new_freq != freq:
            freq = new_freq
            win_f.clear()
            curses.textpad.rectangle(win_f, 0, 0, 2, 22)
            win_f.addstr(1, 2, "Frequency: {0:.1f}MHz".format(freq))
            win_f.refresh()

        if  time.time() - start > 3:
            win_r.clear()
            curses.textpad.rectangle(win_r, 0, 0, 2, 22)
            win_r.addstr(1, 2, "RSSI: {0: 2d}/75dBuV".format(fm.getRSSI()))
            win_r.refresh()

            win_rds.clear()
            curses.textpad.rectangle(win_rds, 0,  0, 2, 66)
            win_rds_pn.clear()
            curses.textpad.rectangle(win_rds_pn, 0,  0, 2, 16)
            if not rds == None:
                win_rds_pn.addstr(1,  4, rds.getProgramName())
                win_rds.addstr(1,  2, rds.getRadioText())
            else:
                win_rds.addstr(1,  30, "No RDS")

            win_rds_pn.refresh()
            win_rds.refresh()
        
            start = time.time()

wrapper(main)
