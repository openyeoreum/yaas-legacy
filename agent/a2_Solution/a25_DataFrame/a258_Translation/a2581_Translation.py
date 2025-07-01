import os
import re
import json
import time
import difflib
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from sqlalchemy.orm.attributes import flag_modified
from agent.a1_Connector.a12_Database import get_db
from agent.a2_Solution.a21_General.a212_GetDBtable import GetProject, GetPromptFrame
from agent.a2_Solution.a25_DataFrame.a251_DataCommit.a2511_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from agent.a2_Solution.a25_DataFrame.a251_DataCommit.a2512_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedSFXMatchingToDB, AddSFXSplitedBodysToDB, SFXMatchingCountLoad, SFXMatchingCompletionUpdate
from agent.a2_Solution.a25_DataFrame.a251_DataCommit.a2513_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
## LoadSFXSplitedBodys 로드
def LoadSFXBodys(projectName, email):
    project = GetProject(projectName, email)
    BodyFrameSplitedBodyScripts = project.HalfBodyFrame[1]['SplitedBodyScripts'][1:]
    SFXMatchingSFXSplitedBodys = project.SFXMatching[1]['SFXSplitedBodys'][1:]
    
    # SFXIndexs와 SFXBodys 치환
    SFXIndexs = []
    SFXBodys = []
    for i in range(len(BodyFrameSplitedBodyScripts)):
        SplitedBodyChunks = BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks']
        IndexId = BodyFrameSplitedBodyScripts[i]['IndexId']
        IndexTag = BodyFrameSplitedBodyScripts[i]['IndexTag']
        Index = BodyFrameSplitedBodyScripts[i]['Index']
        BodyId = BodyFrameSplitedBodyScripts[i]['BodyId']
        SFXSplitedBodys = []
        for j in range(len(SplitedBodyChunks)):
            ChunkId = SplitedBodyChunks[j]['ChunkId']
            Tag = SplitedBodyChunks[j]['Tag']
            Chunk = SplitedBodyChunks[j]['Chunk']
            for k in range(len(SFXMatchingSFXSplitedBodys)):
                SFXSplitedBodyChunks = SFXMatchingSFXSplitedBodys[k]['SFXSplitedBodyChunks']
                for l in range(len(SFXSplitedBodyChunks)):
                    if SFXSplitedBodyChunks[l]['ChunkId'] == SplitedBodyChunks[j]['ChunkId']:
                        if Tag not in ['Title', 'Logue', 'Part', 'Chapter', 'Index']:
                            Chunk = SFXSplitedBodyChunks[l]['SFX']['Range']
            SFXSplitedBodys.append({'IndexId': IndexId, 'IndexTag': IndexTag, 'Index': Index, 'BodyId': BodyId, 'ChunkId': ChunkId, 'Tag': Tag, 'Chunk': Chunk})
        if Tag in ['Title', 'Logue', 'Part', 'Chapter', 'Index']:
            SFXIndexs.append(SFXSplitedBodys)
        else:
            SFXBodys.append(SFXSplitedBodys)
    
    return SFXIndexs, SFXBodys

## 16-1. TranslationIndex (목차번역)의 inputList 치환
def TranslationIndexToInputList(projectName, email):
    SFXIndexs, SFXBodys = LoadSFXBodys(projectName, email)
    ## 16-1. TranslationIndex (목차번역)
    ## 1: IndexInputText 치환
    IndexText = ''
    IndexsCount = len(SFXIndexs)
    IndexTagList = []
    for i in range(IndexsCount):
        Indexs = SFXIndexs[i]
        IndexTag = Indexs[0]['Tag']
        IndexTagList.append(IndexTag)
        
        Enter = ''
        Index = ''
        for j in range(len(Indexs)):
            Index += f"{Indexs[j]['Chunk']}"
        if IndexTag in ['Title', 'Logue']:
            Enter = '\n\n'
        else:
            Enter = '\n'
        if i == len(SFXIndexs)-1 :
            Enter = ''
        IndexText += f'[{IndexTag}]\n{Index}{Enter}'
    IndexInputList = [{'Id': 1, 'Continue': IndexText}]
    
    return IndexInputList, IndexsCount, IndexTagList
    
## 16-2. TranslationKeyWordList (단어장번역)의 inputList 치환
def TranslationKeyWordListToInputList(projectName, email, TranslationIndexText):
    SFXIndexs, SFXBodys = LoadSFXBodys(projectName, email)
    ## 16-2. TranslationKeyWordList (단어장번역)
    ## 2: BodyText 치환
    BodyInputList = []
    for i in range(len(SFXBodys)):
        Bodys = SFXBodys[i]
        
        IndexId = Bodys[0]['IndexId']
        IndexTag = Bodys[0]['IndexTag']
        Index = Bodys[0]['Index']
        
        BodyId = Bodys[0]['BodyId']
        BodyTag = Bodys[0]['Tag']
        
        Tab = ''
        Enter = ''
        Body = ''
        if BodyTag == 'Caption':
            Tab = '\t'
        for j in range(len(Bodys)):
            if j == len(Bodys)-1 :
                Enter = ''
            else:
                Enter = '\n'
            Body += f"{Tab}{Bodys[j]['Chunk']}{Enter}"
        BodyInputList.append({'Id': BodyId, 'Index': {'IndexId': IndexId, 'IndexTag': IndexTag, 'Index': Index}, 'Continue': Body})
        
    return BodyInputList

# ## 16-3. TranslationBody (연계번역)의 inputList 치환
# def TranslationKeyWordListToInputList(projectName, email, KeyWordList):
#     BodyInputList = TranslationKeyWordListToInputList(projectName, email)

