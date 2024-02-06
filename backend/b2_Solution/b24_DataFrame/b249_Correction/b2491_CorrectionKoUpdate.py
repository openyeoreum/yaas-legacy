import os
import re
import json
import time
import difflib
import sys
sys.path.append("/yaas")

from datetime import datetime
from tqdm import tqdm
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, LoadAddOutputMemory, SaveOutputMemory, SaveAddOutputMemory, AddExistedCorrectionKoToDB, AddCorrectionKoSplitedBodysToDB, AddCorrectionKoChunksToDB, CorrectionKoCountLoad, CorrectionKoCompletionUpdate
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
        TaskBody = BodyFrameBodys[i]['SFX']

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

## DiffINPUT과 DiffOUTPUT중 가장 긴 공통문자열 찾기(CleanInput의 replace를 통한 데이터 무결성 확인)
def LongCommonSubstring(DiffINPUT, DiffOUTPUT):
    # Create a matrix to keep track of matches
    dp = [[0 for _ in range(len(DiffOUTPUT)+1)] for _ in range(len(DiffINPUT)+1)]
    longest, end_pos = 0, 0

    # Iterate through each character in both strings
    for i in range(1, len(DiffINPUT)+1):
        for j in range(1, len(DiffOUTPUT)+1):
            if DiffINPUT[i-1] == DiffOUTPUT[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
                if dp[i][j] > longest:
                    longest = dp[i][j]
                    end_pos = i  # Mark the end position of the common substring
            else:
                dp[i][j] = 0  # Reset if characters don't match

    # Extract the common substring
    return DiffINPUT[end_pos-longest:end_pos]

## CorrectionKo의 Filter(Error 예외처리)
def CorrectionKoFilter(DotsInput, responseData, InputDots, InputSFXTags, InPutPeriods, InputChunkId):
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
    
    OutputDic = responseData.replace('<S', '<효과음시작')
    OutputDic = responseData.replace('<E', '<효과음끝')
    OutputDic = responseData.split('●')
    OutputDic = [Output for Output in OutputDic if Output]
    OutputDic = [item for item in OutputDic if item.strip() != '']
    InputDic = DotsInput.split('●')
    InputDic = [Input for Input in InputDic if Input]
    InputDic = [item for item in InputDic if item.strip() != '']

    # Error1: 결과가 list가 아닐 때의 예외 처리
    if not isinstance(OutputDic, list):
        return "JSONType에서 오류 발생: JSONTypeError"
    # Error2: INPUT, OUTPUT .(Periods) 불일치시 예외 처리
    OutPutPeriods = str(responseData).count('.')
    Difference = abs(OutPutPeriods - InPutPeriods) / InPutPeriods * 100
    if Difference >= 25:
        return f"INPUT, OUTPUT '.(Periods)' 불일치율 25% 이상 오류 발생: 불일치율({Difference}))"
    # Error3: INPUT, OUTPUT 불일치시 예외 처리
    try:
        nonCommonParts, nonCommonPartRatio = DiffOutputDic(InputDic, OutputDic)
        if nonCommonPartRatio < 97.5:
            return f"INPUT, OUTPUT 불일치율 2.5% 이상 오류 발생: 불일치율({nonCommonPartRatio}), 불일치요소({len(nonCommonParts)})"
    except ValueError as e:
        return f"INPUT, OUTPUT 매우 높은 불일치율 발생: {e}"
    # Error4: OUTPUT 내에 SFXTag 불일치시 예외 처리
    for SFXTag in InputSFXTags:
        if SFXTag not in responseData:
            return f"OUTPUT 내에 SFXTag 불일치 오류 발생: INPUT({SFXTag})"
    # Error5: InputDots, responseDataDots 불일치시 예외 처리
    if len(InputDic) != len(OutputDic) != InputDots:
        print(f'@@@@@@@@@@\nInputDic: {InputDic}\nOutputDic: {OutputDic}\n@@@@@@@@@@')
        return f"INPUT, OUTPUT [n] 갯수 불일치 오류 발생: INPUT({len(InputDic)}), OUTPUT({len(OutputDic)}), InputDots({InputDots})"
    # Error6: Input, responseData 불일치시 예외 처리
    nonCommonPartsNum = 0
    for i in range(len(InputDic)):
        CleanInput = re.sub("[^가-힣]", "", InputDic[i])
        CleanOutput = re.sub("[^가-힣]", "", OutputDic[i])
        
        if CleanInput != CleanOutput:
            try:
                nonCommonPart = nonCommonParts[nonCommonPartsNum]
                DiffINPUT = nonCommonPart['DiffINPUT']
                print(f'\n\n\n({i}, {nonCommonPartsNum})@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\nDiffINPUT: {DiffINPUT}')
                DiffOUTPUT = nonCommonPart['DiffOUTPUT']
                print(f'DiffOUTPUT: {DiffOUTPUT}')
                longCommonSubstring = LongCommonSubstring(DiffINPUT, DiffOUTPUT)
                longCommonSubstring = longCommonSubstring.replace('콼', '')
                print(f'longCommonSubstring: {longCommonSubstring}')
                NonINPUT = nonCommonPart['NonINPUT']
                print(f'NonINPUT: {NonINPUT}')
                NonOUTPUT = nonCommonPart['NonOUTPUT']
                print(f'NonOUTPUT: {NonOUTPUT}')
                if longCommonSubstring in CleanInput:
                    ReplaceCleanInput = CleanInput.replace(NonINPUT + longCommonSubstring, NonOUTPUT + longCommonSubstring)
                    ReplaceCleanOutput = CleanOutput
                else:
                    ReplaceCleanInput = CleanInput.replace(NonINPUT, NonOUTPUT)
                    ReplaceCleanOutput = CleanOutput.replace(NonINPUT, NonOUTPUT)
                print(f'replace1: {NonINPUT + longCommonSubstring}')
                print(f'replace2: {NonOUTPUT + longCommonSubstring}\n------------------------------------\n')
                print(f'CleanInput: {CleanInput}')
                print(f'CleanOutput: {CleanOutput}')
                print(f'ReplaceCleanInput: {ReplaceCleanInput}')
                print(f'ReplaceCleanOutput: {ReplaceCleanOutput}\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
                    
                if ReplaceCleanInput == ReplaceCleanOutput:
                    nonCommonPartsNum += 1
                else:
                    for i in range(len(CleanInput) + 1):
                        ReplaceCleanInput = CleanInput[:i] + NonOUTPUT + CleanInput[i:]
                        ReplaceCleanOutput = CleanOutput[:i] + NonINPUT + CleanOutput[i:]
                        print(f'1) ReplaceCleanInput: {ReplaceCleanInput}')
                        print(f'1) CleanOutput: {CleanOutput}\n')
                        print(f'2) CleanInput: {CleanInput}')
                        print(f'2) ReplaceCleanOutput: {ReplaceCleanOutput}\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
                        if ReplaceCleanInput == CleanOutput or CleanInput == ReplaceCleanOutput:
                            nonCommonPartsNum += 1
                            continue
                        else:
                            return f"INPUT, OUTPUT [n] 불일치 오류 발생: INPUT({InputDic[i]}), OUTPUT({OutputDic[i]})"
            except IndexError as e:
                return f"INPUT, OUTPUT [n] 불일치 오류 발생: IndexError({e})"

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
def CorrectionKoProcess(projectName, email, DataFramePath, Process = "CorrectionKo", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '21', DataFramePath)
    AddOutputMemoryDicsFile = LoadAddOutputMemory(projectName, email, '21', DataFramePath)
    inputList, inputChunkIdList = BodyFrameBodysToInputList(projectName, email)
    InputList = inputList[OutputMemoryCount:]
    if InputList == []:
        return OutputMemoryDicsFile, AddOutputMemoryDicsFile

    # FineTuningMemoryList = BodyFrameBodysToInputList(projectName, email, Task = "Body")
    TotalCount = 0
    ProcessCount = 1
    ContinueCount = 0
    inputMemoryDics = []
    inputMemory = []
    InputDic = InputList[0]
    InputChunkId = inputChunkIdList[0]
    inputMemoryDics.append(InputDic)
    outputMemoryDics = OutputMemoryDicsFile
    outputMemory = []
    ErrorCount = 0
    nonCommonPartList = AddOutputMemoryDicsFile
        
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
            SFXTagsPattern = r"<[SE]\d{1,5}>"
            InputSFXTags = re.findall(SFXTagsPattern, DotsInput)
            
            Input = DotsToNumbers(DotsInput)
            InPutPeriods = str(Input).count('.')
            
            # Filter, MemoryCounter, OutputEnder 처리
            memoryCounter = f" - 중요: 꼼꼼한 끊어읽기!, 띄어쓰기 맞춤법 오타 등 절대 수정 및 변경 없음!, <Sn> <En>의 기호와 [1] ~ [{InputDots}]까지 그대로 유지! -\n"
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
         
            Filter = CorrectionKoFilter(DotsInput, responseData, InputDots, InputSFXTags, InPutPeriods, InputChunkId)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                
                ErrorCount += 1
                if ErrorCount == 10:
                    print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | 오류횟수 10회 초과, 프롬프트 종료")
                    sys.exit(1)  # 오류 상태와 함께 프로그램을 종료합니다.
                    
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                nonCommonParts = Filter['nonCommonParts']
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
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '21', DataFramePath)
        SaveAddOutputMemory(projectName, email, nonCommonPartList, '21', DataFramePath)

    return outputMemoryDics, nonCommonPartList

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
## 오늘 날짜
def Date(Option = "Day"):
    if Option == "Day":
      now = datetime.now()
      date = now.strftime('%y%m%d')
    elif Option == "Second":
      now = datetime.now()
      date = now.strftime('%y%m%d%H%M%S')
    
    return date

## ResponseJson의 Text변환
def ResponseJsonText(projectName, email, responseJson):
    responseJsonText = ""
    for i in range(len(responseJson)):
        for j in range(len(responseJson[i]['CorrectionChunks'])):
            for token_dict in responseJson[i]['CorrectionChunks'][j]['CorrectionChunkTokens']:
                token = next(iter(token_dict.values()))
                responseJsonText += token

    baseFilePath = f"/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/{email}_{projectName}_21_responseJson"
    fullFilePath = f"{baseFilePath}_{str(Date())}.txt"

    # 파일이 존재하는지 확인
    if not any(re.match(f"{baseFilePath}_\d{{6}}\.txt", filename) for filename in os.listdir(os.path.dirname(baseFilePath))):
        with open(fullFilePath, "w", encoding="utf-8") as file:
            file.write(responseJsonText)

## Chunk를 Tokens로 치환
def SplitChunkIntoTokens(Chunk):
    pattern = r"""
        (?P<Pause>\(\d\.\d\)) | # 끊어읽기 '(0.n)'
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
def CorrectionKoResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):
    # Chunk, ChunkId 데이터 추출
    project = GetProject(projectName, email)
    BodyFrameSplitedBodyScripts = project.HalfBodyFrame[1]['SplitedBodyScripts'][1:]

    # 데이터 치환
    outputMemoryDics, nonCommonPartList = CorrectionKoProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)

    # 기본 Chunks 생성
    InputList = []
    for i in range(len(BodyFrameSplitedBodyScripts)):
        SplitedBodyChunks = BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks']
        for j in range(len(SplitedBodyChunks)):
            ChunkId = SplitedBodyChunks[j]['ChunkId']
            Tag = SplitedBodyChunks[j]['Tag']
            Chunk = SplitedBodyChunks[j]['Chunk']
            InputList.append({'ChunkId': ChunkId, 'Tag': Tag, 'Chunk': Chunk})

    # 기존 데이터 구조 ResponseJson 형성
    OutputList = []
    chunkId = 1
    for i in range(len(outputMemoryDics)):
        OutputId = i + 1
        outputMemory = outputMemoryDics[i]
        for j in range(len(outputMemory)):
            ChunkId = chunkId
            CorrectionChunk = outputMemory[j]
            OutputList.append({'OutputId': OutputId, 'ChunkId': ChunkId, 'CorrectionChunk': CorrectionChunk})
        
    # ResponseJson 생성
    ResponseJson = []
    for i in range(len(InputList)):
        ChunkId = InputList[i]['ChunkId']
        Tag = InputList[i]['Tag']
        CorrectionChunk = OutputList[i]['CorrectionChunk']
        CorrectionChunkTokens = SplitChunkIntoTokens(CorrectionChunk)
        ResponseJson.append({'ChunkId': ChunkId, 'Tag': Tag, 'CorrectionChunk': CorrectionChunk, 'CorrectionChunkTokens': CorrectionChunkTokens})

    # ResponseJson의 끊어읽기 보정(말의 끝맺음 뒤에 끊어읽기가 존재할 경우 삭제)
    for i in range(len(ResponseJson)):
        
        tokens = ResponseJson[i]['CorrectionChunkTokens']
        
        if len(tokens) >= 2:
            BeforeEndtoken = tokens[-2]
            Endtoken = tokens[-1]
            if 'Period' in BeforeEndtoken and 'Pause' in Endtoken:
                del tokens[-1]
            elif 'Pause' in BeforeEndtoken and 'Period' in Endtoken:
                del tokens[-2]
            elif 'Period' in BeforeEndtoken and 'SFXEnd' in Endtoken:
                tokens[-2], tokens[-1] = tokens[-1], tokens[-2]

        if len(tokens) >= 4:
            PreviousPreviousBeforeEndtoken = tokens[-4]
            PreviousBeforeEndtoken = tokens[-3]
            BeforeEndtoken = tokens[-2]
            Endtoken = tokens[-1]
            if 'Period' in PreviousPreviousBeforeEndtoken and 'SFXEnd' in PreviousBeforeEndtoken and 'SFXEnd' in BeforeEndtoken and 'SFXEnd' in Endtoken:
                tokens[-4], tokens[-3], tokens[-2], tokens[-1] = tokens[-1], tokens[-4], tokens[-3], tokens[-2]
            elif 'Period' in PreviousBeforeEndtoken and 'SFXEnd' in BeforeEndtoken and 'SFXEnd' in Endtoken:
                tokens[-3], tokens[-2], tokens[-1] = tokens[-1], tokens[-3], tokens[-2]

        if len(tokens) >= 5:
            PreviousBeforeEndtoken = tokens[-3]
            BeforeEndtoken = tokens[-2]
            Endtoken = tokens[-1]
            for j in range(len(tokens) - 5):
                try:
                    if 'Comma' in tokens[j] and 'Pause' in tokens[j+1]:
                        del tokens[j]
                    elif 'Pause' in tokens[j] and 'Comma' in tokens[j+1]:
                        del tokens[j+1]
                    elif ('Ko' in tokens[j] and 'Period' in tokens[j+1] and 'Pause' in tokens[j+2]) or ('En' in tokens[j] and 'Period' in tokens[j+1] and 'Pause' in tokens[j+2]) or ('SFXEnd' in tokens[j] and 'Period' in tokens[j+1] and 'Pause' in tokens[j+2]):
                        del tokens[j+2]
                except IndexError:
                    pass
                        
    # ResponseJson의 끊어읽기 보정(끝맺음 부분 끊어읽기 추가)
    for i in range(len(ResponseJson)):
        tag = ResponseJson[i]['Tag']
        
        Aftertag = None
        if i < (len(ResponseJson) - 1):
            Aftertag = ResponseJson[i+1]['Tag']
            
        AfterAftertag = None
        if i < (len(ResponseJson) - 2):
            AfterAftertag = ResponseJson[i+2]['Tag']
        
        tokens = ResponseJson[i]['CorrectionChunkTokens']
        
        # Title, 일반 문장 처리
        if tag == "Title":
            tokens.append({"Pause": "(2.0)"})
            tokens.append({"Enter": "\n"})
        elif tag in ["Logue", "Part", "Chapter"]:
            tokens.append({"Pause": "(1.5)"})
            tokens.append({"Enter": "\n"})
        elif tag == "Index":
            tokens.append({"Pause": "(1.3)"})
            tokens.append({"Enter": "\n"})
        elif tag == "Caption" and Aftertag != "Caption" or tag == "Caption" and Aftertag != "CaptionComment":
            tokens.append({"Pause": "(1.2)"})
            tokens.append({"Enter": "\n"})
        # elif tag == "Comment":
        #     tokens.append({"Pause": "(0.4)"})
        #     tokens.append({"Enter": "\n"})
        else:
            if len(tokens) >= 2:
                BeforeEndtoken = tokens[-2]
                Endtoken = tokens[-1]
                if ('Ko' in BeforeEndtoken and 'Period' in Endtoken) or ('En' in BeforeEndtoken and 'Period' in Endtoken) or ('SFXEnd' in BeforeEndtoken and 'Period' in Endtoken):
                    tokens.append({"Pause": "(0.7)"})
                    tokens.append({"Enter": "\n"})
                if len(tokens) >= 5:
                    for k in range(len(tokens) - 5):
                        if ('Ko' in tokens[k] and 'Period' in tokens[k+1]) or ('En' in tokens[k] and 'Period' in tokens[k+1]) or ('SFXEnd' in tokens[k] and 'Period' in tokens[k+1]):
                            tokens.insert(k + 2, {"Pause": "(0.6)"})

        RemoveSFXtokens = [item for item in tokens if "SFXEnd" not in item and "SFXStart" not in item]
        
        # 앞, 뒤Chunk를 통한 처리
        if tag == "Character" and Aftertag == "Character":
            tokens.append({"Pause": "(0.7)"})
            tokens.append({"Enter": "\n"})
        elif tag == "Character" and Aftertag == "Narrator":
            tokens.append({"Pause": "(0.3)"})
            tokens.append({"Enter": "\n"})
        elif tag == "Character" and Aftertag == "Comment":
            tokens.append({"Pause": "(0.2)"})
            tokens.append({"Enter": "\n"})
        elif tag == "Narrator" and Aftertag == "Character":
            if len(RemoveSFXtokens) >= 2:
                BeforeEndtoken = RemoveSFXtokens[-2]
                Endtoken = RemoveSFXtokens[-1]
                if 'Pause' not in BeforeEndtoken and 'Pause' not in Endtoken and 'Comma' not in BeforeEndtoken and 'Comma' not in Endtoken:
                    tokens.append({"Pause": "(0.4)"})
                    tokens.append({"Enter": "\n"})
        elif (tag == "Narrator" and Aftertag == "Comment") or (tag == "Caption" and Aftertag == "CaptionComment"):
            if len(RemoveSFXtokens) >= 2:
                BeforeEndtoken = RemoveSFXtokens[-2]
                Endtoken = RemoveSFXtokens[-1]
                if 'Pause' not in BeforeEndtoken and 'Pause' not in Endtoken and 'Comma' not in BeforeEndtoken and 'Comma' not in Endtoken:
                    tokens.append({"Pause": "(0.2)"})

    # responseJson 구조 형성###
    responseJson = []
    ResponseCount = 0
    for i in range(len(BodyFrameSplitedBodyScripts)):
        SplitedBodyChunks = BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks']
        BodyId = BodyFrameSplitedBodyScripts[i]['SplitedBodyChunks']
        CorrectionChunks = []
        for j in range(len(SplitedBodyChunks)):
            ChunkId = ResponseJson[ResponseCount]['ChunkId']
            Tag = ResponseJson[ResponseCount]['Tag']
            CorrectionChunkTokens = ResponseJson[ResponseCount]['CorrectionChunkTokens']
            CorrectionChunks.append({'ChunkId': ChunkId, 'Tag': Tag, 'CorrectionChunkTokens': CorrectionChunkTokens})
            ResponseCount += 1
        CorrectionKoSplitedBody = {'BodyId': BodyId, 'CorrectionChunks': CorrectionChunks}
        responseJson.append(CorrectionKoSplitedBody)
            
    # JSON 파일로 저장
    with open('/yaas/response.json', 'w', encoding = 'utf-8') as file:
        json.dump(responseJson, file, ensure_ascii = False, indent = 4)

    # ResponseJson의 Text변환
    ResponseJsonText(projectName, email, responseJson)
                        
    return responseJson

## 프롬프트 요청 및 결과물 Json을 CorrectionKo에 업데이트
def CorrectionKoUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 21_CorrectionKoUpdate 시작 >")
    # CorrectionKo의 Count값 가져오기
    ContinueCount, ContextCount, Completion = CorrectionKoCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedCorrectionKoToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "CorrectionKo", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 21_CorrectionKoUpdate는 ExistedCorrectionKo으로 대처됨 ]\n")
        else:
            responseJson = CorrectionKoResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
            
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
                UpdateTQDM.set_description(f"CorrectionKoUpdate: {Update['BodyId']}")
                time.sleep(0.0001)
                AddCorrectionKoSplitedBodysToDB(projectName, email)
                for j in range(len(Update['CorrectionChunks'])):
                    ChunkId = Update['CorrectionChunks'][j]['ChunkId']
                    Tag = Update['CorrectionChunks'][j]['Tag']
                    ChunkTokens = Update['CorrectionChunks'][j]['CorrectionChunkTokens']
                
                    AddCorrectionKoChunksToDB(projectName, email, ChunkId, Tag, ChunkTokens)

                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            CorrectionKoCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 21_CorrectionKoUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 21_CorrectionKoUpdate는 이미 완료됨 ]\n")
    
    
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s11_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################