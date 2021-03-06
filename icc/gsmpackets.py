from scapy.all import *


class GSMTap(Packet):
    name = "GSMTap header"
    fields_desc = [XByteField("version", 0),
                   XByteField("header_length", 0),
                   XByteField("payload_type", 0),
                   XByteField("timeslot", 0, ),
                   XShortField("arfcn", 0),
                   XByteField("signal_level", 0),  # Returns wrong value, should be signed
                   XByteField("signal_noise_ratio", 0),
                   XIntField("gsm_frame_number", 0),
                   XByteField("channel_type", 0),
                   XByteField("antenna_number", 0),
                   XByteField("sub_slot", 0),
                   XByteField("end_junk", 0)]

    def guess_payload_class(self, payload):
        if self.channel_type == 1:
            return BCCHCommon
        elif self.channel_type == 2:
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
        if self.control_field == 32:
            return GSMAIFDTAP
        else:
            return Raw


class GSMAIFDTAP(Packet):
    name = "GSMAIFDTAP"
    fields_desc = [XByteField("rrmm", 0),
                   XByteField("message_type", 0)]

    def guess_payload_class(self, payload):
        if self.message_type == 53:
            return CipherModeCommand
        elif self.message_type == 24:
            return IdentityRequest
        else:
            return Raw

class BCCHCommon(Packet):
    name = "BCCHCommon"
    fields_desc = [XShortField("junk1", 0),
                   XByteField("message_type", 0)]

    def guess_payload_class(self, payload):
        if self.message_type == 0x1b:
            return SystemInfoType3
        else:
            return Raw


class SystemInfoType3(Packet):
    name = "SystemInfoType3"
    fields_desc = [XShortField("cid", 0),
                   XBitField("mcc_1", 0, 4),
                   XBitField("mcc_0", 0, 4),
                   XBitField("mnc_0", 0, 4),
                   XBitField("mcc_2", 0, 4),
                   XBitField("mnc_2", 0, 4),
                   XBitField("mnc_1", 0, 4),
                   XShortField("lac", 0),
                   X3BytesField("control_channel_description", 0),
                   XByteField("cell_options", 0),
                   XBitField("cell_reselection_hysteresis", 0 , 3),
                   XBitField("other_cell_selection_parameters", 0, 13),
                   X3BytesField("rach_control_parameters", 0),
                   XBitField("selection_parameters_present", 0, 1),
                   XBitField("cbq", 0, 1),
                   XBitField("cell_reselection_offset", 0, 6)]

    def post_dissection(self, s):
        self.mcc = int(str(self.mcc_0) + str(self.mcc_1) + str(self.mcc_2))
        self.mnc = int((str(self.mnc_0) if self.mnc_0 != 0xf else '') + str(self.mnc_1) + str(self.mnc_2))

    # rest of packet is left out]


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
                   XByteField("packet_channel_description", 6)  # Extract indivual bits for detailed information
                   ]
