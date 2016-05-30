from icc.aux import TowerRank
from collections import Counter

def lac(found_list):
    ranks = []
    for info in sorted(found_list):
        rank = 0
        comment = None

        ## checking local area code consistency
        lacodes = []
        for tower in found_list:
            if info.mcc == tower.mcc and info.mnc == info.mnc:
                lacodes.append(tower.lac)

        areacounter = dict(Counter(lacodes))
        if len(areacounter) > 1 and sorted(areacounter, key=areacounter.get)[0] == info.lac:
            comment = "Uncommon local area code"
            rank = 1

        ranks.append(TowerRank(rank, "lac", comment, info.cellobservation_id))

    return ranks
