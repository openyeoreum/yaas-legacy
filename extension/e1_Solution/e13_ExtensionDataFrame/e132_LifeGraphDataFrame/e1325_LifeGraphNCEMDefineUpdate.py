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
# from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import AddExistedLifeGraphNCEMDefineToDB, AddLifeGraphNCEMDefineNCEMChunksToDB, AddLifeGraphNCEMDefineLifeDataNCEMTextsToDB, LifeGraphNCEMDefineCountLoad, InitLifeGraphNCEMDefine, LifeGraphNCEMDefineCompletionUpdate, UpdatedLifeGraphNCEMDefine

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
## LifeGraphNCEMDefine의 Filter(Error 예외처리)
def LifeGraphNCEMDefineFilter(Input, responseData, memoryCounter):
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
    INPUT = re.sub("[^가-힣]", "", str(Input))
    for dic in OutputDic:
        try:
            key = list(dic.keys())[0]
            # '핵심문구' 키에 접근하는 부분에 예외 처리 추가
            try:
                OUTPUT = re.sub("[^가-힣]", "", str(dic[key]['이유']))
            except TypeError:
                return "JSON에서 오류 발생: TypeError"
            except KeyError:
                return "JSON에서 오류 발생: KeyError"
            if not '중요부분' in key:
                return "JSON에서 오류 발생: JSONKeyError"
            elif not OUTPUT in INPUT:
                return f"JSON에서 오류 발생: JSON '이유'가 Input에 포함되지 않음 Error\n문구: {dic[key]['이유']}"
            elif not ('욕구상태' in dic[key] and '욕구상태선택이유' in dic[key] and '이해상태' in dic[key] and '이해상태선택이유' in dic[key] and '마음상태' in dic[key] and '마음상태선택이유' in dic[key] and '정확도' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        
    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def LifeGraphNCEMDefineInputMemory(inputMemoryDics, MemoryLength):
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
def LifeGraphNCEMDefineOutputMemory(outputMemoryDics, MemoryLength):
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
## LifeGraphNCEMDefine 프롬프트 요청 및 결과물 Json화
def LifeGraphNCEMDefineProcess(lifeGraphSetName, latestUpdateDate, Process = "LifeGraphNCEMDefine", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):

    InputList = LifeDataTextsKoToInputList(lifeGraphSetName, latestUpdateDate)
    TotalCount = 0
    ProcessCount = 1
    ContinueCount = 0
    inputMemoryDics = []
    inputMemory = []
    InputDic = InputList[0]
    inputMemoryDics.append(InputDic)
    outputMemoryDics = []
    outputMemory = []
        
    # NCEMDefineProcess
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
         
            Filter = LifeGraphNCEMDefineFilter(Input, responseData, memoryCounter)
            
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
            inputMemory = LifeGraphNCEMDefineInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = LifeGraphNCEMDefineOutputMemory(outputMemoryDics, MemoryLength)
        
        # ########## 테스트 후 삭제 ##########
        # LifeGraphFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/23120601_CourseraMeditation_04_outputMemoryDics_231211.json"
        # with open(LifeGraphFramePath, 'w', encoding='utf-8') as file:
        #     json.dump(outputMemoryDics, file, ensure_ascii = False, indent = 4)
        # ########## 테스트 후 삭제 ##########
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################

def LifeGraphNCEMDefineResponseJson(lifeGraphSetName, latestUpdateDate, messagesReview = 'off', mode = "Memory"):
    # outputMemoryDics = LifeGraphNCEMDefineProcess(lifeGraphSetName, latestUpdateDate, MessagesReview = messagesReview, Mode = mode)

    ########## 테스트 후 삭제 ##########
    LifeGraphFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/23120601_CourseraMeditation_04_outputMemoryDics_231211.json"
    with open(LifeGraphFramePath, 'r', encoding = 'utf-8') as file:
        outputMemoryDics = json.load(file)
    ########## 테스트 후 삭제 ##########
    
    responseJson = []
    for i, response in enumerate(outputMemoryDics):
        if response != "Pass":
            LifeGraphId = i + 1
            NCEMChunks = []
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
                NCEMChunk = {'ChunkId': ChunkId, 'StartAge': StartAge, 'EndAge': EndAge, 'Score': Score, 'Chunk': Chunk, 'Purpose': Purpose, 'Reason': Reason, 'Question': Question, 'Writer': Writer, 'Subject': Subject, 'Accuracy': Accuracy}
                NCEMChunks.append(NCEMChunk)
            responseJson.append({'LifeGraphId': LifeGraphId, 'NCEMChunks': NCEMChunks})

    return responseJson

def LifeDataToText(lifeGraphSetName, latestUpdateDate, ResponseJson):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeDataTextsKo = lifeGraph.LifeGraphTranslationKo[1]['LifeGraphsKo'][1:]

    LifeDataNCEMTexts = []
    for i in range(len(LifeDataTextsKo)):
        LifeGraphDate = LifeDataTextsKo[i]["LifeGraphDate"]
        Name = LifeDataTextsKo[i]["Name"]
        Age = LifeDataTextsKo[i]["Age"]
        Email = LifeDataTextsKo[i]["Email"]
        Language = LifeDataTextsKo[i]["Language"]
        Translation = LifeDataTextsKo[i]["Translation"]
        LifeData = []
        NCEMChunkCount = 0
        for j in range(len(LifeDataTextsKo[i]["LifeData"])):
            
            StartAge = LifeDataTextsKo[i]["LifeData"][j]["StartAge"]
            EndAge = LifeDataTextsKo[i]["LifeData"][j]["EndAge"]
            Score = LifeDataTextsKo[i]["LifeData"][j]["Score"]

            if LifeDataTextsKo[i]["LifeData"][j]["ReasonKo"] == '':
                Reason = '내용없음'
            else:
                Reason = LifeDataTextsKo[i]["LifeData"][j]["ReasonKo"]

            NCEMChunk = ResponseJson[i]['NCEMChunks'][NCEMChunkCount]
            if str(StartAge) == str(NCEMChunk['StartAge']) and str(EndAge) == str(NCEMChunk['EndAge']) and str(Score) == str(NCEMChunk['Score']):
                Purpose = NCEMChunk['Purpose']
                Reason = NCEMChunk['Reason']
                Question = NCEMChunk['Question']
                Writer = NCEMChunk['Writer']
                Subject = NCEMChunk['Subject']
                if NCEMChunkCount < (len(ResponseJson[i]['NCEMChunks']) - 1):
                    NCEMChunkCount += 1

                if j == (len(LifeDataTextsKo[i]["LifeData"]) - 1):
                    Memo = f"[메모{NCEMChunkCount}] {{'목적또는문제': '{Purpose}', '원인': '{Reason}', '예상질문': '{Question}', '인물유형': '{Writer}', '주제': '{Subject}'}}"
                    LifeData.append(f'\n\n[중요문구{NCEMChunkCount}] {StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}\n{Memo}')
                else:
                    Memo = f"[메모{NCEMChunkCount}] {{'목적또는문제': '{Purpose}', '원인': '{Reason}', '예상질문': '{Question}', '인물유형': '{Writer}', '주제': '{Subject}'}}\n"
                    LifeData.append(f'\n[중요문구{NCEMChunkCount}] {StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}\n{Memo}\n')
            else:
                if j == (len(LifeDataTextsKo[i]["LifeData"]) - 1):
                    LifeData.append(f'{StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}')
                else:
                    LifeData.append(f'{StartAge}-{EndAge} 시기의 행복지수: {Score}, 이유: {Reason}\n\n')

        LifeDataText = f"작성일: {LifeGraphDate}\nEmail: {Email}\n\n● '{Name}'의 {Age}세 까지의 인생\n\n" + "".join(LifeData).replace('\n\n\n', '\n\n')
        LifeDataNCEMTexts.append({"Name": Name, "Email": Email, "Language": Language, "Translation": Translation, "Text": LifeDataText})

    return LifeDataNCEMTexts

## LifeDataTexts를 LifeGraphNCEMDefine에 업데이트
def LifeGraphNCEMDefineLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson):
    LifeDataTexts = LifeDataToText(lifeGraphSetName, latestUpdateDate, ResponseJson)
    LifeDataTextsCount = len(LifeDataTexts)
    
    # TQDM 셋팅
    UpdateTQDM = tqdm(LifeDataTexts,
                    total = LifeDataTextsCount,
                    desc = 'LifeGraphNCEMDefineLifeDataTextsUpdate')
    # i값 수동 생성
    i = 0
    for Update in UpdateTQDM:
        UpdateTQDM.set_description(f'LifeGraphNCEMDefineLifeDataTextsUpdate: {Update["Name"]}, {Update["Email"]} ...')
        time.sleep(0.0001)
        LifeGraphId = i + 1
        Text = LifeDataTexts[i]["Text"]
        
        AddLifeGraphNCEMDefineLifeDataNCEMTextsToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, Text)
        # i값 수동 업데이트
        i += 1

    UpdateTQDM.close()

