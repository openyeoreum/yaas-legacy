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
from backend.b2_Solution.b25_DataFrame.b251_DataCommit.b2511_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from backend.b2_Solution.b25_DataFrame.b251_DataCommit.b2512_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedBookPreprocessToDB, AddBookPreprocessBookPagesToDB, BookPreprocessCountLoad, BookPreprocessCompletionUpdate
from backend.b2_Solution.b25_DataFrame.b251_DataCommit.b2513_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################

## Script파일 여부 확인
def ExistenceOrNotScriptFile(projectName, email):
    project = GetProject(projectName, email)
    ScriptFilesPath = project.UploadScriptPath
    PDFFileSourcePath = os.path.join(ScriptFilesPath, projectName + ".pdf")
    IndexFileSourcePath = os.path.join(ScriptFilesPath, projectName + "_Index.txt")
    BodyFileSourcePath = os.path.join(ScriptFilesPath, projectName + "_Body.txt")
    ProjectConfig = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_config.json"
    
    with open(ProjectConfig, 'r', encoding = 'utf-8') as ConfigJson:
        Config = json.load(ConfigJson)
        ScriptConfig = Config['ScriptConfig']
    
    if ScriptConfig == {}:
        if os.path.exists(PDFFileSourcePath) or (os.path.exists(IndexFileSourcePath) and os.path.exists(BodyFileSourcePath)):
            pass
        else:
            sys.exit(f"\n[ 아래 폴더에 ((({projectName + '.pdf'}))) 또는 ((({projectName + '_Index.txt'} + {projectName + '_Body.txt'}))) 파일을 넣어주세요 ]\n({ScriptFilesPath})")

## PDF파일 편집
def PDFBookCropping(projectName, email, PDFBookToTextSetting, TextDirPath):
    ExistenceOrNotScriptFile(projectName, email)
    # 경로 설정
    PDFPath = TextDirPath + f'/{projectName}.pdf'
    NormalPDFPath = TextDirPath + f'/{projectName}_Normal.pdf'
    CroppedPDFPath = TextDirPath + f'/{projectName}_Cropped.pdf'
    
    PageForm = PDFBookToTextSetting['PDFBookToTextSetting']['PageForm']
    Left = PDFBookToTextSetting['PDFBookToTextSetting']['Left']
    Right = PDFBookToTextSetting['PDFBookToTextSetting']['Right']
    Up = PDFBookToTextSetting['PDFBookToTextSetting']['Up']
    Down = PDFBookToTextSetting['PDFBookToTextSetting']['Down']

    # 기준 폭을 결정하기 위해 PDF의 3번째 페이지 폭 확인
    with open(PDFPath, 'rb') as pdf:
        pdf_reader = PdfReader(pdf)
        if len(pdf_reader.pages) >= 3:
            reference_width = pdf_reader.pages[2].mediabox.width - 1
        else:
            reference_width = pdf_reader.pages[1].mediabox.width - 1  # 페이지가 3장 미만인 경우 두번째 페이지 폭 사용

    ## 1. 페이지 분할
    if PageForm == "Wide":
        NormalPDFWriter = PdfWriter()
        with open(PDFPath, 'rb') as pdf:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                page_width = page.mediabox.width
                page_height = page.mediabox.height
                
                # 페이지가 기준 폭보다 작은 경우 분할하지 않고 그대로 추가
                if page_width < reference_width:
                    NormalPDFWriter.add_page(page)
                else:
                    # 좌측 페이지 추가
                    left_page = page
                    left_page.mediabox.upper_right = (page_width / 2, page_height)
                    NormalPDFWriter.add_page(left_page)
                    # 우측 페이지 추가
                    right_page = page
                    right_page.mediabox.lower_left = (page_width / 2, 0)
                    right_page.mediabox.upper_right = (page_width, page_height)
                    NormalPDFWriter.add_page(right_page)

        with open(NormalPDFPath, 'wb') as NormalPDF:
            NormalPDFWriter.write(NormalPDF)
    else:
        with open(PDFPath, 'rb') as pdf:
            with open(NormalPDFPath, 'wb') as NormalPDF:
                NormalPDF.write(pdf.read())

    ## 2. 페이지별 사이즈 잘라내기
    with open(NormalPDFPath, 'rb') as normal_pdf_file:
        pdf_reader = PdfReader(normal_pdf_file)
        CroppedPDFWriter = PdfWriter()
        for page in pdf_reader.pages:
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            original_left = float(page.mediabox.lower_left[0])
            original_bottom = float(page.mediabox.lower_left[1])
            # 새 좌표 계산
            new_left = original_left + (1 - Left) * page_width / 2
            new_right = original_left + page_width - (1 - Right) * page_width / 2
            new_bottom = original_bottom + (1 - Down) * page_height / 2
            new_top = original_bottom + page_height - (1 - Up) * page_height / 2
            # Mediabox 설정
            page.mediabox.lower_left = (new_left, new_bottom)
            page.mediabox.upper_right = (new_right, new_top)
            
            CroppedPDFWriter.add_page(page)

    with open(CroppedPDFPath, 'wb') as CroppedPDF:
        CroppedPDFWriter.write(CroppedPDF)
        
    return PDFBookToTextSetting

