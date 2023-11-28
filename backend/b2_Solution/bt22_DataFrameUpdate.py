import os
import re
import unicodedata
import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import AddFrameMetaDataToDB, InitIndexFrame, UpdatedIndexFrame, InitBodyFrame, UpdatedBodyFrame, InitSummaryBodyFrame, UpdatedSummaryBodyFrame, InitContextDefine, UpdatedContextDefine, InitContextCompletion, UpdatedContextCompletion, InitNCEMDefine, UpdatedNCEMDefine, InitCharacterDefine, UpdatedCharacterDefine, InitCharacterCompletion, UpdatedCharacterCompletion, InitCorrectionKo, UpdatedCorrectionKo
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import LoadExistedDataSets, AddDataSetMetaDataToDB, SaveDataSet, InitRawDataSet
from backend.b2_Solution.b24_DataFrame.b242_Script.b2421_IndexDefineUpdate import IndexFrameUpdate
from backend.b2_Solution.b24_DataFrame.b242_Script.b2422_BodyFrameUpdate import BodyFrameUpdate
from backend.b2_Solution.b24_DataFrame.b242_Script.b2423_BodySummaryUpdate import SummaryBodyFrameUpdate
from backend.b2_Solution.b24_DataFrame.b243_Context.b2431_ContextDefineUpdate import ContextDefineUpdate
from backend.b2_Solution.b24_DataFrame.b243_Context.b2432_ContextCompletionUpdate import ContextCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b243_Context.b2433_NCEMDefineUpdate import NCEMDefineUpdate
from backend.b2_Solution.b24_DataFrame.b244_Character.b2441_CharacterDefineUpdate import CharacterDefineUpdate
from backend.b2_Solution.b24_DataFrame.b244_Character.b2442_CharacterCompletionUpdate import CharacterCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b249_Correction.b2491_CorrectionKoUpdate import CorrectionKoUpdate

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
    with open(newFilename, 'w', encoding='utf-8') as f:
        json.dump(UpdatedFrame, f, ensure_ascii = False, indent = 4)
        
def LoadexistedDataFrame(projectName, email, Process, DataFramePath):
    # 문자열 정규화
    EmailNormalized = unicodedata.normalize('NFC', email)
    ProjectNameNormalized = unicodedata.normalize('NFC', projectName)
    ProcessNormalized = unicodedata.normalize('NFC', Process)
    
    # 정규 표현식으로 파일명에서 생성날짜와 프로세스 이름 추출
    patternSTR = rf"{re.escape(EmailNormalized)}_{re.escape(ProjectNameNormalized)}_\d+_{re.escape(ProcessNormalized)}DataFrame_(\d+).json"
    pattern = re.compile(patternSTR)
    
    MaxDate = 0
    RecentFile = None

    for FileName in os.listdir(DataFramePath):
        FileNameNormalized = unicodedata.normalize('NFC', FileName)
        match = pattern.match(FileNameNormalized)
        if match:
            date = int(match.group(1))
            if date > MaxDate:
                MaxDate = date
                RecentFile = FileName

    if RecentFile:
        with open(os.path.join(DataFramePath, RecentFile), 'r', encoding='utf-8') as file:
            ExistedDataFrame = json.load(file)
            return ExistedDataFrame

    return None

