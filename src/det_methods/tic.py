import src.database.query_cell_tower as CellTower

def tic(found_list, info, verbose):
# Tower Information Consistency Check
    if len(found_list) > 0:
        print("Printing cell tower info and checking database....")
        for info in sorted(found_list):
            print info
            if verbose:
                print info.get_verbose_info()
            nr_of_hits = len(CellTower.queryTower(info.mcc, info.mnc, info.cid))
            if nr_of_hits > 0:
                print(" Cell tower found in database, " + str(nr_of_hits) + " matches")
            else:
                print(" No match found in database")
    else:
        print("No cell towers found...")
