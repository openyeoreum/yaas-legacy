import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from datetime import datetime
from agent.a2_Solution.a22_Operation.a225_LoadLLM import OpenAI_LLMresponse, ANTHROPIC_LLMresponse

#####################
##### Input 생성 #####
#####################
## SearchResultScoreFilter InputList 생성
def SearchResultScoreFilterToInputList(Intention, Extension, DataTempJsonPath, MinScore=35e-7):
    ## 1) 원본 데이터를 로드
    with open(DataTempJsonPath, 'r', encoding='utf-8') as f:
        OrginSearchResult = json.load(f)
    SearchResult = OrginSearchResult['SearchResult']

    # Extension 전처리
    extension = [""] + Extension
    if extension == ["", ""]:
        extension = [""]

    ## 2) 함수: 주어진 MinScore로 필터링하여 InputList 생성
    def InputListGen(SearchResult, Intention, extension, min_score):
        InputListLocal = []
        
        for ext in extension:
            context_key = f"{Intention}Context{ext}"
            if context_key in SearchResult and SearchResult[context_key] is not None:
                Context = SearchResult[context_key]
                
                # (A) Context가 dict인 경우
                if isinstance(Context, dict):
                    # 필드가 존재하지 않을 경우를 대비하여 get 사용
                    CollectionAnalysis = Context.get('CollectionAnalysis')
                    ContextCollectionSearch = Context.get('CollectionSearch', [])
                    
                    # min_score 기준 필터
                    NewContextCollectionSearch = [
                        cs for cs in ContextCollectionSearch
                        if cs['Score'] >= min_score
                    ]
                    
                    # 반영
                    Context['CollectionSearch'] = NewContextCollectionSearch
                    
                    # 필터링 후 남은 결과가 있다면 InputDic 생성
                    if NewContextCollectionSearch:
                        SearchContextCollectionList = []
                        for newContextCollectionSearch in NewContextCollectionSearch:
                            Rank = newContextCollectionSearch['Rank']
                            Score = newContextCollectionSearch['Score']
                            Collection = newContextCollectionSearch['Collection']
                            SearchCollectionId = newContextCollectionSearch['CollectionId']
                            SearchContext = newContextCollectionSearch['CollectionAnalysis']['Context']
                            
                            SearchContextCollection = {
                                'Rank': Rank,
                                'Score': Score,
                                'Collection': Collection,
                                'CollectionId': SearchCollectionId,
                                'CollectionAnalysis': SearchContext
                            }
                            SearchContextCollectionList.append(SearchContextCollection)
                        
                        InputDic = {
                            'SearchId': None,
                            'Extension': ext,
                            'CollectionAnalysis': CollectionAnalysis,
                            'CollectionSearch': SearchContextCollectionList
                        }
                        InputListLocal.append(InputDic)
                
                # (B) Context가 list인 경우
                elif isinstance(Context, list):
                    for i, item in enumerate(Context):
                        CollectionAnalysis = item.get('CollectionAnalysis')
                        ContextCollectionSearch = item.get('CollectionSearch', [])
                        
                        # min_score 기준 필터
                        NewContextCollectionSearch = [
                            cs for cs in ContextCollectionSearch
                            if cs['Score'] >= min_score
                        ]
                        
                        # 반영
                        item['CollectionSearch'] = NewContextCollectionSearch
                        
                        # 필터링 후 남은 결과가 있다면 InputDic 생성
                        if NewContextCollectionSearch:
                            SearchContextCollectionList = []
                            for newContextCollectionSearch in NewContextCollectionSearch:
                                Rank = newContextCollectionSearch['Rank']
                                Score = newContextCollectionSearch['Score']
                                Collection = newContextCollectionSearch['Collection']
                                SearchCollectionId = newContextCollectionSearch['CollectionId']
                                SearchContext = newContextCollectionSearch['CollectionAnalysis']['Context']
                                
                                SearchContextCollection = {
                                    'Rank': Rank,
                                    'Score': Score,
                                    'Collection': Collection,
                                    'CollectionId': SearchCollectionId,
                                    'CollectionAnalysis': SearchContext
                                }
                                SearchContextCollectionList.append(SearchContextCollection)
                            
                            InputDic = {
                                'SearchId': i,
                                'Extension': ext,
                                'CollectionAnalysis': CollectionAnalysis,
                                'CollectionSearch': SearchContextCollectionList
                            }
                            InputListLocal.append(InputDic)
                            
        return InputListLocal

    ## 3) 1차 필터링 (MinScore=35e-7)
    InputList = InputListGen(SearchResult, Intention, extension, MinScore)

    # 전체 필터링된 Document 수(= CollectionSearch 수) 합계를 계산
    TotalCollections = sum(len(dic['CollectionSearch']) for dic in InputList)

    ## 4) 결과가 10개 미만이면, 상위 10번째 점수로 재필터링
    SearchQuality = "Good"
    if TotalCollections < 10:
        SearchQuality = "Bad"
        # (A) 전체 스코어를 수집하여 상위 10번째 점수를 구함
        with open(DataTempJsonPath, 'r', encoding='utf-8') as f:
            OrginSearchResult = json.load(f)
        SearchResult = OrginSearchResult['SearchResult']

        AllScores = []
        for ext in extension:
            context_key = f"{Intention}Context{ext}"
            if context_key in SearchResult and SearchResult[context_key] is not None:
                context = SearchResult[context_key]
                
                if isinstance(context, dict):
                    if 'CollectionSearch' in context:
                        for ColSearch in context['CollectionSearch']:
                            AllScores.append(ColSearch['Score'])
                elif isinstance(context, list):
                    for item in context:
                        if 'CollectionSearch' in item:
                            for ColSearch in item['CollectionSearch']:
                                AllScores.append(ColSearch['Score'])
        
        AllScores.sort(reverse = True)
        fallbackMinScore = AllScores[9]  # 상위 10번째

        # (B) 다시 필터링
        InputList = InputListGen(SearchResult, Intention, extension, fallbackMinScore)

    return OrginSearchResult, SearchResult, extension, InputList, SearchQuality

