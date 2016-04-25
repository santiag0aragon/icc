from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event
from sqlalchemy.orm.exc import NoResultFound,MultipleResultsFound

engine = create_engine("sqlite:///test_database.sqlite" )
session_class = sessionmaker(bind=engine)

Base = declarative_base()
