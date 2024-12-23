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
## TotalPublisherDataList 로드
def LoadTotalPublisherDataList(TotalPublisherDataJsonPath):
    with open(TotalPublisherDataJsonPath, 'r', encoding = 'utf-8') as PublisherJson:
        TotalPublisherDataList = json.load(PublisherJson)
    
    return TotalPublisherDataList

## totalPublisherDataList로 필터
def FilterTotalPublisherDataList(TotalPublisherDataPath):
    TotalPublisherDataList = LoadTotalPublisherDataList(TotalPublisherDataPath)
    ## TotalPublisherDataList중 업데이트가 필요한 부분 선정(이중 분석 방지)
    totalPublisherDataList = []
    for PublisherData in TotalPublisherDataList:
        if ('Vector' not in PublisherData):
            totalPublisherDataList.append(PublisherData)
    
    return totalPublisherDataList

## LoadTotalPublisherData의 inputList 치환
def LoadTotalPublisherDataToInputList(TotalPublisherDataPath):
    totalPublisherDataList = FilterTotalPublisherDataList(TotalPublisherDataPath)
    
    InputList = []
    for i, PublisherData in enumerate(totalPublisherDataList):
        PublisherId = PublisherData['Id']
        PublisherName = f"[출판사명] {PublisherData['PublisherInformation']['Name']}\n\n"
        Classification = f"[주요항목] {PublisherData['PublisherInformation']['Classification']}\n\n"
        Subcategories = f"[세부항목] {PublisherData['PublisherInformation']['Subcategories']}\n\n"
        HomePage = f"[홈페이지] {PublisherData['PublisherInformation']['HomePage']}\n\n"
        WebPageKoreanTxtPath = f"{PublisherData['PublisherInformation']['WebPageTxtPath'].rsplit('.', 1)[0]}_Extract.txt"
        if 'None' in WebPageKoreanTxtPath:
            PublisherDataText = None
        else:
            with open(WebPageKoreanTxtPath, 'r', encoding = 'utf-8') as f:
                PageBody = f.read() 
            HomePageBody = f"[홈페이지내용발췌] {PageBody}"
            if PageBody != '':
                PublisherDataText = PublisherName + Classification + Subcategories + HomePage + HomePageBody
            else:
                PublisherDataText = None
   
        InputDic = {'Id': i, 'PublisherId': PublisherId, 'PublisherName': PublisherData['PublisherInformation']['Name'], 'PublisherText': PublisherDataText}
        InputList.append(InputDic)
        
    return totalPublisherDataList, InputList

######################
##### Filter 조건 #####
######################
## Process1: PublisherContextDefine의 Filter(Error 예외처리)
def PublisherContextDefineFilter(Response):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "PublisherContextDefine, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 딕셔너리가 "매칭독자"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic = outputJson['매칭독자']
    except:
        return "PublisherContextDefine, JSON에서 오류 발생: '매칭독자' 미포함"
    # Error3: 자료의 구조가 다를 때의 예외 처리
    if ('독자키워드' not in OutputDic or '주제키워드' not in OutputDic or '한줄메세지' not in OutputDic or '독자목적' not in OutputDic or '독자원인' not in OutputDic or '독자질문' not in OutputDic or '독자리뷰' not in OutputDic or '독자만족도' not in OutputDic):
        return "PublisherContextDefine, JSON에서 오류 발생: JSONKeyError"
        
    return OutputDic

## Process2: PublisherContextDefine의 Filter(Error 예외처리)
def PublisherCommentAnalysisFilter(Response, CommentCount):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "PublisherCommentAnalysis, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 딕셔너리가 "매칭독자"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic = outputJson['리뷰평가']
    except:
        return "PublisherCommentAnalysis, JSON에서 오류 발생: '리뷰평가' 미포함"
    # Error4: 리뷰가 없을 경우 처리
    if OutputDic == '없음':
        return {'평가': '없음', '종합': '없음', '피드백': '없음'}
    # Error5: 자료의 구조가 다를 때의 예외 처리
    if ('평가' not in OutputDic or '종합' not in OutputDic or '피드백' not in OutputDic):
        return "PublisherCommentAnalysis, JSON에서 오류 발생: JSONKeyError"
    # Error6: 자료의 구조가 다를 때의 예외 처리
    if len(OutputDic['평가']) < CommentCount:
        return "PublisherCommentAnalysis, JSON에서 오류 발생: 평가수 누락"
    else:
        OutputDic['평가'] = OutputDic['평가'][:CommentCount]
    # '평가' 부분 리스트화
    OutputDic['평가'] = [list(item.values())[0] for item in OutputDic['평가']]
    # '피드백' 부분 리스트화
    OutputDic['피드백'] = [list(item.values())[0] for item in OutputDic['피드백']]
    
    return OutputDic

