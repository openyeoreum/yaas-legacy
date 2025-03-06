import os
import re
import unicodedata
import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject
from backend.b2_Solution.b25_DataFrame.b251_DataCommit.b2512_DataFrameCommit import FindDataframeFilePaths, AddFrameMetaDataToDB, InitScriptGen, UpdatedScriptGen, InitBookPreprocess, UpdatedBookPreprocess, InitIndexFrame, UpdatedIndexFrame, InitDuplicationPreprocess, UpdatedDuplicationPreprocess, InitPronunciationPreprocess, UpdatedPronunciationPreprocess, InitBodyFrame, UpdatedBodyFrame, InitHalfBodyFrame, UpdatedHalfBodyFrame, InitCaptionCompletion, UpdatedCaptionCompletion, InitContextDefine, UpdatedContextDefine, InitContextCompletion, UpdatedContextCompletion, InitWMWMDefine, UpdatedWMWMDefine, InitWMWMMatching, UpdatedWMWMMatching, InitCharacterDefine, UpdatedCharacterDefine, InitCharacterCompletion, UpdatedCharacterCompletion, InitSoundMatching, UpdatedSoundMatching, InitSFXMatching, UpdatedSFXMatching, InitCorrectionKo, UpdatedCorrectionKo, InitSelectionGenerationKo, UpdatedSelectionGenerationKo
from backend.b2_Solution.b25_DataFrame.b251_DataCommit.b2513_DataSetCommit import LoadExistedDataSets, AddDataSetMetaDataToDB, SaveDataSet, InitRawDataSet
from backend.b2_Solution.b25_DataFrame.b251_ScriptGen.b2511_ScriptGenUpdate import ScriptGenUpdate, ScriptGenResponseJson
from backend.b2_Solution.b25_DataFrame.b252_Script.b2520_BookPreprocessUpdate import BookPreprocessUpdate
from backend.b2_Solution.b25_DataFrame.b252_Script.b2521_IndexDefineUpdate import IndexFrameUpdate
from backend.b2_Solution.b25_DataFrame.b252_Script.b2522_DuplicationPreprocessUpdate import DuplicationPreprocessUpdate
from backend.b2_Solution.b25_DataFrame.b252_Script.b2523_PronunciationPreprocessUpdate import PronunciationPreprocessUpdate
from backend.b2_Solution.b25_DataFrame.b252_Script.b2524_BodyFrameUpdate import BodyFrameUpdate
from backend.b2_Solution.b25_DataFrame.b252_Script.b2525_HalfBodyFrameUpdate import HalfBodyFrameUpdate
from backend.b2_Solution.b25_DataFrame.b252_Script.b2526_CaptionCompletionUpdate import CaptionCompletionUpdate
from backend.b2_Solution.b25_DataFrame.b253_Context.b2531_ContextDefineUpdate import ContextDefineUpdate
from backend.b2_Solution.b25_DataFrame.b253_Context.b2532_ContextCompletionUpdate import ContextCompletionUpdate
from backend.b2_Solution.b25_DataFrame.b253_Context.b2533_WMWMDefineUpdate import WMWMDefineUpdate
from backend.b2_Solution.b25_DataFrame.b253_Context.b2534_WMWMMatchingUpdate import WMWMMatchingUpdate
from backend.b2_Solution.b25_DataFrame.b254_Character.b2541_CharacterDefineUpdate import CharacterDefineUpdate
from backend.b2_Solution.b25_DataFrame.b254_Character.b2542_CharacterCompletionUpdate import CharacterCompletionUpdate
from backend.b2_Solution.b25_DataFrame.b256_Sound.b2561_SoundMatchingUpdate import SoundMatchingUpdate
from backend.b2_Solution.b25_DataFrame.b257_SFX.b2571_SFXMatchingUpdate import SFXMatchingUpdate
from backend.b2_Solution.b25_DataFrame.b259_Correction.b2591_CorrectionKoUpdate import CorrectionKoUpdate
from backend.b2_Solution.b25_DataFrame.b2510_SelectionGeneration.b25101_SelectionGenerationKo import SelectionGenerationKoUpdate

