import os
import re
import json
import time
import ast
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from collections import Counter
from agent.a2_Solution.a21_General.a214_GetProcessData import GetProject, GetPromptFrame
from agent.a2_Solution.a25_DataFrame.a251_DataCommit.a2511_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from agent.a2_Solution.a25_DataFrame.a251_DataCommit.a2512_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedWMWMMatchingToDB, AddWMWMMatchingChunksToDB, AddWMWMMatchingBODYsToDB, AddWMWMMatchingIndexsToDB, AddWMWMMatchingBookToDB, WMWMMatchingCountLoad, WMWMMatchingCompletionUpdate
from agent.a2_Solution.a25_DataFrame.a251_DataCommit.a2513_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
## ContextFrame 로드
def LoadContextCompletions(projectName, email):
    project = GetProject(projectName, email)
    HalfBodyFrameSplitedBodyScripts = project["HalfBodyFrame"][1]['SplitedBodyScripts'][1:]
    ContextChunks = project["ContextDefine"][1]['ContextChunks'][1:]
    ContextCompletions = project["ContextCompletion"][1]['ContextCompletions'][1:]
    WMWMCompletions =  project["WMWMDefine"][1]['WMWMCompletions'][1:]
    
    return HalfBodyFrameSplitedBodyScripts, ContextChunks, ContextCompletions, WMWMCompletions

## BodyFrameBodys의 inputList 치환
def ContextToText(Id, BookTitle, Index, Chunk, ContextDefine, ContextCompletion, WMWM):
    
    Scores = {
    "생리": 1, "안전": 2, "애정": 3, "존경": 4, "자아실현": 5,
    "무지": 1, "인지": 2, "이해": 3, "확신": 4, "지혜": 5,
    "거절": 1, "부정": 2, "중립": 3, "긍정": 4, "수용": 5,
    "소극": 1, "수동": 2, "능동": 3, "적극": 4, "성공": 5
    }
    
    Purpose = ContextDefine['Purpose']
    Reason = ContextDefine['Reason']
    Question = ContextDefine['Question']
    Subject = ContextDefine['Subject']
    Reader = ContextDefine['Reader']
    
    Genre = ContextCompletion['Genre']
    Gender = ContextCompletion['Gender']
    Age = ContextCompletion['Age']
    Personality = ContextCompletion['Personality']
    Emotion = ContextCompletion['Emotion']
    
    Needs = WMWM['Needs']
    ReasonOfNeeds = WMWM['ReasonOfNeeds']
    Wisdom = WMWM['Wisdom']
    ReasonOfWisdom = WMWM['ReasonOfWisdom']
    Mind = WMWM['Mind']
    ReasonOfPotentialMind = WMWM['ReasonOfPotentialMind']
    Wildness = WMWM['Wildness']
    ReasonOfWildness = WMWM['ReasonOfWildness']

    if not isinstance(Needs, (int, float, complex)):
        # print(Scores)
        # print(Purpose)
        # print(Needs)
        NeedsScore = Scores.get(Needs, 0)
    else:
        NeedsScore = Needs
        
    if not isinstance(Wisdom, (int, float, complex)):
        WisdomScore = Scores.get(Wisdom, 0)
    else:
        WisdomScore = Wisdom
        
    if not isinstance(Mind, (int, float, complex)):
        MindScore = Scores.get(Mind, 0)
    else:
        MindScore = Mind
        
    if not isinstance(Wildness, (int, float, complex)):
        WildnessScore = Scores.get(Wildness, 0)
    else:
        WildnessScore = Wildness
    
    ContextText = f"○ {Id}번째 토론: '{Chunk}' {BookTitle} 중에서\n\n- 토론 도서 -\n\n도서명: {BookTitle}\n목차: {Index}\n장르: {Genre}\n성별: {Gender}\n연령: {Age}\n성향: {Personality}\n감성: {Emotion}\n\n- 토론의 내용 -\n\n문구: {Chunk}\n대상독자: {Reader}\n주제: {Subject}\n목적: {Purpose}\n이유: {Reason}\n대표질문: {Question}\n\n- 토론의 유익성 -\n\n필요성: {NeedsScore}\n필요성 배점 이유: {ReasonOfNeeds}\n지식적 유익성: {WisdomScore}\n지식적 유익성 배점 이유: {ReasonOfWisdom}\n마음가짐의 유익성: {MindScore}\n마음가짐의 유익성 배점 이유: {ReasonOfPotentialMind}\n실천의 유익성: {WildnessScore}\n실천의 유익성 배점 이유: {ReasonOfWildness}\n\n\n"
    
    return ContextText
    
