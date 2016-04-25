from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, deferred, backref
from functools import partial
from database import Base

#Prevents setting Not Null on each NotNullColumn
NotNullColumn = partial(Column, nullable=False)

class CellTowerScan(Base):
    __tablename__ = 'celltowerscans'
    id = NotNullColumn(Integer, primary_key=True)
    cellobservation_id = NotNullColumn(Integer, ForeignKey('cellobservations.id'))
    sample_rate = NotNullColumn(Float)
    rec_time_sec = NotNullColumn(Integer)
    timestamp = NotNullColumn(DateTime(True))

    def getCaptureFileName(self):
        return "celltowerscan_{}-cellobservation_{}-samplerate_{}-timestamp_{}".format(self.id, self.cellobservation_id, self.sample_rate, self.timestamp.isoformat())
