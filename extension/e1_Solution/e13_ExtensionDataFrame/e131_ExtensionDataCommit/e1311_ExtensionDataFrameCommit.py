import os
import re
import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import LifeGraph
from backend.b1_Api.b13_Database import get_db
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraph, GetVideo
from extension.e1_Solution.e12_ExtensionProject.e121_LifeGraph.e1211_LifeGraphCommit import GetLifeGraphDataPath, LoadJsonFrame

############################################
########## DataFrameCommitGeneral ##########
############################################

## 오늘 날짜
def Date(Option = "Day"):
    if Option == "Day":
      now = datetime.now()
      date = now.strftime('%y%m%d')
    elif Option == "Second":
      now = datetime.now()
      date = now.strftime('%y%m%d%H%M%S')
    
    return date

## 업데이트된 OutputMemoryDics 파일 Count 불러오기
def LoadExtensionOutputMemory(lifeGraphSetName, latestUpdateDate, ProcessNum, DataFramePath):
    # 정규 표현식 패턴 정의
    pattern = re.compile(rf"{re.escape(DataFramePath + str(latestUpdateDate) + '_' + lifeGraphSetName + '_' + ProcessNum + '_')}outputMemoryDics_.*\.json")

    OutputMemoryDicsFile = []
    OutputMemoryCount = 0
    for filename in os.listdir(DataFramePath):
        FullPath = os.path.join(DataFramePath, filename)
        if pattern.match(FullPath):
            with open(FullPath, 'r', encoding='utf-8') as file:
                OutputMemoryDicsFile = json.load(file)
            OutputMemoryCount = len(OutputMemoryDicsFile)
            break  # 첫 번째 일치하는 파일을 찾으면 반복 종료

    return OutputMemoryDicsFile, OutputMemoryCount

## 업데이트된 OutputMemoryDics 파일 저장하기
def SaveExtensionOutputMemory(lifeGraphSetName, latestUpdateDate, OutputMemoryDics, ProcessNum, DataFramePath):
    # 정규 표현식 패턴 정의
    pattern = re.compile(rf"{re.escape(str(latestUpdateDate) + '_' + lifeGraphSetName + '_' + ProcessNum + '_outputMemoryDics_')}.*\.json")

    # 일치하는 파일 검색
    matched_file = None
    for filename in os.listdir(DataFramePath):
        if pattern.match(filename):
            matched_file = filename
            break

    if matched_file:
        # 일치하는 파일이 있는 경우
        OutputMemoryDicsFilename = os.path.join(DataFramePath, matched_file)
    else:
        # 일치하는 파일이 없는 경우 새 파일명 생성
        OutputMemoryDicsFilename = os.path.join(DataFramePath, str(latestUpdateDate) + '_' + lifeGraphSetName + '_' + ProcessNum + '_outputMemoryDics_' + str(Date()) + '.json')

    # OutputMemoryDics 데이터를 파일에 덮어쓰기
    with open(OutputMemoryDicsFilename, 'w', encoding='utf-8') as file:
        json.dump(OutputMemoryDics, file, ensure_ascii = False, indent = 4)

###############################
########## LifeGraph ##########
###############################

######################################################
##### 0. 전체 LifeGraph의 MetaData(식별)부분을 업데이트 #####
######################################################
def AddLifeGraphMetaDataToDB(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)

        if not lifeGraph:
            print("LifeGraph not found!")
            return
        
        for column in LifeGraph.__table__.columns:
            if column.name == 'LifeGraphSets':  # LifeGraphSets 컬럼은 건너뜁니다.
                continue
            
            if isinstance(column.type, JSON):
                ProcessData = getattr(lifeGraph, column.name)
                if ProcessData is None:
                    continue
                ProcessData[0]["LifeGraphSetId"] = lifeGraph.LifeGraphSetId
                ProcessData[0]["LifeGraphSetDate"] = lifeGraph.LifeGraphSetDate
                ProcessData[0]["LifeGraphSetName"] = lifeGraph.LifeGraphSetName
                ProcessData[0]["LifeGraphSetManager"] = lifeGraph.LifeGraphSetManager
                ProcessData[0]["LifeGraphSetSource"] = lifeGraph.LifeGraphSetSource
                ProcessData[0]["LatestUpdateDate"] = lifeGraph.LatestUpdateDate
                ProcessData[0]["Language"] = lifeGraph.LifeGraphSetLanguage
                setattr(lifeGraph, column.name, ProcessData)
                flag_modified(lifeGraph, column.name)

        db.add(lifeGraph)
        db.commit()
    

