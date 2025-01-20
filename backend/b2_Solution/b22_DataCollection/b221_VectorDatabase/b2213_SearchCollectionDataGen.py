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
## Process1-1: SearchResultScoreFilter
def SearchResultScoreFilter(Intention, Extension, MinScore = 35e-7):
    with open('/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1513_SearchResultData/s15131_TotalSearchResultData/TotalSearchResultDataTemp/SearchResultData_(20250111021236)_[나는 오디오북 자동 제작 AI솔루션 ].json', 'r', encoding = 'utf-8') as SearchResultJson:
        SearchResult = json.load(SearchResultJson)['SearchResult']

    ## Intention과 Extension에 따라서 데이터 분리
    extension = [""] + Extension
    for ext in extension:
        if SearchResult[f"{Intention}Context{ext}"] != None:
            Context = SearchResult[f"{Intention}Context{ext}"]
            if Context is not None:
                if isinstance(Context, dict):
                    ContextCollectionSearch = Context['CollectionSearch']
                    NewContextCollectionSearch = []
                    for CollectionSearch in ContextCollectionSearch:
                        if CollectionSearch['Score'] >= MinScore:
                            NewContextCollectionSearch.append(CollectionSearch)
                    Context['CollectionSearch'] = NewContextCollectionSearch
                elif isinstance(Context, list):
                    for i in range(len(Context)):
                        ContextCollectionSearch = Context[i]['CollectionSearch']
                        NewContextCollectionSearch = []
                        for CollectionSearch in ContextCollectionSearch:
                            if CollectionSearch['Score'] >= MinScore:
                                NewContextCollectionSearch.append(CollectionSearch)
                        Context[i]['CollectionSearch'] = NewContextCollectionSearch
    with open('/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1513_SearchResultData/s15131_TotalSearchResultData/TotalSearchResultDataTemp/SearchResultData_(20250111021236)_[나는 오디오북 자동 제작 AI솔루션 ]_ScoreCal.json', 'w', encoding = 'utf-8') as SearchResultJson:
        json.dump(SearchResult, SearchResultJson, ensure_ascii = False, indent = 4)
    
    return SearchResult
    
## Process1-2: SearchResultSelection의 Input
def SearchResultSelectionInput():
    with open('/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1513_SearchResultData/s15131_TotalSearchResultData/TotalSearchResultDataTemp/SearchResultData_(20250111021236)_[나는 오디오북 자동 제작 AI솔루션 ].json', 'r', encoding = 'utf-8') as SearchResultJson:
        SearchResult = json.load(SearchResultJson)
    print(SearchResult)

