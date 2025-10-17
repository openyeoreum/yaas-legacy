import os
import re
import json
import base64
import time
import unicodedata
import sys
sys.path.append("/yaas")

from mistralai import Mistral
from langdetect import detect_langs, DetectorFactory
from agent.a3_Operation.a32_Solution.a321_LoadLLM import OpenAI_LLMresponse, ANTHROPIC_LLMresponse, GOOGLE_LLMresponse, DEEPSEEK_LLMresponse

###############################################
##### Translation PDF, Index, Body 불러오기 #####
###############################################
## Load1-1: TranslationPDF 경로 불러오기
def LoadTranslationPDFPath(projectName, UploadTranslationFilePath):
    # TranslationPDF 경로 설정
    TranslationPDFFileName = f"{projectName}(Translation).pdf"
    TranslationPDFFilePath = os.path.join(UploadTranslationFilePath, TranslationPDFFileName)
    
    # TranslationPDF 불러오기
    if os.path.exists(TranslationPDFFilePath):
        OCRDirectoryPath = os.path.join(UploadTranslationFilePath, f"{projectName}_OCR")
        os.makedirs(OCRDirectoryPath, exist_ok = True)
    else:
        sys.exit(f"\n\n[ ((({projectName}(Translation).pdf))) 또는 ((({projectName}_Index(Translation).txt))), ((({projectName}_Body(Translation).txt))) 파일을 완성하여 아래 경로에 복사해주세요. ]\n({UploadTranslationFilePath})\n\n1. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n3. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차는 <제목>의 형태로 괄호처리 권장\n3. 본문((_Body(Translation)))파일 내 쌍따옴표(“대화문”의 완성) 개수 일치\n\n")
        
    return TranslationPDFFileName, TranslationPDFFilePath, OCRDirectoryPath

## Load1-2: TranslationPDF OCR
def OCRTranslationPDF(projectName, UploadTranslationFilePath):
    ## TranslationBody 경로 설정
    TranslationBodyFileName = f"{projectName}_Body(Translation).txt"
    TranslationBodyFilePath = os.path.join(UploadTranslationFilePath, TranslationBodyFileName)
    
    ## TranslationIndex 경로 설정
    TranslationIndexFileName = f"{projectName}_Index(Translation).txt"
    TranslationIndexFilePath = os.path.join(UploadTranslationFilePath, TranslationIndexFileName)
    
    ## TranslationIndex 존재확인
    if not os.path.exists(TranslationIndexFilePath):
        ## TranslationBody 존재확인
        if not os.path.exists(TranslationBodyFilePath):
            ## 환경 변수에서 API 키를 불러오고 클라이언트 초기화
            MistralClient = Mistral(api_key = os.getenv("MISTRAL_API_KEY"))

            ## OCR할 PDF 파일 경로 설정
            TranslationPDFFileName, TranslationPDFFilePath, OCRDirectoryPath = LoadTranslationPDFPath(projectName, UploadTranslationFilePath)

            ## PDF 파일을 OCR 용도로 업로드
            with open(TranslationPDFFilePath, "rb") as TranslationPDFFile:
                UploadedPDF = MistralClient.files.upload(
                    file = {
                        "file_name": TranslationPDFFileName,
                        "content": TranslationPDFFile,
                    },
                    purpose = "ocr"
                )

            ## 업로드된 파일의 서명된 URL을 받아옴
            SignedURL = MistralClient.files.get_signed_url(file_id=UploadedPDF.id)

            ## 서명된 URL을 이용하여 OCR 처리 수행 (이미지 데이터 포함)
            OCRresponse = MistralClient.ocr.process(
                model = "mistral-ocr-latest",
                document = {
                    "type": "document_url",
                    "document_url": SignedURL.url,
                },
                include_image_base64 = True
            )

            ## 전체 OCR 응답을 JSON 형식으로 저장
            OCRresponseJson = json.dumps(OCRresponse.model_dump(), indent = 4, ensure_ascii = False)
            OCRresponseJsonFileName = os.path.join(OCRDirectoryPath, f"{projectName}_OCR.json")
            with open(OCRresponseJsonFileName, "w", encoding = "utf-8") as f:
                f.write(OCRresponseJson)

            ## 각 페이지별로 markdown 텍스트와 이미지 저장
            OCRTextFilePath = os.path.join(UploadTranslationFilePath, f"{projectName}_Body(Translation).txt")
            with open(OCRTextFilePath, "w", encoding = "utf-8") as OCRTextFile:
                for BookPage in OCRresponse.pages:
                    # 페이지 번호 (예: 1, 2, …)를 사용하여 파일명 생성
                    BookPageIndex = BookPage.index

                    # 페이지의 markdown 텍스트 저장 (있을 경우)
                    if hasattr(BookPage, "markdown") and BookPage.markdown:
                        # 현재 페이지의 markdown 텍스트를 작성하고, 끝에 두 줄바꿈 추가
                        OCRTextFile.write(BookPage.markdown + f"\n\n@({BookPageIndex + 2})@\n\n")
                    
                    # 페이지 내 이미지가 존재할 경우 저장
                    if hasattr(BookPage, "images") and BookPage.images:
                        for Image in BookPage.images:
                            # 이미지 객체에서 id와 base64 문자열 추출 (딕셔너리 대신 속성 접근)
                            ImageId = Image.id
                            ImageBase64str = Image.image_base64
                            if ImageBase64str:
                                # "data:image/jpeg;base64," 접두사가 있으면 제거
                                prefix = "data:image/jpeg;base64,"
                                if ImageBase64str.startswith(prefix):
                                    ImageBase64str = ImageBase64str[len(prefix):]
                                try:
                                    ImageData = base64.b64decode(ImageBase64str)
                                except Exception as e:
                                    print(f"페이지 {BookPageIndex}의 이미지 {ImageId} 디코딩 실패: {e}")
                                    continue
                                # 저장할 이미지 파일 경로 (예: 프로젝트명과 페이지 번호를 포함하여 생성)
                                ImageFilePath = os.path.join(OCRDirectoryPath, f"{projectName}_Image({BookPageIndex}).jpeg")
                                with open(ImageFilePath, "wb") as ImageFile:
                                    ImageFile.write(ImageData)
                                print(f"페이지 {BookPageIndex}의 이미지 ({f'{projectName}_Image({BookPageIndex}).jpeg'})가 저장되었습니다.")

            sys.exit(f"\n\n[ ((({projectName}_Index(Translation).txt)))을 ((({projectName}_Body(Translation).txt))) 파일에 따라서 완성해주세요. ]\n({TranslationBodyFilePath})\n\n1. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n3. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차는 <제목>의 형태로 괄호처리 권장\n3. 본문((_Body(Translation)))파일 내 쌍따옴표(“대화문”의 완성) 개수 일치\n\n")
        else:
            sys.exit(f"\n\n[ ((({projectName}_Index(Translation).txt)))을 ((({projectName}_Body(Translation).txt))) 파일에 따라서 완성해주세요. ]\n({TranslationBodyFilePath})\n\n1. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n3. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차는 <제목>의 형태로 괄호처리 권장\n3. 본문((_Body(Translation)))파일 내 쌍따옴표(“대화문”의 완성) 개수 일치\n\n")

## Load2: TranslationIndex 불러오기
def LoadTranslationIndex(projectName, UploadTranslationFilePath):
    # TranslationIndex 경로 설정
    TranslationIndexFileName = f"{projectName}_Index(Translation).txt"
    TranslationIndexFilePath = os.path.join(UploadTranslationFilePath, TranslationIndexFileName)
    
    # TranslationIndex 불러오기
    if os.path.exists(TranslationIndexFilePath):
        with open(TranslationIndexFilePath, "r") as TranslationIndexFile:
            TranslationIndex = TranslationIndexFile.read()
    # else:
    #     sys.exit(f"\n\n[ ((({projectName}_Index(Translation).txt))), ((({projectName}_Body(Translation).txt))) 파일을 완성하여 아래 경로에 복사해주세요. ]\n({UploadTranslationFilePath})\n\n1. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n3. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차는 <제목>의 형태로 괄호처리 권장\n3. 본문((_Body(Translation)))파일 내 쌍따옴표(“대화문”의 완성) 개수 일치\n\n")
    
    return TranslationIndex

## Load3: TranslationSplitBody 불러오기
def LoadTranslationSplitBody(projectName, UploadTranslationFilePath, TranslationEditPath, BeforeProcess):
    # TranslationIndex 불러오기
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationIndex = json.load(TranslationEditJson)[BeforeProcess]
    # TranslationBody 경로 설정
    TranslationBodyFileName = f"{projectName}_Body(Translation).txt"
    TranslationBodyFilePath = os.path.join(UploadTranslationFilePath, TranslationBodyFileName)
    
    # TranslationBody 불러오기
    if os.path.exists(TranslationBodyFilePath):
        with open(TranslationBodyFilePath, "r") as TranslationBodyFile:
            TranslationBody = TranslationBodyFile.read()
    # else:
    #     sys.exit(f"\n\n[ ((({projectName}_Index(Translation).txt))), ((({projectName}_Body(Translation).txt))) 파일을 완성하여 아래 경로에 복사해주세요. ]\n({UploadTranslationFilePath})\n\n1. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n3. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차는 <제목>의 형태로 괄호처리 권장\n3. 본문((_Body(Translation)))파일 내 쌍따옴표(“대화문”의 완성) 개수 일치\n\n")
        
    return TranslationIndex, TranslationBody, TranslationBodyFilePath

########################################
##### TranslationBodySplit Process #####
########################################
## Process1: MaxLength 이상인 경우 분할 함수
def SplitBySentence(TranslationBodyFilePath, ProjectName, IndexText, SectionText, MaxLength):
    ## 초기화 및 유효성 검사를 수행하는 함수
    def InitializeAndValidate(TranslationBodyFilePath, ProjectName, IndexText, SectionText):
        # 쌍따옴표, 따옴표 일치화
        SectionText = SectionText.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
        
        # 따옴표 균형 확인
        if SectionText.count('"') % 2 != 0:
            FirstPart = SectionText[:20] if len(SectionText) > 20 else SectionText
            LastPart = SectionText[-20:] if len(SectionText) > 20 else SectionText
            sys.exit(f"TranslationBodySplit 따옴표 개수 홀수 오류: Project: {ProjectName} | Process: TranslationBodySplit | SplitBodyError\n[ 아래 경로 파일 {ProjectName}_Body(Translation).txt -> <{IndexText}> -> ({FirstPart} ... {LastPart}) 문단에서 따옴표 개수가 홀수개 입니다. ]\n{TranslationBodyFilePath}")
        
        # 주석 패턴 정규식 (도서 본문의 주석 [^n: ...])
        FootnotePattern = re.compile(r'\[\^(\d+):\s*(.*?)\]', re.DOTALL)
        
        # 주석 위치와 내용을 리스트로 저장
        FootnoteMatches = list(FootnotePattern.finditer(SectionText))
        
        return SectionText, FootnoteMatches

    ## 대화문 처리 및 분할 함수
    # – 대화문 내부에 주석이 포함된 경우, 해당 대화문은 MaxLength와 상관없이 하나의 단위로 처리합니다.
    def ProcessDialoguesAndFootnotes(SectionText, FootnoteMatches, MaxLength):
        ProcessedText = ""
        dialogueBuffer = None  # 대화문이 열려있으면 대화 내용을 누적 (없으면 None)
        dialogueHasFootnote = False  # 대화문 내에 주석이 포함되었는지 여부
        AdditionalQuotesCount = 0

        currentFootnoteIndex = 0
        i = 0
        while i < len(SectionText):
            # 주석 시작 위치 확인
            if currentFootnoteIndex < len(FootnoteMatches) and i == FootnoteMatches[currentFootnoteIndex].start():
                footnote = FootnoteMatches[currentFootnoteIndex].group(0)
                footnoteEnd = i + len(footnote)
                # 대화문 내부인 경우: 주석을 대화문 내용에 포함하고, 분할 대상에서 제외
                if dialogueBuffer is not None:
                    dialogueHasFootnote = True
                    dialogueBuffer += footnote
                else:
                    ProcessedText += footnote
                i = footnoteEnd
                currentFootnoteIndex += 1
                continue

            c = SectionText[i]
            if c == '"':
                # 따옴표를 만나면 대화문 상태 전환
                if dialogueBuffer is None:
                    # 대화문 시작: 새 버퍼를 생성하고(아직 따옴표는 나중에 추가)
                    dialogueBuffer = ""
                    dialogueHasFootnote = False
                    i += 1
                else:
                    # 대화문 종료 시: 대화문 내용을 처리
                    # 만약 대화문 내에 주석이 없다면 MaxLength 초과 시 분할
                    if not dialogueHasFootnote and len(dialogueBuffer) > MaxLength:
                        # 분할을 위해 기존에 추가된 시작 따옴표는 제거한 후 분할 함수 호출
                        splitDialogue, extra_quotes = SplitLongDialogueBuffer(dialogueBuffer, MaxLength)
                        AdditionalQuotesCount += extra_quotes
                        ProcessedText += splitDialogue
                    else:
                        ProcessedText += '"' + dialogueBuffer + '"'
                    dialogueBuffer = None
                    dialogueHasFootnote = False
                    i += 1
            else:
                # 대화문 내부이면 버퍼에 누적, 아니면 바로 출력
                if dialogueBuffer is not None:
                    dialogueBuffer += c
                else:
                    ProcessedText += c
                i += 1

        # 만약 대화문이 끝나지 않고 남아있으면 그냥 닫아서 추가 (유효성 검사상 이 경우는 없을 것)
        if dialogueBuffer is not None:
            ProcessedText += '"' + dialogueBuffer
        return ProcessedText, AdditionalQuotesCount

    ## 긴 대화문을 적절하게 분할하는 함수 (대화문 내 주석이 없을 때만 호출됨)
    def SplitLongDialogueBuffer(dialogueContent, MaxLength):
        dialogueLength = len(dialogueContent)
        numSplits = max(2, (dialogueLength + MaxLength - 1) // MaxLength)
        splitSize = dialogueLength // numSplits
        if splitSize > MaxLength:
            numSplits = (dialogueLength + MaxLength - 1) // MaxLength
            splitSize = dialogueLength // numSplits
        sections = []
        start = 0
        while start < len(dialogueContent):
            end = min(start + splitSize, len(dialogueContent))
            if len(dialogueContent) - end < splitSize // 3 and sections:
                sections[-1] += dialogueContent[start:]
                break
            sections.append(dialogueContent[start:end])
            start = end
        processedDialogue = ""
        for j, section in enumerate(sections):
            if j > 0:
                processedDialogue += " "
            processedDialogue += f'"{section}"'
        extra_quotes = 2 * len(sections) - 2
        return processedDialogue, extra_quotes

    ## 텍스트를 문장 단위로 분할하는 함수
    def SplitIntoSentences(ProcessedText):
        CommonAbbreviations = [
            'Mr.', 'Mrs.', 'Dr.', 'Prof.', 'Ms.', 'Rev.', 'Capt.', 'Lt.', 'Col.', 'Gen.',
            'St.', 'Ave.', 'Blvd.', 'Rd.', 'Ph.D.', 'M.D.', 'B.A.', 'M.A.', 'Jr.', 'Sr.',
            'Inc.', 'Ltd.', 'Co.', 'Corp.', 'e.g.', 'i.e.', 'etc.', 'vs.', 'Fig.', 'p.',
            'pp.', 'Vol.', 'ex.', 'No.', 'Dept.', 'Jan.', 'Feb.', 'Mar.', 'Apr.', 'Jun.',
            'Jul.', 'Aug.', 'Sep.', 'Sept.', 'Oct.', 'Nov.', 'Dec.', 'a.m.', 'p.m.'
        ]
        SentenceDelimiters = [
            '। ', '۔ ', '؟ ', '։ ', '।\n', '۔\n', '؟\n', '։\n',
            '。 ', '. ', '！ ', '! ', '？ ', '? ',
            '。\n', '.\n', '！\n', '!\n', '？\n', '?\n',
            '.', '!', '?', '।', '۔', '؟', '։', '。', '！', '？'
        ]
        FootnotePattern = re.compile(r'\[\^(\d+):\s*(.*?)\]')
        
        Sentences = []
        Start = 0
        i = 0
        InDialogue = False
        
        ProcessedFootnoteMatches = list(FootnotePattern.finditer(ProcessedText))
        
        while i < len(ProcessedText):
            isFootnoteStart = False
            for match in ProcessedFootnoteMatches:
                if i == match.start():
                    if i > Start:
                        Sentences.append(ProcessedText[Start:i])
                    footnoteText = match.group(0)
                    Sentences.append(footnoteText)
                    Start = match.end()
                    i = Start
                    isFootnoteStart = True
                    break
            if isFootnoteStart:
                continue
                    
            if ProcessedText[i] == '"':
                InDialogue = not InDialogue
            
            if not InDialogue:
                FoundDelimiter = handle_sentence_delimiter(ProcessedText, i, Sentences, Start, SentenceDelimiters, CommonAbbreviations)
                if FoundDelimiter:
                    Start = FoundDelimiter
                    i = Start
                else:
                    i += 1
            else:
                i += 1
        
        if Start < len(ProcessedText):
            Sentences.append(ProcessedText[Start:])
        
        return Sentences

    def handle_sentence_delimiter(ProcessedText, i, Sentences, Start, SentenceDelimiters, CommonAbbreviations):
        for Delimiter in SentenceDelimiters:
            if i + len(Delimiter) <= len(ProcessedText) and ProcessedText[i:i+len(Delimiter)] == Delimiter:
                IsAbbreviation = check_for_abbreviations(ProcessedText, i, Delimiter, CommonAbbreviations)
                if not IsAbbreviation:
                    Sentences.append(ProcessedText[Start:i+len(Delimiter)])
                    return i + len(Delimiter)
        return None

    def check_for_abbreviations(ProcessedText, i, Delimiter, CommonAbbreviations):
        IsAbbreviation = False
        if Delimiter in ['. ', '.\n', '.']:
            for Abbr in CommonAbbreviations:
                CheckStart = max(0, i + 1 - len(Abbr))
                CheckEnd = i + 1
                if CheckStart >= 0 and ProcessedText[CheckStart:CheckEnd] == Abbr:
                    IsAbbreviation = True
                    break
        if Delimiter == '.':
            if i > 0 and i + 1 < len(ProcessedText):
                if ProcessedText[i-1].isdigit() and ProcessedText[i+1].isdigit():
                    IsAbbreviation = True
                elif ProcessedText[i-1].isdigit():
                    IsAbbreviation = True
                elif (i > 2 and ProcessedText[i-2:i].replace('.', '').isdigit() and 
                      i + 4 <= len(ProcessedText) and ProcessedText[i+1:i+4].replace('.', '').isdigit()):
                    IsAbbreviation = True
                elif (i > 0 and ProcessedText[i-1].isalnum() and 
                      i + 1 < len(ProcessedText) and ProcessedText[i+1].isalnum()):
                    IsAbbreviation = True
            if i + 1 < len(ProcessedText) and ProcessedText[i+1].islower():
                IsAbbreviation = True
        return IsAbbreviation

    def SeparateFootnotesAndRegular(Sentences, MaxLength):
        FootnotePattern = re.compile(r'\[\^(\d+):\s*(.*?)\]')
        FootnoteSentences = []
        RegularSentences = []
        for sentence in Sentences:
            if FootnotePattern.match(sentence.strip()):
                if len(sentence) > MaxLength:
                    FootnoteSentences.append(sentence)
                else:
                    RegularSentences.append(sentence)
            else:
                RegularSentences.append(sentence)
        return FootnoteSentences, RegularSentences

    def CreateOptimalSegments(RegularSentences, FootnoteSentences, MaxLength):
        TotalChars = sum(len(sentence) for sentence in RegularSentences)
        NumSubSections = max(1, (TotalChars + MaxLength - 1) // MaxLength)
        TargetSize = TotalChars / NumSubSections if NumSubSections > 0 else 0
        SubSections = []
        CurrentSegment = ""
        for Sentence in RegularSentences:
            PotentialLength = len(CurrentSegment) + len(Sentence)
            if PotentialLength <= MaxLength:
                if (not CurrentSegment or abs(PotentialLength - TargetSize) < abs(len(CurrentSegment) - TargetSize)):
                    CurrentSegment += Sentence
                else:
                    HasNewline = CurrentSegment.endswith('\n')
                    SubSections.append({
                        'CurrentSegment': CurrentSegment,
                        'FinalEnding': '\n' if HasNewline else ''
                    })
                    CurrentSegment = Sentence
            else:
                if CurrentSegment:
                    HasNewline = CurrentSegment.endswith('\n')
                    SubSections.append({
                        'CurrentSegment': CurrentSegment,
                        'FinalEnding': '\n' if HasNewline else ''
                    })
                CurrentSegment = Sentence
        if CurrentSegment:
            HasNewline = CurrentSegment.endswith('\n')
            LastSegment = {
                'CurrentSegment': CurrentSegment,
                'FinalEnding': '\n' if HasNewline else ''
            }
            if SubSections and len(SubSections[-1]['CurrentSegment']) + len(CurrentSegment) <= MaxLength:
                Combined = SubSections[-1]['CurrentSegment'] + CurrentSegment
                SubSections[-1] = {
                    'CurrentSegment': Combined,
                    'FinalEnding': '\n' if Combined.endswith('\n') else ''
                }
            else:
                SubSections.append(LastSegment)
        for footnote in FootnoteSentences:
            HasNewline = footnote.endswith('\n')
            SubSections.append({
                'CurrentSegment': footnote,
                'FinalEnding': '\n' if HasNewline else ''
            })
        return SubSections

    # 실행 순서
    SectionText, FootnoteMatches = InitializeAndValidate(TranslationBodyFilePath, ProjectName, IndexText, SectionText)
    ProcessedText, AdditionalQuotesCount = ProcessDialoguesAndFootnotes(SectionText, FootnoteMatches, MaxLength)
    Sentences = SplitIntoSentences(ProcessedText)
    if not Sentences:
        HasNewline = ProcessedText.endswith('\n')
        return {
            'SubSections': [{'CurrentSegment': ProcessedText, 'FinalEnding': '\n' if HasNewline else ''}],
            'AdditionalQuotes': AdditionalQuotesCount
        }
    FootnoteSentences, RegularSentences = SeparateFootnotesAndRegular(Sentences, MaxLength)
    SubSections = CreateOptimalSegments(RegularSentences, FootnoteSentences, MaxLength)
    return {
        'SubSections': SubSections,
        'AdditionalQuotes': AdditionalQuotesCount
    }

## Process1: TranslationBodySplit Process
def TranslationBodySplitProcess(projectName, UploadTranslationFilePath, TranslationEditPath, BeforeProcess, ProjectDataFrameTranslationIndexDefinePath, MaxLength):
    TranslationIndex, TranslationBody, TranslationBodyFilePath = LoadTranslationSplitBody(projectName, UploadTranslationFilePath, TranslationEditPath, BeforeProcess)

    ## Load1-1: BodyLines와 TranslationIndex 위치 찾기 (수정됨)
    BodyLines = TranslationBody.splitlines()
    IndexPositions = []
    CurrentIndexIdx = 0
    UpdatedTranslationIndex = TranslationIndex.copy()  # TranslationIndex의 복사본 생성

    for lineNum, BodyLine in enumerate(BodyLines):
        # 현재 처리 중인 목차 항목 가져오기
        if CurrentIndexIdx < len(TranslationIndex):
            CurrentIndex = TranslationIndex[CurrentIndexIdx]
            
            # 기본 비교: 정확히 일치하는지 확인
            if BodyLine.strip() == CurrentIndex["Index"].strip():
                # 일치하는 줄을 찾았으므로 위치 기록
                IndexPositions.append((lineNum, CurrentIndex))
                CurrentIndexIdx += 1
            
            # 추가 비교: BodyLine이 <목차> 형태이고 CurrentIndex가 목차 형태인 경우
            elif BodyLine.strip().startswith('<') and BodyLine.strip().endswith('>'):
                # 앵글 브래킷 제거하여 비교
                body_content = BodyLine.strip()[1:-1]  # '<목차>' -> '목차'
                index_content = CurrentIndex["Index"].strip()
                
                if body_content == index_content:
                    # BodyLine 형식에 맞게 CurrentIndex["Index"] 업데이트
                    UpdatedTranslationIndex[CurrentIndexIdx]["Index"] = BodyLine.strip()
                    
                    # 일치하는 줄을 찾았으므로 위치 기록
                    IndexPositions.append((lineNum, CurrentIndex))
                    CurrentIndexIdx += 1

    ## Load1-2: Index와 Body 불일치로 인한 인덱스 누락 확인
    if CurrentIndexIdx != len(TranslationIndex):
        sys.exit(f"Index 불일치 오류 발생: Project: {projectName} | Process: TranslationBodySplit | IndexMatchingError\n[ 아래 _Body(Translation).txt 또는 Edit에서 해당 목차 부분부터 확인 >> ((({CurrentIndex['Index']}))) ]\n\n{TranslationBodyFilePath}\n\n{TranslationEditPath}")

    ## 수정된 TranslationIndex 저장
    # Dataframe 저장
    with open(ProjectDataFrameTranslationIndexDefinePath, 'r', encoding='utf-8') as IndexDataFrameJson:
        TranslationEditIndex = json.load(IndexDataFrameJson)
        TranslationEditIndex[1] = UpdatedTranslationIndex
    with open(ProjectDataFrameTranslationIndexDefinePath, 'w', encoding='utf-8') as IndexDataFrameJson:
        json.dump(TranslationEditIndex, IndexDataFrameJson, ensure_ascii = False, indent = 4)
    # Edit 저장
    with open(TranslationEditPath, 'r', encoding='utf-8') as TranslationEditJson:
        TranslationEditIndex = json.load(TranslationEditJson)
        TranslationEditIndex[BeforeProcess] = UpdatedTranslationIndex
    with open(TranslationEditPath, 'w', encoding='utf-8') as TranslationEditJson:
        json.dump(TranslationEditIndex, TranslationEditJson, ensure_ascii = False, indent = 4)

    ## Load2-3: SplitedTranslationBody 생성
    SplitedTranslationBody = []
    BodyId = 1
    AddQuotes = 0
    for i, (lineNum, IndexDic) in enumerate(IndexPositions):
        IndexId = IndexDic["IndexId"]
        IndexTag = IndexDic["IndexTag"]
        IndexText = IndexDic["Index"]
        
        # 다음 섹션의 시작 줄 번호 결정
        NextStartLine = len(BodyLines)
        if i < len(IndexPositions) - 1:
            NextStartLine = IndexPositions[i + 1][0]
        
        # 현재 섹션의 시작 줄 번호 (목차 줄은 제외)
        StartLine = lineNum + 1
        
        # 현재 섹션의 텍스트 추출
        SectionLines = BodyLines[StartLine:NextStartLine]
        SectionText = "\n".join(SectionLines)
        
        # 섹션이 MaxLength(2,000, 3,000, 4,000)자를 초과하는지 확인
        if len(SectionText) <= MaxLength:
            SplitedTranslationBody.append({"IndexId": IndexId, "IndexTag": IndexTag, "Index": IndexText, "BodyId": BodyId, "Body": SectionText, 'FinalEnding': '\n'})
            BodyId += 1
        else:
            # 섹션이 MaxLength(2,000, 3,000, 4,000)자를 초과하면 문장 단위로 추가 분할
            SubSectionsDic = SplitBySentence(TranslationBodyFilePath, projectName, IndexText, SectionText, MaxLength)
            SubSections = SubSectionsDic['SubSections']
            AddQuotes += SubSectionsDic['AdditionalQuotes']
            
            
            for SubText in SubSections:
                SplitedTranslationBody.append({"IndexId": IndexId, "IndexTag": IndexTag, "Index": IndexText, "BodyId": BodyId, "Body": SubText['CurrentSegment'], 'FinalEnding': SubText['FinalEnding']})
                BodyId += 1
    
    ## Load2-4: 분할 전/후 최종 글자수 일치 확인
    # 목차 줄들을 제외한 원본 텍스트
    OriginalLines = []
    for lineNum, BodyLine in enumerate(BodyLines):
        IsIndexLine = False
        for pos, idx in IndexPositions:
            if lineNum == pos:
                IsIndexLine = True
                break
        if not IsIndexLine:
            OriginalLines.append(BodyLine)
    
    OriginalText = "\n".join(OriginalLines)
    CleanOriginalText = re.sub(r'\s+', '', OriginalText).replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
    OriginalCount = len(CleanOriginalText)
    
    # 분할된 본문의 모든 문자 결합 후 공백 제거
    SplitedBodyText = ''.join(TranslationBodyDic["Body"] for TranslationBodyDic in SplitedTranslationBody)
    CleanSplitedBodyText = re.sub(r'\s+', '', SplitedBodyText).replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
    SplitCount = len(CleanSplitedBodyText)
    
    # 최종 글자수 일치 확인
    if (OriginalCount + AddQuotes) == SplitCount:
        return SplitedTranslationBody
    else:
        # 차이점 찾기: 문자 단위 비교
        MinLength = min(len(CleanOriginalText), len(CleanSplitedBodyText))
        DiffIndex = next((i for i, (c1, c2) in enumerate(zip(CleanOriginalText, CleanSplitedBodyText)) if c1 != c2), -1)
        if DiffIndex == -1 and len(CleanOriginalText) != len(CleanSplitedBodyText):
            DiffIndex = MinLength

        StartIdx = max(0, DiffIndex - 50)
        EndIdxOriginal = min(len(CleanOriginalText), DiffIndex + 50)
        EndIdxSplited = min(len(CleanSplitedBodyText), DiffIndex + 50)

        OriginalContext = CleanOriginalText[StartIdx:EndIdxOriginal]
        SplitedContext = CleanSplitedBodyText[StartIdx:EndIdxSplited]
        PositionMark = ' ' * (DiffIndex - StartIdx) + '^'

        ErrorMessage = (
            f"TranslationSplitBody 길이 불일치 오류: Project: {projectName} | Process: TranslationBodySplit | SplitBodyLengthError\n"
            f"분할 전후 텍스트 수가 다름 (분할전: {OriginalCount} != 분할후: {SplitCount})\n\n"
            f"차이점 발생 위치 (인덱스 {DiffIndex}):\n"
            f"분할전: {OriginalContext}\n"
            f"위치:   {PositionMark}\n"
            f"분할후: {SplitedContext}"
        )

        sys.exit(ErrorMessage)
        # sys.exit(f"TranslationSplitBody 길이 불일치 오류: Project: {projectName} | Process: TranslationBodySplit | SplitBodyLengthError\n[ 분할 전후 텍스트 수가 다름 (분할전: {OriginalCount} != 분할후: {SplitCount}) ]")

## Load3: MainLang, Translation 불러오기
def LoadTranslation(Translation, ProjectDataFrameTranslationIndexDefinePath):
    with open(ProjectDataFrameTranslationIndexDefinePath, 'r', encoding = 'utf-8') as TranslationIndexDefineJson:
        TranslationIndexDefine = json.load(TranslationIndexDefineJson)
    
    if Translation in ['auto', 'Auto']:
        Translation = TranslationIndexDefine[0]['Translation']
    elif Translation.lower() not in ['en', 'zh', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'pt', 'ru', 'ar', 'nl', 'sv', 'no', 'da', 'fi', 'pl', 'tr', 'el', 'cs', 'hu', 'ro', 'sk', 'uk', 'hi', 'id', 'ms', 'th', 'vi', 'he', 'bg', 'ca']:
        Translation = TranslationIndexDefine[0]['Translation']
        
    return Translation

##########################
##### 언어감지 관련 함수 #####
##########################
## Language Code 생성
def LanguageCodeGen(MainLang, Translation):
    def LanguageCode(Lang):
        # 언어 코드와 해당 언어명, 격식체 구분 여부를 딕셔너리로 정의
        LanguageDict = {
            "en": {"code": "English - English - 영어", "toneDistinction": "No"},
            "zh": {"code": "Chinese - 中文 - 중국어", "toneDistinction": "No"},
            "es": {"code": "Spanish - Español - 스페인어", "toneDistinction": "Yes"},
            "fr": {"code": "French - Français - 프랑스어", "toneDistinction": "Yes"},
            "de": {"code": "German - Deutsch - 독일어", "toneDistinction": "Yes"},
            "it": {"code": "Italian - Italiano - 이탈리아어", "toneDistinction": "Yes"},
            "ja": {"code": "Japanese - 日本語 - 일본어", "toneDistinction": "Yes"},
            "ko": {"code": "Korean - 한국어 - 한국어", "toneDistinction": "Yes"},
            "pt": {"code": "Portuguese - Português - 포르투갈어", "toneDistinction": "Yes"},
            "ru": {"code": "Russian - Русский - 러시아어", "toneDistinction": "Yes"},
            "ar": {"code": "Arabic - العربية - 아랍어", "toneDistinction": "No"},
            "nl": {"code": "Dutch - Nederlands - 네덜란드어", "toneDistinction": "Yes"},
            "sv": {"code": "Swedish - Svenska - 스웨덴어", "toneDistinction": "No"},
            "no": {"code": "Norwegian - Norsk - 노르웨이어", "toneDistinction": "No"},
            "da": {"code": "Danish - Dansk - 덴마크어", "toneDistinction": "No"},
            "fi": {"code": "Finnish - Suomi - 핀란드어", "toneDistinction": "Yes"},
            "pl": {"code": "Polish - Polski - 폴란드어", "toneDistinction": "Yes"},
            "tr": {"code": "Turkish - Türkçe - 터키어", "toneDistinction": "Yes"},
            "el": {"code": "Greek - Ελληνικά - 그리스어", "toneDistinction": "Yes"},
            "cs": {"code": "Czech - Čeština - 체코어", "toneDistinction": "Yes"},
            "hu": {"code": "Hungarian - Magyar - 헝가리어", "toneDistinction": "Yes"},
            "ro": {"code": "Romanian - Română - 루마니아어", "toneDistinction": "Yes"},
            "sk": {"code": "Slovak - Slovenčina - 슬로바키아어", "toneDistinction": "Yes"},
            "uk": {"code": "Ukrainian - Українська - 우크라이나어", "toneDistinction": "Yes"},
            "hi": {"code": "Hindi - हिन्दी - 힌디어", "toneDistinction": "Yes"},
            "id": {"code": "Indonesian - Bahasa Indonesia - 인도네시아어", "toneDistinction": "No"},
            "ms": {"code": "Malay - Bahasa Melayu - 말레이어", "toneDistinction": "No"},
            "th": {"code": "Thai - ไทย - 태국어", "toneDistinction": "Yes"},
            "vi": {"code": "Vietnamese - Tiếng Việt - 베트남어", "toneDistinction": "Yes"},
            "he": {"code": "Hebrew - עברית - 히브리어", "toneDistinction": "Yes"},
            "bg": {"code": "Bulgarian - Български - 불가리아어", "toneDistinction": "Yes"},
            "ca": {"code": "Catalan - Català - 카탈루냐어", "toneDistinction": "Yes"}
        }
        
        # 입력된 언어 코드를 소문자로 변환하여 처리
        LangCode = Lang.lower()
        
        # 딕셔너리에서 언어 정보 반환
        return LanguageDict.get(LangCode)
    
    # Main Language Code
    MainLangCode = LanguageCode(MainLang)["code"]
    
    # TTranslation Language Code
    TranslationLangCode = LanguageCode(Translation)["code"]
    
    # ToneDistinction
    ToneDistinction = LanguageCode(MainLang)["toneDistinction"]
    
    return MainLangCode, TranslationLangCode, ToneDistinction

## 언어 감지 함수
def LanguageDetection(Body, DetectionLength = 10):
    # 결과 재현성을 위해 시드 설정
    DetectorFactory.seed = 0
    if not Body or len(Body.strip()) == 0:
        return []
    
    DetectedLanguages = set()  # 중복 없이 저장하기 위해 set 사용
    
    # 1단계: 특수 문자셋 언어 감지 (명확한 패턴이 있는 언어)
    LanguagePatterns = {
        "ko": r'[가-힣]+',                     # 한국어
        "ja": r'[\u3040-\u309F\u30A0-\u30FF]+',  # 일본어 (히라가나, 가타카나)
        "zh": r'[\u4E00-\u9FFF]+',             # 중국어 (하지만 일본어 한자와 겹침)
        "ru": r'[А-Яа-я]+',                   # 러시아어
        "el": r'[Α-Ωα-ω]+',                   # 그리스어
        "ar": r'[\u0600-\u06FF]+',             # 아랍어
        "th": r'[\u0E00-\u0E7F]+',             # 태국어
        "he": r'[\u0590-\u05FF]+',             # 히브리어
        "hi": r'[\u0900-\u097F]+',             # 힌디어
    }
    
    # 특수 문자셋 기반 언어 감지
    HasJaSpecific = re.search(r'[\u3040-\u309F\u30A0-\u30FF]', Body)  # 히라가나, 가타카나 확인
    HasZhChars = re.search(r'[\u4E00-\u9FFF]', Body)  # 한자 확인
    
    # 일본어 특화 문자가 있으면 일본어로 판단
    if HasJaSpecific:
        DetectedLanguages.add("ja")
        
    # 한자가 있지만 일본어 특화 문자가 없으면 중국어로 판단
    elif HasZhChars:
        DetectedLanguages.add("zh")
    
    # 나머지 언어는 그대로 패턴 검사
    for lang_code, pattern in LanguagePatterns.items():
        if lang_code not in ["ja", "zh"] and re.search(pattern, Body):
            DetectedLanguages.add(lang_code)
    
    # 2단계: 라틴 알파벳 기반 언어 감지 (langdetect 라이브러리 활용)
    # 라틴 알파벳만 포함된 텍스트 길이가 충분한지 확인
    LatinBody = re.sub(r'[^a-zA-Z\s]', '', Body)
    
    # 영어 단어 패턴 확인 (짧은 단어도 포함)
    if re.search(r'\b[a-zA-Z]{2,}\b', Body):
        DetectedLanguages.add("en")
        
    if len(LatinBody.strip()) >= DetectionLength:  # 최소 10자 이상의 라틴 텍스트가 있는 경우에만 분석
        try:
            # 텍스트의 일부만 분석 (너무 긴 경우)
            SampleBody = Body[:3000] if len(Body) > 3000 else Body
            LangResults = detect_langs(SampleBody)
            
            # 확률이 높은 언어만 선택 (threshold: 0.3)
            for lang in LangResults:
                if lang.prob > 0.3:
                    DetectedLanguages.add(lang.lang)
        except:
            # langdetect가 실패할 경우, 간단한 휴리스틱 적용
            # 영어 단어 패턴 확인
            if re.search(r'\b[a-zA-Z]{2,}\b', Body):
                DetectedLanguages.add("en")
                
            # 특수 문자나 특정 조합을 기반으로 라틴 알파벳 기반 언어 추정
            LatinSpecialChars = {
                "fr": r'[àâçéèêëîïôùûüÿ]|Bonjour',  # 프랑스어
                "es": r'[áéíóúüñ¿¡]|Hola',           # 스페인어
                "de": r'[äöüß]|Guten|Hallo',         # 독일어
                "it": r'[àèéìíîòóù]|Ciao',           # 이탈리아어
                "pt": r'[áàâãçéêíóôõú]|Olá',         # 포르투갈어
            }
            
            for lang_code, pattern in LatinSpecialChars.items():
                if re.search(pattern, Body):
                    DetectedLanguages.add(lang_code)
    
    # 결과를 리스트로 변환
    return list(DetectedLanguages)

##############################
##### Input Response 생성 #####
##############################

## Process1: TranslationIndexDefine의 InputList
def TranslationIndexDefineInputList(projectName, UploadTranslationFilePath):
    IndexTranslation = LoadTranslationIndex(projectName, UploadTranslationFilePath)

    InputId = 1
    InputList = []
    Input = IndexTranslation
    
    InputDic = {"Id": InputId, "Input": Input}
    InputList.append(InputDic)
    
    return InputList

## Process2, 14: TranslationBodySummary의 InputList
def TranslationBodySummaryInputList(TranslationEditPath, BeforeProcess):
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)[BeforeProcess]
        
    InputId = 1
    InputList = []
    for i, TranslationEdit in enumerate(TranslationEditList):
        IndexId = TranslationEdit['IndexId']
        Index = TranslationEdit['Index']
        Body = TranslationEdit['Body']
        
        Input = f"[현재목차]\n{Index}\n\n[현재내용]\n{Body}\n\n"
        
        InputList.append({"Id": InputId, "IndexId": IndexId, "Index": Index, "Body": Body, "Input": Input})
        InputId += 1
    
    return InputList

## Process2, 14: TranslationBodySummary의 추가 Input
def TranslationBodySummaryAddInput(ProjectDataFrameTranslationBodySummaryPath, TranslationLangCode):
    if os.path.exists(ProjectDataFrameTranslationBodySummaryPath):
        with open(ProjectDataFrameTranslationBodySummaryPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
            BodySummary = json.load(TranslationDataFrame)[1][-1]
        AddInput = f"[언어]\n{TranslationLangCode}\n\n[직전요약]\n{BodySummary}\n\n\n"
    
    else:
        AddInput = f"[언어]\n{TranslationLangCode}\n\n[직전요약]\nNone\n\n\n"
    
    return AddInput

## Process3,4: WordListGen의 InputList
def WordListGenInputList(TranslationEditPath, MainLangCode, TranslationLangCode, BeforeProcess):
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)[BeforeProcess]
        
    InputId = 1
    InputList = []
    for i, TranslationEdit in enumerate(TranslationEditList):
        IndexId = TranslationEdit['IndexId']
        Body = TranslationEdit['Body']
        
        Input = f"[원문언어] {TranslationLangCode}\n[번역언어] {MainLangCode}\n[원문내용]\n{Body}\n\n"
        
        InputList.append({"Id": InputId, "IndexId": IndexId, "Input": Input})
        InputId += 1
        
    return InputList

## Process5: WordListPostprocessing의 InputList
def WordListPostprocessingInputList(TranslationEditPath, MainLangCode, TranslationLangCode, BeforeProcess1, BeforeProcess2, BeforeProcess3):
    ## OrganizedBodyList 함수
    def OrganizedBodyListGen(WordList, BodyList):
        # 1. 동일한 Word별로 모아 중복 Translation 제거
        OrganizedWordDict = {}

        for WordIDic in WordList:
            word = WordIDic['Word']
            translation = WordIDic['Translation']

            if word not in OrganizedWordDict:
                OrganizedWordDict[word] = []

            if translation not in OrganizedWordDict[word]:
                OrganizedWordDict[word].append(translation)

        # 딕셔너리를 리스트 형태로 변환
        OrganizedWordList = [{'Word': word, 'Translation': translations} 
                            for word, translations in OrganizedWordDict.items()]

        # 2. 각 Body에 포함된 단어 찾기
        OrganizedBodyList = []

        for BodyDic in BodyList:
            IndexId = BodyDic['IndexId']
            BodyId = BodyDic['BodyId']
            Body = BodyDic['Body']

            # 이 Body에 포함된 단어 찾기 및 등장 위치 기록
            WordPositions = []

            for wordDic in OrganizedWordList:
                word = wordDic['Word']

                # 단어가 문단에 포함되어 있는지 확인
                position = Body.find(word)
                if position != -1:
                    WordPositions.append({'Word': word, 'Translation': wordDic['Translation'], 'Position': position})

            # 등장 위치에 따라 정렬
            WordPositions.sort(key=lambda x: x['Position'])

            # Position 정보 제거 후 최종 리스트 생성
            IncludedWords = [{
                'Word': item['Word'],
                'Translation': item['Translation']
            } for item in WordPositions]

            # 포함된 단어가 있는 경우만 결과에 추가
            if IncludedWords:
                OrganizedBodyList.append({'IndexId': IndexId, 'BodyId': BodyId, 'Body': Body, 'OrganizedWordList': IncludedWords})

        return OrganizedBodyList
    
    ## BodyList, WordList 불러오기
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)
    BodyList = TranslationEditList[BeforeProcess1]
    WordList = TranslationEditList[BeforeProcess2] + TranslationEditList[BeforeProcess3]
    OrganizedBodyList = OrganizedBodyListGen(WordList, BodyList)
    
    # ## TranslationIndexDefineFrame 저장
    # with open('/yaas/OrganizedBodyList.json', 'w', encoding = 'utf-8') as DataFrameJson:
    #     json.dump(OrganizedBodyList, DataFrameJson, indent = 4, ensure_ascii = False)
    
    InputId = 1
    InputList = []
    for i, OrganizedDic in enumerate(OrganizedBodyList):
        IndexId = OrganizedDic['IndexId']
        Body = OrganizedDic['Body']
        WordsText = ''
        for j, WordDic in enumerate(OrganizedDic['OrganizedWordList']):
            Word = WordDic['Word']
            Translation = WordDic['Translation']
            WordsText += f"[번호] {j+1}\n[원문] {Word}\n[번역] {', '.join(Translation)}\n\n"
        
        Input = f"[원문언어] {TranslationLangCode}\n[번역언어] {MainLangCode}\n[원문내용]\n{Body}\n\n\n<단어장>\n{WordsText}\n"
        
        InputList.append({"Id": InputId, "IndexId": IndexId, "Input": Input, "InputLength": len(OrganizedDic['OrganizedWordList'])})
        InputId += 1
        
    return InputList

