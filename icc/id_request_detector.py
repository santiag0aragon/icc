import socket
from scapy.all import *
from gsmpackets import *
from multiprocessing import Process
from detector import Detector

class IDRequestDetector(Detector):

    def handle_packet(self, data):
        p = GSMTap(data)
        if p.payload.name is 'LAPDm' and p.payload.payload.name is 'GSMAIFDTAP' and p.payload.payload.payload.name is 'IdentityRequest':
                id_type = p.payload.payload.payload.id_type
                if id_type == 1:
                    # print 'IMSI request detected'
                    # TODO add a counter and find a threshold
                    self.update_s_rank(Detector.UNKNOWN)
