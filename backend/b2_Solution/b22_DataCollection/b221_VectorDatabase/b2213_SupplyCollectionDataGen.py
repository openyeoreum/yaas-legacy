import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from datetime import datetime
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import OpenAI_LLMresponse, ANTHROPIC_LLMresponse

######################
##### Filter 조건 #####
######################
## Process1: SupplyCollectionDataDetail의 Filter(Error 예외처리)
def SupplyCollectionDataDetailFilter(Response, CheckCount):
    # Error1: JSON 형식이 아닐 때의 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplyCollectionDataDetail, JSONDecode에서 오류 발생: JSONDecodeError"
    
    # Error2: 최상위 필수 키 존재 여부 확인
    required_keys = ['핵심솔루션', '제안할내용', '제안할목표', '제안할해결책', '검색어완성도', '검색어피드백']
    missing_keys = [key for key in required_keys if key not in OutputDic]
    if missing_keys:
        return f"SupplyCollectionDataDetail, JSONKeyError: 누락된 키: {', '.join(missing_keys)}"
    
    # Error3: 데이터 타입 검증
    # 핵심솔루션, 제안할내용, 제안할목표, 제안할해결책은 문자열이어야 함
    for key in ['핵심솔루션', '제안할내용', '제안할목표', '제안할해결책']:
        if not isinstance(OutputDic[key], str):
            return f"SupplyCollectionDataDetail, JSON에서 오류 발생: '{key}'가 문자열이 아님"

    # 검색어완성도는 0-100 사이의 정수여야 함
    if not isinstance(OutputDic['검색어완성도'], int) or not (0 <= OutputDic['검색어완성도'] <= 100):
        return "SupplyCollectionDataDetail, JSON에서 오류 발생: '검색어완성도'는 0-100 사이의 정수가 아님"

    # 검색어피드백은 문자열 리스트여야 함
    if not isinstance(OutputDic['검색어피드백'], list) or not all(isinstance(item, str) for item in OutputDic['검색어피드백']):
        return "SupplyCollectionDataDetail, JSON에서 오류 발생: '검색어피드백'은 문자열 리스트가 아님"
    
    return OutputDic


## Process2: SupplyCollectionDataContext의 Filter(Error 예외처리)
def SupplyCollectionDataContextFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplyCollectionDataContext, JSONDecode에서 오류 발생: JSONDecodeError"
    
    # Error2: 최상위 필수 키 존재 여부 확인
    required_top_level_keys = ['핵심솔루션', '분야', '제안', '정보의질']
    missing_keys = [key for key in required_top_level_keys if key not in OutputDic]
    if missing_keys:
        return f"SupplyCollectionDataContext, JSONKeyError: 누락된 최상위 키: {', '.join(missing_keys)}"

    # Error3: 데이터 타입 검증
    # 핵심솔루션은 문자열이어야 함
    if not isinstance(OutputDic['핵심솔루션'], str):
        return "SupplyCollectionDataContext, JSON에서 오류 발생: '핵심솔루션'은 문자열이 아님"
    
    # 분야는 문자열 리스트여야 함
    if not isinstance(OutputDic['분야'], list) or not all(isinstance(item, str) for item in OutputDic['분야']):
        return "SupplyCollectionDataContext, JSON에서 오류 발생: '분야'는 문자열 리스트가 아님"
    
    # 정보의질은 0-100 사이의 정수여야 함
    if not isinstance(OutputDic['정보의질'], int) or not (0 <= OutputDic['정보의질'] <= 100):
        return "SupplyCollectionDataContext, JSON에서 오류 발생: '정보의질'은 0-100 사이의 정수가 아님"

    # Error4: '제안' 키의 구조 검증
    if not isinstance(OutputDic['제안'], dict):
        return "SupplyCollectionDataContext, JSON에서 오류 발생: '제안'은 딕셔너리 형태가 아님"

    # '제안' 내부 필수 키 확인
    required_sub_keys = ['제안내용', '제안할목표', '제안할해결책']
    missing_sub_keys = [key for key in required_sub_keys if key not in OutputDic['제안']]
    if missing_sub_keys:
        return f"SupplyCollectionDataContext, JSONKeyError: '제안'에 누락된 키: {', '.join(missing_sub_keys)}"
    
    # '제안' 내부 구조 검증
    for sub_key in required_sub_keys:
        sub_item = OutputDic['제안'][sub_key]
        if not isinstance(sub_item, dict):
            return f"SupplyCollectionDataContext, JSON에서 오류 발생: '제안 > {sub_key}'는 딕셔너리 형태가 아님"
        
        # 각 제안 항목의 내부 필수 키 확인
        required_detail_keys = ['설명', '키워드', '중요도']
        missing_detail_keys = [key for key in required_detail_keys if key not in sub_item]
        if missing_detail_keys:
            return f"SupplyCollectionDataContext, JSONKeyError: '제안 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

        # 데이터 타입 및 값 검증
        if not isinstance(sub_item['설명'], str):
            return f"SupplyCollectionDataContext, JSON에서 오류 발생: '제안 > {sub_key} > 설명'은 문자열이가 아님"
        if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
            return f"SupplyCollectionDataContext, JSON에서 오류 발생: '제안 > {sub_key} > 키워드'는 문자열 리스트가 아님"
        if not isinstance(sub_item['중요도'], int) or not (0 <= sub_item['중요도'] <= 100):
            return f"SupplyCollectionDataContext, JSON에서 오류 발생: '제안 > {sub_key} > 중요도'는 0-100 사이의 정수가 아님"

    # 모든 조건을 만족하면 파싱된 JSON 반환
    return OutputDic

