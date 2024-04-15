import re
import regex as _re
import tiktoken
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, AddExistedHalfBodyFrameToDB, AddHalfBodyFrameBodyToDB, AddHalfBodyFrameChunkToDB, AddHalfBodyFrameBodysToDB, HalfBodyFrameCountLoad, InitHalfBodyFrame, UpdatedHalfBodyFrame, HalfBodyFrameCompletionUpdate

# BodyText 로드
def LoadBodyText(projectName, email):
    project = GetProject(projectName, email)
    _bodyText = project.BodyText
    PronunciationPreprocessFrame = project.PronunciationPreprocessFrame[1]['PreprocessScripts'][1:]
    
    bodyText = ""
    BeforeIndex = None
    for i, Dic in enumerate(PronunciationPreprocessFrame):
        Index = Dic['Index']
        Script = Dic['PronunciationScript']
        if BeforeIndex != Index and i == 0:
            bodyText += f'{Index}\n\n'
            bodyText += Script
        elif BeforeIndex != Index and i != 0:
            bodyText += f'\n\n{Index}\n\n'
            bodyText += Script
        else:
            bodyText += f' {Script}'
        BeforeIndex = Index
    
    # 두 파일의 텍스트 수 확인
    Len_bodyText = len(_bodyText)
    LenbodyText = len(bodyText)
    AbsDiff = abs(Len_bodyText - LenbodyText)
    RelativeDiff = AbsDiff / LenbodyText
    if RelativeDiff >= 0.03:
        sys.exit(f"[ 분할 전후 텍스트 {RelativeDiff}% 만큼 다름 (_bodyText: {Len_bodyText} != bodyText: {LenbodyText}) ]")
    
    return bodyText

## Body최초 전처리
def BodyReplace(chunk):
    # /내용/ 부분에 잘못된 표현을 치환
    ReplaceTermElements = [
        (' 다/.', '다./'), ('다 /.', '다./'), ('다/.', '다./'),
        (' 나/.', '나./'), ('나 /.', '나./'), ('나/.', '나./'),
        (' 까/.', '까./'), ('까 /.', '까./'), ('까/.', '까./'),
        (' 요/.', '요./'), ('요 /.', '요./'), ('요/.', '요./'),
        (' 죠/.', '죠./'), ('죠 /.', '죠./'), ('죠/.', '죠./'),
        (' 듯/.', '듯./'), ('듯 /.', '듯./'), ('듯/.', '듯./'),
        (' 것/.', '것./'), ('것 /.', '것./'), ('것/.', '것./'),
        (' 라/.', '라./'), ('라 /.', '라./'), ('라/.', '라./'),
        (' 가/.', '가./'), ('가 /.', '가./'), ('가/.', '가./'),
        (' 니/.', '니./'), ('니 /.', '니./'), ('니/.', '니./'),
        (' 군/.', '군./'), ('군 /.', '군./'), ('군/.', '군./'),
        (' 오/.', '오./'), ('오 /.', '오./'), ('오/.', '오./'),
        (' 자/.', '자./'), ('자 /.', '자./'), ('자/.', '자./'),
        (' 네/.', '네./'), ('네 /.', '네./'), ('네/.', '네./'),
        (' 소/.', '소./'), ('소 /.', '소./'), ('소/.', '소./'),
        (' 지/.', '지./'), ('지 /.', '지./'), ('지/.', '지./'),
        (' 어/.', '어./'), ('어 /.', '어./'), ('어/.', '어./')
    ]
    original_chunk = chunk[:]
    start_index = 0
    is_odd = True

    while True:
        index_slash = original_chunk.find("/", start_index)
        if index_slash == -1:
            break

        if is_odd:
            for old, new in ReplaceTermElements:
                if old in chunk[index_slash-3:index_slash+4]:
                    chunk = chunk[:index_slash-3] + chunk[index_slash-3:index_slash+4].replace(old, new) + chunk[index_slash+4:]
                    break

        start_index = index_slash + 1
        is_odd = not is_odd

    # 특정 문자열을 다른 문자열로 치환
    ReplaceElements = [
        ('.....', '.'), ('....', '.'),
        ('...', '.'), ('..', '.'), 
        ('"', '∥'), ('“', '∥'), ('”', '∥'),
        ('*', '○'),
        # ('’', '∥'), ('‘', '∥'), ('’', '∥'),
        ('. \n', '&&\n'), ('.\n', '&&\n'),
        (' /.', '/@@'), ('/.', '/@@'),
        (' 다.', '다@@'), ('다.', '다@@'),
        (' 나.', '나@@'), ('나.', '나@@'),
        (' 까.', '까@@'), ('까.', '까@@'),
        (' 요.', '요@@'), ('요.', '요@@'),
        (' 죠.', '죠@@'), ('죠.', '죠@@'),
        (' 듯.', '듯@@'), ('듯.', '듯@@'),
        (' 것.', '것@@'), ('것.', '것@@'),
        (' 라.', '라@@'), ('라.', '라@@'),
        (' 가.', '가@@'), ('가.', '가@@'),
        (' 니.', '니@@'), ('니.', '니@@'),
        (' 군.', '군@@'), ('군.', '군@@'),
        (' 오.', '오@@'), ('오.', '오@@'),
        (' 자.', '자@@'), ('자.', '자@@'),
        (' 네.', '네@@'), ('네.', '네@@'),
        (' 소.', '소@@'), ('소.', '소@@'),
        (' 지.', '지@@'), ('지.', '지@@'),
        (' 어.', '어@@'), ('어.', '어@@')
    ]
    for old, new in ReplaceElements:
        chunk = chunk.replace(old, new)
    
    # 숫자 뒤에 점, 영어 뒤에 점을 ●으로 치환
    chunk = re.sub(r'(\d)\.(\d|\s|$)', r'\1●\2', chunk)
    chunk = re.sub(r'([a-zA-Z])\.(\s|$)', r'\1●\2', chunk)

    # 치환된 문자열을 복구
    RestoreElements = [
        ('.', ''),
        ('@@', '.'), ('.', '. '), ('&&', '.'),
        ('      ', ' '), ('     ', ' '), ('    ', ' '),
        ('   ', ' '), ('  ', ' '),
        ('\n\n\n\n\n', '\n\n'), ('\n\n\n\n', '\n\n'), ('\n\n\n', '\n\n'),
    ]
    for old, new in RestoreElements:
        chunk = chunk.replace(old, new)

    return chunk

