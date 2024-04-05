import re
import json
import tiktoken
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from extension.e1_Solution.e11_General.e111_GetDBtable import GetExtensionPromptFrame
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraph
from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import LoadExtensionOutputMemory, SaveExtensionOutputMemory, AddExistedLifeGraphTranslationKoToDB, AddLifeGraphTranslationKoLifeGraphsToDB, AddLifeGraphTranslationKoLifeDataTextsToDB, LifeGraphTranslationKoCountLoad, InitLifeGraphTranslationKo, LifeGraphTranslationKoCompletionUpdate, UpdatedLifeGraphTranslationKo

#########################
##### InputList 생성 #####
#########################
# LifeGraphSet 로드
def LoadLifeGraphFrameTexts(lifeGraphSetName, latestUpdateDate):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphFrameTexts = lifeGraph.LifeGraphFrame[2]['LifeDataTexts'][1:]
    
    return LifeGraphFrameTexts

## LifeGraphFrameTexts의 inputList 치환
def LifeGraphFrameTextsToInputList(lifeGraphSetName, latestUpdateDate):
    LifeGraphFrameTexts = LoadLifeGraphFrameTexts(lifeGraphSetName, latestUpdateDate)
    
    InputList = []
    for i in range(len(LifeGraphFrameTexts)):
        Id = LifeGraphFrameTexts[i]['LifeGraphId']
        Language = LifeGraphFrameTexts[i]['Language']
        TextGlobalKo = LifeGraphFrameTexts[i]['TextGlobal']['Ko']

        if Language in ['ko', 'None']:
            Tag = 'Pass'
        else:
            Tag = 'Continue'
            
        InputDic = {'Id': Id, Tag: TextGlobalKo}
        InputList.append(InputDic)
        
    return InputList

