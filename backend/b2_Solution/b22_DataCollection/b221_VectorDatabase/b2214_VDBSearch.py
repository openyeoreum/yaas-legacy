import os
import re
import json
import sys
sys.path.append("/yaas")

from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from backend.b2_Solution.b22_DataCollection.b221_VectorDatabase.b2211_DemandCollectionDataGen import DemandCollectionDataDetailProcessUpdate
from backend.b2_Solution.b22_DataCollection.b221_VectorDatabase.b2212_SupplyCollectionDataGen import SupplyCollectionDataDetailProcessUpdate

## Pinecone에 인덱스 생성
def Pinecone_CreateIndex(Collection, IndexDimension = 1536):
    PineConeClient = Pinecone(api_key = os.getenv("PINECONE_API_KEY"))
    # Pinecone 인덱스 생성
    if not PineConeClient.has_index(Collection):
        PineConeClient.create_index(
            name = Collection,
            dimension = IndexDimension,
            metric = "cosine",
            spec = ServerlessSpec(
                cloud = 'aws',
                region = 'us-east-1'
            )
        )
    
    return PineConeClient

## OpenAI API를 이용하여 텍스트를 임베딩하여 벡터로 반환
def OpenAI_TextEmbedding(Text, EmbedModel = "text-embedding-3-small"):
    OpenAIClinet = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
    # 비어있는 문자열을 방지하기 위한 처리
    if not Text:
        Text = " "
    response = OpenAIClinet.embeddings.create(
        input = Text,
        model = EmbedModel
    )
    Embedding = response.data[0].embedding
    
    return Embedding

## 가중치 일반화 함수 (str -> int / 100)
def GetWeight(Weight):
    return (int(Weight.replace('점', '')) if isinstance(Weight, str) else int(Weight)) / 100

## TempFilePaths 생성
def GetCollectionDataPaths(Collection):
    if Collection == 'publisher' or Collection == 'Publisher':
        TempFolderPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s152_TargetData/s1522_PublisherData/s15221_TotalPublisherData/TotalPublisherDataTemp"
        MainKey = 'PublisherAnalysis'
    elif Collection == 'book' or Collection == 'Book':
        TempFolderPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s153_TrendData/s1532_BookData/s15321_TotalBookData/TotalBookDataTemp"
        MainKey = "BookAnalysis"
    ## ... 추가 예정
    
    TempFilePaths = {}
    TempFileNamePattern = r'^[A-Za-z]+_\((\d+)\)_.+\.json$'
    TempFileNamePatternRegex = re.compile(TempFileNamePattern)

    for TempFileName in os.listdir(TempFolderPath):
        # 정규 표현식을 이용해 파일명 매칭
        match = TempFileNamePatternRegex.match(TempFileName)
        if match:
            DataId = match.group(1)  # 번호 추출
            TempFileFullPath = os.path.join(TempFolderPath, TempFileName)  # 전체 경로 생성
            TempFilePaths[DataId] = TempFileFullPath
            
    return MainKey, TempFilePaths