## BodySplit
def BodySplitPreprocess(projectName, email):
    # BodyText 로드
    BodyText = LoadBodyText(projectName, email)
    splitedBody = BodyText.splitlines(keepends=True)
    
    # splitedBody 다중표현 방지 전처리
    SplitedBodyReplace = [BodyReplace(chunk) for chunk in splitedBody]
    
    # preprocessSplitedBody 문단 단위 전처리
    BodyChunks = []
    bufferChunk = ""

    for chunk in SplitedBodyReplace:
        # bufferChunk에 새로운 chunk를 추가
        bufferChunk += chunk
        
        if bufferChunk.count('∥') % 2 == 0:  # 짝수인 경우
            BodyChunks.append(bufferChunk)
            bufferChunk = ""

    # BodySplitPreprocess 오류체크
    for chunk in BodyChunks:
        if chunk.count('∥')%2 != 0:
            sys.exit(f"Body의 따옴표 숫자 오류 발생: Project: {projectName} | Process: BodyFrameUpdate | BodySplitPreprocessError\n\n[ {projectName}의 PronunciationPreprocess에서 따옴표 수를 체크하세요! ]\n\n문제 따옴표수: {chunk.count('∥')}")
    print(f"Project: {projectName} | Process: HalfBodyFrameUpdate | BodySplitPreprocess 완료")
      
    return BodyChunks

