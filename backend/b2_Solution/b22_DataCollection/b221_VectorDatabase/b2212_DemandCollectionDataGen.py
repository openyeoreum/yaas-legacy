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
        if not isinstance(OutputDic[key], str):
            return f"DemandCollectionDataDetail, JSON에서 오류 발생: '{key}'은 문자열이 아님"

    # 검색어완성도는 0-100 사이의 정수여야 함
    if not isinstance(OutputDic['검색어완성도'], int) or not (0 <= OutputDic['검색어완성도'] <= 100):
        return "DemandCollectionDataDetail, JSON에서 오류 발생: '검색어완성도'는 0-100 사이의 정수가 아님"

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
    if not isinstance(OutputDic['정보의질'], int) or not (0 <= OutputDic['정보의질'] <= 100):
        return "DemandCollectionDataContext, JSON에서 오류 발생: '정보의질'은 0-100 사이의 정수가 아님"

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
        if not isinstance(sub_item['중요도'], int) or not (0 <= sub_item['중요도'] <= 100):
            return f"DemandCollectionDataContext, JSON에서 오류 발생: '{sub_key} > 중요도'는 0-100 사이의 정수가 아님"

    return OutputDic

## Process3: DemandCollectionDataExtensionChainFilter의 Filter(Error 예외처리)
def DemandCollectionDataExtensionChainFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "DemandCollectionDataExtensionChain, JSONDecode에서 오류 발생: JSONDecodeError"
    
    # Error2: 최상위 키 검사 (전문데이터1~5)
    top_level_keys = [f"전문데이터{i}" for i in range(1, 6)]
    missing_keys = [key for key in top_level_keys if key not in OutputDic]
    if missing_keys:
        return f"DemandCollectionDataExtensionChain, JSONKeyError: 누락된 전문데이터 키: {', '.join(missing_keys)}"
    
    # Error3: 각 전문데이터 항목에 대한 검증
    for key in top_level_keys:
        data = OutputDic[key]

        # 전문데이터 내부 필수 키 확인
        required_keys = ['핵심목적', '분야', '필요', '정보의질']
        missing_inner_keys = [k for k in required_keys if k not in data]
        if missing_inner_keys:
            return f"DemandCollectionDataExtensionChain, JSONKeyError: '{key}'에 누락된 키: {', '.join(missing_inner_keys)}"
        
        # 데이터 타입 검증
        if not isinstance(data['핵심목적'], str):
            return f"DemandCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 핵심목적'은 문자열이 아님"
        if not isinstance(data['분야'], list) or not all(isinstance(item, str) for item in data['분야']):
            return f"DemandCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 분야'는 문자열 리스트가 아님"
        if not isinstance(data['정보의질'], int) or not (0 <= data['정보의질'] <= 100):
            return f"DemandCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 정보의질'은 0-100 사이의 정수가 아님"

        # '필요' 키 검증
        if not isinstance(data['필요'], dict):
            return f"DemandCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 필요'는 딕셔너리가 아님"
        
        # '필요' 내부 구조 검증
        required_sub_keys = ['필요내용', '필요목표', '필요질문']
        missing_sub_keys = [sub_key for sub_key in required_sub_keys if sub_key not in data['필요']]
        if missing_sub_keys:
            return f"DemandCollectionDataExtensionChain, JSONKeyError: '{key} > 필요'에 누락된 키: {', '.join(missing_sub_keys)}"
        
        for sub_key in required_sub_keys:
            sub_item = data['필요'][sub_key]
            if not isinstance(sub_item, dict):
                return f"DemandCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 필요 > {sub_key}'는 딕셔너리가 아님"
            
            # '필요내용', '필요목표', '필요질문' 내부 구조 검증
            required_detail_keys = ['설명', '키워드', '중요도']
            missing_detail_keys = [k for k in required_detail_keys if k not in sub_item]
            if missing_detail_keys:
                return f"DemandCollectionDataExtensionChain, JSONKeyError: '{key} > 필요 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"
            
            # 데이터 타입 및 값 검증
            if not isinstance(sub_item['설명'], str):
                return f"DemandCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 필요 > {sub_key} > 설명'은 문자열이 아님"
            if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
                return f"DemandCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 필요 > {sub_key} > 키워드'는 문자열 리스트가 아님"
            if not isinstance(sub_item['중요도'], int) or not (0 <= sub_item['중요도'] <= 100):
                return f"DemandCollectionDataExtensionChain, JSON에서 오류 발생: '{key} > 필요 > {sub_key} > 중요도'는 0-100 사이의 정수가 아님"

    return OutputDic

