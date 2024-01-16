import re
import json
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from collections import Counter
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import LoadOutputMemory, SaveOutputMemory, AddExistedCharacterCompletionToDB, AddCharacterCompletionChunksToDB, AddCharacterCompletionCheckedCharacterTagsToDB, CharacterCompletionCountLoad, CharacterCompletionCompletionUpdate
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

## CharacterDefine 로드
def LoadCharacterDefine(projectName, email):
    project = GetProject(projectName, email)
    CharacterChunks = project.CharacterDefine[1]['CharacterChunks'][1:]
    
    return CharacterChunks

## TaskBody를 [말n] 이름 : 내용 형식으로 변환
def ReplaceName(TaskBody, CharacterChunks):
    pattern = re.compile(r'\[말(\d+)\]')
    matches = pattern.finditer(TaskBody)
    for match in reversed(list(matches)):
        n = int(match.group(1))
        for chunk in CharacterChunks:
            if chunk['CharacterChunkId'] == n:
                CharName = chunk['Character']
                replacement = f"[말{n}] {CharName}: "
                TaskBody = TaskBody[:match.start()] + replacement + TaskBody[match.end():]
                break

    return TaskBody

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
    CharacterChunks = LoadCharacterDefine(projectName, email)
    
    inputList = []
    for i in range(len(BodyFrameBodys)):
        Id = BodyFrameBodys[i]['BodyId']
        task = BodyFrameBodys[i]['Task']
        TaskBody = ReplaceName(BodyFrameBodys[i][Task], CharacterChunks)

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
## 12-1. CharacterCompletion의 Filter(Error 예외처리)
def CharacterCompletionFilter(TalkTag, responseData, memoryCounter):
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
                if not ('말하는인물' in dic[key] and '대표명칭' in dic[key] and '저자와동일인물여부' in dic[key]):
                    return "JSON에서 오류 발생: JSONKeyError"
        # Error5: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
    # Error6: Input과 Output의 개수가 다를 때의 예외처리
    if len(OutputDic) != len(TalkTag):
        return "JSONCount에서 오류 발생: JSONCountError"

    return {'json': outputJson, 'filter': OutputDic}

## 12-2. CharacterPostCompletion의 Filter(Error 예외처리)
## MisMatchCharacters(요청 결과에 오류부분 검출)
def MisMatchCharacters(inputIdList, outputIdList):
    # Finding matches, mismatches, and duplicates
    Match = list(set(inputIdList) & set(outputIdList))
    MisMatch = list(set(inputIdList) - set(outputIdList))

    # Finding duplicates in outputIdList
    Duplicate = [item for item in outputIdList if outputIdList.count(item) > 1]
    Duplicate = list(set(Duplicate))  # Remove duplicates within the duplicate list

    # Calculating the number of elements in MisMatch and Duplicate
    num_mismatch = len(MisMatch)
    num_duplicate = len(Duplicate)

    # Total number of elements in inputIdList
    total_elements_input = len(inputIdList)

    # Calculating the miss ratio
    miss_ratio = (num_mismatch + num_duplicate) / total_elements_input

    # Creating the result dictionary
    MisMatchCharactersDic = {'Match': Match, 'MisMatch': MisMatch, 'Duplicate': Duplicate, 'MissRatio': miss_ratio}

    return MisMatchCharactersDic

## 성우 데이터에서 중복된 인물 제거
def RemoveDuplicates(OutputDic, Duplicate):
    # Creating a dictionary to hold the highest accuracy for each duplicate character
    highest_accuracy = {char: 0 for char in Duplicate}
    
    # Iterating over the data to find the highest accuracy for each duplicate character
    for entry in OutputDic:
        voice_actor = list(entry.keys())[0]
        accuracy = int(entry[voice_actor]['정확도'])
        characters = entry[voice_actor]['담당인물번호']

        for char in characters:
            if char in Duplicate:
                if accuracy > highest_accuracy[char]:
                    highest_accuracy[char] = accuracy

    # Creating a list to hold all the character IDs
    OutputDicIdList = []

    # Removing duplicates based on the highest accuracy and populating OutputDicIdList
    for entry in OutputDic:
        voice_actor = list(entry.keys())[0]
        characters = entry[voice_actor]['담당인물번호']

        # Filtering characters based on the highest accuracy
        filtered_characters = [char for char in characters if char not in Duplicate or (char in Duplicate and int(entry[voice_actor]['정확도']) == highest_accuracy[char])]
        entry[voice_actor]['담당인물번호'] = filtered_characters

        # Adding characters to the OutputDicIdList
        OutputDicIdList.extend(filtered_characters)

    # Removing duplicates in OutputDicIdList
    OutputDicIdList = list(set(OutputDicIdList))

    return OutputDic, sorted(OutputDicIdList)

