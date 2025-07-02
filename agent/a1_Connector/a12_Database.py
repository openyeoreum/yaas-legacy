from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

engine = create_engine("postgresql://yeoreum:0128@yaasdb:5432/yeoreum")
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

def GetDB():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()