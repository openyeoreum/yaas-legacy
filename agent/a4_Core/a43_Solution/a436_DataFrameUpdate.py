import os
import re
import unicodedata
import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from agent.a4_Core.a42_Access.a424_GetProcessData import GetProject
from agent.a5_Solution.a54_Audiobook.a541_DataCommit.a5411_DataFrameCommit import FindDataframeFilePaths, AddFrameMetaDataToDB, InitScriptGen, UpdatedScriptGen, InitBookPreprocess, UpdatedBookPreprocess, InitIndexFrame, UpdatedIndexFrame, InitDuplicationPreprocess, UpdatedDuplicationPreprocess, InitPronunciationPreprocess, UpdatedPronunciationPreprocess, InitBodyFrame, UpdatedBodyFrame, InitHalfBodyFrame, UpdatedHalfBodyFrame, InitCaptionCompletion, UpdatedCaptionCompletion, InitContextDefine, UpdatedContextDefine, InitContextCompletion, UpdatedContextCompletion, InitWMWMDefine, UpdatedWMWMDefine, InitWMWMMatching, UpdatedWMWMMatching, InitCharacterDefine, UpdatedCharacterDefine, InitCharacterCompletion, UpdatedCharacterCompletion, InitSoundMatching, UpdatedSoundMatching, InitSFXMatching, UpdatedSFXMatching, InitCorrectionKo, UpdatedCorrectionKo, InitSelectionGenerationKo, UpdatedSelectionGenerationKo
from agent.a5_Solution.a54_Audiobook.a541_DataCommit.a5412_DataSetCommit import LoadExistedDataSets, AddDataSetMetaDataToDB, SaveDataSet, InitRawDataSet
from agent.a5_Solution.a54_Audiobook.a542_Script.a5420_BookPreprocessUpdate import BookPreprocessUpdate
from agent.a5_Solution.a54_Audiobook.a542_Script.a5421_IndexDefineUpdate import IndexFrameUpdate
from agent.a5_Solution.a54_Audiobook.a542_Script.a5422_DuplicationPreprocessUpdate import DuplicationPreprocessUpdate
from agent.a5_Solution.a54_Audiobook.a542_Script.a5423_PronunciationPreprocessUpdate import PronunciationPreprocessUpdate
from agent.a5_Solution.a54_Audiobook.a542_Script.a5424_BodyFrameUpdate import BodyFrameUpdate
from agent.a5_Solution.a54_Audiobook.a542_Script.a5425_HalfBodyFrameUpdate import HalfBodyFrameUpdate
from agent.a5_Solution.a54_Audiobook.a542_Script.a5426_CaptionCompletionUpdate import CaptionCompletionUpdate
from agent.a5_Solution.a54_Audiobook.a543_Context.a5431_ContextDefineUpdate import ContextDefineUpdate
from agent.a5_Solution.a54_Audiobook.a543_Context.a5432_ContextCompletionUpdate import ContextCompletionUpdate
from agent.a5_Solution.a54_Audiobook.a543_Context.a5433_WMWMDefineUpdate import WMWMDefineUpdate
from agent.a5_Solution.a54_Audiobook.a543_Context.a5434_WMWMMatchingUpdate import WMWMMatchingUpdate
from agent.a5_Solution.a54_Audiobook.a544_Character.a5441_CharacterDefineUpdate import CharacterDefineUpdate
from agent.a5_Solution.a54_Audiobook.a544_Character.a5442_CharacterCompletionUpdate import CharacterCompletionUpdate
from agent.a5_Solution.a54_Audiobook.a546_Sound.a5461_SoundMatchingUpdate import SoundMatchingUpdate
from agent.a5_Solution.a54_Audiobook.a547_SFX.a5471_SFXMatchingUpdate import SFXMatchingUpdate
from agent.a5_Solution.a54_Audiobook.a549_Correction.a5491_CorrectionKoUpdate import CorrectionKoUpdate
from agent.a5_Solution.a54_Audiobook.a5410_SelectionGeneration.a54101_SelectionGenerationKo import SelectionGenerationKoUpdate

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
def SaveDataFrame(projectName, email, Process, UpdatedFrame, RawDataFramePath):
    # 현재 날짜 및 시간을 가져옵니다.
    filename = RawDataFramePath + email + '_' + projectName + '_' + Process + 'DataFrame_' + str(Date()) + '.json'
    
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
        bodyFrame = project["BodyFrame"]
    elif Process == "HalfBodyFrame":
        bodyFrame = project["HalfBodyFrame"]

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
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}/{projectName}/{projectName}_audiobook/{projectName}_dataset_audiobook_file/"
    
    ### existedDataFrameMode는 개발과정에서 지속적인 데이터베이스 포멧에 따라 필요, 프로덕트에서는 필요없음.
    existedDataFrameMode = "on" # <- 개발 후 off #
    
    ProjectConfig = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}/{projectName}/{projectName}_config.json"
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


    #########################
    ### 00_BookPreprocess ###
    #########################
    if ScriptConfig == {}:
        if existedDataFrameMode == "on":
            existedDataFrame = LoadexistedDataFrame(projectName, email, "BookPreprocessFrame", DataFramePath)
            recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "BookPreprocess", RawDataSetPath)
        
        if existedDataFrame == None:
            InitBookPreprocess(projectName, email)
        if existedDataSet == None:
            InitRawDataSet(projectName, email, "BookPreprocess")

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
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "IndexFrame", DataFramePath)
        recentFile, existedDataSet1 = LoadExistedDataSets(projectName, email, "IndexDefinePreprocess", RawDataSetPath)
        recentFile, existedDataSet2 = LoadExistedDataSets(projectName, email, "IndexDefine", RawDataSetPath)

    if existedDataFrame == None:
        InitIndexFrame(projectName, email)
    if existedDataSet1 == None:
        InitRawDataSet(projectName, email, "IndexDefinePreprocess")
        InitRawDataSet(projectName, email, "IndexDefine")

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
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "DuplicationPreprocess", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "DuplicationPreprocess", RawDataSetPath)

    if existedDataFrame == None:
        InitDuplicationPreprocess(projectName, email)
    if existedDataSet == None:
        InitRawDataSet(projectName, email, "DuplicationPreprocess")

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
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "PronunciationPreprocess", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "PronunciationPreprocess", RawDataSetPath)

    if existedDataFrame == None:
        InitPronunciationPreprocess(projectName, email)
    if existedDataSet == None:
        InitRawDataSet(projectName, email, "PronunciationPreprocess")

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
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "BodyFrame", DataFramePath)

    if existedDataFrame == None:
        InitBodyFrame(projectName, email)

    BodyFrameUpdate(projectName, email, tokensCount = 2500, ExistedDataFrame = existedDataFrame)

    if existedDataFrame == None:
        updatedBodyFrame = UpdatedBodyFrame(projectName, email)
        SaveDataFrame(projectName, email, "03_BodyFrame", updatedBodyFrame, DataFramePath)
    existedDataFrame = None
    
    
    ##################################################
    ### 04_HalfBodyFrame-[BodySplit, IndexTagging] ###
    ##################################################
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "HalfBodyFrame", DataFramePath)

    if existedDataFrame == None:
        InitHalfBodyFrame(projectName, email)

    HalfBodyFrameUpdate(projectName, email, tokensCount = 750, ExistedDataFrame = existedDataFrame)

    if existedDataFrame == None:
        updatedHalfBodyFrame = UpdatedHalfBodyFrame(projectName, email)
        SaveDataFrame(projectName, email, "04_HalfBodyFrame", updatedHalfBodyFrame, DataFramePath)
    existedDataFrame = None


    ############################
    ### 06_CaptionCompletion ###
    ############################
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "CaptionCompletion", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CaptionCompletion", RawDataSetPath)

    if existedDataFrame == None:
        InitCaptionCompletion(projectName, email)
    if existedDataSet == None:
        InitRawDataSet(projectName, email, "CaptionCompletion")

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
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "ContextDefine", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "ContextDefine", RawDataSetPath)

    if existedDataFrame == None:
        InitContextDefine(projectName, email)
    if existedDataSet == None:
        InitRawDataSet(projectName, email, "ContextDefine")

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
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "ContextCompletion", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "ContextCompletion", RawDataSetPath)

    if existedDataFrame == None:
        InitContextCompletion(projectName, email)
    if existedDataSet == None:
        InitRawDataSet(projectName, email, "ContextCompletion")

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
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "WMWMDefine", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "WMWMDefine", RawDataSetPath)

    if existedDataFrame == None:
        InitWMWMDefine(projectName, email)
    if existedDataSet == None:
        InitRawDataSet(projectName, email, "WMWMDefine")

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
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "WMWMMatching", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "WMWMMatching", RawDataSetPath)

    if existedDataFrame == None:
        InitWMWMMatching(projectName, email)
    if existedDataSet == None:
        InitRawDataSet(projectName, email, "WMWMMatching")

    mode = "Master"
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
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "CharacterDefine", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CharacterDefine", RawDataSetPath)

    if existedDataFrame == None:
        InitCharacterDefine(projectName, email)
    if existedDataSet == None:
        InitRawDataSet(projectName, email, "CharacterDefine")

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
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "CharacterCompletion", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CharacterCompletion", RawDataSetPath)
    if existedDataFrame == None:
        InitCharacterCompletion(projectName, email)
    if existedDataSet == None:
        InitRawDataSet(projectName, email, "CharacterCompletion")

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
    # if existedDataFrameMode == "on":
    #     existedDataFrame = LoadexistedDataFrame(projectName, email, "SoundMatching", DataFramePath)
    #     recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "SoundMatching", RawDataSetPath)

    # if existedDataFrame == None:
    #     InitSoundMatching(projectName, email)
    # if existedDataSet == None:
    #     InitRawDataSet(projectName, email, "SoundMatching")

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
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "SFXMatching", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "SFXMatching", RawDataSetPath)

    if existedDataFrame == None:
        InitSFXMatching(projectName, email)
    if existedDataSet == None:
        InitRawDataSet(projectName, email, "SFXMatching")

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


    #######################
    ### 21_CorrectionKo ###
    #######################
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "CorrectionKo", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CorrectionKo", RawDataSetPath)

    if existedDataFrame == None:
        InitCorrectionKo(projectName, email)
    if existedDataSet == None:
        InitRawDataSet(projectName, email, "CorrectionKo")

    mode = "Master"
    CorrectionKoUpdate(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedCorrectionKo = UpdatedCorrectionKo(projectName, email)
        SaveDataFrame(projectName, email, "21_CorrectionKo", updatedCorrectionKo, DataFramePath)       
        SaveDataSet(projectName, email, "21", "CorrectionKo", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None


    ################################
    ### 26_SelectionGenerationKo ###
    ################################
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "SelectionGenerationKo", DataFramePath)

    if existedDataFrame == None:
        InitSelectionGenerationKo(projectName, email)

    SelectionGenerationKoUpdate(projectName, email, ExistedDataFrame = existedDataFrame)
    
    if existedDataFrame == None:
        updatedSelectionGenerationKo = UpdatedSelectionGenerationKo(projectName, email)
        SaveDataFrame(projectName, email, "26_SelectionGenerationKo", updatedSelectionGenerationKo, DataFramePath)       
    existedDataFrame = None


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