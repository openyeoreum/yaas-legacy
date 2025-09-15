import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from agent.a3_Operation.a32_Solution.a321_LoadLLM import OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from agent.a5_Solution.a51_Collection.a511_VectorDatabase.a5114_VDBUpsert import UpsertCollectionData

#########################
##### InputList 생성 #####
#########################
## totalBookDataList로 로드(업데이트가 필요한 부분 선정, 이중 분석 방지)
def LoadTotalBookDataList(TotalBookDataJsonPath, TotalBookDataTempPath, StartPoint = 0):
    # TempISBNList 생성
    TempISBNList = []
    TempJsonList = []
    if os.path.exists(TotalBookDataTempPath):
        TempJsonList = os.listdir(TotalBookDataTempPath)
    FileNamePattern = r"^BookData_\((\d+)\)_.*\.json$"
    for TempJson in TempJsonList:
        match = re.match(FileNamePattern, TempJson)
        if match:
            TempISBNList.append(int(match.group(1)))
    SortedTempISBNList = sorted(TempISBNList)
    
    ## TotalBookDataList 로드
    with open(TotalBookDataJsonPath, 'r', encoding = 'utf-8') as BookJson:
        TotalBookDataList = json.load(BookJson)[StartPoint:]
    ## TotalBookDataList중 업데이트가 필요한 부분 선정, 이중 분석 방지
    totalBookDataList = []
    for BookData in TotalBookDataList:
        if int(BookData['ISBN']) not in SortedTempISBNList:
            totalBookDataList.append(BookData)

    return totalBookDataList

## LoadTotalBookData의 inputList 치환
def LoadTotalBookDataToInputList(TotalBookDataJsonPath, TotalBookDataTempPath):
    totalBookDataList = LoadTotalBookDataList(TotalBookDataJsonPath, TotalBookDataTempPath)
    
    ## InputList 생성
    InputList = []
    for i ,BookData in enumerate(totalBookDataList):
        ISBN = BookData['ISBN']
        TitleText = f"[도서명] {BookData['Title']}\n\n"
        PublishedDateText = f"[발행일] {BookData['PublishedDate']}\n\n"
        AuthorText = f"[저자] {BookData['Author']}\n\n"
        if BookData['AuthorInfo'] is not None:
            AuthorInfo = BookData['AuthorInfo'].replace('\n\n\n', '\n\n').replace('\n\n\n', '\n\n')
        else:
            AuthorInfo = BookData['AuthorInfo']
        AuthorInfoText = f"[저자소개]\n{AuthorInfo}\n\n"
        IntroCategory = BookData['IntroCategory']
        IntroCategoryText = f"[도서카테고리]\n{', '.join(IntroCategory)}\n\n"
        if BookData['Intro'] is not None:
            Intro = BookData['Intro'].replace('\n\n\n', '\n\n').replace('\n\n\n', '\n\n')
        else:
            Intro = BookData['Intro']
        IntroText = f"[도서소개]\n{Intro}\n\n"
        BookIndexText = f"[도서목차]\n{BookData['BookIndex']}\n\n"
        if BookData['BookReviews'] is not None:
            BookReviews = BookData['BookReviews'].replace('\n\n\n', '\n\n').replace('\n\n\n', '\n\n')
        else:
            BookReviews = BookData['BookReviews']
        BookReviewsText = f"[출판사 서평]\n{BookReviews}\n\n"
        CommentList = BookData['CommentList']
        CommentsCountText = f"[구매자 리뷰]\n총 {BookData['CommentsCount']}개의 리뷰 중 {len(CommentList)}개\n\n"
        CommentTextList = []
        CommentLikeList = []
        for j in range(len(CommentList)):
            CommentText = f"구매자{j+1}: {CommentList[j]['comment']}\n좋아요({CommentList[j]['like']})"
            CommentTextList.append(CommentText)
            CommentLikeList.append(CommentList[j]['like'])
        if len(CommentTextList) == 0:
            CommentDataText = CommentsCountText + '\n\n구매자 리뷰가 0개, 없습니다.'
        else:
            CommentDataText = CommentsCountText + '\n\n'.join(CommentTextList)
        
        BookDataText = TitleText + PublishedDateText + AuthorText + AuthorInfoText + IntroCategoryText + IntroText + BookIndexText + BookReviewsText + CommentDataText
   
        InputDic = {'Id': i+1, 'ISBN': ISBN, 'BookText': BookDataText, 'CommentText': CommentDataText, 'CommentLikeList': CommentLikeList, 'CommentCount': len(CommentList)}
        InputList.append(InputDic)
        
    return InputList

