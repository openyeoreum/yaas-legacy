import re
import json
import tiktoken
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from langdetect import detect
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraph
from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import AddExistedLifeGraphFrameToDB, AddLifeGraphFrameLifeGraphsToDB, AddLifeGraphFrameLifeDataTextsToDB, LifeGraphFrameCountLoad, LifeGraphFrameCompletionUpdate

# LifeGraphSet 로드
def LoadLifeGraphSet(lifeGraphSetName, latestUpdateDate):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    DataPattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}%3A\d{2}%3A\d{2}")
    
    lifeGraphSets = lifeGraph.LifeGraphSets
    lifeGraphList = list(lifeGraphSets.items())
    
    return lifeGraphList

## LifeGraphSet 구조변경
def LifeGraphSetJson(lifeGraphSetName, latestUpdateDate, quality = 0):
    lifeGraphList = LoadLifeGraphSet(lifeGraphSetName, latestUpdateDate)
    DataPattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    
    LifeGraphs = []
    for i in range(len(lifeGraphList)):
        LifeGraphId = i + 1
        LifeGraphDate = DataPattern.search(lifeGraphList[i][1]['graph_url']).group()
        Name = lifeGraphList[i][0].strip()
        Age = lifeGraphList[i][1]['age']
        Source = lifeGraphSetName
        Residence = "None"
        PhoneNumber = "None"
        Email = lifeGraphList[i][1]['email']
        LifeData = []
        LifeDataReasons = []
        LifeDataDic = {"LifeDataId": 0, "StartAge": "None", "EndAge": "None", "Score": "None", "ReasonGlobal": "None"}
        
        QualityCount = 0
        for j in range(len(lifeGraphList[i][1]['lifeData'])):
            LifeDataId = j + 1
            StartAge = lifeGraphList[i][1]['lifeData'][j]['startAge']
            EndAge = lifeGraphList[i][1]['lifeData'][j]['endAge']
            Score = lifeGraphList[i][1]['lifeData'][j]['score']
            ReasonGlobal = lifeGraphList[i][1]['lifeData'][j]['reason']
            LifeDataDic = {"LifeDataId": LifeDataId, "StartAge": StartAge, "EndAge": EndAge, "Score": Score, "ReasonGlobal": ReasonGlobal}
            LifeData.append(LifeDataDic)
            if ReasonGlobal != '':
                QualityCount += 1
            LifeDataReasons.append(ReasonGlobal)
        
        LifeDataReasonsText = " ".join(LifeDataReasons)
        try:
            Language = detect(LifeDataReasonsText)
        except:
            Language = "None"
        Quality = QualityCount
        
        LifeGraphDic = {"LifeGraphId": LifeGraphId, "LifeGraphDate": LifeGraphDate, "Name": Name, "Age": Age, "Source": Source, "Language": Language, "Residence": Residence, "PhoneNumber": PhoneNumber, "Email": Email, "Quality": Quality, "LifeData": LifeData}
        if Quality >= quality:
            LifeGraphs.append(LifeGraphDic)
    
    return LifeGraphs

def LifeDataToText(lifeGraphSetName, latestUpdateDate, QUALITY = 0):
    LifeGraphs = LifeGraphSetJson(lifeGraphSetName, latestUpdateDate, quality = QUALITY)
    
    LifeDataTexts = []
    for i in range(len(LifeGraphs)):
        LifeGraphDate = LifeGraphs[i]["LifeGraphDate"]
        Name = LifeGraphs[i]["Name"]
        Age = LifeGraphs[i]["Age"]
        Email = LifeGraphs[i]["Email"]
        Language = LifeGraphs[i]["Language"]
        LifeDataKo = []
        LifeDataEn = []
        for j in range(len(LifeGraphs[i]["LifeData"])):
            StartAge = LifeGraphs[i]["LifeData"][j]["StartAge"]
            EndAge = LifeGraphs[i]["LifeData"][j]["EndAge"]
            Score = LifeGraphs[i]["LifeData"][j]["Score"]
            if LifeGraphs[i]["LifeData"][j]["ReasonGlobal"] == '':
                ReasonKo = '내용없음'
                ReasonEn = 'No Content'
            else:
                ReasonKo = LifeGraphs[i]["LifeData"][j]["ReasonGlobal"]
                ReasonEn = LifeGraphs[i]["LifeData"][j]["ReasonGlobal"]
                
            if j == (len(LifeGraphs[i]["LifeData"]) - 1):
                LifeDataKo.append(f'{StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {ReasonKo}')
                LifeDataEn.append(f'{StartAge}-{EndAge} Happiness Score: {Score}, Reason: {ReasonEn}')
            else:
                LifeDataKo.append(f'{StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {ReasonKo}\n')
                LifeDataEn.append(f'{StartAge}-{EndAge} Happiness Score: {Score}, Reason: {ReasonEn}\n')
        
        LifeDataTextKo = f"작성일: {LifeGraphDate}\nEmail: {Email}\n\n● '{Name}'의 {Age}세 까지의 인생\n\n" + "".join(LifeDataKo)
        LifeDataTextEn = f"Date: {LifeGraphDate}\nEmail: {Email}\n\n● Life up to the age of {Age} for '{Name}'\n\n" + "".join(LifeDataEn)
        LifeDataTexts.append({"Name": Name, "Email": Email, "TextGlobal": {'Ko': LifeDataTextKo, 'En': LifeDataTextEn}, "Language": Language})
        
    return LifeDataTexts

