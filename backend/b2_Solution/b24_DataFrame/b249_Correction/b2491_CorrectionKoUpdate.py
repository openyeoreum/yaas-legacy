import os
import re
import json
import unicodedata
import random
import time
import difflib
import tiktoken
import sys
sys.path.append("/yaas")

from datetime import datetime
from tqdm import tqdm
from backend.b1_Api.b14_Models import User
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
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
def BodyFrameBodysToInputList(projectName, email):
    BodyFrameSplitedBodyScripts, BodyFrameBodys = LoadBodyFrameBodys(projectName, email)
    
    # 토큰 계산을 위한 encoder 초기화
    encoder = tiktoken.get_encoding("cl100k_base")
    
    inputList = []
    prev_task = None
    accumulatedTokens = 0  # 연속되는 'Caption' 작업의 토큰 수를 누적합니다.

    for i in range(len(BodyFrameBodys)):
        Id = BodyFrameBodys[i]['BodyId']
        task = BodyFrameBodys[i]['Task']
        TaskBody = BodyFrameBodys[i]['SFX']
        taskTokens = len(encoder.encode(TaskBody))  # 현재 작업의 토큰 수를 계산합니다.

        if 'Body' in task:
            Tag = 'Continue'
            accumulatedTokens = 0  # 'Caption' 외의 작업에서는 누적 토큰 수를 초기화합니다.
        elif 'Caption' in task:
            # 'Caption' 작업이 연속되는 경우 토큰 수를 누적하고, 750을 초과하는지 확인합니다.
            if 'Caption' in prevTask and (accumulatedTokens + taskTokens) > 750:
                Tag = 'Continue'  # 누적 토큰 수가 750을 초과하면 Tag를 'Continue'로 설정합니다.
                accumulatedTokens = taskTokens  # 토큰 수를 현재 작업의 토큰 수로 재설정합니다.
            else:
                Tag = 'Merge'
                accumulatedTokens += taskTokens  # 토큰 수를 누적합니다.
        elif 'Body' not in task:
            Tag = 'Merge'
            accumulatedTokens = 0
        else:
            Tag = 'Pass'
            accumulatedTokens = 0

        # 단일 작업의 토큰 수가 750을 초과하는 경우 처리
        if taskTokens > 750:
            Tag = 'Continue'
        
        InputDic = {'Id': Id, Tag: TaskBody}
        inputList.append(InputDic)
        
        prevTask = task  # 이전 작업을 현재 작업으로 업데이트합니다.

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

## [n] 불일치 오류시 이를 찾을 수 있도록 UnmatchedSpotsText를 작성
def FindUnmatchedChunkAndSpot(InputText, CorrectionText):
    # Find all chunk markers in the InputText and corrected texts
    InputChunks = re.findall(r'\[\d+\]', InputText)
    CorrectionChunks = re.findall(r'\[\d+\]', CorrectionText)

    # Find Unmatched chunk markers that are in InputText but not in CorrectionText
    Unmatched = list(set(InputChunks) - set(CorrectionChunks))

    # Initialize list to store the Unmatched spots
    UnmatchedSpots = []

    # For each Unmatched chunk marker, find the surrounding text in the InputText string
    for chunk in Unmatched:
        # Pattern to find the text immediately before and after the Unmatched chunk marker
        pattern = r'(.{0,10}\s?)' + re.escape(chunk) + r'(\s?.{0,10})'
        SpotSearch = re.search(pattern, InputText)
        if SpotSearch:
            UnmatchedSpot = SpotSearch.group(1) + chunk + SpotSearch.group(2)
            UnmatchedSpots.append(UnmatchedSpot)
            
    UnmatchedText = ' | '.join(Unmatched)
    UnmatchedSpotsText = " | ".join([f"...{text}..." for text in UnmatchedSpots])

    return UnmatchedText, UnmatchedSpotsText

