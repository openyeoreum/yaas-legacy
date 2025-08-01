import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from agent.a2_Solution.a25_DataFrame.a251_DataCommit.a2511_LoadLLM import OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from agent.a2_Solution.a22_DataCollection.a221_VectorDatabase.a2214_VDBUpsert import UpsertCollectionData

#########################
##### InputList 생성 #####
#########################
## totalPublisherDataList로 로드(업데이트가 필요한 부분 선정, 이중 분석 방지)
def LoadTotalPublisherDataList(TotalPublisherDataJsonPath, TotalPublisherDataTempPath, StartPoint = 1):
    # TempIdList 생성
    TempIdList = []
    TempJsonList = []
    if os.path.exists(TotalPublisherDataTempPath):
        TempJsonList = os.listdir(TotalPublisherDataTempPath)
    FileNamePattern = r"^PublisherData_\((\d+)\)_.*\.json$"
    for TempJson in TempJsonList:
        match = re.match(FileNamePattern, TempJson)
        if match:
            TempIdList.append(int(match.group(1)))
    SortedTempIdList = sorted(TempIdList)
    
    ## TotalPublisherDataList 로드
    with open(TotalPublisherDataJsonPath, 'r', encoding = 'utf-8') as PublisherJson:
        TotalPublisherDataList = json.load(PublisherJson)[StartPoint:]
    ## TotalPublisherDataList중 업데이트가 필요한 부분 선정, 이중 분석 방지
    totalPublisherDataList = []
    for PublisherData in TotalPublisherDataList:
        if PublisherData['Id'] not in SortedTempIdList:
            totalPublisherDataList.append(PublisherData)
    
    return totalPublisherDataList

## LoadTotalPublisherData의 inputList 치환
def LoadTotalPublisherDataToInputList(TotalPublisherDataJsonPath, TotalPublisherDataTempPath, MaxTextLength = 4000):
    totalPublisherDataList = LoadTotalPublisherDataList(TotalPublisherDataJsonPath, TotalPublisherDataTempPath)
    
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

        InputDic = {'Id': i+1, 'PublisherId': PublisherId, 'PublisherName': PublisherData['PublisherInformation']['Name'], 'PublisherText': PublisherDataText}
        InputList.append(InputDic)
        
    return InputList

######################
##### Filter 조건 #####
######################
## Process1: PublisherContextDefine의 Filter(Error 예외처리)
def PublisherContextDefineFilter(Response, CheckCount):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "PublisherContextDefine, JSONDecode에서 오류 발생: JSONDecodeError"
    
    # Error2: 딕셔너리가 "정리"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic = outputJson['정리']
    except KeyError:
        return "PublisherContextDefine, JSON에서 오류 발생: '정리' 미포함"
    
    # Error3: 자료의 구조가 다를 때의 예외 처리
    required_keys = ['요약', '분야', '수요', '공급', '정보의질']
    if not all(key in OutputDic for key in required_keys):
        return "PublisherContextDefine, JSON에서 오류 발생: JSONKeyError"
    
    # 수요 검증
    demand_keys = ['필요', '목표', '질문']
    if not all(key in outputJson['정리']['수요'] for key in demand_keys):
        return "PublisherContextDefine, JSON에서 오류 발생: '필요', '목표', '질문' 미포함"
    
    # 공급 검증
    supply_keys = ['충족', '달성', '해결책']
    if not all(key in outputJson['정리']['공급'] for key in supply_keys):
        return "PublisherContextDefine, JSON에서 오류 발생: '충족', '달성', '해결책' 미포함"
    
    # 세부 키 검증
    for demand_key in demand_keys:
        if not all(sub_key in outputJson['정리']['수요'][demand_key] for sub_key in ['설명', '키워드', '중요도']):
            return f"PublisherContextDefine, JSON에서 오류 발생: 수요 {demand_key} '설명', '키워드', '중요도' 미포함"
    
    for supply_key in supply_keys:
        if not all(sub_key in outputJson['정리']['공급'][supply_key] for sub_key in ['설명', '키워드', '중요도']):
            return f"PublisherContextDefine, JSON에서 오류 발생: 공급 {supply_key} '설명', '키워드', '중요도' 미포함"
    
    return OutputDic

