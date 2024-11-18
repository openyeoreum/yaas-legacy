import os
import re
import json
import time
import pdfplumber
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from PyPDF2 import PdfWriter, PdfReader
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedScriptGenToDB, AddScriptGenBookPagesToDB, ScriptGenCountLoad, ScriptGenCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
## LoadRawScript 로드
def LoadRawScript(projectName, email, Process):
    ScriptFilePath = f'/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script_file'
    RawScriptJsonFileName = f'{projectName}_RawScript.json'
    RawScriptFilePath = os.path.join(ScriptFilePath, RawScriptJsonFileName)
    
    # 기본 RawScript JSON 구조
    RawScriptJson = [
        {
            "RawScript_Completion": "No",
            "Process": f"{Process}"
        },
        {
            "Id": 1,
            "Tag": "",
            "Name": "",
            "Age": "",
            "Gender": "",
            "Title": "",
            "Content": ""
        }
    ]

    # 파일이 존재할 경우 로드
    if os.path.exists(RawScriptFilePath):
        with open(RawScriptFilePath, 'r', encoding = 'utf-8') as RawScript_Json:
            rawScriptJson = json.load(RawScript_Json)
        # RawScript_Completion 체크
        if rawScriptJson[0].get("RawScript_Completion") == "Yes" and rawScriptJson[0].get("RawScript_Completion") != "":
            Raw_ScriptJson = rawScriptJson[1:]
            return Raw_ScriptJson
        else:
            sys.exit(f'[ (([{projectName}_RawScript.json])) 작성을 완료하고 "RawScript_Completion": "Yes"로 변경해주세요 ]\n{RawScriptFilePath}')
    else:
        # 파일이 없으면 생성하고 초기 데이터 저장
        with open(RawScriptFilePath, 'w', encoding = 'utf-8') as file:
            json.dump(RawScriptJson, file, ensure_ascii = False, indent = 4)
        sys.exit(f'[ (([{projectName}_RawScript.json])) 작성을 완료하고 "RawScript_Completion": "Yes"로 변경해주세요 ]\n{RawScriptFilePath}')

## LoadRawScript의 inputList 치환
def LoadRawScriptToInputList(projectName, email, Process):
    rawScriptJson = LoadRawScript(projectName, email, Process)
    
    InputList = []
    for i in range(len(rawScriptJson)):
        Id = rawScriptJson[i]['Id']
        
        Tag = rawScriptJson[i]['Tag']
        tag = ''
        if Tag != '':
            tag = f'[{Tag}]\n'
        
        Name = rawScriptJson[i]['Name']
        name = ''
        if Name != '':
            name = f'이름: {Name}\n'
            
        Age = rawScriptJson[i]['Age']
        age = ''
        if Age != '':
            age = f'나이: {Age}\n'
            
        Gender = rawScriptJson[i]['Gender']
        gender = ''
        if Gender != '':
            gender = f'성별: {Gender}\n'
            
        Title = rawScriptJson[i]['Title']
        title = ''
        if Title != '':
            title = f'제목: {Title}\n'
            
        Content = rawScriptJson[i]['Content']
        content = ''
        if Content != '':
            content = f'내용:\n{Content}'
        
        RawScript = tag + name + age + gender + title + content
            
        InputDic = {'Id': Id, 'Continue': RawScript}
        InputList.append(InputDic)
        
    return InputList

######################
##### Filter 조건 #####
######################
## ScriptGen의 Filter(Error 예외처리)
def ScriptGenFilter(responseData):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(responseData)
        OutputDic = [{key: value} for key, value in outputJson.items()]
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 결과가 list가 아닐 때의 예외 처리
    if not isinstance(OutputDic, list):
        return "JSONType에서 오류 발생: JSONTypeError"
    for dic in OutputDic:
        try:
            if not '인공지능 음성 스크립트' in dic:
                return "JSON에서 오류 발생: JSONKeyError"
        # Error3: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"

    return {'json': outputJson, 'filter': OutputDic}

