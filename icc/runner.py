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
from detectors.detector import Detector
from detectors.a5_detector import A5Detector
from detectors.id_request_detector import IDRequestDetector
from detectors.cell_reselection_offset import CellReselectionOffsetDetector
from detectors.cell_reselection_hysteresis import CellReselectionHysteresisDetector
from detectors.tic import TIC
from cellinfochecks import TowerRank
from icc.file_analyzer import FileAnalyzer

class Runner():
    def __init__(self, bands, sample_rate, ppm, gain, speed, rec_time_sec, current_location, store_capture):
        self.bands = bands
        self.sample_rate = sample_rate
        self.ppm = ppm
        self.gain = gain
        self.speed = speed
        self.scan_id = None
        self.rec_time_sec = rec_time_sec
        self.store_capture = store_capture

    def start(self, lat=None, lon=None, analyze=True, detection=True, mute=True):
        db_session = session_class()
        found = self.doScan(lat, lon)

        s_ranks = []

        random.shuffle(found)
        for i, ch in enumerate(found):
            cellobs = CellObservation(freq=ch.freq, lac=ch.lac, mnc=ch.mnc, mcc=ch.mcc, arfcn=ch.arfcn, cid=ch.cid, scan_id=self.scan_id, power=ch.power)
            if (self.store_capture):
                db_session.add(cellobs)
                db_session.commit()
                ch.cellobservation_id = cellobs.id
            else:
                ch.cellobservation_id = ch.id = i
            if analyze:
                s_ranks += self.analyze(cellobs, detection=detection, mute=mute)

        if self.store_capture:
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

        if self.store_capture:
            for cellobs_id, ranks in obs_ranks.iteritems():
                try:
                    co = db_session.query(CellObservation).filter(CellObservation.id == cellobs_id).one()
                    co.s_rank = sum([x.s_rank for x in ranks])
                    db_session.commit()
                except (NoResultFound, MultipleResultsFound) as e:
                    print "cell observation not found in database during rank update"

            co_list = sorted(scan_obj.cell_observations, lambda x,y: x.s_rank - y.s_rank, reverse=True)
        else:
            cell_observations = dict((v.cellobservation_id, v) for v in found)
            for cellobs_id, ranks in obs_ranks.iteritems():
                cell_observations[cellobs_id].s_rank = sum([x.s_rank for x in ranks])

            co_list = sorted(found, lambda x,y: x.s_rank - y.s_rank, reverse=True)


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
                s_ranks = self.analyze(co_list[index], detection=detection, lat=lat, lon=lon)
################# PRINTING RANK
                obs_ranks = {}
                for s in s_ranks:
                    if s.cellobs_id in obs_ranks:
                        obs_ranks[s.cellobs_id].append(s)
                    else:
                        obs_ranks[s.cellobs_id] = [s]

                co_list = sorted(scan_obj.cell_observations, lambda x,y: x.s_rank - y.s_rank, reverse=True)
                #print the cell observation, and ask if a longer scan on one of the towers should be performed
                for index, co in enumerate(co_list):
                    print "#{} | Rank: {} | ARFCN: {} | Freq: {} | LAC: {} | MCC: {} | MNC: {} | Power: {}".format(index, co.s_rank, co.arfcn, co.freq, co.lac, co.mcc, co.mnc, co.power)
                    if co.id in obs_ranks:
                        for tr in obs_ranks[co.id]:
                            print "--- Detector: {} | Rank: {} | Comment: {}".format(tr.detector, tr.s_rank, tr.comment)
#################
    def doCellInfoChecks(self, lat, lon, channel_infos=[]):
        ranks = tic(channel_infos,lat,lon) + lac(channel_infos) + neighbours(channel_infos)
        return ranks

    def analyze(self, cell_obs, detection=True, mute=True, lat=None, lon=None):
        print "analyzing"
        cellobs_id = cell_obs.id
        s_ranks = []
        cellscan = CellTowerScan(cellobservation_id=cellobs_id, sample_rate=self.sample_rate, rec_time_sec=self.rec_time_sec, timestamp=datetime.datetime.now())
        if self.store_capture:
            db_session = session_class()
            db_session.add(cellscan)
            db_session.commit()
        udp_port = 2333
        if detection:
            detector_man = DetectorManager(udp_port=udp_port)
            #detector_man.addDetector(Detector('test_detector', cellobs_id))
            detector_man.addDetector(A5Detector('a5_detector', cellobs_id))
            detector_man.addDetector(IDRequestDetector('id_request_detector', cellobs_id))
            detector_man.addDetector(CellReselectionOffsetDetector('cell_reselection_offset_detector', cellobs_id))
            detector_man.addDetector(CellReselectionHysteresisDetector('cell_reselection_offset_hysteresis', cellobs_id))
            detector_man.addDetector(TIC('tic', cellobs_id, lat, lon))
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
                                verbose=False, test=False, store_capture=self.store_capture)
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
            # print s_ranks
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
        if self.store_capture:
            db_session = session_class()
            scan_obj = Scan(timestamp=datetime.datetime.now(), bands=','.join(self.bands), latitude=lat, longitude=lon)
            db_session.add(scan_obj)
            db_session.commit()
            self.scan_id = scan_obj.id
        return sscan(bands=self.bands, sample_rate=self.sample_rate, ppm=self.ppm, gain=self.gain, speed=self.speed)

