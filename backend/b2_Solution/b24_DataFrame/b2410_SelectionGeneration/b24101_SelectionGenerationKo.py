import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, AddExistedSelectionGenerationKoToDB, AddSelectionGenerationKoBookContextToDB, AddSelectionGenerationKoSplitedIndexsToDB, SelectionGenerationKoCountLoad, SelectionGenerationKoCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB

#############################################
##### b24101_SelectionGenerationKo 생성 #####
#############################################
## BodyFrameBodys 로드
def SelectionGenerationKoJson(projectName, email):
    project = GetProject(projectName, email)
    BodyFrame = project.HalfBodyFrame[1]['SplitedBodyScripts'][1:]
    
    CaptionFrame = project.CaptionFrame[1]['CaptionCompletions'][1:]
    WMWMFrameBookContext = project.WMWMMatching[1]['BookContexts'][1:]
    WMWMFrameIndexs = project.WMWMMatching[1]['SplitedIndexContexts'][1:]
    WMWMFrameBodys = project.WMWMMatching[1]['SplitedBodyContexts'][1:]
    WMWMFrameChunks = project.WMWMMatching[1]['SplitedChunkContexts'][1:]
    CharacterFrame = project.CharacterCompletion[1]['CharacterCompletions'][1:]
    CharacterTags = project.CharacterCompletion[2]['CheckedCharacterTags'][1:]
    if len(project.CharacterCompletion[2]['CheckedCharacterTags']) > 1:
        Narrater = CharacterTags[0]
    else:
        # NarraterGenre 기본값
        NarraterGender = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Gender']['Gender']
        NarraterAge = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Age']['Age']
        # BookEmotion을 CharacterEmotion으로 치환
        bookemotion = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Emotion']['Emotion']
        if bookemotion in ['행복', '즐거움']:
            NarraterEmotion = '즐거움'
        elif bookemotion in ['평온', '침착']:
            NarraterEmotion = '침착함'
        elif bookemotion in ['슬픔', '두려움']:
            NarraterEmotion = '슬픔'
        elif bookemotion in ['놀람', '화남']:
            NarraterEmotion = '화남'
        else:
            NarraterEmotion = '중립'
        Narrater = {"CharacterId": 1, "CharacterTag": "Narrator", "Gender": NarraterGender, "Age": NarraterAge, "Emotion": {NarraterEmotion: 100.0}, "MainCharacterList": {"Id": 1, "MainCharacter": "저자"}}
    SoundFrame = project.SoundMatching[1]['SoundSplitedIndexs'][1:]
    SFXFrame =  project.SFXMatching[1]['SFXSplitedBodys'][1:]
    CorrectionKoFrame = project.CorrectionKo[1]['CorrectionKoSplitedBodys'][1:]
    
    ## SelectionGenerationKoSplitedIndexs 구조 구성
    SelectionGenerationKoSplitedBodys = []
    SelectionGenerationKoSplitedIndexs = []
    lastIndexId = None

    for i in range(len(BodyFrame)):
        BodyFrameIndexId = BodyFrame[i]['IndexId']
        IndexTag = BodyFrame[i]['IndexTag']
        Index = BodyFrame[i]['Index']
        
        # 새로운 IndexId가 시작될 때
        if lastIndexId is not None and lastIndexId != BodyFrameIndexId:
            SelectionGenerationKoSplitedIndexs.append({
                'IndexId': lastIndexId,
                'IndexTag': lastTag,
                'Index': lastIndex,
                'IndexContext': "None",
                'Music': "None",
                'Sound': "None",
                'SelectionGenerationKoSplitedBodys': SelectionGenerationKoSplitedBodys
            })
            SelectionGenerationKoSplitedBodys = []

        lastIndexId = BodyFrameIndexId
        lastTag = IndexTag
        lastIndex = Index

        BodyFrameBodyId = BodyFrame[i]['BodyId']
        SplitedBodys = {
            'BodyId': BodyFrameBodyId,
            'BodyContext': "None",
            'ChunkId': [],
            'SelectionGenerationKoSplitedChunks': []
        }
        SplitedBodyChunks = BodyFrame[i]['SplitedBodyChunks']
        for j in range(len(SplitedBodyChunks)):
            BodyFrameChunkId = SplitedBodyChunks[j]['ChunkId']
            SplitedBodys['ChunkId'].append(BodyFrameChunkId)

        SelectionGenerationKoSplitedBodys.append(SplitedBodys)

    # 마지막 IndexId에 대한 항목 추가
    if SelectionGenerationKoSplitedBodys:
        SelectionGenerationKoSplitedIndexs.append({
            'IndexId': lastIndexId,
            'IndexTag': lastTag,
            'Index': lastIndex,
            'IndexContext': "None",
            'Music': "None",
            'Sound': "None",
            'SelectionGenerationKoSplitedBodys': SelectionGenerationKoSplitedBodys
        })

    ## SelectionGenerationKoSplitedIndexs 데이터 구축
    # Index 중 IndexContext, Music, Sound 부분
    # LatestIndex 초기화
    LatestIndex = None
    for i in range(len(SelectionGenerationKoSplitedIndexs)):
        # IndexContext
        for j in range(len(WMWMFrameIndexs)):
            # print(SelectionGenerationKoSplitedIndexs[i]['IndexId'])
            # print(SelectionGenerationKoSplitedIndexs[i]['IndexContext'])
            if SelectionGenerationKoSplitedIndexs[i]['IndexId'] == WMWMFrameIndexs[j]['IndexId']:
                SelectionGenerationKoSplitedIndexs[i]['IndexContext'] = {'Vector': WMWMFrameIndexs[j]['Vector'], 'WMWM': WMWMFrameIndexs[j]['WMWM']}
                LatestIndex = SelectionGenerationKoSplitedIndexs[i]['IndexContext']
                break

        # Music
        IndexTag = SelectionGenerationKoSplitedIndexs[i]['IndexTag']
        if IndexTag == 'Title':
            bookGenre = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Genre']['Genre']
            bookGender = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Gender']['Gender']
            bookAge = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Age']['Age']
            bookPersonality = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Personality']['Personality']
            bookEmotion = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Emotion']['Emotion']
            SelectionGenerationKoSplitedIndexs[i]['Music'] = {"Genre": bookGenre, "Gender": bookGender, "Age": bookAge, "Personality": bookPersonality, "Emotion": bookEmotion}
        else:
            if LatestIndex:
                SelectionGenerationKoSplitedIndexs[i]['Music'] = LatestIndex['Vector']['ContextCompletion']
            else:
                # MusicGenre 기본값
                MusicGenre = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Genre']['Genre']
                MusicGender = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Gender']['Gender']
                MusicAge = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Age']['Age']
                MusicPersonality = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Personality']['Personality']
                MusicEmotion = WMWMFrameBookContext[0]['Vector']['ContextCompletion']['Emotion']['Emotion']
                SelectionGenerationKoSplitedIndexs[i]['Music'] = {"Genre": MusicGenre, "Gender": MusicGender, "Age": MusicAge, "Personality": MusicPersonality, "Emotion": MusicEmotion, "Accuracy": 100}
            
        # Sound
        for k in range(len(SoundFrame)):
            if SelectionGenerationKoSplitedIndexs[i]['IndexId'] == SoundFrame[k]['IndexId']:
                SelectionGenerationKoSplitedIndexs[i]['Sound'] = SoundFrame[k]['Sounds']
                break

    # Body 중 BodyContext, SelectionGenerationKoSplitedChunks 부분
    BookContext = {'Vector': WMWMFrameBookContext[0]['Vector'], 'WMWM': WMWMFrameBookContext[0]['WMWM']} #####
    for i in range(len(SelectionGenerationKoSplitedIndexs)):
        IndexContext = SelectionGenerationKoSplitedIndexs[i]['IndexContext'] #####
        SelectionGenerationKoSplitedBodys = SelectionGenerationKoSplitedIndexs[i]['SelectionGenerationKoSplitedBodys']
        for j in range(len(SelectionGenerationKoSplitedBodys)):
            for k in range(len(WMWMFrameBodys)):
                if SelectionGenerationKoSplitedBodys[j]['BodyId'] == WMWMFrameBodys[k]['BodyId']:
                    SelectionGenerationKoSplitedBodys[j]['BodyContext'] = {'Vector': WMWMFrameBodys[k]['Vector'], 'WMWM': WMWMFrameBodys[k]['WMWM']}
                    BodyContext = SelectionGenerationKoSplitedBodys[j]['BodyContext'] #####
            ChunkIds = SelectionGenerationKoSplitedBodys[j]['ChunkId']
            for chunkid in ChunkIds:
                
                # ChunkContext
                ChunkContext = "None"
                for WMWMFrameChunk in WMWMFrameChunks:
                    if WMWMFrameChunk['ChunkId'] == chunkid:
                        Vector = WMWMFrameChunk['Vector']
                        WMWM = WMWMFrameChunk['WMWM']
                        ChunkContext = {'Vector': Vector, 'WMWM': WMWM}
                
                # SelectionGenerationKoChunkTokens
                for CorrectionKoFrameBody in CorrectionKoFrame:
                    CorrectionKoFrameChunk = CorrectionKoFrameBody['CorrectionKoSplitedBodyChunks']
                    for CorrectionKoChunk in CorrectionKoFrameChunk:
                        if CorrectionKoChunk['ChunkId'] == chunkid:
                            ChunkTokens = CorrectionKoChunk['CorrectionKoChunkTokens']
                            Chunk = ''.join([list(ChunkToken.values())[0] for ChunkToken in ChunkTokens])
                            Tag = CorrectionKoChunk['Tag']
                            SelectionGenerationKoChunkTokens = CorrectionKoChunk['CorrectionKoChunkTokens']

                # CaptionMusic
                CaptionMusic = "None"
                for CaptionFrameChunk in CaptionFrame:
                    CaptionTag = CaptionFrameChunk['CaptionTag']
                    if CaptionTag == 'Caption':
                        CaptionChunkIds = CaptionFrameChunk['ChunkIds']
                        SplitedCaptionChunks = CaptionFrameChunk['SplitedCaptionChunks']
                        for SplitedCaptionChunk in SplitedCaptionChunks:
                            CaptionMusicStart = "None"
                            CaptionMusicEnd = "None"
                            if SplitedCaptionChunk['ChunkId'] == chunkid:
                                if CaptionChunkIds[0] == SplitedCaptionChunk['ChunkId']:
                                    CaptionMusicStart = "True"
                                if CaptionChunkIds[-1] == SplitedCaptionChunk['ChunkId']:
                                    CaptionMusicEnd = "True"
                                genre = BookContext['Vector']['ContextCompletion']['Genre']
                                gender = BookContext['Vector']['ContextCompletion']['Gender']
                                age = BookContext['Vector']['ContextCompletion']['Age']
                                personality = BookContext['Vector']['ContextCompletion']['Personality']
                                emotion = BookContext['Vector']['ContextCompletion']['Emotion']
                                CaptionMusic = {"CaptionMusicStart": CaptionMusicStart, "CaptionMusicEnd": CaptionMusicEnd, "Genre": genre, "Gender": gender, "Age": age, "Personality": personality, "Emotion": emotion}
                    # New Caption Tag 적용
                    else:
                        CaptionChunkIds = CaptionFrameChunk['ChunkIds']
                        SplitedCaptionChunks = CaptionFrameChunk['SplitedCaptionChunks']
                        for SplitedCaptionChunk in SplitedCaptionChunks:
                            if SplitedCaptionChunk['ChunkId'] == chunkid:
                                Tag = SplitedCaptionChunk['Tag']

                # Voice
                # Chunk가 비어있거나, 내에 문자가 없을 경우의 예외처리
                try:
                    Language = detect(Chunk)
                except LangDetectException:
                    Language = "ko"
                emotions = list(Narrater['Emotion'].keys())
                Voice = {'Character': Narrater['MainCharacterList'][0]['Id'], 'CharacterTag': Narrater['CharacterTag'], 'Language': Language, 'Gender': Narrater['Gender'], 'Age': Narrater['Age'], 'Emotion': emotions[00]}
                for CharacterChunk in CharacterFrame:
                    if CharacterChunk['ChunkId'] == chunkid:
                        print(CharacterChunk)
                        Character = CharacterChunk['MainCharacter']
                        CharacterTag = CharacterChunk['Voice']['CharacterTag']
                        Gender = CharacterChunk['Voice']['Gender']
                        Age = CharacterChunk['Voice']['Age']
                        Emotion = CharacterChunk['Context']['Emotion']
                        Voice = {'Character': Character, 'CharacterTag': CharacterTag, 'Language': Language, 'Gender': Gender, 'Age': Age, 'Emotion': Emotion}
                
                # SFX
                SFX = "None"
                for SFXFrameBody in SFXFrame:
                    SFXFrameChunk = SFXFrameBody['SFXSplitedBodyChunks']
                    for SFXChunk in SFXFrameChunk:
                        if not isinstance(SFXChunk['ChunkId'], list):
                            SFXChunk['ChunkId'] = [SFXChunk['ChunkId']]
                        if SFXChunk['ChunkId'][0] == chunkid:
                            sFX = SFXChunk['SFX']['SFX']
                            Prompt = SFXChunk['SFX']['Prompt']
                            Type = SFXChunk['SFX']['Type']
                            Role = SFXChunk['SFX']['Role']
                            Direction = SFXChunk['SFX']['Direction']
                            Importance = SFXChunk['SFX']['Importance']
                            SFX = {'SFX': sFX, 'Prompt': Prompt, 'Type': Type, 'Role': Role, 'Direction': Direction, 'Importance': Importance}
                
                ## 모두 합쳐서 SelectionGenerationKoSplitedChunks에 합치기
                SelectionGenerationKoSplitedBodys[j]['SelectionGenerationKoSplitedChunks'].append({'ChunkId': chunkid, 'Chunk': Chunk, 'Tag': Tag, 'ChunkContext': ChunkContext, 'CaptionMusic': CaptionMusic, 'Voice': Voice, 'SFX': SFX, 'SelectionGenerationKoChunkTokens': SelectionGenerationKoChunkTokens})
                
    SelectionGenerationKoBookContext = WMWMFrameBookContext[0]
    SelectionGenerationKoSplitedIndexs = SelectionGenerationKoSplitedIndexs
    
    # file_path = "/yaas/SelectionGenerationKoFrame.json"
    # with open(file_path, 'w', encoding='utf-8') as file:
    #     json.dump(SelectionGenerationKoFrame, file, ensure_ascii = False, indent = 4)
        
    return SelectionGenerationKoBookContext, SelectionGenerationKoSplitedIndexs