######################
##### Memory 생성 #####
######################
## inputMemory 형성
def ScriptGenInputMemory(inputMemoryDics, MemoryLength):
    inputMemoryDic = inputMemoryDics[-(MemoryLength + 1):]
    
    inputMemoryList = []
    for inputmeMory in inputMemoryDic:
        key = list(inputmeMory.keys())[1]  # 두 번째 키값
        print(inputmeMory)
        if key == "Continue":
            inputMemoryList.append(inputmeMory['Continue'])
        else:
            inputMemoryList.append(inputmeMory['Pass'])
    inputMemory = "".join(inputMemoryList)
    # print(f"@@@@@@@@@@\ninputMemory :{inputMemory}\n@@@@@@@@@@")
    
    return inputMemory

## outputMemory 형성
def ScriptGenOutputMemory(outputMemoryDics, MemoryLength):
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
## ScriptGen 프롬프트 요청 및 결과물 Json화
def ScriptGenProcess(projectName, email, DataFramePath, Process = "SejongCityOfficeOfEducation_Elementary", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '00', DataFramePath)
    inputList = LoadRawScriptToInputList(projectName, email, Process)
    InputList = inputList[OutputMemoryCount:]
    if InputList == []:
        return OutputMemoryDicsFile, inputList

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
        
    # ScriptGenProcess
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
            memoryCounter = ""
            outputEnder = ""

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
                    
            Filter = ScriptGenFilter(responseData)
            
            if isinstance(Filter, str):
                if Mode == "Memory" and mode == "Example" and ContinueCount == 1:
                    ContinueCount = 0 # Example에서 오류가 발생하면 Memory로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                if Mode == "MemoryFineTuning" and mode == "ExampleFineTuning" and ContinueCount == 1:
                    ContinueCount = 0 # ExampleFineTuning에서 오류가 발생하면 MemoryFineTuning로 넘어가는걸 방지하기 위해 ContinueCount 초기화
                print(f"Project: {projectName} | Process: {Process} {OutputMemoryCount + ProcessCount}/{len(inputList)} | {Filter}")
                
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
            inputMemory = ScriptGenInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = ScriptGenOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '00', DataFramePath)
    
    return outputMemoryDics, inputList

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
## _Index.txt, _Body.txt의 목차일치 확인
def IndexInspection(IndexText: str, BodyText: str) -> bool:
    # IndexText는 여러 줄로 되어 있으므로 줄 단위로 분리
    index_lines = IndexText.splitlines()

    # 각 목차가 BodyText 안에 존재하는지 확인
    IndexCompletion = True
    for line in index_lines:
        # 공백 줄이나 빈 줄은 건너뛰기
        if line.strip() == "":
            continue
        Line = f'{line}\n'
        # 목차 항목이 BodyText에 없으면 False 반환
        if Line not in BodyText:
            print(f'- 누락 인덱스: {line}')
            IndexCompletion = False
    
    # 모든 목차가 BodyText에 있으면 True 반환
    return IndexCompletion

