import os
import glob
import unicodedata
import sys

sys.path.append("/yaas")

from backend.b1_Api.b14_Models import ProjectsStorage, User, SeoulNow
from backend.b1_Api.b13_Database import get_db

def GetUserPath(email):
    with get_db() as db:
        # 이메일로 사용자의 UserPath를 반환
        user = db.query(User).filter(User.Email == email).first()
        if user:
            return user.UserPath
        else:
            print(f"No user found for email: {email}")
            return None

def AddProjectsStorageToDB(projectsStorageName, email):
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()

        # 해당 이메일에 대한 사용자가 DB에 없으면 함수 종료
        if not user:
            print(f"No user found for email: {email}")
            return

        UserPath = user.UserPath
        # 가능한 모든 ProjectsStoragePath 검색
        possiblePaths = glob.glob(os.path.join(UserPath, f"*_{projectsStorageName}_storage"))
        possiblePathsNormalized = unicodedata.normalize('NFC', possiblePaths)
        print(f'있다 경로 : {possiblePathsNormalized}')
        # 존재하는 경로 중 가장 최근 것 사용
        if possiblePathsNormalized:
            projectsStoragePath = max(possiblePathsNormalized, key = os.path.getctime)
            print(f'본래 경로 : {possiblePathsNormalized}')
        else:
            # 존재하는 경로가 없으면 새로운 경로 생성
            projectsStoragePath = os.path.join(UserPath, f"{SeoulNow()}_{projectsStorageName}_storage")
            # 새로운 폴더 생성
            os.makedirs(projectsStoragePath, exist_ok=True)
            
        ExistingProjectsStorage = db.query(ProjectsStorage).filter(ProjectsStorage.UserId == user.UserId, ProjectsStorage.ProjectsStorageName == projectsStorageName).first()

        # ProjectsStorage 객체 생성 및 초기 정보 입력
        if not ExistingProjectsStorage:
            projectsStorage = ProjectsStorage(
                UserId = user.UserId,
                ProjectsStorageName = projectsStorageName,
                ProjectsStoragePath = projectsStoragePath
                )
            db.add(projectsStorage)
            # 사용자 스토리지 폴더 생성
            os.makedirs(projectsStoragePath, exist_ok = True)
        
            db.commit()
            print(f"[ Email: {email} | ProjectsStorageName: {projectsStorageName} | AddProjectsStorageToDB 완료 ]")
        else:
            print(f"[ Email: {email} | ProjectsStorageName: {projectsStorageName} | AddProjectsStorageToDB가 이미 완료됨 ]")

if __name__ == "__main__":
    
    AddProjectsStorageToDB('yeoreum', 'yeoreum00128@gmail.com')
    AddProjectsStorageToDB('junyoung', 'junsun0128@gmail.com')
    AddProjectsStorageToDB('ahyeon', 'ahyeon0128@gmail.com')