## Process2: PublisherWMWMDefine의 Filter(Error 예외처리)
def PublisherWMWMDefineFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "PublisherWMWMDefine, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: "심리" 키 존재 여부 확인
    try:
        outputDic = outputJson['심리']
    except KeyError:
        return "PublisherWMWMDefine, JSON에서 오류 발생: '심리' 미포함"

    # Error3: 주요 키 확인
    required_keys = ['요약', '욕구상태', '이해상태', '마음상태', '행동상태', '정보의질']
    if not all(key in outputDic for key in required_keys):
        return "PublisherWMWMDefine, JSON에서 오류 발생: 주요 키 누락"

    # 요약 키 확인
    if not isinstance(outputDic['요약'], list):
        return "PublisherWMWMDefine, JSON에서 오류 발생: '요약'이 리스트 형태가 아님"

    # 상태별 검증
    state_keys = ['욕구상태', '이해상태', '마음상태', '행동상태']
    for state_key in state_keys:
        if not all(sub_key in outputDic[state_key] for sub_key in [state_key, f'{state_key}선택이유', '중요도']):
            return f"PublisherWMWMDefine, JSON에서 오류 발생: {state_key} '설명', '선택이유', '중요도' 미포함"
    
    # 정보의질 키 확인
    if '정보의질' not in outputDic:
        return "PublisherWMWMDefine, JSON에서 오류 발생: '정보의질' 미포함"

    # 모든 검사를 통과하면 심리 데이터를 반환
    return outputDic