## Process3: SupplyCollectionDataExtensionChainFilter의 Filter(Error 예외처리)
def SupplyCollectionDataExtensionChainFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplyCollectionDataExtensionChain, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 전문데이터1~5 존재 여부 확인
    required_top_level_keys = [f'전문데이터{i}' for i in range(1, 6)]
    missing_keys = [key for key in required_top_level_keys if key not in OutputDic]
    if missing_keys:
        return f"SupplyCollectionDataExtensionChain, JSONKeyError: 누락된 키: {', '.join(missing_keys)}"
    
    # Error3: 각 전문데이터의 구조 검증
    for key in required_top_level_keys:
        data = OutputDic[key]

        # 전문데이터 내부 필수 키 확인
        required_inner_keys = ['핵심솔루션', '분야', '제안', '정보의질']
        missing_inner_keys = [inner_key for inner_key in required_inner_keys if inner_key not in data]
        if missing_inner_keys:
            return f"SupplyCollectionDataExtensionChain, JSONKeyError: '{key}'에 누락된 키: {', '.join(missing_inner_keys)}"
        
        # 데이터 타입 검증
        if not isinstance(data['핵심솔루션'], str):
            return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 핵심솔루션'은 문자열이 아님"
        if not isinstance(data['분야'], list) or not all(isinstance(item, str) for item in data['분야']):
            return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 분야'는 문자열 리스트가 아님"
        if not isinstance(data['정보의질'], int) or not (0 <= data['정보의질'] <= 100):
            return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 정보의질'은 0-100 사이의 정수가 아님"

        # '제안' 키 구조 검증
        if not isinstance(data['제안'], dict):
            return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 제안'은 딕셔너리 형태가 아님"

        # '제안' 내부 필수 키 확인
        required_sub_keys = ['제안내용', '제안할목표', '제안할해결책']
        missing_sub_keys = [sub_key for sub_key in required_sub_keys if sub_key not in data['제안']]
        if missing_sub_keys:
            return f"SupplyCollectionDataExtensionChain, JSONKeyError: '{key} > 제안'에 누락된 키: {', '.join(missing_sub_keys)}"

        # '제안' 내부 구조 검증
        for sub_key in required_sub_keys:
            sub_item = data['제안'][sub_key]
            if not isinstance(sub_item, dict):
                return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key}'는 딕셔너리 형태가 아님"
            
            # 각 항목의 내부 필수 키 확인
            required_detail_keys = ['설명', '키워드', '중요도']
            missing_detail_keys = [k for k in required_detail_keys if k not in sub_item]
            if missing_detail_keys:
                return f"SupplyCollectionDataExtensionChain, JSONKeyError: '{key} > 제안 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

            # 데이터 타입 및 값 검증
            if not isinstance(sub_item['설명'], str):
                return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key} > 설명'은 문자열이 아님"
            if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
                return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key} > 키워드'는 문자열 리스트가 아님"
            if not isinstance(sub_item['중요도'], int) or not (0 <= sub_item['중요도'] <= 100):
                return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key} > 중요도'는 0-100 사이의 정수가 아님"

    return OutputDic

