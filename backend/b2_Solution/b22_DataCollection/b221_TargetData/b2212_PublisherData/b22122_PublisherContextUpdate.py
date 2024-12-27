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
        OutputDic = outputJson['분석']
    except:
        return "PublisherContextDefine, JSON에서 오류 발생: '분석' 미포함"
    # Error3: 자료의 구조가 다를 때의 예외 처리
    if ('핵심슬로건' not in OutputDic or '목적' not in OutputDic or '이유' not in OutputDic or '질문' not in OutputDic or '주제' not in OutputDic or '전문가' not in OutputDic):
        return "PublisherContextDefine, JSON에서 오류 발생: JSONKeyError"
        
    return OutputDic

## Process2: PublisherContextDefine의 Filter(Error 예외처리)
def PublisherWMWMDefineFilter(Response):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "PublisherWMWMDefine, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 딕셔너리가 "매칭독자"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic = outputJson['분석']
    except:
        return "PublisherWMWMDefine, JSON에서 오류 발생: '분석' 미포함"
    # Error3: 자료의 구조가 다를 때의 예외 처리
    if '핵심문구' not in OutputDic:
        return "PublisherWMWMDefine, JSON에서 오류 발생: '핵심문구' 미포함"
    if not isinstance(OutputDic['핵심문구'], list):
        return "PublisherWMWMDefine, JSON에서 오류 발생: '핵심문구'가 리스트 형식이 아님"
    if ('욕구상태' not in OutputDic or '욕구상태선택이유' not in OutputDic or '이해상태' not in OutputDic or '이해상태선택이유' not in OutputDic or '마음상태' not in OutputDic or '마음상태선택이유' not in OutputDic or '행동상태' not in OutputDic or '행동상태선택이유' not in OutputDic or '정확도' not in OutputDic):
        return "PublisherWMWMDefine, JSON에서 오류 발생: JSONKeyError"
        
    return OutputDic

#######################
##### Process 진행 #####
#######################
## Process LLMResponse 함수
def ProcessResponse(projectName, email, Process, Input, ProcessCount, InputCount, FilterFunc, LLM, mode, MessagesReview):

    ErrorCount = 0
    
    while True:
        if LLM == "OpenAI":
            Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, messagesReview = MessagesReview)
        elif LLM == "Anthropic":
            Response, Usage, Model = ANTHROPIC_LLMresponse(projectName, email, Process, Input, ProcessCount, Mode = mode, messagesReview = MessagesReview)
        Filter = FilterFunc(Response)
        
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
    
## ProcessResponse Update 함수(프롬프트 요청 및 결과물 기존 Json에 업데이트)

## PublisherProcess 프롬프트 요청 및 결과물 Json화
def PublisherProcess(TotalPublisherDataPath, projectName, email, mode = "Master", MessagesReview = "on"):
    ## 작업이 되지 않은 부분부터 totalPublisherDataList와 InputList 형성
    totalPublisherDataList, inputList = LoadTotalPublisherDataToInputList(TotalPublisherDataPath)
    
    ## PublisherProcess
    StartPoint = 1
    InputList = inputList[StartPoint:]
    ProcessCount = 1
    InputCount = len(InputList)
    i = 0
    
    while i < InputCount:
        ProcessCount = i+1
        Input = InputList[i]['PublisherText']
        if Input != None:
            
            ## Process1: PublisherContextDefine Response 생성
            PublisherContextDefineOutputDic = ProcessResponse(projectName, email, "PublisherContextDefine", Input, ProcessCount, InputCount, PublisherContextDefineFilter, "OpenAI", mode, MessagesReview)
                
            ## Process2: PublisherCommentAnalysis Response 생성
            PublisherCommentAnalysisOutputDic = ProcessResponse(projectName, email, "PublisherWMWMDefine", Input, ProcessCount, InputCount, PublisherWMWMDefineFilter, "OpenAI", mode, MessagesReview)

            # ## ProcessResponse Update
            # for PublisherData in totalPublisherDataList:
            #     if PublisherData['ISBN'] == InputList[i]['ISBN']:
            #         ## PublisherCommentAnalysis
            #         if OutputDic2['평가'] == '없음':
            #             PublisherData['CommentAnalysis'] = None
            #         else:
            #             Evaluation = OutputDic2['평가']
            #             for k in range(len(Evaluation)):
            #                 PublisherData['CommentList'][k]['evaluation'] = Evaluation[k]
            #             Synthesis = OutputDic2['종합']
            #             Feedback = OutputDic2['피드백']
            #             CommentAnalysis = {'synthesis': Synthesis, 'feedback': Feedback}
            #             PublisherData['CommentAnalysis'] = CommentAnalysis
                    
            #         ## PublisherContextDefine
            #         Message = OutputDic1['한줄메세지']
            #         Reader = OutputDic1['독자키워드']
            #         Subject = OutputDic1['주제키워드']
            #         Purpose = OutputDic1['독자목적']
            #         Reason = OutputDic1['독자원인']
            #         Question = OutputDic1['독자질문']
            #         Comment = OutputDic1['독자리뷰']
            #         Importance = OutputDic1['독자만족도']
            #         Context = {"Message": Message, "Reader": Reader, "Subject": Subject, "Purpose": Purpose, "Reason": Reason, "Question": Question, "Comment": Comment, "Importance": Importance}
            #         PublisherData['Context'] = Context
            #         break
                
            # with open(TempTotalPublisherDataPath, 'w', encoding = 'utf-8') as TempPublishersJson:
            #     json.dump(totalPublisherDataList, TempPublishersJson, ensure_ascii = False, indent = 4)
            
        # 다음 아이템으로 이동
        i += 1

    return totalPublisherDataList

## PublisherContextDefine 프롬프트 요청 및 결과물 TotalPublisherDataList에 업데이트 및 점수배점
def PublisherContextDefineUpdate(projectName = "Publisher", email = "General", process1 = "PublisherContextDefine", process2 = "PublisherWMWMDefine", messagesReview = "on", mode = "Master"):
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
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241204_개정교육과정초등교과별이해연수'
    #########################################################################
    TotalPublisherDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_TargetData/s1512_PublisherData/s15121_TotalPublisherData/TotalPublisherData.json"
    PublisherContextDefineProcess(TotalPublisherDataPath, ProjectName, email)