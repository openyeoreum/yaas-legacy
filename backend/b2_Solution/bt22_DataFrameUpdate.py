import os
import re
import unicodedata
import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import AddFrameMetaDataToDB, InitIndexFrame, UpdatedIndexFrame, InitBodyFrame, UpdatedBodyFrame, InitSummaryBodyFrame, UpdatedSummaryBodyFrame, InitBodyCharacterDefine, UpdatedBodyCharacterDefine, InitBodyCharacterAnnotation, UpdatedBodyCharacterAnnotation
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import LoadExistedDataSets, AddDataSetMetaDataToDB, SaveDataSet, InitRawDataSet
from backend.b2_Solution.b24_DataFrame.b242_Script.b2421_IndexDefineUpdate import IndexFrameUpdate
from backend.b2_Solution.b24_DataFrame.b242_Script.b2422_BodyFrameUpdate import BodyFrameUpdate
from backend.b2_Solution.b24_DataFrame.b242_Script.b2423_BodySummaryUpdate import SummaryBodyFrameUpdate
from backend.b2_Solution.b24_DataFrame.b243_BodyDefine.b2431_BodyCharacterDefineUpdate import BodyCharacterDefineUpdate
from backend.b2_Solution.b24_DataFrame.b243_BodyDefine.b2432_BodyCharacterAnnotationUpdate import BodyCharacterAnnotationUpdate

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
        json.dump(UpdatedFrame, f, ensure_ascii=False, indent = 4)
        
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

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "데미안"
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    
    ### existedDataFrameMode는 개발과정에서 지속적인 데이터베이스 포멧에 따라 필요, 프로덕트에서는 필요없음.
    existedDataFrameMode = "off" # <- 개발 후 off #
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
    mode = "Example"
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
    BodyFrameUpdate(projectName, email, ExistedDataFrame = existedDataFrame)

    if existedDataFrame == None:
        updatedBodyFrame = UpdatedBodyFrame(projectName, email)
        SaveDataFrame(projectName, email, "02_BodyFrame", updatedBodyFrame, DataFramePath)
    existedDataFrame = None


    # #########################################
    # ### 03_SummaryBodyFrame-[BodySummary] ###
    # #########################################
    # InitSummaryBodyFrame(projectName, email)
    # InitRawDataSet(projectName, email, "BodySummary")
    # if existedDataFrameMode == "on":
    #     existedDataFrame = LoadexistedDataFrame(projectName, email, "SummaryBodyFrame", DataFramePath)
    #     recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "BodySummary", RawDataSetPath)
    # mode = "ExampleFineTuning" # mode의 종류: "Example", "ExampleFineTuning", "Memory", "MemoryFineTuning"
    # SummaryBodyFrameUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    # if existedDataFrame == None:
    #     updatedSummaryBodyFrame = UpdatedSummaryBodyFrame(projectName, email)
    #     SaveDataFrame(projectName, email, "03_SummaryBodyFrame", updatedSummaryBodyFrame, DataFramePath)
    #     SaveDataSet(projectName, email, "03", "BodySummary", RawDataSetPath)
    # existedDataFrame = None
    # existedDataSet = None


    ##############################
    ### 04_BodyCharacterDefine ###
    ##############################
    InitBodyCharacterDefine(projectName, email)
    InitRawDataSet(projectName, email, "BodyCharacterDefine")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "BodyCharacterDefine", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "BodyCharacterDefine", RawDataSetPath)
    mode = "ExampleFineTuning"
    BodyCharacterDefineUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedBodyCharacterDefine = UpdatedBodyCharacterDefine(projectName, email)
        SaveDataFrame(projectName, email, "04_BodyCharacterDefine", updatedBodyCharacterDefine, DataFramePath)       
        SaveDataSet(projectName, email, "04", "BodyCharacterDefine", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None


    ##################################
    ### 05_BodyCharacterAnnotation ###
    ##################################
    InitBodyCharacterAnnotation(projectName, email)
    InitRawDataSet(projectName, email, "BodyCharacterAnnotation")
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedDataFrame(projectName, email, "BodyCharacterAnnotation", DataFramePath)
        recentFile, existedDataSet = LoadExistedDataSets(projectName, email, "BodyCharacterAnnotation", RawDataSetPath)
    mode = "ExampleFineTuning"
    BodyCharacterAnnotationUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedDataFrame = existedDataFrame, ExistedDataSet = existedDataSet)
    
    if existedDataFrame == None:
        updatedBodyCharacterAnnotation = UpdatedBodyCharacterAnnotation(projectName, email)
        SaveDataFrame(projectName, email, "05_BodyCharacterAnnotation", updatedBodyCharacterAnnotation, DataFramePath)       
        SaveDataSet(projectName, email, "05", "BodyCharacterAnnotation", RawDataSetPath)
    existedDataFrame = None
    existedDataSet = None