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

## 가중치 일반화 함수 (str -> int / 100)
def GetWeight(Weight):
    return (int(Weight.replace('점', '')) if isinstance(Weight, str) else int(Weight)) / 100

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
    Weight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Weight'])
    
    Field = "Context-Summary"
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
    Weight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Demand']['Needs']['Weight'])
    
    Field = "Context-Demand-Needs-Sentence"
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
    Weight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Demand']['Purpose']['Weight'])
    
    Field = "Context-Demand-Purpose-Sentence"
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
    Weight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Demand']['Question']['Weight'])
    
    Field = "Context-Demand-Question-Sentence"
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
    Weight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Supply']['Satisfy']['Weight'])
    
    Field = "Context-Supply-Satisfy-Sentence"
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
    Weight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Supply']['Support']['Weight'])
    
    Field = "Context-Supply-Support-Sentence"
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
    Weight = GetWeight(CollectionData['CollectionAnalysis']['Context']['Supply']['Solution']['Weight'])
    
    Field = "Context-Supply-Solution-Sentence"
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

if __name__ == "__main__":
    CollectionName = "publisher"
    TotalCollectionDataTempPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s152_TargetData/s1522_PublisherData/s15221_TotalPublisherData/TotalPublisherDataTemp"
    UpsertCollectionData(TotalCollectionDataTempPath, CollectionName)