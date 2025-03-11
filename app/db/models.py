from sqlalchemy import Column, Integer, String, Text, Date, Time, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base=declarative_base()

class Notice(Base):
    __tablename__ = 'notices'

    notice_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    original_link = Column(String(255), nullable=False, unique=True)
    date_posted = Column(String(100), nullable=True)
    source_school = Column(String(100), nullable=False)


