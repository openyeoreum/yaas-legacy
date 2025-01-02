import os
import json
import math
import pinecone
import openai
import sys
sys.path.append("/yaas")

## Pinecone에 인덱스 생성
def Pinecone_CreateIndex(CollectionName, IndexDimension = 1536):
    pinecone.init(api_key = os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENV"))
    
    if CollectionName not in pinecone.list_indexes():
        pinecone.create_index(name = CollectionName, dimension = IndexDimension, metric = "cosine")
    else:
        print(f"[ Pinecone_CreateIndex : '{CollectionName}' 이미 존재함 ]")

## OpenAI API를 이용하여 텍스트를 임베딩하여 벡터로 반환
def OpenAI_TextEmbedding(Text, EmbedModel = "text-embedding-ada-002"):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # 비어있는 문자열을 방지하기 위한 처리
    if not Text:
        Text = " "
    response = openai.Embedding.create(
        input = Text,
        model = EmbedModel
    )
    Embedding = response["data"][0]["embedding"]
    
    return Embedding

## Pinecone에 임베딩 데이터 업서트
def UpsertEmbeddedData(TotalCollectionDataList, CollectionName):
    ## Pinecone에 인덱스 생성
    Pinecone_CreateIndex(CollectionName, IndexDimension = 1536)
    VDBIndex = pinecone.Index(CollectionName)

    # 업서트할 벡터(레코드)들을 담을 리스트
    UpsertEmbeddedData = []

    for CollectionData in TotalCollectionDataList:
        Id = CollectionData['Id']
        DocId = f"{CollectionName}-{Id}"
        
        # 1) ContextKeyChunk
        ContextKeyChunkText = next(iter(CollectionData['PublisherAnalysis'].values()))
        ContextKeyChunkVector = OpenAI_TextEmbedding(ContextKeyChunkText)
        UpsertEmbeddedData.append((
            f"{DocId}:ContextKeyChunk",
            ContextKeyChunkVector,
            {
                "DocId": DocId,
                "Field": "ContextKeyChunk"
            }
        ))
        
        # 2) ContextPurpose
        ContextPurposeText = CollectionData['PublisherAnalysis']['Context']['Purpose']
        ContextPurposeVector = OpenAI_TextEmbedding(ContextPurposeText)
        UpsertEmbeddedData.append((
            f"{DocId}:ContextPurpose",
            ContextPurposeVector,
            {
                "DocId": DocId,
                "Field": "ContextPurpose"
            }
        ))

        # 3) ContextReason
        ContextReasonText = CollectionData['PublisherAnalysis']['Context']['Reason']
        ContextReasonVector = OpenAI_TextEmbedding(ContextReasonText)
        UpsertEmbeddedData.append((
            f"{DocId}:ContextReason",
            ContextReasonVector,
            {
                "DocId": DocId,
                "Field": "ContextReason"
            }
        ))

        # 4) ContextQuestion
        ContextQuestionText = CollectionData['PublisherAnalysis']['Context']['Question']
        ContextQuestionVector = OpenAI_TextEmbedding(ContextQuestionText)
        UpsertEmbeddedData.append((
            f"{DocId}:ContextQuestion",
            ContextQuestionVector,
            {
                "DocId": DocId,
                "Field": "ContextQuestion"
            }
        ))

        # 5) ContextSubject (리스트이므로 쉼표로 join)
        ContextSubjectList = CollectionData['PublisherAnalysis']['Context']['Subject']
        ContextSubjectText = ", ".join(ContextSubjectList)
        ContextSubjectVector = OpenAI_TextEmbedding(ContextSubjectText)
        UpsertEmbeddedData.append((
            f"{DocId}:ContextSubject",
            ContextSubjectVector,
            {
                "DocId": DocId,
                "Field": "ContextSubject"
            }
        ))

        # 6) ContextPerson (리스트이므로 쉼표로 join)
        ContextPersonList = CollectionData['PublisherAnalysis']['Context']['Person']
        ContextPersonText = ", ".join(ContextPersonList)
        ContextPersonVector = OpenAI_TextEmbedding(ContextPersonText)
        UpsertEmbeddedData.append((
            f"{DocId}:ContextPerson",
            ContextPersonVector,
            {
                "DocId": DocId,
                "Field": "ContextPerson"
            }
        ))

    # Pinecone에 업서트
    VDBIndex.upsert(vectors = UpsertEmbeddedData)

## Pinecone에 임베딩 데이터 검색
def SearchEmbeddedData(CollectionData, CollectionName, TopK = 50):
    # 검색할 필드
    SearchFieldList = ["ContextKeyChunk", "Purpose", "Reason", "Question", "Subject", "Person"]
    VDBIndex = pinecone.Index(CollectionName)

    # 검색 결과를 저장하기 위한 dict (DocId를 기준으로 저장)
    ScoresByDoc = {}

    # 각 필드에 대해 검색
    for SearchField in SearchFieldList:
        if SearchField == "ContextKeyChunk":
            ContextQueryText = next(iter(CollectionData['PublisherAnalysis'].values()))
            ScoreWeight = 1
        elif SearchField == "Purpose":
            ContextQueryText = CollectionData['PublisherAnalysis']['Context']['Purpose']
            ScoreWeight = 0.333
        elif SearchField == "Reason":
            ContextQueryText = CollectionData['PublisherAnalysis']['Context']['Reason']
            ScoreWeight = 0.333
        elif SearchField == "Question":
            ContextQueryText = CollectionData['PublisherAnalysis']['Context']['Question']
            ScoreWeight = 0.333
        elif SearchField == "Subject":
            subject_list = CollectionData['PublisherAnalysis']['Context']['Subject']
            ContextQueryText = ", ".join(subject_list)
            ScoreWeight = 0.5
        elif SearchField == "Person":
            person_list = CollectionData['PublisherAnalysis']['Context']['Person']
            ContextQueryText = ", ".join(person_list)
            ScoreWeight = 0.5
        else:
            ContextQueryText = ""
            ScoreWeight = 0  # 기본 가중치 0

        # 해당 필드의 쿼리 벡터 생성
        ContextQueryVector = OpenAI_TextEmbedding(ContextQueryText)

        # Pinecone에 쿼리 수행 (상위 TopK만 검색, 특정 필드 필터링)
        ContextQueryResult = VDBIndex.query(
            vector = ContextQueryVector,
            top_k = TopK,
            include_metadata = True,
            filter = {"Field": SearchField}
        )

        # 가장 높은 유사도 점수와 DocId를 사용
        for match in ContextQueryResult["matches"]:
            DocId = match["metadata"]["DocId"]
            ContextQueryScore = match["score"] * ScoreWeight

            # DocId 기준으로 점수를 누적
            if DocId not in ScoresByDoc:
                ScoresByDoc[DocId] = {"ContextKeyChunk": 0, "PRQScore": 0, "KeyWordScore": 0}

            if SearchField == "ContextKeyChunk":
                ScoresByDoc[DocId]["ContextKeyChunk"] = max(ScoresByDoc[DocId]["ContextKeyChunk"],ContextQueryScore)
            elif SearchField in ["Purpose", "Reason", "Question"]:
                ScoresByDoc[DocId]["PRQScore"] += ContextQueryScore
            elif SearchField in ["Subject", "Person"]:
                ScoresByDoc[DocId]["KeyWordScore"] += ContextQueryScore

    # 최종 스코어 계산
    FinalScores = []
    for DocId, scores in ScoresByDoc.items():
        # 공식: ContextKeyChunk * PRQScore * KeyWordScore
        ContextKeyChunkScore = scores["ContextKeyChunk"]
        PRQScore = scores["PRQScore"]
        KeyWordScore = scores["KeyWordScore"]

        # 최종 스코어 계산
        FinalScore = ContextKeyChunkScore * PRQScore * KeyWordScore

        FinalScores.append({"DocId": DocId, "Score": FinalScore})

    # score 내림차순(유사도 높은 순) 정렬 후 상위 10개 추출
    FinalScores = sorted(FinalScores, key = lambda x: x["Score"], reverse = True)[:10]
    
    return FinalScores

if __name__ == "__main__":
    CollectionName = "Publisher"
    TotalPublisherDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_TargetData/s1512_PublisherData/s15121_TotalPublisherData/TotalPublisherData.json"
    with open(TotalPublisherDataPath, 'r', encoding='utf-8') as f:
        TotalCollectionDataList = json.load(f)
        
    UpsertEmbeddedData(TotalCollectionDataList, CollectionName)