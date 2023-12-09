import sys
sys.path.append("/yaas")

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import LifeGraph
from backend.b1_Api.b13_Database import get_db
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraph, GetVideo
from extension.e1_Solution.e12_ExtensionProject.e121_LifeGraph.e1211_LifeGraphCommit import GetLifeGraphDataPath, LoadJsonFrame

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
##### 01_LifeGraphTranslationKo Process #####
#############################################
## 1. 1-0 LifeGraphTranslationKo이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedLifeGraphTranslationKoToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        
        lifeGraph.LifeGraphTranslationKo[1] = ExistedDataFrame[1]
        lifeGraph.LifeGraphTranslationKo[2] = ExistedDataFrame[2]
        
        flag_modified(lifeGraph, "LifeGraphTranslationKo")
        
        db.add(lifeGraph)
        db.commit()


## 1. 1-1 LifeGraphTranslationKo의 LifeGraphs부분 업데이트 형식
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
    
    lifeGraph.LifeGraphTranslationKo[1]["LifeGraphs"].append(updateLifeGraphs)
    # Count 업데이트
    lifeGraph.LifeGraphTranslationKo[0]["LifeGraphCount"] = LifeGraphId

## 1. 1-2 LifeGraphTranslationKo의 LifeGraphs부분 업데이트
def AddLifeGraphTranslationKoLifeGraphsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Residence, PhoneNumber, Email, Quality, LifeData):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateLifeGraphs(lifeGraph, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Residence, PhoneNumber, Email, Quality, LifeData)
        
        flag_modified(lifeGraph, "LifeGraphTranslationKo")
        
        db.add(lifeGraph)
        db.commit()

## 1. 1-3 LifeGraphTranslationKo의 LifeDataTexts부분 업데이트 형식
def UpdateLifeDataTextsKo(lifeGraph, LifeGraphId, Language, TextKo):
    
    updateLifeDataTextsKo = {
        "LifeGraphId": LifeGraphId,
        "Language": Language,
        "TextKo": TextKo
    }
    
    lifeGraph.LifeGraphTranslationKo[2]["LifeDataTextsKo"].append(updateLifeDataTextsKo)
    # Count 업데이트
    lifeGraph.LifeGraphTranslationKo[0]["LifeDataTextsCount"] = LifeGraphId

## 1. 1-4 LifeGraphTranslationKo의 LifeDataTexts부분 업데이트
def AddLifeGraphTranslationKoLifeDataTextsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Language, TextKo):
    with get_db() as db:
    
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        UpdateLifeDataTextsKo(lifeGraph, LifeGraphId, Language, TextKo)
        
        flag_modified(lifeGraph, "LifeGraphTranslationKo")
        
        db.add(lifeGraph)
        db.commit()

## 1. LifeGraphTranslationKoCount 가져오기
def LifeGraphTranslationKoCountLoad(lifeGraphSetName, latestUpdateDate):

    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphCount = lifeGraph.LifeGraphTranslationKo[0]["LifeGraphCount"]
    LifeDataTextsCount = lifeGraph.LifeGraphTranslationKo[0]["LifeDataTextsCount"]
    Completion = lifeGraph.LifeGraphTranslationKo[0]["Completion"]
    
    return LifeGraphCount, LifeDataTextsCount, Completion
        
## 1. LifeGraphTranslationKo의 초기화
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
        
## 1. 업데이트된 LifeGraphTranslationKo 출력
def UpdatedLifeGraphTranslationKo(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:
        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)

    return lifeGraph.LifeGraphTranslationKo

## 1. LifeGraphTranslationKoCompletion 업데이트
def LifeGraphTranslationKoCompletionUpdate(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:

        lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
        lifeGraph.LifeGraphTranslationKo[0]["Completion"] = "Yes"

        flag_modified(lifeGraph, "LifeGraphTranslationKo")

        db.add(lifeGraph)
        db.commit()
        
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = 'CourseraMeditation'
    latestUpdateDate = 23120601
    LifeGraphFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData"
    #########################################################################