## Response결과에 SFX 중복 발생시 이를 여러개의 리스트로 나누는 작업
def generateOutputDicList(output_dic, sfx_tag):
    # Finding all instances of the tag
    instances = []
    for i, text in enumerate(output_dic):
        start = 0
        while start != -1:
            start = text.find(sfx_tag, start)
            if start != -1:
                instances.append((i, start))
                start += len(sfx_tag)
    
    # Creating a list for each instance where it's the only one present
    output_dic_list = []
    for instance_index, _ in enumerate(instances):
        new_version = []
        for i, text in enumerate(output_dic):
            if any(instance[0] == i for instance in instances):
                # Removing all instances of the tag in this text
                new_text = text.replace(sfx_tag, "")
                # Re-adding the tag only for the current instance
                if instances[instance_index][0] == i:
                    tag_position = instances[instance_index][1]
                    new_text = new_text[:tag_position] + sfx_tag + new_text[tag_position:]
                new_version.append(new_text)
            else:
                new_version.append(text)
        output_dic_list.append(new_version)

    return output_dic_list

## CleanInput과 CleanOutput내에 replace해야 하는 대상 문자가 여러개일(1글자인 경우 그런 유행이 많음) 경우 하나씩 replace 하여 모두를 비교확인
def ReplaceNthOccurrence(CleanText, NonINPUT, NonOUTPUT, n):
    pos = -1
    for _ in range(n):
        pos = CleanText.find(NonINPUT, pos + 1)
        if pos == -1:  # 찾고자 하는 대상이 더 이상 없으면 종료
            return CleanText
    # 찾은 위치에서 교체를 수행
    return CleanText[:pos] + NonOUTPUT + CleanText[pos+len(NonINPUT):]

