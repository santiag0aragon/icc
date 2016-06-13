# iMSI catcher catcher (icc).


This program tries to find nearby IMSI catchers using a RTL_SDR device.
TODO: Diagram
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

TODO: output of analysis and detection

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

#### Identity request detector.


