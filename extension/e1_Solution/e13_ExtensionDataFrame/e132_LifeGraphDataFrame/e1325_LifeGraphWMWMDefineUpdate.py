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
# from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import AddExistedLifeGraphWMWMDefineToDB, AddLifeGraphWMWMDefineWMWMChunksToDB, AddLifeGraphWMWMDefineLifeDataWMWMTextsToDB, LifeGraphWMWMDefineCountLoad, InitLifeGraphWMWMDefine, LifeGraphWMWMDefineCompletionUpdate, UpdatedLifeGraphWMWMDefine

#########################
##### InputList 생성 #####
#########################
# LifeDataContextTexts 로드
def LoadLifeDataContextTexts(lifeGraphSetName, latestUpdateDate):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeDataContextTexts = lifeGraph.LifeGraphContextDefine[2]['LifeDataContextTexts'][1:]
    
    return LifeDataContextTexts

## LifeGraphFrameTexts의 inputList 치환
def LifeDataContextTextsToInputList(lifeGraphSetName, latestUpdateDate):
    LifeDataContextTexts = LoadLifeDataContextTexts(lifeGraphSetName, latestUpdateDate)   
    
    InputList = []
    for i in range(len(LifeDataContextTexts)):
        Id = LifeDataContextTexts[i]['LifeGraphId']
        Translation = LifeDataContextTexts[i]['Translation']
        Text = LifeDataContextTexts[i]['Text']
        
        if Translation != 'ko':
            Tag = 'Pass'
        else:
            Tag = 'Continue'
            
        InputDic = {'Id': Id, Tag: Text}
        InputList.append(InputDic)
        
    return InputList

