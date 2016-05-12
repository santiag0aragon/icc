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
from multiprocessing import Process
import click

from database import *
from models import *
from analyzer import Analyzer
from detector_manager import DetectorManager
from scanner import scan as sscan
from cellinfochecks import *
from aux.lat_log_utils import parse_dms
class Runner():
    def __init__(self, bands, sample_rate, ppm, gain, speed, rec_time_sec, current_location):
        self.bands = bands
        self.sample_rate = sample_rate
        self.ppm = ppm
        self.gain = gain
        self.speed = speed
        self.scan_id = None
        self.rec_time_sec = rec_time_sec

    def start(self, current_location, analyze=True, detection=False):
        db_session = session_class()
        found = self.doScan()
        self.doCellInfoChecks(found, current_location)
        for ch in found:
            cellobs = CellObservation(freq=ch.freq, lac=ch.lac, mnc=ch.mnc, mcc=ch.mcc, arfcn=ch.arfcn, cid=ch.cid, scan_id=self.scan_id, power=ch.power)
            db_session.add(cellobs)
            db_session.commit()
            if analyze:
                self.analyze(cellobs.id, ch, current_location, detection=detection)

    def doCellInfoChecks(self, current_location, channel_infos=[]):
        loc = parse_dms(current_location)
        lat = loc[0]
        lon = loc[1]
        tic(channel_infos,lat,lon)
        neighbours(channel_infos)

    def analyze(self, cellobs_id, ch, current_location, detection=True):
        print "analyzing"
        db_session = session_class()
        cellscan = CellTowerScan(cellobservation_id=cellobs_id, sample_rate=self.sample_rate, rec_time_sec=self.rec_time_sec, timestamp=datetime.datetime.now())
        db_session.add(cellscan)
        db_session.commit()
        udp_port = 2333
        if detection:
            detector_man = DetectorManager(udp_port=udp_port)
            proc = Process(target=detector_man.start)
            proc.start(current_location)
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
        return sscan(bands=self.bands, sample_rate=self.sample_rate, ppm=self.ppm, gain=self.gain, speed=self.speed)

@click.group()
@click.option('--ppm', '-p', default=0)
@click.option('--samplerate', '-s', default=2e6, type=float)
@click.option('--gain', '-g', type=float, default=30.0)
@click.option('--speed', '-s', type=int, default=4)
@click.pass_context
def cli(ctx, samplerate, ppm, gain, speed):
    if speed < 0 or speed > 5:
        print "Invalid scan speed.\n"
        return

    if (samplerate / 0.2e6) % 2 != 0:
        print "Invalid sample rate. Sample rate must be an even numer * 0.2e6"
        return

    ctx.obj['samplerate'] = samplerate
    ctx.obj['ppm'] = ppm
    ctx.obj['gain'] = gain
    ctx.obj['speed'] = speed

@click.command()
@click.option('--band', '-b', default="900M-Bands")
@click.option('--rec_time_sec', '-r', default=10)
@click.option('--analyze' , '-a', is_flag=True)
@click.pass_context
def scan(ctx, band, rec_time_sec, analyze):
    if band != "900M-Bands":
        if band not in grgsm.arfcn.get_bands():
            print "Invalid GSM band\n"
            return

    if band == "900M-Bands":
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
        to_scan = [band]



    print "GSM bands to be scanned:\n"
    print "\t", "\n\t".join(to_scan)

    args=ctx.obj

    #Add scan to database
    Base.metadata.create_all(engine)
    runner = Runner(bands=to_scan, sample_rate=args['samplerate'], ppm=args['ppm'], gain=args['gain'], speed=args['speed'], rec_time_sec=rec_time_sec, current_location)
    runner.start(analyze=analyze)

if __name__ == "__main__":
    cli.add_command(scan)
    cli(obj={})