#####################################
##### 01_LifeGraphFrame Process #####
#####################################
## 1. 1-0 LifeGraphFrame이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedLifeGraphFrameToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        
        lifeGraph.LifeGraphFrame[1] = ExistedDataFrame[1]
        lifeGraph.LifeGraphFrame[2] = ExistedDataFrame[2]
        
        flag_modified(lifeGraph, "LifeGraphFrame")
        
        db.add(lifeGraph)
        db.commit()


## 1. 1-1 LifeGraphFrame의 LifeGraphs부분 업데이트 형식
def UpdateLifeGraphs(lifeGraph, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Residence, PhoneNumber, Email, Quality, LifeData):
    
    updateLifeGraphs = {
        "LifeGraphId": LifeGraphId,
        "LifeGraphDate": LifeGraphDate,
        "Name": Name,
        "Age": Age,
        "Source": Source,
        "Language": Language,
        "Residence": Residence,
        "PhoneNumber": PhoneNumber,
        "Email": Email,
        "Quality": Quality,
        "LifeData": LifeData
    }
    
    lifeGraph.LifeGraphFrame[1]["LifeGraphs"].append(updateLifeGraphs)
    # Count 업데이트
    lifeGraph.LifeGraphFrame[0]["LifeGraphCount"] = LifeGraphId

## 1. 1-2 LifeGraphFrame의 LifeGraphs부분 업데이트
def AddLifeGraphFrameLifeGraphsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Residence, PhoneNumber, Email, Quality, LifeData):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateLifeGraphs(lifeGraph, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Residence, PhoneNumber, Email, Quality, LifeData)
        
        flag_modified(lifeGraph, "LifeGraphFrame")
        
        db.add(lifeGraph)
        db.commit()

## 1. 1-3 LifeGraphFrame의 LifeDataTexts부분 업데이트 형식
def UpdateLifeDataTexts(lifeGraph, LifeGraphId, Language, TextGlobal):
    
    updateLifeDataTexts = {
        "LifeGraphId": LifeGraphId,
        "Language": Language,
        "TextGlobal": TextGlobal
    }
    
    lifeGraph.LifeGraphFrame[2]["LifeDataTexts"].append(updateLifeDataTexts)
    # Count 업데이트
    lifeGraph.LifeGraphFrame[0]["LifeDataTextsCount"] = LifeGraphId

## 1. 1-4 LifeGraphFrame의 LifeDataTexts부분 업데이트
def AddLifeGraphFrameLifeDataTextsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Language, TextGlobal):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateLifeDataTexts(lifeGraph, LifeGraphId, Language, TextGlobal)
        
        flag_modified(lifeGraph, "LifeGraphFrame")
        
        db.add(lifeGraph)
        db.commit()

## 1. LifeGraphFrameCount 가져오기
def LifeGraphFrameCountLoad(lifeGraphSetName, latestUpdateDate):

    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphCount = lifeGraph.LifeGraphFrame[0]["LifeGraphCount"]
    LifeDataTextsCount = lifeGraph.LifeGraphFrame[0]["LifeDataTextsCount"]
    Completion = lifeGraph.LifeGraphFrame[0]["Completion"]
    
    return LifeGraphCount, LifeDataTextsCount, Completion
        
