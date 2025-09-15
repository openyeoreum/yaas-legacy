import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from datetime import datetime
from agent.a3_Operation.a32_Solution.a321_LoadLLM import OpenAI_LLMresponse, ANTHROPIC_LLMresponse

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
        if isinstance(OutputDic[key], list):
            OutputDic[key] = ' '.join(OutputDic[key])
        if not isinstance(OutputDic[key], str):
            return f"SupplyCollectionDataDetail, JSON에서 오류 발생: '{key}'가 문자열이 아님"

    # 검색어완성도는 0-100 사이의 정수여야 함
    if (not isinstance(OutputDic['검색어완성도'], (int, str))) or (isinstance(OutputDic['검색어완성도'], str) and not OutputDic['검색어완성도'].isdigit()) or (isinstance(OutputDic['검색어완성도'], (int, str)) and (int(OutputDic['검색어완성도']) < 0 or int(OutputDic['검색어완성도']) > 100)):
        return "SupplyCollectionDataDetail, JSON에서 오류 발생: '검색어완성도'가 0-100 사이의 정수가 아님"
    else:
        OutputDic['검색어완성도'] = int(OutputDic['검색어완성도'])

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
    if (not isinstance(OutputDic['정보의질'], (int, str))) or (isinstance(OutputDic['정보의질'], str) and not OutputDic['정보의질'].isdigit()) or (isinstance(OutputDic['정보의질'], (int, str)) and (int(OutputDic['정보의질']) < 0 or int(OutputDic['정보의질']) > 100)):
        return "SupplyCollectionDataContext, JSON에서 오류 발생: '정보의질'은 0-100 사이의 정수가 아님"
    else:
        OutputDic['정보의질'] = int(OutputDic['정보의질'])

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
        if (not isinstance(sub_item['중요도'], (int, str))) or (isinstance(sub_item['중요도'], str) and not sub_item['중요도'].isdigit()) or (isinstance(sub_item['중요도'], (int, str)) and (int(sub_item['중요도']) < 0 or int(sub_item['중요도']) > 100)):
            return f"SupplyCollectionDataContext, JSON에서 오류 발생: '제안 > {sub_key} > 중요도'가 0-100 사이의 정수가 아님"
        else:
            sub_item['중요도'] = int(sub_item['중요도'])

    # 모든 조건을 만족하면 파싱된 JSON 반환
    return OutputDic

## Process3-1: SupplyCollectionDataExpertiseFilter의 Filter(Error 예외처리)
def SupplyCollectionDataExpertiseFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplyCollectionDataExpertiseChain, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '전문분야들' not in OutputDic:
        return "SupplyCollectionDataExpertiseChain, JSONKeyError: '전문분야들' 키가 누락"

    # Error3: '전문분야들' 데이터 타입 확인
    ExpertiseList = OutputDic['전문분야들']
    if not isinstance(ExpertiseList, list):
        return "SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문분야들'은 리스트 형태가 아님"
    if len(ExpertiseList) != 5:
        return "SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문분야들'은 5개의 항목을 가져야 함"

    # Error4: 리스트 내부 검증
    for idx, item in enumerate(ExpertiseList):
        # 각 항목은 딕셔너리 형태여야 함
        if not isinstance(item, dict):
            return f"SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문분야들[{idx}]'은 딕셔너리 형태가 아님"

        # 필수 키 확인
        required_keys = ['전문분야', '이유']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"SupplyCollectionDataExpertiseChain, JSONKeyError: '전문분야들[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 검증
        if not isinstance(item['전문분야'], str):
            return f"SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문분야들[{idx}] > 전문분야'는 문자열이 아님"
        if not isinstance(item['이유'], str):
            return f"SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문분야들[{idx}] > 이유'는 문자열이 아님"

    return OutputDic['전문분야들']

