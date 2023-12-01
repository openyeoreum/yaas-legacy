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
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import AddExistedCorrectionKoToDB, AddCorrectionKoChunksToDB, CorrectionKoCountLoad, CorrectionKoCompletionUpdate
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
        TaskBody = BodyFrameBodys[i]['Correction']

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
## DiffINPUT과 DiffOUTPUT의 공통부분을 찾고 아닌 앞부분 출력
def CommonSubstring(INPUT, OUTPUT):
  m = [[0] * (1 + len(OUTPUT)) for i in range(1 + len(INPUT))]
  longest, x_longest = 0, 0
  for x in range(1, 1 + len(INPUT)):
      for y in range(1, 1 + len(OUTPUT)):
          if INPUT[x - 1] == OUTPUT[y - 1]:
              m[x][y] = m[x - 1][y - 1] + 1
              if m[x][y] > longest:
                  longest = m[x][y]
                  x_longest = x
          else:
              m[x][y] = 0

  return INPUT[x_longest - longest: x_longest]

## DiffINPUT과 DiffOUTPUT의 공통부분을 찾고 아닌 앞부분 출력
def CommonPart(DiffINPUT, DiffOUTPUT, commonSubstring):
  nonCommonPartInput = DiffINPUT.split(commonSubstring)[0] if commonSubstring in DiffINPUT else ''
  nonCommonPartOutput = DiffOUTPUT.split(commonSubstring)[0] if commonSubstring in DiffOUTPUT else ''

  return nonCommonPartInput, nonCommonPartOutput

## DiffINPUT과 DiffOUTPUT의 공통부분을 찾고 아닌 앞부분 출력
def DiffOutputDic(Input, OutputDic):
  INPUT = re.sub(r'[^가-힣]', '', str(Input))
  INPUT = INPUT + "콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼"
  OUTPUT = re.sub(r'[^가-힣]', '', str(OutputDic))
  OUTPUT = OUTPUT + "콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼콼"

  nonCommonParts = []
  try:
    for i in range(len(INPUT)):
      if INPUT[i] != OUTPUT[i]:
        DiffINPUT = INPUT[i:i+10]
        DiffOUTPUT = OUTPUT[i:i+10]

        commonSubstring = CommonSubstring(DiffINPUT, DiffOUTPUT)
        nonCommonPartInput, nonCommonPartOutput = CommonPart(DiffINPUT, DiffOUTPUT, commonSubstring)
        nonCommonParts.append({'DiffINPUT': DiffINPUT, 'NonINPUT': nonCommonPartInput, 'DiffOUTPUT': DiffOUTPUT, 'NonOUTPUT': nonCommonPartOutput})

        if len(nonCommonPartInput) == len(nonCommonPartOutput):
          nonCommonPartInputNum = 0
          nonCommonPartOutput = 0
        else:
          nonCommonPartInputNum = len(nonCommonPartInput)
          nonCommonPartOutput = len(nonCommonPartOutput)
        commonSubstringINPUT = DiffINPUT.replace(DiffINPUT, commonSubstring)
        INPUT = INPUT[:i] + commonSubstringINPUT + INPUT[i + 10 - nonCommonPartOutput:]
        commonSubstringOUTPUT = DiffOUTPUT.replace(DiffOUTPUT, commonSubstring)
        OUTPUT = OUTPUT[:i] + commonSubstringOUTPUT + OUTPUT[i + 10 - nonCommonPartInputNum:]
  except IndexError:
      pass

  # Input과 OutputDic의 차이를 %로 환산
  INPUTnonCommonPartCount = 0
  OUTPUTnonCommonPartCount = 0
  for nonCommonPart in nonCommonParts:
    INPUTnonCommonPartCount += len(nonCommonPart['NonINPUT'])
    OUTPUTnonCommonPartCount += len(nonCommonPart['NonOUTPUT'])

  INPUTnonCommonPartCount += len(INPUT)
  OUTPUTnonCommonPartCount += len(OUTPUT)
  nonCommonPartRatio = round(abs((INPUTnonCommonPartCount - OUTPUTnonCommonPartCount)/INPUTnonCommonPartCount), 3)
  nonCommonPartRatio = (1 - nonCommonPartRatio) * 100

  return nonCommonParts, nonCommonPartRatio

## ● 을 [n]으로 변경
def DotsToNumbers(DotsText):
    parts = DotsText.split('●')
    numtext = ''.join(f'{part}[{i}]' for i, part in enumerate(parts, start=1) if part.strip())
    return numtext

