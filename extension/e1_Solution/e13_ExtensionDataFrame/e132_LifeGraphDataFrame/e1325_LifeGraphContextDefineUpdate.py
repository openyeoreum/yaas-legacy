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
from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import LoadExtensionOutputMemory, SaveExtensionOutputMemory, AddExistedLifeGraphContextDefineToDB, AddLifeGraphContextDefineContextChunksToDB, AddLifeGraphContextDefineLifeDataContextTextsToDB, LifeGraphContextDefineCountLoad, InitLifeGraphContextDefine, LifeGraphContextDefineCompletionUpdate, UpdatedLifeGraphContextDefine

#########################
##### InputList 생성 #####
#########################
# LifeGraphTranslationKo 로드
def LoadLifeDataTextsKo(lifeGraphSetName, latestUpdateDate):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeDataTextsKo = lifeGraph.LifeGraphTranslationKo[2]['LifeDataTextsKo'][1:]
    
    return LifeDataTextsKo

## LifeGraphFrameTexts의 inputList 치환
def LifeDataTextsKoToInputList(lifeGraphSetName, latestUpdateDate):
    LoadLifeDataTextsko = LoadLifeDataTextsKo(lifeGraphSetName, latestUpdateDate)
    
    InputList = []
    for i in range(len(LoadLifeDataTextsko)):
        Id = LoadLifeDataTextsko[i]['LifeGraphId']
        Translation = LoadLifeDataTextsko[i]['Translation']
        TextKo = LoadLifeDataTextsko[i]['TextKo']

        if Translation != 'ko':
            Tag = 'Pass'
        else:
            Tag = 'Continue'
            
        InputDic = {'Id': Id, Tag: TextKo}
        InputList.append(InputDic)
        
    return InputList

