import os
import sys
import json
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import TrainingDataset, Project, User
from backend.b1_Api.b13_Database import get_db

def GetTrainingDatasetPath(relativePath='../../b5_Database/b55_TrainingDataset/b551_TrainingDataset.json'):
    CurrentDir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(CurrentDir, relativePath)

def LoadJsonDataset(filepath):
    with open(filepath, 'r') as file:
        DataDataset = json.load(file)
    return DataDataset

def AddTrainingDatasetToDB(projectName, email):
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()
        project = db.query(Project).filter(Project.UserId == user.UserId, Project.ProjectName == projectName).first()
        projectsStorageId = project.ProjectsStorageId,
        projectId = project.ProjectId,
        projectname = project.ProjectName,
        
        # JSON 데이터 불러오기
        TrainingDatasetPath = GetTrainingDatasetPath()
        trainingDataset = LoadJsonDataset(TrainingDatasetPath)

        ExistingDataset = db.query(TrainingDataset).filter(TrainingDataset.UserId == user.UserId, TrainingDataset.ProjectName == projectName).first()

        # DB Commit
        if ExistingDataset:
            ExistingDataset.UserId = user.UserId
            ExistingDataset.ProjectsStorageId = projectsStorageId
            ExistingDataset.ProjectId = projectId
            ExistingDataset.ProjectName = projectname
            ExistingDataset.IndexDefinePreprocess = trainingDataset
            ExistingDataset.IndexDefineDivisionPreprocess = trainingDataset
            ExistingDataset.IndexDefine = trainingDataset
            # ExistingDataset.PreprocessBody = trainingDataset
            ExistingDataset.CaptionPhargraph = trainingDataset
            # ExistingDataset.TransitionPhargraph = trainingDataset
            ExistingDataset.BodySummary = trainingDataset
            ExistingDataset.ContextDefine = trainingDataset
            ExistingDataset.ContextCompletion = trainingDataset
            ExistingDataset.NCEMCompletion = trainingDataset
            ExistingDataset.CharacterDefine = trainingDataset
            ExistingDataset.CharacterCompletion = trainingDataset
            ExistingDataset.SFXMatching = trainingDataset
            ExistingDataset.SFXMultiQuery = trainingDataset
            ExistingDataset.TranslationKo = trainingDataset
            # ExistingDataset.TranslationEn = trainingDataset
            ExistingDataset.CorrectionKo = trainingDataset
            # ExistingDataset.CorrectionEn = trainingDataset
            
            ### 아래로 추가되는 데이터셋 작성 ###
            
            print(f"[ Email: {email} | ProjectName: {projectName} | AddTrainingDatasetToDB 변경사항 업데이트 ]")
        else:
            trainingDataset = TrainingDataset(
                UserId = user.UserId,
                ProjectsStorageId = projectsStorageId,
                ProjectId = projectId,
                ProjectName = projectname,
                IndexDefinePreprocess = trainingDataset,
                IndexDefineDivisionPreprocess = trainingDataset,
                IndexDefine = trainingDataset,
                # PreprocessBody = trainingDataset,
                CaptionPhargraph = trainingDataset,
                # TransitionPhargraph = trainingDataset,
                BodySummary = trainingDataset,
                ContextDefine = trainingDataset,
                ContextCompletion = trainingDataset,
                NCEMCompletion = trainingDataset,
                CharacterDefine = trainingDataset,
                CharacterCompletion = trainingDataset,
                SFXMatching = trainingDataset,
                SFXMultiQuery = trainingDataset,
                TranslationKo = trainingDataset,
                # TranslationEn = trainingDataset,
                CorrectionKo = trainingDataset
                # CorrectionEn = trainingDataset
                ### 아래로 추가되는 데이터셋 작성 ###
                )
            db.add(trainingDataset)
            print(f"[ Email: {email} | ProjectName: {projectName} | AddTrainingDatasetToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    #########################################################################
    
    AddTrainingDatasetToDB(projectName, email)