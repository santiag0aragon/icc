class ChannelInfo(object):

    def __init__(self, arfcn, freq, cid, lac, mcc, mnc, ccch_conf, power, neighbours, cell_arfcns):
        self.arfcn = arfcn
        self.freq = freq
        self.cid = cid
        self.lac = lac
        self.mcc = mcc
        self.mnc = mnc
        self.ccch_conf = ccch_conf
        self.power = power
        self.neighbours = neighbours
        self.cell_arfcns = cell_arfcns

    def get_verbose_info(self):
        i = "  |---- Configuration: %s\n" % self.get_ccch_conf()
        i += "  |---- Cell ARFCNs: " + ", ".join(map(str, self.cell_arfcns)) + "\n"
        i += "  |---- Neighbour Cells: " + ", ".join(map(str, self.neighbours)) + "\n"
        return i

    def get_ccch_conf(self):
        if self.ccch_conf == 0:
            return "1 CCCH, not combined"
        elif self.ccch_conf == 1:
            return "1 CCCH, combined"
        elif self.ccch_conf == 2:
            return "2 CCCH, not combined"
        elif self.ccch_conf == 4:
            return "3 CCCH, not combined"
        elif self.ccch_conf == 6:
            return "4 CCCH, not combined"
        else:
            return "Unknown"

    def getKey(self):
        return self.arfcn

    def __cmp__(self, other):
        if hasattr(other, 'getKey'):
            return self.getKey().__cmp__(other.getKey())

    #def __repr__(self):
    #    return "ARFCN: %4u, Freq: %6.1fM, CID: %5u, LAC: %5u, MCC: %3u, MNC: %3u, Pwr: %3i" % (self.arfcn, self.freq/1e6, self.cid, self.lac, self.mcc, self.mnc, self.power)
