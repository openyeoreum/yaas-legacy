import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from datetime import datetime
from agent.a2_Solution.a21_General.a215_LoadLLM import OpenAI_LLMresponse, ANTHROPIC_LLMresponse

######################
##### Filter 조건 #####
######################
## Process1: DemandCollectionDataDetail의 Filter(Error 예외처리)
def DemandCollectionDataDetailFilter(Response, CheckCount):
    # Error1: JSON 형식이 아닐 때의 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "DemandCollectionDataDetail, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 존재 여부 확인
    required_keys = ['핵심목적', '필요내용', '필요목표', '필요질문', '검색어완성도', '검색어피드백']
    missing_keys = [key for key in required_keys if key not in OutputDic]
    if missing_keys:
        return f"DemandCollectionDataDetail, JSONKeyError: 누락된 키: {', '.join(missing_keys)}"
    
    # Error3: 데이터 타입 검증
    # 핵심목적, 필요내용, 필요목표, 필요질문은 문자열이어야 함
    for key in ['핵심목적', '필요내용', '필요목표', '필요질문']:
        if isinstance(OutputDic[key], list):
            OutputDic[key] = ' '.join(OutputDic[key])
        if not isinstance(OutputDic[key], str):
            return f"DemandCollectionDataDetail, JSON에서 오류 발생: '{key}'은 문자열이 아님"

    # 검색어완성도는 0-100 사이의 정수여야 함  
    if (not isinstance(OutputDic['검색어완성도'], (int, str))) or (isinstance(OutputDic['검색어완성도'], str) and not OutputDic['검색어완성도'].isdigit()) or (isinstance(OutputDic['검색어완성도'], (int, str)) and (int(OutputDic['검색어완성도']) < 0 or int(OutputDic['검색어완성도']) > 100)):
        return "DemandCollectionDataDetail, JSON에서 오류 발생: '검색어완성도'가 0-100 사이의 정수가 아님"
    else: OutputDic['검색어완성도'] = int(OutputDic['검색어완성도'])

    # 검색어피드백은 문자열 리스트여야 함
    if not isinstance(OutputDic['검색어피드백'], list) or not all(isinstance(item, str) for item in OutputDic['검색어피드백']):
        return "DemandCollectionDataDetail, JSON에서 오류 발생: '검색어피드백'은 문자열 리스트가 아님"
    
    return OutputDic