######################
##### Filter 조건 #####
######################
## Process1: BookContextDefine의 Filter(Error 예외처리)
def BookContextDefineFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        outputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "BookContextDefine, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error3: 주요 키 확인
    required_keys = ['요약', '분야', '가치', '발전', '정보의질']
    if not all(key in outputDic for key in required_keys):
        return "BookContextDefine, JSON에서 오류 발생: 주요 키 누락"

    # '가치' 검증
    value_keys = ['충족', '달성', '해결책']
    for value_key in value_keys:
        if not all(sub_key in outputDic['가치'][value_key] for sub_key in ['설명', '키워드', '중요도']):
            return f"BookContextDefine, JSON에서 오류 발생: '가치' {value_key}에 '설명', '키워드', '중요도' 미포함"

    # '발전' 검증
    development_keys = ['필요', '목표', '질문']
    for development_key in development_keys:
        if not all(sub_key in outputDic['발전'][development_key] for sub_key in ['설명', '키워드', '중요도']):
            return f"BookContextDefine, JSON에서 오류 발생: '발전' {development_key}에 '설명', '키워드', '중요도' 미포함"

    # '분야' 키 확인
    if not isinstance(outputDic['분야'], list):
        return "BookContextDefine, JSON에서 오류 발생: '분야'가 리스트 형태가 아님"

    # '정보의질' 키 확인
    if '정보의질' not in outputDic:
        return "BookContextDefine, JSON에서 오류 발생: '정보의질' 미포함"

    # 모든 검사를 통과하면 '정리' 데이터를 반환
    return outputDic

## Process2: BookWMWMDefine의 Filter(Error 예외처리)
def BookWMWMDefineFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        outputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "BookWMWMDefine, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error3: 주요 키 확인
    required_keys = ['요약', '욕구상태', '이해상태', '마음상태', '행동상태', '정보의질']
    if not all(key in outputDic for key in required_keys):
        return "BookWMWMDefine, JSON에서 오류 발생: 주요 키 누락"

    # '요약' 키 확인
    if not isinstance(outputDic['요약'], list):
        return "BookWMWMDefine, JSON에서 오류 발생: '요약'이 리스트 형태가 아님"

    # 상태별 검증
    state_keys = ['욕구상태', '이해상태', '마음상태', '행동상태']
    for state_key in state_keys:
        if not all(sub_key in outputDic[state_key] for sub_key in [state_key, f'{state_key}선택이유', '중요도']):
            return f"BookWMWMDefine, JSON에서 오류 발생: {state_key}에 '상태', '선택이유', '중요도' 미포함"

    # '정보의질' 키 확인
    if '정보의질' not in outputDic:
        return "BookWMWMDefine, JSON에서 오류 발생: '정보의질' 미포함"

    # 모든 검사를 통과하면 '심리' 데이터를 반환
    return outputDic

