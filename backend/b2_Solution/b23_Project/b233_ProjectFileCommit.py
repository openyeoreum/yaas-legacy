import os
import shutil
import sys
sys.path.append("/yaas")

from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b23_Project.b231_GetDBtable import GetProject

def LoadTextFile(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        Text = file.read()
    return Text

def AddTextToDB(projectName, email):
    with get_db() as db:
        project = GetProject(projectName, email)

        # 해당 이메일에 대한 프로젝트 스토리지가 DB에 없으면 함수 종료
        if not project:
            print(f"No Project found for email: {email}")
            return
        
        # Text 데이터 불러오기
        IndexFilePath = os.path.join(project.ScriptPath, projectName + "_Index.txt")
        BodyFilePath = os.path.join(project.ScriptPath, projectName + "_Body.txt")

        IndexFileText = LoadTextFile(IndexFilePath)
        BodyFileText = LoadTextFile(BodyFilePath)
        
        # Project의 IndexFile 및 BodyFile 컬럼 업데이트
        project.IndexFile = IndexFilePath
        project.BodyFile = BodyFilePath
        project.IndexText = IndexFileText
        project.BodyText = BodyFileText

        # 변경 사항을 데이터베이스에 커밋
        db.add(project)
        db.commit()
        
# Script 파일 복사, Test에만 활용
def MoveTextFile(projectName, email):
    ScriptFilesPath = "/yaas/backend/b6_Storage/b62_UserStorage/230923_script_files"
    IndexFileSourcePath = os.path.join(ScriptFilesPath, projectName + "_Index.txt")
    BodyFileSourcePath = os.path.join(ScriptFilesPath, projectName + "_Body.txt")
    
    project = GetProject(projectName, email)
    
    shutil.copy(IndexFileSourcePath, project.ScriptPath)
    shutil.copy(BodyFileSourcePath, project.ScriptPath)
        
if __name__ == "__main__":

    MoveTextFile('데미안', 'yeoreum00128@gmail.com')
    MoveTextFile('빨간머리앤', 'yeoreum00128@gmail.com')
    MoveTextFile('웹3.0메타버스', 'yeoreum00128@gmail.com')
    MoveTextFile('나는선비로소이다', 'yeoreum00128@gmail.com')
    MoveTextFile('나는노비로소이다', 'yeoreum00128@gmail.com')
    MoveTextFile('카이스트명상수업', 'yeoreum00128@gmail.com')
    MoveTextFile('우리는행복을진단한다', 'yeoreum00128@gmail.com')
    
    AddTextToDB('데미안', 'yeoreum00128@gmail.com')
    AddTextToDB('빨간머리앤', 'yeoreum00128@gmail.com')
    AddTextToDB('웹3.0메타버스', 'yeoreum00128@gmail.com')
    AddTextToDB('나는선비로소이다', 'yeoreum00128@gmail.com')
    AddTextToDB('나는노비로소이다', 'yeoreum00128@gmail.com')
    AddTextToDB('카이스트명상수업', 'yeoreum00128@gmail.com')
    AddTextToDB('우리는행복을진단한다', 'yeoreum00128@gmail.com')