## Process4: SupplyCollectionDataExtensionChainFilter의 Filter(Error 예외처리)
def SupplyCollectionDataExtensionChainFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplyCollectionDataExtensionChain, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 전문데이터1~5 존재 여부 확인
    required_top_level_keys = [f'전문데이터{i}' for i in range(1, 6)]
    missing_keys = [key for key in required_top_level_keys if key not in OutputDic]
    if missing_keys:
        return f"SupplyCollectionDataExtensionChain, JSONKeyError: 누락된 키: {', '.join(missing_keys)}"
    
    # Error3: 각 전문데이터의 구조 검증
    for key in required_top_level_keys:
        data = OutputDic[key]

        # 전문데이터 내부 필수 키 확인
        required_inner_keys = ['핵심솔루션', '분야', '제안', '정보의질']
        missing_inner_keys = [inner_key for inner_key in required_inner_keys if inner_key not in data]
        if missing_inner_keys:
            return f"SupplyCollectionDataExtensionChain, JSONKeyError: '{key}'에 누락된 키: {', '.join(missing_inner_keys)}"
        
        # 데이터 타입 검증
        if not isinstance(data['핵심솔루션'], str):
            return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 핵심솔루션'은 문자열이 아님"
        if not isinstance(data['분야'], list) or not all(isinstance(item, str) for item in data['분야']):
            return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 분야'는 문자열 리스트가 아님"
        if not isinstance(data['정보의질'], int) or not (0 <= data['정보의질'] <= 100):
            return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 정보의질'은 0-100 사이의 정수가 아님"

        # '제안' 키 구조 검증
        if not isinstance(data['제안'], dict):
            return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 제안'은 딕셔너리 형태가 아님"

        # '제안' 내부 필수 키 확인
        required_sub_keys = ['제안내용', '제안할목표', '제안할해결책']
        missing_sub_keys = [sub_key for sub_key in required_sub_keys if sub_key not in data['제안']]
        if missing_sub_keys:
            return f"SupplyCollectionDataExtensionChain, JSONKeyError: '{key} > 제안'에 누락된 키: {', '.join(missing_sub_keys)}"

        # '제안' 내부 구조 검증
        for sub_key in required_sub_keys:
            sub_item = data['제안'][sub_key]
            if not isinstance(sub_item, dict):
                return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key}'는 딕셔너리 형태가 아님"
            
            # 각 항목의 내부 필수 키 확인
            required_detail_keys = ['설명', '키워드', '중요도']
            missing_detail_keys = [k for k in required_detail_keys if k not in sub_item]
            if missing_detail_keys:
                return f"SupplyCollectionDataExtensionChain, JSONKeyError: '{key} > 제안 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

            # 데이터 타입 및 값 검증
            if not isinstance(sub_item['설명'], str):
                return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key} > 설명'은 문자열이 아님"
            if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
                return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key} > 키워드'는 문자열 리스트가 아님"
            if not isinstance(sub_item['중요도'], int) or not (0 <= sub_item['중요도'] <= 100):
                return f"SupplyCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key} > 중요도'는 0-100 사이의 정수가 아님"

    return OutputDic

