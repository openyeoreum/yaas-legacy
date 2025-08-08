import os
import re
import unicodedata
import json
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from nltk.metrics.distance import edit_distance
from agent.a2_Solution.a21_General.a214_GetProcessData import GetProject, SaveProject, GetPromptFrame
from agent.a2_Solution.a25_DataFrame.a251_DataCommit.a2511_LoadLLM import OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from agent.a2_Solution.a25_DataFrame.a251_DataCommit.a2513_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedContextDefineToDB, AddContextDefineChunksToDB, ContextDefineCountLoad, UpdatedContextDefine, ContextDefineCompletionUpdate
from agent.a2_Solution.a25_DataFrame.a251_DataCommit.a2514_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
## BodyFrameBodys 로드
def LoadBodyFrameBodys(projectName, email):
    project = GetProject(projectName, email)
    BodyFrameSplitedBodyScripts = project["BodyFrame"][1]['SplitedBodyScripts'][1:]
    BodyFrameBodys = project["BodyFrame"][2]['Bodys'][1:]
    
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
            
        InputDic = {'Id': Id, Tag: TaskBody}
        inputList.append(InputDic)
        
    InputList = MergeInputList(inputList)
        
    return InputList

######################
##### Filter 조건 #####
######################
## 거리측정을 통해 핵심문구에서 문자 1개만 틀린 경우도 허용하기
def IsSimilar(inputText, outputText, threshold = 1):
    # 두 문자열 간의 편집 거리 계산
    distance = edit_distance(inputText, outputText)
    # 편집 거리가 threshold 이하인지 판단
    return distance <= threshold

## ContextDefine의 Filter(Error 예외처리)
def ContextDefineFilter(Input, responseData, memoryCounter):
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
    # InputList(문장단위로 나누어서 Clean 처리)
    InputList = str(Input).split(". ")
    CleanInputList = []
    for _input in InputList:
        input = re.sub("[^가-힣]", "", str(_input))
        CleanInputList.append(input)
    # Input(전체를 통으로 Clean 처리)
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
                TrueSwitch = 0
                for CleanInput in CleanInputList:
                    if IsSimilar(CleanInput, OUTPUT, threshold = 1):
                        TrueSwitch += 1
                if TrueSwitch == 0:
                    return f"JSON에서 오류 발생: JSON '핵심문구'가 Input에 포함되지 않음\n문구: {dic[key]['핵심문구']}"
            elif not ('목적' in dic[key] and '원인' in dic[key] and '핵심문구' in dic[key] and '예상질문' in dic[key] and '매칭독자' in dic[key] and '주제' in dic[key] and '중요도' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
            
            # 중요도 값이 숫자 또는 문자열 숫자인지 검사
            importance_value = dic[key]['중요도']
            if not (isinstance(importance_value, (int, float)) or 
                    (isinstance(importance_value, str) and importance_value.isdigit())):
                return "JSON에서 오류 발생: 중요도 값이 숫자가 아님"
            
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        
    return {'json': outputJson, 'filter': OutputDic}

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
def ContextDefineProcess(projectName, email, DataFramePath, Process = "ContextDefine", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '07', DataFramePath)
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
            Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)

            # OutputStarter, OutputEnder에 따른 Response 전처리
            promptFrame = GetPromptFrame(Process)
            if mode in ["Example", "ExampleFineTuning", "Master"]:
                Example = promptFrame["Example"]
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
            inputMemory = ContextDefineInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = ContextDefineOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '07', DataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
## ContextDefine의 Bodys전환
def ContextDefineToBodys(projectName, email, ResponseJson):
    project = GetProject(projectName, email)
    bodyFrame = project["BodyFrame"]
    Bodys = bodyFrame[2]["Bodys"][1:]

    responseCount = 0  # 마지막으로 처리된 ResponseJson의 인덱스를 추적
    for body in Bodys:
        ContextBody = body['Body']
        memoAdded = False  # {메모} 태그가 추가되었는지 추적하는 플래그
        for i in range(responseCount, len(ResponseJson)):
            response = ResponseJson[i]
            Chunk = response['Chunk']
            if isinstance(response['ChunkId'], list):
                if all(elem in body['ChunkId'] for elem in response['ChunkId']):
                    memoAdded = True
                    PhrasesTag = f"\n\n[핵심문구{i+1}] "
                    MemoTag = f"\n{{메모{i+1}}}\n\n"
                    newStartChunk = PhrasesTag + Chunk[0]
                    newEndChunk = Chunk[-1] + MemoTag
                    ContextBody = ContextBody.replace(Chunk[0], newStartChunk, 1)
                    ContextBody = ContextBody.replace(Chunk[-1], newEndChunk, 1)
                    responseCount = i + 1
            else:
                if response['ChunkId'] in body['ChunkId']:
                    memoAdded = True
                    PhrasesTag = f"\n\n[핵심문구{i+1}] "
                    MemoTag = f"\n{{메모{i+1}}}\n\n"
                    newChunk = PhrasesTag + Chunk + MemoTag
                                    
                    ContextBody = ContextBody.replace(Chunk, newChunk, 1)
                    responseCount = i + 1
        
        if memoAdded:
            if 'Context' not in body['Task']:
                body['Task'].append('Context')
        body['Context'] = ContextBody
        
    SaveProject(projectName, email, project)