## _Body.txt의 대화문 확인
def BodyTextInspection(BodyText, _BodyTextInspectionFilePath):
    text = BodyText

    # 큰 따옴표 시작(“)의 개수를 카운트합니다.
    start_quote_count = text.count('“')
    # 큰 따옴표 끝(”)의 개수를 카운트합니다.
    end_quote_count = text.count('”')

    # 패턴을 정의합니다: “로 시작하고 ”로 끝나는 부분을 찾습니다.
    # 큰 따옴표 끝이 없을 수도 있으므로, 이를 고려하여 패턴을 작성합니다.
    pattern = r'“(.*?)”'

    # 정규식을 사용하여 매칭되는 부분을 찾습니다.
    matches = list(re.finditer(pattern, text))

    # 만약 큰 따옴표 끝(”)이 없는 경우를 처리하기 위해 시작 따옴표 위치를 모두 찾습니다.
    start_positions = [m.start() for m in re.finditer('“', text)]

    # 처리된 텍스트를 저장할 변수를 초기화합니다.
    processed_text = ''
    last_pos = 0
    quote_number = 1

    # 이미 매칭된 위치의 끝 인덱스를 저장합니다.
    matched_ends = set()

    MarkCount = 0
    for match in matches:
        start, end = match.span()
        matched_ends.add(end)

        segmentN = text[last_pos:start]
        MarkN = ''
        if '”' in segmentN:
            MarkN = '***'
            MarkCount += 1
        segmentQ = match.group()
        MarkQ = ''
        if segmentQ.count('“') >= 2:
            MarkQ = '***'
            MarkCount += 1

        # 이전 위치부터 현재 매칭 시작 지점까지의 텍스트를 추가합니다.
        processed_text += f'{MarkN}{segmentN}'
        
        # 큰 따옴표 시작 부분 처리
        processed_text += '\n\n'
        processed_text += f'{MarkQ}({quote_number}): '
        processed_text += segmentQ
        processed_text += '\n\n'
        
        # 인덱스와 위치 업데이트
        quote_number += 1
        last_pos = end

    # 큰 따옴표 끝(”)이 없는 시작 따옴표를 처리합니다.
    for pos in start_positions:
        if pos < last_pos:
            continue  # 이미 처리된 시작 따옴표는 건너뜁니다.
        # 다음 큰 따옴표 시작 위치 또는 텍스트의 끝까지를 가져옵니다.
        next_start = text.find('“', pos + 1)
        if next_start == -1:
            next_start = len(text)
        # 시작 따옴표부터 다음 시작 따옴표 전까지의 텍스트를 가져옵니다.
        segmentQ = text[pos:next_start]
        segmentN = text[last_pos:pos]
        # 이전 위치부터 현재 시작 따옴표까지의 텍스트를 추가합니다.
        processed_text += segmentN
        # 큰 따옴표 시작 부분 처리
        processed_text += '\n\n'
        processed_text += f'***({quote_number}): '
        MarkCount += 1
        processed_text += segmentQ
        processed_text += '\n\n'
        # 인덱스와 위치 업데이트
        quote_number += 1
        last_pos = next_start

    # 남은 텍스트를 추가합니다.
    processed_text += text[last_pos:]

    # 검수용 파일의 첫 줄 작성 및 다음 코드 스탭 결정
    BodyTextCompletion = False
    if (start_quote_count == end_quote_count) and (MarkCount == 0):
        BodyTextCompletion = True
        inspection_text = f'[큰 따옴표 (“...”) 개수 : {start_quote_count}, 검수완료]\n\n'
    else:
        inspection_text = f'[큰 따옴표 시작(“) 개수 : {start_quote_count}, 큰 따옴표 끝(”) 개수 : {end_quote_count}, ***가 표시된 부분 ({MarkCount}) 곳을 잘 확인]\n\n'
    inspection_text += processed_text

    # 검수용 파일 저장
    with open(_BodyTextInspectionFilePath, 'w', encoding = 'utf-8') as file:
        file.write(inspection_text)

    return BodyTextCompletion

## BodyText 긴 대화문장 사이 분할 생성 함수
def SplitLongDialogues(BodyText, EndPunctuation):
    # 대화문을 찾는 정규 표현식 패턴
    dialogue_pattern = r'“([^”]+)”'

    def SplitDialogue(dialogue):
        if len(dialogue) <= 100:
            return f'“{dialogue}”'
        
        parts = []
        current_part = ""
        for i, char in enumerate(dialogue):
            current_part += char
            if len(current_part) >= 80 and any(current_part.endswith(p) for p in EndPunctuation):
                parts.append(current_part.strip())
                current_part = ""
        
        # 마지막 부분이 남아 있으면 추가
        if current_part:
            parts.append(current_part.strip())
        # 각 부분을 " "로 연결
        return ' ” “ '.join(parts)

    # 대화문을 찾고 분리 후 다시 합침
    SplitedBodyText = re.sub(dialogue_pattern, lambda match: SplitDialogue(match.group(1)), BodyText)
    
    return SplitedBodyText