## Process3-2: SupplyCollectionDataExpertiseChainFilter의 Filter(Error 예외처리)
def SupplyCollectionDataExpertiseChainFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplyCollectionDataExpertiseChain, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '전문데이터' not in OutputDic:
        return "SupplyCollectionDataExpertiseChain, JSONKeyError: '전문데이터' 키가 누락되었음"

    # Error3: 전문데이터 내부 필수 키 확인
    expertise_data = OutputDic['전문데이터']
    required_keys = ['핵심솔루션', '분야', '제안', '정보의질']
    missing_keys = [key for key in required_keys if key not in expertise_data]
    if missing_keys:
        return f"SupplyCollectionDataExpertiseChain, JSONKeyError: '전문데이터'에 누락된 키: {', '.join(missing_keys)}"

    # Error4: 데이터 타입 검증
    if not isinstance(expertise_data['핵심솔루션'], str):
        return "SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 핵심솔루션'은 문자열이어야 합니다"
    if not isinstance(expertise_data['분야'], list) or not all(isinstance(item, str) for item in expertise_data['분야']):
        return "SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 분야'는 문자열 리스트가 아님"
    if (not isinstance(expertise_data['정보의질'], (int, str))) or (isinstance(expertise_data['정보의질'], str) and not expertise_data['정보의질'].isdigit()) or (isinstance(expertise_data['정보의질'], (int, str)) and (int(expertise_data['정보의질']) < 0 or int(expertise_data['정보의질']) > 100)):
        return "SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 정보의질'은 0-100 사이의 정수가 아님"
    else:
        expertise_data['정보의질'] = int(expertise_data['정보의질'])

    # Error5: '제안' 내부 구조 검증
    if not isinstance(expertise_data['제안'], dict):
        return "SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 제안'는 딕셔너리 형태가 아님"

    required_sub_keys = ['제안내용', '제안할목표', '제안할해결책']
    for sub_key in required_sub_keys:
        if sub_key not in expertise_data['제안']:
            return f"SupplyCollectionDataExpertiseChain, JSONKeyError: '전문데이터 > 제안'에 누락된 키: {sub_key}"
        sub_item = expertise_data['제안'][sub_key]

        if not isinstance(sub_item, dict):
            return f"SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 제안 > {sub_key}'는 딕셔너리 형태가 아님"

        # 내부 필수 키 확인
        required_detail_keys = ['설명', '키워드', '중요도']
        missing_detail_keys = [key for key in required_detail_keys if key not in sub_item]
        if missing_detail_keys:
            return f"SupplyCollectionDataExpertiseChain, JSONKeyError: '전문데이터 > 제안 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

        # 데이터 타입 검증
        if not isinstance(sub_item['설명'], str):
            return f"SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 제안 > {sub_key} > 설명'은 문자열이 아님"
        if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
            return f"SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 제안 > {sub_key} > 키워드'는 문자열 리스트가 아님"
        if (not isinstance(sub_item['중요도'], (int, str))) or (isinstance(sub_item['중요도'], str) and not sub_item['중요도'].isdigit()) or (isinstance(sub_item['중요도'], (int, str)) and (int(sub_item['중요도']) < 0 or int(sub_item['중요도']) > 100)):
            return f"SupplyCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 제안 > {sub_key} > 중요도'가 0-100 사이의 정수가 아님"
        else:
            sub_item['중요도'] = int(sub_item['중요도'])

    return OutputDic['전문데이터']