######################
##### Filter 조건 #####
######################
## LifeGraphTranslationKo의 Filter(Error 예외처리)
def LifeGraphTranslationKoFilter(responseData, memoryCounter):
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
            # '인생데이터' 키 확인 및 처리
            if '인생데이터' in dic:
                for item in dic['인생데이터']:
                    if not all(key in item for key in ['시기', '행복지수', '이유']):
                        return "JSON에서 오류 발생: JSONKeyError, 인생데이터 내의 항목, {key}"

            # '예상거주지' 키 확인 및 처리
            if '예상거주지' in dic:
                for item in dic['예상거주지']:
                    if not all(key in item for key in ['지역', '이유', '정확도']):
                        return "JSON에서 오류 발생: JSONKeyError, 인생데이터 내의 항목, {key}"

        except AttributeError as e:
            return f"JSON에서 오류 발생: AttributeError, {str(e)}"
            
        return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def LifeGraphTranslationKoInputMemory(inputMemoryDics, MemoryLength):
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
def LifeGraphTranslationKoOutputMemory(outputMemoryDics, MemoryLength):
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
## LifeGraphTranslationKo 프롬프트 요청 및 결과물 Json화
def LifeGraphTranslationKoProcess(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, Process = "LifeGraphTranslationKo", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):

    OutputMemoryDicsFile, OutputMemoryCount = LoadExtensionOutputMemory(lifeGraphSetName, latestUpdateDate, '02', LifeGraphDataFramePath)    
    inputList = LifeGraphFrameTextsToInputList(lifeGraphSetName, latestUpdateDate)
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
            outputEnder = f"{{'인생데이터': [{{'시기': '"
            
            # Response 생성
            Response, Usage, Model = OpenAI_LLMresponse(lifeGraphSetName, latestUpdateDate, Process, Input, ProcessCount, root = "extension", Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)

            # OutputStarter, OutputEnder에 따른 Response 전처리
            promptFrame = GetExtensionPromptFrame(Process)
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
         
            Filter = LifeGraphTranslationKoFilter(responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"LifeGraphSetName: {lifeGraphSetName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                
                # 2분 대기 이후 다시 코드 실행
                ErrorCount += 1
                print((f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | 오류횟수 {ErrorCount}회, 2분 후 프롬프트 재시도"))
                time.sleep(120)
                if ErrorCount == 5:
                    print(f"Project: {lifeGraphSetName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | 오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
                    sys.exit(1)  # 오류 상태와 함께 프로그램을 종료합니다.
                    
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                print(f"LifeGraphSetName: {lifeGraphSetName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | JSONDecode 완료")
                ErrorCount = 0
                
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
            inputMemory = LifeGraphTranslationKoInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = LifeGraphTranslationKoOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveExtensionOutputMemory(lifeGraphSetName, latestUpdateDate, outputMemoryDics, '02', LifeGraphDataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################

def LifeGraphTranslationKoResponseJson(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, messagesReview = 'off', mode = "Memory"):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphs = lifeGraph.LifeGraphFrame[1]['LifeGraphs'][1:]
    outputMemoryDics = LifeGraphTranslationKoProcess(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    TranslatedKeys = {
        '지역': 'Area',
        '이유': 'Reason',
        '정확도': 'Accuracy'
    }
    
    responseJson = []
    for i, response in enumerate(outputMemoryDics):
        if response != "Pass":
            LifeGraphId = i + 1
            LifeGraphDate = LifeGraphs[i]['LifeGraphDate']
            Name = LifeGraphs[i]['Name']
            Age = LifeGraphs[i]['Age']
            Source = LifeGraphs[i]['Source']
            Language = LifeGraphs[i]['Language']
            Translation = 'ko'
            print(response[1]["예상거주지"])
            residence = {TranslatedKeys[key]: value for key, value in response[1]["예상거주지"].items()}
            Residence = residence
            PhoneNumber = LifeGraphs[i]['PhoneNumber']
            Email = LifeGraphs[i]['Email']
            Quality = LifeGraphs[i]['Quality']
            LifeData = []
            for j in range(len(response[0]["인생데이터"])):
                LifeDataId = j + 1
                Ages = response[0]["인생데이터"][j]["시기"].split('-')
                StartAge = int(Ages[0])
                EndAge = int(Ages[-1])
                Score = int(response[0]["인생데이터"][j]["행복지수"])
                ReasonKo = response[0]["인생데이터"][j]["이유"]
                LifeData.append({'LifeDataId': LifeDataId, 'StartAge': StartAge, 'EndAge': EndAge, 'Score': Score, 'ReasonKo': ReasonKo})
            responseJson.append({'LifeGraphId': LifeGraphId, 'LifeGraphDate': LifeGraphDate, 'Name': Name, 'Age': Age, 'Source': Source, 'Language': Language, 'Translation': Translation, 'Residence': Residence, 'PhoneNumber': PhoneNumber, 'Email': Email, 'Quality': Quality, 'LifeData': LifeData})
        else:
            LifeGraphId = i + 1
            LifeGraphDate = LifeGraphs[i]['LifeGraphDate']
            Name = LifeGraphs[i]['Name']
            Age = LifeGraphs[i]['Age']
            Source = LifeGraphs[i]['Source']
            Language = LifeGraphs[i]['Language']
            Residence = LifeGraphs[i]["Residence"]
            PhoneNumber = LifeGraphs[i]['PhoneNumber']
            Email = LifeGraphs[i]['Email']
            Quality = LifeGraphs[i]['Quality']
            for k in range(len(LifeGraphs[i]['LifeData'])):
                LifeGraphs[i]['LifeData'][k]['ReasonKo'] = LifeGraphs[i]['LifeData'][k].pop('ReasonGlobal')
            LifeData = LifeGraphs[i]['LifeData']
            responseJson.append({'LifeGraphId': LifeGraphId, 'LifeGraphDate': LifeGraphDate, 'Name': Name, 'Age': Age, 'Source': Source, 'Language': Language, 'Translation': Language, 'Residence': Residence, 'PhoneNumber': PhoneNumber, 'Email': Email, 'Quality': Quality, 'LifeData': LifeData})

    return responseJson

def LifeDataToText(ResponseJson):

    LifeDataTexts = []
    for i in range(len(ResponseJson)):
        LifeGraphDate = ResponseJson[i]["LifeGraphDate"]
        Name = ResponseJson[i]["Name"]
        Age = ResponseJson[i]["Age"]
        Email = ResponseJson[i]["Email"]
        Language = ResponseJson[i]["Language"]
        Translation = ResponseJson[i]["Translation"]
        LifeData = []
        for j in range(len(ResponseJson[i]["LifeData"])):
            StartAge = ResponseJson[i]["LifeData"][j]["StartAge"]
            EndAge = ResponseJson[i]["LifeData"][j]["EndAge"]
            Score = ResponseJson[i]["LifeData"][j]["Score"]

            if ResponseJson[i]["LifeData"][j]["ReasonKo"] == '':
                ReasonKo = '내용없음'
            else:
                ReasonKo = ResponseJson[i]["LifeData"][j]["ReasonKo"]

            if j == (len(ResponseJson[i]["LifeData"]) - 1):
                LifeData.append(f'{StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {ReasonKo}')
            else:
                LifeData.append(f'{StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {ReasonKo}\n')

        LifeDataText = f"작성일: {LifeGraphDate}\nEmail: {Email}\n\n● '{Name}'의 {Age}세 까지의 인생\n\n" + "".join(LifeData)
        LifeDataTexts.append({"Name": Name, "Email": Email, "Language": Language, "Translation": Translation, "TextKo": LifeDataText})

    return LifeDataTexts

## LifeDataTexts를 LifeGraphTranslationKo에 업데이트
def LifeGraphTranslationKoLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson):
    LifeDataTexts = LifeDataToText(ResponseJson)
    LifeDataTextsCount = len(LifeDataTexts)
    
    # TQDM 셋팅
    UpdateTQDM = tqdm(LifeDataTexts,
                    total = LifeDataTextsCount,
                    desc = 'LifeGraphTranslationKoLifeDataTextsUpdate')
    # i값 수동 생성
    i = 0
    for Update in UpdateTQDM:
        UpdateTQDM.set_description(f'LifeGraphTranslationKoLifeDataTextsUpdate: {Update["Name"]}, {Update["Email"]} ...')
        time.sleep(0.0001)
        LifeGraphId = i + 1
        Language = LifeDataTexts[i]["Language"]
        Translation = LifeDataTexts[i]["Translation"]
        TextKo = LifeDataTexts[i]["TextKo"]
        
        AddLifeGraphTranslationKoLifeDataTextsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Language, Translation, TextKo)
        # i값 수동 업데이트
        i += 1

    UpdateTQDM.close()

## 결과물 Json을 LifeGraphTranslationKo에 업데이트
def LifeGraphTranslationKoUpdate(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None):
    print(f"< LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 02_LifeGraphTranslationKoUpdate 시작 >")
    # LifeGraphTranslationKo의 Count값 가져오기
    LifeGraphCount, LifeDataTextsCount, Completion = LifeGraphTranslationKoCountLoad(lifeGraphSetName, latestUpdateDate)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedLifeGraphTranslationKoToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame)
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 02_LifeGraphTranslationKo로 대처됨 ]\n")
        else:
            responseJson = LifeGraphTranslationKoResponseJson(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, messagesReview = MessagesReview, mode = Mode)
            # LifeGraphs를 LifeGraphCount로 슬라이스
            ResponseJson = responseJson[LifeGraphCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'LifeGraphTranslationKoUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'LifeGraphTranslationKoUpdate: {Update["Residence"]} ...')
                time.sleep(0.0001)
                
                LifeGraphId = i + 1
                LifeGraphDate = Update["LifeGraphDate"]
                Name = Update["Name"]
                Age = Update["Age"]
                Source = Update["Source"]
                Language = Update["Language"]
                Translation = Update["Translation"]
                Residence = Update["Residence"]
                PhoneNumber = Update["PhoneNumber"]
                Email = Update["Email"]
                Quality = Update["Quality"]
                LifeData = Update["LifeData"]

                AddLifeGraphTranslationKoLifeGraphsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Translation, Residence, PhoneNumber, Email, Quality, LifeData)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            ##### LifeDataTexts 업데이트
            LifeGraphTranslationKoLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson)
            #####
            # Completion "Yes" 업데이트
            LifeGraphTranslationKoCompletionUpdate(lifeGraphSetName, latestUpdateDate)
            
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 02_LifeGraphTranslationKoUpdate 완료 ]\n")
    else:
        print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 02_LifeGraphTranslationKoUpdate는 이미 완료됨 ]\n")
    
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################