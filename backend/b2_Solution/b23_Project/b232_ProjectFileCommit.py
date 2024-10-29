import os
import shutil
import sys
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import User, Project
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject

def LoadTextFile(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding = 'utf-8') as file:
            Text = file.read()
        return Text
    else:
        return None

# 개발시에만 활용
def ExistenceOrNotTextFile(projectName, email):
    project = GetProject(projectName, email)
    ScriptFilesPath = project.ScriptPath
    PDFFileSourcePath = os.path.join(ScriptFilesPath, projectName + ".pdf")
    IndexFileSourcePath = os.path.join(ScriptFilesPath, projectName + "_Index.txt")
    BodyFileSourcePath = os.path.join(ScriptFilesPath, projectName + "_Body.txt")

    if os.path.exists(PDFFileSourcePath) or (os.path.exists(IndexFileSourcePath) and os.path.exists(BodyFileSourcePath)):
        pass
    else:
        sys.exit(f"\n[ 아래 폴더에 ((({projectName + '.pdf'}))) 또는 ((({projectName + '_Index.txt'} + {projectName + '_Body.txt'}))) 파일을 넣어주세요 ]\n({ScriptFilesPath})")

def AddTextToDB(projectName, email):
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()
        project = GetProject(projectName, email)

        if not project:
            print(f"No Project found for email: {email}")
            return
        
        indexFilePath = os.path.join(project.ScriptPath, projectName + "_Index.txt")
        bodyFilePath = os.path.join(project.ScriptPath, projectName + "_Body.txt")
        
        # # 파일이 이미 존재하면 삭제
        # if os.path.exists(indexFilePath):
        #     os.remove(indexFilePath)
        # if os.path.exists(bodyFilePath):
        #     os.remove(bodyFilePath)

        # 파일 이동 (개발시에만 활용)
        ExistenceOrNotTextFile(projectName, email)

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

if __name__ == "__main__":
    
    AddTextToDB('데미안', 'yeoreum00128@gmail.com')
    AddTextToDB('빨간머리앤', 'yeoreum00128@gmail.com')
    AddTextToDB('웹3.0메타버스', 'yeoreum00128@gmail.com')
    AddTextToDB('나는선비로소이다', 'yeoreum00128@gmail.com')
    AddTextToDB('나는노비로소이다', 'yeoreum00128@gmail.com')
    AddTextToDB('카이스트명상수업', 'yeoreum00128@gmail.com')
    AddTextToDB('우리는행복을진단한다', 'yeoreum00128@gmail.com')