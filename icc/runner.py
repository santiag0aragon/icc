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
from a5_detector import A5Detector
from id_request_detector import IDRequestDetector
from cell_reselection_offset import CellReselectionOffsetDetector
from cellinfochecks import TowerRank

class Runner():
    def __init__(self, bands, sample_rate, ppm, gain, speed, rec_time_sec, current_location):
        self.bands = bands
        self.sample_rate = sample_rate
        self.ppm = ppm
        self.gain = gain
        self.speed = speed
        self.scan_id = None
        self.rec_time_sec = rec_time_sec

    def start(self, lat=None, lon=None, analyze=True, detection=True, mute=True):
        db_session = session_class()
        found = self.doScan(lat, lon)

        s_ranks = []

        random.shuffle(found)
        for ch in found:
            cellobs = CellObservation(freq=ch.freq, lac=ch.lac, mnc=ch.mnc, mcc=ch.mcc, arfcn=ch.arfcn, cid=ch.cid, scan_id=self.scan_id, power=ch.power)
            db_session.add(cellobs)
            db_session.commit()
            ch.cellobservation_id = cellobs.id
            if analyze:
                s_ranks += self.analyze(cellobs.id, detection=detection, mute=mute)
        scan_obj = db_session.query(Scan).filter(Scan.id == self.scan_id).one()
        #Perform offline checks
        if not (lat is None or lon is None):
            print "Performing offline checks..."
            s_ranks += self.doCellInfoChecks(lat, lon, found)

        #Merge the ranks for each detector on cellobs_id
        obs_ranks = {}
        for s in s_ranks:
            if s.cellobs_id in obs_ranks:
                obs_ranks[s.cellobs_id].append(s)
            else:
                obs_ranks[s.cellobs_id] = [s]

        for cellobs_id, ranks in obs_ranks.iteritems():
            try:
                co = db_session.query(CellObservation).filter(CellObservation.id == cellobs_id).one()
                co.s_rank = sum([x.s_rank for x in ranks])
                db_session.commit()
            except (NoResultFound, MultipleResultsFound) as e:
                print "cell observation not found in database during rank update"

        co_list = sorted(scan_obj.cell_observations, lambda x,y: x.s_rank - y.s_rank, reverse=True)
        #print the cell observation, and ask if a longer scan on one of the towers should be performed
        for index, co in enumerate(co_list):
            print "#{} | Rank: {} | ARFCN: {} | Freq: {} | LAC: {} | MCC: {} | MNC: {} | Power: {}".format(index, co.s_rank, co.arfcn, co.freq, co.lac, co.mcc, co.mnc, co.power)
            if co.id in obs_ranks:
                for tr in obs_ranks[co.id]:
                    print "--- Detector: {} | Rank: {} | Comment: {}".format(tr.detector, tr.s_rank, tr.comment)
        if len(co_list) > 0:
            while click.confirm('Do you want to perform an additional scan on one of the displayed towers?'):
                index = click.prompt('Enter the index of the cell tower you want to scan', type=int)
                rec_time = click.prompt('Enter the scan duration in seconds', type=int)
                self.rec_time_sec = rec_time
                self.analyze(co_list[index].id, detection=detection)

    def doCellInfoChecks(self, lat, lon, channel_infos=[]):
        ranks = tic(channel_infos,lat,lon) + neighbours(channel_infos)
        return ranks

    def analyze(self, cellobs_id, detection=True, mute=True):
        print "analyzing"
        s_ranks = []
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
            detector_man.addDetector(Detector('test_detector', cellobs_id))
            detector_man.addDetector(A5Detector('a5_detector', cellobs_id))
            detector_man.addDetector(IDRequestDetector('id_request_detector', cellobs_id))
            detector_man.addDetector(CellReselectionOffsetDetector('cell_reselection_offset_detector', cellobs_id))
            proc = Thread(target=detector_man.start)
            proc.start()
            if mute:
                # silence rtl_sdr output:
                # open 2 fds
                null_fds = [os.open(os.devnull, os.O_RDWR) for x in xrange(2)]
                # save the current file descriptors to a tuple
                save = os.dup(1), os.dup(2)
                # put /dev/null fds on 1 and 2
                os.dup2(null_fds[0], 1)
                os.dup2(null_fds[1], 2)
            analyzer = Analyzer(gain=self.gain, samp_rate=self.sample_rate,
                                ppm=self.ppm, arfcn=cell_obs.arfcn, capture_id=cellscan.getCaptureFileName(),
                                udp_ports=[udp_port], rec_length=self.rec_time_sec, max_timeslot=2,
                                verbose=False, test=False)
            analyzer.start()
            analyzer.wait()
            analyzer.stop()
            if mute:
                # restore file descriptors so we can print the results
                os.dup2(save[0], 1)
                os.dup2(save[1], 2)
                # close the temporary fds
                os.close(null_fds[0])
                os.close(null_fds[1])

            print "analyzer stopped"
            s_ranks = detector_man.stop()
            print "detector stopping..."

            proc.join()

            #proc.terminate()
            print "detector stopped"
            print s_ranks
            # for r in rankings:
            #     total_rank += r['s_rank']
            # cell_obs.s_rank = total_rank

        else:
            # silence rtl_sdr output:
            # open 2 fds
            null_fds = [os.open(os.devnull, os.O_RDWR) for x in xrange(2)]
            # save the current file descriptors to a tuple
            save = os.dup(1), os.dup(2)
            # put /dev/null fds on 1 and 2
            os.dup2(null_fds[0], 1)
            os.dup2(null_fds[1], 2)
            analyzer = Analyzer(gain=self.gain, samp_rate=self.sample_rate,
                                ppm=self.ppm, arfcn=cell_obs.arfcn, capture_id=cellscan.getCaptureFileName(),
                                udp_ports=[udp_port], rec_length=self.rec_time_sec, max_timeslot=2,
                                verbose=False, test=True)
            analyzer.start()
            analyzer.wait()
            analyzer.stop()
            # restore file descriptors so we can print the results
            os.dup2(save[0], 1)
            os.dup2(save[1], 2)
            # close the temporary fds
            os.close(null_fds[0])
            os.close(null_fds[1])
            print "analyzer stopped"

        return s_ranks


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

def listScans(limit, printscans):
    db_session = session_class()
    scans = db_session.query(Scan).order_by(desc(Scan.timestamp)).limit(limit).all()
    for s in scans:
        print "Scan# {} - {} - lat: {} lon: {}".format(s.timestamp, s.bands, s.latitude, s.longitude)
        for co in s.cell_observations:
            print "--- Cell tower observation# ARFCN: {} | Freq: {} | Susp. Rank: {} | LAC: {} | MCC: {} | MNC: {} | Power: {}".format(co.arfcn, co.freq, co.s_rank, co.lac, co.mcc, co.mnc, co.power)
            if printscans:
                for ts in co.celltowerscans:
                    print "------ Cell tower scan# {} | Rec. time: {} | UUID: {} | Samplerate: {}".format(ts.timestamp, ts.rec_time_sec, ts.id, ts.sample_rate)
                print ""
        print ""

def createDatabase():
    Base.metadata.create_all(engine)