## PDF파일 편집 및 텍스트화
def PDFBookToText(projectName, email, PDFBookToTextSetting):
    # 경로 설정
    TextDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script/{projectName}_upload_script_file"
    CroppedPDFPath = TextDirPath + f'/{projectName}_Cropped.pdf'
    TextOutputDir = TextDirPath + f'/{projectName}_Text'
    # PDF파일 편집
    PDFBookToTextSetting = PDFBookCropping(projectName, email, PDFBookToTextSetting, TextDirPath)
    # 텍스트 출력 폴더 생성
    os.makedirs(TextOutputDir, exist_ok = True)
    os.makedirs(os.path.join(TextOutputDir, f'{projectName}_Pages'), exist_ok = True)

    # PDF 파일 열기
    BookTextList = []
    
    with pdfplumber.open(CroppedPDFPath) as pdf:
        for i, page in enumerate(pdf.pages, start = 1):
            # 페이지의 bbox 좌표 가져오기
            x0, y0, x1, y1 = page.bbox
            # 페이지를 bbox 영역으로 자르기
            cropped_page = page.crop((x0, y0, x1, y1))
            # 텍스트 추출
            text = cropped_page.extract_text()
            # 각 페이지의 텍스트를 파일로 저장
            text_filename = os.path.join(TextOutputDir, f'{projectName}_Pages', f'{projectName}_Page_{i}.txt')
            BookTextList.append(text)
            with open(text_filename, 'w', encoding = 'utf-8') as text_file:
                text_file.write(text)
                
    return BookTextList

## InputList 페이지별 단어 가장 앞/뒤 부분의 재배치
def FixSplitWords(InputList):
    for i in range(len(InputList) - 1):
        current_entry = InputList[i]
        next_entry = InputList[i + 1]

        # 현재와 다음 엔트리가 모두 "Body"인 경우에만 처리합니다.
        if current_entry["PageElement"] == "Body" and next_entry["PageElement"] == "Body":
            second_continue = next_entry["Continue"]
            # 정규식을 사용하여 선행 공백, 첫 번째 단어, 나머지로 분리합니다.
            # re.DOTALL 플래그를 사용하여 줄바꿈 문자를 포함합니다.
            match = re.match(r'(\s*)(\S*)(.*)', second_continue, re.DOTALL)

            if match:
                leading_spaces = match.group(1)
                first_word = match.group(2)
                rest_of_text = match.group(3)
                # 선행 공백이 없고 첫 번째 단어가 존재하면 분리된 단어로 판단합니다.
                if leading_spaces == '' and first_word != '':
                    # 첫 번째 단어를 현재 엔트리의 "Continue"에 추가합니다.
                    current_entry["Continue"] += first_word
                    # 다음 엔트리의 "Continue"에서 첫 번째 단어를 제거합니다.
                    next_entry["Continue"] = rest_of_text
                else:
                    continue
            else:
                continue
    return InputList

