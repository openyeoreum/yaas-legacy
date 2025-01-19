import os
import re
import json
import time
import pdfplumber
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from PyPDF2 import PdfWriter, PdfReader
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedScriptGenToDB, AddScriptGenBookPagesToDB, ScriptGenCountLoad, ScriptGenCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
## LoadRawScript 로드
def LoadRawScript(projectName, email, Process, TextDirPath):
    RawScriptJsonFileName = f'{projectName}_RawScript.json'
    RawScriptFilePath = os.path.join(TextDirPath, RawScriptJsonFileName)
    
    # 기본 RawScript JSON 구조
    RawScriptJson = [
        {
            "RawScript_Completion": "No",
            "Process": f"{Process}"
        },
        {
            "Id": 1,
            "Tag": "",
            "Name": "",
            "Age": "",
            "Gender": "",
            "Title": "",
            "Content": ""
        }
    ]

    # 파일이 존재할 경우 로드
    if os.path.exists(RawScriptFilePath):
        with open(RawScriptFilePath, 'r', encoding = 'utf-8') as RawScript_Json:
            rawScriptJson = json.load(RawScript_Json)
        # RawScript_Completion 체크
        if rawScriptJson[0].get("RawScript_Completion") == "Yes" and rawScriptJson[0].get("RawScript_Completion") != "":
            Raw_ScriptJson = rawScriptJson[1:]
            return Raw_ScriptJson
        else:
            sys.exit(f'[ (([{projectName}_RawScript.json])) 작성을 완료하고 "RawScript_Completion": "Yes"로 변경해주세요 ]\n{RawScriptFilePath}')
    else:
        # 파일이 없으면 생성하고 초기 데이터 저장
        with open(RawScriptFilePath, 'w', encoding = 'utf-8') as file:
            json.dump(RawScriptJson, file, ensure_ascii = False, indent = 4)
        sys.exit(f'[ (([{projectName}_RawScript.json])) 작성을 완료하고 "RawScript_Completion": "Yes"로 변경해주세요 ]\n{RawScriptFilePath}')

## LoadRawScript의 inputList 치환
def LoadRawScriptToInputList(projectName, email, Process, TextDirPath):
    rawScriptJson = LoadRawScript(projectName, email, Process, TextDirPath)
    
    InputList = []
    for i in range(len(rawScriptJson)):
        Id = rawScriptJson[i]['Id']
        
        Tag = rawScriptJson[i]['Tag']
        tag = ''
        if Tag != '':
            tag = f'[{Tag}]\n'
        
        Name = rawScriptJson[i]['Name']
        name = ''
        if Name != '':
            name = f'이름: {Name}\n'
            
        Age = rawScriptJson[i]['Age']
        age = ''
        if Age != '':
            age = f'나이: {Age}\n'
            
        Gender = rawScriptJson[i]['Gender']
        gender = ''
        if Gender != '':
            gender = f'성별: {Gender}\n'
            
        Title = rawScriptJson[i]['Title']
        title = ''
        if Title != '':
            title = f'제목: {Title}\n'
            
        Content = rawScriptJson[i]['Content']
        content = ''
        if Content != '':
            content = f'내용:\n{Content}'
        
        RawScript = '\n' + tag + name + age + gender + title + content + '\n'
            
        InputDic = {'Id': Id, 'Continue': RawScript, 'Name': Name, 'Title': Title}
        InputList.append(InputDic)
        
    return InputList

