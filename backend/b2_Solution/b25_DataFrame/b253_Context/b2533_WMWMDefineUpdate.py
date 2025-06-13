import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b25_DataFrame.b251_DataCommit.b2511_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from backend.b2_Solution.b25_DataFrame.b251_DataCommit.b2512_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedWMWMDefineToDB, AddWMWMDefineChunksToDB, WMWMDefineCountLoad, WMWMDefineCompletionUpdate
from backend.b2_Solution.b25_DataFrame.b251_DataCommit.b2513_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
## BodyFrameBodys 로드
def LoadBodyFrameBodys(projectName, email):
    project = GetProject(projectName, email)
    BodyFrameSplitedBodyScripts = project.BodyFrame[1]['SplitedBodyScripts'][1:]
    BodyFrameBodys = project.BodyFrame[2]['Bodys'][1:]
    ContextChunks =  project.ContextDefine[1]['ContextChunks'][1:]
    
    return BodyFrameSplitedBodyScripts, BodyFrameBodys, ContextChunks

## inputList의 InputList 치환 (인덱스, 캡션 부분 합치기)
def MergeInputList(inputList):
    InputList = []
    MergeBuffer = ''
    MergeIds = []
    NonMergeFound = False

    for INput in inputList:
        if list(INput.keys())[1] == 'Merge':
            # 'Merge' 태그가 붙은 항목의 내용을 버퍼에 추가하고 ID를 MergeIds에 추가합니다.
            MergeBuffer += list(INput.values())[1]
            MergeIds.append(INput['Id'])
        else:
            # 'Merge'가 아닌 태그가 발견된 경우
            NonMergeFound = True
            if MergeBuffer:
                # 버퍼에 내용이 있으면 현재 항목과 합칩니다.
                content = MergeBuffer + list(INput.values())[1]
                # 'Id'는 MergeIds에 현재 항목의 'Id'를 추가하여 리스트로 만듭니다.
                currentId = MergeIds + [INput['Id']]
                # 합쳐진 내용과 'Id' 리스트를 가진 새 딕셔너리를 만듭니다.
                mergedINput = {'Id': currentId, list(INput.keys())[1]: content.replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')}
                InputList.append(mergedINput)
                # 버퍼와 ID 리스트를 초기화합니다.
                MergeBuffer = ''
                MergeIds = []
            else:
                # 버퍼가 비어 있으면 현재 항목을 결과 리스트에 그대로 추가합니다.
                InputList.append(INput)
    
    # 리스트의 끝에 도달했을 때 버퍼에 남아 있는 'Merge' 내용을 처리합니다.
    if MergeBuffer and not NonMergeFound:
        # 모든 항목이 'Merge'인 경우 마지막 항목만 처리합니다.
        mergedINput = {'Id': MergeIds, list(INput.keys())[1]: MergeBuffer.replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')}
        InputList.append(mergedINput)

    return InputList

## BodyFrameBodys의 inputList 치환
def BodyFrameBodysToInputList(projectName, email, Task = "Context"):
    BodyFrameSplitedBodyScripts, BodyFrameBodys, ContextChunks = LoadBodyFrameBodys(projectName, email)
    
    inputList = []
    for i in range(len(BodyFrameBodys)):
        Id = BodyFrameBodys[i]['BodyId']
        task = BodyFrameBodys[i]['Task']
        TaskBody = BodyFrameBodys[i][Task]

        if "Context" in task:
            Tag = 'Continue'
            # 메모 기입
            for j in range(len(ContextChunks)):
                ContextMemoIndex = f"{{메모{ContextChunks[j]['ContextChunkId']}}}"
                if ContextMemoIndex in TaskBody:
                    ContextMemoBody = f"[메모{ContextChunks[j]['ContextChunkId']}] {{'매칭독자': {ContextChunks[j]['Reader']}, '주제': {ContextChunks[j]['Subject']}, '읽는목적': {ContextChunks[j]['Purpose']}, '읽는원인': {ContextChunks[j]['Reason']}, '읽은후질문': {ContextChunks[j]['Question']}}}"
                    TaskBody = TaskBody.replace(ContextMemoIndex, ContextMemoBody)
                    
        elif 'Body' not in task:
            Tag = 'Merge'
        else:
            Tag = 'Pass'
            
        InputDic = {'Id': Id, Tag: TaskBody}
        inputList.append(InputDic)
        
    InputList = MergeInputList(inputList)
        
    return InputList

######################
##### Filter 조건 #####
######################
## WMWMDefine의 Filter(Error 예외처리)
def WMWMDefineFilter(MemoTag, responseData, memoryCounter):
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
            if not key in MemoTag:
                return "JSON에서 오류 발생: JSONMemoTagError"
            else:
                if not ('욕구상태' in dic[key] and '욕구상태선택이유' in dic[key] and '이해상태' in dic[key] and '이해상태선택이유' in dic[key] and '마음상태' in dic[key] and '마음상태선택이유' in dic[key] and '행동상태' in dic[key] and '행동상태선택이유' in dic[key] and '정확도' in dic[key]):
                    return "JSON에서 오류 발생: JSONKeyError"
                
            # 정확도 값이 숫자 또는 문자열 숫자인지 검사
            importance_value = dic[key]['정확도']
            if not (isinstance(importance_value, (int, float)) or 
                    (isinstance(importance_value, str) and importance_value.isdigit())):
                return "JSON에서 오류 발생: 정확도 값이 숫자가 아님"
                
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        # Error4: Input과 Output의 개수가 다를 때의 예외처리
        if len(OutputDic) != len(MemoTag):
            return f"JSONCount에서 오류 발생: JSONCountError, OutputDic: {len(OutputDic)}, MemoTag: {len(MemoTag)}"
        
    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def WMWMDefineInputMemory(inputMemoryDics, MemoryLength):
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
def WMWMDefineOutputMemory(outputMemoryDics, MemoryLength):
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
## WMWMDefine 프롬프트 요청 및 결과물 Json화
def WMWMDefineProcess(projectName, email, DataFramePath, Process = "WMWMDefine", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '09', DataFramePath)
    inputList = BodyFrameBodysToInputList(projectName, email)
    InputList = inputList[OutputMemoryCount:]
    if InputList == []:
        return OutputMemoryDicsFile

    FineTuningMemoryList = BodyFrameBodysToInputList(projectName, email, Task = "Body")
    TotalCount = 0
    ProcessCount = 1
    ContinueCount = 0
    inputMemoryDics = []
    inputMemory = []
    InputDic = InputList[0]
    inputMemoryDics.append(InputDic)
    outputMemoryDics = OutputMemoryDicsFile
    outputMemory = []
    ErrorCount = 0
        
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
            if Mode == "Master" or Mode == "ExampleFineTuning":
                memoTag = re.findall(r'\[핵심문구(\d{1,5})\]', str(Input))
            else:
                memoTag = re.findall(r'\[핵심문구(\d{1,5})\]', str(InputDic))
            
            MemoTag = ["핵심문구" + match for match in memoTag]
            memoryCounter = " - 이어서 작업할 데이터 (갯수만큼만 딱 맞게 작성): " + ', '.join(['[' + tag + ']' for tag in MemoTag]) + ' -\n'
            outputEnder = f"{{'핵심문구"

            # Response 생성
            Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)
            
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
                                
            Filter = WMWMDefineFilter(MemoTag, responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                
                # 2분 대기 이후 다시 코드 실행
                ErrorCount += 1
                print((f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | 오류횟수 {ErrorCount}회, 10초 후 프롬프트 재시도"))
                time.sleep(10)
                if ErrorCount >= 10:
                    sys.exit(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | 오류횟수 {ErrorCount}회 초과, 프롬프트 종료")

                continue

            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | JSONDecode 완료")
                ErrorCount = 0
                
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
            inputMemory = WMWMDefineInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = WMWMDefineOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '09', DataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
    
## 데이터 치환
def WMWMDefineResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):
    # Chunk, ChunkId 데이터 추출
    project = GetProject(projectName, email)
    ContextDefine = project.ContextDefine[1]['ContextChunks'][1:]
    
    # 데이터 치환
    outputMemoryDics = WMWMDefineProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)
    
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

## 프롬프트 요청 및 결과물 Json을 WMWMDefine에 업데이트
def WMWMDefineUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 09_WMWMDefineUpdate 시작 >")
    # WMWMDefine의 Count값 가져오기
    ContinueCount, WMWMCount, Completion = WMWMDefineCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedWMWMDefineToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "WMWMDefine", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 09_WMWMDefineUpdate는 ExistedWMWMDefine으로 대처됨 ]\n")
        else:
            responseJson = WMWMDefineResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            WMWMChunkId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'WMWMDefineUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'WMWMDefineUpdate: {Update}')
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
                
                AddWMWMDefineChunksToDB(projectName, email, WMWMChunkId, ChunkId, Chunk, Needs, ReasonOfNeeds, Wisdom, ReasonOfWisdom, Mind, ReasonOfMind, Wildness, ReasonOfWildness, Accuracy)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            WMWMDefineCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 09_WMWMDefineUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 09_WMWMDefineUpdate는 이미 완료됨 ]\n")
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################