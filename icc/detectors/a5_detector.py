from scapy.all import *
from icc.gsmpackets import *
from detector import Detector

class A5Detector(Detector):


    def handle_packet(self, data):
        p = GSMTap(data)
        if p.payload.name is 'LAPDm' and p.payload.payload.name is 'GSMAIFDTAP' and p.payload.payload.payload.name is 'CipherModeCommand':
                if p.payload.payload.payload.cipher_mode & 1 != 0:
                    self.update_s_rank(Detector.SUSPICIOUS*10)
                    self.comment = 'A5/0 detected! NO ENCRYPTION USED!'
                else:
                    cipher = p.payload.payload.payload.cipher_mode >> 1
                    cipher = cipher & 15 # MASK cipher AND 00001111 to only use the first four bits
                    if cipher == 0:
                        self.update_s_rank(Detector.SUSPICIOUS)
                        self.comment = 'A5/1 detected'
                    elif cipher == 1:
                        self.update_s_rank(Detector.SUSPICIOUS)
                        self.comment = 'A5/2 detected'
                    elif cipher == 2:
                        self.comment = 'A5/3 detected'
                        self.update_s_rank(Detector.NOT_SUSPICIOUS)
                    elif cipher == 3:
                        self.comment = 'A5/4 detected'
                        self.update_s_rank(Detector.NOT_SUSPICIOUS)
                    elif cipher == 4:
                        self.comment = 'A5/5 detected'
                        self.update_s_rank(Detector.NOT_SUSPICIOUS)
                    elif cipher == 5:
                        self.comment = 'A5/6 detected'
                        self.update_s_rank(Detector.NOT_SUSPICIOUS)
                    elif cipher == 6:
                        self.comment = 'A5/7 detected'
                        self.update_s_rank(Detector.NOT_SUSPICIOUS)
                    else:
                        self.update_s_rank(Detector.UNKNOWN)
                        self.comment = 'cipher used %s:' % cipher
        else:
                if self.comment is '' or self.comment is None:
                    self.comment = 'No enough information found.'
                    self.update_s_rank(Detector.UNKNOWN)