## 1. LifeGraphFrame의 초기화
def InitLifeGraphFrame(lifeGraphSetName, latestUpdateDate):
    LifeGraphDataPath = GetLifeGraphDataPath()
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        lifeGraph.LifeGraphFrame[0]["LifeGraphCount"] = 0
        lifeGraph.LifeGraphFrame[0]["LifeDataTextsCount"] = 0
        lifeGraph.LifeGraphFrame[0]["Completion"] = "No"
        lifeGraph.LifeGraphFrame[1] = LoadJsonFrame(LifeGraphDataPath + "/e4211_RawData/e4211-02_LifeGraphFrame.json")[1]
        
        flag_modified(lifeGraph, "LifeGraphFrame")
        
        db.add(lifeGraph)
        db.commit()
        
## 1. 업데이트된 LifeGraphFrame 출력
def UpdatedLifeGraphFrame(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)

    return lifeGraph.LifeGraphFrame

## 1. LifeGraphFrameCompletion 업데이트
def LifeGraphFrameCompletionUpdate(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:

        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        lifeGraph.LifeGraphFrame[0]["Completion"] = "Yes"

        flag_modified(lifeGraph, "LifeGraphFrame")

        db.add(lifeGraph)
        db.commit()
        
#############################################
##### 02_LifeGraphTranslationKo Process #####
#############################################
## 2. 1-0 LifeGraphTranslationKo이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedLifeGraphTranslationKoToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        
        lifeGraph.LifeGraphTranslationKo[1] = ExistedDataFrame[1]
        lifeGraph.LifeGraphTranslationKo[2] = ExistedDataFrame[2]
        
        flag_modified(lifeGraph, "LifeGraphTranslationKo")
        
        db.add(lifeGraph)
        db.commit()


## 2. 1-1 LifeGraphTranslationKo의 LifeGraphs부분 업데이트 형식
def UpdateLifeGraphsKo(lifeGraph, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Translation, Residence, PhoneNumber, Email, Quality, LifeData):
    
    updateLifeGraphsKo = {
        "LifeGraphId": LifeGraphId,
        "LifeGraphDate": LifeGraphDate,
        "Name": Name,
        "Age": Age,
        "Source": Source,
        "Language": Language,
        "Translation": Translation,
        "Residence": Residence,
        "PhoneNumber": PhoneNumber,
        "Email": Email,
        "Quality": Quality,
        "LifeData": LifeData
    }
    
    lifeGraph.LifeGraphTranslationKo[1]["LifeGraphsKo"].append(updateLifeGraphsKo)
    # Count 업데이트
    lifeGraph.LifeGraphTranslationKo[0]["LifeGraphCount"] = LifeGraphId

## 2. 1-2 LifeGraphTranslationKo의 LifeGraphs부분 업데이트
def AddLifeGraphTranslationKoLifeGraphsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Translation, Residence, PhoneNumber, Email, Quality, LifeData):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateLifeGraphsKo(lifeGraph, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Translation, Residence, PhoneNumber, Email, Quality, LifeData)
        
        flag_modified(lifeGraph, "LifeGraphTranslationKo")
        
        db.add(lifeGraph)
        db.commit()

## 2. 1-3 LifeGraphTranslationKo의 LifeDataTexts부분 업데이트 형식
def UpdateLifeDataTextsKo(lifeGraph, LifeGraphId, Language, Translation, TextKo):
    
    updateLifeDataTextsKo = {
        "LifeGraphId": LifeGraphId,
        "Language": Language,
        "Translation": Translation,
        "TextKo": TextKo
    }
    
    lifeGraph.LifeGraphTranslationKo[2]["LifeDataTextsKo"].append(updateLifeDataTextsKo)
    # Count 업데이트
    lifeGraph.LifeGraphTranslationKo[0]["LifeDataTextsCount"] = LifeGraphId

## 2. 1-4 LifeGraphTranslationKo의 LifeDataTexts부분 업데이트
def AddLifeGraphTranslationKoLifeDataTextsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Language, Translation, TextKo):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateLifeDataTextsKo(lifeGraph, LifeGraphId, Language, Translation, TextKo)
        
        flag_modified(lifeGraph, "LifeGraphTranslationKo")
        
        db.add(lifeGraph)
        db.commit()

