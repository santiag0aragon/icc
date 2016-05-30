from sqlalchemy import *
from functools import partial
from icc.database import Base

from UUID import id_column

# Prevents setting Not Null on each NotNullColumn
NotNullColumn = partial(Column, nullable=False)


class Scan(Base):
    __tablename__ = 'scans'
    id = id_column()
    timestamp = NotNullColumn(DateTime(True))
    bands = NotNullColumn(String)
    latitude = Column(Float)
    longitude = Column(Float)

    def getScanCaptureFileName(self):
        return "scan_{}_{}.file".format(self.id, str(self.timestamp))
