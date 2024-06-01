import os
import re
import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from sqlalchemy import desc
from backend.b1_Api.b14_Models import LifeGraph
from backend.b1_Api.b13_Database import get_db

def GetLifeGraphDataPath():
    RootPath = "/yaas"
    DataPath = "extension/e4_Database/e42_ProjectData/e421_LifeGraph"
    return os.path.join(RootPath, DataPath)

def GetLifeGraphSetsPath(lifeGraphSetName):
    LifeGraphDataPath = GetLifeGraphDataPath()
    directory = LifeGraphDataPath + "/e4211_RawData/e4211-01_LifeGraphSets/"
    pattern = f"e4211-01_\\d{{6}}_{lifeGraphSetName}_LifeGraph.json"
    
    def GetLatestFile(Files):
        FileDates = []
        for file in Files:
            try:
                DateStr = file.split('_')[1]
                FileDate = datetime.strptime(DateStr, '%y%m%d')
                FileDates.append((file, FileDate))
            except ValueError:
                continue

        FileDates.sort(key=lambda x: x[1], reverse=True)
        LatestFile = FileDates[0][0] if FileDates else None

        return LatestFile
    
    filename = GetLatestFile(os.listdir(directory))
    
    if re.match(pattern, filename):
        return os.path.join(directory, filename)

    return None

def LoadJsonFrame(filepath):
    with open(filepath, 'r') as file:
        DataFrame = json.load(file)
    return DataFrame

def AddLifeGraphToDB(lifeGraphSetName, lifeGraphSetManager, lifeGraphSetSource, lifeGraphSetLanguage, latestUpdateDate):
    with get_db() as db:
        
        # JSON 데이터 불러오기
        LifeGraphDataPath = GetLifeGraphDataPath()
        lifeGraphSets = LoadJsonFrame(GetLifeGraphSetsPath(lifeGraphSetName))
        lifeGraphFrame = LoadJsonFrame(LifeGraphDataPath + "/e4211_RawData/e4211-02_LifeGraphFrame.json")
        lifeGraphTranslationKo = LoadJsonFrame(LifeGraphDataPath + "/e4212_Preprocess/e4212-01_LifeGraphTranslationKo.json")
        lifeGraphTranslationEn = LoadJsonFrame(LifeGraphDataPath + "/e4212_Preprocess/e4212-02_LifeGraphTranslationEn.json")
        lifeGraphContextDefine = LoadJsonFrame(LifeGraphDataPath + "/e4213_Context/e4213-01_LifeGraphContextDefine.json")
        lifeGraphWMWMDefine = LoadJsonFrame(LifeGraphDataPath + "/e4213_Context/e4213-02_LifeGraphWMWMDefine.json")
        lifeGraphWMWMMatching = LoadJsonFrame(LifeGraphDataPath + "/e4213_Context/e4213-03_LifeGraphWMWMMatching.json")
        ### 아래로 추가되는 프롬프트 작성 ###

        ExistingLifeGraph = db.query(LifeGraph).filter(LifeGraph.LifeGraphSetName == lifeGraphSetName, LifeGraph.LifeGraphSetManager == lifeGraphSetManager, LifeGraph.LatestUpdateDate == latestUpdateDate).first()

        # DB Commit
        if ExistingLifeGraph:
                ExistingLifeGraph.LifeGraphSetName = lifeGraphSetName
                ExistingLifeGraph.LifeGraphSetManager = lifeGraphSetManager
                ExistingLifeGraph.LifeGraphSetSource = lifeGraphSetSource
                ExistingLifeGraph.LifeGraphSetLanguage = lifeGraphSetLanguage
                ExistingLifeGraph.LatestUpdateDate = latestUpdateDate
                ExistingLifeGraph.LifeGraphSets = lifeGraphSets
                ExistingLifeGraph.LifeGraphFrame = lifeGraphFrame
                ExistingLifeGraph.LifeGraphTranslationKo = lifeGraphTranslationKo
                ExistingLifeGraph.LifeGraphTranslationEn = lifeGraphTranslationEn
                ExistingLifeGraph.LifeGraphContextDefine = lifeGraphContextDefine
                ExistingLifeGraph.LifeGraphWMWMDefine = lifeGraphWMWMDefine
                ExistingLifeGraph.LifeGraphWMWMMatching = lifeGraphWMWMMatching
                ### 아래로 추가되는 프롬프트 작성 ###
                
                print(f"[ ExtensionProject | AddLifeGraphToDB 변경사항 업데이트 ]")
        else:
            lifeGraph = LifeGraph(
                LifeGraphSetName = lifeGraphSetName,
                LifeGraphSetManager = lifeGraphSetManager,
                LifeGraphSetSource = lifeGraphSetSource,
                LifeGraphSetLanguage = lifeGraphSetLanguage,
                LatestUpdateDate = latestUpdateDate,
                LifeGraphSets = lifeGraphSets,
                LifeGraphFrame = lifeGraphFrame,
                LifeGraphTranslationKo = lifeGraphTranslationKo,
                LifeGraphTranslationEn = lifeGraphTranslationEn,
                LifeGraphContextDefine = lifeGraphContextDefine,
                LifeGraphWMWMDefine = lifeGraphWMWMDefine,
                LifeGraphWMWMMatching = lifeGraphWMWMMatching
                ### 아래로 추가되는 프롬프트 작성 ###
                )
            db.add(lifeGraph)
            print(f"[ ExtensionProject | AddLifeGraphToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################
    LifeGraphSetsPath = GetLifeGraphSetsPath(lifeGraphSetName)
    print(LifeGraphSetsPath)
    # AddLifeGraphToDB("CourseraMeditation", "Duck-JooLee", "Coursera", "Global", 23120601)