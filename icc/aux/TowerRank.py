class TowerRank:
    def __init__(self, rank, detector, comment, cellobs_id):
        self.s_rank = rank
        self.detector = detector
        self.comment = comment
        self.cellobs_id = cellobs_id

    def __repr__(self):
        return self.detector + ": " + self.comment + "(" + str(self.s_rank) + ")"
