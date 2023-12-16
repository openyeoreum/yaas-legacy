import sys
sys.path.append("/yaas")

from sqlalchemy.orm import Session
from backend.b1_Api.b13_Database import get_db
from backend.b1_Api.b14_Models import User, Project

def GetUser(db: Session, email: str):
    return db.query(User).filter(User.Email == email).first()

def GetProjectsProcess(db: Session, email: str, projectname: str, process: str):
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()
        project = db.query(Project).filter(Project.UserId == user.UserId, Project.ProjectName == projectname).first()
        # Process = getattr(project, process, None)
        # return db.query(Process).first()
        return getattr(project, process, None)

if __name__ == "__main__":
    
    Process = GetProjectsProcess(get_db, 'yeoreum00128@gmail.com', '우리는행복을진단한다', 'BodyFrame')
    print(Process)