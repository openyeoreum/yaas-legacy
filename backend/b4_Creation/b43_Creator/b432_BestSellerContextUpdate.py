import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import Date, FindDataframeFilePaths, LoadOutputMemory, SaveOutputMemory, AddExistedWMWMDefineToDB, AddWMWMDefineChunksToDB, WMWMDefineCountLoad, WMWMDefineCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

#########################
##### InputList 생성 #####
#########################
## TotalBookDataList 로드
def LoadTotalBookDataList(TotalBookDataPath):
    with open(TotalBookDataPath, 'r', encoding = 'utf-8') as BooksJson:
        TotalBookDataList = json.load(BooksJson)
    
    ## TotalBookDataList중 업데이트가 필요한 부분 선정(이중 분석 방지)
    totalBookDataList = []
    for BookData in TotalBookDataList:
        if ('Context' not in BookData) and ('CommentAnalysis' not in BookData):
            totalBookDataList.append(BookData)
    
    return totalBookDataList

## LoadTotalBookData의 inputList 치환
def LoadTotalBookDataToInputList(TotalBookDataPath):
    totalBookDataList = LoadTotalBookDataList(TotalBookDataPath)
    
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
        for j in range(len(CommentList)):
            CommentText = f"구매자{j+1}: {CommentList[j]['comment']}\n좋아요({CommentList[j]['like']})"
            CommentTextList.append(CommentText)
        CommentTexts = CommentsCountText + '\n\n'.join(CommentTextList)
        
        BookDataText = TitleText + PublishedDateText + AuthorText + AuthorInfoText + IntroCategoryText + IntroText + BookIndexText + BookReviewsText + CommentTexts
   
        InputDic = {'Id': i+1, 'ISBN': ISBN, 'Book': BookDataText, 'Comment': CommentTexts, 'CommentCount': len(CommentList)}
        InputList.append(InputDic)
        
    return totalBookDataList, InputList

######################
##### Filter 조건 #####
######################
## Process1: BSContextDefine의 Filter(Error 예외처리)
def BSContextDefineFilter(Response):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "BSContextDefine, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 딕셔너리가 "매칭독자"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic = outputJson['매칭독자']
    except:
        return "BSContextDefine, JSON에서 오류 발생: '매칭독자' 미포함"
    # Error3: 자료의 구조가 다를 때의 예외 처리
    if ('독자키워드' not in OutputDic or '주제키워드' not in OutputDic or '한줄메세지' not in OutputDic or '독자목적' not in OutputDic or '독자원인' not in OutputDic or '독자질문' not in OutputDic or '독자리뷰' not in OutputDic or '독자만족도' not in OutputDic):
        return "BSContextDefine, JSON에서 오류 발생: JSONKeyError"
        
    return OutputDic

## Process2: BSContextDefine의 Filter(Error 예외처리)
def BSCommentAnalysisFilter(Response, CommentCount):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "BSCommentAnalysis, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 딕셔너리가 "매칭독자"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic = outputJson['리뷰평가']
    except:
        return "BSCommentAnalysis, JSON에서 오류 발생: '리뷰평가' 미포함"
    # Error4: 리뷰가 없을 경우 처리
    if OutputDic == '없음':
        return {'평가': '없음', '종합': '없음', '피드백': '없음'}
    # Error5: 자료의 구조가 다를 때의 예외 처리
    if ('평가' not in OutputDic or '종합' not in OutputDic or '피드백' not in OutputDic):
        return "BSCommentAnalysis, JSON에서 오류 발생: JSONKeyError"
    # Error6: 자료의 구조가 다를 때의 예외 처리
    if len(OutputDic['평가']) != CommentCount:
        return "BSCommentAnalysis, JSON에서 오류 발생: 평가수 누락"
    # '평가' 부분 리스트화
    OutputDic['평가'] = [list(item.values())[0] for item in OutputDic['평가']]
    # '피드백' 부분 리스트화
    OutputDic['피드백'] = [list(item.values())[0] for item in OutputDic['피드백']]
    
    return OutputDic

