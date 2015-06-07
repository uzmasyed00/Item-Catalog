import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Categories(Base):
    __tablename__ = 'Categories'

    c_id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer,ForeignKey('User.id'))
    user = relationship(User)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'c_id'         : self.c_id,
       }

    
class Items(Base):
    __tablename__ = 'Items'
    
    name =Column(String(80), nullable = False)
    item_id = Column(Integer, primary_key = True)
    description = Column(String(500))
    category_id = Column(Integer,ForeignKey('Categories.c_id'))
    user_id = Column(Integer,ForeignKey('User.id'))
    category = relationship(Categories, backref=backref("children", cascade="all,delete"))
    user = relationship(User)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'item_id'         : self.item_id,
           'description'     : self.description,
           'category_id'     : self.category_id,
       }

engine = create_engine('sqlite:///Project3.db')

Base.metadata.create_all(engine)