#######################
##### Process 진행 #####
#######################
## PublisherContextDefine 프롬프트 요청 및 결과물 Json화
def PublisherContextDefineProcess(TotalPublisherDataPath, projectName, email, Process1 = "PublisherContextDefine", Process2 = "PublisherCommentAnalysis", MessagesReview = "on", mode = "Master"):
    ## 작업이 되지 않은 부분부터 totalPublisherDataList와 InputList 형성
    totalPublisherDataList, inputList = LoadTotalPublisherDataToInputList(TotalPublisherDataPath)
    StartPoint = 0
    
    ## WMWMDefineProcess
    InputList = inputList[StartPoint:]
    ProcessCount = 1
    ErrorCount1 = 0
    ErrorCount2 = 0
    InputCount = len(InputList)
    i = 0
    
    while i < InputCount:
        ProcessCount = i+1
        Input = InputList[i]['Publisher']
        
        # 상태 추적 변수
        process1_complete = False
        process2_complete = False

        ## PublisherContextDefine Response 생성
        while not process1_complete:
            Response1, Usage, Model = OpenAI_LLMresponse(projectName, email, Process1, Input, ProcessCount, Mode = mode, messagesReview = MessagesReview)
            Filter1 = PublisherContextDefineFilter(Response1)

            if isinstance(Filter1, str):
                print(f"Project: {projectName} | Process: {Process1} {ProcessCount}/{InputCount} | {Filter1}")
                ErrorCount1 += 1
                print(f"Project: {projectName} | Process: {Process1} {ProcessCount}/{InputCount} | 오류횟수 {ErrorCount1}회, 2분 후 프롬프트 재시도")
                time.sleep(120)
                if ErrorCount1 == 5:
                    sys.exit(f"Project: {Date} {projectName} | Process: {Process1} {ProcessCount}/{InputCount} | 오류횟수 {ErrorCount1}회 초과, 프롬프트 종료")
                continue
            else:
                OutputDic1 = Filter1
                print(f"Project: {Date} {projectName} | Process: {Process1} {ProcessCount}/{InputCount} | JSONDecode 완료")
                ErrorCount1 = 0
                process1_complete = True
            
        ## PublisherCommentAnalysis Response 생성
        while not process2_complete:
            Response2, Usage, Model = OpenAI_LLMresponse(projectName, email, Process2, Input2, ProcessCount, Mode = mode, messagesReview = MessagesReview)
            Filter2 = PublisherCommentAnalysisFilter(Response2, CommentCount)

            if isinstance(Filter2, str):
                print(f"Project: {Date} {projectName} | Process: {Process2} {ProcessCount}/{InputCount} | {Filter2}")
                ErrorCount2 += 1
                print(f"Project: {Date} {projectName} | Process: {Process2} {ProcessCount}/{InputCount} | 오류횟수 {ErrorCount2}회, 2분 후 프롬프트 재시도")
                time.sleep(120)
                if ErrorCount2 == 5:
                    sys.exit(f"Project: {Date} {projectName} | Process: {Process2} {ProcessCount}/{InputCount} | 오류횟수 {ErrorCount2}회 초과, 프롬프트 종료")
                continue
            else:
                OutputDic2 = Filter2
                print(f"Project: {Date} {projectName} | Process: {Process2} {ProcessCount}/{InputCount} | JSONDecode 완료")
                ErrorCount2 = 0
                process2_complete = True

        ## totalPublisherDataList 업데이트
        for PublisherData in totalPublisherDataList:
            if PublisherData['ISBN'] == InputList[i]['ISBN']:
                ## PublisherCommentAnalysis
                if OutputDic2['평가'] == '없음':
                    PublisherData['CommentAnalysis'] = None
                else:
                    Evaluation = OutputDic2['평가']
                    for k in range(len(Evaluation)):
                        PublisherData['CommentList'][k]['evaluation'] = Evaluation[k]
                    Synthesis = OutputDic2['종합']
                    Feedback = OutputDic2['피드백']
                    CommentAnalysis = {'synthesis': Synthesis, 'feedback': Feedback}
                    PublisherData['CommentAnalysis'] = CommentAnalysis
                
                ## PublisherContextDefine
                Message = OutputDic1['한줄메세지']
                Reader = OutputDic1['독자키워드']
                Subject = OutputDic1['주제키워드']
                Purpose = OutputDic1['독자목적']
                Reason = OutputDic1['독자원인']
                Question = OutputDic1['독자질문']
                Comment = OutputDic1['독자리뷰']
                Importance = OutputDic1['독자만족도']
                Context = {"Message": Message, "Reader": Reader, "Subject": Subject, "Purpose": Purpose, "Reason": Reason, "Question": Question, "Comment": Comment, "Importance": Importance}
                PublisherData['Context'] = Context
                break
            
        with open(TempTotalPublisherDataPath, 'w', encoding = 'utf-8') as TempPublishersJson:
            json.dump(totalPublisherDataList, TempPublishersJson, ensure_ascii = False, indent = 4)
            
        # 다음 아이템으로 이동
        i += 1

    return totalPublisherDataList

