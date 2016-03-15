import socket
from scapy.all import *

class Parser:

    def __init__(self, udp_port, hooks=[]):
        """
        Parameters:
        hooks = list of functions to call with the received frame as argument
        """
        self.udp_port = udp_port
        self.sock = None
        self.hooks = hooks

    def listen(self):

        UDP_IP = "127.0.0.1"
        self.sock = socket.socket(socket.AF_INET, # Internet
        socket.SOCK_DGRAM) # UDP
        self.sock.bind((UDP_IP, self.udp_port))

        while True:
            data, addr = self.sock.recvfrom(39) # buffer size is 1024 bytes

            print ':'.join(x.encode('hex') for x in data)
            #print '%x', data
            #print "received message:", data
            handle_packet(data)
            for hook in self.hooks:
                hook(data)

    def handle_packet(data):
        pass

class GSMTap(Packet):
    name = "GSMTap header"
    fields_desc = [XByteField("version", 0),
                   XByteField("header_length", 0),
                   XByteField("payload_type", 0),
                   XByteField("timeslot", 0, ),
                   XShortField("arfcn", 0),
                   XByteField("signal_level", 0), #Returns wrong value, should be signed
                   XByteField("signal_noise_ratio", 0),
                   XIntField("gsm_frame_number", 0),
                   XByteField("channel_type", 0),
                   XByteField("antenna_number", 0),
                   XByteField("sub_slot", 0)]

    def guess_payload_class(self, payload):
        if self.channel_type == 2:
            return CCCHCommon
        else:
            return Raw

class CCCHCommon(Packet):
    name = "CCCHCommon"
    fields_desc = [XShortField("junk1", 0),
                   XByteField("message_type", 0)]

    def guess_payload_class(self, payload):
        if self.message_type == 2:
            return CCCHCommon
        else:
            return Raw

class ImmediateAssignment(Packet):
    name = "ImmediateAssignment"
    fields_desc = [XByteField("junk", 2),
                   XByteField("packet_channel_description", 6) #Extract indivual bits for detailed information
                  ]


if __name__ == '__main__':
        #parser = Parser(4729)
        #parser.listen()
        p = GSMTap("02 04 01 00 03 f9 e1 00 00 06 07 ba 02 00 08 00 2d 06 3f 10 0e 83 f9 7e 54 48 01 00 c6 94 aa 34 2b 2b 2b 2b 2b 2b 2b".replace(' ', '').decode('hex'))
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
        print type(p.payload)
