from scapy.all import *

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
                   XByteField("sub_slot", 0),
                   XByteField("end_junk", 0)]

    def guess_payload_class(self, payload):
        if self.channel_type == 2:
            return CCCHCommon
        elif self.channel_type == 8:
            return LAPDm
        else:
            return Raw


class LAPDm(Packet):
    name = "LAPDm"
    fields_desc = [XByteField("address_field", 0),
                   XByteField("control_field", 0),
                   XByteField("len_field", 0)]

    def guess_payload_class(self, payload):
        if self.control_field == 100:
            return GSMAIFDTAP
        elif self.control_field == 32:
            return
        else:
            return Raw


class GSMAIFDTAP(Packet):
    name = "GSMAIFDTAP"
    fields_desc = [XByteField("rrmm", 0),
                   XByteField("message_type", 0)]

    def guess_payload_class(self, payload):
        if self.message_type == 53:
            return CipherModeCommand
        elif self.control_field == 24:
            return
        else:
            return Raw


class CipherModeCommand(Packet):
    name = "CipherModeCommand"
    fields_desc = [XByteField("cipher_mode", 0)]


class IdentityRequest(Packet):
    name = "IdentityRequest"
    fields_desc = [XByteField("id_type", 0)]


class CCCHCommon(Packet):
    name = "CCCHCommon"
    fields_desc = [XShortField("junk1", 0),
                   XByteField("message_type", 0)]

    def guess_payload_class(self, payload):
        if self.message_type == 63:
            return ImmediateAssignment
        else:
            return Raw


class ImmediateAssignment(Packet):
    name = "ImmediateAssignment"
    fields_desc = [XByteField("junk", 2),
                   XByteField("packet_channel_description", 6) #Extract indivual bits for detailed information
                  ]
