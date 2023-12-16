import re
import json
import tiktoken
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from extension.e1_Solution.e11_General.e111_GetDBtable import GetExtensionPromptFrame
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraph
from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import LoadExtensionOutputMemory, SaveExtensionOutputMemory, AddExistedLifeGraphWMWMDefineToDB, AddLifeGraphWMWMDefineCompeletionsToDB, AddLifeGraphWMWMDefineQuerysToDB, LifeGraphWMWMDefineCountLoad, InitLifeGraphWMWMDefine, LifeGraphWMWMDefineCompletionUpdate, UpdatedLifeGraphWMWMDefine

#########################
##### InputList 생성 #####
#########################
# LifeDataContextTexts 로드
def LoadLifeDataContextTexts(lifeGraphSetName, latestUpdateDate):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeDataContextTexts = lifeGraph.LifeGraphContextDefine[2]['LifeDataContextTexts'][1:109]
    
    return LifeDataContextTexts

## LifeGraphFrameTexts의 inputList 치환
def LifeDataContextTextsToInputList(lifeGraphSetName, latestUpdateDate):
    LifeDataContextTexts = LoadLifeDataContextTexts(lifeGraphSetName, latestUpdateDate)   
    
    InputList = []
    for i in range(len(LifeDataContextTexts)):
        Id = LifeDataContextTexts[i]['LifeGraphId']
        Translation = LifeDataContextTexts[i]['Translation']
        Text = LifeDataContextTexts[i]['Text']
        
        if Translation != 'ko':
            Tag = 'Pass'
        else:
            Tag = 'Continue'
            
        InputDic = {'Id': Id, Tag: Text}
        InputList.append(InputDic)
        
    return InputList