def ContextCompletionsToInputList(projectName, email):
    HalfBodyFrameSplitedBodyScripts, ContextChunks, ContextCompletions, WMWMCompletions = LoadContextCompletions(projectName, email)

    BookTitle = HalfBodyFrameSplitedBodyScripts[0]['Index']
    SplitedContexts = []
    SplitedChunkContexts = []
    SplitedBodyTexts = []
    ContextChunksCount = 0
    for i in range(len(HalfBodyFrameSplitedBodyScripts)):
        SplitedBodyScripts = HalfBodyFrameSplitedBodyScripts[i]
        IndexId = SplitedBodyScripts['IndexId']
        IndexTag = SplitedBodyScripts['IndexTag']
        Index = SplitedBodyScripts['Index']
        BodyId = SplitedBodyScripts['BodyId']
        SplitedBodyChunks = SplitedBodyScripts['SplitedBodyChunks']
        SplitedBodyContextsList = []
        SplitedBodyContextsText = []
        for j in range(len(SplitedBodyChunks)):
            FrameChunkId = SplitedBodyChunks[j]['ChunkId']
            ContextCounkId = ContextChunks[ContextChunksCount]['ChunkId']
            if isinstance(ContextCounkId, list):
                ContextCounkIdList = ContextCounkId
            else:
                ContextCounkIdList = [ContextCounkId]
            if FrameChunkId in ContextCounkIdList:
                # print(FrameChunkId)
                # print(ContextCounkIdList)
                ChunkId = ContextCounkId
                Chunk = ContextChunks[ContextChunksCount]['Chunk']
                
                Purpose = ContextChunks[ContextChunksCount]['Purpose']
                Reason = ContextChunks[ContextChunksCount]['Reason']
                Question = ContextChunks[ContextChunksCount]['Question']
                Subject = ContextChunks[ContextChunksCount]['Subject']
                Reader = ContextChunks[ContextChunksCount]['Reader']
                Importance = ContextChunks[ContextChunksCount]['Importance']
                ContextDefine = {"Purpose": Purpose, "Reason": Reason, "Question": Question, "Subject": Subject, "Reader": Reader, "Importance": Importance}
                
                Genre = ContextCompletions[ContextChunksCount]['Genre']
                Gender = ContextCompletions[ContextChunksCount]['Gender']
                Age = ContextCompletions[ContextChunksCount]['Age']
                Personality = ContextCompletions[ContextChunksCount]['Personality']
                Emotion = ContextCompletions[ContextChunksCount]['Emotion']
                Accuracy = ContextCompletions[ContextChunksCount]['Accuracy']
                ContextCompletion = {"Genre": Genre, "Gender": Gender, "Age": Age, "Personality": Personality, "Emotion": Emotion, "Accuracy": Accuracy}
                
                Needs = WMWMCompletions[ContextChunksCount]['Needs']
                ReasonOfNeeds = WMWMCompletions[ContextChunksCount]['ReasonOfNeeds']
                Wisdom = WMWMCompletions[ContextChunksCount]['Wisdom']
                ReasonOfWisdom = WMWMCompletions[ContextChunksCount]['ReasonOfWisdom']
                Mind = WMWMCompletions[ContextChunksCount]['Mind']
                ReasonOfPotentialMind = WMWMCompletions[ContextChunksCount]['ReasonOfPotentialMind']
                Wildness = WMWMCompletions[ContextChunksCount]['Wildness']
                ReasonOfWildness = WMWMCompletions[ContextChunksCount]['ReasonOfWildness']
                accuracy = WMWMCompletions[ContextChunksCount]['Accuracy']
                WMWM = {"Needs": Needs, "ReasonOfNeeds": ReasonOfNeeds, "Wisdom": Wisdom, "ReasonOfWisdom": ReasonOfWisdom, "Mind": Mind, "ReasonOfPotentialMind": ReasonOfPotentialMind, "Wildness": Wildness, "ReasonOfWildness": ReasonOfWildness, "Accuracy": accuracy}
                
                SplitedBodyContextsList.append({"ChunkId": ChunkId, "Chunk": Chunk, "Vector": {"ContextDefine": ContextDefine, "ContextCompletion": ContextCompletion}, "WMWM": WMWM})
                
                ContextText = ContextToText(ContextChunksCount + 1, BookTitle, Index, Chunk, ContextDefine, ContextCompletion, WMWM)
                
                SplitedBodyContextsText.append(ContextText)
                
                if ContextChunksCount < len(ContextChunks)-1:
                    ContextChunksCount += 1

        SplitedContexts.append({"IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "SplitedBodyContexts": SplitedBodyContextsList})  
        if SplitedBodyContextsText != []:
            SplitedChunkContexts.append(SplitedBodyContextsList)
            TaskBody = ''.join(SplitedBodyContextsText)
            SplitedBodyTexts.append({'Id': BodyId, 'Continue': TaskBody})
        else:
            SplitedBodyTexts.append({'Id': BodyId, 'Pass': ''})
        
    InputList = SplitedBodyTexts
        
    return SplitedContexts, SplitedChunkContexts, InputList

######################
##### Filter 조건 #####
######################
## WMWMMatching의 Filter(Error 예외처리)
def WMWMMatchingFilter(responseData, memoryCounter):
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
            key = '토론요약'
            if not ('장르' in dic[key] and '성별' in dic[key] and '연령' in dic[key] and '성향' in dic[key] and '감성' in dic[key] and '문구' in dic[key] and '대상독자' in dic[key] and '주제' in dic[key] and '목적' in dic[key] and '이유' in dic[key] and '대표질문' in dic[key] and '필요성' in dic[key] and '필요성배점이유' in dic[key] and '지식적유익성' in dic[key] and '지식적유익성배점이유' in dic[key] and '마음가짐의유익성' in dic[key] and '마음가짐의유익성배점이유' in dic[key] and '실천의유익성' in dic[key] and '실천의유익성배점이유' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
            
            # 유익성 점수들이 1-5 범위의 숫자 또는 문자열 숫자인지 검사
            usefulness_keys = ['필요성', '지식적유익성', '마음가짐의유익성', '실천의유익성']
            for usefulness_key in usefulness_keys:
                value = dic[key][usefulness_key]
                # 숫자 또는 문자열 숫자인지 확인
                if isinstance(value, (int, float)):
                    score = int(value)
                elif isinstance(value, str) and value.isdigit():
                    score = int(value)
                else:
                    return f"JSON에서 오류 발생: {usefulness_key} 값이 숫자가 아님"
                
                # 1-5 범위 내에 있는지 확인
                if score < 1 or score > 5:
                    return f"JSON에서 오류 발생: {usefulness_key} 값이 1-5 범위를 벗어남"
            
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        except KeyError:
            return "JSON에서 오류 발생: KeyError"
        
    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def WMWMMatchingInputMemory(inputMemoryDics, MemoryLength):
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
def WMWMMatchingOutputMemory(outputMemoryDics, MemoryLength):
    outputMemoryDic = outputMemoryDics[-MemoryLength:]
    
    OUTPUTmemoryDic = []
    for INput in outputMemoryDic:
        if isinstance(INput, list):
            OUTPUTmemoryDic.extend(INput)
        else:
            OUTPUTmemoryDic.append(INput)
    OUTPUTmemoryDic = [entry for entry in OUTPUTmemoryDic if entry != "Pass"]
    outputMemory = str(OUTPUTmemoryDic)
    outputMemory = outputMemory[:-1] + ", "
    outputMemory = outputMemory.replace("[, ", "[")
    # print(f"@@@@@@@@@@\noutputMemory :{outputMemory}\n@@@@@@@@@@")
    
    return outputMemory

#######################
##### Process 진행 #####
#######################
## WMWMMatching 프롬프트 요청 및 결과물 Json화
def WMWMMatchingProcess(projectName, email, DataFramePath, BeforeResponse = None, Process = "WMWMMatching", ProcessNumber = '10-1', memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, ProcessNumber, DataFramePath)
    SplitedContexts, SplitedChunkContexts, inputList = ContextCompletionsToInputList(projectName, email)
    
    if BeforeResponse != None:
        inputList = BeforeResponse
        
    InputList = inputList[OutputMemoryCount:]
    if InputList == []:
        return SplitedContexts, SplitedChunkContexts, OutputMemoryDicsFile

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
        
    # WMWMMatchingProcess
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
            memoryCounter = "\n"
            outputEnder = ""

            # Response 생성
            Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)
            
            # OutputStarter, OutputEnder에 따른 Response 전처리
            promptFrame = GetPromptFrame(Process)
            if mode in ["Example", "ExampleFineTuning", "Master"]:
                Example = promptFrame["Example"]
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
                                
            Filter = WMWMMatchingFilter(responseData, memoryCounter)
            
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
            inputMemory = WMWMMatchingInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = WMWMMatchingOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, ProcessNumber, DataFramePath)
    
    return SplitedContexts, SplitedChunkContexts, outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
### 데이터 치환
## outputMemoryDics의 ResponseJson변환
def outputMemoryDicsToResponseJson(SplitedContexts, outputMemoryDics):
    ResponseJson = []
    for i, response in enumerate(outputMemoryDics):
        if response != "Pass":
            responseDic = response[0]['토론요약']
            IndexId = SplitedContexts[i]['IndexId']
            Index = SplitedContexts[i]['Index']
            BodyId = SplitedContexts[i]['BodyId']
            Phrases = responseDic['문구']
            splitedContexts = SplitedContexts[i]['SplitedBodyContexts']        

            Purpose = responseDic['목적']
            Reason = responseDic['이유']
            Question = responseDic['대표질문']
            
            Subject = responseDic['주제']
            # Subject가 리스트가 아닐 경우의 처리
            if isinstance(Subject, str):
                try:
                    # 문자열이 리스트 형식이면, 실제 리스트로 변환
                    Subject = ast.literal_eval(Subject)
                except (ValueError, SyntaxError):
                    # 문자열이 일반 문자열이면, 쉼표로 분할
                    Subject = [s.strip() for s in Subject.split(',')]
                    
            Reader = responseDic['대상독자']
            # Reader가 리스트가 아닐 경우의 처리
            if isinstance(Reader, str):
                try:
                    # 문자열이 리스트 형식이면, 실제 리스트로 변환
                    Reader = ast.literal_eval(Reader)
                except (ValueError, SyntaxError):
                    # 문자열이 일반 문자열이면, 쉼표로 분할
                    Reader = [r.strip() for r in Reader.split(',')]
                    
            importanceList = []
            for j in (range(len(splitedContexts))):
                importance = splitedContexts[j]['Vector']['ContextDefine']['Importance']
                importanceList.append(int(importance))
            
            total = sum(importanceList)
            count = len(importanceList)
            Importance = total / count
            
            ContextDefine = {"Purpose": Purpose, "Reason": Reason, "Question": Question, "Subject": Subject, "Reader": Reader, "Importance": Importance}
            
            Genre = responseDic['장르']
            Gender = responseDic['성별']
            Age = responseDic['연령']
            Personality = responseDic['성향']
            Emotion = responseDic['감성']

            accuracyList = []
            for j in (range(len(splitedContexts))):
                accuracy = splitedContexts[j]['Vector']['ContextCompletion']['Accuracy']
                accuracyList.append(int(accuracy))
            
            total = sum(accuracyList)
            count = len(accuracyList)
            Accuracy = total / count

            ContextCompletion = {"Genre": Genre, "Gender": Gender, "Age": Age, "Personality": Personality, "Emotion": Emotion, "Accuracy": Accuracy}
            
            Needs = responseDic['필요성']
            ReasonOfNeeds = responseDic['필요성배점이유']
            Wisdom = responseDic['지식적유익성']
            ReasonOfWisdom = responseDic['지식적유익성배점이유']
            Mind = responseDic['마음가짐의유익성']
            ReasonOfPotentialMind = responseDic['마음가짐의유익성배점이유']
            Wildness = responseDic['실천의유익성']
            ReasonOfWildness = responseDic['실천의유익성배점이유']

            accuracyList = []
            for j in (range(len(splitedContexts))):
                accuracy = splitedContexts[j]['WMWM']['Accuracy']
                accuracyList.append(int(accuracy))
            
            total = sum(accuracyList)
            count = len(accuracyList)
            Accuracy = total / count

            WMWM = {"Needs": Needs, "ReasonOfNeeds": ReasonOfNeeds, "Wisdom": Wisdom, "ReasonOfWisdom": ReasonOfWisdom, "Mind": Mind, "ReasonOfPotentialMind": ReasonOfPotentialMind, "Wildness": Wildness, "ReasonOfWildness": ReasonOfWildness, "Accuracy": Accuracy}           
            
            ResponseJson.append({"IndexId": IndexId, "Index": Index, "BodyId": BodyId, "Phrases": Phrases, "Vector": {"ContextDefine": ContextDefine, "ContextCompletion": ContextCompletion}, "WMWM": WMWM})
            
    return ResponseJson

## WMWMMatchingBody 데이터 치환
def WMWMMatchingBodyResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Example"):   
    # 데이터 치환
    ## B. Body Process ##
    SplitedContexts, SplitedChunkContexts, outputMemoryDics = WMWMMatchingProcess(projectName, email, DataFramePath, ProcessNumber = '10-1', MessagesReview = messagesReview, Mode = mode)
    
    ## B. BodyResponseJson 생성 ##
    BodyResponseJson = outputMemoryDicsToResponseJson(SplitedContexts, outputMemoryDics)

    ## B. IndexInputlist 생성 ##
    Input = []
    Inputlist = []
    indexid = 1
    for i in range(len(SplitedContexts)):
        IndexId = SplitedContexts[i]['IndexId']
        BodyId = SplitedContexts[i]['BodyId']

        if IndexId == indexid:
            # 현재 IndexId와 동일한 BodyId의 데이터를 모음
            for j in range(len(BodyResponseJson)):
                BodyResponseJsonId = BodyResponseJson[j]['BodyId']
                if BodyId == BodyResponseJsonId:
                    Input.append(BodyResponseJson[j])
        else:
            # IndexId가 변경되면 현재까지 수집된 데이터를 Inputlist에 추가
            Inputlist.append(Input)
            Input = []
            indexid = IndexId  # indexid 업데이트
            # 새로운 IndexId에 대한 첫 번째 BodyId 처리
            for j in range(len(BodyResponseJson)):
                BodyResponseJsonId = BodyResponseJson[j]['BodyId']
                if BodyId == BodyResponseJsonId:
                    Input.append(BodyResponseJson[j])

    # 마지막 IndexId에 대한 데이터를 Inputlist에 추가
    if Input:
        Inputlist.append(Input)
    
    # inputlist 만들기
    HalfBodyFrameSplitedBodyScripts, ContextChunks, ContextCompletions, WMWMCompletions = LoadContextCompletions(projectName, email)
    BookTitle = HalfBodyFrameSplitedBodyScripts[0]['Index']
    inputlist = []
    for input in Inputlist:
        if input != []:
            inputText = []
            for inputBody in input:
                BodyId = inputBody['BodyId']
                Index = inputBody['Index']
                Phrases = inputBody['Phrases']
                ContextDefine = inputBody['Vector']['ContextDefine']
                ContextCompletion = inputBody['Vector']['ContextCompletion']
                WMWM = inputBody['WMWM']
                TaskBody = ContextToText(BodyId, BookTitle, Index, Phrases, ContextDefine, ContextCompletion, WMWM)
                inputText.append(TaskBody)
            if len(inputText) == 1:
                TaskBody = ''.join(inputText)
                inputlist.append({'Id': BodyId, 'Pass': TaskBody})
            else:
                TaskBody = ''.join(inputText)
                inputlist.append({'Id': BodyId, 'Continue': TaskBody})
        else:
            inputlist.append({'Id': BodyId, 'Pass': ''})
            
    # Continue가 존재하지 않는 경우(예외 처리)
    if not any('Continue' in item for item in inputlist):
        for item in inputlist:
            # 'Pass'가 있고 값이 비어있지 않은 경우에만 'Continue'로 변경
            if 'Pass' in item and item['Pass']:
                item['Continue'] = item.pop('Pass')

    return SplitedChunkContexts, BodyResponseJson, inputlist, BookTitle

## WMWMMatchingIndex, Book 데이터 치환
def WMWMMatchingResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Example"):

    SplitedChunkContexts, BodyResponseJson, inputlist, BookTitle = WMWMMatchingBodyResponseJson(projectName, email, DataFramePath, messagesReview = messagesReview, mode = mode)
    
    ## C. Index Process ##
    SplitedContexts, SplitedChunkContexts, outputMemoryDics = WMWMMatchingProcess(projectName, email, DataFramePath, BeforeResponse = inputlist, ProcessNumber = '10-2', MessagesReview = messagesReview, Mode = mode)

    ## C. SplitedIndexContexts 생성 ##
    SplitedIndexContexts = []
    CurrentContexts = None

    for context in SplitedContexts:
        if CurrentContexts is None or CurrentContexts['IndexId'] == context['IndexId']:
            # 현재 처리 중인 IndexId와 동일하거나 처음인 경우
            if CurrentContexts is None:
                CurrentContexts = context.copy()
                CurrentContexts['BodyId'] = [context['BodyId']]
                CurrentContexts['SplitedBodyContexts'] = context['SplitedBodyContexts']
            else:
                CurrentContexts['BodyId'].append(context['BodyId'])
                CurrentContexts['SplitedBodyContexts'] += context['SplitedBodyContexts']
        else:
            # 현재 처리 중인 IndexId와 다른 경우
            SplitedIndexContexts.append(CurrentContexts)
            CurrentContexts = context.copy()
            CurrentContexts['BodyId'] = [context['BodyId']]
            CurrentContexts['SplitedBodyContexts'] = context['SplitedBodyContexts']

    # 마지막으로 처리 중인 데이터 추가
    if CurrentContexts is not None:
        SplitedIndexContexts.append(CurrentContexts)
    
    ## C. IndexResponseJson 생성 ##
    IndexResponseJson = outputMemoryDicsToResponseJson(SplitedIndexContexts, outputMemoryDics)
    
    ## C. BookInputlist 생성 ##
    Inputlist = [{'Id': 1, 'Continue': None}]
    inputText = []
    for IndexResponse in IndexResponseJson:
        IndexId = IndexResponse['IndexId']
        Index = IndexResponse['Index']
        Phrases = IndexResponse['Phrases']
        ContextDefine = IndexResponse['Vector']['ContextDefine']
        ContextCompletion = IndexResponse['Vector']['ContextCompletion']
        WMWM = IndexResponse['WMWM']
        TaskBody = ContextToText(IndexId, BookTitle, Index, Phrases, ContextDefine, ContextCompletion, WMWM)
        inputText.append(TaskBody)
        
    Inputlist[0]['Continue'] = ''.join(inputText)
    
    ## A. ChunkResponseJson 생성 ##
    ChunkResponseJson = []
    GenreList = []
    GenderList = []
    AgeList = []
    PersonalityList = []
    EmotionList = []
    for i in range(len(SplitedChunkContexts)):
        for j in range(len(SplitedChunkContexts[i])):
            ChunkResponseJson.append(SplitedChunkContexts[i][j])
            # 각 요소 리스트 형성
            ContextCompletion = SplitedChunkContexts[i][j]['Vector']['ContextCompletion']
            GenreList.append(ContextCompletion['Genre'])
            GenderList.append(ContextCompletion['Gender'])
            AgeList.append(ContextCompletion['Age'])
            PersonalityList.append(ContextCompletion['Personality'])
            EmotionList.append(ContextCompletion['Emotion'])
    
    # 각 요소별 % 계산
    def CalculateRatio(lst):
        count = Counter(lst)
        total = len(lst)
        return {k: (v / total) * 100 for k, v in count.items()}
    
    def ItemsWithOthers(RatioDict):
        sorted_items = sorted(RatioDict.items(), key=lambda item: item[1], reverse=True)
        Top3 = dict(sorted_items[:3])
        OthersRatio = 100 - sum(Top3.values())
        if OthersRatio > 0:
            Top3['기타'] = OthersRatio
        return Top3

    GenresRatio = CalculateRatio(GenreList)
    GendersRatio = CalculateRatio(GenderList)
    AgesRatio = CalculateRatio(AgeList)
    PersonalitisRatio = CalculateRatio(PersonalityList)
    EmotionsRatio = CalculateRatio(EmotionList)
            
    ContextCompletionRatio = {"GenreRatio": ItemsWithOthers(GenresRatio), "GenderRatio": ItemsWithOthers(GendersRatio), "AgeRatio": ItemsWithOthers(AgesRatio), "PersonalityRatio": ItemsWithOthers(PersonalitisRatio), "EmotionRatio": ItemsWithOthers(EmotionsRatio)}
    
    ## D. Book Process ##
    SplitedContexts, SplitedChunkContexts, OutputMemoryDics = WMWMMatchingProcess(projectName, email, DataFramePath, BeforeResponse = Inputlist, ProcessNumber = '10-3', MessagesReview = messagesReview, Mode = "Master")
    
    ## D. SplitedBodyContexts 생성 ##
    IndexId = []
    IndexTag = []
    Index = []
    BodyId = []
    SplitedBodyContexts = []
    for IndexContexts in SplitedIndexContexts:
        IndexId.append(IndexContexts['IndexId'])
        IndexTag.append(IndexContexts['IndexTag'])
        Index.append(IndexContexts['Index'])
        BodyId.append(IndexContexts['BodyId'])
        SplitedBodyContexts += IndexContexts['SplitedBodyContexts']
        
    BookContexts = [{"IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "SplitedBodyContexts": SplitedBodyContexts}]
    
    ## D. BookResponseJson 생성 ##
    RawBookResponseJson = outputMemoryDicsToResponseJson(BookContexts, OutputMemoryDics)
    Phrases = RawBookResponseJson[0]['Phrases']
    ContextDefine = RawBookResponseJson[0]['Vector']['ContextDefine']
    
    ContextCompletion = RawBookResponseJson[0]['Vector']['ContextCompletion']
    Genre = ContextCompletion['Genre']
    GenreRatio = ContextCompletionRatio['GenreRatio']
    GenreSet = {"Genre": Genre, "GenreRatio": GenreRatio}
    
    Gender = ContextCompletion['Gender']
    GenderRatio = ContextCompletionRatio['GenderRatio']
    GenderSet = {"Gender": Gender, "GenderRatio": GenderRatio}
    
    Age = ContextCompletion['Age']
    AgeRatio = ContextCompletionRatio['AgeRatio']
    AgeSet = {"Age": Age, "AgeRatio": AgeRatio}
    
    Personality = ContextCompletion['Personality']
    PersonalityRatio = ContextCompletionRatio['PersonalityRatio']
    PersonalitySet = {"Personality": Personality, "PersonalityRatio": PersonalityRatio}
    
    Emotion = ContextCompletion['Emotion']
    EmotionRatio = ContextCompletionRatio['EmotionRatio']
    EmotionSet = {"Emotion": Emotion, "EmotionRatio": EmotionRatio}
    
    ContextCompletion = {"Genre": GenreSet, "Gender": GenderSet, "Age": AgeSet, "Personality": PersonalitySet, "Emotion": EmotionSet}
    
    WMWM = RawBookResponseJson[0]['WMWM']
    BookResponseJson = [{"BookId": 1, "Title": BookTitle, "Phrases": Phrases, "Vector": {"ContextDefine": ContextDefine, "ContextCompletion":ContextCompletion}, "WMWM": WMWM}]

    return ChunkResponseJson, BodyResponseJson, IndexResponseJson, BookResponseJson
                                                                                 
## 프롬프트 요청 및 결과물 Json을 WMWMMatching에 업데이트
def WMWMMatchingUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 10_WMWMMatchingUpdate 시작 >")
    # WMWMMatching의 Count값 가져오기
    WMWMChunkCount, WMWMBodyCount, WMWMIndexCount, Completion = WMWMMatchingCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedWMWMMatchingToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "WMWMMatching", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 10_WMWMMatchingUpdate는 ExistedWMWMMatching으로 대처됨 ]\n")
        else:
            ChunkResponseJson, BodyResponseJson, IndexResponseJson, BookResponseJson = WMWMMatchingResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
            
            ## A. ChunkResponseJson ##
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = ChunkResponseJson[WMWMChunkCount:]
            ResponseJsonCount = len(ResponseJson)
                        
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'WMWMMatchingChunkUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'WMWMMatchingChunkUpdate: {Update["Chunk"]}')
                time.sleep(0.0001)
                ChunkId = Update["ChunkId"]
                Chunk = Update["Chunk"]
                Vector = Update["Vector"]
                WMWM = Update["WMWM"]
                
                AddWMWMMatchingChunksToDB(projectName, email, ChunkId, Chunk, Vector, WMWM)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            
            ## B. BodyResponseJson ##
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = BodyResponseJson[WMWMBodyCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'WMWMMatchingBodyUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'WMWMMatchingBodyUpdate: {Update["Phrases"]}')
                time.sleep(0.0001)
                BodyId = Update["BodyId"]
                Phrases = Update["Phrases"]
                Vector = Update["Vector"]
                WMWM = Update["WMWM"]
                
                AddWMWMMatchingBODYsToDB(projectName, email, BodyId, Phrases, Vector, WMWM)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            
            ## C. IndexResponseJson ##
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = IndexResponseJson[WMWMIndexCount:]
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'WMWMMatchingIndexUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'WMWMMatchingIndexUpdate: {Update["Phrases"]}')
                time.sleep(0.0001)
                IndexId = Update["IndexId"]
                Index = Update["Index"]
                Phrases = Update["Phrases"]
                Vector = Update["Vector"]
                WMWM = Update["WMWM"]
                
                AddWMWMMatchingIndexsToDB(projectName, email, IndexId, Index, Phrases, Vector, WMWM)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            
            ## D. BookResponseJson ##
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = BookResponseJson
            ResponseJsonCount = len(ResponseJson)
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'WMWMMatchingBookUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'WMWMMatchingBookUpdate: {Update["Title"]}')
                time.sleep(0.0001)
                BookId = Update["BookId"]
                Title = Update["Title"]
                Phrases = Update["Phrases"]
                Vector = Update["Vector"]
                WMWM = Update["WMWM"]
                
                AddWMWMMatchingBookToDB(projectName, email, BookId, Title, Phrases, Vector, WMWM)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            WMWMMatchingCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 10_WMWMMatchingUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 10_WMWMMatchingUpdate는 이미 완료됨 ]\n")
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################