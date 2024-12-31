import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import OpenAI_LLMresponse, ANTHROPIC_LLMresponse

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
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "BookContextDefine, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 딕셔너리가 "매칭독자"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic = outputJson['매칭독자']
    except:
        return "BookContextDefine, JSON에서 오류 발생: '매칭독자' 미포함"
    # Error3: 자료의 구조가 다를 때의 예외 처리
    if ('핵심메세지' not in OutputDic or '독자목적' not in OutputDic or '독자이유' not in OutputDic or '독자질문' not in OutputDic or '독자리뷰' not in OutputDic or '독자만족도' not in OutputDic or '독자키워드' not in OutputDic or '주제키워드' not in OutputDic):
        return "BookContextDefine, JSON에서 오류 발생: JSONKeyError"
        
    return OutputDic

## Process2: BookWMWMDefine의 Filter(Error 예외처리)
def BookWMWMDefineFilter(Response, CheckCount):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "BookWMWMDefine, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 딕셔너리가 "매칭독자"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic = outputJson['분석']
    except:
        return "BookWMWMDefine, JSON에서 오류 발생: '매칭독자' 미포함"
    # Error3: 자료의 구조가 다를 때의 예외 처리
    if ('핵심문구' not in OutputDic or '욕구상태' not in OutputDic or '욕구상태선택이유' not in OutputDic or '이해상태' not in OutputDic or '이해상태선택이유' not in OutputDic or '마음상태' not in OutputDic or '마음상태선택이유' not in OutputDic or '행동상태' not in OutputDic or '행동상태선택이유' not in OutputDic or '정확도' not in OutputDic):
        return "BookWMWMDefine, JSON에서 오류 발생: JSONKeyError"
        
    return OutputDic

## Process3: BookCommentAnalysis의 Filter(Error 예외처리)
def BookCommentAnalysisFilter(Response, CheckCount):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "BookCommentAnalysis, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 딕셔너리가 "매칭독자"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic = outputJson['리뷰평가']
    except:
        return "BookCommentAnalysis, JSON에서 오류 발생: '리뷰평가' 미포함"
    # Error3: 자료의 구조가 다를 때의 예외 처리
    if ('평가' not in OutputDic or '종합' not in OutputDic or '피드백' not in OutputDic):
        return "BookCommentAnalysis, JSON에서 오류 발생: JSONKeyError"
    # Error4: 자료의 구조가 다를 때의 예외 처리
    if len(OutputDic['평가']) < CheckCount:
        return "BookCommentAnalysis, JSON에서 오류 발생: 평가수 누락"
    else:
        OutputDic['평가'] = OutputDic['평가'][:CheckCount]
    # '평가' 부분 리스트화
    OutputDic['평가'] = [list(item.values())[0] for item in OutputDic['평가']]
    # Error5: 자료의 구조가 다를 때의 예외 처리
    if not isinstance(OutputDic['피드백'], list):
        return "BookCommentAnalysis, JSON에서 오류 발생: 피드백 형식이 리스트가 아님"
    
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
                Message = OutputDicList[0]['핵심메세지']
                Context = {"Purpose": OutputDicList[0]['독자목적'], "Reason": OutputDicList[0]['독자이유'], "Question": OutputDicList[0]['독자질문'], "Review": OutputDicList[0]['독자리뷰'], "Subject": OutputDicList[0]['주제키워드'], "Person": OutputDicList[0]['독자키워드'], "Importance": OutputDicList[0]['독자만족도']}
                Phrases = OutputDicList[1]['핵심문구']
                WMWM = {"Needs": OutputDicList[1]['욕구상태'], "ReasonOfNeeds": OutputDicList[1]['욕구상태선택이유'], "Wisdom": OutputDicList[1]['이해상태'], "ReasonOfWisdom": OutputDicList[1]['이해상태선택이유'], "Mind": OutputDicList[1]['마음상태'], "ReasonOfPotentialMind": OutputDicList[1]['마음상태선택이유'], "Wildness": OutputDicList[1]['행동상태'], "ReasonOfWildness": OutputDicList[1]['행동상태선택이유'], "Accuracy": OutputDicList[1]['정확도']}
                if OutputDicList[2] is not None:
                    ReviewPhrases = OutputDicList[2]['종합']
                    EvaluationList = OutputDicList[2]['평가']
                    ReviewEvaluation = []
                    for j, Evaluation in enumerate(EvaluationList):
                        ReviewEvaluation.append({'Evaluation': Evaluation, 'Like': InputDic['CommentLikeList'][j]})
                    Review = {"ReviewEvaluation": ReviewEvaluation, "Feedback": OutputDicList[2]['피드백']}
                else:
                    ReviewPhrases = None
                    Review = None
                DataTemp = {MainKey: {'Message': Message, 'Context': Context, 'Phrases': Phrases, 'WMWM': WMWM, 'ReviewPhrases': ReviewPhrases, 'Review': Review}}
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
    ReviewEvaluationList = DataDic['BookAnalysis']['Review']['ReviewEvaluation']
    _CommentListScore = 0
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
            DataTempJsonPath = os.path.join(DataTempPath, f"BookData_({DataList[i]['ISBN']})_{DataList[i]['Title']}.json")
            with open(DataTempJsonPath, 'r', encoding = 'utf-8') as DataTempJson:
                DataTemp = json.load(DataTempJson)
            DataList[i][MainKey] = DataTemp[MainKey]
            ##### 추가 후처리 사항 #####
            BookScore = BookScoreCalculation(DataList[i])
            ##### 추가 후처리 사항 #####
            DataList[i]['BookScore'] = BookScore
        
        # DataListJson 저장
        with open(DataJsonPath, 'w', encoding = 'utf-8') as DataListJson:
            json.dump(DataList, DataListJson, ensure_ascii = False, indent = 4)
           
################################
##### Process 진행 및 업데이트 #####
################################
## BookProcess 프롬프트 요청 및 결과물 Json화
def BookProcessUpdate(projectName, email, mode = "Master", MainKey = 'BookAnalysis', MessagesReview = "on"):
    ## TotalBookData 경로 설정
    TotalBookDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s152_TrendData/s1522_BookData/s15221_TotalBookData"
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

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241204_개정교육과정초등교과별이해연수'
    #########################################################################
    
    BookProcessUpdate(ProjectName, email)