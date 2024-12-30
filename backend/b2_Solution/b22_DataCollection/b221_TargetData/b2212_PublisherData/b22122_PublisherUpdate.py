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
## totalPublisherDataList로 로드(업데이트가 필요한 부분 선정, 이중 분석 방지)
def LoadTotalPublisherDataList(TotalPublisherDataJsonPath, MainKey):
    ## TotalPublisherDataList 로드
    with open(TotalPublisherDataJsonPath, 'r', encoding = 'utf-8') as PublisherJson:
        TotalPublisherDataList = json.load(PublisherJson)
    ## TotalPublisherDataList중 업데이트가 필요한 부분 선정, 이중 분석 방지
    totalPublisherDataList = []
    for PublisherData in TotalPublisherDataList:
        if (MainKey not in PublisherData):
            totalPublisherDataList.append(PublisherData)
    
    return totalPublisherDataList

## LoadTotalPublisherData의 inputList 치환
def LoadTotalPublisherDataToInputList(TotalPublisherDataJsonPath, MainKey, MaxTextLength = 4000):
    totalPublisherDataList = LoadTotalPublisherDataList(TotalPublisherDataJsonPath, MainKey)
    
    ## InputList 생성
    InputList = []
    for i, PublisherData in enumerate(totalPublisherDataList):
        PublisherId = PublisherData['Id']
        PublisherName = f"[출판사명] {PublisherData['PublisherInformation']['Name']}\n\n"
        Classification = f"[주요항목] {PublisherData['PublisherInformation']['Classification']}\n\n"
        Subcategories = f"[세부항목] {PublisherData['PublisherInformation']['Subcategories']}\n\n"
        HomePage = f"[홈페이지] {PublisherData['PublisherInformation']['HomePage']}\n\n"
        WebPageKoreanTxtPath = f"{PublisherData['PublisherInformation']['WebPageTXTPath'].rsplit('.', 1)[0]}_Extract.txt"
        if 'None' in WebPageKoreanTxtPath:
            PublisherDataText = None
        else:
            with open(WebPageKoreanTxtPath, 'r', encoding = 'utf-8') as f:
                PageBody = f.read()
                if len(PageBody) > MaxTextLength:
                    PageBody = PageBody[:MaxTextLength] + "..."
                    
            HomePageBody = f"[홈페이지내용발췌] {PageBody}"
            if PageBody != '':
                PublisherDataText = PublisherName + Classification + Subcategories + HomePage + HomePageBody
            else:
                PublisherDataText = None
            
        InputDic = {'Id': i, 'PublisherId': PublisherId, 'PublisherName': PublisherData['PublisherInformation']['Name'], 'PublisherText': PublisherDataText}
        InputList.append(InputDic)
        
    return InputList

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

## Process3: PublisherServiceDemandFilter의 Filter(Error 예외처리)
def PublisherServiceDemandFilter(Response):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "PublisherServiceDemand, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 딕셔너리가 "매칭독자"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic = outputJson['수요']
    except:
        return "PublisherServiceDemand, JSON에서 오류 발생: '분석' 미포함"
    # Error3: 자료의 구조가 다를 때의 예외 처리
    if '핵심문구' not in OutputDic:
        return "PublisherServiceDemand, JSON에서 오류 발생: '핵심문구' 미포함"
    if not isinstance(OutputDic['핵심문구'], list):
        return "PublisherServiceDemand, JSON에서 오류 발생: '핵심문구'가 리스트 형식이 아님"
    if ('텍스트북' not in OutputDic or '텍스트북수요정도' not in OutputDic or '오디오북' not in OutputDic or '오디오북수요정도' not in OutputDic or '비디오북' not in OutputDic or '비디오북수요정도' not in OutputDic or '기타' not in OutputDic or '기타수요정도' not in OutputDic):
        return "PublisherServiceDemand, JSON에서 오류 발생: JSONKeyError"
        
    return OutputDic

