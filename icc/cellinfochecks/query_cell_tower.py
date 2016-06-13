from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tower import Tower

def queryTower(mcc, mnc, lac, cell_id):
    """
    Queries the database for cell towers selected by the given arguments
    Returns the results as a list
    """

    engine = create_engine('sqlite:///opencellid-nl.sqlite')
    Session = sessionmaker(bind=engine)
    session = Session()

    result_list = session.query(Tower).filter_by(mcc=mcc, net=mnc, area=lac, cell=cell_id).all()

    return result_list