## Process4: DemandCollectionDataExtensionChainFilter의 Filter(Error 예외처리)
def DemandCollectionDataUltimateChainFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "DemandCollectionDataUltimateChain, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_level_keys = ['최초핵심목적', '궁극적핵심목적']
    linked_data_keys = [f'연계데이터{i}' for i in range(1, 6)]
    missing_top_keys = [key for key in required_top_level_keys + linked_data_keys if key not in OutputDic]
    if missing_top_keys:
        return f"DemandCollectionDataUltimateChain, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"

    # Error3: 데이터 타입 검증 (최초핵심목적, 궁극적핵심목적)
    if not isinstance(OutputDic['최초핵심목적'], str):
        return "DemandCollectionDataUltimateChain, JSON에서 오류 발생: '최초핵심목적'은 문자열이어야 합니다"
    if not isinstance(OutputDic['궁극적핵심목적'], str):
        return "DemandCollectionDataUltimateChain, JSON에서 오류 발생: '궁극적핵심목적'은 문자열이어야 합니다"

    # Error4: 연계데이터 구조 검증
    for key in linked_data_keys:
        data = OutputDic[key]

        # 연계데이터 내부 필수 키 확인
        required_keys = ['핵심목적', '분야', '필요', '정보의질']
        missing_inner_keys = [k for k in required_keys if k not in data]
        if missing_inner_keys:
            return f"DemandCollectionDataUltimateChain, JSONKeyError: '{key}'에 누락된 키: {', '.join(missing_inner_keys)}"

        # 데이터 타입 검증
        if not isinstance(data['핵심목적'], str):
            return f"DemandCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 핵심목적'은 문자열이어야 합니다"
        if not isinstance(data['분야'], list) or not all(isinstance(item, str) for item in data['분야']):
            return f"DemandCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 분야'는 문자열 리스트여야 합니다"
        if not isinstance(data['정보의질'], int) or not (0 <= data['정보의질'] <= 100):
            return f"DemandCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 정보의질'은 0-100 사이의 정수여야 합니다"

        # '필요' 키 검증
        if not isinstance(data['필요'], dict):
            return f"DemandCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 필요'는 딕셔너리 형태여야 합니다"

        # '필요' 내부 구조 검증
        required_sub_keys = ['필요내용', '필요목표', '필요질문']
        missing_sub_keys = [sub_key for sub_key in required_sub_keys if sub_key not in data['필요']]
        if missing_sub_keys:
            return f"DemandCollectionDataUltimateChain, JSONKeyError: '{key} > 필요'에 누락된 키: {', '.join(missing_sub_keys)}"

        for sub_key in required_sub_keys:
            sub_item = data['필요'][sub_key]
            if not isinstance(sub_item, dict):
                return f"DemandCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 필요 > {sub_key}'는 딕셔너리 형태여야 합니다"

            # '필요내용', '필요목표', '필요질문' 내부 구조 검증
            required_detail_keys = ['설명', '키워드', '중요도']
            missing_detail_keys = [k for k in required_detail_keys if k not in sub_item]
            if missing_detail_keys:
                return f"DemandCollectionDataUltimateChain, JSONKeyError: '{key} > 필요 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

            # 데이터 타입 및 값 검증
            if not isinstance(sub_item['설명'], str):
                return f"DemandCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 필요 > {sub_key} > 설명'은 문자열이어야 합니다"
            if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
                return f"DemandCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 필요 > {sub_key} > 키워드'는 문자열 리스트여야 합니다"
            if not isinstance(sub_item['중요도'], int) or not (0 <= sub_item['중요도'] <= 100):
                return f"DemandCollectionDataUltimateChain, JSON에서 오류 발생: '{key} > 필요 > {sub_key} > 중요도'는 0-100 사이의 정수여야 합니다"

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
    ScarchSummary = OutputDicList[0]['핵심목적']
    # Detail-Needs
    DetailNeeds = OutputDicList[0]['필요내용']
    # Detail-Purpose
    DetailPurpose = OutputDicList[0]['필요목표']
    # Detail-Question
    DetailQuestion = OutputDicList[0]['필요질문']
    # Detail-Weight
    DetailWeight = OutputDicList[0]['검색어완성도']
    # Detail-Feedback
    DetailFeedback = OutputDicList[0]['검색어피드백']
    ## DetailDic ##
    DetailDic = {'Summary': ScarchSummary, 'Needs': DetailNeeds, 'Purpose': DetailPurpose, 'Question': DetailQuestion, 'Weight': DetailWeight, 'Feedback': DetailFeedback}
    #### Detail ####
    
    #### Context ####
    # Context-Summary
    ContextSummary = OutputDicList[1]['핵심목적']
    # Context-KeyWord
    ContextKeyWord = OutputDicList[1]['분야']
    # Context-Demand
    ContextDemandNeeds = {"Sentence": OutputDicList[1]['필요']['필요내용']['설명'], "KeyWord": OutputDicList[1]['필요']['필요내용']['키워드'], "Weight": OutputDicList[1]['필요']['필요내용']['중요도']}
    ContextDemandPurpose = {"Sentence": OutputDicList[1]['필요']['필요목표']['설명'], "KeyWord": OutputDicList[1]['필요']['필요목표']['키워드'], "Weight": OutputDicList[1]['필요']['필요목표']['중요도']}
    ContextDemandQuestion = {"Sentence": OutputDicList[1]['필요']['필요질문']['설명'], "KeyWord": OutputDicList[1]['필요']['필요질문']['키워드'], "Weight": OutputDicList[1]['필요']['필요질문']['중요도']}
    ContextDemand = {'Needs': ContextDemandNeeds, 'Purpose': ContextDemandPurpose, 'Question': ContextDemandQuestion}
    # Context-Weight
    ContextWeight = OutputDicList[1]['정보의질']
    ## ContextDic ##
    ContextDic = {'Summary': ContextSummary, 'KeyWord': ContextKeyWord, 'Demand': ContextDemand, 'Weight': ContextWeight}
    #### Context ####
    
    #### ContextExtension ####
    ContextExtensionDicList = []
    for i in range(5):
        # ContextExtension-Summary
        ContextExtensionSummary = OutputDicList[2][f'전문데이터{i+1}']['핵심목적']
        # ContextExtension-KeyWord
        ContextExtensionKeyWord = OutputDicList[2][f'전문데이터{i+1}']['분야']
        # ContextExtension-Demand
        ContextExtensionDemandNeeds = {"Sentence": OutputDicList[2][f'전문데이터{i+1}']['필요']['필요내용']['설명'], "KeyWord": OutputDicList[2][f'전문데이터{i+1}']['필요']['필요내용']['키워드'], "Weight": OutputDicList[2][f'전문데이터{i+1}']['필요']['필요내용']['중요도']}
        ContextExtensionDemandPurpose = {"Sentence": OutputDicList[2][f'전문데이터{i+1}']['필요']['필요목표']['설명'], "KeyWord": OutputDicList[2][f'전문데이터{i+1}']['필요']['필요목표']['키워드'], "Weight": OutputDicList[2][f'전문데이터{i+1}']['필요']['필요목표']['중요도']}
        ContextExtensionDemandQuestion = {"Sentence": OutputDicList[2][f'전문데이터{i+1}']['필요']['필요질문']['설명'], "KeyWord": OutputDicList[2][f'전문데이터{i+1}']['필요']['필요질문']['키워드'], "Weight": OutputDicList[2][f'전문데이터{i+1}']['필요']['필요질문']['중요도']}
        ContextExtensionDemand = {'Needs': ContextExtensionDemandNeeds, 'Purpose': ContextExtensionDemandPurpose, 'Question': ContextExtensionDemandQuestion}
        # ContextExtension-Weight
        ContextExtensionWeight = OutputDicList[2][f'전문데이터{i+1}']['정보의질']
        ## ContextExtensionDic ##
        ContextExtensionDic = {'Summary': ContextExtensionSummary, 'KeyWord': ContextExtensionKeyWord, 'Demand': ContextExtensionDemand, 'Weight': ContextExtensionWeight}
        ContextExtensionDicList.append(ContextExtensionDic)
    #### ContextExtension ####
    
    #### ContextUltimate ####
    ContextUltimateDicList = []
    for i in range(5):
        # ContextUltimate-Summary
        ContextUltimateSummary = OutputDicList[3][f'연계데이터{i+1}']['핵심목적']
        # ContextUltimate-KeyWord
        ContextUltimateKeyWord = OutputDicList[3][f'연계데이터{i+1}']['분야']
        # ContextUltimate-Demand
        ContextUltimateDemandNeeds = {"Sentence": OutputDicList[3][f'연계데이터{i+1}']['필요']['필요내용']['설명'], "KeyWord": OutputDicList[3][f'연계데이터{i+1}']['필요']['필요내용']['키워드'], "Weight": OutputDicList[3][f'연계데이터{i+1}']['필요']['필요내용']['중요도']}
        ContextUltimateDemandPurpose = {"Sentence": OutputDicList[3][f'연계데이터{i+1}']['필요']['필요목표']['설명'], "KeyWord": OutputDicList[3][f'연계데이터{i+1}']['필요']['필요목표']['키워드'], "Weight": OutputDicList[3][f'연계데이터{i+1}']['필요']['필요목표']['중요도']}
        ContextUltimateDemandQuestion = {"Sentence": OutputDicList[3][f'연계데이터{i+1}']['필요']['필요질문']['설명'], "KeyWord": OutputDicList[3][f'연계데이터{i+1}']['필요']['필요질문']['키워드'], "Weight": OutputDicList[3][f'연계데이터{i+1}']['필요']['필요질문']['중요도']}
        ContextUltimateDemand = {'Needs': ContextUltimateDemandNeeds, 'Purpose': ContextUltimateDemandPurpose, 'Question': ContextUltimateDemandQuestion}
        # ContextUltimate-Weight
        ContextUltimateWeight = OutputDicList[3][f'연계데이터{i+1}']['정보의질']
        ## ContextUltimateDic ##
        ContextUltimateDic = {'Summary': ContextUltimateSummary, 'KeyWord': ContextUltimateKeyWord, 'Demand': ContextUltimateDemand, 'Weight': ContextUltimateWeight}
        ContextUltimateDicList.append(ContextUltimateDic)
    #### ContextUltimate ####
    
    DataTemp = {MainKey: {'Search': SearchDic, 'Detail': DetailDic, 'Context': ContextDic, 'ContextExtension': ContextExtensionDicList, 'ContextUltimate': ContextUltimateDicList}}
    
    # DataTempJson 저장
    DataTempJsonPath = os.path.join(DataTempPath, f"DemandCollectionData_({datetime.now().strftime('%Y%m%d%H%M%S')})_{re.sub(r'[^가-힣a-zA-Z0-9]', '', Term)[:15]}.json")
    with open(DataTempJsonPath, 'w', encoding = 'utf-8') as DataTempJson:
        json.dump(DataTemp, DataTempJson, ensure_ascii = False, indent = 4)
        
    return DataTemp