## CharacterPostCompletion의 Filter(Error 예외처리)
def CharacterPostCompletionFilter(inputIdList, responseData, memoryCounter):
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
    outputIdList = []
    for dic in OutputDic:
        try:
            key = list(dic.keys())[0]
            if not ('성별' in dic[key] and '연령' in dic[key] and '담당인물번호' in dic[key] and '정확도' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
            outputIdList += dic[key]['담당인물번호']
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except:
            return "JSON에서 오류 발생: JSONError"
    # Error5: outputIdList와 inputIdList의 불일치가 클 때의 오류
    MisMatchCharactersDic = MisMatchCharacters(inputIdList, outputIdList)
    Duplicate = MisMatchCharactersDic['Duplicate']
    if MisMatchCharactersDic['MissRatio'] >= 0.05:
        return f"INPUT, OUTPUT [n] 갯수 불일치 오류 발생: MissRatio({MisMatchCharactersDic['MissRatio']}), MisMatchOUTPUT({MisMatchCharactersDic['MisMatch']})"
    else:
        OutputDic[0]['메인성우']['담당인물번호'] += MisMatchCharactersDic['MisMatch']
        OutputDic, OutputDicIdList = RemoveDuplicates(OutputDic, Duplicate)
    # Error6: 변형된 outputIdList와 inputIdList의 불일치 할때
    if inputIdList != OutputDicIdList:
        return f"INPUT, OUTPUT 불일치 오류 발생: InputIdList({inputIdList}), OutputDicIdList({OutputDicIdList})"

    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def CharacterCompletionInputMemory(inputMemoryDics, MemoryLength):
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
def CharacterCompletionOutputMemory(outputMemoryDics, MemoryLength):
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
## 12-1. CharacterCompletion 프롬프트 요청 및 결과물 Json화
def CharacterCompletionProcess(projectName, email, DataFramePath, Process = "CharacterCompletion", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '12-1', DataFramePath)    
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
        
    # CharacterCompletionProcess
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
            MasterMemory = InputList[TotalCount - 1] if TotalCount > 0 else {'Id': 0, 'Pass': ''}
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
                talkTag = re.findall(r'\[말(\d{1,5})\]', str(Input))
            else:
                talkTag = re.findall(r'\[말(\d{1,5})\]', str(InputDic))
            
            TalkTag = ["말" + match for match in talkTag]
            memoryCounter = " - 이어서 작업할 데이터: " + ', '.join(['[' + tag + ']' for tag in TalkTag]) + ' -\n'
            outputEnder = ""

            # Response 생성
            Response, Usage, Model = LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)
            # print(f"@@@@@@@@@@\n\nResponse: {Response}\n\n@@@@@@@@@@")
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
            
            Filter = CharacterCompletionFilter(TalkTag, responseData, memoryCounter)
            
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
            inputMemory = CharacterCompletionInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = CharacterCompletionOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '12-1', DataFramePath)
    
    return outputMemoryDics

## 12-2. CharacterPostCompletion 프롬프트 요청 및 결과물 Json화
def CharacterPostCompletionProcess(projectName, email, DataFramePath, inputList, inputIdList, Process = "CharacterPostCompletion", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '12-2', DataFramePath)
    InputList = inputList[OutputMemoryCount:]
    if InputList == []:
        return OutputMemoryDicsFile

    # FineTuningMemoryList = BodyFrameBodysToInputList(projectName, email, Task = "Body")
    TotalCount = 0
    ProcessCount = 1
    ContinueCount = 0
    inputMemoryDics = []
    inputMemory = []
    InputDic = InputList[0]
    inputMemoryDics.append(InputDic)
    outputMemoryDics = OutputMemoryDicsFile
    outputMemory = []
        
    # CharacterPostCompletionProcess
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
            memoryCounter = " - 주의사항1: <인물리스트>에서 등장횟수가 큰 인물[특히 앞부분 인물들이 등장횟수가 큼]들은 절대 묶지 않으며, 인물 1인당 1명의 개별성우로 선정. 주의사항2: <인물리스트>의 인물은 절대 1명도 빠트리지 않으며, 동일인물번호를 중복하여 작성하지 않음. -\n"
            outputEnder = ""

            # Response 생성
            Response, Usage, Model = LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)
            # print(f"@@@@@@@@@@\n\nResponse: {Response}\n\n@@@@@@@@@@")
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
            
            Filter = CharacterPostCompletionFilter(inputIdList, responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(InputList)} | {Filter}")
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(InputList)} | JSONDecode 완료")
                
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
            inputMemory = CharacterCompletionInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = CharacterCompletionOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '12-2', DataFramePath)
    
    return outputMemoryDics