######################
##### Filter 조건 #####
######################
## 16-1. TranslationIndex의 Filter(Error 예외처리)
def TranslationIndexFilter(responseData, IndexsCount, IndexTagList):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        OutputDic = json.loads(responseData)
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 결과에 '중요단어장'과 '영어도서목차'가 없을 때의 예외 처리
    try:
        IndexWordList = OutputDic['중요단어장']
        TranslationIndexList = OutputDic['영어도서목차']
    except:
        return "JSONStructure에서 오류 발생: JSONStructureError"
    # Error3: 결과에 '한국어'와 '영어'가 없을 때의 예외 처리
    for IndexWord in IndexWordList:
        if '한국어' not in IndexWord:
            return "JSON에서 오류 발생: JSONKeyError: '한국어'가 누락"
        if '영어' not in IndexWord:
            return "JSON에서 오류 발생: JSONKeyError: '영어'가 누락"
    # Error4: 자료의 구조가 다를 때의 예외 처리
    if len(TranslationIndexList) != IndexsCount:
        return "JSON에서 오류 발생: 번역된 목차 개수가 누락됨 (모자라거나 큼)"
    else:
        for i in range(len(TranslationIndexList)):
            if '목차기호' not in TranslationIndexList[i]:
                return "JSON에서 오류 발생: JSONKeyError: '목차기호'가 누락"
            else:
                if f'[{IndexTagList[i]}]' != TranslationIndexList[i]['목차기호']:
                    return "JSON에서 오류 발생: JSONValueError: '목차기호'가 틀림"
            if '영어목차' not in TranslationIndexList[i]:
                return "JSON에서 오류 발생: JSONKeyError: '영어목차'가 누락"

    return {'json': OutputDic, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def TranslationInputMemory(inputMemoryDics, MemoryLength):
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
def TranslationOutputMemory(outputMemoryDics, MemoryLength):
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
## 16-1. TranslationIndex (목차번역) 프롬프트 요청 및 결과물 Json화
def TranslationIndexProcess(projectName, email, processNumber, DataFramePath, memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # 언어별 Process 설정
    if processNumber == '17':
        Process = 'TranslationIndexEn'
        ProcessNumber = '17-1'
    if processNumber == '18':
        Process = 'TranslationIndexJa'
        ProcessNumber = '18-1'
    if processNumber == '19':
        Process = 'TranslationIndexZh'
        ProcessNumber = '19-1'
    if processNumber == '20':
        Process = 'TranslationIndexEs'
        ProcessNumber = '20-1'
        
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, f'{Process}_{ProcessNumber}', DataFramePath)    
    inputList, IndexsCount, IndexTagList = TranslationIndexToInputList(projectName, email)
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
    ErrorCount = 0
        
    # TranslationIndexProcess
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
         
            Filter = TranslationIndexFilter(responseData, IndexsCount, IndexTagList)
            
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
            inputMemory = TranslationInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = TranslationOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, ProcessNumber, DataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
## 데이터 치환
def TranslationResponseJson(projectName, email, ProcessNumber, DataFramePath, messagesReview = 'off', mode = "Memory", importance = 0):   
    # 16-1. TranslationIndex (목차번역) 데이터 치환
    translationIndexOutputMemoryDics = TranslationIndexProcess(projectName, email, ProcessNumber, DataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    translationIndexWordList = translationIndexOutputMemoryDics[0]['중요단어장']
    translationIndexList = translationIndexOutputMemoryDics[0]['영어도서목차']
    
    ## TranslationIndex 중요단어장
    IndexWordList = []
    for IndexWord in translationIndexWordList:
        Source = IndexWord['한국어']
        Target = IndexWord['영어']
        IndexWordList.append({'Source': Source, 'Target': Target})
    
    ## TranslationIndex 영어번역 목차
    TranslationIndexText = '<영어 도서목차>\n'
    for translationIndex in translationIndexList:
        Tag = translationIndex['목차기호']
        TranslationIndex = translationIndex['영어목차']
        TranslationIndexText += f'{Tag} {TranslationIndex}\n'
    TranslationIndexText += '\n'
    
    print(TranslationIndexText)
    sys.exit()

    TranslationKeyWordListToInputList(projectName, email, TranslationIndexText)
    # return responseJson

## 프롬프트 요청 및 결과물 Json을 SFXMatching에 업데이트
def TranslationUpdate(projectName, email, ProcessNumber, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None, Importance = 0):
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    # SFXMatching의 Count값 가져오기
    ContinueCount, Completion = SFXMatchingCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedSFXMatchingToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, f"{Process}", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}는 Existed{Process}으로 대처됨 ]\n")
        else:
            responseJson = TranslationResponseJson(projectName, email, ProcessNumber, DataFramePath, messagesReview = MessagesReview, mode = Mode, importance = Importance)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            SFXBodyId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = f'{Process}Update')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f"{Process}Update: {Update['BodyId']}")
                time.sleep(0.0001)
                SFXSplitedBodyChunks = Update[f'{Process}SplitedBodyChunks']
                AddSFXSplitedBodysToDB(projectName, email, SFXSplitedBodyChunks)

                # i값 수동 업데이트
                i += 1

            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            SFXMatchingCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")

    else:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}는 이미 완료됨 ]\n")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "240801_빨간풍차가있는집"
    ProcessNumber = '17'
    Process = 'TranslationKo'
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################
    
    TranslationResponseJson(projectName, email, ProcessNumber, DataFramePath, messagesReview = messagesReview)