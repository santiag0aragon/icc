from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, deferred, backref
from functools import partial
from database import Base

#Prevents setting Not Null on each NotNullColumn
NotNullColumn = partial(Column, nullable=False)

class Scan(Base):
    __tablename__ = 'scans'
    id = NotNullColumn(Integer, primary_key=True)
    timestamp = NotNullColumn(DateTime(True))
    bands = NotNullColumn(String)
    latitude = Column(Float)
    longitude = Column(Float)

    def getScanCaptureFileName():
        return "scan_{}_{}.file".format(self.id, str(self.timestamp))

class CellObservation(Base):
    __tablename__ = 'cellobservations'
    id = NotNullColumn(Integer, primary_key=True)
    cid = NotNullColumn(Integer)
    arfcn = NotNullColumn(Integer)
    freq = NotNullColumn(Float)
    lac = NotNullColumn(Integer)
    mcc = NotNullColumn(Integer)
    mnc = NotNullColumn(Integer)
    #ccch_conf = ccch_conf
    power = NotNullColumn(Integer)
    #neighbours = neighbours
    #cell_arfcns = cell_arfcns
    scan_id = NotNullColumn(Integer, ForeignKey('scans.id'))

class CellTowerScan(Base):
    __tablename__ = 'celltowerscans'
    id = NotNullColumn(Integer, primary_key=True)
    cellobservation_id = NotNullColumn(Integer, ForeignKey('cellobservations.id'))
    sample_rate = NotNullColumn(Float)
    rec_time_sec = NotNullColumn(Integer)
    timestamp = NotNullColumn(DateTime(True))

    def getCaptureFileName(self):
        return "celltowerscan_{}-cellobservation_{}-samplerate_{}-timestamp_{}".format(self.id, self.cellobservation_id, self.sample_rate, self.timestamp.isoformat())