## Process5: SupplyCollectionDataUltimateChainFilter의 Filter(Error 예외처리)
def SupplyCollectionDataUltimateChainFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplyCollectionDataUltimateChain, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_keys = ['최초핵심솔루션', '궁극적핵심솔루션']
    linked_data_keys = [f'연계데이터{i}' for i in range(1, 6)]
    missing_keys = [key for key in required_top_keys + linked_data_keys if key not in OutputDic]
    if missing_keys:
        return f"SupplyCollectionDataUltimateChain, JSONKeyError: 누락된 키: {', '.join(missing_keys)}"

    # Error3: 최상위 키 데이터 타입 검증
    if not isinstance(OutputDic['최초핵심솔루션'], str):
        return "SupplyCollectionDataUltimateChain, JSON에서 오류 발생: '최초핵심솔루션'은 문자열이 아님"
    if not isinstance(OutputDic['궁극적핵심솔루션'], str):
        return "SupplyCollectionDataUltimateChain, JSON에서 오류 발생: '궁극적핵심솔루션'은 문자열이 아님"

    # Error4: 연계 데이터 검증
    for key in linked_data_keys:
        data = OutputDic[key]

        # 연계데이터 내부 필수 키 확인
        required_inner_keys = ['핵심솔루션', '분야', '제안', '정보의질']
        missing_inner_keys = [inner_key for inner_key in required_inner_keys if inner_key not in data]
        if missing_inner_keys:
            return f"SupplyCollectionDataUltimateChain, JSONKeyError: '{key}'에 누락된 키: {', '.join(missing_inner_keys)}"

        # 데이터 타입 검증
        if not isinstance(data['핵심솔루션'], str):
            return f"SupplyCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 핵심솔루션'은 문자열이 아님"
        if not isinstance(data['분야'], list) or not all(isinstance(item, str) for item in data['분야']):
            return f"SupplyCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 분야'는 문자열 리스트가 아님"
        if not isinstance(data['정보의질'], int) or not (0 <= data['정보의질'] <= 100):
            return f"SupplyCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 정보의질'은 0-100 사이의 정수가 아님"

        # '제안' 키 구조 검증
        if not isinstance(data['제안'], dict):
            return f"SupplyCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 제안'은 딕셔너리 형태가 아님"

        # '제안' 내부 필수 키 확인
        required_sub_keys = ['제안내용', '제안할목표', '제안할해결책']
        missing_sub_keys = [sub_key for sub_key in required_sub_keys if sub_key not in data['제안']]
        if missing_sub_keys:
            return f"SupplyCollectionDataUltimateChain, JSONKeyError: '{key} > 제안'에 누락된 키: {', '.join(missing_sub_keys)}"

        # '제안' 내부 구조 검증
        for sub_key in required_sub_keys:
            sub_item = data['제안'][sub_key]
            if not isinstance(sub_item, dict):
                return f"SupplyCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key}'는 딕셔너리 형태가 아님"

            # 내부 필수 키 확인
            required_detail_keys = ['설명', '키워드', '중요도']
            missing_detail_keys = [detail_key for detail_key in required_detail_keys if detail_key not in sub_item]
            if missing_detail_keys:
                return f"SupplyCollectionDataUltimateChain, JSONKeyError: '{key} > 제안 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

            # 데이터 타입 및 값 검증
            if not isinstance(sub_item['설명'], str):
                return f"SupplyCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key} > 설명'은 문자열이 아님"
            if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
                return f"SupplyCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key} > 키워드'는 문자열 리스트가 아님"
            if not isinstance(sub_item['중요도'], int) or not (0 <= sub_item['중요도'] <= 100):
                return f"SupplyCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 제안 > {sub_key} > 중요도'는 0-100 사이의 정수가 아님"

    return OutputDic