## 2. LifeGraphTranslationKoCount 가져오기
def LifeGraphTranslationKoCountLoad(lifeGraphSetName, latestUpdateDate):

    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphCount = lifeGraph.LifeGraphTranslationKo[0]["LifeGraphCount"]
    LifeDataTextsCount = lifeGraph.LifeGraphTranslationKo[0]["LifeDataTextsCount"]
    Completion = lifeGraph.LifeGraphTranslationKo[0]["Completion"]
    
    return LifeGraphCount, LifeDataTextsCount, Completion
        
## 2. LifeGraphTranslationKo의 초기화
def InitLifeGraphTranslationKo(lifeGraphSetName, latestUpdateDate):
    LifeGraphDataPath = GetLifeGraphDataPath()
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        lifeGraph.LifeGraphTranslationKo[0]["LifeGraphCount"] = 0
        lifeGraph.LifeGraphTranslationKo[0]["LifeDataTextsCount"] = 0
        lifeGraph.LifeGraphTranslationKo[0]["Completion"] = "No"
        lifeGraph.LifeGraphTranslationKo[1] = LoadJsonFrame(LifeGraphDataPath + "/e4212_Preprocess/e4212-01_LifeGraphTranslationKo.json")[1]
        
        flag_modified(lifeGraph, "LifeGraphTranslationKo")
        
        db.add(lifeGraph)
        db.commit()
        
## 2. 업데이트된 LifeGraphTranslationKo 출력
def UpdatedLifeGraphTranslationKo(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)

    return lifeGraph.LifeGraphTranslationKo

## 2. LifeGraphTranslationKoCompletion 업데이트
def LifeGraphTranslationKoCompletionUpdate(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:

        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        lifeGraph.LifeGraphTranslationKo[0]["Completion"] = "Yes"

        flag_modified(lifeGraph, "LifeGraphTranslationKo")

        db.add(lifeGraph)
        db.commit()
        
#############################################
##### 03_LifeGraphTranslationEn Process #####
#############################################
## 3. 1-0 LifeGraphTranslationEn이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedLifeGraphTranslationEnToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        
        lifeGraph.LifeGraphTranslationEn[1] = ExistedDataFrame[1]
        lifeGraph.LifeGraphTranslationEn[2] = ExistedDataFrame[2]
        
        flag_modified(lifeGraph, "LifeGraphTranslationEn")
        
        db.add(lifeGraph)
        db.commit()


## 3. 1-1 LifeGraphTranslationEn의 LifeGraphs부분 업데이트 형식
def UpdateLifeGraphsEn(lifeGraph, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Translation, Residence, PhoneNumber, Email, Quality, LifeData):
    
    updateLifeGraphsEn = {
        "LifeGraphId": LifeGraphId,
        "LifeGraphDate": LifeGraphDate,
        "Name": Name,
        "Age": Age,
        "Source": Source,
        "Language": Language,
        "Translation": Translation,
        "Residence": Residence,
        "PhoneNumber": PhoneNumber,
        "Email": Email,
        "Quality": Quality,
        "LifeData": LifeData
    }
    
    lifeGraph.LifeGraphTranslationEn[1]["LifeGraphsEn"].append(updateLifeGraphsEn)
    # Count 업데이트
    lifeGraph.LifeGraphTranslationEn[0]["LifeGraphCount"] = LifeGraphId

## 3. 1-2 LifeGraphTranslationEn의 LifeGraphs부분 업데이트
def AddLifeGraphTranslationEnLifeGraphsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Translation, Residence, PhoneNumber, Email, Quality, LifeData):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateLifeGraphsEn(lifeGraph, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Translation, Residence, PhoneNumber, Email, Quality, LifeData)
        
        flag_modified(lifeGraph, "LifeGraphTranslationEn")
        
        db.add(lifeGraph)
        db.commit()

