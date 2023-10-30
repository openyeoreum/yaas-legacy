import re
import json
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b23_Project.b231_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import AddExistedSummaryBodyFrameToDB, AddSummaryBodyFrameBodyToDB, SummaryBodyFrameCountLoad, SummaryBodyFrameCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

## BodyFrameBodys 로드
def LoadBodyFrameBodys(projectName, email):
    project = GetProject(projectName, email)
    BodyFrameBodys = project.BodyFrame[2]['Bodys'][1:]
    
    return BodyFrameBodys

## BodyFrameBodys의 InputList 치환
def BodyFrameBodysToInputList(projectName, email, Task = "Body"):
    BodyFrameBodys = LoadBodyFrameBodys(projectName, email, )
    
    InputList = []
    for BodyDic in BodyFrameBodys:
        Id = BodyDic["BodyId"]
        if Task in BodyDic["Task"]:
            Tag = "Continue"
        else:
            Tag = "Pass"
        TaskBody = BodyDic[Task]
        InputDic = {'Id': Id, Tag: TaskBody}
        InputList.append(InputDic)
    
    return InputList

## BodySummary의 Filter(Error 예외처리)
def BodySummaryFilter(InputDic, responseData, memoryCounter):
    # responseData의 전처리
    responseData = responseData.replace("<요약>" + memoryCounter, "").replace("<요약>" + memoryCounter + " ", "")
    responseData = responseData.replace("<요약> 작업 결과:", "").replace("<요약> 작업 결과: ", "")
    responseData = responseData.replace("<요약> 결과:", "").replace("<요약> 결과: ", "")
    responseData = responseData.replace("<요약>", "").replace("<요약> ", "")
    responseData = responseData.replace("\n", "").replace("'", "\"")
    responseData = re.sub(r'^\[', '', responseData) # 시작과 끝에 있는 대괄호[,]를 제거
    responseData = re.sub(r'\]$', '', responseData) # 시작과 끝에 있는 대괄호[,]를 제거
    # # 문장 생성을 위한 str의 json 형식 전처리
    # responseData = responseData.replace("'", '"')
    # quote_indices = [i for i, char in enumerate(responseData) if char == '"']
    # for index in quote_indices[5:-1]:
    #     responseData = responseData[:index] + '\"' + responseData[index+1:]
        
    print(f'\n\n@@@@@@@@@@@@@@@\n\n{responseData}\n\n@@@@@@@@@@@@@@@\n\n')
    
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        OutputDic = json.loads(responseData)
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: Id와 Summary 키가 존재하지 않을 때의 예외 처리
    if not {"Id", "Summary"}.issubset(OutputDic.keys()):
        return "JSON에서 오류 발생: JSONKeyError"
    # # Error3: SummaryBody길이가 길때의 예외 처리
    # if not (
    #     len(InputDic.get("Continue")) > len(OutputDic.get('Summary')) and
    #     InputDic.get('Id') == OutputDic.get('Id')
    # ):
    #     return "SummaryBody길이 오류 발생: SummaryBodyLengthError"
    # Error4: Input과 Output의 Id가 다를 때의 예외처리
    if InputDic["Id"] != OutputDic["Id"]:
        return "JSONId에서 오류 발생: JSONIdError"
    return OutputDic

## inputMemory 형성
def BodySummaryInputMemory(inputMemoryDics, MemoryLength):
    
    inputMemoryDic = []
    continueCount = 0
    for entry in reversed(inputMemoryDics):
        if continueCount == MemoryLength + 1:
            break
        else:
            if "Continue" in entry:
                continueCount += 1
                inputMemoryDic.append(entry)
            else:
                inputMemoryDic.append(entry)
    inputMemoryDic = list(reversed(inputMemoryDic))
    inputMemory = str(inputMemoryDic)
    
    return inputMemory

## outputMemory 형성
def BodySummaryOutputMemory(outputMemoryDics, MemoryLength):

    outputMemoryDic = []
    continueCount = 0
    for entry in reversed(outputMemoryDics):
        if continueCount == MemoryLength:
            break
        else:
            if "Summary" in entry:
                continueCount += 1
                outputMemoryDic.append(entry)
            else:
                outputMemoryDic.append(entry)
    outputMemoryDic = list(reversed(outputMemoryDic))
    outputMemory = str(outputMemoryDic)
    outputMemory = outputMemory[:-1] + ", "
    outputMemory = outputMemory.replace("[, ", "[")
    
    return outputMemory