## Process3: PublisherServiceDemandFilter의 Filter(Error 예외처리)
def PublisherServiceDemandFilter(Response, CheckCount):
    # Error1: JSON 형식 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "PublisherServiceDemand, JSONDecode에서 오류 발생: JSONDecodeError"

    # Error2: "수요" 키 존재 여부 확인
    try:
        outputDic = outputJson['수요']
    except KeyError:
        return "PublisherServiceDemand, JSON에서 오류 발생: '수요' 미포함"

    # Error3: 주요 키 확인
    required_keys = ['요약', '텍스트북', '오디오북', '비디오북', '기타', '정보의질']
    if not all(key in outputDic for key in required_keys):
        return "PublisherServiceDemand, JSON에서 오류 발생: 주요 키 누락"

    # 요약 키 확인
    if not isinstance(outputDic['요약'], list):
        return "PublisherServiceDemand, JSON에서 오류 발생: '요약'이 리스트 형태가 아님"

    # 상태별 검증
    state_keys = ['텍스트북', '오디오북', '비디오북', '기타']
    for state_key in state_keys:
        if not all(sub_key in outputDic[state_key] for sub_key in ['제작필요', '제작물', '필요도']):
            return f"PublisherServiceDemand, JSON에서 오류 발생: {state_key} '제작필요', '제작물', '필요도' 미포함"

        # 제작물 키 확인
        if not isinstance(outputDic[state_key]['제작물'], list):
            return f"PublisherServiceDemand, JSON에서 오류 발생: {state_key} '제작물'이 리스트 형태가 아님"

    # 정보의질 키 확인
    if '정보의질' not in outputDic:
        return "PublisherServiceDemand, JSON에서 오류 발생: '정보의질' 미포함"

    # 모든 검사를 통과하면 수요 데이터를 반환
    return outputDic

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
        if DataList[i]['Id'] == InputDic['PublisherId']:
            if OutputDicList != []:
                #### Search ####
                #### Search-Detail ####
                #### Search-Context ####
                #### Search-Extention ####
                #### Search-Ultimate ####
                #### Context ####
                # Context-Summary
                ContextSummary = OutputDicList[0]['요약']
                # Context-KeyWord
                ContextKeyWord = OutputDicList[0]['분야']
                # Context-Demand
                ContextDemandNeeds = {"Sentence": OutputDicList[0]['수요']['필요']['설명'], "KeyWord": OutputDicList[0]['수요']['필요']['키워드'], "Weight": OutputDicList[0]['수요']['필요']['중요도']}
                ContextDemandPurpose = {"Sentence": OutputDicList[0]['수요']['목표']['설명'], "KeyWord": OutputDicList[0]['수요']['목표']['키워드'], "Weight": OutputDicList[0]['수요']['목표']['중요도']}
                ContextDemandQuestion = {"Sentence": OutputDicList[0]['수요']['질문']['설명'], "KeyWord": OutputDicList[0]['수요']['질문']['키워드'], "Weight": OutputDicList[0]['수요']['질문']['중요도']}
                ContextDemand = {'Needs': ContextDemandNeeds, 'Purpose': ContextDemandPurpose, 'Question': ContextDemandQuestion}
                # Context-Supply
                ContextSupplySatisfy = {"Sentence": OutputDicList[0]['공급']['충족']['설명'], "KeyWord": OutputDicList[0]['공급']['충족']['키워드'], "Weight": OutputDicList[0]['공급']['충족']['중요도']}
                ContextSupplySupport = {"Sentence": OutputDicList[0]['공급']['달성']['설명'], "KeyWord": OutputDicList[0]['공급']['달성']['키워드'], "Weight": OutputDicList[0]['공급']['달성']['중요도']}
                ContextSupplySolution = {"Sentence": OutputDicList[0]['공급']['해결책']['설명'], "KeyWord": OutputDicList[0]['공급']['해결책']['키워드'], "Weight": OutputDicList[0]['공급']['해결책']['중요도']}
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

                #### ServiceDemand ####
                ServiceDemandSummary = OutputDicList[2]['요약']
                # ServiceDemand-Textbook
                ServiceDemandTextbook = {'Needs': OutputDicList[2]['텍스트북']['제작필요'], 'Product': OutputDicList[2]['텍스트북']['제작물'], 'Weight': OutputDicList[2]['텍스트북']['필요도']}
                # ServiceDemand-Audiobook
                ServiceDemandAudiobook = {'Needs': OutputDicList[2]['오디오북']['제작필요'], 'Product': OutputDicList[2]['오디오북']['제작물'], 'Weight': OutputDicList[2]['오디오북']['필요도']}
                # ServiceDemand-Videobook
                ServiceDemandVideobook = {'Needs': OutputDicList[2]['비디오북']['제작필요'], 'Product': OutputDicList[2]['비디오북']['제작물'], 'Weight': OutputDicList[2]['비디오북']['필요도']}
                # ServiceDemand-ETC
                ServiceDemandETC = {'Needs': OutputDicList[2]['기타']['제작필요'], 'Product': OutputDicList[2]['기타']['제작물'], 'Weight': OutputDicList[2]['기타']['필요도']}
                # ServiceDemand-Weight
                ServiceDemandWeight = OutputDicList[2]['정보의질']
                ## ServiceDemandDic ##
                ServiceDemandDic = {'Summary': ServiceDemandSummary, 'Textbook': ServiceDemandTextbook, 'Audiobook': ServiceDemandAudiobook, 'Videobook': ServiceDemandVideobook, 'ETC': ServiceDemandETC, 'Weight': ServiceDemandWeight}
                #### ServiceDemand ####
                
                DataTemp = {MainKey: {'Context': ContextDic, 'WMWM': WMWMDic, 'ServiceDemand': ServiceDemandDic}}
            else:
                DataTemp = {MainKey: None}
            
            # DataTempJson 저장
            DataTempJsonPath = os.path.join(DataTempPath, f"PublisherData_({DataList[i]['Id']})_{DataList[i]['PublisherInformation']['Name']}.json")
            with open(DataTempJsonPath, 'w', encoding = 'utf-8') as DataTempJson:
                json.dump(DataTemp, DataTempJson, ensure_ascii = False, indent = 4)
            break

##### Process 추가 후처리 #####

##### Process 추가 후처리 #####