################################
##### 데이터 치환 및 DB 업데이트 #####
################################
## outputMemoryDics 후처리
def MergeOutputMemoryDics(outputMemoryDics):
    MergedOutput = []
    SeenSpeeches = {}

    for sublist in outputMemoryDics:
        if sublist == 'Pass':
            MergedOutput.append('Pass')
            continue

        NewSublist = []
        for item in sublist:
            for SpeechId, speechInfo in item.items():
                if SpeechId in SeenSpeeches:
                    ExistingInfo = SeenSpeeches[SpeechId]
                    for key in speechInfo:
                        if speechInfo[key] != ExistingInfo[key]:
                            if not isinstance(ExistingInfo[key], list):
                                ExistingInfo[key] = [ExistingInfo[key]]
                            if speechInfo[key] not in ExistingInfo[key]:
                                ExistingInfo[key].append(speechInfo[key])
                else:
                    SeenSpeeches[SpeechId] = speechInfo
                    NewSublist.append({SpeechId: speechInfo})
        
        if NewSublist:
            MergedOutput.append(NewSublist)

    return MergedOutput

## 캐릭터 선별하기(필터)
def MainCharacterFilter(responseJson):
    # 캐릭터 선별1 [이름1, 이름2] 서로의 이름이 포함된 경우 긴 이름만 남김
    for i in range(len(responseJson)):
        MainCharacter = responseJson[i]['MainCharacter']
        if isinstance(MainCharacter, list):
            if MainCharacter[0] in MainCharacter[1]:
                responseJson[i]['MainCharacter'] = MainCharacter[1]
            elif MainCharacter[1] in MainCharacter[0]:
                responseJson[i]['MainCharacter'] = MainCharacter[0]
            else:
                responseJson[i]['MainCharacter'] = MainCharacter
        else:
            responseJson[i]['MainCharacter'] = MainCharacter
    
    # 캐릭터 선별2 [이름1, 이름2]이 존재할 경우 외부에 존재하는 이름으로 남기고, 둘다 존재할 경우 가까운 이름으로 남김
    for i in range(len(responseJson)):
        MainCharacter = responseJson[i]['MainCharacter']
        if isinstance(MainCharacter, list):
            Name1, Name2 = MainCharacter
            distance1, distance2 = float('inf'), float('inf')

            for j in range(len(responseJson)):
                if Name1 == responseJson[j]['MainCharacter']:
                    distance1 = min(distance1, abs(j - i))
                if Name2 == responseJson[j]['MainCharacter']:
                    distance2 = min(distance2, abs(j - i))

            if distance1 < distance2:
                responseJson[i]['MainCharacter'] = Name1
            else:
                responseJson[i]['MainCharacter'] = Name2
                
    # 캐릭터 선별3 여전히 리스트가 남아 있는 경우 뒷 이름(더 많은 데이터로 선별된)을 최종 대표명칭으로 설정
    for i in range(len(responseJson)):
        MainCharacter = responseJson[i]['MainCharacter']
        if isinstance(MainCharacter, list):
            responseJson[i]['MainCharacter'] = MainCharacter[1]
            
    # 캐릭터 선별4 자료내에 동일한 이름이 있을 경우 긴이름으로 대처
    for i in range(len(responseJson)):
        currentName = responseJson[i]['MainCharacter']
        for j in range(len(responseJson)):
            comparedName = responseJson[j]['MainCharacter']

            # 현재 이름이 비교되는 이름을 포함하고 있으며, 더 길면 현재 이름을 유지
            if currentName in comparedName and len(currentName) < len(comparedName):
                responseJson[i]['MainCharacter'] = comparedName

            # 비교되는 이름이 현재 이름을 포함하고 있으며, 더 길면 비교되는 이름으로 변경
            elif comparedName in currentName and len(comparedName) < len(currentName):
                responseJson[j]['MainCharacter'] = currentName

    # 캐릭터 선별5 실제 등장인물의 리스트
    characterCounts = Counter(dic['MainCharacter'] for dic in responseJson)
    sortedCharacters = sorted(characterCounts, key=characterCounts.get, reverse=True)
    
    return responseJson, sortedCharacters

