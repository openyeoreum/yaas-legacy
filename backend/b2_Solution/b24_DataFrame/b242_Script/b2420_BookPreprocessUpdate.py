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
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedBookPreprocessToDB, AddBookPreprocessBookPagesToDB, BookPreprocessCountLoad, BookPreprocessCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################

## PDF파일 편집
def PDFBookCropping(projectName, email, TextDirPath):
    # PDF 파일 경로 설정
    JsonPath = TextDirPath + f'/[{projectName}_PDFToTextSetting].json'
    PDFPath = TextDirPath + f'/{projectName}.pdf'
    NormalPDFPath = TextDirPath + f'/{projectName}_Normal.pdf'
    CroppedPDFPath = TextDirPath + f'/{projectName}_Cropped.pdf'

    # 1. PDFBookToTextSetting.json 생성
    PDFBookToTextSetting = {
        "ProjectName": f"{projectName}",
        "PDFBookToTextSetting": {
            "PageForm": "Normal", # 1페이지씩 구성된 경우는 "Normal", 2페이지씩 구성된 경우는 "Wide"
            "Left": 1, # 페이지의 좌측 1-0 값으로, 1이면 모두, 0이면 없음
            "Right": 1, # 페이지의 우측 1-0 값으로, 1이면 모두, 0이면 없음
            "Up": 1, # 페이지의 위측 1-0 값으로, 1이면 모두, 0이면 없음
            "Down": 1, # 페이지의 아래측 1-0 값으로, 1이면 모두, 0이면 없음
            "TitlePages": [1], # {projectName}_Cropped.pdf 파일에서 Title이 존재하는 페이지의 리스트
            "IndexPages": [2, 3], # {projectName}_Cropped.pdf 파일에서 Title이 존재하는 페이지 리스트
            "DuplicatePage": [],  # {projectName}_Cropped.pdf 파일에서 중복되어 필요없는 페이지 리스트
            "SettingCompletion": "세팅 완료 후 Completion으로 변경",
            "IndexBodyCompletion": "_Index.txt, _Body.txt 완료 후 Completion으로 변경"
        }
    }
    
    # JSON 파일이 없으면 생성
    if not os.path.exists(JsonPath):
        with open(JsonPath, 'w', encoding='utf-8') as json_file:
            json.dump(PDFBookToTextSetting, json_file, ensure_ascii = False, indent = 4)
            
    # JSON 파일 불러오기
    with open(JsonPath, 'r', encoding='utf-8') as json_file:
        PDFBookToTextSetting = json.load(json_file)
    
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

    ## 2. 페이지 분할
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

    ## 3. 페이지별 사이즈 잘라내기
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
        
    return PDFBookToTextSetting, JsonPath

