import os
import re
import unicodedata
import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraph, GetVideo
from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import AddLifeGraphMetaDataToDB, InitLifeGraphFrame, UpdatedLifeGraphFrame
from extension.e1_Solution.e13_ExtensionDataFrame.e132_LifeGraphDataFrame.e1321_LifeGraphFrameUpdate import LifeGraphFrameUpdate

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
def SaveExtensionDataFrame(lifeGraphSetName, latestUpdateDate, Process, UpdatedFrame, RawDataSetPath):
    # 현재 날짜 및 시간을 가져옵니다.
    filename = RawDataSetPath + str(latestUpdateDate) + '_' + lifeGraphSetName + '_' + Process + 'DataFrame_' + str(Date()) + '.json'
    
    base, ext = os.path.splitext(filename)
    counter = 0
    newFilename = filename
    while os.path.exists(newFilename):
        counter += 1
        newFilename = f"{base} ({counter}){ext}"
    with open(newFilename, 'w', encoding='utf-8') as f:
        json.dump(UpdatedFrame, f, ensure_ascii = False, indent = 4)
        
def LoadexistedExtensionDataFrame(lifeGraphSetName, latestUpdateDate, Process, DataFramePath):
    # 문자열 정규화
    latestUpdateDateNormalized = unicodedata.normalize('NFC', str(latestUpdateDate))
    lifeGraphSetNameNormalized = unicodedata.normalize('NFC', lifeGraphSetName)
    ProcessNormalized = unicodedata.normalize('NFC', Process)
    
    # 정규 표현식으로 파일명에서 생성날짜와 프로세스 이름 추출
    patternSTR = rf"{re.escape(latestUpdateDateNormalized)}_{re.escape(lifeGraphSetNameNormalized)}_\d+_{re.escape(ProcessNormalized)}DataFrame_(\d+).json"
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
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    
    ### existedDataFrameMode는 개발과정에서 지속적인 데이터베이스 포멧에 따라 필요, 프로덕트에서는 필요없음.
    existedDataFrameMode = "on" # <- 개발 후 off #
    
    # existedDataFrame 초기화
    existedDataFrame = None
    #########################################################################


    ###########################################
    ### 00_ExtensionDataFrame-[AllMetaData] ###
    ###########################################
    AddLifeGraphMetaDataToDB(lifeGraphSetName, latestUpdateDate)


    #########################
    ### 01_LifeGraphFrame ###
    #########################
    InitLifeGraphFrame(lifeGraphSetName, latestUpdateDate)
    if existedDataFrameMode == "on":
        existedDataFrame = LoadexistedExtensionDataFrame(lifeGraphSetName, latestUpdateDate, "LifeGraphFrame", LifeGraphDataFramePath)
    LifeGraphFrameUpdate(lifeGraphSetName, latestUpdateDate, QUALITY = 6, ExistedDataFrame = existedDataFrame)

    if existedDataFrame == None:
        updatedLifeGraphFrame = UpdatedLifeGraphFrame(lifeGraphSetName, latestUpdateDate)
        SaveExtensionDataFrame(lifeGraphSetName, latestUpdateDate, "01_LifeGraphFrame", updatedLifeGraphFrame, LifeGraphDataFramePath)
    existedDataFrame = None