import socket
from scapy.all import *
from gsmpackets import *
from multiprocessing import Process
from aux import TowerRank

class Detector:
    SUSPICIOUS = 2
    UNKNOWN = 1
    NOT_SUSPICIOUS = 0
    def __init__(self, name, cellobs_id):
        """
        Parameters:
        """
        self.s_rank = 0
        self.name = name
        self.comment = ""
        self.cellobs_id = cellobs_id

    def update_s_rank(self, new_s_rank):
        self.s_rank = new_s_rank if new_s_rank > self.s_rank else self.s_rank

    def handle_packet(self, data):
        print ':'.join(x.encode('hex') for x in data)

    def on_finish(self):
        return TowerRank(self.s_rank, self.name, self.comment, self.cellobs_id)

    def start(self):
        self.process = Process(target=self.listen)
        self.process.start()

    def stop(self):
        if not self.process is None:
            self.process.terminate()

if __name__ == '__main__':
        #parser = Parser(4729)
        #parser.listen()
        im_as_packet_dump = "02 04 01 00 03 f9 e2 00 00 1e 45 1d 02 00 04 00 2d 06 3f 10 0e 83 f9 7a c0 c5 02 00 c6 94 e0 a4 2b 2b 2b 2b 2b 2b 2b"
        #p = GSMTap("02 04 01 00 03 f9 e1 00 00 06 07 ba 02 00 08 00 2d 06 3f 10 0e 83 f9 7e 54 48 01 00 c6 94 aa 34 2b 2b 2b 2b 2b 2b 2b".replace(' ', '').decode('hex'))
        p = GSMTap(im_as_packet_dump.replace(' ', '').decode('hex'))
        print p.version
        print p.header_length
        print p.payload_type
        print p.timeslot
        print p.arfcn
        print p.signal_level
        print p.signal_noise_ratio
        print p.gsm_frame_number
        print p.channel_type
        print p.antenna_number
        print p.sub_slot
        print p.payload.message_type
        print hexdump(p)
        print type(p.payload)
        print hexdump(p.payload)
        #print p.payload.encode('hex')
        print(type(p.payload.payload))