#######################
##### Process 진행 #####
#######################
## BSContextDefine 프롬프트 요청 및 결과물 Json화
def BestSellerContextDefineProcess(Process1 = "BestSellerContextDefine", Process2 = "BestSellerCommentAnalysis", MessagesReview = "on"):   
    ## TotalBookData와 임시TotalBookData 경로 
    TotalBookDataPath = "/yaas/storage/s1_Yeoreum/s18_MarketDataStorage/s181_BookData/s1811_TotalBookData/TotalBookData.json"

    ## 작업이 되지 않은 부분부터 totalBookDataList와 InputList 형성
    totalBookDataList, inputList = LoadTotalBookDataToInputList(TotalBookDataPath)
    Date = totalBookDataList[0]['Rank'][-1]['Date']
    TempTotalBookDataPath = f"/yaas/storage/s1_Yeoreum/s18_MarketDataStorage/s181_BookData/s1811_TotalBookData/TempTotalBookData/{Date}_TempTotalBookData.json"
    StartPoint = 0
    if os.path.exists(TempTotalBookDataPath):
        with open(TempTotalBookDataPath, 'r', encoding = 'utf-8') as TempBooksJson:
            totalBookDataList = json.load(TempBooksJson)
            for StartPoint in range(len(totalBookDataList)):
                if 'Context' not in totalBookDataList[StartPoint]:
                    break
    InputList = inputList[StartPoint:]
    
    ## General 하이퍼 파라미터
    email = "General"
    projectName = "BestSeller"
    mode = "Master"
    
    ## WMWMDefineProcess
    ProcessCount = 1
    ErrorCount1 = 0
    ErrorCount2 = 0
    InputCount = len(InputList)
    projectName = "BestSeller"
    email = "General"
    mode = "Master"
    i = 0
    
    while i < InputCount:
        ProcessCount = i+1
        Input1 = InputList[i]['Book']
        Input2 = InputList[i]['Comment']
        CommentCount = InputList[i]['CommentCount']
        
        # 상태 추적 변수
        process1_complete = False
        process2_complete = False

        ## BestSellerContextDefine Response 생성
        while not process1_complete:
            Response1, Usage, Model = OpenAI_LLMresponse(projectName, email, Process1, Input1, ProcessCount, Mode = mode, messagesReview = MessagesReview)
            Filter1 = BSContextDefineFilter(Response1)

            if isinstance(Filter1, str):
                print(f"Project: {projectName} | Process: {Process1} {ProcessCount}/{InputCount} | {Filter1}")
                ErrorCount1 += 1
                print(f"Project: {projectName} | Process: {Process1} {ProcessCount}/{InputCount} | 오류횟수 {ErrorCount1}회, 2분 후 프롬프트 재시도")
                time.sleep(120)
                if ErrorCount1 == 5:
                    sys.exit(f"Project: {projectName} | Process: {Process1} {ProcessCount}/{InputCount} | 오류횟수 {ErrorCount1}회 초과, 프롬프트 종료")
                continue
            else:
                OutputDic1 = Filter1
                print(f"Project: {projectName} | Process: {Process1} {ProcessCount}/{InputCount} | JSONDecode 완료")
                ErrorCount1 = 0
                process1_complete = True
            
        ## BestSellerCommentAnalysis Response 생성
        while not process2_complete:
            Response2, Usage, Model = OpenAI_LLMresponse(projectName, email, Process2, Input2, ProcessCount, Mode = mode, messagesReview = MessagesReview)
            Filter2 = BSCommentAnalysisFilter(Response2, CommentCount)

            if isinstance(Filter2, str):
                print(f"Project: {projectName} | Process: {Process2} {ProcessCount}/{InputCount} | {Filter2}")
                ErrorCount2 += 1
                print(f"Project: {projectName} | Process: {Process2} {ProcessCount}/{InputCount} | 오류횟수 {ErrorCount2}회, 2분 후 프롬프트 재시도")
                time.sleep(120)
                if ErrorCount2 == 5:
                    sys.exit(f"Project: {projectName} | Process: {Process2} {ProcessCount}/{InputCount} | 오류횟수 {ErrorCount2}회 초과, 프롬프트 종료")
                continue
            else:
                OutputDic2 = Filter2
                print(f"Project: {projectName} | Process: {Process2} {ProcessCount}/{InputCount} | JSONDecode 완료")
                ErrorCount2 = 0
                process2_complete = True

        ## totalBookDataList 업데이트
        for BookData in totalBookDataList:
            if BookData['ISBN'] == InputList[i]['ISBN']:
                ## BestSellerCommentAnalysis
                if OutputDic2['평가'] == '없음':
                    BookData['CommentAnalysis'] = None
                else:
                    Evaluation = OutputDic2['평가']
                    for k in range(len(Evaluation)):
                        BookData['CommentList'][k]['evaluation'] = Evaluation[k]
                    Synthesis = OutputDic2['종합']
                    Feedback = OutputDic2['피드백']
                    CommentAnalysis = {'synthesis': Synthesis, 'feedback': Feedback}
                    BookData['CommentAnalysis'] = CommentAnalysis
                
                ## BestSellerContextDefine
                Message = OutputDic1['한줄메세지']
                Reader = OutputDic1['독자키워드']
                Subject = OutputDic1['주제키워드']
                Purpose = OutputDic1['독자목적']
                Reason = OutputDic1['독자원인']
                Question = OutputDic1['독자질문']
                Comment = OutputDic1['독자리뷰']
                Importance = OutputDic1['독자만족도']
                Context = {"Message": Message, "Reader": Reader, "Subject": Subject, "Purpose": Purpose, "Reason": Reason, "Question": Question, "Comment": Comment, "Importance": Importance}
                BookData['Context'] = Context
                break
            
        with open(TempTotalBookDataPath, 'w', encoding = 'utf-8') as TempBooksJson:
            json.dump(totalBookDataList, TempBooksJson, ensure_ascii = False, indent = 4)
            
        # 다음 아이템으로 이동
        i += 1

    return totalBookDataList

## BSContextDefine 프롬프트 요청 및 결과물 TotalBookDataList에 업데이트 및 점수배점
# def BestSellerContextDefineUpdate():

if __name__ == "__main__":

    BestSellerContextDefineProcess()