## ProcessResponse 업데이트 및 저장
def ProcessResponseUpdate(MainKey, DataJsonPath, DataTempPath):
    # 오리지날 DataList 불러와서 변경사항 저장
    with open(DataJsonPath, 'r', encoding='utf-8') as DataListJson:
        DataList = json.load(DataListJson)
        
    if MainKey not in DataList[-1]:
        # TextDataList 업데이트
        for i in range(len(DataList)):
            try:
                DataTempJsonPath = os.path.join(DataTempPath, f"PublisherData_({DataList[i]['Id']})_{DataList[i]['PublisherInformation']['Name']}.json")
                with open(DataTempJsonPath, 'r', encoding = 'utf-8') as DataTempJson:
                    DataTemp = json.load(DataTempJson)
                DataList[i][MainKey] = DataTemp[MainKey]
                ##### Process 추가 후처리 #####

                ##### Process 추가 후처리 #####
            except:
                print(f"[ DataTempJsonPath Is None : >>> PublisherData_({DataList[i]['Id']})_{DataList[i]['PublisherInformation']['Name']}.json <<< 파일 존재하지 않음 ]")
                continue
        
        # DataListJson 저장
        with open(DataJsonPath, 'w', encoding = 'utf-8') as DataListJson:
            json.dump(DataList, DataListJson, ensure_ascii = False, indent = 4)

################################
##### Process 진행 및 업데이트 #####
################################
## PublisherProcess 프롬프트 요청 및 결과물 Json화
def PublisherDataProcessUpdate(projectName, email, mode = "Master", MainKey = 'PublisherAnalysis', MessagesReview = "on"):
    print(f"< User: {email} | Project: {projectName} | PublisherDataProcessUpdate 시작 >")
    ## TotalPublisherData 경로 설정
    TotalPublisherDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s152_TargetData/s1522_PublisherData/s15221_TotalPublisherData"
    TotalPublisherDataJsonPath = os.path.join(TotalPublisherDataPath, 'TotalPublisherData.json')
    TotalPublisherDataTempPath = os.path.join(TotalPublisherDataPath, 'TotalPublisherDataTemp')
    
    ## 작업이 되지 않은 부분부터 totalPublisherDataList와 InputList 형성
    InputList = LoadTotalPublisherDataToInputList(TotalPublisherDataJsonPath, TotalPublisherDataTempPath)
    
    ## PublisherProcess
    InputCount = len(InputList)
    ProcessCount = 0
    
    while ProcessCount < InputCount:
        processCount = ProcessCount + 1
        InputDic = InputList[ProcessCount]
        Input = InputDic['PublisherText']
        CheckCount = 0
        OutputDicList = []
        
        if Input != None: ## Input이 None이 아닐 때만 Process 진행
            ## Process1: PublisherContextDefine Response 생성
            PublisherContextDefineResponse = ProcessResponse(projectName, email, "PublisherContextDefine", Input, processCount, InputCount, PublisherContextDefineFilter, CheckCount, "OpenAI", mode, MessagesReview)
            OutputDicList.append(PublisherContextDefineResponse)
            
            ## Process2: PublisherWMWMDefine Response 생성
            PublisherWMWMDefineResponse = ProcessResponse(projectName, email, "PublisherWMWMDefine", Input, processCount, InputCount, PublisherWMWMDefineFilter, CheckCount, "OpenAI", mode, MessagesReview)
            OutputDicList.append(PublisherWMWMDefineResponse)
            
            ## Process3: PublisherCommentAnalysis Response 생성
            PublisherServiceDemandResponse = ProcessResponse(projectName, email, "PublisherServiceDemand", Input, processCount, InputCount, PublisherServiceDemandFilter, CheckCount, "OpenAI", mode, MessagesReview)
            OutputDicList.append(PublisherServiceDemandResponse)
            
            ## ProcessResponse 임시저장
            ProcessResponseTempSave(MainKey, InputDic, OutputDicList, TotalPublisherDataJsonPath, TotalPublisherDataTempPath)
        # 다음 아이템으로 이동
        ProcessCount += 1
    
    ## ProcessResponse 업데이트
    ProcessResponseUpdate(MainKey, TotalPublisherDataJsonPath, TotalPublisherDataTempPath)
    print(f"[ User: {email} | Project: {projectName} | PublisherDataProcessUpdate 완료 ]\n")
    
    ## ProcessResponse 업서트
    UpsertCollectionData(TotalPublisherDataTempPath, "Publisher")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241204_개정교육과정초등교과별이해연수'
    #########################################################################
    
    PublisherDataProcessUpdate(ProjectName, email)