## Process2: DemandCollectionDataContext의 Filter(Error 예외처리)
def DemandCollectionDataContextFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "DemandCollectionDataContext, JSONDecode에서 오류 발생: JSONDecodeError"
    
    # Error2: 최상위 필수 키 존재 여부 확인
    required_top_level_keys = ['핵심목적', '분야', '필요', '정보의질']
    missing_top_keys = [key for key in required_top_level_keys if key not in OutputDic]
    if missing_top_keys:
        return f"DemandCollectionDataContext, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"
    
    # Error3: 데이터 타입 확인 (핵심목적, 분야, 정보의질)
    if not isinstance(OutputDic['핵심목적'], str):
        return "DemandCollectionDataContext, JSON에서 오류 발생: '핵심목적'은 문자열이 아님"
    if not isinstance(OutputDic['분야'], list) or not all(isinstance(item, str) for item in OutputDic['분야']):
        return "DemandCollectionDataContext, JSON에서 오류 발생: '분야'는 문자열 리스트가 아님"
    if (not isinstance(OutputDic['정보의질'], (int, str))) or (isinstance(OutputDic['정보의질'], str) and not OutputDic['정보의질'].isdigit()) or (isinstance(OutputDic['정보의질'], (int, str)) and (int(OutputDic['정보의질']) < 0 or int(OutputDic['정보의질']) > 100)):
        return "DemandCollectionDataContext, JSON에서 오류 발생: '정보의질'은 0-100 사이의 정수가 아님"
    else:
        OutputDic['정보의질'] = int(OutputDic['정보의질'])

    # Error4: '필요' 키의 구조와 데이터 검증
    if not isinstance(OutputDic['필요'], dict):
        return "DemandCollectionDataContext, JSON에서 오류 발생: '필요'는 딕셔너리가 아님"
    
    required_sub_keys = ['필요내용', '필요목표', '필요질문']
    missing_sub_keys = [key for key in required_sub_keys if key not in OutputDic['필요']]
    if missing_sub_keys:
        return f"DemandCollectionDataContext, JSONKeyError: '필요' 딕셔너리에 누락된 키: {', '.join(missing_sub_keys)}"
    
    for sub_key in required_sub_keys:
        sub_item = OutputDic['필요'][sub_key]
        if not isinstance(sub_item, dict):
            return f"DemandCollectionDataContext, JSON에서 오류 발생: '{sub_key}'는 딕셔너리가 아님"
        
        # 각 서브 키 내 필수 키 확인
        required_detail_keys = ['설명', '키워드', '중요도']
        missing_detail_keys = [key for key in required_detail_keys if key not in sub_item]
        if missing_detail_keys:
            return f"DemandCollectionDataContext, JSONKeyError: '{sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"
        
        # 설명 검증
        if not isinstance(sub_item['설명'], str):
            return f"DemandCollectionDataContext, JSON에서 오류 발생: '{sub_key} > 설명'은 문자열이 아님"
        
        # 키워드 검증
        if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
            return f"DemandCollectionDataContext, JSON에서 오류 발생: '{sub_key} > 키워드'는 문자열 리스트가 아님"
        
        # 중요도 검증
        if (not isinstance(sub_item['중요도'], (int, str))) or (isinstance(sub_item['중요도'], str) and not sub_item['중요도'].isdigit()) or (isinstance(sub_item['중요도'], (int, str)) and (int(sub_item['중요도']) < 0 or int(sub_item['중요도']) > 100)):
            return f"DemandCollectionDataContext, JSON에서 오류 발생: '{sub_key} > 중요도'가 0-100 사이의 정수가 아님"
        else:
            sub_item['중요도'] = int(sub_item['중요도'])

    return OutputDic

## Process3-1: DemandCollectionDataExpertiseFilter의 Filter(Error 예외처리)
def DemandCollectionDataExpertiseFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "DemandCollectionDataExpertiseChain, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '전문분야들' not in OutputDic:
        return "DemandCollectionDataExpertiseChain, JSONKeyError: '전문분야들' 키가 누락"

    # Error3: '전문분야들' 데이터 타입 확인
    ExpertiseList = OutputDic['전문분야들']
    if not isinstance(ExpertiseList, list):
        return "DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문분야들'은 리스트 형태가 아님"
    if len(OutputDic['전문분야들']) != 5:
        return "DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문분야들'은 5개의 항목을 가져야 합니다"

    # Error4: 리스트 내부 검증
    for idx, item in enumerate(ExpertiseList):
        # 각 항목은 딕셔너리 형태여야 함
        if not isinstance(item, dict):
            return f"DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문분야들[{idx}]'은 딕셔너리 형태가 아님"

        # 필수 키 확인
        required_keys = ['전문분야', '이유']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"DemandCollectionDataExpertiseChain, JSONKeyError: '전문분야들[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 검증
        if not isinstance(item['전문분야'], str):
            return f"DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문분야들[{idx}] > 전문분야'는 문자열이 아님"
        if not isinstance(item['이유'], str):
            return f"DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문분야들[{idx}] > 이유'는 문자열이 아님"

    return OutputDic['전문분야들']

