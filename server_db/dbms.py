from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def create_database(db_path):
    engine = create_engine("sqlite:///{}".format(db_path))
    Session = sessionmaker(bind=engine)

    return engine, Session
