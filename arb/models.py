import datetime
import enum

from sqlalchemy import Boolean, Enum, Column, DateTime, Integer, String

from extensions import db


class CustomerData(db.Model):
    __tablename__ = 'arb-user-data'
    id = Column(Integer(), primary_key=True)
    full_name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    phone = Column(String(16), nullable=False)
    datetime = Column('Created on', DateTime, default=datetime.datetime.now)

    def __repr__(self) -> str:
        return f"{self.full_name}"
    
    
class Languages(enum.Enum):
    EN = 'en'
    GE = 'ge'
    UA = 'ua'
    RU = 'ru'

    
class Translation(db.Model):
    __tablename__ = 'arb-translation'
    id = Column(Integer(), primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(String(1000), nullable=False)
    language_code = Column(Enum(Languages), default=Languages.EN, nullable=False)
    context_key = Column(String(50), unique=True, nullable=False)
    is_visible = Column(Boolean, default=True, nullable=True)