## CorrectionKo의 Filter(Error 예외처리)
def CorrectionKoFilter(Input, DotsInput, responseData, InputDots, InputSFXTags, InPutPeriods, InputChunkId, ErrorCount):
    # Error1: 결과가 마지막까지 생성되지 않을 경우 예외 처리
    if f'[{InputDots}]' not in responseData:
        return f"OUTPUT의 마지막 [{InputDots}]이 생성되지 않음, OUTPUT이 덜 생성됨"
    
    # [n] 불일치 오류시 이를 찾을 수 있도록 CorrectionText를 미리 저장
    CorrectionText = responseData
    
    # [n]을 통해 문장 분리 및 전처리가 가능하도록 [n]을 '●'로 치환
    responseData = NumbersToDots(responseData)
    LastTagIndex = responseData.rfind("<끊어읽기보정>")
    if LastTagIndex != -1:
        responseData = responseData[LastTagIndex + len("<끊어읽기보정>"):].strip()
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
    OutputDic = OutputDic.replace('<E', '<효과음끝')
    OutputDic = OutputDic.split('●')
    OutputDic = [Output for Output in OutputDic if Output]
    OutputDic = [item for item in OutputDic if item.strip() != '']

    DotsInput = DotsInput.replace('<S', '<효과음시작')
    DotsInput = DotsInput.replace('<E', '<효과음끝')
    InputDic = DotsInput.split('●')
    InputDic = [Input for Input in InputDic if Input]
    InputDic = [item for item in InputDic if item.strip() != '']

    # Error2: 결과가 list가 아닐 때의 예외 처리
    if not isinstance(OutputDic, list):
        return "JSONType에서 오류 발생: JSONTypeError"
    # # Error2: INPUT, OUTPUT .(Periods) 불일치시 예외 처리
    # if InPutPeriods > 1:
    #     PeriodsPattern = r"(?<!\d)\.(?!\d)"
    #     OutPutPeriods = len(re.findall(PeriodsPattern, responseData))
    #     Difference = abs(OutPutPeriods - InPutPeriods) / InPutPeriods * 100
    #     if Difference > 25:
    #         return f"INPUT, OUTPUT '.(Periods)' 불일치율 25% 이상 오류 발생: 불일치율({Difference}))"
    # Error2: INPUT, OUTPUT .(Periods) 불일치시 예외 처리
    # Error3: INPUT, OUTPUT 불일치시 예외 처리
    try:
        nonCommonParts, nonCommonPartRatio = DiffOutputDic(InputDic, OutputDic)
        if nonCommonPartRatio < 97.5:
            return f"INPUT, OUTPUT 불일치율 2.5% 이상 오류 발생: 불일치율({nonCommonPartRatio}), 불일치요소({len(nonCommonParts)})"
    except ValueError as e:
        return f"INPUT, OUTPUT 매우 높은 불일치율 발생: {e}"
    # Error5: InputDots, responseDataDots 불일치시 예외 처리
    if len(InputDic) != len(OutputDic) != InputDots:
        print(f'@@@@@@@@@@\nInputDic: {InputDic}\nOutputDic: {OutputDic}\n@@@@@@@@@@')
        UnmatchedText, UnmatchedSpotsText = FindUnmatchedChunkAndSpot(Input, CorrectionText)
        return {"Error": f"INPUT, OUTPUT [n] 갯수 불일치 오류 발생: INPUT({len(InputDic)}), OUTPUT({len(OutputDic)}), InputDots({InputDots})", "Unmatched": UnmatchedText, "UnmatchedSpot": UnmatchedSpotsText}
    # Error5: OUTPUT 내에 SFXTag 불일치시 예외 처리
    OutputDicList = [OutputDic]
    for SFXTag in InputSFXTags:
        if SFXTag not in responseData:
            return f"OUTPUT 내에 SFXTag 불일치 오류 발생: INPUT({SFXTag})"
        elif responseData.count(SFXTag) > 1:
            ReplaceSFXTag = SFXTag.replace('<S', '<효과음시작').replace('<E', '<효과음끝')
            OutputDics = generateOutputDicList(OutputDic, ReplaceSFXTag)
            OutputDicList += OutputDics
    # Error6: Input, responseData 불일치시 예외 처리
    OutputDicErrorList = []
    for OutputDic in OutputDicList:  # OutputDicList를 순회
        OutputDicError = 0 # 최종 에러 확인
        nonCommonPartsNum = 0
        for i in range(len(InputDic)):
            CleanInput = re.sub("[^가-힣]", "", InputDic[i])
            CleanOutput = re.sub("[^가-힣]", "", OutputDic[i])
            ## ErrorCount가 2 이상일 경우에는 SFX는 오타 평가에서 무시
            if ErrorCount >= 2:
                CleanInput = CleanInput.replace("효과음시작", "")
                CleanInput = CleanInput.replace("효과음끝", "")
                CleanOutput = CleanOutput.replace("효과음시작", "")
                CleanOutput = CleanOutput.replace("효과음끝", "")
                
            nonOutputDicError = 0 # 반복 테스트에서 하나의 일치라도 발생하면 통과
            ## Test1 (단순 replace)
            if CleanInput != CleanOutput:
                try:
                    for nonCommonPartsNum in range(len(nonCommonParts)):
                        nonCommonPart = nonCommonParts[nonCommonPartsNum]
                        DiffINPUT = nonCommonPart['DiffINPUT']
                        print(f'\n\n\n({i}, {nonCommonPartsNum})@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\nDiffINPUT: {DiffINPUT}')
                        DiffOUTPUT = nonCommonPart['DiffOUTPUT']
                        print(f'DiffOUTPUT: {DiffOUTPUT}')
                        longCommonSubstring = LongCommonSubstring(DiffINPUT, DiffOUTPUT)
                        longCommonSubstring = longCommonSubstring.replace('콼', '')
                        print(f'longCommonSubstring: {longCommonSubstring}')
                        NonINPUT = nonCommonPart['NonINPUT']
                        print(f'NonINPUT:  {NonINPUT}')
                        NonOUTPUT = nonCommonPart['NonOUTPUT']
                        print(f'NonOUTPUT: {NonOUTPUT}')
                        ## Test2 (단순 NonINPUT, NonOUTPUT을 replace) 비교확인
                        if CleanInput.replace(NonINPUT, NonOUTPUT) != CleanOutput:
                            ## Test3 (longCommonSubstring을 더하여 특정부분의 NonINPUT, NonOUTPUT을 replace) 비교확인 
                            if CleanInput.replace(NonINPUT + longCommonSubstring, NonOUTPUT + longCommonSubstring) != CleanOutput:
                                ## Test4 CleanInput과 CleanOutput내에 동일한 문자가 여러개일 경우 하나씩 replace 하여 비교확인
                                for n in range(10):
                                    ReplaceCleanInput = ReplaceNthOccurrence(CleanInput, NonINPUT, NonOUTPUT, n)
                                    for N in range(10):
                                        ReplaceCleanOutput = ReplaceNthOccurrence(CleanOutput, NonINPUT, NonOUTPUT, N)
                                        # print(f'replace1: {NonINPUT + longCommonSubstring}')
                                        # print(f'replace2: {NonOUTPUT + longCommonSubstring}\n------------------------------------\n')
                                        # print(f'CleanInput:  {CleanInput}')
                                        # print(f'CleanOutput: {CleanOutput}')
                                        # print(f'ReplaceCleanInput:  {ReplaceCleanInput}')
                                        # print(f'ReplaceCleanOutput: {ReplaceCleanOutput}\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n')
                                        # ReplaceCleanInput과 ReplaceCleanOutput를 비교하여 동일한 문자 발견시 바로 코드 종료
                                        if ReplaceCleanInput == ReplaceCleanOutput:
                                            # nonCommonPartsNum += 1
                                            nonOutputDicError += 1 ## Test4
                                            break
                                        else:
                                            ## Test5 NonINPUT과 NonOUTPUT중에 "" 빈문자가 있을 경우 CleanInput와 ReplaceCleanOutput내에 하나씩 문자를 추가하여 비교확인 
                                            for j in range(len(CleanInput) + 1):
                                                ReplaceCleanInput = CleanInput[:j] + NonOUTPUT + CleanInput[j:]
                                                ReplaceCleanOutput = CleanOutput[:j] + NonINPUT + CleanOutput[j:]
                                                # print(f'{j}-1) ReplaceCleanInput: {ReplaceCleanInput}')
                                                # print(f'{j}-1) CleanOutput:       {CleanOutput}\n')
                                                # print(f'{j}-2) CleanInput:         {CleanInput}')
                                                # print(f'{j}-2) ReplaceCleanOutput: {ReplaceCleanOutput}\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n')
                                                if ReplaceCleanInput == CleanOutput or CleanInput == ReplaceCleanOutput:
                                                    # nonCommonPartsNum += 1
                                                    nonOutputDicError += 1 ## Test5
                                                    break
                            else:
                                nonOutputDicError += 1 ## Test3
                                break
                        else:
                            nonOutputDicError += 1 ## Test2
                            break
                                
                except IndexError as e:
                    OutputDicError += 1
                    print(f"INPUT, OUTPUT [n] 일부분 불일치: (nonCommonPartsNum: {nonCommonPartsNum}, i: {i}, n: {n}, N: {N}, Error: {e})")
                if nonOutputDicError == 0:
                    OutputDicError += 1
        ## OutputDicList의 Error 수치 리스트 형성 (각 OutputDicList의 순서별 에러숫자가 있었는지 없었는지 확인)
        OutputDicErrorList.append(OutputDicError)

    # OutputDicErrorList중 에러(OutputDicError가 0)가 없었던 OutputDic 찾기, 존재할 경우 해당 OutputDic(OutputDicList[i])값을 리턴
    NonErrorNum = None
    for k in range(len(OutputDicErrorList)):
        if OutputDicErrorList[k] == 0:
            NonErrorNum = k
    
    if NonErrorNum == None:
        return f"INPUT, OUTPUT [n]의 최종 불일치 오류 발생"
    else:
        return {'json': OutputDicList[k], 'filter': OutputDicList[k], 'nonCommonParts': nonCommonParts}

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
    UnmatchedSpot = ""
        
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
            if UnmatchedSpot != "":
                momoryCounterAttention = f", 특히 '{UnmatchedSpot}' 부분 주의해주세요. -"
            else:
                momoryCounterAttention = " -"
            memoryCounter = f" - 중요: 매우 꼼꼼한 끊어읽기!, 띄어쓰기 맞춤법 오타 등 절대 수정 및 변경 없음!, 효과음 시작/끝 기호 <Sn> <En>와 [숫자]는 절대로 변경 말고 그대로 유지!, 청크 기호 [1] ~ [{InputDots}]까지 숫자를 절대 하나도 빠트리지 않고 그대로 작성!" + momoryCounterAttention
            outputEnder = ""
            
            # Response 생성
            Response, Usage, Model = ANTHROPIC_LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, InputMemory = inputMemory, OutputMemory = outputMemory, MemoryCounter = memoryCounter, OutputEnder = outputEnder, messagesReview = MessagesReview)

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
         
            Filter = CorrectionKoFilter(Input, DotsInput, responseData, InputDots, InputSFXTags, InPutPeriods, InputChunkId, ErrorCount)
            
            if isinstance(Filter, str) or "UnmatchedSpot" in Filter:
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                if "UnmatchedSpot" in Filter:
                    UnmatchedSpot = Filter['UnmatchedSpot']
                else:
                    UnmatchedSpot = ""
                    
                # 2분 대기 이후 다시 코드 실행
                ErrorCount += 1
                print((f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | 오류횟수 {ErrorCount}회, 2분 후 프롬프트 재시도"))
                time.sleep(120)
                if ErrorCount == 5:
                    sys.exit(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | 오류횟수 {ErrorCount}회 초과, 프롬프트 종료")

                    
                continue
            else:
                OutputDic = Filter['filter']
                outputJson = Filter['json']
                nonCommonParts = Filter['nonCommonParts']
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | JSONDecode 완료")
                UnmatchedSpot = ""
                
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
        # 예상하지 못한 오류 (During handling of the above exception, another exception occurred)로 인해 3회 반복 구현
        try:
            SaveAddOutputMemory(projectName, email, nonCommonPartList, '21', DataFramePath)
        except:
            try:
                time.sleep(1)
                SaveAddOutputMemory(projectName, email, nonCommonPartList, '21', DataFramePath)
            except:
                time.sleep(1)
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

    # 데이터베이스에서 사용자 이름 찾기
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()
        if user is None:
            raise ValueError("User not found with the provided email")
        
        username = user.UserName
        
    # 문자열 정규화
    _baseFilePath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/{username}_user/{username}_storage/{projectName}/{projectName}_dataframe_file/{email}_{projectName}_21_responseJson"
    baseFilePathNFCNormalized = unicodedata.normalize('NFC', _baseFilePath)
    baseFilePathNFDNormalized = unicodedata.normalize('NFD', _baseFilePath)
    
    ## 한글의 유니코드 문제로 인해 일반과 노멀라이즈를 2개로 분리하여 가장 최근 파일찾기 실행
    try:
        if os.listdir(os.path.dirname(_baseFilePath)):
            baseFilePath = _baseFilePath
        fullFilePath = f"{_baseFilePath}_{str(Date())}.txt"
    except:
        try:
            if os.listdir(os.path.dirname(baseFilePathNFCNormalized)):
                baseFilePath = baseFilePathNFCNormalized
            fullFilePath = f"{baseFilePathNFCNormalized}_{str(Date())}.txt"
        except:
            if os.listdir(os.path.dirname(baseFilePathNFDNormalized)):
                baseFilePath = baseFilePathNFDNormalized
            fullFilePath = f"{baseFilePathNFDNormalized}_{str(Date())}.txt"

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
    
    # outputMemoryDics에 간혹 발생하는 불필요 데이터 삭제

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
            tokens.append({"Pause": "(3.00)"})
            tokens.append({"Enter": "\n"})
        elif tag in ["Logue", "Part", "Chapter"]:
            tokens.append({"Pause": "(1.50)"})
            tokens.append({"Enter": "\n"})
        elif tag == "Index":
            tokens.append({"Pause": "(1.30)"})
            tokens.append({"Enter": "\n"})
        # elif tag == "Comment":
        #     tokens.append({"Pause": "(0.40)"})
        #     tokens.append({"Enter": "\n"})
        else:
            if len(tokens) >= 2:
                BeforeEndtoken = tokens[-2]
                Endtoken = tokens[-1]
                if ('Ko' in BeforeEndtoken and 'Period' in Endtoken) or ('En' in BeforeEndtoken and 'Period' in Endtoken) or ('SFXEnd' in BeforeEndtoken and 'Period' in Endtoken):
                    tokens.append({"Pause": random.choice(["(0.51)", "(0.55)", "(0.59)"])})
                    tokens.append({"Enter": "\n"})
                if len(tokens) >= 5:
                    for k in range(len(tokens) - 5):
                        if ('Ko' in tokens[k] and 'Period' in tokens[k+1]) or ('En' in tokens[k] and 'Period' in tokens[k+1]) or ('SFXEnd' in tokens[k] and 'Period' in tokens[k+1]):
                            tokens.insert(k + 2, {"Pause": "(0.60)"})

        RemoveSFXtokens = [item for item in tokens if "SFXEnd" not in item and "SFXStart" not in item]
        
        # 앞, 뒤Chunk를 통한 처리
        if Aftertag in ["Logue", "Part", "Chapter"]:
            if len(tokens) >= 2:
                if "Pause" in tokens[-2]:
                    tokens[-2]['Pause'] = "(2.00)"
                else:
                    tokens.append({"Pause": "(2.00)"})
            else:
                tokens.append({"Pause": "(2.00)"})
        elif Aftertag == "Index":
            if len(tokens) >= 2:
                if "Pause" in tokens[-2]:
                    tokens[-2]['Pause'] = "(1.30)"
                else:
                    tokens.append({"Pause": "(1.30)"})
            else:
                tokens.append({"Pause": "(1.30)"})
        elif (tag not in ["Caption", "CaptionComment"]) and (Aftertag in ["Caption", "CaptionComment"]):
            if len(tokens) >= 2:
                if "Pause" in tokens[-2]:
                    if tokens[-2]['Pause'] not in ['(3.00)', '(2.00)', '(1.50)', '(1.30)']:
                        tokens[-2]['Pause'] = "(1.10)"
                else:
                    tokens.append({"Pause": "(1.10)"})
                    tokens.append({"Enter": "\n"})
            else:
                tokens.append({"Pause": "(1.20)"})
                tokens.append({"Enter": "\n"})
        elif (tag in ["Caption", "CaptionComment"]) and (Aftertag not in ["Caption", "CaptionComment"]):
            tokens.append({"Pause": "(1.10)"})
            tokens.append({"Enter": "\n"})
        elif tag == "Character" and Aftertag == "Character":
            tokens.append({"Pause": "(0.75)"})
            tokens.append({"Enter": "\n"})
        elif tag == "Character" and Aftertag == "Narrator":
            tokens.append({"Pause": "(0.40)"})
            tokens.append({"Enter": "\n"})
        elif tag == "Character" and Aftertag == "Comment":
            tokens.append({"Pause": "(0.20)"})
            tokens.append({"Enter": "\n"})
        elif tag == "Narrator" and Aftertag == "Character":
            if len(RemoveSFXtokens) >= 2:
                BeforeEndtoken = RemoveSFXtokens[-2]
                Endtoken = RemoveSFXtokens[-1]
                if 'Pause' not in BeforeEndtoken and 'Pause' not in Endtoken and 'Comma' not in BeforeEndtoken and 'Comma' not in Endtoken:
                    tokens.append({"Pause": "(0.40)"})
                    tokens.append({"Enter": "\n"})
        elif (tag == "Narrator" and Aftertag == "Comment") or (tag == "Caption" and Aftertag == "CaptionComment"):
            if len(RemoveSFXtokens) >= 2:
                BeforeEndtoken = RemoveSFXtokens[-2]
                Endtoken = RemoveSFXtokens[-1]
                if 'Pause' not in BeforeEndtoken and 'Pause' not in Endtoken and 'Comma' not in BeforeEndtoken and 'Comma' not in Endtoken:
                    tokens.append({"Pause": "(0.20)"})

        # 마지막으로 Pause가 없는 경우의 처리
        PauseCount = 0
        for token in tokens[-3:]:
            if 'Pause' in token:
                PauseCount += 1
        if PauseCount == 0:
            tokens.append({"Pause": random.choice(["(0.51)", "(0.55)", "(0.59)"])})

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
            
    # # JSON 파일로 저장
    # with open('/yaas/response.json', 'w', encoding = 'utf-8') as file:
    #     json.dump(responseJson, file, ensure_ascii = False, indent = 4)

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
    projectName = "나는외식창업에적합한사람인가"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################