## Process4-1: SupplyCollectionDataUltimateFilter의 Filter(Error 예외처리)
def SupplyCollectionDataUltimateFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplyCollectionDataUltimateFilter, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_keys = ['최초핵심솔루션', '궁극적핵심솔루션', '5단계핵심솔루션']
    missing_top_keys = [key for key in required_top_keys if key not in OutputDic]
    if missing_top_keys:
        return f"SupplyCollectionDataUltimateFilter, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"

    # Error3: 최상위 키 데이터 타입 확인
    if not isinstance(OutputDic['최초핵심솔루션'], str):
        return "SupplyCollectionDataUltimateFilter, JSON에서 오류 발생: '최초핵심솔루션'은 문자열이어야 합니다"
    if not isinstance(OutputDic['궁극적핵심솔루션'], str):
        return "SupplyCollectionDataUltimateFilter, JSON에서 오류 발생: '궁극적핵심솔루션'은 문자열이어야 합니다"

    # Error4: 5단계핵심솔루션 검증
    if not isinstance(OutputDic['5단계핵심솔루션'], list):
        return "SupplyCollectionDataUltimateFilter, JSON에서 오류 발생: '5단계핵심솔루션'은 리스트 형태여야 합니다"
    if len(OutputDic['5단계핵심솔루션']) != 5:
        return "SupplyCollectionDataUltimateFilter, JSON에서 오류 발생: '5단계핵심솔루션'는 5개의 항목을 가져야 합니다"

    for idx, item in enumerate(OutputDic['5단계핵심솔루션']):
        # 리스트의 각 항목은 딕셔너리 형태여야 함
        if not isinstance(item, dict):
            return f"SupplyCollectionDataUltimateFilter, JSON에서 오류 발생: '5단계핵심솔루션[{idx}]'은 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['새로운문제와목적', '핵심솔루션']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"SupplyCollectionDataUltimateFilter, JSONKeyError: '5단계핵심솔루션[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 검증
        if not isinstance(item['새로운문제와목적'], str):
            return f"SupplyCollectionDataUltimateFilter, JSON에서 오류 발생: '5단계핵심솔루션[{idx}] > 새로운문제와목적'은 문자열이어야 합니다"
        if not isinstance(item['핵심솔루션'], str):
            return f"SupplyCollectionDataUltimateFilter, JSON에서 오류 발생: '5단계핵심솔루션[{idx}] > 핵심솔루션'은 문자열이어야 합니다"

    return OutputDic['5단계핵심솔루션']