######################
##### Filter 조건 #####
######################
## Process1: SupplyCollectionDataDetail의 Filter(Error 예외처리)
def SupplyCollectionDataDetailFilter(Response, CheckCount):
    # Error1: JSON 형식이 아닐 때의 예외 처리
    try:
        OutputDic = json.loads(Response)
    except json.JSONDecodeError:
        return "SupplyCollectionDataDetail, JSONDecode에서 오류 발생: JSONDecodeError"
    
    # Error2: 최상위 필수 키 존재 여부 확인
    required_keys = ['핵심솔루션', '제안할내용', '제안할목표', '제안할해결책', '검색어완성도', '검색어피드백']
    missing_keys = [key for key in required_keys if key not in OutputDic]
    if missing_keys:
        return f"SupplyCollectionDataDetail, JSONKeyError: 누락된 키: {', '.join(missing_keys)}"
    
    # Error3: 데이터 타입 검증
    # 핵심솔루션, 제안할내용, 제안할목표, 제안할해결책은 문자열이어야 함
    for key in ['핵심솔루션', '제안할내용', '제안할목표', '제안할해결책']:
        if isinstance(OutputDic[key], list):
            OutputDic[key] = ' '.join(OutputDic[key])
        if not isinstance(OutputDic[key], str):
            return f"SupplyCollectionDataDetail, JSON에서 오류 발생: '{key}'가 문자열이 아님"

    # 검색어완성도는 0-100 사이의 정수여야 함
    if not isinstance(OutputDic['검색어완성도'], int) or not (0 <= OutputDic['검색어완성도'] <= 100):
        return "SupplyCollectionDataDetail, JSON에서 오류 발생: '검색어완성도'가 0-100 사이의 정수가 아님"

    # 검색어피드백은 문자열 리스트여야 함
    if not isinstance(OutputDic['검색어피드백'], list) or not all(isinstance(item, str) for item in OutputDic['검색어피드백']):
        return "SupplyCollectionDataDetail, JSON에서 오류 발생: '검색어피드백'은 문자열 리스트가 아님"
    
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
def ProcessResponseTempSave(MainKey, InputDic, OutputDicSet, DataTempPath):
    # DataTempPath 폴더가 없으면 생성
    if not os.path.exists(DataTempPath):
        os.makedirs(DataTempPath)
    
    # ProcessKeyList 생성
    ProcessKeyList = []
    ProcessDicList = []
    
    #### Search ####
    # Search-Term
    Term = InputDic['Input']
    TermText = InputDic['TermText']
    ## SearchDic ##
    SearchDic = {'Term': Term}

    ProcessKeyList.append("SupplySearch")
    ProcessDicList.append(SearchDic)
    #### Search ####
    
    #### Detail ####
    Process = "SupplyCollectionDataDetail"
    if Process in OutputDicSet:
        # Detail-Summary
        ScarchSummary = OutputDicSet[Process]['핵심솔루션']
        # Detail-Satisfy
        DetailSatisfy = OutputDicSet[Process]['제안할내용']
        # Detail-Support
        DetailSupport = OutputDicSet[Process]['제안할목표']
        # Detail-Solution
        DetailSolution = OutputDicSet[Process]['제안할해결책']
        # Detail-Weight
        DetailWeight = OutputDicSet[Process]['검색어완성도']
        # Detail-Feedback
        DetailFeedback = OutputDicSet[Process]['검색어피드백']
        ## DetailDic ##
        DetailDic = {'Summary': ScarchSummary, 'Satisfy': DetailSatisfy, 'Support': DetailSupport, 'Solution': DetailSolution, 'Weight': DetailWeight, 'Feedback': DetailFeedback}
        
        ProcessKeyList.append("SupplyDetail")
        ProcessDicList.append(DetailDic)
    #### Detail ####
    
    #### Context ####
    Process = "SupplyCollectionDataContext"
    if Process in OutputDicSet:
        # Context-Summary
        ContextSummary = OutputDicSet[Process]['핵심솔루션']
        # Context-KeyWord
        ContextKeyWord = OutputDicSet[Process]['분야']
        # Context-Supply
        ContextSupplySatisfy = {"Sentence": OutputDicSet[Process]['제안']['제안내용']['설명'], "KeyWord": OutputDicSet[Process]['제안']['제안내용']['키워드'], "Weight": OutputDicSet[Process]['제안']['제안내용']['중요도']}
        ContextSupplySupport = {"Sentence": OutputDicSet[Process]['제안']['제안할목표']['설명'], "KeyWord": OutputDicSet[Process]['제안']['제안할목표']['키워드'], "Weight": OutputDicSet[Process]['제안']['제안할목표']['중요도']}
        ContextSupplySolution = {"Sentence": OutputDicSet[Process]['제안']['제안할해결책']['설명'], "KeyWord": OutputDicSet[Process]['제안']['제안할해결책']['키워드'], "Weight": OutputDicSet[Process]['제안']['제안할해결책']['중요도']}
        ContextSupply = {'Satisfy': ContextSupplySatisfy, 'Support': ContextSupplySupport, 'Solution': ContextSupplySolution}
        # Context-Weight
        ContextWeight = OutputDicSet[Process]['정보의질']
        ## ContextDic ##
        ContextDic = {'Summary': ContextSummary, 'KeyWord': ContextKeyWord, 'Supply': ContextSupply, 'Weight': ContextWeight}
        
        ProcessKeyList.append("SupplyContext")
        ProcessDicList.append(ContextDic)
    #### Context ####
    
    #### ContextExpertise ####
    Process = "SupplyCollectionDataExpertiseChain"
    if Process in OutputDicSet:
        ContextExpertiseDicList = []
        for i in range(5):
            # ContextExpertise-Summary
            ContextExpertiseSummary = OutputDicSet[Process][f'전문데이터{i+1}']['핵심솔루션']
            # ContextExpertise-KeyWord
            ContextExpertiseKeyWord = OutputDicSet[Process][f'전문데이터{i+1}']['분야']
            # ContextExpertise-Supply
            ContextExpertiseSupplySatisfy = {"Sentence": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안내용']['설명'], "KeyWord": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안내용']['키워드'], "Weight": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안내용']['중요도']}
            ContextExpertiseSupplySupport = {"Sentence": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할목표']['설명'], "KeyWord": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할목표']['키워드'], "Weight": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할목표']['중요도']}
            ContextExpertiseSupplySolution = {"Sentence": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할해결책']['설명'], "KeyWord": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할해결책']['키워드'], "Weight": OutputDicSet[Process][f'전문데이터{i+1}']['제안']['제안할해결책']['중요도']}
            ContextExpertiseSupply = {'Satisfy': ContextExpertiseSupplySatisfy, 'Support': ContextExpertiseSupplySupport, 'Solution': ContextExpertiseSupplySolution}
            # ContextExpertise-Weight
            ContextExpertiseWeight = OutputDicSet[Process][f'전문데이터{i+1}']['정보의질']
            ## ContextExpertiseDic ##
            ContextExpertiseDic = {'Summary': ContextExpertiseSummary, 'KeyWord': ContextExpertiseKeyWord, 'Supply': ContextExpertiseSupply, 'Weight': ContextExpertiseWeight}
            ContextExpertiseDicList.append(ContextExpertiseDic)
        
        ProcessKeyList.append("SupplyContextExpertise")
        ProcessDicList.append(ContextExpertiseDicList)
    #### ContextExpertise ####
    
    #### ContextUltimate ####
    Process = "SupplyCollectionDataUltimateChain"
    if Process in OutputDicSet:
        ContextUltimateDicList = []
        for i in range(5):
            # ContextUltimate-Summary
            ContextUltimateSummary = OutputDicSet[Process][f'연계데이터{i+1}']['핵심솔루션']
            # ContextUltimate-KeyWord
            ContextUltimateKeyWord = OutputDicSet[Process][f'연계데이터{i+1}']['분야']
            # ContextUltimate-Supply
            ContextUltimateSupplySatisfy = {"Sentence": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안내용']['설명'], "KeyWord": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안내용']['키워드'], "Weight": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안내용']['중요도']}
            ContextUltimateSupplySupport = {"Sentence": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할목표']['설명'], "KeyWord": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할목표']['키워드'], "Weight": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할목표']['중요도']}
            ContextUltimateSupplySolution = {"Sentence": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할해결책']['설명'], "KeyWord": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할해결책']['키워드'], "Weight": OutputDicSet[Process][f'연계데이터{i+1}']['제안']['제안할해결책']['중요도']}
            ContextUltimateSupply = {'Satisfy': ContextUltimateSupplySatisfy, 'Support': ContextUltimateSupplySupport, 'Solution': ContextUltimateSupplySolution}
            # ContextUltimate-Weight
            ContextUltimateWeight = OutputDicSet[Process][f'연계데이터{i+1}']['정보의질']
            ## ContextUltimateDic ##
            ContextUltimateDic = {'Summary': ContextUltimateSummary, 'KeyWord': ContextUltimateKeyWord, 'Supply': ContextUltimateSupply, 'Weight': ContextUltimateWeight}
            ContextUltimateDicList.append(ContextUltimateDic)
        
        ProcessKeyList.append("SupplyContextUltimate")
        ProcessDicList.append(ContextUltimateDicList)
    #### ContextUltimate ####
    
    DataTemp = {MainKey: {}}
    for i in range(len(ProcessKeyList)):
        DataTemp[MainKey][ProcessKeyList[i]] = ProcessDicList[i]
    
    # DataTempJson 저장
    DateTime = datetime.now().strftime('%Y%m%d%H%M%S')
    DataTempJsonPath = os.path.join(DataTempPath, f"SupplyCollectionData_({DateTime})_{TermText}.json")
    with open(DataTempJsonPath, 'w', encoding = 'utf-8') as DataTempJson:
        json.dump(DataTemp, DataTempJson, ensure_ascii = False, indent = 4)
        
    # CollectionDataChain 추출
    CollectionDataChain = DataTemp[MainKey]
        
    return CollectionDataChain, DateTime

