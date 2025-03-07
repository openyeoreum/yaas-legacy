import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from datetime import datetime
from backend.b2_Solution.b25_DataFrame.b251_DataCommit.b2511_LLMLoad import OpenAI_LLMresponse, ANTHROPIC_LLMresponse

##########################################
##### Translation Index, Body 불러오기 #####
##########################################
## Load1: TranslationIndex 불러오기
def LoadTranslationIndex(projectName, UploadTranslationFilePath):
    # TranslationIndex 경로 설정
    TranslationIndexFileName = f"{projectName}_Index(Translation).txt"
    TranslationIndexFilePath = os.path.join(UploadTranslationFilePath, TranslationIndexFileName)
    
    # TranslationIndex 불러오기
    if os.path.exists(TranslationIndexFilePath):
        with open(TranslationIndexFilePath, "r") as TranslationIndexFile:
            TranslationIndex = TranslationIndexFile.read()
    else:
        sys.exit(f"\n\n[ ((({projectName}_Index(Translation).txt))), ((({projectName}_Body(Translation).txt))) 파일을 완성하여 아래 경로에 복사해주세요. ]\n({UploadTranslationFilePath})\n\n1. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n3. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차는 <제목>의 형태로 괄호처리 권장\n3. 본문((_Body(Translation)))파일 내 쌍따옴표(“대화문”의 완성) 개수 일치\n\n")
        
    return TranslationIndex

## Load2: TranslationSplitBody 불러오기
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
    else:
        sys.exit(f"\n\n[ ((({projectName}_Index(Translation).txt))), ((({projectName}_Body(Translation).txt))) 파일을 완성하여 아래 경로에 복사해주세요. ]\n({UploadTranslationFilePath})\n\n1. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n3. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차는 <제목>의 형태로 괄호처리 권장\n3. 본문((_Body(Translation)))파일 내 쌍따옴표(“대화문”의 완성) 개수 일치\n\n")
        
    return TranslationIndex, TranslationBody, TranslationBodyFilePath

########################################
##### TranslationBodySplit Process #####
########################################
## Process1: TranslationBodySplit Process
def TranslationBodySplitProcess(projectName, UploadTranslationFilePath, TranslationEditPath, BeforeProcess, MaxLength):
    TranslationIndex, TranslationBody, TranslationBodyFilePath = LoadTranslationSplitBody(projectName, UploadTranslationFilePath, TranslationEditPath, BeforeProcess)
    
    ## Load2-1: BodyLines과 TranslationIndex 위치 찾기
    BodyLines = TranslationBody.splitlines()
    IndexPositions = []
    CurrentIndexIdx = 0
    for lineNum, BodyLine in enumerate(BodyLines):
        # 현재 처리 중인 목차 항목 가져오기
        if CurrentIndexIdx < len(TranslationIndex):
            CurrentIndex = TranslationIndex[CurrentIndexIdx]
            # 현재 줄이 목차 항목과 정확히 일치하는지 확인
            if BodyLine.strip() == CurrentIndex["Index"].strip():
                # 일치하는 줄을 찾았으므로 위치 기록
                IndexPositions.append((lineNum, CurrentIndex))
                # 다음 목차 항목으로 이동
                CurrentIndexIdx += 1
    ## Load2-2: Index와 Body 불일치로 이한 인덱스 누락 확인
    if CurrentIndexIdx != len(TranslationIndex):
        sys.exit(f"Index 불일치 오류 발생: Project: {projectName} | Process: TranslationBodySplit | IndexMatchingError\n[ 아래 _Body(Translation).txt 또는 Edit에서 해당 목차 부분 확인 >> ((({CurrentIndex['Index']}))) ]\n\n{TranslationBodyFilePath}\n\n{TranslationEditPath}")

    ## Load2-3: SplitedTranslationBody 생성
    SplitedTranslationBody = []
    BodyId = 1
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
        
        # 섹션이 4,000자를 초과하는지 확인
        if len(SectionText) <= MaxLength:
            SplitedTranslationBody.append({"IndexId": IndexId, "IndexTag": IndexTag, "Index": IndexText, "BodyId": BodyId, "Body": SectionText})
            BodyId += 1
        else:
            # 섹션이 4,000자를 초과하면 문장 단위로 추가 분할
            SubSections = SplitBySentence(SectionText, MaxLength)
            for sub_text in SubSections:
                SplitedTranslationBody.append({"IndexId": IndexId, "IndexTag": IndexTag, "Index": IndexText, "BodyId": BodyId, "Body": sub_text})
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
    CleanOriginalText = re.sub(r'\s+', '', OriginalText)
    OriginalCount = len(CleanOriginalText)
    
    # 분할된 본문의 모든 문자 결합 후 공백 제거
    SplitedBodyText = ''.join(TranslationBodyDic["Body"] for TranslationBodyDic in SplitedTranslationBody)
    CleanSplitedBodyText = re.sub(r'\s+', '', SplitedBodyText)
    SplitCount = len(CleanSplitedBodyText)
    
    # 최종 글자수 일치 확인
    if OriginalCount == SplitCount:
        return SplitedTranslationBody
    else:
        sys.exit(f"TranslationSplitBody 길이 불일치 오류 발생: Project: {projectName} | Process: TranslationBodySplit | SplitBodyLengthError\n[ 분할 전후 텍스트 수가 다름 (분할전: {OriginalCount} != 분할후: {SplitCount}) ]")

