import sys
sys.path.append("/yaas")

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.b1_Api.b13_Database import get_db
from backend.b1_Api.b14_Models import Project
from backend.b1_Api.b15_CRUD import GetUserList, GetUser
from backend.b1_Api.b17_Schemas import UserSchema, ProjectsStorageSchema, ProjectsSchema

UserRouter = APIRouter(
    prefix="/api/user",
)

@UserRouter.get("/list", response_model = list[UserSchema])
def UserList(db: Session = Depends(get_db)):
    _UserList = GetUserList(db)

    return _UserList

@UserRouter.get("/detail/{UserId}", response_model = UserSchema)
def UserDetail(UserId: int, db: Session = Depends(get_db)):
    _User = GetUser(db, UserId = UserId)
    
    return _User

ProjectsStorageRouter = APIRouter(
    prefix="/api/projectsstorage",
)

@ProjectsStorageRouter.get("/list")
def ProjectsStorageList(db: Session = Depends(get_db)):
    _ProjectsStorageList = db.query(ProjectsStorage).order_by(ProjectsStorage.ProjectsStorageDate.desc()).all()

    return _ProjectsStorageList

ProjetsRouter = APIRouter(
    prefix="/api/projects",
)

@ProjetsRouter.get("/MixingMasteringKo", response_model = list[b17_Schemas.Projects])
def ProjectsMixingMasteringKo(db: Session = Depends(get_db)):
    _ProjectsMixingMasteringKo = db.query(Project).order_by(Project.MixingMasteringKo.desc()).all()

    return _ProjectsMixingMasteringKo