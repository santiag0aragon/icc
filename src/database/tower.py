from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Float, DateTime

class Tower(declarative_base()):
    __tablename__ = 'towers'

    radio = Column(String, primary_key=True)
    mcc = Column(Integer, primary_key=True)
    net = Column(Integer, primary_key=True) #mnc
    area = Column(Integer, primary_key=True) #lac
    cell = Column(Integer, primary_key=True)
    unit = Column(String)
    lon = Column(Float)
    lat = Column(Float)
    range = Column(Integer)
    samples = Column(Integer)
    changeable = Column(Integer)
    created = Column(Integer)
    updated = Column(Integer)
    average_signal = Column(Integer)

    def __repr__(self):
        return "<Tower(radio='%s', mcc='%s', net='%s', area='%s'," \
               " cell='%s', unit='%s', lon='%s', lat='%s', range='%s'," \
               " samples='%s', changeable='%s', created='%s'," \
               " updated='%s', average_signal='%s')>" % (
                   self.radio,
                   self.mcc,
                   self.net,
                   self.area,
                   self.cell,
                   self.unit,
                   self.lon,
                   self.lat,
                   self.range,
                   self.samples,
                   self.changeable,
                   self.created,
                   self.updated,
                   self.average_signal)