######################
##### Filter 조건 #####
######################
## LifeGraphWMWMDefine의 Filter(Error 예외처리)
def LifeGraphWMWMDefineFilter(MemoTag, responseData, memoryCounter):
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
            if not '중요부분' in key:
                return "JSON에서 오류 발생: JSONKeyError"
            elif not ('욕구상태' in dic[key] and '욕구상태선택이유' in dic[key] and '이해상태' in dic[key] and '이해상태선택이유' in dic[key] and '마음상태' in dic[key] and '마음상태선택이유' in dic[key] and '행동상태' in dic[key] and '행동상태선택이유' in dic[key] and '정확도' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        if len(OutputDic) != len(MemoTag):
            return f"JSONCount에서 오류 발생: JSONCountError, OutputDic: {len(OutputDic)}, MemoTag: {len(MemoTag)}"
        
    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def LifeGraphWMWMDefineInputMemory(inputMemoryDics, MemoryLength):
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
def LifeGraphWMWMDefineOutputMemory(outputMemoryDics, MemoryLength):
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
## LifeGraphWMWMDefine 프롬프트 요청 및 결과물 Json화
def LifeGraphWMWMDefineProcess(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, Process = "LifeGraphWMWMDefine", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):

    OutputMemoryDicsFile, OutputMemoryCount = LoadExtensionOutputMemory(lifeGraphSetName, latestUpdateDate, '05', LifeGraphDataFramePath)    
    inputList = LifeDataContextTextsToInputList(lifeGraphSetName, latestUpdateDate)
    InputList = inputList[OutputMemoryCount:]
    if InputList == []:
        return OutputMemoryDicsFile

    TotalCount = 0
    ProcessCount = 1
    ContinueCount = 0
    inputMemoryDics = []
    inputMemory = []
    InputDic = InputList[0]
    inputMemoryDics.append(InputDic)
    outputMemoryDics = OutputMemoryDicsFile
    outputMemory = []
        
    # WMWMDefineProcess
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
            else:
                mode = "MemoryFineTuning"
        # Example 계열 모드의 순서
        elif Mode == "Master":
            mode = "Master"
        elif Mode == "ExampleFineTuning":
            mode = "ExampleFineTuning"
        elif Mode == "Example":
            mode = "Example"
            
        if "Continue" in InputDic:
            Input = InputDic['Continue']
            
            # Filter, MemoryCounter, OutputEnder 처리
            if Mode == "Master" or Mode == "ExampleFineTuning":
                memoTag = re.findall(r'\[중요부분(\d{1,5})\]', str(Input))
            else:
                memoTag = re.findall(r'\[중요부분(\d{1,5})\]', str(InputDic))
            
            MemoTag = ["중요부분" + match for match in memoTag]
            memoryCounter = " - 이어서 작업할 데이터 (갯수만큼만 딱 맞게 작성): " + ', '.join(['[' + tag + ']' for tag in MemoTag]) + ' -\n'
            outputEnder = f"{{'중요부분"
            
            # Response 생성
            Response, Usage, Model = LLMresponse(lifeGraphSetName, latestUpdateDate, Process, Input, ProcessCount, root = "extension", Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)

            # OutputStarter, OutputEnder에 따른 Response 전처리
            promptFrame = GetExtensionPromptFrame(Process)
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
         
            Filter = LifeGraphWMWMDefineFilter(MemoTag, responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"LifeGraphSetName: {lifeGraphSetName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                print(f"LifeGraphSetName: {lifeGraphSetName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | JSONDecode 완료")
                
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
            inputMemory = LifeGraphWMWMDefineInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = LifeGraphWMWMDefineOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveExtensionOutputMemory(lifeGraphSetName, latestUpdateDate, outputMemoryDics, '05', LifeGraphDataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################

def LifeGraphWMWMDefineResponseJson(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, messagesReview = 'off', mode = "Memory"):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    ContextChunks = lifeGraph.LifeGraphContextDefine[1]['ContextChunks'][1:]
    outputMemoryDics = LifeGraphWMWMDefineProcess(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    for i, response in enumerate(outputMemoryDics):
        if response != "Pass":
            LifeGraphId = i + 1
            Translation = ContextChunks[i]['Translation']
            WMWMChunks = []
            for j, Dic in enumerate(response):
                key = list(Dic.keys())[0]
                ChunkId = j + 1
                Chunk = ContextChunks[i]['ContextChunks'][j]['Chunk']
                Needs = Dic[key]['욕구상태']
                ReasonOfNeeds = Dic[key]['욕구상태선택이유']
                Wisdom = Dic[key]['이해상태']
                ReasonOfWisdom = Dic[key]['이해상태선택이유']
                Mind = Dic[key]['마음상태']
                ReasonOfMind = Dic[key]['마음상태선택이유']
                Wildness = Dic[key]['행동상태']
                ReasonOfWildness = Dic[key]['행동상태선택이유']
                Accuracy = Dic[key]['정확도']
                WMWMChunk = {'ChunkId': ChunkId, 'Chunk': Chunk, 'Needs': Needs, 'ReasonOfNeeds': ReasonOfNeeds, 'Wisdom': Wisdom, 'ReasonOfWisdom': ReasonOfWisdom, 'Mind': Mind, 'ReasonOfMind': ReasonOfMind, 'Wildness': Wildness, 'ReasonOfWildness': ReasonOfWildness, 'Accuracy': Accuracy}
                WMWMChunks.append(WMWMChunk)
            responseJson.append({'LifeGraphId': LifeGraphId, 'Translation': Translation, 'WMWMChunks': WMWMChunks})

    return responseJson

def WMWMToQuerys(lifeGraphSetName, latestUpdateDate, ResponseJson):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    lifeGraphContextDefine = lifeGraph.LifeGraphContextDefine[1]['ContextChunks'][1:]

    WMWMQuerys = []
    for i in range(len(lifeGraphContextDefine)):
        LifeGraphId = lifeGraphContextDefine[i]["LifeGraphId"]
        Translation = lifeGraphContextDefine[i]["Translation"]
        Querys = []
        for j in range(len(lifeGraphContextDefine[i]["ContextChunks"])):
            ChunkId = j + 1
            
            Purpose = lifeGraphContextDefine[i]['ContextChunks'][j]['Purpose']
            Reason = lifeGraphContextDefine[i]['ContextChunks'][j]['Reason']
            Question = lifeGraphContextDefine[i]['ContextChunks'][j]['Question']
            Chunk = lifeGraphContextDefine[i]['ContextChunks'][j]['Chunk']
            Subject = lifeGraphContextDefine[i]['ContextChunks'][j]['Subject']
            Writer = lifeGraphContextDefine[i]['ContextChunks'][j]['Writer']
            Vector = {"Purpose": Purpose, "Reason": Reason, "Question": Question, "Chunk": Chunk, "Subject": Subject, "Writer": Writer}
            
            Needs = ResponseJson[i]['WMWMChunks'][j]['Needs']
            Wisdom = ResponseJson[i]['WMWMChunks'][j]['Wisdom']
            Mind = ResponseJson[i]['WMWMChunks'][j]['Mind']
            Wildness = ResponseJson[i]['WMWMChunks'][j]['Wildness']
            WMWM = {"Needs": Needs, "Wisdom": Wisdom, "Mind": Mind, "Wildness": Wildness}
            
            Querys.append({'ChunkId': ChunkId, 'Vector': Vector, 'WMWM': WMWM})
            
        WMWMQuery = {'LifeGraphId': LifeGraphId, 'Translation': Translation, 'Querys': Querys}
        WMWMQuerys.append(WMWMQuery)

    return WMWMQuerys

## LifeDataTexts를 LifeGraphWMWMDefine에 업데이트
def LifeGraphWMWMDefineQuerysUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson):
    WMWMQuerys = WMWMToQuerys(lifeGraphSetName, latestUpdateDate, ResponseJson)
    WMWMQuerysCount = len(WMWMQuerys)
    
    # TQDM 셋팅
    UpdateTQDM = tqdm(WMWMQuerys,
                    total = WMWMQuerysCount,
                    desc = 'LifeGraphWMWMDefineQuerysUpdate')
    # i값 수동 생성
    i = 0
    for Update in UpdateTQDM:
        UpdateTQDM.set_description(f'LifeGraphWMWMDefineQuerysUpdate: ...')
        time.sleep(0.0001)
        LifeGraphId = i + 1
        Translation = Update['Translation']
        Querys = Update['Querys']
        
        AddLifeGraphWMWMDefineQuerysToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Translation, Querys)
        # i값 수동 업데이트
        i += 1

    UpdateTQDM.close()

## 결과물 Json을 LifeGraphWMWMDefine에 업데이트
def LifeGraphWMWMDefineUpdate(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None):
    print(f"< LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 05_LifeGraphWMWMDefineUpdate 시작 >")
    # LifeGraphWMWMDefine의 Count값 가져오기
    LifeGraphCount, WMWMQuerysCount, Completion = LifeGraphWMWMDefineCountLoad(lifeGraphSetName, latestUpdateDate)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedLifeGraphWMWMDefineToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame)
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 05_LifeGraphWMWMDefine로 대처됨 ]\n")
        else:
            responseJson = LifeGraphWMWMDefineResponseJson(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, messagesReview = MessagesReview, mode = Mode)
            # LifeGraphs를 LifeGraphCount로 슬라이스
            ResponseJson = responseJson[LifeGraphCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'LifeGraphWMWMDefineUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'LifeGraphWMWMDefineUpdate: ...')
                time.sleep(0.0001)
                
                LifeGraphId = i + 1
                Translation = Update["Translation"]
                WMWMChunks = Update["WMWMChunks"]

                AddLifeGraphWMWMDefineCompeletionsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Translation, WMWMChunks)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            ##### LifeDataTexts 업데이트
            LifeGraphWMWMDefineQuerysUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson)
            #####
            # Completion "Yes" 업데이트
            LifeGraphWMWMDefineCompletionUpdate(lifeGraphSetName, latestUpdateDate)
            
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 05_LifeGraphWMWMDefineUpdate 완료 ]\n")
    else:
        print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 05_LifeGraphWMWMDefineUpdate는 이미 완료됨 ]\n")
    
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################