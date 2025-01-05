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
    Wight = CollectionData['CollectionAnalysis']['Context']['Wight'] / 100
    ContextSummaryText = CollectionData['CollectionAnalysis']['Context']['Summary']
    ContextSummaryVector = OpenAI_TextEmbedding(ContextSummaryText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSummaryVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
            }
        })
    
    # 2) Context-KeyWord
    Field = "Context-KeyWord"
    Wight = CollectionData['CollectionAnalysis']['Context']['Wight'] / 100
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
            "Wight": Wight
            }
        })
    
    # 3) Context-Demand-Needs-Sentence
    Field = "Context-Demand-Needs-Sentence"
    Wight = CollectionData['CollectionAnalysis']['Context']['Demand']['필요']['중요도'] / 100
    ContextDemandNeedsText = CollectionData['CollectionAnalysis']['Context']['Demand']['필요']['설명']
    ContextDemandNeedsVector = OpenAI_TextEmbedding(ContextDemandNeedsText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandNeedsVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
            }
        })
    
    # 4) Context-Demand-Needs-Keyword
    Field = "Context-Demand-Needs-Keyword"
    Wight = CollectionData['CollectionAnalysis']['Context']['Demand']['필요']['중요도'] / 100
    ContextDemandNeedsKeyword = CollectionData['CollectionAnalysis']['Context']['Demand']['필요']['키워드']
    ContextDemandNeedsKeywordText = ", ".join(ContextDemandNeedsKeyword)
    ContextDemandNeedsKeywordVector = OpenAI_TextEmbedding(ContextDemandNeedsKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandNeedsKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
            }
        })

    # 5) Context-Demand-Purpose-Sentence
    Field = "Context-Demand-Purpose-Sentence"
    Wight = CollectionData['CollectionAnalysis']['Context']['Demand']['목표']['중요도'] / 100
    ContextDemandPurposeText = CollectionData['CollectionAnalysis']['Context']['Demand']['목표']['설명']
    ContextDemandPurposeVector = OpenAI_TextEmbedding(ContextDemandPurposeText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandPurposeVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
            }
        })

    # 6) Context-Demand-Purpose-Keyword
    Field = "Context-Demand-Purpose-Keyword"
    Wight = CollectionData['CollectionAnalysis']['Context']['Demand']['목표']['중요도'] / 100
    ContextDemandPurposeKeyword = CollectionData['CollectionAnalysis']['Context']['Demand']['목표']['키워드']
    ContextDemandPurposeKeywordText = ", ".join(ContextDemandPurposeKeyword)
    ContextDemandPurposeKeywordVector = OpenAI_TextEmbedding(ContextDemandPurposeKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandPurposeKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
            }
        })

    # 7) Context-Demand-Question-Sentence
    Field = "Context-Demand-Question-Sentence"
    Wight = CollectionData['CollectionAnalysis']['Context']['Demand']['질문']['중요도'] / 100
    ContextDemandQuestionText = CollectionData['CollectionAnalysis']['Context']['Demand']['질문']['설명']
    ContextDemandQuestionVector = OpenAI_TextEmbedding(ContextDemandQuestionText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandQuestionVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight * SubWight
            }
        })

    # 8) Context-Demand-Question-Keyword
    Field = "Context-Demand-Question-Keyword"
    Wight = CollectionData['CollectionAnalysis']['Context']['Demand']['질문']['중요도'] / 100
    ContextDemandQuestionKeyword = CollectionData['CollectionAnalysis']['Context']['Demand']['질문']['키워드']
    ContextDemandQuestionKeywordText = ", ".join(ContextDemandQuestionKeyword)
    ContextDemandQuestionKeywordVector = OpenAI_TextEmbedding(ContextDemandQuestionKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextDemandQuestionKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
            }
        })

    # 9) Context-Supply-Satisfy-Sentence
    Field = "Context-Supply-Satisfy-Sentence"
    Wight = CollectionData['CollectionAnalysis']['Context']['Supply']['충족']['중요도'] / 100
    ContextSupplySatisfyText = CollectionData['CollectionAnalysis']['Context']['Supply']['충족']['설명']
    ContextSupplySatisfyVector = OpenAI_TextEmbedding(ContextSupplySatisfyText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySatisfyVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
            }
        })

    # 10) Context-Supply-Satisfy-Keyword
    Field = "Context-Supply-Satisfy-Keyword"
    Wight = CollectionData['CollectionAnalysis']['Context']['Supply']['충족']['중요도'] / 100
    ContextSupplySatisfyKeyword = CollectionData['CollectionAnalysis']['Context']['Supply']['충족']['키워드']
    ContextSupplySatisfyKeywordText = ", ".join(ContextSupplySatisfyKeyword)
    ContextSupplySatisfyKeywordVector = OpenAI_TextEmbedding(ContextSupplySatisfyKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySatisfyKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
            }
        })

    # 11) Context-Supply-Support-Sentence
    Field = "Context-Supply-Support-Sentence"
    Wight = CollectionData['CollectionAnalysis']['Context']['Supply']['달성']['중요도'] / 100
    ContextSupplySupportText = CollectionData['CollectionAnalysis']['Context']['Supply']['달성']['설명']
    ContextSupplySupportVector = OpenAI_TextEmbedding(ContextSupplySupportText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySupportVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
            }
        })

    # 12) Context-Supply-Support-Keyword
    Field = "Context-Supply-Support-Keyword"
    Wight = CollectionData['CollectionAnalysis']['Context']['Supply']['달성']['중요도'] / 100
    ContextSupplySupportKeyword = CollectionData['CollectionAnalysis']['Context']['Supply']['달성']['키워드']
    ContextSupplySupportKeywordText = ", ".join(ContextSupplySupportKeyword)
    ContextSupplySupportKeywordVector = OpenAI_TextEmbedding(ContextSupplySupportKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySupportKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
            }
        })

    # 13) Context-Supply-Solution-Sentence
    Field = "Context-Supply-Solution-Sentence"
    Wight = CollectionData['CollectionAnalysis']['Context']['Supply']['해결책']['중요도'] / 100
    ContextSupplySolutionText = CollectionData['CollectionAnalysis']['Context']['Supply']['해결책']['설명']
    ContextSupplySolutionVector = OpenAI_TextEmbedding(ContextSupplySolutionText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySolutionVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
            }
        })

    # 14) Context-Supply-Solution-Keyword
    Field = "Context-Supply-Solution-Keyword"
    Wight = CollectionData['CollectionAnalysis']['Context']['Supply']['해결책']['중요도'] / 100
    ContextSupplySolutionKeyword = CollectionData['CollectionAnalysis']['Context']['Supply']['해결책']['키워드']
    ContextSupplySolutionKeywordText = ", ".join(ContextSupplySolutionKeyword)
    ContextSupplySolutionKeywordVector = OpenAI_TextEmbedding(ContextSupplySolutionKeywordText)
    UpsertEmbeddedData.append({
        "id" :f"{DocId}-{Field}",
        "values": ContextSupplySolutionKeywordVector,
        "metadata": {
            "Collection": f"{CollectionName}",
            "CollectionId": f"{Id}",
            "Field": Field,
            "Wight": Wight
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
def SearchEmbeddedData(CollectionData, CollectionName, Matching = 'Similarity', TopK = 50): # Matching: 'Similarity', 'Demand, 'Supply'
    print(f"[ YaaS VDB Search: {CollectionName} | VBD에 {CollectionName}TempFile.json 리스트 업서트 완료 ]")
    
    PineConeClient = Pinecone_CreateIndex(CollectionName)
    VDBIndex = PineConeClient.Index(name = CollectionName)
    # 검색할 필드
    SearchFieldList = ["ContextKeyChunk", "ContextPurpose", "ContextReason", "ContextQuestion", "ContextSubject", "ContextPerson"]

    # 검색 결과를 저장하기 위한 dict (DocId를 기준으로 저장)
    ScoresByDoc = {}

    # 각 필드에 대해 검색
    # ScoreWeight를 동적으로 변경
    for SearchField in SearchFieldList:
        if SearchField == "ContextKeyChunk":
            ContextQueryText = CollectionData['CollectionAnalysis']['Context']['Summary']
            ScoreWeight = 1
        elif SearchField == "ContextPurpose":
            ContextQueryText = CollectionData['CollectionAnalysis']['Context']['목표']
            ScoreWeight = 0.334
        elif SearchField == "ContextReason":
            ContextQueryText = CollectionData['CollectionAnalysis']['Context']['Reason']
            ScoreWeight = 0.333
        elif SearchField == "ContextQuestion":
            ContextQueryText = CollectionData['CollectionAnalysis']['Context']['질문']
            ScoreWeight = 0.333
        elif SearchField == "ContextSubject":
            subject_list = CollectionData['CollectionAnalysis']['Context']['Subject']
            ContextQueryText = ", ".join(subject_list)
            ScoreWeight = 0.5
        elif SearchField == "ContextPerson":
            person_list = CollectionData['CollectionAnalysis']['Context']['Person']
            ContextQueryText = ", ".join(person_list)
            ScoreWeight = 0.5

        # 해당 필드의 쿼리 벡터 생성
        ContextQueryVector = OpenAI_TextEmbedding(ContextQueryText)

        # Pinecone에 쿼리 수행 (상위 TopK만 검색, 특정 필드 필터링)
        ContextQueryResult = VDBIndex.query(
            vector = ContextQueryVector,
            top_k = TopK,
            include_metadata = True,
            namespace = CollectionName,
            filter = {"Field": SearchField}
        )
        # print(f'ContextQueryResult["matches"] ::: {ContextQueryResult["matches"]}\n')
        # 가장 높은 유사도 점수와 DocId를 사용
        for match in ContextQueryResult["matches"]:
            Collection = match["metadata"]["Collection"]
            CollectionId = match["metadata"]["CollectionId"]
            ContextQueryScore = match["score"] * ScoreWeight

            # DocId 기준으로 점수를 누적
            if CollectionId not in ScoresByDoc:
                ScoresByDoc[CollectionId] = {"ContextKeyChunk": 0, "PRQScore": 0, "KeyWordScore": 0}

            if SearchField == "ContextKeyChunk":
                ScoresByDoc[CollectionId]["ContextKeyChunk"] = max(ScoresByDoc[CollectionId]["ContextKeyChunk"],ContextQueryScore)
            elif SearchField in ["ContextPurpose", "ContextReason", "ContextQuestion"]:
                ScoresByDoc[CollectionId]["PRQScore"] += ContextQueryScore
            elif SearchField in ["ContextSubject", "ContextPerson"]:
                ScoresByDoc[CollectionId]["KeyWordScore"] += ContextQueryScore

    # 최종 스코어 계산
    FinalScores = []
    # print(f'ScoresByDoc ::: {ScoresByDoc}\n')
    for CollectionId, scores in ScoresByDoc.items():
        # 공식: ContextKeyChunk * PRQScore * KeyWordScore
        ContextKeyChunkScore = scores["ContextKeyChunk"]
        PRQScore = scores["PRQScore"]
        KeyWordScore = scores["KeyWordScore"]

        # 최종 스코어 계산
        FinalScore = ContextKeyChunkScore * PRQScore * KeyWordScore

        FinalScores.append({"Collection": Collection, "CollectionId": CollectionId, "Score": FinalScore})

    # score 내림차순(유사도 높은 순) 정렬 후 상위 10개 추출
    FinalScores = sorted(FinalScores, key = lambda x: x["Score"], reverse = True)[:10]
    
    return FinalScores

if __name__ == "__main__":
    CollectionName = "publisher"
    TotalCollectionDataTempPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_TargetData/s1512_PublisherData/s15121_TotalPublisherData/TotalPublisherDataTemp"
    UpsertCollectionData(TotalCollectionDataTempPath, CollectionName)

    # CollectionData = {
    #     "CollectionAnalysis": {
    #         "Message": "『불안사회』는 불안으로 가득 찬 현대사회에서 우리가 잃어버린 연대와 공감, 그리고 진정한 희망의 본질을 되찾고자 하는 메시지를 전달합니다.",
    #         "Context": {
    #             "Purpose": "현대 사회에서 느끼는 만연한 불안과 무기력에 대한 근본적인 원인을 이해하고, 이를 극복할 수 있는 철학적 통찰과 실질적인 방향을 찾고자 합니다.",
    #             "Reason": "팬데믹, 경제적 위기, 사회적 고립 등으로 인해 불확실한 미래와 존재에 대한 불안을 느끼며, 이러한 상황에서 희망과 연대의 가치를 알고 싶어졌기 때문입니다.",
    #             "Question": "불안 사회를 극복한 후, 제가 더 나은 삶과 더 깊은 철학적 이해를 위해 읽어야 할 철학 또는 사회학 도서를 추천해 주실 수 있을까요?",
    #             "Review": "『불안사회』는 현대 사회를 정교하게 해부하며, 불안이란 무엇인지, 그리고 이를 극복하기 위해 우리가 무엇을 해야 하는지에 대해 깊이 있는 통찰을 제공합니다. 희망이라는 주제에 대한 새로운 관점을 제시하면서도, 읽는 내내 우리 삶에 어떤 변화가 필요한지 스스로 고민하게 만듭니다.",
    #             "Subject": [
    #                 "불안사회",
    #                 "희망",
    #                 "연대",
    #                 "철학적통찰",
    #                 "사회비판"
    #             ],
    #             "Person": [
    #                 "불안",
    #                 "희망",
    #                 "연대",
    #                 "공감",
    #                 "철학"
    #             ],
    #             "Importance": 95
    #         }}}
    
    # CollectionData = {
    #     "CollectionAnalysis": {
    #         "Slogan": "치매와 함께 살아가는 사회, 전문적 정보와 통찰을 제공합니다.",
    #         "Context": {
    #             "Purpose": "치매 관련 정보와 전문적 지식을 공유하여 치매 환자와 가족들의 삶의 질을 향상시키고, 사회적 인식을 제고하기 위함입니다.",
    #             "Reason": "고령화 사회에서 치매가 중요한 사회적, 의료적 이슈로 부각되고 있으며, 이에 대한 이해와 대비가 필요하다는 점에서 도출되었습니다.",
    #             "Question": "효과적인 치매 예방과 관리, 사회적 공감대를 형성하기 위해 어떤 새로운 접근법과 협력 모델을 도입할 수 있을까요?",
    #             "Subject": [
    #                 "치매",
    #                 "사회적 공감",
    #                 "전문 정보 제공",
    #                 "치유와 미래"
    #             ],
    #             "Person": [
    #                 "치매 전문의",
    #                 "사회복지사",
    #                 "간병 전문가",
    #                 "치매 연구자",
    #                 "정신건강 전문가"
    #             ],
    #             "Importance": "95"
    #     }}}

    # FinalScores = SearchEmbeddedData(CollectionData, CollectionName)
    # print(f'FinalScores ::: {FinalScores}\n')