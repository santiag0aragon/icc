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
