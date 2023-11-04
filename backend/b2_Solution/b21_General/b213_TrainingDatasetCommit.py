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
            ExistingDataset.CaptionDefine = trainingDataset
            ExistingDataset.BodySummary = trainingDataset
            ExistingDataset.BodyCharacterDefine = trainingDataset
            ExistingDataset.BodyCharacterAnnotation = trainingDataset
            ExistingDataset.BodyContextDefine = trainingDataset
            ExistingDataset.SplitedBodyCharacterDefine = trainingDataset
            ExistingDataset.SplitedBodyContextDefine = trainingDataset
            ExistingDataset.PhargraphTransitionDefine = trainingDataset
            ExistingDataset.CharacterTagging = trainingDataset
            ExistingDataset.MusicTagging = trainingDataset
            ExistingDataset.SoundTagging = trainingDataset
            ExistingDataset.CharacterMatching = trainingDataset
            ExistingDataset.SoundMatching = trainingDataset
            ExistingDataset.SFXMatching = trainingDataset
            ExistingDataset.CharacterMultiQuery = trainingDataset
            ExistingDataset.SoundMultiQuery = trainingDataset
            ExistingDataset.SFXMultiQuery = trainingDataset
            ExistingDataset.TranslationKo = trainingDataset
            ExistingDataset.TranslationEn = trainingDataset
            ExistingDataset.TranslationJa = trainingDataset
            ExistingDataset.TranslationZh = trainingDataset
            ExistingDataset.TranslationEs = trainingDataset
            ExistingDataset.CorrectionKo = trainingDataset
            ExistingDataset.CorrectionEn = trainingDataset
            ExistingDataset.CorrectionJa = trainingDataset
            ExistingDataset.CorrectionZh = trainingDataset
            ExistingDataset.CorrectionEs = trainingDataset
            ExistingDataset.VoiceGenerationKo = trainingDataset
            ExistingDataset.VoiceGenerationEn = trainingDataset
            ExistingDataset.VoiceGenerationJa = trainingDataset
            ExistingDataset.VoiceGenerationZh = trainingDataset
            ExistingDataset.VoiceGenerationEs = trainingDataset
            ExistingDataset.MusicSelection = trainingDataset
            ExistingDataset.SoundSelection = trainingDataset
            ExistingDataset.SFXSelectionKo = trainingDataset
            ExistingDataset.SFXSelectionEn = trainingDataset
            ExistingDataset.SFXSelectionJa = trainingDataset
            ExistingDataset.SFXSelectionZh = trainingDataset
            ExistingDataset.SFXSelectionEs = trainingDataset
            ExistingDataset.MixingMasteringKo = trainingDataset
            ExistingDataset.MixingMasteringEn = trainingDataset
            ExistingDataset.MixingMasteringJa = trainingDataset
            ExistingDataset.MixingMasteringZh = trainingDataset
            ExistingDataset.MixingMasteringEs = trainingDataset
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
                CaptionDefine = trainingDataset,
                BodySummary = trainingDataset,
                BodyCharacterDefine = trainingDataset,
                BodyCharacterAnnotation = trainingDataset,
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
            print(f"[ Email: {email} | ProjectName: {projectName} | AddTrainingDatasetToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    #########################################################################
    
    AddTrainingDatasetToDB(projectName, email)