## PDF파일 편집 및 텍스트화
def PDFBookToText(projectName, email):
    # 경로 설정
    TextDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script_file"
    CroppedPDFPath = TextDirPath + f'/{projectName}_Cropped.pdf'
    TextOutputDir = TextDirPath + f'/{projectName}_Text'
    # PDF파일 편집
    PDFBookToTextSetting, JsonPath = PDFBookCropping(projectName, email, TextDirPath)
    # 텍스트 출력 폴더 생성
    os.makedirs(TextOutputDir, exist_ok = True)

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
            text_filename = os.path.join(TextOutputDir, f'{projectName}_Page_{i}.txt')
            BookTextList.append(text)
            with open(text_filename, 'w', encoding='utf-8') as text_file:
                text_file.write(text)
                
    return BookTextList, PDFBookToTextSetting, TextOutputDir, JsonPath

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
                    "PageElement": "Body",
                    "Continue": current_element["Continue"] + InputList[i + 1]["Continue"]
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
    BookTextList, PDFBookToTextSetting, TextOutputDir, JsonPath = PDFBookToText(projectName, email)

    InputList = []
    if PDFBookToTextSetting['PDFBookToTextSetting']['SettingCompletion'] == 'Completion':
        TitlePages = PDFBookToTextSetting['PDFBookToTextSetting']['TitlePages']
        IndexPages = PDFBookToTextSetting['PDFBookToTextSetting']['IndexPages']
        DuplicatePage = PDFBookToTextSetting['PDFBookToTextSetting']['DuplicatePage']
        for i, BookText in enumerate(BookTextList, start = 1):
            Input = {'Id': i, 'PageElement': '', 'Continue': BookText}
            if BookText != '' and i not in DuplicatePage:
                if i in TitlePages:
                    Input['PageElement'] = 'Title'
                    Input['Continue'] = f'{BookText}\n\n'
                elif i in IndexPages:
                    Input['PageElement'] = 'Index'
                    Input['Continue'] = f'\n{BookText}\n'
                elif (len(BookText) <= IndexLength) and ((len(BookText) >= 3 and '.' not in BookText[-3:]) or (len(BookText) < 3 and '.' not in BookText)):
                    Input['PageElement'] = 'index'
                    Input['Continue'] = f'\n\n{BookText}\n\n'
                else:
                    Input['PageElement'] = 'Body'
                InputList.append(Input)
        
        # InputList 페이지별 단어 가장 앞/뒤 부분의 재배치
        InputList = FixSplitWords(InputList)
        # InputList의 Body부분 합치고 Id 재정렬
        MergedInputList = MergeBodyElements(InputList)
        
        # JSON 파일로 저장
        with open(os.path.join(TextOutputDir, f'{projectName}_BookPreprocess_InputList.json'), 'w', encoding = 'utf-8') as InputListJson:
            json.dump(MergedInputList, InputListJson, ensure_ascii = False, indent = 4)
    else:
        sys.exit(f'[ PDF To Text 세팅을 완료하세요 : {JsonPath} ]')

    return InputList

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
    # # Error3: 결과가 '말하는인물'이 '없음'일 때의 예외 처리 (없음일 경우에는 Narrator 낭독)
    # for dic in OutputDic:
    #     for key, value in dic.items():
    #         if value['말하는인물'] == '없음' or value['말하는인물'] == '' or value['말하는인물'] == 'none':
    #             return "'말하는인물': '없음' 오류 발생: NonValueError"
    # Error4: 자료의 구조가 다를 때의 예외 처리
    for dic in OutputDic:
        try:
            key = list(dic.keys())[0]
            if not key in TalkTag:
                return "JSON에서 오류 발생: JSONKeyError"
            else:
                if not ('말의종류' in dic[key] and '말하는인물' in dic[key] and '말하는인물의성별' in dic[key] and '말하는인물의나이' in dic[key] and '말하는인물의감정' in dic[key] and '인물의역할' in dic[key] and '듣는인물' in dic[key]):
                    return "JSON에서 오류 발생: JSONKeyError"
        # Error5: 자료의 형태가 Str일 때의 예외처리
        except AttributeError:
            return "JSON에서 오류 발생: strJSONError"
    # Error6: Input과 Output의 개수가 다를 때의 예외처리
    if len(OutputDic) != len(TalkTag):
        return "JSONCount에서 오류 발생: JSONCountError"

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
            PageElement = InputDic['PageElement']
            memoryCounter = ""
            outputEnder = ""

            if PageElement == "Body":
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
                print(Response)
                sys.exit()
                        
                Filter = BookPreprocessFilter(responseData)
            else:
                pass
            
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
            inputMemory = BookPreprocessInputMemory(inputMemoryDics, MemoryLength)
        except IndexError:
            pass
        
        # outputMemory 형성
        outputMemoryDics.append(OutputDic)
        outputMemory = BookPreprocessOutputMemory(outputMemoryDics, MemoryLength)
        
        SaveOutputMemory(projectName, email, outputMemoryDics, '02-1', DataFramePath)
    
    return outputMemoryDics

