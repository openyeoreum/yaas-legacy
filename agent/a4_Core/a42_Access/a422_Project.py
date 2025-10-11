import os
import json
import sys
sys.path.append("/yaas")

## Project 경로 설정
def GetProjectPath(projectName, email):
    ProjectPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}/{projectName}"
    return ProjectPath

## Init audiobookDataFrame 경로 불러오기
def GetProjectDataPath():
    ProjectDataPath = "/yaas/agent/a0_Database_temp/a03_ProjectData/a034_AudioBookProject"
    return ProjectDataPath

## audiobookDataFrameConfig 경로 설정
def GetProjectConfigPath(projectName, email):
    ProjectConfigPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}/{projectName}/{projectName}_audiobook/{projectName}_dataframe_audiobook_file/{email}_{projectName}_AudiobookProcess_Config.json"
    return ProjectConfigPath

## DataFrame JSON 데이터 불러오기
def LoadJsonFrame(filepath):
    with open(filepath, 'r', encoding = 'utf-8') as file:
        DataFrame = json.load(file)
    return DataFrame

## DataFrameName이 포함된 DataFrame JSON 데이터 불러오기
def LoadExistingDataFrame(audiobookDataFramePath, DataFrameName, InitDataFramePath):
    AllFiles = os.listdir(audiobookDataFramePath)

    # DataFrameName이 포함된 파일 찾기
    for DataFrameFile in AllFiles:
        if DataFrameName in DataFrameFile:
            DataFramePath = os.path.join(audiobookDataFramePath, DataFrameFile)
            return LoadJsonFrame(DataFramePath)
        
    return LoadJsonFrame(InitDataFramePath)

