from scapy.all import *
from icc.gsmpackets import *
from detector import Detector

class A5Detector(Detector):


    def handle_packet(self, data):
        p = GSMTap(data)
        if p.payload.name is 'LAPDm' and p.payload.payload.name is 'GSMAIFDTAP' and p.payload.payload.payload.name is 'CipherModeCommand':
                if p.payload.payload.payload.cipher_mode & 1 == 0:
                    self.update_rank(Detector.SUSPICIOUS * 10, 'A5/0 detected! NO ENCRYPTION USED!')
                else:
                    cipher = p.payload.payload.payload.cipher_mode >> 1
                    cipher = cipher & 15 # MASK cipher AND 00001111 to only use the first four bits
                    if cipher == 0:
                        self.update_rank(Detector.SUSPICIOUS, 'A5/1 detected')
                    elif cipher == 1:
                        self.update_rank(Detector.SUSPICIOUS, 'A5/2 detected')
                    elif cipher == 2:
                        self.update_rank(Detector.NOT_SUSPICIOUS, 'A5/3 detected')
                    elif cipher == 3:
                        self.update_rank(Detector.NOT_SUSPICIOUS, 'A5/4 detected')
                    elif cipher == 4:
                        self.update_rank(Detector.NOT_SUSPICIOUS, 'A5/5 detected')
                    elif cipher == 5:
                        self.update_rank(Detector.NOT_SUSPICIOUS, 'A5/6 detected')
                    elif cipher == 6:
                        self.update_rank(Detector.NOT_SUSPICIOUS, 'A5/7 detected')
                    else:
                        self.update_rank(Detector.UNKNOWN, 'cipher used %s:' % cipher)
