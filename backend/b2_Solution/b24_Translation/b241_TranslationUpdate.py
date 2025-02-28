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
def LoadTranslationSplitBody(projectName, UploadTranslationFilePath, TranslationEditPath, Process, MaxLength):
    # TranslationIndex 불러오기
    with open(TranslationEditPath, 'r', encoding = 'utf-8') as TranslationEditJson:
        TranslationIndex = json.load(TranslationEditJson)[Process]
    # TranslationBody 경로 설정
    TranslationBodyFileName = f"{projectName}_Body(Translation).txt"
    TranslationBodyFilePath = os.path.join(UploadTranslationFilePath, TranslationBodyFileName)
    
    # TranslationBody 불러오기
    if os.path.exists(TranslationBodyFilePath):
        with open(TranslationBodyFilePath, "r") as TranslationBodyFile:
            TranslationBody = TranslationBodyFile.read()
    else:
        sys.exit(f"\n\n[ ((({projectName}_Index(Translation).txt))), ((({projectName}_Body(Translation).txt))) 파일을 완성하여 아래 경로에 복사해주세요. ]\n({UploadTranslationFilePath})\n\n1. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n3. 목차((_Index(Translation)))파일과 본문((_Body(Translation))) 파일의 목차는 <제목>의 형태로 괄호처리 권장\n3. 본문((_Body(Translation)))파일 내 쌍따옴표(“대화문”의 완성) 개수 일치\n\n")

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

## Load2: MaxLength 이상인 경우 분할
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
        Translation = TranslationIndexDefine['Translation']
    elif Translation.lower() not in ['en', 'zh', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'pt', 'ru', 'ar', 'nl', 'sv', 'no', 'da', 'fi', 'pl', 'tr', 'el', 'cs', 'hu', 'ro', 'sk', 'uk', 'hi', 'id', 'ms', 'th', 'vi', 'he', 'bg', 'ca']:
        Translation = TranslationIndexDefine['Translation']
        
    return Translation
    

#####################
##### Input 생성 #####
#####################
## Language Code 생성
def LanguageCodeGen(MainLang, Translation):
    def LanguageCode(Lang):
        # 언어 코드와 해당 언어명을 딕셔너리로 정의
        LanguageDict = {
            "en": "English - English - 영어",
            "zh": "Chinese - 中文 - 중국어",
            "es": "Spanish - Español - 스페인어",
            "fr": "French - Français - 프랑스어",
            "de": "German - Deutsch - 독일어",
            "it": "Italian - Italiano - 이탈리아어",
            "ja": "Japanese - 日本語 - 일본어",
            "ko": "Korean - 한국어 - 한국어",
            "pt": "Portuguese - Português - 포르투갈어",
            "ru": "Russian - Русский - 러시아어",
            "ar": "Arabic - العربية - 아랍어",
            "nl": "Dutch - Nederlands - 네덜란드어",
            "sv": "Swedish - Svenska - 스웨덴어",
            "no": "Norwegian - Norsk - 노르웨이어",
            "da": "Danish - Dansk - 덴마크어",
            "fi": "Finnish - Suomi - 핀란드어",
            "pl": "Polish - Polski - 폴란드어",
            "tr": "Turkish - Türkçe - 터키어",
            "el": "Greek - Ελληνικά - 그리스어",
            "cs": "Czech - Čeština - 체코어",
            "hu": "Hungarian - Magyar - 헝가리어",
            "ro": "Romanian - Română - 루마니아어",
            "sk": "Slovak - Slovenčina - 슬로바키아어",
            "uk": "Ukrainian - Українська - 우크라이나어",
            "hi": "Hindi - हिन्दी - 힌디어",
            "id": "Indonesian - Bahasa Indonesia - 인도네시아어",
            "ms": "Malay - Bahasa Melayu - 말레이어",
            "th": "Thai - ไทย - 태국어",
            "vi": "Vietnamese - Tiếng Việt - 베트남어",
            "he": "Hebrew - עברית - 히브리어",
            "bg": "Bulgarian - Български - 불가리아어",
            "ca": "Catalan - Català - 카탈루냐어"
        }
        
        # 입력된 언어 코드를 소문자로 변환하여 처리
        LangCode = Lang.lower()
        
        # 딕셔너리에서 언어 정보 반환
        return LanguageDict.get(LangCode)
    
    # Main Language Code
    MainLangCode = LanguageCode(MainLang)
    
    # Translation Language Code
    TranslationLangCode = LanguageCode(Translation)
    
    return MainLangCode, TranslationLangCode

## Process1: TranslationIndexDefine의 Input
def TranslationIndexDefineInputList(projectName, UploadTranslationFilePath):
    IndexTranslation = LoadTranslationIndex(projectName, UploadTranslationFilePath)
    InputList = []
    
    InputId = 1
    Input = IndexTranslation
    
    InputDic = {"Id": InputId, "Input": Input}
    InputList.append(InputDic)
    
    return InputList

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