## 오늘 날짜
def Date(Option = "Day"):
    if Option == "Day":
      now = datetime.now()
      date = now.strftime('%y%m%d')
    elif Option == "Second":
      now = datetime.now()
      date = now.strftime('%y%m%d%H%M%S')
    
    return date

## 업데이트된 DataFrame 파일저장
def SaveDataFrame(projectName, email, Process, UpdatedFrame, RawDataSetPath):
    # 현재 날짜 및 시간을 가져옵니다.
    filename = RawDataSetPath + email + '_' + projectName + '_' + Process + 'DataFrame_' + str(Date()) + '.json'
    
    base, ext = os.path.splitext(filename)
    counter = 0
    newFilename = filename
    while os.path.exists(newFilename):
        counter += 1
        newFilename = f"{base} ({counter}){ext}"
    with open(newFilename, 'w', encoding = 'utf-8') as f:
        json.dump(UpdatedFrame, f, ensure_ascii = False, indent = 4)
        
def LoadexistedDataFrame(projectName, email, Process, DataFramePath):
    # 문자열 정규화
    EmailNormalized = unicodedata.normalize('NFC', email)
    ProjectNameNormalized = unicodedata.normalize('NFC', projectName)
    ProcessNormalized = unicodedata.normalize('NFC', Process)
    print(DataFramePath)
    DataFramePathNormalized = unicodedata.normalize('NFC', DataFramePath)
    
    # 정규 표현식으로 파일명에서 생성날짜와 프로세스 이름 추출
    patternSTR = rf"{re.escape(EmailNormalized)}_{re.escape(ProjectNameNormalized)}_\d+(-\d+)?_{re.escape(ProcessNormalized)}DataFrame_(\d+).json"
    pattern = re.compile(patternSTR)

    MaxDate = 0
    RecentFile = None

    ## 한글의 유니코드 문제로 인해 일반과 노멀라이즈를 2개로 분리하여 가장 최근 파일찾기 실행
    try:
        DataFramePathList = os.listdir(DataFramePath)
        dataFramePath = DataFramePath
    except:
        DataFramePathList = os.listdir(DataFramePathNormalized)
        dataFramePath = DataFramePathNormalized
        
    for FileName in DataFramePathList:
        FileNameNormalized = unicodedata.normalize('NFC', FileName)
        match = pattern.match(FileNameNormalized)
        if match:
            date = int(match.group(2))
            if date > MaxDate:
                MaxDate = date
                RecentFile = FileName

    if RecentFile:
        with open(os.path.join(dataFramePath, RecentFile), 'r', encoding = 'utf-8') as file:
            ExistedDataFrame = json.load(file)
            return ExistedDataFrame

    return None