## Process3-2: DemandCollectionDataExpertiseChainFilter의 Filter(Error 예외처리)
def DemandCollectionDataExpertiseChainFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "DemandCollectionDataExpertiseChain, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '전문데이터' not in OutputDic:
        return "DemandCollectionDataExpertiseChain, JSONKeyError: '전문데이터' 키가 누락되었음"

    # Error3: 전문데이터 내부 필수 키 확인
    expertise_data = OutputDic['전문데이터']
    required_keys = ['핵심목적', '분야', '필요', '정보의질']
    missing_keys = [key for key in required_keys if key not in expertise_data]
    if missing_keys:
        return f"DemandCollectionDataExpertiseChain, JSONKeyError: '전문데이터'에 누락된 키: {', '.join(missing_keys)}"

    # Error4: 데이터 타입 검증
    if not isinstance(expertise_data['핵심목적'], str):
        return "DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 핵심목적'은 문자열이어야 합니다"
    if not isinstance(expertise_data['분야'], list) or not all(isinstance(item, str) for item in expertise_data['분야']):
        return "DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 분야'는 문자열 리스트가 아님"
    if (not isinstance(expertise_data['정보의질'], (int, str))) or (isinstance(expertise_data['정보의질'], str) and not expertise_data['정보의질'].isdigit()) or (isinstance(expertise_data['정보의질'], (int, str)) and (int(expertise_data['정보의질']) < 0 or int(expertise_data['정보의질']) > 100)):
        return "DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 정보의질'은 0-100 사이의 정수가 아님"
    else:
        expertise_data['정보의질'] = int(expertise_data['정보의질'])

    # Error5: '필요' 내부 구조 검증
    if not isinstance(expertise_data['필요'], dict):
        return "DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 필요'는 딕셔너리 형태가 아님"

    required_sub_keys = ['필요내용', '필요목표', '필요질문']
    for sub_key in required_sub_keys:
        if sub_key not in expertise_data['필요']:
            return f"DemandCollectionDataExpertiseChain, JSONKeyError: '전문데이터 > 필요'에 누락된 키: {sub_key}"
        sub_item = expertise_data['필요'][sub_key]

        if not isinstance(sub_item, dict):
            return f"DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 필요 > {sub_key}'는 딕셔너리 형태가 아님"

        # 내부 필수 키 확인
        required_detail_keys = ['설명', '키워드', '중요도']
        missing_detail_keys = [key for key in required_detail_keys if key not in sub_item]
        if missing_detail_keys:
            return f"DemandCollectionDataExpertiseChain, JSONKeyError: '전문데이터 > 필요 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

        # 데이터 타입 검증
        if not isinstance(sub_item['설명'], str):
            return f"DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 필요 > {sub_key} > 설명'은 문자열이 아님"
        if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
            return f"DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 필요 > {sub_key} > 키워드'는 문자열 리스트가 아님"
        if (not isinstance(sub_item['중요도'], (int, str))) or (isinstance(sub_item['중요도'], str) and not sub_item['중요도'].isdigit()) or (isinstance(sub_item['중요도'], (int, str)) and (int(sub_item['중요도']) < 0 or int(sub_item['중요도']) > 100)):
            return f"DemandCollectionDataExpertiseChain, JSON에서 오류 발생: '전문데이터 > 필요 > {sub_key} > 중요도'가 0-100 사이의 정수가 아님"
        else:
            sub_item['중요도'] = int(sub_item['중요도'])

    return OutputDic['전문데이터']

