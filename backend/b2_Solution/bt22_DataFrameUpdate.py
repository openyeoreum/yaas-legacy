import os
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

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    DataFramePath = "/yaas/backend/b5_Database/b50_DatabaseTest/b53_ProjectDataTest/"
    DataSetPath = "/yaas/backend/b5_Database/b50_DatabaseTest/b55_TrainingDataTest/"
    messagesReview = "off"
    mode = "FineTuning"
    #########################################################################

    ### 00_DataFrame-[AllMetaData] ###
    AddFrameMetaDataToDB(projectName, email)

    AddDataSetMetaDataToDB(projectName, email)


    ### 01_IndexFrame-[IndexDefine] ###
    InitIndexFrame(projectName, email)
    IndexFrameUpdate(projectName, email, MessagesReview = messagesReview)

    updatedIndexFrame = UpdatedIndexFrame(projectName, email)
    SaveDataFrame(projectName, email, "01_IndexFrame", updatedIndexFrame, DataFramePath)
    SaveDataSet(projectName, email, "01", "IndexDefinePreprocess", DataSetPath)
    SaveDataSet(projectName, email, "01", "IndexDefine", DataSetPath)


    ### 02_BodyFrame-[BodySplit, IndexTagging] ###
    InitBodyFrame(projectName, email)
    BodyFrameUpdate(projectName, email)

    updatedBodyFrame = UpdatedBodyFrame(projectName, email)
    SaveDataFrame(projectName, email, "02_BodyFrame", updatedBodyFrame, DataFramePath)


    ### 03_SummaryBodyFrame-[BodySummary] ###
    InitSummaryBodyFrame(projectName, email)
    SummaryBodyFrameUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode)

    updatedSummaryBodyFrame = UpdatedSummaryBodyFrame(projectName, email)
    SaveDataFrame(projectName, email, "03_SummaryBodyFrame", updatedSummaryBodyFrame, DataFramePath)
    SaveDataSet(projectName, email, "03", "BodySummary", DataSetPath)


    ### 04_BodyCharacterDefine ###
    InitBodyCharacterDefine(projectName, email)
    BodyCharacterDefineUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode)
    
    updatedBodyCharacterDefine = UpdatedBodyCharacterDefine(projectName, email)
    SaveDataFrame(projectName, email, "04_BodyCharacterDefine", updatedBodyCharacterDefine, DataFramePath)       
    SaveDataSet(projectName, email, "04", "BodyCharacterDefine", DataSetPath)