## BodyText 긴 일반문장 사이 분할 생성 함수
def SplitLongSentences(BodyText, EndPunctuation):   
    # 중간에 분할 가능한 패턴들
    SplitablePhrases = [
        '데 ', '고 ', '로 ', '며 ', '서 ', '지 ', '게 ', '을 ', 
        '이 ', '가 ', '니 ', '도 ', '와 ', '과 ', '의 ', 
        '서 ', '럼 ', '에 ', '큼 ', '만 ', '뿐 ', '때 ', '것 ', ','
    ]

    def SplitSentence(sentence):
        if len(sentence) <= 300:
            return sentence
        
        current_part = ""
        count_since_split = 0  # 80자 카운트를 위한 변수
        i = 0
        
        while i < len(sentence):
            current_part += sentence[i]
            count_since_split += 1
            
            # 80자 이후에 splitable_phrases에 해당하는 패턴을 찾음
            if count_since_split >= 200:
                for phrase in SplitablePhrases:
                    if current_part.endswith(phrase):
                        # 패턴을 찾으면 그 위치에서 문장을 분할
                        split_idx = len(current_part)
                        return current_part[:split_idx] + '∨∨' + SplitSentence(sentence[split_idx:].strip())
            i += 1
        
        return sentence

    # end_punctuation으로 문장을 분리
    sentence_pattern = '|'.join(map(re.escape, EndPunctuation))
    sentences = re.split(f'({sentence_pattern})', BodyText)
    
    # 각 문장을 처리하고 다시 합침
    SplitedBodyText = ''.join([SplitSentence(sentence) for sentence in sentences])
    
    return SplitedBodyText

## BodyText 긴 문단 분할 생성 함수
def SplitParagraphs(BodyText, EnterEndPunctuation, max_length = 3000):
    paragraphs = []
    start = 0
    in_quote = False
    current_length = 0
    
    for i in range(len(BodyText)):
        # 따옴표 시작과 끝 구간을 확인
        if BodyText[i] == '“':
            in_quote = True
        elif BodyText[i] == '”':
            in_quote = False
        # 줄바꿈 문자를 만나면 길이 제한을 초기화
        if BodyText[i] == '\n':
            current_length = 0
            continue
        # 따옴표 밖에서만 작업을 수행
        if not in_quote:
            current_length += 1
            
            if current_length >= max_length:
                # 가능한 구두점에서 문단 나누기
                for p in EnterEndPunctuation:
                    if BodyText[i-len(p)+1:i+1] == p:
                        paragraphs.append(BodyText[start:i+1].strip())
                        start = i + 1
                        current_length = 0
                        break
    # 마지막 문단 추가
    if start < len(BodyText):
        paragraphs.append(BodyText[start:].strip())
    BodyText = '\n'.join(paragraphs)

    return BodyText

