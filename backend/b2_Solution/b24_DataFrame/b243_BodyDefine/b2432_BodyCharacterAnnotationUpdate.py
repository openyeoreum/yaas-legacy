import re
import json
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b23_Project.b231_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import AddExistedBodyCharacterAnnotationToDB, AddBodyCharacterAnnotationChunksToDB, AddBodyCharacterAnnotationCheckedCharacterTagsToDB, BodyCharacterAnnotationCountLoad, BodyCharacterAnnotationCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

## BodyFrameBodys 로드
def LoadBodyFrameBodys(projectName, email):
    project = GetProject(projectName, email)
    BodyFrameBodys = project.BodyFrame[2]['Bodys'][1:]
    
    return BodyFrameBodys

## BodyCharacterDefine 로드
def LoadBodyCharacterDefine(projectName, email):
    project = GetProject(projectName, email)
    CharacterChunks = project.BodyCharacterDefine[1]['CharacterChunks'][1:]
    CharacterTags = project.BodyCharacterDefine[2]['CharacterTags'][1:]
    
    return CharacterChunks, CharacterTags

## TaskBody를 [말n] 이름 : 내용 형식으로 변환
def ReplaceName(TaskBody, CharacterChunks):
    pattern = re.compile(r'\[말(\d+)\]')
    matches = pattern.finditer(TaskBody)
    for match in reversed(list(matches)):
        n = int(match.group(1))
        for chunk in CharacterChunks:
            if chunk['CharacterChunkId'] == n:
                CharName = chunk['Character']
                replacement = f"[말{n}] {CharName} : "
                TaskBody = TaskBody[:match.start()] + replacement + TaskBody[match.end():]
                break

    return TaskBody

## BodyFrameBodys의 InputList 치환
def BodyFrameBodysToInputList(projectName, email, Task = "Character"):
    BodyFrameBodys = LoadBodyFrameBodys(projectName, email)
    CharacterChunks, CharacterTags = LoadBodyCharacterDefine(projectName, email)
    
    InputList = []
    for BodyDic in BodyFrameBodys:
        Id = BodyDic["BodyId"]
        if Task in BodyDic["Task"]:
            Tag = "Continue"
        else:
            Tag = "Pass"
        TaskBody = ReplaceName(BodyDic[Task], CharacterChunks)
        InputDic = {'Id': Id, Tag: TaskBody}
        InputList.append(InputDic)
    
    return InputList

## BodyCharacterAnnotation의 Filter(Error 예외처리)
def CharNameBodyCharacterAnnotationFilter(TalkTag, responseData, memoryCounter):
    # responseData의 전처리
    responseData = responseData.replace("<태그.json>" + memoryCounter, "").replace("<태그.json>" + memoryCounter + " ", "")
    responseData = responseData.replace("<태그.json>", "").replace("<태그.json> ", "")
    responseData = responseData.replace("\n", "").replace("'", "\"")
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
    # Error3: 결과가 '말하는인물'이 '없음'일 때의 예외 처리 (없음일 경우에는 Narrator 낭독)
    for dic in OutputDic:
        for key, value in dic.items():
            if value['말하는인물'] == '없음' or value['말하는인물'] == '' or value['말하는인물'] == 'none':
                return "'말하는인물': '없음' 오류 발생: NonValueError"
    # Error4: 자료의 구조가 다를 때의 예외 처리
    for dic in OutputDic:
        try:
            key = list(dic.keys())[0]
            if not key in TalkTag:
                return "JSON에서 오류 발생: JSONKeyError"
            else:
                if not ('말하는인물' in dic[key] and '정답' in dic[key] and '수정된인물' in dic[key] and '증거문장' in dic[key]):
                    return "JSON에서 오류 발생: JSONKeyError"
        # Error5: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
    # Error6: Input과 Output의 개수가 다를 때의 예외처리
    if len(OutputDic) != len(TalkTag):
        return "JSONCount에서 오류 발생: JSONCountError"
    return OutputDic

## inputMemory 형성
def BodyCharacterAnnotationInputMemory(inputMemoryDics, MemoryLength):
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
def BodyCharacterAnnotationOutputMemory(outputMemoryDics, MemoryLength):
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

