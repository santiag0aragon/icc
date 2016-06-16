# iMSI catcher catcher (icc).


This program tries to find nearby IMSI catchers using a RTL_SDR device.

![alt text](https://github.com/santiag0aragon/icc/blob/master/report/img/scanner.png "icc Diagram")

## Instalation
The project depends on the following python libraries:
```gnuradio, osmosdr, pcapy, scapy, SQLAlchemy```

##Usage
```main.py [OPTIONS] COMMAND [ARGS]```

###OPTIONS
+ -p, --ppm INTEGER        frequency offset in parts per million, default 0

+ -sr, --samplerate FLOAT  samplerate in Hz

+ -g, --gain FLOAT gain in dBs

+ -s, --speed INTEGER      determines the speed of the scanner, .i.e. the speed value is subtracted from the sampling time for each frequency

+ --help                   Show this message and exit.

###COMMANDS
+ analyzefile:  Run the analyzer on a cfile
  +  --sample_rate FLOAT
  +  --arfcn INTEGER
  +  --timeslot INTEGER   Decode timeslot a range of timeslots. I.e. 0 - [timeslot]
  +  --chan_mode TEXT     Channel mode to demap the different timeslots other than t0
  ++ --help               Show this message and exit.
+ createdb:     Create  a new data base

+ detectoffline: Run the detectors on a cfile.

  + --timeslot INTEGER  Decode timeslot 0 - [timeslot]
  + --chan_mode TEXT    Channel mode to demap the timeslots other than t0
  + --help              Show this message and exit.

+ listscans:    Prints the saved scans.
  + -n, --limit INTEGER             Limit the number of results returned
  + --printscans / --no-printscans
  + --help                          Show this message and exit.

+ scan:         Scans for nearby cell towers and analyzes
  + -b, --band TEXT             select the band to scan. One of: E-GSM, P-GSM or
                              R-GSM
  + -r, --rec_time_sec INTEGER  if the analyze option is specified, sets the
                              recording time for each tower analysis in
                              seocnds
  + -a, --analyze               turns on anylis of each tower found of the scan.
                              Will produce a capture file of each tower for
                              duration specified with --rec_time_sec
  + -d, --detection             if the analyze option is specified, turns on
                              IMSI catcher detection during analysis of each
                              tower
  + -l, --location TEXT         current location used to mark a scan in Apple
                              GPS minutes format
  + --lat FLOAT                 latitude used to specify the scan location, is
                              used by detectors that perform location based
                              detection of IMSI catchers
  + --lon FLOAT                 longitude used to specify the scan location, is
                              used by detectors that perform location based
                              detection of IMSI catchers
  + -u, --unmute                if the analyze option is specified, unmutes the
                              output during analysis which will show the
                              output of your capture device when it starts
  + --help                      Show this message and exit.

## Detection methods

Detections methods (DM) are defined as python scripts in ```detectors/some_dector.py```. Every method should extend the **class Detector** specified in ```detectors/Detector.py``` and define its own callback function **handle_packet**, e.g.:

```python
    def handle_packet(self, data):
        p = GSMTap(data)
        if p.payload.name is 'LAPDm' and p.payload.payload.name is 'GSMAIFDTAP' and p.payload.payload.payload.name is 'CipherModeCommand':
                cipher = p.payload.payload.payload.cipher_mode >> 1
                if cipher == 0:
                    self.update_s_rank(Detector.SUSPICIOUS)
                    self.comment = 'A5/1 detected'
                elif cipher == 2:
                    self.comment = 'A5/3 detected'
                    self.update_s_rank(Detector.NOT_SUSPICIOUS)
                else:
                    self.update_s_rank(Detector.UNKNOWN)
                    self.comment = 'cipher used %s:' % cipher
                print self.comment
        else:
                if self.comment is '':
                    self.comment = 'No enough information found.'
                    self.update_s_rank(Detector.UNKNOWN)
```
This function will be applied packet wise and should rank the analyzed packets and at the end modify the **s_rank** and **comment** fields by calling ```self.update_s_rank(RANK)```(resp. ```self.comment='A descriptive comment'```).
The function ```self.update_s_rank(RANK)``` updates the **s_rank** field if **RANK** is greater than the actual value of **s_rank**.
We define rank the suspiciousness of a BTS in the **class Detector** as:
```
    SUSPICIOUS = 2
    UNKNOWN = 1
    NOT_SUSPICIOUS = 0
```

The output of a detector is a **TowerRank** object.

The final output of the program is a list of **CellObservation** objects containing a list of **CellTowerScan** objects. An example of it is showed below:
```
#0 | Rank: 5 | ARFCN: 9 | Freq: 936800000.0 | LAC: 3330 | MCC: 204 | MNC: 8 | Power: -34
--- Detector: a5_detector | Rank: 1 | Comment: No enough information found.
--- Detector: id_request_detector | Rank: 1 | Comment: IMSI request detected 1 times
--- Detector: cell_reselection_offset_detector | Rank: 0 | Comment: low (0 dB) cell reselection offset detected
--- Detector: cell_reselection_offset_hysteresis | Rank: 0 | Comment: low (6 dB) cell reselection hysteresis detected
--- Detector: tic | Rank: 1 | Comment: Cell tower found in database, but in wrong location 174545 m (range 5369 m)
--- Detector: lac | Rank: 0 | Comment: Common local area code
--- Detector: neighbours | Rank: 2 | Comment: Cell '9' has no neighbours
```


### Consistency checks
To verify the information received by **icc**, we use the database (DB) provided by [OpenCellID](http://wiki.opencellid.org/wiki/What_is_OpenCellID), a collaborative community project that collects cell tower information, e.g., LAC, MCC, MNC, geolocation, etc.

#### Neighbor consistency. ```cellinfochecks/neighbours.py```
Neighbor cell broadcasted information is verified against the DB and the others cells detected in the surroundings. It is also verified that the BTS announces a valid neighbor list, i.e. a non empty list. Furthermore, the BTS should also appear in other neighbor lists.

#### Tower information consistency and BTS expected location. ```cellinfochecks/tic.py```
Every detected BTS is verified against the DB where MCC, MNC, CID are checked. Furthermore, if the current geolocation (LAT, LON) is provided, it is verified if the BTS is broadcasting in the expected location, i.e. the measurement is taken within a valid transmission range.


### Packet based Detectors
Used to examine every packet forwarded by the analyzer.

#### Encryption algorithm detection. A5/X
**CipherModeCommand** packets are parsed and scanned for the encryption algorithm used to secure the communication.
+ A5/0 No encryption
+ A5/1 Broken algorithm
+ A5/2 Weakened algorithm to fulfill exportation regulation
+ A5/3 Updated algorithm for 3G

#### Cell reselection offset. C2_OFFSET
In order to evaluate the quality of a BTS during the cell reselection process a C2 parameter is calculated for each cell. The MS will switch to a a different BTS if the C2 value of that cell is higher than the C2 value of the current BTS. The C2 value incorporates the cell reselection offset of a BTS, which is an offset, from 0 - 126 dB, to the measured quality by the MS. For higher cell reselection offset values, the MS will be more likely to select a BTS and stay at that BTS. The recommended value for the cell reselection offset is 0 dB, therefore most values above that are suspicious:
+ 0 dB: not suspicious
+ 1 - 25 dB: somewhat suspicious
+ 26 - 126 dB: very suspicious

#### Cell reselection hysteresis. C2_HYSTERESIS
To prevent constant switching of BTSs with a similar C2 value, an additional C2 offset parameter between 0 and 14 dB, the cell reselection hysteresis, is used. The cell reselection hysteresis is added to the C2 value of the current BTS when comparing it to the C2 values of different BTSs, so the C2 value of another BTS has to be higher for a longer period in order to switch. The recommended value for the cell reselection hysteresis is 6 dB, therefore most values above that are suspicious
+ 0-6 dB: not suspicious
+ 7 - 9 dB: somewhat suspicious
+ 10 - 14 dB: very suspicious

#### Identity request detector.
To identify a subscriber the International Mobile Subscriber Identity (IMSI) is used, and to avoid likability between transactions the Temporal Mobile Subscriber Identity, therefore the IMSI should be transmitted only when its strictly necessary. Thus, the presence a big amount of Identity Request Procedures querying a subscriber by IMSI may indicate suspicious behavior.
