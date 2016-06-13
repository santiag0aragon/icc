from sqlalchemy import *
from sqlalchemy.orm import relationship
from functools import partial
from icc.database import Base

from UUID import id_column, UUID

# Prevents setting Not Null on each NotNullColumn
NotNullColumn = partial(Column, nullable=False)


class CellObservation(Base):
    __tablename__ = 'cellobservations'
    id = id_column()
    cid = NotNullColumn(Integer)
    arfcn = NotNullColumn(Integer)
    freq = NotNullColumn(Float)
    lac = NotNullColumn(Integer)
    mcc = NotNullColumn(Integer)
    mnc = NotNullColumn(Integer)
    # ccch_conf = ccch_conf
    power = NotNullColumn(Integer)
    s_rank = NotNullColumn(Integer, default=0)
    # neighbours = neighbours
    # cell_arfcns = cell_arfcns
    scan_id = NotNullColumn(UUID(), ForeignKey('scans.id'))
    scan = relationship("Scan", backref="cell_observations")
    celltowerscans = relationship('CellTowerScan')
