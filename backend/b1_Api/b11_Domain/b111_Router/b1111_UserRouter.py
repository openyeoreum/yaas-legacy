from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ...b11_Domain.b112_Schema import b1121_UserSchema
from ...b11_Domain.b113_CRUD import b1131_UserCRUD
from ...b13_Database import get_db
from ...b14_Models import User

router = APIRouter(
    prefix="/api/user",
)

@router.get("/list", response_model = list[b1121_UserSchema.User])
def UserList(db: Session = Depends(get_db)):
    _UserList = b1131_UserCRUD.GetUserList(db)

    return _UserList

@router.get("/detail/{UserId}", response_model = b1121_UserSchema.User)
def UserDetail(UserId: int, db: Session = Depends(get_db)):
    _User = b1131_UserCRUD.GetUser(db, UserId = UserId)
    
    return _User