## Comment 태깅
def CommentTagging(projectName, email):
    # 전처리된 SplitedBodyText 로드
    BodyChunks = BodySplitPreprocess(projectName, email)

    # Comment, CaptionComment 태깅
    CommentTaggedChunks = []
    CommentPattern = re.compile(r'/(.*?)/')
    CaptionCommentPattern = re.compile(r'<(.*?)>')

    for BodyChunk in BodyChunks:
        # Find and split by CaptionCommentPattern
        captionParts = CaptionCommentPattern.split(BodyChunk)
        
        for j, captionPart in enumerate(captionParts):
            if j % 2 == 0:
                # Find and split by CommentPattern within the captionPart
                parts = CommentPattern.split(captionPart)
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        partStrip = str(i) + '@' + part.strip()  # 이상한 오류 방지...
                        CommentTaggedChunks.append({"Tag": "None", "TagChunks": re.sub(r'^\d+@', '', partStrip)})
                    else:
                        partStrip = str(i) + '@' + part.strip()  # 이상한 오류 방지...
                        CommentTaggedChunks.append({"Tag": "Comment", "TagChunks": re.sub(r'^\d+@', '', partStrip)})
            else:
                # Add the CaptionComment part as a separate chunk
                captionPart_strip = str(j) + '@' + captionPart.strip()  # 이상한 오류 방지...
                CommentTaggedChunks.append({"Tag": "CaptionComment", "TagChunks": re.sub(r'^\d+@', '', captionPart_strip)})

    # Comment 태깅 후처리(* 표시)
    for i, chunk in enumerate(CommentTaggedChunks):
        if chunk["Tag"] == "Comment":
            # 앞쪽 None에 * 추가
            if i > 0 and CommentTaggedChunks[i-1]["Tag"] == "None":
                CommentTaggedChunks[i-1]["TagChunks"] = CommentTaggedChunks[i-1]["TagChunks"].rstrip() + "*"
            # 뒤쪽 None에 * 추가
            if i < len(CommentTaggedChunks) - 1 and CommentTaggedChunks[i+1]["Tag"] == "None":
                CommentTaggedChunks[i+1]["TagChunks"] = CommentTaggedChunks[i+1]["TagChunks"].rstrip() + "*"
    
    # Comment, CaptionComment 태깅 후처리(구두점 위치 변경)
    indicesToRemove = []
    
    for i in range(len(CommentTaggedChunks) - 2):
        if (
            CommentTaggedChunks[i]["Tag"] == "None" and 
            CommentTaggedChunks[i+1]["Tag"] in ["Comment", "CaptionComment"] and 
            CommentTaggedChunks[i+2]["Tag"] == "None"
        ):
            prefixes = [
                " .", " ,", " '", " ’", " ∥", " 》", " )", " ]",
                ".", ",", "'", "’", "∥", "》", ")", "]"
            ]
            for prefix in prefixes:
                if CommentTaggedChunks[i+2]["TagChunks"].startswith(prefix):
                    CommentTaggedChunks[i]["TagChunks"] += prefix.strip(' ')
                    CommentTaggedChunks[i+2]["TagChunks"] = CommentTaggedChunks[i+2]["TagChunks"][len(prefix):]
                    if CommentTaggedChunks[i+2]["TagChunks"] == "":
                        indicesToRemove.append(i+2)
    
    for idx in reversed(indicesToRemove):
        del CommentTaggedChunks[idx]
        
    for TaggedChunk in CommentTaggedChunks:
        TaggedChunk["TagChunks"] = TaggedChunk["TagChunks"].lstrip()
    
    # CommentTagging 오류체크
    INPUT = re.sub("[^가-힣]", "", LoadBodyText(projectName, email))
    OUTPUT = re.sub("[^가-힣]", "", str(CommentTaggedChunks))
    if INPUT == OUTPUT:
        print(f"Project: {projectName} | Process: HalfBodyFrameUpdate | CommentTagging 완료")
    else:
        sys.exit(f"BodyText와 CommentTaggedChunks 불일치 오류 발생: Project: {projectName} | Process: HalfBodyFrameUpdate | CommentTaggingMatchingError, INPUT({len(INPUT)}), OUTPUT({len(OUTPUT)})")

    return CommentTaggedChunks

## Caption 태깅
def CaptionTagging(projectName, email):
    # 전처리된 CommentTaggedChunks 로드
    CommentTaggedChunks = CommentTagging(projectName, email)
    CaptionTaggedChunks = CommentTaggedChunks.copy()
    
    for chunk in CaptionTaggedChunks:
        # _, |가 포함될 때
        if (
            chunk["Tag"] == "None" and
            chunk["TagChunks"] != "" and
            re.search(r'[_|]', chunk["TagChunks"])
        ):
            chunk["Tag"] = "Caption"
        #Option 문장에 ?, !, ., *가 포함되나, 끝부분에 ?, !, ., *가 포함 안될 때
        elif (
            chunk["Tag"] == "None" and
            chunk["TagChunks"] != "" and
            len(chunk["TagChunks"]) < 120 and
            not re.search(r'[∥]', chunk["TagChunks"]) and
            not re.search(r'[?!.*]', chunk["TagChunks"][-2:])
        ):
            chunk["Tag"] = "Caption"
        # ?, !, ., ∥, *가 포함 안될 때
        elif (
            chunk["Tag"] == "None" and
            chunk["TagChunks"] != "" and
            not re.search(r'[?!.∥*]', chunk["TagChunks"])
        ):
            chunk["Tag"] = "Caption"
    
    # 만약 Text에 '*'이면, 모든 '*' 삭제
    for chunk in CaptionTaggedChunks:
        chunk["TagChunks"] = chunk["TagChunks"][:-4] + chunk["TagChunks"][-4:].replace('*', '')

    # 빈 Text 삭제
    CaptionTaggedChunks = [chunk for chunk in CaptionTaggedChunks if chunk["TagChunks"].strip() != ""]

    # CaptionTagging 오류체크
    INPUT = re.sub("[^가-힣]", "", LoadBodyText(projectName, email))
    OUTPUT = re.sub("[^가-힣]", "", str(CaptionTaggedChunks))
    if INPUT == OUTPUT:
        print(f"Project: {projectName} | Process: HalfBodyFrameUpdate | CaptionTagging 완료")
    else:
        sys.exit(f"BodyText와 CaptionTaggedChunks 불일치 오류 발생: Project: {projectName} | Process: HalfBodyFrameUpdate | CaptionTaggingMatchingError, INPUT({len(INPUT)}), OUTPUT({len(OUTPUT)})")

    return CaptionTaggedChunks
    
## Character 태깅
def CharacterTagging(projectName, email):
    # 전처리된 CaptionTaggedChunks 로드
    CaptionTaggedChunks = CaptionTagging(projectName, email)
    
    # Character 태그 안에 다른 태그가 포함된 문제 해결
    MergedTaggedChunks = []
    nonMergedTaggedChunks = []
    tempChunkText = None
    
    for chunk in CaptionTaggedChunks:
        if chunk['Tag'] == 'None':
            if tempChunkText is None:
                tempChunkText = chunk["TagChunks"]
            else:
                tempChunkText += chunk["TagChunks"]
            
            if tempChunkText.count('∥') % 2 == 0:
                MergedTaggedChunks.append({"Tag": "None", "TagChunks": tempChunkText})
                tempChunkText = None
        elif tempChunkText is None:
            MergedTaggedChunks.append(chunk)
        else:
            nonMergedTaggedChunks.append(chunk["TagChunks"]) # 삭제되는 부분들 저장

    # Character, Narrator 태깅
    CharacterTaggedChunks = []
    for chunk in MergedTaggedChunks:
        if chunk['Tag'] == "None":
            # ∥ 기호를 기준으로 텍스트 분리
            parts = chunk["TagChunks"].split('∥')
            for i, part in enumerate(parts):
                # 홀수 인덱스는 Character 태그, 짝수 인덱스는 Narrator 태그
                if i % 2 == 0:  # 짝수 인덱스
                    newTag = "Narrator"
                    # 문장별로 나누기
                    sentences = re.split('(?<=[.!?])\s+', part.strip())
                    for sentence in sentences:
                        if sentence:  # 텍스트가 비어있지 않은 경우만 추가
                            CharacterTaggedChunks.append({"Tag": newTag, "TagChunks": sentence})
                else:  # 홀수 인덱스
                    newTag = "Character"
                    part = "∥" + part + "∥"  # 텍스트에 ∥ 추가
                    if part.strip():  # 텍스트가 비어있지 않은 경우만 추가
                        CharacterTaggedChunks.append({"Tag": newTag, "TagChunks": part})
        else:
            # 다른 태그는 그대로 유지
            CharacterTaggedChunks.append(chunk)
            
    # CharacterTagging 오류체크
    INPUT = re.sub("[^가-힣]", "", LoadBodyText(projectName, email))
    OUTPUT = re.sub("[^가-힣]", "", str(CharacterTaggedChunks)) + re.sub("[^가-힣]", "", str(nonMergedTaggedChunks))
    if len(INPUT) == len(OUTPUT):
        print(f"Project: {projectName} | Process: HalfBodyFrameUpdate | CharacterTagging 완료, 삭제된 데이터: {nonMergedTaggedChunks}")
    else:
        sys.exit(f"BodyText와 CharacterTaggedChunks 불일치 오류 발생: Project: {projectName} | Process: HalfBodyFrameUpdate | CharacterTaggingMatchingError, INPUT({len(INPUT)}), OUTPUT({len(OUTPUT)})")

    return CharacterTaggedChunks