## 3. 1-3 LifeGraphTranslationEn의 LifeDataTexts부분 업데이트 형식
def UpdateLifeDataTextsEn(lifeGraph, LifeGraphId, Language, Translation, TextEn):
    
    updateLifeDataTextsEn = {
        "LifeGraphId": LifeGraphId,
        "Language": Language,
        "Translation": Translation,
        "TextEn": TextEn
    }
    
    lifeGraph.LifeGraphTranslationEn[2]["LifeDataTextsEn"].append(updateLifeDataTextsEn)
    # Count 업데이트
    lifeGraph.LifeGraphTranslationEn[0]["LifeDataTextsCount"] = LifeGraphId

## 3. 1-4 LifeGraphTranslationEn의 LifeDataTexts부분 업데이트
def AddLifeGraphTranslationEnLifeDataTextsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Language, Translation, TextEn):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateLifeDataTextsEn(lifeGraph, LifeGraphId, Language, Translation, TextEn)
        
        flag_modified(lifeGraph, "LifeGraphTranslationEn")
        
        db.add(lifeGraph)
        db.commit()

## 3. LifeGraphTranslationEnCount 가져오기
def LifeGraphTranslationEnCountLoad(lifeGraphSetName, latestUpdateDate):

    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphCount = lifeGraph.LifeGraphTranslationEn[0]["LifeGraphCount"]
    LifeDataTextsCount = lifeGraph.LifeGraphTranslationEn[0]["LifeDataTextsCount"]
    Completion = lifeGraph.LifeGraphTranslationEn[0]["Completion"]
    
    return LifeGraphCount, LifeDataTextsCount, Completion
        
## 3. LifeGraphTranslationEn의 초기화
def InitLifeGraphTranslationEn(lifeGraphSetName, latestUpdateDate):
    LifeGraphDataPath = GetLifeGraphDataPath()
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        lifeGraph.LifeGraphTranslationEn[0]["LifeGraphCount"] = 0
        lifeGraph.LifeGraphTranslationEn[0]["LifeDataTextsCount"] = 0
        lifeGraph.LifeGraphTranslationEn[0]["Completion"] = "No"
        lifeGraph.LifeGraphTranslationEn[1] = LoadJsonFrame(LifeGraphDataPath + "/e4212_Preprocess/e4212-02_LifeGraphTranslationEn.json")[1]
        
        flag_modified(lifeGraph, "LifeGraphTranslationEn")
        
        db.add(lifeGraph)
        db.commit()
        
## 3. 업데이트된 LifeGraphTranslationEn 출력
def UpdatedLifeGraphTranslationEn(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)

    return lifeGraph.LifeGraphTranslationEn

## 3. LifeGraphTranslationEnCompletion 업데이트
def LifeGraphTranslationEnCompletionUpdate(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:

        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        lifeGraph.LifeGraphTranslationEn[0]["Completion"] = "Yes"

        flag_modified(lifeGraph, "LifeGraphTranslationEn")

        db.add(lifeGraph)
        db.commit()

#############################################
##### 04_LifeGraphContextDefine Process #####
#############################################
## 4. 1-0 LifeGraphContextDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedLifeGraphContextDefineToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        
        lifeGraph.LifeGraphContextDefine[1] = ExistedDataFrame[1]
        lifeGraph.LifeGraphContextDefine[2] = ExistedDataFrame[2]
        
        flag_modified(lifeGraph, "LifeGraphContextDefine")
        
        db.add(lifeGraph)
        db.commit()

## 4. 1-1 LifeGraphContextDefine의 ContextChunks부분 업데이트 형식
def UpdateContextChunks(lifeGraph, LifeGraphId, Translation, ContextChunks):
    
    updateContextChunks = {
        "LifeGraphId": LifeGraphId,
        "Translation": Translation,
        "ContextChunks": ContextChunks
    }
    
    lifeGraph.LifeGraphContextDefine[1]["ContextChunks"].append(updateContextChunks)
    # Count 업데이트
    lifeGraph.LifeGraphContextDefine[0]["LifeGraphCount"] = LifeGraphId

## 4. 1-2 LifeGraphContextDefine의 ContextChunks부분 업데이트
def AddLifeGraphContextDefineContextChunksToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Translation, ContextChunks):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateContextChunks(lifeGraph, LifeGraphId, Translation, ContextChunks)
        
        flag_modified(lifeGraph, "LifeGraphContextDefine")
        
        db.add(lifeGraph)
        db.commit()

