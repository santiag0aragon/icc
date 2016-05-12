from sqlalchemy import *
from functools import partial
from database import Base
from sqlalchemy.orm import relationship

from UUID import id_column, UUID

# Prevents setting Not Null on each NotNullColumn
NotNullColumn = partial(Column, nullable=False)


class CellTowerScan(Base):
    __tablename__ = 'celltowerscans'
    id = id_column()
    sample_rate = NotNullColumn(Float)
    rec_time_sec = NotNullColumn(Integer)
    timestamp = NotNullColumn(DateTime(True))
    cellobservation_id = NotNullColumn(UUID(), ForeignKey('cellobservations.id'))
    relationship("CellObservation")

    def getCaptureFileName(self):
        return "celltowerscan_{}-cellobservation_{}-samplerate_{}-timestamp_{}".format(self.id, self.cellobservation_id,
                                                                                       self.sample_rate,
                                                                                       self.timestamp.isoformat())