## InputList의 Body부분 합치고 Id 재정렬
def MergeBodyElements(InputList):
    MergedInputList = []
    i = 0
    new_id = 1
    
    while i < len(InputList):
        current_element = InputList[i]
        if current_element["PageElement"].lower() == "body":
            if i + 1 < len(InputList) and InputList[i + 1]["PageElement"].lower() == "body":
                # Merge the current and next Body elements
                merged_element = {
                    "Id": new_id,
                    "Continue": current_element["Continue"] + InputList[i + 1]["Continue"],
                    "PageElement": "Body"
                }
                MergedInputList.append(merged_element)
                new_id += 1
                i += 2  # Skip the next element as it has been merged
            else:
                # Add the current element without merging
                current_element["Id"] = new_id
                MergedInputList.append(current_element)
                new_id += 1
                i += 1
        else:
            # Add non-Body elements without merging
            current_element["Id"] = new_id
            MergedInputList.append(current_element)
            new_id += 1
            i += 1
    
    return MergedInputList

## TextFile의 BookPreprocessInputList 치환 (인덱스, 캡션 부분 합치기)
def BookPreprocessInputList(projectName, email, IndexLength = 50):
    # 경로 설정
    TextDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script/{projectName}_upload_script_file"
    JsonPath = os.path.join(TextDirPath, f'[{projectName}_PDFSetting].json')
    TextOutputDir = TextDirPath + f'/{projectName}_Text'
    ## JSON 파일이 없으면 생성
    if not os.path.exists(JsonPath):
        print(f"JSON 파일을 생성합니다: {JsonPath}")
        ## PDFBookToTextSetting.json 생성
        pdfBookToTextSetting = {
            "ProjectName": f"{projectName}",
            "PDFBookToTextSetting": {
                "PageForm": "Normal", # 1페이지씩 구성된 경우는 "Normal", 2페이지씩 구성된 경우는 "Wide"
                "Left": 1, # 페이지의 좌측 1-0 값으로, 1이면 모두, 0이면 없음
                "Right": 1, # 페이지의 우측 1-0 값으로, 1이면 모두, 0이면 없음
                "Up": 1, # 페이지의 위측 1-0 값으로, 1이면 모두, 0이면 없음
                "Down": 1, # 페이지의 아래측 1-0 값으로, 1이면 모두, 0이면 없음
                "TitlePages": [1], # {projectName}_Cropped.pdf 파일에서 Title이 존재하는 페이지의 리스트
                "IndexPages": [2, 3], # {projectName}_Cropped.pdf 파일에서 목차이 존재하는 페이지 리스트
                "indexPages": [], # {projectName}_Cropped.pdf 파일에서 각 목차의 내용이 존재하는 페이지 리스트
                "DeletePages": [],  # {projectName}_Cropped.pdf 파일에서 중복되어 필요없는 페이지 리스트
                "SettingCompletion": "세팅 완료 후 Completion",
                "PDFBookToTextCompletion": "완료 후 Completion으로 자동변경",
                "InspectionCompletion": "완료 후 Completion으로 자동변경"
            }
        }
        with open(JsonPath, 'w', encoding = 'utf-8') as json_file:
            json.dump(pdfBookToTextSetting, json_file, ensure_ascii = False, indent = 4)
 
    ## JSON 파일 불러오기
    with open(JsonPath, 'r', encoding = 'utf-8') as json_file:
        PDFBookToTextSetting = json.load(json_file)

    ## PDFBookToTextSetting.json 생성
    if PDFBookToTextSetting['PDFBookToTextSetting']['PDFBookToTextCompletion'] != 'Completion':
        BookTextList = PDFBookToText(projectName, email, PDFBookToTextSetting)

        InputList = []
        if PDFBookToTextSetting['PDFBookToTextSetting']['SettingCompletion'] == 'Completion':
            TitlePages = PDFBookToTextSetting['PDFBookToTextSetting']['TitlePages']
            IndexPages = PDFBookToTextSetting['PDFBookToTextSetting']['IndexPages']
            DeletePages = PDFBookToTextSetting['PDFBookToTextSetting']['DeletePages']
            for i, BookText in enumerate(BookTextList, start = 1):
                Input = {'Id': i, 'Continue': BookText, 'PageElement': None}
                if BookText != '' and i not in DeletePages:
                    if i in TitlePages:
                        Input['Continue'] = f'{BookText}\n\n'
                        Input['PageElement'] = 'Title'
                    elif i in IndexPages:
                        Input['Continue'] = f'\n{BookText}\n'
                        Input['PageElement'] = 'Index'
                    elif (len(BookText) <= IndexLength) and ((len(BookText) >= 3 and '.' not in BookText[-3:]) or (len(BookText) < 3 and '.' not in BookText)):
                        Input['Continue'] = f'\n\n{BookText}\n\n'
                        Input['PageElement'] = 'index'
                    else:
                        Input['PageElement'] = 'Body'
                    InputList.append(Input)
            
            # InputList 페이지별 단어 가장 앞/뒤 부분의 재배치
            InputList = FixSplitWords(InputList)
            # InputList의 Body부분 합치고 Id 재정렬
            MergedInputList = MergeBodyElements(InputList)
            # InputList의 정렬
            ArraiedInputList = []
            for InputList in MergedInputList:
                ArraiedInput = {'Id': InputList['Id'], 'Continue': InputList['Continue'], 'PageElement': InputList['PageElement']}
                ArraiedInputList.append(ArraiedInput)
            
            # JSON 파일로 저장
            with open(os.path.join(TextOutputDir, f'{projectName}_InputList.json'), 'w', encoding = 'utf-8') as InputListJson:
                json.dump(ArraiedInputList, InputListJson, ensure_ascii = False, indent = 4)
            
            # "PDFBookToTextCompletion" = Completion
            PDFBookToTextSetting['PDFBookToTextSetting']['PDFBookToTextCompletion'] = 'Completion'
            # JSON 파일 저장
            with open(JsonPath, 'w', encoding = 'utf-8') as json_file:
                json.dump(PDFBookToTextSetting, json_file, ensure_ascii = False, indent = 4)
        else:
            sys.exit(f'\n[ (([{projectName}_PDFSetting.json])) 세팅을 완료하세요 ]\n({JsonPath})\n')
    else:
        with open(os.path.join(TextOutputDir, f'{projectName}_InputList.json'), 'r', encoding = 'utf-8') as InputListJson:
            ArraiedInputList = json.load(InputListJson)
        
    return ArraiedInputList

