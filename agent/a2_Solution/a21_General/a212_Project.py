import os
import json
import sys
sys.path.append("/yaas")

def GetProjectDataPath():
    RootPath = "/yaas"
    DataPath = "agent/a5_Database/a53_ProjectData/a534_AudioBookProject"
    return os.path.join(RootPath, DataPath)

def GetProjectConfigPath(email, projectName):
    ProjectConfigPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}/{projectName}/{projectName}_audiobook/{projectName}_dataframe_audiobook_file/{email}_{projectName}_AudiobookProcess_Config.json"
    return ProjectConfigPath

def LoadJsonFrame(filepath):
    with open(filepath, 'r') as file:
        DataFrame = json.load(file)
    return DataFrame

def SetupProject(projectName, email):
    # 디렉토리 경로 생성
    ProjectDataPath = GetProjectDataPath()
    projectPath = os.path.join(ProjectDataPath, f"{email}", f"{projectName}")
    
    # estimate
    estimatePath = os.path.join(projectPath, f"{projectName}_estimate")
    masterEstimatePath = os.path.join(estimatePath, f"{projectName}_master_estimate_file") # estimatePath = os.path.join(projectPath, f"{projectName}_estimate_file")
    
    # script
    scriptPath = os.path.join(projectPath, f"{projectName}_script")
    scriptDataFramePath = os.path.join(scriptPath, f"{projectName}_dataframe_script_file")
    masterScriptPath = os.path.join(scriptPath, f"{projectName}_master_script_file")
    uploadScriptPath = os.path.join(scriptPath, f"{projectName}_upload_script_file")

    # translation
    translationPath = os.path.join(projectPath, f"{projectName}_translation")
    translationDataFramePath = os.path.join(translationPath, f"{projectName}_dataframe_translation_file")
    masterTranslationPath = os.path.join(translationPath, f"{projectName}_master_translation_file")
    uploadTranslationPath = os.path.join(translationPath, f"{projectName}_upload_translation_file")

    # textbook
    textbookPath = os.path.join(projectPath, f"{projectName}_textbook")
    textbookDataFramePath = os.path.join(textbookPath, f"{projectName}_dataframe_textbook_file")
    mixedTextBookPath = os.path.join(textbookPath, f"{projectName}_mixed_textbook_file")
    masterTextBookPath = os.path.join(textbookPath, f"{projectName}_master_textbook_file")
    
    # audiobook
    audiobookPath = os.path.join(projectPath, f"{projectName}_audiobook")
    audiobookDataFramePath = os.path.join(audiobookPath, f"{projectName}_dataframe_audiobook_file") # dataFramePath = os.path.join(projectPath, f"{projectName}_dataframe_file")
    audiobookProcessConfigFilePath = GetProjectConfigPath(email, projectName)
    audiobookDataSetPath = os.path.join(audiobookPath, f"{projectName}_dataset_audiobook_file") # dataSetPath = os.path.join(projectPath, f"{projectName}_dataset_file")
    mixedAudioBookPath = os.path.join(audiobookPath, f"{projectName}_mixed_audiobook_file") # mixedTextBookPath = os.path.join(projectPath, f"{projectName}_mixed_textbook_file")

    voiceLayersPath = os.path.join(mixedAudioBookPath, 'VoiceLayers') # masterTextBookPath = os.path.join(projectPath, f"{projectName}_master_textbook_file")

    # narratorPath = os.path.join(voiceLayersPath, 'Narrator')
    # character1Path = os.path.join(voiceLayersPath, 'Character1')
    # character2Path = os.path.join(voiceLayersPath, 'Character2')
    # character3Path = os.path.join(voiceLayersPath, 'Character3')
    # character4Path = os.path.join(voiceLayersPath, 'Character4')
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
    music1Path = os.path.join(musicLayersPath, 'Music1') # music1FolderPath = os.path.join(musicLayersPath, 'Music1')
    music2Path = os.path.join(musicLayersPath, 'Music2')
    masterAudioBookPath = os.path.join(audiobookPath, f"{projectName}_master_audiobook_file") # masterAudioBookPath = os.path.join(projectPath, f"{projectName}_master_audiobook_file")
    
    # videobook
    videobookPath = os.path.join(projectPath, f"{projectName}_videobook")
    videobookDataFramePath = os.path.join(videobookPath, f"{projectName}_dataframe_videobook_file")
    mixedVideoBookPath = os.path.join(videobookPath, f"{projectName}_mixed_videobook_file")
    masterVideoBookPath = os.path.join(videobookPath, f"{projectName}_master_videobook_file")
    
    # marketing
    marketingPath = os.path.join(projectPath, f"{projectName}_marketing")
    marketingDataFramePath = os.path.join(marketingPath, f"{projectName}_dataframe_marketing_file")
    masterMarketingPath = os.path.join(marketingPath, f"{projectName}_master_marketing_file")
    
    # 디렉토리 생성
    if not os.path.exists(scriptPath):
        os.makedirs(projectPath, exist_ok = True)
        os.makedirs(estimatePath, exist_ok = True)
        os.makedirs(masterEstimatePath, exist_ok = True)
        os.makedirs(scriptPath, exist_ok = True)
        os.makedirs(scriptDataFramePath, exist_ok = True)
        os.makedirs(masterScriptPath, exist_ok = True)
        os.makedirs(uploadScriptPath, exist_ok = True)
        os.makedirs(translationPath, exist_ok = True)
        os.makedirs(translationDataFramePath, exist_ok = True)
        os.makedirs(masterTranslationPath, exist_ok = True)
        os.makedirs(uploadTranslationPath, exist_ok = True)
        os.makedirs(textbookPath, exist_ok = True)
        os.makedirs(textbookDataFramePath, exist_ok = True)
        os.makedirs(mixedTextBookPath, exist_ok = True)
        os.makedirs(masterTextBookPath, exist_ok = True)
        os.makedirs(audiobookPath, exist_ok = True)
        os.makedirs(audiobookDataFramePath, exist_ok = True)
        os.makedirs(audiobookDataSetPath, exist_ok = True)
        os.makedirs(mixedAudioBookPath, exist_ok = True)
        os.makedirs(voiceLayersPath, exist_ok = True)
        # os.makedirs(narratorPath, exist_ok = True)
        # os.makedirs(character1Path, exist_ok = True)
        # os.makedirs(character2Path, exist_ok = True)
        # os.makedirs(character3Path, exist_ok = True)
        # os.makedirs(character4Path, exist_ok = True)
        os.makedirs(sFXLayersPath, exist_ok = True)
        os.makedirs(sFX1Path, exist_ok = True)
        os.makedirs(sFX2Path, exist_ok = True)
        os.makedirs(sFX3Path, exist_ok = True)
        os.makedirs(sFX4Path, exist_ok = True)
        os.makedirs(sFX5Path, exist_ok = True)
        os.makedirs(soundLayersPath, exist_ok = True)
        os.makedirs(backgoundSoundPath, exist_ok = True)
        os.makedirs(captionSoundPath, exist_ok = True)
        os.makedirs(musicLayersPath, exist_ok = True)
        os.makedirs(music1Path, exist_ok = True)
        os.makedirs(music2Path, exist_ok = True)
        os.makedirs(masterAudioBookPath, exist_ok = True)
        os.makedirs(videobookPath, exist_ok = True)
        os.makedirs(videobookDataFramePath, exist_ok = True)
        os.makedirs(mixedVideoBookPath, exist_ok = True)
        os.makedirs(masterVideoBookPath, exist_ok = True)
        os.makedirs(marketingPath, exist_ok = True)
        os.makedirs(marketingDataFramePath, exist_ok = True)
        os.makedirs(masterMarketingPath, exist_ok = True)
        
    # JSON 데이터 불러오기
    bookPreprocessFrame = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-00_BookPreprocessFrame.json")
    indexFrame = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-01_IndexFrame.json")
    duplicationPreprocessFrame = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-02_DuplicationPreprocessFrame.json")
    pronunciationPreprocessFrame = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-03_PronunciationPreprocessFrame.json")
    bodyFrame = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-04_BodyFrame.json")
    halfBodyFrame = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-04_BodyFrame.json")
    captionFrame = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-05_CaptionFrame.json")
    phargraphTransitionFrame = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-06_PhargraphTransitionFrame.json")
    bodyContextTags = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-07_BodyContextTags.json")
    wMWMContextTags = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-08_WMWMContextTags.json")
    characterContextTags = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-09_CharacterContextTags.json")
    soundContextTags = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-10_SoundContextTags.json")
    sFXContextTags = LoadJsonFrame(ProjectDataPath + "/a5341_Script/a5341-11_SFXContextTags.json")
    contextDefine = LoadJsonFrame(ProjectDataPath + "/a5342_Context/a5342-01_ContextDefine.json")
    contextCompletion = LoadJsonFrame(ProjectDataPath + "/a5342_Context/a5342-02_ContextCompletion.json")
    wMWMDefine = LoadJsonFrame(ProjectDataPath + "/a5342_Context/a5342-03_WMWMDefine.json")
    wMWMMatching = LoadJsonFrame(ProjectDataPath + "/a5342_Context/a5342-04_WMWMMatching.json")
    characterDefine = LoadJsonFrame(ProjectDataPath + "/a5343_Character/a5343-01_CharacterDefine.json")
    characterCompletion = LoadJsonFrame(ProjectDataPath + "/a5343_Character/a5343-02_CharacterCompletion.json")
    soundMatching = LoadJsonFrame(ProjectDataPath + "/a5345_Sound/a5345-01_SoundMatching.json")
    sFXMatching = LoadJsonFrame(ProjectDataPath + "/a5346_SFX/a5346-01_SFXMatching.json")
    correctionKo = LoadJsonFrame(ProjectDataPath + "/a5348_Correction/a5348-01_CorrectionKo.json")
    correctionEn = LoadJsonFrame(ProjectDataPath + "/a5348_Correction/a5348-02_CorrectionEn.json")
    selectionGenerationKo = LoadJsonFrame(ProjectDataPath + "/a5349_SelectionGeneration/a5349-01_SelectionGenerationKo.json")
    mixingMasteringKo = LoadJsonFrame(ProjectDataPath + "/a53410_MixingMastering/a53410-01_MixingMasteringKo.json")
    ### 아래로 추가되는 데이터프레임 작성 ###

    ## audiobookProcessConfig 생성
    if not os.path.exists(audiobookProcessConfigFilePath):
        audiobookProcessConfig = {
            "ProjectName": projectName,
            "ProjectPath": projectPath,
            "EstimatePath": estimatePath,
            "MasterEstimatePath": masterEstimatePath,
            "ScriptPath": scriptPath,
            "ScriptDataFramePath": scriptDataFramePath,
            "MasterScriptPath": masterScriptPath,
            "UploadScriptPath": uploadScriptPath,
            "TranslationPath": translationPath,
            "TranslationDataFramePath": translationDataFramePath,
            "MasterTranslationPath": masterTranslationPath,
            "UploadTranslationPath": uploadTranslationPath,
            "TextbookPath": textbookPath,
            "TextbookDataFramePath": textbookDataFramePath,
            "MixedTextBookPath": mixedTextBookPath,
            "MasterTextBookPath": masterTextBookPath,
            "AudiobookPath": audiobookPath,
            "AudiobookDataFramePath": audiobookDataFramePath,
            "AudiobookDataSetPath": audiobookDataSetPath,
            "MixedAudioBookPath": mixedAudioBookPath,
            "VoiceLayersPath": voiceLayersPath,
            # "NarratorPath": narratorPath,
            # "Character1Path": character1Path,
            # "Character2Path": character2Path,
            # "Character3Path": character3Path,
            # "Character4Path": character4Path,
            "SFXLayersPath": sFXLayersPath,
            "SFX1Path": sFX1Path,
            "SFX2Path": sFX2Path,
            "SFX3Path": sFX3Path,
            "SFX4Path": sFX4Path,
            "SFX5Path": sFX5Path,
            "SoundLayersPath": soundLayersPath,
            "BackgoundSoundPath": backgoundSoundPath,
            "CaptionSoundPath": captionSoundPath,
            "MusicLayersPath": musicLayersPath,
            "Music1Path": music1Path,
            "Music2Path": music2Path,
            "MasterAudioBookPath": masterAudioBookPath,
            "VideobookPath": videobookPath,
            "VideobookDataFramePath": videobookDataFramePath,
            "MixedVideoBookPath": mixedVideoBookPath,
            "MasterVideoBookPath": masterVideoBookPath,
            "MarketingPath": marketingPath,
            "MarketingDataFramePath": marketingDataFramePath,
            "MasterMarketingPath": masterMarketingPath,
            "BookPreprocessFrame": bookPreprocessFrame,
            "IndexFrame": indexFrame,
            "DuplicationPreprocessFrame": duplicationPreprocessFrame,
            "PronunciationPreprocessFrame": pronunciationPreprocessFrame,
            "BodyFrame": bodyFrame,
            "HalfBodyFrame": halfBodyFrame,
            "CaptionFrame": captionFrame,
            "PhargraphTransitionFrame": phargraphTransitionFrame,
            "BodyContextTags": bodyContextTags,
            "WMWMContextTags": wMWMContextTags,
            "CharacterContextTags": characterContextTags,
            "SoundContextTags": soundContextTags,
            "SFXContextTags": sFXContextTags,
            "ContextDefine": contextDefine,
            "ContextCompletion": contextCompletion,
            "WMWMDefine": wMWMDefine,
            "WMWMMatching": wMWMMatching,
            "CharacterDefine": characterDefine,
            "CharacterCompletion": characterCompletion,
            "SoundMatching": soundMatching,
            "SFXMatching": sFXMatching,
            "CorrectionKo": correctionKo,
            "CorrectionEn": correctionEn,
            "SelectionGenerationKo": selectionGenerationKo,
            "MixingMasteringKo": mixingMasteringKo
            ### 아래로 추가되는 데이터프레임 작성 ###
        }
        ## 프로젝트 설정 생성
        with open(audiobookProcessConfigFilePath, 'w') as ConfigFile:
            json.dump(audiobookProcessConfig, ConfigFile)
        
        print(f"[ Email: {email} | ProjectName: {projectName} | AudiobookProcessConfig 완료 ]")
    else:
        print(f"[ Email: {email} | ProjectName: {projectName} | ExistedAudiobookProcessConfig로 대처됨 ]")
         
if __name__ == "__main__":
    
    SetupProject('데미안', 'yeoreum00128@gmail.com')
    SetupProject('빨간머리앤', 'yeoreum00128@gmail.com')
    SetupProject('웹3.0메타버스', 'yeoreum00128@gmail.com')
    SetupProject('나는선비로소이다', 'yeoreum00128@gmail.com')
    SetupProject('나는노비로소이다', 'yeoreum00128@gmail.com')
    SetupProject('카이스트명상수업', 'yeoreum00128@gmail.com')
    SetupProject('우리는행복을진단한다', 'yeoreum00128@gmail.com')