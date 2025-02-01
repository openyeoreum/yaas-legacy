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
## Process1~3: SearchResult 불러오기
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
    with open(LastestSearchResultPath, "r", encoding = "utf-8") as SearchResult_json:
        SearchResultJson = json.load(SearchResult_json)
    with open(LastestTopScoreSearchResultPath, "r", encoding = "utf-8") as TopScoreSearchResult_json:
        TopScoreSearchResultJson = json.load(TopScoreSearchResult_json)
    

    return SearchResultJson, TopScoreSearchResultJson

## Process1, 3: DemandScriptPlan의 Input
def DemandCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, ProjectName, Intention):
    SearchResultJson, TopScoreSearchResultJson = LoadSearchResult(TotalSearchResultDataTempPath, ProjectName, Intention)
    
    SearchResult = SearchResultJson['SearchResult']
    Term = SearchResult[f'{Intention}Search']['Term']
    NormalDetail = SearchResult[f'{Intention}Detail']['Summary']
    
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
        
        FrontInput = f"[최초의도]\n{Term}\n{NormalDetail}\n\n[핵심목적]\n일반: {NormalSummary}\n심화: {AdvancedSummary}\n\n[분야]\n일반: {', '.join(NormalKeyWord)}\n심화: {', '.join(AdvancedKeyWord)}\n\n"
    
        BackInput = f"[필요내용]\n일반: {NormalDemandNeedsSentence}\n심화: {AdvancedDemandNeedsSentence}\n\n[필요내용-키워드]\n일반: {', '.join(NormalDemandNeedsKeyWord)}\n심화: {', '.join(AdvancedDemandNeedsKeyWord)}\n\n[필요목표]\n일반: {NormalDemandPurposeSentence}\n심화: {AdvancedDemandPurposeSentence}\n\n[필요목표-키워드]\n일반: {', '.join(NormalDemandPurposeKeyWord)}\n심화: {', '.join(AdvancedDemandPurposeKeyWord)}\n\n[필요질문]\n일반: {NormalDemandQuestionSentence}\n심화: {AdvancedDemandQuestionSentence}\n\n[필요질문-키워드]\n일반: {', '.join(NormalDemandQuestionKeyWord)}\n심화: {', '.join(AdvancedDemandQuestionKeyWord)}"

    else:
        FrontInput = f"[최초의도]\n{Term}\n{NormalDetail}\n\n[핵심목적]\n{NormalSummary}\n\n[분야]\n{', '.join(NormalKeyWord)}\n\n"

        BackInput = f"[필요내용]\n{NormalDemandNeedsSentence}\n\n[필요내용-키워드]\n{', '.join(NormalDemandNeedsKeyWord)}\n\n[필요목표]\n{NormalDemandPurposeSentence}\n\n[필요목표-키워드]\n{', '.join(NormalDemandPurposeKeyWord)}\n\n[필요질문]\n{NormalDemandQuestionSentence}\n\n[필요질문-키워드]\n{', '.join(NormalDemandQuestionKeyWord)}"

    ## Intention에 따라 Input 결정
    if Intention == 'Demand':
        Input = FrontInput + BackInput
    elif Intention == 'Similarity':
        Input = BackInput

    return Input

## Process2, 3: SupplyScriptPlan의 Input
def SupplyCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, ProjectName, Intention):
    SearchResultJson, TopScoreSearchResultJson = LoadSearchResult(TotalSearchResultDataTempPath, ProjectName, Intention)
    
    SearchResult = SearchResultJson['SearchResult']
    Term = SearchResult[f'{Intention}Search']['Term']
    NormalDetail = SearchResult[f'{Intention}Detail']['Summary']
    
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
    
        Input = f"[최초의도]\n{Term}\n{NormalDetail}\n\n[핵심솔루션]\n일반: {NormalSummary}\n심화: {AdvancedSummary}\n\n[분야]\n일반: {', '.join(NormalKeyWord)}\n심화: {', '.join(AdvancedKeyWord)}\n\n[제안내용]\n일반: {NormalSupplySatisfySentence}\n심화: {AdvancedSupplySatisfySentence}\n\n[제안내용-키워드]\n일반: {', '.join(NormalSupplySatisfyKeyWord)}\n심화: {', '.join(AdvancedSupplySatisfyKeyWord)}\n\n[제안할목표]\n일반: {NormalSupplySupportSentence}\n심화: {AdvancedSupplySupportSentence}\n\n[제안할목표-키워드]\n일반: {', '.join(NormalSupplySupportKeyWord)}\n심화: {', '.join(AdvancedSupplySupportKeyWord)}\n\n[제안할해결책]\n일반: {NormalSupplySolutionSentence}\n심화: {AdvancedSupplySolutionSentence}\n\n[제안할해결책-키워드]\n일반: {', '.join(NormalSupplySolutionKeyWord)}\n심화: {', '.join(AdvancedSupplySolutionKeyWord)}"

    else:
        Input = f"[최초의도]\n{Term} {NormalDetail}\n\n[핵심솔루션]\n{NormalSummary}\n\n[분야]\n{', '.join(NormalKeyWord)}\n\n[제안내용]\n{NormalSupplySatisfySentence}\n\n[제안내용-키워드]\n{', '.join(NormalSupplySatisfyKeyWord)}\n\n[제안할목표]\n{NormalSupplySupportSentence}\n\n[제안할목표-키워드]\n{', '.join(NormalSupplySupportKeyWord)}\n\n[제안할해결책]\n{NormalSupplySolutionSentence}\n\n[제안할해결책-키워드]\n{', '.join(NormalSupplySolutionKeyWord)}"

    return Input

## Process5: TitleAndIndexGen의 InputList
def EditToTitleAndIndexGenInputList(ScriptEditPath, BeforeProcess):
    with open(ScriptEditPath, "r", encoding = "utf-8") as ScriptEditJson:
        ScriptEditList = json.load(ScriptEditJson)[BeforeProcess]
    
    InputList = []
    for i, ScriptEdit in enumerate(ScriptEditList):
        Background = ScriptEdit['Background']
        Subject = ScriptEdit['Subject']
        Range = ScriptEdit['Range']
        ConceptKeyword = ScriptEdit['ConceptKeyword']
        TargetKeyword = ScriptEdit['TargetKeyword']
        SupplyValueSentence = ScriptEdit['Supply']['Value']['Sentence']
        SupplyValueKeyword = ScriptEdit['Supply']['Value']['KeyWord']
        SupplyPointSentence = ScriptEdit['Supply']['Points']['Sentence']
        SupplyPointKeyword = ScriptEdit['Supply']['Points']['KeyWord']
        SupplyVisionSentence = ScriptEdit['Supply']['Vision']['Sentence']
        SupplyVisionKeyword = ScriptEdit['Supply']['Vision']['KeyWord']
        
        Input = f"[배경]\n{Background}\n\n[주제]\n{Subject}\n\n[범위]\n{Range}\n\n[개념키워드]\n{', '.join(ConceptKeyword)}\n\n[독자키워드]\n{', '.join(TargetKeyword)}\n\n[글이전해줄핵심가치]\n{SupplyValueSentence}\n\n[글이전해줄핵심가치-키워드]\n{', '.join(SupplyValueKeyword)}\n\n[글이전해줄핵심포인트들]\n{SupplyPointSentence}\n\n[글이전해줄핵심포인트들-키워드]\n{', '.join(SupplyPointKeyword)}\n\n[글이전해줄핵심비전]\n{SupplyVisionSentence}\n\n[글이전해줄핵심비전-키워드]\n{', '.join(SupplyVisionKeyword)}"
        
        InputList.append({'Id': i+1, 'Input': Input})
    
    return InputList

