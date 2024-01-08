import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import LoadOutputMemory, SaveOutputMemory
# AddExistedWMWMMatchingToDB, AddWMWMMatchingChunksToDB, WMWMMatchingCountLoad, WMWMMatchingCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
## ContextFrame 로드
def LoadContextCompeletions(projectName, email):
    project = GetProject(projectName, email)
    HalfBodyFrameSplitedBodyScripts = project.HalfBodyFrame[1]['SplitedBodyScripts'][1:]
    ContextChunks = project.ContextDefine[1]['ContextChunks'][1:]
    ContextCompeletions = project.ContextCompletion[1]['ContextCompeletions'][1:]
    WMWMCompeletions =  project.WMWMDefine[1]['WMWMCompeletions'][1:]
    # CharacterChunks = project.CharacterDefine[1]['CharacterChunks'][1:]
    # SFXSplitedBodys = project.SFXMatching[1]['SFXSplitedBodys'][1:]
    
    return HalfBodyFrameSplitedBodyScripts, ContextChunks, ContextCompeletions, WMWMCompeletions

## BodyFrameBodys의 inputList 치환
def ContextCompeletionsToInputList(projectName, email):
    HalfBodyFrameSplitedBodyScripts, ContextChunks, ContextCompeletions, WMWMCompeletions = LoadContextCompeletions(projectName, email)
    
    Scores = {
        "생리": 1, "안전": 2, "애정": 3, "존경": 4, "자아실현": 5,
        "무지": 1, "인지": 2, "이해": 3, "확신": 4, "지혜": 5,
        "거절": 1, "부정": 2, "중립": 3, "긍정": 4, "수용": 5,
        "소극": 1, "수동": 2, "능동": 3, "적극": 4, "성공": 5
    }
    BookTitle = HalfBodyFrameSplitedBodyScripts[0]['Index']
    SplitedBodyContexts = []
    SplitedBodyTexts = []
    ContextChunksCount = 0
    for i in range(len(HalfBodyFrameSplitedBodyScripts)):
        SplitedBodyScripts = HalfBodyFrameSplitedBodyScripts[i]
        IndexId = SplitedBodyScripts['IndexId']
        IndexTag = SplitedBodyScripts['IndexTag']
        Index = SplitedBodyScripts['Index']
        BodyId = SplitedBodyScripts['BodyId']
        SplitedBodyChunks = SplitedBodyScripts['SplitedBodyChunks']
        SplitedBodyContextsList = []
        SplitedBodyContextsText = []
        for j in range(len(SplitedBodyChunks)):
            FrameChunkId = SplitedBodyChunks[j]['ChunkId']
            ContextCounkId = ContextChunks[ContextChunksCount]['ChunkId']
            if isinstance(ContextCounkId, list):
                ContextCounkIdList = ContextCounkId
            else:
                ContextCounkIdList = [ContextCounkId]
            if FrameChunkId in ContextCounkIdList:
                ChunkId = ContextCounkId
                Chunk = ContextChunks[ContextChunksCount]['Chunk']
                
                Reader = ContextChunks[ContextChunksCount]['Reader']
                Subject = ContextChunks[ContextChunksCount]['Subject']
                Purpose = ContextChunks[ContextChunksCount]['Purpose']
                Reason = ContextChunks[ContextChunksCount]['Reason']
                Question = ContextChunks[ContextChunksCount]['Question']
                Importance = ContextChunks[ContextChunksCount]['Importance']
                ContextDefine = {"Reader": Reader, "Subject": Subject, "Purpose": Purpose, "Reason": Reason, "Question": Question, "Importance": Importance}
                
                Genre = ContextCompeletions[ContextChunksCount]['Genre']
                Gender = ContextCompeletions[ContextChunksCount]['Gender']
                Age = ContextCompeletions[ContextChunksCount]['Age']
                Personality = ContextCompeletions[ContextChunksCount]['Personality']
                Emotion = ContextCompeletions[ContextChunksCount]['Emotion']
                Accuracy = ContextCompeletions[ContextChunksCount]['Accuracy']
                ContextCompeletion = {"Genre": Genre, "Gender": Gender, "Age": Age, "Personality": Personality, "Emotion": Emotion, "Accuracy": Accuracy}
                
                Needs = WMWMCompeletions[ContextChunksCount]['Needs']
                ReasonOfNeeds = WMWMCompeletions[ContextChunksCount]['ReasonOfNeeds']
                Wisdom = WMWMCompeletions[ContextChunksCount]['Wisdom']
                ReasonOfWisdom = WMWMCompeletions[ContextChunksCount]['ReasonOfWisdom']
                Mind = WMWMCompeletions[ContextChunksCount]['Mind']
                ReasonOfPotentialMind = WMWMCompeletions[ContextChunksCount]['ReasonOfPotentialMind']
                Wildness = WMWMCompeletions[ContextChunksCount]['Wildness']
                ReasonOfWildness = WMWMCompeletions[ContextChunksCount]['ReasonOfWildness']
                accuracy = WMWMCompeletions[ContextChunksCount]['Accuracy']
                WMWMCompeletion = {"Needs": Needs, "ReasonOfNeeds": ReasonOfNeeds, "Wisdom": Wisdom, "ReasonOfWisdom": ReasonOfWisdom, "Mind": Mind, "ReasonOfPotentialMind": ReasonOfPotentialMind, "Wildness": Wildness, "ReasonOfWildness": ReasonOfWildness, "accuracy": accuracy}
                
                SplitedBodyContextsList.append({"ChunkId": ChunkId, "Chunk": Chunk, "ContextDefine": ContextDefine, "ContextCompeletion": ContextCompeletion, "WMWMCompeletion": WMWMCompeletion})
                
                NeedsScore = Scores.get(Needs, 0)
                WisdomScore = Scores.get(Wisdom, 0)
                MindScore = Scores.get(Mind, 0)
                WildnessScore = Scores.get(Wildness, 0)

                if isinstance(ChunkId, list):
                    ChunkId = ChunkId[0]
                
                SplitedBodyContextsText.append(f"○ {ContextChunksCount + 1}번째 토론: '{Chunk}' {BookTitle} 중에서\n\n- 토론 도서 -\n\n도서명: {BookTitle}\n목차: {Index}\n장르: {Genre}\n성별: {Gender}\n연령: {Age}\n성향: {Personality}\n감성: {Emotion}\n\n- 토론의 내용 -\n\n문구: {Chunk}\n대상독자: {Reader}\n주제: {Subject}\n목적: {Purpose}\n이유: {Reason}\n대표질문: {Question}\n\n- 토론의 유익성 -\n\n필요성: {NeedsScore}\n필요성 배점 이유: {ReasonOfNeeds}\n지식적 유익성: {WisdomScore}\n지식적 유익성 배점 이유: {ReasonOfWisdom}\n마음가짐의 유익성: {MindScore}\n마음가짐의 유익성 배점 이유: {ReasonOfPotentialMind}\n실천의 유익성: {WildnessScore}\n실천의 유익성 배점 이유: {ReasonOfWildness}\n\n\n")
                
                ContextChunksCount += 1
                
        SplitedBodyContexts.append({"IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "SplitedBodyContexts": SplitedBodyContextsList})
        if SplitedBodyContextsText != []:
            TaskBody = ''.join(SplitedBodyContextsText)
            SplitedBodyTexts.append({'Id': BodyId, 'Continue': TaskBody})
        else:
            SplitedBodyTexts.append({'Id': BodyId, 'Pass': ''})
        
    InputList = SplitedBodyTexts
        
    return SplitedBodyContexts, InputList

######################
##### Filter 조건 #####
######################
## WMWMMatching의 Filter(Error 예외처리)
def WMWMMatchingFilter(responseData, memoryCounter):
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
            key = '토론요약'
            if not ('장르' in dic[key] and '성별' in dic[key] and '연령' in dic[key] and '성향' in dic[key] and '감성' in dic[key] and '문구' in dic[key] and '대상독자' in dic[key] and '주제' in dic[key] and '목적' in dic[key] and '이유' in dic[key] and '대표질문' in dic[key] and '필요성' in dic[key] and '필요성배점이유' in dic[key] and '지식적유익성' in dic[key] and '지식적유익성배점이유' in dic[key] and '마음가짐의유익성' in dic[key] and '마음가짐의유익성배점이유' in dic[key] and '실천의유익성' in dic[key] and '실천의유익성배점이유' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        
    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def WMWMMatchingInputMemory(inputMemoryDics, MemoryLength):
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
def WMWMMatchingOutputMemory(outputMemoryDics, MemoryLength):
    outputMemoryDic = outputMemoryDics[-MemoryLength:]
    
    OUTPUTmemoryDic = []
    for INput in outputMemoryDic:
        if isinstance(INput, list):
            OUTPUTmemoryDic.extend(INput)
        else:
            OUTPUTmemoryDic.append(INput)
    OUTPUTmemoryDic = [entry for entry in OUTPUTmemoryDic if entry != "Pass"]
    outputMemory = str(OUTPUTmemoryDic)
    outputMemory = outputMemory[:-1] + ", "
    outputMemory = outputMemory.replace("[, ", "[")
    # print(f"@@@@@@@@@@\noutputMemory :{outputMemory}\n@@@@@@@@@@")
    
    return outputMemory

#######################
##### Process 진행 #####
#######################
## WMWMMatching 프롬프트 요청 및 결과물 Json화
def WMWMMatchingProcess(projectName, email, DataFramePath, Process = "WMWMMatching", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '10', DataFramePath)
    SplitedBodyContexts, inputList = ContextCompeletionsToInputList(projectName, email)
    
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
        
    # WMWMMatchingProcess
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
            
            memoryCounter = "\n"
            outputEnder = ""

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
                                
            Filter = WMWMMatchingFilter(responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | JSONDecode 완료")
                
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
            inputMemory = WMWMMatchingInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = WMWMMatchingOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '10', DataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
    
## 데이터 치환
def WMWMMatchingResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):
    # Chunk, ChunkId 데이터 추출
    project = GetProject(projectName, email)
    ContextDefine = project.ContextDefine[1]['ContextChunks'][1:]
    
    # 데이터 치환
    outputMemoryDics = WMWMMatchingProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    ContextDefineCount = 0
    for response in outputMemoryDics:
        if response != "Pass":
            for dic in response:
                for key, value in dic.items():
                    ChunkId = ContextDefine[ContextDefineCount]['ChunkId']
                    Chunk = ContextDefine[ContextDefineCount]['Chunk']
                    Needs = value['욕구상태']
                    ReasonOfNeeds = value['욕구상태선택이유']
                    Wisdom = value['이해상태']
                    ReasonOfWisdom = value['이해상태선택이유']
                    Mind = value['마음상태']
                    ReasonOfMind = value['마음상태선택이유']
                    Wildness = value['행동상태']
                    ReasonOfWildness = value['행동상태선택이유']
                    Accuracy = value['정확도']
                    ContextDefineCount += 1
                responseJson.append({"ChunkId": ChunkId, "Chunk": Chunk, "Needs": Needs, "ReasonOfNeeds": ReasonOfNeeds, "Wisdom": Wisdom, "ReasonOfWisdom": ReasonOfWisdom, "Mind": Mind, "ReasonOfMind": ReasonOfMind, "Wildness": Wildness, "ReasonOfWildness": ReasonOfWildness, "Accuracy": Accuracy})

    return responseJson

## 프롬프트 요청 및 결과물 Json을 WMWMMatching에 업데이트
def WMWMMatchingUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 10_WMWMMatchingUpdate 시작 >")
    # WMWMMatching의 Count값 가져오기
    ContinueCount, WMWMCount, Completion = WMWMMatchingCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedWMWMMatchingToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "WMWMMatching", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 10_WMWMMatchingUpdate는 ExistedWMWMMatching으로 대처됨 ]\n")
        else:
            responseJson = WMWMMatchingResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            WMWMChunkId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'WMWMMatchingUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'WMWMMatchingUpdate: {Update}')
                time.sleep(0.0001)
                WMWMChunkId += 1
                ChunkId = Update["ChunkId"]
                Chunk = Update["Chunk"]
                Needs = Update["Needs"]
                ReasonOfNeeds = Update["ReasonOfNeeds"]
                Wisdom = Update["Wisdom"]
                ReasonOfWisdom = Update["ReasonOfWisdom"]
                Mind = Update["Mind"]
                ReasonOfMind = Update["ReasonOfMind"]
                Wildness = Update["Wildness"]
                ReasonOfWildness = Update["ReasonOfWildness"]
                Accuracy = Update["Accuracy"]
                
                AddWMWMMatchingChunksToDB(projectName, email, WMWMChunkId, ChunkId, Chunk, Needs, ReasonOfNeeds, Wisdom, ReasonOfWisdom, Mind, ReasonOfMind, Wildness, ReasonOfWildness, Accuracy)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            WMWMMatchingCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 10_WMWMMatchingUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 10_WMWMMatchingUpdate는 이미 완료됨 ]\n")
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "웹3.0메타버스"
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################
    WMWMMatchingProcess(projectName, email, DataFramePath, Mode = "Example")