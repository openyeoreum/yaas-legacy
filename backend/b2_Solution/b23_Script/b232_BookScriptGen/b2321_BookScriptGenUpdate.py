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
## ContextToInput 생성 필요시 프롬프트 생성 ## 필터 말고 원본 파일?
def ContextToInput(FilteredSearchResult, Type):
    return ContextData

## Process1-1: DemandScriptPlan의 Input
def DemandCollectionDataToScriptPlanInput(FilteredSearchResult, Type):
    ContextData = ContextToInput(FilteredSearchResult, Type)
    
    CollectionAnalysis = ContextData['CollectionAnalysis']
    Summary = CollectionAnalysis['Summary']
    KeyWord = CollectionAnalysis['KeyWord']
    DemandNeedsSentence = CollectionAnalysis['Demand']['Needs']['Sentence']
    DemandNeedsKeyWord = CollectionAnalysis['Demand']['Needs']['KeyWord']
    DemandPurposeSentence = CollectionAnalysis['Demand']['Purpose']['Sentence']
    DemandPurposeKeyWord = CollectionAnalysis['Demand']['Purpose']['KeyWord']
    DemandQuestionSentence = CollectionAnalysis['Demand']['Question']['Sentence']
    DemandQuestionKeyWord = CollectionAnalysis['Demand']['Question']['KeyWord']
    Input = '[핵심목적]\n' + Summary + '\n\n[분야]\n-' + '-\n'.join(KeyWord) + '\n\n[필요내용]\n' + DemandNeedsSentence + '\n[필요내용-키워드]\n-' + '-\n'.join(DemandNeedsKeyWord) + '\n\n[필요목표]\n' + DemandPurposeSentence + '\n[필요목표-키워드]\n-' + '-\n'.join(DemandPurposeKeyWord) + '\n\n[필요질문]\n' + DemandQuestionSentence + '\n[필요질문-키워드]\n-' + '-\n'.join(DemandQuestionKeyWord)
    
    return Input

## Process1-2: SupplyScriptPlan의 Input
def SupplyCollectionDataToScriptPlanInput(FilteredSearchResult, Type):
    ContextData = ContextToInput(FilteredSearchResult, Type)
    
    CollectionAnalysis = ContextData['CollectionAnalysis']
    Summary = CollectionAnalysis['Summary']
    KeyWord = CollectionAnalysis['KeyWord']
    SupplyNeedsSentence = CollectionAnalysis['Supply']['Satisfy']['Sentence']
    SupplyNeedsKeyWord = CollectionAnalysis['Supply']['Satisfy']['KeyWord']
    SupplyPurposeSentence = CollectionAnalysis['Supply']['Support']['Sentence']
    SupplyPurposeKeyWord = CollectionAnalysis['Supply']['Support']['KeyWord']
    SupplyQuestionSentence = CollectionAnalysis['Supply']['Solution']['Sentence']
    SupplyQuestionKeyWord = CollectionAnalysis['Supply']['Solution']['KeyWord']
    Input = '[핵심솔루션]\n' + Summary + '\n\n[분야]\n-' + '-\n'.join(KeyWord) + '\n\n[제안내용]\n' + SupplyNeedsSentence + '\n[제안내용-키워드]\n-' + '-\n'.join(SupplyNeedsKeyWord) + '\n\n[제안할목표]\n' + SupplyPurposeSentence + '\n[제안할목표-키워드]\n-' + '-\n'.join(SupplyPurposeKeyWord) + '\n\n[제안할해결책]\n' + SupplyQuestionSentence + '\n[제안할해결책-키워드]\n-' + '-\n'.join(SupplyQuestionKeyWord)
    
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
## Process1-1: DemandScriptPlan의 Filter(Error 예외처리)
def DemandScriptPlanFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "DemandScriptPlan, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_keys = ['배경', '주제', '범위', '개념키워드', '독자키워드', '가치', '정보의질']
    missing_top_keys = [key for key in required_top_keys if key not in OutputDic]
    if missing_top_keys:
        return f"DemandScriptPlan, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"

    # Error3: 최상위 키 데이터 타입 검증
    if not isinstance(OutputDic['배경'], str):
        return "DemandScriptPlan, JSON에서 오류 발생: '배경'은 문자열이어야 합니다"
    if not isinstance(OutputDic['주제'], str):
        return "DemandScriptPlan, JSON에서 오류 발생: '주제'은 문자열이어야 합니다"
    if not isinstance(OutputDic['범위'], str):
        return "DemandScriptPlan, JSON에서 오류 발생: '범위'은 문자열이어야 합니다"
    if not isinstance(OutputDic['개념키워드'], list) or not all(isinstance(item, str) for item in OutputDic['개념키워드']):
        return "DemandScriptPlan, JSON에서 오류 발생: '개념키워드'는 문자열 리스트여야 합니다"
    if not isinstance(OutputDic['독자키워드'], list) or not all(isinstance(item, str) for item in OutputDic['독자키워드']):
        return "DemandScriptPlan, JSON에서 오류 발생: '독자키워드'는 문자열 리스트여야 합니다"
    if not isinstance(OutputDic['정보의질'], int) or not (0 <= OutputDic['정보의질'] <= 100):
        return "DemandScriptPlan, JSON에서 오류 발생: '정보의질'은 0-100 사이의 정수여야 합니다"

    # Error4: '가치' 키 구조 검증
    if not isinstance(OutputDic['가치'], dict):
        return "DemandScriptPlan, JSON에서 오류 발생: '가치'는 딕셔너리 형태여야 합니다"

    # '가치' 내부 필수 키 확인
    required_sub_keys = ['글이전해줄핵심가치', '글이전해줄핵심포인트들', '글이전해줄핵심비전']
    for sub_key in required_sub_keys:
        if sub_key not in OutputDic['가치']:
            return f"DemandScriptPlan, JSONKeyError: '가치'에 누락된 키: {sub_key}"

        sub_item = OutputDic['가치'][sub_key]

        # 각 항목은 딕셔너리 형태여야 함
        if not isinstance(sub_item, dict):
            return f"DemandScriptPlan, JSON에서 오류 발생: '가치 > {sub_key}'는 딕셔너리 형태여야 합니다"

        # 내부 필수 키 확인
        required_detail_keys = ['설명', '키워드', '중요도']
        missing_detail_keys = [key for key in required_detail_keys if key not in sub_item]
        if missing_detail_keys:
            return f"DemandScriptPlan, JSONKeyError: '가치 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

        # 데이터 타입 검증
        if not isinstance(sub_item['설명'], str):
            return f"DemandScriptPlan, JSON에서 오류 발생: '가치 > {sub_key} > 설명'은 문자열이어야 합니다"
        if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
            return f"DemandScriptPlan, JSON에서 오류 발생: '가치 > {sub_key} > 키워드'는 문자열 리스트여야 합니다"
        if not isinstance(sub_item['중요도'], int) or not (0 <= sub_item['중요도'] <= 100):
            return f"DemandScriptPlan, JSON에서 오류 발생: '가치 > {sub_key} > 중요도'는 0-100 사이의 정수여야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic

## Process1-2: SupplyScriptPlan의 Filter(Error 예외처리)
def SupplyScriptPlanFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplyScriptPlan, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_keys = ['배경', '주제', '범위', '개념키워드', '독자키워드', '가치', '정보의질']
    missing_top_keys = [key for key in required_top_keys if key not in OutputDic]
    if missing_top_keys:
        return f"SupplyScriptPlan, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"

    # Error3: 최상위 키 데이터 타입 검증
    if not isinstance(OutputDic['배경'], str):
        return "SupplyScriptPlan, JSON에서 오류 발생: '배경'은 문자열이어야 합니다"
    if not isinstance(OutputDic['주제'], str):
        return "SupplyScriptPlan, JSON에서 오류 발생: '주제'은 문자열이어야 합니다"
    if not isinstance(OutputDic['범위'], str):
        return "SupplyScriptPlan, JSON에서 오류 발생: '범위'은 문자열이어야 합니다"
    if not isinstance(OutputDic['개념키워드'], list) or not all(isinstance(item, str) for item in OutputDic['개념키워드']):
        return "SupplyScriptPlan, JSON에서 오류 발생: '개념키워드'는 문자열 리스트여야 합니다"
    if not isinstance(OutputDic['독자키워드'], list) or not all(isinstance(item, str) for item in OutputDic['독자키워드']):
        return "SupplyScriptPlan, JSON에서 오류 발생: '독자키워드'는 문자열 리스트여야 합니다"
    if not isinstance(OutputDic['정보의질'], int) or not (0 <= OutputDic['정보의질'] <= 100):
        return "SupplyScriptPlan, JSON에서 오류 발생: '정보의질'은 0-100 사이의 정수여야 합니다"

    # Error4: '가치' 키 구조 검증
    if not isinstance(OutputDic['가치'], dict):
        return "SupplyScriptPlan, JSON에서 오류 발생: '가치'는 딕셔너리 형태여야 합니다"

    # '가치' 내부 필수 키 확인
    required_sub_keys = ['글이전해줄핵심가치', '글이전해줄핵심포인트들', '글이전해줄핵심비전']
    for sub_key in required_sub_keys:
        if sub_key not in OutputDic['가치']:
            return f"SupplyScriptPlan, JSONKeyError: '가치'에 누락된 키: {sub_key}"

        sub_item = OutputDic['가치'][sub_key]

        # 각 항목은 딕셔너리 형태여야 함
        if not isinstance(sub_item, dict):
            return f"SupplyScriptPlan, JSON에서 오류 발생: '가치 > {sub_key}'는 딕셔너리 형태여야 합니다"

        # 내부 필수 키 확인
        required_detail_keys = ['설명', '키워드', '중요도']
        missing_detail_keys = [key for key in required_detail_keys if key not in sub_item]
        if missing_detail_keys:
            return f"SupplyScriptPlan, JSONKeyError: '가치 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

        # 데이터 타입 검증
        if not isinstance(sub_item['설명'], str):
            return f"SupplyScriptPlan, JSON에서 오류 발생: '가치 > {sub_key} > 설명'은 문자열이어야 합니다"
        if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
            return f"SupplyScriptPlan, JSON에서 오류 발생: '가치 > {sub_key} > 키워드'는 문자열 리스트여야 합니다"
        if not isinstance(sub_item['중요도'], int) or not (0 <= sub_item['중요도'] <= 100):
            return f"SupplyScriptPlan, JSON에서 오류 발생: '가치 > {sub_key} > 중요도'는 0-100 사이의 정수여야 합니다"

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
## ProcessDataFrame 저장
def ProcessDataFrameSave(MainKey, InputDic, OutputDicSet, DataTempPath):
    # DataTempPath 폴더가 없으면 생성
    if not os.path.exists(DataTempPath):
        os.makedirs(DataTempPath)

    # ProcessKeyList 생성
    ProcessKeyList = []
    ProcessDicList = []

    #### Search ####
    # Search-Term
    Term = InputDic['Input']
    TermText = InputDic['TermText']
    ## SearchDic ##
    SearchDic = {'Term': Term}
    
    ProcessKeyList.append("DemandSearch")
    ProcessDicList.append(SearchDic)
    #### Search ####
    
    #### Detail ####
    Process = "BookScriptDetail"
    if Process in OutputDicSet:
        # Detail-Summary
        ScarchSummary = OutputDicSet[Process]['핵심목적']
        # Detail-Needs
        DetailNeeds = OutputDicSet[Process]['필요내용']
        # Detail-Purpose
        DetailPurpose = OutputDicSet[Process]['필요목표']
        # Detail-Question
        DetailQuestion = OutputDicSet[Process]['필요질문']
        # Detail-Weight
        DetailWeight = OutputDicSet[Process]['검색어완성도']
        # Detail-Feedback
        DetailFeedback = OutputDicSet[Process]['검색어피드백']
        ## DetailDic ##
        DetailDic = {'Summary': ScarchSummary, 'Needs': DetailNeeds, 'Purpose': DetailPurpose, 'Question': DetailQuestion, 'Weight': DetailWeight, 'Feedback': DetailFeedback}
        
        ProcessKeyList.append("DemandDetail")
        ProcessDicList.append(DetailDic)
    #### Detail ####
    
    #### Context ####
    Process = "BookScriptContext"
    if Process in OutputDicSet:
        # Context-Summary
        ContextSummary = OutputDicSet[Process]['핵심목적']
        # Context-KeyWord
        ContextKeyWord = OutputDicSet[Process]['분야']
        # Context-Demand
        ContextDemandNeeds = {"Sentence": OutputDicSet[Process]['필요']['필요내용']['설명'], "KeyWord": OutputDicSet[Process]['필요']['필요내용']['키워드'], "Weight": OutputDicSet[Process]['필요']['필요내용']['중요도']}
        ContextDemandPurpose = {"Sentence": OutputDicSet[Process]['필요']['필요목표']['설명'], "KeyWord": OutputDicSet[Process]['필요']['필요목표']['키워드'], "Weight": OutputDicSet[Process]['필요']['필요목표']['중요도']}
        ContextDemandQuestion = {"Sentence": OutputDicSet[Process]['필요']['필요질문']['설명'], "KeyWord": OutputDicSet[Process]['필요']['필요질문']['키워드'], "Weight": OutputDicSet[Process]['필요']['필요질문']['중요도']}
        ContextDemand = {'Needs': ContextDemandNeeds, 'Purpose': ContextDemandPurpose, 'Question': ContextDemandQuestion}
        # Context-Weight
        ContextWeight = OutputDicSet[Process]['정보의질']
        ## ContextDic ##
        ContextDic = {'Summary': ContextSummary, 'KeyWord': ContextKeyWord, 'Demand': ContextDemand, 'Weight': ContextWeight}
        
        ProcessKeyList.append("DemandContext")
        ProcessDicList.append(ContextDic)
    #### Context ####
    
    #### ContextExpertise ####
    Process = "BookScriptExpertiseChain"
    if Process in OutputDicSet:
        ContextExpertiseDicList = []
        for i in range(5):
            # ContextExpertise-Summary
            ContextExpertiseSummary = OutputDicSet[Process][f'전문데이터{i+1}']['핵심목적']
            # ContextExpertise-KeyWord
            ContextExpertiseKeyWord = OutputDicSet[Process][f'전문데이터{i+1}']['분야']
            # ContextExpertise-Demand
            ContextExpertiseDemandNeeds = {"Sentence": OutputDicSet[Process][f'전문데이터{i+1}']['필요']['필요내용']['설명'], "KeyWord": OutputDicSet[Process][f'전문데이터{i+1}']['필요']['필요내용']['키워드'], "Weight": OutputDicSet[Process][f'전문데이터{i+1}']['필요']['필요내용']['중요도']}
            ContextExpertiseDemandPurpose = {"Sentence": OutputDicSet[Process][f'전문데이터{i+1}']['필요']['필요목표']['설명'], "KeyWord": OutputDicSet[Process][f'전문데이터{i+1}']['필요']['필요목표']['키워드'], "Weight": OutputDicSet[Process][f'전문데이터{i+1}']['필요']['필요목표']['중요도']}
            ContextExpertiseDemandQuestion = {"Sentence": OutputDicSet[Process][f'전문데이터{i+1}']['필요']['필요질문']['설명'], "KeyWord": OutputDicSet[Process][f'전문데이터{i+1}']['필요']['필요질문']['키워드'], "Weight": OutputDicSet[Process][f'전문데이터{i+1}']['필요']['필요질문']['중요도']}
            ContextExpertiseDemand = {'Needs': ContextExpertiseDemandNeeds, 'Purpose': ContextExpertiseDemandPurpose, 'Question': ContextExpertiseDemandQuestion}
            # ContextExpertise-Weight
            ContextExpertiseWeight = OutputDicSet[Process][f'전문데이터{i+1}']['정보의질']
            ## ContextExpertiseDic ##
            ContextExpertiseDic = {'Summary': ContextExpertiseSummary, 'KeyWord': ContextExpertiseKeyWord, 'Demand': ContextExpertiseDemand, 'Weight': ContextExpertiseWeight}
            ContextExpertiseDicList.append(ContextExpertiseDic)
            
        ProcessKeyList.append("DemandContextExpertise")
        ProcessDicList.append(ContextExpertiseDicList)
    #### ContextExpertise ####
    
    #### ContextUltimate ####
    Process = "BookScriptUltimateChain"
    if Process in OutputDicSet:
        ContextUltimateDicList = []
        for i in range(5):
            # ContextUltimate-Summary
            ContextUltimateSummary = OutputDicSet[Process][f'연계데이터{i+1}']['핵심목적']
            # ContextUltimate-KeyWord
            ContextUltimateKeyWord = OutputDicSet[Process][f'연계데이터{i+1}']['분야']
            # ContextUltimate-Demand
            ContextUltimateDemandNeeds = {"Sentence": OutputDicSet[Process][f'연계데이터{i+1}']['필요']['필요내용']['설명'], "KeyWord": OutputDicSet[Process][f'연계데이터{i+1}']['필요']['필요내용']['키워드'], "Weight": OutputDicSet[Process][f'연계데이터{i+1}']['필요']['필요내용']['중요도']}
            ContextUltimateDemandPurpose = {"Sentence": OutputDicSet[Process][f'연계데이터{i+1}']['필요']['필요목표']['설명'], "KeyWord": OutputDicSet[Process][f'연계데이터{i+1}']['필요']['필요목표']['키워드'], "Weight": OutputDicSet[Process][f'연계데이터{i+1}']['필요']['필요목표']['중요도']}
            ContextUltimateDemandQuestion = {"Sentence": OutputDicSet[Process][f'연계데이터{i+1}']['필요']['필요질문']['설명'], "KeyWord": OutputDicSet[Process][f'연계데이터{i+1}']['필요']['필요질문']['키워드'], "Weight": OutputDicSet[Process][f'연계데이터{i+1}']['필요']['필요질문']['중요도']}
            ContextUltimateDemand = {'Needs': ContextUltimateDemandNeeds, 'Purpose': ContextUltimateDemandPurpose, 'Question': ContextUltimateDemandQuestion}
            # ContextUltimate-Weight
            ContextUltimateWeight = OutputDicSet[Process][f'연계데이터{i+1}']['정보의질']
            ## ContextUltimateDic ##
            ContextUltimateDic = {'Summary': ContextUltimateSummary, 'KeyWord': ContextUltimateKeyWord, 'Demand': ContextUltimateDemand, 'Weight': ContextUltimateWeight}
            ContextUltimateDicList.append(ContextUltimateDic)
            
        ProcessKeyList.append("DemandContextUltimate")
        ProcessDicList.append(ContextUltimateDicList)
    #### ContextUltimate ####
    
    DataTemp = {MainKey: {}}
    for i in range(len(ProcessKeyList)):
        DataTemp[MainKey][ProcessKeyList[i]] = ProcessDicList[i]
    
    # DataTempJson 저장
    DateTime = datetime.now().strftime('%Y%m%d%H%M%S')
    DataTempJsonPath = os.path.join(DataTempPath, f"BookScript_({DateTime})_{TermText}.json")
    with open(DataTempJsonPath, 'w', encoding = 'utf-8') as DataTempJson:
        json.dump(DataTemp, DataTempJson, ensure_ascii = False, indent = 4)
        
    # CollectionDataChain 추출
    CollectionDataChain = DataTemp[MainKey]
        
    return CollectionDataChain, DateTime

##############################
##### ProcessEdit 업데이트 #####
##############################

################################
##### Process 진행 및 업데이트 #####
################################
## BookScript 프롬프트 요청 및 결과물 Json화
def BookScriptGenProcessUpdate(projectName, email, InputDic, mode = "Master", MainKey = 'BookScriptGen', MessagesReview = "on"):
    print(f"< User: {email} | Gen: {projectName} | BookScriptGenUpdate 시작 >")
    ## TotalPublisherData 경로 설정
    ProjectScriptPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script"
    ProjectDataFrameScriptPath = os.path.join(ProjectScriptPath, f'{projectName}_dataframe_script_file')
    ProjectMasterScriptPath = os.path.join(ProjectScriptPath, f'{projectName}_master_script_file')
    
    ## BookScriptDetailProcess
    CollectionData = InputDic['CollectionData']
    Type = InputDic['Type']
    # InputCount 계산
    InputCount = 8
    processCount = 1
    CheckCount = 0
    OutputDicSet = {}

    ## Process1-1: DemandScriptPlan Response 생성
    if Type == "Search":
        Process = "BookScriptDetail"
        Input = InputDic['Input']
        
        BookScriptDetailResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, BookScriptDetailFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicSet[Process] = BookScriptDetailResponse
        processCount += 1
    
    ## Process2: BookScriptContext Response 생성
    if Type == "Search":
        Process = "BookScriptContext"
        Input = BookScriptDetailResponse.copy()
        DeleteKeys = ['검색어완성도', '검색어피드백']
        for key in DeleteKeys:
            del Input[key]
    
        BookScriptContextResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, BookScriptContextFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicSet[Process] = BookScriptContextResponse
    elif Type == "Match":
        Process = "BookScriptContext"
        OutputDicSet[Process] = InputDic['CollectionData']
    processCount += 1
    
    ## Process3-1: BookScriptExpertise Response 생성
    if "Expertise" in Extension:
        Process = "BookScriptExpertise"
        if Type == "Search":
            Input = BookScriptContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        
        BookScriptExpertiseResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, BookScriptExpertiseFilter, CheckCount, "OpenAI", mode, MessagesReview)
        processCount += 1
        
        ## Process3-2: BookScriptExpertiseChain Response 연속 생성 및 Set로 합치기
        Process = "BookScriptExpertiseChain"
        BookScriptExpertiseChainResponseSet = {}
        for i, Response in enumerate(BookScriptExpertiseResponse):
            InputText = f'{Response}\n\n<데이터>\n{Input}\n'
            BookScriptExpertiseChainResponse = ProcessResponse(projectName, email, Process, InputText, processCount, InputCount, BookScriptExpertiseChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
            BookScriptExpertiseChainResponseSet[f'전문데이터{i+1}'] = {}
            BookScriptExpertiseChainResponse['핵심목적'] = f"{Response['전문분야']}  {BookScriptExpertiseChainResponse['핵심목적']}"
            BookScriptExpertiseChainResponseSet[f'전문데이터{i+1}'].update(BookScriptExpertiseChainResponse)
            processCount += 1

        # 최종 Set 데이터 추가
        OutputDicSet[Process] = BookScriptExpertiseChainResponseSet

    ## Process4-1: BookScriptUltimate Response 생성
    if "Ultimate" in Extension:
        Process = "BookScriptUltimate"
        if Type == "Search":
            Input = BookScriptContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        
        BookScriptUltimateResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, BookScriptUltimateFilter, CheckCount, "OpenAI", mode, MessagesReview)
        processCount += 1
        
        ## Process4-2: BookScriptUltimateChain Response 연속 생성 및 Set로 합치기
        Process = "BookScriptUltimateChain"
        BookScriptUltimateChainResponseSet = {}
        for i, Response in enumerate(BookScriptUltimateResponse):
            InputText = f'{Input}\n\n<새로운 핵심목적 메모>\n{Response}\n'
            BookScriptUltimateChainResponse = ProcessResponse(projectName, email, Process, InputText, processCount, InputCount, BookScriptUltimateChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
            BookScriptUltimateChainResponseSet[f'연계데이터{i+1}'] = {}
            BookScriptUltimateChainResponse['핵심목적'] = f"{Response['핵심목적']}  {BookScriptUltimateChainResponse['핵심목적']}"
            BookScriptUltimateChainResponseSet[f'연계데이터{i+1}'].update(BookScriptUltimateChainResponse)
            processCount += 1

        # 최종 Set 데이터 추가
        OutputDicSet[Process] = BookScriptUltimateChainResponseSet
    
    ## Process5: BookScriptDetailChain Response 생성
    if "Detail" in Extension:
        Process = "BookScriptDetailChain"
        if Type == "Search":
            Input = BookScriptContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        pass
    
    ## Process6: BookScriptRethinkingChain Response 생성
    if "Rethinking" in Extension:
        Process = "BookScriptRethinkingChain"
        if Type == "Search":
            Input = BookScriptContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        pass

    ## ProcessResponse 임시저장
    CollectionDataChain, DateTime = ProcessResponseTempSave(MainKey, InputDic, OutputDicSet, TotalBookScriptTempPath)

    print(f"[ User: {email} | Chain: {projectName} | BookScriptGenUpdate 완료 ]")
    
    return CollectionDataChain, DateTime

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241204_개정교육과정초등교과별이해연수'
    #########################################################################