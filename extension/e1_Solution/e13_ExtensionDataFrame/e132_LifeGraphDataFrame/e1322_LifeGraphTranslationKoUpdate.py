import re
import json
import tiktoken
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from langdetect import detect
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraph
from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import AddExistedLifeGraphFrameToDB, AddLifeGraphFrameLifeGraphsToDB, LifeGraphFrameCountLoad, InitLifeGraphFrame, LifeGraphFrameCompletionUpdate, UpdatedLifeGraphFrame

#########################
##### InputList 생성 #####
#########################
# LifeGraphSet 로드
def LoadLifeGraphFrameTexts(lifeGraphSetName, latestUpdateDate):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphFrameTexts = lifeGraph.LifeGraphFrame[2]['LifeDataTexts'][1:]
    
    return LifeGraphFrameTexts

## LifeGraphFrameTexts의 inputList 치환
def LifeGraphFrameTextsToInputList(lifeGraphSetName, latestUpdateDate):
    LifeGraphFrameTexts = LoadLifeGraphFrameTexts(lifeGraphSetName, latestUpdateDate)
    
    InputList = []
    for i in range(len(LifeGraphFrameTexts)):
        Id = LifeGraphFrameTexts[i]['LifeGraphId']
        Language = LifeGraphFrameTexts[i]['Language']
        TextGlobal = LifeGraphFrameTexts[i]['TextGlobal']

        if Language in ['ko', 'None']:
            Tag = 'Pass'
        else:
            Tag = 'Continue'
            
        InputDic = {'Id': Id, Tag: TextGlobal}
        InputList.append(InputDic)
        
    return InputList

######################
##### Filter 조건 #####
######################
## LifeGraphTranslationKo의 Filter(Error 예외처리)
def LifeGraphTranslationKoFilter(Input, responseData, memoryCounter):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(responseData)
        OutputDic = [{key: value} for key, value in outputJson.items()]
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 결과가 list가 아닐 때의 예외 처리
    if not isinstance(OutputDic, list):
        return "JSONType에서 오류 발생: JSONTypeError"  
    # Error3: 자료의 구조가 다를 때의 예외 처리
    INPUT = re.sub("[^가-힣]", "", str(Input))
    for dic in OutputDic:
        try:
            key = list(dic.keys())[0]
            # '핵심문구' 키에 접근하는 부분에 예외 처리 추가
            try:
                OUTPUT = re.sub("[^가-힣]", "", str(dic[key]['핵심문구']))
            except TypeError:
                return "JSON에서 오류 발생: TypeError"
            except KeyError:
                return "JSON에서 오류 발생: KeyError"
            if not '메모' in key:
                return "JSON에서 오류 발생: JSONKeyError"
            elif not OUTPUT in INPUT:
                return f"JSON에서 오류 발생: JSON '핵심문구'가 Input에 포함되지 않음 Error\n문구: {dic[key]['핵심문구']}"
            elif not ('목적' in dic[key] and '원인' in dic[key] and '핵심문구' in dic[key] and '예상질문' in dic[key] and '매칭독자' in dic[key] and '주제' in dic[key] and '중요도' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        
    return {'json': outputJson, 'filter': OutputDic}

## 결과물 Json을 LifeGraphFrame에 업데이트
def LifeGraphFrameUpdate(lifeGraphSetName, latestUpdateDate, QUALITY = 6, ExistedDataFrame = None):
    print(f"< LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 01_LifeGraphFrameUpdate 시작 >")
    # LifeGraphFrame의 Count값 가져오기
    LifeGraphCount, Completion = LifeGraphFrameCountLoad(lifeGraphSetName, latestUpdateDate)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedLifeGraphFrameToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame)
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 01_LifeGraphFrameUpdate으로 대처됨 ]\n")
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
                LifeGraphDate = LifeGraphsList[i]["LifeGraphDate"]
                Name = LifeGraphsList[i]["Name"]
                Age = LifeGraphsList[i]["Age"]
                Source = LifeGraphsList[i]["Source"]
                Language = LifeGraphsList[i]["Language"]
                Residence = LifeGraphsList[i]["Residence"]
                PhoneNumber = LifeGraphsList[i]["PhoneNumber"]
                Email = LifeGraphsList[i]["Email"]
                Quality = LifeGraphsList[i]["Quality"]
                LifeData = LifeGraphsList[i]["LifeData"]

                AddLifeGraphFrameLifeGraphsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Residence, PhoneNumber, Email, Quality, LifeData)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            #####
            # Completion "Yes" 업데이트
            LifeGraphFrameCompletionUpdate(lifeGraphSetName, latestUpdateDate)
            
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 01_LifeGraphFrameUpdate 완료 ]\n")
    else:
        print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 01_LifeGraphFrameUpdate는 이미 완료됨 ]\n")
    
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = 'CourseraMeditation'
    latestUpdateDate = 23120601
    LifeGraphFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData"
    #########################################################################