import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedCaptionCompletionToDB, AddCaptionCompletionChunksToDB, CaptionCompletionCountLoad, CaptionCompletionCompletionUpdate
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

            # 앞뒤 7개 요소 포함하고 CaptionStart, CaptionEnd 추가
            start_idx = max(j - 8, 0)  # 이전에는 max(j - 6, 0) 이었음
            combined_chunks = ""
            for k in range(start_idx, j - len(temp_caption_ids)):
                combined_chunks += SplitedBodyChunkList[k]['Chunk'] + ' '
            combined_chunks += '\n\n[캡션시작]\n' + combined_caption + '\n[캡션끝]\n\n'
            end_idx = min(j + 7, len(SplitedBodyChunkList))  # 이전에는 min(j + 5, len(SplitedBodyChunkList)) 이었음
            for k in range(j, end_idx):
                combined_chunks += SplitedBodyChunkList[k]['Chunk'] + ' '

            InputList.append({'Id': id_counter, 'Continue': combined_chunks})
            CaptionIdList.append(temp_caption_ids)
            id_counter += 1  # 다음 아이템에 대해 Id 증가
        else:
            j += 1
        
    return InputList, CaptionIdList, SplitedBodyChunkList

######################
##### Filter 조건 #####
######################
## CaptionCompletion의 Filter(Error 예외처리)
def CaptionCompletionFilter(responseData, memoryCounter):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        OutputDic = json.loads(responseData)
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    try:
        if not ('유형' in OutputDic and '맞는이유' in OutputDic and '아닌이유' in OutputDic and '최종캡션판단여부' in OutputDic and '정확도' in OutputDic) and (OutputDic['최종캡션판단여부'] == '맞다' or OutputDic['최종캡션판단여부'] == '아니다' or OutputDic['최종캡션판단여부'] == '알수없다'):
            return "JSON에서 오류 발생: JSONKeyError"
    # Error5: 자료의 형태가 Str일 때의 예외처리
    except AttributeError:
        return "JSON에서 오류 발생: strJSONError"

    return {'json': OutputDic, 'filter': OutputDic}

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

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '06', DataFramePath)
    inputList, CaptionIdList, SplitedBodyChunkList = BodyFrameCaptionsToInputList(projectName, email)
    InputList = inputList[OutputMemoryCount:]
    if InputList == []:
        return OutputMemoryDicsFile, CaptionIdList, SplitedBodyChunkList

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
                    
            Filter = CaptionCompletionFilter(responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                
                # 2분 대기 이후 다시 코드 실행
                time.sleep(120)
                ErrorCount += 1
                if ErrorCount == 3:
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
            inputMemory = CaptionCompletionInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = CaptionCompletionOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '06', DataFramePath)
    
    return outputMemoryDics, CaptionIdList, SplitedBodyChunkList
################################
##### 데이터 치환 및 DB 업데이트 #####
################################
# ## BodyFrame CaptionTag 업데이트
# def CaptionTagUpdateToBodyFrame(BodyFrame, CaptionFrame):
#     ## BodyFrame CaptionTag 업데이트
#     for i in range(len(BodyFrame)):
#         SplitedBodyChunks = BodyFrame[i]['SplitedBodyChunks']
#         for j in range(len(SplitedBodyChunks)):
#             for k in range(len(CaptionFrame)):
#                 CaptionTag = CaptionFrame[k]['CaptionTag']
#                 ChunkIds = CaptionFrame[k]['ChunkIds']
#                 SplitedCaptionChunks = CaptionFrame[k]['SplitedCaptionChunks']
#                 for l in range(len(SplitedCaptionChunks)):
#                     if SplitedBodyChunks[j]['ChunkId'] == SplitedCaptionChunks[l]['ChunkId']:
#                         SplitedBodyChunks[j]['NewTag'] = SplitedCaptionChunks[l]['Tag']
#                     if SplitedBodyChunks[j]['ChunkId'] == ChunkIds[0] and CaptionTag == 'Caption':
#                         SplitedBodyChunks[j]['CaptionMusicStart'] = "None"
#                     if SplitedBodyChunks[j]['ChunkId'] == ChunkIds[-1] and CaptionTag == 'Caption':
#                         SplitedBodyChunks[j]['CaptionMusicEnd'] = "None"

#     return BodyFrame

