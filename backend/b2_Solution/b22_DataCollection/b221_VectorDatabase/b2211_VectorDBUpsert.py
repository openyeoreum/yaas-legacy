import os
import re
import json
import sys
sys.path.append("/yaas")

from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

## Pinecone에 인덱스 생성
def Pinecone_CreateIndex(CollectionName, IndexDimension = 1536):
    PineConeClient = Pinecone(api_key = os.getenv("PINECONE_API_KEY"))
    # Pinecone 인덱스 생성
    if not PineConeClient.has_index(CollectionName):
        PineConeClient.create_index(
            name = CollectionName,
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

## Pinecone에 임베딩 데이터 업서트
def UpsertEmbeddedData(CollectionData, CollectionName, LastId):
    ## Pinecone에 인덱스 생성
    PineConeClient = Pinecone_CreateIndex(CollectionName)
    VDBIndex = PineConeClient.Index(CollectionName)

    # Pinecone에 임베딩 데이터 업서트
    UpsertEmbeddedData = []
    Id = CollectionData['Id']
    DocId = f"{CollectionName}-{Id}"

    # 1) Context-Summary
    Field = "Context-Summary"
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Weight'], str):
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Weight'].replace('점', '')) / 100
    else:
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Weight']) / 100
    ContextSummaryText = CollectionData['CollectionAnalysis']['Context']['Summary']
    ContextSummaryVector = OpenAI_TextEmbedding(ContextSummaryText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSummaryVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })
    
    # 2) Context-KeyWord
    Field = "Context-KeyWord"
    ContextKeyWord = CollectionData['CollectionAnalysis']['Context']['KeyWord']
    ContextKeyWordText = ", ".join(ContextKeyWord)
    ContextKeyWordVector = OpenAI_TextEmbedding(ContextKeyWordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextKeyWordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })
    
    # 3) Context-Demand-Needs-Sentence
    Field = "Context-Demand-Needs-Sentence"
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['Weight'], str):
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['Weight'].replace('점', '')) / 100
    else:
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['Weight'])
    ContextDemandNeedsText = CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['Sentence']
    ContextDemandNeedsVector = OpenAI_TextEmbedding(ContextDemandNeedsText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandNeedsVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })
    
    # 4) Context-Demand-Needs-Keyword
    Field = "Context-Demand-Needs-Keyword"
    ContextDemandNeedsKeyword = CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['KeyWord']
    ContextDemandNeedsKeywordText = ", ".join(ContextDemandNeedsKeyword)
    ContextDemandNeedsKeywordVector = OpenAI_TextEmbedding(ContextDemandNeedsKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandNeedsKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })

    # 5) Context-Demand-Purpose-Sentence
    Field = "Context-Demand-Purpose-Sentence"
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['Weight'], str):
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['Weight'].replace('점', '')) / 100
    else:
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['Weight'])
    ContextDemandPurposeText = CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['Sentence']
    ContextDemandPurposeVector = OpenAI_TextEmbedding(ContextDemandPurposeText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandPurposeVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })

    # 6) Context-Demand-Purpose-Keyword
    Field = "Context-Demand-Purpose-Keyword"
    ContextDemandPurposeKeyword = CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['KeyWord']
    ContextDemandPurposeKeywordText = ", ".join(ContextDemandPurposeKeyword)
    ContextDemandPurposeKeywordVector = OpenAI_TextEmbedding(ContextDemandPurposeKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandPurposeKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })

    # 7) Context-Demand-Question-Sentence
    Field = "Context-Demand-Question-Sentence"
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['Weight'], str):
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['Weight'].replace('점', '')) / 100
    else:
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['Weight'])
    ContextDemandQuestionText = CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['Sentence']
    ContextDemandQuestionVector = OpenAI_TextEmbedding(ContextDemandQuestionText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandQuestionVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })

    # 8) Context-Demand-Question-Keyword
    Field = "Context-Demand-Question-Keyword"
    ContextDemandQuestionKeyword = CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['KeyWord']
    ContextDemandQuestionKeywordText = ", ".join(ContextDemandQuestionKeyword)
    ContextDemandQuestionKeywordVector = OpenAI_TextEmbedding(ContextDemandQuestionKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandQuestionKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })

    # 9) Context-Supply-Satisfy-Sentence
    Field = "Context-Supply-Satisfy-Sentence"
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['Weight'], str):
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['Weight'].replace('점', '')) / 100
    else:
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['Weight'])
    ContextSupplySatisfyText = CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['Sentence']
    ContextSupplySatisfyVector = OpenAI_TextEmbedding(ContextSupplySatisfyText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySatisfyVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })

    # 10) Context-Supply-Satisfy-Keyword
    Field = "Context-Supply-Satisfy-Keyword"
    ContextSupplySatisfyKeyword = CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['KeyWord']
    ContextSupplySatisfyKeywordText = ", ".join(ContextSupplySatisfyKeyword)
    ContextSupplySatisfyKeywordVector = OpenAI_TextEmbedding(ContextSupplySatisfyKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySatisfyKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })

    # 11) Context-Supply-Support-Sentence
    Field = "Context-Supply-Support-Sentence"
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['Weight'], str):
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['Weight'].replace('점', '')) / 100
    else:
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['Weight'])
    ContextSupplySupportText = CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['Sentence']
    ContextSupplySupportVector = OpenAI_TextEmbedding(ContextSupplySupportText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySupportVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })

    # 12) Context-Supply-Support-Keyword
    Field = "Context-Supply-Support-Keyword"
    ContextSupplySupportKeyword = CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['KeyWord']
    ContextSupplySupportKeywordText = ", ".join(ContextSupplySupportKeyword)
    ContextSupplySupportKeywordVector = OpenAI_TextEmbedding(ContextSupplySupportKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySupportKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })

    # 13) Context-Supply-Solution-Sentence
    Field = "Context-Supply-Solution-Sentence"
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['Weight'], str):
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['Weight'].replace('점', '')) / 100
    else:
        Weight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['Weight'])
    ContextSupplySolutionText = CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['Sentence']
    ContextSupplySolutionVector = OpenAI_TextEmbedding(ContextSupplySolutionText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySolutionVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })

    # 14) Context-Supply-Solution-Keyword
    Field = "Context-Supply-Solution-Keyword"
    ContextSupplySolutionKeyword = CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['KeyWord']
    ContextSupplySolutionKeywordText = ", ".join(ContextSupplySolutionKeyword)
    ContextSupplySolutionKeywordVector = OpenAI_TextEmbedding(ContextSupplySolutionKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySolutionKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Weight": Weight
            }
        })

    # Pinecone에 업서트
    VDBIndex.upsert(vectors = UpsertEmbeddedData, namespace = CollectionName)
    VDBStatus = VDBIndex.describe_index_stats()
    
    # Pinecone에 업서트 로딩에 따라서 달리 출력(로딩이 조금 늦음..)
    try:
        print(f"[ VDBIndexUpsert: {CollectionName} | Upsert: {DocId} -> {VDBStatus['namespaces'][CollectionName]} ({Id}/{LastId}) ]")
    except:
        print(f"[ VDBIndexUpsert: {CollectionName} | Upsert: {DocId} -> {VDBStatus['namespaces']} ({Id}/{LastId}) ]")
        
