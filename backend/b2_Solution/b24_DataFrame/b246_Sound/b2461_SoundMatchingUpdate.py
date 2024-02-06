import os
import re
import json
import time
import difflib
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedSoundMatchingToDB, AddSoundSplitedIndexsToDB, SoundMatchingCountLoad, SoundMatchingCompletionUpdate
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

## BodyFrameBodys의 inputList 치환
def BodyFrameBodysToInputList(projectName, email, Task = "Correction"):
    BodyFrameSplitedBodyScripts, BodyFrameBodys = LoadBodyFrameBodys(projectName, email)

    InputList = []
    IndexId = 1
    CorrectionTexts = []
    for i in range(len(BodyFrameSplitedBodyScripts)):
        BodyFrameIndexId = BodyFrameSplitedBodyScripts[i]['IndexId']
        SplitedBodyChunks = BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks']
        if BodyFrameIndexId == IndexId:
            if len(SplitedBodyChunks) == 1:
                Tag = 'Pass'
                ChunkId = SplitedBodyChunks[0]['ChunkId']
                Chunk = SplitedBodyChunks[0]['Chunk']
                CorrectionTexts.append(f'[{ChunkId}]' + Chunk)
                CorrectionText = ' '.join(CorrectionTexts)
                InputDic = {'Id': IndexId, Tag: CorrectionText}
                InputList.append(InputDic)
                CorrectionTexts = []
            else:
                for j in range(len(SplitedBodyChunks)):
                    ChunkId = SplitedBodyChunks[j]['ChunkId']
                    Chunk = SplitedBodyChunks[j]['Chunk']
                    CorrectionTexts.append(f'[{ChunkId}]' + Chunk)
        else:
            if len(CorrectionTexts) != 0:
                if len(CorrectionTexts) == 1:
                    Tag = 'Pass'
                else:
                    Tag = 'Continue'
                CorrectionText = ' '.join(CorrectionTexts)
                InputDic = {'Id': IndexId, Tag: CorrectionText}
                InputList.append(InputDic)
                CorrectionTexts = []

            if len(SplitedBodyChunks) == 1:
                Tag = 'Pass'
                ChunkId = SplitedBodyChunks[0]['ChunkId']
                Chunk = SplitedBodyChunks[0]['Chunk']
                CorrectionTexts.append(f'[{ChunkId}]' + Chunk)
                CorrectionText = ' '.join(CorrectionTexts)
                InputDic = {'Id': IndexId, Tag: CorrectionText}
                InputList.append(InputDic)
                CorrectionTexts = []
            else:
                for j in range(len(SplitedBodyChunks)):
                    ChunkId = SplitedBodyChunks[j]['ChunkId']
                    Chunk = SplitedBodyChunks[j]['Chunk']
                    CorrectionTexts.append(f'[{ChunkId}]' + Chunk)
            IndexId += 1

    if CorrectionTexts != []:
        if len(CorrectionTexts) <= 1:
            Tag = 'Pass'
        else:
            Tag = 'Continue'
        CorrectionText = ' '.join(CorrectionTexts)
        InputDic = {'Id': IndexId, Tag: CorrectionText}
        InputList.append(InputDic)
        CorrectionTexts = []

    return InputList

