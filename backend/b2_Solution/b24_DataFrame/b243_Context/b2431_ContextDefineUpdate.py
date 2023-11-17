import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import AddExistedContextDefineToDB, AddContextDefineChunksToDB, ContextDefineCountLoad, ContextDefineCompletionUpdate
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
                mergedItem = { 'Id': currentId, list(item.keys())[1]: content.replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')}
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
        mergedItem = { 'Id': MergeIds, list(item.keys())[1]: MergeBuffer.replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')}
        InputList.append(mergedItem)

    return InputList

## BodyFrameBodys의 inputList 치환
def BodyFrameBodysToInputList(projectName, email, Task = "Body"):
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
            print(f'Pass Task: {task}')
            print(f'Pass TaskBody: {TaskBody}')
            
        InputDic = {'Id': Id, Tag: TaskBody}
        inputList.append(InputDic)
        
    InputList = MergeInputList(inputList)
        
    return InputList

######################
##### Filter 조건 #####
######################
## ContextDefine의 Filter(Error 예외처리)
def ContextDefineFilter(Input, responseData, memoryCounter):
    # responseData의 전처리
    responseData = responseData.replace("<태그.json>" + memoryCounter, "").replace("<태그.json>" + memoryCounter + " ", "")
    responseData = responseData.replace("<태그.json>", "").replace("<태그.json> ", "")
    responseData = responseData.replace("\n", "").replace("'", "\"")
    responseData = responseData.replace("```json", "").replace("```", "")
    responseData = re.sub(r'^\[', '', responseData) # 시작에 있는 대괄호[를 제거
    responseData = re.sub(r'\]$', '', responseData) # 끝에 있는 대괄호]를 제거
    responseData = f"[{responseData}]"

    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        OutputDic = json.loads(responseData)
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
            # '문구' 키에 접근하는 부분에 예외 처리 추가
            try:
                OUTPUT = re.sub("[^가-힣]", "", str(dic[key]['문구']))
            except TypeError:
                return "JSON에서 오류 발생: TypeError"
            except KeyError:
                return "JSON에서 오류 발생: KeyError"
            if not '메모' in key:
                return "JSON에서 오류 발생: JSONKeyError"
            elif not OUTPUT in INPUT:
                return f"JSON에서 오류 발생: JSON '문구'가 Input에 포함되지 않음 Error\n문구: {dic[key]['문구']}"
            elif not ('독자' in dic[key] and '목적' in dic[key] and '주제' in dic[key] and '문구' in dic[key] and '중요도' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        
    return OutputDic

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def ContextDefineInputMemory(inputMemoryDics, MemoryLength):
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
def ContextDefineOutputMemory(outputMemoryDics, MemoryLength):
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
                OutputDic = Filter
                print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{len(InputList)} | JSONDecode 완료")
                
                # DataSets 업데이트
                if mode in ["Example", "ExampleFineTuning", "Master"]:
                    # mode가 ["Example", "ExampleFineTuning", "Master"]중 하나인 경우 Memory 초기화
                    INPUTMemory = "None"
                elif mode in ["Memory", "MemoryFineTuning"]:
                    INPUTMemory = inputMemory
                    
                AddProjectRawDatasetToDB(projectName, email, Process, mode, Model, Usage, InputDic, OutputDic, INPUTMEMORY = INPUTMemory)
                AddProjectFeedbackDataSetsToDB(projectName, email, Process, InputDic, OutputDic, INPUTMEMORY = INPUTMemory)

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

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
    
## 데이터 치환
def ContextDefineResponseJson(projectName, email, messagesReview = 'off', mode = "Memory"):
    # Chunk, ChunkId 데이터 추출
    project = GetProject(projectName, email)
    BodyFrame = project.BodyFrame[1]['SplitedBodyScripts'][1:]
    
    # 데이터 치환
    # outputMemoryDics = ContextDefineProcess(projectName, email, MessagesReview = messagesReview, Mode = mode)
    
    ### 테스트 후 삭제 ###
    filepath = '/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/yeoreum00128@gmail.com_우리는행복을진단한다_06_OutputMemoryDics_231028.json'
    with open(filepath, 'r', encoding='utf-8') as file:
        outputMemoryDics = json.load(file)
    ### 테스트 후 삭제 ###
    
    responseJson = []
    StartCount = 0  # 시작 인덱스 초기화
    for response in outputMemoryDics:
        if response != "Pass":
            for dic in response:
                for key, value in dic.items():
                    CleanPhrases = re.sub("[^가-힣]", "", str(value['문구']))
                    found = False  # 플래그 설정
                    ChunkId = None  # 기본값 설정
                    Chunk = None  # 기본값 설정
                    for i in range(len(BodyFrame)):
                        if found:
                            break
                        for j in range(StartCount, len(BodyFrame[i]['SplitedBodyChunks'])):  # StartCount부터 시작
                            CleanChunk = re.sub("[^가-힣]", "", str(BodyFrame[i]['SplitedBodyChunks'][j]['Chunk']))
                            if CleanPhrases in CleanChunk:
                                ChunkId = BodyFrame[i]['SplitedBodyChunks'][j]['ChunkId']
                                Chunk = BodyFrame[i]['SplitedBodyChunks'][j]['Chunk']
                                # StartCount = j + 1  # 다음 검색 시작 위치 업데이트
                                found = True
                                break
                    Reader = value['독자']
                    Purpose = value['목적']
                    Subject = value['주제']
                    Phrases = value['문구']
                    Importance = value['중요도']
                responseJson.append({"ChunkId": ChunkId, "Chunk": Chunk, "Reader": Reader, "Purpose": Purpose, "Subject": Subject, "Phrases": Phrases, "Importance": Importance})

    # Chunk가 None인 경우 재분석
    PrevSwitch = 0
    PrevCleanChunk = ""
    for response in responseJson:
        if response['Chunk'] is None:  # 'None' 비교 시 'is None' 사용
            CleanPhrases = re.sub("[^가-힣]", "", str(response['Phrases']))
            found = False  # 플래그 변수 추가
            for i in range(len(BodyFrame)):
                if found:
                    break  # 외부 루프 종료 조건 추가
                ChunkIds = []
                Chunks = []
                CleanChunks = ""
                for j in range(len(BodyFrame[i]['SplitedBodyChunks'])):
                    CleanChunk = re.sub("[^가-힣]", "", str(BodyFrame[i]['SplitedBodyChunks'][j]['Chunk']))
                    TestPrevCleanChunk = re.sub("[^가-힣]", "", str(BodyFrame[i]['SplitedBodyChunks'][j-1]['Chunk']))
                    if len(TestPrevCleanChunk) <= 3:
                        TestPrevCleanChunk = "None"
                    if (CleanChunk in CleanPhrases) and (CleanChunk != ''):
                        if PrevSwitch == 0 and ((TestPrevCleanChunk[-3:] + CleanChunk) in CleanPhrases) and j > 0:
                            PrevCleanChunk = re.sub("[^가-힣]", "", str(BodyFrame[i]['SplitedBodyChunks'][j-1]['Chunk']))
                            PrevChunkId = BodyFrame[i]['SplitedBodyChunks'][j-1]['ChunkId']
                            PrevChunk = BodyFrame[i]['SplitedBodyChunks'][j-1]['Chunk']
                            PrevSwitch = 1
                        ChunkIds.append(BodyFrame[i]['SplitedBodyChunks'][j]['ChunkId'])
                        Chunks.append(BodyFrame[i]['SplitedBodyChunks'][j]['Chunk'])
                        CleanChunks += CleanChunk
                        if CleanChunks == CleanPhrases:
                            response['ChunkId'] = ChunkIds
                            response['Chunk'] = Chunks
                            PrevCleanChunk = ""
                            PrevSwitch = 0
                            found = True  # 플래그 변수 설정
                            break  # 현재 루프 종료
                        elif (CleanPhrases in (PrevCleanChunk + CleanChunks)) and (PrevCleanChunk not in CleanPhrases):
                            response['ChunkId'] = [PrevChunkId] + ChunkIds
                            response['Chunk'] = [PrevChunk] + Chunks
                            PrevCleanChunk = ""
                            PrevSwitch = 0
                            found = True  # 플래그 변수 설정
                            break  # 현재 루프 종료

        # ChunkId가 연속적이지 않은 경우를 처리하는 로직
        if isinstance(response['ChunkId'], list) and all(isinstance(x, int) for x in response['ChunkId']):
            NonConsecutive = True
            for i in range(1, len(response['ChunkId'])):
                if response['ChunkId'][i] - response['ChunkId'][i - 1] == 1:
                    NonConsecutive = False
                    break

            if NonConsecutive:
                # print(response['ChunkId'])
                fullChunkIdList = range(min(response['ChunkId']), max(response['ChunkId']) + 1)
                missingChunkIds = [id for id in fullChunkIdList if id not in response['ChunkId']]

                for missingId in missingChunkIds:
                    for body in BodyFrame:
                        for splitedChunk in body['SplitedBodyChunks']:
                            if splitedChunk['ChunkId'] == missingId:
                                response['ChunkId'].append(missingId)
                                response['Chunk'].append(splitedChunk['Chunk'])
                                break
                            
                # ChunkId에 따라 Chunk를 정렬
                chunkIdChunkPairs = sorted(zip(response['ChunkId'], response['Chunk']))
                response['ChunkId'], response['Chunk'] = map(list, zip(*chunkIdChunkPairs))
    
    # ChunkId의 순번대로 재배열
    ResponseJson = sorted(responseJson, key = lambda x: x['ChunkId'][0] if isinstance(x['ChunkId'], list) else x['ChunkId'])

    return ResponseJson

## 프롬프트 요청 및 결과물 Json을 ContextDefine에 업데이트
def ContextDefineUpdate(projectName, email, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 07_ContextDefineUpdate 시작 >")
    # SummaryBodyFrame의 Count값 가져오기
    ContinueCount, ContextCount, Completion = ContextDefineCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedContextDefineToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "ContextDefine", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 07_ContextDefineUpdate는 ExistedContextDefine으로 대처됨 ]\n")
        else:
            responseJson = ContextDefineResponseJson(projectName, email, messagesReview = MessagesReview, mode = Mode)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            ContextChunkId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'ContextDefineUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'ContextDefineUpdate: {Update}')
                time.sleep(0.0001)
                ContextChunkId += 1
                ChunkId = ResponseJson[i]["ChunkId"]
                Chunk = ResponseJson[i]["Chunk"]
                Reader = ResponseJson[i]["Reader"]
                Purpose = ResponseJson[i]["Purpose"]
                Subject = ResponseJson[i]["Subject"]
                Phrases = ResponseJson[i]["Phrases"]
                Importance = ResponseJson[i]["Importance"]
                
                AddContextDefineChunksToDB(projectName, email, ContextChunkId, ChunkId, Chunk, Reader, Purpose, Subject, Phrases, Importance)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            ContextDefineCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 07_ContextDefineUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 07_ContextDefineUpdate는 이미 완료됨 ]\n")
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################