## PublisherContextDefine 프롬프트 요청 및 결과물 TotalPublisherDataList에 업데이트 및 점수배점
def PublisherContextDefineUpdate(projectName = "Publisher", email = "General", process1 = "PublisherContextDefine", process2 = "PublisherCommentAnalysis", messagesReview = "on", mode = "Master"):
    TotalPublisherDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_TargetData/s1512_PublisherData/s15121_TotalPublisherData/TotalPublisherData.json"
    TotalPublisherDataList, Date = LoadTotalPublisherDataList(TotalPublisherDataPath)
    
    print(f"< User: {email} | Project: {Date} {projectName} | Publisher ContextDefine/CommentAnalysis 시작 >")
    ## 0: TotalPublisherDataList 업데이트 여부 확인
    NonUpdate = False
    for PublisherData in TotalPublisherDataList:
        if ('Context' not in PublisherData) or ('CommentAnalysis' not in PublisherData) or ('PublisherScore' not in PublisherData):
            NonUpdate = True
            break

    if NonUpdate:
        totalPublisherDataList = PublisherContextDefineProcess(TotalPublisherDataPath, projectName, email, Process1 = process1, Process2 = process2, MessagesReview = messagesReview, mode = mode)
        
        ## 1: TotalPublisherDataList 업데이트
        for bookData in totalPublisherDataList:
            for i in range(len(TotalPublisherDataList)):
                if bookData['ISBN'] == TotalPublisherDataList[i]['ISBN']:
                    print(f"{bookData['ISBN']}\n{PublisherData['ISBN']}\n")
                    TotalPublisherDataList[i] = bookData
                    break
        
        ## 2: TotalPublisherDataList 점수배점
        for i in range(len(TotalPublisherDataList)):
            # A: RankScore (40%)
            Rank = TotalPublisherDataList[i]['Rank'][-1]['Rank']
            if Rank <= 50:
                RankScore = (51 - Rank) * 2 * 0.4
            else:
                RankScore = 0
            # B: RankHistoryScore (10%)
            RankHistory = TotalPublisherDataList[i]['Rank']
            if len(RankHistory) >= 10:
                RankHistory = RankHistory[-10:]
                
            RankScores = 0
            for rank in RankHistory:
                _Rank = rank['Rank']
                if _Rank <= 50:
                    RankScores += (51 - _Rank) / 5
            RankHistoryScores = RankScores * 0.1
            # C: CommentCountScore (30%)
            CommentCount = TotalPublisherDataList[i]['CommentsCount']
            if CommentCount >= 1000:
                CommentCountScore = 1000 / 10 * 0.3
            else:
                CommentCountScore = CommentCount / 10 * 0.3
            # D: CommentLikeScore (20%)
            CommentList = TotalPublisherDataList[i]['CommentList']
            _CommentListScore = 0
            for Comment in CommentList:
                Like = Comment['like']
                Evaluation = Comment['evaluation']
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
                
            ## PublisherScore 합산
            PublisherScore = RankScore + RankHistoryScores + CommentCountScore + CommentListScore
        
            TotalPublisherDataList[i]['PublisherScore'] = PublisherScore
            
        with open(TotalPublisherDataPath, 'w', encoding = 'utf-8') as PublishersJson:
            json.dump(TotalPublisherDataList, PublishersJson, ensure_ascii = False, indent = 4)
        print(f"< User: {email} | Project: {Date} {projectName} | Publisher ContextDefine/CommentAnalysis 완료 >")
        
    else:
        print(f"[ User: {email} | Project: {Date} {projectName} | Publisher ContextDefine/CommentAnalysis는 이미 완료됨 ]\n")

if __name__ == "__main__":
    TotalPublisherDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_TargetData/s1512_PublisherData/s15121_TotalPublisherData/TotalPublisherData.json"
    totalPublisherDataList, InputList = LoadTotalPublisherDataToInputList(TotalPublisherDataPath)
    print(InputList[1])