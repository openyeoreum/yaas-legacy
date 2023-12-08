import sys
sys.path.append("/yaas")

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import LifeGraph
from backend.b1_Api.b13_Database import get_db
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraphFrame, GetVideoFrame
from extension.e1_Solution.e12_ExtensionProject.e121_LifeGraph.e1211_LifeGraphCommit import GetLifeGraphDataPath, LoadJsonFrame

###############################
########## LifeGraph ##########
###############################

######################################################
##### 0. 전체 LifeGraph의 MetaData(식별)부분을 업데이트 #####
######################################################
def AddLifeGraphFrameMetaDataToDB(Process):
    with get_db() as db:
        lifeGraph = GetLifeGraphFrame(Process)

        if not lifeGraph:
            print("LifeGraph not found!")
            return
        
        for column in LifeGraph.__table__.columns:
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
def AddExistedLifeGraphFrameToDB(Process, ExistedDataFrame):
    with get_db() as db:
    
        lifeGraph = GetLifeGraphFrame(Process)
        lifeGraph.LifeGraphFrame[1] = ExistedDataFrame[1]
        
        flag_modified(lifeGraph, "LifeGraphFrame")
        
        db.add(lifeGraph)
        db.commit()


## 1. 1-2 LifeGraphFrame의 LifeGraphs부분 업데이트 형식
def UpdateLifeGraphs(lifeGraph, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Residence, PhoneNumber, Email):
    
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
        "LifeData": []
    }
    
    lifeGraph.LifeGraphFrame[1]["LifeGraphs"].append(updateLifeGraphs)
    # Count 업데이트
    lifeGraph.LifeGraphFrame[0]["LifeGraphCount"] = LifeGraphId

## 1. 1-3 LifeGraphFrame의 LifeGraphs부분 업데이트
def AddLifeGraphFrameLifeGraphsToDB(Process, lifeGraph, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Residence, PhoneNumber, Email):
    with get_db() as db:
    
        lifeGraph = GetLifeGraphFrame(Process)
        UpdateLifeGraphs(lifeGraph, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Residence, PhoneNumber, Email)
        
        flag_modified(lifeGraph, "LifeGraphFrame")
        
        db.add(lifeGraph)
        db.commit()
        
## 1. 2-1 LifeGraphFrame의 LifeGraphs, LifeData부분 업데이트 형식
def UpdateLifeData(lifeGraph, LifeDataId, StartAge, EndAge, Score, ReasonGlobal):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    LifeGraphId = len(lifeGraph.LifeGraphFrame[1]["LifeGraphs"]) -1
    
    updateLifeData = {
        "LifeDataId": LifeDataId,
        "StartAge": StartAge,
        "EndAge": EndAge,
        "Score": Score,
        "ReasonGlobal": ReasonGlobal
    }
    
    lifeGraph.LifeGraphFrame[1]["LifeGraphs"][LifeGraphId]["LifeData"].append(updateLifeData)

## 1. 2-2 LifeGraphFrame의 LifeGraphs, LifeData부분 업데이트
def AddLifeGraphFrameLifeDataToDB(Process, lifeGraph, LifeDataId, StartAge, EndAge, Score, ReasonGlobal):
    with get_db() as db:
        
        lifeGraph = GetLifeGraphFrame(Process)
        UpdateLifeData(lifeGraph, LifeDataId, StartAge, EndAge, Score, ReasonGlobal)
        
        flag_modified(lifeGraph, "LifeGraphFrame")
        
        db.add(lifeGraph)
        db.commit()

## 1. LifeGraphFrameCount 가져오기
def LifeGraphFrameCountLoad(Process):

    lifeGraph = GetLifeGraphFrame(Process)
    LifeGraphCount = lifeGraph.LifeGraphFrame[0]["LifeGraphCount"]
    Completion = lifeGraph.LifeGraphFrame[0]["Completion"]
    
    return LifeGraphCount, Completion
        
## 1. LifeGraphFrame의 초기화
def InitLifeGraphFrame(Process):
    LifeGraphDataPath = GetLifeGraphDataPath()
    with get_db() as db:
    
        lifeGraph = GetLifeGraphFrame(Process)
        lifeGraph.LifeGraphFrame[0]["LifeGraphCount"] = 0
        lifeGraph.LifeGraphFrame[0]["Completion"] = "No"
        lifeGraph.LifeGraphFrame[1] = LoadJsonFrame(LifeGraphDataPath + "/e4211_RawData/e4211-02_LifeGraphFrame.json")[1]
        
        flag_modified(lifeGraph, "LifeGraphFrame")
        
        db.add(lifeGraph)
        db.commit()
        
## 1. 업데이트된 LifeGraphFrame 출력
def UpdatedLifeGraphFrame(Process):
    with get_db() as db:
        lifeGraph = GetLifeGraphFrame(Process)

    return lifeGraph.LifeGraphFrame

## 1. LifeGraphFrameCompletion 업데이트
def LifeGraphFrameCompletionUpdate(Process):
    with get_db() as db:

        lifeGraph = GetLifeGraphFrame(Process)
        lifeGraph.LifeGraphFrame[0]["Completion"] = "Yes"

        flag_modified(lifeGraph, "LifeGraphFrame")

        db.add(lifeGraph)
        db.commit()
        
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    process = 'IndexDefinePreprocess'
    LifeGraphFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData"
    #########################################################################