## Pinecone에 임베딩 데이터 검색
def SearchEmbeddedData(CollectionData, Intention, Collection, Range): # Intention: 'similarity', 'demand, 'supply' // Collection: 'entire', 'target', 'trend', 'publisher', 'book'...
    print(f"[ YaaS VDB ({Search['Type']}): {Search['Term']} | Intention({Intention}) | Collection({Collection}) | Range({Range}) ]")
        
    ## A. TempFilePaths, MainKey 생성 및 Pinecone VDB 연결 ##
    PineConeClient = Pinecone_CreateIndex(Collection)
    VDBIndex = PineConeClient.Index(name = Collection)
    MainKey, TempFilePaths = GetCollectionDataPaths(Collection)
    
    ## B. 검색 쿼리와 가중치 ##
    # Context-Weight
    ContextQueryWeight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Weight'])
    # 1) Context-Summary
    ContextSummaryQueryText = CollectionData['CollectionAnalysis']['Context']['Summary']
    # 2) Context-KeyWord
    ContextKeyWordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['KeyWord'])

    # Context-Demand-Needs-Weight
    ContextDemandNeedsQueryWeight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['Weight'])
    # 3) Context-Demand-Needs-Sentence
    ContextDemandNeedsSentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['Sentence']
    # 4) Context-Demand-Needs-Keyword
    ContextDemandNeedsKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['KeyWord'])

    # Context-Demand-Purpose-Weight
    ContextDemandPurposeQueryWeight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['Weight'])
    # 5) Context-Demand-Purpose-Sentence
    ContextDemandPurposeSentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['Sentence']
    # 6) Context-Demand-Purpose-Keyword
    ContextDemandPurposeKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['KeyWord'])

    # Context-Demand-Question-Weight
    ContextDemandQuestionQueryWeight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['Weight'])
    # 7) Context-Demand-Question-Sentence
    ContextDemandQuestionSentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['Sentence']
    # 8) Context-Demand-Question-Keyword
    ContextDemandQuestionKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['KeyWord'])

    # Context-Supply-Satisfy-Weight
    ContextSupplySatisfyQueryWeight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['Weight'])
    # 9) Context-Supply-Satisfy-Sentence
    ContextSupplySatisfySentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['Sentence']
    # 10) Context-Supply-Satisfy-Keyword
    ContextSupplySatisfyKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['KeyWord'])

    # Context-Supply-Support-Weight
    ContextSupplySupportQueryWeight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['Weight'])
    # 11) Context-Supply-Support-Sentence
    ContextSupplySupportSentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['Sentence']
    # 12) Context-Supply-Support-Keyword
    ContextSupplySupportKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['KeyWord'])

    # Context-Supply-Solution-Weight
    ContextSupplySolutionQueryWeight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['Weight'])
    # 13) Context-Supply-Solution-Sentence
    ContextSupplySolutionSentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['Sentence']
    # 14) Context-Supply-Solution-Keyword
    ContextSupplySolutionKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['KeyWord'])

    ## C. 검색 옵션 설정 ##
    # Similarity = 유사도검색 : 유사한 정보/대상 검색
    if Intention == 'similarity':
        QueryList = [{"Field": "Context-Summary", "Text": ContextSummaryQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-KeyWord", "Text": ContextKeyWordQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-Demand-Needs-Sentence", "Text": ContextDemandNeedsSentenceQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Needs-Keyword", "Text": ContextDemandNeedsKeywordQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Purpose-Sentence", "Text": ContextDemandPurposeSentenceQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Purpose-Keyword", "Text": ContextDemandPurposeKeywordQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Question-Sentence", "Text": ContextDemandQuestionSentenceQueryText, "Weight": ContextDemandQuestionQueryWeight}, {"Field": "Context-Demand-Question-Keyword", "Text": ContextDemandQuestionKeywordQueryText, "Weight": ContextDemandQuestionQueryWeight}, {"Field": "Context-Supply-Satisfy-Sentence", "Text": ContextSupplySatisfySentenceQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Satisfy-Keyword", "Text": ContextSupplySatisfyKeywordQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Support-Sentence", "Text": ContextSupplySupportSentenceQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Support-Keyword", "Text": ContextSupplySupportKeywordQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Solution-Sentence", "Text": ContextSupplySolutionSentenceQueryText, "Weight": ContextSupplySolutionQueryWeight}, {"Field": "Context-Supply-Solution-Keyword", "Text": ContextSupplySolutionKeywordQueryText, "Weight": ContextSupplySolutionQueryWeight}]
    # Demand = 수요검색 : 나에게 필요한 정보/대상 검색
    elif Intention == 'demand':
        QueryList = [{"Field": "Context-Summary", "Text": ContextSummaryQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-KeyWord", "Text": ContextKeyWordQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-Demand-Needs-Sentence", "Text": ContextDemandNeedsSentenceQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Needs-Keyword", "Text": ContextDemandNeedsKeywordQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Purpose-Sentence", "Text": ContextDemandPurposeSentenceQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Purpose-Keyword", "Text": ContextDemandPurposeKeywordQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Question-Sentence", "Text": ContextDemandQuestionSentenceQueryText, "Weight": ContextDemandQuestionQueryWeight}, {"Field": "Context-Demand-Question-Keyword", "Text": ContextDemandQuestionKeywordQueryText, "Weight": ContextDemandQuestionQueryWeight}]
    # Supply = 공급검색 : 나를 필요로 하는 정보/대상 검색
    elif Intention == 'supply':
        QueryList = [{"Field": "Context-Summary", "Text": ContextSummaryQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-KeyWord", "Text": ContextKeyWordQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-Supply-Satisfy-Sentence", "Text": ContextSupplySatisfySentenceQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Satisfy-Keyword", "Text": ContextSupplySatisfyKeywordQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Support-Sentence", "Text": ContextSupplySupportSentenceQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Support-Keyword", "Text": ContextSupplySupportKeywordQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Solution-Sentence", "Text": ContextSupplySolutionSentenceQueryText, "Weight": ContextSupplySolutionQueryWeight}, {"Field": "Context-Supply-Solution-Keyword", "Text": ContextSupplySolutionKeywordQueryText, "Weight": ContextSupplySolutionQueryWeight}]

    # 검색 결과를 저장하기 위한 dict (DocId를 기준으로 저장)
    QueryResultList = []
    MinScores = {}
    MaxScores = {}
    ## D. 각 필드에 대한 검색 쿼리 생성 ##
    for Query in QueryList:
        if Query['Field'] == "Context-Summary":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Summary"
        elif Query['Field'] == "Context-KeyWord":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-KeyWord"
        elif Query['Field'] == "Context-Demand-Needs-Sentence":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Demand-Needs-Sentence"
        elif Query['Field'] == "Context-Demand-Needs-Keyword":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Demand-Needs-Keyword"
        elif Query['Field'] == "Context-Demand-Purpose-Sentence":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Demand-Purpose-Sentence"
        elif Query['Field'] == "Context-Demand-Purpose-Keyword":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Demand-Purpose-Keyword"
        elif Query['Field'] == "Context-Demand-Question-Sentence":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Demand-Question-Sentence"
        elif Query['Field'] == "Context-Demand-Question-Keyword":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Demand-Question-Keyword"
        elif Query['Field'] == "Context-Supply-Satisfy-Sentence":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Supply-Satisfy-Sentence"
        elif Query['Field'] == "Context-Supply-Satisfy-Keyword":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Supply-Satisfy-Keyword"
        elif Query['Field'] == "Context-Supply-Support-Sentence":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Supply-Support-Sentence"
        elif Query['Field'] == "Context-Supply-Support-Keyword":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Supply-Support-Keyword"
        elif Query['Field'] == "Context-Supply-Solution-Sentence":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Supply-Solution-Sentence"
        elif Query['Field'] == "Context-Supply-Solution-Keyword":
            QueryText = Query['Text']
            QueryWeight = Query['Weight']
            QueryField = "Context-Supply-Solution-Keyword"

        # 해당 필드의 쿼리 벡터 생성
        QueryVector = OpenAI_TextEmbedding(QueryText)

        ## E. Pinecone에 쿼리 수행 ##
        QueryResult = VDBIndex.query(
            vector = QueryVector,
            top_k = Range,
            include_metadata = True,
            namespace = Collection,
            filter = {"Field": QueryField}
        )
        ## F. 최소값 저장
        if QueryResult.matches:
            # MinScore 계산 (0이 아닌 값)
            MinScore = min(match.score * QueryWeight for match in QueryResult.matches if match.score * QueryWeight != 0)
            MinScores[QueryField] = MinScore
            QueryResultList.append(QueryResult)

    ## G. Pinecone에 Result Score 계산 ##
    for QueryResult in QueryResultList:
        # 가장 높은 유사도 점수와 CollectionId를 사용
        for result in QueryResult["matches"]:
            collection = Result["metadata"]["Collection"]
            CollectionId = result["metadata"]["CollectionId"]
            ResultField = result["metadata"]["Field"]
            ResultWeight = result["metadata"]["Weight"] / 100
            ResultScore = result["score"] * QueryWeight * ResultWeight

            # CollectionId 처음 생성시 MinScores로 초기화 및 해당 CollectionId 가중치 적용
            if CollectionId not in MaxScores:
                ## MinScores 초기화 ##
                with open(TempFilePaths[CollectionId], 'r', encoding = 'utf-8') as TempFile:
                    TempData = json.load(TempFile)
                # MinScores 초기화(복사)
                MaxScores[CollectionId] = MinScores.copy()
                # MinScores 가중치 적용
                MaxScores[CollectionId]["Context-Summary"] = MinScores["Context-Summary"] * GetWeight(TempData[MainKey]["Context"]["Weight"])
                MaxScores[CollectionId]["Context-KeyWord"] = MinScores["Context-KeyWord"] * GetWeight(TempData[MainKey]["Context"]["Weight"])
                MaxScores[CollectionId]["Context-Demand-Needs-Sentence"] = MinScores["Context-Demand-Needs-Sentence"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Needs"]["Weight"])
                MaxScores[CollectionId]["Context-Demand-Needs-Keyword"] = MinScores["Context-Demand-Needs-Keyword"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Needs"]["Weight"])
                MaxScores[CollectionId]["Context-Demand-Purpose-Sentence"] = MinScores["Context-Demand-Purpose-Sentence"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Purpose"]["Weight"])
                MaxScores[CollectionId]["Context-Demand-Purpose-Keyword"] = MinScores["Context-Demand-Purpose-Keyword"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Purpose"]["Weight"])
                MaxScores[CollectionId]["Context-Demand-Question-Sentence"] = MinScores["Context-Demand-Question-Sentence"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Question"]["Weight"])
                MaxScores[CollectionId]["Context-Demand-Question-Keyword"] = MinScores["Context-Demand-Question-Keyword"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Question"]["Weight"])
                MaxScores[CollectionId]["Context-Supply-Satisfy-Sentence"] = MinScores["Context-Supply-Satisfy-Sentence"] * GetWeight(TempData[MainKey]["Context"]["Supply"]["Satisfy"]["Weight"])
                MaxScores[CollectionId]["Context-Supply-Satisfy-Keyword"] = MinScores["Context-Supply-Satisfy-Keyword"] * GetWeight(TempData[MainKey]["Context"]["Supply"]["Satisfy"]["Weight"])
                MaxScores[CollectionId]["Context-Supply-Support-Sentence"] = MinScores["Context-Supply-Support-Sentence"] * GetWeight(TempData[MainKey]["Context"]["Supply"]["Support"]["Weight"])
                MaxScores[CollectionId]["Context-Supply-Support-Keyword"] = MinScores["Context-Supply-Support-Keyword"] * GetWeight(TempData[MainKey]["Context"]["Supply"]["Support"]["Weight"])
                MaxScores[CollectionId]["Context-Supply-Solution-Sentence"] = MinScores["Context-Supply-Solution-Sentence"] * GetWeight(TempData[MainKey]["Context"]["Supply"]["Solution"]["Weight"])
                MaxScores[CollectionId]["Context-Supply-Solution-Keyword"] = MinScores["Context-Supply-Solution-Keyword"] * GetWeight(TempData[MainKey]["Context"]["Supply"]["Solution"]["Weight"])
                ## MinScores 초기화 ##

            if ResultField == "Context-Summary":
                MaxScores[CollectionId]["Context-Summary"] = max(MaxScores[CollectionId]["Context-Summary"], ResultScore)
            elif ResultField == "Context-KeyWord":
                MaxScores[CollectionId]["Context-KeyWord"] = max(MaxScores[CollectionId]["Context-KeyWord"], ResultScore)
            elif ResultField == "Context-Demand-Needs-Sentence":
                MaxScores[CollectionId]["Context-Demand-Needs-Sentence"] = max(MaxScores[CollectionId]["Context-Demand-Needs-Sentence"], ResultScore)
            elif ResultField == "Context-Demand-Needs-Keyword":
                MaxScores[CollectionId]["Context-Demand-Needs-Keyword"] = max(MaxScores[CollectionId]["Context-Demand-Needs-Keyword"], ResultScore)
            elif ResultField == "Context-Demand-Purpose-Sentence":
                MaxScores[CollectionId]["Context-Demand-Purpose-Sentence"] = max(MaxScores[CollectionId]["Context-Demand-Purpose-Sentence"], ResultScore)
            elif ResultField == "Context-Demand-Purpose-Keyword":
                MaxScores[CollectionId]["Context-Demand-Purpose-Keyword"] = max(MaxScores[CollectionId]["Context-Demand-Purpose-Keyword"], ResultScore)
            elif ResultField == "Context-Demand-Question-Sentence":
                MaxScores[CollectionId]["Context-Demand-Question-Sentence"] = max(MaxScores[CollectionId]["Context-Demand-Question-Sentence"], ResultScore)
            elif ResultField == "Context-Demand-Question-Keyword":
                MaxScores[CollectionId]["Context-Demand-Question-Keyword"] = max(MaxScores[CollectionId]["Context-Demand-Question-Keyword"], ResultScore)
            elif ResultField == "Context-Supply-Satisfy-Sentence":
                MaxScores[CollectionId]["Context-Supply-Satisfy-Sentence"] = max(MaxScores[CollectionId]["Context-Supply-Satisfy-Sentence"], ResultScore)
            elif ResultField == "Context-Supply-Satisfy-Keyword":
                MaxScores[CollectionId]["Context-Supply-Satisfy-Keyword"] = max(MaxScores[CollectionId]["Context-Supply-Satisfy-Keyword"], ResultScore)
            elif ResultField == "Context-Supply-Support-Sentence":
                MaxScores[CollectionId]["Context-Supply-Support-Sentence"] = max(MaxScores[CollectionId]["Context-Supply-Support-Sentence"], ResultScore)
            elif ResultField == "Context-Supply-Support-Keyword":
                MaxScores[CollectionId]["Context-Supply-Support-Keyword"] = max(MaxScores[CollectionId]["Context-Supply-Support-Keyword"], ResultScore)
            elif ResultField == "Context-Supply-Solution-Sentence":
                MaxScores[CollectionId]["Context-Supply-Solution-Sentence"] = max(MaxScores[CollectionId]["Context-Supply-Solution-Sentence"], ResultScore)
            elif ResultField == "Context-Supply-Solution-Keyword":
                MaxScores[CollectionId]["Context-Supply-Solution-Keyword"] = max(MaxScores[CollectionId]["Context-Supply-Solution-Keyword"], ResultScore)
            # print(f'MaxScores[{CollectionId}] ::: {MaxScores[CollectionId]}\n')
    
    # 최종 스코어 계산
    FinalResultDics = []
    for CollectionId, Scores in MaxScores.items():
        ContextSummaryScore = Scores["Context-Summary"]
        ContextKeyWordScore = Scores["Context-KeyWord"]
        ContextDemandNeedsScore = (Scores["Context-Demand-Needs-Sentence"] + Scores["Context-Demand-Needs-Keyword"]) / 6
        ContextDemandPurposeScore = (Scores["Context-Demand-Purpose-Sentence"] + Scores["Context-Demand-Purpose-Keyword"]) / 6
        ContextDemandQuestionScore = (Scores["Context-Demand-Question-Sentence"] + Scores["Context-Demand-Question-Keyword"]) / 6
        ContextSupplySatisfyScore = (Scores["Context-Supply-Satisfy-Sentence"] + Scores["Context-Supply-Satisfy-Keyword"]) / 6
        ContextSupplySupportScore = (Scores["Context-Supply-Support-Sentence"] + Scores["Context-Supply-Support-Keyword"]) / 6
        ContextSupplySolutionScore = (Scores["Context-Supply-Solution-Sentence"] + Scores["Context-Supply-Solution-Keyword"]) / 6
        
        # 최종 스코어 계산
        FinalResultScore = ContextSummaryScore * ContextKeyWordScore * ContextDemandNeedsScore * ContextDemandPurposeScore * ContextDemandQuestionScore * ContextSupplySatisfyScore * ContextSupplySupportScore * ContextSupplySolutionScore
        
        FinalResultDics.append({"Collection": collection, "CollectionId": CollectionId, "Score": FinalResultScore})

    # score 내림차순(유사도 높은 순) 정렬 후 상위 10개 추출
    FinalResultDics = sorted(FinalResultDics, key = lambda x: x["Score"], reverse = True)[:10]
    
    ## H. 최종 결과 출력 ##
    Result = []
    for i, FinalResultDic in enumerate(FinalResultDics):
        collection = FinalResultDic["Collection"]
        Score = FinalResultDic["Score"]
        CollectionId = FinalResultDic["CollectionId"]
        with open(TempFilePaths[CollectionId], 'r', encoding = 'utf-8') as TempFile:
            TempData = json.load(TempFile)
        FinalResult = {"Rank": i + 1, "Score": Score, "Collection": collection, "CollectionId": CollectionId, "CollectionAnalysis": TempData[MainKey]}
        Result.append(FinalResult)
    
    return Result

## Pinecone에 CollectionData 검색 ##
def SearchCollectionData(CollectionDataList, Intention, Collection, Range):
    Results = []
    for CollectionData in CollectionDataList:
        Result = SearchEmbeddedData(CollectionData, Intention, Collection, Range)
        Results.append(Result)
    
    return Results

## 검색 CollectionData 구축
def YaaSsearch(projectName, email, Search, Intention, Extension, Collection, Range):
    ## A. Search ##
    if Search['Type'] == "Search":
        InputDic = {"Input": Search['Term'], "Extension": Extension}
        
        CollectionDataList = []
        if Intention == "Similarity":
            Search = DemandCollectionDataDetailProcessUpdate(projectName, email, InputDic)
            CollectionDataList.append(Search)
            
            Search = SupplyCollectionDataDetailProcessUpdate(projectName, email, InputDic)
            CollectionDataList.append(Search)

        if Intention == "Demand":
            Search = DemandCollectionDataDetailProcessUpdate(projectName, email, InputDic)
            CollectionDataList.append(Search)

        if Intention == "Supply":
            Search = SupplyCollectionDataDetailProcessUpdate(projectName, email, InputDic)
            CollectionDataList.append(Search)
        sys.exit()
            
        Results = SearchCollectionData(CollectionDataList, Intention, Collection, Range)
    
    ## B. Match ##
    elif Search['Type'] == "Match":
        
        CollectionDataList = []
        CollectionDataMatch = re.match(r"([A-Za-z]+)_\((\d+)\).*", Search['Term'])
        if CollectionDataMatch:
            InputCollection = CollectionDataMatch.group(1).replace('Data', '')
            InputCollectionId = CollectionDataMatch.group(2)
        InputMainKey, InputTempFilePaths = GetCollectionDataPaths(InputCollection)
        with open(InputTempFilePaths[InputCollectionId], 'r', encoding = 'utf-8') as InputTempFile:
            CollectionData = json.load(InputTempFile)
            # CollectionData의 MainKey를 CollectionAnalysis로 통일
            CollectionData['CollectionAnalysis'] = CollectionData.pop(InputMainKey)
            CollectionDataList.append(CollectionData)
            
        Results = SearchCollectionData(CollectionDataList, Intention, Collection, Range)
    
    return Results

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    Search = {"Type": "Search", "Term": "나는 지금 몸무게가 67키로그램의 30대 남성인데, 1달만에 60키로로 빼고 싶습니다."} # Type: Search, Match // Term: SearchTerm, PublisherData_(Id)
    Intention = "Demand" # Similarity, Demand, Supply ...
    Extension = "Expertise" # Expertise, Ultimate, Detail, Rethinking ...
    Collection = "publisher" # Entire, Target, Trend, Publisher, Book ...
    Range = 100 # 10-100
    #########################################################################
    Results = YaaSsearch(projectName, email, Search, Intention, Extension, Collection, Range)
    
    for Result in Results:
        print(f"{Result}\n")