## 결과물 Json을 LifeGraphNCEMDefine에 업데이트
def LifeGraphNCEMDefineUpdate(lifeGraphSetName, latestUpdateDate, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None):
    print(f"< LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 04_LifeGraphNCEMDefineUpdate 시작 >")
    # LifeGraphNCEMDefine의 Count값 가져오기
    LifeGraphCount, LifeDataTextsCount, Completion = LifeGraphNCEMDefineCountLoad(lifeGraphSetName, latestUpdateDate)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedLifeGraphNCEMDefineToDB(lifeGraphSetName, latestUpdateDate, ExistedDataFrame)
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 04_LifeGraphNCEMDefine로 대처됨 ]\n")
        else:
            responseJson = LifeGraphNCEMDefineResponseJson(lifeGraphSetName, latestUpdateDate, messagesReview = MessagesReview, mode = Mode)
            # LifeGraphs를 LifeGraphCount로 슬라이스
            ResponseJson = responseJson[LifeGraphCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'LifeGraphNCEMDefineUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'LifeGraphNCEMDefineUpdate: {ResponseJson[i]["NCEMChunks"][0]["Chunk"]} ...')
                time.sleep(0.0001)
                
                LifeGraphId = i + 1
                NCEMChunks = ResponseJson[i]["NCEMChunks"]

                AddLifeGraphNCEMDefineNCEMChunksToDB(lifeGraphSetName, latestUpdateDate, LifeGraphId, NCEMChunks)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            ##### LifeDataTexts 업데이트
            LifeGraphNCEMDefineLifeDataTextsUpdate(lifeGraphSetName, latestUpdateDate, ResponseJson)
            #####
            # Completion "Yes" 업데이트
            LifeGraphNCEMDefineCompletionUpdate(lifeGraphSetName, latestUpdateDate)
            
            print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 04_LifeGraphNCEMDefineUpdate 완료 ]\n")
    else:
        print(f"[ LifeGraphSetName: {lifeGraphSetName} | LatestUpdateDate: {latestUpdateDate} | 04_LifeGraphNCEMDefineUpdate는 이미 완료됨 ]\n")
    
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################
    
    LifeDataContextTexts = LifeDataContextTextsToInputList(lifeGraphSetName, latestUpdateDate)
    

    print(f'{LifeDataContextTexts[0]}')