## Process3: BookCommentAnalysis의 Filter(Error 예외처리)
def BookCommentAnalysisFilter(Response, CheckCount):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "BookCommentAnalysis, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error3: 자료의 구조가 다를 때의 예외 처리
    if ('요약' not in OutputDic or '평가' not in OutputDic or '긍정' not in OutputDic or '부정' not in OutputDic or '정보의질' not in OutputDic):
        return "BookCommentAnalysis, JSON에서 오류 발생: JSONKeyError"
    # Error4: 자료의 구조가 다를 때의 예외 처리
    if len(OutputDic['평가']) < CheckCount:
        return "BookCommentAnalysis, JSON에서 오류 발생: 평가수 누락"
    else:
        OutputDic['평가'] = OutputDic['평가'][:CheckCount]
    # '평가' 부분 리스트화
    OutputDic['평가'] = [list(item.values())[0] for item in OutputDic['평가']]
    # Error5: 자료의 구조가 다를 때의 예외 처리
    if not isinstance(OutputDic['요약'], list):
        return "BookCommentAnalysis, JSON에서 오류 발생: 요약 형식이 리스트가 아님"
    # Error6: 상태별 검증
    state_keys = ['긍정', '부정']
    for state_key in state_keys:
        if state_key == '긍정':
            sub_keys = ['가치', '키워드', '필요도']
        elif state_key == '부정':
            sub_keys = ['발전', '키워드', '필요도']
        if not all(sub_key in OutputDic[state_key] for sub_key in sub_keys):
            return f"BookWMWMDefine, JSON에서 오류 발생: {state_key}에 '가치', '키워드', '필요도' 미포함"
    
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
                f"오류횟수 {ErrorCount}회, 10초 후 프롬프트 재시도")
            
            if ErrorCount >= 10:
                sys.exit(f"Project: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | "
                        f"오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
            time.sleep(10)
            continue
        
        print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | JSONDecode 완료")
        return Filter

##################################
##### ProcessResponse 업데이트 #####
##################################
## ProcessResponseTemp 저장
def ProcessResponseTempSave(MainKey, InputDic, OutputDicList, DataJsonPath, DataTempPath):
    # DataTempPath 폴더가 없으면 생성
    if not os.path.exists(DataTempPath):
        os.makedirs(DataTempPath)
        
    # 오리지날 DataList 불러와서 변경사항 저장
    with open(DataJsonPath, 'r', encoding = 'utf-8') as DataListJson:
        DataList = json.load(DataListJson)
    
    # TextDataList 업데이트
    for i in range(len(DataList)):
        if DataList[i]['ISBN'] == InputDic['ISBN']:
            if OutputDicList != []:
                #### Context ####
                # Context-Summary
                ContextSummary = OutputDicList[0]['요약']
                # Context-KeyWord
                ContextKeyWord = OutputDicList[0]['분야']
                # Context-Demand
                ContextDemandNeeds = {"Sentence": OutputDicList[0]['발전']['필요']['설명'], "KeyWord": OutputDicList[0]['발전']['필요']['키워드'], "Weight": OutputDicList[0]['발전']['필요']['중요도']}
                ContextDemandPurpose = {"Sentence": OutputDicList[0]['발전']['목표']['설명'], "KeyWord": OutputDicList[0]['발전']['목표']['키워드'], "Weight": OutputDicList[0]['발전']['목표']['중요도']}
                ContextDemandQuestion = {"Sentence": OutputDicList[0]['발전']['질문']['설명'], "KeyWord": OutputDicList[0]['발전']['질문']['키워드'], "Weight": OutputDicList[0]['발전']['질문']['중요도']}
                ContextDemand = {'Needs': ContextDemandNeeds, 'Purpose': ContextDemandPurpose, 'Question': ContextDemandQuestion}
                # Context-Supply
                ContextSupplySatisfy = {"Sentence": OutputDicList[0]['가치']['충족']['설명'], "KeyWord": OutputDicList[0]['가치']['충족']['키워드'], "Weight": OutputDicList[0]['가치']['충족']['중요도']}
                ContextSupplySupport = {"Sentence": OutputDicList[0]['가치']['달성']['설명'], "KeyWord": OutputDicList[0]['가치']['달성']['키워드'], "Weight": OutputDicList[0]['가치']['달성']['중요도']}
                ContextSupplySolution = {"Sentence": OutputDicList[0]['가치']['해결책']['설명'], "KeyWord": OutputDicList[0]['가치']['해결책']['키워드'], "Weight": OutputDicList[0]['가치']['해결책']['중요도']}
                ContextSupply = {'Satisfy': ContextSupplySatisfy, 'Support': ContextSupplySupport, 'Solution': ContextSupplySolution}
                # Context-Weight
                ContextWeight = OutputDicList[0]['정보의질']
                ## ContextDic ##
                ContextDic = {'Summary': ContextSummary, 'KeyWord': ContextKeyWord, 'Demand': ContextDemand, 'Supply': ContextSupply, 'Weight': ContextWeight}
                #### Context ####

                #### WMWM ####
                # WMWM-Summary
                WMWMSummary = OutputDicList[1]['요약']
                # WMWM-Needs
                WMWMNeeds = {"State": OutputDicList[1]['욕구상태']['욕구상태'], "Reason": OutputDicList[1]['욕구상태']['욕구상태선택이유'], "Weight": OutputDicList[1]['욕구상태']['중요도']}
                # WMWM-Wisdom
                WMWMWisdom = {"State": OutputDicList[1]['이해상태']['이해상태'], "Reason": OutputDicList[1]['이해상태']['이해상태선택이유'], "Weight": OutputDicList[1]['이해상태']['중요도']}
                # WMWM-Mind
                WMWMMind = {"State": OutputDicList[1]['마음상태']['마음상태'], "Reason": OutputDicList[1]['마음상태']['마음상태선택이유'], "Weight": OutputDicList[1]['마음상태']['중요도']}
                # WMWM-Action
                WMWMAction = {"State": OutputDicList[1]['행동상태']['행동상태'], "Reason": OutputDicList[1]['행동상태']['행동상태선택이유'], "Weight": OutputDicList[1]['행동상태']['중요도']}
                # WMWM-Weight
                WMWMWeight = OutputDicList[1]['정보의질']
                ## WMWMDic ##
                WMWMDic = {'Summary': WMWMSummary, 'Needs': WMWMNeeds, 'Wisdom': WMWMWisdom, 'Mind': WMWMMind, 'Action': WMWMAction, 'Weight': WMWMWeight}
                #### WMWM ####
                
                #### BookReview ####
                if OutputDicList[2] is not None:
                    # BookReview-Summary
                    BookReviewSummary = OutputDicList[2]['요약']
                    # BookReview-Evaluation
                    EvaluationList = OutputDicList[2]['평가']
                    Evaluations = []
                    for j, Evaluation in enumerate(EvaluationList):
                        Evaluations.append({'Evaluation': Evaluation, 'Like': InputDic['CommentLikeList'][j]})
                    # BookReview-Negativity
                    BookReviewNegativity = {'Sentence': OutputDicList[2]['부정']['발전'], 'Keyword': OutputDicList[2]['부정']['키워드'], 'Weight': OutputDicList[2]['부정']['필요도']}
                    # BookReview-Positivity
                    BookReviewPositivity = {'Sentence': OutputDicList[2]['긍정']['가치'], 'Keyword': OutputDicList[2]['긍정']['키워드'], 'Weight': OutputDicList[2]['긍정']['필요도']}
                    BookReviewWeight = OutputDicList[2]['정보의질']
                    ## BookReviewDic ##
                    BookReviewDic = {'Summary': BookReviewSummary, 'Evaluations': Evaluations, 'Negativity': BookReviewNegativity, 'Positivity': BookReviewPositivity, 'Weight': BookReviewWeight}
                else:
                    ## BookReviewDic ##
                    BookReviewDic = None
                #### BookReview ####
                
                DataTemp = {MainKey: {'Context': ContextDic, 'WMWM': WMWMDic, 'BookReview': BookReviewDic}}
            else:
                DataTemp = {MainKey: None}
            
            # DataTempJson 저장
            DataTempJsonPath = os.path.join(DataTempPath, f"BookData_({DataList[i]['ISBN']})_{DataList[i]['Title']}.json")
            with open(DataTempJsonPath, 'w', encoding = 'utf-8') as DataTempJson:
                json.dump(DataTemp, DataTempJson, ensure_ascii = False, indent = 4)
            break

##### 추가 후처리 사항 #####

## BookScore 계산
def BookScoreCalculation(DataDic):
    # A: RankScore (40%)
    Rank = DataDic['Rank'][-1]['Rank']
    if Rank <= 50:
        RankScore = (51 - Rank) * 2 * 0.4
    else:
        RankScore = 0
    # B: RankHistoryScore (10%)
    RankHistory = DataDic['Rank']
    if len(RankHistory) >= 10:
        RankHistory = RankHistory[-10:]
        
    RankScores = 0
    for rank in RankHistory:
        _Rank = rank['Rank']
        if _Rank <= 50:
            RankScores += (51 - _Rank) / 5
    RankHistoryScores = RankScores * 0.1
    # C: CommentCountScore (30%)
    CommentCount = DataDic['CommentsCount']
    if CommentCount >= 1000:
        CommentCountScore = 1000 / 10 * 0.3
    else:
        CommentCountScore = CommentCount / 10 * 0.3
    # D: CommentLikeScore (20%)
    CommentListScore = 0
    _CommentListScore = 0
    if DataDic['BookAnalysis']['BookReview'] is not None:
        ReviewEvaluationList = DataDic['BookAnalysis']['BookReview']['Evaluations']
        for ReviewEvaluation in ReviewEvaluationList:
            Like = ReviewEvaluation['Like']
            Evaluation = ReviewEvaluation['Evaluation']
            if Evaluation == '긍정':
                evaluation = 1
            elif Evaluation == '부정':
                evaluation = -0.5
            else:
                evaluation = 0.5
            _CommentListScore += Like * evaluation
        
        if _CommentListScore >= 500:
            CommentListScore = 500 / 5 * 0.2
        elif _CommentListScore <= -500:
            CommentListScore = -500 / 5 * 0.2
        else:
            CommentListScore = _CommentListScore / 5 * 0.2
        
    ## BookScore 합산
    BookScore = RankScore + RankHistoryScores + CommentCountScore + CommentListScore

    return BookScore
    
##### 추가 후처리 사항 #####

## ProcessResponse 업데이트 및 저장
def ProcessResponseUpdate(MainKey, DataJsonPath, DataTempPath):
    # 오리지날 DataList 불러와서 변경사항 저장
    with open(DataJsonPath, 'r', encoding='utf-8') as DataListJson:
        DataList = json.load(DataListJson)
        
    if MainKey not in DataList[-1]:
        # TextDataList 업데이트
        for i in range(len(DataList)):
            try:
                DataTempJsonPath = os.path.join(DataTempPath, f"BookData_({DataList[i]['ISBN']})_{DataList[i]['Title']}.json")
                with open(DataTempJsonPath, 'r', encoding = 'utf-8') as DataTempJson:
                    DataTemp = json.load(DataTempJson)
                DataList[i][MainKey] = DataTemp[MainKey]
                ##### 추가 후처리 사항 #####
                BookScore = BookScoreCalculation(DataList[i])
                ##### 추가 후처리 사항 #####
                DataList[i]['BookScore'] = BookScore
            except:
                print(f"[ DataTempJsonPath Is None : >>> BookData_({DataList[i]['ISBN']})_{DataList[i]['Title']}.json <<< 파일 존재하지 않음 ]")
                continue
        
        # DataListJson 저장
        with open(DataJsonPath, 'w', encoding = 'utf-8') as DataListJson:
            json.dump(DataList, DataListJson, ensure_ascii = False, indent = 4)
           
################################
##### Process 진행 및 업데이트 #####
################################
## BookProcess 프롬프트 요청 및 결과물 Json화
def BookDataProcessUpdate(projectName, email, mode = "Master", MainKey = 'BookAnalysis', MessagesReview = "on"):
    print(f"< User: {email} | Project: {projectName} | BookDataProcessUpdate 시작 >")
    ## TotalBookData 경로 설정
    TotalBookDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s153_TrendData/s1532_BookData/s15321_TotalBookData"
    TotalBookDataJsonPath = os.path.join(TotalBookDataPath, 'TotalBookData.json')
    TotalBookDataTempPath = os.path.join(TotalBookDataPath, 'TotalBookDataTemp')
    
    ## 작업이 되지 않은 부분부터 totalBookDataList와 InputList 형성
    InputList = LoadTotalBookDataToInputList(TotalBookDataJsonPath, TotalBookDataTempPath)
    
    ## BookProcess
    InputCount = len(InputList)
    ProcessCount = 0
    
    while ProcessCount < InputCount:
        processCount = ProcessCount + 1
        InputDic = InputList[ProcessCount]
        BookInput = InputDic['BookText']
        CommentInput = InputDic['CommentText']
        CheckCount = InputDic['CommentCount']
        OutputDicList = []
        
        ## Process1: BookContextDefine Response 생성
        BookContextDefineResponse = ProcessResponse(projectName, email, "BestSellerContextDefine", BookInput, processCount, InputCount, BookContextDefineFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicList.append(BookContextDefineResponse)
        
        ## Process2: BookWMWMDefine Response 생성
        BookWMWMDefineResponse = ProcessResponse(projectName, email, "BestSellerWMWMDefine", BookInput, processCount, InputCount, BookWMWMDefineFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicList.append(BookWMWMDefineResponse)
        
        ## Process3: BookCommentAnalysis Response 생성
        if '구매자 리뷰가 0개, 없습니다.' not in CommentInput:
            BookCommentAnalysisResponse = ProcessResponse(projectName, email, "BestSellerCommentAnalysis", CommentInput, processCount, InputCount, BookCommentAnalysisFilter, CheckCount, "OpenAI", mode, MessagesReview)
        else:
            BookCommentAnalysisResponse = None
        OutputDicList.append(BookCommentAnalysisResponse)
            
        ## ProcessResponse 임시저장
        ProcessResponseTempSave(MainKey, InputDic, OutputDicList, TotalBookDataJsonPath, TotalBookDataTempPath)
        # 다음 아이템으로 이동
        ProcessCount += 1
    
    ## ProcessResponse 업데이트
    ProcessResponseUpdate(MainKey, TotalBookDataJsonPath, TotalBookDataTempPath)
    print(f"[ User: {email} | Project: {projectName} | BookDataProcessUpdate 완료 ]\n")
    
    ## ProcessResponse 업서트
    UpsertCollectionData(TotalBookDataTempPath, "Book")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241204_개정교육과정초등교과별이해연수'
    #########################################################################
    
    BookDataProcessUpdate(ProjectName, email)