## 4. 1-3 LifeGraphContextDefine의 LifeDataContextTexts부분 업데이트 형식
def UpdateLifeDataContextTexts(lifeGraph, LifeGraphId, Translation, Text):
    
    updateContextChunks = {
        "LifeGraphId": LifeGraphId,
        "Translation": Translation,
        "Text": Text
    }
    
    lifeGraph.LifeGraphContextDefine[2]["LifeDataContextTexts"].append(updateContextChunks)
    # Count 업데이트
    lifeGraph.LifeGraphContextDefine[0]["LifeGraphTextsCount"] = LifeGraphId

## 4. 1-4 LifeGraphContextDefine의 LifeDataContextTexts부분 업데이트
def AddLifeGraphContextDefineLifeDataContextTextsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Translation, Text):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateLifeDataContextTexts(lifeGraph, LifeGraphId, Translation, Text)
        
        flag_modified(lifeGraph, "LifeGraphContextDefine")
        
        db.add(lifeGraph)
        db.commit()

## 4. LifeGraphContextDefineCount 가져오기
def LifeGraphContextDefineCountLoad(lifeGraphSetName, latestUpdateDate):

    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphCount = lifeGraph.LifeGraphContextDefine[0]["LifeGraphCount"]
    LifeGraphTextsCount = lifeGraph.LifeGraphContextDefine[0]["LifeGraphTextsCount"]
    Completion = lifeGraph.LifeGraphContextDefine[0]["Completion"]
    
    return LifeGraphCount, LifeGraphTextsCount, Completion
        
## 4. LifeGraphContextDefine의 초기화
def InitLifeGraphContextDefine(lifeGraphSetName, latestUpdateDate):
    LifeGraphDataPath = GetLifeGraphDataPath()
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        lifeGraph.LifeGraphContextDefine[0]["LifeGraphCount"] = 0
        lifeGraph.LifeGraphContextDefine[0]["LifeGraphTextsCount"] = 0
        lifeGraph.LifeGraphContextDefine[0]["Completion"] = "No"
        lifeGraph.LifeGraphContextDefine[1] = LoadJsonFrame(LifeGraphDataPath + "/e4213_Context/e4213-01_LifeGraphContextDefine.json")[1]
        
        flag_modified(lifeGraph, "LifeGraphContextDefine")
        
        db.add(lifeGraph)
        db.commit()
        
## 4. 업데이트된 LifeGraphContextDefine 출력
def UpdatedLifeGraphContextDefine(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)

    return lifeGraph.LifeGraphContextDefine

