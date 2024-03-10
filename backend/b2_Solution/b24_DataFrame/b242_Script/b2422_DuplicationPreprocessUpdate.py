import re
import time
import json
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedDuplicationPreprocessToDB, AddPreprocessScriptsToDB, DuplicationPreprocessCountLoad, DuplicationPreprocessCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
# IndexBodyText 로드
def LoadIndexBody(projectName, email):
    project = GetProject(projectName, email)
    indexFrame = project.IndexFrame[1]['IndexTags'][1:]
    bodyText = project.BodyText
    
    return indexFrame, bodyText

## 언어를 제외한 뛰어쓰기와 특수문자를 모두 제거
def CleanText(text):
    return re.sub(r'[\s\W]+', '', text)

## 본문을 목차별로 나누기 (따옴표 개수 누락 및 내부 문장 길이 검사, 목차 누락 검사)
def PreprocessAndSplitScripts(bodyText, indexFrame):
    ## 1. 따옴표 개수 검사 및 문장 길이 검사
    # ', "의 여러 형태를 통일
    bodyText = bodyText.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"')
    singleQuotesScripts = re.findall(r"'(.*?)'", bodyText)
    doubleQuotesScripts = re.findall(r'"(.*?)"', bodyText)
    
    # 따옴표의 개수가 짝수인지 확인
    if len(singleQuotesScripts) % 2 != 0 or len(doubleQuotesScripts) % 2 != 0:
        print("[ 전체 따옴표 개수가 홀수입니다. ]")
    
    # 따옴표 내부 문장의 길이 검토
    for ScriptInQuotes in singleQuotesScripts + doubleQuotesScripts:
        ScriptInQuotesTokens = re.sub(r'\s+', ' ', ScriptInQuotes).strip().split()
        if len(ScriptInQuotesTokens) > 100:
            print(f"[ 따옴표 내부의 문장이 너무 길어(단어수, {len(ScriptInQuotesTokens)}) 확인 필요: {' '.join(ScriptInQuotesTokens[:6])} ... {' '.join(ScriptInQuotesTokens[6:])}]\n")
    
    ## 2. 인덱스 단위로 문장 분할
    lines = bodyText.split('\n')
    preprocessedLines = [CleanText(line) for line in lines]

    MissingIndexes = []
    SplitedScripts = []
    current_index = None
    content = ""
    start_search_from_index = 0  # 다음 인덱스 검사를 시작할 위치

    for i, (preprocessedLine, originalLine) in enumerate(zip(preprocessedLines, lines)):
        if i < start_search_from_index:
            continue  # 이미 찾은 인덱스 다음부터 검사 시작

        for index in indexFrame:
            preprocessedIndex = CleanText(index["Index"])
            # 인덱스가 현재 줄에 정확하게 일치하는지 확인
            if preprocessedIndex == preprocessedLine:
                if current_index is not None:
                    # 이전 인덱스에 대한 내용 저장
                    SplitedScripts.append((current_index, content.strip()))
                    content = ""
                current_index = index["Index"]
                start_search_from_index = i + 1  # 다음 인덱스 검사는 이 줄 다음부터
                break

        if current_index is not None and i >= start_search_from_index:
            # 현재 인덱스에 대한 내용 누적
            content += originalLine + '\n'

    if current_index is not None:
        SplitedScripts.append((current_index, content.strip()))

    presentIndexes = set([index["Index"] for index in indexFrame])
    foundIndexes = set([index for index, _ in SplitedScripts])
    MissingIndexes = list(presentIndexes - foundIndexes)
    if MissingIndexes:
        print(f"[ 인덱스 누락: {MissingIndexes} ]")

    return SplitedScripts

## 문장 단위로 나누고, 3000 토큰 기준으로 분할, 따옴표로 묶인 부분은 하나의 문장으로 취급
def SplitIntoSentencesAndTokens(SplitedScripts):
    ScriptsDicList = []
    # 문장 경계 정의, 따옴표로 묶인 대화 포함
    SentenceDelimiters = re.compile(r'(?:(?<=\.)|(?<=")|(?<=\?))(?<!\.\.\.)(?<!\w\.\w.)(?<!\d\.\d)(?<=\.|\?|!)\s|(?<=\")\s')
    
    for Index, _Script in SplitedScripts:
        sentences = SentenceDelimiters.split(_Script)
        chunk = []
        script = ''
        token_count = 0
        for sentence in sentences:
            # 따옴표 내부의 문장은 하나의 문장으로 취급
            if '"' in sentence or "'" in sentence:
                sentence = re.sub(r'\s+', ' ', sentence).strip()
            token_count += len(sentence.split())
            if token_count <= 3000:
                chunk.append(sentence)
            else:
                script += ' '.join(chunk)
                chunk = [sentence]
                token_count = len(sentence.split())
        if chunk:
            script += ' '.join(chunk)
        ScriptsDicList.append({"Index": Index, "Script": script})
    
    return ScriptsDicList

## ScriptsDicList inputList 치환
def ScriptsDicListToInputList(projectName, email):
    indexFrame, bodyText = LoadIndexBody(projectName, email)

    # Raw Text를 ScriptsDicList로 치환
    SplitedScripts = PreprocessAndSplitScripts(bodyText, indexFrame)
    ScriptsDicList = SplitIntoSentencesAndTokens(SplitedScripts)

    # Raw Text를 ScriptsDicList로 치환 확인
    CleanScripts = ''
    Clean_Scripts = ''
    for i in range(len(SplitedScripts)):
        CleanScripts += CleanText(SplitedScripts[i][0])
        CleanScripts += CleanText(SplitedScripts[i][1])
        Clean_Scripts += CleanText(SplitedScripts[i][1])
    if CleanText(bodyText) != CleanScripts:
        print(f"[ 인덱스 누락: 전체 문장수 ({len(SplitedScripts)}) ]")
    clean_scripts = ''
    for i in range(len(ScriptsDicList)):
        clean_scripts += CleanText(' '.join(ScriptsDicList[i]['Script']))
    if Clean_Scripts != clean_scripts:
        print(f"[ 인덱스 누락: 전체 문장수 ({len(ScriptsDicList)}) ]")

    InputList = []
    for i in range(len(ScriptsDicList)):
        InputList.append({'Id': i+1, 'Continue': ScriptsDicList[i]['Script']})
        
    return InputList