## Process7: SummaryOfIndexGen의 Input
def EditToSummaryOfIndexGenInputList(ScriptEditPath, BeforeProcess):
    with open(ScriptEditPath, "r", encoding = "utf-8") as ScriptEditJson:
        ScriptEditList = json.load(ScriptEditJson)[BeforeProcess]
        
    InputList = []
    for i, ScriptEdit in enumerate(ScriptEditList):
        Type = ScriptEdit['Type']
        TitleType = ScriptEdit['TitleType']
        Title = ScriptEdit['Title']
        SubTitle = ScriptEdit['SubTitle']
        MainIndex = []
        for MainIndexDic in ScriptEdit['MainIndex']:
            MainIndex.append(f"순번: {MainIndexDic['IndexId']}\n메인목차: {MainIndexDic['Index']}")
        
        ## MainIndex에서 2개씩 메인목차 부분에 이번에 진행할 서브목차 표기
        SelectedMainIndexId = []
        InputId = 1
        for j in range(len(MainIndex)):
            SelectedMainIndexId.append(j + 1)
            if j % 2 != 0:
                mainIndex = MainIndex.copy()
                MainIndexText = ''
                for k in range(len(MainIndex)):
                    if k + 1 in SelectedMainIndexId:
                        mainIndex[k] = MainIndex[k] + '\n서브목차: * 지금 작성할 서브목차 *\n\n'
                    else:
                        mainIndex[k] = MainIndex[k] + '\n\n'
                    MainIndexText += mainIndex[k]
                        
            
                Input = f"[글쓰기형태]\n{Type}\n\n[제목부제형태]\n{TitleType}\n\n[제목]\n{Title}\n\n[부제]\n{SubTitle}\n\n[메인목차]\n{MainIndexText}"
                
                if SelectedMainIndexId[0] == 1:
                    Caution = f"\n\n※ 작성사항 ※\n- 첫번째 작업입니다.\n- 따라서, <목차별내용요약.json>의 구조대로 순번 {SelectedMainIndexId[0]}, {SelectedMainIndexId[1]}번을 작성해 주세요.\n\n"
                else:
                    Caution = f"\n\n※ 작성사항 ※\n- 순번 1~{SelectedMainIndexId[0] - 1} 까지는 작업이 완료되었습니다.\n- 따라서, 아래의 순번 {SelectedMainIndexId[0] - 2}, {SelectedMainIndexId[0] - 1}번과 내용이 자연스럽게 이어지도록 <목차별내용요약.json>의 구조대로 순번 {SelectedMainIndexId[0]}, {SelectedMainIndexId[1]}번을 작성해 주세요.\n\n"

                InputList.append({'Id': InputId, 'Input': Input, 'Caution': Caution})
                SelectedMainIndexId = []
                InputId += 1
    
    return InputList

## Process4: ScriptIntroductionGenGen의 Input

## Process5: ShortScriptGen의 Input

## Process6: ShortScriptMerge의 Input

## Process7: LongScriptGen의 Input

## Process8: LongScriptEdit의 Input

######################
##### Filter 조건 #####
######################
## Process1~3: ScriptPlan의 Filter(Error 예외처리)
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

## Process4: ScriptPlanFeedback의 Filter(Error 예외처리)
def ScriptPlanFeedbackFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "ScriptPlanFeedback, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: 최상위 필수 키 확인
    required_top_keys = ['배경', '주제', '범위', '개념키워드', '독자키워드', '가치']
    missing_top_keys = [key for key in required_top_keys if key not in OutputDic]
    if missing_top_keys:
        return f"ScriptPlanFeedback, JSONKeyError: 누락된 최상위 키: {', '.join(missing_top_keys)}"

    # Error3: 최상위 키 데이터 타입 검증
    if not isinstance(OutputDic['배경'], str):
        return "ScriptPlanFeedback, JSON에서 오류 발생: '배경'은 문자열이어야 합니다"
    if not isinstance(OutputDic['주제'], str):
        return "ScriptPlanFeedback, JSON에서 오류 발생: '주제'은 문자열이어야 합니다"
    if not isinstance(OutputDic['범위'], str):
        return "ScriptPlanFeedback, JSON에서 오류 발생: '범위'은 문자열이어야 합니다"
    if not isinstance(OutputDic['개념키워드'], list) or not all(isinstance(item, str) for item in OutputDic['개념키워드']):
        return "ScriptPlanFeedback, JSON에서 오류 발생: '개념키워드'는 문자열 리스트여야 합니다"
    if not isinstance(OutputDic['독자키워드'], list) or not all(isinstance(item, str) for item in OutputDic['독자키워드']):
        return "ScriptPlanFeedback, JSON에서 오류 발생: '독자키워드'는 문자열 리스트여야 합니다"

    # Error4: '가치' 키 구조 검증
    if not isinstance(OutputDic['가치'], dict):
        return "ScriptPlanFeedback, JSON에서 오류 발생: '가치'는 딕셔너리 형태여야 합니다"

    # '가치' 내부 필수 키 확인
    required_sub_keys = ['글이전해줄핵심가치', '글이전해줄핵심포인트들', '글이전해줄핵심비전']
    for sub_key in required_sub_keys:
        if sub_key not in OutputDic['가치']:
            return f"ScriptPlanFeedback, JSONKeyError: '가치'에 누락된 키: {sub_key}"

        sub_item = OutputDic['가치'][sub_key]

        # 각 항목은 딕셔너리 형태여야 함
        if not isinstance(sub_item, dict):
            return f"ScriptPlanFeedback, JSON에서 오류 발생: '가치 > {sub_key}'는 딕셔너리 형태여야 합니다"

        # 내부 필수 키 확인
        required_detail_keys = ['설명', '키워드']
        missing_detail_keys = [key for key in required_detail_keys if key not in sub_item]
        if missing_detail_keys:
            return f"ScriptPlanFeedback, JSONKeyError: '가치 > {sub_key}'에 누락된 키: {', '.join(missing_detail_keys)}"

        # 데이터 타입 검증
        if not isinstance(sub_item['설명'], str):
            return f"ScriptPlanFeedback, JSON에서 오류 발생: '가치 > {sub_key} > 설명'은 문자열이어야 합니다"
        if not isinstance(sub_item['키워드'], list) or not all(isinstance(item, str) for item in sub_item['키워드']):
            return f"ScriptPlanFeedback, JSON에서 오류 발생: '가치 > {sub_key} > 키워드'는 문자열 리스트여야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic

