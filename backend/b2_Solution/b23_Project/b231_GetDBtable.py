import sys
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import TrainingDataset, Prompt, Project, ProjectsStorage, User
from backend.b1_Api.b13_Database import get_db

def GetProjectsStorage(email):
    with get_db() as db:
        # 이메일로 사용자의 UserId를 반환
        user = db.query(User).filter(User.Email == email).first()
        # UserId로 사용자의 ProjectsStoragePath를 반환
        projectsStorage = db.query(ProjectsStorage).filter(ProjectsStorage.UserId == user.UserId).first()
        if projectsStorage:
            return user, projectsStorage
        else:
            print(f"No ProjectsStorage found for email: {email}")
            return None
        
def GetProject(projectName, email):
    with get_db() as db:
        # 이메일로 사용자의 UserId를 반환
        user = db.query(User).filter(User.Email == email).first()
        # UserId로 사용자의 Project를 반환
        project = db.query(Project).filter(Project.UserId == user.UserId, Project.ProjectName == projectName).first()
        if project:
            return project
        else:
            print(f"No Project found for email: {email}")
            return None
        
def GetPromptFrame(Process):
    with get_db() as db:
        column = getattr(Prompt, Process, None)
        if column is None:
            raise ValueError(f"No such column: {Process}")
        
        # order_by를 사용해 PromptId 기준으로 내림차순 정렬 후 첫 번째 행을 가져옵니다.
        prompt = db.query(column).order_by(Prompt.PromptId.desc()).first()
    return prompt

def GetTrainingDataset(projectName, email):
    with get_db() as db:  
        # 이메일로 사용자의 UserId를 반환
        user = db.query(User).filter(User.Email == email).first()
        # UserId로 사용자의 trainingDataset를 반환
        trainingDataset = db.query(TrainingDataset).filter(TrainingDataset.UserId == user.UserId, TrainingDataset.ProjectName == projectName).first()
        if trainingDataset:
            return trainingDataset
        else:
            print(f"No Project found for email: {email}")
            return None
        
if __name__ == "__main__":
    
    GetPromptFrame("IndexDefinePreprocess")