# icc
IMSI Catcher Catcher
This program tries to find nearby IMSI catchers using a RTL_SDR device.

## Instalation
The project depends on the following python libraries:
```gnuradio, osmosdr, pcapy, scapy, SQLAlchemy```

##Usage
```main.py [OPTIONS] COMMAND [ARGS]```

###OPTIONS
  -p, --ppm INTEGER        frequency offset in parts per million, default 0

  -sr, --samplerate FLOAT  samplerate in Hz

  -g, --gain FLOAT gain in dBs

  -s, --speed INTEGER      determines the speed of the scanner, .i.e. the speed value is subtracted from the sampling time for each frequency

  --help                   Show this message and exit.

###COMMANDS
  analyzefile:

  createdb:

  listscans:    Prints the saved scans

  scan:         Scans for nearby cell towers and analyzes...

## Detection methods

Detections methods (DM) are defined as python scripts in detectors/some_dector.py. Every method should extend the class Detector specified in detectors/Detector.py and define its own callback function, e.g.:

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
This function will be applied packet wise and should rank the anylyzed BTS and at the end modify the *s_rank* and *comment* variables calling ```self.update_s_rank(RANK)``(resp. ```self.comment='A descriptive comment'``).

We define rank the suspiciones of a BTS as
```
    SUSPICIOUS = 2
    UNKNOWN = 1
    NOT_SUSPICIOUS = 0
```

At the end of the detection the detectors return a *TowerRank* object.