######################
##### Filter 조건 #####
######################
## BookPreprocess의 Filter(Error 예외처리)
def BookPreprocessFilter(responseData):
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
def BookPreprocessInputMemory(inputMemoryDics, MemoryLength):
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
def BookPreprocessOutputMemory(outputMemoryDics, MemoryLength):
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
## BookPreprocess 프롬프트 요청 및 결과물 Json화
def BookPreprocessProcess(projectName, email, DataFramePath, Process = "BookPreprocess", memoryLength = 2, MessagesReview = "on", Mode = "Memory"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, "BookPreprocess")

    OutputMemoryDicsFile, OutputMemoryCount = LoadOutputMemory(projectName, email, '00', DataFramePath)
    inputList = BookPreprocessInputList(projectName, email)
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
        
    # BookPreprocessProcess
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
            memoryCounter = "- 구두점(, .), 따옴표(“” \" ')는 낭독에서 매우 중요함으로, 절대로 절대로 수정 및 추가, 삭제 하지 않습니다. -\n"
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
                    
            Filter = BookPreprocessFilter(responseData)
            
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
            inputMemory = BookPreprocessInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = BookPreprocessOutputMemory(outputMemoryDics, MemoryLength)
        
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
def BookPreprocessResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):   
    ### A. 데이터 치환 ###
    outputMemoryDics, inputList = BookPreprocessProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)
    
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
    TextDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script/{projectName}_upload_script_file"
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