## 데이터 치환
def ContextDefineResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):
    # Chunk, ChunkId 데이터 추출
    project = GetProject(projectName, email)
    BodyFrame = project["BodyFrame"][1]['SplitedBodyScripts'][1:]
    
    # 데이터 치환
    outputMemoryDics = ContextDefineProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    for response in outputMemoryDics:
        if response != "Pass":
            for dic in response:
                for key, value in dic.items():
                    CleanPhrases = re.sub("[^가-힣]", "", str(value['핵심문구']))
                    # CleanPhrases가 비어 있으면 다음 항목으로 이동
                    if not CleanPhrases:
                        continue
                    found = False  # 플래그 설정
                    ChunkId = None  # 기본값 설정
                    Chunk = None  # 기본값 설정
                    for i in range(len(BodyFrame)):
                        if found:
                            break
                        for j in range(len(BodyFrame[i]['SplitedBodyChunks'])):
                            CleanChunk = re.sub("[^가-힣]", "", str(BodyFrame[i]['SplitedBodyChunks'][j]['Chunk']))
                            if CleanPhrases in CleanChunk:
                                ChunkId = BodyFrame[i]['SplitedBodyChunks'][j]['ChunkId']
                                Chunk = BodyFrame[i]['SplitedBodyChunks'][j]['Chunk']
                                found = True
                                break
                    Phrases = value['핵심문구']
                    Reader = value['매칭독자']
                    Subject = value['주제']
                    Purpose = value['목적']
                    Reason = value['원인']
                    Question = value['예상질문']
                    Importance = value['중요도']
                responseJson.append({"ChunkId": ChunkId, "Chunk": Chunk, "Phrases": Phrases, "Reader": Reader, "Subject": Subject, "Purpose": Purpose, "Reason": Reason, "Question": Question, "Importance": Importance})

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
    
    # ChunkId의 None 부분 제거 및 순번대로 재배열
    responseJson = [item for item in responseJson if item['ChunkId'] is not None]
    ResponseJson = sorted(responseJson, key = lambda x: x['ChunkId'][0] if isinstance(x['ChunkId'], list) else x['ChunkId'])
        
    # 동일한 Chunk 또는 겹치는 Chunk를 지닌 자료를 합침
    newResponseJson = []

    # 첫 번째 요소를 newResponseJson에 추가
    if len(ResponseJson) > 0:
        newResponseJson.append(ResponseJson[0])

    for i in range(1, len(ResponseJson)):
        current = ResponseJson[i]
        previous = newResponseJson[-1]

        # ChunkId가 겹치는지 확인
        overlap = False
        if isinstance(previous['ChunkId'], list):
            if isinstance(current['ChunkId'], list):
                overlap = any(cid in previous['ChunkId'] for cid in current['ChunkId'])
            else:
                overlap = current['ChunkId'] in previous['ChunkId']
        else:
            if isinstance(current['ChunkId'], list):
                overlap = previous['ChunkId'] in current['ChunkId']
            else:
                overlap = current['ChunkId'] == previous['ChunkId']

        # 겹치는 경우, Importance와 ChunkId 길이를 기준으로 선택
        if overlap:
            if int(current['Importance']) > int(previous['Importance']):
                newResponseJson[-1] = current
            elif int(current['Importance']) == int(previous['Importance']):
                if len(str(current['ChunkId'])) > len(str(previous['ChunkId'])):
                    newResponseJson[-1] = current
        else:
            newResponseJson.append(current)
    
    # ContextDefine을 BodyFrameBodys의 Context 업데이트
    ContextDefineToBodys(projectName, email, newResponseJson)

    return newResponseJson

## 프롬프트 요청 및 결과물 Json을 ContextDefine에 업데이트
def ContextDefineUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 07_ContextDefineUpdate 시작 >")
    # ContextDefine의 Count값 가져오기
    ContinueCount, ContextCount, Completion = ContextDefineCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            # AddExistedContextDefineToDB(projectName, email, ExistedDataFrame)
            # AddExistedDataSetToDB(projectName, email, "ContextDefine", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 07_ContextDefineUpdate는 ExistedContextDefine으로 대처됨 ]\n")
        else:
            responseJson = ContextDefineResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
            
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
            DataFrame = UpdatedContextDefine(projectName, email)
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'ContextDefineUpdate: {Update}')
                time.sleep(0.0001)
                ContextChunkId += 1
                ChunkId = Update["ChunkId"]
                Chunk = Update["Chunk"]
                Phrases = Update["Phrases"]
                Reader = Update["Reader"]
                Subject = Update["Subject"]
                Purpose = Update["Purpose"]
                Reason = Update["Reason"]
                Question = Update["Question"]
                Importance = Update["Importance"]
                
                DataFrame = AddContextDefineChunksToDB(DataFrame, ContextChunkId, ChunkId, Chunk, Phrases, Reader, Subject, Purpose, Reason, Question, Importance)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            ContextDefineCompletionUpdate(projectName, email, DataFrame)
            print(f"[ User: {email} | Project: {projectName} | 07_ContextDefineUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 07_ContextDefineUpdate는 이미 완료됨 ]\n")
    
    
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################