######################
##### Filter 조건 #####
######################
## ScriptGen의 Filter(Error 예외처리)
def ScriptGenFilter(responseData, MainKey, KeyList):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(responseData)
        OutputDic = [{key: value} for key, value in outputJson.items()]
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 결과가 list가 아닐 때의 예외 처리
    if not isinstance(OutputDic, list):
        return "JSONType에서 오류 발생: JSONTypeError"
    # Error3: 자료의 첫번째 키가 MainKey가 아닐 경우
    for dic in OutputDic:
        try:
            mainKey = next(iter(dic.keys()))
            if mainKey != MainKey:
                return "JSON에서 오류 발생: JSONKeyError"
        # Error3: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        # Error4: 자료의 하부 키들이
        for Key in KeyList:
            if not Key in dic[MainKey]:
                return f"JSON에서 오류 발생: JSONKeyError, '{Key}' Key 누락"

    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def ScriptGenInputMemory(inputMemoryDics, MemoryLength):
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
def ScriptGenOutputMemory(outputMemoryDics, MemoryLength):
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
## ScriptGen 프롬프트 요청 및 결과물 Json화
def ScriptGenProcess(projectName, email, DataFramePath, ScriptConfig, TextDirPath, Process = "ScriptGen", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, "ScriptGen")

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '00', DataFramePath)
    inputList = LoadRawScriptToInputList(projectName, email, ScriptConfig['Process'], TextDirPath)
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
        
    # ScriptGenProcess
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
            Input = '\n' + InputDic['Continue']
            if outputMemory == []:
                memoryCounter = f" '{InputDic['Name']}, {InputDic['Title']}'의 부분을 작성해주세요.\n\n".replace("', ", "'").replace(", '", "'")
            else:
                memoryCounter = f"에서 '{InputDic['Name']} {InputDic['Title']}'의 부분을 이어서 작성해주세요.\n\n".replace("', ", "'").replace(", '", "'")
            outputEnder = ""

            # Response 생성
            if ScriptConfig['Model'] == "OpenAI":
                Response, Usage, Model = OpenAI_LLMresponse(projectName, email, ScriptConfig['Process'], Input, ProcessCount, Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)
            elif ScriptConfig['Model'] == "ANTHROPIC":
                Response, Usage, Model = ANTHROPIC_LLMresponse(projectName, email, ScriptConfig['Process'], Input, ProcessCount, Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)
            
            # OutputStarter, OutputEnder에 따른 Response 전처리
            promptFrame = GetPromptFrame(ScriptConfig['Process'])
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
            Filter = ScriptGenFilter(responseData, ScriptConfig['MainKey'], ScriptConfig['KeyList'])
            
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
            inputMemory = ScriptGenInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = ScriptGenOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '00', DataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
## 데이터 치환
def ScriptGenResponseJson(projectName, email, DataFramePath, TextDirPath, ScriptConfig, messagesReview = 'off', mode = "Memory"):   
    ### A. 데이터 치환 ###
    RawScriptJson = LoadRawScript(projectName, email, ScriptConfig['Process'], TextDirPath)
    outputMemoryDics = ScriptGenProcess(projectName, email, DataFramePath, ScriptConfig, TextDirPath, MessagesReview = messagesReview, Mode = ScriptConfig['Mode'])

    responseJson = []
    ScriptIndex = ''
    ScriptBody = ''
    ## A-1. RawScriptJson에 Title이 표기된 경우 (프롬프트에 타이틀을 주어준 경우)
    if RawScriptJson[0]['Title'] != '':
        for i in range(len(outputMemoryDics)):
            Title = f"<{RawScriptJson[i]['Title']}>\n"
            Name = f"{RawScriptJson[i]['Name']}\n\n"
            Scripts = ""
            for Key in ScriptConfig['KeyList']:
                Scripts += f"{outputMemoryDics[i][0][ScriptConfig['MainKey']][Key]}\n\n"
            
            Script = Title + Name + Scripts
            ScriptDic = {'ScriptId': i+1, 'Script': Script}
            
            ScriptIndex += f'{Title}\n'
            ScriptBody += Script
            
            responseJson.append(ScriptDic)
    ## A-2. RawScriptJson에 Title이 표기된 경우 (프롬프트에 타이틀을 주어준 경우)
    else:
        for i in range(len(outputMemoryDics)):
            ScriptIndex = f"{outputMemoryDics[i][0][ScriptConfig['MainKey']][ScriptConfig['KeyList'][0]]}"
            ScriptBody = f"{outputMemoryDics[i][0][ScriptConfig['MainKey']][ScriptConfig['KeyList'][1]]}"
            ScriptDic = {'ScriptId': i+1, 'Script': ScriptBody}
            
            responseJson.append(ScriptDic)
    
    ### B. projectName_Index.text 저장 ###
    if ScriptConfig['RawMode'] == 'on':
        ScriptRawIndexFilePath = TextDirPath + f'/{projectName}_Index(Raw).txt'
        ScriptRawBodyFilePath = TextDirPath + f'/{projectName}_Body(Raw).txt'
    else:
        ScriptRawIndexFilePath = TextDirPath + f'/{projectName}_Index.txt'
        ScriptRawBodyFilePath = TextDirPath + f'/{projectName}_Body.txt'
        
    ScriptIndexFilePath = TextDirPath + f'/{projectName}_Index.txt'
    if not (os.path.exists(ScriptRawIndexFilePath) or os.path.exists(ScriptIndexFilePath)):
        with open(ScriptRawIndexFilePath, 'w', encoding = 'utf-8') as index_file:
            index_file.write(ScriptIndex)
    
    ### C. projectName_Body.text 저장 ###
    ScriptBodyFilePath = TextDirPath + f'/{projectName}_Body.txt'
    if not (os.path.exists(ScriptRawBodyFilePath) or os.path.exists(ScriptBodyFilePath)):
        with open(ScriptRawBodyFilePath, 'w', encoding = 'utf-8') as body_file:
            body_file.write(ScriptBody)
            
    return responseJson