## [n] 을 ●으로 변경
def NumbersToDots(NumText):
    text = re.sub(r'\[\d+\]', '●', NumText)
    return text

## CorrectionKo의 Filter(Error 예외처리)
def CorrectionKoFilter(DotsInput, responseData, InputDots, InputChunkId):
    responseData = NumbersToDots(responseData)
    responseData = responseData.replace('<끊어읽기보정>\n\n', '')
    responseData = responseData.replace('<끊어읽기보정>\n', '')
    responseData = responseData.replace('<끊어읽기보정>', '')
    responseData = responseData.replace('●\n\n\n\n', '●')
    responseData = responseData.replace('●\n\n\n', '●')
    responseData = responseData.replace('●\n\n', '●')
    responseData = responseData.replace('●\n', '●')
    responseData = responseData.replace('●  ', '●')
    responseData = responseData.replace('  ●', '●')
    responseData = responseData.replace('● ', '●')
    responseData = responseData.replace(' ●', '●')
    responseData = responseData.replace('{', '[')
    responseData = responseData.replace('}', ']')
    responseData = responseData.rstrip('●')
    
    OutputDic = responseData.split('●')
    OutputDic = [Output for Output in OutputDic if Output]
    InputDic = DotsInput.split('●')
    InputDic = [Input for Input in InputDic if Input]

    # Error1: 결과가 list가 아닐 때의 예외 처리
    if not isinstance(OutputDic, list):
        return "JSONType에서 오류 발생: JSONTypeError"  
    # Error2: INPUT, OUTPUT 불일치시 예외 처리
    nonCommonParts, nonCommonPartRatio = DiffOutputDic(InputDic, OutputDic)
    if nonCommonPartRatio < 98.5:
        return f"INPUT, OUTPUT 불일치율 1.5% 이상 오류 발생: 불일치율({nonCommonPartRatio}), 불일치요소({len(nonCommonParts)})"
    # Error3: InputDots, responseDataDots 불일치시 예외 처리
    if InputDots != len(OutputDic):
        return f"INPUT, OUTPUT [n] 불일치 오류 발생: INPUT({InputDots}), OUTPUT({len(OutputDic)})"
    # Error4: Input, responseData 불일치시 예외 처리
    for i in range(len(InputDic)):
        CleanInput = re.sub("[^가-힣]", "", InputDic[i])
        CleanOutput = re.sub("[^가-힣]", "", OutputDic[i])
        if CleanInput != CleanOutput:
            diff = list(difflib.ndiff(CleanInput, CleanOutput))
            # 차이점을 저장할 리스트
            NonINPUT = ""
            NonOUTPUT = ""
            # 차이점 추출
            for d in diff:
                if d.startswith('- '):
                    NonINPUT += d[2:]
                elif d.startswith('+ '):
                    NonOUTPUT += d[2:]
            for j in range(len(nonCommonParts)):
                if nonCommonParts[j]['NonINPUT'] != NonINPUT or nonCommonParts[j]['NonOUTPUT'] != NonOUTPUT:
                    return f"INPUT, OUTPUT [n] 불일치 오류 발생: INPUT({InputDic}), OUTPUT({OutputDic})"

    return {'json': OutputDic, 'filter': OutputDic, 'nonCommonParts': nonCommonParts}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def CorrectionKoInputMemory(inputMemoryDics, MemoryLength):
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
def CorrectionKoOutputMemory(outputMemoryDics, MemoryLength):
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
## CorrectionKo 프롬프트 요청 및 결과물 Json화
def CorrectionKoProcess(projectName, email, Process = "CorrectionKo", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    InputList, inputChunkIdList = BodyFrameBodysToInputList(projectName, email)
    FineTuningMemoryList = BodyFrameBodysToInputList(projectName, email, Task = "Body")
    TotalCount = 0
    ProcessCount = 1
    ContinueCount = 0
    inputMemoryDics = []
    inputMemory = []
    InputDic = InputList[0]
    InputChunkId = inputChunkIdList[0]
    inputMemoryDics.append(InputDic)
    outputMemoryDics = []
    outputMemory = []
    nonCommonPartList = []
        
    # CorrectionKoProcess
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
            DotsInput = InputDic['Continue']
            # Input의 [n] 전처리
            DotsInput = DotsInput.replace('\n\n\n\n●', '●\n\n\n\n')
            DotsInput = DotsInput.replace('\n\n\n●', '●\n\n\n')
            DotsInput = DotsInput.replace('\n\n●', '●\n\n')
            DotsInput = DotsInput.replace('\n●', '●\n')
            DotsInput = DotsInput.replace('[', '{')
            DotsInput = DotsInput.replace(']', '}')
            InputDots = str(DotsInput).count('●')
            Input = DotsToNumbers(DotsInput)
            
            # Filter, MemoryCounter, OutputEnder 처리
            memoryCounter = f" - 중요: 꼼꼼한 끊어읽기!, [1] ~ [{InputDots}]까지 그대로 유지! -\n"
            outputEnder = ""
            
            # Response 생성
            Response, Usage, Model = LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)

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
         
            Filter = CorrectionKoFilter(DotsInput, responseData, InputDots, InputChunkId)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{len(InputList)} | {Filter}")
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                nonCommonParts = Filter['nonCommonParts']
                print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{len(InputList)} | JSONDecode 완료")
                
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
            InputChunkId = inputChunkIdList[TotalCount]
            inputMemoryDics.append(InputDic)
            inputMemory = CorrectionKoInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = CorrectionKoOutputMemory(outputMemoryDics, MemoryLength)
        
        # nonCommonPartList 형성
        nonCommonPartList.append(nonCommonParts)
    
    return outputMemoryDics, nonCommonPartList

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
## Chunk를 Tokens로 치환
def SplitChunkIntoTokens(Chunk):

    pattern = r"""
        (?P<Pause>\(\d\.\d\)) | # 끊어읽기 '(0.n)'
        (?P<SFX>\{효과음\d+\}) | # 효과음 '{효과음n}'
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
def CorrectionKoResponseJson(projectName, email, messagesReview = 'off', mode = "Memory"):
    # Chunk, ChunkId 데이터 추출
    project = GetProject(projectName, email)
    BodyFrameSplitedBodyScripts = project.HalfBodyFrame[1]['SplitedBodyScripts'][1:]
    
    # 데이터 치환
    outputMemoryDics, nonCommonPartList = CorrectionKoProcess(projectName, email, MessagesReview = messagesReview, Mode = mode)
    
    ########## 테스트 후 삭제 ##########
    filePath = f"/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/yeoreum00128@gmail.com_{projectName}_26_outputMemoryDics_231128.json"
    with open(filePath, "w", encoding = 'utf-8') as file:
        json.dump(outputMemoryDics, file, ensure_ascii = False, indent = 4)
    # with open(filePath, "r", encoding = 'utf-8') as file:
    #     outputMemoryDics = json.load(file)
    ########## 테스트 후 삭제 ##########

    # 기존 데이터 구조 responseJson 형성
    outputMemoryDicsList = []
    for i in range(len(outputMemoryDics)):
        for j in range(len(outputMemoryDics[i])):
            outputMemoryDicsList.append({"outputId": i, "Output": outputMemoryDics[i][j]})
    
    responseJson = []
    ChunkIds = []
    CorrectionChunks = []
    k = 0
    for i in range(len(BodyFrameSplitedBodyScripts)):
        CorrectionKoSplitedBody = {"OutputId": None, "BodyId": i + 1, "ChunkId": [], "CorrectionChunks": []}
        for j in range(len(BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks'])):
            Tag = BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks'][j]['Tag']
            CorrectionChunk = outputMemoryDicsList[k]['Output']
            CorrectionChunkTokens = SplitChunkIntoTokens(CorrectionChunk)
            CorrectionChunks.append({'Tag': Tag, 'CorrectionChunkTokens': CorrectionChunkTokens})
            OutputId = outputMemoryDicsList[k]['outputId']
            ChunkIds.append(k + 1) 
            k += 1

        CorrectionKoSplitedBody['OutputId'] = OutputId + 1
        CorrectionKoSplitedBody['ChunkId'] = ChunkIds
        CorrectionKoSplitedBody['CorrectionChunks'] = CorrectionChunks
        ChunkIds = []
        CorrectionChunks = []
        responseJson.append(CorrectionKoSplitedBody)
    
    # responseJson의 끊어읽기 보정(말의 끝맺음 뒤에 끊어읽기가 존재할 경우 삭제)
    for i in range(len(responseJson)):
        for j in range(len(responseJson[i]['CorrectionChunks'])):
            tokens = responseJson[i]['CorrectionChunks'][j]['CorrectionChunkTokens']
            if len(tokens) >= 2:
                BeforeEndtoken = tokens[-2]
                Endtoken = tokens[-1]
                if 'Period' in BeforeEndtoken and 'Pause' in Endtoken:
                    del tokens[-1]
                for k in range(len(tokens) - 6):
                    if 'Comma' in tokens[k] and 'Pause' in tokens[k+1]:
                        del tokens[k]
                    elif 'Pause' in tokens[k] and 'Comma' in tokens[k+1]:
                        del tokens[k+1]
                for l in range(len(tokens) - 6):
                    if 'Ko' in tokens[l] and 'Period' in tokens[l+1] and 'Pause' in tokens[l+2]:
                        del tokens[l+2]

                    
    # responseJson의 끊어읽기 보정(끝맺음 부분 끊어읽기 추가)
    for i in range(len(responseJson)):
        for j in range(len(responseJson[i]['CorrectionChunks'])):
            tag = responseJson[i]['CorrectionChunks'][j]['Tag']
            
            Aftertag = None
            if j < (len(responseJson[i]['CorrectionChunks']) - 1):
                Aftertag = responseJson[i]['CorrectionChunks'][j + 1]['Tag']
                
            AfterAftertag = None
            if j < (len(responseJson[i]['CorrectionChunks']) - 2):
                AfterAftertag = responseJson[i]['CorrectionChunks'][j + 2]['Tag']
            
            # 새로운 조건을 위한 변수
            NextChunkFirstTag = None
            if i < (len(responseJson) - 1):
                NextChunkFirstTag = responseJson[i+1]['CorrectionChunks'][0]['Tag']
            
            tokens = responseJson[i]['CorrectionChunks'][j]['CorrectionChunkTokens']
            
            if tag == "Title":
                tokens.append({"Pause": "(2.0)"})
                tokens.append({"Enter": "\n"})
            elif tag in ["Logue", "Part", "Chapter"]:
                tokens.append({"Pause": "(1.5)"})
                tokens.append({"Enter": "\n"})
            elif tag == "Index":
                tokens.append({"Pause": "(1.3)"})
                tokens.append({"Enter": "\n"})
            elif tag == "Caption":
                tokens.append({"Pause": "(1.2)"})
                tokens.append({"Enter": "\n"})
            else:
                if len(tokens) >= 2:
                    BeforeEndtoken = tokens[-2]
                    Endtoken = tokens[-1]
                    if 'Ko' in BeforeEndtoken and 'Period' in Endtoken:
                        tokens.append({"Pause": "(0.7)"})
                        tokens.append({"Enter": "\n"})
                    for k in range(len(tokens) - 5):
                        if 'Ko' in tokens[k] and 'Period' in tokens[k+1]:
                            tokens.insert(k + 2, {"Pause": "(0.6)"})
            
            # 앞, 뒤Chunk를 통한 처리
            if tag == "Character" and Aftertag == "Character":
                tokens.append({"Pause": "(0.7)"})
                tokens.append({"Enter": "\n"})
            elif tag == "Character" and Aftertag == "Narrator":
                tokens.append({"Pause": "(0.2)"})
                tokens.append({"Enter": "\n"})
            elif tag == "Character" and Aftertag == "Comment":
                tokens.append({"Pause": "(0.2)"})
                tokens.append({"Enter": "\n"})
            elif tag == "Narrator" and Aftertag == "Character":
                if len(tokens) >= 2:
                    BeforeEndtoken = tokens[-2]
                    Endtoken = tokens[-1]
                    if 'Pause' not in BeforeEndtoken and 'Pause' not in Endtoken and 'Comma' not in BeforeEndtoken and 'Comma' not in Endtoken:
                        tokens.append({"Pause": "(0.4)"})
                        tokens.append({"Enter": "\n"})
            elif (tag == "Narrator" and Aftertag == "Comment") or (tag == "Caption" and Aftertag == "CaptionComment"):
                if len(tokens) >= 2:
                    BeforeEndtoken = tokens[-2]
                    Endtoken = tokens[-1]
                    if ('Pause' not in BeforeEndtoken and 'Pause' not in Endtoken) or ('Comma' not in BeforeEndtoken and 'Comma' not in Endtoken):
                        tokens.append({"Pause": "(0.2)"})

            # Chunk가 중간에 끊길 경우 처리
            if tag == "Character" and j == (len(responseJson[i]['CorrectionChunks']) - 1) and NextChunkFirstTag == "Character":
                tokens.append({"Pause": "(0.7)"})
                tokens.append({"Enter": "\n"})
            elif tag == "Character" and j == (len(responseJson[i]['CorrectionChunks']) - 1) and NextChunkFirstTag == "Narrator":
                tokens.append({"Pause": "(0.2)"})
                tokens.append({"Enter": "\n"})
            elif tag == "Character" and j == (len(responseJson[i]['CorrectionChunks']) - 1) and NextChunkFirstTag == "Comment":
                tokens.append({"Pause": "(0.2)"})
                tokens.append({"Enter": "\n"})
            elif tag == "Narrator" and j == (len(responseJson[i]['CorrectionChunks']) - 1) and NextChunkFirstTag == "Character":
                if len(tokens) >= 2:
                    BeforeEndtoken = tokens[-2]
                    Endtoken = tokens[-1]
                    if 'Pause' not in BeforeEndtoken and 'Pause' not in Endtoken and 'Comma' not in BeforeEndtoken and 'Comma' not in Endtoken:
                        tokens.append({"Pause": "(0.4)"})
                        tokens.append({"Enter": "\n"})
            elif (tag == "Narrator" and j == (len(responseJson[i]['CorrectionChunks']) - 1) and NextChunkFirstTag == "Comment") or (tag == "Caption" and j == (len(responseJson[i]['CorrectionChunks']) - 1) and NextChunkFirstTag == "CaptionComment"):
                if len(tokens) >= 2:
                    BeforeEndtoken = tokens[-2]
                    Endtoken = tokens[-1]
                    if 'Pause' not in BeforeEndtoken and 'Pause' not in Endtoken and 'Comma' not in BeforeEndtoken and 'Comma' not in Endtoken:
                        tokens.append({"Pause": "(0.2)"})

    ########## 테스트 후 삭제 ##########
    filePath2 = f"/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/yeoreum00128@gmail.com_{projectName}_26_responseJson_231128.json"
    
    with open(filePath2, "w", encoding = 'utf-8') as file:
        json.dump(responseJson, file, ensure_ascii = False, indent = 4)
    
    responseJsonText = ""
    for i in range(len(responseJson)):
        for j in range(len(responseJson[i]['CorrectionChunks'])):
            for token_dict in responseJson[i]['CorrectionChunks'][j]['CorrectionChunkTokens']:
                # 딕셔너리에서 value 추출 (딕셔너리의 첫 번째 값)
                token = next(iter(token_dict.values()))
                responseJsonText += token

    filePath3 = f"/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/yeoreum00128@gmail.com_{projectName}_26_responseJson_231128.txt"
    # 텍스트 파일에 저장
    with open(filePath3, "w", encoding="utf-8") as file:
        file.write(responseJsonText)
    ########## 테스트 후 삭제 ##########
    
    # return responseJson

## 프롬프트 요청 및 결과물 Json을 CorrectionKo에 업데이트
def CorrectionKoUpdate(projectName, email, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 26_CorrectionKoUpdate 시작 >")
    # SummaryBodyFrame의 Count값 가져오기
    ContinueCount, ContextCount, Completion = CorrectionKoCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedCorrectionKoToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "CorrectionKo", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 26_CorrectionKoUpdate는 ExistedCorrectionKo으로 대처됨 ]\n")
        else:
            responseJson = CorrectionKoResponseJson(projectName, email, messagesReview = MessagesReview, mode = Mode)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            ContextChunkId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'CorrectionKoUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'CorrectionKoUpdate: {Update}')
                time.sleep(0.0001)
                ContextChunkId += 1
                ChunkId = ResponseJson[i]["ChunkId"]
                Chunk = ResponseJson[i]["Chunk"]
                Reader = ResponseJson[i]["Reader"]
                Purpose = ResponseJson[i]["Purpose"]
                Subject = ResponseJson[i]["Subject"]
                Phrases = ResponseJson[i]["Phrases"]
                Importance = ResponseJson[i]["Importance"]
                
                AddCorrectionKoChunksToDB(projectName, email, ContextChunkId, ChunkId, Chunk, Reader, Purpose, Subject, Phrases, Importance)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            CorrectionKoCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 26_CorrectionKoUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 26_CorrectionKoUpdate는 이미 완료됨 ]\n")
    
    
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################
    CorrectionKoResponseJson(projectName, email)