## 데이터 치환
def ScriptGenResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):   
    ### A. 데이터 치환 ###
    outputMemoryDics, inputList = ScriptGenProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    for i in range(len(outputMemoryDics)):
        PageId = inputList[i]['Id']
        PageElement = inputList[i]['PageElement']
        Input = inputList[i]['Continue']
        Script = outputMemoryDics[i][0]['인공지능 음성 스크립트']
        
        ## Script에 마지막 단어 누락 방지 코드 ##
        # 1. Input에서 마지막 라인을 추출합니다.
        lines = Input.split('\n')
        InputLine = lines[-1]

        # 2. Input 마지막 라인에서 앞 10 - 15글자를 추출
        substring = ''
        if len(InputLine) >= 15:
            substring = InputLine[:15]
        elif len(InputLine) >= 10:
            substring = InputLine[:10]
        else:
            pass
        if substring:
            # 3. Script에서 동일한 부분을 찾아 그 이후 부분을 삭제
            pos = Script.find(substring)
            if pos != -1:
                Script = Script[:pos + len(substring)]
                # 4. Script에서 일치하는 부분을 Input의 마지막 라인으로 대체
                Script = Script.replace(substring, InputLine)
        ## 마지막 단어 누락 방지 코드 ##

        responseJson.append({"PageId": PageId, "PageElement": PageElement, "Script": Script})

    ### B. 검수 ###
    # 경로 설정
    TextDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script_file"
    JsonPath = os.path.join(TextDirPath, f'[{projectName}_PDFSetting].json')
    TextOutputDir = TextDirPath + f'/{projectName}_Text'
    IndexTextFilePath = TextDirPath + f'/{projectName}_Index.txt'
    BodyTextFilePath = TextDirPath + f'/{projectName}_Body.txt'
    _IndexTextFilePath = TextOutputDir + f'/{projectName}_Index.txt'
    _BodyTextFilePath = TextOutputDir + f'/{projectName}_Body.txt'
    _BodyTextInspectionFilePath = TextOutputDir + f'/{projectName}_Body(검수용).txt'
    
    ## JSON 파일 불러오기
    with open(JsonPath, 'r', encoding = 'utf-8') as json_file:
        PDFBookToTextSetting = json.load(json_file)
    
    TextProcess = False
    if PDFBookToTextSetting['PDFBookToTextSetting']['InspectionCompletion'] != 'Completion':
        ## IndexText와 BodyText 저장
        if not (os.path.exists(_IndexTextFilePath) and os.path.exists(_BodyTextFilePath)):
            IndexText = ''
            BodyText = ''
            for Response in responseJson:
                PageElement = Response['PageElement']
                Script = Response['Script']
                if PageElement == 'Index':
                    IndexText += f'{Script}\n'
                elif PageElement == 'Title':
                    IndexText += f'{Script}\n'
                    BodyText += f'{Script}\n\n'
                elif PageElement == 'index':
                    BodyText += f'\n\n{Script}\n\n'
                elif PageElement == 'Body':
                    BodyText += f'{Script} '
        else:
            with open(_IndexTextFilePath, 'r', encoding = 'utf-8') as file:
                IndexText = file.read()
            with open(_BodyTextFilePath, 'r', encoding = 'utf-8') as file:
                BodyText = file.read()

        ## 검수1: 목차 확인
        IndexCompletion = IndexInspection(IndexText, BodyText)
        if not IndexCompletion:
            print(f"\n[ * 검수1: ({projectName}_Index.txt), ({projectName}_Body.txt) 목차 검수 필요 * ]")
        ## 검수2: 대화문 확인
        BodyTextCompletion = BodyTextInspection(BodyText, _BodyTextInspectionFilePath)
        if not BodyTextCompletion:
            print(f"[ * 검수2: ({projectName}_Index.txt), ({projectName}_Body.txt) 따옴표 검수 필요 * ]")
        
        if IndexCompletion and BodyTextCompletion:
            ## 문장종결 부호, 아래 함수들에 필요
            EnterEndPunctuation = [
                '다.', '다!', '다?', 
                '나.', '나!', '나?', 
                '까.', '까!', '까?', 
                '요.', '요!', '요?', 
                '죠.', '죠!', '죠?', 
                '듯.', '듯!', '듯?', 
                '것.', '것!', '것?', 
                '라.', '라!', '라?', 
                '가.', '가!', '가?', 
                '니.', '니!', '니?', 
                '군.', '군!', '군?', 
                '오.', '오!', '오?', 
                '자.', '자!', '자?', 
                '네.', '네!', '네?', 
                '소.', '소!', '소?', 
                '지.', '지!', '지?', 
                '어.', '어!', '어?', 
                '봐.', '봐!', '봐?', 
                '해.', '해!', '해?', 
                '야.', '야!', '야?', 
                '아.', '아!', '아?', 
                '든.', '든!', '든?'
            ]
            EndPunctuation = EnterEndPunctuation + ['\n', '∨∨']
            
            ## BodyText 긴 대화문장 사이 분할
            BodyText = SplitLongDialogues(BodyText, EndPunctuation)
            ## BodyText 긴 일반문장 사이 분할
            BodyText = SplitLongSentences(BodyText, EndPunctuation)
            ## 긴 문단을 분할
            BodyText = SplitParagraphs(BodyText, EnterEndPunctuation)

            PDFBookToTextSetting['PDFBookToTextSetting']['InspectionCompletion'] = 'Completion'
            with open(JsonPath, 'w', encoding = 'utf-8') as json_file:
                json.dump(PDFBookToTextSetting, json_file, ensure_ascii = False, indent = 4)
            print(f"\n[ ({projectName}_Index.txt), ({projectName}_Body.txt) 파일이 완성되었습니다. ]")
            TextProcess = True
            with open(IndexTextFilePath, 'w', encoding = 'utf-8') as file:
                file.write(IndexText)
            with open(BodyTextFilePath, 'w', encoding = 'utf-8') as file:
                file.write(BodyText)
        
        with open(_IndexTextFilePath, 'w', encoding = 'utf-8') as file:
            file.write(IndexText)
        with open(_BodyTextFilePath, 'w', encoding = 'utf-8') as file:
            file.write(BodyText)
            
    return responseJson, TextProcess