## Process4-2: SupplyCollectionDataUltimateChainFilter의 Filter(Error 예외처리)
def SupplyCollectionDataUltimateChainFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplyCollectionDataUltimateChainFilter의, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_keys = ['핵심솔루션', '분야', '제안', '정보의질']
    missing_top_keys = [key for key in required_top_keys if key not in OutputDic]
    if missing_top_keys:
        return f"SupplyCollectionDataUltimateChainFilter의, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"

    # Error3: 최상위 키 데이터 타입 검증
    if not isinstance(OutputDic['핵심솔루션'], str):
        return "SupplyCollectionDataUltimateChainFilter의, JSON에서 오류 발생: '핵심솔루션'은 문자열이어야 합니다"
    if not isinstance(OutputDic['분야'], list) or not all(isinstance(item, str) for item in OutputDic['분야']):
        return "SupplyCollectionDataUltimateChainFilter의, JSON에서 오류 발생: '분야'는 문자열 리스트여야 합니다"
    if (not isinstance(OutputDic['정보의질'], (int, str))) or (isinstance(OutputDic['정보의질'], str) and not OutputDic['정보의질'].isdigit()) or (isinstance(OutputDic['정보의질'], (int, str)) and (int(OutputDic['정보의질']) < 0 or int(OutputDic['정보의질']) > 100)):
        return "SupplyCollectionDataUltimateChainFilter의, JSON에서 오류 발생: '정보의질'은 0-100 사이의 정수여야 합니다"
    else:
        OutputDic['정보의질'] = int(OutputDic['정보의질'])

    # Error4: '제안' 키 구조 검증
    if not isinstance(OutputDic['제안'], dict):
        return "SupplyCollectionDataUltimateChainFilter의, JSON에서 오류 발생: '제안'은 딕셔너리 형태여야 합니다"

    # '제안' 내부 필수 키 확인
    required_sub_keys = ['제안내용', '제안할목표', '제안할해결책']
    missing_sub_keys = [key for key in required_sub_keys if key not in OutputDic['제안']]
    if missing_sub_keys:
        return f"SupplyCollectionDataUltimateChainFilter의, JSONKeyError: '제안'에 누락된 키: {', '.join(missing_sub_keys)}"

    # '제안' 내부 구조 검증
    for sub_key in required_sub_keys:
        sub_item = OutputDic['제안'][sub_key]

        if not isinstance(sub_item, dict):
            return f"SupplyCollectionDataUltimateChainFilter의, JSON에서 오류 발생: '제안 > {sub_key}'는 딕셔너리 형태여야 합니다"

        # 내부 필수 키 확인
        required_detail_keys = ['설명', '키워드', '중요도']
        missing_detail_keys = [key for key in required_detail_keys if key not in sub_item]
        if missing_detail_keys:
            return f"SupplyCollectionDataUltimateChainFilter의, JSONKeyError: '제안 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

        # 데이터 타입 검증
        if not isinstance(sub_item['설명'], str):
            return f"SupplyCollectionDataUltimateChainFilter의, JSON에서 오류 발생: '제안 > {sub_key} > 설명'은 문자열이어야 합니다"
        if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
            return f"SupplyCollectionDataUltimateChainFilter의, JSON에서 오류 발생: '제안 > {sub_key} > 키워드'는 문자열 리스트여야 합니다"
        if (not isinstance(sub_item['중요도'], (int, str))) or (isinstance(sub_item['중요도'], str) and not sub_item['중요도'].isdigit()) or (isinstance(sub_item['중요도'], (int, str)) and (int(sub_item['중요도']) < 0 or int(sub_item['중요도']) > 100)):
            return f"SupplyCollectionDataUltimateChainFilter의, JSON에서 오류 발생: '제안 > {sub_key} > 중요도'는 0-100 사이의 정수여야 합니다"
        else:
            sub_item['중요도'] = int(sub_item['중요도'])

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
## ProcessResponseTemp 저장
def ProcessResponseTempSave(MainKey, InputDic, OutputDicSet, DataTempPath):
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

    ProcessKeyList.append("SupplySearch")
    ProcessDicList.append(SearchDic)
    #### Search ####
    
    #### Detail ####
    Process = "SupplyCollectionDataDetail"
    if Process in OutputDicSet:
        # Detail-Summary
        ScarchSummary = OutputDicSet[Process]['핵심솔루션']
        # Detail-Satisfy
        DetailSatisfy = OutputDicSet[Process]['제안할내용']
        # Detail-Support
        DetailSupport = OutputDicSet[Process]['제안할목표']
        # Detail-Solution
        DetailSolution = OutputDicSet[Process]['제안할해결책']
        # Detail-Weight
        DetailWeight = OutputDicSet[Process]['검색어완성도']
        # Detail-Feedback
        DetailFeedback = OutputDicSet[Process]['검색어피드백']
        ## DetailDic ##
        DetailDic = {'Summary': ScarchSummary, 'Satisfy': DetailSatisfy, 'Support': DetailSupport, 'Solution': DetailSolution, 'Weight': DetailWeight, 'Feedback': DetailFeedback}
        
        ProcessKeyList.append("SupplyDetail")
        ProcessDicList.append(DetailDic)
    #### Detail ####
    
    #### Context ####
    Process = "SupplyCollectionDataContext"
    if Process in OutputDicSet:
        # Context-Summary
        ContextSummary = OutputDicSet[Process]['핵심솔루션']
        # Context-KeyWord
        ContextKeyWord = OutputDicSet[Process]['분야']
        # Context-Supply
        ContextSupplySatisfy = {"Sentence": OutputDicSet[Process]['제안']['제안내용']['설명'], "KeyWord": OutputDicSet[Process]['제안']['제안내용']['키워드'], "Weight": OutputDicSet[Process]['제안']['제안내용']['중요도']}
        ContextSupplySupport = {"Sentence": OutputDicSet[Process]['제안']['제안할목표']['설명'], "KeyWord": OutputDicSet[Process]['제안']['제안할목표']['키워드'], "Weight": OutputDicSet[Process]['제안']['제안할목표']['중요도']}
        ContextSupplySolution = {"Sentence": OutputDicSet[Process]['제안']['제안할해결책']['설명'], "KeyWord": OutputDicSet[Process]['제안']['제안할해결책']['키워드'], "Weight": OutputDicSet[Process]['제안']['제안할해결책']['중요도']}
        ContextSupply = {'Satisfy': ContextSupplySatisfy, 'Support': ContextSupplySupport, 'Solution': ContextSupplySolution}
        # Context-Weight
        ContextWeight = OutputDicSet[Process]['정보의질']
        ## ContextDic ##
        ContextDic = {'Summary': ContextSummary, 'KeyWord': ContextKeyWord, 'Supply': ContextSupply, 'Weight': ContextWeight}
        
        ProcessKeyList.append("SupplyContext")
        ProcessDicList.append(ContextDic)
    #### Context ####
    
    #### ContextExpertise ####
    Process = "SupplyCollectionDataExpertiseChain"
    if Process in OutputDicSet:
        ContextExpertiseDicList = []
        for i in range(5):
            # ContextExpertise-Summary
            ContextExpertiseSummary = OutputDicSet[Process][f'전문데이터{i+1}']['핵심솔루션']
            # ContextExpertise-KeyWord
            ContextExpertiseKeyWord = OutputDicSet[Process][f'전문데이터{i+1}']['분야']
            # ContextExpertise-Supply
            ContextExpertiseSupplySatisfy = {"Sentence": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안내용']['설명'], "KeyWord": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안내용']['키워드'], "Weight": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안내용']['중요도']}
            ContextExpertiseSupplySupport = {"Sentence": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할목표']['설명'], "KeyWord": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할목표']['키워드'], "Weight": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할목표']['중요도']}
            ContextExpertiseSupplySolution = {"Sentence": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할해결책']['설명'], "KeyWord": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할해결책']['키워드'], "Weight": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할해결책']['중요도']}
            ContextExpertiseSupply = {'Satisfy': ContextExpertiseSupplySatisfy, 'Support': ContextExpertiseSupplySupport, 'Solution': ContextExpertiseSupplySolution}
            # ContextExpertise-Weight
            ContextExpertiseWeight = OutputDicSet[Process][f'전문데이터{i+1}']['정보의질']
            ## ContextExpertiseDic ##
            ContextExpertiseDic = {'Summary': ContextExpertiseSummary, 'KeyWord': ContextExpertiseKeyWord, 'Supply': ContextExpertiseSupply, 'Weight': ContextExpertiseWeight}
            ContextExpertiseDicList.append(ContextExpertiseDic)
        
        ProcessKeyList.append("SupplyContextExpertise")
        ProcessDicList.append(ContextExpertiseDicList)
    #### ContextExpertise ####
    
    #### ContextUltimate ####
    Process = "SupplyCollectionDataUltimateChain"
    if Process in OutputDicSet:
        ContextUltimateDicList = []
        for i in range(5):
            # ContextUltimate-Summary
            ContextUltimateSummary = OutputDicSet[Process][f'연계데이터{i+1}']['핵심솔루션']
            # ContextUltimate-KeyWord
            ContextUltimateKeyWord = OutputDicSet[Process][f'연계데이터{i+1}']['분야']
            # ContextUltimate-Supply
            ContextUltimateSupplySatisfy = {"Sentence": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안내용']['설명'], "KeyWord": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안내용']['키워드'], "Weight": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안내용']['중요도']}
            ContextUltimateSupplySupport = {"Sentence": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할목표']['설명'], "KeyWord": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할목표']['키워드'], "Weight": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할목표']['중요도']}
            ContextUltimateSupplySolution = {"Sentence": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할해결책']['설명'], "KeyWord": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할해결책']['키워드'], "Weight": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할해결책']['중요도']}
            ContextUltimateSupply = {'Satisfy': ContextUltimateSupplySatisfy, 'Support': ContextUltimateSupplySupport, 'Solution': ContextUltimateSupplySolution}
            # ContextUltimate-Weight
            ContextUltimateWeight = OutputDicSet[Process][f'연계데이터{i+1}']['정보의질']
            ## ContextUltimateDic ##
            ContextUltimateDic = {'Summary': ContextUltimateSummary, 'KeyWord': ContextUltimateKeyWord, 'Supply': ContextUltimateSupply, 'Weight': ContextUltimateWeight}
            ContextUltimateDicList.append(ContextUltimateDic)
        
        ProcessKeyList.append("SupplyContextUltimate")
        ProcessDicList.append(ContextUltimateDicList)
    #### ContextUltimate ####
    
    DataTemp = {MainKey: {}}
    for i in range(len(ProcessKeyList)):
        DataTemp[MainKey][ProcessKeyList[i]] = ProcessDicList[i]
    
    # DataTempJson 저장
    DateTime = datetime.now().strftime('%Y%m%d%H%M%S')
    DataTempJsonPath = os.path.join(DataTempPath, f"SupplyCollectionData_({DateTime})_{TermText}.json")
    with open(DataTempJsonPath, 'w', encoding = 'utf-8') as DataTempJson:
        json.dump(DataTemp, DataTempJson, ensure_ascii = False, indent = 4)
        
    # CollectionDataChain 추출
    CollectionDataChain = DataTemp[MainKey]
        
    return CollectionDataChain, DateTime

