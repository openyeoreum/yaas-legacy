import re
import time
import json
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedPronunciationPreprocessToDB, AddPronunciationPreprocessScriptsToDB, PronunciationPreprocessCountLoad, PronunciationPreprocessCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
# duplicationPreprocessFrame 로드
def LoadduplicationPreprocessFrame(projectName, email):
    project = GetProject(projectName, email)
    duplicationPreprocessFrame = project.DuplicationPreprocessFrame[1]['PreprocessScripts'][1:]
    
    return duplicationPreprocessFrame

## duplicationPreprocessFrame inputList 치환
def DuplicationPreprocessFrameToInputList(projectName, email):
    duplicationPreprocessFrame = LoadduplicationPreprocessFrame(projectName, email)
    InputList = []
    for i in range(len(duplicationPreprocessFrame)):
        InputList.append({'Id': i+1, 'Index': duplicationPreprocessFrame[i]['Index'], 'Continue': duplicationPreprocessFrame[i]['DuplicationScript'].replace('∨∨', ''), 'Script': duplicationPreprocessFrame[i]['DuplicationScript']})
        
    return InputList

######################
##### Filter 조건 #####
######################
## PronunciationPreprocess의 Filter(Error 예외처리)
def PronunciationPreprocessFilter(responseData, Input, Index):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputDic = json.loads(responseData)
        OutputDic = outputDic['발음수정']
        if OutputDic == []:
            Output = {"Index": Index, "Pronunciation": OutputDic, "PronunciationScript": Input}
            return {'json': Output, 'filter': Output}
    
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    sortedOutputDic = sorted(OutputDic, key = lambda x: len(x["발음수정전"]), reverse = True)
    for Output in sortedOutputDic:
        try:
            if not ('발음수정전' in Output and '발음수정후' in Output):
                return "JSON에서 오류 발생: JSONKeyError"
            elif not Output['종류'] in ['숫자', '외국어', '영어', '일본어', '중국어', '한자', '프랑스어', '독일어', '기호', '특수문자', '기타']:
                return f"JSON에서 오류 발생 ({Output['종류']}): JSONKeyError"
            else:
                if not Output['발음수정전'] in ['◆', '◇', '◎']:
                    if Output['종류'] not in ['기호', '특수문자']:
                        Input = Input.replace(Output['발음수정전'], Output['발음수정후'])
        # Error2: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"

    Output = {"Index": Index, "Pronunciation": OutputDic, "PronunciationScript": Input}
    return {"json": Output, "filter": Output}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def PronunciationPreprocessInputMemory(inputMemoryDics, MemoryLength):
    inputMemoryDic = inputMemoryDics[-(MemoryLength + 1):]
    
    inputMemoryList = []
    for inputmeMory in inputMemoryDic:
        key = list(inputmeMory.keys())[2]  # 두 번째 키값
        if key == "Continue":
            inputMemoryList.append(inputmeMory['Continue'])
        else:
            inputMemoryList.append(inputmeMory['Pass'])
    inputMemory = "".join(inputMemoryList)
    # print(f"@@@@@@@@@@\ninputMemory :{inputMemory}\n@@@@@@@@@@")
    
    return inputMemory

## outputMemory 형성
def PronunciationPreprocessOutputMemory(outputMemoryDics, MemoryLength):
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
## 수와 관련된 기호(+, -, /, 를 제외한
def RemoveSpecialCharacters(Input):
    # 수학 기호를 한글 발음으로 변환하는 딕셔너리 (마침표 제외)
    mathSymbols = {
        r'\+': '플러스', r'=': '는', r'\%': '퍼센트', r'\^': '제곱', r'±': '플러스마이너스', r'×': '곱하기', r'÷': '나누기', r'≠': '같지않다', r'≤': '작거나같다', r'≥': '크거나같다', r'∞': '무한대', r'∴': '그러므로', r'♂': '수컷', r'♀': '암컷', r'∠': '각', r'⊥': '수직', r'⌒': '호', r'∂': '편미분', r'∇': '델', r'≡': '항등', r'≒': '근사', r'≪': '매우작다', r'≫': '매우크다', r'√': '제곱근', r'∝': '비례', r'∵': '왜냐하면', r'∫': '적분', r'∬': '이중적분', r'∈': '원소', r'∋': '원소포함', r'⊆': '부분집합', r'⊇': '부분집합포함', r'⊂': '진부분집합', r'⊃': '초집합', r'∪': '합집합', r'∩': '교집합', r'∧': '논리곱', r'∨': '논리합', r'￢': '부정', r'⇒': '함의', r'⇔': '동치', r'∀': '모든', r'∃': '존재한다', r'∮': '선적분', r'∑': '시그마', r'∏': '파이', r'\＄': '달러', r'％': '퍼센트', r'￦': '원화', r'°': '도씨', r'℃': '섭씨', r'Å': '옹스트롬', r'￠': '센트', r'￡': '파운드', r'￥': '엔화', r'¤': '통화', r'℉': '화씨', r'‰': '퍼밀', r'€': '유로', r'Ω': '옴'
    }

    # 수학 기호를 한글 발음으로 변환
    for symbol, hangul in mathSymbols.items():
        Input = re.sub(symbol, hangul, Input)

    return Input