## Process5~6: TitleAndIndexGen의 Filter(Error 예외처리)
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

        if (not isinstance(item['순번'], (int, str))) or (isinstance(item['순번'], str) and not item['순번'].isdigit()):
            return f"TitleAndIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 순번'은 정수 또는 숫자로 된 문자열이어야 합니다"

        if not isinstance(item['목차'], str):
            return f"TitleAndIndexGen, JSON에서 오류 발생: '메인목차[{idx}] > 목차'는 문자열이어야 합니다"

    # 모든 조건을 만족하면 JSON 반환
    return OutputDic

## Process7: SummaryOfIndexGen의 Filter(Error 예외처리)
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
    return OutputDic['메인목차']

## Process8: SummaryOfIndexGenFeedback의 Filter(Error 예외처리)
def SummaryOfIndexGenFeedback(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SummaryOfIndexGen, JSONDecode에서 오류 발생: JSONDecodeError"

    # 각 항목이 딕셔너리인지 확인
    if not isinstance(OutputDic, dict):
        return f"SummaryOfIndexGen, JSON에서 오류 발생: 'OutputDic'은 딕셔너리 형태여야 합니다"

    # 필수 키 확인
    required_main_keys = ['순번', '메인목차', '서브목차', '전체요약']
    missing_main_keys = [key for key in required_main_keys if key not in OutputDic]
    if missing_main_keys:
        return f"SummaryOfIndexGen, JSONKeyError: 'OutputDic'에 누락된 키: {', '.join(missing_main_keys)}"

    # 데이터 타입 검증
    if (not isinstance(OutputDic['순번'], (int, str))) or (isinstance(OutputDic['순번'], str) and not OutputDic['순번'].isdigit()):
        return f"SummaryOfIndexGen, JSON에서 오류 발생: '순번'은 숫자로 된 문자열이어야 합니다"
    if not isinstance(OutputDic['메인목차'], str):
        return f"SummaryOfIndexGen, JSON에서 오류 발생: '메인목차'는 문자열이어야 합니다"
    if not isinstance(OutputDic['전체요약'], str):
        return f"SummaryOfIndexGen, JSON에서 오류 발생: '전체요약'은 문자열이어야 합니다"

    # Error4: '서브목차' 리스트 검증
    if not isinstance(OutputDic['서브목차'], list):
        return f"SummaryOfIndexGen, JSON에서 오류 발생: '서브목차'는 리스트 형태여야 합니다"

    if len(OutputDic['서브목차']) < 5:
        return f"SummaryOfIndexGen, JSON에서 오류 발생: '서브목차'는 최소 5개 이상의 항목을 포함해야 합니다"

    for sub_idx, sub_item in enumerate(OutputDic['서브목차']):
        # 각 서브목차가 딕셔너리인지 확인
        if not isinstance(sub_item, dict):
            return f"SummaryOfIndexGen, JSON에서 오류 발생: '서브목차[{sub_idx}]'은 딕셔너리 형태여야 합니다"

        # 필수 키 확인
        required_sub_keys = ['서브목차', '키워드', '요약']
        missing_sub_keys = [key for key in required_sub_keys if key not in sub_item]
        if missing_sub_keys:
            return f"SummaryOfIndexGen, JSONKeyError: '서브목차[{sub_idx}]'에 누락된 키: {', '.join(missing_sub_keys)}"

        # 데이터 타입 검증
        if not isinstance(sub_item['서브목차'], str):
            return f"SummaryOfIndexGen, JSON에서 오류 발생: '서브목차[{sub_idx}] > 서브목차'는 문자열이어야 합니다"
        if not isinstance(sub_item['키워드'], list) or not all(isinstance(kw, str) for kw in sub_item['키워드']):
            return f"SummaryOfIndexGen, JSON에서 오류 발생: '서브목차[{sub_idx}] > 키워드'는 문자열 리스트여야 합니다"
        if not isinstance(sub_item['요약'], str):
            return f"SummaryOfIndexGen, JSON에서 오류 발생: '서브목차[{sub_idx}] > 요약'은 문자열이어야 합니다"

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
            ScriptEditFrame = json.load(DataFrameJson)
        
        ## InputCount 및 DataFrameCompletion 확인
        InputCount = ScriptEditFrame[0]['InputCount']
        DataFrameCompletion = ScriptEditFrame[0]['Completion']
        
        return InputCount, DataFrameCompletion

## Process1~3: ScriptPlanProcess DataFrame 저장
def ScriptPlanProcessDataFrameSave(ProjectName, BookScriptGenDataFramePath, ProjectDataFrameScriptPalnPath, ScriptPlanResponse, Process, InputCount, TotalInputCount):
    ## ScriptPlanFrame 불러오기
    if os.path.exists(ProjectDataFrameScriptPalnPath):
        ScriptPlanFramePath = ProjectDataFrameScriptPalnPath
    else:
        ScriptPlanFramePath = os.path.join(BookScriptGenDataFramePath, "b5312-01_ScriptPlanFrame.json") 
    with open(ScriptPlanFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        ScriptPlanFrame = json.load(DataFrameJson)
    
    ## ScriptPlanFrame 업데이트
    ScriptPlanFrame[0]['ProjectName'] = ProjectName
    ScriptPlanFrame[0]['TaskName'] = Process
    
    ## ScriptPlanFrame 첫번째 데이터 프레임 복사
    ScriptPlan = ScriptPlanFrame[1][0].copy()
    ScriptPlan['PlanId'] = InputCount
    ScriptPlan['Background'] = ScriptPlanResponse['배경']
    ScriptPlan['Subject'] = ScriptPlanResponse['주제']
    ScriptPlan['Range'] = ScriptPlanResponse['범위']
    ScriptPlan['ConceptKeyword'] = ScriptPlanResponse['개념키워드']
    ScriptPlan['TargetKeyword'] = ScriptPlanResponse['독자키워드']

    ScriptPlan['Supply']['Value']['Sentence'] = ScriptPlanResponse['가치']['글이전해줄핵심가치']['설명']
    ScriptPlan['Supply']['Value']['KeyWord'] = ScriptPlanResponse['가치']['글이전해줄핵심가치']['키워드']
    ScriptPlan['Supply']['Value']['Weight'] = ScriptPlanResponse['가치']['글이전해줄핵심가치']['중요도']

    ScriptPlan['Supply']['Points']['Sentence'] = ScriptPlanResponse['가치']['글이전해줄핵심포인트들']['설명']
    ScriptPlan['Supply']['Points']['KeyWord'] = ScriptPlanResponse['가치']['글이전해줄핵심포인트들']['키워드']
    ScriptPlan['Supply']['Points']['Weight'] = ScriptPlanResponse['가치']['글이전해줄핵심포인트들']['중요도']

    ScriptPlan['Supply']['Vision']['Sentence'] = ScriptPlanResponse['가치']['글이전해줄핵심비전']['설명']
    ScriptPlan['Supply']['Vision']['KeyWord'] = ScriptPlanResponse['가치']['글이전해줄핵심비전']['키워드']
    ScriptPlan['Supply']['Vision']['Weight'] = ScriptPlanResponse['가치']['글이전해줄핵심비전']['중요도']

    ScriptPlan['Weight'] = ScriptPlanResponse['정보의질']
    
    ## ScriptPlanFrame 데이터 프레임 업데이트
    ScriptPlanFrame[1].append(ScriptPlan)
    
    ## ScriptPlanFrame ProcessCount 및 Completion 업데이트
    ScriptPlanFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        ScriptPlanFrame[0]['Completion'] = 'Yes'
    
    ## ScriptPlanFrame 저장
    with open(ProjectDataFrameScriptPalnPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(ScriptPlanFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process5: TitleAndIndexGenProcess DataFrame 저장
def TitleAndIndexGenProcessDataFrameSave(ProjectName, BookScriptGenDataFramePath, ProjectDataFrameTitleAndIndexPath, TitleAndIndexGenResponse, Process, InputCount, TotalInputCount):
    ## TitleAndIndexGenFrame 불러오기
    if os.path.exists(ProjectDataFrameTitleAndIndexPath):
        TitleAndIndexFramePath = ProjectDataFrameTitleAndIndexPath
    else:
        TitleAndIndexFramePath = os.path.join(BookScriptGenDataFramePath, "b5312-02_TitleAndIndexFrame.json")
    with open(TitleAndIndexFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        TitleAndIndexFrame = json.load(DataFrameJson)
        
    ## TitleAndIndexFrame 업데이트
    TitleAndIndexFrame[0]['ProjectName'] = ProjectName
    TitleAndIndexFrame[0]['TaskName'] = Process
    
    ## TitleAndIndexFrame 첫번째 데이터 프레임 복사
    TitleAndIndex = TitleAndIndexFrame[1][0].copy()
    TitleAndIndex['MainIndexId'] = InputCount
    TitleAndIndex['Type'] = TitleAndIndexGenResponse['글쓰기형태']
    TitleAndIndex['TitleType'] = TitleAndIndexGenResponse['제목부제형태']
    TitleAndIndex['Title'] = TitleAndIndexGenResponse['제목']
    TitleAndIndex['SubTitle'] = TitleAndIndexGenResponse['부제']
    TitleAndIndex['MainIndex'] = []
    for MainIndex in TitleAndIndexGenResponse['메인목차']:
        IndexId = int(MainIndex['순번'])
        Index = MainIndex['목차']
        TitleAndIndex['MainIndex'].append({'IndexId': IndexId, 'Index': Index})
        
    ## TitleAndIndexFrame 데이터 프레임 업데이트
    TitleAndIndexFrame[1].append(TitleAndIndex)
    
    ## TitleAndIndexFrame ProcessCount 및 Completion 업데이트
    TitleAndIndexFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        TitleAndIndexFrame[0]['Completion'] = 'Yes'
        
    ## TitleAndIndexFrame 저장
    with open(ProjectDataFrameTitleAndIndexPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(TitleAndIndexFrame, DataFrameJson, indent = 4, ensure_ascii = False)

## Process7: SummaryOfIndexGenProcess DataFrame 저장
def SummaryOfIndexGenProcessDataFrameSave(ProjectName, BookScriptGenDataFramePath, ProjectDataFrameSummaryOfIndexPath, SummaryOfIndexGenResponse, Process, InputCount, TotalInputCount):
    ## SummaryOfIndexGenFrame 불러오기
    if os.path.exists(ProjectDataFrameSummaryOfIndexPath):
        SummaryOfIndexFramePath = ProjectDataFrameSummaryOfIndexPath
    else:
        SummaryOfIndexFramePath = os.path.join(BookScriptGenDataFramePath, "b5312-03_SummaryOfIndexFrame.json")
    with open(SummaryOfIndexFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        SummaryOfIndexFrame = json.load(DataFrameJson)
        
    ## SummaryOfIndexFrame 업데이트
    SummaryOfIndexFrame[0]['ProjectName'] = ProjectName
    SummaryOfIndexFrame[0]['TaskName'] = Process
    
    ## SummaryOfIndexFrame 첫번째 데이터 프레임 복사
    for Response in SummaryOfIndexGenResponse:
        SummaryOfIndex = SummaryOfIndexFrame[1][0].copy()

        SummaryOfIndex['IndexId'] = int(Response['순번'])
        SummaryOfIndex['Index'] = Response['메인목차']
        SummaryOfIndex['Summary'] = Response['전체요약']
        SummaryOfIndex['SubIndex'] = []
        for idx, subIndex in enumerate(Response['서브목차']):
            SubIndexId = idx + 1
            SubIndex = subIndex['서브목차']
            Keyword = subIndex['키워드']
            Summary = subIndex['요약']
            SummaryOfIndex['SubIndex'].append({'SubIndexId': SubIndexId, 'SubIndex': SubIndex, 'Keyword': Keyword, 'Summary': Summary})
    
        ## SummaryOfIndexFrame 데이터 프레임 업데이트
        SummaryOfIndexFrame[1].append(SummaryOfIndex)
        
    ## SummaryOfIndexFrame ProcessCount 및 Completion 업데이트
    SummaryOfIndexFrame[0]['InputCount'] = InputCount
    if InputCount == TotalInputCount:
        SummaryOfIndexFrame[0]['Completion'] = 'Yes'
        
    ## SummaryOfIndexFrame 저장
    with open(ProjectDataFrameSummaryOfIndexPath, 'w', encoding = 'utf-8') as DataFrameJson:
        json.dump(SummaryOfIndexFrame, DataFrameJson, indent = 4, ensure_ascii = False)

#####################################
##### ProcessFeedback Input 생성 #####
#####################################
## Prompt 벨류값 수정 함수
def PromptToModify(Value):
    if isinstance(Value, list):
        # 리스트 내부의 각 요소 처리
        return [
            value.replace("<prompt:", "<수정:").replace("<수정: >", "").strip() 
            if isinstance(value, str) else value
            for value in Value
        ]
    elif isinstance(Value, str):
        # 문자열 처리
        return Value.replace("<prompt:", "<수정:").replace("<수정: >", "").strip()
    else:
        return Value

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
            if len(data) > 0 and all(isinstance(item, str) for item in data):
                # 모든 요소가 문자열인 리스트인 경우 "<prompt: >" 추가
                return data + ["<prompt: >"]
            return [ModifyValues(item) if isinstance(item, dict) else 
                    item + "<prompt: >" if isinstance(item, str) else 
                    item for item in data]
        else:
            return data

    return ModifyValues(ProcessDic)

## Feedback1~3: ScriptPlanFeedback Input 생성
def ScriptPlanFeedbackInput(PromptInputDic):
    PromptInput = PromptInputDic['PromptData']
    ## PromptModifyInput 생성
    PromptModifyInput = {
        '배경': PromptToModify(PromptInput['Background']),
        '주제': PromptToModify(PromptInput['Subject']),
        '범위': PromptToModify(PromptInput['Range']),
        '개념키워드': PromptToModify(PromptInput['ConceptKeyword']),
        '독자키워드': PromptToModify(PromptInput['TargetKeyword']),
        '가치': {
            '글이전해줄핵심가치': {
                '설명': PromptToModify(PromptInput['Supply']['Value']['Sentence']),
                '키워드': PromptToModify(PromptInput['Supply']['Value']['KeyWord'])
            },
            '글이전해줄핵심포인트들': {
                '설명': PromptToModify(PromptInput['Supply']['Points']['Sentence']),
                '키워드': PromptToModify(PromptInput['Supply']['Points']['KeyWord'])
            },
            '글이전해줄핵심비전': {
                '설명': PromptToModify(PromptInput['Supply']['Vision']['Sentence']),
                '키워드': PromptToModify(PromptInput['Supply']['Vision']['KeyWord'])
            }
        }
    }
    
    return PromptModifyInput

## Feedback5: TitleAndIndexGenFeedback Input 생성
def TitleAndIndexGenFeedbackInput(PromptInputDic):
    PromptInput = PromptInputDic['PromptData']
    ## PromptModifyInput 생성
    PromptModifyInput = {
        '글쓰기형태': PromptToModify(PromptInput['Type']),
        '제목부제형태': PromptToModify(PromptInput['TitleType']),
        '제목': PromptToModify(PromptInput['Title']),
        '부제': PromptToModify(PromptInput['SubTitle']),
        '메인목차': [
            {
                '순번': PromptToModify(PromptInput['MainIndex'][i]['IndexId']),
                '목차': PromptToModify(PromptInput['MainIndex'][i]['Index'])
            }
            for i in range(len(PromptInput['MainIndex']))
        ]
    }
    
    return PromptModifyInput

## Feedback7: SummaryOfIndexGenFeedback Input 생성 및 앞/뒤 예시 확장
def SummaryOfIndexGenFeedbackInputAndExtension(PromptInputDic, ScriptEditPath, Process):
    with open(ScriptEditPath, 'r', encoding = 'utf-8') as ScriptEditJson:
        ScriptEdit = json.load(ScriptEditJson)[Process]

    ## PromptInputList 생성 (앞/뒤 예시 확장)
    PromptId = PromptInputDic['PromptId']
    PromptInput = PromptInputDic['PromptData']
    PromptInputList = []
    for i in range(len(ScriptEdit)):
        if PromptId == ScriptEdit[i]['IndexId']:
            if i > 0:
                PromptInputList.append({'Mark': '[수정 부분의 앞 부분 참고]', 'PromptInput': ScriptEdit[i-1]})
            PromptInputList.append({'Mark': '\n[** 수정 부분 **]', 'PromptInput': PromptInput})
            if i < len(ScriptEdit) - 1:
                PromptInputList.append({'Mark': '[수정 부분의 뒷 부분 참고]', 'PromptInput': ScriptEdit[i+1]})
            break
        
    ## PromptModifyInput 생성
    PromptModifyInput = ''
    for PromptInputDic in PromptInputList:
        Mark = PromptInputDic['Mark']
        PromptInput = PromptInputDic['PromptInput']
        promptModifyInput = {
            '순번': PromptToModify(PromptInput['IndexId']),
            '메인목차': PromptToModify(PromptInput['Index']),
            '전체요약': PromptToModify(PromptInput['Summary']),
            '서브목차': [
                {
                    '서브목차': PromptToModify(PromptInput['SubIndex'][i]['SubIndex']),
                    '키워드': PromptToModify(PromptInput['SubIndex'][i]['Keyword']),
                    '요약': PromptToModify(PromptInput['SubIndex'][i]['Summary'])
                }
                for i in range(len(PromptInput['SubIndex']))
            ]
        }
        PromptModifyInput += f"{Mark}\n\n{json.dumps(promptModifyInput, indent = 4, ensure_ascii = False)}\n\n"
    
    return PromptModifyInput

####################################
##### ProcessFeedback Edit 저장 #####
####################################
## Feedback1~3: ScriptPlanFeedback Edit 저장
def ScriptPlanFeedbackEditUpdate(ScriptEditPath, ModifiedScriptEditPath, Process, EditCount, Response):
    ## ScriptEdit 불러오기
    with open(ScriptEditPath, 'r', encoding = 'utf-8') as ScriptEditJson:
        ScriptEdit = json.load(ScriptEditJson)
    ## Feedback 이전 ScriptEdit 저장
    with open(ModifiedScriptEditPath, 'w', encoding = 'utf-8') as ScriptEditJson:
        json.dump(ScriptEdit, ScriptEditJson, indent = 4, ensure_ascii = False)
    
    ## ScriptEdit 업데이트
    ProcessDic = ScriptEdit[Process][EditCount]
    ProcessDic['Background'] = Response['배경']
    ProcessDic['Subject'] = Response['주제']
    ProcessDic['Range'] = Response['범위']
    ProcessDic['ConceptKeyword'] = Response['개념키워드']
    ProcessDic['TargetKeyword'] = Response['독자키워드']
    ProcessDic['Supply']['Value']['Sentence'] = Response['가치']['글이전해줄핵심가치']['설명']
    ProcessDic['Supply']['Value']['KeyWord'] = Response['가치']['글이전해줄핵심가치']['키워드']
    ProcessDic['Supply']['Points']['Sentence'] = Response['가치']['글이전해줄핵심포인트들']['설명']
    ProcessDic['Supply']['Points']['KeyWord'] = Response['가치']['글이전해줄핵심포인트들']['키워드']
    ProcessDic['Supply']['Vision']['Sentence'] = Response['가치']['글이전해줄핵심비전']['설명']
    ProcessDic['Supply']['Vision']['KeyWord'] = Response['가치']['글이전해줄핵심비전']['키워드']
    ReStructureProcessDic = RestructureProcessDic(ProcessDic)
    ScriptEdit[Process][EditCount] = ReStructureProcessDic
    
    ## ScriptEdit 저장
    with open(ScriptEditPath, 'w', encoding = 'utf-8') as ScriptEditJson:
        json.dump(ScriptEdit, ScriptEditJson, indent = 4, ensure_ascii = False)
        
## Feedback5: TitleAndIndexGenFeedback Edit 저장
def TitleAndIndexGenFeedbackEditUpdate(ScriptEditPath, ModifiedScriptEditPath, Process, EditCount, Response):
    ## ScriptEdit 불러오기
    with open(ScriptEditPath, 'r', encoding = 'utf-8') as ScriptEditJson:
        ScriptEdit = json.load(ScriptEditJson)
    ## Feedback 이전 ScriptEdit 저장
    with open(ModifiedScriptEditPath, 'w', encoding = 'utf-8') as ScriptEditJson:
        json.dump(ScriptEdit, ScriptEditJson, indent = 4, ensure_ascii = False)
    
    ## ScriptEdit 업데이트
    ProcessDic = ScriptEdit[Process][EditCount]
    ProcessDic['Type'] = Response['글쓰기형태']
    ProcessDic['TitleType'] = Response['제목부제형태']
    ProcessDic['Title'] = Response['제목']
    ProcessDic['SubTitle'] = Response['부제']
    ProcessDic['MainIndex'] = []
    for MainIndex in Response['메인목차']:
        IndexId = int(MainIndex['순번'])
        Index = MainIndex['목차']
        ProcessDic['MainIndex'].append({'IndexId': IndexId, 'Index': Index})
    ReStructureProcessDic = RestructureProcessDic(ProcessDic)
    ScriptEdit[Process][EditCount] = ReStructureProcessDic

    ## ScriptEdit 저장
    with open(ScriptEditPath, 'w', encoding = 'utf-8') as ScriptEditJson:
        json.dump(ScriptEdit, ScriptEditJson, indent = 4, ensure_ascii = False)

## Feedback7: SummaryOfIndexGenFeedback Edit 저장
def SummaryOfIndexGenFeedbackEditUpdate(ScriptEditPath, ModifiedScriptEditPath, Process, BeforeProcess, EditCount, Response):
    ## ScriptEdit 불러오기
    with open(ScriptEditPath, 'r', encoding = 'utf-8') as ScriptEditJson:
        ScriptEdit = json.load(ScriptEditJson)
    ## Feedback 이전 ScriptEdit 저장
    with open(ModifiedScriptEditPath, 'w', encoding = 'utf-8') as ScriptEditJson:
        json.dump(ScriptEdit, ScriptEditJson, indent = 4, ensure_ascii = False)

    ## BeforeScriptEdit 업데이트
    BeforeProcessDic = ScriptEdit[BeforeProcess][0]['MainIndex'][EditCount]
    BeforeProcessDic['Index'] = Response['메인목차']

    ## ScriptEdit 업데이트
    ProcessDic = ScriptEdit[Process][EditCount]
    ProcessDic['IndexId'] = int(Response['순번'])
    ProcessDic['Index'] = Response['메인목차']
    ProcessDic['Summary'] = Response['전체요약']
    ProcessDic['SubIndex'] = []
    for idx, subIndex in enumerate(Response['서브목차']):
        SubIndexId = idx + 1
        SubIndex = subIndex['서브목차']
        Keyword = subIndex['키워드']
        Summary = subIndex['요약']
        ProcessDic['SubIndex'].append({'SubIndexId': SubIndexId, 'SubIndex': SubIndex, 'Keyword': Keyword, 'Summary': Summary})
    ReStructureProcessDic = RestructureProcessDic(ProcessDic)
    ScriptEdit[Process][EditCount] = ReStructureProcessDic
    
    ## ScriptEdit 저장
    with open(ScriptEditPath, 'w', encoding = 'utf-8') as ScriptEditJson:
        json.dump(ScriptEdit, ScriptEditJson, indent = 4, ensure_ascii = False)

##############################
##### ProcessEdit 업데이트 #####
##############################
## Process Edit 저장
def ProcessEditSave(ProjectDataFramePath, ScriptEditPath, Process):
    ## ScriptDataFrame 불러온 뒤 Completion 확인
    with open(ProjectDataFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
        ScriptDataFrame = json.load(DataFrameJson)
    ## ScriptEdit 재구조화 후 저장
    if ScriptDataFrame[0]['Completion'] == 'Yes':
        ## ScriptEdit이 존재할때
        if os.path.exists(ScriptEditPath):
            with open(ScriptEditPath, 'r', encoding = 'utf-8') as ScriptEditJson:
                ScriptEdit = json.load(ScriptEditJson)
        ## ScriptEdit이 존재 안할때
        else:
            ScriptEdit = {}
        ## ScriptEdit 업데이트
        ScriptEdit[Process] = []
        ScriptEdit[f"{Process}Completion"] = '완료 후 Completion'
        ScriptDataList = ScriptDataFrame[1]
        for i in range(1, len(ScriptDataList)):
            ProcessDic = ScriptDataList[i]
            ReStructureProcessDic = RestructureProcessDic(ProcessDic)
            ScriptEdit[Process].append(ReStructureProcessDic)
        
        ## ScriptEdit 저장
        with open(ScriptEditPath, 'w', encoding = 'utf-8') as ScriptEditJson:
            json.dump(ScriptEdit, ScriptEditJson, indent = 4, ensure_ascii = False)

## Process Edit Prompt 확인
def ProcessEditPromptCheck(ScriptEditPath, Process, TotalInputCount, NumProcesses = 1):
    
    ## 빈 Prompt 제거 함수
    def CleanPrompts(Edit):
        if isinstance(Edit, dict):
            NewDict = {}
            for key, value in Edit.items():
                # 숫자나 ID 관련 필드는 그대로 유지
                if "Id" in key:  # ID 관련 키들 보존
                    NewDict[key] = value
                
                if isinstance(value, str):
                    # 문자열에서 빈 prompt 태그 제거
                    NewValue = value.replace("<prompt: >", "").strip()
                    if NewValue:  # 값이 비어있지 않으면 추가
                        NewDict[key] = NewValue
                elif isinstance(value, dict):
                    # 중첩된 딕셔너리 처리
                    NewValue = CleanPrompts(value)
                    if NewValue:  # 빈 딕셔너리가 아니면 추가
                        NewDict[key] = NewValue
                elif isinstance(value, list):
                    # 리스트 내부 요소 처리
                    cleaned_list = []
                    for item in value:
                        if isinstance(item, dict):
                            cleaned_dict = CleanPrompts(item)
                            if cleaned_dict:  # 빈 딕셔너리가 아니면 추가
                                cleaned_list.append(cleaned_dict)
                        elif isinstance(item, str):
                            cleaned_str = item.replace("<prompt: >", "").strip()
                            if cleaned_str:  # 빈 문자열이 아니면 추가
                                cleaned_list.append(cleaned_str)
                        else:
                            cleaned_list.append(item)
                    if cleaned_list:  # 리스트가 비어있지 않으면 추가
                        NewDict[key] = cleaned_list
                else:
                    # 다른 타입의 값은 그대로 유지
                    NewDict[key] = value
            return NewDict
        elif isinstance(Edit, list):
            # 리스트 처리
            return [CleanPrompts(item) if isinstance(item, dict) else 
                   item.replace("<prompt: >", "").strip() if isinstance(item, str) 
                   else item for item in Edit if item]
        elif isinstance(Edit, str):
            # 문자열 처리
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
    
    ## EditCheck
    EditCheck = False
    EditCompletion = False
    promptCheck = False
    PromptInputList = []
    ScriptEditProcess = []
    if os.path.exists(ScriptEditPath):
        ## '[...Edit].json' 확인
        with open(ScriptEditPath, 'r', encoding = 'utf-8') as ScriptEditJson:
            ScriptEdit = json.load(ScriptEditJson)
        if Process in ScriptEdit and len(ScriptEdit[Process]) == TotalInputCount * NumProcesses:
            EditCheck = True
            ScriptEditProcess = ScriptEdit[Process]
        
            ## '<prompt: ...>' 확인
            for i, ProcessDic in enumerate(ScriptEditProcess):
                CleanedProcessDic = CleanPrompts(ProcessDic)  # 빈 '<prompt: >' 삭제 후 데이터 정리
                if PromptCheck(CleanedProcessDic):  # '<prompt: ...>'이 있는 경우만 리스트에 추가
                    PromptInputList.append({'PromptId': i + 1, 'PromptData': CleanedProcessDic})
                    promptCheck = True
                    
            ## 'ProcessCompletion' 확인
            if ScriptEdit[f"{Process}Completion"] == 'Completion':
                ScriptEdit[Process] = CleanPrompts(ScriptEdit[Process])
                with open(ScriptEditPath, 'w', encoding='utf-8') as ScriptEditJson:
                    json.dump(ScriptEdit, ScriptEditJson, indent = 4, ensure_ascii = False)
                EditCompletion = True
        
    return EditCheck, EditCompletion, promptCheck, PromptInputList

## Process Edit Prompt 결과 업데이트

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
    
    ## projectName_Modified 경로 설정
    BaseModifyFolder = f"[{projectName}_Modified]"
    ModifyFolderPath = os.path.join(ProjectMasterScriptPath, BaseModifyFolder)
    if not os.path.exists(ModifyFolderPath):
        os.makedirs(ModifyFolderPath)
    
    ModifyTime = datetime.now().strftime("%Y%m%d%H%M%S")
    ModifiedScriptEditPath = os.path.join(ProjectMasterScriptPath, BaseModifyFolder, f'[{ModifyTime}_{projectName}_Script_ModifiedEdit].json')

    
    BookScriptGenDataFramePath = "/yaas/backend/b5_Database/b53_ProjectData/b531_ScriptProject/b5312_BookScriptGen"

    #########################################
    ### Process1: ScriptPlan Response 생성 ###
    #########################################

    ## Process 설정
    ProcessNumber = '01'
    Process = "ScriptPlan"
    IntentionProcess = Intention + Process

    ## ScriptPlan 경로 생성
    ProjectDataFrameScriptPalnPath = os.path.join(ProjectDataFrameScriptPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')

    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    TotalInputCount = 1 # TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameScriptPalnPath)
    EditCheck, EditCompletion, PromptCheck, PromptInputList = ProcessEditPromptCheck(ScriptEditPath, Process, TotalInputCount)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    # print(f"PromptCheck: {PromptCheck}")
    # print(f"PromptInputList: {PromptInputList}")
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for inputCount in range(InputCount, TotalInputCount + 1):
                ## Process1-1: DemandScriptPlan Response 생성
                if Intention == "Demand":
                    ## Input 생성
                    Input = DemandCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, projectName, Intention)
                    
                    ## Response 생성
                    ScriptPlanResponse = ProcessResponse(projectName, email, IntentionProcess, Input, inputCount, TotalInputCount, ScriptPlanFilter, CheckCount, "OpenAI", mode, MessagesReview)
                    
                ## Process1-2: SupplyScriptPlan Response 생성
                if Intention == "Supply":
                    ## Input 생성
                    Input = SupplyCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, projectName, Intention)
                    
                    ## Response 생성
                    ScriptPlanResponse = ProcessResponse(projectName, email, IntentionProcess, Input, inputCount, TotalInputCount, ScriptPlanFilter, CheckCount, "OpenAI", mode, MessagesReview)
                    
                ## Process1-3: SimilarityScriptPlan Response 생성
                if Intention == "Similarity":
                    ## Input 생성
                    Input1 = SupplyCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, projectName, Intention)
                    Input2 = DemandCollectionDataToScriptPlanInput(TotalSearchResultDataTempPath, projectName, Intention)
                    
                    ## Response 생성
                    ScriptPlanResponse = ProcessResponse(projectName, email, IntentionProcess, Input1, inputCount, TotalInputCount, ScriptPlanFilter, CheckCount, "OpenAI", mode, MessagesReview, input2 = Input2)
                    
                ## DataFrame 저장
                ScriptPlanProcessDataFrameSave(projectName, BookScriptGenDataFramePath, ProjectDataFrameScriptPalnPath, ScriptPlanResponse, Process, inputCount, TotalInputCount)
                
        ## Edit 저장
        ProcessEditSave(ProjectDataFrameScriptPalnPath, ScriptEditPath, Process)
        sys.exit(f"[ {projectName}_Script_Edit -> {Process} 생성 완료: (({Process}))을 검수한 뒤 직접 수정, 또는 수정 사항을 ((<prompt: >))에 작성, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{ScriptEditPath}")
        
    if EditCheck:
        ## FeedbackPrompt Response 생성
        if PromptCheck:
            FeedbackProcess = Process + "Feedback"
            TotalInputCount = len(PromptInputList)
            for PromptInputDic in PromptInputList:
                inputCount = PromptInputDic['PromptId']
                EditCount = PromptInputDic['PromptId'] - 1

                ## PromptInput 생성
                FeedbackPromptInput = ScriptPlanFeedbackInput(PromptInputDic)

                ## Response 생성
                ScriptPlanFeedbackResponse = ProcessResponse(projectName, email, FeedbackProcess, FeedbackPromptInput, inputCount, TotalInputCount, ScriptPlanFeedbackFilter, CheckCount, "OpenAI", mode, MessagesReview)

                ## Edit 업데이트
                ScriptPlanFeedbackEditUpdate(ScriptEditPath, ModifiedScriptEditPath, Process, EditCount, ScriptPlanFeedbackResponse)
                    ## 1. Input수정 한글화, prompt를 수정으로 변경, 2. 수정 프로세스 진행, 3. 수정 사항으로 ScriptEdit 변경 후 다시 <prompt: > 적용
                    # ScriptPlanResponse = ProcessResponse(projectName, email, IntentionProcess, PromptInput, InputCount, InputCount, ScriptPlanFilter, CheckCount, "OpenAI", mode, MessagesReview, input2 = Input2)
    
            sys.exit(f"[ {projectName}_Script_Edit -> {Process} 수정 완료: (({Process}))을 검수한 뒤 직접 수정, 또는 수정 사항을 ((<prompt: >))에 작성, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{ScriptEditPath}")

        if not EditCompletion:
            ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
            sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 또는 수정 사항을 ((<prompt: >))에 작성, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{ScriptEditPath}")

    ###############################################
    ### Process2: TitleAndIndexGen Response 생성 ###
    ###############################################
    
    ## Process 설정
    ProcessNumber = '02'
    Process = "TitleAndIndexGen"
    
    ## TitleAndIndexGen 경로 생성
    ProjectDataFrameTitleAndIndexPath = os.path.join(ProjectDataFrameScriptPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')
    
    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList = EditToTitleAndIndexGenInputList(ScriptEditPath, "ScriptPlan")
    TotalInputCount = len(InputList) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameTitleAndIndexPath)
    EditCheck, EditCompletion, PromptCheck, PromptInputList = ProcessEditPromptCheck(ScriptEditPath, Process, TotalInputCount)
    
    ## Process 진행
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList[i]['Id']
                Input = InputList[i]['Input']
    
                ## Response 생성
                TitleAndIndexGenResponse = ProcessResponse(projectName, email, Process, Input, inputCount, TotalInputCount, TitleAndIndexGenFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## DataFrame 저장
                TitleAndIndexGenProcessDataFrameSave(projectName, BookScriptGenDataFramePath, ProjectDataFrameTitleAndIndexPath, TitleAndIndexGenResponse, Process, inputCount, TotalInputCount)

        ## Edit 저장
        ProcessEditSave(ProjectDataFrameTitleAndIndexPath, ScriptEditPath, Process)
        sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 또는 수정 사항을 ((<prompt: >))에 작성, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{ScriptEditPath}")
        
    if EditCheck:
        ## FeedbackPrompt Response 생성
        if PromptCheck:
            FeedbackProcess = Process + "Feedback"
            TotalInputCount = len(PromptInputList)
            for PromptInputDic in PromptInputList:
                inputCount = PromptInputDic['PromptId']
                EditCount = PromptInputDic['PromptId'] - 1
                
                ## PromptInput 생성
                FeedbackPromptInput = TitleAndIndexGenFeedbackInput(PromptInputDic)
                
                ## Response 생성
                TitleAndIndexGenFeedbackResponse = ProcessResponse(projectName, email, FeedbackProcess, FeedbackPromptInput, inputCount, TotalInputCount, TitleAndIndexGenFilter, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## Edit 업데이트
                TitleAndIndexGenFeedbackEditUpdate(ScriptEditPath, ModifiedScriptEditPath, Process, EditCount, TitleAndIndexGenFeedbackResponse)

            sys.exit(f"[ {projectName}_Script_Edit -> {Process} 수정 완료: (({Process}))을 검수한 뒤 직접 수정, 또는 수정 사항을 ((<prompt: >))에 작성, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{ScriptEditPath}")
            
        if not EditCompletion:
            sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 또는 수정 사항을 ((<prompt: >))에 작성, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{ScriptEditPath}")
            
    ################################################
    ### Process3: SummaryOfIndexGen Response 생성 ###
    ################################################
    
    ## Process 설정
    ProcessNumber = '03'
    Process = "SummaryOfIndexGen"
    
    ## SummaryOfIndexGen 경로 생성
    ProjectDataFrameSummaryOfIndexPath = os.path.join(ProjectDataFrameScriptPath, f'{email}_{projectName}_{ProcessNumber}_{Process}DataFrame.json')
    
    ## Process Count 계산 및 Check
    CheckCount = 0 # 필터에서 데이터 체크가 필요한 카운트
    InputList1 = InputList
    InputList2 = EditToSummaryOfIndexGenInputList(ScriptEditPath, "TitleAndIndexGen")
    TotalInputCount = len(InputList2) # 인풋의 전체 카운트
    InputCount, DataFrameCompletion = ProcessDataFrameCheck(ProjectDataFrameSummaryOfIndexPath)
    EditCheck, EditCompletion, PromptCheck, PromptInputList = ProcessEditPromptCheck(ScriptEditPath, Process, TotalInputCount, NumProcesses = 2)
    # print(f"InputCount: {InputCount}")
    # print(f"EditCheck: {EditCheck}")
    # print(f"EditCompletion: {EditCompletion}")
    # print(f"PromptCheck: {PromptCheck}")
    # print(f"PromptInputList: {PromptInputList}")
    ## Process 진행
    SummaryOfIndexGenResponse = None
    if not EditCheck:
        if DataFrameCompletion == 'No':
            for i in range(InputCount - 1, TotalInputCount):
                ## Input 생성
                inputCount = InputList2[i]['Id']
                Input1 = InputList1[0]['Input']
                Input2 = InputList2[i]['Input']
                if SummaryOfIndexGenResponse:
                    SummaryOfIndexGenBeforeResponse = {"메인목차": SummaryOfIndexGenResponse}
                else:
                    SummaryOfIndexGenBeforeResponse = ""
                Caution = InputList2[i]['Caution'] + json.dumps(SummaryOfIndexGenBeforeResponse, indent = 4, ensure_ascii = False)
    
                ## Response 생성
                SummaryOfIndexGenResponse = ProcessResponse(projectName, email, Process, Input1, inputCount, TotalInputCount, SummaryOfIndexGenFilter, CheckCount, "OpenAI", mode, MessagesReview, input2 = Input2, memoryCounter = Caution)
                
                ## DataFrame 저장
                SummaryOfIndexGenProcessDataFrameSave(projectName, BookScriptGenDataFramePath, ProjectDataFrameSummaryOfIndexPath, SummaryOfIndexGenResponse, Process, inputCount, TotalInputCount)

        ## Edit 저장
        ProcessEditSave(ProjectDataFrameSummaryOfIndexPath, ScriptEditPath, Process)
        sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 또는 수정 사항을 ((<prompt: >))에 작성, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{ScriptEditPath}")
        
    if EditCheck:
        ## FeedbackPrompt Response 생성
        if PromptCheck:
            FeedbackProcess = Process + "Feedback"
            TotalInputCount = len(PromptInputList)
            for PromptInputDic in PromptInputList:
                inputCount = PromptInputDic['PromptId']
                EditCount = inputCount - 1
                
                ## PromptInput 생성 및 앞/뒤 예시 확장
                FeedbackPromptInput = SummaryOfIndexGenFeedbackInputAndExtension(PromptInputDic, ScriptEditPath, Process)
                
                ## Response 생성
                SummaryOfIndexGenFeedbackResponse = ProcessResponse(projectName, email, FeedbackProcess, FeedbackPromptInput, inputCount, TotalInputCount, SummaryOfIndexGenFeedback, CheckCount, "OpenAI", mode, MessagesReview)
                
                ## Edit 업데이트
                SummaryOfIndexGenFeedbackEditUpdate(ScriptEditPath, ModifiedScriptEditPath, Process, "TitleAndIndexGen", EditCount, SummaryOfIndexGenFeedbackResponse)
                
            sys.exit(f"[ {projectName}_Script_Edit -> {Process} 수정 완료: (({Process}))을 검수한 뒤 직접 수정, 또는 수정 사항을 ((<prompt: >))에 작성, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{ScriptEditPath}")
            
        if not EditCompletion:
            sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 또는 수정 사항을 ((<prompt: >))에 작성, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n{ScriptEditPath}")

    #############################################
    ### Process4: ScriptShortGen Response 생성 ###
    #############################################

    print(f"[ User: {email} | Project: {projectName} | BookScriptGenUpdate 완료 ]")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '250121_테스트'
    #########################################################################
    Intention = "Similarity"
    # JSON 파일 경로
    BookScriptGenProcessUpdate(ProjectName, email, Intention)