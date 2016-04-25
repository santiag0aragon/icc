from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, deferred, backref
from functools import partial
from database import Base

#Prevents setting Not Null on each NotNullColumn
NotNullColumn = partial(Column, nullable=False)

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