######################
##### Filter 조건 #####
######################
def CheckCorrectness(before, after):
    # "After"가 "Before"에 포함되는지 확인
    if after in before:
        # "After"가 "Before"의 시작 부분에 있는지 확인
        if before.startswith(after):
            return True
        # "After"가 "Before"의 끝 부분에 있는지 확인
        elif before.endswith(after):
            return True
        else:
            # "After"가 "Before"의 중간에 있지만, 중복 발음이 아니라면 올바르지 않음
            return False
    else:
        # "After"가 "Before"에 포함되지 않으면 올바르지 않음
        return False

## DuplicationPreprocess의 Filter(Error 예외처리)
def DuplicationPreprocessFilter(responseData, Input):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputDic = json.loads(responseData)
        OutputDic = outputDic['중복수정']
        if OutputDic == []:
            Output = {"Duplication": OutputDic, "DuplicationScript": Input}
            return {'json': Output, 'filter': Output}
    
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    for Output in OutputDic:
        try:
            if not ('중복수정전' in Output and '중복수정후' in Output):
                return "JSON에서 오류 발생: JSONKeyError"
            else:
                Check = CheckCorrectness(Output['중복수정전'], Output['중복수정후'])
                if (Check == True) and (Output['종류'] in ['번역', '약어', '발음', '체크']):
                    Input = Input.replace(Output['중복수정전'], Output['중복수정후'])
        # Error5: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"

    Output = {"Duplication": OutputDic, "DuplicationScript": Input}
    return {"json": Output, "filter": Output}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def DuplicationPreprocessInputMemory(inputMemoryDics, MemoryLength):
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
def DuplicationPreprocessOutputMemory(outputMemoryDics, MemoryLength):
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
## DuplicationPreprocess 프롬프트 요청 및 결과물 Json화
def DuplicationPreprocessProcess(projectName, email, DataFramePath, Process = "DuplicationPreprocess",  memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, "DuplicationPreprocess")

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '02-1', DataFramePath)
    inputList = ScriptsDicListToInputList(projectName, email)
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
        
    # DuplicationPreprocessProcess
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
            memoryCounter = " - 중요사항 | '중복수정전'과 '중복수정후'는 내용과 서술을 변경하여 글을 바꾸는 것이 절대로 아니며, 단순히 이어서 2번 이상 낭독되는 번역, 약어, 발음, 기타를 찾아서 작성하는 것 | 중복수정이 없을 경우는 {'중복수정': []}로 작성 -\n"
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
                    
            Filter = DuplicationPreprocessFilter(responseData, Input)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(InputList)} | {Filter}")
                
                ErrorCount += 1
                if ErrorCount == 7:
                    print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | 오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
                    sys.exit(1)  # 오류 상태와 함께 프로그램을 종료합니다.
                    
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(InputList)} | JSONDecode 완료")
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
            inputMemory = DuplicationPreprocessInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = DuplicationPreprocessOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '02-1', DataFramePath)
    
    return outputMemoryDics
################################
##### 데이터 치환 및 DB 업데이트 #####
################################
## 데이터 치환
def DuplicationPreprocessResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):   
    # 데이터 치환
    outputMemoryDics = DuplicationPreprocessProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    DuplicationDicList = []
    for i, response in enumerate(outputMemoryDics):
        if response['Duplication'] != []:
            for Duplication in response['Duplication']:
                DuplicationDic = {"Before": Duplication['중복수정전'], "After": Duplication['중복수정후'], "Type": Duplication['종류']}
                DuplicationDicList.append(DuplicationDic)
        else:
            DuplicationDic = []
        DuplicationPreprocess = {"PreprocessId": i + 1, "Duplication": DuplicationDicList, "DuplicationScript": response['DuplicationScript']}
        responseJson.append(DuplicationPreprocess)
        DuplicationDicList = []
    
    return responseJson

## 프롬프트 요청 및 결과물 Json을 DuplicationPreprocess에 업데이트
def DuplicationPreprocessUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 02-1_DuplicationPreprocessUpdate 시작 >")
    # DuplicationPreprocess의 Count값 가져오기
    ContinueCount, Completion = DuplicationPreprocessCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedDuplicationPreprocessToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "DuplicationPreprocess", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 02-1_DuplicationPreprocessUpdate는 ExistedDuplicationPreprocess으로 대처됨 ]\n")
        else:
            responseJson = DuplicationPreprocessResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'DuplicationPreprocessUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'DuplicationPreprocessUpdate: {Update["Duplication"]}')
                time.sleep(0.0001)
                PreprocessId = Update["PreprocessId"]
                Duplication = Update["Duplication"]
                DuplicationScript = Update["DuplicationScript"]
                
                AddPreprocessScriptsToDB(projectName, email, PreprocessId, Duplication, DuplicationScript)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # # BodyFrame DuplicationPreprocessTag 업데이트
            # DuplicationPreprocessToBodyFrame(projectName, email)
            # Completion "Yes" 업데이트
            DuplicationPreprocessCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 02-1_DuplicationPreprocessUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 02-1_DuplicationPreprocessUpdate는 이미 완료됨 ]\n")
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "노인을위한나라는있다"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################