## 프롬프트 요청 및 결과물 Json을 ScriptGen에 업데이트
def ScriptGenUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    # 경로 설정
    TextDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script_file"
    IndexTextFilePath = TextDirPath + f'/{projectName}_Index.txt'
    BodyTextFilePath = TextDirPath + f'/{projectName}_Body.txt'
    
    if not (os.path.exists(IndexTextFilePath) and os.path.exists(BodyTextFilePath)):
        
        print(f"< User: {email} | Project: {projectName} | 00_ScriptGenUpdate 시작 >")
        # ScriptGen의 Count값 가져오기
        PageCount, Completion = ScriptGenCountLoad(projectName, email)
        if Completion == "No":
            
            if ExistedDataFrame != None:
                # 이전 작업이 존재할 경우 가져온 뒤 업데이트
                AddExistedScriptGenToDB(projectName, email, ExistedDataFrame)
                AddExistedDataSetToDB(projectName, email, "ScriptGen", ExistedDataSet)
                print(f"[ User: {email} | Project: {projectName} | 00_ScriptGenUpdate는 ExistedScriptGen으로 대처됨 ]\n")
                
                _, TextProcess = ScriptGenResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)

                if TextProcess == False:
                    sys.exit(f"\n\n[ ((({projectName}_Index.txt))), ((({projectName}_Body.txt))) 파일을 완성하여 아래 경로에 복사해주세요. ]\n({TextDirPath})\n\n1. 목차(_Index)파일과 본문(_Body) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n2. 본문(_Body)파일 내 쌍따옴표(“대화문”의 완성) 개수 일치 * _Body(검수용) 파일 확인\n3. 캡션 등의 줄바꿈 및 캡션이 아닌 일반 문장은 마지막 온점(.)처리\n\n")
                else:
                    time.sleep(0.1)
            else:
                responseJson, _ = ScriptGenResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
                
                # ResponseJson을 ContinueCount로 슬라이스
                ResponseJson = responseJson[PageCount:]
                ResponseJsonCount = len(ResponseJson)

                # TQDM 셋팅
                UpdateTQDM = tqdm(ResponseJson,
                                total = ResponseJsonCount,
                                desc = 'ScriptGenUpdate')
                # i값 수동 생성
                i = 0
                for Update in UpdateTQDM:
                    UpdateTQDM.set_description(f'ScriptGenUpdate: {Update["Script"][:10]}...')
                    time.sleep(0.0001)
                    PageId = Update["PageId"]
                    PageElement = Update["PageElement"]
                    Script = Update["Script"]
                    
                    AddScriptGenBookPagesToDB(projectName, email, PageId, PageElement, Script)
                    # i값 수동 업데이트
                    i += 1
                
                UpdateTQDM.close()
                # Completion "Yes" 업데이트
                ScriptGenCompletionUpdate(projectName, email)
                print(f"[ User: {email} | Project: {projectName} | 00_ScriptGenUpdate 완료 ]\n")
        else:
            print(f"[ User: {email} | Project: {projectName} | 00_ScriptGenUpdate는 이미 완료됨 ]\n")
    else:
        print(f"[ User: {email} | Project: {projectName} | 00_ScriptGenUpdate는 ExistedScriptGen으로 대처됨 ]\n")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "241118_우리반오디오북아름초5학년5반"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################
    
    # InputList = LoadRawScriptToInputList(projectName, email, "SejongCityOfficeOfEducation_Middle")
    # print(InputList)
    ScriptGenProcess(projectName, email, DataFramePath)