## 프롬프트 요청 및 결과물 Json을 ScriptGen에 업데이트
def ScriptGenUpdate(projectName, email, DataFramePath, ScriptConfig, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    # 경로 설정
    TextDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script/{projectName}_master_script_file"
    IndexTextFilePath = TextDirPath + f'/{projectName}_Index.txt'
    RawIndexTextFilePath = TextDirPath + f'/{projectName}_Index(Raw).txt'
    BodyTextFilePath = TextDirPath + f'/{projectName}_Body.txt'
    RawBodyTextFilePath = TextDirPath + f'/{projectName}_Body(Raw).txt'
    
    if not (os.path.exists(IndexTextFilePath) and os.path.exists(BodyTextFilePath)):
        print(f"< User: {email} | Project: {projectName} | 00_ScriptGenUpdate 시작 >")
        # ScriptGen의 Count값 가져오기
        ScriptCount, Completion = ScriptGenCountLoad(projectName, email)
        if Completion == "No":
            if ExistedDataFrame != None:
                # 이전 작업이 존재할 경우 가져온 뒤 업데이트
                AddExistedScriptGenToDB(projectName, email, ExistedDataFrame)
                AddExistedDataSetToDB(projectName, email, "ScriptGen", ExistedDataSet)
                print(f"[ User: {email} | Project: {projectName} | 00_ScriptGenUpdate는 ExistedScriptGen으로 대처됨 ]\n")
                
                responseJson = ScriptGenResponseJson(projectName, email, DataFramePath, TextDirPath, ScriptConfig, messagesReview = MessagesReview, mode = Mode)

                if os.path.exists(RawIndexTextFilePath) and os.path.exists(RawBodyTextFilePath):
                    sys.exit(f"\n\n[ ((({projectName}_Index(Raw).txt))), ((({projectName}_Body(Raw).txt))) 파일을 완성한뒤 파일이름 뒤에  -> (Raw) <- 를 제거해 주세요. ]\n({TextDirPath})\n\n1. 타이틀과 로그 부분을 작성\n2. 추가로 필요한 내용 작성\n3. 낭독이 바뀌는 부분에 \"...\" 쌍따옴표 처리\n\n4. 목차(_Index)파일과 본문(_Body) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n5. 본문(_Body)파일 내 쌍따옴표(“대화문”의 완성) 개수 일치 * _Body(검수용) 파일 확인\n6. 캡션 등의 줄바꿈 및 캡션이 아닌 일반 문장은 마지막 온점(.)처리\n\n7. {projectName}_Index(Raw).txt, {projectName}_Body(Raw).txt 파일명에 -> (Raw) <- 를 제거\n\n")
                else:
                    time.sleep(0.1)
            else:
                responseJson = ScriptGenResponseJson(projectName, email, DataFramePath, TextDirPath, ScriptConfig, messagesReview = MessagesReview, mode = Mode)
                
                # ResponseJson을 ContinueCount로 슬라이스
                ResponseJson = responseJson[ScriptCount:]
                ResponseJsonCount = len(ResponseJson)

                # TQDM 셋팅
                UpdateTQDM = tqdm(ResponseJson,
                                total = ResponseJsonCount,
                                desc = 'ScriptGenUpdate')
                # i값 수동 생성
                i = 0
                for Update in UpdateTQDM:
                    UpdateTQDM.set_description(f'ScriptGenUpdate: {Update["ScriptId"]}...')
                    time.sleep(0.0001)
                    ScriptId = Update["ScriptId"]
                    Script = Update["Script"]
                    
                    AddScriptGenBookPagesToDB(projectName, email, ScriptId, Script)
                    # i값 수동 업데이트
                    i += 1
                
                UpdateTQDM.close()
                # Completion "Yes" 업데이트
                ScriptGenCompletionUpdate(projectName, email)
                print(f"[ User: {email} | Project: {projectName} | 00_ScriptGenUpdate 완료 ]\n")
        else:
            print(f"[ User: {email} | Project: {projectName} | 00_ScriptGenUpdate는 이미 완료됨 ]\n")
    else:
        print(f"[ User: {email} | Project: {projectName} | 00_ScriptGenUpdate는 ExistedScriptGen으로 대처됨 ]\n")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "241118_우리반오디오북아름초5학년5반"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################