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
# AddExistedCaptionCompletionToDB, AddCaptionCompletionChunksToDB, CaptionCompletionCountLoad, CaptionCompletionCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
## BodyFrameBodys 로드
def LoadBodyFrameBodys(projectName, email):
    project = GetProject(projectName, email)
    BodyFrameSplitedBodyScripts = project.BodyFrame[1]['SplitedBodyScripts'][1:]
    
    return BodyFrameSplitedBodyScripts

## BodyFrameBodys의 inputList 치환
def BodyFrameCaptionsToInputList(projectName, email):
    BodyFrameSplitedBodyScripts = LoadBodyFrameBodys(projectName, email)

    SplitedBodyChunkList = []
    for i in range(len(BodyFrameSplitedBodyScripts)):
        SplitedBodyChunks = BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks']
        for j in range(len(SplitedBodyChunks)):
            SplitedBodyChunkList.append(SplitedBodyChunks[j])

    InputList = []
    CaptionIdList = []
    id_counter = 1  # Id를 1부터 시작하기 위한 카운터

    j = 0
    while j < len(SplitedBodyChunkList):
        if SplitedBodyChunkList[j]['Tag'] in ['Caption', 'CaptionComment']:
            # 연속된 Caption 또는 CaptionComment 찾기
            combined_caption = SplitedBodyChunkList[j]['Chunk']
            temp_caption_ids = [SplitedBodyChunkList[j]['ChunkId']]  # 현재 ChunkId를 추가
            j += 1
            while j < len(SplitedBodyChunkList) and SplitedBodyChunkList[j]['Tag'] in ['Caption', 'CaptionComment']:
                combined_caption += SplitedBodyChunkList[j]['Chunk'] + ' '
                temp_caption_ids.append(SplitedBodyChunkList[j]['ChunkId'])  # 추가적인 ChunkId들을 추가
                j += 1

            # 앞뒤 5개 요소 포함하고 CaptionStart, CaptionEnd 추가
            start_idx = max(j - 6, 0)
            combined_chunks = ""
            for k in range(start_idx, j - len(temp_caption_ids)):
                combined_chunks += SplitedBodyChunkList[k]['Chunk'] + ' '
            combined_chunks += '\n\n[캡션시작]\n' + combined_caption + '\n[캡션끝]\n\n'
            end_idx = min(j + 5, len(SplitedBodyChunkList))
            for k in range(j, end_idx):
                combined_chunks += SplitedBodyChunkList[k]['Chunk'] + ' '

            InputList.append({'Id': id_counter, 'Continue': combined_chunks})
            CaptionIdList.append(temp_caption_ids)
            id_counter += 1  # 다음 아이템에 대해 Id 증가
        else:
            j += 1
        
    return InputList, CaptionIdList

######################
##### Filter 조건 #####
######################
## CaptionCompletion의 Filter(Error 예외처리)
def CaptionCompletionFilter(TalkTag, responseData, memoryCounter):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(responseData)
        OutputDic = [{key: value} for key, value in outputJson.items()]
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 결과가 list가 아닐 때의 예외 처리
    if not isinstance(OutputDic, list):
        return "JSONType에서 오류 발생: JSONTypeError"
    # # Error3: 결과가 '말하는인물'이 '없음'일 때의 예외 처리 (없음일 경우에는 Narrator 낭독)
    # for dic in OutputDic:
    #     for key, value in dic.items():
    #         if value['말하는인물'] == '없음' or value['말하는인물'] == '' or value['말하는인물'] == 'none':
    #             return "'말하는인물': '없음' 오류 발생: NonValueError"
    # Error4: 자료의 구조가 다를 때의 예외 처리
    for dic in OutputDic:
        try:
            key = list(dic.keys())[0]
            if not key in TalkTag:
                return "JSON에서 오류 발생: JSONKeyError"
            else:
                if not ('말의종류' in dic[key] and '말하는인물' in dic[key] and '말하는인물의성별' in dic[key] and '말하는인물의나이' in dic[key] and '말하는인물의감정' in dic[key] and '인물의역할' in dic[key] and '듣는인물' in dic[key]):
                    return "JSON에서 오류 발생: JSONKeyError"
        # Error5: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
    # Error6: Input과 Output의 개수가 다를 때의 예외처리
    if len(OutputDic) != len(TalkTag):
        return "JSONCount에서 오류 발생: JSONCountError"

    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def CaptionCompletionInputMemory(inputMemoryDics, MemoryLength):
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
def CaptionCompletionOutputMemory(outputMemoryDics, MemoryLength):
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
## CaptionCompletion 프롬프트 요청 및 결과물 Json화
def CaptionCompletionProcess(projectName, email, DataFramePath, Process = "CaptionCompletion", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '05', DataFramePath)    
    inputList = BodyFrameCaptionsToInputList(projectName, email)
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
        
    # CaptionCompletionProcess
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
                    
            Filter = CaptionCompletionFilter(responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(InputList) - 1} | {Filter}")
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(InputList) - 1} | JSONDecode 완료")
                
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
            inputMemory = CaptionCompletionInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = CaptionCompletionOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '05', DataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
    