################################
##### 데이터 치환 및 DB 업데이트 #####
################################
    
## 데이터 치환
def BookPreprocessResponseJson(projectName, email, DataFramePath, messagesReview = 'off', mode = "Memory"):
    # Chunk, ChunkId 데이터 추출
    project = GetProject(projectName, email)
    BodyFrame = project.BodyFrame[1]['SplitedBodyScripts'][1:]
    CharacterTagChunk = []
    CharacterTagChunkId = []
    for i in range(len(BodyFrame)):
        for j in range(len(BodyFrame[i]['SplitedBodyChunks'])):
            if BodyFrame[i]['SplitedBodyChunks'][j]['Tag'] == "Character":
                CharacterTagChunk.append(BodyFrame[i]['SplitedBodyChunks'][j]['Chunk'])
                CharacterTagChunkId.append(BodyFrame[i]['SplitedBodyChunks'][j]['ChunkId'])
    
    # 데이터 치환
    outputMemoryDics = BookPreprocessProcess(projectName, email, DataFramePath, MessagesReview = messagesReview, Mode = mode)
    
    responseJson = []
    responseCount = 0
    
    for response in outputMemoryDics:
        if response != "Pass":
            for dic in response:
                ChunkId = CharacterTagChunkId[responseCount]
                Chunk = CharacterTagChunk[responseCount]
                for key, value in dic.items():
                    Character = value['말하는인물']
                    Type = value['말의종류']
                    Gender = value['말하는인물의성별']
                    Age = value['말하는인물의나이']
                    Emotion = value['말하는인물의감정']
                    Role = value['인물의역할']
                    Listener = value['듣는인물']
                responseCount += 1
                responseJson.append({"ChunkId": ChunkId, "Chunk": Chunk, "Character": Character, "Type": Type, "Gender": Gender, "Age": Age, "Emotion": Emotion, "Role": Role, "Listener": Listener})
    
    return responseJson

## 프롬프트 요청 및 결과물 Json을 BookPreprocess에 업데이트
def BookPreprocessUpdate(projectName, email, DataFramePath, MessagesReview = 'off', Mode = "Memory", ExistedDataFrame = None, ExistedDataSet = None):
    print(f"< User: {email} | Project: {projectName} | 00_BookPreprocessUpdate 시작 >")
    # BookPreprocess의 Count값 가져오기
    ContinueCount, CharacterCount, Completion = BookPreprocessCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedBookPreprocessToDB(projectName, email, ExistedDataFrame)
            AddExistedDataSetToDB(projectName, email, "BookPreprocess", ExistedDataSet)
            print(f"[ User: {email} | Project: {projectName} | 00_BookPreprocessUpdate는 ExistedBookPreprocess으로 대처됨 ]\n")
        else:
            responseJson = BookPreprocessResponseJson(projectName, email, DataFramePath, messagesReview = MessagesReview, mode = Mode)
            
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = responseJson[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)
            
            CharacterChunkId = ContinueCount
            
            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'BookPreprocessUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'BookPreprocessUpdate: {Update}')
                time.sleep(0.0001)
                CharacterChunkId += 1
                ChunkId = Update["ChunkId"]
                Chunk = Update["Chunk"]
                Character = Update["Character"]
                Type = Update["Type"]
                Gender = Update["Gender"]
                Age = Update["Age"]
                Emotion = Update["Emotion"]
                Role = Update["Role"]
                Listener = Update["Listener"]
                
                AddBookPreprocessChunksToDB(projectName, email, CharacterChunkId, ChunkId, Chunk, Character, Type, Gender, Age, Emotion, Role, Listener)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            BookPreprocessCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 00_BookPreprocessUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 00_BookPreprocessUpdate는 이미 완료됨 ]\n")
        
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
                    
    # 예제 호출
    BookPreprocessProcess(projectName, email, DataFramePath)