## 단어리스트 %로 표현
def WordFrequency(words):
    wordFrequency = {}
    for word in words:
        wordFrequency[word] = wordFrequency.get(word, 0) + 1
    # Calculating total number of words
    TotalWords = len(words)
    # Converting frequency to percentage and rounding to 2 decimal places
    WordPercentage = {word: round((count / TotalWords) * 100, 2) for word, count in wordFrequency.items()}
    
    # Sorting the dictionary by frequency in descending order and converting back to dictionary
    SortedWordPercentage = dict(sorted(WordPercentage.items(), key=lambda x: x[1], reverse=True))
    
    return SortedWordPercentage

## 평균 나이 계산기
def AgeAverageCalculator(SelectedAge):
    AgeList = ['유년', '청소년', '청년', '중년', '장년', '노년']
    AgeCount = 0
    for Age in AgeList:
        if Age in SelectedAge:
            AgeCount += 1
            
    if AgeCount == 0:
        return next(iter(SelectedAge))
    
    else:
        SelectedAge = {key: value for key, value in SelectedAge.items() if key in AgeList}
        # 각 나이대의 범위 정의
        AgeRanges = {AgeList[0]: (0, 10), AgeList[1]: (10, 20), AgeList[2]: (20, 35), AgeList[3]: (35, 50), AgeList[4]: (50, 65), AgeList[5]: (65, 80)}
        # 평균 나이 계산
        AverageAge = sum((AgeRanges[age][0] + AgeRanges[age][1]) / 2 * percentage for age, percentage in SelectedAge.items()) / 100
        # 평균 나이에 가장 가까운 나이대 찾기
        ClosestAgeCategory = min(AgeRanges.keys(), key=lambda x: abs((AgeRanges[x][0] + AgeRanges[x][1]) / 2 - AverageAge))

        return ClosestAgeCategory

## 캐릭터 더 선별하기
def CarefullySelectedCharacter(projectName, email, DataFramePath, messagesReview, mode, SelectedCharacters):
    SelectedCharactersTexts = []
    inputIdList = []
    for i, Selected in enumerate(SelectedCharacters):
        if '남' in Selected['Gender'] and '여' in Selected['Gender']:
            Gender = '남/여'
        else:
            Gender = next(iter(Selected['Gender']))
        Age = AgeAverageCalculator(Selected['Age'])
        
        SelectedCharactersText = f"인물{Selected['Id']} \"{Selected['MainCharacter']}\" (등장횟수: {Selected['Frequency']}번, 성별: {Gender}, 연령: {Age}, 역할의 비중(%): {Selected['Role']})\n\n"
        SelectedCharactersTexts.append(SelectedCharactersText)
        inputIdList.append(i+1)

    # CharacterPostCompletionProcess 실행
    TaskBody = ''.join(SelectedCharactersTexts)
    inputList = [{'Id': 1, 'Continue': TaskBody}]
        
    OutputMemoryDics = CharacterPostCompletionProcess(projectName, email, DataFramePath, inputList, inputIdList, MessagesReview = messagesReview, Mode = mode)
    
    outputMemoryDics = OutputMemoryDics[0]
    # outputMemoryDics 후처리
    MainActor = outputMemoryDics[0]['메인성우']
    for actor in outputMemoryDics[1:]:
        ActorData = list(actor.values())[0]
        if int(ActorData['정확도']) <= 75 and len(ActorData['담당인물번호']) <= 1:
            MainActor['담당인물번호'].extend(ActorData['담당인물번호'])
    # 삭제 조건에 맞는 일반성우 제거
    outputMemoryDics = [outputMemoryDics[0]] + [actor for actor in outputMemoryDics[1:] if len(list(actor.values())[0]['담당인물번호']) > 0 and int(list(actor.values())[0]['정확도']) >= 80]
    # 변환
    CharacterList = []
    for idx, actor in enumerate(outputMemoryDics, start=1):
        ActorData = list(actor.values())[0]
        CharacterName = 'Narrator' if idx == 1 else f'Character{idx-1}'
        CharacterList.append({'CharacterId': idx, 'CharacterTag': CharacterName, 'Gender': ActorData['성별'], 'Age': ActorData['연령'], 'Actors': sorted(ActorData['담당인물번호'])})
    
    # 삭제 조건에 맞는 일반성우 제거
    for Character in CharacterList:
        for i in range(len(SelectedCharacters)):
            if SelectedCharacters[i]['Id'] in Character['Actors']:
                SelectedCharacters[i]['Voice'] = {'CharacterId': Character['CharacterId'], 'CharacterTag': Character['CharacterTag'], 'Gender': Character['Gender'], 'Age': Character['Age']}
    
    return SelectedCharacters, CharacterList

