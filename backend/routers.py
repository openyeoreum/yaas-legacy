import sys
sys.path.append("/yaas")

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Project
from backend.crud import GetUser, GetProjectsStorage, GetProjectsProcess
from backend.schemas import UserSchema, ProjectsStorageSchema, ProjectsProcessSchema

UserRouter = APIRouter(
    prefix="/api/user",
)

@UserRouter.get("/{email}", response_model = UserSchema)
def UserDetail(email: str, db: Session = Depends(get_db)):
    dbUser = GetUser(db, email = email)

    if dbUser is None:
        raise HTTPException(status_code = 404, detail = "User not found")

    return dbUser

@UserRouter.get("/{email}/ProjectsStorage", response_model = ProjectsStorageSchema)
def ProjectsStorageDetail(email: str, db: Session = Depends(get_db)):
    dbProjectsStorage = GetProjectsStorage(db, email = email)

    if dbProjectsStorage is None:
        raise HTTPException(status_code = 404, detail = "User not found")

    return dbProjectsStorage

@UserRouter.get("/{email}/{projectname}/{process}", response_model = ProjectsProcessSchema)
def ProjectsProcess(email: str, projectname: str, process: str, db: Session = Depends(get_db)):
    dbProjectsProcess = GetProjectsProcess(db, email = email, projectname = projectname, process = process)

    if dbProjectsProcess is None:
        raise HTTPException(status_code = 404, detail = "Process not found")

    ProjectsProcess = ProjectsProcessSchema(Process = dbProjectsProcess)
    return ProjectsProcess