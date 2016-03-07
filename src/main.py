from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tower import Tower

engine = create_engine('sqlite:///opencellid-nl.sqlite')
Session = sessionmaker(bind=engine)

session = Session()

for tower in session.query(Tower).filter_by(area=224, cell=36201):
    print(tower)
