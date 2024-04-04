import os
import re
import json
import time
import difflib
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedSFXMatchingToDB, AddSFXSplitedBodysToDB, SFXMatchingCountLoad, SFXMatchingCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
## BodyFrameBodys 로드
def LoadBodyFrameBodys(projectName, email):
    project = GetProject(projectName, email)
    BodyFrameSplitedBodyScripts = project.HalfBodyFrame[1]['SplitedBodyScripts'][1:]
    BodyFrameBodys = project.HalfBodyFrame[2]['Bodys'][1:]
    
    return BodyFrameSplitedBodyScripts, BodyFrameBodys

## inputList의 InputList 치환 (인덱스, 캡션 부분 합치기)
def MergeInputList(inputList):
    InputList = []
    MergeBuffer = ''
    MergeIds = []
    NonMergeFound = False

    for item in inputList:
        if list(item.keys())[1] == 'Merge':
            # 'Merge' 태그가 붙은 항목의 내용을 버퍼에 추가하고 ID를 MergeIds에 추가합니다.
            MergeBuffer += list(item.values())[1]
            MergeIds.append(item['Id'])
        else:
            # 'Merge'가 아닌 태그가 발견된 경우
            NonMergeFound = True
            if MergeBuffer:
                # 버퍼에 내용이 있으면 현재 항목과 합칩니다.
                content = MergeBuffer + list(item.values())[1]
                # 'Id'는 MergeIds에 현재 항목의 'Id'를 추가하여 리스트로 만듭니다.
                currentId = MergeIds + [item['Id']]
                # 합쳐진 내용과 'Id' 리스트를 가진 새 딕셔너리를 만듭니다.
                mergedItem = {'Id': currentId, list(item.keys())[1]: content.replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')}
                InputList.append(mergedItem)
                # 버퍼와 ID 리스트를 초기화합니다.
                MergeBuffer = ''
                MergeIds = []
            else:
                # 버퍼가 비어 있으면 현재 항목을 결과 리스트에 그대로 추가합니다.
                InputList.append(item)
    
    # 리스트의 끝에 도달했을 때 버퍼에 남아 있는 'Merge' 내용을 처리합니다.
    if MergeBuffer and not NonMergeFound:
        # 모든 항목이 'Merge'인 경우 마지막 항목만 처리합니다.
        mergedItem = {'Id': MergeIds, list(item.keys())[1]: MergeBuffer.replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')}
        InputList.append(mergedItem)

    return InputList

## BodyFrameBodys의 inputList 치환
def BodyFrameBodysToInputList(projectName, email, Task = "Body"):
    BodyFrameSplitedBodyScripts, BodyFrameBodys = LoadBodyFrameBodys(projectName, email)
    
    inputList = []
    for i in range(len(BodyFrameBodys)):
        Id = BodyFrameBodys[i]['BodyId']
        task = BodyFrameBodys[i]['Task']
        TaskBody = BodyFrameBodys[i][Task]

        if Task in task:
            Tag = 'Continue'
        elif 'Body' not in task:
            Tag = 'Merge'
        else:
            Tag = 'Pass'
            
        InputDic = {'Id': Id, Tag: TaskBody}
        inputList.append(InputDic)
        
    InputList = MergeInputList(inputList)
    
    # ChunkIdList 형성
    InputChunkIdList = []
    for Input in InputList:
        InputChunkIds = []

        # 'Id'가 리스트인지 확인
        if isinstance(Input['Id'], list):
            for Id in Input['Id']:
                InputChunkIds += BodyFrameBodys[Id - 1]['ChunkId']
        else:
            # 'Id'가 단일 정수인 경우
            Id = Input['Id']
            InputChunkIds += BodyFrameBodys[Id - 1]['ChunkId']

        InputChunkIdList.append(InputChunkIds)
        
    return InputList, InputChunkIdList

######################
##### Filter 조건 #####
######################
## SFXMatching의 Filter(Error 예외처리)
def SFXMatchingFilter(Input, responseData, memoryCounter):
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
                OUTPUT = str(dic[key]['길이']).replace('<시작>', '')
                OUTPUT = OUTPUT.replace('<끝>', '')
                OUTPUT = re.sub("[^가-힣]", "", OUTPUT)
            except TypeError:
                return "JSON에서 오류 발생: TypeError"
            except KeyError:
                return "JSON에서 오류 발생: KeyError"
            if not '효과음' in key:
                return "JSON에서 오류 발생: JSONKeyError"
            elif not ('<시작>' in dic[key]['길이'] and '<끝>' in dic[key]['길이']):
                return f"JSON에서 오류 발생: JSON <시작>, <끝>의 표기가 Output에 포함되지 않음 Error\n문구: {dic[key]['길이']}"
            elif not OUTPUT in INPUT:
                print(f"JSON에서 오류 발생: JSON '길이'의 문구가 Input에 포함되지 않음 Error\n문구: {dic[key]['길이']}")
                dic[key]['길이'] = ''
            elif not ('명칭' in dic[key] and '영어명칭' in dic[key] and '유형' in dic[key] and '역할' in dic[key] and '공간음향' in dic[key] and '길이' in dic[key] and '필요성' in dic[key]):
                return "JSON에서 오류 발생: JSONKeyError"
        # Error4: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
        
    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def SFXMatchingInputMemory(inputMemoryDics, MemoryLength):
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
def SFXMatchingOutputMemory(outputMemoryDics, MemoryLength):
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
## SFXMatching 프롬프트 요청 및 결과물 Json화
def SFXMatchingProcess(projectName, email, DataFramePath, Process = "SFXMatching", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '15', DataFramePath)    
    inputList, inputChunkIdList = BodyFrameBodysToInputList(projectName, email)
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
        
    # SFXMatchingProcess
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
            memoryCounter = " - 주의사항: '길이'에서 <내용>에 포함된 문장을 그대로 작성하며 <시작> <끝>을 꼭 표기, 효과음의 명칭은 구체적이고 물리적으로 작성, 글의 순서에 맞도록 '효과음1' ... '효과음n' 까지 작성 -\n"
            outputEnder = "{{'효과음"
            
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
         
            Filter = SFXMatchingFilter(Input, responseData, memoryCounter)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                
                # 2분 대기 이후 다시 코드 실행
                time.sleep(120)
                ErrorCount += 1
                if ErrorCount == 3:
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
            inputMemory = SFXMatchingInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = SFXMatchingOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '15', DataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
## SFXChunk의 위치데이터 저장
def SFXChunkToSFXDic(SFXChunk):
    # 정규 표현식을 사용하여 모든 형태의 SFX 태그 찾기
    StartTagPattern = r"<효과음시작(\d{1,5})>"
    EndTagPattern = r"<효과음끝(\d{1,5})>"
    # 태그가 시작되는 지점 찾기
    StartTagMatch = re.search(StartTagPattern, SFXChunk)
    EndTagMatch = re.search(EndTagPattern, SFXChunk)
    # Chunk 만들기
    Chunk = SFXChunk.replace(StartTagMatch[0], '')
    Chunk = Chunk.replace(EndTagMatch[0], '')
    # 태그 바로 전 지점의 문자열 길이를 구함
    StartPoint = StartTagMatch.start() if StartTagMatch else None
    EndPoint = EndTagMatch.start() - len(StartTagMatch[0]) if EndTagMatch else None

    sfxPoint = [StartPoint, EndPoint] if StartPoint is not None and EndPoint is not None else None
    
    return {"Chunk": Chunk, "SFX": [StartTagMatch[0], EndTagMatch[0]], "SFXPoint": sfxPoint}

def SFXDicToSFXChunk(SFXDics):
    # SFXDics가 리스트가 아니라면 리스트로 변환
    if not isinstance(SFXDics, list):
        SFXDics = [SFXDics]
    # 태그와 해당 위치를 저장할 리스트
    tags = []
    Chunk = SFXDics[0]['Chunk']
    # 각 SFXDic에서 태그와 위치를 추출하여 tags 리스트에 추가
    for SFXDic in SFXDics:
        StartTag, EndTag = SFXDic['SFX']
        StartPoint, EndPoint = SFXDic['SFXPoint']
        tags.append((StartPoint, StartTag))
        tags.append((EndPoint, EndTag))
    # 시작점을 기준으로 태그들을 정렬
    tags.sort(key=lambda x: x[0])
    # 태그를 Chunk에 삽입
    SFXChunk = ""
    last_index = 0
    for point, tag in tags:
        SFXChunk += Chunk[last_index:point] + tag
        last_index = point
    # 마지막 부분 추가
    SFXChunk += Chunk[last_index:]

    return SFXChunk

# SFXCorrectionChunk 합성
def ApplyTagsToChunk(Chunk, SFXPoint, SFXTag, CorrectionPoint, CorrectionTag):
    # CorrectionPoint와 CorrectionTag가 None이면 빈 리스트로 처리
    CorrectionPoint = [] if CorrectionPoint is None else CorrectionPoint
    CorrectionTag = [] if CorrectionTag is None else CorrectionTag

    # 태그와 포인트를 결합
    tags = [(SFXPoint[i], SFXTag[i]) for i in range(len(SFXPoint))] + \
           [(CorrectionPoint[i], CorrectionTag[i]) for i in range(len(CorrectionPoint))]

    # 태그 위치에 따라 정렬
    tags.sort(key=lambda x: x[0])

    # 문자열에 태그 적용
    offset = 0
    Chunk  # 초기화
    for point, tag in tags:
        Chunk = Chunk[:point + offset] + tag + Chunk[point + offset:]
        offset += len(tag)

    return Chunk

## SFX의 Bodys전환
def SFXToBodys(projectName, email, ResponseJson):
    # ResponseJson의 RangeList화
    SFXChunkList = []
    SameIdSFXChunkList = []
    SameIdRangePointList = []
    lastChunkId = None
    for i in range(len(ResponseJson)):
        response = ResponseJson[i]['SFXSplitedBodyChunks']
        for j in range(len(response)):
            ChunkId = response[j]['ChunkId']
            Chunk = response[j]['Chunk']
            SFXChunk = response[j]['SFX']['Range']
            RangePoint = response[j]['SFX']['RangePoint']

            if ChunkId == lastChunkId:
                # 동일한 ChunkId를 가진 경우, SFXChunk를 SameIdSFXChunkList에 추가
                SameIdSFXChunkList.append(SFXChunk)
                SameIdRangePointList.append(RangePoint)
            else:
                # ChunkId가 변경된 경우 이전 데이터 처리
                if SameIdSFXChunkList:
                    sfxchunk = SFXDicToSFXChunk(SameIdRangePointList)
                    sfxlist = []
                    sfxpointlist = []
                    for SameIdRangePoint in SameIdRangePointList:
                        sfx = SameIdRangePoint['SFX']
                        sfxpoint = SameIdRangePoint['SFXPoint']
                        sfxlist += sfx
                        sfxpointlist += sfxpoint
                    chunk = SameIdRangePoint['Chunk']
                    rangePoint = {'Chunk': chunk, 'SFX': sfxlist, 'SFXPoint': sfxpointlist}
                    # print(f"{lastChunkId}: {rangePoint}\n\n")
                    # 이전 ChunkId의 데이터를 SFXChunkList에 추가
                    SFXChunkList.append({'ChunkId': lastChunkId, 'Chunk': lastChunk, 'SFXChunk': sfxchunk, 'SFXChunks': SameIdSFXChunkList, 'RangePoint': rangePoint})
                    SameIdSFXChunkList = []
                    SameIdRangePointList = []

                # 새로운 ChunkId 시작
                SameIdSFXChunkList.append(SFXChunk)
                SameIdRangePointList.append(RangePoint)
                lastChunkId = ChunkId
                lastChunk = Chunk

    # 반복문 종료 후 마지막 데이터 처리
    if SameIdSFXChunkList:
        sfxchunk = SFXDicToSFXChunk(SameIdRangePointList)
        sfxlist = []
        sfxpointlist = []
        for SameIdRangePoint in SameIdRangePointList:
            sfx = SameIdRangePoint['SFX']
            sfxpoint = SameIdRangePoint['SFXPoint']
            sfxlist += sfx
            sfxpointlist += sfxpoint
        chunk = SameIdRangePoint['Chunk']
        rangePoint = {'Chunk': chunk, 'SFX': sfxlist, 'SFXPoint': sfxpointlist}
        
        SFXChunkList.append({'ChunkId': lastChunkId, 'Chunk': lastChunk, 'SFXChunk': sfxchunk, 'SFXChunks': SameIdSFXChunkList, 'RangePoint': rangePoint})

    with get_db() as db:
        project = GetProject(projectName, email)
        HalfBodyFrame = project.HalfBodyFrame
        SplitedBodyScripts = HalfBodyFrame[1]["SplitedBodyScripts"][1:]
        Bodys = HalfBodyFrame[2]["Bodys"][1:]
        
        # HalfBodyFrameChunkList
        ChunkList = []
        for i in range(len(SplitedBodyScripts)):
            SplitedBodyChunks = SplitedBodyScripts[i]['SplitedBodyChunks']
            for j in range(len(SplitedBodyChunks)):
                ChunkId = SplitedBodyChunks[j]['ChunkId']
                Tag = SplitedBodyChunks[j]['Tag']
                Chunk = SplitedBodyChunks[j]['Chunk']
                ChunkList.append({'ChunkId': ChunkId, 'Tag': Tag, 'Chunk': Chunk})

        # SFXBody 변환
        ChunkIdx = []
        Chunks = []
        CorrectionChunkList = []
        for i in range(len(SFXChunkList)):
            SFXChunkDic = SFXChunkList[i]
            SFXChunkIdx = SFXChunkDic['ChunkId']
            if not isinstance(SFXChunkIdx, list):
                SFXChunkIdx = [SFXChunkIdx]
            # SFXChunk = SFXChunkDic['Chunk']
            for j in range(len(ChunkList)):
                ChunkDic = ChunkList[j]
                ChunkId = ChunkDic['ChunkId']
                Chunk = ChunkDic['Chunk']
                if ChunkId in SFXChunkIdx:
                    ChunkIdx.append(ChunkId)
                    Chunks.append(Chunk)
                    if ChunkIdx == SFXChunkIdx:
                        Correction = []
                        CorrectionPoint = []
                        CP = 0
                        if len(Chunks) > 1:
                            for k in range(len(Chunks)):
                                if k == len(Chunks) - 1:
                                    break
                                Correction.append('●')
                                ChunkPoint = len(Chunks[k]) + 1
                                CP += ChunkPoint
                                CorrectionPoint.append(CP)
                        else:
                            Correction = None
                            CorrectionPoint = None
                        CorrectionChunk = ' ●'.join(Chunks)
                        CorrectionChunkList.append({'ChunkId': ChunkIdx, 'CorrectionChunk': CorrectionChunk, 'Correction': Correction, 'CorrectionPoint': CorrectionPoint})
                        ChunkIdx = []
                        Chunks = []
                        break

        # json_data = json.dumps(CorrectionChunkList, ensure_ascii = False, indent = 4)
        # with open('CorrectionChunkList.json', 'w', encoding='utf-8') as file:
        #     file.write(json_data)

        # SFXCorrectionChunk 합성
        SFXCorrectionChunkList = []
        for i in range(len(SFXChunkList)):
            ChunkId = SFXChunkList[i]['ChunkId']
            Chunk = SFXChunkList[i]['Chunk']
            SFXChunk = SFXChunkList[i]['SFXChunk']
            SFXPoint = SFXChunkList[i]['RangePoint']['SFXPoint']
            # print(ChunkId)
            # print(SFXPoint)
            # print('')
            SFXTag = SFXChunkList[i]['RangePoint']['SFX']
            
            CorrectionChunk = CorrectionChunkList[i]['CorrectionChunk']
            CorrectionPoint = CorrectionChunkList[i]['CorrectionPoint']
            CorrectionTag = CorrectionChunkList[i]['Correction']
            
            SFXCorrectionChunk = ApplyTagsToChunk(Chunk, SFXPoint, SFXTag, CorrectionPoint, CorrectionTag)
            SFXCorrectionChunkList.append({'ChunkId': ChunkId, 'CorrectionChunk': CorrectionChunk, 'SFXCorrectionChunk': SFXCorrectionChunk})
        
        # SFXBody 형성
        for body in Bodys:
            SFXBody = body['Correction']
            SFXBodyChunkIds = body['ChunkId']
            for i in range(len(SFXCorrectionChunkList)):
                SFXCorrectionChunkDic = SFXCorrectionChunkList[i]
                ChunkId = SFXCorrectionChunkDic['ChunkId']
                if isinstance(ChunkId, list):
                    ChunkId = ChunkId[0]
                if ChunkId in SFXBodyChunkIds:
                    CorrectionChunk = SFXCorrectionChunkDic['CorrectionChunk']
                    
                    SFXCorrectionChunk = SFXCorrectionChunkDic['SFXCorrectionChunk']
                    SFXCorrectionChunk = SFXCorrectionChunk.replace('<효과음시작', '<S')
                    SFXCorrectionChunk = SFXCorrectionChunk.replace('<효과음끝', '<E')
                    
                    SFXBody = SFXBody.replace(CorrectionChunk, SFXCorrectionChunk, 1)

            if 'SFX' not in body['Task']:
                body['Task'].append('SFX')
            body['SFX'] = SFXBody

    # json_data = json.dumps(Bodys, ensure_ascii = False, indent = 4)
    # with open('Bodys.json', 'w', encoding='utf-8') as file:
    #     file.write(json_data)

    flag_modified(project, "HalfBodyFrame")
    
    db.add(project)
    db.commit()

## Chunk에서 ExtractedSFXchunk와 가장 유사한 부분을 찾아서 ExtractedSFXchunk로 대처
def ReplaceSimilarChunk(Chunk, ExtractedSFXchunk, SFXID):
    # Chunk의 각 부분 문자열과 ExtractedSFXchunk를 비교하여 가장 유사한 부분 찾기
    bestRatio = 0
    bestStart = 0
    bestEnd = 0

    for start in range(len(Chunk)):
        for end in range(start + 1, len(Chunk) + 1):
            substring = Chunk[start:end]
            ratio = difflib.SequenceMatcher(None, substring, ExtractedSFXchunk).ratio()
            if ratio > bestRatio:
                bestRatio = ratio
                bestStart = start
                bestEnd = end

    # 가장 유사한 부분을 target_chunk로 변경
    NewChunk = Chunk[:bestStart] + f'<효과음시작{SFXID}>' + ExtractedSFXchunk + f'<효과음끝{SFXID}>' + Chunk[bestEnd:]

    return NewChunk

## Chunk를 Tokens로 치환
def SplitChunkIntoTokens(Chunk):
    pattern = r"""
        (?P<SFXStart>\<효과음시작\d{1,5}\>) | # 효과음시작 '<시작n>'
        (?P<SFXEnd>\<효과음끝\d{1,5}\>) | # 효과음끝 '<끝n>'
        (?P<Space>\s) | # 띄어쓰기 ' '
        (?P<Enter>\\n) | # 줄바꿈 '\n'
        (?P<Comma>,) | # 콤마 ','
        (?P<Quotes>['“”"‘’]) | # 따옴표 '" ... ’'
        (?P<Period>[!?.]) | # 종결점 '!, ?, .'
        (?P<ETC>[^a-zA-Z0-9가-힣\s,‘’“”'!?.一-龠ぁ-んァ-ンㄱ-ㅎㅏ-ㅣア-ンáéíóúÁÉÍÓÚñÑ]) | # 특수문자 (한국어, 영어, 일본어, 중국어, 스페인어 제외)
        (?P<Number>\d+(\.\d+)?) | # 숫자 (정수 및 소수)
        (?P<Ko>[가-힣]+) | # 한국어
        (?P<En>[a-zA-Z]+) | # 영어
        (?P<Ja>[ぁ-んァ-ンㄱ-ㅎㅏ-ㅣ]+) | # 일본어 (히라가나, 카타카나, 한글 자모)
        (?P<Zh>[一-龠]+) | # 중국어 (한자)
        (?P<Es>[áéíóúÁÉÍÓÚñÑa-zA-Z]+) # 스페인어 (스페인어 특수 문자 포함)
    """

    Tokens = []
    for match in re.finditer(pattern, Chunk, re.VERBOSE):
        kind = [k for k, v in match.groupdict().items() if v][0]
        Tokens.append({kind: match.group()})

    return Tokens

## 데이터 치환
def SFXMatchingResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory", importance = 0):
    # Chunk, ChunkId 데이터 추출
    InputList, InputChunkIdList = BodyFrameBodysToInputList(projectName, email, Task = "Body")
    BodyFrameSplitedBodyScripts, BodyFrameBodys = LoadBodyFrameBodys(projectName, email)
    
    # 데이터 치환
    outputMemoryDics = SFXMatchingProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)

    # outputMemoryDics의 ChunksList 형성
    ChunkList = []
    for i in range(len(BodyFrameSplitedBodyScripts)):
        BodyId = BodyFrameSplitedBodyScripts[i]['BodyId']
        for j in range(len(BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks'])):
            chunk = BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks'][j]
            ChunkId = chunk['ChunkId']
            Chunk = chunk['Chunk']
            ChunkList.append({'BodyId': BodyId, 'ChunkId': ChunkId, 'Chunk': Chunk})

    InputsList = []
    ChunkListCount = 0
    for i in range(len(InputChunkIdList)):
        ChunksList = []
        for j in range(ChunkListCount, len(ChunkList)):
            if ChunkList[j]['ChunkId'] in InputChunkIdList[i]:
                outputId = i + 1
                BodyId = ChunkList[j]['BodyId']
                ChunkId = ChunkList[j]['ChunkId']
                Chunk = ChunkList[j]['Chunk']
                ChunksList.append({'outputId': outputId, 'BodyId': BodyId, 'ChunkId': ChunkId, 'Chunk': Chunk})
            else:
                ChunkListCount = j
                break
        InputsList.append(ChunksList)

    # outputMemoryDics의 순서를 글의 순서대로 전처리
    OutputMemoryDics = []
    pattern = r"[A-Za-z’]+(?:\s+[A-Za-z’]+)*"
    for i in range(len(InputList)):
        Input = InputList[i]['Continue']
        EngInput = re.sub(pattern, "영문어문글장", Input)
        CleanInput = re.sub("[^가-힣]", "", EngInput)
        
        OutputDic = outputMemoryDics[i]
        CleanOutputs = []
        for Output in OutputDic:
            OutputValue = next(iter(Output.values()))
            Output = OutputValue['길이']
            EngOutput = re.sub(pattern, "영문어문글장", Output)
            startIndex = EngOutput.find('<시작>') + len('<시작>')
            endIndex = EngOutput.find('<끝>')
            Content = EngOutput[startIndex:endIndex].strip()
            CleanContent = re.sub("[^가-힣]", "", Content)
            CleanOutputs.append(CleanContent)
        
        positions = [(CleanInput.find(word), index) for index, word in enumerate(CleanOutputs)]
        # 위치 정보를 기준으로 정렬
        positions.sort()
        # 정렬된 순서대로 새로운 리스트와 변경된 순서값 생성
        NewCleanOutputs = [CleanOutputs[index] for position, index in positions]
        NewOutputsOrder = [index for position, index in positions]
        
        NewDics = []
        for NewOrder in NewOutputsOrder:
            NewDics.append(OutputDic[NewOrder])
            
        OutputMemoryDics.append(NewDics)

    # outputMemoryDics의 Chunk단위 전처리
    SFXID = 1
    outputMemoryDicsList = []
    for i in range(len(OutputMemoryDics)):
        for j in range(len(OutputMemoryDics[i])):
            key = next(iter(OutputMemoryDics[i][j]))
            SFXDic = OutputMemoryDics[i][j][key]
            RANGE = SFXDic['길이']
            ImportanceScore = int(SFXDic['필요성'])
            
            if ImportanceScore >= importance:
                if '<시작>' in RANGE and '<끝>' in RANGE:
                    RANGE = RANGE.replace('<시작>', f'<시작{SFXID}>')
                    RANGE = RANGE.replace(f'<시작{SFXID}>. ', f'. <시작{SFXID}>')
                    RANGE = RANGE.replace(f'.<시작{SFXID}>', f'<시작{SFXID}>.')
                    RANGE = RANGE.replace(f',<시작{SFXID}>', f'<시작{SFXID}>,')
                    RANGE = RANGE.replace(f'<시작{SFXID}> ', f' <시작{SFXID}>')
                    RANGE = RANGE.replace('<끝>', f'<끝{SFXID}>')
                    RANGE = RANGE.replace(f'.<끝{SFXID}>', f'<끝{SFXID}>.')
                    RANGE = RANGE.replace(f',<끝{SFXID}>', f'<끝{SFXID}>,')
                    RANGE = RANGE.replace(f'<끝{SFXID}> ', f' <끝{SFXID}>')
                    Chunk = RANGE
                    SFXId = SFXID
                    sFX = SFXDic['명칭']
                    Prompt = SFXDic['영어명칭']
                    Type = SFXDic['유형']
                    Role = SFXDic['역할']
                    Direction = SFXDic['공간음향']
                    Range = RANGE
                    Importance = SFXDic['필요성']
                    
                    outputMemoryDicsList.append({"outputId": i + 1, "Chunk": Chunk, "SFX": {"SFXId": SFXId, "SFX": sFX, "Prompt": Prompt, "Type": Type, "Role": Role, "Direction": Direction, "Range": Range, "RangePoint": None, "Importance": Importance}})
                    SFXID += 1

    # outputMemoryDics의 전처리
    # TQDM 셋팅
    InputsListCount = len(InputsList)
    UpdateTQDM = tqdm(InputsList,
                    total = InputsListCount,
                    desc = 'SFXMatchingOutputMemoryDicsPreprocess')

    ResponseJson = []
    MemoryDicsCount = 0
    SFXIdCounter = 1
    for i, Update in enumerate(UpdateTQDM):
        outputId = i + 1
        Inputs = Update
        for j in range(len(Update)):
            InputsId = Inputs[j]['outputId']
            BodyId = Inputs[j]['BodyId']
            
            if j >= 2:
                BeBeforeInputsChunk = Inputs[j-2]['Chunk']
                CleanBeBeforeInputsChunk = re.sub("[^가-힣]", "", BeBeforeInputsChunk)
                BeforeInputsChunk = Inputs[j-1]['Chunk']
                CleanBeforeInputsChunk = re.sub("[^가-힣]", "", BeforeInputsChunk)
            InputsChunk = Inputs[j]['Chunk']
            CleanInputsChunk = re.sub("[^가-힣]", "", InputsChunk)
            
            for k in range(MemoryDicsCount, len(outputMemoryDicsList)):
                MemoryDicsOutput = outputMemoryDicsList[k]
                MemoryDicsOutputId = MemoryDicsOutput['outputId']
                
                if outputId == InputsId == MemoryDicsOutputId:
                    SFX = MemoryDicsOutput['SFX']
                    SFX['SFXId'] = SFXIdCounter
                    SFXchunk = MemoryDicsOutput['Chunk']
                    Match = re.search(r'<시작\d{1,5}>(.*?)<끝\d{1,5}>', SFXchunk)
                    if Match:
                        ExtractedSFXchunk = Match.group(0)
                        ExtractedSFXchunk = re.sub(r'<시작\d{1,5}>', '', ExtractedSFXchunk)
                        ExtractedSFXchunk = re.sub(r'<끝\d{1,5}>', '', ExtractedSFXchunk)
                        CleanExtractedSFXchunk = re.sub("[^가-힣]", "", ExtractedSFXchunk)
                        if CleanExtractedSFXchunk == '':
                            CleanExtractedSFXchunk = "None"
                    else:
                        CleanExtractedSFXchunk = "None"
                                            
                    if CleanExtractedSFXchunk in CleanInputsChunk:
                        ChunkId = Inputs[j]['ChunkId']
                        OrigianlChunk = Inputs[j]['Chunk']
                        SFXID = SFX['SFXId']
                        Chunk = InputsChunk
                        Chunk = ReplaceSimilarChunk(Chunk, ExtractedSFXchunk, SFXID)
                        SFX['Range'] = Chunk
                        SFX['RangePoint'] = SFXChunkToSFXDic(Chunk)
                        SFXChunkTokens = SplitChunkIntoTokens(Chunk)
                        ResponseJson.append({"outputId": outputId, "BodyId": BodyId, "SFXChunk":{"ChunkId": ChunkId, "Chunk": OrigianlChunk, "SFX": SFX, "SFXChunkTokens": SFXChunkTokens}})
                        SFXIdCounter += 1
                        MemoryDicsCount = k + 1
                    elif j >= 2:
                        if CleanExtractedSFXchunk in CleanBeforeInputsChunk + CleanInputsChunk:
                            ChunkId = [Inputs[j-1]['ChunkId'], Inputs[j]['ChunkId']]
                            OrigianlChunk = Inputs[j-1]['Chunk'] + ' ' + Inputs[j]['Chunk']
                            SFXID = SFX['SFXId']
                            Chunk = BeforeInputsChunk + ' ' + InputsChunk
                            Chunk = ReplaceSimilarChunk(Chunk, ExtractedSFXchunk, SFXID)
                            SFX['Range'] = Chunk
                            SFX['RangePoint'] = SFXChunkToSFXDic(Chunk)
                            SFXChunkTokens = SplitChunkIntoTokens(Chunk)
                            ResponseJson.append({"outputId": outputId, "BodyId": BodyId, "SFXChunk":{"ChunkId": ChunkId, "Chunk": OrigianlChunk, "SFX": SFX, "SFXChunkTokens": SFXChunkTokens}})
                            SFXIdCounter += 1
                            MemoryDicsCount = k + 1

                        elif CleanExtractedSFXchunk in CleanBeBeforeInputsChunk + CleanBeforeInputsChunk + CleanInputsChunk:
                            ChunkId = [Inputs[j-2]['ChunkId'], Inputs[j-1]['ChunkId'], Inputs[j]['ChunkId']]
                            OrigianlChunk = Inputs[j-2]['Chunk'] + ' ' + Inputs[j-1]['Chunk'] + ' ' + Inputs[j]['Chunk']
                            SFXID = SFX['SFXId']
                            Chunk = BeBeforeInputsChunk + ' ' + BeforeInputsChunk + ' ' + InputsChunk
                            Chunk = ReplaceSimilarChunk(Chunk, ExtractedSFXchunk, SFXID)
                            SFX['Range'] = Chunk
                            SFX['RangePoint'] = SFXChunkToSFXDic(Chunk)
                            SFXChunkTokens = SplitChunkIntoTokens(Chunk)
                            ResponseJson.append({"outputId": outputId, "BodyId": BodyId, "SFXChunk":{"ChunkId": ChunkId, "Chunk": OrigianlChunk, "SFX": SFX, "SFXChunkTokens": SFXChunkTokens}})
                            SFXIdCounter += 1
                            MemoryDicsCount = k + 1

    # 최종 responseJson구조 완성
    responseJson = []
    BODYID = 1
    SFXChunks = []

    for Response in ResponseJson:
        if Response['BodyId'] == BODYID:
            SFXChunks.append(Response['SFXChunk'])
        else:
            # 현재 BodyId에 대한 데이터 추가
            responseJson.append({"BodyId": BODYID, "SFXSplitedBodyChunks": SFXChunks})
            
            # 다음 BodyId까지 비어있는 BodyId를 체크하고 추가
            for emptyBodyId in range(BODYID + 1, Response['BodyId']):
                responseJson.append({"BodyId": emptyBodyId, "SFXSplitedBodyChunks": []})
            
            # 다음 BodyId로 이동
            BODYID = Response['BodyId']
            SFXChunks = [Response['SFXChunk']]

    # 마지막 BodyId에 대한 처리
    responseJson.append({"BodyId": BODYID, "SFXSplitedBodyChunks": SFXChunks})
    
    # SFX를 BodyFrameBodys의 SFX 업데이트
    SFXToBodys(projectName, email, responseJson)

    return responseJson

## 프롬프트 요청 및 결과물 Json을 SFXMatching에 업데이트
def SFXMatchingUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None, Importance = 0):
    print(f"< User: {email} | Project: {projectName} | 15_SFXMatchingUpdate 시작 >")
    # SFXMatching의 Count값 가져오기
    ContinueCount, Completion = SFXMatchingCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedSFXMatchingToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "SFXMatching", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 15_SFXMatchingUpdate는 ExistedSFXMatching으로 대처됨 ]\n")
        else:
            responseJson = SFXMatchingResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode, importance = Importance)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            SFXBodyId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'SFXMatchingUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f"SFXMatchingUpdate: {Update['BodyId']}")
                time.sleep(0.0001)
                SFXSplitedBodyChunks = Update['SFXSplitedBodyChunks']
                AddSFXSplitedBodysToDB(projectName, email, SFXSplitedBodyChunks)

                # i값 수동 업데이트
                i += 1

            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            SFXMatchingCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 15_SFXMatchingUpdate 완료 ]\n")

    else:
        print(f"[ User: {email} | Project: {projectName} | 15_SFXMatchingUpdate는 이미 완료됨 ]\n")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################