## Process4-1: DemandCollectionDataUltimateFilter의 Filter(Error 예외처리)
def DemandCollectionDataUltimateFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "DemandCollectionDataUltimateFilter, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_keys = ['최초핵심목적', '궁극적핵심목적', '5단계핵심목적']
    missing_top_keys = [key for key in required_top_keys if key not in OutputDic]
    if missing_top_keys:
        return f"DemandCollectionDataUltimateFilter, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"

    # Error3: 최상위 키 데이터 타입 검증
    if not isinstance(OutputDic['최초핵심목적'], str):
        return "DemandCollectionDataUltimateFilter, JSON에서 오류 발생: '최초핵심목적'은 문자열이어야 합니다"
    if not isinstance(OutputDic['궁극적핵심목적'], str):
        return "DemandCollectionDataUltimateFilter, JSON에서 오류 발생: '궁극적핵심목적'은 문자열이어야 합니다"

    # Error4: 5단계핵심목적 검증
    if not isinstance(OutputDic['5단계핵심목적'], list):
        return "DemandCollectionDataUltimateFilter, JSON에서 오류 발생: '5단계핵심목적'은 리스트 형태여야 합니다"
    if len(OutputDic['5단계핵심목적']) != 5:
        return "DemandCollectionDataUltimateFilter, JSON에서 오류 발생: '5단계핵심목적'은 5개의 항목을 가져야 합니다"

    for idx, item in enumerate(OutputDic['5단계핵심목적']):
        # 리스트의 각 항목은 딕셔너리 형태여야 함
        if not isinstance(item, dict):
            return f"DemandCollectionDataUltimateFilter, JSON에서 오류 발생: '5단계핵심목적[{idx}]'은 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['새로운문제와필요', '핵심목적']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"DemandCollectionDataUltimateFilter, JSONKeyError: '5단계핵심목적[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 검증
        if not isinstance(item['새로운문제와필요'], str):
            return f"DemandCollectionDataUltimateFilter, JSON에서 오류 발생: '5단계핵심목적[{idx}] > 새로운문제와필요'는 문자열이어야 합니다"
        if not isinstance(item['핵심목적'], str):
            return f"DemandCollectionDataUltimateFilter, JSON에서 오류 발생: '5단계핵심목적[{idx}] > 핵심목적'은 문자열이어야 합니다"

    return OutputDic['5단계핵심목적']

## Process4-2: DemandCollectionDataUltimateChainFilter의 Filter(Error 예외처리)
def DemandCollectionDataUltimateChainFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "DemandCollectionDataUltimateChainFilter, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_keys = ['핵심목적', '분야', '필요', '정보의질']
    missing_top_keys = [key for key in required_top_keys if key not in OutputDic]
    if missing_top_keys:
        return f"DemandCollectionDataUltimateChainFilter, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"

    # Error3: 최상위 키 데이터 타입 검증
    if not isinstance(OutputDic['핵심목적'], str):
        return "DemandCollectionDataUltimateChainFilter, JSON에서 오류 발생: '핵심목적'은 문자열이어야 합니다"
    if not isinstance(OutputDic['분야'], list) or not all(isinstance(item, str) for item in OutputDic['분야']):
        return "DemandCollectionDataUltimateChainFilter, JSON에서 오류 발생: '분야'는 문자열 리스트여야 합니다"
    if (not isinstance(OutputDic['정보의질'], (int, str))) or (isinstance(OutputDic['정보의질'], str) and not OutputDic['정보의질'].isdigit()) or (isinstance(OutputDic['정보의질'], (int, str)) and (int(OutputDic['정보의질']) < 0 or int(OutputDic['정보의질']) > 100)):
        return "DemandCollectionDataUltimateChainFilter, JSON에서 오류 발생: '정보의질'은 0-100 사이의 정수여야 합니다"
    else:
        OutputDic['정보의질'] = int(OutputDic['정보의질'])

    # Error4: '필요' 키 구조 검증
    if not isinstance(OutputDic['필요'], dict):
        return "DemandCollectionDataUltimateChainFilter, JSON에서 오류 발생: '필요'는 딕셔너리 형태여야 합니다"

    # '필요' 내부 필수 키 확인
    required_sub_keys = ['필요내용', '필요목표', '필요질문']
    for sub_key in required_sub_keys:
        if sub_key not in OutputDic['필요']:
            return f"DemandCollectionDataUltimateChainFilter, JSONKeyError: '필요'에 누락된 키: {sub_key}"

        sub_item = OutputDic['필요'][sub_key]

        # 각 항목은 딕셔너리 형태여야 함
        if not isinstance(sub_item, dict):
            return f"DemandCollectionDataUltimateChainFilter, JSON에서 오류 발생: '필요 > {sub_key}'는 딕셔너리 형태여야 합니다"

        # 내부 필수 키 확인
        required_detail_keys = ['설명', '키워드', '중요도']
        missing_detail_keys = [key for key in required_detail_keys if key not in sub_item]
        if missing_detail_keys:
            return f"DemandCollectionDataUltimateChainFilter, JSONKeyError: '필요 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

        # 데이터 타입 검증
        if not isinstance(sub_item['설명'], str):
            return f"DemandCollectionDataUltimateChainFilter, JSON에서 오류 발생: '필요 > {sub_key} > 설명'은 문자열이어야 합니다"
        if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
            return f"DemandCollectionDataUltimateChainFilter, JSON에서 오류 발생: '필요 > {sub_key} > 키워드'는 문자열 리스트여야 합니다"
        if (not isinstance(sub_item['중요도'], (int, str))) or (isinstance(sub_item['중요도'], str) and not sub_item['중요도'].isdigit()) or (isinstance(sub_item['중요도'], (int, str)) and (int(sub_item['중요도']) < 0 or int(sub_item['중요도']) > 100)):
            return f"DemandCollectionDataUltimateChainFilter, JSON에서 오류 발생: '필요 > {sub_key} > 중요도'는 0-100 사이의 정수여야 합니다"
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
    
    ProcessKeyList.append("DemandSearch")
    ProcessDicList.append(SearchDic)
    #### Search ####
    
    #### Detail ####
    Process = "DemandCollectionDataDetail"
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
    Process = "DemandCollectionDataContext"
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
    Process = "DemandCollectionDataExpertiseChain"
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
    Process = "DemandCollectionDataUltimateChain"
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
    DataTempJsonPath = os.path.join(DataTempPath, f"DemandCollectionData_({DateTime})_{TermText}.json")
    with open(DataTempJsonPath, 'w', encoding = 'utf-8') as DataTempJson:
        json.dump(DataTemp, DataTempJson, ensure_ascii = False, indent = 4)
        
    # CollectionDataChain 추출
    CollectionDataChain = DataTemp[MainKey]
        
    return CollectionDataChain, DateTime