## BodyCharacterAnnotation 프롬프트 요청 및 결과물 Json화
def BodyCharacterAnnotationProcess(projectName, email, Process = "BodyCharacterAnnotation", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    InputList = BodyFrameBodysToInputList(projectName, email)
    FineTuningMemoryList = BodyFrameBodysToInputList(projectName, email, Task = "Body")
    TotalCount = 0
    ContinueCount = 0
    inputMemoryDics = []
    InputDic = InputList[0]
    inputMemoryDics.append(InputDic)
    outputMemoryDics = []
        
    # BodyCharacterAnnotationProcess
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
                FineTuningMemory = FineTuningMemoryList[TotalCount - 1] if TotalCount > 0 else ""
            else:
                mode = "MemoryFineTuning"
        # Example 계열 모드의 순서
        elif Mode == "ExampleFineTuning":
            mode = "ExampleFineTuning"
            # "ExampleFineTuning"의 fineTuningMemory 형성
            FineTuningMemory = FineTuningMemoryList[TotalCount - 1] if TotalCount > 0 else ""
        elif Mode == "Example":
            mode = "Example"

        if "Continue" in InputDic:
            if Mode == "ExampleFineTuning":
                Keys = list(FineTuningMemory.keys())
                Input = FineTuningMemory[Keys[1]] + InputDic['Continue']
            else:
                Input = InputDic['Continue']
            
            # Filter, MemoryCounter, OutputEnder 처리
            talkTag = re.findall(r'\[말(\d{1,5})\]', str(InputDic))
            TalkTag = ["말" + match for match in talkTag]
            memoryCounter = " - 이어서 작업할 추가데이터: " + ', '.join(['[' + tag + ']' for tag in TalkTag]) + ' -\n'
            outputEnder = f"{{'{TalkTag[0]}': {{'말의종류': '"

            # Response 생성
            Response, Usage, Model = LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)
            
            # OutputStarter, OutputEnder에 따른 Response 전처리
            promptFrame = GetPromptFrame(Process)
            if mode in ["Example", "ExampleFineTuning"]:
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

            Filter = CharNameBodyCharacterAnnotationFilter(TalkTag, responseData, memoryCounter)
            
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
                if mode in ["Example", "ExampleFineTuning"]:
                    # mode가 ["Example", "ExampleFineTuning"]중 하나인 경우 Memory 초기화
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
            inputMemory = BodyCharacterAnnotationInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = BodyCharacterAnnotationOutputMemory(outputMemoryDics, MemoryLength)

    return outputMemoryDics

## 데이터 치환
def BodyCharacterAnnotationResponseJson(projectName, email, messagesReview = 'off', mode = "Memory"):
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
    outputMemoryDics = BodyCharacterAnnotationProcess(projectName, email, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    responseCount = 0
    
    for response in outputMemoryDics:
        if response != "Pass":
            for dic in response:
                ChunkId = CharacterTagChunkId[responseCount]
                Chunk = CharacterTagChunk[responseCount]
                for key, value in dic.items():
                    Annotation = value['증거문장']
                    Character = value['수정된인물']
                    Answer = value['정답']
                responseCount += 1
                responseJson.append({"ChunkId": ChunkId, "Chunk": Chunk, "Annotation": Annotation, "Character": Character, "Answer": Answer})
    
    return responseJson

## 프롬프트 요청 및 결과물 Json을 BodyCharacterAnnotation에 업데이트
def BodyCharacterAnnotationUpdate(projectName, email, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 05_BodyCharacterAnnotationUpdate 시작 >")
    # SummaryBodyFrame의 Count값 가져오기
    ContinueCount, CharacterCount, Completion = BodyCharacterAnnotationCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedBodyCharacterAnnotationToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "BodyCharacterAnnotation", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 05_BodyCharacterAnnotationUpdate는 ExistedBodyCharacterAnnotation으로 대처됨 ]\n")
        else:
            responseJson = BodyCharacterAnnotationResponseJson(projectName, email, messagesReview = MessagesReview, mode = Mode)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            CharacterChunkId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'BodyCharacterAnnotationUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'BodyCharacterAnnotationUpdate: {Update}')
                time.sleep(0.0001)
                CharacterChunkId += 1
                ChunkId = ResponseJson[i]["ChunkId"]
                Chunk = ResponseJson[i]["Chunk"]
                Annotation = ResponseJson[i]["Annotation"]
                Character = ResponseJson[i]["Character"]
                Answer = ResponseJson[i]["Answer"]
                
                AddBodyCharacterAnnotationChunksToDB(projectName, email, CharacterChunkId, ChunkId, Chunk, Annotation, Character, Answer)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            BodyCharacterAnnotationCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 05_BodyCharacterAnnotationUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 05_BodyCharacterAnnotationUpdate는 이미 완료됨 ]\n")
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    mode = "Example"
    #########################################################################
    
    BodyCharacterAnnotationUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode)