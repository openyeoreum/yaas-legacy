import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from datetime import datetime
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import OpenAI_LLMresponse, ANTHROPIC_LLMresponse

#####################
##### Input 생성 #####
#####################
## Process1: SearchResult 불러오기
def LoadSearchResult(TotalSearchResultDataTempPath, ProjectName, Intention):
    # 파일명 패턴 정규식 (검색한시간을 추출하기 위해 사용)
    pattern = re.compile(r"SearchResultData_\((\d{14})\)_\[" + re.escape(ProjectName) + r"_" + re.escape(Intention) + r": (.*?)\]\.json")
    Files = os.listdir(TotalSearchResultDataTempPath)

    # 필터링된 파일 목록을 저장
    MatchingSearchResult = []
    for File in Files:
        Match = pattern.match(File)
        if Match:
            SearchTime = Match.group(1)
            MatchingSearchResult.append((SearchTime, File))

    # 검색한시간을 기준으로 정렬
    MatchingSearchResult.sort(key = lambda x: x[0], reverse = True)
    print(f"[ LastestSearchResult: {MatchingSearchResult} ]")
    LastestSearchResult = MatchingSearchResult[0][1]
    LastestSearchResultPath = os.path.join(TotalSearchResultDataTempPath, LastestSearchResult)
    LastestTopScoreSearchResultPath = LastestSearchResultPath.replace('].json', ']_TopScore.json')

    # SearchResult, TopScoreSearchResultPath 로드
    with open(LastestSearchResultPath, "r", encoding="utf-8") as f:
        SearchResultJson = json.load(f)
    with open(LastestTopScoreSearchResultPath, "r", encoding="utf-8") as f:
        TopScoreSearchResultJson = json.load(f)
    

    return SearchResultJson, TopScoreSearchResultJson

## Process1-1: DemandScriptPlan의 Input
def DemandCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, ProjectName, Intention):
    SearchResultJson, TopScoreSearchResultJson = LoadSearchResult(TotalSearchResultDataTempPath, ProjectName, Intention)
    
    SearchResult = SearchResultJson['SearchResult']
    Term = SearchResult[f'{Intention}Search']['Term']
    SimilarityDetail = SearchResult[f'{Intention}Detail']['Summary']
    
    NomalContextKey = f'{Intention}Context'
    NormalCollectionAnalysis = SearchResult[NomalContextKey]['CollectionAnalysis']
    NormalSummary = NormalCollectionAnalysis['Summary']
    NormalKeyWord = NormalCollectionAnalysis['KeyWord']
    NormalDemandNeedsSentence = NormalCollectionAnalysis['Demand']['Needs']['Sentence']
    NormalDemandNeedsKeyWord = NormalCollectionAnalysis['Demand']['Needs']['KeyWord']
    NormalDemandPurposeSentence = NormalCollectionAnalysis['Demand']['Purpose']['Sentence']
    NormalDemandPurposeKeyWord = NormalCollectionAnalysis['Demand']['Purpose']['KeyWord']
    NormalDemandQuestionSentence = NormalCollectionAnalysis['Demand']['Question']['Sentence']
    NormalDemandQuestionKeyWord = NormalCollectionAnalysis['Demand']['Question']['KeyWord']
    
    AdvacedContextKey = list(TopScoreSearchResultJson['SearchResult'].keys())[2]
    if NomalContextKey != AdvacedContextKey:
        AdvancedCollectionAnalysis = TopScoreSearchResultJson['SearchResult'][AdvacedContextKey]['CollectionAnalysis']
        AdvancedSummary = AdvancedCollectionAnalysis['Summary']
        AdvancedKeyWord = AdvancedCollectionAnalysis['KeyWord']
        AdvancedDemandNeedsSentence = AdvancedCollectionAnalysis['Demand']['Needs']['Sentence']
        AdvancedDemandNeedsKeyWord = AdvancedCollectionAnalysis['Demand']['Needs']['KeyWord']
        AdvancedDemandPurposeSentence = AdvancedCollectionAnalysis['Demand']['Purpose']['Sentence']
        AdvancedDemandPurposeKeyWord = AdvancedCollectionAnalysis['Demand']['Purpose']['KeyWord']
        AdvancedDemandQuestionSentence = AdvancedCollectionAnalysis['Demand']['Question']['Sentence']
        AdvancedDemandQuestionKeyWord = AdvancedCollectionAnalysis['Demand']['Question']['KeyWord']
        
        FrontInput = f"[최초의도]\n{Term}\n{SimilarityDetail}\n\n"
    
        BackInput = f"[핵심목적]\n일반: {NormalSummary}\n심화: {AdvancedSummary}\n\n[분야]\n일반: {', '.join(NormalKeyWord)}\n심화: {', '.join(AdvancedKeyWord)}\n\n[필요내용]\n일반: {NormalDemandNeedsSentence}\n심화: {AdvancedDemandNeedsSentence}\n\n[필요내용-키워드]\n일반: {', '.join(NormalDemandNeedsKeyWord)}\n심화: {', '.join(AdvancedDemandNeedsKeyWord)}\n\n[필요목표]\n일반: {NormalDemandPurposeSentence}\n심화: {AdvancedDemandPurposeSentence}\n\n[필요목표-키워드]\n일반: {', '.join(NormalDemandPurposeKeyWord)}\n심화: {', '.join(AdvancedDemandPurposeKeyWord)}\n\n[필요질문]\n일반: {NormalDemandQuestionSentence}\n심화: {AdvancedDemandQuestionSentence}\n\n[필요질문-키워드]\n일반: {', '.join(NormalDemandQuestionKeyWord)}\n심화: {', '.join(AdvancedDemandQuestionKeyWord)}"

    else:
        FrontInput = f"[최초의도]\n{Term}\n{SimilarityDetail}\n\n"

        BackInput = f"[핵심목적]\n{NormalSummary}\n\n[분야]\n{', '.join(NormalKeyWord)}\n\n[필요내용]\n{NormalDemandNeedsSentence}\n\n[필요내용-키워드]\n{', '.join(NormalDemandNeedsKeyWord)}\n\n[필요목표]\n{NormalDemandPurposeSentence}\n\n[필요목표-키워드]\n{', '.join(NormalDemandPurposeKeyWord)}\n\n[필요질문]\n{NormalDemandQuestionSentence}\n\n[필요질문-키워드]\n{', '.join(NormalDemandQuestionKeyWord)}"

    ## Intention에 따라 Input 결정
    if Intention == 'Demand':
        Input = FrontInput + BackInput
    elif Intention == 'Similarity':
        Input = BackInput

    return Input

