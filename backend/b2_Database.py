from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Engine = create_engine("postgresql://yeoreum:0128@yaasdb:5432/yeoreum")
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = Engine)
Base = declarative_base()

def GetDB():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()