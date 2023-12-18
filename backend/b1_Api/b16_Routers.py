import sys
sys.path.append("/yaas")

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.b1_Api.b13_Database import get_DB
from backend.b1_Api.b14_Models import Project
from backend.b1_Api.b15_CRUD import GetUser, GetProjectsStorage, GetProjectsProcess
from backend.b1_Api.b17_Schemas import UserSchema, ProjectsStorageSchema, ProjectsProcessSchema

UserRouter = APIRouter(
    prefix="/api/user",
)

@UserRouter.get("/{email}", response_model = UserSchema)
def UserDetail(email: str, db: Session = Depends(get_DB)):
    dbUser = GetUser(db, email = email)

    if dbUser is None:
        raise HTTPException(status_code = 404, detail = "User not found")

    return dbUser

@UserRouter.get("/{email}/ProjectsStorage", response_model = ProjectsStorageSchema)
def ProjectsStorageDetail(email: str, db: Session = Depends(get_DB)):
    dbProjectsStorage = GetProjectsStorage(db, email = email)

    if dbProjectsStorage is None:
        raise HTTPException(status_code = 404, detail = "User not found")

    return dbProjectsStorage

@UserRouter.get("/{email}/{projectname}/{process}", response_model = ProjectsProcessSchema)
def ProjectsProcess(email: str, projectname: str, process: str, db: Session = Depends(get_DB)):
    dbProjectsProcess = GetProjectsProcess(db, email = email, projectname = projectname, process = process)

    if dbProjectsProcess is None:
        raise HTTPException(status_code = 404, detail = "Process not found")

    ProjectsProcess = ProjectsProcessSchema(Process = dbProjectsProcess)
    return ProjectsProcess