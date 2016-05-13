# -*- coding: utf-8 -*-
import re
import math

from gps import *

def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
    if direction == 'S' or direction == 'W':
        dd *= -1
    return dd;

def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]

def parse_dms(dms):
    parts = re.split('[^\d\w]+', dms)
    lat = dms2dd(parts[0], parts[1], parts[2], parts[3])
    lng = dms2dd(parts[4], parts[5], parts[6], parts[7])

    return (lat, lng)

def getgps():
    gpsd = gps(mode=WATCH_ENABLE)
    while gpsd.fix.latitude == 0.:
        gpsd.next()

    return (gpsd.fix.latitude, gpsd.fix.longitude)