## Pinecone에 CollectionData 업서트
def UpsertCollectionData(TotalCollectionDataTempPath, CollectionName):
    print(f"[ VDBIndexUpsert: {CollectionName} | VBD에 {CollectionName}TempFile.json 리스트 업서트 시작 ]")
    
    # CollectionName의 첫 글자를 대문자로 변환
    ProperCollectionName = CollectionName[0].upper() + CollectionName[1:]
    # 정규표현식을 사용하여 파일명에서 (n) 추출
    TempJsonPattern = re.compile(rf'^{re.escape(ProperCollectionName)}Data_\((\d+)\)_.*\.json$')
    # 지정된 경로 내의 모든 파일 목록 가져오기
    CollectionTempDatas = os.listdir(TotalCollectionDataTempPath)
    # (Id) 값과 파일 경로를 튜플로 저장
    TempDataIdAndFileList = []
    for TempData in CollectionTempDatas:
        match = TempJsonPattern.match(TempData)
        if match:
            Id = int(match.group(1))
            DataTempFilePath = os.path.join(TotalCollectionDataTempPath, TempData)
            TempDataIdAndFileList.append((Id, DataTempFilePath))
        else:
            print(f"[ 패턴과 일치하지 않는 파일명 : {TempData} ]")
    
    # (Id) 값을 기준으로 정렬
    SortedTempDataIdAndFileList = sorted(TempDataIdAndFileList, key = lambda x: x[0])
    # 마지막(Id) 값 추출
    LastId = SortedTempDataIdAndFileList[-1][0]
    
    # CollectionData VDB에 업서트
    for CollectionTempFileTuffle in SortedTempDataIdAndFileList:
        Id = CollectionTempFileTuffle[0]
        CollectionDataTempFilePath = CollectionTempFileTuffle[1]
        with open(CollectionDataTempFilePath, 'r', encoding='utf-8') as CollectionDataTempJson:
            CollectionDataTempFile = json.load(CollectionDataTempJson)
        # VDB에 이미 업서트 되었는지 확인
        if 'VDB' not in CollectionDataTempFile:
            CollectionData = {'Id': Id, 'CollectionAnalysis': CollectionDataTempFile['PublisherAnalysis']}   
            UpsertEmbeddedData(CollectionData, CollectionName, LastId)
            CollectionDataTempFile['VDB'] = CollectionName
            with open(CollectionDataTempFilePath, 'w', encoding='utf-8') as CollectionDataTempJson:
                json.dump(CollectionDataTempFile, CollectionDataTempJson, ensure_ascii = False, indent = 4)
    
    print(f"[ VDBIndexUpsert: {CollectionName} | VBD에 {CollectionName}TempFile.json 리스트 업서트 완료 ]")
        