## 캐릭터 나머지 요소 합치기
def SelectedCharacterFilter(projectName, email, DataFramePath, messagesReview, mode, ResponseJson, sortedCharacters):
    # Character 요소들 모두 합치기
    SelectedCharacters = []
    Id = 1
    for Character in sortedCharacters:
        Type = []
        Gender = []
        Age = []
        Emotion = []
        Role = []
        frequency = 0
        for Response in ResponseJson:
            MainCharacter = Response['MainCharacter']
            if Character == MainCharacter:
                frequency += 1
                if isinstance(Response['Type'], list):
                    Type += Response['Type']
                else:
                    Type.append(Response['Type'])
                if isinstance(Response['Gender'], list):
                    Gender += Response['Gender']
                else:
                    Gender.append(Response['Gender'])
                if isinstance(Response['Age'], list):
                    Age += Response['Age']
                else:
                    Age.append(Response['Age'])
                if isinstance(Response['Emotion'], list):
                    Emotion += Response['Emotion']
                else:
                    Emotion.append(Response['Emotion'])
                if isinstance(Response['Role'], list):
                    Role += Response['Role']
                else:
                    Role.append(Response['Role'])
                if isinstance(Response['AuthorRelationship'], list):
                    Role += Response['AuthorRelationship']
                else:
                    Role.append(Response['AuthorRelationship'])
                
        type = WordFrequency(Type)
        gender = WordFrequency(Gender)
        age = WordFrequency(Age)
        emotion = WordFrequency(Emotion)
        role = WordFrequency(Role)
        SelectedCharacter = {'Id': Id, 'MainCharacter': Character, 'Voice': None, 'Frequency': frequency, 'Type': type, 'Gender': gender, 'Age': age, 'Emotion': emotion, 'Role': role}
        SelectedCharacters.append(SelectedCharacter)
        Id += 1
    
    ## SelectedCharacters (캐릭터에 성우 적용)
    SelectedCharacters, CharacterList = CarefullySelectedCharacter(projectName, email, DataFramePath, messagesReview, mode, SelectedCharacters)

    # 성우별 담당 배역이름 리스트 업데이트
    ActorNames =[]
    Emotion = []
    for Character in CharacterList:
        for SelectedCharacter in SelectedCharacters:
            if SelectedCharacter['Id'] in Character['Actors']:
                ActorNames.append(SelectedCharacter['MainCharacter'])
                Emotions = list(SelectedCharacter['Emotion'].keys())
                Emotion.append(Emotions[0])
                
        Character['ActorNames'] = ActorNames
        ActorNames =[]
        
        EmotionCounts = Counter(Emotion)
        TotalEmotions = sum(EmotionCounts.values())
        # 백분율로 감정 비중 계산
        EmotionPercentage = {emotion: round((count / TotalEmotions) * 100, 2)
                            for emotion, count in EmotionCounts.items()}
        Character['Emotion'] = EmotionPercentage
        Emotion = []

    # 전체 Chunk별 성우 업데이트
    for Character in SelectedCharacters:
        for Response in ResponseJson:
            if Character['MainCharacter'] == Response['MainCharacter']:
                Response['Voice'] = Character['Voice']

    return ResponseJson, CharacterList

