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
def LifeGraphTranslationKoFilter(responseData, memoryCounter):
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
    for dic in OutputDic:
        try:
            key = list(dic.keys())[0]
            # '핵심문구' 키에 접근하는 부분에 예외 처리 추가
            if not '인생데이터' in key:
                return "JSON에서 오류 발생: JSONKeyError"
            elif not ('시기' in dic[key] and '행복지수' in dic[key] and '이유' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        
    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def LifeGraphTranslationKoInputMemory(inputMemoryDics, MemoryLength):
    inputMemoryDic = inputMemoryDics[-(MemoryLength + 1):]
    
    inputMemoryList = []
    for inputmeMory in inputMemoryDic:
        key = list(inputmeMory.keys())[1]  # 두 번째 키값
        if key == "Continue":
            inputMemoryList.append(inputmeMory['Continue'])
        else:
            inputMemoryList.append(inputmeMory['Pass'])
    inputMemory = "".join(inputMemoryList)
    # print(f"@@@@@@@@@@\ninputMemory :{inputMemory}\n@@@@@@@@@@")
    
    return inputMemory

## outputMemory 형성
def LifeGraphTranslationKoOutputMemory(outputMemoryDics, MemoryLength):
    outputMemoryDic = outputMemoryDics[-MemoryLength:]
    
    OUTPUTmemoryDic = []
    for item in outputMemoryDic:
        if isinstance(item, list):
            OUTPUTmemoryDic.extend(item)
        else:
            OUTPUTmemoryDic.append(item)
    OUTPUTmemoryDic = [entry for entry in OUTPUTmemoryDic if entry != "Pass"]
    outputMemory = str(OUTPUTmemoryDic)
    outputMemory = outputMemory[:-1] + ", "
    outputMemory = outputMemory.replace("[, ", "[")
    # print(f"@@@@@@@@@@\noutputMemory :{outputMemory}\n@@@@@@@@@@")
    
    return outputMemory





#######################
##### Process 진행 #####
#######################
## ContextDefine 프롬프트 요청 및 결과물 Json화
def ContextDefineProcess(projectName, email, Process = "ContextDefine", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    InputList = BodyFrameBodysToInputList(projectName, email)
    FineTuningMemoryList = BodyFrameBodysToInputList(projectName, email, Task = "Body")
    TotalCount = 0
    ProcessCount = 1
    ContinueCount = 0
    inputMemoryDics = []
    inputMemory = []
    InputDic = InputList[0]
    inputMemoryDics.append(InputDic)
    outputMemoryDics = []
    outputMemory = []
        
    # ContextDefineProcess
    while TotalCount < len(InputList):
        # Momory 계열 모드의 순서
        if Mode == "Memory":
            if "Continue" in InputDic:
                ContinueCount += 1
            if ContinueCount == 1:
                mode = "Example"
            else:
                mode = "Memory"
        elif Mode == "MemoryFineTuning":
            if "Continue" in InputDic:
                ContinueCount += 1
            if ContinueCount == 1:
                mode = "ExampleFineTuning"
                # "ExampleFineTuning"의 fineTuningMemory 형성
                FineTuningMemory = FineTuningMemoryList[TotalCount - 1] if TotalCount > 0 else {'Id': 0, 'Pass': ''}
            else:
                mode = "MemoryFineTuning"
        # Example 계열 모드의 순서
        elif Mode == "Master":
            mode = "Master"
            # "Master"의 MasterMemory 형성
            MasterMemory = FineTuningMemoryList[TotalCount - 1] if TotalCount > 0 else {'Id': 0, 'Pass': ''}
        elif Mode == "ExampleFineTuning":
            mode = "ExampleFineTuning"
            # "ExampleFineTuning"의 fineTuningMemory 형성
            FineTuningMemory = FineTuningMemoryList[TotalCount - 1] if TotalCount > 0 else {'Id': 0, 'Pass': ''}
        elif Mode == "Example":
            mode = "Example"
            
        if "Continue" in InputDic:
            if Mode == "Master":
                Keys = list(MasterMemory.keys())
                Input = MasterMemory[Keys[1]] + InputDic['Continue']
            elif Mode == "ExampleFineTuning":
                Keys = list(FineTuningMemory.keys())
                Input = FineTuningMemory[Keys[1]] + InputDic['Continue']
            else:
                Input = InputDic['Continue']
            
            # Filter, MemoryCounter, OutputEnder 처리
            memoryCounter = "\n"
            outputEnder = f"{{'메모"
            
            # Response 생성
            Response, Usage, Model = LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)

            # OutputStarter, OutputEnder에 따른 Response 전처리
            promptFrame = GetPromptFrame(Process)
            if mode in ["Example", "ExampleFineTuning", "Master"]:
                Example = promptFrame[0]["Example"]
                if Response.startswith(Example[2]["OutputStarter"]):
                    Response = Response.replace(Example[2]["OutputStarter"], "", 1)
                responseData = Example[2]["OutputStarter"] + Response
            elif mode in ["Memory", "MemoryFineTuning"]:
                if Response.startswith("[" + outputEnder):
                    responseData = Response
                else:
                    if Response.startswith(outputEnder):
                        Response = Response.replace(outputEnder, "", 1)
                    responseData = outputEnder + Response
         
            Filter = ContextDefineFilter(Input, responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{len(InputList)} | {Filter}")
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{len(InputList)} | JSONDecode 완료")
                
                # DataSets 업데이트
                if mode in ["Example", "ExampleFineTuning", "Master"]:
                    # mode가 ["Example", "ExampleFineTuning", "Master"]중 하나인 경우 Memory 초기화
                    INPUTMemory = "None"
                elif mode in ["Memory", "MemoryFineTuning"]:
                    INPUTMemory = inputMemory
                    
                AddProjectRawDatasetToDB(projectName, email, Process, mode, Model, Usage, InputDic, outputJson, INPUTMEMORY = INPUTMemory)
                AddProjectFeedbackDataSetsToDB(projectName, email, Process, InputDic, outputJson, INPUTMEMORY = INPUTMemory)

        else:
            OutputDic = "Pass"
        
        TotalCount += 1
        ProcessCount = TotalCount + 1
        
        # Memory 형성
        MemoryLength = memoryLength
        # inputMemory 형성
        try:
            InputDic = InputList[TotalCount]
            inputMemoryDics.append(InputDic)
            inputMemory = ContextDefineInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = ContextDefineOutputMemory(outputMemoryDics, MemoryLength)
    
    return outputMemoryDics





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
    
    InputList = LifeGraphFrameTextsToInputList(lifeGraphSetName, latestUpdateDate)
    print(len(InputList))