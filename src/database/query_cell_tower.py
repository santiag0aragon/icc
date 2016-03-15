import math

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

from tower import Tower

def queryTower(lac, cell_id):
    """
    Queries the database for cell towers selected by the given arguments
    Returns the results as a list
    """

    engine = create_engine('sqlite:///opencellid-nl.sqlite')
    Session = sessionmaker(bind=engine)
    session = Session()

    result_list = session.query(Tower).filter_by(area=lac, cell=cell_id).all()

    return result_list

def calculateDerivedPosition(lat, lon, distance, bearing):
    earthRadius = 6371000.
    
    latRad = math.radians(lat)
    lonRad = math.radians(lon)
    angularDistance = distance / earthRadius
    trueCourse = math.radians(bearing)
    print latRad, lonRad, angularDistance, trueCourse
    
    rlat = math.asin(math.sin(latRad) * math.cos(angularDistance) + math.cos(latRad) * math.sin(angularDistance) * math.cos(trueCourse))
    
    dlon = math.atan2(math.sin(trueCourse) * math.sin(angularDistance) * math.cos(latRad), math.cos(angularDistance) - math.sin(latRad) * math.sin(rlat))
    
    rlon = ((lonRad + dlon + math.pi) % (math.pi * 2)) - math.pi
    
    return (math.degrees(rlat), math.degrees(rlon))

def queryLocation(lat, lon, distance = 1000):
    """
    Queries the database for cell towers in the area
    Range can be specified in meters using distance
    This functions can return some towers just outside the range as it doesn't query exactly on distance
    Returns the results as a list
    """

    engine = create_engine('sqlite:///opencellid-nl.sqlite')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    lat_upper, _ = calculateDerivedPosition(lat, lon, distance, 0)
    _, lon_upper = calculateDerivedPosition(lat, lon, distance, 90)
    lat_lower, _ = calculateDerivedPosition(lat, lon, distance, 180)
    _, lon_lower = calculateDerivedPosition(lat, lon, distance, 270)

    result_list = session.query(Tower).filter(and_(Tower.lat.between(lat_lower, lat_upper), Tower.lon.between(lon_lower, lon_upper))).all()

    return result_list
