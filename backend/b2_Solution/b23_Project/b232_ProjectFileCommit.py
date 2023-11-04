import os
import shutil
import sys
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import User, Project
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject

def LoadTextFile(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            Text = file.read()
        return Text
    else:
        print(f"No file found at path: {filepath}")
        return None

# 개발시에만 활용
def MoveTextFile(projectName, email):
    ScriptFilesPath = "/yaas/backend/b6_Storage/b62_UserStorage/230923_script_files"
    IndexFileSourcePath = os.path.join(ScriptFilesPath, projectName + "_Index.txt")
    BodyFileSourcePath = os.path.join(ScriptFilesPath, projectName + "_Body.txt")
    
    project = GetProject(projectName, email)
    
    shutil.copy(IndexFileSourcePath, project.ScriptPath)
    shutil.copy(BodyFileSourcePath, project.ScriptPath)

def AddTextToDB(projectName, email):
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()
        project = GetProject(projectName, email)

        if not project:
            print(f"No Project found for email: {email}")
            return
        
        indexFilePath = os.path.join(project.ScriptPath, projectName + "_Index.txt")
        bodyFilePath = os.path.join(project.ScriptPath, projectName + "_Body.txt")

        # 파일이 존재하지 않을 경우에만 이동
        if not os.path.exists(indexFilePath) or not os.path.exists(bodyFilePath):
            MoveTextFile(projectName, email)  # 개발시에만 활용

        IndexFileText = LoadTextFile(indexFilePath)
        BodyFileText = LoadTextFile(bodyFilePath)
        
        ExistingIndexFile = db.query(Project).filter(Project.UserId == user.UserId, Project.IndexFile == indexFilePath).first()
        ExistingBodyFile = db.query(Project).filter(Project.UserId == user.UserId, Project.BodyFile == bodyFilePath).first()
        
        if not ExistingIndexFile:
            project.IndexFile = indexFilePath
            project.IndexText = IndexFileText
            db.add(project)
            db.commit()
            print(f"[ Email: {email} | ProjectName: {projectName} | AddTextToDB, Index 완료 ]")
        else:
            print(f"[ Email: {email} | ProjectName: {projectName} | AddTextToDB, Index 이미 완료됨 ]")
            
        if not ExistingBodyFile:
            project.BodyFile = bodyFilePath
            project.BodyText = BodyFileText
            db.add(project)
            db.commit()
            print(f"[ Email: {email} | ProjectName: {projectName} | AddTextToDB, Body 완료 ]")
        else:
            print(f"[ Email: {email} | ProjectName: {projectName} | AddTextToDB, Body 이미 완료됨 ]")
        
if __name__ == "__main__":
    
    AddTextToDB('데미안', 'yeoreum00128@gmail.com')
    AddTextToDB('빨간머리앤', 'yeoreum00128@gmail.com')
    AddTextToDB('웹3.0메타버스', 'yeoreum00128@gmail.com')
    AddTextToDB('나는선비로소이다', 'yeoreum00128@gmail.com')
    AddTextToDB('나는노비로소이다', 'yeoreum00128@gmail.com')
    AddTextToDB('카이스트명상수업', 'yeoreum00128@gmail.com')
    AddTextToDB('우리는행복을진단한다', 'yeoreum00128@gmail.com')