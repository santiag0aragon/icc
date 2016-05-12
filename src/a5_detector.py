import socket
from scapy.all import *
from gsmpackets import *
from multiprocessing import Process
from detector import Detector

class A5Detector(Detector):

    def __init__(self, udp_port=4729):
        """
        Parameters:
        """
        self.udp_port = udp_port
        self.sock = None
        self.running = False
        self.process = None

    def listen(self):

        UDP_IP = "127.0.0.1"
        self.sock = socket.socket(socket.AF_INET, # Internet
        socket.SOCK_DGRAM) # UDP
        self.sock.bind((UDP_IP, self.udp_port))

        while True:
            data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
            self.handle_packet(data)

    def handle_packet(self, data):
        p = GSMTap(data)
        if p.payload.name is 'LAPDm' and p.payload.payload.name is 'GSMAIFDTAP' and p.payload.payload.payload.name is 'CipherModeCommand':
                cipher = p.payload.payload.payload.cipher_mode >> 1
                if cipher == 0:
                    print 'A5/1 detected'
                elif cipher == 2:
                    print 'A5/3 detected'
                else:
                    print 'cipher used %s:' % cipher

        # print ':'.join(x.encode('hex') for x in data)

    def on_finish():
        pass

    def start(self):
        self.process = Process(target=self.listen)
        self.process.start()

    def stop(self):
        if not self.process is None:
            self.process.terminate()


