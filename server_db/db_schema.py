from dbms import Base

import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    surname = Column(String)
    is_yp = Column(Boolean)
    is_active = Column(Boolean)

    def __repr__(self):
        return "<User: {} {}>".format(self.first_name, self.surname)

    def to_dict(self):
        return {"id": self.id,
                "first_name": self.first_name,
                "surname": self.surname,
                "num_projects": 0,
                "is_YP": self.is_yp,
                "is_active": self.is_active}


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(Integer) #  0 - Blender
    sw_version = Column(String)
    file_name = Column(String)
    dir_name = Column(String)

    def __repr__(self):
        return "<Project(name='{}')>".format(self.name)

    def to_dict(self):
        return {"id": self.id,
                "name": self.name,
                "category": self.category,
                "sw_version": self.sw_version,
                "dir_name": self.dir_name,
                "file_name": self.file_name}


class ProjectOwner(Base):
    __tablename__ = "project_owners"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)


class RenderItem(Base):
    __tablename__ = "render_queue"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer)
    file_name = Column(String)
    submission_time = Column(DateTime, default=datetime.datetime.utcnow)
