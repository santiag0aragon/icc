from detector import Detector
from gsmpackets import GSMTap


class CellReselectionOffsetDetector(Detector):
    rank = 0

    def handle_packet(self, data):
        p = GSMTap(data)
        if p.channel_type == 1 and p.payload.message_type == 0x1b:
            sys_info3 = p.payload.payload
            if sys_info3.selection_parameters_present == 1:
                if self.rank < 1 and 0 < sys_info3.cell_reselection_offset <= 20:  # Maybe this value is too low
                    self.rank = 1
                elif self.rank < 2 and sys_info3.cell_reselection_offset > 20:
                    self.rank = 2

    def on_finish(self):
        return self.rank
