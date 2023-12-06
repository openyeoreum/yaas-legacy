import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import AddExistedCharacterDefineToDB, AddCharacterDefineChunksToDB, CharacterDefineCountLoad, CharacterDefineCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
## BodyFrameBodys 로드
def LoadBodyFrameBodys(projectName, email):
    project = GetProject(projectName, email)
    BodyFrameSplitedBodyScripts = project.BodyFrame[1]['SplitedBodyScripts'][1:]
    BodyFrameBodys = project.BodyFrame[2]['Bodys'][1:]
    
    return BodyFrameSplitedBodyScripts, BodyFrameBodys

## inputList의 InputList 치환 (인덱스, 캡션 부분 합치기)
def MergeInputList(inputList):
    InputList = []
    MergeBuffer = ''
    MergeIds = []
    NonMergeFound = False

    for item in inputList:
        if list(item.keys())[1] == 'Merge':
            # 'Merge' 태그가 붙은 항목의 내용을 버퍼에 추가하고 ID를 MergeIds에 추가합니다.
            MergeBuffer += list(item.values())[1]
            MergeIds.append(item['Id'])
        else:
            # 'Merge'가 아닌 태그가 발견된 경우
            NonMergeFound = True
            if MergeBuffer:
                # 버퍼에 내용이 있으면 현재 항목과 합칩니다.
                content = MergeBuffer + list(item.values())[1]
                # 'Id'는 MergeIds에 현재 항목의 'Id'를 추가하여 리스트로 만듭니다.
                currentId = MergeIds + [item['Id']]
                # 합쳐진 내용과 'Id' 리스트를 가진 새 딕셔너리를 만듭니다.
                mergedItem = {'Id': currentId, list(item.keys())[1]: content.replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')}
                InputList.append(mergedItem)
                # 버퍼와 ID 리스트를 초기화합니다.
                MergeBuffer = ''
                MergeIds = []
            else:
                # 버퍼가 비어 있으면 현재 항목을 결과 리스트에 그대로 추가합니다.
                InputList.append(item)
    
    # 리스트의 끝에 도달했을 때 버퍼에 남아 있는 'Merge' 내용을 처리합니다.
    if MergeBuffer and not NonMergeFound:
        # 모든 항목이 'Merge'인 경우 마지막 항목만 처리합니다.
        mergedItem = {'Id': MergeIds, list(item.keys())[1]: MergeBuffer.replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')}
        InputList.append(mergedItem)

    return InputList

## BodyFrameBodys의 inputList 치환
def BodyFrameBodysToInputList(projectName, email, Task = "Character"):
    BodyFrameSplitedBodyScripts, BodyFrameBodys = LoadBodyFrameBodys(projectName, email)
    
    inputList = []
    for i in range(len(BodyFrameBodys)):
        Id = BodyFrameBodys[i]['BodyId']
        task = BodyFrameBodys[i]['Task']
        TaskBody = BodyFrameBodys[i][Task]

        if Task in task:
            Tag = 'Continue'
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
## CharacterDefine의 Filter(Error 예외처리)
def CharacterDefineFilter(TalkTag, responseData, memoryCounter):
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
def CharacterDefineInputMemory(inputMemoryDics, MemoryLength):
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
def CharacterDefineOutputMemory(outputMemoryDics, MemoryLength):
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
## CharacterDefine 프롬프트 요청 및 결과물 Json화
def CharacterDefineProcess(projectName, email, Process = "CharacterDefine", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
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
        
    # CharacterDefineProcess
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
            talkTag = re.findall(r'\[말(\d{1,5})\]', str(InputDic))
            TalkTag = ["말" + match for match in talkTag]
            memoryCounter = " - 이어서 작업할 데이터: " + ', '.join(['[' + tag + ']' for tag in TalkTag]) + ' -\n'
            outputEnder = f"{{'{TalkTag[0]}': {{'말의종류': '"

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
                    
            Filter = CharacterDefineFilter(TalkTag, responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{len(InputList) - 1} | {Filter}")
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{len(InputList) - 1} | JSONDecode 완료")
                
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
            inputMemory = CharacterDefineInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = CharacterDefineOutputMemory(outputMemoryDics, MemoryLength)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
    
## 데이터 치환
def CharacterDefineResponseJson(projectName, email, messagesReview = 'off', mode = "Memory"):
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
    outputMemoryDics = CharacterDefineProcess(projectName, email, MessagesReview = messagesReview, Mode = mode)
    
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

## 프롬프트 요청 및 결과물 Json을 CharacterDefine에 업데이트
def CharacterDefineUpdate(projectName, email, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 11_CharacterDefineUpdate 시작 >")
    # SummaryBodyFrame의 Count값 가져오기
    ContinueCount, CharacterCount, Completion = CharacterDefineCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedCharacterDefineToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "CharacterDefine", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 11_CharacterDefineUpdate는 ExistedCharacterDefine으로 대처됨 ]\n")
        else:
            responseJson = CharacterDefineResponseJson(projectName, email, messagesReview = MessagesReview, mode = Mode)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            CharacterChunkId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'CharacterDefineUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'CharacterDefineUpdate: {Update}')
                time.sleep(0.0001)
                CharacterChunkId += 1
                ChunkId = ResponseJson[i]["ChunkId"]
                Chunk = ResponseJson[i]["Chunk"]
                Character = ResponseJson[i]["Character"]
                Type = ResponseJson[i]["Type"]
                Gender = ResponseJson[i]["Gender"]
                Age = ResponseJson[i]["Age"]
                Emotion = ResponseJson[i]["Emotion"]
                Role = ResponseJson[i]["Role"]
                Listener = ResponseJson[i]["Listener"]
                
                AddCharacterDefineChunksToDB(projectName, email, CharacterChunkId, ChunkId, Chunk, Character, Type, Gender, Age, Emotion, Role, Listener)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            CharacterDefineCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 11_CharacterDefineUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 11_CharacterDefineUpdate는 이미 완료됨 ]\n")
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "데미안"
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################