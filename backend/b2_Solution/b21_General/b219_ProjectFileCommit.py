import os
import json
import sys
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import User, Project
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject

# Load Index, Body
def LoadTextFile(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            Text = file.read()
        return Text
    else:
        print(f"No file found at path: {filepath}")
        return None

# Index, Body Commit
def AddTextToDB(projectName, email, TextDirPath):
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()
        project = GetProject(projectName, email)
        
        # 디렉토리 경로 생성
        indexFilePath = os.path.join(TextDirPath, f"{projectName}_Index.txt")
        bodyFilePath = os.path.join(TextDirPath, f"{projectName}_Body.txt")

        IndexFileText = LoadTextFile(indexFilePath)
        BodyFileText = LoadTextFile(bodyFilePath)

        ExistingIndexFile = db.query(Project).filter(Project.UserId == user.UserId, Project.IndexFile == indexFilePath).first()
        ExistingBodyFile = db.query(Project).filter(Project.UserId == user.UserId, Project.BodyFile == bodyFilePath).first()

        project.IndexFile = indexFilePath
        project.IndexText = IndexFileText
        project.BodyFile = bodyFilePath
        project.BodyText = BodyFileText
        
        if not ExistingIndexFile:
            db.add(project)
            print(f"[ Email: {email} | ProjectName: {projectName} | AddTextToDB, Index 완료 ]")
        else:
            db.merge(project)
            print(f"[ Email: {email} | ProjectName: {projectName} | AddTextToDB, Index 변경사항 업데이트 ]")
            
        if not ExistingBodyFile:
            db.add(project)
            print(f"[ Email: {email} | ProjectName: {projectName} | AddTextToDB, Body 완료 ]")
        else:
            db.merge(project)
            print(f"[ Email: {email} | ProjectName: {projectName} | AddTextToDB, Body 변경사항 업데이트 ]")
            
        db.commit()