## BodyFrameBodys Context 부분 json파일에 업데이트 반영
def LoadAndUpdateBodyFrameBodys(projectName, email, Process, Data, DataFramePath):

    project = GetProject(projectName, email)

    if Process == "BodyFrame":
        bodyFrame = project.BodyFrame
    elif Process == "HalfBodyFrame":
        bodyFrame = project.HalfBodyFrame

    if Data == "SplitedBodyScripts":
        Bodys = bodyFrame[1]["SplitedBodyScripts"]
    elif Data == "Bodys":
        Bodys = bodyFrame[2]["Bodys"]

    # 문자열 정규화
    EmailNormalized = unicodedata.normalize('NFC', email)
    ProjectNameNormalized = unicodedata.normalize('NFC', projectName)
    ProcessNormalized = unicodedata.normalize('NFC', Process)
    DataFramePathNormalized = unicodedata.normalize('NFC', DataFramePath)

    # 정규 표현식으로 파일명에서 생성날짜와 프로세스 이름 추출
    patternSTR = rf"{re.escape(EmailNormalized)}_{re.escape(ProjectNameNormalized)}_\d+(-\d+)?_{re.escape(ProcessNormalized)}DataFrame_(\d+).json"
    pattern = re.compile(patternSTR)

    MaxDate = 0
    RecentFile = None

    ## 한글의 유니코드 문제로 인해 일반과 노멀라이즈를 2개로 분리하여 가장 최근 파일찾기 실행
    try:
        DataFramePathList = os.listdir(DataFramePath)
        dataFramePath = DataFramePath
    except:
        DataFramePathList = os.listdir(DataFramePathNormalized)
        dataFramePath = DataFramePathNormalized
        
    for FileName in DataFramePathList:
        FileNameNormalized = unicodedata.normalize('NFC', FileName)
        match = pattern.match(FileNameNormalized)
        if match:
            date = int(match.group(2))
            if date > MaxDate:
                MaxDate = date
                RecentFile = FileName

    # 파일 읽기 및 데이터 업데이트
    if RecentFile:
        FilePath = os.path.join(dataFramePath, RecentFile)
        with open(FilePath, 'r', encoding = 'utf-8') as file:
            ExistedDataFrame = json.load(file)
        
        # Bodys 데이터 업데이트
        if Data == "SplitedBodyScripts":
            ExistedDataFrame[1]["SplitedBodyScripts"] = Bodys
        elif Data == "Bodys":
            ExistedDataFrame[2]["Bodys"] = Bodys

        # 변경된 데이터 저장
        with open(FilePath, 'w', encoding = 'utf-8') as file:
            json.dump(ExistedDataFrame, file, ensure_ascii = False, indent = 4)

    return None

###################################
###################################
##### SolutionDataFrameUpdate #####
###################################
###################################