################################
##### Process 진행 및 업데이트 #####
################################
## SupplyCollectionData 프롬프트 요청 및 결과물 Json화
def SupplyCollectionDataProcessUpdate(projectName, email, InputDic, mode = "Master", MainKey = 'SupplySearchAnalysis', MessagesReview = "on"):
    print(f"< User: {email} | Chain: {projectName} | SupplyCollectionDataUpdate 시작 >")
    ## TotalPublisherData 경로 설정
    TotalSupplyCollectionDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1512_SupplyCollectionData/s15121_TotalSupplyCollectionData"
    TotalSupplyCollectionDataJsonPath = os.path.join(TotalSupplyCollectionDataPath, 'TotalSupplyCollectionData.json')
    TotalSupplyCollectionDataTempPath = os.path.join(TotalSupplyCollectionDataPath, 'TotalSupplyCollectionDataTemp')
    
    ## SupplyCollectionDataDetailProcess
    Type = InputDic['Type']
    Extension = InputDic['Extension']
    # InputCount 계산
    InputCount = 1
    if Type == "Search":
        InputCount += 1
    if Extension != []:
        InputCount += (len(InputDic['Extension'])) * 6
    processCount = 1
    CheckCount = 0
    OutputDicSet = {}

    ## Process1: SupplyCollectionDataDetail Response 생성
    if Type == "Search":
        Process = "SupplyCollectionDataDetail"
        Input = InputDic['Input']
        
        SupplyCollectionDataDetailResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, SupplyCollectionDataDetailFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicSet[Process] = SupplyCollectionDataDetailResponse
        processCount += 1
    
    ## Process2: SupplyCollectionDataContext Response 생성
    if Type == "Search":
        Process = "SupplyCollectionDataContext"
        Input = SupplyCollectionDataDetailResponse.copy()
        DeleteKeys = ['검색어완성도', '검색어피드백']
        for key in DeleteKeys:
            del Input[key]
    
        SupplyCollectionDataContextResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, SupplyCollectionDataContextFilter, CheckCount, "OpenAI", mode, MessagesReview)
        OutputDicSet[Process] = SupplyCollectionDataContextResponse
    elif Type == "Match":
        Process = "SupplyCollectionDataContext"
        OutputDicSet[Process] = InputDic['CollectionData']
    processCount += 1
    
    ## Process3-1: SupplyCollectionDataExpertise Response 생성
    if "Expertise" in Extension:
        Process = "SupplyCollectionDataExpertise"
        if Type == "Search":
            Input = SupplyCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        
        SupplyCollectionDataExpertiseResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, SupplyCollectionDataExpertiseFilter, CheckCount, "OpenAI", mode, MessagesReview)
        processCount += 1
        
        ## Process3-2: SupplyCollectionDataExpertiseChain Response 연속 생성 및 Set로 합치기
        Process = "SupplyCollectionDataExpertiseChain"
        SupplyCollectionDataExpertiseChainResponseSet = {}
        for i, Response in enumerate(SupplyCollectionDataExpertiseResponse):
            InputText = f'{Response}\n\n<데이터>\n{Input}\n'
            SupplyCollectionDataExpertiseChainResponse = ProcessResponse(projectName, email, Process, InputText, processCount, InputCount, SupplyCollectionDataExpertiseChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
            SupplyCollectionDataExpertiseChainResponseSet[f'전문데이터{i+1}'] = {}
            SupplyCollectionDataExpertiseChainResponse['핵심솔루션'] = f"{Response['전문분야']}  {SupplyCollectionDataExpertiseChainResponse['핵심솔루션']}"
            SupplyCollectionDataExpertiseChainResponseSet[f'전문데이터{i+1}'].update(SupplyCollectionDataExpertiseChainResponse)
            processCount += 1

        # 최종 Set 데이터 추가
        OutputDicSet[Process] = SupplyCollectionDataExpertiseChainResponseSet
    
    ## Process4-1: SupplyCollectionDataUltimate Response 생성
    if "Ultimate" in Extension:
        Process = "SupplyCollectionDataUltimate"
        if Type == "Search":
            Input = SupplyCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        
        SupplyCollectionDataUltimateResponse = ProcessResponse(projectName, email, Process, Input, processCount, InputCount, SupplyCollectionDataUltimateFilter, CheckCount, "OpenAI", mode, MessagesReview)
        processCount += 1
        
        ## Process4-2: SupplyCollectionDataUltimateChain Response 연속 생성 및 Set로 합치기
        Process = "SupplyCollectionDataUltimateChain"
        SupplyCollectionDataUltimateChainResponseSet = {}
        for i, Response in enumerate(SupplyCollectionDataUltimateResponse):
            InputText = f'{Input}\n\n<새로운 핵심솔루션 메모>\n{Response}\n'
            SupplyCollectionDataUltimateChainResponse = ProcessResponse(projectName, email, Process, InputText, processCount, InputCount, SupplyCollectionDataUltimateChainFilter, CheckCount, "OpenAI", mode, MessagesReview)
            SupplyCollectionDataUltimateChainResponseSet[f'연계데이터{i+1}'] = {}
            SupplyCollectionDataUltimateChainResponse['핵심솔루션'] = f"{Response['핵심솔루션']}  {SupplyCollectionDataUltimateChainResponse['핵심솔루션']}"
            SupplyCollectionDataUltimateChainResponseSet[f'연계데이터{i+1}'].update(SupplyCollectionDataUltimateChainResponse)
            processCount += 1

        # 최종 Set 데이터 추가
        OutputDicSet[Process] = SupplyCollectionDataUltimateChainResponseSet
    
    ## Process5: SupplyCollectionDataDetailChain Response 생성
    if "Detail" in Extension:
        Process = "SupplyCollectionDataDetailChain"
        if Type == "Search":
            Input = SupplyCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        pass
    
    ## Process6: SupplyCollectionDataRethinkingChain Response 생성
    if "Rethinking" in Extension:
        Process = "SupplyCollectionDataRethinkingChain"
        if Type == "Search":
            Input = SupplyCollectionDataContextResponse
        elif Type == "Match":
            Input = InputDic['Input']
        pass

    ## ProcessResponse 임시저장
    CollectionDataChain, DateTime = ProcessResponseTempSave(MainKey, InputDic, OutputDicSet, TotalSupplyCollectionDataTempPath)

    print(f"[ User: {email} | Chain: {projectName} | SupplyCollectionDataUpdate 완료 ]")
    
    return CollectionDataChain, DateTime

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "오디오북제작자동화솔루션의새로운활용"
    Search = "나는 오디오북 자동 제작 AI솔루션 대표입니다. 우리회사의 오디오북 솔루션은 100권의 고품질 오디오북을 탄생시키고 의뢰인들을 만족시킬 만큼 성능과 효율성이 뛰어납니다. 오디오북 솔루션은 고품질 TTS, 음악, 효과음, 스크립트 제작 자동화의 기능을 모두 담고 있습니다. 나는 이 오디오북 솔루션의 새로운 활용방안을 고민하고 있습니다. 좋은 해결책을 얻고 싶습니다." # Search: SearchTerm, Match: PublisherData_(Id)
    Intention = "Similarity" # Demand, Supply, Similarity ...
    Extension = ["Expertise", "Ultimate"] # Expertise, Ultimate, Detail, Rethink ...
    Collection = "publisher" # Entire, Target, Trend, Publisher, Book ...
    Range = 10 # 10-100
    MessagesReview = "on" # on, off
    #########################################################################
    SearchResultScoreFilter(Intention, Extension)