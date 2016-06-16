from detector import Detector
from icc.gsmpackets import GSMTap

import icc.cellinfochecks.query_cell_tower as CellTower

import math

def calc_distance(lat1, lon1, lat2, lon2):
    # approximate radius of earth in km
    R = 6373.0

    rlat1 = math.radians(lat1)
    rlon1 = math.radians(lon1)
    rlat2 = math.radians(lat2)
    rlon2 = math.radians(lon2)

    dlon = rlon2 - rlon1
    dlat = rlat2 - rlat1

    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return (R * c) * 1000


class TIC(Detector, object):
    was_run = False

    def __init__(self, name, cellobs_id, current_lat=52.2311057, current_lon=6.8553815, range_multiplier=1):
        super(self.__class__, self).__init__(name, cellobs_id)
        self.current_lat = current_lat
        self.current_lon = current_lon
        self.range_multiplier = range_multiplier

    def handle_packet(self, data):
        p = GSMTap(data)

        if p.channel_type == 1 and p.payload.message_type == 0x1b:
            sys_info3 = p.payload.payload

            if self.was_run:
                return

            self.was_run = True

            towers = CellTower.queryTower(sys_info3.mcc, sys_info3.mnc, sys_info3.lac, sys_info3.cid)
            if len(towers) > 0:
                tower = towers[0]
                distance = calc_distance(tower.lat, tower.lon, self.current_lat, self.current_lon)
                if distance > (tower.range * self.range_multiplier):
                    self.update_rank(Detector.UNKNOWN, "Cell tower found in database, but in wrong location %d m (range %d m)" % (distance, tower.range))
                else:
                    self.update_rank(Detector.NOT_SUSPICIOUS, "Cell tower found in database and is in range")
            else:
                self.update_rank(Detector.UNKNOWN, "No match found in database")