## Process6: IndexTranslation의 InputList
def IndexTranslationInputList(TranslationEditPath, BeforeProcess1, BeforeProcess2, BeforeProcess3):
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)
    TranslationIndexDefine = TranslationEditList[BeforeProcess1]
    TranslationBodySummary = TranslationEditList[BeforeProcess2]
    TranslationWordList = TranslationEditList[BeforeProcess3]
    
    ## 전체목차원문 생성
    IndexText = ''
    for i, TranslationIndex in enumerate(TranslationIndexDefine):
        IndexTag = TranslationIndex['IndexTag']
        Index = TranslationIndex['Index']
        IndexText += f"{IndexTag}: {Index}\n"
    
    ## InputList 생성
    InputId = 1
    InputList = []
    MaxTokenLength = 8000
    for i, TranslationIndex in enumerate(TranslationIndexDefine):
        IndexId = TranslationIndex['IndexId']
        IndexTag = TranslationIndex['IndexTag']
        Index = TranslationIndex['Index']
        BodySummary = ''
        for TranslationBody in TranslationBodySummary:
            # 현재 목차에 해당하는 본문 요약 찾기 (IndexId로 매칭, MaxTokenLength 초과 시 중단)
            if TranslationBody['IndexId'] == IndexId:
                AdditionalText = TranslationBody['BodySummary']
                CurrentTokens = len(BodySummary.split())
                AdditionalTokens = len(AdditionalText.split())
                if CurrentTokens + AdditionalTokens > MaxTokenLength:
                    RemainingTokens = MaxTokenLength - CurrentTokens
                    Tokens = AdditionalText.split()
                    # 허용된 토큰만 추가
                    BodySummary += " " + " ".join(Tokens[:RemainingTokens])
                    # 최대 토큰 길이에 도달하였으므로 반복 종료
                    break
                else:
                    BodySummary += " " + AdditionalText
        WordList = ''
        ExistWordList = []
        for TranslationWord in TranslationWordList:
            if TranslationWord['Word'].lower() not in ExistWordList and TranslationWord['IndexId'] == TranslationIndex['IndexId'] and TranslationWord["Processing"] != '삭제' and TranslationWord["Word"].lower() in Index.lower():
                WordList += f"{TranslationWord['Word']} -> {TranslationWord['Translation']}\n"
                ExistWordList.append(TranslationWord['Word'].lower())
        if WordList == '':
            WordList = 'None'
        
        Input = f"<현재목차정보>\n[현재목차원문]\n{Index}\n\n[원문본문내용요약]\n{BodySummary}\n\n[본문단어번역]\n{WordList}\n\n"
        
        InputList.append({"Id": InputId, "IndexId": IndexId, "IndexTag": IndexTag, "IndexText": IndexText, "Input": Input})
        InputId += 1
    
    return InputList