## 데이터 치환
def CaptionCompletionResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):
    # Chunk, ChunkId 데이터 추출
    project = GetProject(projectName, email)
    BodyFrame = project.BodyFrame[1]['SplitedBodyScripts'][1:]
    CharacterTagChunk = []
    CharacterTagChunkId = []
    for i in range(len(BodyFrame)):
        for j in range(len(BodyFrame[i]['SplitedBodyChunks'])):
            if BodyFrame[i]['SplitedBodyChunks'][j]['Tag'] == "Character":
                CharacterTagChunk.append(BodyFrame[i]['SplitedBodyChunks'][j]['Chunk'])
                CharacterTagChunkId.append(BodyFrame[i]['SplitedBodyChunks'][j]['ChunkId'])
    
    # 데이터 치환
    outputMemoryDics = CaptionCompletionProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    responseCount = 0
    
    for response in outputMemoryDics:
        if response != "Pass":
            for dic in response:
                ChunkId = CharacterTagChunkId[responseCount]
                Chunk = CharacterTagChunk[responseCount]
                for key, value in dic.items():
                    Character = value['말하는인물']
                    Type = value['말의종류']
                    Gender = value['말하는인물의성별']
                    Age = value['말하는인물의나이']
                    Emotion = value['말하는인물의감정']
                    Role = value['인물의역할']
                    Listener = value['듣는인물']
                responseCount += 1
                responseJson.append({"ChunkId": ChunkId, "Chunk": Chunk, "Character": Character, "Type": Type, "Gender": Gender, "Age": Age, "Emotion": Emotion, "Role": Role, "Listener": Listener})
    
    return responseJson

## 프롬프트 요청 및 결과물 Json을 CaptionCompletion에 업데이트
def CaptionCompletionUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 05_CaptionCompletionUpdate 시작 >")
    # CaptionCompletion의 Count값 가져오기
    ContinueCount, CharacterCount, Completion = CaptionCompletionCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedCaptionCompletionToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "CaptionCompletion", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 05_CaptionCompletionUpdate는 ExistedCaptionCompletion으로 대처됨 ]\n")
        else:
            responseJson = CaptionCompletionResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            CharacterChunkId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'CaptionCompletionUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'CaptionCompletionUpdate: {Update}')
                time.sleep(0.0001)
                CharacterChunkId += 1
                ChunkId = Update["ChunkId"]
                Chunk = Update["Chunk"]
                Character = Update["Character"]
                Type = Update["Type"]
                Gender = Update["Gender"]
                Age = Update["Age"]
                Emotion = Update["Emotion"]
                Role = Update["Role"]
                Listener = Update["Listener"]
                
                AddCaptionCompletionChunksToDB(projectName, email, CharacterChunkId, ChunkId, Chunk, Character, Type, Gender, Age, Emotion, Role, Listener)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            CaptionCompletionCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 05_CaptionCompletionUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 05_CaptionCompletionUpdate는 이미 완료됨 ]\n")
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "웹3.0메타버스"
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################
    InputList, CaptionIdList = BodyFrameCaptionsToInputList(projectName, email)
    for input in InputList:
        print(input)