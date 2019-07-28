"""This won't overwrite anything if the table already exists"""

from dbms import create_database, Base

db_path = "LivePipes2019.db"
engine, Session = create_database(db_path)

session = Session()
Base.metadata.create_all(engine)

#peter_user = User(name="Peter Noble")
#james_user = User(name="James Tait")

#session.add_all([james_user])

session.commit()
session.close()