## Index 매칭
def IndexMatching(projectName, email):
    CharacterTaggedChunks = CharacterTagging(projectName, email)
    IndexMatchedChunks = CharacterTaggedChunks.copy()
    
    project = GetProject(projectName, email)
    IndexFrame = project.IndexFrame[1]["IndexTags"][1:]

    # nonMatchingIndexList 구성
    nonMatchingIndexList = []
    for index in IndexFrame:
        nonMatchingIndexList.append(index["Index"])
    BigIndexList = ["Chapter", "Part"]
    # Index 매칭
    indexid = 0
    for i, chunk in enumerate(IndexMatchedChunks):
        if chunk["Tag"] == "Caption":
            Cleanchunk = re.sub("[^가-힣]", "", chunk["TagChunks"])
            CleanIndex = re.sub("[^가-힣]", "", IndexFrame[indexid]["Index"])
            if Cleanchunk == CleanIndex:
                # print(f'Cleanchunk: {Cleanchunk}')
                indexTag = IndexFrame[indexid]["IndexTag"]
                tagChunk = chunk["TagChunks"]
                if indexTag in BigIndexList:
                    if re.search(r'(\d|일|이|삼|사|오|육|칠|팔|구|십)\s*부', chunk["TagChunks"]):
                        tagChunk = re.sub(r'(\d|일|이|삼|사|오|육|칠|팔|구|십)\s*부', r'\1부,', tagChunk)
                        tagChunk = re.sub(r'(\d|일|이|삼|사|오|육|칠|팔|구|십)\s*부,.', r'\1부,', tagChunk)
                        tagChunk = re.sub(r'(\d|일|이|삼|사|오|육|칠|팔|구|십)\s*부.,', r'\1부,', tagChunk)
                        indexTag = "Part"
                    if re.search(r'(\d|일|이|삼|사|오|육|칠|팔|구|십)\s*장', chunk["TagChunks"]):
                        tagChunk = re.sub(r'(\d|일|이|삼|사|오|육|칠|팔|구|십)\s*장', r'\1장,', tagChunk)
                        tagChunk = re.sub(r'(\d|일|이|삼|사|오|육|칠|팔|구|십)\s*장,.', r'\1장,', tagChunk)
                        tagChunk = re.sub(r'(\d|일|이|삼|사|오|육|칠|팔|구|십)\s*장.,', r'\1장,', tagChunk)
                        indexTag = "Chapter"

                IndexMatchedChunks[i] = {"IndexTag": indexTag, "TagChunks": tagChunk}
                nonMatchingIndexList.remove(IndexFrame[indexid]["Index"])
                # print(indexid)
                # print(IndexFrame[indexid]["Index"])
                if indexid < len(IndexFrame) - 1:
                    indexid += 1

    # 아주 가끔 빈 인덱스가 생성되는 경우 제거
    if '' in nonMatchingIndexList:
        nonMatchingIndexList.remove('')

    # 치환된 표현들 복구
    RestoreElements = [
        ('|', '"'), ('_', '.'),
        ('∥', '"'), ('○', '*'), ('●', '.')
        ]

    for i, chunk in enumerate(IndexMatchedChunks):
        tagChunks = chunk["TagChunks"]
        for old, new in RestoreElements:
            tagChunks = tagChunks.replace(old, new)
            IndexMatchedChunks[i]["TagChunks"] = tagChunks
    
    # IndexMatching 오류체크
    if nonMatchingIndexList != []:
        sys.exit(f"Index 불일치 오류 발생: Project: {projectName} | Process: BodyFrameUpdate | IndexMatchingError\n\n[ {projectName}의 IndexFrame과 PronunciationPreprocess를 비교 후 수정하세요! ]\n\n{nonMatchingIndexList}")
        
    INPUT = re.sub("[^가-힣]", "", str(CharacterTaggedChunks))
    OUTPUT = re.sub("[^가-힣]", "", str(IndexMatchedChunks))
    if INPUT != OUTPUT:
        sys.exit(f"CharacterTaggedChunks와 IndexMatchedChunks 불일치 오류 발생: Project: {projectName} | Process: HalfBodyFrameUpdate | IndexMatchedChunksError, INPUT({len(INPUT)}), OUTPUT({len(OUTPUT)})")
    else:
        print(f"Project: {projectName} | Process: HalfBodyFrameUpdate | IndexMatching 완료")
        
    return IndexMatchedChunks