################################
##### Process 진행 및 업데이트 #####
################################
## DemandCollectionData 프롬프트 요청 및 결과물 Json화
def DemandCollectionDataProcessUpdate(projectName, email, InputDic, mode = "Master", MainKey = 'DemandSearchAnalysis', MessagesReview = "on"):
    print(f"< User: {email} | Chain: {projectName} | DemandCollectionDataUpdate 시작 >")
    ## TotalPublisherData 경로 설정
    TotalDemandCollectionDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1511_DemandCollectionData/s15111_TotalDemandCollectionData"
    TotalDemandCollectionDataJsonPath = os.path.join(TotalDemandCollectionDataPath, 'TotalDemandCollectionData.json')
    TotalDemandCollectionDataTempPath = os.path.join(TotalDemandCollectionDataPath, 'TotalDemandCollectionDataTemp')
    
    ## DemandCollectionDataDetailProcess
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

    ## Process1: DemandCollectionDataDetail Response 생성
    if Type == "Search":
        Process = "DemandCollectionDataDetail"
        Input = InputDic['Input']
        
        DemandCollectionDataDetailResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, DemandCollectionDataDetailFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicSet[Process] = DemandCollectionDataDetailResponse
        processCount += 1
    
    ## Process2: DemandCollectionDataContext Response 생성
    if Type == "Search":
        Process = "DemandCollectionDataContext"
        Input = DemandCollectionDataDetailResponse.copy()
        DeleteKeys = ['검색어완성도', '검색어피드백']
        for key in DeleteKeys:
            del Input[key]
    
        DemandCollectionDataContextResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, DemandCollectionDataContextFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicSet[Process] = DemandCollectionDataContextResponse
    elif Type == "Match":
        Process = "DemandCollectionDataContext"
        OutputDicSet[Process] = InputDic['CollectionData']
    processCount += 1
    
    ## Process3-1: DemandCollectionDataExpertise Response 생성
    if "Expertise" in Extension:
        Process = "DemandCollectionDataExpertise"
        if Type == "Search":
            Input = DemandCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        
        DemandCollectionDataExpertiseResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, DemandCollectionDataExpertiseFilter, CheckCount, "OpenAI", mode, MessagesReview)
        processCount += 1
        
        ## Process3-2: DemandCollectionDataExpertiseChain Response 연속 생성 및 Set로 합치기
        Process = "DemandCollectionDataExpertiseChain"
        DemandCollectionDataExpertiseChainResponseSet = {}
        for i, Response in enumerate(DemandCollectionDataExpertiseResponse):
            InputText = f'{Response}\n\n<데이터>\n{Input}\n'
            DemandCollectionDataExpertiseChainResponse = ProcessResponse(projectName, email, Process, InputText, processCount, InputCount, DemandCollectionDataExpertiseChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
            DemandCollectionDataExpertiseChainResponseSet[f'전문데이터{i+1}'] = {}
            DemandCollectionDataExpertiseChainResponse['핵심목적'] = f"{Response['전문분야']}  {DemandCollectionDataExpertiseChainResponse['핵심목적']}"
            DemandCollectionDataExpertiseChainResponseSet[f'전문데이터{i+1}'].update(DemandCollectionDataExpertiseChainResponse)
            processCount += 1

        # 최종 Set 데이터 추가
        OutputDicSet[Process] = DemandCollectionDataExpertiseChainResponseSet

    ## Process4-1: DemandCollectionDataUltimate Response 생성
    if "Ultimate" in Extension:
        Process = "DemandCollectionDataUltimate"
        if Type == "Search":
            Input = DemandCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        
        DemandCollectionDataUltimateResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, DemandCollectionDataUltimateFilter, CheckCount, "OpenAI", mode, MessagesReview)
        processCount += 1
        
        ## Process4-2: DemandCollectionDataUltimateChain Response 연속 생성 및 Set로 합치기
        Process = "DemandCollectionDataUltimateChain"
        DemandCollectionDataUltimateChainResponseSet = {}
        for i, Response in enumerate(DemandCollectionDataUltimateResponse):
            InputText = f'{Input}\n\n<새로운 핵심목적 메모>\n{Response}\n'
            DemandCollectionDataUltimateChainResponse = ProcessResponse(projectName, email, Process, InputText, processCount, InputCount, DemandCollectionDataUltimateChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
            DemandCollectionDataUltimateChainResponseSet[f'연계데이터{i+1}'] = {}
            DemandCollectionDataUltimateChainResponse['핵심목적'] = f"{Response['핵심목적']}  {DemandCollectionDataUltimateChainResponse['핵심목적']}"
            DemandCollectionDataUltimateChainResponseSet[f'연계데이터{i+1}'].update(DemandCollectionDataUltimateChainResponse)
            processCount += 1

        # 최종 Set 데이터 추가
        OutputDicSet[Process] = DemandCollectionDataUltimateChainResponseSet
    
    ## Process5: DemandCollectionDataDetailChain Response 생성
    if "Detail" in Extension:
        Process = "DemandCollectionDataDetailChain"
        if Type == "Search":
            Input = DemandCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        pass
    
    ## Process6: DemandCollectionDataRethinkingChain Response 생성
    if "Rethinking" in Extension:
        Process = "DemandCollectionDataRethinkingChain"
        if Type == "Search":
            Input = DemandCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        pass

    ## ProcessResponse 임시저장
    CollectionDataChain, DateTime = ProcessResponseTempSave(MainKey, InputDic, OutputDicSet, TotalDemandCollectionDataTempPath)

    print(f"[ User: {email} | Chain: {projectName} | DemandCollectionDataUpdate 완료 ]")
    
    return CollectionDataChain, DateTime

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241204_개정교육과정초등교과별이해연수'
    #########################################################################