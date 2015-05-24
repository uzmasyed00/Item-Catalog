import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Categories(Base):
    __tablename__ = 'Categories'

    c_id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    
class Items(Base):
    __tablename__ = 'Items'
    
    name =Column(String(80), nullable = False)
    item_id = Column(Integer, primary_key = True)
    description = Column(String(500))
    category_id = Column(Integer,ForeignKey('Categories.c_id'))
    category = relationship(Categories)

engine = create_engine('sqlite:///Project3.db')

Base.metadata.create_all(engine)
