import sys
sys.path.append("/yaas")

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.b1_Api.b13_Database import get_DB
from backend.b1_Api.b14_Models import Project
from backend.b1_Api.b15_CRUD import GetUser
from backend.b1_Api.b17_Schemas import UserSchema

UserRouter = APIRouter(
    prefix="/api/user",
)

@UserRouter.get("/{email}", response_model = UserSchema)
def UserDetail(email: str, db: Session = Depends(get_DB)):
    dbUser = GetUser(db, email = email)
    if dbUser is None:
        raise HTTPException(status_code = 404, detail = "User not found")
    return dbUser

ProjectsStorageRouter = APIRouter(
    prefix="/api/projectsstorage",
)

# @ProjectsStorageRouter.get("/list")
# def ProjectsStorageList(db: Session = Depends(get_db)):
#     _ProjectsStorageList = db.query(ProjectsStorage).order_by(ProjectsStorage.ProjectsStorageDate.desc()).all()

#     return _ProjectsStorageList

# ProjetsRouter = APIRouter(
#     prefix="/api/projects",
# )

# @ProjetsRouter.get("/MixingMasteringKo", response_model = list[b17_Schemas.Projects])
# def ProjectsMixingMasteringKo(db: Session = Depends(get_db)):
#     _ProjectsMixingMasteringKo = db.query(Project).order_by(Project.MixingMasteringKo.desc()).all()

#     return _ProjectsMixingMasteringKo