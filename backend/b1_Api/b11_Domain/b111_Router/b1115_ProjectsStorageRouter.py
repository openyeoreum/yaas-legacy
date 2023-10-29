from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...b13_Database import get_db
from ...b14_Models import ProjectsStorage

router = APIRouter(
    prefix="/api/projectsstorage",
)

@router.get("/list")
def ProjectsStorageList(db: Session = Depends(get_db)):
    _ProjectsStorageList = db.query(ProjectsStorage).order_by(ProjectsStorage.ProjectsStorageDate.desc()).all()

    return _ProjectsStorageList