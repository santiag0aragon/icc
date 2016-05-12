from gnuradio import blocks
from gnuradio import gr
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.filter import pfb
from math import pi
from optparse import OptionParser

import grgsm
import numpy
import os
import osmosdr
import pmt
import time
import datetime
import random
from multiprocessing import Process

from database import *
from models import *
from analyzer import Analyzer
from detector_manager import DetectorManager
from scanner import scan
from cellinfochecks import *

class Runner():
    def __init__(self, bands, sample_rate, ppm, gain, speed, rec_time_sec):
        self.bands = bands
        self.sample_rate = sample_rate
        self.ppm = ppm
        self.gain = gain
        self.speed = speed
        self.scan_id = None
        self.rec_time_sec = rec_time_sec

    def start(self, analyze=True, detection=False):
        db_session = session_class()
        found = self.doScan()
        self.doCellInfoChecks(found)
        random.shuffle(found)
        for ch in found:
            cellobs = CellObservation(freq=ch.freq, lac=ch.lac, mnc=ch.mnc, mcc=ch.mcc, arfcn=ch.arfcn, cid=ch.cid, scan_id=self.scan_id, power=ch.power)
            db_session.add(cellobs)
            db_session.commit()
            if analyze:
                self.analyze(cellobs.id, ch, detection=detection)

    def doCellInfoChecks(self, channel_infos=[]):
        tic(channel_infos)
        neighbours(channel_infos)

    def analyze(self, cellobs_id, ch, detection=True):
        print "analyzing"
        db_session = session_class()
        cellscan = CellTowerScan(cellobservation_id=cellobs_id, sample_rate=self.sample_rate, rec_time_sec=self.rec_time_sec, timestamp=datetime.datetime.now())
        db_session.add(cellscan)
        db_session.commit()
        udp_port = 2333
        if detection:
            detector_man = DetectorManager(udp_port=udp_port)
            proc = Process(target=detector_man.start)
            proc.start()
            analyzer = Analyzer(gain=self.gain, samp_rate=self.sample_rate,
                                ppm=self.ppm, arfcn=ch.arfcn, capture_id=cellscan.getCaptureFileName(),
                                udp_ports=[udp_port], rec_length=self.rec_time_sec, max_timeslot=2,
                                verbose=False, test=False)
            analyzer.start()
            analyzer.wait()
            analyzer.stop()
            print "analyzer stopped"
            #detector_man.stop()
            print "detector stopping..."

            proc.terminate()
            print "detector stopped"
        else:
            analyzer = Analyzer(gain=self.gain, samp_rate=self.sample_rate,
                                ppm=self.ppm, arfcn=ch.arfcn, capture_id=cellscan.getCaptureFileName(),
                                udp_ports=[udp_port], rec_length=self.rec_time_sec, max_timeslot=2,
                                verbose=False, test=True)
            analyzer.start()
            analyzer.wait()
            analyzer.stop()
            print "analyzer stopped"


    def doScan(self):
        """
        Runs the scanner.
        Returns a list of cell towers

        """
        db_session = session_class()
        scan_obj = Scan(timestamp=datetime.datetime.now(), bands=','.join(self.bands))
        db_session.add(scan_obj)
        db_session.commit()
        self.scan_id = scan_obj.id
        return scan(bands=self.bands, sample_rate=self.sample_rate, ppm=self.ppm, gain=self.gain, speed=self.speed)

if __name__ == "__main__":
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    bands_list = ", ".join(grgsm.arfcn.get_bands())
    parser.add_option("-b", "--band", dest="band", default="900M-Bands",
                      help="Specify the GSM band for the frequency.\nAvailable bands are: " + bands_list)
    parser.add_option("-s", "--samp-rate", dest="samp_rate", type="float", default=2e6,
        help="Set sample rate [default=%default] - allowed values even_number*0.2e6")
    parser.add_option("-p", "--ppm", dest="ppm", type="intx", default=0,
        help="Set frequency correction in ppm [default=%default]")
    parser.add_option("-g", "--gain", dest="gain", type="eng_float", default=24.0,
        help="Set gain [default=%default]")
    parser.add_option("", "--args", dest="args", type="string", default="",
        help="Set device arguments [default=%default]")
    parser.add_option("--speed", dest="speed", type="intx", default=4,
        help="Scan speed [default=%default]. Value range 0-5.")
    parser.add_option("-v", "--verbose", action="store_true",
                      help="If set, verbose information output is printed: ccch configuration, cell ARFCN's, neighbor ARFCN's")

    (options, args) = parser.parse_args()

    if options.band is not "900M-Bands":
        if options.band not in grgsm.arfcn.get_bands():
            parser.error("Invalid GSM band\n")

    if options.speed < 0 or options.speed > 5:
        parser.error("Invalid scan speed.\n")

    if (options.samp_rate / 0.2e6) % 2 != 0:
        parser.error("Invalid sample rate. Sample rate must be an even numer * 0.2e6")
    channels_num = int(options.samp_rate/0.2e6)
    if options.band is "900M-Bands":
        to_scan = ['P-GSM',
                   'E-GSM',
                   'R-GSM',
                   #'GSM450',
                   #'GSM480',
                   #'GSM850',  Nothing found
                   #'DCS1800', #BTS found with kal
                   #'PCS1900', #Nothing interesting
                    ]
    else:
        to_scan = [options.band]

    print "GSM bands to be scanned:\n"
    print "\t", "\n\t".join(to_scan)

    #Add scan to database
    Base.metadata.create_all(engine)
    runner = Runner(bands=to_scan, sample_rate=options.samp_rate, ppm=options.ppm, gain=options.gain, speed=options.speed, rec_time_sec=10)
    runner.start(analyze=False)