## Process2: TranslationBodySummary의 Filter(Error 예외처리)
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
    if '요약' not in OutputDic['현재내용요약']:
        return "TranslationBodySummary, JSONKeyError: '현재내용요약'에 '요약' 키가 누락되었습니다"

    # 데이터 타입 검증
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

    for idx, item in enumerate(OutputDic['정리된단어장']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"WordListPostprocessing, JSON에서 오류 발생: '정리된단어장[{idx}]'는 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['번호', '원문', '번역', '선택이유']
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

        if not isinstance(item['선택이유'], str):
            return f"WordListPostprocessing, JSON에서 오류 발생: '정리된단어장[{idx}] > 선택이유'는 문자열이어야 합니다"

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

## Process7: BodyTranslation의 Filter(Error 예외처리)
def BodyTranslationFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "BodyTranslation, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '원문번역' not in OutputDic:
        return "BodyTranslation, JSONKeyError: '원문번역' 키가 누락되었습니다"

    # Error3: '원문번역' 데이터 타입 검증
    if not isinstance(OutputDic['원문번역'], dict):
        return "BodyTranslation, JSON에서 오류 발생: '원문번역'은 딕셔너리 형태여야 합니다"

    # 필수 키 확인
    if '번역' not in OutputDic['원문번역']:
        return "BodyTranslation, JSONKeyError: '원문번역'에 '번역' 키가 누락되었습니다"

    # 데이터 타입 검증
    if not isinstance(OutputDic['원문번역']['번역'], str):
        return "BodyTranslation, JSON에서 오류 발생: '원문번역 > 번역'은 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['원문번역']

## Process8: TranslationEditing의 Filter(Error 예외처리)
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
    ## TranslationIndexDefineGenFrame 불러오기
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
    ## TranslationBodySplitGenFrame 불러오기
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

##############################
##### ProcessEdit 업데이트 #####
##############################
## Process Edit 저장
def ProcessEditSave(ProjectDataFramePath, TranslationEditPath, Process):
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
        TranslationEdit[f"{Process}Completion"] = '완료 후 Completion'
        TranslationDataList = TranslationDataFrame[1]
        for i in range(1, len(TranslationDataList)):
            ProcessDic = TranslationDataList[i]
            TranslationEdit[Process].append(ProcessDic)
        
        ## TranslationEdit 저장
        with open(TranslationEditPath, 'w', encoding = 'utf-8') as TranslationEditJson:
            json.dump(TranslationEdit, TranslationEditJson, indent = 4, ensure_ascii = False)

## Process Edit Prompt 확인
def ProcessEditPromptCheck(TranslationEditPath, Process, TotalInputCount, NumProcesses = 1):
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
def TranslationProcessUpdate(projectName, email, MainLang, Translation, mode = "Master", MessagesReview = "on"):
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
        ProcessEditSave(ProjectDataFrameTranslationIndexDefinePath, TranslationEditPath, Process)
        sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    if EditCheck:
        if not EditCompletion:
            ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
            sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{TranslationEditPath}")

    ## 최종 설정된 Translation 불러오기 및 MainLangCode, TranslationLangCode 설정
    Translation = LoadTranslation(Translation, ProjectDataFrameTranslationIndexDefinePath)
    MainLangCode, TranslationLangCode = LanguageCodeGen(MainLang, Translation)
    print(f"MainLangCode: {MainLangCode} | TranslationLangCode: {TranslationLangCode}")

    ####################################################
    ### Process1: TranslationBodySplit Response 생성 ##
    ####################################################
    
    ## Process 설정
    ProcessNumber = '01'
    BeforeProcess = Process
    Process = "TranslationBodySplit"

    ## TranslationBodySplit 경로 생성
    ProjectDataFrameTranslationBodySplitPath = os.path.join(ProjectDataFrameTranslationPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Result 생성
    TranslationBodySplitResult = LoadTranslationSplitBody(projectName, UploadTranslationFilePath, TranslationEditPath, BeforeProcess, 4000)
    
    ## DataFrame 저장
    TranslationBodySplitProcessDataFrameSave(projectName, MainLang, Translation, TranslationDataFramePath, ProjectDataFrameTranslationBodySplitPath, TranslationBodySplitResult, Process, len(TranslationBodySplitResult), len(TranslationBodySplitResult))

    ## Edit 저장
    with open(ProjectDataFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TranslationDataFrame = json.load(DataFrameJson)

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '250121_테스트'
    Intention = "Similarity"
    #########################################################################
    # BookScriptGenProcessUpdate(ProjectName, email, Intention)