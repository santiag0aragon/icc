from icc.aux import TowerRank
from collections import Counter

lac_threshold = .25 # % of most common LAC

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

        areacounter = Counter(lacodes)
        if (areacounter.most_common(1)[0][1] * lac_threshold) > areacounter[info.lac]:
            comment = "Uncommon local area code"
            rank = 1

        ranks.append(TowerRank(rank, "lac", comment, info.cellobservation_id))

    return ranks