## 프롬프트 요청 및 결과물 Json을 SelectionGenerationKo에 업데이트
def SelectionGenerationKoUpdate(projectName, email, ExistedDataFrame = None):
    print(f"< User: {email} | Project: {projectName} | 26_SelectionGenerationKoUpdate 시작 >")
    # SelectionGenerationKo의 Count값 가져오기
    ContinueCount, Completion = SelectionGenerationKoCountLoad(projectName, email)
    if Completion == "No":
        
        if ExistedDataFrame != None:
            # 이전 작업이 존재할 경우 가져온 뒤 업데이트
            AddExistedSelectionGenerationKoToDB(projectName, email, ExistedDataFrame)
            print(f"[ User: {email} | Project: {projectName} | 26_SelectionGenerationKoUpdate는 ExistedSelectionGenerationKo으로 대처됨 ]\n")
        else:
            SelectionGenerationKoBookContext, SelectionGenerationKoSplitedIndexs = SelectionGenerationKoJson(projectName, email)

            ## A. SelectionGenerationKoBookContext
            AddSelectionGenerationKoBookContextToDB(projectName, email, SelectionGenerationKoBookContext)

            ## B. SelectionGenerationKoSplitedIndexs
            # ResponseJson을 ContinueCount로 슬라이스
            ResponseJson = SelectionGenerationKoSplitedIndexs[ContinueCount:]
            ResponseJsonCount = len(ResponseJson)

            # TQDM 셋팅
            UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'SelectionGenerationKoUpdate')
            
            # i값 수동 생성
            i = 0
            for Update in UpdateTQDM:
                UpdateTQDM.set_description(f"SelectionGenerationKoUpdate: {Update['IndexId']}")
                time.sleep(0.0001)
                IndexId = Update['IndexId']
                IndexTag = Update['IndexTag']
                Index = Update['Index']
                IndexContext = Update['IndexContext']
                Music = Update['Music']
                Sound = Update['Sound']
                SelectionGenerationKoSplitedBodys = Update['SelectionGenerationKoSplitedBodys']
                AddSelectionGenerationKoSplitedIndexsToDB(projectName, email, IndexId, IndexTag, Index, IndexContext, Music, Sound, SelectionGenerationKoSplitedBodys)

                # i값 수동 업데이트
                i += 1
            
            UpdateTQDM.close()
            # Completion "Yes" 업데이트
            SelectionGenerationKoCompletionUpdate(projectName, email)
            print(f"[ User: {email} | Project: {projectName} | 26_SelectionGenerationKoUpdate 완료 ]\n")
        
    else:
        print(f"[ User: {email} | Project: {projectName} | 26_SelectionGenerationKoUpdate는 이미 완료됨 ]\n")
    
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s11_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################