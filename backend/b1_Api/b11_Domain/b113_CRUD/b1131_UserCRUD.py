from sqlalchemy.orm import Session

from ...b14_Models import User, HashPassword

def GetUserList(db: Session):
    userlist = db.query(User).order_by(User.UserDate.desc()).all()

    return userlist

def GetUser(db: Session, UserId: int):
    user = db.query(User).get(UserId)
    
    return user