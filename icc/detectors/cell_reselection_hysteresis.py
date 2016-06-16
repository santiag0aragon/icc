from detector import Detector
from icc.gsmpackets import GSMTap

cell_reselection_hysteresis_lower_threshold = 6  # db
cell_reselection_hysteresis_upper_threshold = 9  # db


class CellReselectionHysteresisDetector(Detector):
    def handle_packet(self, data):
        p = GSMTap(data)
        if p.channel_type == 1 and p.payload.message_type == 0x1b:
            sys_info3 = p.payload.payload
            cell_reselection_hysteresis = sys_info3.cell_reselection_hysteresis * 2
            if cell_reselection_hysteresis <= cell_reselection_hysteresis_lower_threshold:
                self.update_rank(Detector.NOT_SUSPICIOUS, "low (%d dB) cell reselection hysteresis detected" % cell_reselection_hysteresis)
            elif cell_reselection_hysteresis <= cell_reselection_hysteresis_upper_threshold:
                self.update_rank(Detector.UNKNOWN, "medium (%d dB) cell reselection hysteresis detected" % cell_reselection_hysteresis)
            else:
                self.update_rank(Detector.SUSPICIOUS, "high (%d dB) cell reselection hysteresis detected" % cell_reselection_hysteresis)