# ## CaptionCompletion의 BodyFrame전환
# def CaptionCompletionToBodyFrame(projectName, email):
#     # BodyFrame CaptionTag 업데이트
#     with get_db() as db:
#         project = GetProject(projectName, email)
#         BodyFrame = project.BodyFrame[1]["SplitedBodyScripts"][1:]
#         CaptionFrame = project.CaptionFrame[1]['CaptionCompletions'][1:]

#         BodyFrame = CaptionTagUpdateToBodyFrame(BodyFrame, CaptionFrame)
#     flag_modified(project, "BodyFrame")
#     db.add(project)
#     db.commit()
    
#     # HalfBodyFrame CaptionTag 업데이트
#     with get_db() as db:
#         project = GetProject(projectName, email)
#         HalfBodyFrame = project.HalfBodyFrame[1]["SplitedBodyScripts"][1:]
#         CaptionFrame = project.CaptionFrame[1]['CaptionCompletions'][1:]
        
#         HalfBodyFrame = CaptionTagUpdateToBodyFrame(HalfBodyFrame, CaptionFrame)
#     flag_modified(project, "HalfBodyFrame")
#     db.add(project)
#     db.commit()

## 데이터 치환
def CaptionCompletionResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):   
    # 데이터 치환
    outputMemoryDics, CaptionIdList, SplitedBodyChunkList = CaptionCompletionProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    for i, response in enumerate(outputMemoryDics):
        CaptionId = i + 1
        CaptionType = response['유형']
        Importance = response['정확도']
        if response['최종캡션판단여부'] == '맞다' and int(Importance) >= 80:
            CaptionTag = 'Caption'
            Reason = response['맞는이유']
        else:
            CaptionTag = 'Narrator'
            Reason = response['아닌이유']
        ChunkIds = CaptionIdList[i]
        CaptionCompletion = {"CaptionId": CaptionId, "CaptionTag": CaptionTag, "CaptionType": CaptionType, "Reason": Reason, "Importance": Importance, "ChunkIds": ChunkIds, "SplitedCaptionChunks": []}
        for Chunkid in ChunkIds:
            ChunkId = Chunkid
            for j in range(len(SplitedBodyChunkList)):
                if ChunkId == SplitedBodyChunkList[j]['ChunkId']:
                    Tag = SplitedBodyChunkList[j]['Tag']
                    Chunk = SplitedBodyChunkList[j]['Chunk']
                    break
            if CaptionTag == 'Caption' and Tag == 'Caption':
                NewTag = 'Caption'
            elif CaptionTag == 'Caption' and Tag == 'CaptionComment':
                NewTag = 'CaptionComment'
            else:
                NewTag = 'Narrator'
                
            CaptionCompletion['SplitedCaptionChunks'].append({"ChunkId": ChunkId, "Tag": NewTag, "Chunk": Chunk})
        
        responseJson.append(CaptionCompletion)
    
    return responseJson

## 프롬프트 요청 및 결과물 Json을 CaptionCompletion에 업데이트
def CaptionCompletionUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 06_CaptionCompletionUpdate 시작 >")
    # CaptionCompletion의 Count값 가져오기
    ContinueCount, Completion = CaptionCompletionCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedCaptionCompletionToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "CaptionCompletion", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 06_CaptionCompletionUpdate는 ExistedCaptionCompletion으로 대처됨 ]\n")
        else:
            responseJson = CaptionCompletionResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'CaptionCompletionUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'CaptionCompletionUpdate: {Update["CaptionType"]}')
                time.sleep(0.0001)
                CaptionId = Update["CaptionId"]
                CaptionTag = Update["CaptionTag"]
                CaptionType = Update["CaptionType"]
                Reason = Update["Reason"]
                Importance = Update["Importance"]
                ChunkIds = Update["ChunkIds"]
                SplitedCaptionChunks = Update["SplitedCaptionChunks"]
                
                AddCaptionCompletionChunksToDB(projectName, email, CaptionId, CaptionTag, CaptionType, Reason, Importance, ChunkIds, SplitedCaptionChunks)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # # BodyFrame CaptionTag 업데이트
            # CaptionCompletionToBodyFrame(projectName, email)
            # Completion "Yes" 업데이트
            CaptionCompletionCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 06_CaptionCompletionUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 06_CaptionCompletionUpdate는 이미 완료됨 ]\n")
        
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