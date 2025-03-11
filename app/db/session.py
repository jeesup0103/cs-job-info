from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment variable or use default
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:1234@localhost:3306/notice_db")

# Create engine
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)