#######################
##### Process 응답 #####
#######################
## Process LLMResponse 함수
def ProcessResponse(projectName, email, Process, Input, ProcessCount, InputCount, FilterFunc, CheckCount, LLM, mode, MessagesReview):

    ErrorCount = 0
    while True:
        if LLM == "OpenAI":
            Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, messagesReview = MessagesReview)
        elif LLM == "Anthropic":
            Response, Usage, Model = ANTHROPIC_LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, messagesReview = MessagesReview)
        Filter = FilterFunc(Response, CheckCount)
        
        if isinstance(Filter, str):
            print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | {Filter}")
            ErrorCount += 1
            print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | "
                f"오류횟수 {ErrorCount}회, 2분 후 프롬프트 재시도")
            
            if ErrorCount >= 5:
                sys.exit(f"Project: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | "
                        f"오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
            time.sleep(120)
            continue
        
        print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | JSONDecode 완료")
        return Filter

##################################
##### ProcessResponse 업데이트 #####
##################################
## ProcessResponseTemp 저장
def ProcessResponseTempSave(MainKey, InputDic, OutputDicList, DataTempPath):
    # DataTempPath 폴더가 없으면 생성
    if not os.path.exists(DataTempPath):
        os.makedirs(DataTempPath)
        
    #### Search ####
    # Search-Term
    Term = InputDic['Input']
    # Search-Intention
    Intention = InputDic['Intention']
    ## SearchDic ##
    SearchDic = {'Term': Term, 'Intention': Intention}
    #### Search ####
    
    #### Detail ####
    # Detail-Summary
    ScarchSummary = OutputDicList[0]['핵심솔루션']
    # Detail-Satisfy
    DetailSatisfy = OutputDicList[0]['제안할내용']
    # Detail-Support
    DetailSupport = OutputDicList[0]['제안할목표']
    # Detail-Solution
    DetailSolution = OutputDicList[0]['제안할해결책']
    # Detail-Weight
    DetailWeight = OutputDicList[0]['검색어완성도']
    # Detail-Feedback
    DetailFeedback = OutputDicList[0]['검색어피드백']
    ## DetailDic ##
    DetailDic = {'Summary': ScarchSummary, 'Satisfy': DetailSatisfy, 'Support': DetailSupport, 'Solution': DetailSolution, 'Weight': DetailWeight, 'Feedback': DetailFeedback}
    #### Detail ####
    
    #### Context ####
    # Context-Summary
    ContextSummary = OutputDicList[1]['핵심솔루션']
    # Context-KeyWord
    ContextKeyWord = OutputDicList[1]['분야']
    # Context-Supply
    ContextSupplySatisfy = {"Sentence": OutputDicList[1]['제안']['제안내용']['설명'], "KeyWord": OutputDicList[1]['제안']['제안내용']['키워드'], "Weight": OutputDicList[1]['제안']['제안내용']['중요도']}
    ContextSupplySupport = {"Sentence": OutputDicList[1]['제안']['제안할목표']['설명'], "KeyWord": OutputDicList[1]['제안']['제안할목표']['키워드'], "Weight": OutputDicList[1]['제안']['제안할목표']['중요도']}
    ContextSupplySolution = {"Sentence": OutputDicList[1]['제안']['제안할해결책']['설명'], "KeyWord": OutputDicList[1]['제안']['제안할해결책']['키워드'], "Weight": OutputDicList[1]['제안']['제안할해결책']['중요도']}
    ContextSupply = {'Satisfy': ContextSupplySatisfy, 'Support': ContextSupplySupport, 'Solution': ContextSupplySolution}
    # Context-Weight
    ContextWeight = OutputDicList[1]['정보의질']
    ## ContextDic ##
    ContextDic = {'Summary': ContextSummary, 'KeyWord': ContextKeyWord, 'Supply': ContextSupply, 'Weight': ContextWeight}
    #### Context ####
    
    #### ContextExtension ####
    ContextExtensionDicList = []
    for i in range(5):
        # ContextExtension-Summary
        ContextExtensionSummary = OutputDicList[2][f'전문데이터{i+1}']['핵심솔루션']
        # ContextExtension-KeyWord
        ContextExtensionKeyWord = OutputDicList[2][f'전문데이터{i+1}']['분야']
        # ContextExtension-Supply
        ContextExtensionSupplySatisfy = {"Sentence": OutputDicList[2][f'전문데이터{i+1}']['제안']['제안내용']['설명'], "KeyWord": OutputDicList[2][f'전문데이터{i+1}']['제안']['제안내용']['키워드'], "Weight": OutputDicList[2][f'전문데이터{i+1}']['제안']['제안내용']['중요도']}
        ContextExtensionSupplySupport = {"Sentence": OutputDicList[2][f'전문데이터{i+1}']['제안']['제안할목표']['설명'], "KeyWord": OutputDicList[2][f'전문데이터{i+1}']['제안']['제안할목표']['키워드'], "Weight": OutputDicList[2][f'전문데이터{i+1}']['제안']['제안할목표']['중요도']}
        ContextExtensionSupplySolution = {"Sentence": OutputDicList[2][f'전문데이터{i+1}']['제안']['제안할해결책']['설명'], "KeyWord": OutputDicList[2][f'전문데이터{i+1}']['제안']['제안할해결책']['키워드'], "Weight": OutputDicList[2][f'전문데이터{i+1}']['제안']['제안할해결책']['중요도']}
        ContextExtensionSupply = {'Satisfy': ContextExtensionSupplySatisfy, 'Support': ContextExtensionSupplySupport, 'Solution': ContextExtensionSupplySolution}
        # ContextExtension-Weight
        ContextExtensionWeight = OutputDicList[2][f'전문데이터{i+1}']['정보의질']
        ## ContextExtensionDic ##
        ContextExtensionDic = {'Summary': ContextExtensionSummary, 'KeyWord': ContextExtensionKeyWord, 'Supply': ContextExtensionSupply, 'Weight': ContextExtensionWeight}
        ContextExtensionDicList.append(ContextExtensionDic)
    #### ContextExtension ####
    
    #### ContextUltimate ####
    ContextUltimateDicList = []
    for i in range(5):
        # ContextUltimate-Summary
        ContextUltimateSummary = OutputDicList[3][f'연계데이터{i+1}']['핵심솔루션']
        # ContextUltimate-KeyWord
        ContextUltimateKeyWord = OutputDicList[3][f'연계데이터{i+1}']['분야']
        # ContextUltimate-Supply
        ContextUltimateSupplySatisfy = {"Sentence": OutputDicList[3][f'연계데이터{i+1}']['제안']['제안내용']['설명'], "KeyWord": OutputDicList[3][f'연계데이터{i+1}']['제안']['제안내용']['키워드'], "Weight": OutputDicList[3][f'연계데이터{i+1}']['제안']['제안내용']['중요도']}
        ContextUltimateSupplySupport = {"Sentence": OutputDicList[3][f'연계데이터{i+1}']['제안']['제안할목표']['설명'], "KeyWord": OutputDicList[3][f'연계데이터{i+1}']['제안']['제안할목표']['키워드'], "Weight": OutputDicList[3][f'연계데이터{i+1}']['제안']['제안할목표']['중요도']}
        ContextUltimateSupplySolution = {"Sentence": OutputDicList[3][f'연계데이터{i+1}']['제안']['제안할해결책']['설명'], "KeyWord": OutputDicList[3][f'연계데이터{i+1}']['제안']['제안할해결책']['키워드'], "Weight": OutputDicList[3][f'연계데이터{i+1}']['제안']['제안할해결책']['중요도']}
        ContextUltimateSupply = {'Satisfy': ContextUltimateSupplySatisfy, 'Support': ContextUltimateSupplySupport, 'Solution': ContextUltimateSupplySolution}
        # ContextUltimate-Weight
        ContextUltimateWeight = OutputDicList[3][f'연계데이터{i+1}']['정보의질']
        ## ContextUltimateDic ##
        ContextUltimateDic = {'Summary': ContextUltimateSummary, 'KeyWord': ContextUltimateKeyWord, 'Supply': ContextUltimateSupply, 'Weight': ContextUltimateWeight}
        ContextUltimateDicList.append(ContextUltimateDic)
    #### ContextUltimate ####
    
    DataTemp = {MainKey: {'Search': SearchDic, 'Detail': DetailDic, 'Context': ContextDic, 'ContextExtension': ContextExtensionDicList, 'ContextUltimate': ContextUltimateDicList}}
    
    # DataTempJson 저장
    DataTempJsonPath = os.path.join(DataTempPath, f"SupplyCollectionData_({datetime.now().strftime('%Y%m%d%H%M%S')})_{re.sub(r'[^가-힣a-zA-Z0-9]', '', Term)[:15]}.json")
    with open(DataTempJsonPath, 'w', encoding = 'utf-8') as DataTempJson:
        json.dump(DataTemp, DataTempJson, ensure_ascii = False, indent = 4)
        
    return DataTemp

################################
##### Process 진행 및 업데이트 #####
################################
## SupplyCollectionDataDetail 프롬프트 요청 및 결과물 Json화
def SupplyCollectionDataDetailProcessUpdate(projectName, email, InputDic, mode = "Master", MainKey = 'SupplySearchAnalysis', MessagesReview = "on"):
    print(f"< User: {email} | Project: {projectName} | SupplyCollectionDataDetailUpdate 시작 >")
    ## TotalPublisherData 경로 설정
    TotalSupplyCollectionDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1512_SupplyCollectionData/s15121_TotalSupplyCollectionData"
    TotalSupplyCollectionDataJsonPath = os.path.join(TotalSupplyCollectionDataPath, 'TotalSupplyCollectionData.json')
    TotalSupplyCollectionDataTempPath = os.path.join(TotalSupplyCollectionDataPath, 'TotalSupplyCollectionDataTemp')
    
    ## SupplyCollectionDataDetailProcess
    InputCount = 1
    processCount = 1
    Input1 = InputDic['Input']
    Intention = InputDic['Intention']
    CheckCount = 0
    OutputDicList = []

    ## Process1: SupplyCollectionDataDetail Response 생성
    SupplyCollectionDataDetailResponse = ProcessResponse(projectName, email, "SupplyCollectionDataDetail", Input1, processCount, InputCount, SupplyCollectionDataDetailFilter, CheckCount, "OpenAI", mode, MessagesReview)
    OutputDicList.append(SupplyCollectionDataDetailResponse)
    
    ## Process2: SupplyCollectionDataContext Response 생성
    Input2 = SupplyCollectionDataDetailResponse.copy()
    DeleteKeys = ['검색어완성도', '검색어피드백']
    for key in DeleteKeys:
        del Input2[key]
    
    SupplyCollectionDataContextResponse = ProcessResponse(projectName, email, "SupplyCollectionDataContext", Input2, processCount, InputCount, SupplyCollectionDataContextFilter, CheckCount, "OpenAI", mode, MessagesReview)
    OutputDicList.append(SupplyCollectionDataContextResponse)
    
    ## Process3: SupplyCollectionDataExtensionChain Response 생성
    Input3 = SupplyCollectionDataContextResponse
    
    SupplyCollectionDataExtensionChainResponse = ProcessResponse(projectName, email, "SupplyCollectionDataExtensionChain", Input3, processCount, InputCount, SupplyCollectionDataExtensionChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
    OutputDicList.append(SupplyCollectionDataExtensionChainResponse)
    
    if Intention in ["SupplyUltimate", "SimilarityUltimate"]:
        ## Process4: SupplyCollectionDataUltimateChain Response 생성
        Input4 = SupplyCollectionDataContextResponse
        
        SupplyCollectionDataUltimateChainResponse = ProcessResponse(projectName, email, "SupplyCollectionDataUltimateChain", Input4, processCount, InputCount, SupplyCollectionDataUltimateChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicList.append(SupplyCollectionDataUltimateChainResponse)

    ## ProcessResponse 임시저장
    DataTemp = ProcessResponseTempSave(MainKey, InputDic, OutputDicList, TotalSupplyCollectionDataTempPath)

    print(f"[ User: {email} | Project: {projectName} | SupplyCollectionDataDetailUpdate 완료 ]\n")
    
    return DataTemp

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241204_개정교육과정초등교과별이해연수'
    #########################################################################
    
    SupplyCollectionDataDetailProcessUpdate(ProjectName, email)