def offlineDetection(chan_mode, timeslot):
    db_session = session_class()
    scans = db_session.query(Scan).all()

    while click.confirm('Press y to continue...'):
        for index, scan in enumerate(scans):
            print "#{} | ID: {} | Timestamp: {} | Latitude: {} | Longitude: {}".format(index, scan.id, scan.timestamp.isoformat(), scan.latitude, scan.longitude)
        index = click.prompt('Enter the index of the scan', type=int)
        if not (index >= 0 and index < len(scans)):
            print "Invalid index specified..."
            continue
        current_scan = scans[index]
        co_list = sorted(current_scan.cell_observations, lambda x,y: x.s_rank - y.s_rank, reverse=True)
        #print the cell observation, and ask if a longer scan on one of the towers should be performed
        printed_scans = 0
        for i, co in enumerate(co_list):
            if len(co.celltowerscans) > 0:
                print "#{} | Rank: {} | ARFCN: {} | Freq: {} | LAC: {} | MCC: {} | MNC: {} | Power: {}".format(i, co.s_rank, co.arfcn, co.freq, co.lac, co.mcc, co.mnc, co.power)
                for i, cts in enumerate(co.celltowerscans):
                    print "--- #{} | ID: {} | Timestamp: {}".format(i, cts.id, cts.timestamp.isoformat())
                    printed_scans += 1
        if printed_scans == 0:
            print("The selected scan does not have any stored capture files in the database. Try another scan.")
            continue
        index2 = click.prompt('Enter the index of the cell tower observation', type=int)
        if not(index2 >= -1 and index2 < len(co_list)):
            print "Invalid cell tower observation index specified."
            continue
        
        if index2 >= 0:
            selected_obs = co_list[index2]
            index3 = click.prompt('Enter the index of the cell tower scan', type=int)
            if not (index3 >= 0 and index3 < len(selected_obs.celltowerscans)):
                print "Invalid tower scan index specified."
                continue
            selected_cts = selected_obs.celltowerscans[index3]
            
            s_ranks = run_detector(current_scan, selected_obs, selected_cts, chan_mode, timeslot)
            print_ranks(s_ranks, [selected_obs])
        else:
            s_ranks = []
            for co in co_list:
                for cts in co.celltowerscans:
                    s_ranks += run_detector(current_scan, co, cts, chan_mode, timeslot)
            print_ranks(s_ranks, co_list)

def run_detector(current_scan, selected_obs, selected_cts, chan_mode, timeslot):
    udp_port = 2333
    detector_man = DetectorManager(udp_port=udp_port)
    #detector_man.addDetector(Detector('test_detector', cellobs_id))
    detector_man.addDetector(A5Detector('a5_detector', selected_obs.id))
    detector_man.addDetector(IDRequestDetector('id_request_detector', selected_obs.id))
    detector_man.addDetector(CellReselectionOffsetDetector('cell_reselection_offset_detector', selected_obs.id))
    detector_man.addDetector(CellReselectionHysteresisDetector('cell_reselection_offset_hysteresis', selected_obs.id))
    detector_man.addDetector(TIC('tic', selected_obs.id, current_scan.latitude, current_scan.longitude))

    proc = Thread(target=detector_man.start)
    proc.start()

    print "Selected file: {}".format(selected_cts.getCaptureFileName())
    fa = FileAnalyzer(selected_cts.getCaptureFileName() +".cfile", selected_cts.sample_rate, selected_cts.cell_observation.arfcn, max_timeslot=timeslot, chan_mode=chan_mode, udp_port=udp_port, verbose=True)
    fa.start()
    fa.wait()
    fa.stop()
    print "analyzer stopped"
    s_ranks = detector_man.stop()
    print "detector stopping..."

    proc.join()

    #proc.terminate()
    print "detector stopped"
    return s_ranks

def print_ranks(s_ranks, observations):
    #print s_ranks
    obs_ranks = {}
    for s in s_ranks:
        if s.cellobs_id in obs_ranks:
            obs_ranks[s.cellobs_id].append(s)
        else:
            obs_ranks[s.cellobs_id] = [s]
    
    co_list = sorted(observations, lambda x,y: x.s_rank - y.s_rank, reverse=True)
    
    for i, selected_obs in enumerate(co_list):
        print "#{} | Rank: {} | ARFCN: {} | Freq: {} | LAC: {} | MCC: {} | MNC: {} | Power: {}".format(i, selected_obs.s_rank,
                                                                                                        selected_obs.arfcn, selected_obs.freq, selected_obs.lac,
                                                                                                        selected_obs.mcc, selected_obs.mnc, selected_obs.power)
        for tr in obs_ranks[selected_obs.id]:
            print "--- Detector: {} | Rank: {} | Comment: {}".format(tr.detector, tr.s_rank, tr.comment)


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
