from detector import Detector
from gsmpackets import GSMTap

cell_reselection_offset_lower_threshold = 0  # db
cell_reselection_offset_upper_threshold = 25  # db


class CellReselectionOffsetDetector(Detector):
    def handle_packet(self, data):
        p = GSMTap(data)
        if p.channel_type == 1 and p.payload.message_type == 0x1b:
            sys_info3 = p.payload.payload
            if sys_info3.selection_parameters_present == 1:
                cell_reselection_offset = sys_info3.cell_reselection_offset * 2
                if cell_reselection_offset <= cell_reselection_offset_lower_threshold:
                    self.update_s_rank(Detector.NOT_SUSPICIOUS)
                    self.comment = "low (%d db) cell reselection offset detected"
                elif cell_reselection_offset <= cell_reselection_offset_upper_threshold:
                    self.update_s_rank(Detector.UNKNOWN)
                    self.comment = "medium (%d db) cell reselection offset detected"
                else:
                    self.update_s_rank(Detector.SUSPICIOUS)
                    self.comment = "high (%d db) cell reselection offset detected"