######################
##### Filter 조건 #####
######################
## LifeGraphWMWMDefine의 Filter(Error 예외처리)
def LifeGraphWMWMDefineFilter(MemoTag, responseData, memoryCounter):
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
            elif not ('이해상태' in dic[key] and '이해상태선택이유' in dic[key] and '마음상태' in dic[key] and '마음상태선택이유' in dic[key] and '행동상태' in dic[key] and '행동상태선택이유' in dic[key] and '정확도' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        if len(OutputDic) != len(MemoTag):
            return f"JSONCount에서 오류 발생: JSONCountError, OutputDic: {len(OutputDic)}, MemoTag: {len(MemoTag)}"
        
    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def LifeGraphWMWMDefineInputMemory(inputMemoryDics, MemoryLength):
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
def LifeGraphWMWMDefineOutputMemory(outputMemoryDics, MemoryLength):
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
## LifeGraphWMWMDefine 프롬프트 요청 및 결과물 Json화
def LifeGraphWMWMDefineProcess(lifeGraphSetName, latestUpdateDate, Process = "LifeGraphWMWMDefine", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):

    InputList = LifeDataContextTextsToInputList(lifeGraphSetName, latestUpdateDate)
    TotalCount = 0
    ProcessCount = 1
    ContinueCount = 0
    inputMemoryDics = []
    inputMemory = []
    InputDic = InputList[0]
    inputMemoryDics.append(InputDic)
    outputMemoryDics = []
    outputMemory = []
        
    # WMWMDefineProcess
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
            if Mode == "Master" or Mode == "ExampleFineTuning":
                memoTag = re.findall(r'\[중요부분(\d{1,5})\]', str(Input))
            else:
                memoTag = re.findall(r'\[중요부분(\d{1,5})\]', str(InputDic))
            
            MemoTag = ["중요부분" + match for match in memoTag]
            memoryCounter = " - 이어서 작업할 데이터 (갯수만큼만 딱 맞게 작성): " + ', '.join(['[' + tag + ']' for tag in MemoTag]) + ' -\n'
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
         
            Filter = LifeGraphWMWMDefineFilter(MemoTag, responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"LifeGraphSetName: {lifeGraphSetName} | Process: {Process} {ProcessCount}/{len(InputList)} | {Filter}")
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                print(f"LifeGraphSetName: {lifeGraphSetName} | Process: {Process} {ProcessCount}/{len(InputList)} | JSONDecode 완료")
                
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
            inputMemory = LifeGraphWMWMDefineInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = LifeGraphWMWMDefineOutputMemory(outputMemoryDics, MemoryLength)
        
        ########## 테스트 후 삭제 ##########
        LifeGraphFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/23120601_CourseraMeditation_05_outputMemoryDics_231212.json"
        with open(LifeGraphFramePath, 'w', encoding='utf-8') as file:
            json.dump(outputMemoryDics, file, ensure_ascii = False, indent = 4)
        ########## 테스트 후 삭제 ##########
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################

def LifeGraphWMWMDefineResponseJson(lifeGraphSetName, latestUpdateDate, messagesReview = 'off', mode = "Memory"):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    ContextChunks = lifeGraph.LifeGraphContextDefine[1]['ContextChunks'][1:]
    # outputMemoryDics = LifeGraphWMWMDefineProcess(lifeGraphSetName, latestUpdateDate, MessagesReview = messagesReview, Mode = mode)

    ########## 테스트 후 삭제 ##########
    LifeGraphFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/23120601_CourseraMeditation_05_outputMemoryDics_231212.json"
    with open(LifeGraphFramePath, 'r', encoding = 'utf-8') as file:
        outputMemoryDics = json.load(file)
    ########## 테스트 후 삭제 ##########
    
    print(outputMemoryDics[0][0])
    
    responseJson = []
    for i, response in enumerate(outputMemoryDics):
        if response != "Pass":
            LifeGraphId = i + 1
            Translation = ContextChunks[i]['Translation']
            WMWMChunks = []
            for j, Dic in enumerate(response):
                key = list(Dic.keys())[0]
                ChunkId = j + 1
                Chunk = ContextChunks[i]['ContextChunks'][j]['Chunk']
                Wisdom = Dic[key]['이해상태']
                ReasonOfWisdom = Dic[key]['이해상태선택이유']
                Mind = Dic[key]['마음상태']
                ReasonOfMind = Dic[key]['마음상태선택이유']
                Wildness = Dic[key]['행동상태']
                ReasonOfWildness = Dic[key]['행동상태선택이유']
                Accuracy = Dic[key]['정확도']
                WMWMChunk = {'ChunkId': ChunkId, 'Chunk': Chunk, 'Wisdom': Wisdom, 'ReasonOfWisdom': ReasonOfWisdom, 'Mind': Mind, 'ReasonOfMind': ReasonOfMind, 'Wildness': Wildness, 'ReasonOfWildness': ReasonOfWildness, 'Accuracy': Accuracy}
                WMWMChunks.append(WMWMChunk)
            responseJson.append({'LifeGraphId': LifeGraphId, 'Translation': Translation, 'WMWMChunks': WMWMChunks})

    return responseJson

def LifeDataToWMWMQuerys(lifeGraphSetName, latestUpdateDate, ResponseJson):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeDataTextsKo = lifeGraph.LifeGraphTranslationKo[1]['LifeGraphsKo'][1:]

    LifeDataWMWMTexts = []
    for i in range(len(LifeDataTextsKo)):
        LifeGraphDate = LifeDataTextsKo[i]["LifeGraphDate"]
        Name = LifeDataTextsKo[i]["Name"]
        Age = LifeDataTextsKo[i]["Age"]
        Email = LifeDataTextsKo[i]["Email"]
        Language = LifeDataTextsKo[i]["Language"]
        Translation = LifeDataTextsKo[i]["Translation"]
        LifeData = []
        WMWMChunkCount = 0
        for j in range(len(LifeDataTextsKo[i]["LifeData"])):
            
            StartAge = LifeDataTextsKo[i]["LifeData"][j]["StartAge"]
            EndAge = LifeDataTextsKo[i]["LifeData"][j]["EndAge"]
            Score = LifeDataTextsKo[i]["LifeData"][j]["Score"]

            if LifeDataTextsKo[i]["LifeData"][j]["ReasonKo"] == '':
                Reason = '내용없음'
            else:
                Reason = LifeDataTextsKo[i]["LifeData"][j]["ReasonKo"]

            WMWMChunk = ResponseJson[i]['WMWMChunks'][WMWMChunkCount]
            if str(StartAge) == str(WMWMChunk['StartAge']) and str(EndAge) == str(WMWMChunk['EndAge']) and str(Score) == str(WMWMChunk['Score']):
                Purpose = WMWMChunk['Purpose']
                Reason = WMWMChunk['Reason']
                Question = WMWMChunk['Question']
                Writer = WMWMChunk['Writer']
                Subject = WMWMChunk['Subject']
                if WMWMChunkCount < (len(ResponseJson[i]['WMWMChunks']) - 1):
                    WMWMChunkCount += 1

                if j == (len(LifeDataTextsKo[i]["LifeData"]) - 1):
                    Memo = f"[메모{WMWMChunkCount}] {{'목적또는문제': '{Purpose}', '원인': '{Reason}', '예상질문': '{Question}', '인물유형': '{Writer}', '주제': '{Subject}'}}"
                    LifeData.append(f'\n\n[중요문구{WMWMChunkCount}] {StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}\n{Memo}')
                else:
                    Memo = f"[메모{WMWMChunkCount}] {{'목적또는문제': '{Purpose}', '원인': '{Reason}', '예상질문': '{Question}', '인물유형': '{Writer}', '주제': '{Subject}'}}\n"
                    LifeData.append(f'\n[중요문구{WMWMChunkCount}] {StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}\n{Memo}\n')
            else:
                if j == (len(LifeDataTextsKo[i]["LifeData"]) - 1):
                    LifeData.append(f'{StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}')
                else:
                    LifeData.append(f'{StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}\n\n')

        LifeDataText = f"작성일: {LifeGraphDate}\nEmail: {Email}\n\n● '{Name}'의 {Age}세 까지의 인생\n\n" + "".join(LifeData).replace('\n\n\n', '\n\n')
        LifeDataWMWMTexts.append({"Name": Name, "Email": Email, "Language": Language, "Translation": Translation, "Text": LifeDataText})

    return LifeDataWMWMTexts

## LifeDataTexts를 LifeGraphWMWMDefine에 업데이트
def LifeGraphWMWMDefineLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson):
    LifeDataTexts = LifeDataToText(lifeGraphSetName, latestUpdateDate, ResponseJson)
    LifeDataTextsCount = len(LifeDataTexts)
    
    # TQDM 셋팅
    UpdateTQDM = tqdm(LifeDataTexts,
                    total = LifeDataTextsCount,
                    desc = 'LifeGraphWMWMDefineLifeDataTextsUpdate')
    # i값 수동 생성
    i = 0
    for Update in UpdateTQDM:
        UpdateTQDM.set_description(f'LifeGraphWMWMDefineLifeDataTextsUpdate: {Update["Name"]}, {Update["Email"]} ...')
        time.sleep(0.0001)
        LifeGraphId = i + 1
        Text = LifeDataTexts[i]["Text"]
        
        AddLifeGraphWMWMDefineLifeDataWMWMTextsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Text)
        # i값 수동 업데이트
        i += 1

    UpdateTQDM.close()