## 4. LifeGraphContextDefineCompletion 업데이트
def LifeGraphContextDefineCompletionUpdate(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:

        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        lifeGraph.LifeGraphContextDefine[0]["Completion"] = "Yes"

        flag_modified(lifeGraph, "LifeGraphContextDefine")

        db.add(lifeGraph)
        db.commit()

#############################################
##### 05_LifeGraphWMWMDefine Process #####
#############################################
## 5. 1-0 LifeGraphWMWMDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedLifeGraphWMWMDefineToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        
        lifeGraph.LifeGraphWMWMDefine[1] = ExistedDataFrame[1]
        lifeGraph.LifeGraphWMWMDefine[2] = ExistedDataFrame[2]
        
        flag_modified(lifeGraph, "LifeGraphWMWMDefine")
        
        db.add(lifeGraph)
        db.commit()

## 5. 1-1 LifeGraphWMWMDefine의 WMWMCompeletions부분 업데이트 형식
def UpdateWMWMCompeletions(lifeGraph, LifeGraphId, Translation, WMWMChunks):
    
    updateWMWMCompeletions = {
        "LifeGraphId": LifeGraphId,
        "Translation": Translation,
        "WMWMChunks": WMWMChunks
    }
    
    lifeGraph.LifeGraphWMWMDefine[1]["WMWMCompeletions"].append(updateWMWMCompeletions)
    # Count 업데이트
    lifeGraph.LifeGraphWMWMDefine[0]["LifeGraphCount"] = LifeGraphId

## 5. 1-2 LifeGraphWMWMDefine의 WMWMCompeletions부분 업데이트
def AddLifeGraphWMWMDefineCompeletionsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Translation, WMWMChunks):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateWMWMCompeletions(lifeGraph, LifeGraphId, Translation, WMWMChunks)
        
        flag_modified(lifeGraph, "LifeGraphWMWMDefine")
        
        db.add(lifeGraph)
        db.commit()

## 5. 1-3 LifeGraphWMWMDefine의 WMWMQuerys부분 업데이트 형식
def UpdateWMWMQuerys(lifeGraph, LifeGraphId, Translation, Querys):
    
    updateWMWMQuerys = {
        "LifeGraphId": LifeGraphId,
        "Translation": Translation,
        "Querys": Querys
    }
    
    lifeGraph.LifeGraphWMWMDefine[2]["WMWMQuerys"].append(updateWMWMQuerys)
    # Count 업데이트
    lifeGraph.LifeGraphWMWMDefine[0]["WMWMQuerysCount"] = LifeGraphId

## 5. 1-4 LifeGraphWMWMDefine의 LifeDataWMWMTexts부분 업데이트
def AddLifeGraphWMWMDefineQuerysToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Translation, Querys):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateWMWMQuerys(lifeGraph, LifeGraphId, Translation, Querys)
        
        flag_modified(lifeGraph, "LifeGraphWMWMDefine")
        
        db.add(lifeGraph)
        db.commit()

## 5. LifeGraphWMWMDefineCount 가져오기
def LifeGraphWMWMDefineCountLoad(lifeGraphSetName, latestUpdateDate):

    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphCount = lifeGraph.LifeGraphWMWMDefine[0]["LifeGraphCount"]
    WMWMQuerysCount = lifeGraph.LifeGraphWMWMDefine[0]["WMWMQuerysCount"]
    Completion = lifeGraph.LifeGraphWMWMDefine[0]["Completion"]
    
    return LifeGraphCount, WMWMQuerysCount, Completion
        
## 5. LifeGraphWMWMDefine의 초기화
def InitLifeGraphWMWMDefine(lifeGraphSetName, latestUpdateDate):
    LifeGraphDataPath = GetLifeGraphDataPath()
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        lifeGraph.LifeGraphWMWMDefine[0]["LifeGraphCount"] = 0
        lifeGraph.LifeGraphWMWMDefine[0]["WMWMQuerysCount"] = 0
        lifeGraph.LifeGraphWMWMDefine[0]["Completion"] = "No"
        lifeGraph.LifeGraphWMWMDefine[1] = LoadJsonFrame(LifeGraphDataPath + "/e4213_Context/e4213-02_LifeGraphWMWMDefine.json")[1]
        
        flag_modified(lifeGraph, "LifeGraphWMWMDefine")
        
        db.add(lifeGraph)
        db.commit()
        
## 5. 업데이트된 LifeGraphWMWMDefine 출력
def UpdatedLifeGraphWMWMDefine(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)

    return lifeGraph.LifeGraphWMWMDefine

## 5. LifeGraphWMWMDefineCompletion 업데이트
def LifeGraphWMWMDefineCompletionUpdate(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:

        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        lifeGraph.LifeGraphWMWMDefine[0]["Completion"] = "Yes"

        flag_modified(lifeGraph, "LifeGraphWMWMDefine")

        db.add(lifeGraph)
        db.commit()

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################