## 프롬프트 요청 및 결과물 Json을 BookPreprocess에 업데이트
def BookPreprocessUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    # 경로 설정
    TextDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script/{projectName}_upload_script_file"
    IndexTextFilePath = TextDirPath + f'/{projectName}_Index.txt'
    BodyTextFilePath = TextDirPath + f'/{projectName}_Body.txt'
    
    if not (os.path.exists(IndexTextFilePath) and os.path.exists(BodyTextFilePath)):
        
        print(f"< User: {email} | Project: {projectName} | 00_BookPreprocessUpdate 시작 >")
        # BookPreprocess의 Count값 가져오기
        PageCount, Completion = BookPreprocessCountLoad(projectName, email)
        if Completion == "No":
            
            if ExistedDataFrame != None:
                # 이전 작업이 존재할 경우 가져온 뒤 업데이트
                AddExistedBookPreprocessToDB(projectName, email, ExistedDataFrame)
                AddExistedDataSetToDB(projectName, email, "BookPreprocess", ExistedDataSet)
                print(f"[ User: {email} | Project: {projectName} | 00_BookPreprocessUpdate는 ExistedBookPreprocess으로 대처됨 ]\n")
                
                _, TextProcess = BookPreprocessResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)

                if TextProcess == False:
                    sys.exit(f"\n\n[ ((({projectName}_Index.txt))), ((({projectName}_Body.txt))) 파일을 완성하여 아래 경로에 복사해주세요. ]\n({TextDirPath})\n\n1. 목차(_Index)파일과 본문(_Body) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n2. 본문(_Body)파일 내 쌍따옴표(“대화문”의 완성) 개수 일치 * _Body(검수용) 파일 확인\n3. 캡션 등의 줄바꿈 및 캡션이 아닌 일반 문장은 마지막 온점(.)처리\n\n")
                else:
                    time.sleep(0.1)
            else:
                responseJson, _ = BookPreprocessResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
                
                # ResponseJson을 ContinueCount로 슬라이스
                ResponseJson = responseJson[PageCount:]
                ResponseJsonCount = len(ResponseJson)

                # TQDM 셋팅
                UpdateTQDM = tqdm(ResponseJson,
                                total = ResponseJsonCount,
                                desc = 'BookPreprocessUpdate')
                # i값 수동 생성
                i = 0
                for Update in UpdateTQDM:
                    UpdateTQDM.set_description(f'BookPreprocessUpdate: {Update["Script"][:10]}...')
                    time.sleep(0.0001)
                    PageId = Update["PageId"]
                    PageElement = Update["PageElement"]
                    Script = Update["Script"]
                    
                    AddBookPreprocessBookPagesToDB(projectName, email, PageId, PageElement, Script)
                    # i값 수동 업데이트
                    i += 1
                
                UpdateTQDM.close()
                # Completion "Yes" 업데이트
                BookPreprocessCompletionUpdate(projectName, email)
                print(f"[ User: {email} | Project: {projectName} | 00_BookPreprocessUpdate 완료 ]\n")
        else:
            print(f"[ User: {email} | Project: {projectName} | 00_BookPreprocessUpdate는 이미 완료됨 ]\n")
    else:
        print(f"[ User: {email} | Project: {projectName} | 00_BookPreprocessUpdate는 ExistedBookPreprocess으로 대처됨 ]\n")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "241005_그해여름필립로커웨이에서일어난소설같은일"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################