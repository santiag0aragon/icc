from detector import Detector
from gsmpackets import GSMTap

cell_reselection_offset_threshold = 20  # Maybe this value is too low


class CellReselectionOffsetDetector(Detector):
    def handle_packet(self, data):
        p = GSMTap(data)
        if p.channel_type == 1 and p.payload.message_type == 0x1b:
            sys_info3 = p.payload.payload
            if sys_info3.selection_parameters_present == 1:
                if self.s_rank < 1 and 0 < sys_info3.cell_reselection_offset <= cell_reselection_offset_threshold:
                    self.update_s_rank(Detector.UNKNOWN)
                elif self.s_rank < 2 and sys_info3.cell_reselection_offset > cell_reselection_offset_threshold:
                    self.update_s_rank(Detector.SUSPICIOUS)
