import os
import re
import unicodedata
import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import AddFrameMetaDataToDB, InitIndexFrame, UpdatedIndexFrame, InitBodyFrame, UpdatedBodyFrame, InitSummaryBodyFrame, UpdatedSummaryBodyFrame, InitBodyCharacterDefine, UpdatedBodyCharacterDefine
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddDataSetMetaDataToDB, SaveDataSet
from backend.b2_Solution.b24_DataFrame.b242_Script.b2421_IndexDefineUpdate import IndexFrameUpdate
from backend.b2_Solution.b24_DataFrame.b242_Script.b2422_BodyFrameUpdate import BodyFrameUpdate
from backend.b2_Solution.b24_DataFrame.b242_Script.b2423_BodySummaryUpdate import SummaryBodyFrameUpdate
from backend.b2_Solution.b24_DataFrame.b243_BodyDefine.b2431_BodyCharacterDefineUpdate import BodyCharacterDefineUpdate

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
def SaveDataFrame(projectName, email, Process, UpdatedFrame, DataSetPath):
    # 현재 날짜 및 시간을 가져옵니다.
    filename = DataSetPath + email + '_' + projectName + '_' + Process + 'DataFrame_' + str(Date()) + '.json'
    
    base, ext = os.path.splitext(filename)
    counter = 0
    newFilename = filename
    while os.path.exists(newFilename):
        counter += 1
        newFilename = f"{base}({counter}) {ext}"
    with open(newFilename, 'w', encoding='utf-8') as f:
        json.dump(UpdatedFrame, f, ensure_ascii=False, indent=4)
        
def LoadExistedFrame(projectName, email, ProcessNumber, ProjectDataTestPath):
    # 문자열 정규화
    EmailNormalized = unicodedata.normalize('NFD', email)
    ProjectNameNormalized = unicodedata.normalize('NFD', projectName)
    
    # 정규 표현식으로 파일명에서 생성날짜 추출
    patternSTR = rf"{re.escape(EmailNormalized)}_{re.escape(ProjectNameNormalized)}_{ProcessNumber}_\w+_(\d+).json"
    pattern = re.compile(patternSTR)
    
    MaxDate = 0
    RecentFile = None

    for FileName in os.listdir(ProjectDataTestPath):
        FileNameNormalized = unicodedata.normalize('NFD', FileName)
        match = pattern.match(FileNameNormalized)       
        if match:
            date = int(match.group(1))
            if date > MaxDate:
                MaxDate = date
                RecentFile = FileName  # 원본 파일명을 반환합니다.

    if RecentFile:
        with open(os.path.join(ProjectDataTestPath, RecentFile), 'r', encoding='utf-8') as file:
            ExistedFrame = json.load(file)
            return ExistedFrame

    return None

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "살아서천국극락낙원에가는방법"
    DataFramePath = "/yaas/backend/b5_Database/b50_DatabaseTest/b53_ProjectDataTest/"
    DataSetPath = "/yaas/backend/b5_Database/b50_DatabaseTest/b55_TrainingDataTest/"
    ProjectDataTestPath = "/yaas/backend/b5_Database/b50_DatabaseTest/b53_ProjectDataTest/"
    messagesReview = "on"
    
    ### existedFrameMode는 개발과정에서 지속적인 데이터베이스 포멧에 따라 필요, 프로덕트에서는 필요없음.
    existedFrameMode = "on" # <- 개발 후 off #
    existedFrame = None
    #########################################################################
    

    ### 00_DataFrame-[AllMetaData] ###
    AddFrameMetaDataToDB(projectName, email)

    AddDataSetMetaDataToDB(projectName, email)


    ### 01_IndexFrame-[IndexDefine] ###
    InitIndexFrame(projectName, email)
    if existedFrameMode == "on":
        existedFrame = LoadExistedFrame(projectName, email, "01", ProjectDataTestPath)
    mode = "Example"
    IndexFrameUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedFrame = existedFrame)
    
    if existedFrame == None:
        updatedIndexFrame = UpdatedIndexFrame(projectName, email)
        SaveDataFrame(projectName, email, "01_IndexFrame", updatedIndexFrame, DataFramePath)
        SaveDataSet(projectName, email, "01", "IndexDefinePreprocess", DataSetPath)
        SaveDataSet(projectName, email, "01", "IndexDefine", DataSetPath)


    ### 02_BodyFrame-[BodySplit, IndexTagging] ###
    InitBodyFrame(projectName, email)
    if existedFrameMode == "on":
        existedFrame = LoadExistedFrame(projectName, email, "02", ProjectDataTestPath)
    BodyFrameUpdate(projectName, email, ExistedFrame = existedFrame)

    if existedFrame == None:
        updatedBodyFrame = UpdatedBodyFrame(projectName, email)
        SaveDataFrame(projectName, email, "02_BodyFrame", updatedBodyFrame, DataFramePath)


    # ### 03_SummaryBodyFrame-[BodySummary] ###
    # InitSummaryBodyFrame(projectName, email)
    # if existedFrameMode == "on":
    #     existedFrame = LoadExistedFrame(projectName, email, "03", ProjectDataTestPath)
    # mode = "ExampleFineTuning" # mode의 종류: "Example", "ExampleFineTuning", "Memory", "MemoryFineTuning"
    # SummaryBodyFrameUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedFrame = existedFrame)
    
    # if existedFrame == None:
    #     updatedSummaryBodyFrame = UpdatedSummaryBodyFrame(projectName, email)
    #     SaveDataFrame(projectName, email, "03_SummaryBodyFrame", updatedSummaryBodyFrame, DataFramePath)
    #     SaveDataSet(projectName, email, "03", "BodySummary", DataSetPath)


    ### 04_BodyCharacterDefine ###
    InitBodyCharacterDefine(projectName, email)
    if existedFrameMode == "on":
        existedFrame = LoadExistedFrame(projectName, email, "04", ProjectDataTestPath)
    mode = "ExampleFineTuning"
    BodyCharacterDefineUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode, ExistedFrame = existedFrame)
    
    if existedFrame == None:
        updatedBodyCharacterDefine = UpdatedBodyCharacterDefine(projectName, email)
        SaveDataFrame(projectName, email, "04_BodyCharacterDefine", updatedBodyCharacterDefine, DataFramePath)       
        SaveDataSet(projectName, email, "04", "BodyCharacterDefine", DataSetPath)