## LifeDataTexts를 LifeGraphFrame에 업데이트
def LifeGraphFrameLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, quality = 0):
    LifeDataTexts = LifeDataToText(lifeGraphSetName, latestUpdateDate, QUALITY = quality)
    LifeDataTextsCount = len(LifeDataTexts)
    
    # TQDM 셋팅
    UpdateTQDM = tqdm(LifeDataTexts,
                    total = LifeDataTextsCount,
                    desc = 'LifeGraphFrameLifeDataTextsUpdate')
    # i값 수동 생성
    i = 0
    for Update in UpdateTQDM:
        UpdateTQDM.set_description(f'LifeGraphFrameLifeDataTextsUpdate: {Update["Name"]}, {Update["Email"]} ...')
        time.sleep(0.0001)
        LifeGraphId = i + 1
        Language = LifeDataTexts[i]["Language"]
        TextGlobal = LifeDataTexts[i]["TextGlobal"]
        
        AddLifeGraphFrameLifeDataTextsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Language, TextGlobal)
        # i값 수동 업데이트
        i += 1

    UpdateTQDM.close()

## 결과물 Json을 LifeGraphFrame에 업데이트
def LifeGraphFrameUpdate(lifeGraphSetName, latestUpdateDate, QUALITY = 0, ExistedDataFrame = None):
    print(f"< LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 01_LifeGraphFrameUpdate 시작 >")
    # LifeGraphFrame의 Count값 가져오기
    LifeGraphCount, LifeDataTextsCount, Completion = LifeGraphFrameCountLoad(lifeGraphSetName, latestUpdateDate)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedLifeGraphFrameToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame)
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 01_LifeGraphFrame으로 대처됨 ]\n")
        else:
            LifeGraphs = LifeGraphSetJson(lifeGraphSetName, latestUpdateDate, quality = QUALITY)
            # LifeGraphs를 LifeGraphCount로 슬라이스
            LifeGraphsList = LifeGraphs[LifeGraphCount:]
            LifeGraphsListCount = len(LifeGraphsList)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(LifeGraphsList,
                            total = LifeGraphsListCount,
                            desc = 'LifeGraphFrameUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'LifeGraphFrameUpdate: {Update["Name"]}, {Update["Email"]} ...')
                time.sleep(0.0001)
                
                LifeGraphId = i + 1
                LifeGraphDate = Update["LifeGraphDate"]
                Name = Update["Name"]
                Age = Update["Age"]
                Source = Update["Source"]
                Language = Update["Language"]
                Residence = Update["Residence"]
                PhoneNumber = Update["PhoneNumber"]
                Email = Update["Email"]
                Quality = Update["Quality"]
                LifeData = Update["LifeData"]

                AddLifeGraphFrameLifeGraphsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Residence, PhoneNumber, Email, Quality, LifeData)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            ##### LifeDataTexts 업데이트
            LifeGraphFrameLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, quality = QUALITY)
            #####
            # Completion "Yes" 업데이트
            LifeGraphFrameCompletionUpdate(lifeGraphSetName, latestUpdateDate)
            
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 01_LifeGraphFrameUpdate 완료 ]\n")
    else:
        print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 01_LifeGraphFrameUpdate는 이미 완료됨 ]\n")
    
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################