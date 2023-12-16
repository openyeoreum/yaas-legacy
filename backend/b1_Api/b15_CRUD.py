import sys
sys.path.append("/yaas")

from sqlalchemy.orm import Session
from backend.b1_Api.b14_Models import User

def GetUser(db: Session, email: str):
    return db.query(User).filter(User.Email == email).first()