## BodySummary 프롬프트 요청 및 결과물 Json화
def BodySummaryProcess(projectName, email, Process = "BodySummary", memoryLength = 2, MessagesReview = "off", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)
    
    InputList = BodyFrameBodysToInputList(projectName, email)
    TotalCount = 0
    ContinueCount = 0
    inputMemoryDics = []
    InputDic = InputList[0]
    inputMemoryDics.append(InputDic)
    outputMemoryDics = []
        
    # BodySummaryProcess
    while TotalCount < len(InputList):
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
                FineTuningMemoryDic = InputList[TotalCount - 1]
                keys = list(FineTuningMemoryDic.keys())
                FineTuningMemory = FineTuningMemoryDic[keys[1]]
            else:
                mode = "MemoryFineTuning"
        elif Mode == "ExampleFineTuning" and TotalCount > 0:
            mode = "ExampleFineTuning"
            FineTuningMemoryDic = InputList[TotalCount - 1]
            keys = list(FineTuningMemoryDic.keys())
            FineTuningMemory = FineTuningMemoryDic[keys[1]]
        else:
            mode = "Example"

        if "Continue" in InputDic:
            if Mode == "ExampleFineTuning":
                Input = FineTuningMemory + str(InputDic)
            else:
                Input = str(InputDic)

            # Filter, MemoryCounter, OutputEnder 처리
            inputDicId = str(InputDic["Id"])
            memoryCounter = " - 이어서 작업할 나머지 부분 Id: " + inputDicId + ", 형식을 꼭 유지합니다! -\n"
            # memoryCounter = ""
            outputEnder = ""
            
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
            
            Filter = BodySummaryFilter(InputDic, responseData, memoryCounter)
            
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
            AddProjectRawDatasetToDB(projectName, email, Process, Model, Usage, InputDic, OutputDic)
            AddProjectFeedbackDataSetsToDB(projectName, email, Process, InputDic, OutputDic)
            
        else:
            OutputDic = InputDic
        
        # Memory 형성
        MemoryLength = memoryLength
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = BodySummaryOutputMemory(outputMemoryDics, MemoryLength)
        
        TotalCount += 1
        ProcessCount = TotalCount + 1
        
        # inputMemory 형성
        try:
            InputDic = InputList[TotalCount]
            inputMemoryDics.append(InputDic)
            inputMemory = BodySummaryInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
    return outputMemoryDics

## 데이터 치환
def BodySummaryResponseJson(projectName, email, messagesReview = "off", mode = "Memory"):
    outputMemoryDics = BodySummaryProcess(projectName, email, MessagesReview = messagesReview, Mode = mode)

    responseJson = []
    for response in outputMemoryDics:
        BodyId = response["Id"]
        if "Index" in response:
            Summary = "No"
            BodySummaryScript = response["Index"]
        elif "Summary" in response:
            Summary = "Yes"
            BodySummaryScript = response["Summary"]
        responseJson.append({"BodyId": BodyId, "Summary": Summary, "BodySummaryScript": BodySummaryScript})
    
    return responseJson

## 프롬프트 요청 및 결과물 Json을 IndexFrame에 업데이트
def SummaryBodyFrameUpdate(projectName, email, MessagesReview = 'off', Mode = "Memory", ExistedFrame = None):
    print(f"< User: {email} | Project: {projectName} | 03_SummaryBodyFrameUpdate 시작 >")
    # SummaryBodyFrame의 Count값 가져오기
    ContinueCount, Completion = SummaryBodyFrameCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedSummaryBodyFrameToDB(projectName, email, ExistedFrame)
            print(f"[ User: {email} | Project: {projectName} | 03_SummaryBodyFrameUpdate는 ExistedSummaryBodyFrame으로 대처됨 ]\n")
        else:
            responseJson = BodySummaryResponseJson(projectName, email, messagesReview = MessagesReview, mode = Mode)
                
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            BodyId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'SummaryBodyFrameUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'SummaryBodyFrameUpdate: {Update}')
                time.sleep(0.0001)
                BodyId += 1
                Summary = ResponseJson[i]["Summary"]
                BodySummaryScript = ResponseJson[i]["BodySummaryScript"]
                
                AddSummaryBodyFrameBodyToDB(projectName, email, BodyId, Summary, BodySummaryScript)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            SummaryBodyFrameCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 03_SummaryBodyFrameUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 03_SummaryBodyFrameUpdate는 이미 완료됨 ]\n")
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    DataFramePath = "/yaas/backend/b5_Database/b50_DatabaseTest/b53_ProjectDataTest/"
    DataSetPath = "/yaas/backend/b5_Database/b50_DatabaseTest/b55_TrainingDataTest/"
    messagesReview = "on"
    mode = "Memory"
    #########################################################################
    
    # SummaryBodyFrameUpdate(projectName, email, MessagesReview = messagesReview, Mode = mode)
    print(BodyFrameBodysToInputList(projectName, email)[:4])