## MaxLength 이상인 경우 분할 함수
def SplitBySentence(SectionText, MaxLength):
    # Define sentence delimiters
    SentenceDelimiters = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
    # Split SectionText into sentences
    sentences = []
    start = 0
    i = 0
    while i < len(SectionText):
        FoundDelimiter = False
        for delimiter in SentenceDelimiters:
            if i + len(delimiter) <= len(SectionText) and SectionText[i:i+len(delimiter)] == delimiter:
                # End of a sentence found
                sentences.append(SectionText[start:i+len(delimiter)])  # Include the delimiter
                start = i + len(delimiter)
                i = start - 1  # Will be incremented in the outer loop
                FoundDelimiter = True
                break

        if not FoundDelimiter:
            i += 1
            
    # Add the last part if any
    if start < len(SectionText):
        sentences.append(SectionText[start:])
        
    # If we have no sentences (no delimiters found), return the SectionText as a single segment
    if not sentences:
        return [SectionText]
    
    # Calculate the optimal number of segments
    TotalChars = len(SectionText)
    NumSegments = max(1, (TotalChars + MaxLength - 1) // MaxLength)  # At least 1 segment
    
    # Calculate target size for each segment for balanced splitting
    target_size = TotalChars / NumSegments
    
    # Group sentences into segments to achieve target size
    segments = []
    CurrentSegment = ""
    
    for sentence in sentences:
        potential_length = len(CurrentSegment) + len(sentence)
        
        if potential_length <= MaxLength:
            # 현재 세그먼트에 문장을 추가했을 때 목표 크기에 더 가까워지는지 확인
            if (not CurrentSegment or 
                abs(potential_length - target_size) < abs(len(CurrentSegment) - target_size)):
                CurrentSegment += sentence
            else:
                segments.append(CurrentSegment)
                CurrentSegment = sentence
        else:
            if CurrentSegment:
                segments.append(CurrentSegment)
            CurrentSegment = sentence
    
    # Add the last segment if any
    if CurrentSegment:
        if segments and len(segments[-1]) + len(CurrentSegment) <= MaxLength:
            segments[-1] += CurrentSegment
        else:
            segments.append(CurrentSegment)
    
    return segments

## Load3: MainLang, Translation 불러오기
def LoadTranslation(Translation, ProjectDataFrameTranslationIndexDefinePath):
    with open(ProjectDataFrameTranslationIndexDefinePath, 'r', encoding = 'utf-8') as TranslationIndexDefineJson:
        TranslationIndexDefine = json.load(TranslationIndexDefineJson)
    
    if Translation in ['auto', 'Auto']:
        Translation = TranslationIndexDefine[0]['Translation']
    elif Translation.lower() not in ['en', 'zh', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'pt', 'ru', 'ar', 'nl', 'sv', 'no', 'da', 'fi', 'pl', 'tr', 'el', 'cs', 'hu', 'ro', 'sk', 'uk', 'hi', 'id', 'ms', 'th', 'vi', 'he', 'bg', 'ca']:
        Translation = TranslationIndexDefine[0]['Translation']
        
    return Translation

#####################
##### Input 생성 #####
#####################
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

## Process1: TranslationIndexDefine의 InputList
def TranslationIndexDefineInputList(projectName, UploadTranslationFilePath):
    IndexTranslation = LoadTranslationIndex(projectName, UploadTranslationFilePath)
    InputList = []
    
    InputId = 1
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
    for i, TranslationIndex in enumerate(TranslationIndexDefine):
        IndexId = TranslationIndex['IndexId']
        IndexTag = TranslationIndex['IndexTag']
        Index = TranslationIndex['Index']
        BodySummary = ''
        for TranslationBody in TranslationBodySummary:
            if TranslationBody['IndexId'] == TranslationIndex['IndexId']:
                BodySummary += TranslationBody['BodySummary']
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
            Marker = f"__MARKER_{i}__"
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
        
        Input = f"<현재번역할내용>\n[현재번역세부목차]\n{IndexTag}: {Index}\n\n[원문]\n{Body}\n\n"
        
        InputList.append({"Id": InputId, "IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "Input": Input})
        InputId += 1
    
    return InputList

## Process8: BodyTranslation의 추가 Input
def BodyTranslationAddInput(ProjectDataFrameBodyTranslationPath, ProjectDataFrameIndexTranslationPath, MainLangCode, TranslationLangCode):
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
        AddInput = f"[원문언어] {TranslationLangCode}\n[번역언어] {MainLangCode}\n\n[도서전체목차]\n{IndexText}\n\n[이전번역문]\nNone\n\n\n"
        
    return AddInput

## Process8: BodyTranslationCheck의 Input
def BodyTranslationCheckInput(ProjectDataFrameBodyTranslationPath, BodyTranslationResponse):
    if os.path.exists(ProjectDataFrameBodyTranslationPath):
        with open(ProjectDataFrameBodyTranslationPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
            BodyTranslation = json.load(TranslationDataFrame)[1]
        BeforeBodyTranslation = BodyTranslation[-1]['Body']
        CurrentBodyTranslation = BodyTranslationResponse['번역문']
        
        CheckInput = f"{BeforeBodyTranslation}\n\n\n<현재도서내용>\n{CurrentBodyTranslation}\n"
        Index = max(-len(BodyTranslation), -3)
        BeforeCheck = BodyTranslation[Index]['Body']
        
    return CheckInput, BeforeCheck

## Process9: TranslationEditing의 InputList
def TranslationEditingInputList(TranslationEditPath, BeforeProcess1, BeforeProcess2):
    ## BracketedBodyGen 함수
    def BracketedBodyGen(OriginalBody, TranslationBody):
        # OriginalBody에서 {원문->번역어} 형태의 패턴 추출
        TranslationPairs = re.findall(r'\{(.*?)->(.*?)\}', OriginalBody)
        
        # 번역된 단어의 길이를 기준으로 내림차순 정렬 (긴 단어부터 처리)
        # 이는 한 단어가 다른 단어의 부분 문자열인 경우 중첩 괄호 문제를 방지
        TranslationPairs.sort(key=lambda x: len(x[1]), reverse=True)
        
        # 번역된 텍스트의 복사본 생성
        BracketedBody = TranslationBody
        
        # 각 번역 쌍에 대해 번역된 단어를 {번역된 단어} 형태로
        for OriginalWord, TranslatedWord in TranslationPairs:
            BracketedBody = BracketedBody.replace(TranslatedWord, f'{{{TranslatedWord}}}')
        
        BracketedBody = BracketedBody.replace('{{{{', '{').replace('}}}}', '}')
        BracketedBody = BracketedBody.replace('{{{', '{').replace('}}}', '}')
        BracketedBody = BracketedBody.replace('{{', '{').replace('}}', '}')
        
        return BracketedBody
    
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
        
        Input = f"<현재편집전내용>\n[편집할내용의목차]\n{IndexTag}: {Index}\n\n[편집할내용]\n{BracketedBody}\n\n"
        
        InputList.append({"Id": InputId, "IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "Input": Input})
        InputId += 1
    
    return InputList

## Process9: TranslationEditing의 추가 Input
def TranslationEditingAddInput(ProjectDataFrameTranslationEditingPath, ProjectDataFrameIndexTranslationPath):
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
    
    ## <현재편집전내용> 생성
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
        AddInput = f"[도서전체목차]\n{IndexText}\n\n[이전편집내용]\nNone\n\n\n"
        
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
        
        Input = f"<교정할도서내용>\n{Body}\n\n"
        
        InputList.append({"Id": InputId, "IndexId": IndexId, "IndexTag": IndexTag, "Index": Index, "BodyId": BodyId, "Body": Body, "Input": Input})
        InputId += 1
    
    return InputList
    
def TranslationProofreadingAddInput(ProjectDataFrameTranslationProofreadingPath):
    if os.path.exists(ProjectDataFrameTranslationProofreadingPath):
        with open(ProjectDataFrameTranslationProofreadingPath, 'r', encoding = 'utf-8') as TranslationDataFrame:
            TranslationProofreading = json.load(TranslationDataFrame)[1]
        AddInput = f"\n{TranslationProofreading[-1]['Body']}\n\n"
    else:
        AddInput = f"\nNone\n\n"
        
    return AddInput

######################
##### Filter 조건 #####
######################
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
    valid_language_tags = {'en', 'zh', 'es', 'ca'}
    if not isinstance(OutputDic['언어태그'], str) or OutputDic['언어태그'] not in valid_language_tags:
        return "TranslationIndexDefine, JSON에서 오류 발생: '언어태그'는 ['en', 'zh', 'es', 'ca'] 중 하나여야 합니다"

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

        # 데이터 타입 검증
        if not isinstance(item['번호'], int):
            return f"TranslationIndexDefine, JSON에서 오류 발생: '목차리스트[{idx}] > 번호'는 정수여야 합니다"

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
        return "TranslationBodySummary, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '현재내용요약' not in OutputDic:
        return "TranslationBodySummary, JSONKeyError: '현재내용요약' 키가 누락되었습니다"

    # Error3: '현재내용요약' 데이터 타입 검증
    if not isinstance(OutputDic['현재내용요약'], dict):
        return "TranslationBodySummary, JSON에서 오류 발생: '현재내용요약'은 딕셔너리 형태여야 합니다"

    # 필수 키 확인
    required_keys = ['핵심문구', '요약']
    missing_keys = [key for key in required_keys if key not in OutputDic['현재내용요약']]
    if missing_keys:
        return f"TranslationBodySummary, JSONKeyError: '현재내용요약'에 누락된 키: {', '.join(missing_keys)}"

    # 데이터 타입 검증
    if not isinstance(OutputDic['현재내용요약']['핵심문구'], list):
        return "TranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 핵심문구'는 리스트 형태여야 합니다"
    
    if not all(isinstance(item, str) for item in OutputDic['현재내용요약']['핵심문구']):
        return "TranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 핵심문구' 리스트의 모든 요소는 문자열이어야 합니다"

    if not (1 <= len(OutputDic['현재내용요약']['핵심문구']) <= 3):
        return "TranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 핵심문구'는 1~3개여야 합니다"

    if not isinstance(OutputDic['현재내용요약']['요약'], str):
        return "TranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 요약'은 문자열이어야 합니다"

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

        # 데이터 타입 검증
        if not isinstance(item['번호'], int):
            return f"WordListGen, JSON에서 오류 발생: '단어장[{idx}] > 번호'는 정수여야 합니다"

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

        # 데이터 타입 검증
        if not isinstance(item['번호'], int):
            return f"UniqueWordListGen, JSON에서 오류 발생: '고유명사[{idx}] > 번호'는 정수여야 합니다"

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

        # 데이터 타입 검증
        if not isinstance(item['번호'], int):
            return f"WordListPostprocessing, JSON에서 오류 발생: '정리된단어장[{idx}] > 번호'는 정수여야 합니다"

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

        # 데이터 타입 검증
        if not isinstance(item['번호'], int):
            return f"BodyTranslationPreprocessing, JSON에서 오류 발생: '수정된번역단어[{idx}] > 번호'는 정수여야 합니다"

        if not isinstance(item['원단어'], str):
            return f"BodyTranslationPreprocessing, JSON에서 오류 발생: '수정된번역단어[{idx}] > 원단어'는 문자열이어야 합니다"

        if not isinstance(item['수정된번역단어'], str):
            return f"BodyTranslationPreprocessing, JSON에서 오류 발생: '수정된번역단어[{idx}] > 수정된번역단어'는 문자열이어야 합니다"

        if not isinstance(item['수정이유'], str):
            return f"BodyTranslationPreprocessing, JSON에서 오류 발생: '수정된번역단어[{idx}] > 수정이유'는 문자열이어야 합니다"

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
    required_keys = ['이전도서내용어조', '현재도서내용어조', '격식일치여부']
    missing_keys = [key for key in required_keys if key not in OutputDic['도서내용어조체크']]
    if missing_keys:
        return f"BodyTranslationCheck, JSONKeyError: '도서내용어조체크'에 누락된 키: {', '.join(missing_keys)}"

    # 데이터 타입 및 값 검증
    valid_tone_types = ['격식어조', '비격식어조']
    valid_match_status = ['일치', '불일치']

    if OutputDic['도서내용어조체크']['이전도서내용어조'] not in valid_tone_types:
        return "BodyTranslationCheck, JSON에서 오류 발생: '도서내용어조체크 > 이전도서내용어조'는 '격식어조' 또는 '비격식어조' 중 하나여야 합니다"

    if OutputDic['도서내용어조체크']['현재도서내용어조'] not in valid_tone_types:
        return "BodyTranslationCheck, JSON에서 오류 발생: '도서내용어조체크 > 현재도서내용어조'는 '격식어조' 또는 '비격식어조' 중 하나여야 합니다"

    if OutputDic['도서내용어조체크']['격식일치여부'] not in valid_match_status:
        return "BodyTranslationCheck, JSON에서 오류 발생: '도서내용어조체크 > 격식일치여부'는 '일치' 또는 '불일치' 중 하나여야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['도서내용어조체크']

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
    
    # Error4: '도서내용'의 값에서 줄바꿈과 쌍따옴표 포함 여부 확인
    invalid_chars = ['"', '“', '”', ' ', '\n']
    for char in invalid_chars:
        if char in OutputDic['교정']['도서내용']:
            return f"TranslationProofreading, JSON에서 오류 발생: '교정 > 도서내용'에 허용되지 않은 문자({char})가 포함되었습니다"
        
    # Error5: 교정 전후 '도서내용' 일치 확인
    EditCheckCount = re.sub(r'[^a-zA-Z0-9\u0080-\uFFFF]', '', OutputDic['교정']['도서내용'])
    if EditCheckCount != CheckCount:
        return f"TranslationProofreading, JSON에서 오류 발생: '교정내용({len(EditCheckCount)}) != 도서내용({len(CheckCount)})'이 교정 전후로 일치하지 않습니다"
    
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
    if '대화문' not in OutputDic:
        return "TranslationDialogueAnalysis, JSONKeyError: '대화문' 키가 누락되었습니다"

    # Error3: '대화문' 데이터 타입 검증
    if not isinstance(OutputDic['대화문'], list):
        return "TranslationDialogueAnalysis, JSON에서 오류 발생: '대화문'은 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['대화문']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화문[{idx}]'는 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['번호', '말하는인물', '성별', '연령', '감정', '말하는인물성격특성', '상황', '듣는인물', '대답']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"TranslationDialogueAnalysis, JSONKeyError: '대화문[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 검증
        if not isinstance(item['번호'], str):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화문[{idx}] > 번호'는 문자열이어야 합니다"

        if not isinstance(item['말하는인물'], str):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화문[{idx}] > 말하는인물'은 문자열이어야 합니다"

        if item['성별'] not in ['남', '여']:
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화문[{idx}] > 성별'은 '남' 또는 '여' 중 하나여야 합니다"

        if item['연령'] not in ['유년', '청소년', '청년', '중년', '장년', '노년']:
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화문[{idx}] > 연령'은 유효한 연령값이 아닙니다"

        if item['감정'] not in ['중립', '즐거움', '화남', '슬픔', '침착함']:
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화문[{idx}] > 감정'은 유효한 감정값이 아닙니다"

        if not isinstance(item['말하는인물성격특성'], str):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화문[{idx}] > 말하는인물성격특성'은 문자열이어야 합니다"

        if not isinstance(item['상황'], str):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화문[{idx}] > 상황'은 문자열이어야 합니다"

        if not isinstance(item['듣는인물'], str):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화문[{idx}] > 듣는인물'은 문자열이어야 합니다"

        if not isinstance(item['대답'], str):
            return f"TranslationDialogueAnalysis, JSON에서 오류 발생: '대화문[{idx}] > 대답'은 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['대화문']

## Process12: TranslationDialogueEditing의 Filter(Error 예외처리)
def TranslationDialogueEditingFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "TranslationDialogueEditing, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '대화문편집' not in OutputDic:
        return "TranslationDialogueEditing, JSONKeyError: '대화문편집' 키가 누락되었습니다"

    # Error3: '대화문편집' 데이터 타입 검증
    if not isinstance(OutputDic['대화문편집'], list):
        return "TranslationDialogueEditing, JSON에서 오류 발생: '대화문편집'은 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['대화문편집']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화문편집[{idx}]'는 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['번호', '편집된대화문', '이유']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"TranslationDialogueEditing, JSONKeyError: '대화문편집[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 검증
        if not isinstance(item['번호'], str):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화문편집[{idx}] > 번호'는 문자열이어야 합니다"

        if not isinstance(item['편집된대화문'], str):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화문편집[{idx}] > 편집된대화문'은 문자열이어야 합니다"

        if not isinstance(item['이유'], str):
            return f"TranslationDialogueEditing, JSON에서 오류 발생: '대화문편집[{idx}] > 이유'는 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['대화문편집']

## Process13: TranslationDialoguePostprocessing의 Filter(Error 예외처리)
def TranslationDialoguePostprocessingFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "TranslationDialoguePostprocessing, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '대화문구수정' not in OutputDic:
        return "TranslationDialoguePostprocessing, JSONKeyError: '대화문구수정' 키가 누락되었습니다"

    # Error3: '대화문구수정' 데이터 타입 검증
    if not isinstance(OutputDic['대화문구수정'], list):
        return "TranslationDialoguePostprocessing, JSON에서 오류 발생: '대화문구수정'은 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['대화문구수정']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"TranslationDialoguePostprocessing, JSON에서 오류 발생: '대화문구수정[{idx}]'는 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['번호', '이름', '대화문구', '수정이유']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"TranslationDialoguePostprocessing, JSONKeyError: '대화문구수정[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 검증
        if not isinstance(item['번호'], str):
            return f"TranslationDialoguePostprocessing, JSON에서 오류 발생: '대화문구수정[{idx}] > 번호'는 문자열이어야 합니다"

        if not isinstance(item['이름'], str):
            return f"TranslationDialoguePostprocessing, JSON에서 오류 발생: '대화문구수정[{idx}] > 이름'은 문자열이어야 합니다"

        if not isinstance(item['대화문구'], str):
            return f"TranslationDialoguePostprocessing, JSON에서 오류 발생: '대화문구수정[{idx}] > 대화문구'는 문자열이어야 합니다"

        if not isinstance(item['수정이유'], str):
            return f"TranslationDialoguePostprocessing, JSON에서 오류 발생: '대화문구수정[{idx}] > 수정이유'는 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['대화문구수정']

## Process14: AfterTranslationBodySummary의 Filter(Error 예외처리)
def AfterTranslationBodySummaryFilter(Response, CheckCount):
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

    if not isinstance(OutputDic['현재내용요약']['중요도'], int):
        return "AfterTranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 중요도'는 정수여야 합니다"

    if not (0 <= OutputDic['현재내용요약']['중요도'] <= 1000):
        return "AfterTranslationBodySummary, JSON에서 오류 발생: '현재내용요약 > 중요도'는 0~1000 사이의 정수여야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['현재내용요약']

#######################
##### Process 응답 #####
#######################
## Process LLMResponse 함수
def ProcessResponse(projectName, email, Process, Input, InputCount, TotalInputCount, FilterFunc, CheckCount, LLM, mode, MessagesReview, input2 = "", memoryCounter = ""):
    ErrorCount = 0
    while True:
        if LLM == "OpenAI":
            Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, Input, InputCount, Mode = mode, Input2 = input2, MemoryCounter = memoryCounter, messagesReview = MessagesReview)
        elif LLM == "Anthropic":
            Response, Usage, Model = ANTHROPIC_LLMresponse(projectName, email, Process, Input, InputCount, Mode = mode, Input2 = input2, MemoryCounter = memoryCounter, messagesReview = MessagesReview)
        Filter = FilterFunc(Response, CheckCount)
        
        if isinstance(Filter, str):
            print(f"Project: {projectName} | Process: {Process} {InputCount}/{TotalInputCount} | {Filter}")
            ErrorCount += 1
            print(f"Project: {projectName} | Process: {Process} {InputCount}/{TotalInputCount} | "
                f"오류횟수 {ErrorCount}회, 10초 후 프롬프트 재시도")
            
            if ErrorCount >= 10:
                sys.exit(f"Project: {projectName} | Process: {Process} {InputCount}/{TotalInputCount} | "
                        f"오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
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
        TranslationIndexDefineFramePath = os.path.join(TranslationDataFramePath, "b532-01_TranslationIndexFrame.json")
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
        TranslationBodySplitFramePath = os.path.join(TranslationDataFramePath, "b532-01_TranslationBodySplitFrame.json")
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
        TranslationBodySummaryFramePath = os.path.join(TranslationDataFramePath, "b532-02_TranslationBodySummaryFrame.json")
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
        WordListGenFramePath = os.path.join(TranslationDataFramePath, "b532-03_WordListGenFrame.json")
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
        UniqueWordListGenFramePath = os.path.join(TranslationDataFramePath, "b532-04_UniqueWordListGenFrame.json")
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
        WordListPostprocessingFramePath = os.path.join(TranslationDataFramePath, "b532-05_WordListPostprocessingFrame.json")
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
        IndexTranslationFramePath = os.path.join(TranslationDataFramePath, "b532-06_IndexTranslationFrame.json")
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
    IndexTranslation['Index'] = IndexTranslationResponse['현재목차원문']
    IndexTranslation['IndexTranslation'] = IndexTranslationResponse['현재목차번역']
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
        BodyTranslationPreprocessingFramePath = os.path.join(TranslationDataFramePath, "b532-07_BodyTranslationPreprocessingFrame.json")
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
        BodyTranslationFramePath = os.path.join(TranslationDataFramePath, "b532-08_BodyTranslationFrame.json")
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
    BodyTranslation['Body'] = BodyTranslationResponse['번역문']
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

## Process9: TranslationEditingProcess DataFrame 저장
def TranslationEditingProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationEditingPath, TranslationEditingResponse, BodyTranslationCheckResponse, Process, InputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount):
    ## TranslationEditingFrame 불러오기
    if os.path.exists(ProjectDataFrameTranslationEditingPath):
        TranslationEditingFramePath = ProjectDataFrameTranslationEditingPath
    else:
        TranslationEditingFramePath = os.path.join(TranslationDataFramePath, "b532-09_TranslationEditingFrame.json")
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

## Process10: TranslationProofreadingProcess DataFrame 저장
def TranslationProofreadingProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationProofreadingPath, TranslationProofreadingResponse, Process, InputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount):
    ## TranslationProofreadingFrame 불러오기
    if os.path.exists(ProjectDataFrameTranslationProofreadingPath):
        TranslationProofreadingFramePath = ProjectDataFrameTranslationProofreadingPath
    else:
        TranslationProofreadingFramePath = os.path.join(TranslationDataFramePath, "b532-10_TranslationProofreadingFrame.json")
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
    TranslationProofreadingBody = TranslationProofreadingResponse['도서내용']
    TranslationProofreadingBody = TranslationProofreadingBody.replace('"', '@').replace('“', '@').replace('”', '@')
    TranslationProofreadingBody = TranslationProofreadingBody.replace('\n', '/')
    TranslationProofreading['Body'] = TranslationProofreadingBody

    ## TranslationProofreadingFrame 데이터 프레임 업데이트
    TranslationProofreadingFrame[1].append(TranslationProofreading)
        
    ## TranslationProofreadingFrame ProcessCount 및 Completion 업데이트
    TranslationProofreadingFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        TranslationProofreadingFrame[0]['Completion'] = 'Yes'
        
    ## TranslationProofreadingFrame 저장
    with open(ProjectDataFrameTranslationProofreadingPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TranslationProofreadingFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process14: AfterTranslationBodySummaryProcess DataFrame 저장
def AfterTranslationBodySummaryProcessDataFrameSave(ProjectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameAfterTranslationBodySummaryPath, AfterTranslationBodySummaryResponse, Process, InputCount, IndexId, TotalInputCount):
    ## AfterTranslationBodySummaryFrame 불러오기
    if os.path.exists(ProjectDataFrameAfterTranslationBodySummaryPath):
        AfterTranslationBodySummaryFramePath = ProjectDataFrameAfterTranslationBodySummaryPath
    else:
        AfterTranslationBodySummaryFramePath = os.path.join(TranslationDataFramePath, "b532-02_AfterTranslationBodySummaryFrame.json")
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
def ProcessEditTextSave(ProjectName, MainLang, ProjectMasterTranslationPath, TranslationEditPath, Process1, Process2):
    ## TranslationEdit 불러오기
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationEdit = json.load(TranslationEditJson)
    TranslationBodyEdit = TranslationEdit[Process2]
    TranslationIndexEdit = TranslationEdit[Process1]
        
    ## TranslationEdit을 Index, Body Text파일로 저장
    EditIndexFileName = f"{ProjectName}_Index({MainLang}).txt"
    EditIndexFilePath = os.path.join(ProjectMasterTranslationPath, EditIndexFileName)
    EditBodyFileName = f"{ProjectName}_Body({MainLang}).txt"
    EditBodyFilePath = os.path.join(ProjectMasterTranslationPath, EditBodyFileName)
    
    # Index 파일 생성  
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
            indexFile.write(IndexText)
    
    # Body 파일 생성
    CurrentIndex = None
    with open(EditBodyFilePath, 'w', encoding='utf-8') as bodyFile:
        for i, ProcessDic in enumerate(TranslationBodyEdit):
            # 새로운 Index인지 확인
            if ProcessDic['Index'] != CurrentIndex:
                CurrentIndex = ProcessDic['Index']
                # 새 Index 작성
                if i != 0:
                    bodyFile.write(f"\n\n\n<{ProcessDic['Index']}>\n\n\n")
                else:
                    bodyFile.write(f"<{ProcessDic['Index']}>\n\n\n")
            
            # Body 내용 작성
            BodyText = ProcessDic['Body'].replace('\n\n\n\n', '\n\n')
            BodyText = BodyText.replace('\n\n\n', '\n\n')
            bodyFile.write(f"{BodyText}")

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
def TranslationProcessUpdate(projectName, email, MainLang, Translation, EditMode, mode = "Master", MessagesReview = "on"):
    print(f"< User: {email} | Translation: {projectName} ({Translation}) >>> ({MainLang}) | TranslationUpdate 시작 >")
    ## projectName_translation 경로 설정
    ProjectTranslationPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_translation"
    UploadTranslationFilePath = os.path.join(ProjectTranslationPath, f"{projectName}_upload_translation_file")
    ProjectDataFrameTranslationPath = os.path.join(ProjectTranslationPath, f'{projectName}_dataframe_translation_file')
    ProjectMasterTranslationPath = os.path.join(ProjectTranslationPath, f'{projectName}_master_translation_file')
    TranslationEditPath = os.path.join(ProjectMasterTranslationPath, f'[{projectName}_Translation_Edit].json')
    
    TranslationDataFramePath = "/yaas/backend/b5_Database/b53_ProjectData/b532_TranslationProject"
    
    ####################################################
    ### Process1: TranslationIndexDefine Response 생성 ##
    ####################################################
    
    ## Process 설정
    ProcessNumber = '01'
    Process = "TranslationIndexDefine"

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
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

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

    ## Result 생성
    TranslationBodySplitResult = TranslationBodySplitProcess(projectName, UploadTranslationFilePath, TranslationEditPath, "TranslationIndexDefine", 4000)
    
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
                    TranslationBodySummaryResponse = {"요약": Body, "핵심문구": ['None']}
                else:
                    ## Response 생성
                    TranslationBodySummaryResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationBodySummaryFilter, CheckCount, "OpenAI", mode, MessagesReview)

                ## DataFrame 저장
                TranslationBodySummaryProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationBodySummaryPath, TranslationBodySummaryResponse, Process, inputCount, IndexId, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameTranslationBodySummaryPath, TranslationEditPath, Process, EditMode)
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    #########################################
    ### Process3: WordListGen Response 생성 ##
    #########################################
    
    ## Process 설정
    ProcessNumber = '03'
    Process = "WordListGen"

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
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    ###############################################
    ### Process4: UniqueWordListGen Response 생성 ##
    ###############################################
    
    ## Process 설정
    ProcessNumber = '04'
    Process = "UniqueWordListGen"

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
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    ####################################################
    ### Process5: WordListPostprocessing Response 생성 ##
    ####################################################
    
    ## Process 설정
    ProcessNumber = '05'
    Process = "WordListPostprocessing"

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
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    ##############################################
    ### Process6: IndexTranslation Response 생성 ##
    ##############################################
    
    ## Process 설정
    ProcessNumber = '06'
    Process = "IndexTranslation"

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
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    ##########################################################
    ### Process7: BodyTranslationPreprocessing Response 생성 ##
    ##########################################################

    ## Process 설정
    ProcessNumber = '07'
    Process = "BodyTranslationPreprocessing"

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
                BodyTranslationPreprocessingResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, BodyTranslationPreprocessingFilter, CheckCount, "Anthropic", mode, MessagesReview)
                
                ## DataFrame 저장
                BodyTranslationPreprocessingProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameBodyTranslationPreprocessingPath, BodyTranslationPreprocessingResponse, Process, inputCount, IndexId, IndexTag, Index, BodyId, TranslationBody, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameBodyTranslationPreprocessingPath, TranslationEditPath, Process, EditMode)
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    #############################################
    ### Process8: BodyTranslation Response 생성 ##
    #############################################

    ## Process 설정
    ProcessNumber = '08'
    Process = "BodyTranslation"

    ## BodyTranslation 경로 생성
    ProjectDataFrameBodyTranslationPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = BodyTranslationInputList(TranslationEditPath, "BodyTranslationPreprocessing")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameBodyTranslationPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    MemoryCounter = ''
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
                Input1 = BodyTranslationAddInput(ProjectDataFrameBodyTranslationPath, ProjectDataFrameIndexTranslationPath, MainLangCode, TranslationLangCode)
                Input2 = InputList[i]['Input']
                Input = Input1 + Input2
                
                ## Response 생성
                BodyTranslationResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, BodyTranslationFilter, CheckCount, "Anthropic", mode, MessagesReview, memoryCounter = MemoryCounter)
                
                ######################################
                ### Process8: BodyTranslationCheck ###
                ######################################
                BodyTranslationCheckResponse = {'현재도서내용어조': '모름'}
                if inputCount >= 4 and ToneDistinction == 'Yes':
                    CheckProcess = "BodyTranslationCheck"
                    CheckInput, BeforeCheck = BodyTranslationCheckInput(ProjectDataFrameBodyTranslationPath, BodyTranslationResponse)
                    BodyTranslationCheckResponse = ProcessResponse(projectName, email, CheckProcess, CheckInput, inputCount, TotalInputCount, BodyTranslationCheckFilter, CheckCount, "OpenAI", mode, MessagesReview)
                    if BodyTranslationCheckResponse['격식일치여부'] == '불일치':
                        if BodyTranslationCheckResponse['이전도서내용어조'] == '모름':
                            if BodyTranslationCheckResponse['현재도서내용어조'] == BeforeCheck:
                                pass
                        elif BodyTranslationCheckResponse['현재도서내용어조'] == '모름':
                            pass
                        elif BodyTranslationCheckResponse['이전도서내용어조'] == '격식어조':
                            MemoryCounter = '\n※ 참고! [원문]의 서술문(대화문, 인용문 외에 내용을 서술하는 문장)은 격식체(습니다. 입니다. 합니다. ... 등의)로 번역해주세요.'
                            continue
                        # Check가 False인 경우, 현재 반복을 다시 실행하기 위해 continue
                        elif BodyTranslationCheckResponse['이전도서내용어조'] == '비격식어조':
                            MemoryCounter = '\n※ 참고! [원문]의 서술문(대화문, 인용문 외에 내용을 서술하는 문장)은 비격식체(이다. 한다. 있다. ... 등의)로 번역해주세요.'
                            continue
                MemoryCounter = ''
                
                ## DataFrame 저장
                BodyTranslationProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameBodyTranslationPath, BodyTranslationResponse, BodyTranslationCheckResponse, Process, inputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount)
                i += 1  # 다음 인덱스로 이동
            
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameBodyTranslationPath, TranslationEditPath, Process, EditMode)
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    ################################################
    ### Process9: TranslationEditing Response 생성 ##
    ################################################

    ## Process 설정
    ProcessNumber = '09'
    Process = "TranslationEditing"

    ## TranslationEditing 경로 생성
    ProjectDataFrameTranslationEditingPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = TranslationEditingInputList(TranslationEditPath, "BodyTranslationPreprocessing", "BodyTranslation")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationEditingPath)
    EditCheck, EditCompletion = ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    ## Process 진행
    MemoryCounter = ''
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                IndexId = InputList[i]['IndexId']
                IndexTag = InputList[i]['IndexTag']
                Index = InputList[i]['Index']
                BodyId = InputList[i]['BodyId']
                Input1 = TranslationEditingAddInput(ProjectDataFrameTranslationEditingPath, ProjectDataFrameIndexTranslationPath)
                Input2 = InputList[i]['Input']
                Input = Input1 + Input2
                
                ## Response 생성
                TranslationEditingResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationEditingFilter, CheckCount, "Anthropic", mode, MessagesReview, memoryCounter = MemoryCounter)

                ######################################
                ### Process8: BodyTranslationCheck ###
                ######################################
                BodyTranslationCheckResponse = {'현재도서내용어조': '모름'}
                print(f"\n\n\n\n\n\n\n\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@\ninputCount: {inputCount}")
                print(f"ToneDistinction: {ToneDistinction}\n@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n\n\n\n\n\n\n\n")
                if inputCount >= 4 and ToneDistinction == 'Yes':
                    CheckProcess = "BodyTranslationCheck"
                    CheckInput, BeforeCheck = BodyTranslationCheckInput(ProjectDataFrameTranslationEditingPath, TranslationEditingResponse)
                    BodyTranslationCheckResponse = ProcessResponse(projectName, email, CheckProcess, CheckInput, inputCount, TotalInputCount, BodyTranslationCheckFilter, CheckCount, "OpenAI", mode, MessagesReview)
                    if BodyTranslationCheckResponse['격식일치여부'] == '불일치':
                        if BodyTranslationCheckResponse['이전도서내용어조'] == '모름':
                            if BodyTranslationCheckResponse['현재도서내용어조'] == BeforeCheck:
                                pass
                        elif BodyTranslationCheckResponse['현재도서내용어조'] == '모름':
                            pass
                        elif BodyTranslationCheckResponse['이전도서내용어조'] == '격식어조':
                            MemoryCounter = '\n※ 참고! [원문]의 서술문(대화문, 인용문 외에 내용을 서술하는 문장)은 격식체(습니다. 입니다. 합니다. ... 등의)로 번역해주세요.'
                            continue
                        # Check가 False인 경우, 현재 반복을 다시 실행하기 위해 continue
                        elif BodyTranslationCheckResponse['이전도서내용어조'] == '비격식어조':
                            MemoryCounter = '\n※ 참고! [원문]의 서술문(대화문, 인용문 외에 내용을 서술하는 문장)은 비격식체(이다. 한다. 있다. ... 등의)로 번역해주세요.'
                            continue
                MemoryCounter = ''

                ## DataFrame 저장
                TranslationEditingProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationEditingPath, TranslationEditingResponse, BodyTranslationCheckResponse, Process, inputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount)

        ## Edit 저장
        ProcessEditSave(ProjectDataFrameTranslationEditingPath, TranslationEditPath, Process, EditMode)
        ## EditText 저장
        ProcessEditTextSave(projectName, MainLang, ProjectMasterTranslationPath, TranslationEditPath, "IndexTranslation", Process)
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    #############################################
    ### Process10: TranslationProofreading 생성 ##
    #############################################

    ## Process 설정
    ProcessNumber = '10'
    Process = "TranslationProofreading"

    ## TranslationProofreading 경로 생성
    ProjectDataFrameTranslationProofreadingPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = TranslationProofreadingInputList(TranslationEditPath, "TranslationEditing")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTranslationProofreadingPath)
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
                CheckCount = re.sub(r'[^a-zA-Z0-9\u0080-\uFFFF]', '', InputList[i]['Body'])
                Input1 = TranslationProofreadingAddInput(ProjectDataFrameTranslationProofreadingPath)
                Input2 = InputList[i]['Input']
                Input = Input1 + Input2
                
                ## Response 생성
                TranslationProofreadingResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TranslationProofreadingFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                TranslationProofreadingProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationProofreadingPath, TranslationProofreadingResponse, Process, inputCount, IndexId, IndexTag, Index, BodyId, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameTranslationProofreadingPath, TranslationEditPath, Process, EditMode)
        ## EditText 저장
        ProcessEditTextSave(projectName, MainLang, ProjectMasterTranslationPath, TranslationEditPath, "IndexTranslation", Process)
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    #################################################
    ### Process11: TranslationDialogueAnalysis 생성 ##
    #################################################
    
    ################################################
    ### Process12: TranslationDialogueEditing 생성 ##
    ################################################
    
    #######################################################
    ### Process13: TranslationDialoguePostprocessing 생성 ##
    #######################################################
    
    #################################################
    ### Process14: AfterTranslationBodySummary 생성 ##
    #################################################
    
    ## Process 설정
    ProcessNumber = '14'
    Process = "AfterTranslationBodySummary"

    ## AfterTranslationBodySummary 경로 생성
    ProjectDataFrameAfterTranslationBodySummaryPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = TranslationBodySummaryInputList(TranslationEditPath, "TranslationEditing")
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
                    AfterTranslationBodySummaryResponse = {"요약": Body, "핵심문구": ['None']}
                else:
                    ## Response 생성
                    AfterTranslationBodySummaryResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, AfterTranslationBodySummaryFilter, CheckCount, "Anthropic", mode, MessagesReview)

                ## DataFrame 저장
                AfterTranslationBodySummaryProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameAfterTranslationBodySummaryPath, AfterTranslationBodySummaryResponse, Process, inputCount, IndexId, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameAfterTranslationBodySummaryPath, TranslationEditPath, Process, EditMode)
        if EditMode == "Manual":
            sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    if EditMode == "Manual":
        if EditCheck:
            if not EditCompletion:
                ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    
    ############################################
    ### Process15: TranslationCatchphrase 생성 ##
    ############################################

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '250121_테스트'
    Intention = "Similarity"
    #########################################################################
    # BookScriptGenProcessUpdate(ProjectName, email, Intention)