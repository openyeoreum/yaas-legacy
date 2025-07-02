import sys
sys.path.append("/yaas")

from sqlalchemy.orm import Session
from backend.database import GetDB
from backend.models import User, ProjectsStorage, Project

def GetUser(db: Session, email: str):
    return db.query(User).filter(User.Email == email).first()

def GetProjectsStorage(db: Session, email: str):
    user = db.query(User).filter(User.Email == email).first()
    return db.query(ProjectsStorage).filter(ProjectsStorage.UserId == user.UserId).first()

def GetProjectsProcess(db: Session, email: str, projectname: str, process: str):
    user = db.query(User).filter(User.Email == email).first()
    project = db.query(Project).filter(Project.UserId == user.UserId, Project.ProjectName == projectname).first()
    return getattr(project, process, None)

if __name__ == "__main__":
    
    Process = GetProjectsProcess(GetDB, 'yeoreum00128@gmail.com', '카이스트명상수업', 'MixingMasteringKo')
    print(Process)