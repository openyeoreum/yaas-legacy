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

        # DB Commit
        trainingDataset = TrainingDataset(
            UserId = user.UserId,
            ProjectsStorageId = projectsStorageId,
            ProjectId = projectId,
            ProjectName = projectname,
            IndexDefinePreprocess = trainingDataset,
            IndexDefineDivisionPreprocess = trainingDataset,
            IndexDefine = trainingDataset,
            CaptionDefine = trainingDataset,
            BodySummary = trainingDataset,
            BodyCharacterDefine = trainingDataset,
            BodyContextDefine = trainingDataset,
            SplitedBodyCharacterDefine = trainingDataset,
            SplitedBodyContextDefine = trainingDataset,
            PhargraphTransitionDefine = trainingDataset,
            CharacterTagging = trainingDataset,
            MusicTagging = trainingDataset,
            SoundTagging = trainingDataset,
            CharacterMatching = trainingDataset,
            SoundMatching = trainingDataset,
            SFXMatching = trainingDataset,
            CharacterMultiQuery = trainingDataset,
            SoundMultiQuery = trainingDataset,
            SFXMultiQuery = trainingDataset,
            TranslationKo = trainingDataset,
            TranslationEn = trainingDataset,
            TranslationJa = trainingDataset,
            TranslationZh = trainingDataset,
            TranslationEs = trainingDataset,
            CorrectionKo = trainingDataset,
            CorrectionEn = trainingDataset,
            CorrectionJa = trainingDataset,
            CorrectionZh = trainingDataset,
            CorrectionEs = trainingDataset,
            VoiceGenerationKo = trainingDataset,
            VoiceGenerationEn = trainingDataset,
            VoiceGenerationJa = trainingDataset,
            VoiceGenerationZh = trainingDataset,
            VoiceGenerationEs = trainingDataset,
            MusicSelection = trainingDataset,
            SoundSelection = trainingDataset,
            SFXSelectionKo = trainingDataset,
            SFXSelectionEn = trainingDataset,
            SFXSelectionJa = trainingDataset,
            SFXSelectionZh = trainingDataset,
            SFXSelectionEs = trainingDataset,
            MixingMasteringKo = trainingDataset,
            MixingMasteringEn = trainingDataset,
            MixingMasteringJa = trainingDataset,
            MixingMasteringZh = trainingDataset,
            MixingMasteringEs = trainingDataset
            )
        
        db.add(trainingDataset)
        db.commit()
         
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    DataFramePath = "/yaas/backend/b5_Database/b50_DatabaseTest/b53_ProjectDataTest/"
    DataSetPath = "/yaas/backend/b5_Database/b50_DatabaseTest/b55_TrainingDataTest/"
    #########################################################################
    
    AddTrainingDatasetToDB(projectName, email)