#######################
##### Process 응답 #####
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
        if DataList[i]['Id'] == InputDic['PublisherId']:
            if OutputDicList != []:
                Slogan = OutputDicList[0]['핵심슬로건']
                Context = {"Purpose": OutputDicList[0]['목적'], "Reason": OutputDicList[0]['이유'], "Question": OutputDicList[0]['질문'], "Subject": OutputDicList[0]['주제'], "Person": OutputDicList[0]['전문가'], "Importance": OutputDicList[0]['정확도']}
                Phrases = OutputDicList[1]['핵심문구']
                WMWM = {"Needs": OutputDicList[1]['욕구상태'], "ReasonOfNeeds": OutputDicList[1]['욕구상태선택이유'], "Wisdom": OutputDicList[1]['이해상태'], "ReasonOfWisdom": OutputDicList[1]['이해상태선택이유'], "Mind": OutputDicList[1]['마음상태'], "ReasonOfPotentialMind": OutputDicList[1]['마음상태선택이유'], "Wildness": OutputDicList[1]['행동상태'], "ReasonOfWildness": OutputDicList[1]['행동상태선택이유'], "Accuracy": OutputDicList[1]['정확도']}
                DemandPhrases = OutputDicList[2]['핵심문구']
                Demand = {"Textbook": OutputDicList[2]['텍스트북'], "TextbookDemand": OutputDicList[2]['텍스트북수요정도'], "Audiobook": OutputDicList[2]['오디오북'], "AudiobookDemand": OutputDicList[2]['오디오북수요정도'], "Videobook": OutputDicList[2]['비디오북'], "VideobookDemand": OutputDicList[2]['비디오북수요정도'], "ETC": OutputDicList[2]['기타'], "ETCDemand": OutputDicList[2]['기타수요정도']}
                DataTemp = {MainKey: {'Slogan': Slogan, 'Context': Context, 'Phrases': Phrases, 'WMWM': WMWM, 'DemandPhrases': DemandPhrases, 'Demand': Demand}}
            else:
                DataTemp = {MainKey: None}
            
            # DataTempJson 저장
            DataTempJsonPath = os.path.join(DataTempPath, f"PublisherData_({DataList[i]['Id']})_{DataList[i]['PublisherInformation']['Name']}.json")
            with open(DataTempJsonPath, 'w', encoding = 'utf-8') as DataTempJson:
                json.dump(DataTemp, DataTempJson, ensure_ascii = False, indent = 4)
            break
        
## ProcessResponse 업데이트
def ProcessResponseUpdate(MainKey, DataJsonPath, DataTempPath):
    # 오리지날 DataList 불러와서 변경사항 저장
    with open(DataJsonPath, 'r', encoding='utf-8') as DataListJson:
        DataList = json.load(DataListJson)
        
    if MainKey not in DataList[-1]:
        # TextDataList 업데이트
        for i in range(len(DataList)):
            DataTempJsonPath = os.path.join(DataTempPath, f"PublisherData_({DataList[i]['Id']})_{DataList[i]['PublisherInformation']['Name']}.json")
            with open(DataTempJsonPath, 'r', encoding = 'utf-8') as DataTempJson:
                DataTemp = json.load(DataTempJson)
            DataList[i][MainKey] = DataTemp[MainKey]
        
        # DataListJson 저장
        with open(DataJsonPath, 'w', encoding = 'utf-8') as DataListJson:
            json.dump(DataList, DataListJson, ensure_ascii = False, indent = 4)
            
################################
##### Process 진행 및 업데이트 #####
################################
## PublisherProcess 프롬프트 요청 및 결과물 Json화
def PublisherProcessUpdate(projectName, email, mode = "Master", MainKey = 'PublisherAnalysis', MessagesReview = "on"):
    ## TotalPublisherData 경로 설정
    TotalPublisherDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_TargetData/s1512_PublisherData/s15121_TotalPublisherData"
    TotalPublisherDataJsonPath = os.path.join(TotalPublisherDataPath, 'TotalPublisherData.json')
    TotalPublisherDataTempPath = os.path.join(TotalPublisherDataPath, 'TotalPublisherDataTemp')
    
    ## 작업이 되지 않은 부분부터 totalPublisherDataList와 InputList 형성
    inputList = LoadTotalPublisherDataToInputList(TotalPublisherDataJsonPath, MainKey)
    
    ## PublisherProcess
    StartPoint = 1
    InputList = inputList[StartPoint:]
    ProcessCount = 1
    InputCount = len(InputList)
    i = 0
    
    while i < InputCount:
        ProcessCount = i+1
        InputDic = InputList[i]
        Input = InputDic['PublisherText']
        OutputDicList = []
        if Input != None:
            ## Process1: PublisherContextDefine Response 생성
            PublisherContextDefineResponse = ProcessResponse(projectName, email, "PublisherContextDefine", Input, ProcessCount, InputCount, PublisherContextDefineFilter, "OpenAI", mode, MessagesReview)
            OutputDicList.append(PublisherContextDefineResponse)
            
            ## Process2: PublisherWMWMDefine Response 생성
            PublisherWMWMDefineResponse = ProcessResponse(projectName, email, "PublisherWMWMDefine", Input, ProcessCount, InputCount, PublisherWMWMDefineFilter, "OpenAI", mode, MessagesReview)
            OutputDicList.append(PublisherWMWMDefineResponse)
            
            ## Process3: PublisherCommentAnalysis Response 생성
            PublisherServiceDemandResponse = ProcessResponse(projectName, email, "PublisherServiceDemand", Input, ProcessCount, InputCount, PublisherServiceDemandFilter, "OpenAI", mode, MessagesReview)
            OutputDicList.append(PublisherServiceDemandResponse)
            
        ## ProcessResponse 임시저장
        ProcessResponseTempSave(MainKey, InputDic, OutputDicList, TotalPublisherDataJsonPath, TotalPublisherDataTempPath)
        # 다음 아이템으로 이동
        i += 1
    
    ## ProcessResponse 업데이트
    ProcessResponseUpdate(MainKey, TotalPublisherDataJsonPath, TotalPublisherDataTempPath)

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241204_개정교육과정초등교과별이해연수'
    #########################################################################
    
    PublisherProcessUpdate(ProjectName, email)