## Process1-2: SupplyScriptPlan의 Input
def SupplyCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, ProjectName, Intention):
    SearchResultJson, TopScoreSearchResultJson = LoadSearchResult(TotalSearchResultDataTempPath, ProjectName, Intention)
    
    SearchResult = SearchResultJson['SearchResult']
    Term = SearchResult[f'{Intention}Search']['Term']
    SimilarityDetail = SearchResult[f'{Intention}Detail']['Summary']
    
    NomalContextKey = f'{Intention}Context'
    NormalCollectionAnalysis = SearchResult[NomalContextKey]['CollectionAnalysis']
    NormalSummary = NormalCollectionAnalysis['Summary']
    NormalKeyWord = NormalCollectionAnalysis['KeyWord']
    NormalSupplySatisfySentence = NormalCollectionAnalysis['Supply']['Satisfy']['Sentence']
    NormalSupplySatisfyKeyWord = NormalCollectionAnalysis['Supply']['Satisfy']['KeyWord']
    NormalSupplySupportSentence = NormalCollectionAnalysis['Supply']['Support']['Sentence']
    NormalSupplySupportKeyWord = NormalCollectionAnalysis['Supply']['Support']['KeyWord']
    NormalSupplySolutionSentence = NormalCollectionAnalysis['Supply']['Solution']['Sentence']
    NormalSupplySolutionKeyWord = NormalCollectionAnalysis['Supply']['Solution']['KeyWord']
    
    AdvacedContextKey = list(TopScoreSearchResultJson['SearchResult'].keys())[2]
    if NomalContextKey != AdvacedContextKey:
        AdvancedCollectionAnalysis = TopScoreSearchResultJson['SearchResult'][AdvacedContextKey]['CollectionAnalysis']
        AdvancedSummary = AdvancedCollectionAnalysis['Summary']
        AdvancedKeyWord = AdvancedCollectionAnalysis['KeyWord']
        AdvancedSupplySatisfySentence = AdvancedCollectionAnalysis['Supply']['Satisfy']['Sentence']
        AdvancedSupplySatisfyKeyWord = AdvancedCollectionAnalysis['Supply']['Satisfy']['KeyWord']
        AdvancedSupplySupportSentence = AdvancedCollectionAnalysis['Supply']['Support']['Sentence']
        AdvancedSupplySupportKeyWord = AdvancedCollectionAnalysis['Supply']['Support']['KeyWord']
        AdvancedSupplySolutionSentence = AdvancedCollectionAnalysis['Supply']['Solution']['Sentence']
        AdvancedSupplySolutionKeyWord = AdvancedCollectionAnalysis['Supply']['Solution']['KeyWord']
    
        Input = f"""[최초의도]
{Term}
{SimilarityDetail}

[핵심목적]
일반: {NormalSummary}
심화: {AdvancedSummary}

[분야]
일반: {', '.join(NormalKeyWord)}
심화: {', '.join(AdvancedKeyWord)}

[필요내용]
일반: {NormalSupplySatisfySentence}
심화: {AdvancedSupplySatisfySentence}

[필요내용-키워드]
일반: {', '.join(NormalSupplySatisfyKeyWord)}
심화: {', '.join(AdvancedSupplySatisfyKeyWord)}

[필요목표]
일반: {NormalSupplySupportSentence}
심화: {AdvancedSupplySupportSentence}

[필요목표-키워드]
일반: {', '.join(NormalSupplySupportKeyWord)}
심화: {', '.join(AdvancedSupplySupportKeyWord)}

[필요질문]
일반: {NormalSupplySolutionSentence}
심화: {AdvancedSupplySolutionSentence}

[필요질문-키워드]
일반: {', '.join(NormalSupplySolutionKeyWord)}
심화: {', '.join(AdvancedSupplySolutionKeyWord)}
"""
    else:
        Input = f"""[최초의도]
{Term} {SimilarityDetail}

[핵심목적]
{NormalSummary}

[분야]
{', '.join(NormalKeyWord)}

[필요내용]
{NormalSupplySatisfySentence}

[필요내용-키워드]
{', '.join(NormalSupplySatisfyKeyWord)}

[필요목표]
{NormalSupplySupportSentence}

[필요목표-키워드]
{', '.join(NormalSupplySupportKeyWord)}

[필요질문]
{NormalSupplySolutionSentence}

[필요질문-키워드]
{', '.join(NormalSupplySolutionKeyWord)}
"""

    return Input