## 데이터 리스트 유닛화
def TaggedChunksToUnitedChunks(projectName, email, tokensCount):
    IndexMatchedChunks = IndexMatching(projectName, email)
    
    IndexUnitList = []
    IndexUnit = []
    
    # Index 단위 묶음 리스트 형성
    for Dic in IndexMatchedChunks:
        if "IndexTag" in Dic:
            # temp_list에 데이터가 있는 경우 IndexBodyUnitChunksUnit 리스트에 추가
            if IndexUnit:
                IndexUnitList.append(IndexUnit)
                IndexUnit = []
        IndexUnit.append(Dic)

    # 마지막 Unit 추가
    if IndexUnit:
        IndexUnitList.append(IndexUnit)
        
    # Tagged Sentences를 Chunk단위로 나누기
    encoding = tiktoken.get_encoding("cl100k_base")

    IndexBodyUnitChunksList = []
    for IndexUnitChunksUnit in IndexUnitList:
        IndexBodyUnitChunksUnit = []
        currentList = []
        currentTokensCount = 0
        IndexBodyUnitChunksUnit.append([IndexUnitChunksUnit[0]])

        for Unit in IndexUnitChunksUnit[1:]:
            UnitTokensCount = len(encoding.encode(Unit["TagChunks"]))
            
            # TagChunks 내에 한글 또는 영어가 있는지 확인
            if _re.search(r'[\p{L}]', Unit["TagChunks"]):
                currentList.append(Unit)
                currentTokensCount += UnitTokensCount
            
            # 만약 현재 항목을 추가했을 때 토큰 수가 tokensCount를 초과한다면
            # 현재까지의 항목들을 결과 리스트에 추가하고 마지막 항목은 다음 리스트의 시작으로 합니다.
            if currentTokensCount > tokensCount: #####
                lastUnit = currentList.pop()  # 마지막 항목을 제거
                if currentList:
                    IndexBodyUnitChunksUnit.append(currentList)
                currentList = [lastUnit]
                currentTokensCount = len(encoding.encode(lastUnit["TagChunks"]))

        # 남은 항목들을 결과 리스트에 추가합니다.
        if currentList:
            IndexBodyUnitChunksUnit.append(currentList)
        
        IndexBodyUnitChunksList.append(IndexBodyUnitChunksUnit)
    
    # TaggedChunksToUnitedChunks 오류체크
    INPUT = re.sub("[^가-힣]", "", str(IndexMatchedChunks))
    OUTPUT = re.sub("[^가-힣]", "", str(IndexBodyUnitChunksList))
    if INPUT != OUTPUT:
        sys.exit(f"IndexMatchedChunks와 IndexMatchedChunks 불일치 오류 발생: Project: {projectName} | Process: HalfBodyFrameUpdate | TaggedChunksToUnitedChunksError, INPUT({len(INPUT)}), OUTPUT({len(OUTPUT)})")
    else:
        print(f"Project: {projectName} | Process: HalfBodyFrameUpdate | TaggedChunksToUnitedChunks 완료")

    return IndexBodyUnitChunksList

####################################
### SplitedBodyScripts의 Bodys전환 ###
####################################

