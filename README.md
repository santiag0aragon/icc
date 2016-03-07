# icc
IMSI Catcher Catcher 

## Create SQLite database from CSV
`CREATE TABLE towers (radio string, mcc integer, net integer, area integer, cell integer, unit string, lon double, lat double, range integer, samples integer, changeable tinyint, created integer, updated integer, average_signal integer, primary key (radio, mcc, net, area, cell))`

`.separator ","`

`.import databasefilename.csv towers`