## PronunciationPreprocess 프롬프트 요청 및 결과물 Json화
def PronunciationPreprocessProcess(projectName, email, DataFramePath, Process = "PronunciationPreprocess",  memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, "PronunciationPreprocess")

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '02-2', DataFramePath)
    inputList = DuplicationPreprocessFrameToInputList(projectName, email)
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
        
    # PronunciationPreprocessProcess
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
            Index = InputDic['Index']
            Script = InputDic['Script']
            Input = RemoveSpecialCharacters(Input)
            memoryCounter = " - 중요사항 | '발음수정전'과 '발음수정후'는 *숫자, *외국어, *기호, *특수문자 등의 요소들을 한글발음으로 수정하는 것 | 발음수정이 없을 경우는 {'발음수정': []}로 작성 -\n"
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
                    
            Filter = PronunciationPreprocessFilter(responseData, Script, Index)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                
                # 2분 대기 이후 다시 코드 실행
                ErrorCount += 1
                print((f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | 오류횟수 {ErrorCount}회, 2분 후 프롬프트 재시도"))
                time.sleep(120)
                if ErrorCount == 5:
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
            inputMemory = PronunciationPreprocessInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = PronunciationPreprocessOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '02-2', DataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
## 데이터 치환
def PronunciationPreprocessResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):   
    # 데이터 치환
    outputMemoryDics = PronunciationPreprocessProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    PronunciationDicList = []
    for i, response in enumerate(outputMemoryDics):
        if response['Pronunciation'] != []:
            for Pronunciation in response['Pronunciation']:
                PronunciationDic = {"Before": Pronunciation['발음수정전'], "After": Pronunciation['발음수정후'], "Type": Pronunciation['종류']}
                PronunciationDicList.append(PronunciationDic)
        else:
            PronunciationDic = []
        PronunciationPreprocess = {"PreprocessId": i + 1, "Index": response['Index'], "Pronunciation": PronunciationDicList, "PronunciationScript": response['PronunciationScript']}
        responseJson.append(PronunciationPreprocess)
        PronunciationDicList = []
    
    return responseJson

## 프롬프트 요청 및 결과물 Json을 PronunciationPreprocess에 업데이트
def PronunciationPreprocessUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 02-2_PronunciationPreprocessUpdate 시작 >")
    # PronunciationPreprocess의 Count값 가져오기
    ContinueCount, Completion = PronunciationPreprocessCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedPronunciationPreprocessToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "PronunciationPreprocess", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 02-2_PronunciationPreprocessUpdate는 ExistedPronunciationPreprocess으로 대처됨 ]\n")
        else:
            responseJson = PronunciationPreprocessResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'PronunciationPreprocessUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'PronunciationPreprocessUpdate: {Update["Pronunciation"]}')
                time.sleep(0.0001)
                PreprocessId = Update["PreprocessId"]
                Index = Update["Index"]
                Pronunciation = Update["Pronunciation"]
                PronunciationScript = Update["PronunciationScript"]
                
                AddPronunciationPreprocessScriptsToDB(projectName, email, PreprocessId, Index, Pronunciation, PronunciationScript)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # # BodyFrame PronunciationPreprocessTag 업데이트
            # PronunciationPreprocessToBodyFrame(projectName, email)
            # Completion "Yes" 업데이트
            PronunciationPreprocessCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 02-2_PronunciationPreprocessUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 02-2_PronunciationPreprocessUpdate는 이미 완료됨 ]\n")
        
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