def SplitedBodyScriptsToBodys(projectName, email):
    project = GetProject(projectName, email)
    HalfBodyFrame = project.HalfBodyFrame
    SplitedBodyScripts = HalfBodyFrame[1]["SplitedBodyScripts"][1:]

    IndexTags = [{"Title"}, {"Logue"}, {"Chapter"}, {"Part"}, {"Index"}]
    CaptionTags = [{"Caption"}, {'CaptionComment', 'Caption'}]
    BodyTags = ["Narrator", "Character", "Caption", "Comment"]
    Tags = []
    ChunkIds = []
    Bodys = []
    bodys = [] # 에러 테스트용도
    BodyChunks = []
    CharacterChunks = []
    TalkCount = 0

    for idx, SplitedBody in enumerate(SplitedBodyScripts):
        SplitedBodyChunks = SplitedBody["SplitedBodyChunks"]
        for i, SplitedBodyChunk in enumerate(SplitedBodyChunks):
            Tags.append(SplitedBodyChunk['Tag'])
            ChunkIds.append(SplitedBodyChunk['ChunkId'])
            if SplitedBodyChunk['Tag'] == "Title":
                BodyChunks.append(SplitedBodyChunk['Chunk'])
                CharacterChunks.append(SplitedBodyChunk['Chunk'])
            elif SplitedBodyChunk['Tag'] in ["Logue", "Chapter", "Part", "Index"]:
                BodyChunks.append('\n\n' + SplitedBodyChunk['Chunk'] + '\n')
                CharacterChunks.append('\n\n' + SplitedBodyChunk['Chunk'] + '\n')
            elif SplitedBodyChunk['Tag'] == "Character":
                TalkCount += 1
                BodyChunks.append(SplitedBodyChunk['Chunk'] + ' ')
                CharacterChunks.append('\n\n[말' + str(TalkCount) + ']' + SplitedBodyChunk['Chunk'] + '\n\n')
            elif SplitedBodyChunk['Tag'] in ["Caption", "CaptionComment"]:
                try:
                    if SplitedBodyChunks[i+1]['Tag'] not in ["Caption", "CaptionComment"]:
                        BodyChunks.append('\n' + SplitedBodyChunk['Chunk'] + '\n')
                        CharacterChunks.append('\n' + SplitedBodyChunk['Chunk'] + '\n')
                    else:
                        BodyChunks.append('\n' + SplitedBodyChunk['Chunk'])
                        CharacterChunks.append('\n' + SplitedBodyChunk['Chunk'])
                except IndexError:
                    if idx + 1 < len(SplitedBodyScripts) and SplitedBodyScripts[idx + 1]["SplitedBodyChunks"][0]['Tag'] in ["Caption", "CaptionComment"]:
                        BodyChunks.append('\n' + SplitedBodyChunk['Chunk'])
                        CharacterChunks.append('\n' + SplitedBodyChunk['Chunk'])
                    else:
                        BodyChunks.append('\n' + SplitedBodyChunk['Chunk'] + '\n')
                        CharacterChunks.append('\n' + SplitedBodyChunk['Chunk'] + '\n')
            else:
                BodyChunks.append(SplitedBodyChunk['Chunk'] + ' ')
                CharacterChunks.append(SplitedBodyChunk['Chunk'] + ' ')

        task = []
        if set(Tags) in IndexTags:
            task.append("Index")
        elif set(Tags) in CaptionTags:
            task.append("Caption")
        elif all(tag in BodyTags for tag in Tags):
            task.append("Body")
            if "Character" in Tags:
                task.append("Character")
        
        # Body, Correction 추출
        BODY = "".join(BodyChunks)
        CORRECTION = "●".join(BodyChunks) + "●"
        
        Bodys.append({'BodyId': idx + 1, 'ChunkId': ChunkIds, 'Task': task, 'Body': BODY, 'Correction': CORRECTION,
                      'Character': "".join(CharacterChunks).replace('\n\n\n\n', '\n\n').replace('\n\n\n', '\n\n')})
        bodys.append({'BodyId': idx + 1, 'ChunkId': ChunkIds, 'Task': task, 'Body': "".join(BodyChunks)}) # 에러 테스트용도
        Tags = []
        ChunkIds = []
        BodyChunks = []
        CharacterChunks = []

    # BodyText와 텍스트 매칭 체크
    HalfBodyFrameList = []
    HalfBodyFrame = UpdatedHalfBodyFrame(projectName, email)[1]["SplitedBodyScripts"]
    for i in range(len(HalfBodyFrame)):
        for j in range(len(HalfBodyFrame[i]["SplitedBodyChunks"])):
            HalfBodyFrameList.append(HalfBodyFrame[i]["SplitedBodyChunks"][j]["Chunk"])
    CleanBodys = re.sub(r'\[말\d{1,5}\]', '', str(bodys))
    
    # HalfBodyFrameBodysUpdate 오류체크
    INPUT = re.sub("[^가-힣]", "", str(HalfBodyFrameList))
    OUTPUT = re.sub("[^가-힣]", "", CleanBodys)
    if INPUT != OUTPUT:
        sys.exit(f"SplitedBodyScripts와 Bodys 불일치 오류 발생: Project: {projectName} | Process: HalfBodyFrameBodysUpdate | HalfBodyFrameBodysUpdateError, INPUT({len(INPUT)}), OUTPUT({len(OUTPUT)})")
    else:
        print(f"[ Project: {projectName} | HalfBodyFrameBodysUpdate 완료 ]\n")     
    
    return Bodys

## Bodys를 HalfBodyFrame에 업데이트
def HalfBodyFrameBodysUpdate(projectName, email):
    Bodys = SplitedBodyScriptsToBodys(projectName, email)
    BodysCount = len(Bodys)
    
    # TQDM 셋팅
    UpdateTQDM = tqdm(Bodys,
                    total = BodysCount,
                    desc = 'HalfBodyFrameBodysUpdate')
    # i값 수동 생성
    i = 0
    for Update in UpdateTQDM:
        UpdateTQDM.set_description(f'HalfBodyFrameBodysUpdate: {Update} ...')
        time.sleep(0.0001)
        ChunkIds = Bodys[i]['ChunkId']
        Task = Bodys[i]['Task']
        Body = Bodys[i]['Body']
        Correction = Bodys[i]['Correction']
        Character = Bodys[i]['Character']
        
        AddHalfBodyFrameBodysToDB(projectName, email, ChunkIds, Task, Body, Correction, Character)
        # i값 수동 업데이트
        i += 1

    UpdateTQDM.close()