################################
##### Process 진행 및 업데이트 #####
################################
## DemandCollectionDataDetail 프롬프트 요청 및 결과물 Json화
def DemandCollectionDataDetailProcessUpdate(projectName, email, InputDic, mode = "Master", MainKey = 'DemandSearchAnalysis', MessagesReview = "on"):
    print(f"< User: {email} | Project: {projectName} | DemandCollectionDataDetailUpdate 시작 >")
    ## TotalPublisherData 경로 설정
    TotalDemandCollectionDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1511_DemandCollectionData/s15111_TotalDemandCollectionData"
    TotalDemandCollectionDataJsonPath = os.path.join(TotalDemandCollectionDataPath, 'TotalDemandCollectionData.json')
    TotalDemandCollectionDataTempPath = os.path.join(TotalDemandCollectionDataPath, 'TotalDemandCollectionDataTemp')
    
    ## DemandCollectionDataDetailProcess
    InputCount = 1
    processCount = 1
    Input1 = InputDic['Input']
    Intention = InputDic['Intention']
    CheckCount = 0
    OutputDicList = []

    ## Process1: DemandCollectionDataDetail Response 생성
    DemandCollectionDataDetailResponse = ProcessResponse(projectName, email, "DemandCollectionDataDetail", Input1, processCount, InputCount, DemandCollectionDataDetailFilter, CheckCount, "OpenAI", mode, MessagesReview)
    OutputDicList.append(DemandCollectionDataDetailResponse)
    
    ## Process2: DemandCollectionDataContext Response 생성
    Input2 = DemandCollectionDataDetailResponse.copy()
    DeleteKeys = ['검색어완성도', '검색어피드백']
    for key in DeleteKeys:
        del Input2[key]
    
    DemandCollectionDataContextResponse = ProcessResponse(projectName, email, "DemandCollectionDataContext", Input2, processCount, InputCount, DemandCollectionDataContextFilter, CheckCount, "OpenAI", mode, MessagesReview)
    OutputDicList.append(DemandCollectionDataContextResponse)
    
    ## Process3: DemandCollectionDataExtensionChain Response 생성
    Input3 = DemandCollectionDataContextResponse
    
    DemandCollectionDataExtensionChainResponse = ProcessResponse(projectName, email, "DemandCollectionDataExtensionChain", Input3, processCount, InputCount, DemandCollectionDataExtensionChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
    OutputDicList.append(DemandCollectionDataExtensionChainResponse)
    
    if Intention in ["DemandUltimate", "SimilarityUltimate"]:
        ## Process4: DemandCollectionDataUltimateChain Response 생성
        Input4 = DemandCollectionDataContextResponse
        
        DemandCollectionDataUltimateChainResponse = ProcessResponse(projectName, email, "DemandCollectionDataUltimateChain", Input4, processCount, InputCount, DemandCollectionDataUltimateChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicList.append(DemandCollectionDataUltimateChainResponse)

    ## ProcessResponse 임시저장
    DataTemp = ProcessResponseTempSave(MainKey, InputDic, OutputDicList, TotalDemandCollectionDataTempPath)

    print(f"[ User: {email} | Project: {projectName} | DemandCollectionDataDetailUpdate 완료 ]\n")
    
    return DataTemp

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241204_개정교육과정초등교과별이해연수'
    #########################################################################
    
    DemandCollectionDataDetailProcessUpdate(ProjectName, email)