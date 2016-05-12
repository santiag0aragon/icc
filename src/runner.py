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
from threading import Thread
import click
from sqlalchemy import desc

from database import *
from models import *
from analyzer import Analyzer
from detector_manager import DetectorManager
from scanner import scan as sscan
from cellinfochecks import *
from aux.lat_log_utils import parse_dms
from detector import Detector

class Runner():
    def __init__(self, bands, sample_rate, ppm, gain, speed, rec_time_sec, current_location):
        self.bands = bands
        self.sample_rate = sample_rate
        self.ppm = ppm
        self.gain = gain
        self.speed = speed
        self.scan_id = None
        self.rec_time_sec = rec_time_sec

    def start(self, lat=None, lon=None, analyze=True, detection=True):
        db_session = session_class()
        found = self.doScan(lat, lon)
        rankings ={}
        if analyze and not (lat is None or lon is None):
            rankings.update(self.doCellInfoChecks(lat, lon, found))
        random.shuffle(found)
        for ch in found:
            cellobs = CellObservation(freq=ch.freq, lac=ch.lac, mnc=ch.mnc, mcc=ch.mcc, arfcn=ch.arfcn, cid=ch.cid, scan_id=self.scan_id, power=ch.power)
            db_session.add(cellobs)
            db_session.commit()
            if analyze:
                self.analyze(cellobs.id, detection=detection)

        scan_obj = db_session.query(Scan).filter(Scan.id == self.scan_id).one()
        co_list = sorted(scan_obj.cell_observations, lambda x,y: x.s_rank - y.s_rank)
        #print the cell observation, and ask if a longer scan on one of the towers should be performed
        for index, co in enumerate(co_list):
            print "#{} | Rank: {} | ARFCN: {} | Freq: {} | LAC: {} | MCC: {} | MNC: {} | Power: {}".format(index, co.s_rank, co.arfcn, co.freq, co.lac, co.mcc, co.mnc, co.power)

        while click.confirm('Do you want to perform an additional scan on one of the displayed towers?'):
            index = click.prompt('Enter the index of the cell tower you want to scan', type=int)
            rec_time = click.prompt('Enter the scan duration in seconds', type=int)
            self.rec_time_sec = rec_time
            self.analyze(co_list[index].id, detection=False)

    def doCellInfoChecks(self, lat, lon, channel_infos=[]):
        tic(channel_infos,lat,lon)
        neighbours(channel_infos)

    def analyze(self, cellobs_id, detection=True):
        print "analyzing"
        total_rank = 0
        db_session = session_class()
        try:
            cell_obs = db_session.query(CellObservation).filter(CellObservation.id == cellobs_id).one()
        except (NoResultFound, MultipleResultsFound):
            print "Could not find celltower observation for cell tower scan in database."
            return
        cellscan = CellTowerScan(cellobservation_id=cellobs_id, sample_rate=self.sample_rate, rec_time_sec=self.rec_time_sec, timestamp=datetime.datetime.now())
        db_session.add(cellscan)
        db_session.commit()
        udp_port = 2333
        if detection:
            detector_man = DetectorManager(udp_port=udp_port)
            detector_man.addDetector(Detector())
            proc = Thread(target=detector_man.start)
            proc.start()
            analyzer = Analyzer(gain=self.gain, samp_rate=self.sample_rate,
                                ppm=self.ppm, arfcn=cell_obs.arfcn, capture_id=cellscan.getCaptureFileName(),
                                udp_ports=[udp_port], rec_length=self.rec_time_sec, max_timeslot=2,
                                verbose=False, test=False)
            analyzer.start()
            analyzer.wait()
            analyzer.stop()
            print "analyzer stopped"
            rankings = detector_man.stop()
            print "detector stopping..."

            #proc.terminate()
            print "detector stopped"
            print rankings
            for r in rankings:
                total_rank += r['s_rank']
            cell_obs.s_rank = total_rank

        else:
            analyzer = Analyzer(gain=self.gain, samp_rate=self.sample_rate,
                                ppm=self.ppm, arfcn=cell_obs.arfcn, capture_id=cellscan.getCaptureFileName(),
                                udp_ports=[udp_port], rec_length=self.rec_time_sec, max_timeslot=2,
                                verbose=False, test=True)
            analyzer.start()
            analyzer.wait()
            analyzer.stop()
            print "analyzer stopped"


    def doScan(self, lat=None, lon=None):
        """
        Runs the scanner.
        Returns a list of cell towers
        """
        db_session = session_class()
        scan_obj = Scan(timestamp=datetime.datetime.now(), bands=','.join(self.bands), latitude=lat, longitude=lon)
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
@click.option('--detection' , '-d', is_flag=True)
@click.option('--location' , '-l', type=str, default='', prompt=True)
@click.pass_context
def scan(ctx, band, rec_time_sec, analyze, detection, location):
    """
    Note: if no location is specified, analysis of found towers is off
    :param detection: determines if druing analysis the packet based detectors are run
    """
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


    args=ctx.obj
    lat = None
    lon = None
    try:
        loc = parse_dms(location)
        lat = loc[0]
        lon = loc[1]
    except:
        print "Warning: no valid location specified. Cell tower consistency checks will be disabled in the analysis phase."


    print "GSM bands to be scanned:\n"
    print "\t", "\n\t".join(to_scan)

    #Add scan to database
    Base.metadata.create_all(engine)
    runner = Runner(bands=to_scan, sample_rate=args['samplerate'], ppm=args['ppm'], gain=args['gain'], speed=args['speed'], rec_time_sec=rec_time_sec, current_location=location)
    runner.start(lat, lon, analyze=analyze, detection=detection)

@click.command(help='Prints the saved scans')
@click.option('--limit', '-n', help='Limit the number of results returned', default=10)
@click.option('--printscans/--no-printscans', default=False)
def listScans(limit, printscans):
    db_session = session_class()
    scans = db_session.query(Scan).order_by(desc(Scan.timestamp)).limit(limit).all()
    for s in scans:
        print "Scan# {} - {} - lat: {} lon: {}".format(s.timestamp, s.bands, s.latitude, s.longitude)
        for co in s.cell_observations:
            print "--- Cell tower observation# ARFCN: {} | Freq: {} | Susp. Rank: {} | LAC: {} | MCC: {} | MNC: {} | Power: {}".format(co.arfcn, co.freq, co.s_rank, co.lac, co.mcc, co.mnc, co.power)
            if printscans:
                for ts in co.celltowerscans:
                    print "------ Cell tower scan# {} | Rec. time: {} | UUID: {}".format(ts.timestamp, ts.rec_time_sec, ts.id)
                print ""
        print ""
if __name__ == "__main__":
    cli.add_command(scan)
    cli.add_command(listScans)
    cli(obj={})