######################
##### Filter 조건 #####
######################
## LifeGraphContextDefine의 Filter(Error 예외처리)
def LifeGraphContextDefineFilter(responseData, memoryCounter):
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
            # '핵심문구' 키에 접근하는 부분에 예외 처리 추가
            if not '중요부분' in key:
                return "JSON에서 오류 발생: JSONKeyError"
            elif not ('시기' in dic[key] and '행복지수' in dic[key] and '이유' in dic[key] and '목적또는문제' in dic[key] and '원인' in dic[key] and '예상질문' in dic[key] and '인물유형' in dic[key] and '주제' in dic[key] and '정확도' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        
    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def LifeGraphContextDefineInputMemory(inputMemoryDics, MemoryLength):
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
def LifeGraphContextDefineOutputMemory(outputMemoryDics, MemoryLength):
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
## LifeGraphContextDefine 프롬프트 요청 및 결과물 Json화
def LifeGraphContextDefineProcess(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, Process = "LifeGraphContextDefine", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):

    OutputMemoryDicsFile, OutputMemoryCount = LoadExtensionOutputMemory(lifeGraphSetName, latestUpdateDate, '05', LifeGraphDataFramePath)    
    inputList = LifeDataTextsKoToInputList(lifeGraphSetName, latestUpdateDate)
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
            outputEnder = f"{{'중요부분"
            
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
         
            Filter = LifeGraphContextDefineFilter(responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"LifeGraphSetName: {lifeGraphSetName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                
                ErrorCount += 1
                if ErrorCount == 5:
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
            inputMemory = LifeGraphContextDefineInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = LifeGraphContextDefineOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveExtensionOutputMemory(lifeGraphSetName, latestUpdateDate, outputMemoryDics, '05', LifeGraphDataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################

def LifeGraphContextDefineResponseJson(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, messagesReview = 'off', mode = "Memory"):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphsKo = lifeGraph.LifeGraphTranslationKo[1]['LifeGraphsKo'][1:]
    outputMemoryDics = LifeGraphContextDefineProcess(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    for i, response in enumerate(outputMemoryDics):
        if response != "Pass":
            LifeGraphId = i + 1
            Translation = LifeGraphsKo[i]['Translation']
            ContextChunks = []
            for j, Dic in enumerate(response):
                key = list(Dic.keys())[0]
                ChunkId = j + 1
                Ages = Dic[key]['시기'].split('-')
                StartAge = int(Ages[0])
                EndAge = int(Ages[-1])
                Score = Dic[key]['행복지수']
                Chunk = Dic[key]['이유']
                Purpose = Dic[key]['목적또는문제']
                Reason = Dic[key]['원인']
                Question = Dic[key]['예상질문']
                Writer = Dic[key]['인물유형']
                Subject = Dic[key]['주제']
                Accuracy = Dic[key]['정확도']
                ContextChunk = {'ChunkId': ChunkId, 'StartAge': StartAge, 'EndAge': EndAge, 'Score': Score, 'Chunk': Chunk, 'Purpose': Purpose, 'Reason': Reason, 'Question': Question, 'Writer': Writer, 'Subject': Subject, 'Accuracy': Accuracy}
                ContextChunks.append(ContextChunk)
        else:
            LifeGraphId = i + 1
            Translation = LifeGraphsKo[i]['Translation']
            ChunkId = 0
            StartAge = 0
            EndAge = 0
            Score = 0
            Chunk = "None"
            Purpose = "None"
            Reason = "None"
            Question = "None"
            Writer = "None"
            Subject = "None"
            Accuracy = 0
            ContextChunks = [{'ChunkId': ChunkId, 'StartAge': StartAge, 'EndAge': EndAge, 'Score': Score, 'Chunk': Chunk, 'Purpose': Purpose, 'Reason': Reason, 'Question': Question, 'Writer': Writer, 'Subject': Subject, 'Accuracy': Accuracy}]
        responseJson.append({'LifeGraphId': LifeGraphId, 'Translation': Translation, 'ContextChunks': ContextChunks})

    return responseJson

def LifeDataToText(lifeGraphSetName, latestUpdateDate, ResponseJson):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeDataTextsKo = lifeGraph.LifeGraphTranslationKo[1]['LifeGraphsKo'][1:]

    LifeDataContextTexts = []
    for i in range(len(LifeDataTextsKo)):
        LifeGraphDate = LifeDataTextsKo[i]["LifeGraphDate"]
        Name = LifeDataTextsKo[i]["Name"]
        Age = LifeDataTextsKo[i]["Age"]
        Email = LifeDataTextsKo[i]["Email"]
        Language = LifeDataTextsKo[i]["Language"]
        Translation = LifeDataTextsKo[i]["Translation"]
        LifeData = []
        ContextChunkCount = 0
        MemoCount = 0
        for j in range(len(LifeDataTextsKo[i]["LifeData"])):
            
            StartAge = LifeDataTextsKo[i]["LifeData"][j]["StartAge"]
            EndAge = LifeDataTextsKo[i]["LifeData"][j]["EndAge"]
            Score = LifeDataTextsKo[i]["LifeData"][j]["Score"]

            if LifeDataTextsKo[i]["LifeData"][j]["ReasonKo"] == '':
                Reason = '내용없음'
            else:
                Reason = LifeDataTextsKo[i]["LifeData"][j]["ReasonKo"]
            try:
                ContextChunk = ResponseJson[i]['ContextChunks'][ContextChunkCount]
            except:
                print(ResponseJson[i])
            if str(StartAge) == str(ContextChunk['StartAge']) and str(EndAge) == str(ContextChunk['EndAge']) and str(Score) == str(ContextChunk['Score']):
                Purpose = ContextChunk['Purpose']
                Reason = ContextChunk['Reason']
                # Question = ContextChunk['Question']
                Writer = ContextChunk['Writer']
                Subject = ContextChunk['Subject']
                
                if ContextChunkCount < (len(ResponseJson[i]['ContextChunks']) - 1):
                    ContextChunkCount += 1
                
                MemoCount += 1

                if j == (len(LifeDataTextsKo[i]["LifeData"]) - 1):
                    Memo = f"[메모{MemoCount}] {{'목적또는문제': '{Purpose}', '원인': '{Reason}', '인물유형': '{Writer}', '주제': '{Subject}'}}"
                    LifeData.append(f'\n\n[중요부분{MemoCount}] {StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}\n{Memo}')
                else:
                    Memo = f"[메모{MemoCount}] {{'목적또는문제': '{Purpose}', '원인': '{Reason}', '인물유형': '{Writer}', '주제': '{Subject}'}}\n"
                    LifeData.append(f'\n[중요부분{MemoCount}] {StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}\n{Memo}\n')
            else:
                if j == (len(LifeDataTextsKo[i]["LifeData"]) - 1):
                    LifeData.append(f'{StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}')
                else:
                    LifeData.append(f'{StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}\n\n')

        LifeDataText = f"작성일: {LifeGraphDate}\nEmail: {Email}\n\n● '{Name}'의 {Age}세 까지의 인생\n\n" + "".join(LifeData).replace('\n\n\n', '\n\n')
        LifeDataContextTexts.append({"Name": Name, "Email": Email, "Language": Language, "Translation": Translation, "Text": LifeDataText})

    return LifeDataContextTexts

## LifeDataTexts를 LifeGraphContextDefine에 업데이트
def LifeGraphContextDefineLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson):
    LifeDataTexts = LifeDataToText(lifeGraphSetName, latestUpdateDate, ResponseJson)
    LifeDataTextsCount = len(LifeDataTexts)
    
    # TQDM 셋팅
    UpdateTQDM = tqdm(LifeDataTexts,
                    total = LifeDataTextsCount,
                    desc = 'LifeGraphContextDefineLifeDataTextsUpdate')
    # i값 수동 생성
    i = 0
    for Update in UpdateTQDM:
        UpdateTQDM.set_description(f'LifeGraphContextDefineLifeDataTextsUpdate: {Update["Name"]}, {Update["Email"]} ...')
        time.sleep(0.0001)
        LifeGraphId = i + 1
        Translation = Update["Translation"]
        Text = Update["Text"]
        
        AddLifeGraphContextDefineLifeDataContextTextsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Translation, Text)
        # i값 수동 업데이트
        i += 1

    UpdateTQDM.close()

## 결과물 Json을 LifeGraphContextDefine에 업데이트
def LifeGraphContextDefineUpdate(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None):
    print(f"< LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 05_LifeGraphContextDefineUpdate 시작 >")
    # LifeGraphContextDefine의 Count값 가져오기
    LifeGraphCount, LifeDataTextsCount, Completion = LifeGraphContextDefineCountLoad(lifeGraphSetName, latestUpdateDate)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedLifeGraphContextDefineToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame)
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 05_LifeGraphContextDefine로 대처됨 ]\n")
        else:
            responseJson = LifeGraphContextDefineResponseJson(lifeGraphSetName, latestUpdateDate, LifeGraphDataFramePath, messagesReview = MessagesReview, mode = Mode)
            # LifeGraphs를 LifeGraphCount로 슬라이스
            ResponseJson = responseJson[LifeGraphCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'LifeGraphContextDefineUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'LifeGraphContextDefineUpdate: {ResponseJson[i]["ContextChunks"][0]["Chunk"]} ...')
                time.sleep(0.0001)
                
                LifeGraphId = i + 1
                Translation = Update["Translation"]
                ContextChunks = Update["ContextChunks"]

                AddLifeGraphContextDefineContextChunksToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Translation, ContextChunks)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            ##### LifeDataTexts 업데이트
            LifeGraphContextDefineLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson)
            #####
            # Completion "Yes" 업데이트
            LifeGraphContextDefineCompletionUpdate(lifeGraphSetName, latestUpdateDate)
            
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 05_LifeGraphContextDefineUpdate 완료 ]\n")
    else:
        print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 05_LifeGraphContextDefineUpdate는 이미 완료됨 ]\n")
    
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################