### 솔루션에 프로젝트 데이터 프레임 진행 및 업데이트 ###
def SolutionDataFrameUpdate(email, projectName, mainLang, indexMode = "Define", messagesReview = "on", bookGenre = "Auto", Translations = []):
    ############################ 하이퍼 파라미터 설정 ############################
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_audiobook/{projectName}_dataset_audiobook_file/"
    
    ### existedDataFrameMode는 개발과정에서 지속적인 데이터베이스 포멧에 따라 필요, 프로덕트에서는 필요없음.
    existedDataFrameMode = "on" # <- 개발 후 off #
    
    ProjectConfig = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_config.json"
    with open(ProjectConfig, 'r', encoding = 'utf-8') as ConfigJson:
        Config = json.load(ConfigJson)
        ScriptConfig = Config['ScriptConfig']

    # existedDataFrame 초기화
    existedDataFrame = None
    existedDataSet = None
    existedDataSet1 = None
    existedDataSet2 = None
    #########################################################################


    ##################################
    ### 00_DataFrame-[AllMetaData] ###
    ##################################
    AddFrameMetaDataToDB(projectName, email)

    AddDataSetMetaDataToDB(projectName, email)


    ####################
    ### 00_ScriptGen ###
    ####################
    if ScriptConfig != {}:
        InitScriptGen(projectName, email)
        InitRawDataSet(projectName, email, "ScriptGen")
        if existedDataFrameMode == "on":
            existedDataFrame = LoadexistedDataFrame(projectName, email, "ScriptGenFrame", DataFramePath)
            recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "ScriptGen", RawDataSetPath)
        mode = "Memory"
        ScriptGenUpdate(projectName, email, DataFramePath, ScriptConfig, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
        if existedDataFrame == None:
            updatedScriptGen = UpdatedScriptGen(projectName, email)
            SaveDataFrame(projectName, email, "00_ScriptGenFrame", updatedScriptGen, DataFramePath)
        if existedDataSet == None:
            SaveDataSet(projectName, email, "00", "ScriptGen", RawDataSetPath)
        existedDataFrame = None
        existedDataSet = None


    #########################
    ### 00_BookPreprocess ###
    #########################
    if ScriptConfig == {}:
        InitBookPreprocess(projectName, email)
        InitRawDataSet(projectName, email, "BookPreprocess")
        if existedDataFrameMode == "on":
            existedDataFrame = LoadexistedDataFrame(projectName, email, "BookPreprocessFrame", DataFramePath)
            recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "BookPreprocess", RawDataSetPath)
        mode = "Master"
        BookPreprocessUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)

        if existedDataFrame == None:
            updatedBookPreprocess = UpdatedBookPreprocess(projectName, email)
            SaveDataFrame(projectName, email, "00_BookPreprocessFrame", updatedBookPreprocess, DataFramePath)
        if existedDataSet == None:
            SaveDataSet(projectName, email, "00", "BookPreprocess", RawDataSetPath)
        existedDataFrame = None
        existedDataSet = None


    ###################################
    ### 01_IndexFrame-[IndexDefine] ###
    ###################################
    InitIndexFrame(projectName, email)
    InitRawDataSet(projectName, email, "IndexDefinePreprocess")
    InitRawDataSet(projectName, email, "IndexDefine")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "IndexFrame", DataFramePath)
        recentFile, existedDataSet1 = LoadExistedDataSets(projectName, email, "IndexDefinePreprocess", RawDataSetPath)
        recentFile, existedDataSet2 = LoadExistedDataSets(projectName, email, "IndexDefine", RawDataSetPath)
    mode = "Master" # mode의 종류: "Example", "ExampleFineTuning", "Memory", "MemoryFineTuning", "Master"
    IndexFrameUpdate(projectName, email, mainLang, MessagesReview = messagesReview, Mode = mode, IndexMode = indexMode, ExistedDataFrame = existedDataFrame, ExistedDataSet1 = existedDataSet1, ExistedDataSet2 = existedDataSet2)
    
    if existedDataFrame == None:
        updatedIndexFrame = UpdatedIndexFrame(projectName, email)
        SaveDataFrame(projectName, email, "01_IndexFrame", updatedIndexFrame, DataFramePath)
    if existedDataSet1 == None:
        SaveDataSet(projectName, email, "01", "IndexDefinePreprocess", RawDataSetPath)
        SaveDataSet(projectName, email, "01", "IndexDefine", RawDataSetPath)
    existedDataFrame = None
    existedDataSet1 = None
    existedDataSet2 = None
    
    
    ##################################
    ### 02-1_DuplicationPreprocess ###
    ##################################
    InitDuplicationPreprocess(projectName, email)
    InitRawDataSet(projectName, email, "DuplicationPreprocess")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "DuplicationPreprocess", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "DuplicationPreprocess", RawDataSetPath)
    mode = "Master"
    DuplicationPreprocessUpdate(projectName, email, mainLang, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)

    if existedDataFrame == None:
        updatedDuplicationPreprocess = UpdatedDuplicationPreprocess(projectName, email)
        SaveDataFrame(projectName, email, "02-1_DuplicationPreprocess", updatedDuplicationPreprocess, DataFramePath)
    if existedDataSet == None:
        SaveDataSet(projectName, email, "02-1", "DuplicationPreprocess", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None


    ####################################
    ### 02-2_PronunciationPreprocess ###
    ####################################
    InitPronunciationPreprocess(projectName, email)
    InitRawDataSet(projectName, email, "PronunciationPreprocess")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "PronunciationPreprocess", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "PronunciationPreprocess", RawDataSetPath)
    mode = "Master"
    PronunciationPreprocessUpdate(projectName, email, mainLang, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)

    if existedDataFrame == None:
        updatedPronunciationPreprocess = UpdatedPronunciationPreprocess(projectName, email)
        SaveDataFrame(projectName, email, "02-2_PronunciationPreprocess", updatedPronunciationPreprocess, DataFramePath)
    if existedDataSet == None:
        SaveDataSet(projectName, email, "02-2", "PronunciationPreprocess", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None


    ##############################################
    ### 03_BodyFrame-[BodySplit, IndexTagging] ###
    ##############################################
    InitBodyFrame(projectName, email)
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "BodyFrame", DataFramePath)
    BodyFrameUpdate(projectName, email, tokensCount = 2500, ExistedDataFrame = existedDataFrame)

    if existedDataFrame == None:
        updatedBodyFrame = UpdatedBodyFrame(projectName, email)
        SaveDataFrame(projectName, email, "03_BodyFrame", updatedBodyFrame, DataFramePath)
    existedDataFrame = None
    
    
    ##################################################
    ### 04_HalfBodyFrame-[BodySplit, IndexTagging] ###
    ##################################################
    InitHalfBodyFrame(projectName, email)
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "HalfBodyFrame", DataFramePath)
    HalfBodyFrameUpdate(projectName, email, tokensCount = 750, ExistedDataFrame = existedDataFrame)

    if existedDataFrame == None:
        updatedHalfBodyFrame = UpdatedHalfBodyFrame(projectName, email)
        SaveDataFrame(projectName, email, "04_HalfBodyFrame", updatedHalfBodyFrame, DataFramePath)
    existedDataFrame = None


    ############################
    ### 06_CaptionCompletion ###
    ############################
    InitCaptionCompletion(projectName, email)
    InitRawDataSet(projectName, email, "CaptionCompletion")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "CaptionCompletion", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CaptionCompletion", RawDataSetPath)
    mode = "Master"
    CaptionCompletionUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedCaptionCompletion = UpdatedCaptionCompletion(projectName, email)
        SaveDataFrame(projectName, email, "06_CaptionCompletion", updatedCaptionCompletion, DataFramePath)
        # # 기존 최신 json 파일의 BodyFrame SplitedBodyScripts, HalfBodyFrame SplitedBodyScripts, Context 부분 업데이트
        # LoadAndUpdateBodyFrameBodys(projectName, email, "BodyFrame", "SplitedBodyScripts", DataFramePath)
        # LoadAndUpdateBodyFrameBodys(projectName, email, "HalfBodyFrame", "SplitedBodyScripts", DataFramePath)
    if existedDataSet == None:
        SaveDataSet(projectName, email, "06", "CaptionCompletion", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None


    ########################
    ### 07_ContextDefine ###
    ########################
    InitContextDefine(projectName, email)
    InitRawDataSet(projectName, email, "ContextDefine")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "ContextDefine", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "ContextDefine", RawDataSetPath)
    mode = "Master"
    ContextDefineUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedContextDefine = UpdatedContextDefine(projectName, email)
        SaveDataFrame(projectName, email, "07_ContextDefine", updatedContextDefine, DataFramePath)
        # 기존 최신 json 파일의 BodyFrameBodys Context 부분 업데이트
        LoadAndUpdateBodyFrameBodys(projectName, email, "BodyFrame", "Bodys", DataFramePath)
    if existedDataSet == None:
        SaveDataSet(projectName, email, "07", "ContextDefine", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None


    ############################
    ### 08_ContextCompletion ###
    ############################
    InitContextCompletion(projectName, email)
    InitRawDataSet(projectName, email, "ContextCompletion")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "ContextCompletion", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "ContextCompletion", RawDataSetPath)
    mode = "Master"
    ContextCompletionUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedContextCompletion = UpdatedContextCompletion(projectName, email)
        SaveDataFrame(projectName, email, "08_ContextCompletion", updatedContextCompletion, DataFramePath)
    if existedDataSet == None:
        SaveDataSet(projectName, email, "08", "ContextCompletion", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None


    #####################
    ### 09_WMWMDefine ###
    #####################
    InitWMWMDefine(projectName, email)
    InitRawDataSet(projectName, email, "WMWMDefine")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "WMWMDefine", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "WMWMDefine", RawDataSetPath)
    mode = "Master"
    WMWMDefineUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedWMWMDefine = UpdatedWMWMDefine(projectName, email)
        SaveDataFrame(projectName, email, "09_WMWMDefine", updatedWMWMDefine, DataFramePath)
    if existedDataSet == None:
        SaveDataSet(projectName, email, "09", "WMWMDefine", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None
    
    
    #######################
    ### 10_WMWMMatching ###
    #######################
    InitWMWMMatching(projectName, email)
    InitRawDataSet(projectName, email, "WMWMMatching")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "WMWMMatching", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "WMWMMatching", RawDataSetPath)
    mode = "Example"
    WMWMMatchingUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedWMWMMatching = UpdatedWMWMMatching(projectName, email)
        SaveDataFrame(projectName, email, "10_WMWMMatching", updatedWMWMMatching, DataFramePath)
    if existedDataSet == None:
        SaveDataSet(projectName, email, "10", "WMWMMatching", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None


    ##########################
    ### 11_CharacterDefine ###
    ##########################
    InitCharacterDefine(projectName, email)
    InitRawDataSet(projectName, email, "CharacterDefine")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "CharacterDefine", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CharacterDefine", RawDataSetPath)
    mode = "Master"
    CharacterDefineUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedCharacterDefine = UpdatedCharacterDefine(projectName, email)
        SaveDataFrame(projectName, email, "11_CharacterDefine", updatedCharacterDefine, DataFramePath)
    if existedDataSet == None:
        SaveDataSet(projectName, email, "11", "CharacterDefine", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None


    ##############################
    ### 12_CharacterCompletion ###
    ##############################
    InitCharacterCompletion(projectName, email)
    InitRawDataSet(projectName, email, "CharacterCompletion")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "CharacterCompletion", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CharacterCompletion", RawDataSetPath)
    mode = "Master"
    CharacterCompletionUpdate(projectName, email, DataFramePath, bookGenre, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedCharacterCompletion = UpdatedCharacterCompletion(projectName, email)
        SaveDataFrame(projectName, email, "12_CharacterCompletion", updatedCharacterCompletion, DataFramePath)
    if existedDataSet == None:
        SaveDataSet(projectName, email, "12", "CharacterCompletion", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None


    # ########################
    # ### 14_SoundMatching ###
    # ########################
    # InitSoundMatching(projectName, email)
    # InitRawDataSet(projectName, email, "SoundMatching")
    # if existedDataFrameMode == "on":
    #     existedDataFrame = LoadexistedDataFrame(projectName, email, "SoundMatching", DataFramePath)
    #     recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "SoundMatching", RawDataSetPath)
    # mode = "Master"
    # SoundMatchingUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet, transitionImportance = 0, backgroundImportance = 0)
    
    # if existedDataFrame == None:
    #     updatedSoundMatching = UpdatedSoundMatching(projectName, email)
    #     SaveDataFrame(projectName, email, "14_SoundMatching", updatedSoundMatching, DataFramePath)
    #     # 기존 최신 json 파일의 BodyFrameBodys Context 부분 업데이트
    #     LoadAndUpdateBodyFrameBodys(projectName, email, "HalfBodyFrame", "Bodys", DataFramePath)
    # if existedDataSet == None:     
    #     SaveDataSet(projectName, email, "14", "SoundMatching", RawDataSetPath)
    # existedDataFrame = None
    # existedDataSet = None


    #######################
    ### 15_SFXMatching ###
    #######################
    InitSFXMatching(projectName, email)
    InitRawDataSet(projectName, email, "SFXMatching")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "SFXMatching", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "SFXMatching", RawDataSetPath)
    mode = "Master"
    SFXMatchingUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet, Importance = 0)
    
    if existedDataFrame == None:
        updatedSFXMatching = UpdatedSFXMatching(projectName, email)
        SaveDataFrame(projectName, email, "15_SFXMatching", updatedSFXMatching, DataFramePath)
        # 기존 최신 json 파일의 BodyFrameBodys Context 부분 업데이트
        LoadAndUpdateBodyFrameBodys(projectName, email, "HalfBodyFrame", "Bodys", DataFramePath)
    if existedDataSet == None:     
        SaveDataSet(projectName, email, "15", "SFXMatching", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None


    #########################
    ### 17-20_Translation ###
    #########################
    if Translations != []:
        for Translation in Translations:
            if Translation == 'En':
                ProcessNumber = '17'
                Process = 'TranslationEn'
            if Translation == 'Ja':
                ProcessNumber = '18'
                Process = 'TranslationJa'
            if Translation == 'Zh':
                ProcessNumber = '19'
                Process = 'TranslationZh'
            if Translation == 'Es':
                ProcessNumber = '20'
                Process = 'TranslationEs'
                
            InitCorrectionKo(projectName, email)
            InitRawDataSet(projectName, email, "CorrectionKo")
            if existedDataFrameMode == "on":
                existedDataFrame = LoadexistedDataFrame(projectName, email, "CorrectionKo", DataFramePath)
                recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CorrectionKo", RawDataSetPath)
            mode = "Master"
            CorrectionKoUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
            
            if existedDataFrame == None:
                updatedCorrectionKo = UpdatedCorrectionKo(projectName, email)
                SaveDataFrame(projectName, email, "21_CorrectionKo", updatedCorrectionKo, DataFramePath)       
                SaveDataSet(projectName, email, "21", "CorrectionKo", RawDataSetPath)
            existedDataFrame = None
            existedDataSet = None


    #######################
    ### 21_CorrectionKo ###
    #######################
    InitCorrectionKo(projectName, email)
    InitRawDataSet(projectName, email, "CorrectionKo")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "CorrectionKo", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CorrectionKo", RawDataSetPath)
    mode = "Master"
    CorrectionKoUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedCorrectionKo = UpdatedCorrectionKo(projectName, email)
        SaveDataFrame(projectName, email, "21_CorrectionKo", updatedCorrectionKo, DataFramePath)       
        SaveDataSet(projectName, email, "21", "CorrectionKo", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None
    
    
    ########################
    ### 22-25_Correction ###
    ########################
    if Translations != []:
        for Translation in Translations:
            if Translation == 'En':
                ProcessNumber = '17'
                Process = 'TranslationEn'
            if Translation == 'Ja':
                ProcessNumber = '18'
                Process = 'TranslationJa'
            if Translation == 'Zh':
                ProcessNumber = '19'
                Process = 'TranslationZh'
            if Translation == 'Es':
                ProcessNumber = '20'
                Process = 'TranslationEs'
    

    ################################
    ### 26_SelectionGenerationKo ###
    ################################
    InitSelectionGenerationKo(projectName, email)
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "SelectionGenerationKo", DataFramePath)
    SelectionGenerationKoUpdate(projectName, email, ExistedDataFrame = existedDataFrame)
    
    if existedDataFrame == None:
        updatedSelectionGenerationKo = UpdatedSelectionGenerationKo(projectName, email)
        SaveDataFrame(projectName, email, "26_SelectionGenerationKo", updatedSelectionGenerationKo, DataFramePath)       
    existedDataFrame = None
    
    
    # #################################
    # ### 27-30_SelectionGeneration ###
    # #################################
    # if Translations != []:
    #     for Translation in Translations:
    #         if Translation == 'En':
    #             ProcessNumber = '17'
    #             Process = 'TranslationEn'
    #         if Translation == 'Ja':
    #             ProcessNumber = '18'
    #             Process = 'TranslationJa'
    #         if Translation == 'Zh':
    #             ProcessNumber = '19'
    #             Process = 'TranslationZh'
    #         if Translation == 'Es':
    #             ProcessNumber = '20'
    #             Process = 'TranslationEs'

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectNameList = ['데미안', '우리는행복을진단한다', '웹3.0메타버스', '살아서천국극락낙원에가는방법']
    IndexMode = "Define"
    MessagesReview = "on"
    BookGenre = "Auto"
    ############################ 하이퍼 파라미터 설정 ############################
    
    ### Step3 : 솔루션에 프로젝트 데이터 프레임 진행 및 업데이트 ###
    for projectName in projectNameList:
        SolutionDataFrameUpdate(email, projectName, indexMode = IndexMode, messagesReview = MessagesReview, bookGenre = BookGenre)