# DATABASE
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Table, Column, Integer, ForeignKey

# DB ORM[ SQLALCHEMY ]
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Boolean, MetaData

# OTHER
import json
from threading import Lock
from typing import Union, List


DATABASE_NAME = 'ads_db'
engine = create_engine(f'sqlite:///{DATABASE_NAME}')
BaseDB = declarative_base()
LocalSession = scoped_session(sessionmaker(bind=engine))


class User(BaseDB):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    is_admin = Column(Boolean, default=False)


class Ad(BaseDB):
    __tablename__ = 'ads'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    discount = Column(String)
    price = Column(String)
    url = Column(String)
    images = Column(String)


class Adolx(BaseDB):
    __tablename__ = 'adolx'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    price = Column(String)
    url = Column(String)
    images = Column(String)
    description = Column(String)


BaseDB.metadata.create_all(bind=engine)