################################
##### Process 진행 및 업데이트 #####
################################
## SupplyCollectionData 프롬프트 요청 및 결과물 Json화
def SupplyCollectionDataProcessUpdate(projectName, email, InputDic, mode = "Master", MainKey = 'SupplySearchAnalysis', MessagesReview = "on"):
    print(f"< User: {email} | Chain: {projectName} | SupplyCollectionDataUpdate 시작 >")
    ## TotalPublisherData 경로 설정
    TotalSupplyCollectionDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1512_SupplyCollectionData/s15121_TotalSupplyCollectionData"
    TotalSupplyCollectionDataJsonPath = os.path.join(TotalSupplyCollectionDataPath, 'TotalSupplyCollectionData.json')
    TotalSupplyCollectionDataTempPath = os.path.join(TotalSupplyCollectionDataPath, 'TotalSupplyCollectionDataTemp')
    
    ## SupplyCollectionDataDetailProcess
    Type = InputDic['Type']
    Extension = InputDic['Extension']
    # InputCount 계산
    InputCount = 1
    if Type == "Search":
        InputCount += 1
    if Extension != []:
        InputCount += (len(InputDic['Extension'])) * 6
    processCount = 1
    CheckCount = 0
    OutputDicSet = {}

    ## Process1: SupplyCollectionDataDetail Response 생성
    if Type == "Search":
        Process = "SupplyCollectionDataDetail"
        Input = InputDic['Input']
        
        SupplyCollectionDataDetailResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, SupplyCollectionDataDetailFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicSet[Process] = SupplyCollectionDataDetailResponse
        processCount += 1
    
    ## Process2: SupplyCollectionDataContext Response 생성
    if Type == "Search":
        Process = "SupplyCollectionDataContext"
        Input = SupplyCollectionDataDetailResponse.copy()
        DeleteKeys = ['검색어완성도', '검색어피드백']
        for key in DeleteKeys:
            del Input[key]
    
        SupplyCollectionDataContextResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, SupplyCollectionDataContextFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicSet[Process] = SupplyCollectionDataContextResponse
    elif Type == "Match":
        Process = "SupplyCollectionDataContext"
        OutputDicSet[Process] = InputDic['CollectionData']
    processCount += 1
    
    ## Process3-1: SupplyCollectionDataExpertise Response 생성
    if "Expertise" in Extension:
        Process = "SupplyCollectionDataExpertise"
        if Type == "Search":
            Input = SupplyCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        
        SupplyCollectionDataExpertiseResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, SupplyCollectionDataExpertiseFilter, CheckCount, "OpenAI", mode, MessagesReview)
        processCount += 1
        
        ## Process3-2: SupplyCollectionDataExpertiseChain Response 연속 생성 및 Set로 합치기
        Process = "SupplyCollectionDataExpertiseChain"
        SupplyCollectionDataExpertiseChainResponseSet = {}
        for i, Response in enumerate(SupplyCollectionDataExpertiseResponse):
            InputText = f'{Response}\n\n<데이터>\n{Input}\n'
            SupplyCollectionDataExpertiseChainResponse = ProcessResponse(projectName, email, Process, InputText, processCount, InputCount, SupplyCollectionDataExpertiseChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
            SupplyCollectionDataExpertiseChainResponseSet[f'전문데이터{i+1}'] = {}
            SupplyCollectionDataExpertiseChainResponse['핵심솔루션'] = f"{Response['전문분야']}  {SupplyCollectionDataExpertiseChainResponse['핵심솔루션']}"
            SupplyCollectionDataExpertiseChainResponseSet[f'전문데이터{i+1}'].update(SupplyCollectionDataExpertiseChainResponse)
            processCount += 1

        # 최종 Set 데이터 추가
        OutputDicSet[Process] = SupplyCollectionDataExpertiseChainResponseSet
    
    ## Process4-1: SupplyCollectionDataUltimate Response 생성
    if "Ultimate" in Extension:
        Process = "SupplyCollectionDataUltimate"
        if Type == "Search":
            Input = SupplyCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        
        SupplyCollectionDataUltimateResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, SupplyCollectionDataUltimateFilter, CheckCount, "OpenAI", mode, MessagesReview)
        processCount += 1
        
        ## Process4-2: SupplyCollectionDataUltimateChain Response 연속 생성 및 Set로 합치기
        Process = "SupplyCollectionDataUltimateChain"
        SupplyCollectionDataUltimateChainResponseSet = {}
        for i, Response in enumerate(SupplyCollectionDataUltimateResponse):
            InputText = f'{Input}\n\n<새로운 핵심솔루션 메모>\n{Response}\n'
            SupplyCollectionDataUltimateChainResponse = ProcessResponse(projectName, email, Process, InputText, processCount, InputCount, SupplyCollectionDataUltimateChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
            SupplyCollectionDataUltimateChainResponseSet[f'연계데이터{i+1}'] = {}
            SupplyCollectionDataUltimateChainResponse['핵심솔루션'] = f"{Response['핵심솔루션']}  {SupplyCollectionDataUltimateChainResponse['핵심솔루션']}"
            SupplyCollectionDataUltimateChainResponseSet[f'연계데이터{i+1}'].update(SupplyCollectionDataUltimateChainResponse)
            processCount += 1

        # 최종 Set 데이터 추가
        OutputDicSet[Process] = SupplyCollectionDataUltimateChainResponseSet
    
    ## Process5: SupplyCollectionDataDetailChain Response 생성
    if "Detail" in Extension:
        Process = "SupplyCollectionDataDetailChain"
        if Type == "Search":
            Input = SupplyCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        pass
    
    ## Process6: SupplyCollectionDataRethinkingChain Response 생성
    if "Rethinking" in Extension:
        Process = "SupplyCollectionDataRethinkingChain"
        if Type == "Search":
            Input = SupplyCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        pass

    ## ProcessResponse 임시저장
    CollectionDataChain, DateTime = ProcessResponseTempSave(MainKey, InputDic, OutputDicSet, TotalSupplyCollectionDataTempPath)

    print(f"[ User: {email} | Chain: {projectName} | SupplyCollectionDataUpdate 완료 ]")
    
    return CollectionDataChain, DateTime

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = '241204_개정교육과정초등교과별이해연수'
    #########################################################################