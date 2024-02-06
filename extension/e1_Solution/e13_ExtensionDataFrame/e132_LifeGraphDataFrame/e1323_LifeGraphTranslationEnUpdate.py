import re
import json
import tiktoken
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from extension.e1_Solution.e11_General.e111_GetDBtable import GetExtensionPromptFrame
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraph
from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import LoadExtensionOutputMemory, SaveExtensionOutputMemory, AddExistedLifeGraphTranslationEnToDB, AddLifeGraphTranslationEnLifeGraphsToDB, AddLifeGraphTranslationEnLifeDataTextsToDB, LifeGraphTranslationEnCountLoad, InitLifeGraphTranslationEn, LifeGraphTranslationEnCompletionUpdate, UpdatedLifeGraphTranslationEn

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
        TextGlobalEn = LifeGraphFrameTexts[i]['TextGlobal']['En']

        if Language in ['en', 'None']:
            Tag = 'Pass'
        else:
            Tag = 'Continue'
            
        InputDic = {'Id': Id, Tag: TextGlobalEn}
        InputList.append(InputDic)
        
    return InputList

######################
##### Filter 조건 #####
######################
## LifeGraphTranslationEn의 Filter(Error 예외처리)
def LifeGraphTranslationEnFilter(responseData, memoryCounter):
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
            # 'LifeData' 키 확인 및 처리
            if 'LifeData' in dic:
                for item in dic['LifeData']:
                    if not all(key in item for key in ['Period', 'Score', 'Reason']):
                        return "JSON에서 오류 발생: JSONKeyError, LifeData 내의 항목, {key}"

            # 'ExpectedResidence' 키 확인 및 처리
            if 'ExpectedResidence' in dic:
                for item in dic['ExpectedResidence']:
                    if not all(key in item for key in ['Area', 'Reason', 'Accuracy']):
                        return "JSON에서 오류 발생: JSONKeyError, LifeData 내의 항목, {key}"

        except AttributeError as e:
            return f"JSON에서 오류 발생: AttributeError, {str(e)}"
            
        return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def LifeGraphTranslationEnInputMemory(inputMemoryDics, MemoryLength):
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
def LifeGraphTranslationEnOutputMemory(outputMemoryDics, MemoryLength):
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
## LifeGraphTranslationEn 프롬프트 요청 및 결과물 Json화
def LifeGraphTranslationEnProcess(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, Process = "LifeGraphTranslationEn", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):

    OutputMemoryDicsFile, OutputMemoryCount = LoadExtensionOutputMemory(lifeGraphSetName, latestUpdateDate, '03', LifeGraphDataFramePath)    
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
            outputEnder = f"{{'LifeData': [{{'Period': '"
            
            # Response 생성
            Response, Usage, Model = LLMresponse(lifeGraphSetName, latestUpdateDate, Process, Input, ProcessCount, root = "extension", Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)

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
         
            Filter = LifeGraphTranslationEnFilter(responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"LifeGraphSetName: {lifeGraphSetName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                
                ErrorCount += 1
                if ErrorCount == 10:
                    print(f"Project: {lifeGraphSetName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | 오류횟수 10회 초과, 프롬프트 종료")
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
            inputMemory = LifeGraphTranslationEnInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = LifeGraphTranslationEnOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveExtensionOutputMemory(lifeGraphSetName, latestUpdateDate, outputMemoryDics, '03', LifeGraphDataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################

def LifeGraphTranslationEnResponseJson(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, messagesReview = 'off', mode = "Memory"):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphs = lifeGraph.LifeGraphFrame[1]['LifeGraphs'][1:]
    outputMemoryDics = LifeGraphTranslationEnProcess(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    for i, response in enumerate(outputMemoryDics):
        if response != "Pass":
            LifeGraphId = i + 1
            LifeGraphDate = LifeGraphs[i]['LifeGraphDate']
            Name = LifeGraphs[i]['Name']
            Age = LifeGraphs[i]['Age']
            Source = LifeGraphs[i]['Source']
            Language = LifeGraphs[i]['Language']
            Translation = 'en'
            Residence = response[1]["ExpectedResidence"]
            PhoneNumber = LifeGraphs[i]['PhoneNumber']
            Email = LifeGraphs[i]['Email']
            Quality = LifeGraphs[i]['Quality']
            LifeData = []
            for j in range(len(response[0]["LifeData"])):
                LifeDataId = j + 1
                Ages = response[0]["LifeData"][j]["Period"].split('-')
                StartAge = int(Ages[0])
                EndAge = int(Ages[-1])
                Score = int(response[0]["LifeData"][j]["Score"])
                ReasonEn = response[0]["LifeData"][j]["Reason"]
                LifeData.append({'LifeDataId': LifeDataId, 'StartAge': StartAge, 'EndAge': EndAge, 'Score': Score, 'ReasonEn': ReasonEn})
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
                LifeGraphs[i]['LifeData'][k]['ReasonEn'] = LifeGraphs[i]['LifeData'][k].pop('ReasonGlobal')
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

            if ResponseJson[i]["LifeData"][j]["ReasonEn"] == '':
                ReasonEn = 'No Content'
            else:
                ReasonEn = ResponseJson[i]["LifeData"][j]["ReasonEn"]

            if j == (len(ResponseJson[i]["LifeData"]) - 1):
                LifeData.append(f'{StartAge}-{EndAge} Happiness Score: {Score}, Reason: {ReasonEn}')
            else:
                LifeData.append(f'{StartAge}-{EndAge} Happiness Score: {Score}, Reason: {ReasonEn}\n')

        LifeDataText = f"Date: {LifeGraphDate}\nEmail: {Email}\n\n● Life up to the age of {Age} for '{Name}'\n\n" + "".join(LifeData)
        LifeDataTexts.append({"Name": Name, "Email": Email, "Language": Language, "Translation": Translation, "TextEn": LifeDataText})

    return LifeDataTexts

## LifeDataTexts를 LifeGraphTranslationEn에 업데이트
def LifeGraphTranslationEnLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson):
    LifeDataTexts = LifeDataToText(ResponseJson)
    LifeDataTextsCount = len(LifeDataTexts)
    
    # TQDM 셋팅
    UpdateTQDM = tqdm(LifeDataTexts,
                    total = LifeDataTextsCount,
                    desc = 'LifeGraphTranslationEnLifeDataTextsUpdate')
    # i값 수동 생성
    i = 0
    for Update in UpdateTQDM:
        UpdateTQDM.set_description(f'LifeGraphTranslationEnLifeDataTextsUpdate: {Update["Name"]}, {Update["Email"]} ...')
        time.sleep(0.0001)
        LifeGraphId = i + 1
        Language = LifeDataTexts[i]["Language"]
        Translation = LifeDataTexts[i]["Translation"]
        TextEn = LifeDataTexts[i]["TextEn"]
        
        AddLifeGraphTranslationEnLifeDataTextsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Language, Translation, TextEn)
        # i값 수동 업데이트
        i += 1

    UpdateTQDM.close()

## 결과물 Json을 LifeGraphTranslationEn에 업데이트
def LifeGraphTranslationEnUpdate(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None):
    print(f"< LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 03_LifeGraphTranslationEnUpdate 시작 >")
    # LifeGraphTranslationEn의 Count값 가져오기
    LifeGraphCount, LifeDataTextsCount, Completion = LifeGraphTranslationEnCountLoad(lifeGraphSetName, latestUpdateDate)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedLifeGraphTranslationEnToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame)
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 03_LifeGraphTranslationEn로 대처됨 ]\n")
        else:
            responseJson = LifeGraphTranslationEnResponseJson(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, messagesReview = MessagesReview, mode = Mode)
            # LifeGraphs를 LifeGraphCount로 슬라이스
            ResponseJson = responseJson[LifeGraphCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'LifeGraphTranslationEnUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'LifeGraphTranslationEnUpdate: {Update["Residence"]} ...')
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

                AddLifeGraphTranslationEnLifeGraphsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, LifeGraphDate, Name, Age, Source, Language, Translation, Residence, PhoneNumber, Email, Quality, LifeData)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            ##### LifeDataTexts 업데이트
            LifeGraphTranslationEnLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson)
            #####
            # Completion "Yes" 업데이트
            LifeGraphTranslationEnCompletionUpdate(lifeGraphSetName, latestUpdateDate)
            
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 03_LifeGraphTranslationEnUpdate 완료 ]\n")
    else:
        print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 03_LifeGraphTranslationEnUpdate는 이미 완료됨 ]\n")
    
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################