## 결과물 Json을 LifeGraphWMWMDefine에 업데이트
def LifeGraphWMWMDefineUpdate(lifeGraphSetName, latestUpdateDate, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None):
    print(f"< LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 04_LifeGraphWMWMDefineUpdate 시작 >")
    # LifeGraphWMWMDefine의 Count값 가져오기
    LifeGraphCount, LifeDataTextsCount, Completion = LifeGraphWMWMDefineCountLoad(lifeGraphSetName, latestUpdateDate)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedLifeGraphWMWMDefineToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame)
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 04_LifeGraphWMWMDefine로 대처됨 ]\n")
        else:
            responseJson = LifeGraphWMWMDefineResponseJson(lifeGraphSetName, latestUpdateDate, messagesReview = MessagesReview, mode = Mode)
            # LifeGraphs를 LifeGraphCount로 슬라이스
            ResponseJson = responseJson[LifeGraphCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'LifeGraphWMWMDefineUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'LifeGraphWMWMDefineUpdate: {ResponseJson[i]["WMWMChunks"][0]["Chunk"]} ...')
                time.sleep(0.0001)
                
                LifeGraphId = i + 1
                WMWMChunks = ResponseJson[i]["WMWMChunks"]

                AddLifeGraphWMWMDefineWMWMChunksToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, WMWMChunks)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            ##### LifeDataTexts 업데이트
            LifeGraphWMWMDefineLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson)
            #####
            # Completion "Yes" 업데이트
            LifeGraphWMWMDefineCompletionUpdate(lifeGraphSetName, latestUpdateDate)
            
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 04_LifeGraphWMWMDefineUpdate 완료 ]\n")
    else:
        print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 04_LifeGraphWMWMDefineUpdate는 이미 완료됨 ]\n")
    
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################
    
    responseJson = LifeGraphWMWMDefineResponseJson(lifeGraphSetName, latestUpdateDate)
    
    for response in responseJson:
        print(f'{response}\n\n')