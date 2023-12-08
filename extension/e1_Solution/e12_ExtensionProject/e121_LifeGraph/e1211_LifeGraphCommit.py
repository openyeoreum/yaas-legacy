import os
import re
import sys
import json
sys.path.append("/yaas")

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

    for filename in os.listdir(directory):
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
        lifeGraphNCEMDefine = LoadJsonFrame(LifeGraphDataPath + "/e4213_Context/e4213-02_LifeGraphNCEMDefine.json")
        lifeGraphNCEMMatching = LoadJsonFrame(LifeGraphDataPath + "/e4213_Context/e4213-03_LifeGraphNCEMMatching.json")
        ### 아래로 추가되는 프롬프트 작성 ###

        ExistingLifeGraph = db.query(LifeGraph).filter(LifeGraph.LifeGraphSetName == lifeGraphSetName, LifeGraph.LifeGraphSetManager == lifeGraphSetManager, LifeGraph.LatestUpdateDate == latestUpdateDate).first()

        # DB Commit
        if ExistingLifeGraph:
                ExistingLifeGraph.LifeGraphSetName = lifeGraphSets
                ExistingLifeGraph.LifeGraphSetManager = lifeGraphSetManager
                ExistingLifeGraph.LifeGraphSetSource = lifeGraphSetSource
                ExistingLifeGraph.LifeGraphSetLanguage = lifeGraphSetLanguage
                ExistingLifeGraph.LatestUpdateDate = latestUpdateDate
                ExistingLifeGraph.LifeGraphSets = lifeGraphSets
                ExistingLifeGraph.LifeGraphFrame = lifeGraphFrame
                ExistingLifeGraph.LifeGraphTranslationKo = lifeGraphTranslationKo
                ExistingLifeGraph.LifeGraphTranslationEn = lifeGraphTranslationEn
                ExistingLifeGraph.LifeGraphContextDefine = lifeGraphContextDefine
                ExistingLifeGraph.LifeGraphNCEMDefine = lifeGraphNCEMDefine
                ExistingLifeGraph.LifeGraphNCEMMatching = lifeGraphNCEMMatching
                ### 아래로 추가되는 프롬프트 작성 ###
                
                print(f"[ ExtensionProject | AddLifeGraphToDB 변경사항 업데이트 ]")
        else:
            lifeGraph = LifeGraph(
                LifeGraphSetName = lifeGraphSets,
                LifeGraphSetManager = lifeGraphSetManager,
                LifeGraphSetSource = lifeGraphSetSource,
                LifeGraphSetLanguage = lifeGraphSetLanguage,
                LatestUpdateDate = latestUpdateDate,
                LifeGraphSets = lifeGraphSets,
                LifeGraphFrame = lifeGraphFrame,
                LifeGraphTranslationKo = lifeGraphTranslationKo,
                LifeGraphTranslationEn = lifeGraphTranslationEn,
                LifeGraphContextDefine = lifeGraphContextDefine,
                LifeGraphNCEMDefine = lifeGraphNCEMDefine,
                LifeGraphNCEMMatching = lifeGraphNCEMMatching
                ### 아래로 추가되는 프롬프트 작성 ###
                )
            db.add(lifeGraph)
            print(f"[ ExtensionProject | AddLifeGraphToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":
    AddLifeGraphToDB("CourseraMeditation", "Duck-JooLee", "Coursera", "Global", 23120601)