## Process6: IndexTranslation의 추가 Input
def IndexTranslationAddInput(ProjectDataFrameIndexTranslationPath, IndexText, MainLangCode, TranslationLangCode):
    if os.path.exists(ProjectDataFrameIndexTranslationPath):
        with open(ProjectDataFrameIndexTranslationPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
            IndexTranslation = json.load(TranslationDataFrame)[1][1:]
        IndexTranslationText = ''
        for IndexTranslationDic in IndexTranslation:
            IndexTranslationText += f"{IndexTranslationDic['IndexTag']}: {IndexTranslationDic['IndexTranslation']}\n"
        AddInput = f"[원문언어] {TranslationLangCode}\n[번역언어] {MainLangCode}\n\n[전체목차원문]\n{IndexText}\n\n[현재까지번역된목차]\n{IndexTranslationText}\n\n\n"
    
    else:
        AddInput = f"※ 첫번째 Title 번역은 도서에서 가장 중요함으로, 목차 내용의 전체를 포괄하며, 핵심적이면서도 현대의 사람들이 도서에 큰 관심을 보일 수 있도록 창의적이고 후킹이 강하도록 번역해주세요.\n\n[원문언어] {TranslationLangCode}\n[번역언어] {MainLangCode}\n\n[전체목차원문]\n{IndexText}\n\n[현재까지번역된목차]\nNone\n\n\n"

    return AddInput

## Process7: BodyTranslationPreprocessing의 InputList
def BodyTranslationPreprocessingInputList(TranslationEditPath, MainLangCode, TranslationLangCode, BeforeProcess1, BeforeProcess2, BeforeProcess3):
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)
    
    TranslationBodyList = TranslationEditList[BeforeProcess1]
    TranslationWordsList = TranslationEditList[BeforeProcess2]
    IndexTranslationList = TranslationEditList[BeforeProcess3]
    
    InputId = 1
    InputList = []
    for i, TranslationBodyDic in enumerate(TranslationBodyList):
        IndexId = TranslationBodyDic['IndexId']
        IndexTag = TranslationBodyDic['IndexTag']
        for IndexTranslationDic in IndexTranslationList:
            if IndexTranslationDic['IndexId'] == IndexId:
                Index = IndexTranslationDic['IndexTranslation']
        BodyId = TranslationBodyDic['BodyId']
        TranslationBody = TranslationBodyDic['Body']
        TranslationWords = []
        for TranslationWordDic in TranslationWordsList:
            if TranslationWordDic['BodyId'] == BodyId:
                TranslationWords.append(TranslationWordDic)
        
        # 단어를 길이 기준으로 정렬 (긴 단어 먼저 처리)
        TranslationWords.sort(key = lambda x: len(x['Word']), reverse=True)
        # 원본 텍스트 복사
        ProcessedInput = TranslationBody
        
        # 모든 단어를 고유한 마커로 대체
        MarkerMap = {}
        for i, WordDict in enumerate(TranslationWords):
            OriginalWord = WordDict['Word']
            Translation = WordDict['Translation']
            
            # 고유 마커 생성
            Marker = f"⒨⒜⒭⒦|{i}|"
            MarkerMap[Marker] = (OriginalWord, Translation)
            
            # 단어를 마커로 대체
            ProcessedInput = ProcessedInput.replace(OriginalWord, Marker)
        # 모든 마커의 위치 찾기
        MarkerPositions = []
        for Marker in MarkerMap:
            StartPos = 0
            while True:
                Pos = ProcessedInput.find(Marker, StartPos)
                if Pos == -1:
                    break
                MarkerPositions.append((Pos, Marker))
                StartPos = Pos + len(Marker)
        # 위치별로 정렬
        MarkerPositions.sort(key=lambda x: x[0])
        
        # 마커를 최종 형식으로 대체
        for Idx, (_, Marker) in enumerate(MarkerPositions, 1):
            OriginalWord, Translation = MarkerMap[Marker]
            Replacement = f"{{{Idx}: {OriginalWord}->{Translation}}}"
            ProcessedInput = ProcessedInput.replace(Marker, Replacement, 1)
        Input = f"[원문언어] {TranslationLangCode}\n[번역언어] {MainLangCode}\n[현재원문]\n{ProcessedInput}\n\n"
        
        # 처리된 입력을 InputList에 추가
        InputList.append({"Id": InputId, "IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "TranslationBody": ProcessedInput, "Input": Input})
        
        # 다음 반복을 위해 InputId 증가
        InputId += 1
    
    # with open('/yaas/InputList.json', 'w', encoding = 'utf-8') as DataFrameJson:
    #     json.dump(InputList, DataFrameJson, indent = 4, ensure_ascii = False)
        
    # 최종 InputList 반환
    return InputList

## Process8: BodyTranslation의 InputList
def BodyTranslationInputList(TranslationEditPath, BeforeProcess):
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)[BeforeProcess]
        
    InputId = 1
    InputList = []
    for i, TranslationEdit in enumerate(TranslationEditList):
        IndexId = TranslationEdit['IndexId']
        IndexTag = TranslationEdit['IndexTag']
        Index = TranslationEdit['Index']
        BodyId = TranslationEdit['BodyId']
        Body = TranslationEdit['Body']
        
        Input = f"<현재번역할내용>\n[현재번역세부목차]\n{IndexTag}: {Index}\n\n\n[*원문]\n{Body}\n\n"
        
        InputList.append({"Id": InputId, "IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "Input": Input})
        InputId += 1
    
    return InputList

## Process8: BodyTranslation의 추가 Input
def BodyTranslationAddInput(ProjectDataFrameBodyTranslationPath, ProjectDataFrameIndexTranslationPath, MainLangCode, TranslationLangCode, Tone):
    ## 전체 도서목차 생성
    with open(ProjectDataFrameIndexTranslationPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
        IndexTranslation = json.load(TranslationDataFrame)[1]
    ## 최상위 태그로 목차를 구성함으로써 매우 긴 목차를 줄이기 위함
    # 태그 우선순위 정의 (순서대로 높은 우선순위)
    PriorityIndexTags = ['Part', 'Chapter', 'Index']

    # 각 우선순위 태그에 대해 확인
    for indexTag in PriorityIndexTags:
        # 해당 태그가 존재하면 그것이 최상위 태그
        if any(item['IndexTag'] == indexTag for item in IndexTranslation):
            MainIndexTag = indexTag
            break
    else:  # for 루프가 break 없이 완료된 경우
        MainIndexTag = 'Index'
        
    IndexText = ''
    for IndexTranslationDic in IndexTranslation:
        if IndexTranslationDic['IndexTag'] in ['Title', MainIndexTag]:
            IndexText += f"{IndexTranslationDic['IndexTag']}: {IndexTranslationDic['IndexTranslation']}\n"
    
    ## <이전번역내용> 생성
    if os.path.exists(ProjectDataFrameBodyTranslationPath):
        with open(ProjectDataFrameBodyTranslationPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
            BodyTranslation = json.load(TranslationDataFrame)[1]
        ## Body번역이 1번 진행된 경우는 이전번역문을 1개만 제시
        if len(BodyTranslation) <= 2:
            BeforeBodyTranslation = BodyTranslation[-1]['Body']
        else:
            BeforeBodyTranslation = BodyTranslation[-2]['Body'] + '\n\n' + BodyTranslation[-1]['Body']
        
        AddInput = f"[원문언어] {TranslationLangCode}\n[번역언어] {MainLangCode}\n\n[도서전체목차]\n{IndexText}\n\n[이전번역문]\n{BeforeBodyTranslation}\n\n\n"
    else:
        if Tone == 'Auto':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전번역문이 없음"
        if Tone == 'Formal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전번역문이 없습니다. 완성 절차 및 방법에 따라서, *원문의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 번역을 시작해주세요."
        elif Tone == 'Normal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전번역문이 없다. 완성 절차 및 방법에 따라서, *원문의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 번역을 시작하세요."
        elif Tone == 'Informal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전번역문이 없어. 완성 절차 및 방법에 따라서, *원문의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 번역을 시작해줘."
        AddInput = f"[원문언어] {TranslationLangCode}\n[번역언어] {MainLangCode}\n\n[도서전체목차]\n{IndexText}\n\n[이전번역문]\n{StartBodyTranslation}\n\n\n"
        
    return AddInput

## Process8: BodyToneEditing의 Input(BodyTranslation용도)
def BodyToneEditingInput(Tone, ToneCode, ProjectDataFrameBodyTranslationPath, BodyTranslationResponse):
    CurrentBodyTranslation = re.sub(r'\{[^{}]*->([^{}]*)\}', r'\1', BodyTranslationResponse['번역문']).replace('{', '').replace('}', '')
    ## 이전번역문과 현재번역문 비교 Input 생성
    if os.path.exists(ProjectDataFrameBodyTranslationPath):
        with open(ProjectDataFrameBodyTranslationPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
            BodyTranslation = json.load(TranslationDataFrame)[1]
        BeforeBodyTranslation = BodyTranslation[-1]['Body']
        
        ## ToneEditInput 생성
        ToneEditInput = f"[이전도서어조]\n{ToneCode}\n\n[이전도서내용]\n{BeforeBodyTranslation}\n\n\n<현재도서내용>\n{CurrentBodyTranslation}\n\n"
    else:
        ## ToneEditInput 생성
        if Tone == 'Auto':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전편집내용이 없음"
        if Tone == 'Formal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전편집내용이 없습니다. 완성 절차 및 방법에 따라서, 현재도서내용의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성을 시작해주세요."
        elif Tone == 'Normal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전편집내용이 없다. 완성 절차 및 방법에 따라서, 현재도서내용의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성을 시작하세요."
        elif Tone == 'Informal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전편집내용이 없어. 완성 절차 및 방법에 따라서, 현재도서내용의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성을 시작하세요."
        ToneEditInput = f"[이전도서어조]\n{ToneCode}\n\n[이전도서내용]\n{StartBodyTranslation}\n\n\n<현재도서내용>\n{CurrentBodyTranslation}\n\n"
    
    return ToneEditInput

## Process8: BodyTranslationCheck의 Input
def BodyTranslationCheckAndBodyToneEditingInput(ProjectName, Process, ToneCode, InputCount, TotalInputCount, ProjectDataFrameBodyTranslationPath, BodyTranslationResponse):
    ## 이전번역문과 현재번역문 비교 Input 생성
    if os.path.exists(ProjectDataFrameBodyTranslationPath):
        with open(ProjectDataFrameBodyTranslationPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
            BodyTranslation = json.load(TranslationDataFrame)[1]
        BeforeBodyTranslation = BodyTranslation[-1]['Body']
        if Process == 'BodyTranslation':
            CurrentBodyTranslation = re.sub(r'\{[^{}]*->([^{}]*)\}', r'\1', BodyTranslationResponse['번역문']).replace('{', '').replace('}', '')
        else:
            CurrentBodyTranslation = re.sub(r'\{[^{}]*->([^{}]*)\}', r'\1', BodyTranslationResponse['내용']).replace('{', '').replace('}', '')
        
        ## CheckInput 생성
        CheckInput = f"{BeforeBodyTranslation}\n\n\n<현재도서내용>\n{CurrentBodyTranslation}\n\n"
        Index = max(-len(BodyTranslation), -3)
        BeforeCheck = BodyTranslation[Index]['Tone']
        ## ToneEditInput 생성
        ToneEditInput = f"[이전도서어조]\n{ToneCode}\n\n[이전도서내용]\n{BeforeBodyTranslation}\n\n\n<현재도서내용>\n{CurrentBodyTranslation}\n\n"
        ## LanguageEditInput 생성
                
        LangCheck = False
        if Process in ['TranslationEditing', 'TranslationRefinement', 'TranslationKinfolkStyleRefinement']:
            BeforeBodyLang = sorted(LanguageDetection(BeforeBodyTranslation))
            CurrentBodyLang = sorted(LanguageDetection(CurrentBodyTranslation))
            
            ## 예외처리(한국어 글에 (중국어 설명)이 있는 경우)
            if sorted(BeforeBodyLang) in [sorted(['ko' 'zh']), sorted(['ko', 'en'])]:
                BeforeBodyLang = ['ko']
            if sorted(CurrentBodyLang) in [sorted(['ko' 'zh']), sorted(['ko', 'en'])]:
                CurrentBodyLang = ['ko']
            
            ## 이전번역문과 현재번역문 언어 동일성 확인
            if set(BeforeBodyLang) == set(CurrentBodyLang):
                LangCheck = True
                print(f"Project: {ProjectName} | Process: {Process} {InputCount}/{TotalInputCount} | "
                    f"{BeforeBodyLang} == {CurrentBodyLang}, 동일 언어 체크 완료")
            else:
                LangCheck = False
                print(f"Project: {ProjectName} | Process: {Process} {InputCount}/{TotalInputCount} | "
                    f"{BeforeBodyLang} =! {CurrentBodyLang}, 동일 언어 체크 재시도")
        
    return LangCheck, CheckInput, ToneEditInput, BeforeCheck

## Process8: BodyLanguageEditing의 Input
def BodyLanguageEditingInput(ProjectName, Process, MainLang, MainLangCode, InputCount, TotalInputCount, ProjectDataFrameBodyTranslationPath, BodyTranslationResponse):
    def FindMixedLanguageWords(CurrentBodyTranslation):
        def GetScript(Char):
            if not Char.isalpha():
                return 'NonAlpha'
                
            try:
                Name = unicodedata.name(Char)
                
                # 스크립트별 분류
                if 'LATIN' in Name:
                    return 'Latin'  # 영어, 로마자 등
                elif 'HANGUL' in Name:
                    return 'Hangul'  # 한글
                elif any(x in Name for x in ['CJK', 'IDEOGRAPH']):
                    return 'CJK'  # 중국어, 일본 한자 등
                elif 'HIRAGANA' in Name or 'KATAKANA' in Name:
                    return 'Japanese'  # 일본어
                elif 'THAI' in Name:
                    return 'Thai'  # 태국어
                elif 'ARABIC' in Name:
                    return 'Arabic'  # 아랍어
                elif 'CYRILLIC' in Name:
                    return 'Cyrillic'  # 러시아어 등
                elif 'DEVANAGARI' in Name:
                    return 'Devanagari'  # 힌디어 등
                elif 'GREEK' in Name:
                    return 'Greek'  # 그리스어
                elif 'HEBREW' in Name:
                    return 'Hebrew'  # 히브리어
                else:
                    return 'Other'
            except ValueError:
                return 'Unknown'

        # 언어별 정상적인 스크립트 조합 정의(일본어는 한자 및 히라가나/가타카나 조합 가능)
        def IsValidScriptCombination(UniqueScripts):
            # 일본어 특수 케이스: 히라가나/가타카나 + 한자 조합은 정상적인 일본어
            if UniqueScripts == {'Japanese', 'CJK'} or UniqueScripts == {'Japanese'} or UniqueScripts == {'CJK'}:
                return True
            # 단일 스크립트이면 항상 유효함
            elif len(UniqueScripts) <= 1:
                return True
            # 다른 모든 스크립트 조합은 혼합 언어로 간주
            return False

        # 텍스트를 단어로 분리
        words = re.findall(r'\b\w+\b', CurrentBodyTranslation)
        MixedLanguageWords = []
        
        for word in words:
            # 각 단어의 문자 스크립트 확인
            CharScripts = []
            for char in word:
                if not char.isalpha():
                    continue
                script = GetScript(char)
                if script != 'NonAlpha' and script != 'Unknown':
                    CharScripts.append(script)
            
            # 단어에 여러 언어가 포함되어 있는지 확인
            UniqueScripts = set(CharScripts)
            if not IsValidScriptCombination(UniqueScripts) and len(UniqueScripts) > 1:
                MixedLanguageWords.append(word)
        
        return MixedLanguageWords, len(MixedLanguageWords) == 0
    
    ## 이전번역문과 현재번역문 비교 Input 생성
    FirstLangCheck = False
    CurrentBodyTranslation = re.sub(r'\{[^{}]*->([^{}]*)\}', r'\1', BodyTranslationResponse['번역문']).replace('{', '').replace('}', '')
    CurrentBodyLang = sorted(LanguageDetection(CurrentBodyTranslation, DetectionLength = 3))
    
    ## DataFrameBodyTranslationPath가 존재하는 경우
    if os.path.exists(ProjectDataFrameBodyTranslationPath):
        with open(ProjectDataFrameBodyTranslationPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
            BodyTranslation = json.load(TranslationDataFrame)[1]
        BeforeBodyTranslation = BodyTranslation[-1]['Body']

        ## LanguageEditInput 생성
        LanguageEditInput = f"{MainLangCode}\n\n<이전도서내용>\n{BeforeBodyTranslation}\n\n\n<현재도서내용>\n{CurrentBodyTranslation}\n\n"
        
        ## 이전번역문과 현재번역문 언어 동일성 체크
        if CurrentBodyLang == [MainLang.lower()]:
            FirstLangCheck = True
        if not FirstLangCheck:
            print(f"Project: {ProjectName} | Process: {Process} {InputCount}/{TotalInputCount} | "
                    f"CurrentBodyLang: {CurrentBodyLang} != MainLang: [{MainLang.lower()}] | BodyLanguageEditing 시작")
            
    else:
        ## LanguageEditInput 생성
        LanguageEditInput = f"{MainLangCode}\n\n<이전도서내용>\n현재 책의 가장 앞부분이라서 이전도서내용이 없음\n\n\n<현재도서내용>\n{CurrentBodyTranslation}\n\n"
        
        ## 이전번역문과 현재번역문 언어 동일성 체크
        if CurrentBodyLang == [MainLang.lower()]:
            FirstLangCheck = True
        if not FirstLangCheck:
            print(f"Project: {ProjectName} | Process: {Process} {InputCount}/{TotalInputCount} | CurrentBodyLang: {CurrentBodyLang} != MainLang: [{MainLang.lower()}] | BodyLanguageEditing 시작")
    
    ## 이전번역문과 현재번역문 비교 Input 생성
    MixedWords, SecondLangCheck = FindMixedLanguageWords(CurrentBodyTranslation)
    if not SecondLangCheck:
        # 최대 5개 단어까지만 출력 
        examples = ", ".join(MixedWords[:5])
        if len(MixedWords) > 5:
            examples += f" 외 {len(MixedWords)-5}개"
            
        print(f"Project: {ProjectName} | Process: {Process} {InputCount}/{TotalInputCount} | "
            f"OneLanguageWordCheck: 번역문에 다국어 혼합 단어 발견 (({examples})) | BodyLanguageEditing 시작")
        
    FinalLangCheck = FirstLangCheck and SecondLangCheck

    return FinalLangCheck, LanguageEditInput, CurrentBodyLang

## Process9: TranslationEditing의 InputList
def TranslationEditingInputList(TranslationEditPath, BeforeProcess1, BeforeProcess2):
    ## BracketedBodyGen 함수
    def BracketedBodyGen(OriginalBody, TranslationBody):
        # OriginalBody에서 {원문->번역어} 형태의 패턴 추출
        TranslationPairs = re.findall(r'\{(.*?)->(.*?)\}', OriginalBody)
        
        # 모든 가능한 괄호 구간을 리스트로 생성
        intervals = []
        for OriginalWord, TranslatedWord in TranslationPairs:
            for match in re.finditer(re.escape(TranslatedWord), TranslationBody):
                start, end = match.span()
                intervals.append((start, end, TranslatedWord))
        
        # 길이가 긴 순서대로 (길이가 같으면 위치가 앞에 있는 순서대로) 정렬
        intervals.sort(key=lambda x: (-(x[1] - x[0]), x[0]))
        
        # 이미 괄호 처리된 위치를 추적하기 위한 배열
        n = len(TranslationBody)
        is_bracketed = [False] * n
        
        # 겹치지 않는 구간 선택하기
        selected_intervals = []
        for start, end, word in intervals:
            # 이 구간이 이미 괄호 처리된 부분과 겹치는지 확인
            if any(is_bracketed[i] for i in range(start, end)):
                continue
            
            # 이 구간 선택
            selected_intervals.append((start, end))
            
            # 해당 위치를 괄호 처리됨으로 표시
            for i in range(start, end):
                is_bracketed[i] = True
        
        # 선택된 구간을 시작 위치 기준으로 역순 정렬
        selected_intervals.sort(reverse=True)
        
        # 문자열 끝에서부터 시작 방향으로 괄호 추가
        TranslationBodyResult = TranslationBody
        for start, end in selected_intervals:
            TranslationBodyResult = TranslationBodyResult[:start] + '{' + TranslationBodyResult[start:end] + '}' + TranslationBodyResult[end:]
        
        ## 잘못 매칭된 조사의 후처리
        KoParticle = ['은', '는', '이', '가', '을', '를', '의', '에', '와', '과', '로']
        for Particle in KoParticle:
            TranslationBodyResult = TranslationBodyResult.replace('{' + Particle + '}', Particle)
        
        return TranslationBodyResult
    
    ## BracketedBody {단어}의 {n 단어}로 숫자 부여 함수
    def NumberBracedWords(BracketedBody):
        counter = 0  # 번호를 위한 변수
        # 매칭된 그룹을 순서대로 대체하는 함수
        def replacer(match):
            nonlocal counter
            counter += 1
            # 매칭된 단어(match.group(1)) 앞에 번호를 추가합니다.
            return "{" + str(counter) + " " + match.group(1) + "}"
        # 정규표현식을 사용하여 {} 내부의 내용을 찾아 replacer 함수로 대체
        return re.sub(r'\{([^{}]+)\}', replacer, BracketedBody)
    
    
    ## BodyTranslationPreprocessingList, BodyTranslationList 불러오기
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)
    
    BodyTranslationPreprocessingList = TranslationEditList[BeforeProcess1]
    BodyTranslationList = TranslationEditList[BeforeProcess2]
        
    InputId = 1
    InputList = []
    for i, BodyTranslation in enumerate(BodyTranslationList):
        IndexId = BodyTranslation['IndexId']
        IndexTag = BodyTranslation['IndexTag']
        Index = BodyTranslation['Index']
        BodyId = BodyTranslation['BodyId']
        TranslationBody = BodyTranslation['Body']
        for BodyTranslationPreprocessing in BodyTranslationPreprocessingList:
            if BodyTranslationPreprocessing['BodyId'] == BodyId:
                OriginalBody = BodyTranslationPreprocessing['Body']
                BracketedBody = BracketedBodyGen(OriginalBody, TranslationBody)
                BracketedBody = NumberBracedWords(BracketedBody)
        
        InputList.append({"Id": InputId, "IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "BracketedBody": BracketedBody})
        InputId += 1
    
    return InputList

## Process9: BodyTranslationWordCheck의 후처리
def WordBracketCheckInput(IndexTag, Index, BracketedBody, BodyTranslationWordCheckResponse):
    for RemoveBracket in BodyTranslationWordCheckResponse:
        RemoveBracketWord = "{" + f"{RemoveBracket['번호']} {RemoveBracket['단어']}" + "}"
        Word = RemoveBracket['단어']
        BracketedBody = BracketedBody.replace(RemoveBracketWord, Word)
        # print(f"{RemoveBracketWord} -> Word")
    
    WordCheckBracketedBody = re.sub(r'\{\d+\s+([^{}]+)\}', r'{\1}', BracketedBody)
    
    CheckInput = f"<현재편집할내용>\n[편집할내용의목차]\n{IndexTag}: {Index}\n\n\n[*편집할내용]\n{WordCheckBracketedBody}\n\n"

    return CheckInput

## Process9: BodyTranslationKinfolkStyleWordCheck의 후처리
def WordBracketCheckKinfolkStyleInput(BracketedBody, BodyTranslationKinfolkStyleWordCheckResponse):
    for RemoveBracket in BodyTranslationKinfolkStyleWordCheckResponse:
        RemoveBracketWord = "{" + f"{RemoveBracket['번호']} {RemoveBracket['단어']}" + "}"
        Word = RemoveBracket['단어']
        BracketedBody = BracketedBody.replace(RemoveBracketWord, Word)
        # print(f"{RemoveBracketWord} -> Word")
    
    WordCheckBracketedBody = re.sub(r'\{\d+\s+([^{}]+)\}', r'{\1}', BracketedBody)
    
    CheckInput = f"<**편집내용-편집대상>\n{WordCheckBracketedBody}\n\n"

    return CheckInput

## Process9: TranslationEditing의 추가 Input
def TranslationEditingAddInput(ProjectDataFrameTranslationEditingPath, ProjectDataFrameIndexTranslationPath, Tone):
    ## 전체 도서목차 생성
    with open(ProjectDataFrameIndexTranslationPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
        IndexTranslation = json.load(TranslationDataFrame)[1]
    ## 최상위 태그로 목차를 구성함으로써 매우 긴 목차를 줄이기 위함
    # 태그 우선순위 정의 (순서대로 높은 우선순위)
    PriorityIndexTags = ['Part', 'Chapter', 'Index']

    # 각 우선순위 태그에 대해 확인
    for indexTag in PriorityIndexTags:
        # 해당 태그가 존재하면 그것이 최상위 태그
        if any(item['IndexTag'] == indexTag for item in IndexTranslation):
            MainIndexTag = indexTag
            break
    else:  # for 루프가 break 없이 완료된 경우
        MainIndexTag = 'Index'
        
    IndexText = ''
    for IndexTranslationDic in IndexTranslation:
        if IndexTranslationDic['IndexTag'] in ['Title', MainIndexTag]:
            IndexText += f"{IndexTranslationDic['IndexTag']}: {IndexTranslationDic['IndexTranslation']}\n"
    
    ## <현재편집할내용> 생성
    if os.path.exists(ProjectDataFrameTranslationEditingPath):
        with open(ProjectDataFrameTranslationEditingPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
            TranslationEditing = json.load(TranslationDataFrame)[1]
        ## Body번역이 1번 진행된 경우는 이전번역문을 1개만 제시
        if len(TranslationEditing) <= 2:
            BeforeTranslationEditing = TranslationEditing[-1]['Body']
        else:
            BeforeTranslationEditing = TranslationEditing[-2]['Body'] + '\n\n' + TranslationEditing[-1]['Body']
        
        AddInput = f"[도서전체목차]\n{IndexText}\n\n[이전편집내용]\n{BeforeTranslationEditing}\n\n\n"
    else:
        if Tone == 'Auto':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전편집내용이 없음"
        if Tone == 'Formal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전편집내용이 없습니다. 완성 절차 및 방법에 따라서, *편집할내용의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 편집을 시작해주세요."
        elif Tone == 'Normal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전편집내용이 없다. 완성 절차 및 방법에 따라서, *편집할내용의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 편집을 시작하세요."
        elif Tone == 'Informal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전편집내용이 없어. 완성 절차 및 방법에 따라서, *편집할내용의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 편집을 시작하세요."
        AddInput = f"[도서전체목차]\n{IndexText}\n\n[이전편집내용]\n{StartBodyTranslation}\n\n\n"
        
    return AddInput

## Process9: TranslationKinfolkStyleRefinement의 추가 Input
def TranslationKinfolkStyleRefinementAddInput(ProjectDataFrameTranslationKinfolkStyleRefinementPath, Tone):   
    ## <현재편집할내용> 생성
    if os.path.exists(ProjectDataFrameTranslationKinfolkStyleRefinementPath):
        with open(ProjectDataFrameTranslationKinfolkStyleRefinementPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
            TranslationKinfolkStyleRefinement = json.load(TranslationDataFrame)[1]
        ## Body번역이 1번 진행된 경우는 이전번역문을 1개만 제시
        if len(TranslationKinfolkStyleRefinement) <= 2:
            BeforeTranslationKinfolkStyleRefinement = TranslationKinfolkStyleRefinement[-1]['Body']
        else:
            BeforeTranslationKinfolkStyleRefinement = TranslationKinfolkStyleRefinement[-2]['Body'] + '\n\n' + TranslationKinfolkStyleRefinement[-1]['Body']
        
        AddInput = f"\n{BeforeTranslationKinfolkStyleRefinement}\n\n\n"
    else:
        if Tone == 'Auto':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 직전에 편집된 글이 없음"
        if Tone == 'Formal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 직전에 편집된 글이 없습니다. 완성 절차 및 방법에 따라서, **편집내용-편집대상의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 편집을 시작해주세요."
        elif Tone == 'Normal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 직전에 편집된 글이 없다. 완성 절차 및 방법에 따라서, **편집내용-편집대상의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 편집을 시작하세요."
        elif Tone == 'Informal':
            StartBodyTranslation = "현재 책의 가장 앞부분이라서 이전번역문이 없어. 완성 절차 및 방법에 따라서, **편집내용-편집대상의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 편집을 시작해줘."
        AddInput = f"\n{StartBodyTranslation}\n\n\n"
        
    return AddInput

## Process10: TranslationProofreading의 InputList
def TranslationProofreadingInputList(TranslationEditPath, BeforeProcess):
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)[BeforeProcess]
        
    InputId = 1
    InputList = []
    
    for i, TranslationEdit in enumerate(TranslationEditList):
        IndexId = TranslationEdit['IndexId']
        IndexTag = TranslationEdit['IndexTag']
        Index = TranslationEdit['Index']
        BodyId = TranslationEdit['BodyId']
        Body = TranslationEdit['Body']
        
        # Body의 길이가 1500자 이상일 경우만 나누기
        if len(Body) >= 1500:
            # Body를 문장 단위로 나눔 (정규 표현식으로 문장 구분)
            sentences = re.split(r'(?<=\.|\!|\?)\s+', Body)  # 문장 끝에 마침표, 물음표, 느낌표 이후 공백 기준으로 나눔
            HalfIndex = len(sentences) // 2  # 절반 위치
            
            # Body를 문장의 끝에서 나누기
            FirstHalfBody = ' '.join(sentences[:HalfIndex]).strip()  # 절반 전까지, 앞뒤 공백 제거
            SecondHalfBody = ' '.join(sentences[HalfIndex:]).strip()  # 절반 후부터, 앞뒤 공백 제거
            
            # Body를 절반으로 나누고 InputList에 추가
            Input = f"\n<**작업: 교정할도서내용>\n{FirstHalfBody}\n\n"
            InputList.append({"Id": InputId, "IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "Body": FirstHalfBody, "Input": Input})
            
            Input = f"\n<**작업: 교정할도서내용>\n{SecondHalfBody}\n\n"
            InputList.append({"Id": InputId + 1, "IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "Body": SecondHalfBody, "Input": Input})
            
            InputId += 2  # 두 번 추가되므로 InputId 두 개 증가
        else:
            # Body가 1500자 미만일 경우 그대로 추가
            Input = f"\n<**작업: 교정할도서내용>\n{Body}\n\n"
            InputList.append({"Id": InputId, "IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "Body": Body, "Input": Input})
            InputId += 1
            
        InputListLength = BodyId

    return InputList, InputListLength

## Process10: TranslationProofreading의 추가 Input
def TranslationProofreadingAddInput(ProjectDataFrameTranslationProofreadingPath):
    if os.path.exists(ProjectDataFrameTranslationProofreadingPath):
        with open(ProjectDataFrameTranslationProofreadingPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
            TranslationProofreading = json.load(TranslationDataFrame)[1]
        AddInput = f"{TranslationProofreading[-1]['Body']}\n\n\n"
    else:
        AddInput = f"\nNone\n\n"
        
    return AddInput

## Process11: TranslationDialogueEditing의 InputList
def TranslationDialogueAnalysisInputList(projectName, Process, ProjectDataFrameTranslationProofreadingPath, TranslationEditPath, BeforeProcess):
    def CountDialogues(Pattern, Body):
        # 텍스트에서 대화문 패턴 찾기
        DialogueMatches = re.findall(Pattern, Body)
        return len(DialogueMatches)
    
    def MarkDialogues(Pattern, Body):
        # 대화문이 없으면 빈 문자열 반환
        if not re.search(Pattern, Body):
            return ''
        
        # 모든 대화문 위치 찾기
        DialogueMatches = list(re.finditer(Pattern, Body))

        # 결과를 저장할 리스트
        DialogueSegments = []
        DialogueCounter = 1
        
        # 연속된 대화 그룹 식별
        i = 0
        while i < len(DialogueMatches):
            # 현재 대화 위치
            CurrentMatch = DialogueMatches[i]
            StartPosition = CurrentMatch.start()
            EndPosition = CurrentMatch.end()
            
            # 현재 대화 그룹의 마지막 위치
            GroupEndPosition = EndPosition
            
            # 대화 그룹 및 원본 텍스트 범위 저장
            GroupDialogues = []
            OriginalDialogueText = Body[StartPosition:EndPosition]
            
            # 첫 번째 대화 추가
            DialogueText = CurrentMatch.group(2) if CurrentMatch.group(2) is not None else CurrentMatch.group(3)
            GroupDialogues.append((DialogueCounter, DialogueText, OriginalDialogueText))
            DialogueCounter += 1
            
            # 인접한 대화 찾기 (50자 이내)
            j = i + 1
            while j < len(DialogueMatches) and DialogueMatches[j].start() - GroupEndPosition < 50:
                NextMatch = DialogueMatches[j]
                NextDialogue = NextMatch.group(2) if NextMatch.group(2) is not None else NextMatch.group(3)
                NextOriginal = Body[DialogueMatches[j].start():DialogueMatches[j].end()]
                
                # 대화 사이 텍스트 보존
                BetweenText = Body[GroupEndPosition:DialogueMatches[j].start()]
                OriginalDialogueText += BetweenText + NextOriginal
                
                # 대화 정보 저장
                GroupDialogues.append((DialogueCounter, NextDialogue, NextOriginal))
                DialogueCounter += 1
                
                # 그룹 끝 위치 업데이트
                GroupEndPosition = DialogueMatches[j].end()
                j += 1
            
            # 대화 그룹 전체 텍스트 (원본)
            DialogueBlock = Body[StartPosition:GroupEndPosition]
            
            # 앞쪽 텍스트
            TextBefore = Body[:StartPosition].strip()
            # 뒤쪽 텍스트
            TextAfter = Body[GroupEndPosition:].strip()
            
            # 앞쪽 최대 2문장 추출 (마침표, 느낌표, 물음표, 줄바꿈으로 구분)
            SentencesBefore = re.split(r'(?<=[.!?])\s+|\n+', TextBefore)
            SentencesBefore = [s.strip() for s in SentencesBefore if s.strip()]
            
            if len(SentencesBefore) > 2:
                ContextBefore = ['...'] + SentencesBefore[-2:]
            else:
                ContextBefore = SentencesBefore
            
            # 뒤쪽 최대 2문장 추출 (마침표, 느낌표, 물음표, 줄바꿈으로 구분)
            SentencesAfter = re.split(r'(?<=[.!?])\s+|\n+', TextAfter)
            SentencesAfter = [s.strip() for s in SentencesAfter if s.strip()]
            
            SentencesAfter = [s.strip() for s in SentencesAfter if s.strip()]
            
            if len(SentencesAfter) > 2:
                ContextAfter = SentencesAfter[:2] + ['...']
            else:
                ContextAfter = SentencesAfter
            
            # 대화문 번호 매기기 및 마킹
            MarkedBlock = DialogueBlock
            for Counter, Dialog, Original in GroupDialogues:
                # 원본 대화문을 마킹된 형식으로 교체
                Dialog = Dialog.replace('\n', " ")
                MarkedBlock = MarkedBlock.replace(Original, f"{{{Counter} 대화: {Dialog}}}", 1)
            
            # 최종 결과 조합
            Result = ' '.join(ContextBefore) + ' ' + MarkedBlock + ' ' + ' '.join(ContextAfter)
            Result = Result.strip()
            
            DialogueSegments.append(Result)
            
            # 다음 그룹으로 이동
            i = j
        
        MarkBody = ' '.join(DialogueSegments)
        MarkBody = MarkBody.replace('... ...', '...')
        
        return MarkBody
    
    # 새로 추가된 함수: 원본 텍스트를 유지하면서 대화문만 마킹
    def MarkDialoguesPreserveText(Pattern, Body):
        # 대화문이 없으면 원본 텍스트 그대로 반환
        if not re.search(Pattern, Body):
            return Body
        
        # 모든 대화문 위치 찾기
        DialogueMatches = list(re.finditer(Pattern, Body))
        
        # 원본 텍스트 복사
        OrginMarkBody = Body
        
        # 텍스트 변경에 따른 오프셋 추적
        offset = 0
        
        # 각 대화문 처리
        for i, Match in enumerate(DialogueMatches, 1):
            # 원본 위치 및 텍스트 가져오기 (오프셋 적용)
            start = Match.start() + offset
            end = Match.end() + offset
            original = OrginMarkBody[start:end]
            
            # 대화문 텍스트 추출
            DialogueText = Match.group(2) if Match.group(2) is not None else Match.group(3)
            
            # 마킹된 버전 생성
            DialogueText = DialogueText.replace("\n", " ")
            marked = f"{{{i} 대화: {DialogueText}}}"
            
            # 텍스트 교체
            OrginMarkBody = OrginMarkBody[:start] + marked + OrginMarkBody[end:]
            
            # 길이 변화에 따른 오프셋 업데이트
            offset += len(marked) - len(original)
        
        return OrginMarkBody
    
    ## 대화문 마킹 함수
    Pattern = r'("([^"]+)"|"([^"]+)")'
    ## 전체 도서내용에 대화문 마킹 생성
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)[BeforeProcess]
    InputId = 1
    InputList = []
    for TranslationEdit in TranslationEditList:
        IndexId = TranslationEdit['IndexId']
        IndexTag = TranslationEdit['IndexTag']
        Index = TranslationEdit['Index']
        BodyId = TranslationEdit['BodyId']
        Body = TranslationEdit['Body'].replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
        if Body.count('"') % 2 != 0:
            QuoteChar = '"'
            ErrorMessage = f"Project: {projectName} | Process: {Process}-InputList | 오류: (('BodyId': {BodyId})) 의 문단에서 '{QuoteChar}' 개수가 홀수 (({Body.count(QuoteChar)})) 개 입니다. 아래 경로 > {BeforeProcess} > 'BodyId': {BodyId}의 'Body'를 확인 후 '{QuoteChar}'를 추가/삭제하여 수정해주세요.\n{ProjectDataFrameTranslationProofreadingPath}"
            sys.exit(ErrorMessage)
        # 해당 항목의 대화문 개수 카운트
        DialogueCount = CountDialogues(Pattern, Body)
        # 대화문 마킹 처리
        MarkBody = MarkDialogues(Pattern, Body)
        MarkBody = MarkBody.replace('... ...', '...')
        # 원본 텍스트를 유지하면서 대화문만 마킹 처리
        OrginMarkBody = MarkDialoguesPreserveText(Pattern, Body)
        Input = f"<**작업: 대화중심편집내용>\n{OrginMarkBody}\n\n"
        InputList.append({"Id": InputId, "IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "Body": OrginMarkBody, "MarkBody": MarkBody, "Input": Input, "DialogueCount": DialogueCount})
        InputId += 1
        
    return InputList

## Process11: TranslationDialogueAnalysis의 추가 Input
def TranslationDialogueAnalysisAddInput(ProjectDataFrameTranslationDialogueAnalysisPath):
    if os.path.exists(ProjectDataFrameTranslationDialogueAnalysisPath):
        with open(ProjectDataFrameTranslationDialogueAnalysisPath, 'r', encoding='utf-8') as TranslationDataFrame:
            TranslationDialogueSet = json.load(TranslationDataFrame)
            TranslationDialogue = TranslationDialogueSet[1]
            
            ## <미리찾은인물> 추가 Input 생성
            BookCharacterText = ''
            BookCharacterList = TranslationDialogueSet[2]
            for BookCharacter in BookCharacterList:
                CharacterId = BookCharacter['CharacterId']
                if CharacterId != 0:
                    CharacterName = BookCharacter['CharacterName']
                    CharacterRole = BookCharacter['CharacterRole']
                    CharacterGender = BookCharacter['CharacterGender']
                    CharacterAge = BookCharacter['CharacterAge']
                    BookCharacterText += f"[{CharacterId}] {CharacterName}/{CharacterRole}/{CharacterGender}/{CharacterAge}\n\n"
            if BookCharacterText == '':
                BookCharacterText = "미리 찾은 인물이 없습니다.\n\n"
            
            ## <참고: 이전내용> 추가 Input 생성
            BeforeMarkBodys = []
            Count = 0
            MaxCount = 6
            # 데이터의 인덱스 1의 리스트를 역순으로 순회
            for i in range(len(TranslationDialogue)-1, -1, -1):
                # 아이템이 존재하고 DialogueBody가 비어있지 않은 경우
                if i >= 0 and TranslationDialogue[i]['DialogueBody'] != '' and TranslationDialogue[i]['DialogueBody'] != 'None':
                    BeforeMarkBodys.append(TranslationDialogue[i]['DialogueBody'])
                    Count += 1
                    # 최대 항목 수에 도달하면 중단
                    if Count >= MaxCount:
                        break
            
            BodyText = TranslationDialogue[-1]['Body']
            # 수집된 내용이 있으면 역순으로 정렬하여 합치기 (최신 항목이 마지막에 오도록)
            if BeforeMarkBodys:
                BeforeMarkBodys.reverse()
                BeforeMarkBodyText = "\n\n...\n\n".join(BeforeMarkBodys)
                
                AddInput = f"{BookCharacterText}\n\n\n<참고: 이전내용>\n{BeforeMarkBodyText}\n\n\n"
            else:
                AddInput = f"{BookCharacterText}\n\n\n<참고: 이전내용>\n{BodyText}\n\n\n"
    else:
        AddInput = "미리 찾은 인물이 없습니다.\n\n\n<참고: 이전내용>\n첫번째 대화 내용으로 이전내용이 없습니다.\n\n\n"
    
    return AddInput

## Process12: TranslationDialogueEditing의 InputList
def TranslationDialogueEditingInputList(TranslationEditPath, BeforeProcess1, BeforeProcess2):
    def NumberDialogues(Text):
        Counter = 1
        Pattern = r'\{([^:]+): ([^\}]+)\}'
        
        def ReplaceDialogue(Match):
            nonlocal Counter
            Result = f"{{{Counter} {Match.group(1)}: {Match.group(2)}}}"
            Counter += 1
            return Result
        
        return re.sub(Pattern, ReplaceDialogue, Text)
    
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)
    TranslationProofreading = TranslationEditList[BeforeProcess1]
    TranslationDialogueAnalysis = TranslationEditList[BeforeProcess2]
    
    InputId = 1
    InputList = []
    for i in range(len(TranslationProofreading)):
        IndexId = TranslationProofreading[i]['IndexId']
        IndexTag = TranslationProofreading[i]['IndexTag']
        Index = TranslationProofreading[i]['Index']
        BodyId = TranslationProofreading[i]['BodyId']
        Body = TranslationDialogueAnalysis[i]['Body']
        NumberingBody = NumberDialogues(Body)
        DialogueBody = TranslationDialogueAnalysis[i]['DialogueBody']
        NumberingDialogueBody = NumberDialogues(DialogueBody)
        DialogueCount = len(TranslationDialogueAnalysis[i]['BodyCharacterList'])
        CheckCharacterList = [character['CharacterName'] for character in TranslationDialogueAnalysis[i]['BodyCharacterList']]
        CharacterList = list(set(character['CharacterName'] for character in TranslationDialogueAnalysis[i]['BodyCharacterList']))
        Input = f"<**작업: 대화중심편집내용>\n{NumberingDialogueBody}\n\n"
        InputList.append({"Id": InputId, "IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "Body": NumberingBody, "MarkBody": NumberingDialogueBody, "Input": Input, "DialogueCount": DialogueCount, "CharacterList": CharacterList, "CheckCharacterList": CheckCharacterList})
        InputId += 1
        
    return InputList

## Process12: TranslationDialogueEditing의 추가 Input
def TranslationDialogueEditingAddInput(ProjectDataFrameTranslationDialogueEditingPath, CharacterList):
    if os.path.exists(ProjectDataFrameTranslationDialogueEditingPath):
        with open(ProjectDataFrameTranslationDialogueEditingPath, 'r', encoding='utf-8') as TranslationDataFrame:
            TranslationDialogue = json.load(TranslationDataFrame)[1]
        
            ## <참고: 이전내용>을 CharacterList에 따라서 추가
            BeforeMarkBodys = []
            Count = 0
            MaxCount = 6
            # 데이터의 인덱스 1의 리스트를 역순으로 순회
            for i in range(len(TranslationDialogue)-1, -1, -1):
                # 아이템이 존재하고 DialogueBody가 비어있지 않은 경우
                if i >= 0 and TranslationDialogue[i]['DialogueBody'] != '' and TranslationDialogue[i]['DialogueBody'] != 'None':
                    BodyId = TranslationDialogue[i]['BodyId']
                    DialogueBody = TranslationDialogue[i]['DialogueBody']
                    BeforeMarkBodys.append({"BodyId": BodyId, "DialogueBody": DialogueBody})
                    Count += 1
                    # 최대 항목 수에 도달하면 중단
                    if Count >= MaxCount:
                        break
            
            CharacterMarkBodys = []
            for Character in CharacterList:
                for i in range(len(TranslationDialogue)):
                    if Character in TranslationDialogue[i]['BodyCharacterList']:
                        BodyId = TranslationDialogue[i]['BodyId']
                        DialogueBody = TranslationDialogue[i]['DialogueBody']
                        CharacterMarkBodys.append({"BodyId": BodyId, "DialogueBody": DialogueBody})
            
            # 1. CharacterMarkBodys의 개수가 MaxCount를 넘으면 BodyId 역순으로 정렬한 뒤 MaxCount만큼만 남긴다
            if len(CharacterMarkBodys) > MaxCount:
                # BodyId 기준으로 역순 정렬
                CharacterMarkBodys.sort(key=lambda x: x["BodyId"], reverse=True)
                # MaxCount만큼만 유지
                CharacterMarkBodys = CharacterMarkBodys[:MaxCount]
            # 2. CharacterMarkBodys의 개수가 MaxCount를 넘지 않으면 BeforeMarkBodys에서 추가
            else:
                # BeforeMarkBodys에서 BodyId 값이 가장 큰 것부터 사용하기 위해 정렬
                BeforeMarkBodys.sort(key=lambda x: x["BodyId"], reverse=True)
                
                # CharacterMarkBodys에 이미 있는 BodyId 목록 생성
                ExistingBodyIds = [Body["BodyId"] for Body in CharacterMarkBodys]
                
                # BeforeMarkBodys에서 하나씩 추가
                for Body in BeforeMarkBodys:
                    # 이미 CharacterMarkBodys에 있는 BodyId는 건너뛴다
                    if Body["BodyId"] not in ExistingBodyIds:
                        CharacterMarkBodys.append(Body)
                        ExistingBodyIds.append(Body["BodyId"])
                        
                        # MaxCount에 도달하면 중단
                        if len(CharacterMarkBodys) >= MaxCount:
                            break

            # 중복된 BodyId를 가진 딕셔너리를 하나만 남김
            UniqueBodyDictionary = {}
            for Body in CharacterMarkBodys:
                UniqueBodyDictionary[Body["BodyId"]] = Body
            SortedBodies = sorted(UniqueBodyDictionary.values(), key=lambda x: x["BodyId"])
            CharacterMarkBodyList = [Body["DialogueBody"] for Body in SortedBodies]

            BodyText = TranslationDialogue[-1]['Body']
            # 3. 최종적으로 CharacterMarkBodys를 BodyId 정순으로 정렬 (오름차순)
            if CharacterMarkBodyList:
                BeforeMarkBodyText = "\n\n...\n\n".join(CharacterMarkBodyList)

                AddInput = f"\n{BeforeMarkBodyText}\n\n\n"
            else:
                AddInput = f"\n{BodyText}\n\n\n"
    else:
        AddInput = "\n첫번째 대화 내용으로 이전내용이 없습니다.\n\n\n"
    
    return AddInput

## Process15: AuthorResearch의 InputList
def AuthorResearchInputList(TranslationEditPath, BeforeProcess1, BeforeProcess2, BeforeProcess3, MainLangCode):
    def TruncateTextAtSentenceEnd(Text, MaxChars = 2000):
        if len(Text) <= MaxChars:
            return Text
        Candidate = Text[:MaxChars]
        LastDot = Candidate.rfind('.')
        LastJapaneseDot = Candidate.rfind('。')
        LastHindiDanda = Candidate.rfind('।')
        LastExclam = Candidate.rfind('!')
        LastJapaneseExclam = Candidate.rfind('！')
        LastQuestion = Candidate.rfind('?')
        LastJapaneseQuestion = Candidate.rfind('？')
        LastPunc = max(LastDot, LastJapaneseDot, LastHindiDanda, LastExclam, LastJapaneseExclam, LastQuestion, LastJapaneseQuestion)
        if LastPunc != -1:
            return Candidate[:LastPunc+1]
        return Candidate

    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)
    TranslationBodySplit = TranslationEditList[BeforeProcess1]
    IndexTranslation = TranslationEditList[BeforeProcess2]
    AfterTranslationBodySummary = TranslationEditList[BeforeProcess3]

    ## 1. 원어앞부분 생성
    BookIntroductionText = TruncateTextAtSentenceEnd(TranslationBodySplit[0]['Body'], 2000)
    
    ## 2. 도서제목, 도서목차 생성
    BookContents = ''
    for Index in IndexTranslation:
        if Index['IndexTag'] == 'Title':
            BookTitle = Index['IndexTranslation']
        else:
            BookContents += f"\n{Index['IndexTag']}: {Index['IndexTranslation']}"
    
    ## 3. 도서핵심내용요약, 도서주요문구모음 생성
    BookSummaryItems = []
    TotalChars = 0
    # Score가 높은 순으로 정렬하여, 8000자 이하가 되도록 선택
    for Item in sorted(AfterTranslationBodySummary, key=lambda x: x['Score'], reverse=True):
        SummaryLength = len(Item['BodySummary'])
        if TotalChars + SummaryLength <= 3000:
            BookSummaryItems.append(Item)
            TotalChars += SummaryLength

    BookSummary = sorted(BookSummaryItems, key=lambda x: x['BodyId'])

    # BookSummary에 추가된 딕셔너리의 MainText만 추출하여 MainTextList 생성
    MainTextList = []
    for Item in BookSummary:
        MainTextList.extend(Item['MainText'])

    # BookSummary와 MainText 텍스트화
    BookSummaryText = "\n".join(item["BodySummary"] for item in BookSummary)
    MainText = ', '.join(MainTextList)
    
    ## InputList 생성
    InputId = 1
    InputList = []
    Input = f"[원어앞부분]\n{BookIntroductionText}\n\n[도서제목]{BookTitle}\n\n[도서목차]\n{BookContents}\n\n[도서핵심내용요약]\n{BookSummaryText}\n\n[도서주요문구모음]\n{MainText}\n\n[작가정보.json 작성언어, 꼭 해당 지정된 언어로 작성]\n{MainLangCode}\n\n"

    InputDic = {"Id": InputId, "Input": Input}
    InputList.append(InputDic)
    
    return InputList

## Process16: TranslationCatchphrase의 InputList
def TranslationCatchphraseInputList(TranslationEditPath, BeforeProcess1, BeforeProcess2, BeforeProcess3, MainLangCode):
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEditList = json.load(TranslationEditJson)
    IndexTranslation = TranslationEditList[BeforeProcess1]
    AfterTranslationBodySummary = TranslationEditList[BeforeProcess2]
    AuthorResearch = TranslationEditList[BeforeProcess3]
    ## 1. 저자 생성
    Author = AuthorResearch[0]['Author']
    Birth = AuthorResearch[0]['Birth']
    Nationality = AuthorResearch[0]['Nationality']
    Major = AuthorResearch[0]['Major']
    Degree = AuthorResearch[0]['Degree']
    MajorCareer = AuthorResearch[0]['MajorCareer']
    RepresentativeWorks = AuthorResearch[0]['RepresentativeWorks']
    ThoughtsAndInfluence = AuthorResearch[0]['ThoughtsAndInfluence']
    OtherInterestingFacts = AuthorResearch[0]['OtherInterestingFacts']
    AuthorText = f"이름: {Author}\n출생: {Birth}\n국적: {Nationality}\n전공: {Major}\n학위: {Degree}\n주요경력: {MajorCareer}\n대표작: {RepresentativeWorks}\n사상 및 영향력: {ThoughtsAndInfluence}\n기타 흥미로운 사실: {OtherInterestingFacts}\n"
    
    ## 2. 도서제목, 도서목차 생성
    BookContents = ''
    for Index in IndexTranslation:
        if Index['IndexTag'] == 'Title':
            BookTitle = Index['IndexTranslation']
        else:
            BookContents += f"\n{Index['IndexTag']}: {Index['IndexTranslation']}"
    
    ## 3. 도서핵심내용요약, 도서주요문구모음 생성
    BookSummaryItems = []
    TotalChars = 0
    # Score가 높은 순으로 정렬하여, 8000자 이하가 되도록 선택
    for Item in sorted(AfterTranslationBodySummary, key=lambda x: x['Score'], reverse=True):
        SummaryLength = len(Item['BodySummary'])
        if TotalChars + SummaryLength <= 6000:
            BookSummaryItems.append(Item)
            TotalChars += SummaryLength

    BookSummary = sorted(BookSummaryItems, key=lambda x: x['BodyId'])

    # BookSummary에 추가된 딕셔너리의 MainText만 추출하여 MainTextList 생성
    MainTextList = []
    for Item in BookSummary:
        MainTextList.extend(Item['MainText'])

    # BookSummary와 MainText 텍스트화
    BookSummaryText = "\n".join(item["BodySummary"] for item in BookSummary)
    MainText = ', '.join(MainTextList)
    
    ## InputList 생성
    InputId = 1
    InputList = []
    Input = f"[저자]\n{AuthorText}\n\n[도서제목]\n{BookTitle}\n\n[도서목차]{BookContents}\n\n[도서핵심내용요약]\n{BookSummaryText}\n\n[도서주요문구모음]\n{MainText}\n\n[도서카피모음.json 작성언어, 꼭 해당 지정된 언어로 작성]\n{MainLangCode}\n\n"

    InputDic = {"Id": InputId, "Input": Input}
    InputList.append(InputDic)
    
    return InputList

######################
##### Filter 조건 #####
######################
## 대괄호 쌍 확인 함수
def CheckBalancedBrackets(text):
    stack = []
    for char in text:
        if char == '[':
            stack.append(char)
        elif char == ']':
            if not stack:
                return False
            stack.pop()
    return len(stack) == 0

## Process1: TranslationIndexDefine의 Filter(Error 예외처리)
def TranslationIndexDefineFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "TranslationIndexDefine, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_keys = ['언어태그', '목차리스트']
    missing_top_keys = [key for key in required_top_keys if key not in OutputDic]
    if missing_top_keys:
        return f"TranslationIndexDefine, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"

    # Error3: '언어태그' 데이터 검증
    valid_language_tags = {'en', 'zh', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'pt', 'ru', 'ar', 'nl', 'sv', 'no', 'da', 'fi', 'pl', 'tr', 'el', 'cs', 'hu', 'ro', 'sk', 'uk', 'hi', 'id', 'ms', 'th', 'vi', 'he', 'bg', 'ca'}
    if not isinstance(OutputDic['언어태그'], str) or OutputDic['언어태그'] not in valid_language_tags:
        return "TranslationIndexDefine, JSON에서 오류 발생: '언어태그'는 유효한 언어 태그 중 하나여야 합니다"

    # Error4: '목차리스트' 데이터 타입 검증
    if not isinstance(OutputDic['목차리스트'], list):
        return "TranslationIndexDefine, JSON에서 오류 발생: '목차리스트'는 리스트여야 합니다"

    for idx, item in enumerate(OutputDic['목차리스트']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"TranslationIndexDefine, JSON에서 오류 발생: '목차리스트[{idx}]'는 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['번호', '목차태그', '목차']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"TranslationIndexDefine, JSONKeyError: '목차리스트[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 및 유효한 값 검증
        if not (isinstance(item['번호'], (str, int)) and (isinstance(item['번호'], int) or item['번호'].isdigit())):
            return f"TranslationIndexDefine, JSON에서 오류 발생: '목차리스트[{idx}] > 번호'는 문자열 또는 정수여야 합니다"
        if isinstance(item['번호'], str):
            if item['번호'].isdigit():
                item['번호'] = int(item['번호'])

        if idx == 0:
            if item['목차태그'] != 'Title':
                return f"TranslationIndexDefine, JSON에서 오류 발생: '목차리스트[{idx}] > 목차태그'는 'Title'이어야 합니다"
        else:
            valid_index_tags = {'Logue', 'Part', 'Chapter', 'Index'}
            if item['목차태그'] not in valid_index_tags:
                return f"TranslationIndexDefine, JSON에서 오류 발생: '목차리스트[{idx}] > 목차태그'는 ['Logue', 'Part', 'Chapter', 'Index'] 중 하나여야 합니다"

        if not isinstance(item['목차'], str):
            return f"TranslationIndexDefine, JSON에서 오류 발생: '목차리스트[{idx}] > 목차'는 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic

## Process2, 14: TranslationBodySummary의 Filter(Error 예외처리)
def TranslationBodySummaryFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "AfterTranslationBodySummary, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '현재내용요약' not in OutputDic:
        return "AfterTranslationBodySummary, JSONKeyError: '현재내용요약' 키가 누락되었습니다"

    # Error3: '현재내용요약' 데이터 타입 검증
    if not isinstance(OutputDic['현재내용요약'], dict):
        return "AfterTranslationBodySummary, JSON에서 오류 발생: '현재내용요약'은 딕셔너리 형태여야 합니다"

    # 필수 키 확인
    required_keys = ['핵심문구', '요약', '중요도']
    missing_keys = [key for key in required_keys if key not in OutputDic['현재내용요약']]
    if missing_keys:
        return f"AfterTranslationBodySummary, JSONKeyError: '현재내용요약'에 누락된 키: {', '.join(missing_keys)}"

    # 데이터 타입 검증
    if not isinstance(OutputDic['현재내용요약']['핵심문구'], list):
        return "AfterTranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 핵심문구'는 리스트 형태여야 합니다"
    
    if not all(isinstance(item, str) for item in OutputDic['현재내용요약']['핵심문구']):
        return "AfterTranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 핵심문구' 리스트의 모든 요소는 문자열이어야 합니다"

    if not (1 <= len(OutputDic['현재내용요약']['핵심문구']) <= 3):
        return "AfterTranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 핵심문구'는 1~3개여야 합니다"

    if not isinstance(OutputDic['현재내용요약']['요약'], str):
        return "AfterTranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 요약'은 문자열이어야 합니다"

    if not isinstance(OutputDic['현재내용요약']['중요도'], (str, int)):
        return "AfterTranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 중요도'는 정수여야 합니다"
    if isinstance(OutputDic['현재내용요약']['중요도'], str):
        ImportanceNum = re.sub(r'\D', '', OutputDic['현재내용요약']['중요도'])
        OutputDic['현재내용요약']['중요도'] = int(ImportanceNum)

    if not (0 <= OutputDic['현재내용요약']['중요도'] <= 1000):
        return "AfterTranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 중요도'는 0~1000 사이의 정수여야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['현재내용요약']

## Process3: WordListGen의 Filter(Error 예외처리)
def WordListGenFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "WordListGen, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '단어장' not in OutputDic:
        return "WordListGen, JSONKeyError: '단어장' 키가 누락되었습니다"

    # Error3: '단어장' 데이터 타입 검증
    if not isinstance(OutputDic['단어장'], list):
        return "WordListGen, JSON에서 오류 발생: '단어장'은 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['단어장']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"WordListGen, JSON에서 오류 발생: '단어장[{idx}]'은 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['번호', '원문', '번역', '선택이유']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"WordListGen, JSONKeyError: '단어장[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 및 유효한 값 검증
        if not (isinstance(item['번호'], (str, int)) and (isinstance(item['번호'], int) or item['번호'].isdigit())):
            return f"WordListGen, JSON에서 오류 발생: '단어장[{idx}] > 번호'는 문자열 또는 정수여야 합니다"
        if isinstance(item['번호'], str):
            if item['번호'].isdigit():
                item['번호'] = int(item['번호'])

        if not isinstance(item['원문'], str):
            return f"WordListGen, JSON에서 오류 발생: '단어장[{idx}] > 원문'은 문자열이어야 합니다"

        if not isinstance(item['번역'], str):
            return f"WordListGen, JSON에서 오류 발생: '단어장[{idx}] > 번역'은 문자열이어야 합니다"

        if not isinstance(item['선택이유'], str):
            return f"WordListGen, JSON에서 오류 발생: '단어장[{idx}] > 선택이유'는 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['단어장']

## Process4: UniqueWordListGen의 Filter(Error 예외처리)
def UniqueWordListGenFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "UniqueWordListGen, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '고유명사' not in OutputDic:
        return "UniqueWordListGen, JSONKeyError: '고유명사' 키가 누락되었습니다"

    # Error3: '고유명사' 데이터 타입 검증
    if not isinstance(OutputDic['고유명사'], list):
        return "UniqueWordListGen, JSON에서 오류 발생: '고유명사'는 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['고유명사']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"UniqueWordListGen, JSON에서 오류 발생: '고유명사[{idx}]'는 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['번호', '원문', '번역', '선택이유']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"UniqueWordListGen, JSONKeyError: '고유명사[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 및 유효한 값 검증
        if not (isinstance(item['번호'], (str, int)) and (isinstance(item['번호'], int) or item['번호'].isdigit())):
            return f"UniqueWordListGen, JSON에서 오류 발생: '고유명사[{idx}] > 번호'는 문자열 또는 정수여야 합니다"
        if isinstance(item['번호'], str):
            if item['번호'].isdigit():
                item['번호'] = int(item['번호'])

        if not isinstance(item['원문'], str):
            return f"UniqueWordListGen, JSON에서 오류 발생: '고유명사[{idx}] > 원문'은 문자열이어야 합니다"

        if not isinstance(item['번역'], str):
            return f"UniqueWordListGen, JSON에서 오류 발생: '고유명사[{idx}] > 번역'은 문자열이어야 합니다"

        if not isinstance(item['선택이유'], str):
            return f"UniqueWordListGen, JSON에서 오류 발생: '고유명사[{idx}] > 선택이유'는 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['고유명사']

## Process5: WordListPostprocessing의 Filter(Error 예외처리)
def WordListPostprocessingFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "WordListPostprocessing, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '정리된단어장' not in OutputDic:
        return "WordListPostprocessing, JSONKeyError: '정리된단어장' 키가 누락되었습니다"

    # Error3: '정리된단어장' 데이터 타입 검증
    if not isinstance(OutputDic['정리된단어장'], list):
        return "WordListPostprocessing, JSON에서 오류 발생: '정리된단어장'은 리스트 형태여야 합니다"

    # Error4: '정리된단어장' 데이터 수 확인
    if len(OutputDic['정리된단어장']) != CheckCount:
        return f"WordListPostprocessing, JSON에서 오류 발생: '정리된단어장' 데이터 수가 ((기존단어장: {CheckCount})) ((정리된단어장: {len(OutputDic['정리된단어장'])})) 다릅니다"
    
    for idx, item in enumerate(OutputDic['정리된단어장']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"WordListPostprocessing, JSON에서 오류 발생: '정리된단어장[{idx}]'는 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['번호', '원문', '번역', '정리방법']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"WordListPostprocessing, JSONKeyError: '정리된단어장[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 및 유효한 값 검증
        if not (isinstance(item['번호'], (str, int)) and (isinstance(item['번호'], int) or item['번호'].isdigit())):
            return f"WordListPostprocessing, JSON에서 오류 발생: '정리된단어장[{idx}] > 번호'는 문자열 또는 정수여야 합니다"
        if isinstance(item['번호'], str):
            if item['번호'].isdigit():
                item['번호'] = int(item['번호'])

        if not isinstance(item['원문'], str):
            return f"WordListPostprocessing, JSON에서 오류 발생: '정리된단어장[{idx}] > 원문'은 문자열이어야 합니다"

        if not isinstance(item['번역'], str):
            return f"WordListPostprocessing, JSON에서 오류 발생: '정리된단어장[{idx}] > 번역'은 문자열이어야 합니다"

        if item['정리방법'] not in ['적합', '삭제', '선택', '수정']:
            return f"WordListPostprocessing, JSON에서 오류 발생: '정리된단어장[{idx}] > 정리방법'은 '적합', '삭제', '선택', '수정' 중 하나여야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['정리된단어장']


## Process6: IndexTranslation의 Filter(Error 예외처리)
def IndexTranslationFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "IndexTranslation, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '현재목차번역' not in OutputDic:
        return "IndexTranslation, JSONKeyError: '현재목차번역' 키가 누락되었습니다"

    # Error3: '현재목차번역' 데이터 타입 검증
    if not isinstance(OutputDic['현재목차번역'], dict):
        return "IndexTranslation, JSON에서 오류 발생: '현재목차번역'은 딕셔너리 형태여야 합니다"

    # 필수 키 확인
    required_keys = ['현재목차원문', '현재목차번역', '번역이유']
    missing_keys = [key for key in required_keys if key not in OutputDic['현재목차번역']]
    if missing_keys:
        return f"IndexTranslation, JSONKeyError: '현재목차번역'에 누락된 키: {', '.join(missing_keys)}"

    # 데이터 타입 검증
    if not isinstance(OutputDic['현재목차번역']['현재목차원문'], str):
        return "IndexTranslation, JSON에서 오류 발생: '현재목차번역 > 현재목차원문'은 문자열이어야 합니다"

    if not isinstance(OutputDic['현재목차번역']['현재목차번역'], str):
        return "IndexTranslation, JSON에서 오류 발생: '현재목차번역 > 현재목차번역'은 문자열이어야 합니다"

    if not isinstance(OutputDic['현재목차번역']['번역이유'], str):
        return "IndexTranslation, JSON에서 오류 발생: '현재목차번역 > 번역이유'는 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['현재목차번역']

## Process7: BodyTranslationPreprocessing의 Filter(Error 예외처리)
def BodyTranslationPreprocessingFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "BodyTranslationPreprocessing, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '수정된번역단어' not in OutputDic:
        return "BodyTranslationPreprocessing, JSONKeyError: '수정된번역단어' 키가 누락되었습니다"

    # Error3: '수정된번역단어' 데이터 타입 검증
    if not isinstance(OutputDic['수정된번역단어'], list):
        return "BodyTranslationPreprocessing, JSON에서 오류 발생: '수정된번역단어'은 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['수정된번역단어']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"BodyTranslationPreprocessing, JSON에서 오류 발생: '수정된번역단어[{idx}]'는 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['번호', '원단어', '수정된번역단어', '수정이유']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"BodyTranslationPreprocessing, JSONKeyError: '수정된번역단어[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 및 유효한 값 검증
        if not (isinstance(item['번호'], (str, int)) and (isinstance(item['번호'], int) or item['번호'].isdigit())):
            return f"BodyTranslationPreprocessing, JSON에서 오류 발생: '수정된번역단어[{idx}] > 번호'는 문자열 또는 정수여야 합니다"
        if isinstance(item['번호'], str):
            if item['번호'].isdigit():
                item['번호'] = int(item['번호'])

        if not isinstance(item['원단어'], str):
            return f"BodyTranslationPreprocessing, JSON에서 오류 발생: '수정된번역단어[{idx}] > 원단어'는 문자열이어야 합니다"

        if not isinstance(item['수정된번역단어'], str):
            return f"BodyTranslationPreprocessing, JSON에서 오류 발생: '수정된번역단어[{idx}] > 수정된번역단어'는 문자열이어야 합니다"

        if not isinstance(item['수정이유'], str):
            return f"BodyTranslationPreprocessing, JSON에서 오류 발생: '수정된번역단어[{idx}] > 수정이유'는 문자열이어야 합니다"
        ## '수정된번역단어' 후처리
        if item['수정이유'] == '삭제':
            item['수정된번역단어'] = ''

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['수정된번역단어']

## Process8: BodyTranslation의 Filter(Error 예외처리)
def BodyTranslationFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "BodyTranslation, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '현재번역문' not in OutputDic:
        return "BodyTranslation, JSONKeyError: '현재번역문' 키가 누락되었습니다"

    # Error3: '현재번역문' 데이터 타입 검증
    if not isinstance(OutputDic['현재번역문'], dict):
        return "BodyTranslation, JSON에서 오류 발생: '현재번역문'은 딕셔너리 형태여야 합니다"

    # 필수 키 확인
    if '번역문' not in OutputDic['현재번역문']:
        return "BodyTranslation, JSONKeyError: '현재번역문'에 '번역문' 키가 누락되었습니다"

    # 데이터 타입 검증
    if not isinstance(OutputDic['현재번역문']['번역문'], str):
        return "BodyTranslation, JSON에서 오류 발생: '현재번역문 > 번역문'은 문자열이어야 합니다"
        
    # Error4: 번역문에 주석 표기 검증
    if ('[' in OutputDic['현재번역문']['번역문']) or (']' in OutputDic['현재번역문']['번역문']):
        if not CheckBalancedBrackets(OutputDic['현재번역문']['번역문']):
            return "BodyTranslation, 주석표기 오류: 번역문 내의 주석표기 대괄호의 짝이 맞지 않습니다"

    # Error5: '현재번역문'에 이전 번역문이 포함되었는지 확인
    BeforeText = CheckCount # CheckCount는 원본 글의 내용으로 가정
    CurrentText = OutputDic['현재번역문']['번역문']
    
    # 각 텍스트에서 앞 문장 3개 추출
    BeforeSentences = [s.strip() for s in re.split(r'[.!?。？！]+', BeforeText) if s.strip()][:3]
    CurrentSentences = [s.strip() for s in re.split(r'[.!?。？！]+', CurrentText) if s.strip()][:3]

    # 각 문장에서 언어를 제외한 모든 것(공백, 특수기호 등) 제거
    CleanBeforeSentences = [re.sub(r'\W+', '', s, flags=re.UNICODE) for s in BeforeSentences]
    CleanCurrentSentences = [re.sub(r'\W+', '', s, flags=re.UNICODE) for s in CurrentSentences]

    # 정제된 문장 비교 및 동일 문장 개수 확인
    MatchCount = 0
    # 두 리스트 중 짧은 길이만큼만 비교 (문장 수가 3개 미만일 경우 대비)
    MinLen = min(len(CleanBeforeSentences), len(CleanCurrentSentences))
    for i in range(MinLen):
        # 비어 있지 않은 문자열끼리 비교했을 때 동일하면 카운트 증가
        if CleanBeforeSentences[i] and CleanCurrentSentences[i] and CleanBeforeSentences[i] == CleanCurrentSentences[i]:
            MatchCount += 1

    # 동일한 문장이 2개 이상이면 오류 메시지 반환
    if MatchCount >= 2:
        return "BodyTranslation, SentenceMatchError: 번역된 내용과 원본 내용의 앞 3문장 중 2개 이상이 동일합니다."

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['현재번역문']

## Process8: BodyTranslationCheck의 Filter(Error 예외처리)
def BodyTranslationCheckFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "BodyTranslationCheck, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '도서내용어조체크' not in OutputDic:
        return "BodyTranslationCheck, JSONKeyError: '도서내용어조체크' 키가 누락되었습니다"

    # Error3: '도서내용어조체크' 데이터 타입 검증
    if not isinstance(OutputDic['도서내용어조체크'], dict):
        return "BodyTranslationCheck, JSON에서 오류 발생: '도서내용어조체크'는 딕셔너리 형태여야 합니다"

    # 필수 키 확인
    required_keys = ['이전도서내용어조', '현재도서내용어조', '어조일치여부']
    missing_keys = [key for key in required_keys if key not in OutputDic['도서내용어조체크']]
    if missing_keys:
        return f"BodyTranslationCheck, JSONKeyError: '도서내용어조체크'에 누락된 키: {', '.join(missing_keys)}"

    # 데이터 타입 및 값 검증
    valid_tone_types = ['격식체', '평서체', '비격식체', '모름']
    valid_match_status = ['일치', '불일치']

    if OutputDic['도서내용어조체크']['이전도서내용어조'] not in valid_tone_types:
        return "BodyTranslationCheck, JSON에서 오류 발생: '도서내용어조체크 > 이전도서내용어조'는 '격식체', '평서체', '비격식체', '모름' 중 하나여야 합니다"

    if OutputDic['도서내용어조체크']['현재도서내용어조'] not in valid_tone_types:
        return "BodyTranslationCheck, JSON에서 오류 발생: '도서내용어조체크 > 현재도서내용어조'는 '격식체', '평서체', '비격식체', '모름' 중 하나여야 합니다"

    if OutputDic['도서내용어조체크']['어조일치여부'] not in valid_match_status:
        return "BodyTranslationCheck, JSON에서 오류 발생: '도서내용어조체크 > 어조일치여부'는 '일치' 또는 '불일치' 중 하나여야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['도서내용어조체크']

## Process8: BodyToneEditing의 Filter(Error 예외처리)
def BodyToneEditingFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "BodyToneEditing, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '어조일치' not in OutputDic:
        return "BodyToneEditing, JSONKeyError: '어조일치' 키가 누락되었습니다"

    # Error3: '어조일치' 데이터 타입 검증
    if not isinstance(OutputDic['어조일치'], dict):
        return "BodyToneEditing, JSON에서 오류 발생: '어조일치'는 딕셔너리 형태여야 합니다"

    required_keys = ['이전도서어조', '어조일치현재도서내용']
    missing_keys = [key for key in required_keys if key not in OutputDic['어조일치']]
    if missing_keys:
        return f"BodyToneEditing, JSONKeyError: '어조일치'에 누락된 키: {', '.join(missing_keys)}"

    item = OutputDic['어조일치']

    # '이전도서어조' 값 검증 ('격식체', '평서체', '비격식체' 중 하나여야 함)
    valid_tones = ['격식체', '평서체', '비격식체']
    if item['이전도서어조'] not in valid_tones:
        return f"BodyToneEditing, JSON에서 오류 발생: '이전도서어조'는 '격식체', '평서체', '비격식체' 중 하나여야 합니다"

    if not item['이전도서어조'] in CheckCount:
        return f"BodyToneEditing, JSON에서 오류 발생: '이전도서어조'는 {CheckCount}가 되어야 합니다"
    
    # '어조일치현재도서내용' 값 검증 (문자열이어야 함)
    if not isinstance(item['어조일치현재도서내용'], str):
        return "BodyToneEditing, JSON에서 오류 발생: '어조일치현재도서내용'은 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['어조일치']

## Process8: BodyLanguageEditing의 Filter(Error 예외처리)
def BodyLanguageEditingFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "BodyLanguageEditing, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '완벽번역' not in OutputDic:
        return "BodyLanguageEditing, JSONKeyError: '완벽번역' 키가 누락되었습니다"

    # Error3: '완벽번역' 데이터 타입 검증
    if not isinstance(OutputDic['완벽번역'], dict):
        return "BodyLanguageEditing, JSON에서 오류 발생: '완벽번역'은 딕셔너리 형태여야 합니다"

    required_keys = ['번역문']
    missing_keys = [key for key in required_keys if key not in OutputDic['완벽번역']]
    if missing_keys:
        return f"BodyLanguageEditing, JSONKeyError: '완벽번역'에 누락된 키: {', '.join(missing_keys)}"

    item = OutputDic['완벽번역']

    # '번역문' 값 검증 (문자열이어야 함)
    if not isinstance(item['번역문'], str):
        return "BodyLanguageEditing, JSON에서 오류 발생: '번역문'은 문자열이어야 합니다"

    # # Error4: '번역문'에 불필요한 언어가 포함되어 있는지 확인 (번역어(원어), 발음(원어)만 허용)
    # ResponseLang = sorted(LanguageDetection(OutputDic['완벽번역']['번역문'], DetectionLength = 3))
    # LangDetection = any(Lang not in CheckCount for Lang in ResponseLang)
    # # 번역언어 외의 언어가 포함되었는지 확인 (예: 한글 텍스트에 영어 문장이 많다면 오류)
    # if LangDetection:
    #     return f"BodyLanguageEditing, JSON에서 오류 발생: '번역문'에는 번역언어 이외의 언어가 포함될 수 없습니다. 번역교정전(({CheckCount})), 번역교정후(({ResponseLang}))"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['완벽번역']

## Process8: BodyTranslationWordCheck의 Filter(Error 예외처리)
def BodyTranslationWordCheckFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "BodyTranslationWordCheck, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '괄호제거단어' not in OutputDic:
        return "BodyTranslationWordCheck, JSONKeyError: '괄호제거단어' 키가 누락되었습니다"

    # Error3: '괄호제거단어' 데이터 타입 검증
    if not isinstance(OutputDic['괄호제거단어'], list):
        return "BodyTranslationWordCheck, JSON에서 오류 발생: '괄호제거단어'는 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['괄호제거단어']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"BodyTranslationWordCheck, JSON에서 오류 발생: '괄호제거단어[{idx}]'는 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['번호', '단어', '제거이유']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"BodyTranslationWordCheck, JSONKeyError: '괄호제거단어[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 및 유효한 값 검증
        if not (isinstance(item['번호'], (str, int)) and (isinstance(item['번호'], int) or item['번호'].isdigit())):
            return f"BodyTranslationWordCheck, JSON에서 오류 발생: '괄호제거단어[{idx}] > 번호'는 문자열 또는 정수여야 합니다"
        if isinstance(item['번호'], str):
            if item['번호'].isdigit():
                item['번호'] = int(item['번호'])

        if not isinstance(item['단어'], str):
            return f"BodyTranslationWordCheck, JSON에서 오류 발생: '괄호제거단어[{idx}] > 단어'는 문자열이어야 합니다"

        if not isinstance(item['제거이유'], str):
            return f"BodyTranslationWordCheck, JSON에서 오류 발생: '괄호제거단어[{idx}] > 제거이유'는 문자열이어야 합니다"

    # Error4: '괄호제거단어' 존재 여부 확인
    for item in OutputDic['괄호제거단어']:
        RemoveBracketWord = "{" + f"{item['번호']} {item['단어']}" + "}"
        if RemoveBracketWord not in CheckCount:
            return f"BodyTranslationWordCheck, JSON에서 오류 발생: '괄호제거단어'에 있는 단어가 번역문에 존재하지 않습니다"
    
    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['괄호제거단어']

## Process9: TranslationEditing의 Filter(Error 예외처리)
def TranslationEditingFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "TranslationEditing, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '편집내용' not in OutputDic:
        return "TranslationEditing, JSONKeyError: '편집내용' 키가 누락되었습니다"

    # Error3: '편집내용' 데이터 타입 검증
    if not isinstance(OutputDic['편집내용'], dict):
        return "TranslationEditing, JSON에서 오류 발생: '편집내용'은 딕셔너리 형태여야 합니다"

    # 필수 키 확인
    if '내용' not in OutputDic['편집내용']:
        return "TranslationEditing, JSONKeyError: '편집내용'에 '내용' 키가 누락되었습니다"

    # 데이터 타입 검증
    if not isinstance(OutputDic['편집내용']['내용'], str):
        return "TranslationEditing, JSON에서 오류 발생: '편집내용 > 내용'은 문자열이어야 합니다"
    
    OriginalText = OutputDic['편집내용']['내용']
    RemovePattern = r"^<이전편집내용>\s*에\s*이\s*어\s*서\s*"
    CleanedText = re.sub(RemovePattern, "", OriginalText)
    OutputDic['편집내용']['내용'] = CleanedText
    
    if '이전편집내용' in OutputDic['편집내용']['내용']:
        return "TranslationEditing, JSON에서 오류 발생: '편집내용 > 내용'에 <이전편집내용>이 포함되어 있으면 안됩니다."
    
    # Error4: 편집내용에 주석 표기 검증
    if ('[' in OutputDic['편집내용']['내용']) or (']' in OutputDic['편집내용']['내용']):
        if not CheckBalancedBrackets(OutputDic['편집내용']['내용']):
            return "TranslationEditing, 주석표기 오류: 번역문 내의 주석표기 대괄호의 짝이 맞지 않습니다"
        
    # Error5: '편집내용'에 이전 내용이 포함되었는지 확인
    BeforeText = CheckCount # CheckCount는 원본 글의 내용으로 가정
    CurrentText = OutputDic['편집내용']['내용']
    
    # 각 텍스트에서 앞 문장 3개 추출
    BeforeSentences = [s.strip() for s in re.split(r'[.!?。？！]+', BeforeText) if s.strip()][:3]
    CurrentSentences = [s.strip() for s in re.split(r'[.!?。？！]+', CurrentText) if s.strip()][:3]

    # 각 문장에서 언어를 제외한 모든 것(공백, 특수기호 등) 제거
    CleanBeforeSentences = [re.sub(r'\W+', '', s, flags=re.UNICODE) for s in BeforeSentences]
    CleanCurrentSentences = [re.sub(r'\W+', '', s, flags=re.UNICODE) for s in CurrentSentences]

    # 정제된 문장 비교 및 동일 문장 개수 확인
    MatchCount = 0
    # 두 리스트 중 짧은 길이만큼만 비교 (문장 수가 3개 미만일 경우 대비)
    MinLen = min(len(CleanBeforeSentences), len(CleanCurrentSentences))
    for i in range(MinLen):
        # 비어 있지 않은 문자열끼리 비교했을 때 동일하면 카운트 증가
        if CleanBeforeSentences[i] and CleanCurrentSentences[i] and CleanBeforeSentences[i] == CleanCurrentSentences[i]:
            MatchCount += 1

    # 동일한 문장이 2개 이상이면 오류 메시지 반환
    if MatchCount >= 2:
        return "TranslationEditing, SentenceMatchError: 편집된 내용과 원본 내용의 앞 3문장 중 2개 이상이 동일합니다."

    # Error6: '편집내용'에 프롬프트가 포함된 경우 제거
    PromtList = ['<현재편집할내용>을 매끄럽고 세련되게 다듬는 윤문, 문장 구조의 다변화, 호소력 있는 어조와 친근한 표현 사용 과정을 통해 편집하여 작성', '[*편집할내용]을 편집작업1, 편집작업2, 편집작업3, 편집작업4에 따라 현대적으로 편집하여 매우 완성도가 높은 글로 재작성', '(완성도 높은 <편집내용.json>완성을 위한 절차와 방법)과 (좋은내용 예시n)에 따라서 <**편집내용-편집대상>를 편집한 내용']
    for prompt in PromtList:
        OutputDic['편집내용']['내용'] = re.sub(rf'\n?{re.escape(prompt)}\n?', '', OutputDic['편집내용']['내용'])

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['편집내용']

## Process10: TranslationProofreading의 Filter(Error 예외처리)
def TranslationProofreadingFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "TranslationProofreading, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '교정' not in OutputDic:
        return "TranslationProofreading, JSONKeyError: '교정' 키가 누락되었습니다"

    # Error3: '교정' 데이터 타입 검증
    if not isinstance(OutputDic['교정'], dict):
        return "TranslationProofreading, JSON에서 오류 발생: '교정'은 딕셔너리 형태여야 합니다"

    # 필수 키 확인
    if '도서내용' not in OutputDic['교정']:
        return "TranslationProofreading, JSONKeyError: '교정'에 '도서내용' 키가 누락되었습니다"

    # 데이터 타입 검증
    if not isinstance(OutputDic['교정']['도서내용'], str):
        return "TranslationProofreading, JSON에서 오류 발생: '교정 > 도서내용'은 문자열이어야 합니다"
    
    # Error5: 따옴표 후처리 및 개수 확인
    # '도서내용'의 값에서 줄바꿈과 쌍따옴표 후처리
    OutputDic['교정']['도서내용'] = OutputDic['교정']['도서내용'].replace('\"', '"').replace('“', '"').replace('”', '"').replace('\'', '"').replace('‘', "'").replace('’', "'")
    if OutputDic['교정']['도서내용'].count('"') % 2 != 0:
        return f"TranslationProofreading, JSON에서 오류 발생: '교정 > 도서내용'의 따옴표 개수가 홀수입니다"
    
    # 가장 앞자리 확인 후 전처리
    if OutputDic['교정']['도서내용'][0] not in ['\n', ' ',]:
        OutputDic['교정']['도서내용'] = ' ' + OutputDic['교정']['도서내용']
    
    # Error6: 교정 전후 '도서내용' 일치 확인
    CheckCount = re.sub(r'\\.', '', CheckCount)
    CheckCount = re.sub(r'[^\w\d]', '', CheckCount, flags = re.UNICODE)
    CheckCount = CheckCount.replace('_', '')
    
    EditCheckCount = re.sub(r'\\.', '', OutputDic['교정']['도서내용'])
    EditCheckCount = re.sub(r'[^\w\d]', '', EditCheckCount, flags = re.UNICODE)
    EditCheckCount = EditCheckCount.replace('_', '')
    # print(f"\n\nCheckCount: {CheckCount}")
    # print(f"\n\nEditCheckCount: {EditCheckCount}\n\n")
    if CheckCount != EditCheckCount:
        return f"TranslationProofreading, JSON에서 오류 발생: '교정내용({len(EditCheckCount)}) != 도서내용({len(CheckCount)})'이 교정 전후로 일치하지 않습니다"

    # Error7: 번역문에 주석 표기 검증
    if ('[' in OutputDic['교정']['도서내용']) or (']' in OutputDic['교정']['도서내용']):
        if not CheckBalancedBrackets(OutputDic['교정']['도서내용']):
            return "TranslationProofreading, 주석표기 오류: 번역문 내의 주석표기 대괄호의 짝이 맞지 않습니다"
        
    # Error8: '도서내용'에 이전 도서내용이 포함되었는지 확인
    BeforeText = CheckCount # CheckCount는 원본 글의 내용으로 가정
    CurrentText = OutputDic['교정']['도서내용']
    
    # 각 텍스트에서 앞 문장 3개 추출
    BeforeSentences = [s.strip() for s in re.split(r'[.!?。？！]+', BeforeText) if s.strip()][:3]
    CurrentSentences = [s.strip() for s in re.split(r'[.!?。？！]+', CurrentText) if s.strip()][:3]

    # 각 문장에서 언어를 제외한 모든 것(공백, 특수기호 등) 제거
    CleanBeforeSentences = [re.sub(r'\W+', '', s, flags=re.UNICODE) for s in BeforeSentences]
    CleanCurrentSentences = [re.sub(r'\W+', '', s, flags=re.UNICODE) for s in CurrentSentences]

    # 정제된 문장 비교 및 동일 문장 개수 확인
    MatchCount = 0
    # 두 리스트 중 짧은 길이만큼만 비교 (문장 수가 3개 미만일 경우 대비)
    MinLen = min(len(CleanBeforeSentences), len(CleanCurrentSentences))
    for i in range(MinLen):
        # 비어 있지 않은 문자열끼리 비교했을 때 동일하면 카운트 증가
        if CleanBeforeSentences[i] and CleanCurrentSentences[i] and CleanBeforeSentences[i] == CleanCurrentSentences[i]:
            MatchCount += 1

    # 동일한 문장이 2개 이상이면 오류 메시지 반환
    if MatchCount >= 2:
        return "TranslationProofreading, SentenceMatchError: 교정된 내용과 원본 내용의 앞 3문장 중 2개 이상이 동일합니다."

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['교정']

## Process11: TranslationDialogueAnalysis의 Filter(Error 예외처리)
def TranslationDialogueAnalysisFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "TranslationDialogueAnalysis, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '대화내용분석' not in OutputDic:
        return "TranslationDialogueAnalysis, JSONKeyError: '대화내용분석' 키가 누락되었습니다"

    # Error3: '대화내용분석' 데이터 타입 검증
    if not isinstance(OutputDic['대화내용분석'], list):
        return "TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석'은 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['대화내용분석']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석[{idx}]'는 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = [
            '번호', '대화문여부', '동일인물존재여부', '인물번호', '인물이름', 
            '역할', '성별', '연령', '상대인물이름'
        ]
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"TranslationDialogueAnalysis, JSONKeyError: '대화내용분석[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 및 유효한 값 검증
        if not (isinstance(item['번호'], int) or (isinstance(item['번호'], str) and item['번호'].isdigit())):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석[{idx}] > 번호'는 숫자형(또는 숫자 문자열)이어야 합니다"
        if isinstance(item['번호'], str):
            item['번호'] = int(item['번호'])

        if item['대화문여부'] not in ['맞음', '아님']:
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석[{idx}] > 대화문여부'는 '맞음' 또는 '아님' 중 하나여야 합니다"

        if item['동일인물존재여부'] not in ['있음', '없음', '']:
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석[{idx}] > 동일인물존재여부'는 '있음' 또는 '없음' 중 하나여야 합니다"

        if not (isinstance(item['인물번호'], (str, int)) and (isinstance(item['인물번호'], int) or item['인물번호'].isdigit() or item['인물번호'] in ['없음', ''])):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석[{idx}] > 인물번호'는 정수, 숫자형 문자열 또는 '없음'이어야 합니다"
        if isinstance(item['인물번호'], str):
            if item['인물번호'].isdigit():
                item['인물번호'] = int(item['인물번호'])

        if not isinstance(item['인물이름'], str):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석[{idx}] > 인물이름'은 문자열이어야 합니다"
        
        if item['인물이름'] == '없음':
            if item['대화문여부'] == '맞음':
                return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석[{idx}] > 인물이름'은 '없음'이 아니어야 합니다"

        if not isinstance(item['역할'], str):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석[{idx}] > 역할'은 문자열이어야 합니다"

        if not isinstance(item['성별'], str):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석[{idx}] > 성별'은 문자열이어야 합니다"

        if not isinstance(item['연령'], str):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석[{idx}] > 연령'은 문자열이어야 합니다"

        if not isinstance(item['상대인물이름'], str):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석[{idx}] > 상대인물이름'은 문자열이어야 합니다"

    # Error4: '대화내용' 리스트 개수 확인
    if len(OutputDic['대화내용분석']) != CheckCount:
        return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화내용분석' 데이터 수가 ((기존대화: {CheckCount})) ((편집대화: {len(OutputDic['대화내용분석'])})) 다릅니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['대화내용분석']

## Process12: TranslationDialogueEditing의 Filter(Error 예외처리)
def TranslationDialogueEditingFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "TranslationDialogueEditing, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '대화내용' not in OutputDic:
        return "TranslationDialogueEditing, JSONKeyError: '대화내용' 키가 누락되었습니다"

    # Error3: '대화내용' 데이터 타입 검증
    if not isinstance(OutputDic['대화내용'], list):
        return "TranslationDialogueEditing, JSON에서 오류 발생: '대화내용'은 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['대화내용']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용[{idx}]'는 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = [
            '번호', '인물', '인물특징', '대화상황', '상대인물',
            '이전내용에서말의높임법', '현재말의높임법', '편집대화내용', '편집이유'
        ]
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"TranslationDialogueEditing, JSONKeyError: '대화내용[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 및 유효한 값 검증
        if not (isinstance(item['번호'], (str, int)) and (isinstance(item['번호'], int) or item['번호'].isdigit())):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용[{idx}] > 번호'는 문자열 또는 정수여야 합니다"
        if isinstance(item['번호'], str):
            if item['번호'].isdigit():
                item['번호'] = int(item['번호'])

        if not isinstance(item['인물'], str):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용[{idx}] > 인물'은 문자열이어야 합니다"

        if not isinstance(item['인물특징'], str):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용[{idx}] > 인물특징'은 문자열이어야 합니다"

        if not isinstance(item['대화상황'], str):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용[{idx}] > 대화상황'은 문자열이어야 합니다"

        if not isinstance(item['상대인물'], str):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용[{idx}] > 상대인물'은 문자열이어야 합니다"

        if item['이전내용에서말의높임법'] not in ['존댓말', '반말', '없음']:
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용[{idx}] > 이전내용에서말의높임법'은 '존댓말', '반말', '없음' 중 하나여야 합니다"

        if item['현재말의높임법'] not in ['존댓말', '반말', '없음']:
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용[{idx}] > 현재말의높임법'은 '존댓말', '반말', '없음' 중 하나여야 합니다"

        if not isinstance(item['편집대화내용'], str):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용[{idx}] > 편집대화내용'은 문자열이어야 합니다"

        if not isinstance(item['편집이유'], str):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용[{idx}] > 편집이유'은 문자열이어야 합니다"

    # Error4: '대화내용' 리스트 개수 확인
    if len(OutputDic['대화내용']) != CheckCount['CheckCount']:
        return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용' 데이터 수가 ((기존대화문: {CheckCount['CheckCount']})) ((편집대화문: {len(OutputDic['대화내용'])})) 다릅니다"
    
    # Error5: '대화내용' 이름 리스트 확인
    for i, CharacterName in enumerate(CheckCount['CheckList']):
        if CharacterName != OutputDic['대화내용'][i]['인물']:
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화내용[{i}] > 인물'이 ((기존대화문: {CharacterName})) ((편집대화문: {OutputDic['대화내용'][i]['인물']}))와 다릅니다"
        
    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['대화내용']

## Process15: AuthorResearch의 Filter(Error 예외처리)
def AuthorResearchFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "AuthorResearch, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '작가정보' not in OutputDic:
        return "AuthorResearch, JSONKeyError: '작가정보' 키가 누락되었습니다"

    # Error3: '작가정보' 데이터 타입 검증
    if not isinstance(OutputDic['작가정보'], dict):
        return "AuthorResearch, JSON에서 오류 발생: '작가정보'는 딕셔너리 형태여야 합니다"

    required_keys = ['이름', '출생', '국적', '전공', '학위', '주요경력', '대표저서', '사상및영향력', '기타흥미로운요소서술', '저자소개']
    missing_keys = [key for key in required_keys if key not in OutputDic['작가정보']]
    if missing_keys:
        return f"AuthorResearch, JSONKeyError: '작가정보'에 누락된 키: {', '.join(missing_keys)}"

    item = OutputDic['작가정보']

    # 각 필드의 데이터 타입 검증
    if not isinstance(item['이름'], str):
        return "AuthorResearch, JSON에서 오류 발생: '이름'은 문자열이어야 합니다"

    if not isinstance(item['출생'], str):
        return "AuthorResearch, JSON에서 오류 발생: '출생'은 문자열이어야 합니다"
    
    if not isinstance(item['국적'], str):
        return "AuthorResearch, JSON에서 오류 발생: '국적'은 문자열이어야 합니다"

    if not isinstance(item['전공'], str):
        return "AuthorResearch, JSON에서 오류 발생: '전공'은 문자열이어야 합니다"

    if not isinstance(item['학위'], str):
        return "AuthorResearch, JSON에서 오류 발생: '학위'는 문자열이어야 합니다"

    if not isinstance(item['주요경력'], str):
        return "AuthorResearch, JSON에서 오류 발생: '주요경력'은 문자열이어야 합니다"

    if not isinstance(item['대표저서'], str):
        return "AuthorResearch, JSON에서 오류 발생: '대표저서'는 문자열이어야 합니다"

    if not isinstance(item['사상및영향력'], str):
        return "AuthorResearch, JSON에서 오류 발생: '사상및영향력'은 문자열이어야 합니다"

    if not isinstance(item['기타흥미로운요소서술'], str):
        return "AuthorResearch, JSON에서 오류 발생: '기타흥미로운요소서술'는 문자열이어야 합니다"
    
    if not isinstance(item['저자소개'], str):
        return "AuthorResearch, JSON에서 오류 발생: '저자소개'는 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['작가정보']

## Process16: TranslationCatchphrase의 Filter(Error 예외처리)
def TranslationCatchphraseFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "TranslationCatchphrase, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '도서카피모음' not in OutputDic:
        return "TranslationCatchphrase, JSONKeyError: '도서카피모음' 키가 누락되었습니다"

    # Error3: '도서카피모음' 데이터 타입 검증
    if not isinstance(OutputDic['도서카피모음'], dict):
        return "TranslationCatchphrase, JSON에서 오류 발생: '도서카피모음'은 딕셔너리 형태여야 합니다"

    required_keys = [
        '부제', '표지카피1', '표지카피2', '표지카피3', '띠지카피',
        '도서핵심메세지', '역자서문', '책소개', '출판사서평'
    ]
    missing_keys = [key for key in required_keys if key not in OutputDic['도서카피모음']]
    if missing_keys:
        return f"TranslationCatchphrase, JSONKeyError: '도서카피모음'에 누락된 키: {', '.join(missing_keys)}"

    item = OutputDic['도서카피모음']

    # 각 필드의 데이터 타입 검증
    if not isinstance(item['부제'], str) or len(item['부제']) > 40:
        return "TranslationCatchphrase, JSON에서 오류 발생: '부제'는 20자 내외의 문자열이어야 합니다"

    if not isinstance(item['표지카피1'], str) or len(item['표지카피1']) > 60:
        return "TranslationCatchphrase, JSON에서 오류 발생: '표지카피1'은 30자 내외의 문자열이어야 합니다"

    if not isinstance(item['표지카피2'], str) or len(item['표지카피2']) > 200:
        return "TranslationCatchphrase, JSON에서 오류 발생: '표지카피2'는 100자 내외의 문자열이어야 합니다"

    if not isinstance(item['표지카피3'], str) or len(item['표지카피3']) > 400:
        return "TranslationCatchphrase, JSON에서 오류 발생: '표지카피3'은 200자 내외의 문자열이어야 합니다"

    if not isinstance(item['띠지카피'], str) or len(item['띠지카피']) > 60:
        return "TranslationCatchphrase, JSON에서 오류 발생: '띠지카피'는 30자 내외의 문자열이어야 합니다"

    if not isinstance(item['도서핵심메세지'], str) or len(item['도서핵심메세지']) > 400:
        return "TranslationCatchphrase, JSON에서 오류 발생: '도서핵심메세지'는 200자 내외의 문자열이어야 합니다"

    if not isinstance(item['역자서문'], str) or len(item['역자서문']) > 5000:
        return "TranslationCatchphrase, JSON에서 오류 발생: '역자서문'은 2500자 내외의 문자열이어야 합니다"

    if not isinstance(item['책소개'], str) or len(item['책소개']) > 3000:
        return "TranslationCatchphrase, JSON에서 오류 발생: '책소개'는 1500자 내외의 문자열이어야 합니다"

    if not isinstance(item['출판사서평'], str) or len(item['출판사서평']) > 1600:
        return "TranslationCatchphrase, JSON에서 오류 발생: '출판사서평'은 800자 내외의 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['도서카피모음']

## Process17: TranslationFundingCatchphrase의 Filter(Error 예외처리)
def TranslationFundingCatchphraseFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "TranslationFundingCatchphrase, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '도서펀딩카피모음' not in OutputDic:
        return "TranslationFundingCatchphrase, JSONKeyError: '도서펀딩카피모음' 키가 누락되었습니다"

    # Error3: '도서펀딩카피모음' 데이터 타입 검증
    if not isinstance(OutputDic['도서펀딩카피모음'], dict):
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '도서펀딩카피모음'은 딕셔너리 형태여야 합니다"

    # Error4: 필수 키 확인
    required_keys = [
        '23자_메인타이틀', '7자_서브타이틀', '50자_프로젝트요약', '상세페이지타이틀',
        '상세페이지서브타이틀', '프로젝트소개', '도서소개', '에디션소개',
        '이런분들께추천합니다', '프로젝트일정', '선물설명'
    ]
    missing_keys = [key for key in required_keys if key not in OutputDic['도서펀딩카피모음']]
    if missing_keys:
        return f"TranslationFundingCatchphrase, JSONKeyError: '도서펀딩카피모음'에 누락된 키: {', '.join(missing_keys)}"

    item = OutputDic['도서펀딩카피모음']

    # 각 필드의 데이터 타입 및 길이 검증 (최대 길이는 '내외' 값의 약 2배로 설정)
    # 각 필드의 설명에 명시된 글자 수를 기준으로 최대 길이를 설정합니다.
    if not isinstance(item.get('23자_메인타이틀'), str) or len(item.get('23자_메인타이틀', '')) > 50: # 약 23 * 2 = 46 -> 50
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '23자_메인타이틀'은 23자 내외의 문자열이어야 합니다"

    if not isinstance(item.get('7자_서브타이틀'), str) or len(item.get('7자_서브타이틀', '')) > 20: # 약 7 * 2 = 14 -> 20
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '7자_서브타이틀'은 7자 내외의 문자열이어야 합니다"

    if not isinstance(item.get('50자_프로젝트요약'), str) or len(item.get('50자_프로젝트요약', '')) > 100: # 약 50 * 2 = 100
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '50자_프로젝트요약'은 50자 내외의 문자열이어야 합니다"

    if not isinstance(item.get('상세페이지타이틀'), str) or len(item.get('상세페이지타이틀', '')) > 100: # 50자 내외 -> 100
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '상세페이지타이틀'은 50자 내외의 문자열이어야 합니다"

    if not isinstance(item.get('상세페이지서브타이틀'), str) or len(item.get('상세페이지서브타이틀', '')) > 200: # 100자 내외 -> 200
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '상세페이지서브타이틀'은 100자 내외의 문자열이어야 합니다"

    if not isinstance(item.get('프로젝트소개'), str) or len(item.get('프로젝트소개', '')) > 1600: # 800자 내외 -> 1600
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '프로젝트소개'는 800자 내외의 문자열이어야 합니다"

    if not isinstance(item.get('도서소개'), str) or len(item.get('도서소개', '')) > 1600: # 800자 내외 -> 1600
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '도서소개'는 800자 내외의 문자열이어야 합니다"

    if not isinstance(item.get('에디션소개'), str) or len(item.get('에디션소개', '')) > 1600: # 800자 내외 -> 1600
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '에디션소개'는 800자 내외의 문자열이어야 합니다"

    # '이런분들께추천합니다'는 "5가지 이상"이라는 조건이 있지만, 여기서는 문자열 타입과 임의의 최대 길이만 검증합니다.
    if not isinstance(item.get('이런분들께추천합니다'), str) or len(item.get('이런분들께추천합니다', '')) > 1200: # 임의의 최대 길이 1200
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '이런분들께추천합니다'는 적절한 길이의 문자열이어야 합니다"

    # '프로젝트일정'은 "5개로 나누어 간략하게 작성" 조건이 있지만, 문자열 타입과 임의의 최대 길이만 검증합니다.
    if not isinstance(item.get('프로젝트일정'), str) or len(item.get('프로젝트일정', '')) > 500: # 임의의 최대 길이 500
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '프로젝트일정'은 적절한 길이의 문자열이어야 합니다"

    # '선물설명'은 "간략하게 작성" 조건이 있지만, 문자열 타입과 임의의 최대 길이만 검증합니다.
    if not isinstance(item.get('선물설명'), str) or len(item.get('선물설명', '')) > 500: # 임의의 최대 길이 500
        return "TranslationFundingCatchphrase, JSON에서 오류 발생: '선물설명'은 적절한 길이의 문자열이어야 합니다"

    # 모든 조건을 만족하면 '도서펀딩카피모음' 딕셔너리 반환
    return OutputDic['도서펀딩카피모음']

#######################
##### Process 응답 #####
#######################
## Process LLMResponse 함수
def ProcessResponse(projectName, email, Process, Input, InputCount, TotalInputCount, FilterFunc, CheckCount, LLM, mode, MessagesReview, input2 = "", memoryNote = ""):
    ErrorCount = 0
    while True:
        if LLM == "OpenAI":
            Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, Input, InputCount, Mode = mode, Input2 = input2, MemoryNote = memoryNote, messagesReview = MessagesReview)
        elif LLM == "Anthropic":
            Response, Usage, Model = ANTHROPIC_LLMresponse(projectName, email, Process, Input, InputCount, Mode = mode, Input2 = input2, MemoryNote = memoryNote, messagesReview = MessagesReview)
        elif LLM == "Google":
            Response, Usage, Model = GOOGLE_LLMresponse(projectName, email, Process, Input, InputCount, Mode = mode, Input2 = input2, MemoryNote = memoryNote, messagesReview = MessagesReview)
        elif LLM == "DeepSeek":
            Response, Usage, Model = DEEPSEEK_LLMresponse(projectName, email, Process, Input, InputCount, Mode = mode, Input2 = input2, MemoryNote = memoryNote, messagesReview = MessagesReview)
        Filter = FilterFunc(Response, CheckCount)
            
        
        if isinstance(Filter, str):
            print(f"Project: {projectName} | Process: {Process} {InputCount}/{TotalInputCount} | {Filter}")
            ErrorCount += 1
            print(f"Project: {projectName} | Process: {Process} {InputCount}/{TotalInputCount} | "
                f"오류횟수 {ErrorCount}회, 10초 후 프롬프트 재시도")
            
            ## Error 3회시 해당 프로세스 사용 안함 예외처리
            if Process in ['TranslationProofreading'] and ErrorCount >= 3:
                print(f"Project: {projectName} | Process: {Process} {InputCount}/{TotalInputCount} | ErrorPass 완료")
                return "ErrorPass"
            
            if ErrorCount >= 10:
                sys.exit(f"Project: {projectName} | Process: {Process} {InputCount}/{TotalInputCount} | 오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
            time.sleep(10)
            continue
        
        print(f"Project: {projectName} | Process: {Process} {InputCount}/{TotalInputCount} | JSONDecode 완료")
        return Filter

##################################
##### ProcessResponse 업데이트 #####
##################################
## Process DataFrame Completion 및 InputCount 확인
def ProcessDataFrameCheck(ProjectDataFramePath):
    ## DataFrameCompletion 초기화
    DataFrameCompletion = 'No'
    ## InputCount 초기화
    InputCount = 1 
    if not os.path.exists(ProjectDataFramePath):
        return InputCount, DataFrameCompletion
    else:
        ## Process Edit 불러오기
        with open(ProjectDataFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
            TranslationEditFrame = json.load(DataFrameJson)
        
        ## InputCount 및 DataFrameCompletion 확인
        NextInputCount = TranslationEditFrame[0]['InputCount'] + 1
        DataFrameCompletion = TranslationEditFrame[0]['Completion']
        
        return NextInputCount, DataFrameCompletion

## Process1: TranslationIndexDefineProcess DataFrame 저장
def TranslationIndexDefineProcessDataFrameSave(ProjectName, MainLang, TranslationDataFramePath, ProjectDataFrameTranslationIndexDefinePath, TranslationIndexDefineResponse, Process, InputCount, TotalInputCount):
    ## TranslationIndexDefineFrame 불러오기
    if os.path.exists(ProjectDataFrameTranslationIndexDefinePath):
        TranslationIndexDefineFramePath = ProjectDataFrameTranslationIndexDefinePath
    else:
        TranslationIndexDefineFramePath = os.path.join(TranslationDataFramePath, "a232-01_TranslationIndexFrame.json")
    with open(TranslationIndexDefineFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationIndexDefineFrame = json.load(DataFrameJson)
        
    ## TranslationIndexDefineFrame 업데이트
    TranslationIndexDefineFrame[0]['ProjectName'] = ProjectName
    TranslationIndexDefineFrame[0]['MainLang'] = MainLang.capitalize()
    TranslationIndexDefineFrame[0]['Translation'] = TranslationIndexDefineResponse['언어태그'].capitalize()
    TranslationIndexDefineFrame[0]['TaskName'] = Process
    
    ## TranslationIndexDefineFrame 첫번째 데이터 프레임 복사
    for Response in TranslationIndexDefineResponse['목차리스트']:
        TranslationIndexDefine = TranslationIndexDefineFrame[1][0].copy()
        TranslationIndexDefine['IndexId'] = Response['번호']
        TranslationIndexDefine['IndexTag'] = Response['목차태그']
        TranslationIndexDefine['Index'] = Response['목차']
        
        ## TranslationIndexDefineFrame 데이터 프레임 업데이트
        TranslationIndexDefineFrame[1].append(TranslationIndexDefine)

    ## TranslationIndexDefineFrame ProcessCount 및 Completion 업데이트
    TranslationIndexDefineFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        TranslationIndexDefineFrame[0]['Completion'] = 'Yes'
        
    ## TranslationIndexDefineFrame 저장
    with open(ProjectDataFrameTranslationIndexDefinePath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TranslationIndexDefineFrame, DataFrameJson, indent = 4, ensure_ascii = False)
        
## Process1: TranslationBodySplitProcess DataFrame 저장
def TranslationBodySplitProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationBodySplitPath, TranslationBodySplitResult, Process, InputCount, TotalInputCount):
    ## TranslationBodySplitFrame 불러오기
    if not os.path.exists(ProjectDataFrameTranslationBodySplitPath):
        TranslationBodySplitFramePath = os.path.join(TranslationDataFramePath, "a232-01_TranslationBodySplitFrame.json")
        with open(TranslationBodySplitFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
            TranslationBodySplitFrame = json.load(DataFrameJson)
            
        ## TranslationBodySplitFrame 업데이트
        TranslationBodySplitFrame[0]['ProjectName'] = ProjectName
        TranslationBodySplitFrame[0]['MainLang'] = MainLang.capitalize()
        TranslationBodySplitFrame[0]['Translation'] = Translation.capitalize()
        TranslationBodySplitFrame[0]['TaskName'] = Process
        
        ## TranslationBodySplitFrame 데이터 프레임 업데이트
        TranslationBodySplitFrame[1] += TranslationBodySplitResult

        ## TranslationBodySplitFrame ProcessCount 및 Completion 업데이트
        TranslationBodySplitFrame[0]['InputCount'] = InputCount
        if InputCount == TotalInputCount:
            TranslationBodySplitFrame[0]['Completion'] = 'Yes'
            
        ## TranslationBodySplitFrame 저장
        with open(ProjectDataFrameTranslationBodySplitPath, 'w', encoding = 'utf-8') as DataFrameJson:
            json.dump(TranslationBodySplitFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process2: TranslationBodySummaryProcess DataFrame 저장
def TranslationBodySummaryProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationBodySummaryPath, TranslationBodySummaryResponse, Process, InputCount, IndexId, TotalInputCount):
    ## TranslationBodySummaryFrame 불러오기
    if os.path.exists(ProjectDataFrameTranslationBodySummaryPath):
        TranslationBodySummaryFramePath = ProjectDataFrameTranslationBodySummaryPath
    else:
        TranslationBodySummaryFramePath = os.path.join(TranslationDataFramePath, "a232-02_TranslationBodySummaryFrame.json")
    with open(TranslationBodySummaryFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationBodySummaryFrame = json.load(DataFrameJson)
        
    ## TranslationBodySummaryFrame 업데이트
    TranslationBodySummaryFrame[0]['ProjectName'] = ProjectName
    TranslationBodySummaryFrame[0]['MainLang'] = MainLang.capitalize()
    TranslationBodySummaryFrame[0]['Translation'] = Translation.capitalize()
    TranslationBodySummaryFrame[0]['TaskName'] = Process
    
    ## TranslationBodySummaryFrame 첫번째 데이터 프레임 복사
    TranslationBodySummary = TranslationBodySummaryFrame[1][0].copy()

    TranslationBodySummary['IndexId'] = IndexId
    TranslationBodySummary['BodyId'] = InputCount
    TranslationBodySummary['MainText'] = TranslationBodySummaryResponse['핵심문구']
    TranslationBodySummary['BodySummary'] = TranslationBodySummaryResponse['요약']

    ## TranslationBodySummaryFrame 데이터 프레임 업데이트
    TranslationBodySummaryFrame[1].append(TranslationBodySummary)
        
    ## TranslationBodySummaryFrame ProcessCount 및 Completion 업데이트
    TranslationBodySummaryFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        TranslationBodySummaryFrame[0]['Completion'] = 'Yes'
        
    ## TranslationBodySummaryFrame 저장
    with open(ProjectDataFrameTranslationBodySummaryPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TranslationBodySummaryFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process3: WordListGenProcess DataFrame 저장
def WordListGenProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameWordListGenPath, WordListGenResponse, Process, InputCount, IndexId, TotalInputCount):
    ## WordListGenFrame 불러오기
    if os.path.exists(ProjectDataFrameWordListGenPath):
        WordListGenFramePath = ProjectDataFrameWordListGenPath
    else:
        WordListGenFramePath = os.path.join(TranslationDataFramePath, "a232-03_WordListGenFrame.json")
    with open(WordListGenFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        WordListGenFrame = json.load(DataFrameJson)
        
    ## WordListGenFrame 업데이트
    WordListGenFrame[0]['ProjectName'] = ProjectName
    WordListGenFrame[0]['MainLang'] = MainLang.capitalize()
    WordListGenFrame[0]['Translation'] = Translation.capitalize()
    WordListGenFrame[0]['TaskName'] = Process
    
    for Response in WordListGenResponse:
        ## WordListGenFrame 첫번째 데이터 프레임 복사
        WordListGen = WordListGenFrame[1][0].copy()
        WordListGen['IndexId'] = IndexId
        WordListGen['BodyId'] = InputCount
        WordListGen['WordId'] = Response['번호']
        WordListGen['Word'] = Response['원문']
        WordListGen['Translation'] = Response['번역']
        WordListGen['Reason'] = Response['선택이유']

        ## WordListGenFrame 데이터 프레임 업데이트
        WordListGenFrame[1].append(WordListGen)
        
    ## WordListGenFrame ProcessCount 및 Completion 업데이트
    WordListGenFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        WordListGenFrame[0]['Completion'] = 'Yes'
        
    ## WordListGenFrame 저장
    with open(ProjectDataFrameWordListGenPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(WordListGenFrame, DataFrameJson, indent = 4, ensure_ascii = False)
        
## Process4: UniqueWordListGenProcess DataFrame 저장
def UniqueWordListGenProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameUniqueWordListGenPath, UniqueWordListGenResponse, Process, InputCount, IndexId, TotalInputCount):
    ## UniqueWordListGenFrame 불러오기
    if os.path.exists(ProjectDataFrameUniqueWordListGenPath):
        UniqueWordListGenFramePath = ProjectDataFrameUniqueWordListGenPath
    else:
        UniqueWordListGenFramePath = os.path.join(TranslationDataFramePath, "a232-04_UniqueWordListGenFrame.json")
    with open(UniqueWordListGenFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        UniqueWordListGenFrame = json.load(DataFrameJson)
        
    ## UniqueWordListGenFrame 업데이트
    UniqueWordListGenFrame[0]['ProjectName'] = ProjectName
    UniqueWordListGenFrame[0]['MainLang'] = MainLang.capitalize()
    UniqueWordListGenFrame[0]['Translation'] = Translation.capitalize()
    UniqueWordListGenFrame[0]['TaskName'] = Process
    
    for Response in UniqueWordListGenResponse:
        ## UniqueWordListGenFrame 첫번째 데이터 프레임 복사
        UniqueWordListGen = UniqueWordListGenFrame[1][0].copy()
        UniqueWordListGen['IndexId'] = IndexId
        UniqueWordListGen['BodyId'] = InputCount
        UniqueWordListGen['WordId'] = Response['번호']
        UniqueWordListGen['Word'] = Response['원문']
        UniqueWordListGen['Translation'] = Response['번역']
        UniqueWordListGen['Reason'] = Response['선택이유']

        ## UniqueWordListGenFrame 데이터 프레임 업데이트
        UniqueWordListGenFrame[1].append(UniqueWordListGen)
        
    ## UniqueWordListGenFrame ProcessCount 및 Completion 업데이트
    UniqueWordListGenFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        UniqueWordListGenFrame[0]['Completion'] = 'Yes'
        
    ## UniqueWordListGenFrame 저장
    with open(ProjectDataFrameUniqueWordListGenPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(UniqueWordListGenFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process5: WordListPostprocessingProcess DataFrame 저장
def WordListPostprocessingProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameWordListPostprocessingPath, WordListPostprocessingResponse, Process, InputCount, IndexId, TotalInputCount):
    ## WordListPostprocessingFrame 불러오기
    if os.path.exists(ProjectDataFrameWordListPostprocessingPath):
        WordListPostprocessingFramePath = ProjectDataFrameWordListPostprocessingPath
    else:
        WordListPostprocessingFramePath = os.path.join(TranslationDataFramePath, "a232-05_WordListPostprocessingFrame.json")
    with open(WordListPostprocessingFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        WordListPostprocessingFrame = json.load(DataFrameJson)

    ## WordListPostprocessingFrame 업데이트
    WordListPostprocessingFrame[0]['ProjectName'] = ProjectName
    WordListPostprocessingFrame[0]['MainLang'] = MainLang.capitalize()
    WordListPostprocessingFrame[0]['Translation'] = Translation.capitalize()
    WordListPostprocessingFrame[0]['TaskName'] = Process
    
    for Response in WordListPostprocessingResponse:
        if Response['정리방법'] != '삭제':
            ## WordListPostprocessingFrame 첫번째 데이터 프레임 복사
            WordListPostprocessing = WordListPostprocessingFrame[1][0].copy()
            WordListPostprocessing['IndexId'] = IndexId
            WordListPostprocessing['BodyId'] = InputCount
            WordListPostprocessing['WordId'] = Response['번호']
            WordListPostprocessing['Word'] = Response['원문']
            WordListPostprocessing['Translation'] = Response['번역']
            WordListPostprocessing['Processing'] = Response['정리방법']

            ## WordListPostprocessingFrame 데이터 프레임 업데이트
            WordListPostprocessingFrame[1].append(WordListPostprocessing)
        
    ## WordListPostprocessingFrame ProcessCount 및 Completion 업데이트
    WordListPostprocessingFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        WordListPostprocessingFrame[0]['Completion'] = 'Yes'
        
    ## WordListPostprocessingFrame 저장
    with open(ProjectDataFrameWordListPostprocessingPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(WordListPostprocessingFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process6: IndexTranslationProcess DataFrame 저장
def IndexTranslationProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameIndexTranslationPath, IndexTranslationResponse, Process, InputCount, IndexId, IndexTag, TotalInputCount):
    ## IndexTranslationFrame 불러오기
    if os.path.exists(ProjectDataFrameIndexTranslationPath):
        IndexTranslationFramePath = ProjectDataFrameIndexTranslationPath
    else:
        IndexTranslationFramePath = os.path.join(TranslationDataFramePath, "a232-06_IndexTranslationFrame.json")
    with open(IndexTranslationFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        IndexTranslationFrame = json.load(DataFrameJson)
        
    ## IndexTranslationFrame 업데이트
    IndexTranslationFrame[0]['ProjectName'] = ProjectName
    IndexTranslationFrame[0]['MainLang'] = MainLang.capitalize()
    IndexTranslationFrame[0]['Translation'] = Translation.capitalize()
    IndexTranslationFrame[0]['TaskName'] = Process
    

    ## IndexTranslationFrame 첫번째 데이터 프레임 복사
    IndexTranslation = IndexTranslationFrame[1][0].copy()
    IndexTranslation['IndexId'] = IndexId
    IndexTranslation['IndexTag'] = IndexTag
    IndexTranslation['Index'] = IndexTranslationResponse['현재목차원문'] if IndexTranslationResponse['현재목차원문'].startswith('<') and IndexTranslationResponse['현재목차원문'].endswith('>') else f"<{IndexTranslationResponse['현재목차원문']}>".replace("<<", "<").replace(">>", ">")
    IndexTranslation['IndexTranslation'] = IndexTranslationResponse['현재목차번역'] if IndexTranslationResponse['현재목차번역'].startswith('<') and IndexTranslationResponse['현재목차번역'].endswith('>') else f"<{IndexTranslationResponse['현재목차번역']}>".replace("<<", "<").replace(">>", ">")
    IndexTranslation['Reason'] = IndexTranslationResponse['번역이유']

    ## IndexTranslationFrame 데이터 프레임 업데이트
    IndexTranslationFrame[1].append(IndexTranslation)
        
    ## IndexTranslationFrame ProcessCount 및 Completion 업데이트
    IndexTranslationFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        IndexTranslationFrame[0]['Completion'] = 'Yes'
        
    ## IndexTranslationFrame 저장
    with open(ProjectDataFrameIndexTranslationPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(IndexTranslationFrame, DataFrameJson, indent = 4, ensure_ascii = False)
        
## Process7: BodyTranslationPreprocessingProcess DataFrame 저장
def BodyTranslationPreprocessingProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameBodyTranslationPreprocessingPath, BodyTranslationPreprocessingResponse, Process, InputCount, IndexId, IndexTag, Index, BodyId, TranslationBody, TotalInputCount):
    ## BodyTranslationPreprocessingFrame 불러오기
    if os.path.exists(ProjectDataFrameBodyTranslationPreprocessingPath):
        BodyTranslationPreprocessingFramePath = ProjectDataFrameBodyTranslationPreprocessingPath
    else:
        BodyTranslationPreprocessingFramePath = os.path.join(TranslationDataFramePath, "a232-07_BodyTranslationPreprocessingFrame.json")
    with open(BodyTranslationPreprocessingFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        BodyTranslationPreprocessingFrame = json.load(DataFrameJson)
        
    ## BodyTranslationPreprocessingFrame 업데이트
    BodyTranslationPreprocessingFrame[0]['ProjectName'] = ProjectName
    BodyTranslationPreprocessingFrame[0]['MainLang'] = MainLang.capitalize()
    BodyTranslationPreprocessingFrame[0]['Translation'] = Translation.capitalize()
    BodyTranslationPreprocessingFrame[0]['TaskName'] = Process
    
    ## 번역 Index 추출
    
    ## WordList를 통해 Body 다시 복구
    TranslationWordsList = BodyTranslationPreprocessingResponse
    if TranslationWordsList != []:
        for TranslationWord in TranslationWordsList:
            TranslationWordId = TranslationWord['번호']
            OriginalWord = TranslationWord['원단어']
            ModifiedWord = TranslationWord['수정된번역단어']
            Pattern = r'(\{' + str(TranslationWordId) + r':\s*.+?\s*->\s*.+?\})'
            Match = re.search(Pattern, TranslationBody)
            if Match:
                TranslationBody = TranslationBody.replace(Match.group(0), f'{{{OriginalWord}->{ModifiedWord}}}')
    # 추가 코드 - 남아 있는 모든 {n: ...->...}를 {...->...}로 처리
    TranslationBody = re.sub(r'\{\d+:\s*', '{', TranslationBody)
    # 번역 단어가 비어있는 경우 {원단어->}를 원단어만 남기도록 처리
    TranslationBody = re.sub(r'\{([^{}]+?)->\}', r'\1', TranslationBody)

    ## BodyTranslationPreprocessingFrame 첫번째 데이터 프레임 복사
    BodyTranslationPreprocessing = BodyTranslationPreprocessingFrame[1][0].copy()
    BodyTranslationPreprocessing['IndexId'] = IndexId
    BodyTranslationPreprocessing['IndexTag'] = IndexTag
    BodyTranslationPreprocessing['Index'] = Index
    BodyTranslationPreprocessing['BodyId'] = BodyId
    BodyTranslationPreprocessing['Body'] = TranslationBody
    ModifiedWord = []
    if TranslationWordsList != []:
        for TranslationWord in TranslationWordsList:
            ModifiedWord.append({"WordId": TranslationWord['번호'], "Word": TranslationWord['원단어'], "Translation": TranslationWord['수정된번역단어'], "Reason": TranslationWord['수정이유']})
    BodyTranslationPreprocessing['ModifiedWord'] = ModifiedWord

    ## BodyTranslationPreprocessingFrame 데이터 프레임 업데이트
    BodyTranslationPreprocessingFrame[1].append(BodyTranslationPreprocessing)
        
    ## BodyTranslationPreprocessingFrame ProcessCount 및 Completion 업데이트
    BodyTranslationPreprocessingFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        BodyTranslationPreprocessingFrame[0]['Completion'] = 'Yes'
        
    ## BodyTranslationPreprocessingFrame 저장
    with open(ProjectDataFrameBodyTranslationPreprocessingPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(BodyTranslationPreprocessingFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process8: BodyTranslationProcess DataFrame 저장
def BodyTranslationProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameBodyTranslationPath, BodyTranslationResponse, BodyTranslationCheckResponse, Process, InputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount):
    ## BodyTranslationFrame 불러오기
    if os.path.exists(ProjectDataFrameBodyTranslationPath):
        BodyTranslationFramePath = ProjectDataFrameBodyTranslationPath
    else:
        BodyTranslationFramePath = os.path.join(TranslationDataFramePath, "a232-08_BodyTranslationFrame.json")
    with open(BodyTranslationFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        BodyTranslationFrame = json.load(DataFrameJson)
        
    ## BodyTranslationFrame 업데이트
    BodyTranslationFrame[0]['ProjectName'] = ProjectName
    BodyTranslationFrame[0]['MainLang'] = MainLang.capitalize()
    BodyTranslationFrame[0]['Translation'] = Translation.capitalize()
    BodyTranslationFrame[0]['TaskName'] = Process
    
    ## BodyTranslationFrame 첫번째 데이터 프레임 복사
    BodyTranslation = BodyTranslationFrame[1][0].copy()
    BodyTranslation['IndexId'] = IndexId
    BodyTranslation['IndexTag'] = IndexTag
    BodyTranslation['Index'] = Index
    BodyTranslation['BodyId'] = BodyId
    BodyTranslation['Body'] = re.sub(r'\{[^{}]*->([^{}]*)\}', r'\1', BodyTranslationResponse['번역문']).replace('{', '').replace('}', '').replace('(원어: ', '(').replace('(원어:', '(')
    BodyTranslation['Tone'] = BodyTranslationCheckResponse['현재도서내용어조']

    ## BodyTranslationFrame 데이터 프레임 업데이트
    BodyTranslationFrame[1].append(BodyTranslation)
        
    ## BodyTranslationFrame ProcessCount 및 Completion 업데이트
    BodyTranslationFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        BodyTranslationFrame[0]['Completion'] = 'Yes'
        
    ## BodyTranslationFrame 저장
    with open(ProjectDataFrameBodyTranslationPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(BodyTranslationFrame, DataFrameJson, indent = 4, ensure_ascii = False)
    
    return BodyTranslation['Body']

## Process9: TranslationEditingProcess DataFrame 저장
def TranslationEditingProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationEditingPath, TranslationEditingResponse, BodyTranslationCheckResponse, Process, InputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount):
    ## TranslationEditingFrame 불러오기
    if os.path.exists(ProjectDataFrameTranslationEditingPath):
        TranslationEditingFramePath = ProjectDataFrameTranslationEditingPath
    else:
        TranslationEditingFramePath = os.path.join(TranslationDataFramePath, "a232-09_TranslationEditingFrame.json")
    with open(TranslationEditingFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationEditingFrame = json.load(DataFrameJson)
        
    ## TranslationEditingFrame 업데이트
    TranslationEditingFrame[0]['ProjectName'] = ProjectName
    TranslationEditingFrame[0]['MainLang'] = MainLang.capitalize()
    TranslationEditingFrame[0]['Translation'] = Translation.capitalize()
    TranslationEditingFrame[0]['TaskName'] = Process
    
    ## TranslationEditingFrame 첫번째 데이터 프레임 복사
    TranslationEditing = TranslationEditingFrame[1][0].copy()
    TranslationEditing['IndexId'] = IndexId
    TranslationEditing['IndexTag'] = IndexTag
    TranslationEditing['Index'] = Index
    TranslationEditing['BodyId'] = BodyId
    TranslationEditing['Body'] = TranslationEditingResponse['내용'].replace('{', '').replace('}', '')
    TranslationEditing['Tone'] = BodyTranslationCheckResponse['현재도서내용어조']    

    ## TranslationEditingFrame 데이터 프레임 업데이트
    TranslationEditingFrame[1].append(TranslationEditing)
        
    ## TranslationEditingFrame ProcessCount 및 Completion 업데이트
    TranslationEditingFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        TranslationEditingFrame[0]['Completion'] = 'Yes'
        
    ## TranslationEditingFrame 저장
    with open(ProjectDataFrameTranslationEditingPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TranslationEditingFrame, DataFrameJson, indent = 4, ensure_ascii = False)
        
    return TranslationEditing['Body']

## Process9: TranslationRefinementProcess DataFrame 저장
def TranslationRefinementProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationRefinementPath, TranslationRefinementResponse, BodyTranslationCheckResponse, Process, InputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount):
    ## TranslationRefinementFrame 불러오기
    if os.path.exists(ProjectDataFrameTranslationRefinementPath):
        TranslationRefinementFramePath = ProjectDataFrameTranslationRefinementPath
    else:
        TranslationRefinementFramePath = os.path.join(TranslationDataFramePath, "a232-09_TranslationRefinementFrame.json")
    with open(TranslationRefinementFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationRefinementFrame = json.load(DataFrameJson)
        
    ## TranslationRefinementFrame 업데이트
    TranslationRefinementFrame[0]['ProjectName'] = ProjectName
    TranslationRefinementFrame[0]['MainLang'] = MainLang.capitalize()
    TranslationRefinementFrame[0]['Translation'] = Translation.capitalize()
    TranslationRefinementFrame[0]['TaskName'] = Process
    
    ## TranslationRefinementFrame 첫번째 데이터 프레임 복사
    TranslationRefinement = TranslationRefinementFrame[1][0].copy()
    TranslationRefinement['IndexId'] = IndexId
    TranslationRefinement['IndexTag'] = IndexTag
    TranslationRefinement['Index'] = Index
    TranslationRefinement['BodyId'] = BodyId
    TranslationRefinement['Body'] = TranslationRefinementResponse['내용'].replace('{', '').replace('}', '')
    TranslationRefinement['Tone'] = BodyTranslationCheckResponse['현재도서내용어조']    

    ## TranslationRefinementFrame 데이터 프레임 업데이트
    TranslationRefinementFrame[1].append(TranslationRefinement)
        
    ## TranslationRefinementFrame ProcessCount 및 Completion 업데이트
    TranslationRefinementFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        TranslationRefinementFrame[0]['Completion'] = 'Yes'
        
    ## TranslationRefinementFrame 저장
    with open(ProjectDataFrameTranslationRefinementPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TranslationRefinementFrame, DataFrameJson, indent = 4, ensure_ascii = False)
        
    return TranslationRefinement['Body']

## Process9: TranslationKinfolkStyleRefinementProcess DataFrame 저장
def TranslationKinfolkStyleRefinementProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationKinfolkStyleRefinementPath, TranslationKinfolkStyleRefinementResponse, BodyTranslationCheckResponse, Process, InputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount):
    ## TranslationKinfolkStyleRefinementFrame 불러오기
    if os.path.exists(ProjectDataFrameTranslationKinfolkStyleRefinementPath):
        TranslationKinfolkStyleRefinementFramePath = ProjectDataFrameTranslationKinfolkStyleRefinementPath
    else:
        TranslationKinfolkStyleRefinementFramePath = os.path.join(TranslationDataFramePath, "a232-09_TranslationKinfolkStyleRefinementFrame.json")
    with open(TranslationKinfolkStyleRefinementFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationKinfolkStyleRefinementFrame = json.load(DataFrameJson)
        
    ## TranslationKinfolkStyleRefinementFrame 업데이트
    TranslationKinfolkStyleRefinementFrame[0]['ProjectName'] = ProjectName
    TranslationKinfolkStyleRefinementFrame[0]['MainLang'] = MainLang.capitalize()
    TranslationKinfolkStyleRefinementFrame[0]['Translation'] = Translation.capitalize()
    TranslationKinfolkStyleRefinementFrame[0]['TaskName'] = Process
    
    ## TranslationKinfolkStyleRefinementFrame 첫번째 데이터 프레임 복사
    TranslationKinfolkStyleRefinement = TranslationKinfolkStyleRefinementFrame[1][0].copy()
    TranslationKinfolkStyleRefinement['IndexId'] = IndexId
    TranslationKinfolkStyleRefinement['IndexTag'] = IndexTag
    TranslationKinfolkStyleRefinement['Index'] = Index
    TranslationKinfolkStyleRefinement['BodyId'] = BodyId
    TranslationKinfolkStyleRefinement['Body'] = TranslationKinfolkStyleRefinementResponse['내용'].replace('{', '').replace('}', '')
    TranslationKinfolkStyleRefinement['Tone'] = BodyTranslationCheckResponse['현재도서내용어조']    

    ## TranslationKinfolkStyleRefinementFrame 데이터 프레임 업데이트
    TranslationKinfolkStyleRefinementFrame[1].append(TranslationKinfolkStyleRefinement)
        
    ## TranslationKinfolkStyleRefinementFrame ProcessCount 및 Completion 업데이트
    TranslationKinfolkStyleRefinementFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        TranslationKinfolkStyleRefinementFrame[0]['Completion'] = 'Yes'
        
    ## TranslationKinfolkStyleRefinementFrame 저장
    with open(ProjectDataFrameTranslationKinfolkStyleRefinementPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TranslationKinfolkStyleRefinementFrame, DataFrameJson, indent = 4, ensure_ascii = False)
        
    return TranslationKinfolkStyleRefinement['Body']

## Process10: TranslationProofreadingProcess DataFrame 저장
def TranslationProofreadingProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationProofreadingPath, TranslationProofreadingResponse, Process, InputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount):
    ## TranslationProofreadingFrame 불러오기
    if os.path.exists(ProjectDataFrameTranslationProofreadingPath):
        TranslationProofreadingFramePath = ProjectDataFrameTranslationProofreadingPath
    else:
        TranslationProofreadingFramePath = os.path.join(TranslationDataFramePath, "a232-10_TranslationProofreadingFrame.json")
    with open(TranslationProofreadingFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationProofreadingFrame = json.load(DataFrameJson)
        
    ## TranslationProofreadingFrame 업데이트
    TranslationProofreadingFrame[0]['ProjectName'] = ProjectName
    TranslationProofreadingFrame[0]['MainLang'] = MainLang.capitalize()
    TranslationProofreadingFrame[0]['Translation'] = Translation.capitalize()
    TranslationProofreadingFrame[0]['TaskName'] = Process
    
    ## TranslationProofreadingFrame 첫번째 데이터 프레임 복사
    TranslationProofreading = TranslationProofreadingFrame[1][0].copy()
    TranslationProofreading['IndexId'] = IndexId
    TranslationProofreading['IndexTag'] = IndexTag
    TranslationProofreading['Index'] = Index
    TranslationProofreading['BodyId'] = BodyId
    TranslationProofreading['Body'] = TranslationProofreadingResponse['도서내용'].replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'").replace('{', '').replace('}', '')

    ## TranslationProofreadingFrame 데이터 프레임 업데이트
    TranslationProofreadingFrame[1].append(TranslationProofreading)
        
    ## TranslationProofreadingFrame ProcessCount 및 Completion 업데이트
    TranslationProofreadingFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        
        ## InputList 위에서 분할한 Body를 다시 합치기
        NewTranslationProofreadingFrame = []
        TempTranslationProofreadingDic = {}
        for TranslationProofreading in TranslationProofreadingFrame[1]:
            bodyId = TranslationProofreading["BodyId"]
            # 새로운 BodyId인 경우 딕셔너리에 저장
            if bodyId not in TempTranslationProofreadingDic:
                TempTranslationProofreadingDic[bodyId] = TranslationProofreading.copy()
            # 기존 BodyId인 경우 Body 내용만 추가
            else:
                TempTranslationProofreadingDic[bodyId]["Body"] += TranslationProofreading["Body"]

        # 정렬된 결과를 새 리스트에 추가
        for bodyId in sorted(TempTranslationProofreadingDic.keys()):
            NewTranslationProofreadingFrame.append(TempTranslationProofreadingDic[bodyId])
            TranslationProofreadingFrame[1] = NewTranslationProofreadingFrame
            
        TranslationProofreadingFrame[0]['Completion'] = 'Yes'
        
    ## TranslationProofreadingFrame 저장
    with open(ProjectDataFrameTranslationProofreadingPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TranslationProofreadingFrame, DataFrameJson, indent = 4, ensure_ascii = False)
        
    return TranslationProofreading['Body']

## Process11: TranslationDialogueAnalysis DataFrame 저장
def TranslationDialogueAnalysisProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationDialogueAnalysisPath, MarkBody, TranslationDialogueAnalysisResponse, Process, InputCount, BodyId, Body, TotalInputCount):
    if os.path.exists(ProjectDataFrameTranslationDialogueAnalysisPath):
        TranslationDialogueAnalysisFramePath = ProjectDataFrameTranslationDialogueAnalysisPath
    else:
        TranslationDialogueAnalysisFramePath = os.path.join(TranslationDataFramePath, "a232-11_TranslationDialogueAnalysisFrame.json")
    with open(TranslationDialogueAnalysisFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationDialogueAnalysisFrame = json.load(DataFrameJson)

    ## TranslationDialogueAnalysisFrame 업데이트
    TranslationDialogueAnalysisFrame[0]['ProjectName'] = ProjectName
    TranslationDialogueAnalysisFrame[0]['MainLang'] = MainLang.capitalize()
    TranslationDialogueAnalysisFrame[0]['Translation'] = Translation.capitalize()
    TranslationDialogueAnalysisFrame[0]['TaskName'] = Process
    
    ## TranslationDialogueAnalysisFrame 첫번째 데이터 프레임 복사
    TranslationDialogueAnalysis = TranslationDialogueAnalysisFrame[1][0].copy()
    TranslationDialogueAnalysis['BodyId'] = BodyId

    # DialogueBody에서 {n 대화: 대화내용} -> 편집대화내용으로 변경
    DialogueBody = MarkBody
    BodyCharacterList = []
    for TranslationDialogue in TranslationDialogueAnalysisResponse:
        TranslationDialogueId = TranslationDialogue['번호']
        TranslationDialogueExistenceOrNot = TranslationDialogue['대화문여부']
        SameCharacterExistenceOrNot = TranslationDialogue['동일인물존재여부']
        CharacterId = TranslationDialogue['인물번호']
        TranslationDialogueName = TranslationDialogue['인물이름']
        TranslationDialogueRole = TranslationDialogue['역할']
        TranslationDialogueGender = TranslationDialogue['성별']
        TranslationDialogueAge = TranslationDialogue['연령']
        
        ## 대화문이 맞는 경우
        if TranslationDialogueExistenceOrNot == '맞음':
            DialogueBody = DialogueBody.replace(f"{{{TranslationDialogueId} 대화: ", f"{{{TranslationDialogueName}: ")
            Body = Body.replace(f"{{{TranslationDialogueId} 대화: ", f"{{{TranslationDialogueName}: ")
            ## 동일인물이 있는 경우
            SameCharacterExistenceOrNotCheck = False
            for i in range(len(TranslationDialogueAnalysisFrame[2])):
                if TranslationDialogueAnalysisFrame[2][i]['CharacterId'] == CharacterId or TranslationDialogueAnalysisFrame[2][i]['CharacterName'] == TranslationDialogueName:
                    if isinstance(CharacterId, int):
                        TranslationDialogueAnalysisFrame[2][i]['CharacterId'] = CharacterId
                    TranslationDialogueAnalysisFrame[2][i]['CharacterName'] = TranslationDialogueName
                    TranslationDialogueAnalysisFrame[2][i]['CharacterRole'] = TranslationDialogueRole
                    TranslationDialogueAnalysisFrame[2][i]['CharacterGender'] = TranslationDialogueGender
                    TranslationDialogueAnalysisFrame[2][i]['CharacterAge'] = TranslationDialogueAge
                    SameCharacterExistenceOrNotCheck = True
            ## 동일인물이 없는 경우
            if not SameCharacterExistenceOrNotCheck:
                NewCharacterId = len(TranslationDialogueAnalysisFrame[2])
                TranslationDialogueAnalysisFrame[2].append({'CharacterId': NewCharacterId, 'CharacterName': TranslationDialogueName, 'CharacterRole': TranslationDialogueRole, 'CharacterGender': TranslationDialogueGender, 'CharacterAge': TranslationDialogueAge})
            BodyCharacterList.append({"DialogueId": TranslationDialogueId, 'CharacterId': CharacterId, 'CharacterName': TranslationDialogueName, 'CharacterRole': TranslationDialogueRole, 'CharacterGender': TranslationDialogueGender, 'CharacterAge': TranslationDialogueAge})
                
        ## 대화문이 아닌 경우
        else:
            DialoguePattern = re.compile(r'\{' + re.escape(str(TranslationDialogueId)) + r'\s+대화:\s+(.*?)\}')
            DialogueBody = DialoguePattern.sub(r"'\1'", DialogueBody)
            Body = DialoguePattern.sub(r"'\1'", Body)
    
    TranslationDialogueAnalysis['Body'] = Body
    TranslationDialogueAnalysis['DialogueBody'] = DialogueBody
    TranslationDialogueAnalysis['BodyCharacterList'] = BodyCharacterList

    ## TranslationDialogueAnalysisFrame 데이터 프레임 업데이트
    TranslationDialogueAnalysisFrame[1].append(TranslationDialogueAnalysis)
    
    ## 앞선 모든 DialogueBody와 Body와 BodyCharacterList에 변경된 이름 적용
    for i in range(len(TranslationDialogueAnalysisFrame[1])):
        ## DialogueBody, Body 이름 업데이트
        BeforeDialogueBody = TranslationDialogueAnalysisFrame[1][i]['DialogueBody']
        BeforeBody = TranslationDialogueAnalysisFrame[1][i]['Body']
        BeforeBodyCharacterList = TranslationDialogueAnalysisFrame[1][i]['BodyCharacterList']
        ## BodyCharacterList 이름 업데이트
        for j in range(len(TranslationDialogueAnalysisFrame[2])):
            for k in range(len(BeforeBodyCharacterList)):
                ## CharacterName으로 업데이트
                if BeforeBodyCharacterList[k]['CharacterName'] == TranslationDialogueAnalysisFrame[2][j]['CharacterName']:
                    BeforeBodyCharacterList[k]['CharacterId'] = TranslationDialogueAnalysisFrame[2][j]['CharacterId']
                    BeforeBodyCharacterList[k]['CharacterName'] = TranslationDialogueAnalysisFrame[2][j]['CharacterName']
                    BeforeBodyCharacterList[k]['CharacterRole'] = TranslationDialogueAnalysisFrame[2][j]['CharacterRole']
                    BeforeBodyCharacterList[k]['CharacterGender'] = TranslationDialogueAnalysisFrame[2][j]['CharacterGender']
                    BeforeBodyCharacterList[k]['CharacterAge'] = TranslationDialogueAnalysisFrame[2][j]['CharacterAge']
                ## CharacterId로 업데이트
                if BeforeBodyCharacterList[k]['CharacterId'] == TranslationDialogueAnalysisFrame[2][j]['CharacterId']:
                    BeforeDialogueBody = re.sub(f"{{{BeforeBodyCharacterList[k]['CharacterName']}: ", f"{{{TranslationDialogueAnalysisFrame[2][j]['CharacterName']}: ", BeforeDialogueBody)
                    BeforeBody = re.sub(f"{{{BeforeBodyCharacterList[k]['CharacterName']}: ", f"{{{TranslationDialogueAnalysisFrame[2][j]['CharacterName']}: ", BeforeBody)
                    BeforeBodyCharacterList[k]['CharacterId'] = TranslationDialogueAnalysisFrame[2][j]['CharacterId']
                    BeforeBodyCharacterList[k]['CharacterName'] = TranslationDialogueAnalysisFrame[2][j]['CharacterName']
                    BeforeBodyCharacterList[k]['CharacterRole'] = TranslationDialogueAnalysisFrame[2][j]['CharacterRole']
                    BeforeBodyCharacterList[k]['CharacterGender'] = TranslationDialogueAnalysisFrame[2][j]['CharacterGender']
                    BeforeBodyCharacterList[k]['CharacterAge'] = TranslationDialogueAnalysisFrame[2][j]['CharacterAge']
        ## 수정된 DialogueBody와 Body와 BodyCharacterList를 프레임에 저장
        TranslationDialogueAnalysisFrame[1][i]['DialogueBody'] = BeforeDialogueBody
        TranslationDialogueAnalysisFrame[1][i]['Body'] = BeforeBody
        TranslationDialogueAnalysisFrame[1][i]['BodyCharacterList'] = BeforeBodyCharacterList
    
    ## TranslationDialogueAnalysisFrame ProcessCount 및 Completion 업데이트
    TranslationDialogueAnalysisFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        TranslationDialogueAnalysisFrame[0]['Completion'] = 'Yes'
        
    ## TranslationDialogueAnalysisFrame 저장
    with open(ProjectDataFrameTranslationDialogueAnalysisPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TranslationDialogueAnalysisFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process12: TranslationDialogueEditing DataFrame 저장
def TranslationDialogueEditingProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationDialogueEditingPath, MarkBody, TranslationDialogueEditingResponse, Process, InputCount, IndexId, IndexTag, Index, BodyId, Body, CharacterList, TotalInputCount):
    if os.path.exists(ProjectDataFrameTranslationDialogueEditingPath):
        TranslationDialogueEditingFramePath = ProjectDataFrameTranslationDialogueEditingPath
    else:
        TranslationDialogueEditingFramePath = os.path.join(TranslationDataFramePath, "a232-12_TranslationDialogueEditingFrame.json")
    with open(TranslationDialogueEditingFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationDialogueEditingFrame = json.load(DataFrameJson)
        
    ## TranslationDialogueEditingFrame 업데이트
    TranslationDialogueEditingFrame[0]['ProjectName'] = ProjectName
    TranslationDialogueEditingFrame[0]['MainLang'] = MainLang.capitalize()
    TranslationDialogueEditingFrame[0]['Translation'] = Translation.capitalize()
    TranslationDialogueEditingFrame[0]['TaskName'] = Process
    
    ## TranslationDialogueEditingFrame 첫번째 데이터 프레임 복사
    TranslationDialogueEditing = TranslationDialogueEditingFrame[1][0].copy()
    TranslationDialogueEditing['IndexId'] = IndexId
    TranslationDialogueEditing['IndexTag'] = IndexTag
    TranslationDialogueEditing['Index'] = Index
    TranslationDialogueEditing['BodyId'] = BodyId
    
    # DialogueBody에서 {n 대화: 대화내용} -> 편집대화내용으로 변경
    DialogueBody = MarkBody
    for TranslationDialogue in TranslationDialogueEditingResponse:
        TranslationDialogueId = TranslationDialogue['번호']
        TranslationDialogueName = TranslationDialogue['인물']
        TranslationDialogueTone = TranslationDialogue['현재말의높임법']
        TranslationEditedDialogueText = TranslationDialogue['편집대화내용']
        # 원본 패턴을 찾아서 편집된 내용으로 대체 (비탐욕적 매칭 사용)
        DialoguePattern = f"{{{TranslationDialogueId} {TranslationDialogueName}: ([^}}]*)}}"
        # 원본 대화 내용 추출 후 할당
        DialogueMatch = re.search(DialoguePattern, DialogueBody)
        TranslationOrginDialogueText = DialogueMatch.group(1)
        
        ## 원래 대화문 글자 개수에 따라서 변경 여부를 결정
        # 조건1. 원본 대화문 글자 개수가 100개(한글기준) 이하인 경우 (언어별로 다르게 해야함)
        # 조건2. 원본 대화문과 편집 대화문의 글자 개수 비율이 0.6-1.7 사이인 경우
        # 언어별 최대 토큰 길이 설정
        if MainLang == 'ko':
            MaxTokenLength = 150  # 한국어: 100자
        elif MainLang == 'en':
            MaxTokenLength = 350  # 영어: 250자 (알파벳 기준)
        elif MainLang == 'zh':
            MaxTokenLength = 120   # 중국어: 80자 (한자 기준)
        elif MainLang == 'es':
            MaxTokenLength = 350  # 스페인어: 250자
        elif MainLang == 'fr':
            MaxTokenLength = 350  # 프랑스어: 250자
        elif MainLang == 'ja':
            MaxTokenLength = 120   # 일본어: 80자 (한자/가나 혼합)
        else:
            MaxTokenLength = 200  # 기타 언어: 기본값
            
        if len(TranslationOrginDialogueText) > MaxTokenLength:
            # 원본 텍스트와 편집된 텍스트의 길이 비율 계산
            if len(TranslationOrginDialogueText) > 0:  # 0으로 나누기 방지
                Ratio = len(TranslationEditedDialogueText) / len(TranslationOrginDialogueText)
                # 비율이 0.6-1.7 범위 내에 있는지 확인
                if 0.6 <= Ratio <= 1.7:
                    ReplaceDialogueText = TranslationEditedDialogueText
                else:
                    ReplaceDialogueText = TranslationOrginDialogueText
            else:
                ReplaceDialogueText = TranslationOrginDialogueText
        else:
            ReplaceDialogueText = TranslationEditedDialogueText
        
        ## 대화문 편집대화문으로 변경
        print(f'\n{TranslationDialogueId}. 대화 변화: {{{TranslationDialogueId} {TranslationDialogueName}: {TranslationOrginDialogueText}}} ->>> {{{TranslationDialogueName}({TranslationDialogueTone}): {ReplaceDialogueText}}}\n')
        # Body에서 패턴 전체를 편집된 내용으로 대체
        Body = Body.replace(f"{{{TranslationDialogueId} {TranslationDialogueName}: {TranslationOrginDialogueText}}}", f'"{ReplaceDialogueText}"')
        # DialogueBody에서도 패턴 대체
        DialogueBody = re.sub(re.escape(f"{{{TranslationDialogueId} {TranslationDialogueName}: {TranslationOrginDialogueText}}}"), f'{{{TranslationDialogueName}({TranslationDialogueTone}): {ReplaceDialogueText}}}', DialogueBody)
    
    TranslationDialogueEditing['Body'] = Body
    TranslationDialogueEditing['DialogueBody'] = DialogueBody
    TranslationDialogueEditing['EditedDialogue'] = TranslationDialogueEditingResponse
    TranslationDialogueEditing['BodyCharacterList'] = CharacterList

    ## TranslationDialogueEditingFrame 데이터 프레임 업데이트
    TranslationDialogueEditingFrame[1].append(TranslationDialogueEditing)
        
    ## TranslationDialogueEditingFrame ProcessCount 및 Completion 업데이트
    TranslationDialogueEditingFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        TranslationDialogueEditingFrame[0]['Completion'] = 'Yes'
        
    ## TranslationDialogueEditingFrame 저장
    with open(ProjectDataFrameTranslationDialogueEditingPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TranslationDialogueEditingFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process14: AfterTranslationBodySummaryProcess DataFrame 저장
def AfterTranslationBodySummaryProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameAfterTranslationBodySummaryPath, AfterTranslationBodySummaryResponse, Process, InputCount, IndexId, TotalInputCount):
    ## AfterTranslationBodySummaryFrame 불러오기
    if os.path.exists(ProjectDataFrameAfterTranslationBodySummaryPath):
        AfterTranslationBodySummaryFramePath = ProjectDataFrameAfterTranslationBodySummaryPath
    else:
        AfterTranslationBodySummaryFramePath = os.path.join(TranslationDataFramePath, "a232-14_AfterTranslationBodySummaryFrame.json")
    with open(AfterTranslationBodySummaryFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        AfterTranslationBodySummaryFrame = json.load(DataFrameJson)
        
    ## AfterTranslationBodySummaryFrame 업데이트
    AfterTranslationBodySummaryFrame[0]['ProjectName'] = ProjectName
    AfterTranslationBodySummaryFrame[0]['MainLang'] = MainLang.capitalize()
    AfterTranslationBodySummaryFrame[0]['Translation'] = Translation.capitalize()
    AfterTranslationBodySummaryFrame[0]['TaskName'] = Process
    
    ## AfterTranslationBodySummaryFrame 첫번째 데이터 프레임 복사
    AfterTranslationBodySummary = AfterTranslationBodySummaryFrame[1][0].copy()

    AfterTranslationBodySummary['IndexId'] = IndexId
    AfterTranslationBodySummary['BodyId'] = InputCount
    AfterTranslationBodySummary['MainText'] = AfterTranslationBodySummaryResponse['핵심문구']
    AfterTranslationBodySummary['BodySummary'] = AfterTranslationBodySummaryResponse['요약']
    AfterTranslationBodySummary['Score'] = AfterTranslationBodySummaryResponse['중요도']

    ## AfterTranslationBodySummaryFrame 데이터 프레임 업데이트
    AfterTranslationBodySummaryFrame[1].append(AfterTranslationBodySummary)
        
    ## AfterTranslationBodySummaryFrame ProcessCount 및 Completion 업데이트
    AfterTranslationBodySummaryFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        AfterTranslationBodySummaryFrame[0]['Completion'] = 'Yes'
        
    ## AfterTranslationBodySummaryFrame 저장
    with open(ProjectDataFrameAfterTranslationBodySummaryPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(AfterTranslationBodySummaryFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process15: AuthorResearchProcess DataFrame 저장
def AuthorResearchProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameAuthorResearchPath, AuthorResearchResponse, Process, InputCount, TotalInputCount):
    ## AuthorResearchFrame 불러오기
    if os.path.exists(ProjectDataFrameAuthorResearchPath):
        AuthorResearchFramePath = ProjectDataFrameAuthorResearchPath
    else:
        AuthorResearchFramePath = os.path.join(TranslationDataFramePath, "a232-15_AuthorResearchFrame.json")
    with open(AuthorResearchFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        AuthorResearchFrame = json.load(DataFrameJson)
        
    ## AuthorResearchFrame 업데이트
    AuthorResearchFrame[0]['ProjectName'] = ProjectName
    AuthorResearchFrame[0]['MainLang'] = MainLang.capitalize()
    AuthorResearchFrame[0]['Translation'] = Translation.capitalize()
    AuthorResearchFrame[0]['TaskName'] = Process
    
    ## AuthorResearchFrame 첫번째 데이터 프레임 복사
    AuthorResearch = AuthorResearchFrame[1][0].copy()
    AuthorResearch['Author'] = AuthorResearchResponse['이름']
    AuthorResearch['Birth'] = AuthorResearchResponse['출생']
    AuthorResearch['Nationality'] = AuthorResearchResponse['국적']
    AuthorResearch['Major'] = AuthorResearchResponse['전공']
    AuthorResearch['Degree'] = AuthorResearchResponse['학위']
    AuthorResearch['MajorCareer'] = AuthorResearchResponse['주요경력']
    AuthorResearch['RepresentativeWorks'] = AuthorResearchResponse['대표저서']
    AuthorResearch['ThoughtsAndInfluence'] = AuthorResearchResponse['사상및영향력']
    AuthorResearch['OtherInterestingFacts'] = AuthorResearchResponse['기타흥미로운요소서술']
    AuthorResearch['AboutTheAuthor'] = AuthorResearchResponse['저자소개']

    ## AuthorResearchFrame 데이터 프레임 업데이트
    AuthorResearchFrame[1].append(AuthorResearch)
        
    ## AuthorResearchFrame ProcessCount 및 Completion 업데이트
    AuthorResearchFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        AuthorResearchFrame[0]['Completion'] = 'Yes'
        
    ## AuthorResearchFrame 저장
    with open(ProjectDataFrameAuthorResearchPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(AuthorResearchFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process16: TranslationCatchphraseProcess DataFrame 저장
def TranslationCatchphraseProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationCatchphrasePath, TranslationCatchphraseResponse, Process, InputCount, TotalInputCount):
    ## TranslationCatchphraseFrame 불러오기
    if os.path.exists(ProjectDataFrameTranslationCatchphrasePath):
        TranslationCatchphraseFramePath = ProjectDataFrameTranslationCatchphrasePath
    else:
        TranslationCatchphraseFramePath = os.path.join(TranslationDataFramePath, "a232-16_TranslationCatchphraseFrame.json")
    with open(TranslationCatchphraseFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationCatchphraseFrame = json.load(DataFrameJson)
        
    ## TranslationCatchphraseFrame 업데이트
    TranslationCatchphraseFrame[0]['ProjectName'] = ProjectName
    TranslationCatchphraseFrame[0]['MainLang'] = MainLang.capitalize()
    TranslationCatchphraseFrame[0]['Translation'] = Translation.capitalize()
    TranslationCatchphraseFrame[0]['TaskName'] = Process
    
    ## TranslationCatchphraseFrame 첫번째 데이터 프레임 복사
    TranslationCatchphrase = TranslationCatchphraseFrame[1][0].copy()
    TranslationCatchphrase['Subtitle'] = TranslationCatchphraseResponse['부제']
    TranslationCatchphrase['CoverCopy1'] = TranslationCatchphraseResponse['표지카피1']
    TranslationCatchphrase['CoverCopy2'] = TranslationCatchphraseResponse['표지카피2']
    TranslationCatchphrase['CoverCopy3'] = TranslationCatchphraseResponse['표지카피3']
    TranslationCatchphrase['BandCopy'] = TranslationCatchphraseResponse['띠지카피']
    TranslationCatchphrase['BookCoreMessage'] = TranslationCatchphraseResponse['도서핵심메세지']
    TranslationCatchphrase['TranslatorPreface'] = TranslationCatchphraseResponse['역자서문']
    TranslationCatchphrase['BookIntroduction'] = TranslationCatchphraseResponse['책소개']
    TranslationCatchphrase['PublisherReview'] = TranslationCatchphraseResponse['출판사서평']

    ## TranslationCatchphraseFrame 데이터 프레임 업데이트
    TranslationCatchphraseFrame[1].append(TranslationCatchphrase)
        
    ## TranslationCatchphraseFrame ProcessCount 및 Completion 업데이트
    TranslationCatchphraseFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        TranslationCatchphraseFrame[0]['Completion'] = 'Yes'
        
    ## TranslationCatchphraseFrame 저장
    with open(ProjectDataFrameTranslationCatchphrasePath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TranslationCatchphraseFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process17: TranslationFundingCatchphraseProcess DataFrame 저장
def TranslationFundingCatchphraseProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationFundingCatchphrasePath, TranslationFundingCatchphraseResponse, Process, InputCount, TotalInputCount):
    if os.path.exists(ProjectDataFrameTranslationFundingCatchphrasePath):
        TranslationFundingCatchphraseFramePath = ProjectDataFrameTranslationFundingCatchphrasePath
    else:
        TranslationFundingCatchphraseFramePath = os.path.join(TranslationDataFramePath, "a232-17_TranslationFundingCatchphraseFrame.json")
    with open(TranslationFundingCatchphraseFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationFundingCatchphraseFrame = json.load(DataFrameJson)
        
    ## TranslationFundingCatchphraseFrame 업데이트
    TranslationFundingCatchphraseFrame[0]['ProjectName'] = ProjectName
    TranslationFundingCatchphraseFrame[0]['MainLang'] = MainLang.capitalize()
    TranslationFundingCatchphraseFrame[0]['Translation'] = Translation.capitalize()
    TranslationFundingCatchphraseFrame[0]['TaskName'] = Process
    
    ## TranslationFundingCatchphraseFrame 첫번째 데이터 프레임 복사
    TranslationFundingCatchphrase = TranslationFundingCatchphraseFrame[1][0].copy()
    TranslationFundingCatchphrase['MainTitle'] = TranslationFundingCatchphraseResponse['23자_메인타이틀']
    TranslationFundingCatchphrase['SubTitle'] = TranslationFundingCatchphraseResponse['7자_서브타이틀']
    TranslationFundingCatchphrase['ProjectSummary'] = TranslationFundingCatchphraseResponse['50자_프로젝트요약']
    TranslationFundingCatchphrase['DetailPageMainTitle'] = TranslationFundingCatchphraseResponse['상세페이지타이틀']
    TranslationFundingCatchphrase['DetailPageSubTitle'] = TranslationFundingCatchphraseResponse['상세페이지서브타이틀']
    TranslationFundingCatchphrase['ProjectDescription'] = TranslationFundingCatchphraseResponse['프로젝트소개']
    TranslationFundingCatchphrase['BookDescription'] = TranslationFundingCatchphraseResponse['도서소개']
    TranslationFundingCatchphrase['EditionDescription'] = TranslationFundingCatchphraseResponse['에디션소개']
    TranslationFundingCatchphrase['Recommendations'] = TranslationFundingCatchphraseResponse['이런분들께추천합니다']
    TranslationFundingCatchphrase['ProjectSchedule'] = TranslationFundingCatchphraseResponse['프로젝트일정']
    TranslationFundingCatchphrase['RewardDescription'] = TranslationFundingCatchphraseResponse['선물설명']

    ## TranslationFundingCatchphraseFrame 데이터 프레임 업데이트
    TranslationFundingCatchphraseFrame[1].append(TranslationFundingCatchphrase)
        
    ## TranslationFundingCatchphraseFrame ProcessCount 및 Completion 업데이트
    TranslationFundingCatchphraseFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        TranslationFundingCatchphraseFrame[0]['Completion'] = 'Yes'
        
    ## TranslationFundingCatchphraseFrame 저장
    with open(ProjectDataFrameTranslationFundingCatchphrasePath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TranslationFundingCatchphraseFrame, DataFrameJson, indent = 4, ensure_ascii = False)

##############################
##### ProcessEdit 업데이트 #####
##############################
## Process Edit 저장
def ProcessEditSave(ProjectDataFramePath, TranslationEditPath, Process, EditMode):
    ## TranslationDataFrame 불러온 뒤 Completion 확인
    with open(ProjectDataFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationDataFrame = json.load(DataFrameJson)
    ## TranslationEdit 저장
    if TranslationDataFrame[0]['Completion'] == 'Yes':
        ## TranslationEdit이 존재할때
        if os.path.exists(TranslationEditPath):
            with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
                TranslationEdit = json.load(TranslationEditJson)
        ## TranslationEdit이 존재 안할때
        else:
            TranslationEdit = {}
        ## TranslationEdit 업데이트
        TranslationEdit[Process] = []
        
        ## Process에서 추가 데이터가 존재하는 경우 예외 저장
        # TranslationDialogueAnalysis
        if Process == 'TranslationDialogueAnalysis':
            TranslationEdit[Process + 'Character'] = TranslationDataFrame[2]
            
        if EditMode == "Manual":
            TranslationEdit[f"{Process}Completion"] = '완료 후 Completion'
        elif EditMode == "Auto":
            TranslationEdit[f"{Process}Completion"] = 'Completion'
        TranslationDataList = TranslationDataFrame[1]
        for i in range(1, len(TranslationDataList)):
            ProcessDic = TranslationDataList[i]
            TranslationEdit[Process].append(ProcessDic)
            
        ## TranslationEdit 저장
        with open(TranslationEditPath, 'w', encoding = 'utf-8') as TranslationEditJson:
            json.dump(TranslationEdit, TranslationEditJson, indent = 4, ensure_ascii = False)
            
## BodySplitProcess Edit 저장
def BodySplitProcessEditSave(ProjectDataFramePath, TranslationEditPath, Process):
    ## TranslationDataFrame 불러온 뒤 Completion 확인
    with open(ProjectDataFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationDataFrame = json.load(DataFrameJson)
    ## TranslationEdit 저장
    if TranslationDataFrame[0]['Completion'] == 'Yes':
        ## TranslationEdit이 존재할때
        if os.path.exists(TranslationEditPath):
            with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
                TranslationEdit = json.load(TranslationEditJson)

        if not Process in TranslationEdit:
            ## TranslationEdit 업데이트
            TranslationEdit[Process] = []
            TranslationEdit[f"{Process}Completion"] = 'Completion'
            TranslationDataList = TranslationDataFrame[1]
            for i in range(1, len(TranslationDataList)):
                ProcessDic = TranslationDataList[i]
                TranslationEdit[Process].append(ProcessDic)
            
            ## TranslationEdit 저장
            with open(TranslationEditPath, 'w', encoding = 'utf-8') as TranslationEditJson:
                json.dump(TranslationEdit, TranslationEditJson, indent = 4, ensure_ascii = False)

## ProcessEditText 저장
def ProcessEditTextSave(ProjectName, MainLang, BookGenre, ProjectMasterTranslationPath, TranslationEditPath, Process1, Process2, Process3, ProofreadingBeforeProcessFileTag):
    # 대화문 끝 따옴표 뒤 공백 처리 및 추가 기능 처리
    def AddSpaceAfterDialog(BodyText):
        # 따옴표 통일
        BodyText = BodyText.replace('”', '"').replace('“', '"')
        BodyText = BodyText.replace('’', "'").replace('‘', "'")
        BodyText = BodyText.replace("………", "…").replace("……", "…")
        
        AddSpaceAfterDialogBodyText = ""
        QuoteCount = 0
        for i in range(len(BodyText)):
            Char = BodyText[i]
            AddSpaceAfterDialogBodyText += Char
            if Char == '"':
                QuoteCount += 1
                # 대화문 끝(짝수번째 인용부호)인 경우
                if QuoteCount % 2 == 0:
                    # 다음 문자가 존재하고 공백이나 줄바꿈이 아니면 공백 추가
                    if i + 1 < len(BodyText) and BodyText[i + 1] not in [' ', '\n']:
                        AddSpaceAfterDialogBodyText += ' '
        
        # 기존 단일 인용부호 내부의 앞뒤 공백 제거 (내부는 공백 없이 붙이기)
        AddSpaceAfterDialogBodyText = re.sub(r"'(\s*)([^']*?)(\s*)'", r"'\2'", AddSpaceAfterDialogBodyText)
        AddSpaceAfterDialogBodyText = AddSpaceAfterDialogBodyText.replace("''", "' '")
        # 기존 이중 인용부호 내부의 앞뒤 공백 제거
        AddSpaceAfterDialogBodyText = re.sub(r'"(\s*)([^"]*?)(\s*)"', r'"\2"', AddSpaceAfterDialogBodyText)
        AddSpaceAfterDialogBodyText = AddSpaceAfterDialogBodyText.replace('""', '" "')

        # 단일 인용문 ('문구')의 시작 인용부호 앞에 무조건 정확히 1개의 공백을 추가
        # (문자열 시작이 아닐 경우에 한해, 기존의 모든 공백을 제거하고 1개의 공백으로 대체)
        AddSpaceAfterDialogBodyText = re.sub(r"(?<!^)\s*(')([^']+?')", r" \1\2", AddSpaceAfterDialogBodyText)

        # 유니코드 ellipsis(…)를 점 3개(...)로 변경
        AddSpaceAfterDialogBodyText = AddSpaceAfterDialogBodyText.replace("…", "...")
        # "..." 뒤에 줄바꿈이 아닌 경우에는 1개의 공백을 추가 (이미 공백이 있거나 여러 개면 1개로 조정)
        AddSpaceAfterDialogBodyText = re.sub(r"\.\.\.(?!\n)\s*", r"... ", AddSpaceAfterDialogBodyText)
        AddSpaceAfterDialogBodyText = AddSpaceAfterDialogBodyText.replace("... ...", "...")
        AddSpaceAfterDialogBodyText = AddSpaceAfterDialogBodyText.replace("... ..", "...")
        AddSpaceAfterDialogBodyText = AddSpaceAfterDialogBodyText.replace("... .", "...")
        AddSpaceAfterDialogBodyText = AddSpaceAfterDialogBodyText.replace('... "', '..."')
        AddSpaceAfterDialogBodyText = AddSpaceAfterDialogBodyText.replace("... '", "...'")
        AddSpaceAfterDialogBodyText = AddSpaceAfterDialogBodyText.replace("\" '", "\"'")
        
        return AddSpaceAfterDialogBodyText
    
    ## TranslationEdit 불러오기
    with open(TranslationEditPath, 'r', encoding='utf-8') as TranslationEditJson:
        TranslationEdit = json.load(TranslationEditJson)
    TranslationBodySplit = TranslationEdit[Process1]
    TranslationIndexEdit = TranslationEdit[Process2]
    TranslationBodyEdit = TranslationEdit[Process3]
        
    ## TranslationEdit을 Index, Body Text 파일로 저장할 경로 설정
    EditIndexFileName = f"{ProjectName}_Index({MainLang}-{BookGenre}).txt"
    EditIndexFilePath = os.path.join(ProjectMasterTranslationPath, EditIndexFileName)
    EditBodyFileName = f"{ProjectName}_Body({MainLang}-{BookGenre}-{ProofreadingBeforeProcessFileTag}).txt"
    EditBodyFilePath = os.path.join(ProjectMasterTranslationPath, EditBodyFileName)
    
    # Index 파일이 존재하지 않을 때만 생성
    if not os.path.exists(EditIndexFilePath):
        with open(EditIndexFilePath, 'w', encoding='utf-8') as indexFile:
            for ProcessDic in TranslationIndexEdit:
                IndexTag = ProcessDic['IndexTag']
                Index = ProcessDic['IndexTranslation']
                if IndexTag == "Title":
                    IndexText = f"<{Index}>\n\n"
                elif IndexTag == "Logue":
                    IndexText = f"\n<{Index}>\n\n"
                elif IndexTag in ["Part", "Chapter"]:
                    IndexText = f"\n<{Index}>\n\n"
                else:
                    IndexText = f"<{Index}>\n"
                IndexText = IndexText.replace("<<", "<").replace(">>", ">")
                indexFile.write(IndexText)
    else:
        print(f"[{ProjectName} Index 파일 {EditIndexFilePath}이(가) 이미 존재합니다.]")
    
    # Body 파일이 존재하지 않을 때만 생성
    if not os.path.exists(EditBodyFilePath):
        CurrentIndex = None
        with open(EditBodyFilePath, 'w', encoding='utf-8') as bodyFile:
            for i, ProcessDic in enumerate(TranslationBodyEdit):
                # 새로운 Index인지 확인
                if ProcessDic['Index'] != CurrentIndex:
                    CurrentIndex = ProcessDic['Index']
                    # 새 Index 작성
                    if i != 0:
                        bodyFile.write(f"\n\n\n<{ProcessDic['Index']}>\n\n\n".replace("<<", "<").replace(">>", ">"))
                    else:
                        bodyFile.write(f"<{ProcessDic['Index']}>\n\n\n".replace("<<", "<").replace(">>", ">"))
                
                # Body 내용 작성
                BodyText = ProcessDic['Body'].replace('\n\n\n\n', '\n\n')
                BodyText = BodyText.replace('\n\n\n', '\n\n')
                BodyText = BodyText.replace(' \n', '\n')
                BodyText = AddSpaceAfterDialog(BodyText)
                BodyText = BodyText.replace('  ', ' ')
                if "FinalEnding" in TranslationBodySplit[i]:
                    if BodyText.endswith('\n'):
                        pass
                    else:
                        BodyText += TranslationBodySplit[i]['FinalEnding']
                bodyFile.write(f"{BodyText}")
    else:
        print(f"[{ProjectName} Body 파일 {EditBodyFilePath}이(가) 이미 존재합니다.]")

## BookCopyText 저장
def BookCopyTextSave(ProjectName, MainLang, ProjectMasterTranslationPath, TranslationEditPath, Process1, Process2):
    ## TranslationEdit 불러오기
    with open(TranslationEditPath, 'r', encoding='utf-8') as TranslationEditJson:
        TranslationEdit = json.load(TranslationEditJson)
    AuthorResearch = TranslationEdit[Process1]
    TranslationBookCopy = TranslationEdit[Process2]
        
    ## TranslationEdit을 BookCopy Text 파일로 저장할 경로 설정
    EditBookCopyFileName = f"{ProjectName}_BookCopy({MainLang}).txt"
    EditBookCopyFilePath = os.path.join(ProjectMasterTranslationPath, EditBookCopyFileName)
    
    # Index 파일이 존재하지 않을 때만 생성
    if not os.path.exists(EditBookCopyFilePath):
        with open(EditBookCopyFilePath, 'w', encoding = 'utf-8') as BookCopyFile:
            Author = AuthorResearch[0]['Author']
            Birth = AuthorResearch[0]['Birth']
            Nationality = AuthorResearch[0]['Nationality']
            Major = AuthorResearch[0]['Major']
            Degree = AuthorResearch[0]['Degree']
            MajorCareer = AuthorResearch[0]['MajorCareer']
            RepresentativeWorks = AuthorResearch[0]['RepresentativeWorks']
            ThoughtsAndInfluence = AuthorResearch[0]['ThoughtsAndInfluence']
            OtherInterestingFacts = AuthorResearch[0]['OtherInterestingFacts']
            AboutTheAuthor = AuthorResearch[0]['AboutTheAuthor']
            OtherInterestingFacts = re.sub(r'(?<!^)(\d+\))', r'\n\1', OtherInterestingFacts).strip()
            
            Subtitle = TranslationBookCopy[0]['Subtitle']
            CoverCopy1 = TranslationBookCopy[0]['CoverCopy1']
            CoverCopy2 = TranslationBookCopy[0]['CoverCopy2']
            CoverCopy3 = TranslationBookCopy[0]['CoverCopy3']
            BandCopy = TranslationBookCopy[0]['BandCopy']
            BookCoreMessage = TranslationBookCopy[0]['BookCoreMessage']
            TranslatorPreface = TranslationBookCopy[0]['TranslatorPreface']
            BookIntroduction = TranslationBookCopy[0]['BookIntroduction']
            PublisherReview = TranslationBookCopy[0]['PublisherReview']
            
            BookCopyText = f"<저자소개>\n\n[이름]\n{Author}\n\n[출생]\n{Birth}\n\n[국적]\n{Nationality}\n\n[전공]\n{Major}\n\n[학위]\n{Degree}\n\n[주요경력]\n{MajorCareer}\n\n[대표저서]\n{RepresentativeWorks}\n\n[사상 및 영향력]\n{ThoughtsAndInfluence}\n\n[기타 흥미로운 요소]\n{OtherInterestingFacts}\n\n[저자소개]\n{AboutTheAuthor}\n\n\n<도서문구>\n\n[부제]\n{Subtitle}\n\n[표지카피1]\n{CoverCopy1}\n\n[표지카피2]\n{CoverCopy2}\n\n[표지카피3]\n{CoverCopy3}\n\n[띠지카피]\n{BandCopy}\n\n[핵심메세지]\n{BookCoreMessage}\n\n[역자 서문]\n{TranslatorPreface}\n\n[책소개]\n{BookIntroduction}\n\n[출판사 서평]\n{PublisherReview}"
            BookCopyFile.write(BookCopyText)
    else:
        print(f"[{ProjectName} BookCopy 파일 {EditBookCopyFilePath}이(가) 이미 존재합니다.]")
        
## BookFundingCopyText 저장
def BookFundingCopyTextSave(ProjectName, MainLang, ProjectMasterTranslationPath, TranslationEditPath, Process):
    ## TranslationEdit 불러오기
    with open(TranslationEditPath, 'r', encoding='utf-8') as TranslationEditJson:
        TranslationEdit = json.load(TranslationEditJson)
    TranslationBookFundingCopy = TranslationEdit[Process]
        
    ## TranslationEdit을 BookCopy Text 파일로 저장할 경로 설정
    EditBookFundingCopyFileName = f"{ProjectName}_BookFundingCopy({MainLang}).txt"
    EditBookFundingCopyFilePath = os.path.join(ProjectMasterTranslationPath, EditBookFundingCopyFileName)
    
    # Index 파일이 존재하지 않을 때만 생성
    if not os.path.exists(EditBookFundingCopyFilePath):
        with open(EditBookFundingCopyFilePath, 'w', encoding = 'utf-8') as BookCopyFile:
            MainTitle = TranslationBookFundingCopy[0]['MainTitle']
            SubTitle = TranslationBookFundingCopy[0]['SubTitle']
            ProjectSummary = TranslationBookFundingCopy[0]['ProjectSummary']
            DetailPageMainTitle = TranslationBookFundingCopy[0]['DetailPageMainTitle']
            DetailPageSubTitle = TranslationBookFundingCopy[0]['DetailPageSubTitle']
            ProjectDescription = TranslationBookFundingCopy[0]['ProjectDescription']
            BookDescription = TranslationBookFundingCopy[0]['BookDescription']
            EditionDescription = TranslationBookFundingCopy[0]['EditionDescription']
            Recommendations = TranslationBookFundingCopy[0]['Recommendations']
            ProjectBudget = "목표 금액은 아래의 지출 항목으로 사용할 예정입니다.\n\n인쇄비: 고품질 하드커버 도서 100권 제작비\n배송비: 각각 개별 포장 및 도서 배송비"
            ProjectSchedule = TranslationBookFundingCopy[0]['ProjectSchedule']
            ProjectTeam = "45일 전: 데미안 유화 에디션의 시안 및 1차 샘플북 제작\n30일 전: 도서 내지 및 삽화 컬러 보정과 최종안 완성\n20일 전: 펀딩 수량 만큼 도서 최종 인쇄 및 제작\n전달일: 일괄 포장 및 배송 (선물 예상 전달일)"
            RewardDescription = TranslationBookFundingCopy[0]['RewardDescription']
            
            BookFundingCopyText = f"<펀딩문구>\n\n[23자 메인타이틀]\n{MainTitle}\n\n[7자 서브타이틀]\n{SubTitle}\n\n[50자 프로젝트요약]\n{ProjectSummary}\n\n[상세페이지 타이틀]\n{DetailPageMainTitle}\n\n[상세페이지 서브타이틀]\n{DetailPageSubTitle}\n\n[프로젝트 소개]\n{ProjectDescription}\n\n[도서 소개]\n{BookDescription}\n\n[에디션 소개]\n{EditionDescription}\n\n[이런 분들께 추천합니다]\n{Recommendations}\n\n[프로젝트 예산]\n{ProjectBudget}\n\n[프로젝트 일정]\n{ProjectSchedule}\n\n[프로젝트 팀 소개]\n{ProjectTeam}\n\n[선물설명]\n{RewardDescription}"
            BookCopyFile.write(BookFundingCopyText)
    else:
        print(f"[{ProjectName} BookFundingCopy 파일 {EditBookFundingCopyFilePath}이(가) 이미 존재합니다.]")

## Process Edit Prompt 확인
def ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount, NumProcesses = 1, OutputCountKey = None):
    ## EditCheck
    EditCheck = False
    EditCompletion = False
    if os.path.exists(TranslationEditPath):
        ## '[...Edit].json' 확인
        with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
            TranslationEdit = json.load(TranslationEditJson)
        
        ## Process가 TranslationIndexDefine인 경우는 TotalInputCount 적용 안됨
        if Process == 'TranslationIndexDefine':
            if Process in TranslationEdit:
                EditCheck = True

                ## 'ProcessCompletion' 확인
                if TranslationEdit[f"{Process}Completion"] == 'Completion':
                    EditCompletion = True
        else:
            if OutputCountKey:
                if Process in TranslationEdit and TranslationEdit[Process][-1][OutputCountKey] == TotalInputCount * NumProcesses:
                    EditCheck = True

                    ## 'ProcessCompletion' 확인
                    if TranslationEdit[f"{Process}Completion"] == 'Completion':
                        EditCompletion = True
            else:
                if Process in TranslationEdit and len(TranslationEdit[Process]) == TotalInputCount * NumProcesses:
                    EditCheck = True

                    ## 'ProcessCompletion' 확인
                    if TranslationEdit[f"{Process}Completion"] == 'Completion':
                        EditCompletion = True
        
    return EditCheck, EditCompletion

################################
##### Process 진행 및 업데이트 #####
################################
## Translation 프롬프트 요청 및 결과물 Json화
def TranslationProcessUpdate(projectName, email, MainLang, Translation, BookGenre, Tone, BodyLength, Editing, Refinement, KinfolkStyleRefinement, EditMode, mode = "Master", MessagesReview = "on"):
    print(f"< User: {email} | Translation: {projectName} ({Translation}) >>> ({MainLang}) | TranslationUpdate 시작 >")
    ## projectName_translation 경로 설정
    ProjectTranslationPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}/{projectName}/{projectName}_translation"
    UploadTranslationFilePath = os.path.join(ProjectTranslationPath, f"{projectName}_upload_translation_file")
    ProjectDataFrameTranslationPath = os.path.join(ProjectTranslationPath, f'{projectName}_dataframe_translation_file')
    ProjectMasterTranslationPath = os.path.join(ProjectTranslationPath, f'{projectName}_master_translation_file')
    TranslationEditPath = os.path.join(ProjectMasterTranslationPath, f'[{projectName}_Translation_Edit].json')
    
    TranslationDataFramePath = "/yaas/agent/a2_Database/a23_ProjectData/a232_TranslationProject"

    ########################
    ### Process0: PDF OCR ##
    ########################

    ## 파일 업로드 확인
    OCRTranslationPDF(projectName, UploadTranslationFilePath)

    ####################################################
    ### Process1: TranslationIndexDefine Response 생성 ##
    ####################################################
    
    ## Process 설정
    ProcessNumber = '01'
    Process = "TranslationIndexDefine"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## TranslationIndexDefine 경로 생성
    ProjectDataFrameTranslationIndexDefinePath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = TranslationIndexDefineInputList(projectName, UploadTranslationFilePath)
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationIndexDefinePath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                Input = InputList[i]['Input']
    
                ## Response 생성
                TranslationIndexDefineResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationIndexDefineFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                TranslationIndexDefineProcessDataFrameSave(projectName, MainLang, TranslationDataFramePath, ProjectDataFrameTranslationIndexDefinePath, TranslationIndexDefineResponse, Process, inputCount, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameTranslationIndexDefinePath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
    
    ## 최종 설정된 Translation 불러오기 및 MainLangCode, TranslationLangCode 설정
    Translation = LoadTranslation(Translation, ProjectDataFrameTranslationIndexDefinePath)
    MainLangCode, TranslationLangCode, ToneDistinction = LanguageCodeGen(MainLang, Translation)

    ##################################################
    ### Process1: TranslationBodySplit Response 생성 ##
    ##################################################
    
    ## Process 설정
    ProcessNumber = '01'
    Process = "TranslationBodySplit"

    ## TranslationBodySplit 경로 생성
    ProjectDataFrameTranslationBodySplitPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## CompletionCheck 및 Process 진행
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEdit = json.load(TranslationEditJson)
    EditCompletion = False
    if Process + 'Completion' in TranslationEdit:
        if TranslationEdit[Process + 'Completion'] == 'Completion':
            EditCompletion = True
    if not EditCompletion:
        ## Result 생성
        TranslationBodySplitResult = TranslationBodySplitProcess(projectName, UploadTranslationFilePath, TranslationEditPath, "TranslationIndexDefine", ProjectDataFrameTranslationIndexDefinePath, BodyLength)
        
        ## DataFrame 저장
        TranslationBodySplitProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationBodySplitPath, TranslationBodySplitResult, Process, len(TranslationBodySplitResult), len(TranslationBodySplitResult))

        ## Edit 저장
        BodySplitProcessEditSave(ProjectDataFrameTranslationBodySplitPath, TranslationEditPath, Process)

    ####################################################
    ### Process2: TranslationBodySummary Response 생성 ##
    ####################################################

    ## Process 설정
    ProcessNumber = '02'
    Process = "TranslationBodySummary"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## TranslationBodySummary 경로 생성
    ProjectDataFrameTranslationBodySummaryPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = TranslationBodySummaryInputList(TranslationEditPath, "TranslationBodySplit")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationBodySummaryPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                IndexId = InputList[i]['IndexId']
                Input1 = TranslationBodySummaryAddInput(ProjectDataFrameTranslationBodySummaryPath, TranslationLangCode)
                Input2 = InputList[i]['Input']
                Input = Input1 + Input2

                ## 현재내용의 길이가 1000자 초과인 경우만 요약
                if len(Input2) <= 500:
                    Body = InputList[i]['Body']
                    TranslationBodySummaryResponse = {"요약": Body, "핵심문구": ['None'], "중요도": 900}
                else:
                    ## Response 생성
                    TranslationBodySummaryResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationBodySummaryFilter, CheckCount, "OpenAI", mode, MessagesReview)

                ## DataFrame 저장
                TranslationBodySummaryProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationBodySummaryPath, TranslationBodySummaryResponse, Process, inputCount, IndexId, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameTranslationBodySummaryPath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
    
    #########################################
    ### Process3: WordListGen Response 생성 ##
    #########################################
    
    ## Process 설정
    ProcessNumber = '03'
    Process = "WordListGen"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## WordListGen 경로 생성
    ProjectDataFrameWordListGenPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = WordListGenInputList(TranslationEditPath, MainLangCode, TranslationLangCode, "TranslationBodySplit")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameWordListGenPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount, OutputCountKey = 'BodyId')
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                IndexId = InputList[i]['IndexId']
                Input = InputList[i]['Input']
                
                ## Response 생성
                WordListGenResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, WordListGenFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                WordListGenProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameWordListGenPath, WordListGenResponse, Process, inputCount, IndexId, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameWordListGenPath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
    
    ###############################################
    ### Process4: UniqueWordListGen Response 생성 ##
    ###############################################
    
    ## Process 설정
    ProcessNumber = '04'
    Process = "UniqueWordListGen"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## UniqueWordListGen 경로 생성
    ProjectDataFrameUniqueWordListGenPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = WordListGenInputList(TranslationEditPath, MainLangCode, TranslationLangCode, "TranslationBodySplit")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameUniqueWordListGenPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount, OutputCountKey = 'BodyId')
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                IndexId = InputList[i]['IndexId']
                Input = InputList[i]['Input']
                
                ## Response 생성
                UniqueWordListGenResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, UniqueWordListGenFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                UniqueWordListGenProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameUniqueWordListGenPath, UniqueWordListGenResponse, Process, inputCount, IndexId, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameUniqueWordListGenPath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
    
    ####################################################
    ### Process5: WordListPostprocessing Response 생성 ##
    ####################################################
    
    ## Process 설정
    ProcessNumber = '05'
    Process = "WordListPostprocessing"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## WordListPostprocessing 경로 생성
    ProjectDataFrameWordListPostprocessingPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = WordListPostprocessingInputList(TranslationEditPath, MainLangCode, TranslationLangCode, "TranslationBodySplit", "WordListGen", "UniqueWordListGen")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameWordListPostprocessingPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount, OutputCountKey = 'BodyId')
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                IndexId = InputList[i]['IndexId']
                Input = InputList[i]['Input']
                CheckCount = InputList[i]['InputLength']
                
                ## Response 생성
                WordListPostprocessingResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, WordListPostprocessingFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                WordListPostprocessingProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameWordListPostprocessingPath, WordListPostprocessingResponse, Process, inputCount, IndexId, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameWordListPostprocessingPath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
    
    ##############################################
    ### Process6: IndexTranslation Response 생성 ##
    ##############################################
    
    ## Process 설정
    ProcessNumber = '06'
    Process = "IndexTranslation"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## IndexTranslation 경로 생성
    ProjectDataFrameIndexTranslationPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')
    
    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = IndexTranslationInputList(TranslationEditPath, "TranslationIndexDefine", "TranslationBodySummary", "WordListPostprocessing")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameIndexTranslationPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                IndexId = InputList[i]['IndexId']
                IndexTag = InputList[i]['IndexTag']
                IndexText = InputList[i]['IndexText']
                Input1 = IndexTranslationAddInput(ProjectDataFrameIndexTranslationPath, IndexText, MainLangCode, TranslationLangCode)
                Input2 = InputList[i]['Input']
                Input = Input1 + Input2

                ## Response 생성
                IndexTranslationResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, IndexTranslationFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                IndexTranslationProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameIndexTranslationPath, IndexTranslationResponse, Process, inputCount, IndexId, IndexTag, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameIndexTranslationPath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
    
    ##########################################################
    ### Process7: BodyTranslationPreprocessing Response 생성 ##
    ##########################################################

    ## Process 설정
    ProcessNumber = '07'
    Process = "BodyTranslationPreprocessing"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## BodyTranslationPreprocessing 경로 생성
    ProjectDataFrameBodyTranslationPreprocessingPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')
    
    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = BodyTranslationPreprocessingInputList(TranslationEditPath, MainLangCode, TranslationLangCode, "TranslationBodySplit", "WordListPostprocessing", "IndexTranslation")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameBodyTranslationPreprocessingPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                IndexId = InputList[i]['IndexId']
                IndexTag = InputList[i]['IndexTag']
                Index = InputList[i]['Index']
                BodyId = InputList[i]['BodyId']
                TranslationBody = InputList[i]['TranslationBody']
                Input = InputList[i]['Input']
                
                ## Response 생성
                BodyTranslationPreprocessingResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, BodyTranslationPreprocessingFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                BodyTranslationPreprocessingProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameBodyTranslationPreprocessingPath, BodyTranslationPreprocessingResponse, Process, inputCount, IndexId, IndexTag, Index, BodyId, TranslationBody, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameBodyTranslationPreprocessingPath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
    
    #############################################
    ### Process8: BodyTranslation Response 생성 ##
    #############################################

    ## Process 설정
    ProcessNumber = '08'
    Process = "BodyTranslation"
    ProofreadingBeforeProcess = Process
    ProofreadingBeforeProcessFileTag = "Translation"
    ToneEditProcess = "BodyToneEditing"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## BodyTranslation 경로 생성
    ProjectDataFrameBodyTranslationPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = "None" # 필터에서 데이터 체크가 필요한 카운트(여기서는 이전내용 체크)
    InputList = BodyTranslationInputList(TranslationEditPath, "BodyTranslationPreprocessing")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameBodyTranslationPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    
    if Tone == 'Auto':
        MemoryNote = ''
    elif Tone == 'Formal':
        MemoryNote = '\n※ 참고! [*원문]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 번역해주세요.'
        ToneCode = '**격식체 ->>> (((습니다. 입니다. 합니다. ... 등)))'
    elif Tone == 'Normal':
        MemoryNote = '\n※ 참고! [*원문]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 번역해주세요.'
        ToneCode = '**평서체 ->>> (((이다. 한다. 있다. ... 등)))'
    elif Tone == 'Informal':
        MemoryNote = '\n※ 참고! [*원문]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 번역해주세요.'
        ToneCode = '**비격식체 ->>> (((이었어. 했어. 있어. ... 등)))'
        
    if not EditCheck:
        if DataFrameCompletion == 'No':
            i = InputCount - 1
            while i < TotalInputCount:
                ## Input 생성
                inputCount = InputList[i]['Id']
                IndexId = InputList[i]['IndexId']
                IndexTag = InputList[i]['IndexTag']
                Index = InputList[i]['Index']
                BodyId = InputList[i]['BodyId']
                Input1 = BodyTranslationAddInput(ProjectDataFrameBodyTranslationPath, ProjectDataFrameIndexTranslationPath, MainLangCode, TranslationLangCode, Tone)
                Input2 = InputList[i]['Input']
                Input = Input1 + Input2
                
                ## Response 생성
                BodyTranslationResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, BodyTranslationFilter, CheckCount, "OpenAI", mode, MessagesReview, memoryNote = MemoryNote)
                
                #######################################################
                ### Process8: BodyTranslationCheck, BodyToneEditing ###
                #######################################################
                BodyTranslationCheckResponse = {'현재도서내용어조': '모름'}
                if inputCount >= 5 and ToneDistinction == 'Yes':
                    
                    ## BodyTranslationCheck, BodyToneEditing ##
                    CheckProcess = "BodyTranslationCheck"
                    _, CheckInput, ToneEditInput, BeforeCheck = BodyTranslationCheckAndBodyToneEditingInput(projectName, Process, ToneCode, inputCount, TotalInputCount, ProjectDataFrameBodyTranslationPath, BodyTranslationResponse)
                    
                    BodyTranslationCheckResponse = ProcessResponse(projectName, email, CheckProcess, CheckInput, inputCount, TotalInputCount, BodyTranslationCheckFilter, CheckCount, "OpenAI", mode, MessagesReview)
                    
                    if BeforeCheck != '모름':
                        if (BodyTranslationCheckResponse['이전도서내용어조'] == '모름' and BodyTranslationCheckResponse['현재도서내용어조'] == '모름') or (BodyTranslationCheckResponse['이전도서내용어조'] != BeforeCheck and BodyTranslationCheckResponse['현재도서내용어조'] != BeforeCheck):
                            BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                            BodyTranslationResponse = {'번역문': BodyToneEditingResponse['어조일치현재도서내용']}
                            BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                            pass
                    if BodyTranslationCheckResponse['어조일치여부'] == '불일치':
                        if BodyTranslationCheckResponse['이전도서내용어조'] == '모름':
                            if BodyTranslationCheckResponse['현재도서내용어조'] == BeforeCheck:
                                pass
                            else:
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                BodyTranslationResponse = {'번역문': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass
                        elif BodyTranslationCheckResponse['현재도서내용어조'] == '모름':
                            BodyTranslationCheckResponse['현재도서내용어조'] = BeforeCheck
                            pass
                        elif BodyTranslationCheckResponse['이전도서내용어조'] == '격식체':
                            MemoryNote = '\n※ 참고! [*원문]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 번역해주세요.'
                            BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                            BodyTranslationResponse = {'번역문': BodyToneEditingResponse['어조일치현재도서내용']}
                            BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                            pass
                        elif BodyTranslationCheckResponse['이전도서내용어조'] == '평서체':
                            MemoryNote = '\n※ 참고! [*원문]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 번역해주세요.'
                            BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                            BodyTranslationResponse = {'번역문': BodyToneEditingResponse['어조일치현재도서내용']}
                            BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                            pass
                        elif BodyTranslationCheckResponse['이전도서내용어조'] == '비격식체':
                            MemoryNote = '\n※ 참고! [*원문]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 번역해주세요.'
                            BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                            BodyTranslationResponse = {'번역문': BodyToneEditingResponse['어조일치현재도서내용']}
                            BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                            pass
                        
                if inputCount <= 4:                   
                    if Tone == 'Auto':
                        MemoryNote = ''
                    elif Tone == 'Formal':
                        MemoryNote = '\n※ 참고! [*원문]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
                    elif Tone == 'Normal':
                        MemoryNote = '\n※ 참고! [*원문]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요.'
                    elif Tone == 'Informal':
                        MemoryNote = '\n※ 참고! [*원문]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요.'
                    
                    ## BodyToneEditing ## BodyTranslation 만 예외 처리
                    ToneEditInput = BodyToneEditingInput(Tone, ToneCode, ProjectDataFrameBodyTranslationPath, BodyTranslationResponse)
                    BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview, memoryNote = MemoryNote)
                    BodyTranslationResponse = {'번역문': BodyToneEditingResponse['어조일치현재도서내용']}
                else:
                    MemoryNote = ''
                    
                #####################################
                ### Process8: BodyLanguageEditing ###
                #####################################
                LanguageEditingProcess = "BodyLanguageEditing"
                FinalLangCheck, LanguageEditInput, CurrentBodyLang = BodyLanguageEditingInput(projectName, Process, MainLang, MainLangCode, inputCount, TotalInputCount, ProjectDataFrameBodyTranslationPath, BodyTranslationResponse)
                
                if not FinalLangCheck:
                    BodyTranslationResponse = ProcessResponse(projectName, email, LanguageEditingProcess, LanguageEditInput, inputCount, TotalInputCount, BodyLanguageEditingFilter, CurrentBodyLang, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                CheckCount = BodyTranslationProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameBodyTranslationPath, BodyTranslationResponse, BodyTranslationCheckResponse, Process, inputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount)
                i += 1  # 다음 인덱스로 이동
            
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameBodyTranslationPath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
    
    ################################################
    ### Process9: TranslationEditing Response 생성 ##
    ################################################
    if Editing == 'on':
        ## Process 설정
        ProcessNumber = '09'
        Process = "TranslationEditing"
        ProofreadingBeforeProcess = Process
        ProofreadingBeforeProcessFileTag = "Editing"
        print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
        
        ## TranslationEditing 경로 생성
        ProjectDataFrameTranslationEditingPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

        ## Process Count 계산 및 Check
        CheckCount = "None" # 필터에서 데이터 체크가 필요한 카운트(여기서는 이전내용 체크)
        InputList = TranslationEditingInputList(TranslationEditPath, "BodyTranslationPreprocessing", "BodyTranslation")
        TotalInputCount = len(InputList) # 인풋의 전체 카운트
        InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationEditingPath)
        EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
        # print(f"InputCount: {InputCount}")
        # print(f"EditCheck: {EditCheck}")
        # print(f"EditCompletion: {EditCompletion}")
        ## Process 진행

        if Tone == 'Auto':
            MemoryNote = ''
        elif Tone == 'Formal':
            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
        elif Tone == 'Normal':
            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
        elif Tone == 'Informal':
            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요.'

        if not EditCheck:
            if DataFrameCompletion == 'No':
                i = InputCount - 1
                ErrorCount = 0
                while i < TotalInputCount:
                    inputCount = InputList[i]['Id']
                    ## LangCheck, BodyTranslationCheck이 3번 이상 일치가 되지 않으면 코드종료
                    if ErrorCount >= 3:
                        sys.exit(f"Project: {projectName} | Process: {Process}-BodyTranslationWordCheck {inputCount}/{TotalInputCount} | 오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
                    ## Input 생성
                    IndexId = InputList[i]['IndexId']
                    IndexTag = InputList[i]['IndexTag']
                    Index = InputList[i]['Index']
                    BodyId = InputList[i]['BodyId']
                    BracketedBody = InputList[i]['BracketedBody']
                    
                    ##########################################
                    ### Process8: BodyTranslationWordCheck ###
                    ##########################################
                    BodyTranslationWordCheckResponse = ProcessResponse(projectName, email, "BodyTranslationWordCheck", BracketedBody, inputCount, TotalInputCount, BodyTranslationWordCheckFilter, BracketedBody, "OpenAI", mode, MessagesReview)
                    Input1 = TranslationEditingAddInput(ProjectDataFrameTranslationEditingPath, ProjectDataFrameIndexTranslationPath, Tone)
                    Input2 = WordBracketCheckInput(IndexTag, Index, BracketedBody, BodyTranslationWordCheckResponse)
                    Input = Input1 + Input2
                    
                    ## Response 생성
                    TranslationEditingResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationEditingFilter, CheckCount, "OpenAI", mode, MessagesReview, memoryNote = MemoryNote)

                    #######################################################
                    ### Process8: BodyTranslationCheck, BodyToneEditing ###
                    #######################################################
                    BodyTranslationCheckResponse = {'현재도서내용어조': '모름'}
                    # print(f"\n\n\n\n\n\n\n\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@\ninputCount: {inputCount}")
                    # print(f"ToneDistinction: {ToneDistinction}\n@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n\n\n\n\n\n\n\n")
                    if inputCount >= 5 and ToneDistinction == 'Yes':
                        
                        ## BodyTranslationCheck, BodyToneEditing ##
                        CheckProcess = "BodyTranslationCheck"
                        ToneEditProcess = "BodyToneEditing"
                        LangCheck, CheckInput, ToneEditInput, BeforeCheck = BodyTranslationCheckAndBodyToneEditingInput(projectName, Process, ToneCode, inputCount, TotalInputCount, ProjectDataFrameTranslationEditingPath, TranslationEditingResponse)
                        BodyTranslationCheckResponse = ProcessResponse(projectName, email, CheckProcess, CheckInput, inputCount, TotalInputCount, BodyTranslationCheckFilter, CheckCount, "OpenAI", mode, MessagesReview)
                        
                        if not LangCheck:
                            MemoryNote = ''
                            if BeforeCheck == '격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
                            elif BeforeCheck == '평서체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
                            elif BeforeCheck == '비격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요.'
                            MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                            ErrorCount += 1
                            ## LangCheck의 경우는 3번 이상 일치가 되지 않으면 pass
                            if ErrorCount >= 3:
                                pass
                            else:
                                continue
                        BodyTranslationCheckResponse = ProcessResponse(projectName, email, CheckProcess, CheckInput, inputCount, TotalInputCount, BodyTranslationCheckFilter, CheckCount, "OpenAI", mode, MessagesReview)
                        if BeforeCheck != '모름':
                            if (BodyTranslationCheckResponse['이전도서내용어조'] == '모름' and BodyTranslationCheckResponse['현재도서내용어조'] == '모름') or (BodyTranslationCheckResponse['이전도서내용어조'] != BeforeCheck and BodyTranslationCheckResponse['현재도서내용어조'] != BeforeCheck):
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationEditingResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass
                        if BodyTranslationCheckResponse['어조일치여부'] == '불일치':
                            if BodyTranslationCheckResponse['이전도서내용어조'] == '모름':
                                if BodyTranslationCheckResponse['현재도서내용어조'] == BeforeCheck:
                                    pass
                                else:
                                    BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                    TranslationEditingResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                    BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                    pass
                            elif BodyTranslationCheckResponse['현재도서내용어조'] == '모름':
                                BodyTranslationCheckResponse['현재도서내용어조'] = BeforeCheck
                                pass
                            elif BodyTranslationCheckResponse['이전도서내용어조'] == '격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
                                MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationEditingResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass
                            elif BodyTranslationCheckResponse['이전도서내용어조'] == '평서체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
                                MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationEditingResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass
                            elif BodyTranslationCheckResponse['이전도서내용어조'] == '비격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요.'
                                MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationEditingResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass

                    if inputCount <= 4:
                        if Tone == 'Auto':
                            MemoryNote = ''
                        elif Tone == 'Formal':
                            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
                        elif Tone == 'Normal':
                            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
                        elif Tone == 'Informal':
                            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요.'
                    else:
                        MemoryNote = ''

                    ## DataFrame 저장
                    CheckCount = TranslationEditingProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationEditingPath, TranslationEditingResponse, BodyTranslationCheckResponse, Process, inputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount)
                    i += 1  # 다음 인덱스로 이동
                    ErrorCount = 0

            ## Edit 저장
            ProcessEditSave(ProjectDataFrameTranslationEditingPath, TranslationEditPath, Process, EditMode)
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
            
            if EditMode == "Manual":
                sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

        if EditMode == "Manual":
            if EditCheck:
                if not EditCompletion:
                    ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                    sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
        if EditCompletion:
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
    
    ####################################################
    ### Process9: TranslationRefinement Response 생성 ###
    ####################################################
    if Refinement == 'on':

        ## Process 설정
        ProcessNumber = '09'
        Process = "TranslationRefinement"
        ProofreadingBeforeProcess = Process
        ProofreadingBeforeProcessFileTag = "Refinement"
        print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
        
        ## TranslationRefinement 경로 생성
        ProjectDataFrameTranslationRefinementPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

        ## Process Count 계산 및 Check
        CheckCount = "None" # 필터에서 데이터 체크가 필요한 카운트(여기서는 이전내용 체크)
        InputList = TranslationEditingInputList(TranslationEditPath, "BodyTranslationPreprocessing", "TranslationEditing")
        TotalInputCount = len(InputList) # 인풋의 전체 카운트
        InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationRefinementPath)
        EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
        # print(f"InputCount: {InputCount}")
        # print(f"EditCheck: {EditCheck}")
        # print(f"EditCompletion: {EditCompletion}")
        ## Process 진행
        
        if Tone == 'Auto':
            MemoryNote = ''
        elif Tone == 'Formal':
            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
        elif Tone == 'Normal':
            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
        elif Tone == 'Informal':
            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요.'
            
        if not EditCheck:
            if DataFrameCompletion == 'No':
                i = InputCount - 1
                ErrorCount = 0
                while i < TotalInputCount:
                    inputCount = InputList[i]['Id']
                    ## LangCheck, BodyTranslationCheck이 3번 이상 일치가 되지 않으면 코드종료
                    if ErrorCount >= 3:
                        sys.exit(f"Project: {projectName} | Process: {Process}-BodyTranslationWordCheck {inputCount}/{TotalInputCount} | 오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
                    ## Input 생성
                    IndexId = InputList[i]['IndexId']
                    IndexTag = InputList[i]['IndexTag']
                    Index = InputList[i]['Index']
                    BodyId = InputList[i]['BodyId']
                    BracketedBody = InputList[i]['BracketedBody']
                    
                    ##########################################
                    ### Process8: BodyTranslationWordCheck ###
                    ##########################################
                    BodyTranslationWordCheckResponse = ProcessResponse(projectName, email, "BodyTranslationWordCheck", BracketedBody, inputCount, TotalInputCount, BodyTranslationWordCheckFilter, BracketedBody, "OpenAI", mode, MessagesReview)
                    Input1 = TranslationEditingAddInput(ProjectDataFrameTranslationRefinementPath, ProjectDataFrameIndexTranslationPath, Tone)
                    Input2 = WordBracketCheckInput(IndexTag, Index, BracketedBody, BodyTranslationWordCheckResponse)
                    Input = Input1 + Input2
                    
                    ## Response 생성
                    TranslationRefinementResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationEditingFilter, CheckCount, "OpenAI", mode, MessagesReview, memoryNote = MemoryNote)

                    #######################################################
                    ### Process8: BodyTranslationCheck, BodyToneEditing ###
                    #######################################################
                    BodyTranslationCheckResponse = {'현재도서내용어조': '모름'}
                    # print(f"\n\n\n\n\n\n\n\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@\ninputCount: {inputCount}")
                    # print(f"ToneDistinction: {ToneDistinction}\n@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n\n\n\n\n\n\n\n")
                    if inputCount >= 5 and ToneDistinction == 'Yes':
                        
                        ## BodyTranslationCheck, BodyToneEditing ##
                        CheckProcess = "BodyTranslationCheck"
                        ToneEditProcess = "BodyToneEditing"
                        LangCheck, CheckInput, ToneEditInput, BeforeCheck = BodyTranslationCheckAndBodyToneEditingInput(projectName, Process, ToneCode, inputCount, TotalInputCount, ProjectDataFrameTranslationRefinementPath, TranslationRefinementResponse)
                        BodyTranslationCheckResponse = ProcessResponse(projectName, email, CheckProcess, CheckInput, inputCount, TotalInputCount, BodyTranslationCheckFilter, CheckCount, "OpenAI", mode, MessagesReview)
                        
                        if not LangCheck:
                            MemoryNote = ''
                            if BeforeCheck == '격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
                            elif BeforeCheck == '평서체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
                            elif BeforeCheck == '비격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요.'
                            MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                            ErrorCount += 1
                            ## LangCheck의 경우는 3번 이상 일치가 되지 않으면 pass
                            if ErrorCount >= 3:
                                pass
                            else:
                                continue
                        BodyTranslationCheckResponse = ProcessResponse(projectName, email, CheckProcess, CheckInput, inputCount, TotalInputCount, BodyTranslationCheckFilter, CheckCount, "OpenAI", mode, MessagesReview)
                        if BeforeCheck != '모름':
                            if (BodyTranslationCheckResponse['이전도서내용어조'] == '모름' and BodyTranslationCheckResponse['현재도서내용어조'] == '모름') or (BodyTranslationCheckResponse['이전도서내용어조'] != BeforeCheck and BodyTranslationCheckResponse['현재도서내용어조'] != BeforeCheck):
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationRefinementResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass
                        if BodyTranslationCheckResponse['어조일치여부'] == '불일치':
                            if BodyTranslationCheckResponse['이전도서내용어조'] == '모름':
                                if BodyTranslationCheckResponse['현재도서내용어조'] == BeforeCheck:
                                    pass
                                else:
                                    BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                    TranslationRefinementResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                    BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                    pass
                            elif BodyTranslationCheckResponse['현재도서내용어조'] == '모름':
                                BodyTranslationCheckResponse['현재도서내용어조'] = BeforeCheck
                                pass
                            elif BodyTranslationCheckResponse['이전도서내용어조'] == '격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
                                MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationRefinementResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass
                            elif BodyTranslationCheckResponse['이전도서내용어조'] == '평서체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
                                MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationRefinementResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass
                            elif BodyTranslationCheckResponse['이전도서내용어조'] == '비격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요.'
                                MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationRefinementResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass

                    if inputCount <= 4:
                        if Tone == 'Auto':
                            MemoryNote = ''
                        elif Tone == 'Formal':
                            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
                        elif Tone == 'Normal':
                            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
                        elif Tone == 'Informal':
                            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요.'
                    else:
                        MemoryNote = ''

                    ## DataFrame 저장
                    CheckCount = TranslationRefinementProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationRefinementPath, TranslationRefinementResponse, BodyTranslationCheckResponse, Process, inputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount)
                    i += 1  # 다음 인덱스로 이동
                    ErrorCount = 0

            ## Edit 저장
            ProcessEditSave(ProjectDataFrameTranslationRefinementPath, TranslationEditPath, Process, EditMode)
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
            
            if EditMode == "Manual":
                sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

        if EditMode == "Manual":
            if EditCheck:
                if not EditCompletion:
                    ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                    sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
        if EditCompletion:
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")

    ################################################################
    ### Process9: TranslationKinfolkStyleRefinement Response 생성 ###
    ################################################################
    if KinfolkStyleRefinement == 'on':

        ## Process 설정
        ProcessNumber = '09'
        Process = "TranslationKinfolkStyleRefinement"
        ProofreadingBeforeProcess = Process
        ProofreadingBeforeProcessFileTag = "KinfolkStyleRefinement"
        print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
        
        ## TranslationKinfolkStyleRefinement 경로 생성
        ProjectDataFrameTranslationKinfolkStyleRefinementPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

        ## Process Count 계산 및 Check
        CheckCount = "None" # 필터에서 데이터 체크가 필요한 카운트(여기서는 이전내용 체크)
        InputList = TranslationEditingInputList(TranslationEditPath, "BodyTranslationPreprocessing", "TranslationEditing")
        TotalInputCount = len(InputList) # 인풋의 전체 카운트
        InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationKinfolkStyleRefinementPath)
        EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
        # print(f"InputCount: {InputCount}")
        # print(f"EditCheck: {EditCheck}")
        # print(f"EditCompletion: {EditCompletion}")
        ## Process 진행
        
        if Tone == 'Auto':
            MemoryNote = ''
        elif Tone == 'Formal':
            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
        elif Tone == 'Normal':
            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
        elif Tone == 'Informal':
            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요. 서술문을 반말인 구어체로 작성하는 겁니다.'

            
        if not EditCheck:
            if DataFrameCompletion == 'No':
                i = InputCount - 1
                ErrorCount = 0
                while i < TotalInputCount:
                    inputCount = InputList[i]['Id']
                    ## LangCheck, BodyTranslationCheck이 3번 이상 일치가 되지 않으면 코드종료
                    if ErrorCount >= 3:
                        sys.exit(f"Project: {projectName} | Process: {Process}-BodyTranslationWordCheck {inputCount}/{TotalInputCount} | 오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
                    ## Input 생성
                    IndexId = InputList[i]['IndexId']
                    IndexTag = InputList[i]['IndexTag']
                    Index = InputList[i]['Index']
                    BodyId = InputList[i]['BodyId']
                    BracketedBody = InputList[i]['BracketedBody']
                    
                    ##########################################
                    ### Process8: BodyTranslationWordCheck ###
                    ##########################################
                    BodyTranslationWordCheckResponse = ProcessResponse(projectName, email, "BodyTranslationWordCheck", BracketedBody, inputCount, TotalInputCount, BodyTranslationWordCheckFilter, BracketedBody, "OpenAI", mode, MessagesReview)
                    Input1 = TranslationKinfolkStyleRefinementAddInput(ProjectDataFrameTranslationKinfolkStyleRefinementPath, Tone)
                    Input2 = WordBracketCheckKinfolkStyleInput(BracketedBody, BodyTranslationWordCheckResponse)
                    Input = Input1 + Input2
                    
                    ## Response 생성
                    TranslationKinfolkStyleRefinementResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationEditingFilter, CheckCount, "OpenAI", mode, MessagesReview, memoryNote = MemoryNote)

                    #######################################################
                    ### Process8: BodyTranslationCheck, BodyToneEditing ###
                    #######################################################
                    BodyTranslationCheckResponse = {'현재도서내용어조': '모름'}
                    # print(f"\n\n\n\n\n\n\n\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@\ninputCount: {inputCount}")
                    # print(f"ToneDistinction: {ToneDistinction}\n@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n\n\n\n\n\n\n\n")
                    if inputCount >= 5 and ToneDistinction == 'Yes':
                        
                        ## BodyTranslationCheck, BodyToneEditing ##
                        CheckProcess = "BodyTranslationCheck"
                        ToneEditProcess = "BodyToneEditing"
                        LangCheck, CheckInput, ToneEditInput, BeforeCheck = BodyTranslationCheckAndBodyToneEditingInput(projectName, Process, ToneCode, inputCount, TotalInputCount, ProjectDataFrameTranslationKinfolkStyleRefinementPath, TranslationKinfolkStyleRefinementResponse)
                        BodyTranslationCheckResponse = ProcessResponse(projectName, email, CheckProcess, CheckInput, inputCount, TotalInputCount, BodyTranslationCheckFilter, CheckCount, "OpenAI", mode, MessagesReview)
                        
                        if not LangCheck:
                            MemoryNote = ''
                            if BeforeCheck == '격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
                            elif BeforeCheck == '평서체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
                            elif BeforeCheck == '비격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요.'
                            MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                            ErrorCount += 1
                            ## LangCheck의 경우는 3번 이상 일치가 되지 않으면 pass
                            if ErrorCount >= 3:
                                pass
                            else:
                                continue
                        BodyTranslationCheckResponse = ProcessResponse(projectName, email, CheckProcess, CheckInput, inputCount, TotalInputCount, BodyTranslationCheckFilter, CheckCount, "OpenAI", mode, MessagesReview)
                        if BeforeCheck != '모름':
                            if (BodyTranslationCheckResponse['이전도서내용어조'] == '모름' and BodyTranslationCheckResponse['현재도서내용어조'] == '모름') or (BodyTranslationCheckResponse['이전도서내용어조'] != BeforeCheck and BodyTranslationCheckResponse['현재도서내용어조'] != BeforeCheck):
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationKinfolkStyleRefinementResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass
                        if BodyTranslationCheckResponse['어조일치여부'] == '불일치':
                            if BodyTranslationCheckResponse['이전도서내용어조'] == '모름':
                                if BodyTranslationCheckResponse['현재도서내용어조'] == BeforeCheck:
                                    pass
                                else:
                                    BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                    TranslationKinfolkStyleRefinementResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                    BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                    pass
                            elif BodyTranslationCheckResponse['현재도서내용어조'] == '모름':
                                BodyTranslationCheckResponse['현재도서내용어조'] = BeforeCheck
                                pass
                            elif BodyTranslationCheckResponse['이전도서내용어조'] == '격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
                                MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationKinfolkStyleRefinementResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass
                            elif BodyTranslationCheckResponse['이전도서내용어조'] == '평서체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
                                MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationKinfolkStyleRefinementResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass
                            elif BodyTranslationCheckResponse['이전도서내용어조'] == '비격식체':
                                MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요.'
                                MemoryNote += f'\n※ 참고! [*편집할내용]을 편집할때는 ((({MainLangCode}))), 단 하나의 언어만 사용해서 전체를 작성합니다. 다른 언어가 존재하면 ((({MainLangCode})))로 번역해야 합니다. 이 외의 언어는 일체 작성하지 않습니다.'
                                BodyToneEditingResponse = ProcessResponse(projectName, email, ToneEditProcess, ToneEditInput, inputCount, TotalInputCount, BodyToneEditingFilter, ToneCode, "OpenAI", mode, MessagesReview)
                                TranslationKinfolkStyleRefinementResponse = {'내용': BodyToneEditingResponse['어조일치현재도서내용']}
                                BodyTranslationCheckResponse['현재도서내용어조'] = BodyToneEditingResponse['이전도서어조']
                                pass

                    if inputCount <= 4:
                        if Tone == 'Auto':
                            MemoryNote = ''
                        elif Tone == 'Formal':
                            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **격식체 ->>> (((습니다. 입니다. 합니다. ... 등))) 로 작성해주세요.'
                        elif Tone == 'Normal':
                            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **평서체 ->>> (((이다. 한다. 있다. ... 등))) 로 작성해주세요. 그렇다고 서술문을 (했어. 이었어. ... 등)의 구어체로 작성하면 안됩니다.'
                        elif Tone == 'Informal':
                            MemoryNote = '\n※ 참고! [*편집할내용]의 **서술문(내레이션이라 하며 대화문, 인용문 이외에 내용을 서술하는 문장)은 **비격식체 ->>> (((이었어. 했어. 있어. ... 등)))인 반말로 작성해주세요. 서술문을 반말인 구어체로 작성하는 겁니다.'
                    else:
                        MemoryNote = ''

                    ## DataFrame 저장
                    CheckCount = TranslationKinfolkStyleRefinementProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationKinfolkStyleRefinementPath, TranslationKinfolkStyleRefinementResponse, BodyTranslationCheckResponse, Process, inputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount)
                    i += 1  # 다음 인덱스로 이동
                    ErrorCount = 0

            ## Edit 저장
            ProcessEditSave(ProjectDataFrameTranslationKinfolkStyleRefinementPath, TranslationEditPath, Process, EditMode)
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
            
            if EditMode == "Manual":
                sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

        if EditMode == "Manual":
            if EditCheck:
                if not EditCompletion:
                    ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                    sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
        if EditCompletion:
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")

    ######################################################
    ### Process10: TranslationProofreading Response 생성 ##
    ######################################################

    ## Process 설정
    ProcessNumber = '10'
    Process = "TranslationProofreading"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## TranslationProofreading 경로 생성
    ProjectDataFrameTranslationProofreadingPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = "None" # 필터에서 데이터 체크가 필요한 카운트(여기서는 이전내용 체크)
    InputList, InputListLength = TranslationProofreadingInputList(TranslationEditPath, ProofreadingBeforeProcess)
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationProofreadingPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, InputListLength)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                IndexId = InputList[i]['IndexId']
                IndexTag = InputList[i]['IndexTag']
                Index = InputList[i]['Index']
                BodyId = InputList[i]['BodyId']
                Body = InputList[i]['Body']
                Input1 = TranslationProofreadingAddInput(ProjectDataFrameTranslationProofreadingPath)
                Input2 = InputList[i]['Input']
                Input = Input1 + Input2
                MemoryNote = '\n※ 참고! 교정 작업의 대상은 <**작업: 교정할도서내용> 입니다. <교정도서내용.json>에 <참고: 이전교정도서내용>은 포함하지 마세요.'
                
                ## Response 생성
                TranslationProofreadingResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationProofreadingFilter, InputList[i]['Body'], "OpenAI", mode, MessagesReview, memoryNote = MemoryNote)
                
                ## ErrorPass 예외처리
                if TranslationProofreadingResponse == "ErrorPass":
                    TranslationProofreadingResponse = {'도서내용': ' ' + Body}
                
                ## DataFrame 저장
                CheckCount = TranslationProofreadingProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationProofreadingPath, TranslationProofreadingResponse, Process, inputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameTranslationProofreadingPath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        ## EditText 저장
        ProcessEditTextSave(projectName, MainLang, BookGenre, ProjectMasterTranslationPath, TranslationEditPath, "TranslationBodySplit", "IndexTranslation", Process, ProofreadingBeforeProcessFileTag)
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")

    ##########################################################
    ### Process11: TranslationDialogueAnalysis Response 생성 ##
    ##########################################################

    if BookGenre == 'Fiction':

        ## Process 설정
        ProcessNumber = '11'
        Process = "TranslationDialogueAnalysis"
        print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
        
        ## TranslationDialogueAnalysis 경로 생성
        ProjectDataFrameTranslationDialogueAnalysisPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')
        
        ## Process Count 계산 및 Check
        CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
        InputList = TranslationDialogueAnalysisInputList(projectName, Process, ProjectDataFrameTranslationProofreadingPath, TranslationEditPath, "TranslationProofreading")
        TotalInputCount = len(InputList) # 인풋의 전체 카운트
        InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationDialogueAnalysisPath)
        EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
        # print(f"InputCount: {InputCount}")
        # print(f"EditCheck: {EditCheck}")
        # print(f"EditCompletion: {EditCompletion}")
        ## Process 진행
        if not EditCheck:
            if DataFrameCompletion == 'No':
                for i in range(InputCount - 1, TotalInputCount):
                    inputCount = InputList[i]['Id']
                    BodyId = InputList[i]['BodyId']
                    Body = InputList[i]['Body']
                    MarkBody = InputList[i]['MarkBody']
                    CheckCount = InputList[i]['DialogueCount']
                    ## Body내에 대화문이 있는지 체크
                    if CheckCount > 0:
                        ## Input 생성
                        Input1 = TranslationDialogueAnalysisAddInput(ProjectDataFrameTranslationDialogueAnalysisPath)
                        Input2 = InputList[i]['Input']
                        Input = Input1 + Input2
                        MemoryNote = f'\n※ 주의사항: <대화내용편집.json>으로 완성될 대화문은 <**작업: 대화중심편집내용>의 {{n 대화: 대화내용}} {CheckCount}개 입니다.'

                        ## Response 생성
                        TranslationDialogueAnalysisResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationDialogueAnalysisFilter, CheckCount, "OpenAI", mode, MessagesReview, memoryNote = MemoryNote)
                    else:
                        TranslationDialogueAnalysisResponse = []
                        
                    ## DataFrame 저장
                    TranslationDialogueAnalysisProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationDialogueAnalysisPath, MarkBody, TranslationDialogueAnalysisResponse, Process, inputCount, BodyId, Body, TotalInputCount)
                    
            ## Edit 저장
            ProcessEditSave(ProjectDataFrameTranslationDialogueAnalysisPath, TranslationEditPath, Process, EditMode)
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
            
            if EditMode == "Manual":
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}\n\n1. TranslationDialogueAnalysis와 TranslationDialogueAnalysisCharacter를 비교하여, 미비한 인물 부분을 수정합니다. 이 경우 'Body'와 'DialogueBody'와 'BodyCharacterList'를 모두 수정해야 합니다.\n2. {{인물이름: 대화내용}} 중에 잘못된 표기나 괄호 묶음을 수정합니다. 이 경우 'Body'와 'DialogueBody' 모두 수정해야 합니다.\n\n")

        if EditMode == "Manual":
            if EditCheck:
                if not EditCompletion:
                    ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                    sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}\n\n1. TranslationDialogueAnalysis와 TranslationDialogueAnalysisCharacter를 비교하여, 미비한 인물 부분을 수정합니다. 이 경우 'Body'와 'DialogueBody'와 'BodyCharacterList'를 모두 수정해야 합니다.\n2. {{인물이름: 대화내용}} 중에 잘못된 표기나 괄호 묶음을 수정합니다. 이 경우 'Body'와 'DialogueBody' 모두 수정해야 합니다.\n\n")
        if EditCompletion:
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
        
    #########################################################
    ### Process12: TranslationDialogueEditing Response 생성 ##
    #########################################################
    
    if BookGenre == 'Fiction':

        ## Process 설정
        ProcessNumber = '12'
        Process = "TranslationDialogueEditing"
        ProofreadingBeforeProcess = Process
        ProofreadingBeforeProcessFileTag = ProofreadingBeforeProcessFileTag + "-DialogueEdit"
        print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
        
        ## TranslationDialogueEditing 경로 생성
        ProjectDataFrameTranslationDialogueEditingPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

        ## Process Count 계산 및 Check
        CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
        InputList = TranslationDialogueEditingInputList(TranslationEditPath, "TranslationProofreading", "TranslationDialogueAnalysis")
        TotalInputCount = len(InputList) # 인풋의 전체 카운트
        InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationDialogueEditingPath)
        EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
        # print(f"InputCount: {InputCount}")
        # print(f"EditCheck: {EditCheck}")
        # print(f"EditCompletion: {EditCompletion}")
        # Process 진행
        if not EditCheck:
            if DataFrameCompletion == 'No':
                for i in range(InputCount - 1, TotalInputCount):
                    inputCount = InputList[i]['Id']
                    IndexId = InputList[i]['IndexId']
                    IndexTag = InputList[i]['IndexTag']
                    Index = InputList[i]['Index']
                    BodyId = InputList[i]['BodyId']
                    Body = InputList[i]['Body']
                    MarkBody = InputList[i]['MarkBody']
                    CheckCount = {"CheckCount": InputList[i]['DialogueCount'], "CheckList": InputList[i]['CheckCharacterList']}
                    CharacterList = InputList[i]['CharacterList']
                    # Body내에 대화문이 있는지 체크
                    if CheckCount['CheckCount'] > 0:
                        ## Input 생성
                        Input1 = TranslationDialogueEditingAddInput(ProjectDataFrameTranslationDialogueEditingPath, CharacterList)
                        Input2 = InputList[i]['Input']
                        Input = Input1 + Input2
                        MemoryNote = f"\n※ 주의사항: <대화내용편집.json>으로 완성될 대화문은 <**작업: 대화중심편집내용>의 {{n 대화: 대화내용}} {CheckCount['CheckCount']}개 입니다.\n※ 주의사항: 특수한 경우 이외에는 \'현재말의높임법\' 표기에 따라서 이에 맞는 말의 높임법대로 '편집대화내용'이 작성되어야 합니다."

                        ## Response 생성
                        TranslationDialogueEditingResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationDialogueEditingFilter, CheckCount, "OpenAI", mode, MessagesReview, memoryNote = MemoryNote)
                    else:
                        TranslationDialogueEditingResponse = []

                    ## DataFrame 저장
                    TranslationDialogueEditingProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationDialogueEditingPath, MarkBody, TranslationDialogueEditingResponse, Process, inputCount, IndexId, IndexTag, Index, BodyId, Body, CharacterList, TotalInputCount)
                    
            ## Edit 저장
            ProcessEditSave(ProjectDataFrameTranslationDialogueEditingPath, TranslationEditPath, Process, EditMode)
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
            
            ## EditText 저장
            ProcessEditTextSave(projectName, MainLang, BookGenre, ProjectMasterTranslationPath, TranslationEditPath, "TranslationBodySplit", "IndexTranslation", Process, ProofreadingBeforeProcessFileTag)
            
            if EditMode == "Manual":
                sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

        if EditMode == "Manual":
            if EditCheck:
                if not EditCompletion:
                    ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                    sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
        if EditCompletion:
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")

    ##########################################################
    ### Process14: AfterTranslationBodySummary Response 생성 ##
    ##########################################################

    ## Process 설정
    ProcessNumber = '14'
    Process = "AfterTranslationBodySummary"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## AfterTranslationBodySummary 경로 생성
    ProjectDataFrameAfterTranslationBodySummaryPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = TranslationBodySummaryInputList(TranslationEditPath, "TranslationProofreading")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameAfterTranslationBodySummaryPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                IndexId = InputList[i]['IndexId']
                Input1 = TranslationBodySummaryAddInput(ProjectDataFrameAfterTranslationBodySummaryPath, MainLangCode)
                Input2 = InputList[i]['Input']
                Input = Input1 + Input2

                ## 현재내용의 길이가 1000자 초과인 경우만 요약
                if len(Input2) <= 500:
                    Body = InputList[i]['Body']
                    AfterTranslationBodySummaryResponse = {"요약": Body, "핵심문구": ['None'], "중요도": 900}
                else:
                    ## Response 생성
                    AfterTranslationBodySummaryResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationBodySummaryFilter, CheckCount, "OpenAI", mode, MessagesReview)

                ## DataFrame 저장
                AfterTranslationBodySummaryProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameAfterTranslationBodySummaryPath, AfterTranslationBodySummaryResponse, Process, inputCount, IndexId, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameAfterTranslationBodySummaryPath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
    
    #############################################
    ### Process15: AuthorResearch Response 생성 ##
    #############################################
    
    ## Process 설정
    ProcessNumber = '15'
    Process = "AuthorResearch"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## AuthorResearch 경로 생성
    ProjectDataFrameAuthorResearchPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')
    
    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = AuthorResearchInputList(TranslationEditPath, "TranslationBodySplit", "IndexTranslation", "AfterTranslationBodySummary", MainLangCode)
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameAuthorResearchPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                Input = InputList[i]['Input']
                
                ## Response 생성
                AuthorResearchResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, AuthorResearchFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                AuthorResearchProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameAuthorResearchPath, AuthorResearchResponse, Process, inputCount, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameAuthorResearchPath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")

    #####################################################
    ### Process16: TranslationCatchphrase Response 생성 ##
    #####################################################
    
    ## Process 설정
    ProcessNumber = '16'
    Process = "TranslationCatchphrase"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## TranslationCatchphrase 경로 생성
    ProjectDataFrameTranslationCatchphrasePath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')
    
    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = TranslationCatchphraseInputList(TranslationEditPath, "IndexTranslation", "AfterTranslationBodySummary", "AuthorResearch", MainLangCode)
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationCatchphrasePath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                Input = InputList[i]['Input']
                
                ## Response 생성
                TranslationCatchphraseResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationCatchphraseFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                TranslationCatchphraseProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationCatchphrasePath, TranslationCatchphraseResponse, Process, inputCount, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameTranslationCatchphrasePath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        ## BookCopyText 저장
        BookCopyTextSave(projectName, MainLang, ProjectMasterTranslationPath, TranslationEditPath, "AuthorResearch", "TranslationCatchphrase")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")
        
    ############################################################
    ### Process17: TranslationFundingCatchphrase Response 생성 ##
    ############################################################
    
    ## Process 설정
    ProcessNumber = '17'
    Process = "TranslationFundingCatchphrase"
    print(f"< User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 시작 >")
    
    ## TranslationFundingCatchphrase 경로 생성
    ProjectDataFrameTranslationFundingCatchphrasePath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')
    
    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = TranslationCatchphraseInputList(TranslationEditPath, "IndexTranslation", "AfterTranslationBodySummary", "AuthorResearch", MainLangCode)
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationFundingCatchphrasePath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                Input = InputList[i]['Input']
                
                ## Response 생성
                TranslationFundingCatchphraseResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationFundingCatchphraseFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                TranslationFundingCatchphraseProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationFundingCatchphrasePath, TranslationFundingCatchphraseResponse, Process, inputCount, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameTranslationFundingCatchphrasePath, TranslationEditPath, Process, EditMode)
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
        
        ## BookCopyText 저장
        BookFundingCopyTextSave(projectName, MainLang, ProjectMasterTranslationPath, TranslationEditPath, "TranslationFundingCatchphrase")
        
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
    if EditCompletion:
        print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '250121_테스트'
    Intention = "Similarity"
    #########################################################################
    # BookScriptGenProcessUpdate(ProjectName, email, Intention)