######################
##### Filter 조건 #####
######################
## SoundMatching의 Filter(Error 예외처리)
def SoundMatchingFilter(responseData, memoryCounter):
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
            if not ('전환소리명칭' in dic[key] and '전환소리영어명칭' in dic[key] and '전환소리필요성' in dic[key] and '배경소리명칭' in dic[key] and '배경소리영어명칭' in dic[key] and '배경소리필요성' in dic[key] and '배경소리길이' in dic[key] and '유형' in dic[key] and '환경' in dic[key] and '상황' in dic[key] and '시대' in dic[key] and '문화' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        
    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def SoundMatchingInputMemory(inputMemoryDics, MemoryLength):
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
def SoundMatchingOutputMemory(outputMemoryDics, MemoryLength):
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
## SoundMatching 프롬프트 요청 및 결과물 Json화
def SoundMatchingProcess(projectName, email, DataFramePath, Process = "SoundMatching", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '14', DataFramePath)    
    inputList = BodyFrameBodysToInputList(projectName, email)
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
    ErrorCount = 0
        
    # SoundMatchingProcess
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
            memoryCounter = " - '배경소리'와 '전환소리'는 추상적으로 않고 구체적이고 물리적으로 작성 -\n"
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
         
            Filter = SoundMatchingFilter(responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                
                ErrorCount += 1
                if ErrorCount == 7:
                    print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | 오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
                    sys.exit(1)  # 오류 상태와 함께 프로그램을 종료합니다.
                    
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
            inputMemory = SoundMatchingInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = SoundMatchingOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '14', DataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
## 데이터 치환
def SoundMatchingResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory", TransitionImportance = 0, BackgroundImportance = 0):
    project = GetProject(projectName, email)
    BodyFrameSplitedBodyScripts = project.BodyFrame[1]['SplitedBodyScripts'][1:]
    # IndexChunkIds 구조 형성
    IndexId = 1
    IndexChunkIds = []
    ChunkIds = []
    for i in range(len(BodyFrameSplitedBodyScripts)):
        indexid = BodyFrameSplitedBodyScripts[i]['IndexId']
        if IndexId == indexid:
            for j in range(len(BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks'])):
                ChunkId = BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks'][j]['ChunkId']
                ChunkIds.append(ChunkId)
        else:
            IndexChunkIds.append({'IndexId': IndexId, 'IndexChunkId': ChunkIds, 'Sounds': []})
            ChunkIds = []
            IndexId += 1
            
            for j in range(len(BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks'])):
                ChunkId = BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks'][j]['ChunkId']
                ChunkIds.append(ChunkId)
            
    if ChunkIds != []:
        IndexChunkIds.append({'IndexId': IndexId, 'IndexChunkId': ChunkIds, 'Sounds': []})
    
    # 데이터 치환
    outputMemoryDics = SoundMatchingProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)

    # responseJson 형성
    responseJson = []
    for i in range(len(outputMemoryDics)):
        if outputMemoryDics[i] != 'Pass':
            for j in range(len(outputMemoryDics[i])):
                dic = outputMemoryDics[i][j]
                key = list(dic.keys())[0]
                transitionImportance = int(outputMemoryDics[i][j][key]['전환소리필요성'])
                backgroundImportance = int(outputMemoryDics[i][j][key]['배경소리필요성'])
                if transitionImportance >= TransitionImportance and backgroundImportance >= BackgroundImportance:
                    dic = outputMemoryDics[i][j][key]
                    SoundRange = dic['배경소리길이']
                    FormattedSoundRange = re.sub(r'\[|\]', '', SoundRange)
                    start, end = map(int, FormattedSoundRange.split('-'))
                    ChunkIds = list(range(start, end + 1))
                    TransitionSound = dic['전환소리명칭']
                    TransitionSoundPrompt = dic['전환소리영어명칭']
                    BackgroundSound = dic['배경소리명칭']
                    BackgroundSoundPrompt = dic['배경소리영어명칭']
                    Type = dic['유형']
                    Environment = dic['환경']
                    Situation = dic['상황']
                    Era = dic['시대']
                    Culture = dic['문화']
                    responseJson.append({'ChunkId': ChunkIds, 'TransitionSound': TransitionSound, 'TransitionSoundPrompt': TransitionSoundPrompt, 'TransitionSoundImportance': transitionImportance, 'BackgroundSound': BackgroundSound, 'BackgroundSoundPrompt': BackgroundSoundPrompt, 'BackgroundSoundImportance': backgroundImportance, 'Type': Type, 'Environment': Environment, 'Situation': Situation, 'Era': Era, 'Culture': Culture})
    
    # responseJson 구조변경
    ResponseCount = 0
    for i in range(len(IndexChunkIds)):
        IndexChunkId = IndexChunkIds[i]['IndexChunkId']
        for j in range(ResponseCount, len(responseJson)):
            SoundChunkId = responseJson[j]['ChunkId']
            if all(Ids in IndexChunkId for Ids in SoundChunkId):
                IndexChunkIds[i]['Sounds'].append(responseJson[j])
            else:
                ResponseCount = j
                break
    
    return IndexChunkIds

## 프롬프트 요청 및 결과물 Json을 SoundMatching에 업데이트
def SoundMatchingUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None, transitionImportance = 0, backgroundImportance = 0):
    print(f"< User: {email} | Project: {projectName} | 14_SoundMatchingUpdate 시작 >")
    # SoundMatching의 Count값 가져오기
    ContinueCount, Completion = SoundMatchingCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedSoundMatchingToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "SoundMatching", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 14_SoundMatchingUpdate는 ExistedSoundMatching으로 대처됨 ]\n")
        else:
            responseJson = SoundMatchingResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode, TransitionImportance = transitionImportance, BackgroundImportance = backgroundImportance)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            IndexId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'SoundMatchingUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f"SoundMatchingUpdate: {Update['IndexId']}")
                time.sleep(0.0001)
                IndexId = Update['IndexId']
                Sounds = Update['Sounds']
                AddSoundSplitedIndexsToDB(projectName, email, IndexId, Sounds)

                # i값 수동 업데이트
                i += 1

            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            SoundMatchingCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 14_SoundMatchingUpdate 완료 ]\n")

    else:
        print(f"[ User: {email} | Project: {projectName} | 14_SoundMatchingUpdate는 이미 완료됨 ]\n")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s11_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################