## Pinecone에 임베딩 데이터 검색
def SearchEmbeddedData(CollectionData, CollectionName = 'publisher', Matching = 'similarity', TopK = 50): # CollectionName: 'entire', 'target', 'trend', 'publisher', 'book'... // Matching: 'similarity', 'demand, 'supply'
    print(f"[ YaaS VDB Search: Collection({CollectionName}) | Matching({Matching}) | Top-K({TopK}) ]")
    
    PineConeClient = Pinecone_CreateIndex(CollectionName)
    VDBIndex = PineConeClient.Index(name = CollectionName)
    
    ## A. 검색 쿼리와 가중치 ##
    # 1) Context-Summary
    ContextSummaryQueryText = CollectionData['CollectionAnalysis']['Context']['Summary']
    # Context-Weight
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Weight'], str):
        ContextQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Weight'].replace('점', '')) / 100
    else:
        ContextQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Weight']) / 100

    # 2) Context-KeyWord
    ContextKeyWordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['KeyWord'])

    # 3) Context-Demand-Needs-Sentence
    ContextDemandNeedsSentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['Sentence']
    # Context-Demand-Needs-Weight
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['Weight'], str):
        ContextDemandNeedsQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['Weight'].replace('점', '')) / 100
    else:
        ContextDemandNeedsQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['Weight']) / 100

    # 4) Context-Demand-Needs-Keyword
    ContextDemandNeedsKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['KeyWord'])

    # 5) Context-Demand-Purpose-Sentence
    ContextDemandPurposeSentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['Sentence']
    # Context-Demand-Purpose-Weight
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['Weight'], str):
        ContextDemandPurposeQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['Weight'].replace('점', '')) / 100
    else:
        ContextDemandPurposeQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['Weight']) / 100

    # 6) Context-Demand-Purpose-Keyword
    ContextDemandPurposeKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['KeyWord'])

    # 7) Context-Demand-Question-Sentence
    ContextDemandQuestionSentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['Sentence']
    # Context-Demand-Question-Weight
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['Weight'], str):
        ContextDemandQuestionQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['Weight'].replace('점', '')) / 100
    else:
        ContextDemandQuestionQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['Weight']) / 100

    # 8) Context-Demand-Question-Keyword
    ContextDemandQuestionKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['KeyWord'])

    # 9) Context-Supply-Satisfy-Sentence
    ContextSupplySatisfySentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['Sentence']
    # Context-Supply-Satisfy-Weight
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['Weight'], str):
        ContextSupplySatisfyQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['Weight'].replace('점', '')) / 100
    else:
        ContextSupplySatisfyQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['Weight']) / 100

    # 10) Context-Supply-Satisfy-Keyword
    ContextSupplySatisfyKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['KeyWord'])

    # 11) Context-Supply-Support-Sentence
    ContextSupplySupportSentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['Sentence']
    # Context-Supply-Support-Weight
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['Weight'], str):
        ContextSupplySupportQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['Weight'].replace('점', '')) / 100
    else:
        ContextSupplySupportQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['Weight']) / 100

    # 12) Context-Supply-Support-Keyword
    ContextSupplySupportKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['KeyWord'])

    # 13) Context-Supply-Solution-Sentence
    ContextSupplySolutionSentenceQueryText = CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['Sentence']
    # Context-Supply-Solution-Weight
    if isinstance(CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['Weight'], str):
        ContextSupplySolutionQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['Weight'].replace('점', '')) / 100
    else:
        ContextSupplySolutionQueryWeight = int(CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['Weight']) / 100

    # 14) Context-Supply-Solution-Keyword
    ContextSupplySolutionKeywordQueryText = ", ".join(CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['KeyWord'])

    ## B. 검색 옵션 설정 ##
    # Similarity = 유사도검색 : 유사한 정보/대상 검색
    if Matching == 'similarity':
        QueryList = [{"Field": "Context-Summary", "Text": ContextSummaryQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-KeyWord", "Text": ContextKeyWordQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-Demand-Needs-Sentence", "Text": ContextDemandNeedsSentenceQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Needs-Keyword", "Text": ContextDemandNeedsKeywordQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Purpose-Sentence", "Text": ContextDemandPurposeSentenceQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Purpose-Keyword", "Text": ContextDemandPurposeKeywordQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Question-Sentence", "Text": ContextDemandQuestionSentenceQueryText, "Weight": ContextDemandQuestionQueryWeight}, {"Field": "Context-Demand-Question-Keyword", "Text": ContextDemandQuestionKeywordQueryText, "Weight": ContextDemandQuestionQueryWeight}, {"Field": "Context-Supply-Satisfy-Sentence", "Text": ContextSupplySatisfySentenceQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Satisfy-Keyword", "Text": ContextSupplySatisfyKeywordQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Support-Sentence", "Text": ContextSupplySupportSentenceQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Support-Keyword", "Text": ContextSupplySupportKeywordQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Solution-Sentence", "Text": ContextSupplySolutionSentenceQueryText, "Weight": ContextSupplySolutionQueryWeight}, {"Field": "Context-Supply-Solution-Keyword", "Text": ContextSupplySolutionKeywordQueryText, "Weight": ContextSupplySolutionQueryWeight}]
    # Demand = 수요검색 : 나에게 필요한 정보/대상 검색
    elif Matching == 'demand':
        QueryList = [{"Field": "Context-Summary", "Text": ContextSummaryQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-KeyWord", "Text": ContextKeyWordQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-Demand-Needs-Sentence", "Text": ContextDemandNeedsSentenceQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Needs-Keyword", "Text": ContextDemandNeedsKeywordQueryText, "Weight": ContextDemandNeedsQueryWeight}, {"Field": "Context-Demand-Purpose-Sentence", "Text": ContextDemandPurposeSentenceQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Purpose-Keyword", "Text": ContextDemandPurposeKeywordQueryText, "Weight": ContextDemandPurposeQueryWeight}, {"Field": "Context-Demand-Question-Sentence", "Text": ContextDemandQuestionSentenceQueryText, "Weight": ContextDemandQuestionQueryWeight}, {"Field": "Context-Demand-Question-Keyword", "Text": ContextDemandQuestionKeywordQueryText, "Weight": ContextDemandQuestionQueryWeight}]
    # Supply = 공급검색 : 나를 필요로 하는 정보/대상 검색
    elif Matching == 'supply':
        QueryList = [{"Field": "Context-Summary", "Text": ContextSummaryQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-KeyWord", "Text": ContextKeyWordQueryText, "Weight": ContextQueryWeight}, {"Field": "Context-Supply-Satisfy-Sentence", "Text": ContextSupplySatisfySentenceQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Satisfy-Keyword", "Text": ContextSupplySatisfyKeywordQueryText, "Weight": ContextSupplySatisfyQueryWeight}, {"Field": "Context-Supply-Support-Sentence", "Text": ContextSupplySupportSentenceQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Support-Keyword", "Text": ContextSupplySupportKeywordQueryText, "Weight": ContextSupplySupportQueryWeight}, {"Field": "Context-Supply-Solution-Sentence", "Text": ContextSupplySolutionSentenceQueryText, "Weight": ContextSupplySolutionQueryWeight}, {"Field": "Context-Supply-Solution-Keyword", "Text": ContextSupplySolutionKeywordQueryText, "Weight": ContextSupplySolutionQueryWeight}]

    # 검색 결과를 저장하기 위한 dict (DocId를 기준으로 저장)
    QueryResultList = []
    MinScores = {}
    ## C. 각 필드에 대한 검색 쿼리 생성 ##
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

        ## D. Pinecone에 쿼리 수행 ##
        QueryResult = VDBIndex.query(
            vector = QueryVector,
            top_k = TopK,
            include_metadata = True,
            namespace = CollectionName,
            filter = {"Field": QueryField}
        )
        # 최소값 저장
        if QueryResult.matches:
            # MinScore 계산 (0이 아닌 값만 고려)
            MinScore = min(match.score for match in QueryResult.matches if match.score != 0)
            MinScores[QueryField] = MinScore

        QueryResultList.append(QueryResult)
        
    ## E. Pinecone에 Result Score 계산 ##
    # Count = 0
    MaxScores = {}
    for QueryResult in QueryResultList:
        # 가장 높은 유사도 점수와 CollectionId를 사용
        for Result in QueryResult["matches"]:
            Collection = Result["metadata"]["Collection"]
            CollectionId = Result["metadata"]["CollectionId"]
            ResultField = Result["metadata"]["Field"]
            try:
                ResultWeight = Result["metadata"]["Weight"]
            except:
                ResultWeight = Result["metadata"]["Wight"]
            ResultScore = Result["score"] * QueryWeight * ResultWeight
            # Count += 1
            # print(f"({Count}) {QueryField} ::: {ResultScore}")

            # CollectionId 기준으로 점수를 누적
            if CollectionId not in MaxScores:
                MaxScores[CollectionId] = MinScores.copy()

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
            # print(f'MaxScores[CollectionId] ::: {MaxScores[CollectionId]}\n')
                
    # 최종 스코어 계산
    FinalResultScores = []
    for CollectionId, Scores in MaxScores.items():
        ContextSummaryScore = Scores["Context-Summary"]
        ContextKeyWordScore = Scores["Context-KeyWord"]
        ContextDemandNeedsScore = (Scores["Context-Demand-Needs-Sentence"] + Scores["Context-Demand-Needs-Keyword"]) / 2
        ContextDemandPurposeScore = (Scores["Context-Demand-Purpose-Sentence"] + Scores["Context-Demand-Purpose-Keyword"]) / 2
        ContextDemandQuestionScore = (Scores["Context-Demand-Question-Sentence"] + Scores["Context-Demand-Question-Keyword"]) / 2
        ContextSupplySatisfyScore = (Scores["Context-Supply-Satisfy-Sentence"] + Scores["Context-Supply-Satisfy-Keyword"]) / 2
        ContextSupplySupportScore = (Scores["Context-Supply-Support-Sentence"] + Scores["Context-Supply-Support-Keyword"]) / 2
        ContextSupplySolutionScore = (Scores["Context-Supply-Solution-Sentence"] + Scores["Context-Supply-Solution-Keyword"]) / 2
        
        # 최종 스코어 계산
        FinalResultScore = ContextSummaryScore * ContextKeyWordScore * ContextDemandNeedsScore * ContextDemandPurposeScore * ContextDemandQuestionScore * ContextSupplySatisfyScore * ContextSupplySupportScore * ContextSupplySolutionScore
        
        FinalResultScores.append({"Collection": Collection, "CollectionId": CollectionId, "Score": FinalResultScore})

    # score 내림차순(유사도 높은 순) 정렬 후 상위 10개 추출
    FinalResultScores = sorted(FinalResultScores, key = lambda x: x["Score"], reverse = True)[:10]
    
    return FinalResultScores

if __name__ == "__main__":
    CollectionName = "publisher"
    TotalCollectionDataTempPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_TargetData/s1512_PublisherData/s15121_TotalPublisherData/TotalPublisherDataTemp"
    UpsertCollectionData(TotalCollectionDataTempPath, CollectionName)

    
    # CollectionData = {
    # "CollectionAnalysis": {
    #     "Context": {
    #         "Summary": "'하이큐!! 매거진 2024 MAY'는 팬들을 위해 후루다테 하루이치의 새로 그린 일러스트 및 다양한 콘텐츠를 수록하여 극장판 '하이큐!! 쓰레기장의 결전'을 더욱 풍부하게 즐길 수 있게 만든 매거진입니다. 하이큐 팬들에게 특별한 정보를 제공하며 캐릭터들의 생생한 매력을 담아냅니다.",
    #         "KeyWord": [
    #             "만화",
    #             "스포츠",
    #             "극장판 관련",
    #             "일러스트",
    #             "팬 서비스"
    #         ],
    #         "Demand": {
    #             "Needs": {
    #                 "Sentence": "예약 및 배송 과정의 투명성과 효율성을 개선하여 소비자의 신뢰를 높일 필요가 있습니다.",
    #                 "KeyWord": [
    #                     "예약 시스템",
    #                     "배송",
    #                     "소비자 신뢰",
    #                     "효율성",
    #                     "투명성"
    #                 ],
    #                 "Weight": 85
    #             },
    #             "Purpose": {
    #                 "Sentence": "차기 매거진 발매 시에는 특전 및 배송 프로세스를 사전 계획 및 관리하여 팬들의 만족도를 높이는 것이 목표입니다.",
    #                 "KeyWord": [
    #                     "특전 관리",
    #                     "배송 계획",
    #                     "팬 만족",
    #                     "사전 준비",
    #                     "프로세스 개선"
    #                 ],
    #                 "Weight": 90
    #             },
    #             "Question": {
    #                 "Sentence": "특전 및 배송 관리 과정에서 팬들에게 보다 나은 경험을 제공하기 위해 어떤 방안을 도입할 수 있을까요?",
    #                 "KeyWord": [
    #                     "특전 방안",
    #                     "배송 개선",
    #                     "팬 경험",
    #                     "관리 효율",
    #                     "문제 해결"
    #                 ],
    #                 "Weight": 80
    #             }
    #         },
    #         "Supply": {
    #             "Satisfy": {
    #                 "Sentence": "하이큐 팬들에게 새로운 일러스트와 정보로 캐릭터와 스토리에 대한 애정을 한층 강화해 줍니다.",
    #                 "KeyWord": [
    #                     "팬 만족",
    #                     "새로운 정보",
    #                     "풍부한 콘텐츠",
    #                     "캐릭터 매력",
    #                     "스토리 확장"
    #                 ],
    #                 "Weight": 90
    #             },
    #             "Support": {
    #                 "Sentence": "팬들이 하이큐 세계관을 더 깊이 이해하고 극장판 경험을 확장할 수 있는 기회를 제공합니다.",
    #                 "KeyWord": [
    #                     "세계관",
    #                     "이해 확장",
    #                     "극장판",
    #                     "몰입감",
    #                     "팬 경험"
    #                 ],
    #                 "Weight": 85
    #             },
    #             "Solution": {
    #                 "Sentence": "하이큐 팬들의 궁금증과 애정 어린 호기심을 충족할 수 있는 다양한 콘텐츠와 일러스트를 제공합니다.",
    #                 "KeyWord": [
    #                     "궁금증 해결",
    #                     "호기심 충족",
    #                     "다양한 콘텐츠",
    #                     "일러스트",
    #                     "팬 서비스"
    #                 ],
    #                 "Weight": 80
    #             }
    #         },
    #         "Weight": 75
    #     }
    # }}

    # FinalResultScores = SearchEmbeddedData(CollectionData, CollectionName = 'publisher')
    # print(f'FinalScores ::: {FinalResultScores}\n')