## BodyFrameBodys Context 부분 json파일에 업데이트 반영
def LoadAndUpdateBodyFrameBodys(projectName, email, DataFramePath):
    Process = "BodyFrame"
    
    project = GetProject(projectName, email)
    bodyFrame = project.BodyFrame
    Bodys = bodyFrame[2]["Bodys"]
    
    # 문자열 정규화
    EmailNormalized = unicodedata.normalize('NFC', email)
    ProjectNameNormalized = unicodedata.normalize('NFC', projectName)
    ProcessNormalized = unicodedata.normalize('NFC', Process)
    
    # 정규 표현식으로 파일명에서 생성날짜와 프로세스 이름 추출
    patternSTR = rf"{re.escape(EmailNormalized)}_{re.escape(ProjectNameNormalized)}_\d+_{re.escape(ProcessNormalized)}DataFrame_(\d+).json"
    pattern = re.compile(patternSTR)
    
    MaxDate = 0
    RecentFile = None

    # 가장 최근 파일 찾기
    for FileName in os.listdir(DataFramePath):
        FileNameNormalized = unicodedata.normalize('NFC', FileName)
        match = pattern.match(FileNameNormalized)
        if match:
            date = int(match.group(1))
            if date > MaxDate:
                MaxDate = date
                RecentFile = FileName

    # 파일 읽기 및 데이터 업데이트
    if RecentFile:
        FilePath = os.path.join(DataFramePath, RecentFile)
        with open(FilePath, 'r', encoding='utf-8') as file:
            ExistedDataFrame = json.load(file)
        
        # Bodys 데이터 업데이트
        ExistedDataFrame[2]["Bodys"] = Bodys

        # 변경된 데이터 저장
        with open(FilePath, 'w', encoding='utf-8') as file:
            json.dump(ExistedDataFrame, file, ensure_ascii=False, indent=4)

    return None

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    
    ### existedDataFrameMode는 개발과정에서 지속적인 데이터베이스 포멧에 따라 필요, 프로덕트에서는 필요없음.
    existedDataFrameMode = "on" # <- 개발 후 off #
    
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
    IndexFrameUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet1 = existedDataSet1, ExistedDataSet2 = existedDataSet2)
    
    if existedDataFrame == None:
        updatedIndexFrame = UpdatedIndexFrame(projectName, email)
        SaveDataFrame(projectName, email, "01_IndexFrame", updatedIndexFrame, DataFramePath)
        SaveDataSet(projectName, email, "01", "IndexDefinePreprocess", RawDataSetPath)
        SaveDataSet(projectName, email, "01", "IndexDefine", RawDataSetPath)
    existedDataFrame = None
    existedDataSet1 = None
    existedDataSet2 = None


    ##############################################
    ### 02_BodyFrame-[BodySplit, IndexTagging] ###
    ##############################################
    InitBodyFrame(projectName, email)
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "BodyFrame", DataFramePath)
    BodyFrameUpdate(projectName, email, tokensCount = 2500, ExistedDataFrame = existedDataFrame)

    if existedDataFrame == None:
        updatedBodyFrame = UpdatedBodyFrame(projectName, email)
        SaveDataFrame(projectName, email, "02_BodyFrame", updatedBodyFrame, DataFramePath)
    existedDataFrame = None


    # #########################################
    # ### 06_SummaryBodyFrame-[BodySummary] ###
    # #########################################
    # InitSummaryBodyFrame(projectName, email)
    # InitRawDataSet(projectName, email, "BodySummary")
    # if existedDataFrameMode == "on":
    #     existedDataFrame = LoadexistedDataFrame(projectName, email, "SummaryBodyFrame", DataFramePath)
    #     recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "BodySummary", RawDataSetPath)
    # mode = "ExampleFineTuning"
    # SummaryBodyFrameUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    # if existedDataFrame == None:
    #     updatedSummaryBodyFrame = UpdatedSummaryBodyFrame(projectName, email)
    #     SaveDataFrame(projectName, email, "06_SummaryBodyFrame", updatedSummaryBodyFrame, DataFramePath)
    #     SaveDataSet(projectName, email, "06", "BodySummary", RawDataSetPath)
    # existedDataFrame = None
    # existedDataSet = None


    # ########################
    # ### 07_ContextDefine ###
    # ########################
    # InitContextDefine(projectName, email)
    # InitRawDataSet(projectName, email, "ContextDefine")
    # if existedDataFrameMode == "on":
    #     existedDataFrame = LoadexistedDataFrame(projectName, email, "ContextDefine", DataFramePath)
    #     recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "ContextDefine", RawDataSetPath)
    # mode = "Master"
    # ContextDefineUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    # if existedDataFrame == None:
    #     updatedContextDefine = UpdatedContextDefine(projectName, email)
    #     SaveDataFrame(projectName, email, "07_ContextDefine", updatedContextDefine, DataFramePath)
    #     SaveDataSet(projectName, email, "07", "ContextDefine", RawDataSetPath)
    #     # 기존 최신 json 파일의 BodyFrameBodys Context 부분 업데이트
    #     LoadAndUpdateBodyFrameBodys(projectName, email, DataFramePath)
    # existedDataFrame = None
    # existedDataSet = None


    # ############################
    # ### 08_ContextCompletion ###
    # ############################
    # InitContextCompletion(projectName, email)
    # InitRawDataSet(projectName, email, "ContextCompletion")
    # if existedDataFrameMode == "on":
    #     existedDataFrame = LoadexistedDataFrame(projectName, email, "ContextCompletion", DataFramePath)
    #     recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "ContextCompletion", RawDataSetPath)
    # mode = "Master"
    # ContextCompletionUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    # if existedDataFrame == None:
    #     updatedContextCompletion = UpdatedContextCompletion(projectName, email)
    #     SaveDataFrame(projectName, email, "08_ContextCompletion", updatedContextCompletion, DataFramePath)
    #     SaveDataSet(projectName, email, "08", "ContextCompletion", RawDataSetPath)
    # existedDataFrame = None
    # existedDataSet = None
    
    
    # #####################
    # ### 09_NCEMDefine ###
    # #####################
    # InitNCEMDefine(projectName, email)
    # InitRawDataSet(projectName, email, "NCEMDefine")
    # if existedDataFrameMode == "on":
    #     existedDataFrame = LoadexistedDataFrame(projectName, email, "NCEMDefine", DataFramePath)
    #     recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "NCEMDefine", RawDataSetPath)
    # mode = "Master"
    # NCEMDefineUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    # if existedDataFrame == None:
    #     updatedNCEMDefine = UpdatedNCEMDefine(projectName, email)
    #     SaveDataFrame(projectName, email, "09_NCEMDefine", updatedNCEMDefine, DataFramePath)
    #     SaveDataSet(projectName, email, "09", "NCEMDefine", RawDataSetPath)
    # existedDataFrame = None
    # existedDataSet = None


    # ##########################
    # ### 11_CharacterDefine ###
    # ##########################
    # InitCharacterDefine(projectName, email)
    # InitRawDataSet(projectName, email, "CharacterDefine")
    # if existedDataFrameMode == "on":
    #     existedDataFrame = LoadexistedDataFrame(projectName, email, "CharacterDefine", DataFramePath)
    #     recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CharacterDefine", RawDataSetPath)
    # mode = "Master"
    # CharacterDefineUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    # if existedDataFrame == None:
    #     updatedCharacterDefine = UpdatedCharacterDefine(projectName, email)
    #     SaveDataFrame(projectName, email, "11_CharacterDefine", updatedCharacterDefine, DataFramePath)       
    #     SaveDataSet(projectName, email, "11", "CharacterDefine", RawDataSetPath)
    # existedDataFrame = None
    # existedDataSet = None


    # ##############################
    # ### 12_CharacterCompletion ###
    # ##############################
    # InitCharacterCompletion(projectName, email)
    # InitRawDataSet(projectName, email, "CharacterCompletion")
    # if existedDataFrameMode == "on":
    #     existedDataFrame = LoadexistedDataFrame(projectName, email, "CharacterCompletion", DataFramePath)
    #     recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CharacterCompletion", RawDataSetPath)
    # mode = "Master"
    # CharacterCompletionUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    # if existedDataFrame == None:
    #     updatedCharacterCompletion = UpdatedCharacterCompletion(projectName, email)
    #     SaveDataFrame(projectName, email, "12_CharacterCompletion", updatedCharacterCompletion, DataFramePath)       
    #     SaveDataSet(projectName, email, "12", "CharacterCompletion", RawDataSetPath)
    # existedDataFrame = None
    # existedDataSet = None
    
    
    #######################
    ### 26_CorrectionKo ###
    #######################
    InitCorrectionKo(projectName, email)
    InitRawDataSet(projectName, email, "CorrectionKo")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "CorrectionKo", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "CorrectionKo", RawDataSetPath)
    mode = "Master"
    CorrectionKoUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedCorrectionKo = UpdatedCorrectionKo(projectName, email)
        SaveDataFrame(projectName, email, "26_CorrectionKo", updatedCorrectionKo, DataFramePath)       
        SaveDataSet(projectName, email, "26", "CorrectionKo", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None