## 데이터 치환
def CharacterCompletionResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):
    # Chunk, ChunkId 데이터 추출
    project = GetProject(projectName, email)
    BodyFrame = project.BodyFrame[1]['SplitedBodyScripts'][1:]
    CharacterDefine = project.CharacterDefine[1]['CharacterChunks'][1:]
    
    CharacterTagChunk = []
    CharacterTagChunkId = []
    for i in range(len(BodyFrame)):
        for j in range(len(BodyFrame[i]['SplitedBodyChunks'])):
            if BodyFrame[i]['SplitedBodyChunks'][j]['Tag'] == "Character":
                CharacterTagChunk.append(BodyFrame[i]['SplitedBodyChunks'][j]['Chunk'])
                CharacterTagChunkId.append(BodyFrame[i]['SplitedBodyChunks'][j]['ChunkId'])
    
    # 데이터 치환
    OutputMemoryDics = CharacterCompletionProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)
        
    outputMemoryDics = MergeOutputMemoryDics(OutputMemoryDics)

    responseJson = []
    responseCount = 0
    CharacterCount = 0
    for response in outputMemoryDics:
        if response != "Pass":
            # if responseCount >= len(CharacterTagChunkId):
            #     print(f"Invalid index: {responseCount}. The list size is {len(CharacterTagChunkId)}.")
            #     break  # 또는 다른 적절한 처리
            for dic in response:
                ChunkId = CharacterTagChunkId[responseCount]
                Chunk = CharacterTagChunk[responseCount]
                for key, value in dic.items():
                    Character = value['말하는인물']
                    MainCharacter = value['대표명칭']
                    Type = CharacterDefine[CharacterCount]['Type']
                    Gender = CharacterDefine[CharacterCount]['Gender']
                    Age = CharacterDefine[CharacterCount]['Age']
                    Emotion = CharacterDefine[CharacterCount]['Emotion']
                    Role = CharacterDefine[CharacterCount]['Role']
                    AuthorRelationship = value['저자와동일인물여부']
                CharacterCount += 1
                responseCount += 1
                responseJson.append({"ChunkId": ChunkId, "Chunk": Chunk, "Character": Character, "MainCharacter": MainCharacter, "Type": Type, "Gender": Gender, "Age": Age, "Emotion": Emotion, "Role": Role, "AuthorRelationship": AuthorRelationship})

    ResponseJson, sortedCharacters = MainCharacterFilter(responseJson)
    ## 12-1. 도서에 대화문이 없는 경우 Pass ##
    if ResponseJson == []:
        return ResponseJson, sortedCharacters
    
    ## 12-2. 도서에 대화문이 있는 경우 SelectedCharacterFilter(프롬프트 포함) Continue ##
    else:
        SelectedResponseJson, CharacterList = SelectedCharacterFilter(projectName, email, DataFramePath, messagesReview, mode, ResponseJson, sortedCharacters)

        return SelectedResponseJson, CharacterList

## 프롬프트 요청 및 결과물 Json을 CharacterCompletion에 업데이트
def CharacterCompletionUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 12_CharacterCompletionUpdate 시작 >")
    # CharacterCompletion의 Count값 가져오기
    ContinueCount, CharacterCount, Completion = CharacterCompletionCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedCharacterCompletionToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "CharacterCompletion", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 12_CharacterCompletionUpdate는 ExistedCharacterCompletion으로 대처됨 ]\n")
        else:
            SelectedResponseJson, CharacterList = CharacterCompletionResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
            print(f"< Project: {projectName} | Process: CharacterCompletion | CharacterFilter 완료, {projectName}의 성우 {len(CharacterList)}명> ")
            
            ## 12-1. CharacterCompletion
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = SelectedResponseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            CharacterChunkId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'CharacterCompletionUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'CharacterCompletionUpdate: {Update["Character"]}')
                time.sleep(0.0001)
                CharacterChunkId += 1
                ChunkId = Update["ChunkId"]
                Chunk = Update["Chunk"]
                Character = Update["Character"]
                MainCharacter = Update["MainCharacter"]
                AuthorRelationship = Update["AuthorRelationship"]
                
                Type = Update["Type"]
                Gender = Update["Gender"]
                Age = Update["Age"]
                Emotion = Update["Emotion"]
                Role = Update["Role"]
                Context = {'Type': Type, 'Gender': Gender, 'Age': Age, 'Emotion': Emotion, 'Role': Role}
                Voice = Update["Voice"]
                
                AddCharacterCompletionChunksToDB(projectName, email, CharacterChunkId, ChunkId, Chunk, Character, MainCharacter, AuthorRelationship, Context, Voice)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            
            ## 12-2. CharacterPostCompletion
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = CharacterList[CharacterCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'CharacterPostCompletionUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'CharacterPostCompletionUpdate: {Update}')
                time.sleep(0.0001)
                CharacterTag = Update["CharacterTag"]
                Gender = Update["Gender"]
                Age = Update["Age"]
                Emotion = Update["Emotion"]
                MainCharacterList = Update["ActorNames"]
                
                AddCharacterCompletionCheckedCharacterTagsToDB(projectName, email, CharacterTag, Gender, Age, Emotion, MainCharacterList)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            CharacterCompletionCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 12_CharacterCompletionUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 12_CharacterCompletionUpdate는 이미 완료됨 ]\n")
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################