######################
##### Filter 조건 #####
######################
## Process1: DemandSearchCollectionDataFilter의 Filter(Error 예외처리)
def DemandSearchCollectionDataFilterFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "DemandSearchCollectionDataFilter, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '선별' not in OutputDic:
        return "DemandSearchCollectionDataFilter, JSONKeyError: '선별' 키가 누락되었습니다"

    # Error3: '선별' 데이터 타입 검증
    if not isinstance(OutputDic['선별'], list):
        return "DemandSearchCollectionDataFilter, JSON에서 오류 발생: '선별'은 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['선별']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"DemandSearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}]'은 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['데이터번호', '선별이유', '연결키워드', '상생키워드', '매칭점수']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"DemandSearchCollectionDataFilter, JSONKeyError: '선별[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 검증
        if not isinstance(item['데이터번호'], str):
            return f"DemandSearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 데이터번호'는 문자열이어야 합니다"

        if not isinstance(item['선별이유'], str):
            return f"DemandSearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 선별이유'는 문자열이어야 합니다"

        if not isinstance(item['연결키워드'], list) or not all(isinstance(kw, str) for kw in item['연결키워드']):
            return f"DemandSearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 연결키워드'는 문자열 리스트여야 합니다"

        if not isinstance(item['상생키워드'], list) or not all(isinstance(kw, str) for kw in item['상생키워드']):
            return f"DemandSearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 상생키워드'는 문자열 리스트여야 합니다"

        if (not isinstance(item['매칭점수'], (int, str))) or (isinstance(item['매칭점수'], str) and not item['매칭점수'].isdigit()) or (isinstance(item['매칭점수'], (int, str)) and (int(item['매칭점수']) < 0 or int(item['매칭점수']) > 100)):
            return f"DemandSearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 매칭점수'는 0-100 사이의 정수여야 합니다"
        else:
            item['매칭점수'] = int(item['매칭점수'])

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['선별']

## Process2: SupplySearchCollectionDataFilter의 Filter(Error 예외처리)
def SupplySearchCollectionDataFilterFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplySearchCollectionDataFilter, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '선별' not in OutputDic:
        return "SupplySearchCollectionDataFilter, JSONKeyError: '선별' 키가 누락되었습니다"

    # Error3: '선별' 데이터 타입 검증
    if not isinstance(OutputDic['선별'], list):
        return "SupplySearchCollectionDataFilter, JSON에서 오류 발생: '선별'은 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['선별']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"SupplySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}]'은 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['데이터번호', '선별이유', '연결키워드', '상생키워드', '매칭점수']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"SupplySearchCollectionDataFilter, JSONKeyError: '선별[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 검증
        if not isinstance(item['데이터번호'], str):
            return f"SupplySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 데이터번호'는 문자열이어야 합니다"

        if not isinstance(item['선별이유'], str):
            return f"SupplySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 선별이유'는 문자열이어야 합니다"

        if not isinstance(item['연결키워드'], list) or not all(isinstance(kw, str) for kw in item['연결키워드']):
            return f"SupplySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 연결키워드'는 문자열 리스트여야 합니다"

        if not isinstance(item['상생키워드'], list) or not all(isinstance(kw, str) for kw in item['상생키워드']):
            return f"SupplySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 상생키워드'는 문자열 리스트여야 합니다"

        if (not isinstance(item['매칭점수'], (int, str))) or (isinstance(item['매칭점수'], str) and not item['매칭점수'].isdigit()) or (isinstance(item['매칭점수'], (int, str)) and (int(item['매칭점수']) < 0 or int(item['매칭점수']) > 100)):
            return f"SupplySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 매칭점수'는 0-100 사이의 정수여야 합니다"
        else:
            item['매칭점수'] = int(item['매칭점수'])

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['선별']
    
## Process3: SimilaritySearchCollectionDataFilter의 Filter(Error 예외처리)
def SimilaritySearchCollectionDataFilterFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SimilaritySearchCollectionDataFilter, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 키 확인
    if '선별' not in OutputDic:
        return "SimilaritySearchCollectionDataFilter, JSONKeyError: '선별' 키가 누락되었습니다"

    # Error3: '선별' 데이터 타입 검증
    if not isinstance(OutputDic['선별'], list):
        return "SimilaritySearchCollectionDataFilter, JSON에서 오류 발생: '선별'은 리스트 형태여야 합니다"

    for idx, item in enumerate(OutputDic['선별']):
        # 각 항목이 딕셔너리인지 확인
        if not isinstance(item, dict):
            return f"SimilaritySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}]'은 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_keys = ['데이터번호', '선별이유', '연결키워드', '상생키워드', '매칭점수']
        missing_keys = [key for key in required_keys if key not in item]
        if missing_keys:
            return f"SimilaritySearchCollectionDataFilter, JSONKeyError: '선별[{idx}]'에 누락된 키: {', '.join(missing_keys)}"

        # 데이터 타입 검증
        if not isinstance(item['데이터번호'], str):
            return f"SimilaritySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 데이터번호'는 문자열이어야 합니다"

        if not isinstance(item['선별이유'], str):
            return f"SimilaritySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 선별이유'는 문자열이어야 합니다"

        if not isinstance(item['연결키워드'], list) or not all(isinstance(kw, str) for kw in item['연결키워드']):
            return f"SimilaritySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 연결키워드'는 문자열 리스트여야 합니다"

        if not isinstance(item['상생키워드'], list) or not all(isinstance(kw, str) for kw in item['상생키워드']):
            return f"SimilaritySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 상생키워드'는 문자열 리스트여야 합니다"

        if (not isinstance(item['매칭점수'], (int, str))) or (isinstance(item['매칭점수'], str) and not item['매칭점수'].isdigit()) or (isinstance(item['매칭점수'], (int, str)) and (int(item['매칭점수']) < 0 or int(item['매칭점수']) > 100)):
            return f"SimilaritySearchCollectionDataFilter, JSON에서 오류 발생: '선별[{idx}] > 매칭점수'는 0-100 사이의 정수여야 합니다"
        else:
            item['매칭점수'] = int(item['매칭점수'])

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic['선별']

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
def ProcessResponseTempSave(OutputDicList, OrginSearchResult, FilteredSearchResult, Intention, Extension, SearchQuality, FilteredDataTempJsonPath, TopScoreDataTempJsonPath):
    ## SearchResultData 재구성
    FilteredSearchResultData = {}
    ## 기본 데이터
    FilteredSearchResultData['SearchQuality'] = SearchQuality
    FilteredSearchResultData['SearchType'] = OrginSearchResult['SearchType']
    FilteredSearchResultData['SearchIntention'] = OrginSearchResult['SearchIntention']
    FilteredSearchResultData['SearchCollection'] = OrginSearchResult['SearchCollection']
    FilteredSearchResultData['SearchRange'] = OrginSearchResult['SearchRange']
    TopScoreFilteredSearchResultData = FilteredSearchResultData.copy()
    
    ## SearchResult 재구성
    SearchResult = {}
    ## SearchResult 기본 데이터
    SearchResult[f'{Intention}Search'] = FilteredSearchResult[f'{Intention}Search']
    SearchResult[f'{Intention}Detail'] = FilteredSearchResult[f'{Intention}Detail']
    TopScoreSearchResult = SearchResult.copy()
    
    ## 가장 높은 CollectionSearchTotalScore를 가진 Context 저장용 변수
    TopScoreContext = None
    TopScore = float('-inf')

    ## Context, ContextExpertise, ContextUltimate 재구성
    for ext in Extension:
        IntentionContext = FilteredSearchResult[f'{Intention}Context{ext}']
        if isinstance(IntentionContext, dict):
            IntentionContext['CollectionSearch'] = []
            for OutputDic in OutputDicList:
                if OutputDic['SearchResultKey'] == f"{Intention}Context{ext}":
                    IntentionContext['CollectionSearch'] += OutputDic['CollectionSearch']
                    CollectionSearchScore = [CollectionSearch['TotalScore'] for CollectionSearch in IntentionContext['CollectionSearch']]
                    IntentionContext['CollectionSearchTotalScore'] = sum(CollectionSearchScore)

                    ## 최상위 점수를 가진 CollectionSearch 비교
                    if IntentionContext['CollectionSearchTotalScore'] > TopScore:
                        TopScore = IntentionContext['CollectionSearchTotalScore']
                        TopScoreContext = {'Key': f'{Intention}Context{ext}', 'Value': IntentionContext}
        
        elif isinstance(IntentionContext, list):
            for i in range(len(IntentionContext)):
                IntentionContext[i]['CollectionSearch'] = []
                for OutputDic in OutputDicList:
                    if OutputDic['SearchResultKey'] == f"{Intention}Context{ext}" and OutputDic['CollectionSearchId'] == i:
                        IntentionContext[i]['CollectionSearch'] += OutputDic['CollectionSearch']
                        CollectionSearchScore = [CollectionSearch['TotalScore'] for CollectionSearch in IntentionContext[i]['CollectionSearch']]
                        IntentionContext[i]['CollectionSearchTotalScore'] = sum(CollectionSearchScore)

                        ## 최상위 점수를 가진 CollectionSearch 비교
                        if IntentionContext[i]['CollectionSearchTotalScore'] > TopScore:
                            TopScore = IntentionContext[i]['CollectionSearchTotalScore']
                            TopScoreContext = {'Key': f'{Intention}Context{ext}', 'Value': IntentionContext[i]}

        SearchResult[f'{Intention}Context{ext}'] = IntentionContext
    
    
    FilteredSearchResultData['SearchResult'] = SearchResult

    ## 필터링된 검색 결과 저장
    with open(FilteredDataTempJsonPath, 'w', encoding='utf-8') as SearchResultJson:
        json.dump(FilteredSearchResultData, SearchResultJson, ensure_ascii = False, indent = 4)

    ## 가장 높은 TotalScore를 가진 CollectionSearch 저장
    if TopScoreContext:
        TopScoreSearchResult[TopScoreContext['Key']] = TopScoreContext['Value']
        TopScoreFilteredSearchResultData['SearchResult'] = TopScoreSearchResult
        with open(TopScoreDataTempJsonPath, 'w', encoding='utf-8') as TopScoreJson:
            json.dump(TopScoreFilteredSearchResultData, TopScoreJson, ensure_ascii = False, indent = 4)

    return TopScoreFilteredSearchResultData

################################
##### Process 진행 및 업데이트 #####
################################
## InputDic의 Text화
def InputDicToText(InputDic, Intention):
    def CollectionAnalysisText(CollectionAnalysis, Intention):
        ## CollectionAnalysis의 Text화
        SummaryMark = "- 요약정보 -\n"
        Summary = f"요약: {CollectionAnalysis['Summary']}\n"
        KeyWord = f"키워드: {', '.join(CollectionAnalysis['KeyWord'])}\n\n"
        SummaryText = SummaryMark + Summary + KeyWord
        
        DemandText = ''
        if Intention in ["Demand", "Similarity"]:
            DemandMark = "- 수요정보 -\n"
            DemandNeedsSentence = f"내용설명: {CollectionAnalysis['Demand']['Needs']['Sentence']}\n"
            DemandNeedsKeyWord = f"내용키워드: {', '.join(CollectionAnalysis['Demand']['Needs']['KeyWord'])}\n\n"
            DemandPurposeSentence = f"목적설명: {CollectionAnalysis['Demand']['Purpose']['Sentence']}\n"
            DemandPurposeKeyWord = f"목적키워드: {', '.join(CollectionAnalysis['Demand']['Purpose']['KeyWord'])}\n\n"
            DemandQuestionSentence = f"질문설명: {CollectionAnalysis['Demand']['Question']['Sentence']}\n"
            DemandQuestionKeyWord = f"질문키워드: {', '.join(CollectionAnalysis['Demand']['Question']['KeyWord'])}\n\n"
            DemandText = DemandMark + DemandNeedsSentence + DemandNeedsKeyWord + DemandPurposeSentence + DemandPurposeKeyWord + DemandQuestionSentence + DemandQuestionKeyWord
        
        SupplyText = ''
        if Intention in ["Supply", "Similarity"]:
            SupplyMark = "- 공급정보 -\n"
            SupplySatisfySentence = f"내용설명: {CollectionAnalysis['Supply']['Satisfy']['Sentence']}\n"
            SupplySatisfyKeyWord = f"내용키워드: {', '.join(CollectionAnalysis['Supply']['Satisfy']['KeyWord'])}\n\n"
            SupplySupportSentence = f"목표설명: {CollectionAnalysis['Supply']['Support']['Sentence']}\n"
            SupplySupportKeyWord = f"목표키워드: {', '.join(CollectionAnalysis['Supply']['Support']['KeyWord'])}\n\n"
            SupplySolutionSentence = f"해결책설명: {CollectionAnalysis['Supply']['Solution']['Sentence']}\n"
            SupplySolutionKeyWord = f"해결책키워드: {', '.join(CollectionAnalysis['Supply']['Solution']['KeyWord'])}\n\n"
            SupplyText = SupplyMark + SupplySatisfySentence + SupplySatisfyKeyWord + SupplySupportSentence + SupplySupportKeyWord + SupplySolutionSentence + SupplySolutionKeyWord
        
        CollectionAnalysisText = SummaryText + DemandText + SupplyText
        
        return CollectionAnalysisText
    
    ## CollectionAnalysis_Text
    CollectionAnalysis_Text = f"(매칭대상)\n{CollectionAnalysisText(InputDic['CollectionAnalysis'], Intention)}"
    
    ## CollectionSearch_Text
    CollectionSearch_Text = ''
    for CollectionSearch in InputDic['CollectionSearch']:
        CollectionSearchMark = f"\n(데이터번호: {CollectionSearch['CollectionId']})\n"
        CollectionSearch_Text += CollectionSearchMark + CollectionAnalysisText(CollectionSearch['CollectionAnalysis'], Intention)
        
    return CollectionAnalysis_Text, CollectionSearch_Text

## InputDic의 OutputDic화
def InputDicToOutputDic(InputDic, Response, Intention):
    CollectionSearchDicList = []
    
    for response in Response:
        for CollectionSearch in InputDic['CollectionSearch']:
            if int(CollectionSearch['CollectionId']) == int(response['데이터번호']):
                CollectionSearchDic = {
                    'TotalRank': CollectionSearch['Rank'],
                    'TotalScore': CollectionSearch['Score'] * response['매칭점수'] / 100,
                    'SearchScore': CollectionSearch['Score'],
                    'MatchingScore': response['매칭점수'],
                    'MatchingReason': response['선별이유'],
                    'MatchingKeyword': response['연결키워드'],
                    'ValueKeyword': response['상생키워드'],
                    'Collection': CollectionSearch['Collection'],
                    'CollectionId': response['데이터번호'],
                    'CollectionAnalysis': CollectionSearch['CollectionAnalysis']
                }
                CollectionSearchDicList.append(CollectionSearchDic)
    
    # MatchingScore 기준으로 정렬 (내림차순)
    CollectionSearchDicList.sort(key = lambda x: x['MatchingScore'], reverse = True)
    
    # Rank 재부여
    for index, item in enumerate(CollectionSearchDicList, start = 1):
        item['TotalRank'] = index
    
    OutputDic = {
        'SearchResultKey': f"{Intention}Context{InputDic['Extension']}",
        'CollectionSearchId': InputDic['SearchId'],
        'CollectionSearch': CollectionSearchDicList
    }
    
    return OutputDic

## SearchCollectionData 프롬프트 요청 및 결과물 Json화
def SearchCollectionDataFilterProcessUpdate(projectName, email, Intention, Extension, DataTempJsonPath, mode = "Master", MainKey = 'SearchCollectionDataFilter', MessagesReview = "on"):
    print(f"< User: {email} | Filter: {projectName} | SearchCollectionDataFilterUpdate 시작 >")
    
    ## TotalPublisherData 경로 설정
    FilteredDataTempJsonPath = DataTempJsonPath.replace("].json", "]_Filtered.json")
    TopScoreDataTempJsonPath = DataTempJsonPath.replace("].json", "]_TopScore.json")
    
    ## SearchCollectionDataDetailProcess
    OrginSearchResult, FilteredSearchResult, extension, InputList, SearchQuality = SearchResultScoreFilterToInputList(Intention, Extension, DataTempJsonPath)

    ## Mark 설정
    if Intention == "Demand":
        AnalysisMark = "수요"
        SearchMark = "공급"
    elif Intention == "Supply":
        AnalysisMark = "공급"
        SearchMark = "수요"
    elif Intention == "Similarity":
        AnalysisMark = "유사"
        SearchMark = "유사"

    ## Count 계산
    InputCount = len(InputList)
    processCount = 1
    CheckCount = 0
    ## Process 진행
    OutputDicList = []
    for InputDic in InputList:
        Extension = InputDic['Extension']
        
        # InputText 생성
        CollectionAnalysisText, CollectionSearchText = InputDicToText(InputDic, Intention)
        Input = f"[{AnalysisMark} 매칭대상]\n\n{CollectionAnalysisText}\n[{SearchMark} 검색결과]\n\n{CollectionSearchText}"

        ## Process1: DemandSearchCollectionDataFilter Response 생성
        if Intention == "Demand":
            Process = "DemandSearchCollectionDataFilter"
            Response = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, DemandSearchCollectionDataFilterFilter, CheckCount, "OpenAI", mode, MessagesReview)
            OutputDic = InputDicToOutputDic(InputDic, Response, Intention)
            processCount += 1
    
        ## Process2: SupplySearchCollectionDataFilter Response 생성
        if Intention == "Supply":
            Process = "SupplySearchCollectionDataFilter"
            Response = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, SupplySearchCollectionDataFilterFilter, CheckCount, "OpenAI", mode, MessagesReview)
            OutputDic = InputDicToOutputDic(InputDic, Response, Intention)
            processCount += 1
            
        ## Process3: SimilaritySearchCollectionDataFilter Response 생성
        if Intention == "Similarity":
            Process = "SimilaritySearchCollectionDataFilter"
            Response = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, SimilaritySearchCollectionDataFilterFilter, CheckCount, "OpenAI", mode, MessagesReview)
            OutputDic = InputDicToOutputDic(InputDic, Response, Intention)
            processCount += 1
            
        OutputDicList.append(OutputDic)

    ## ProcessResponse 임시저장
    TopScoreFilteredSearchResultData = ProcessResponseTempSave(OutputDicList, OrginSearchResult, FilteredSearchResult, Intention, extension, SearchQuality, FilteredDataTempJsonPath, TopScoreDataTempJsonPath)

    print(f"[ User: {email} | Filter: {projectName} | SearchCollectionDataUpdate 완료 ]")
    
    return TopScoreFilteredSearchResultData

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "오디오북제작자동화솔루션의새로운활용"
    Search = "나는 오디오북 자동 제작 AI솔루션 대표입니다. 우리회사의 오디오북 솔루션은 100권의 고품질 오디오북을 탄생시키고 의뢰인들을 만족시킬 만큼 성능과 효율성이 뛰어납니다. 오디오북 솔루션은 고품질 TTS, 음악, 효과음, 스크립트 제작 자동화의 기능을 모두 담고 있습니다. 나는 이 오디오북 솔루션의 새로운 활용방안을 고민하고 있습니다. 좋은 해결책을 얻고 싶습니다." # Search: SearchTerm, Match: PublisherData_(Id)
    Intention = "Similarity" # Demand, Supply, Similarity ...
    Extension = ["Expertise", "Ultimate"] # Expertise, Ultimate, Detail, Rethink ...
    Collection = "Book" # Entire, Target, Trend, Publisher, Book ...
    Range = 10 # 10-100
    MessagesReview = "on" # on, off
    #########################################################################
    DataTempJsonPath = '/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1513_SearchResultData/s15131_TotalSearchResultData/TotalSearchResultDataTemp/SearchResultData_(20250123125342)_[250121_테스트_Similarity: 나는 오디오북 자동 제작 AI솔루션 등 204자].json'
    FilteredSearchResultData = SearchCollectionDataFilterProcessUpdate(projectName, email, Intention, Extension, DataTempJsonPath)