###################################################
### IndexBodyUnitChunksList을 HalfBodyFrame에 업데이트 ###
###################################################

def HalfBodyFrameUpdate(projectName, email, tokensCount = 3000, ExistedDataFrame = None):
    print(f"< User: {email} | Project: {projectName} | 04_HalfBodyFrameUpdate 시작 >")
    # HalfBodyFrame의 Count값 가져오기
    IndexCount, BodyCount, ChunkCount, Completion = HalfBodyFrameCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedHalfBodyFrameToDB(projectName, email, ExistedDataFrame)
            print(f"[ User: {email} | Project: {projectName} | 04_HalfBodyFrameUpdate는 ExistedHalfBodyFrame으로 대처됨 ]\n")
        else:
            indexBodyUnitChunksList = TaggedChunksToUnitedChunks(projectName, email, tokensCount)
            
            # IndexBodyUnitChunksList를 IndexCount로 슬라이스
            IndexBodyUnitChunksList = indexBodyUnitChunksList[IndexCount:]
            IndexBodyUnitChunksListCount = len(IndexBodyUnitChunksList)

            IndexId = IndexCount
            ChunkId = ChunkCount

            # TQDM 셋팅
            UpdateTQDM = tqdm(IndexBodyUnitChunksList,
                            total = IndexBodyUnitChunksListCount,
                            desc = 'HalfBodyFrameUpdate')
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f'HalfBodyFrameUpdate: {Update[0]} ...')
                time.sleep(0.0001)
                
                IndexId += 1
                IndexTag = IndexBodyUnitChunksList[i][0][0]['IndexTag']
                IndexChunk = IndexBodyUnitChunksList[i][0][0]['TagChunks']

                for j in range(len(IndexBodyUnitChunksList[i])):
                    AddHalfBodyFrameBodyToDB(projectName, email, IndexId, IndexTag, IndexChunk)
                    
                    for k in range(len(IndexBodyUnitChunksList[i][j])):
                        ChunkId += 1
                        
                        if "IndexTag" in IndexBodyUnitChunksList[i][j][k].keys():
                            Tag = IndexBodyUnitChunksList[i][j][k]["IndexTag"]
                        else:
                            Tag = IndexBodyUnitChunksList[i][j][k]["Tag"]
                        Chunk = IndexBodyUnitChunksList[i][j][k]["TagChunks"]
                        
                        AddHalfBodyFrameChunkToDB(projectName, email, ChunkId, Tag, Chunk)
                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            ##### Bodys 업데이트
            HalfBodyFrameBodysUpdate(projectName, email)
            #####
            # Completion "Yes" 업데이트
            HalfBodyFrameCompletionUpdate(projectName, email)
            
            # BodyText와 텍스트 매칭 체크
            HalfBodyFrameList = []
            HalfBodyFrame = UpdatedHalfBodyFrame(projectName, email)[1]["SplitedBodyScripts"]
            for i in range(len(HalfBodyFrame)):
                for j in range(len(HalfBodyFrame[i]["SplitedBodyChunks"])):
                    HalfBodyFrameList.append(HalfBodyFrame[i]["SplitedBodyChunks"][j]["Chunk"])
            
            # HalfBodyFrameUpdate 오류체크
            INPUT = re.sub("[^가-힣]", "", str(IndexBodyUnitChunksList))
            OUTPUT = re.sub("[^가-힣]", "", str(HalfBodyFrameList))
            if INPUT != OUTPUT:
                sys.exit(f"IndexBodyUnitChunksList와 HalfBodyFrameList 불일치 오류 발생: Project: {projectName} | Process: HalfBodyFrameUpdate | HalfBodyFrameUpdateError, INPUT({len(INPUT)}), OUTPUT({len(OUTPUT)})")
            else:
                print(f"[ User: {email} | Project: {projectName} | 04_HalfBodyFrameUpdate 완료 ]\n")
    else:
        print(f"[ User: {email} | Project: {projectName} | 04_HalfBodyFrameUpdate는 이미 완료됨 ]\n")
    
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################