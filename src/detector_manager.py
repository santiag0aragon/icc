from detector import Detector
import socket

class DetectorManager():

    def __init__(self, udp_port):
        """
        Parameters:
        hooks = list of functions to call with the received frame as argument
        """
        self.udp_port = udp_port
        self.sock = None
        self.running = False
        self.detectors = []

    def addDetector(self, detector):
        print self.running
        if not isinstance(detector, Detector) or self.running is True:
            print "Could not add Detector to DetectorManager"
            return
        self.detectors.append(detector)

    def start(self):

        UDP_IP = "127.0.0.1"
        self.sock = socket.socket(socket.AF_INET, # Internet
        socket.SOCK_DGRAM) # UDP
        self.sock.bind((UDP_IP, self.udp_port))
        self.running = True
        print "detectormanager started"
        while self.running:
            data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
            for detector in self.detectors:
                detector.handle_packet(data)

    def stop(self):
        self.running = False
        self.sock.shutdown()
        for detector in self.detectors:
            detector.on_finish()
