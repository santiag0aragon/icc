# icc
IMSI Catcher Catcher

## Create SQLite database from CSV
`CREATE TABLE towers (radio string, mcc integer, net integer, area integer, cell integer, unit string, lon double, lat double, range integer, samples integer, changeable tinyint, created integer, updated integer, average_signal integer, primary key (radio, mcc, net, area, cell))`

`.separator ","`

`.import databasefilename.csv towers`


## Detection method

Detections methods (DM) are defined in a python file src/det_methods.
A parser option should be added in `main` of `grgsm_scanner_mod` method of to disable each particular DM i.e., for Tower Information Consistency Check (TIC):
    `parser.add_option("--no_TIC", action="store_true", default=False, help="Disable the tower information consistency checks.")`

Finally, the corresponding information should be logged by adding inn `grgsm_scanner_mod` if a particular DM will be used, i.e., for TIC:
`    if !options.no_TIC:
        print "Tower Information Consistency Check"
`
