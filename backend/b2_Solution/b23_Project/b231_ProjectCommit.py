import os
import json
import sys
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import Project
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProjectsStorage

def GetProjectDataPath():
    RootPath = "/yaas"
    DataPath = "backend/b5_Database/b53_ProjectData"
    return os.path.join(RootPath, DataPath)

def LoadJsonFrame(filepath):
    with open(filepath, 'r') as file:
        DataFrame = json.load(file)
    return DataFrame

def AddProjectToDB(projectName, email):
    with get_db() as db:
        user, ProjectsStorage = GetProjectsStorage(email)
        projectsStorageId = ProjectsStorage.ProjectsStorageId
        pojectsStoragePath = ProjectsStorage.ProjectsStoragePath

        # 해당 이메일에 대한 프로젝트 스토리지가 DB에 없으면 함수 종료
        if not pojectsStoragePath:
            print(f"No ProjectsStorage found for email: {email}")
            return
        
        # 디렉토리 경로 생성
        projectPath = os.path.join(pojectsStoragePath, f"{projectName}")
        scriptPath = os.path.join(projectPath, f"{projectName}_script_file")
        dataFramePath = os.path.join(projectPath, f"{projectName}_dataframe_file")
        mixedAudioBookPath = os.path.join(projectPath, f"{projectName}_mixed_audiobook_file")
        
        voiceLayersPath = os.path.join(mixedAudioBookPath, 'VoiceLayers')
        narratorPath = os.path.join(voiceLayersPath, 'Narrator')
        character1Path = os.path.join(voiceLayersPath, 'Character1')
        character2Path = os.path.join(voiceLayersPath, 'Character2')
        character3Path = os.path.join(voiceLayersPath, 'Character3')
        character4Path = os.path.join(voiceLayersPath, 'Character4')
        
        sFXLayersPath = os.path.join(mixedAudioBookPath, 'SFXLayers')
        sFX1Path = os.path.join(sFXLayersPath, 'SFX1')
        sFX2Path = os.path.join(sFXLayersPath, 'SFX2')
        sFX3Path = os.path.join(sFXLayersPath, 'SFX3')
        sFX4Path = os.path.join(sFXLayersPath, 'SFX4')
        sFX5Path = os.path.join(sFXLayersPath, 'SFX5')
        
        soundLayersPath = os.path.join(mixedAudioBookPath, 'SoundLayers')
        backgoundSoundPath = os.path.join(soundLayersPath, 'BackgoundSound')
        captionSoundPath = os.path.join(soundLayersPath, 'CaptionSound')
        
        musicLayersPath = os.path.join(mixedAudioBookPath, 'MusicLayers')
        music1FolderPath = os.path.join(musicLayersPath, 'Music1Folder')
        music2FolderPath = os.path.join(musicLayersPath, 'Music2Folder')
        
        masterAudioBookPath = os.path.join(projectPath, f"{projectName}_master_audiobook_file")

        # 디렉토리 생성
        if not os.path.exists(scriptPath):
            os.makedirs(projectPath)
            os.makedirs(scriptPath)
            os.makedirs(dataFramePath)
            os.makedirs(mixedAudioBookPath)
            os.makedirs(voiceLayersPath)
            os.makedirs(narratorPath)
            os.makedirs(character1Path)
            os.makedirs(character2Path)
            os.makedirs(character3Path)
            os.makedirs(character4Path)
            os.makedirs(sFXLayersPath)
            os.makedirs(sFX1Path)
            os.makedirs(sFX2Path)
            os.makedirs(sFX3Path)
            os.makedirs(sFX4Path)
            os.makedirs(sFX5Path)
            os.makedirs(soundLayersPath)
            os.makedirs(backgoundSoundPath)
            os.makedirs(captionSoundPath)
            os.makedirs(musicLayersPath)
            os.makedirs(music1FolderPath)
            os.makedirs(music2FolderPath)
            os.makedirs(masterAudioBookPath)

        # JSON 데이터 불러오기
        ProjectDataPath = GetProjectDataPath()
        
        indexFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-01_IndexFrame.json")
        preprocessFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-02_PreprocessFrame.json")
        bodyFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-03_BodyFrame.json")
        halfBodyFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-03_BodyFrame.json")
        phargraphCaptionFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-04_PhargraphCaptionFrame.json")
        phargraphTransitionFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-05_PhargraphTransitionFrame.json")
        bodyContextTags = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-07_BodyContextTags.json")
        wMWMContextTags = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-08_WMWMContextTags.json")
        characterContextTags = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-09_CharacterContextTags.json")
        soundContextTags = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-10_SoundContextTags.json")
        sFXContextTags = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-11_SFXContextTags.json")
        contextDefine = LoadJsonFrame(ProjectDataPath + "/b532_Context/b532-01_ContextDefine.json")
        contextCompletion = LoadJsonFrame(ProjectDataPath + "/b532_Context/b532-02_ContextCompletion.json")
        WMWMDefine = LoadJsonFrame(ProjectDataPath + "/b532_Context/b532-03_WMWMDefine.json")
        characterDefine = LoadJsonFrame(ProjectDataPath + "/b533_Character/b533-01_CharacterDefine.json")
        characterCompletion = LoadJsonFrame(ProjectDataPath + "/b533_Character/b533-02_CharacterCompletion.json")
        sFXMatching = LoadJsonFrame(ProjectDataPath + "/b536_SFX/b536-01_SFXMatching.json")
        translationKo = LoadJsonFrame(ProjectDataPath + "/b537_Translation/b537-01_TranslationKo.json")
        translationEn = LoadJsonFrame(ProjectDataPath + "/b537_Translation/b537-02_TranslationEn.json")
        correctionKo = LoadJsonFrame(ProjectDataPath + "/b538_Correction/b538-01_CorrectionKo.json")
        correctionEn = LoadJsonFrame(ProjectDataPath + "/b538_Correction/b538-02_CorrectionEn.json")
        mixingMasteringKo = LoadJsonFrame(ProjectDataPath + "/b5310_Mixing-Mastering/b5310-01_Mixing-MasteringKo.json")
        ### 아래로 추가되는 데이터프레임 작성 ###

        ExistingProject = db.query(Project).filter(Project.UserId == user.UserId, Project.ProjectName == projectName).first()

        # DB Commit
        if ExistingProject:
            ExistingProject.UserId = user.UserId
            ExistingProject.ProjectsStorageId = projectsStorageId
            ExistingProject.ProjectName = projectName
            ExistingProject.ProjectPath = projectPath
            ExistingProject.ScriptPath = scriptPath
            ExistingProject.DataFramePath = dataFramePath
            ExistingProject.MixedAudioBookPath = mixedAudioBookPath
            ExistingProject.VoiceLayersPath = voiceLayersPath
            ExistingProject.NarratorPath = narratorPath
            ExistingProject.Character1Path = character1Path
            ExistingProject.Character2Path = character2Path
            ExistingProject.Character3Path = character3Path
            ExistingProject.Character4Path = character4Path
            ExistingProject.SFXLayersPath = sFXLayersPath
            ExistingProject.SFX1Path = sFX1Path
            ExistingProject.SFX2Path = sFX2Path
            ExistingProject.SFX3Path = sFX3Path
            ExistingProject.SFX4Path = sFX4Path
            ExistingProject.SFX5Path = sFX5Path
            ExistingProject.SoundLayersPath = soundLayersPath
            ExistingProject.BackgoundSoundPath = backgoundSoundPath
            ExistingProject.CaptionSoundPath = captionSoundPath
            ExistingProject.MusicLayersPath = musicLayersPath
            ExistingProject.Music1FolderPath = music1FolderPath
            ExistingProject.Music2FolderPath = music2FolderPath
            ExistingProject.MasterAudioBookPath = masterAudioBookPath
            ExistingProject.IndexFrame = indexFrame
            ExistingProject.PreprocessFrame = preprocessFrame
            ExistingProject.BodyFrame = bodyFrame
            ExistingProject.HalfBodyFrame = halfBodyFrame
            ExistingProject.PhargraphCaptionFrame = phargraphCaptionFrame
            ExistingProject.PhargraphTransitionFrame = phargraphTransitionFrame
            ExistingProject.BodyContextTags = bodyContextTags
            ExistingProject.WMWMContextTags = wMWMContextTags
            ExistingProject.CharacterContextTags = characterContextTags
            ExistingProject.SoundContextTags = soundContextTags
            ExistingProject.SFXContextTags = sFXContextTags
            ExistingProject.ContextDefine = contextDefine
            ExistingProject.ContextCompletion = contextCompletion
            ExistingProject.WMWMDefine = WMWMDefine
            ExistingProject.CharacterDefine = characterDefine
            ExistingProject.CharacterCompletion = characterCompletion
            ExistingProject.SFXMatching = sFXMatching
            ExistingProject.TranslationKo = translationKo
            ExistingProject.TranslationEn = translationEn
            ExistingProject.CorrectionKo = correctionKo
            ExistingProject.CorrectionEn = correctionEn
            ExistingProject.MixingMasteringKo = mixingMasteringKo
            ### 아래로 추가되는 데이터프레임 작성 ###
            
            print(f"[ Email: {email} | ProjectName: {projectName} | AddProjectToDB 변경사항 업데이트 ]")
        else:
            project = Project(
                UserId = user.UserId,
                ProjectsStorageId = projectsStorageId,
                ProjectName = projectName,
                ProjectPath = projectPath,
                ScriptPath = scriptPath,
                DataFramePath = dataFramePath,
                MixedAudioBookPath = mixedAudioBookPath,
                VoiceLayersPath = voiceLayersPath,
                NarratorPath = narratorPath,
                Character1Path = character1Path,
                Character2Path = character2Path,
                Character3Path = character3Path,
                Character4Path = character4Path,
                SFXLayersPath = sFXLayersPath,
                SFX1Path = sFX1Path,
                SFX2Path = sFX2Path,
                SFX3Path = sFX3Path,
                SFX4Path = sFX4Path,
                SFX5Path = sFX5Path,
                SoundLayersPath = soundLayersPath,
                BackgoundSoundPath = backgoundSoundPath,
                CaptionSoundPath = captionSoundPath,
                MusicLayersPath = musicLayersPath,
                Music1FolderPath = music1FolderPath,
                Music2FolderPath = music2FolderPath,
                MasterAudioBookPath = masterAudioBookPath,
                IndexFrame = indexFrame,
                PreprocessFrame = preprocessFrame,
                BodyFrame = bodyFrame,
                HalfBodyFrame = halfBodyFrame,
                PhargraphCaptionFrame = phargraphCaptionFrame,
                PhargraphTransitionFrame = phargraphTransitionFrame,
                BodyContextTags = bodyContextTags,
                WMWMContextTags = wMWMContextTags,
                CharacterContextTags = characterContextTags,
                SoundContextTags = soundContextTags,
                SFXContextTags = sFXContextTags,
                ContextDefine = contextDefine,
                ContextCompletion = contextCompletion,
                WMWMDefine = WMWMDefine,
                CharacterDefine = characterDefine,
                CharacterCompletion = characterCompletion,
                SFXMatching = sFXMatching,
                TranslationKo = translationKo,
                TranslationEn = translationEn,
                CorrectionKo = correctionKo,
                CorrectionEn = correctionEn,
                MixingMasteringKo = mixingMasteringKo
                ### 아래로 추가되는 데이터프레임 작성 ###
                )
            db.add(project)
            print(f"[ Email: {email} | ProjectName: {projectName} | AddProjectToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":
    
    AddProjectToDB('데미안', 'yeoreum00128@gmail.com')
    AddProjectToDB('빨간머리앤', 'yeoreum00128@gmail.com')
    AddProjectToDB('웹3.0메타버스', 'yeoreum00128@gmail.com')
    AddProjectToDB('나는선비로소이다', 'yeoreum00128@gmail.com')
    AddProjectToDB('나는노비로소이다', 'yeoreum00128@gmail.com')
    AddProjectToDB('카이스트명상수업', 'yeoreum00128@gmail.com')
    AddProjectToDB('우리는행복을진단한다', 'yeoreum00128@gmail.com')