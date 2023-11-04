import os
import sys
import json
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import Project, SeoulNow
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProjectsStorage

def GetProjectDataPath(relativePath='../../b5_Database/b53_ProjectData/'):
    CurrentDir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(CurrentDir, relativePath)

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

        seoulNow = SeoulNow()
        
        # 디렉토리 경로 생성
        projectPath = os.path.join(pojectsStoragePath, f"{seoulNow}_{projectName}")
        scriptPath = os.path.join(projectPath, f"{seoulNow}_{projectName}_script_file")
        mixedAudioBookPath = os.path.join(projectPath, f"{seoulNow}_{projectName}_mixed_audiobook_file")
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
        masterAudioBookPath = os.path.join(projectPath, f"{seoulNow}_{projectName}_master_audiobook_file")
        
        # 디렉토리 생성
        if not os.path.exists(scriptPath):
            os.makedirs(projectPath)
            os.makedirs(scriptPath)
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
            characterFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-02_CharacterFrame.json")
            bodyFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-03_BodyFrame.json")
            captionPhargraphFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-04_CaptionPhargraphFrame.json")
            summaryBodyFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-05_SummaryBodyFrame.json")
            bodyContextFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-06_BodyContextFrame.json")
            characterContextFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-07_CharacterContextFrame.json")
            soundContextFrame = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-08_SoundContextFrame.json")
            bodyCharacterDefine = LoadJsonFrame(ProjectDataPath + "/b532_BodyDefine/b532-01_BodyCharacterDefine.json")
            bodyCharacterAnnotation = LoadJsonFrame(ProjectDataPath + "/b532_BodyDefine/b532-02_BodyCharacterAnnotation.json")
            bodyContextDefine = LoadJsonFrame(ProjectDataPath + "/b532_BodyDefine/b532-03_BodyContextDefine.json")
            splitedBodyCharacterDefine = LoadJsonFrame(ProjectDataPath + "/b533_SplitedBodyDefine/b533-01_SplitedBodyCharacterDefine.json")
            splitedBodyContextDefine = LoadJsonFrame(ProjectDataPath + "/b533_SplitedBodyDefine/b533-02_SplitedBodyContextDefine.json")
            phargraphTransitionDefine = LoadJsonFrame(ProjectDataPath + "/b533_SplitedBodyDefine/b533-03_PhargraphTransitionDefine.json")
            characterTagging = LoadJsonFrame(ProjectDataPath + "/b534_Tagging/b534-01_CharacterTagging.json")
            musicTagging = LoadJsonFrame(ProjectDataPath + "/b534_Tagging/b534-02_MusicTagging.json")
            soundTagging = LoadJsonFrame(ProjectDataPath + "/b534_Tagging/b534-03_SoundTagging.json")
            characterMatching = LoadJsonFrame(ProjectDataPath + "/b535_Matching/b535-01_CharacterMatching.json")
            soundMatching = LoadJsonFrame(ProjectDataPath + "/b535_Matching/b535-02_SoundMatching.json")
            sFXMatching = LoadJsonFrame(ProjectDataPath + "/b535_Matching/b535-03_SFXMatching.json")
            characterMultiQuery = LoadJsonFrame(ProjectDataPath + "/b536_MultiQuery/b536-01_CharacterMultiQuery.json")
            soundMultiQuery = LoadJsonFrame(ProjectDataPath + "/b536_MultiQuery/b536-02_SoundMultiQuery.json")
            sFXMultiQuery = LoadJsonFrame(ProjectDataPath + "/b536_MultiQuery/b536-03_SFXMultiQuery.json")
            translationKo = LoadJsonFrame(ProjectDataPath + "/b537_Translation/b537-01_TranslationKo.json")
            translationEn = LoadJsonFrame(ProjectDataPath + "/b537_Translation/b537-02_TranslationEn.json")
            translationJa = LoadJsonFrame(ProjectDataPath + "/b537_Translation/b537-03_TranslationJa.json")
            translationZh = LoadJsonFrame(ProjectDataPath + "/b537_Translation/b537-04_TranslationZh.json")
            translationEs = LoadJsonFrame(ProjectDataPath + "/b537_Translation/b537-05_TranslationEs.json")
            correctionKo = LoadJsonFrame(ProjectDataPath + "/b538_Correction/b538-01_CorrectionKo.json")
            correctionEn = LoadJsonFrame(ProjectDataPath + "/b538_Correction/b538-02_CorrectionEn.json")
            correctionJa = LoadJsonFrame(ProjectDataPath + "/b538_Correction/b538-03_CorrectionJa.json")
            correctionZh = LoadJsonFrame(ProjectDataPath + "/b538_Correction/b538-04_CorrectionZh.json")
            correctionEs = LoadJsonFrame(ProjectDataPath + "/b538_Correction/b538-05_CorrectionEs.json")
            voiceGenerationKo = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-01_VoiceGenerationKo.json")
            voiceGenerationEn = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-02_VoiceGenerationEn.json")
            voiceGenerationJa = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-03_VoiceGenerationJa.json")
            voiceGenerationZh = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-04_VoiceGenerationZh.json")
            voiceGenerationEs = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-05_VoiceGenerationEs.json")
            musicSelection = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-06_MusicSelection.json")
            soundSelection = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-07_SoundSelection.json")
            sFXSelectionKo = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-08_SFXSelectionKo.json")
            sFXSelectionEn = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-09_SFXSelectionEn.json")
            sFXSelectionJa = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-10_SFXSelectionJa.json")
            sFXSelectionZh = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-11_SFXSelectionZh.json")
            sFXSelectionEs = LoadJsonFrame(ProjectDataPath + "/b539_Selection-Generation/b539-12_SFXSelectionEs.json")
            mixingMasteringKo = LoadJsonFrame(ProjectDataPath + "/b5310_Mixing-Mastering/b5310-01_Mixing-MasteringKo.json")
            mixingMasteringEn = LoadJsonFrame(ProjectDataPath + "/b5310_Mixing-Mastering/b5310-02_Mixing-MasteringEn.json")
            mixingMasteringJa = LoadJsonFrame(ProjectDataPath + "/b5310_Mixing-Mastering/b5310-03_Mixing-MasteringJa.json")
            mixingMasteringZh = LoadJsonFrame(ProjectDataPath + "/b5310_Mixing-Mastering/b5310-04_Mixing-MasteringZh.json")
            mixingMasteringEs = LoadJsonFrame(ProjectDataPath + "/b5310_Mixing-Mastering/b5310-05_Mixing-MasteringEs.json")

            ExistingProject = db.query(Project).filter(Project.UserId == user.UserId, Project.ProjectName == projectName).first()

            # DB Commit
            if ExistingProject:
                ExistingProject.UserId = user.UserId
                ExistingProject.ProjectsStorageId = projectsStorageId
                ExistingProject.ProjectName = projectName
                ExistingProject.ProjectPath = projectPath
                ExistingProject.ScriptPath = scriptPath
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
                ExistingProject.CharacterFrame = characterFrame
                ExistingProject.BodyFrame = bodyFrame
                ExistingProject.CaptionPhargraphFrame = captionPhargraphFrame
                ExistingProject.SummaryBodyFrame = summaryBodyFrame
                ExistingProject.BodyContextFrame = bodyContextFrame
                ExistingProject.CharacterContextFrame = characterContextFrame
                ExistingProject.SoundContextFrame = soundContextFrame
                ExistingProject.BodyCharacterDefine = bodyCharacterDefine
                ExistingProject.BodyCharacterAnnotation = bodyCharacterAnnotation
                ExistingProject.BodyContextDefine = bodyContextDefine
                ExistingProject.SplitedBodyCharacterDefine = splitedBodyCharacterDefine
                ExistingProject.SplitedBodyContextDefine = splitedBodyContextDefine
                ExistingProject.PhargraphTransitionDefine = phargraphTransitionDefine
                ExistingProject.CharacterTagging = characterTagging
                ExistingProject.MusicTagging = musicTagging
                ExistingProject.SoundTagging = soundTagging
                ExistingProject.CharacterMatching = characterMatching
                ExistingProject.SoundMatching = soundMatching
                ExistingProject.SFXMatching = sFXMatching
                ExistingProject.CharacterMultiQuery = characterMultiQuery
                ExistingProject.SoundMultiQuery = soundMultiQuery
                ExistingProject.SFXMultiQuery = sFXMultiQuery
                ExistingProject.TranslationKo = translationKo
                ExistingProject.TranslationEn = translationEn
                ExistingProject.TranslationJa = translationJa
                ExistingProject.TranslationZh = translationZh
                ExistingProject.TranslationEs = translationEs
                ExistingProject.CorrectionKo = correctionKo
                ExistingProject.CorrectionEn = correctionEn
                ExistingProject.CorrectionJa = correctionJa
                ExistingProject.CorrectionZh = correctionZh
                ExistingProject.CorrectionEs = correctionEs
                ExistingProject.VoiceGenerationKo = voiceGenerationKo
                ExistingProject.VoiceGenerationEn = voiceGenerationEn
                ExistingProject.VoiceGenerationJa = voiceGenerationJa
                ExistingProject.VoiceGenerationZh = voiceGenerationZh
                ExistingProject.VoiceGenerationEs = voiceGenerationEs
                ExistingProject.MusicSelection = musicSelection
                ExistingProject.SoundSelection = soundSelection
                ExistingProject.SFXSelectionKo = sFXSelectionKo
                ExistingProject.SFXSelectionEn = sFXSelectionEn
                ExistingProject.SFXSelectionJa = sFXSelectionJa
                ExistingProject.SFXSelectionZh = sFXSelectionZh
                ExistingProject.SFXSelectionEs = sFXSelectionEs
                ExistingProject.MixingMasteringKo = mixingMasteringKo
                ExistingProject.MixingMasteringEn = mixingMasteringEn
                ExistingProject.MixingMasteringJa = mixingMasteringJa
                ExistingProject.MixingMasteringZh = mixingMasteringZh
                ExistingProject.MixingMasteringEs = mixingMasteringEs
                
            else:
                project = Project(
                    UserId = user.UserId,
                    ProjectsStorageId = projectsStorageId,
                    ProjectName = projectName,
                    ProjectPath = projectPath,
                    ScriptPath = scriptPath,
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
                    CharacterFrame = characterFrame,
                    BodyFrame = bodyFrame,
                    CaptionPhargraphFrame = captionPhargraphFrame,
                    SummaryBodyFrame = summaryBodyFrame,
                    BodyContextFrame = bodyContextFrame,
                    CharacterContextFrame = characterContextFrame,
                    SoundContextFrame = soundContextFrame,
                    BodyCharacterDefine = bodyCharacterDefine,
                    BodyCharacterAnnotation = bodyCharacterAnnotation,
                    BodyContextDefine = bodyContextDefine,
                    SplitedBodyCharacterDefine = splitedBodyCharacterDefine,
                    SplitedBodyContextDefine = splitedBodyContextDefine,
                    PhargraphTransitionDefine = phargraphTransitionDefine,
                    CharacterTagging = characterTagging,
                    MusicTagging = musicTagging,
                    SoundTagging = soundTagging,
                    CharacterMatching = characterMatching,
                    SoundMatching = soundMatching,
                    SFXMatching = sFXMatching,
                    CharacterMultiQuery = characterMultiQuery,
                    SoundMultiQuery = soundMultiQuery,
                    SFXMultiQuery = sFXMultiQuery,
                    TranslationKo = translationKo,
                    TranslationEn = translationEn,
                    TranslationJa = translationJa,
                    TranslationZh = translationZh,
                    TranslationEs = translationEs,
                    CorrectionKo = correctionKo,
                    CorrectionEn = correctionEn,
                    CorrectionJa = correctionJa,
                    CorrectionZh = correctionZh,
                    CorrectionEs = correctionEs,
                    VoiceGenerationKo = voiceGenerationKo,
                    VoiceGenerationEn = voiceGenerationEn,
                    VoiceGenerationJa = voiceGenerationJa,
                    VoiceGenerationZh = voiceGenerationZh,
                    VoiceGenerationEs = voiceGenerationEs,
                    MusicSelection = musicSelection,
                    SoundSelection = soundSelection,
                    SFXSelectionKo = sFXSelectionKo,
                    SFXSelectionEn = sFXSelectionEn,
                    SFXSelectionJa = sFXSelectionJa,
                    SFXSelectionZh = sFXSelectionZh,
                    SFXSelectionEs = sFXSelectionEs,
                    MixingMasteringKo = mixingMasteringKo,
                    MixingMasteringEn = mixingMasteringEn,
                    MixingMasteringJa = mixingMasteringJa,
                    MixingMasteringZh = mixingMasteringZh,
                    MixingMasteringEs = mixingMasteringEs)
                db.add(project)
            
            db.commit()
         
if __name__ == "__main__":
    
    AddProjectToDB('데미안', 'yeoreum00128@gmail.com')
    AddProjectToDB('빨간머리앤', 'yeoreum00128@gmail.com')
    AddProjectToDB('웹3.0메타버스', 'yeoreum00128@gmail.com')
    AddProjectToDB('나는선비로소이다', 'yeoreum00128@gmail.com')
    AddProjectToDB('나는노비로소이다', 'yeoreum00128@gmail.com')
    AddProjectToDB('카이스트명상수업', 'yeoreum00128@gmail.com')
    AddProjectToDB('우리는행복을진단한다', 'yeoreum00128@gmail.com')