## Process2: TitleAndIndexGen의 Input   

## Process3: SummaryOfIndexGen의 Input

## Process4: ScriptIntroductionGenGen의 Input

## Process5: ShortScriptGen의 Input

## Process6: ShortScriptMerge의 Input

## Process7: LongScriptGen의 Input

## Process8: LongScriptEdit의 Input

######################
##### Filter 조건 #####
######################
## Process1: ScriptPlan의 Filter(Error 예외처리)
def ScriptPlanFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "ScriptPlan, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_keys = ['배경', '주제', '범위', '개념키워드', '독자키워드', '가치', '정보의질']
    missing_top_keys = [key for key in required_top_keys if key not in OutputDic]
    if missing_top_keys:
        return f"ScriptPlan, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"

    # Error3: 최상위 키 데이터 타입 검증
    if not isinstance(OutputDic['배경'], str):
        return "ScriptPlan, JSON에서 오류 발생: '배경'은 문자열이어야 합니다"
    if not isinstance(OutputDic['주제'], str):
        return "ScriptPlan, JSON에서 오류 발생: '주제'은 문자열이어야 합니다"
    if not isinstance(OutputDic['범위'], str):
        return "ScriptPlan, JSON에서 오류 발생: '범위'은 문자열이어야 합니다"
    if not isinstance(OutputDic['개념키워드'], list) or not all(isinstance(item, str) for item in OutputDic['개념키워드']):
        return "ScriptPlan, JSON에서 오류 발생: '개념키워드'는 문자열 리스트여야 합니다"
    if not isinstance(OutputDic['독자키워드'], list) or not all(isinstance(item, str) for item in OutputDic['독자키워드']):
        return "ScriptPlan, JSON에서 오류 발생: '독자키워드'는 문자열 리스트여야 합니다"
    if not isinstance(OutputDic['정보의질'], int) or not (0 <= OutputDic['정보의질'] <= 100):
        return "ScriptPlan, JSON에서 오류 발생: '정보의질'은 0-100 사이의 정수여야 합니다"

    # Error4: '가치' 키 구조 검증
    if not isinstance(OutputDic['가치'], dict):
        return "ScriptPlan, JSON에서 오류 발생: '가치'는 딕셔너리 형태여야 합니다"

    # '가치' 내부 필수 키 확인
    required_sub_keys = ['글이전해줄핵심가치', '글이전해줄핵심포인트들', '글이전해줄핵심비전']
    for sub_key in required_sub_keys:
        if sub_key not in OutputDic['가치']:
            return f"ScriptPlan, JSONKeyError: '가치'에 누락된 키: {sub_key}"

        sub_item = OutputDic['가치'][sub_key]

        # 각 항목은 딕셔너리 형태여야 함
        if not isinstance(sub_item, dict):
            return f"ScriptPlan, JSON에서 오류 발생: '가치 > {sub_key}'는 딕셔너리 형태여야 합니다"

        # 내부 필수 키 확인
        required_detail_keys = ['설명', '키워드', '중요도']
        missing_detail_keys = [key for key in required_detail_keys if key not in sub_item]
        if missing_detail_keys:
            return f"ScriptPlan, JSONKeyError: '가치 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

        # 데이터 타입 검증
        if not isinstance(sub_item['설명'], str):
            return f"ScriptPlan, JSON에서 오류 발생: '가치 > {sub_key} > 설명'은 문자열이어야 합니다"
        if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
            return f"ScriptPlan, JSON에서 오류 발생: '가치 > {sub_key} > 키워드'는 문자열 리스트여야 합니다"
        if not isinstance(sub_item['중요도'], int) or not (0 <= sub_item['중요도'] <= 100):
            return f"ScriptPlan, JSON에서 오류 발생: '가치 > {sub_key} > 중요도'는 0-100 사이의 정수여야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic

## Process2: TitleAndIndexGen의 Filter(Error 예외처리)
def TitleAndIndexGenFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "TitleAndIndexGen, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_keys = ['글쓰기형태', '제목부제형태', '제목', '부제', '메인목차']
    missing_top_keys = [key for key in required_top_keys if key not in OutputDic]
    if missing_top_keys:
        return f"TitleAndIndexGen, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"

    # Error3: 최상위 키 데이터 타입 검증
    valid_writing_styles = {'열거형', '결론우선형', '공감형'}
    valid_title_styles = {'신조어', '성과강조', '문제해결', '호기심', '숫자임팩트', '스토리메타포', '트렌드접목', '고민언급', '키워드감성', '비전도전'}

    if not isinstance(OutputDic['글쓰기형태'], str) or OutputDic['글쓰기형태'] not in valid_writing_styles:
        return "TitleAndIndexGen, JSON에서 오류 발생: '글쓰기형태'는 ['열거형', '결론우선형', '공감형'] 중 하나여야 합니다"

    if not isinstance(OutputDic['제목부제형태'], str) or OutputDic['제목부제형태'] not in valid_title_styles:
        return "TitleAndIndexGen, JSON에서 오류 발생: '제목부제형태'는 ['신조어', '성과강조', '문제해결', '호기심', '숫자임팩트', '스토리메타포', '트렌드접목', '고민언급', '키워드감성', '비전도전'] 중 하나여야 합니다"

    if not isinstance(OutputDic['제목'], str):
        return "TitleAndIndexGen, JSON에서 오류 발생: '제목'은 문자열이어야 합니다"

    if not isinstance(OutputDic['부제'], str):
        return "TitleAndIndexGen, JSON에서 오류 발생: '부제'는 문자열이어야 합니다"

    # Error4: '메인목차' 리스트 검증
    if not isinstance(OutputDic['메인목차'], list):
        return "TitleAndIndexGen, JSON에서 오류 발생: '메인목차'는 리스트여야 합니다"

    if len(OutputDic['메인목차']) != 10:
        return "TitleAndIndexGen, JSON에서 오류 발생: '메인목차'는 정확히 10개의 항목을 포함해야 합니다"

    for idx, item in enumerate(OutputDic['메인목차']):
        if not isinstance(item, dict):
            return f"TitleAndIndexGen, JSON에서 오류 발생: '메인목차[{idx}]'은 딕셔너리 형태여야 합니다"

        required_keys = ['순번', '목차']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"TitleAndIndexGen, JSONKeyError: '메인목차[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        if not isinstance(item['순번'], str) or not item['순번'].isdigit():
            return f"TitleAndIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 순번'은 숫자로 된 문자열이어야 합니다"

        if not isinstance(item['목차'], str):
            return f"TitleAndIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 목차'는 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic

## Process3: SummaryOfIndexGen의 Filter(Error 예외처리)
def SummaryOfIndexGenFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SummaryOfIndexGen, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '메인목차' not in OutputDic:
        return "SummaryOfIndexGen, JSONKeyError: '메인목차' 키가 누락되었습니다"

    # Error3: '메인목차' 데이터 타입 검증
    if not isinstance(OutputDic['메인목차'], list):
        return "SummaryOfIndexGen, JSON에서 오류 발생: '메인목차'는 리스트 형태여야 합니다"

    for idx, main_item in enumerate(OutputDic['메인목차']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(main_item, dict):
            return f"SummaryOfIndexGen, JSON에서 오류 발생: '메인목차[{idx}]'은 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_main_keys = ['순번', '메인목차', '서브목차', '전체요약']
        missing_main_keys = [key for key in required_main_keys if key not in main_item]
        if missing_main_keys:
            return f"SummaryOfIndexGen, JSONKeyError: '메인목차[{idx}]'에 누락된 키: {', '.join(missing_main_keys)}"

        # 데이터 타입 검증
        if not isinstance(main_item['순번'], str) or not main_item['순번'].isdigit():
            return f"SummaryOfIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 순번'은 숫자로 된 문자열이어야 합니다"
        if not isinstance(main_item['메인목차'], str):
            return f"SummaryOfIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 메인목차'는 문자열이어야 합니다"
        if not isinstance(main_item['전체요약'], str):
            return f"SummaryOfIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 전체요약'은 문자열이어야 합니다"

        # Error4: '서브목차' 리스트 검증
        if not isinstance(main_item['서브목차'], list):
            return f"SummaryOfIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 서브목차'는 리스트 형태여야 합니다"

        if len(main_item['서브목차']) < 5:
            return f"SummaryOfIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 서브목차'는 최소 5개 이상의 항목을 포함해야 합니다"

        for sub_idx, sub_item in enumerate(main_item['서브목차']):
            # 각 서브목차가 딕셔너리인지 확인
            if not isinstance(sub_item, dict):
                return f"SummaryOfIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 서브목차[{sub_idx}]'은 딕셔너리 형태여야 합니다"

            # 필수 키 확인
            required_sub_keys = ['서브목차', '키워드', '요약']
            missing_sub_keys = [key for key in required_sub_keys if key not in sub_item]
            if missing_sub_keys:
                return f"SummaryOfIndexGen, JSONKeyError: '메인목차[{idx}] > 서브목차[{sub_idx}]'에 누락된 키: {', '.join(missing_sub_keys)}"

            # 데이터 타입 검증
            if not isinstance(sub_item['서브목차'], str):
                return f"SummaryOfIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 서브목차[{sub_idx}] > 서브목차'는 문자열이어야 합니다"
            if not isinstance(sub_item['키워드'], list) or not all(isinstance(kw, str) for kw in sub_item['키워드']):
                return f"SummaryOfIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 서브목차[{sub_idx}] > 키워드'는 문자열 리스트여야 합니다"
            if not isinstance(sub_item['요약'], str):
                return f"SummaryOfIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 서브목차[{sub_idx}] > 요약'은 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic

## Process4: ScriptIntroductionGen의 Filter(Error 예외처리)
def ScriptIntroductionGenFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "ScriptIntroductionGen, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    if '도입내용' not in OutputDic:
        return "ScriptIntroductionGen, JSONKeyError: '도입내용' 키가 누락되었습니다"

    # Error3: '도입내용'이 딕셔너리인지 확인
    if not isinstance(OutputDic['도입내용'], dict):
        return "ScriptIntroductionGen, JSON에서 오류 발생: '도입내용'은 딕셔너리 형태여야 합니다"

    # 필수 키 확인
    required_keys = ['참고요소', '도입']
    missing_keys = [key for key in required_keys if key not in OutputDic['도입내용']]
    if missing_keys:
        return f"ScriptIntroductionGen, JSONKeyError: '도입내용'에 누락된 키: {', '.join(missing_keys)}"

    # Error4: 데이터 타입 검증
    if not isinstance(OutputDic['도입내용']['참고요소'], list) or not all(isinstance(item, str) for item in OutputDic['도입내용']['참고요소']):
        return "ScriptIntroductionGen, JSON에서 오류 발생: '도입내용 > 참고요소'는 문자열 리스트여야 합니다"

    if not isinstance(OutputDic['도입내용']['도입'], str):
        return "ScriptIntroductionGen, JSON에서 오류 발생: '도입내용 > 도입'은 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic

## Process5: ShortScriptGen의 Filter(Error 예외처리)
def ShortScriptGenFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "ShortScriptGen, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 필수 키 확인
    required_keys = ['파트순번', '파트명', '챕터순번', '챕터명', '초안']
    missing_keys = [key for key in required_keys if key not in OutputDic]
    if missing_keys:
        return f"ShortScriptGen, JSONKeyError: 누락된 키: {', '.join(missing_keys)}"

    # Error3: 데이터 타입 검증
    if not isinstance(OutputDic['파트순번'], str) or not OutputDic['파트순번'].isdigit():
        return "ShortScriptGen, JSON에서 오류 발생: '파트순번'은 숫자로 된 문자열이어야 합니다"
    
    if not isinstance(OutputDic['파트명'], str):
        return "ShortScriptGen, JSON에서 오류 발생: '파트명'은 문자열이어야 합니다"

    if not isinstance(OutputDic['챕터순번'], str) or not OutputDic['챕터순번'].isdigit():
        return "ShortScriptGen, JSON에서 오류 발생: '챕터순번'은 숫자로 된 문자열이어야 합니다"
    
    if not isinstance(OutputDic['챕터명'], str):
        return "ShortScriptGen, JSON에서 오류 발생: '챕터명'은 문자열이어야 합니다"

    if not isinstance(OutputDic['초안'], str):
        return "ShortScriptGen, JSON에서 오류 발생: '초안'은 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic

## Process6: ShortScriptMerge의 Filter(Error 예외처리)
def ShortScriptMergeFilter(Response, CheckCount):
    # Error1: JSON 형식이 아닐 때의 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "ShortScriptMerge, JSONDecode에서 오류 발생: JSONDecodeError"
    
    return OutputDic

## Process7: LongScriptGen의 Filter(Error 예외처리)
def LongScriptGenFilter(Response, CheckCount):
    # Error1: JSON 형식이 아닐 때의 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "LongScriptGen, JSONDecode에서 오류 발생: JSONDecodeError"
    
    return OutputDic

## Process8: LongScriptEdit의 Filter(Error 예외처리)
def LongScriptEditFilter(Response, CheckCount):
    # Error1: JSON 형식이 아닐 때의 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "LongScriptEdit, JSONDecode에서 오류 발생: JSONDecodeError"
    
    return OutputDic

#######################
##### Process 응답 #####
#######################
## Process LLMResponse 함수
def ProcessResponse(projectName, email, Process, Input, ProcessCount, InputCount, FilterFunc, CheckCount, LLM, mode, MessagesReview, input2 = ""):

    ErrorCount = 0
    while True:
        if LLM == "OpenAI":
            Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, Input2 = input2, messagesReview = MessagesReview)
        elif LLM == "Anthropic":
            Response, Usage, Model = ANTHROPIC_LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, messagesReview = MessagesReview)
        Filter = FilterFunc(Response, CheckCount)
        
        if isinstance(Filter, str):
            print(f"Chain: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | {Filter}")
            ErrorCount += 1
            print(f"Chain: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | "
                f"오류횟수 {ErrorCount}회, 10초 후 프롬프트 재시도")
            
            if ErrorCount >= 10:
                sys.exit(f"Chain: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | "
                        f"오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
            time.sleep(10)
            continue
        
        print(f"Chain: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | JSONDecode 완료")
        return Filter

##################################
##### ProcessResponse 업데이트 #####
##################################
## Process DataFrame Completion 및 InputCount 확인
def ProcessDataFrameCheck(ScriptEditPath):
    ## Process Edit 불러오기
    with open(ScriptEditPath, 'r', encoding = 'utf-8') as DataFrameJson:
        ScriptEditFrame = json.load(DataFrameJson)
    
    ## Completion 및 ProcessCount 확인
    Completion = ScriptEditFrame[0]['Completion']
    InputCount = ScriptEditFrame[0]['ProcessCount']
    
    return Completion, InputCount

## Process1: ScriptPlanProcess DataFrame 저장
def ScriptPlanProcessDataFrameSave(email, ProjectName, BookScriptGenDataFramePath, ProjectDataFrameScriptPath, DemandScriptPlanResponse, Process, InputCount, TotalInputCount, ProcessNumber):
    ## ScriptPlanFrame 불러오기
    ScriptPlanFramePath = os.path.join(BookScriptGenDataFramePath, "b5312-01_ScriptPlanFrame.json") 
    with open(ScriptPlanFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        ScriptPlanFrame = json.load(DataFrameJson)
    
    ## ScriptPlanFrame 업데이트
    ScriptPlanFrame[0]['ProjectName'] = ProjectName
    ScriptPlanFrame[0]['TaskName'] = Process
    
    ## ScriptPlanFrame 첫번째 데이터 프레임 복사
    ScriptPlan = ScriptPlanFrame[1][0].copy()
    ScriptPlan['Background'] = DemandScriptPlanResponse['배경']
    ScriptPlan['Subject'] = DemandScriptPlanResponse['주제']
    ScriptPlan['Range'] = DemandScriptPlanResponse['범위']
    ScriptPlan['ConceptKeyword'] = DemandScriptPlanResponse['개념키워드']
    ScriptPlan['TargetKeyword'] = DemandScriptPlanResponse['독자키워드']

    ScriptPlan['Supply']['Value']['Sentence'] = DemandScriptPlanResponse['가치']['글이전해줄핵심가치']['설명']
    ScriptPlan['Supply']['Value']['KeyWord'] = DemandScriptPlanResponse['가치']['글이전해줄핵심가치']['키워드']
    ScriptPlan['Supply']['Value']['Weight'] = DemandScriptPlanResponse['가치']['글이전해줄핵심가치']['중요도']

    ScriptPlan['Supply']['Points']['Sentence'] = DemandScriptPlanResponse['가치']['글이전해줄핵심포인트들']['설명']
    ScriptPlan['Supply']['Points']['KeyWord'] = DemandScriptPlanResponse['가치']['글이전해줄핵심포인트들']['키워드']
    ScriptPlan['Supply']['Points']['Weight'] = DemandScriptPlanResponse['가치']['글이전해줄핵심포인트들']['중요도']

    ScriptPlan['Supply']['Vision']['Sentence'] = DemandScriptPlanResponse['가치']['글이전해줄핵심비전']['설명']
    ScriptPlan['Supply']['Vision']['KeyWord'] = DemandScriptPlanResponse['가치']['글이전해줄핵심비전']['키워드']
    ScriptPlan['Supply']['Vision']['Weight'] = DemandScriptPlanResponse['가치']['글이전해줄핵심비전']['중요도']

    ScriptPlan['Weight'] = DemandScriptPlanResponse['정보의질']
    
    ## ScriptPlanFrame 데이터 프레임 업데이트
    ScriptPlanFrame[1].append(ScriptPlan)
    
    ## ScriptPlanFrame ProcessCount 및 Completion 업데이트
    ScriptPlanFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        ScriptPlanFrame[0]['Completion'] = 'Yes'
    
    ## ScriptPlanFrame 저장
    ProjectDataFrameScriptPalnPath = os.path.join(ProjectDataFrameScriptPath, f'{email}_{ProjectName}_{ProcessNumber}_{Process}DataFrame.json')
    with open(ProjectDataFrameScriptPalnPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(ScriptPlanFrame, DataFrameJson, indent = 4, ensure_ascii = False)
    
    return ProjectDataFrameScriptPalnPath

##############################
##### ProcessEdit 업데이트 #####
##############################
## Process Edit Completion 및 ProcessCount 확인
def ProcessEditCompletionCheck(ScriptEditPath):
    ## Process Edit 불러오기
    with open(ScriptEditPath, 'r', encoding = 'utf-8') as ScriptEditJson:
        ScriptEdit = json.load(ScriptEditJson)
    
    ## Completion 및 ProcessCount 확인
    Completion = ScriptEdit[0]['Completion']
    ProcessCount = ScriptEdit[0]['InputCount']
    
    return Completion, ProcessCount

## Process Edit Prompt 확인
def ProcessEditPromptCheck(ScriptEditPath, Process):
    
    ## 빈 Prompt 제거 함수
    def CleanPrompts(Edit):
        if isinstance(Edit, dict):
            NewDict = {}
            for key, value in Edit.items():
                if isinstance(value, str):
                    NewValue = value.replace("<prompt: >", "").strip()
                    if NewValue:  # 값이 비어있지 않다면 추가
                        NewDict[key] = NewValue
                elif isinstance(value, dict):
                    NewValue = CleanPrompts(value)
                    if NewValue:  # 빈 딕셔너리는 추가하지 않음
                        NewDict[key] = NewValue
                elif isinstance(value, list):
                    cleaned_list = [CleanPrompts(item) if isinstance(item, dict) else item.replace("<prompt: >", "").strip() for item in value]
                    cleaned_list = [item for item in cleaned_list if item]  # 빈 값 제거
                    if cleaned_list:  # 리스트가 비어 있지 않다면 추가
                        NewDict[key] = cleaned_list
            return NewDict

        elif isinstance(Edit, list):
            cleaned_list = [CleanPrompts(item) if isinstance(item, dict) else item.replace("<prompt: >", "").strip() for item in Edit]
            return [item for item in cleaned_list if item]  # 빈 값 제거

        elif isinstance(Edit, str):
            return Edit.replace("<prompt: >", "").strip()

        return Edit

    ## Prompt 확인 함수
    def PromptCheck(Edit):
        if isinstance(Edit, dict):
            for key, value in Edit.items():
                if isinstance(value, str) and "<prompt:" in value:
                    return True  # '<prompt: ...>'이 포함된 문자열이면 True 반환
                if isinstance(value, dict) and PromptCheck(value):
                    return True
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and "<prompt:" in item:
                            return True
                        if isinstance(item, dict) and PromptCheck(item):
                            return True
        elif isinstance(Edit, list):
            for item in Edit:
                if isinstance(item, str) and "<prompt:" in item:
                    return True
                if isinstance(item, dict) and PromptCheck(item):
                    return True
        return False  # '<prompt: ...>'이 없으면 False 반환
    
    PromptList = []
    if os.path.exists(ScriptEditPath):
        ## ScriptEdit 불러오기
        with open(ScriptEditPath, 'r', encoding='utf-8') as ScriptEditJson:
            ScriptEdit = json.load(ScriptEditJson)
        ScriptEditProcess = ScriptEdit.get(Process, [])
        
        ## '<prompt: ...>' 확인
        for i, ProcessDic in enumerate(ScriptEditProcess):
            CleanedProcessDic = CleanPrompts(ProcessDic)  # 빈 '<prompt: >' 삭제 후 데이터 정리
            if PromptCheck(CleanedProcessDic):  # '<prompt: ...>'이 있는 경우만 리스트에 추가
                PromptList.append({'PromptId': i + 1, 'PromptData': CleanedProcessDic})
        
    return PromptList

## Process Edit 저장
def ScriptPlanProcessEditSave(ProjectDataFramePath, ScriptEditPath, Process, InputCount):
        
    ## ProcessDic 재구조화 함수
    def RestructureProcessDic(ProcessDic):
        def ModifyValues(data):
            if isinstance(data, dict):
                NewDict = {}
                for key, value in data.items():
                    if key == "Weight":
                        continue  # 'Weight' 키 제거
                    
                    if isinstance(value, dict) or isinstance(value, list):
                        NewValue = ModifyValues(value)  # 재귀 처리
                    elif isinstance(value, str):
                        NewValue = value + "<prompt: >"
                    else:
                        NewValue = value
                    
                    NewDict[key] = NewValue
                return NewDict
            elif isinstance(data, list):
                if len(data) > 0:
                    data[-1] = "<prompt: >"  # 리스트의 마지막 요소 변경
                return data
            else:
                return data

        return ModifyValues(ProcessDic)
    
    ## ScriptDataFrame 불러온 뒤 Completion 확인
    with open(ProjectDataFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        ScriptDataFrame = json.load(DataFrameJson)
    ## ScriptEdit 재구조화 후 저장
    ScriptEdit = {}
    if ScriptDataFrame[0]['Completion'] == 'Yes':
        ## ScriptEdit이 존재할때
        if os.path.exists(ScriptEditPath):
            ## ScriptEdit 업데이트
            with open(ScriptEditPath, 'r', encoding = 'utf-8') as ScriptEditJson:
                ScriptEdit = json.load(ScriptEditJson)
        
        ## ScriptEdit 업데이트
        ScriptEdit[Process] = []
        for i in range(InputCount, len(ScriptDataFrame)):
            ProcessDic = ScriptDataFrame[1][i]
            ReStructureProcessDic = RestructureProcessDic(ProcessDic)
            ScriptEdit[Process].append(ReStructureProcessDic)
        
        ## ScriptEdit 저장
        with open(ScriptEditPath, 'w', encoding = 'utf-8') as ScriptEditJson:
            json.dump(ScriptEdit, ScriptEditJson, indent = 4, ensure_ascii = False)
            
        return True
    
    else:
        return False

################################
##### Process 진행 및 업데이트 #####
################################
## BookScript 프롬프트 요청 및 결과물 Json화
def BookScriptGenProcessUpdate(projectName, email, Intention, mode = "Master", MessagesReview = "on"):
    print(f"< User: {email} | Gen: {projectName} | BookScriptGenUpdate 시작 >")
    ## SearchResultData 경로
    TotalSearchResultDataTempPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1513_SearchResultData/s15131_TotalSearchResultData/TotalSearchResultDataTemp"
    
    ## projectName_script 경로 설정
    ProjectScriptPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script"
    ProjectDataFrameScriptPath = os.path.join(ProjectScriptPath, f'{projectName}_dataframe_script_file')
    ProjectMasterScriptPath = os.path.join(ProjectScriptPath, f'{projectName}_master_script_file')
    ScriptEditPath = os.path.join(ProjectMasterScriptPath, f'[{projectName}_Script_Edit].json')
    
    ## BookScriptGenDataFrame 경로
    BookScriptGenDataFramePath = "/yaas/backend/b5_Database/b53_ProjectData/b531_ScriptProject/b5312_BookScriptGen"
    
    ## Process1: ScriptPlan Response 생성
    # InputCount 계산
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    TotalInputCount = 1 # 인풋의 전체 카운트
    InputCount = 1 # 현재 인풋 카운트
    Process = "ScriptPlan"
    IntentionProcess = Intention + Process
    PromptList = ProcessEditPromptCheck(ScriptEditPath, Process)
    #### PromptList의 결과에 따라서 1. 최초 프롬프트 진행 2. 피드백 프롬프트 진행 3. 완료 후 넘어가기 ####
    ## Process1-1: DemandScriptPlan Response 생성
    if Intention == "Demand":
        ## Input 생성
        Input = DemandCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, ProjectName, Intention)
        
        ## Response 생성
        ScriptPlanResponse = ProcessResponse(projectName, email, IntentionProcess, Input, InputCount, InputCount, ScriptPlanFilter, CheckCount, "OpenAI", mode, MessagesReview)
        
    ## Process1-2: SupplyScriptPlan Response 생성
    if Intention == "Supply":
        ## Input 생성
        Input = SupplyCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, ProjectName, Intention)
        
        ## Response 생성
        ScriptPlanResponse = ProcessResponse(projectName, email, IntentionProcess, Input, InputCount, InputCount, ScriptPlanFilter, CheckCount, "OpenAI", mode, MessagesReview)
        
    ## Process1-3: SimilarityScriptPlan Response 생성
    if Intention == "Similarity":
        ## Input 생성
        Input1 = SupplyCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, ProjectName, Intention)
        Input2 = DemandCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, ProjectName, Intention)
        
        ## Response 생성
        ScriptPlanResponse = ProcessResponse(projectName, email, IntentionProcess, Input1, InputCount, InputCount, ScriptPlanFilter, CheckCount, "OpenAI", mode, MessagesReview, input2 = Input2)
        
    ## DataFrame 및 Edit 저장
    ProjectDataFrameScriptPalnPath = ScriptPlanProcessDataFrameSave(email, ProjectName, BookScriptGenDataFramePath, ProjectDataFrameScriptPath, ScriptPlanResponse, Process, InputCount, TotalInputCount, '01')
    ScriptPlanProcessEditSave(ProjectDataFrameScriptPalnPath, ScriptEditPath, Process, InputCount)

    print(f"[ User: {email} | Chain: {projectName} | BookScriptGenUpdate 완료 ]")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '250121_테스트'
    #########################################################################
    Intention = "Similarity"
    # JSON 파일 경로
    BookScriptGenProcessUpdate(ProjectName, email, Intention)