## DataFrame Config 설정
def SetupProject(projectName, email):
    # 디렉토리 경로 생성
    projectPath = GetProjectPath(projectName, email)
    ProjectDataPath = GetProjectDataPath()
    
    # estimate
    estimatePath = os.path.join(projectPath, f"{projectName}_estimate")
    masterEstimatePath = os.path.join(estimatePath, f"{projectName}_master_estimate_file") # estimatePath = os.path.join(projectPath, f"{projectName}_estimate_file")
    
    # script
    scriptPath = os.path.join(projectPath, f"{projectName}_script")
    scriptDataFramePath = os.path.join(scriptPath, f"{projectName}_dataframe_script_file")
    masterScriptPath = os.path.join(scriptPath, f"{projectName}_master_script_file")
    uploadScriptPath = os.path.join(scriptPath, f"{projectName}_upload_script_file")
    mixedScriptPath = os.path.join(scriptPath, f"{projectName}_mixed_script_file")

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
    audiobookProcessConfigFilePath = GetProjectConfigPath(projectName, email)
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
        os.makedirs(mixedScriptPath, exist_ok = True)
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
    bookPreprocessFrame = LoadExistingDataFrame(audiobookDataFramePath, "00_BookPreprocessFrameDataFrame", ProjectDataPath + "/a0341_Script/a0341-00_BookPreprocessFrame.json")
    indexFrame = LoadExistingDataFrame(audiobookDataFramePath, "01_IndexFrameDataFrame", ProjectDataPath + "/a0341_Script/a0341-01_IndexFrame.json")
    duplicationPreprocessFrame = LoadExistingDataFrame(audiobookDataFramePath, "02-1_DuplicationPreprocessDataFrame", ProjectDataPath + "/a0341_Script/a0341-02_DuplicationPreprocessFrame.json")
    pronunciationPreprocessFrame = LoadExistingDataFrame(audiobookDataFramePath, "02-2_PronunciationPreprocessDataFrame", ProjectDataPath + "/a0341_Script/a0341-03_PronunciationPreprocessFrame.json")
    bodyFrame = LoadExistingDataFrame(audiobookDataFramePath, "03_BodyFrameDataFrame", ProjectDataPath + "/a0341_Script/a0341-04_BodyFrame.json")
    halfBodyFrame = LoadExistingDataFrame(audiobookDataFramePath, "04_HalfBodyFrameDataFrame", ProjectDataPath + "/a0341_Script/a0341-04_BodyFrame.json")
    captionFrame = LoadExistingDataFrame(audiobookDataFramePath, "06_CaptionCompletionDataFrame", ProjectDataPath + "/a0341_Script/a0341-05_CaptionFrame.json")
    phargraphTransitionFrame = LoadExistingDataFrame(audiobookDataFramePath, "PhargraphTransitionFrame", ProjectDataPath + "/a0341_Script/a0341-06_PhargraphTransitionFrame.json")
    bodyContextTags = LoadExistingDataFrame(audiobookDataFramePath, "BodyContextTags", ProjectDataPath + "/a0341_Script/a0341-07_BodyContextTags.json")
    wMWMContextTags = LoadExistingDataFrame(audiobookDataFramePath, "WMWMContextTags", ProjectDataPath + "/a0341_Script/a0341-08_WMWMContextTags.json")
    characterContextTags = LoadExistingDataFrame(audiobookDataFramePath, "CharacterContextTags", ProjectDataPath + "/a0341_Script/a0341-09_CharacterContextTags.json")
    soundContextTags = LoadExistingDataFrame(audiobookDataFramePath, "SoundContextTags", ProjectDataPath + "/a0341_Script/a0341-10_SoundContextTags.json")
    sFXContextTags = LoadExistingDataFrame(audiobookDataFramePath, "SFXContextTags", ProjectDataPath + "/a0341_Script/a0341-11_SFXContextTags.json")
    contextDefine = LoadExistingDataFrame(audiobookDataFramePath, "07_ContextDefineDataFrame", ProjectDataPath + "/a0342_Context/a0342-01_ContextDefine.json")
    contextCompletion = LoadExistingDataFrame(audiobookDataFramePath, "08_ContextCompletionDataFrame", ProjectDataPath + "/a0342_Context/a0342-02_ContextCompletion.json")
    wMWMDefine = LoadExistingDataFrame(audiobookDataFramePath, "09_WMWMDefineDataFrame", ProjectDataPath + "/a0342_Context/a0342-03_WMWMDefine.json")
    wMWMMatching = LoadExistingDataFrame(audiobookDataFramePath, "10_WMWMMatchingDataFrame", ProjectDataPath + "/a0342_Context/a0342-04_WMWMMatching.json")
    characterDefine = LoadExistingDataFrame(audiobookDataFramePath, "11_CharacterDefineDataFrame", ProjectDataPath + "/a0343_Character/a0343-01_CharacterDefine.json")
    characterCompletion = LoadExistingDataFrame(audiobookDataFramePath, "12_CharacterCompletionDataFrame", ProjectDataPath + "/a0343_Character/a0343-02_CharacterCompletion.json")
    soundMatching = LoadExistingDataFrame(audiobookDataFramePath, "SoundMatching", ProjectDataPath + "/a0345_Sound/a0345-01_SoundMatching.json")
    sFXMatching = LoadExistingDataFrame(audiobookDataFramePath, "15_SFXMatchingDataFrame", ProjectDataPath + "/a0346_SFX/a0346-01_SFXMatching.json")
    translationKo = LoadExistingDataFrame(audiobookDataFramePath, "TranslationKo", ProjectDataPath + "/a0347_Translation/a0347-01_TranslationKo.json")
    translationEn = LoadExistingDataFrame(audiobookDataFramePath, "TranslationEn", ProjectDataPath + "/a0347_Translation/a0347-02_TranslationEn.json")
    correctionKo = LoadExistingDataFrame(audiobookDataFramePath, "CorrectionKo", ProjectDataPath + "/a0348_Correction/a0348-01_CorrectionKo.json")
    correctionEn = LoadExistingDataFrame(audiobookDataFramePath, "CorrectionEn", ProjectDataPath + "/a0348_Correction/a0348-02_CorrectionEn.json")
    selectionGenerationKo = LoadExistingDataFrame(audiobookDataFramePath, "26_SelectionGenerationKoDataFrame", ProjectDataPath + "/a0349_SelectionGeneration/a0349-01_SelectionGenerationKo.json")
    mixingMasteringKo = LoadExistingDataFrame(audiobookDataFramePath, "MixingMasteringKo", ProjectDataPath + "/a03410_MixingMastering/a03410-01_MixingMasteringKo.json")
    ### 아래로 추가되는 데이터프레임 작성 ###

    ## audiobookProcessConfig 생성
    if not os.path.exists(audiobookProcessConfigFilePath):
        audiobookProcessConfig = {
            "ProjectName": projectName,
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
            "TranslationEn": translationEn,
            "TranslationKo": translationKo,
            "CorrectionKo": correctionKo,
            "CorrectionEn": correctionEn,
            "SelectionGenerationKo": selectionGenerationKo,
            "MixingMasteringKo": mixingMasteringKo,
            ### 아래로 추가되는 데이터프레임 작성 ###
        }
        ## 프로젝트 설정 생성
        with open(audiobookProcessConfigFilePath, 'w', encoding = 'utf-8') as ConfigFile:
            json.dump(audiobookProcessConfig, ConfigFile, ensure_ascii = False, indent = 4)
        
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