import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm

from backend.b2_Solution.b22_DataCollection.b221_VectorDatabase.b2211_DemandCollectionDataGen import DemandCollectionDataProcessUpdate
from backend.b2_Solution.b22_DataCollection.b221_VectorDatabase.b2212_SupplyCollectionDataGen import SupplyCollectionDataProcessUpdate
from backend.b2_Solution.b22_DataCollection.b221_VectorDatabase.b2213_SearchCollectionDataFilter import SearchCollectionDataFilterProcessUpdate

## Pinecone에 인덱스 생성
def Pinecone_CreateIndex(Name, IndexDimension = 1536):
    PineConeClient = Pinecone(api_key = os.getenv("PINECONE_API_KEY"))
    # Pinecone 인덱스 생성
    if not PineConeClient.has_index(Collection):
        PineConeClient.create_index(
            name = Name,
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
def SearchEmbeddedData(VDBIndex, CollectionData, Type, TermText, Intention, Collection, Range): # Intention: 'similarity', 'demand, 'supply' // Collection: 'entire', 'target', 'trend', 'publisher', 'book'...
    ## A. TempFilePaths, MainKey 생성 ##
    MainKey, TempFilePaths = GetCollectionDataPaths(Collection)
    
    ## B. 검색 쿼리와 가중치 ##
    # Context-Weight
    ContextQueryWeight = GetWeight(CollectionData['Weight'])
    # 1) Context-Summary
    ContextSummaryQueryText = CollectionData['Summary']
    # 2) Context-KeyWord
    ContextKeyWordQueryText = ", ".join(CollectionData['KeyWord'])

    if Intention in ['Demand', 'Similarity']:
        # Context-Demand-Needs-Weight
        ContextDemandNeedsQueryWeight = GetWeight(CollectionData['Demand']['Needs']['Weight'])
        # 3) Context-Demand-Needs-Sentence
        ContextDemandNeedsSentenceQueryText = CollectionData['Demand']['Needs']['Sentence']
        # 4) Context-Demand-Needs-Keyword
        ContextDemandNeedsKeywordQueryText = ", ".join(CollectionData['Demand']['Needs']['KeyWord'])

        # Context-Demand-Purpose-Weight
        ContextDemandPurposeQueryWeight = GetWeight(CollectionData['Demand']['Purpose']['Weight'])
        # 5) Context-Demand-Purpose-Sentence
        ContextDemandPurposeSentenceQueryText = CollectionData['Demand']['Purpose']['Sentence']
        # 6) Context-Demand-Purpose-Keyword
        ContextDemandPurposeKeywordQueryText = ", ".join(CollectionData['Demand']['Purpose']['KeyWord'])

        # Context-Demand-Question-Weight
        ContextDemandQuestionQueryWeight = GetWeight(CollectionData['Demand']['Question']['Weight'])
        # 7) Context-Demand-Question-Sentence
        ContextDemandQuestionSentenceQueryText = CollectionData['Demand']['Question']['Sentence']
        # 8) Context-Demand-Question-Keyword
        ContextDemandQuestionKeywordQueryText = ", ".join(CollectionData['Demand']['Question']['KeyWord'])

    if Intention in ['Supply', 'Similarity']:
        # Context-Supply-Satisfy-Weight
        ContextSupplySatisfyQueryWeight = GetWeight(CollectionData['Supply']['Satisfy']['Weight'])
        # 9) Context-Supply-Satisfy-Sentence
        ContextSupplySatisfySentenceQueryText = CollectionData['Supply']['Satisfy']['Sentence']
        # 10) Context-Supply-Satisfy-Keyword
        ContextSupplySatisfyKeywordQueryText = ", ".join(CollectionData['Supply']['Satisfy']['KeyWord'])

        # Context-Supply-Support-Weight
        ContextSupplySupportQueryWeight = GetWeight(CollectionData['Supply']['Support']['Weight'])
        # 11) Context-Supply-Support-Sentence
        ContextSupplySupportSentenceQueryText = CollectionData['Supply']['Support']['Sentence']
        # 12) Context-Supply-Support-Keyword
        ContextSupplySupportKeywordQueryText = ", ".join(CollectionData['Supply']['Support']['KeyWord'])

        # Context-Supply-Solution-Weight
        ContextSupplySolutionQueryWeight = GetWeight(CollectionData['Supply']['Solution']['Weight'])
        # 13) Context-Supply-Solution-Sentence
        ContextSupplySolutionSentenceQueryText = CollectionData['Supply']['Solution']['Sentence']
        # 14) Context-Supply-Solution-Keyword
        ContextSupplySolutionKeywordQueryText = ", ".join(CollectionData['Supply']['Solution']['KeyWord'])

    ## C. 검색 옵션 설정 ##
    # Similarity = 유사도검색 : 유사한 정보/대상 검색
    if Intention == 'Similarity':
        QueryList = [{"Field": "Context-Summary", "Text": ContextSummaryQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-KeyWord", "Text": ContextKeyWordQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-Demand-Needs-Sentence", "Text": ContextDemandNeedsSentenceQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Needs-Keyword", "Text": ContextDemandNeedsKeywordQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Purpose-Sentence", "Text": ContextDemandPurposeSentenceQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Purpose-Keyword", "Text": ContextDemandPurposeKeywordQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Question-Sentence", "Text": ContextDemandQuestionSentenceQueryText, "Weight": ContextDemandQuestionQueryWeight}, {"Field": "Context-Demand-Question-Keyword", "Text": ContextDemandQuestionKeywordQueryText, "Weight": ContextDemandQuestionQueryWeight}, {"Field": "Context-Supply-Satisfy-Sentence", "Text": ContextSupplySatisfySentenceQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Satisfy-Keyword", "Text": ContextSupplySatisfyKeywordQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Support-Sentence", "Text": ContextSupplySupportSentenceQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Support-Keyword", "Text": ContextSupplySupportKeywordQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Solution-Sentence", "Text": ContextSupplySolutionSentenceQueryText, "Weight": ContextSupplySolutionQueryWeight}, {"Field": "Context-Supply-Solution-Keyword", "Text": ContextSupplySolutionKeywordQueryText, "Weight": ContextSupplySolutionQueryWeight}]
    # Demand = 수요검색 : 나에게 필요한 정보/대상 검색
    elif Intention == 'Demand':
        QueryList = [{"Field": "Context-Summary", "Text": ContextSummaryQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-KeyWord", "Text": ContextKeyWordQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-Demand-Needs-Sentence", "Text": ContextDemandNeedsSentenceQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Needs-Keyword", "Text": ContextDemandNeedsKeywordQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Purpose-Sentence", "Text": ContextDemandPurposeSentenceQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Purpose-Keyword", "Text": ContextDemandPurposeKeywordQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Question-Sentence", "Text": ContextDemandQuestionSentenceQueryText, "Weight": ContextDemandQuestionQueryWeight}, {"Field": "Context-Demand-Question-Keyword", "Text": ContextDemandQuestionKeywordQueryText, "Weight": ContextDemandQuestionQueryWeight}]
    # Supply = 공급검색 : 나를 필요로 하는 정보/대상 검색
    elif Intention == 'Supply':
        QueryList = [{"Field": "Context-Summary", "Text": ContextSummaryQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-KeyWord", "Text": ContextKeyWordQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-Supply-Satisfy-Sentence", "Text": ContextSupplySatisfySentenceQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Satisfy-Keyword", "Text": ContextSupplySatisfyKeywordQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Support-Sentence", "Text": ContextSupplySupportSentenceQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Support-Keyword", "Text": ContextSupplySupportKeywordQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Solution-Sentence", "Text": ContextSupplySolutionSentenceQueryText, "Weight": ContextSupplySolutionQueryWeight}, {"Field": "Context-Supply-Solution-Keyword", "Text": ContextSupplySolutionKeywordQueryText, "Weight": ContextSupplySolutionQueryWeight}]

    # 검색 결과를 저장하기 위한 dict (DocId를 기준으로 저장)
    QueryResultList = []
    MinScores = {}
    MaxScores = {}
    ## D. 각 필드에 대한 검색 쿼리 생성 ##
    # Result Score 계산 TQDM 셋팅
    UpdateTQDM = tqdm(QueryList,
                    total = len(QueryList),
                    desc = f'YaaS VDB Search ({Type}): {TermText}')

    for Query in UpdateTQDM:
        UpdateTQDM.set_description(f'Search: {Query["Field"]}')
        time.sleep(0.0001)
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
    # Result Score 계산 TQDM 셋팅
    UpdateTQDM = tqdm(QueryResultList,
                    total = len(QueryResultList),
                    desc = f'YaaS VDB Score Calculate ({Type}): {TermText}')
    
    for QueryResult in UpdateTQDM:
        UpdateTQDM.set_description(f'Score Calculate: {QueryResult["matches"][0]["metadata"]["Field"]}')
        time.sleep(0.0001)
        # 가장 높은 유사도 점수와 CollectionId를 사용
        for result in QueryResult["matches"]:
            collection = result["metadata"]["Collection"]
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
                if Intention in ['Demand', 'Similarity']:
                    MaxScores[CollectionId]["Context-Demand-Needs-Sentence"] = MinScores["Context-Demand-Needs-Sentence"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Needs"]["Weight"])
                    MaxScores[CollectionId]["Context-Demand-Needs-Keyword"] = MinScores["Context-Demand-Needs-Keyword"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Needs"]["Weight"])
                    MaxScores[CollectionId]["Context-Demand-Purpose-Sentence"] = MinScores["Context-Demand-Purpose-Sentence"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Purpose"]["Weight"])
                    MaxScores[CollectionId]["Context-Demand-Purpose-Keyword"] = MinScores["Context-Demand-Purpose-Keyword"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Purpose"]["Weight"])
                    MaxScores[CollectionId]["Context-Demand-Question-Sentence"] = MinScores["Context-Demand-Question-Sentence"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Question"]["Weight"])
                    MaxScores[CollectionId]["Context-Demand-Question-Keyword"] = MinScores["Context-Demand-Question-Keyword"] * GetWeight(TempData[MainKey]["Context"]["Demand"]["Question"]["Weight"])
                elif Intention in ['Supply', 'Similarity']:
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
        if Intention == 'Demand':
            ContextDemandNeedsScore = (Scores["Context-Demand-Needs-Sentence"] + Scores["Context-Demand-Needs-Keyword"]) / 3
            ContextDemandPurposeScore = (Scores["Context-Demand-Purpose-Sentence"] + Scores["Context-Demand-Purpose-Keyword"]) / 3
            ContextDemandQuestionScore = (Scores["Context-Demand-Question-Sentence"] + Scores["Context-Demand-Question-Keyword"]) / 3
            FinalResultScore = ContextSummaryScore * ContextKeyWordScore * ContextDemandNeedsScore * ContextDemandPurposeScore * ContextDemandQuestionScore
        elif Intention == 'Supply':
            ContextSupplySatisfyScore = (Scores["Context-Supply-Satisfy-Sentence"] + Scores["Context-Supply-Satisfy-Keyword"]) / 3
            ContextSupplySupportScore = (Scores["Context-Supply-Support-Sentence"] + Scores["Context-Supply-Support-Keyword"]) / 3
            ContextSupplySolutionScore = (Scores["Context-Supply-Solution-Sentence"] + Scores["Context-Supply-Solution-Keyword"]) / 3
            FinalResultScore = ContextSummaryScore * ContextKeyWordScore * ContextSupplySatisfyScore * ContextSupplySupportScore * ContextSupplySolutionScore
        elif Intention == 'Similarity':
            ContextDemandNeedsScore = (Scores["Context-Demand-Needs-Sentence"] + Scores["Context-Demand-Needs-Keyword"]) / 6
            ContextDemandPurposeScore = (Scores["Context-Demand-Purpose-Sentence"] + Scores["Context-Demand-Purpose-Keyword"]) / 6
            ContextDemandQuestionScore = (Scores["Context-Demand-Question-Sentence"] + Scores["Context-Demand-Question-Keyword"]) / 6
            ContextSupplySatisfyScore = (Scores["Context-Supply-Satisfy-Sentence"] + Scores["Context-Supply-Satisfy-Keyword"]) / 6
            ContextSupplySupportScore = (Scores["Context-Supply-Support-Sentence"] + Scores["Context-Supply-Support-Keyword"]) / 6
            ContextSupplySolutionScore = (Scores["Context-Supply-Solution-Sentence"] + Scores["Context-Supply-Solution-Keyword"]) / 6
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

## Demand와 Supply를 합쳐서 Similarity로 재구조화 함수
def RestructureSimilarity(CollectionDataChainSet, Type):
    # SimilaritySearch 재구조화
    NewCollectionDataChainSet = {"SimilaritySearch": CollectionDataChainSet['SimilaritySearch']}
    # SimilarityDetail 재구조화
    if Type == 'Search':
        SimilarityDetail = {"Summary": f"{CollectionDataChainSet['DemandDetail']['Summary']} {CollectionDataChainSet['SupplyDetail']['Summary']}", "Needs":f"{CollectionDataChainSet['DemandDetail']['Needs']} {CollectionDataChainSet['SupplyDetail']['Satisfy']}", "Purpose":f"{CollectionDataChainSet['DemandDetail']['Purpose']} {CollectionDataChainSet['SupplyDetail']['Support']}", "Question":f"{CollectionDataChainSet['DemandDetail']['Question']} {CollectionDataChainSet['SupplyDetail']['Solution']}", "Weight": (CollectionDataChainSet['DemandDetail']['Weight'] + CollectionDataChainSet['SupplyDetail']['Weight']) / 2, "Feedback": CollectionDataChainSet['DemandDetail']['Feedback'] + CollectionDataChainSet['SupplyDetail']['Feedback']}
        NewCollectionDataChainSet['SimilarityDetail'] = SimilarityDetail
    elif Type == 'Match':
        NewCollectionDataChainSet['SimilarityDetail'] = CollectionDataChainSet['SimilarityDetail']
    # SimilarityContext 재구조화
    NewCollectionDataChainSet['SimilarityContext'] = {"Summary": f"{CollectionDataChainSet['DemandContext']['Summary']} {CollectionDataChainSet['SupplyContext']['Summary']}", "KeyWord": CollectionDataChainSet['DemandContext']['KeyWord'] + CollectionDataChainSet['SupplyContext']['KeyWord'], "Demand": CollectionDataChainSet['DemandContext']['Demand'], "Supply": CollectionDataChainSet['SupplyContext']['Supply'], 'Weight': (CollectionDataChainSet['DemandContext']['Weight'] + CollectionDataChainSet['SupplyContext']['Weight']) / 2}
    # SimilarityContextExpertise 재구조화
    if ('DemandContextExpertise' in CollectionDataChainSet) or ('SupplyContextExpertise' in CollectionDataChainSet):
        SimilarityContextExpertise = []
        for DemandContextExpertise, SupplyContextExpertise in zip(CollectionDataChainSet['DemandContextExpertise'], CollectionDataChainSet['SupplyContextExpertise']):
            SimilarityContextExpertise.append({"Summary": f"{DemandContextExpertise['Summary']} {SupplyContextExpertise['Summary']}", "KeyWord": DemandContextExpertise['KeyWord'] + SupplyContextExpertise['KeyWord'], "Demand": DemandContextExpertise['Demand'], "Supply": SupplyContextExpertise['Supply'], 'Weight': (DemandContextExpertise['Weight'] + SupplyContextExpertise['Weight']) / 2})
        NewCollectionDataChainSet['SimilarityContextExpertise'] = SimilarityContextExpertise
    # SimilarityContextUltimate 재구조화
    if ('DemandContextUltimate' in CollectionDataChainSet) or ('SupplyContextUltimate' in CollectionDataChainSet):
        SimilarityContextUltimate = []
        for DemandContextUltimate, SupplyContextUltimate in zip(CollectionDataChainSet['DemandContextUltimate'], CollectionDataChainSet['SupplyContextUltimate']):
            SimilarityContextUltimate.append({"Summary": f"{DemandContextUltimate['Summary']} {SupplyContextUltimate['Summary']}", "KeyWord": DemandContextUltimate['KeyWord'] + SupplyContextUltimate['KeyWord'], "Demand": DemandContextUltimate['Demand'], "Supply": SupplyContextUltimate['Supply'], 'Weight': (DemandContextUltimate['Weight'] + SupplyContextUltimate['Weight']) / 2})
        NewCollectionDataChainSet['SimilarityContextUltimate'] = SimilarityContextUltimate
    # SimilarityContextDetail 재구조화
    if ('DemandContextDetail' in CollectionDataChainSet) or ('SupplyContextDetail' in CollectionDataChainSet):
        SimilarityContextDetail = []
        for DemandContextDetail, SupplyContextDetail in zip(CollectionDataChainSet['DemandContextDetail'], CollectionDataChainSet['SupplyContextDetail']):
            SimilarityContextDetail.append({"Summary": f"{DemandContextDetail['Summary']} {SupplyContextDetail['Summary']}", "KeyWord": DemandContextDetail['KeyWord'] + SupplyContextDetail['KeyWord'], "Demand": DemandContextDetail['Demand'], "Supply": SupplyContextDetail['Supply'], 'Weight': (DemandContextDetail['Weight'] + SupplyContextDetail['Weight']) / 2})
        NewCollectionDataChainSet['SimilarityContextDetail'] = SimilarityContextDetail
    # SimilarityContextRethinking 재구조화
    if ('DemandContextRethinking' in CollectionDataChainSet) or ('SupplyContextRethinking' in CollectionDataChainSet):
        SimilarityContextRethinking = []
        for DemandContextRethinking, SupplyContextRethinking in zip(CollectionDataChainSet['DemandContextRethinking'], CollectionDataChainSet['SupplyContextRethinking']):
            SimilarityContextRethinking.append({"Summary": f"{DemandContextRethinking['Summary']} {SupplyContextRethinking['Summary']}", "KeyWord": DemandContextRethinking['KeyWord'] + SupplyContextRethinking['KeyWord'], "Demand": DemandContextRethinking['Demand'], "Supply": SupplyContextRethinking['Supply'], 'Weight': (DemandContextRethinking['Weight'] + SupplyContextRethinking['Weight']) / 2})
        NewCollectionDataChainSet['SimilarityContextRethinking'] = SimilarityContextRethinking
    
    return NewCollectionDataChainSet

## SearchResult Analysis와 Search를 묶어서 재구조화 함수
def RestructureSearchResult(SearchResult, IntentionKey):
    if IntentionKey in SearchResult['SearchResult']:
        # CollectionAnalysis와 CollectionSearch 추출
        CollectionAnalysis = SearchResult['SearchResult'][IntentionKey]['CollectionAnalysis']
        CollectionSearch = SearchResult['SearchResult'][IntentionKey]['CollectionSearch']
        NewSupplyContextExpertise = []
        # Analysis와 Search를 순서대로 묶기
        for i in range(len(CollectionAnalysis)):
            AnalysisData = CollectionAnalysis[i]
            SearchData = CollectionSearch[i]
            NewSupplyContextExpertise.append({
                "CollectionAnalysis": AnalysisData,
                "CollectionSearch": SearchData
            })
        # 새로 생성된 구조로 덮어쓰기
        SearchResult['SearchResult'][IntentionKey] = NewSupplyContextExpertise

## Pinecone에 CollectionData 검색 ##
def SearchCollectionData(CollectionDataChainSet, DateTime, Type, TermText, Intention, Extension, Collection, Range, Name = 'collection'):
    print(f"[ YaaS VDB Search CollectionData ({Type}): {TermText} | Intention({Intention}) | Extension({Extension}) | Collection({Collection}) | Range({Range}) 시작 ]")
    ## TotalPublisherData 경로 설정
    TotalSearchResultDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1513_SearchResultData/s15131_TotalSearchResultData"
    TotalSearchResultDataJsonPath = os.path.join(TotalSearchResultDataPath, 'TotalSearchResultData.json')
    TotalSearchResultDataTempPath = os.path.join(TotalSearchResultDataPath, 'TotalSearchResultDataTemp')
    
    ## A. Pinecone VDB 연결 ##
    PineConeClient = Pinecone_CreateIndex(Name)
    VDBIndex = PineConeClient.Index(Name)
    
    ## B. Similarity 재구조화 ##
    if Intention == 'Similarity':
        CollectionDataChainSet = RestructureSimilarity(CollectionDataChainSet, Type)
    
    ## C. Pinecone VDB 검색 및 결과 종합 ##
    SearchResult = {"SearchType": Type, "SearchIntention": Intention, "SearchCollection": Collection, "SearchRange": Range, "SearchResult": {}}

    # Search (Result 없음)
    intentionKey = Intention + "Search"
    if intentionKey in CollectionDataChainSet:
        CollectionData = CollectionDataChainSet[intentionKey]
        SearchResult['SearchResult'][intentionKey] = CollectionData
    else:
        SearchResult['SearchResult'][intentionKey] = None
    # Detail (Result 없음)
    intentionKey = Intention + "Detail"
    if intentionKey in CollectionDataChainSet:
        CollectionData = CollectionDataChainSet[intentionKey]
        SearchResult['SearchResult'][intentionKey] = CollectionData
    else:
        SearchResult['SearchResult'][intentionKey] = None
    # Context
    intentionKey = Intention + "Context"
    if intentionKey in CollectionDataChainSet:
        CollectionData = CollectionDataChainSet[intentionKey]
        if intentionKey not in SearchResult['SearchResult']:
            SearchResult['SearchResult'][intentionKey] = {}
        SearchResult['SearchResult'][intentionKey]['CollectionAnalysis'] = CollectionData
        Result = SearchEmbeddedData(VDBIndex, CollectionData, Type, TermText, Intention, Collection, Range)
        SearchResult['SearchResult'][intentionKey]['CollectionSearch'] = Result
    else:
        SearchResult['SearchResult'][intentionKey] = None
        
    IntentionKeyList = []
    # ContextExpertise (연속 검색)
    intentionKey = Intention + "ContextExpertise"
    if intentionKey in CollectionDataChainSet:
        IntentionKeyList.append(intentionKey)
        CollectionDataList = CollectionDataChainSet[intentionKey]
        if intentionKey not in SearchResult['SearchResult']:
            SearchResult['SearchResult'][intentionKey] = {}
        SearchResult['SearchResult'][intentionKey]['CollectionAnalysis'] = CollectionDataList
        ResultList = []
        for CollectionData in CollectionDataList:
            Result = SearchEmbeddedData(VDBIndex, CollectionData, Type, TermText, Intention, Collection, Range)
            ResultList.append(Result)
        SearchResult['SearchResult'][intentionKey]['CollectionSearch'] = ResultList
    else:
        SearchResult['SearchResult'][intentionKey] = None
    # ContextUltimate (연속 검색)
    intentionKey = Intention + "ContextUltimate"
    if intentionKey in CollectionDataChainSet:
        IntentionKeyList.append(intentionKey)
        CollectionDataList = CollectionDataChainSet[intentionKey]
        if intentionKey not in SearchResult['SearchResult']:
            SearchResult['SearchResult'][intentionKey] = {}
        SearchResult['SearchResult'][intentionKey]['CollectionAnalysis'] = CollectionDataList
        ResultList = []
        for CollectionData in CollectionDataList:
            Result = SearchEmbeddedData(VDBIndex, CollectionData, Type, TermText, Intention, Collection, Range)
            ResultList.append(Result)
        SearchResult['SearchResult'][intentionKey]['CollectionSearch'] = ResultList
    else:
        SearchResult['SearchResult'][intentionKey] = None
    # ContextDetail (연속 검색)
    intentionKey = Intention + "ContextDetail"
    if intentionKey in CollectionDataChainSet:
        IntentionKeyList.append(intentionKey)
        CollectionDataList = CollectionDataChainSet[intentionKey]
        if intentionKey not in SearchResult['SearchResult']:
            SearchResult['SearchResult'][intentionKey] = {}
        SearchResult['SearchResult'][intentionKey]['CollectionAnalysis'] = CollectionDataList
        ResultList = []
        for CollectionData in CollectionDataList:
            Result = SearchEmbeddedData(VDBIndex, CollectionData, Type, TermText, Intention, Collection, Range)
            ResultList.append(Result)
        SearchResult['SearchResult'][intentionKey]['CollectionSearch'] = ResultList
    # ContextRethinking (연속 검색)
    intentionKey = Intention + "ContextRethinking"
    if intentionKey in CollectionDataChainSet:
        IntentionKeyList.append(intentionKey)
        CollectionDataList = CollectionDataChainSet[intentionKey]
        if intentionKey not in SearchResult['SearchResult']:
            SearchResult['SearchResult'][intentionKey] = {}
        SearchResult['SearchResult'][intentionKey]['CollectionAnalysis'] = CollectionDataList
        ResultList = []
        for CollectionData in CollectionDataList:
            Result = SearchEmbeddedData(VDBIndex, CollectionData, Type, TermText, Intention, Collection, Range)
            ResultList.append(Result)
        SearchResult['SearchResult'][intentionKey]['CollectionSearch'] = ResultList

    ## D. SearchResult 재구조화 ##
    for IntentionKey in IntentionKeyList:
        RestructureSearchResult(SearchResult, IntentionKey)
        
    ## E. SearchResult 재구성 ##
    
    ## E. DataTempJson 저장 ##
    # TotalSearchResultDataTempPath 폴더가 없으면 생성
    if not os.path.exists(TotalSearchResultDataTempPath):
        os.makedirs(TotalSearchResultDataTempPath)
        
    # DataTempJson 저장
    DataTempJsonPath = os.path.join(TotalSearchResultDataTempPath, f"SearchResultData_({DateTime})_{TermText}.json")
    with open(DataTempJsonPath, 'w', encoding = 'utf-8') as DataTempJson:
        json.dump(SearchResult, DataTempJson, ensure_ascii = False, indent = 4)

    print(f"[ YaaS VDB Search CollectionData ({Type}): {TermText} | Intention({Intention}) | Extension({Extension}) | Collection({Collection}) | Range({Range}) 완료 ]")
        
    return SearchResult, DataTempJsonPath

## Match 데이터 키값의 한글화
def ChangeKeys(CollectionData, Intention):
    if Intention == "Demand":
        NewCollectionData = {
            '핵심목적': CollectionData["Summary"],
            '분야': CollectionData["KeyWord"],
            '필요': {
                '필요내용': {
                    '설명': CollectionData["Demand"]["Needs"]["Sentence"],
                    '키워드': CollectionData["Demand"]["Needs"]["KeyWord"],
                    '중요도': CollectionData["Demand"]["Needs"]["Weight"],
                },
                '필요목표': {
                    '설명': CollectionData["Demand"]["Purpose"]["Sentence"],
                    '키워드': CollectionData["Demand"]["Purpose"]["KeyWord"],
                    '중요도': CollectionData["Demand"]["Purpose"]["Weight"],
                },
                '필요질문': {
                    '설명': CollectionData["Demand"]["Question"]["Sentence"],
                    '키워드': CollectionData["Demand"]["Question"]["KeyWord"],
                    '중요도': CollectionData["Demand"]["Question"]["Weight"],
                }
            },
            '정보의질': CollectionData["Weight"]
        }
    elif Intention == "Supply":
        NewCollectionData = {
            '핵심솔루션': CollectionData["Supply"]["Satisfy"]["Sentence"],
            '분야': CollectionData["Supply"]["Satisfy"]["KeyWord"],
            '제안': {
                '제안내용': {
                    '설명': CollectionData["Supply"]["Satisfy"]["Sentence"],
                    '키워드': CollectionData["Supply"]["Satisfy"]["KeyWord"],
                    '중요도': CollectionData["Supply"]["Satisfy"]["Weight"],
                },
                '제안할목표': {
                    '설명': CollectionData["Supply"]["Support"]["Sentence"],
                    '키워드': CollectionData["Supply"]["Support"]["KeyWord"],
                    '중요도': CollectionData["Supply"]["Support"]["Weight"],
                },
                '제안할해결책': {
                    '설명': CollectionData["Supply"]["Solution"]["Sentence"],
                    '키워드': CollectionData["Supply"]["Solution"]["KeyWord"],
                    '중요도': CollectionData["Supply"]["Solution"]["Weight"],
                }
            },
            '정보의질': CollectionData["Weight"]
        }
    return NewCollectionData

## CollectionData 검색
def YaaSsearch(projectName, email, Search, Intention, Extension, Collection, Range, MessagesReview):
    ## A. 검색어 검사 ##Type = Search['Type'] ##
    ## A-1. Match, Search 검색어 패턴 검사
    MatchPattern = r'^([A-Za-z]+_\(\d+\))'
    if re.match(MatchPattern, Search):
        Type = "Match"
    else:
        Type = "Search"
    
    ## A-2. 요약 검색어 생성
    Term = Search
    if Type == "Match":
        TermText = f"[{Term}]"
    elif Type == "Search":
        TermText = f"[{Term[:20]}]"

    ## B. Search ##
    print(f"[ YaaS Gen Chain CollectionData ({Type}): {TermText} | Intention({Intention}) | Extension({Extension}) | Collection({Collection}) | Range({Range}) 시작 ]")
    ## B-1. Search 존재 여부 확인 ##
    TotalSearchResultDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_SearchData/s1513_SearchResultData/s15131_TotalSearchResultData"
    TotalSearchResultDataTempPath = os.path.join(TotalSearchResultDataPath, 'TotalSearchResultDataTemp')
    
    # 검색어 포함 파일 여부 확인
    ExistingSearchResultDatas = os.listdir(TotalSearchResultDataTempPath)
    MatchedSearchResultData = [FileName for FileName in ExistingSearchResultDatas if TermText in FileName and "_Filtered.json" in FileName]
    
    ## 기존 검색결과가 존재할 경우
    if MatchedSearchResultData:
        FilePath = os.path.join(TotalSearchResultDataTempPath, MatchedSearchResultData[0])
        print(f"[ YaaS Gen Chain CollectionData ({Type}): {TermText} | Intention({Intention}) | Extension({Extension}) | Collection({Collection}) | Range({Range}) 동일한 검색 결과가 이미 존재함 ]\n")
    
        with open(FilePath, 'r', encoding = 'utf-8') as FilteredSearchJson:
            FilteredSearchResult = json.load(FilteredSearchJson)
            
        return FilteredSearchResult
    
    ## 기존 검색결과가 존재하지 않는 경우
    else:
        if Type == "Search":
            ## B-1. Search: Similarity CollectionDataChain 프로세스 ##
            if Intention == "Similarity":
                CollectionDataChainSet = {f"SimilaritySearch": {"Term": Term}}
            else:
                CollectionDataChainSet = {}
            
            # InputDic 생성
            InputDic = {"Type": Type, "Input": Term, "Extension": Extension, "TermText": TermText}

            ## B-2. Search: Demand, Supply CollectionDataChain 프로세스 ##
            if Intention == "Demand":
                CollectionDataChain, DateTime = DemandCollectionDataProcessUpdate(projectName, email, InputDic, MessagesReview = MessagesReview)
                CollectionDataChainSet.update(CollectionDataChain)

            elif Intention == "Supply":
                CollectionDataChain, DateTime = SupplyCollectionDataProcessUpdate(projectName, email, InputDic, MessagesReview = MessagesReview)
                CollectionDataChainSet.update(CollectionDataChain)
                
            elif Intention == "Similarity":
                CollectionDataChain, DateTime = DemandCollectionDataProcessUpdate(projectName, email, InputDic, MessagesReview = MessagesReview)
                CollectionDataChainSet.update(CollectionDataChain)
                CollectionDataChain, DateTime = SupplyCollectionDataProcessUpdate(projectName, email, InputDic, MessagesReview = MessagesReview)
                CollectionDataChainSet.update(CollectionDataChain)
        
        ## C. Match ##
        elif Type == "Match":
            ## C-1. Match: Similarity CollectionDataChain 프로세스 ##
            if Intention == "Similarity":
                CollectionDataChainSet = {f"SimilaritySearch": {"Term": Term}}
            else:
                CollectionDataChainSet = {}
            
            # Match CollectionData 불러오기
            CollectionDataMatch = re.match(r"([A-Za-z]+)_\((\d+)\).*", Term)
            InputCollection = None
            if CollectionDataMatch:
                InputCollection = CollectionDataMatch.group(1).replace('Data', '')
                InputCollectionId = CollectionDataMatch.group(2)
            if InputCollection is None:
                sys.exit(f"[ YaaS Gen Chain CollectionData Error: 데이터명_(Id)가 존재하지 않음 ((({TermText}))) ]")
            InputMainKey, InputTempFilePaths = GetCollectionDataPaths(InputCollection)
            with open(InputTempFilePaths[InputCollectionId], 'r', encoding = 'utf-8') as InputTempFile:
                CollectionData = json.load(InputTempFile)
                # CollectionData의 MainKey를 CollectionAnalysis로 통일
                CollectionData['CollectionAnalysis'] = CollectionData.pop(InputMainKey)
                CollectionDataChainSet.update({f"{Intention}Detail": None})
                
            ## C-2. Match: Demand, Supply CollectionDataChain 프로세스 ##
            if Intention == "Demand":
                # InputDic 생성 및 기존 영어로 되어 있던 딕셔너리 키를 한글 키로 변경
                NewCollectionData = ChangeKeys(CollectionData['CollectionAnalysis']['Context'], Intention)
                InputDic = {"Type": Type, "Input": str(NewCollectionData), "Extension": Extension, "CollectionData": NewCollectionData, "TermText": TermText}
                
                CollectionDataChain, DateTime = DemandCollectionDataProcessUpdate(projectName, email, InputDic, MessagesReview = MessagesReview)
                CollectionDataChainSet.update(CollectionDataChain)

            elif Intention == "Supply":
                # InputDic 생성 및 기존 영어로 되어 있던 딕셔너리 키를 한글 키로 변경
                NewCollectionData = ChangeKeys(CollectionData['CollectionAnalysis']['Context'], Intention)
                InputDic = {"Type": Type, "Input": str(NewCollectionData), "Extension": Extension, "CollectionData": NewCollectionData, "TermText": TermText}
                
                CollectionDataChain, DateTime = SupplyCollectionDataProcessUpdate(projectName, email, InputDic, MessagesReview = MessagesReview)
                CollectionDataChainSet.update(CollectionDataChain)
                
            elif Intention == "Similarity":
                # InputDic 생성 및 기존 영어로 되어 있던 딕셔너리 키를 한글 키로 변경 'Similarity'의 경우 두번 변환
                NewCollectionData = ChangeKeys(CollectionData['CollectionAnalysis']['Context'], "Demand")
                InputDic = {"Type": Type, "Input": str(NewCollectionData), "Extension": Extension, "CollectionData": NewCollectionData, "TermText": TermText}
                
                CollectionDataChain, DateTime = DemandCollectionDataProcessUpdate(projectName, email, InputDic, MessagesReview = MessagesReview)
                CollectionDataChainSet.update(CollectionDataChain)
                
                # InputDic 생성 및 기존 영어로 되어 있던 딕셔너리 키를 한글 키로 변경 'Similarity'의 경우 두번 변환
                NewCollectionData = ChangeKeys(CollectionData['CollectionAnalysis']['Context'], "Supply")
                InputDic = {"Type": Type, "Input": str(NewCollectionData), "Extension": Extension, "CollectionData": NewCollectionData, "TermText": TermText}
                
                CollectionDataChain, DateTime = SupplyCollectionDataProcessUpdate(projectName, email, InputDic, MessagesReview = MessagesReview)
                CollectionDataChainSet.update(CollectionDataChain)
        
        # with open(f'CollectionDataChainSet({Type}).json', 'w', encoding = 'utf-8') as CollectionDataChainSetFile:
        #     json.dump(CollectionDataChainSet, CollectionDataChainSetFile, ensure_ascii = False, indent = 4)
        # sys.exit()
        ## D. CollectionDataChainSet Search ##
        print(f"[ YaaS Gen Chain CollectionData ({Type}): {TermText} | Intention({Intention}) | Extension({Extension}) | Collection({Collection}) | Range({Range}) 완료 ]\n")
        Result, DataTempJsonPath = SearchCollectionData(CollectionDataChainSet, DateTime, Type, TermText, Intention, Extension, Collection, Range)
        
        ## E. SearchCollectionDataFilterProcess ##
        FilteredSearchResult = SearchCollectionDataFilterProcessUpdate(projectName, email, Result, Intention, Extension, DataTempJsonPath)
        
        return FilteredSearchResult

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
    Result = YaaSsearch(projectName, email, Search, Intention, Extension, Collection, Range, MessagesReview)
    print(Result)