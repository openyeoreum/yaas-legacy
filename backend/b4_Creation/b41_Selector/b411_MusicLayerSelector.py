import os
import unicodedata
import sys
import re
import random
import copy
import json
sys.path.append("/yaas")

from tqdm import tqdm
from pydub import AudioSegment
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import User
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetSoundDataSet


#######################
##### DataSet 로드 #####
#######################
## LoadMusicDataSet 로드
def LoadMusicDataSet(projectName, email, MainLang = 'Ko'):
    project = GetProject(projectName, email)
    
    ## MainLang의 언어별 SelectionGenerationKoChunks 불러오기
    if MainLang == 'Ko':
        SelectionGeneration = project.SelectionGenerationKo[1]
    if MainLang == 'En':
        SelectionGeneration = project.SelectionGenerationEn[1]
    # if MainLang == 'Ja':
        # SelectionGeneration = project.SelectionGenerationJa[1]
    # if MainLang == 'Zh':
        # SelectionGeneration = project.SelectionGenerationZh[1]
    # if MainLang == 'Es':
        # SelectionGeneration = project.SelectionGenerationEs[1]
    
    ## MainLang의 언어별 VoiceLayer 불러오기
    EditGeneration = project.MixingMasteringKo[1]['AudioBookLayers' + MainLang]

    ## LogoDataSet 불러오기
    soundDataSet = GetSoundDataSet("LogoDataSet")
    LogoDataSet = soundDataSet[0][1]['Logos'][1:]
    
    ## IntroDataSet 불러오기
    soundDataSet = GetSoundDataSet("IntroDataSet")
    IntroDataSet = soundDataSet[0][1]['Intros'][1:]
    
    ## TitleMusicDataSet 불러오기
    soundDataSet = GetSoundDataSet("TitleMusicDataSet")
    TitleMusicDataSet = soundDataSet[0][1]['TitleMusics'][1:]
    
    return SelectionGeneration, EditGeneration, LogoDataSet, IntroDataSet, TitleMusicDataSet

############################
##### MusicMatched 생성 #####
############################
## VoiceLayerPath 경로 생성
def VoiceLayerPathGen(projectName, email, FileName, Folder = 'Mixed'):
    # 데이터베이스에서 사용자 이름 찾기
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()
        if user is None:
            raise ValueError("User not found with the provided email")
        
        username = user.UserName

    # 첫번째, 두번째 폴더 패턴: 시간 스탬프와 사용자 이름을 포함
    UserFolderName = username + '_user'
    StorageFolderName = username + '_storage'
    BasePath = '/yaas/storage/s1_Yeoreum/s12_UserStorage'

    # 최종 경로 생성
    if Folder == "Mixed":
        LayerPath = os.path.join(BasePath, UserFolderName, StorageFolderName, projectName, f"{projectName}_mixed_audiobook_file", "VoiceLayers", FileName)
    if Folder == "Master":
        LayerPath = os.path.join(BasePath, UserFolderName, StorageFolderName, projectName, f"{projectName}_master_audiobook_file", FileName)
    # print(voiceLayerPath)

    return LayerPath

## MusicLayerPath 경로 생성
def MusicLayerPathGen(projectName, email, FileName):
    # 데이터베이스에서 사용자 이름 찾기
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()
        if user is None:
            raise ValueError("User not found with the provided email")
        
        username = user.UserName

    # 첫번째, 두번째 폴더 패턴: 시간 스탬프와 사용자 이름을 포함
    UserFolderName = username + '_user'
    StorageFolderName = username + '_storage'
    BasePath = '/yaas/storage/s1_Yeoreum/s12_UserStorage'

    # 최종 경로 생성
    LayerPath = os.path.join(BasePath, UserFolderName, StorageFolderName, projectName, f"{projectName}_mixed_audiobook_file", "MusicLayers", "Music1", FileName)
    # print(voiceLayerPath)

    return LayerPath

## VoiceLayer에 Logo 선택 후 경로 생성
def MusicMatchedSelectionGenerationChunks(projectName, email, MainLang = 'Ko', Intro = 'off'):

    ## MatchedMusics 파일 경로 생성
    fileName = '[' + projectName + '_' + 'MatchedMusics.json'
    MatchedMusicLayerPath = MusicLayerPathGen(projectName, email, fileName)
    
    ## MusicDataSet 불러오기
    SelectionGeneration, EditGeneration, LogoDataSet, IntroDataSet, TitleMusicDataSet = LoadMusicDataSet(projectName, email, MainLang = MainLang)
    
    if not os.path.exists(MatchedMusicLayerPath):
        
        ## 도서 SelectionGenerationKoBookContext 로드
        Genre = SelectionGeneration['SelectionGenerationKoBookContext'][1]['Vector']['ContextCompletion']['Genre']['Genre']
        GenreRatio = SelectionGeneration['SelectionGenerationKoBookContext'][1]['Vector']['ContextCompletion']['Genre']['GenreRatio']
        GenderRatio = SelectionGeneration['SelectionGenerationKoBookContext'][1]['Vector']['ContextCompletion']['Gender']['GenderRatio']
        AgeRatio = SelectionGeneration['SelectionGenerationKoBookContext'][1]['Vector']['ContextCompletion']['Age']['AgeRatio']
        PersonalityRatio = SelectionGeneration['SelectionGenerationKoBookContext'][1]['Vector']['ContextCompletion']['Personality']['PersonalityRatio']
        EmotionRatio = SelectionGeneration['SelectionGenerationKoBookContext'][1]['Vector']['ContextCompletion']['Emotion']['EmotionRatio']
        
        ## MatchedMusics 생성
        MatchedMusics = []
        
        ## LogoDataSet에서 LogoPath 찾기
        for Logo in LogoDataSet:
            if (Logo['Logo']['Genre'] == Genre) and (Logo['Logo']['Language'] == MainLang):
                MatchedLogoDic = {'Tag': 'Logo', 'FilePath': Logo['FilePath'], 'Setting': Logo['Setting']}
                break
        MatchedMusics.append(MatchedLogoDic)
        
        ## IntroDataSet에서 IntroPath 찾기
        MatchedIntroDic = {'Tag': None, 'FilePath': None, 'Setting': None}
        if Intro != "off":
            for Intro in IntroDataSet:
                if (Intro['Intro']['Type'] == Intro) and (Intro['Intro']['Language'] == MainLang):
                    MatchedIntroDic = {'Tag': 'Intro', 'FilePath': Intro['FilePath'], 'Setting': Intro['Setting']}
                    break
        MatchedMusics.append(MatchedIntroDic)
        
        ## TitleMusicDataSet에서 TitleMusicPath 찾기
        TitleMusicScoreList = []
        for TitleMusic in TitleMusicDataSet:
            # GenreScore 계산
            GenreScores = TitleMusic['TitleMusic']['Genre']
            MergedGenreScore = 0
            for GenreScore in GenreScores:
                if GenreScore['index'] in GenreRatio:
                    MergedGenreScore += (GenreScore['Score'] * GenreRatio[GenreScore['index']])
            # GenderScore 계산
            GenderScores = TitleMusic['TitleMusic']['Gender']
            MergedGenderScore = 0
            for GenderScore in GenderScores:
                if GenderScore['index'] in GenderRatio:
                    MergedGenderScore += (GenderScore['Score'] * GenderRatio[GenderScore['index']])
            # AgeScore 계산
            AgeScores = TitleMusic['TitleMusic']['Age']
            MergedAgeScore = 0
            for AgeScore in AgeScores:
                if AgeScore['index'] in AgeRatio:
                    MergedAgeScore += (AgeScore['Score'] * AgeRatio[AgeScore['index']])
            # PersonalityScore 계산
            PersonalityScores = TitleMusic['TitleMusic']['Personality']
            MergedPersonalityScore = 0
            for PersonalityScore in PersonalityScores:
                if PersonalityScore['index'] in PersonalityRatio:
                    MergedPersonalityScore += (PersonalityScore['Score'] * PersonalityRatio[PersonalityScore['index']])
            # EmotionScore 계산
            EmotionScores = TitleMusic['TitleMusic']['Emotion']
            MergedEmotionScore = 0
            for EmotionScore in EmotionScores:
                if EmotionScore['index'] in EmotionRatio:
                    MergedEmotionScore += (EmotionScore['Score'] * EmotionRatio[EmotionScore['index']])
            # TitleMusic Score 합산
            TitleMusicScoreList.append((MergedGenreScore/1000) * (MergedGenderScore/1000) * (MergedAgeScore/1000) * (MergedPersonalityScore/1000) * (MergedEmotionScore/1000))
            
        # TitleMusic FilePath 도출
        MatchedTitleMusic = TitleMusicDataSet[TitleMusicScoreList.index(max(TitleMusicScoreList))]
        
        # TitleMusic 선택
        RandomTitleMusicDic = random.choice(MatchedTitleMusic['MusicSet']['TitleMusic'])
        MatchedTitleMusicDic = {'Tag': 'Title', 'FilePath': RandomTitleMusicDic['FilePath'], 'Setting': RandomTitleMusicDic['Setting']}
        MatchedMusics.append(MatchedTitleMusicDic)
        
        # MainPartChapterMusic 선택
        RandomMainPartChapterMusicDic = random.sample(MatchedTitleMusic['MusicSet']['PartMusic'], 2)
        MatchedMainPartChapterMusicDic = {'Tag': 'MainChapterPart', 'FilePath': RandomMainPartChapterMusicDic[0]['FilePath'], 'Setting': RandomMainPartChapterMusicDic[0]['Setting']}
        MatchedMusics.append(MatchedMainPartChapterMusicDic)
        
        # SubPartChapterMusic, IndexMusic, CaptionMusic 선택
        RandomIndexMusicDic = random.sample(MatchedTitleMusic['MusicSet']['IndexMusic'], 3)
        # 초가 가장 높은 값을 1순위로 정렬
        SortedIndexMusicDic = sorted(RandomIndexMusicDic, key = lambda x: x["Setting"]["Length"][-1] * 0.3 + x["Setting"]["Length"][0], reverse=True)
        
        MatchedSubPartChapterMusicDic = {'Tag': 'SubChapterPart', 'FilePath': SortedIndexMusicDic[0]['FilePath'], 'Setting': SortedIndexMusicDic[0]['Setting']}
        MatchedMusics.append(MatchedSubPartChapterMusicDic)
        
        MatchedIndexMusicDic = {'Tag': 'Index', 'FilePath': SortedIndexMusicDic[1]['FilePath'], 'Setting': SortedIndexMusicDic[1]['Setting']}
        MatchedMusics.append(MatchedIndexMusicDic)
        
        MatchedCaptionMusicDic = {'Tag': 'Caption', 'FilePath': SortedIndexMusicDic[2]['FilePath'], 'Setting': SortedIndexMusicDic[2]['Setting']}
        MatchedMusics.append(MatchedCaptionMusicDic)
        
        ## MatchedMusics 파일 생성
        with open(MatchedMusicLayerPath, 'w', encoding='utf-8') as MatchedMusicsJson:
            json.dump(MatchedMusics, MatchedMusicsJson, ensure_ascii=False, indent=4)
    else:
        with open(MatchedMusicLayerPath, 'r', encoding = 'utf-8') as MatchedMusicsJson:
            MatchedMusics = json.load(MatchedMusicsJson)
        
    return EditGeneration, MatchedMusics

################################################
##### VoiceLayer에 Logo, Intro, Music 합치기 #####
################################################
## VoiceLayer에 Musics 믹싱 파일 선정
def MusicsMixingPath(projectName, email, MainLang = 'Ko', Intro = 'off'):
    
    EditGeneration, MatchedMusics = MusicMatchedSelectionGenerationChunks(projectName, email, MainLang = 'Ko', Intro = 'off')
    
    ## EditGeneration 내에 Part, Chapter 유무 확인
    PartSwitch = False
    ChapterSwitch = False
    for Edit in EditGeneration:
        if Edit['Tag'] == 'Part':
            PartSwitch = True
        elif Edit['Tag'] == 'Chapter':
            ChapterSwitch = True
            
    PartChapterSwitch = False
    if PartSwitch and ChapterSwitch:
        PartChapterSwitch = True
    
    ## EditGeneration에서 Tag 추출하기
    # TagMusic 선정
    Intro = None
    for matchedMusic in MatchedMusics:
        if matchedMusic['Tag'] != None:
            if 'Logo' in matchedMusic['Tag']:
                Logo = matchedMusic
            if 'Intro' in matchedMusic['Tag']:
                Intro = matchedMusic
            if 'Title' in matchedMusic['Tag']:
                TitleMusic = matchedMusic
            if PartChapterSwitch:
                if 'MainChapterPart' in matchedMusic['Tag']:
                    PartMusic = matchedMusic
                if 'SubChapterPart' in matchedMusic['Tag']:
                    ChapterMusic = matchedMusic
            else:
                if 'MainChapterPart' in matchedMusic['Tag']:
                    if PartSwitch:
                        PartMusic = matchedMusic
                    if ChapterSwitch:
                        ChapterMusic = matchedMusic
            if 'Index' in matchedMusic['Tag']:
                IndexMusic = matchedMusic
            if 'Caption' in matchedMusic['Tag']:
                CaptionMusic = matchedMusic

    # TagMusic 위치 매칭
    MusicMixingDatas = []
    EndMusicMixingDatas = []
    MusicMixingDataDic = None
    EndMusicMixingDataDic = None
    StartTime = 0
    for i in range(len(EditGeneration)):
        if i > 0:
            BeforeTag = EditGeneration[i-1]['Tag']
            StartTime = EditGeneration[i-1]['ActorChunk'][-1]['EndTime']['Second']
        
        EditId = EditGeneration[i]['EditId']
        ActorName = EditGeneration[i]['ActorName']
        Tag = EditGeneration[i]['Tag']
        Pause = EditGeneration[i]['ActorChunk'][-1]['Pause']
        EndTime = EditGeneration[i]['ActorChunk'][-1]['EndTime']['Second']
        VoiceFileName = []
        for k in range(len(EditGeneration[i]['ActorChunk'])):
            VoiceFileName.append(f'{projectName}_{EditId}_{ActorName}_({k})M.wav')
            VoiceFileName.append(f'{projectName}_{EditId}_{ActorName}_({k}).wav')
        
        if Tag == 'Title':
            TitleMusicMixingDataDics = [{'EditId': EditId, 'ActorChunkId': 0, 'Tag': Tag, 'Pause': Pause, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': TitleMusic}]
            EditGeneration[i]['Logo'] = Logo['FilePath'].split('/')[-1]
            if Intro != None:
                EditGeneration[i]['Intro'] = Intro['FilePath'].split('/')[-1]
            EditGeneration[i]['Music'] = TitleMusic['FilePath'].split('/')[-1]
            if EditGeneration[i+1]['Tag'] == 'Narrator' and EditGeneration[i+2]['Tag'] in ['Logue', 'Part', 'Chapter', 'Index']:
                TitleActorChunks = EditGeneration[i+1]['ActorChunk']
                EditId = EditGeneration[i+1]['EditId']
                StartTime = EndTime
                for j in range(min(len(TitleActorChunks), 2)):
                    Pause = TitleActorChunks[j]['Pause']
                    EndTime = TitleActorChunks[j]['EndTime']['Second']
                    VoiceFileName = [f'{projectName}_{EditId}_{ActorName}_({j})M.wav', f'{projectName}_{EditId}_{ActorName}_({j}).wav']
                    TitleMusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': j, 'Tag': Tag, 'Pause': Pause, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': TitleMusic}
                    TitleMusicMixingDataDics.append(TitleMusicMixingDataDic)
                    StartTime = EndTime
                MusicMixingDatas += TitleMusicMixingDataDics
                TitleMusicMixingDataDics = []
                continue

        elif Tag == 'Part':
            MusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': 0, 'Tag': Tag, 'Pause': Pause, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': PartMusic}
            EditGeneration[i]['Music'] = PartMusic['FilePath'].split('/')[-1]
        elif Tag == 'Chapter':
            MusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': 0, 'Tag': Tag, 'Pause': Pause, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': ChapterMusic}
            EditGeneration[i]['Music'] = ChapterMusic['FilePath'].split('/')[-1]
        elif Tag == 'Index':
            MusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': 0, 'Tag': Tag, 'Pause': Pause, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': IndexMusic}
            EditGeneration[i]['Music'] = IndexMusic['FilePath'].split('/')[-1]
        elif (BeforeTag not in ['Caption', 'CaptionComment']) and (Tag == 'Caption'):
            MusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': 0, 'Tag': Tag, 'Pause': Pause, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': CaptionMusic}
            EditGeneration[i]['Music'] = CaptionMusic['FilePath'].split('/')[-1]

        elif i >= (len(EditGeneration)-2):
            ActorChunk = EditGeneration[i]['ActorChunk']
            EditGeneration[i]['Music'] = TitleMusic['FilePath'].split('/')[-1]
            for z in range(len(ActorChunk)):
                EndTime = ActorChunk[z]['EndTime']['Second']
                Pause = ActorChunk[z]['Pause']
                Chunk = ActorChunk[z]['Chunk']
                EndMusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': z, 'Tag': 'TitleEnd', 'Pause': Pause, 'Chunk': Chunk, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': [VoiceFileName[z*2], VoiceFileName[z*2+1]], 'Music': TitleMusic}
                StartTime = EndTime
                EndMusicMixingDatas.append(EndMusicMixingDataDic)
                EndMusicMixingDataDic = None
        
        if MusicMixingDataDic != None:
            MusicMixingDatas.append(MusicMixingDataDic)
        MusicMixingDataDic = None
    
    # TitleEnd를 30초만 남기기
    EndTime = 0
    SelectedEndMusicMixingDatas = []
    for MixingData in reversed(EndMusicMixingDatas):
        duration = MixingData['EndTime'] - MixingData['StartTime']
        if EndTime + duration <= 40:
            EndTime += duration
            SelectedEndMusicMixingDatas.append(MixingData)
        else:
            break
    MusicMixingDatas += list(reversed(SelectedEndMusicMixingDatas))
        
    # for data in MusicMixingDatas:
    #     print(f'{data}\n\n')
    ## matchedMusic 경로
    LogoPath = Logo['FilePath']
    IntroPath = None
    if Intro != None:
        IntroPath = Intro['FilePath']
    TitleMusicPath = TitleMusic['FilePath']
    PartMusicPath = PartMusic['FilePath']
    ChapterMusicPath = ChapterMusic['FilePath']
    IndexMusicPath = IndexMusic['FilePath']
    CaptionMusicPath = CaptionMusic['FilePath']
    
    return EditGeneration, MusicMixingDatas, LogoPath, IntroPath, TitleMusicPath, PartMusicPath, ChapterMusicPath, IndexMusicPath, CaptionMusicPath

## Musics 믹싱
def MusicsMixing(projectName, email, MainLang = 'Ko', Intro = 'off'):
    
    EditGeneration, MusicMixingDatas, LogoPath, IntroPath, TitleMusicPath, PartMusicPath, ChapterMusicPath, IndexMusicPath, CaptionMusicPath = MusicsMixingPath(projectName, email, MainLang = MainLang, Intro = Intro)
    ## 각 사운드 생성
    Logo_Audio = AudioSegment.from_wav(LogoPath) + AudioSegment.silent(duration = 3000)
    Intro_Audio = AudioSegment.empty()
    if IntroPath != None:
        Intro_Audio = AudioSegment.from_wav(IntroPath) + AudioSegment.silent(duration = 3500)
    TitleMusic_Audio = AudioSegment.from_wav(TitleMusicPath)
    PartMusic_Audio = AudioSegment.from_wav(PartMusicPath)
    ChapterMusic_Audio = AudioSegment.from_wav(ChapterMusicPath)
    IndexMusic_Audio = AudioSegment.from_wav(IndexMusicPath)
    CaptionMusic_Audio = AudioSegment.from_wav(CaptionMusicPath)
    
    ### 초기화: Mixed Audio누적 추가 시간 생성 ###
    MixedMusicAudio = Logo_Audio + Intro_Audio
    AccumulatedTimesList = [{'EditId': 0, 'ActorChunkId': 0, 'AccumulatedTime': MixedMusicAudio.duration_seconds + MusicMixingDatas[0]['Music']['Setting']['Length'][0]}]
    
    ###################################
    ### Logo, Intro, TitleMusic 믹싱 ###
    ###################################
    # TitleVoices 및 Setting
    TitleVoices = []
    AccumulatedTime = 0
    for i, MusicMixingData in enumerate(MusicMixingDatas):
        if MusicMixingData['Tag'] == 'Title':
            StartTime = MusicMixingData['StartTime']
            EndTime = MusicMixingData['EndTime']
            VoiceFileNames = MusicMixingData['VoiceFileName']
            # 파일 선별
            if os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[0])):
                TitleVoice = AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[0]))
                LastVoiceFileName = VoiceFileNames[0]
            elif os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[1])):
                TitleVoice = AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[1]))
                LastVoiceFileName = VoiceFileNames[1]
            MusicFilePath = MusicLayerPathGen(projectName, email, LastVoiceFileName)
            # TitleVoice 생성 및 리스트 저장
            TitleVoices.append(TitleVoice)
            
            EditId = MusicMixingData['EditId']
            ActorChunkId = MusicMixingData['ActorChunkId']
            Length = MusicMixingData['Music']['Setting']['Length']

            # AccumulatedTime 계산
            AccumulatedTime = (Length[i+1] - Length[i]) - (EndTime - StartTime)

            ## AccumulatedTimeDic 형성 및 합치기
            AccumulatedTimeDic = {'EditId': EditId, 'ActorChunkId': ActorChunkId, 'AccumulatedTime': AccumulatedTime}
            AccumulatedTimesList.append(AccumulatedTimeDic)
            
            # 최종 구간(페이드부분) 시간
            LastLengthTime = Length[i+2] - Length[i+1]
            EndTitleLength = Length[i+2]

    AccumulatedTimesList[-1]['AccumulatedTime'] += LastLengthTime
            
    # Mixing
    MixedTitleMusicAudio = TitleMusic_Audio
    for i in range(len(TitleVoices)):
        # 성우의 목소리 오버레이
        MixedTitleMusicAudio = MixedTitleMusicAudio.overlay(TitleVoices[i], position = Length[i] * 1000)
    
    # FadeOut
    FadeLenth = int((Length[i+2] * 1000) - (Length[i+1] * 1000))
    MixedTitleMusicAudioOrigin = MixedTitleMusicAudio[: Length[i+1] * 1000]
    MixedTitleMusicAudioFadeOut = MixedTitleMusicAudio[Length[i+1] * 1000 : Length[i+1] * 1000 + FadeLenth].fade_out(FadeLenth)
    MixedTitleMusicAudio = MixedTitleMusicAudioOrigin + MixedTitleMusicAudioFadeOut

    # MixedMusicAudio에 결합 및 저장
    MixedMusicAudio += MixedTitleMusicAudio
    MixedTitleMusicPath = MusicFilePath.replace('.wav', '_[TitleMusic].wav')
    MixedMusicAudio.export(MixedTitleMusicPath, format = 'wav')
    
    #########################
    ### TitleEndMusic 믹싱 ###
    #########################
    # EndTitleVoices 및 Setting
    EndTitleVoices = AudioSegment.empty()
    for i, MusicMixingData in enumerate(MusicMixingDatas):
        if MusicMixingData['Tag'] == 'TitleEnd':
            VoiceFileNames = MusicMixingData['VoiceFileName']
            Pause = MusicMixingData['Pause']
            Chunk = MusicMixingData['Chunk']
            # 파일 선별
            if os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[0])):
                EndTitleVoice = AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[0])) + AudioSegment.silent(duration = Pause * 1000)
                LastVoiceFileName = VoiceFileNames[0]
            elif os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[1])):
                EndTitleVoice = AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[1])) + AudioSegment.silent(duration = Pause * 1000)
                LastVoiceFileName = VoiceFileNames[1]
            MusicFilePath = MusicLayerPathGen(projectName, email, LastVoiceFileName)
            # EndTitleVoices 생성 및 리스트 저장
            EndTitleVoices += EndTitleVoice
    
    # EndTitleMusic 슬라이스
    MixedTitleEndMusicAudio = TitleMusic_Audio[EndTitleLength * 1000 : (EndTitleLength * 1000) + 45000]
    
    # FadeIn
    FadedInAudio = MixedTitleEndMusicAudio.fade_in(5000)
    _MixedTitleEndMusicAudio = FadedInAudio.fade_out(10000)
    
    # Mixing
    MixedTitleEndMusicAudio = _MixedTitleEndMusicAudio.overlay(EndTitleVoices, position = 500)
    
    # MixedMusicAudio에 저장
    MixedTitleMusicPath = MusicFilePath.replace('.wav', '_[EndMusic].wav')
    MixedTitleEndMusicAudio.export(MixedTitleMusicPath, format = 'wav')
    
    ###############################################
    ### Part, Chapter, Index, Caption Music 믹싱 ###
    ###############################################
    for i, MusicMixingData in enumerate(MusicMixingDatas):
        StartTime = MusicMixingData['StartTime']
        VoiceFileNames = MusicMixingData['VoiceFileName']
        EditId = MusicMixingData['EditId']
        ActorChunkId = MusicMixingData['ActorChunkId']
        Length = MusicMixingData['Music']['Setting']['Length']
        
        if MusicMixingData['Tag'] == 'Part':
            Pause = MusicMixingData['Pause']
            # 파일 선별
            PartVoice = AudioSegment.empty()
            if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[0]))) and ('M' in VoiceFileNames[0]):
                M_Switch = 1
            else:
                M_Switch = 0
            for j in range(len(VoiceFileNames)):
                if M_Switch == 1:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' in VoiceFileNames[j]):
                        PartVoice += (AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j])) + AudioSegment.silent(duration = Pause * 1000))
                        LastVoiceFileName = VoiceFileNames[j]
                else:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' not in VoiceFileNames[j]):
                        PartVoice += (AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j])) + AudioSegment.silent(duration = Pause * 1000))
                        LastVoiceFileName = VoiceFileNames[j]
            MusicFilePath = MusicLayerPathGen(projectName, email, LastVoiceFileName)
            M_Switch = 0
            
            # Mixing
            if PartMusic_Audio.duration_seconds >= PartVoice.duration_seconds:
                MixedMusicAudio = PartMusic_Audio.overlay(PartVoice, position = Length[0] * 1000)
            else:
                _PartVoice = AudioSegment.silent(duration = Length[0] * 1000) + PartVoice
                MixedMusicAudio = _PartVoice.overlay(PartMusic_Audio, position = 0)
            AccumulatedTime = MixedMusicAudio.duration_seconds - PartVoice.duration_seconds
            
        elif MusicMixingData['Tag'] == 'Chapter':
            Pause = MusicMixingData['Pause']
            # 파일 선별
            ChapterVoice = AudioSegment.empty()
            if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[0]))) and ('M' in VoiceFileNames[0]):
                M_Switch = 1
            else:
                M_Switch = 0
            for j in range(len(VoiceFileNames)):
                if M_Switch == 1:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' in VoiceFileNames[j]):
                        ChapterVoice += (AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j])) + AudioSegment.silent(duration = Pause * 1000))
                        LastVoiceFileName = VoiceFileNames[j]
                else:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' not in VoiceFileNames[j]):
                        ChapterVoice += (AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j])) + AudioSegment.silent(duration = Pause * 1000))
                        LastVoiceFileName = VoiceFileNames[j]
            MusicFilePath = MusicLayerPathGen(projectName, email, LastVoiceFileName)
            M_Switch = 0
            
            # Mixing
            if ChapterMusic_Audio.duration_seconds >= ChapterVoice.duration_seconds:
                MixedMusicAudio = ChapterMusic_Audio.overlay(ChapterVoice, position = Length[0] * 1000)
            else:
                _ChapterVoice = AudioSegment.silent(duration = Length[0] * 1000) + ChapterVoice
                MixedMusicAudio = _ChapterVoice.overlay(ChapterMusic_Audio, position = 0)
            AccumulatedTime = MixedMusicAudio.duration_seconds - ChapterVoice.duration_seconds
            
        elif MusicMixingData['Tag'] == 'Index':
            Pause = MusicMixingData['Pause']
            # 파일 선별
            IndexVoice = AudioSegment.empty()
            if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[0]))) and ('M' in VoiceFileNames[0]):
                M_Switch = 1
            else:
                M_Switch = 0
            for j in range(len(VoiceFileNames)):
                if M_Switch == 1:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' in VoiceFileNames[j]):
                        IndexVoice += (AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j])) + AudioSegment.silent(duration = Pause * 1000))
                        LastVoiceFileName = VoiceFileNames[j]
                else:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' not in VoiceFileNames[j]):
                        IndexVoice += (AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j])) + AudioSegment.silent(duration = Pause * 1000))
                        LastVoiceFileName = VoiceFileNames[j]
            MusicFilePath = MusicLayerPathGen(projectName, email, LastVoiceFileName)
            M_Switch = 0

            # Mixing
            if IndexMusic_Audio.duration_seconds >= IndexVoice.duration_seconds:
                MixedMusicAudio = IndexMusic_Audio.overlay(IndexVoice, position = Length[0] * 1000)
            else:
                _IndexVoice = AudioSegment.silent(duration = Length[0] * 1000) + IndexVoice
                MixedMusicAudio = _IndexVoice.overlay(IndexMusic_Audio, position = 0)
            AccumulatedTime = MixedMusicAudio.duration_seconds - IndexVoice.duration_seconds
            
        elif MusicMixingData['Tag'] == 'Caption':
            Pause = MusicMixingData['Pause']
            # 파일 선별
            CaptionVoice = AudioSegment.empty()
            if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[0]))) and ('M' in VoiceFileNames[0]):
                M_Switch = 1
            else:
                M_Switch = 0
            for j in range(len(VoiceFileNames)):
                if M_Switch == 1:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' in VoiceFileNames[j]):
                        CaptionVoice += (AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j])) + AudioSegment.silent(duration = Pause * 1000))
                        LastVoiceFileName = VoiceFileNames[j]
                else:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' not in VoiceFileNames[j]):
                        CaptionVoice += (AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j])) + AudioSegment.silent(duration = Pause * 1000))
                        LastVoiceFileName = VoiceFileNames[j]
            MusicFilePath = MusicLayerPathGen(projectName, email,LastVoiceFileName)
            M_Switch = 0

            # Mixing
            if CaptionMusic_Audio.duration_seconds >= CaptionVoice.duration_seconds:
                MixedMusicAudio = CaptionMusic_Audio.overlay(CaptionVoice, position = Length[0] * 1000)
            else:
                _CaptionVoice = AudioSegment.silent(duration = Length[0] * 1000) + CaptionVoice
                MixedMusicAudio = _CaptionVoice.overlay(CaptionMusic_Audio, position = 0)
            AccumulatedTime = MixedMusicAudio.duration_seconds - CaptionVoice.duration_seconds

        else:
            continue

        # AccumulatedTimeDic 형성 및 합치기
        AccumulatedTimeDic = {'EditId': EditId, 'ActorChunkId': ActorChunkId, 'AccumulatedTime': AccumulatedTime, 'Test': MixedMusicAudio.duration_seconds}
        AccumulatedTimesList.append(AccumulatedTimeDic)

        # MixedMusicAudio에 결합 및 저장
        MixedMusicPath = MusicFilePath.replace('.wav', f"_[{MusicMixingData['Tag']}Music].wav")
        MixedMusicAudio.export(MixedMusicPath, format = 'wav')
    
    return EditGeneration, MusicMixingDatas

## 생성된 음성파일 정렬/필터
def SortAndRemoveDuplicates(editGenerationKoChunks, files):
    # 파일명에서 필요한 정보를 추출하는 함수
    def ExtractFileInfo(FileName, removeList):
        match = re.match(r"(.+)\_(\d+(\.\d+)?)\_(.+?\(.+?\))\_\((\d+)\)(M?).*\.wav", FileName)
        if match == None:
            normalizeFileName = unicodedata.normalize('NFC', FileName)
            match = re.match(r"(.+)\_(\d+(\.\d+)?)\_(.+?\(.+?\))\_\((\d+)\)(M?).*\.wav", normalizeFileName)
        if match:
            # 생성넘버, 세부생성넘버, M의 유무, 이름(괄호 포함)을 반환
            return {
                'base_name': match.group(1),
                'gen_num': float(match.group(2)),
                'name_with_info': match.group(4),
                'detail_gen_num': int(match.group(5)),
                'has_M': match.group(6) == 'M'
            }
        else:
            # [ 파일 삭제 필요: FileName ]이 한번만 출력되도록 하는 장치
            if FileName not in removeList:
                print(f"[ 파일 삭제: {FileName} ]")  # 파일 정보 추출 실패 시 출력
                removeList.append(FileName)
            return {
                'base_name': '',
                'gen_num': float('inf'),
                'name_with_info': '',
                'detail_gen_num': float('inf'),
                'has_M': False
            }

    # 파일 정보 추출
    RemoveList = []
    file_infos = [ExtractFileInfo(File, RemoveList) for File in files]

    # 추출된 파일 정보를 기반으로 정렬 및 중복 제거
    SortedFiles = sorted(files, key=lambda File: (
        file_infos[files.index(File)]['gen_num'],
        file_infos[files.index(File)]['name_with_info'],
        file_infos[files.index(File)]['detail_gen_num'],
        not file_infos[files.index(File)]['has_M']  # 'M'이 없는 파일을 우선 정렬
    ))

    # 중복 제거
    UniqueFiles = []
    seen = set()
    for file in SortedFiles:
        info = ExtractFileInfo(file, RemoveList)
        if info['base_name'] != None:
            identifier = (info['base_name'], info['name_with_info'], info['gen_num'], info['detail_gen_num'])
            if identifier not in seen:
                UniqueFiles.append(file)
                seen.add(identifier)
            elif info['has_M']:  # 'M'이 포함된 파일이면 이전 'M'이 없는 파일을 대체
                # 마지막으로 추가된 파일이 'M'이 없는 파일인지 확인하고, 맞다면 제거
                if UniqueFiles and ExtractFileInfo(UniqueFiles[-1], RemoveList)['has_M'] == False and ExtractFileInfo(UniqueFiles[-1], RemoveList)['gen_num'] == info['gen_num'] and ExtractFileInfo(UniqueFiles[-1], RemoveList)['detail_gen_num'] == info['detail_gen_num']:
                    UniqueFiles.pop()  # 'M'이 없는 파일 제거
                UniqueFiles.append(file)

    return UniqueFiles

## 생성된 음성파일 합치기
def MusicSelector(projectName, email, MainLang = 'Ko', Intro = 'off'):
    EditGeneration, MusicMixingDatas = MusicsMixing(projectName, email, MainLang = MainLang, Intro = Intro)
    
    ## voiceLayer 경로와 musicLayer 경로 ##
    voiceLayerPath = VoiceLayerPathGen(projectName, email, '')
    musicLayerPath = MusicLayerPathGen(projectName, email, '')

    # Voice 폴더 내의 모든 .wav 파일 목록 추출
    VoiceRawFiles = [f for f in os.listdir(voiceLayerPath) if f.endswith('.wav')]
    # Voice 모든 .wav 파일 목록의 노멀라이즈
    VoiceRawFiles = [unicodedata.normalize('NFC', s) for s in VoiceRawFiles]
    
    VoiceFiles = []
    VoiceFilePattern = r".*?_(\d+(?:\.\d+)?)_([가-힣]+\(.*?\))_\((\d+)\)M?\.wav"
    for i in range(len(VoiceRawFiles)):
        VoiceFileMatch = re.match(VoiceFilePattern, VoiceRawFiles[i])
        if VoiceFileMatch == None:
            normalizeVoiceRawFile = unicodedata.normalize('NFC', VoiceRawFiles[i])
            VoiceFileMatch = re.match(VoiceFilePattern, normalizeVoiceRawFile)
        
        if VoiceFileMatch:
            chunkid, actorname, _ = VoiceFileMatch.groups()
        for j in range(len(EditGeneration)):
            if float(chunkid) == EditGeneration[j]['EditId'] and actorname == EditGeneration[j]['ActorName']:
                VoiceFiles.append(VoiceRawFiles[i])
                break
    
    ## musicLayer 파일 ##
    musicLayerPath = MusicLayerPathGen(projectName, email, '',)
    
    # Music 폴더 내의 모든 .wav 파일 목록 추출
    MusicRawFiles = [f for f in os.listdir(musicLayerPath) if f.endswith('.wav')]
    # Music 모든 .wav 파일 목록의 노멀라이즈
    MusicRawFiles = [unicodedata.normalize('NFC', s) for s in MusicRawFiles]
    
    MusicFiles = []
    MusicFilePattern = r".*?_(\d+(?:\.\d+)?)_([가-힣]+\(.*?\))_\((\d+)\)M?_([A-Za-z]+)\.wav"
    for i in range(len(MusicRawFiles)):
        MusicFileMatch = re.match(MusicFilePattern, MusicRawFiles[i])
        if MusicFileMatch == None:
            normalizeMusicRawFile = unicodedata.normalize('NFC', MusicRawFiles[i])
            MusicFileMatch = re.match(MusicFilePattern, normalizeMusicRawFile)
        
        if MusicFileMatch:
            chunkid, actorname, _ = MusicFileMatch.groups()
        for j in range(len(EditGeneration)):
            if float(chunkid) == EditGeneration[j]['EditId'] and actorname == EditGeneration[j]['ActorName']:
                MusicFiles.append(MusicRawFiles[i])
                break

    ## MusicMixingDatas를 활용하여 VoiceFilteredFiles파일 제거
    removeCount = 0
    for i in range(len(MusicMixingDatas)):
        VoiceFileName = MusicMixingDatas[i]['VoiceFileName']
        EditId = MusicMixingDatas[i]['EditId']
        ActorChunkId = MusicMixingDatas[i]['ActorChunkId']
        for j in range(len(VoiceFileName)):
            if VoiceFileName[j] in VoiceFiles:
                VoiceFiles.remove(VoiceFileName[j])
                removeCount += 1
                
        # EditGeneration에서 Music 부분 수정
        for k in range(len(EditGeneration)):
            if EditGeneration[k]['EditId'] == EditId:
                EditGeneration[k]['ActorChunk'][ActorChunkId]['EndTime'] = {'Time': None, 'Second': None}
            
    # 폴더 내의 모든 .wav 파일 목록 정렬/필터
    FilteredFiles = SortAndRemoveDuplicates(EditGeneration, VoiceFiles + MusicFiles)

    # 시간, 분, 초로 변환
    def SecondsToHMS(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    ## List -> Dic, EditGenerationKoChunks의 각 요소를 가독성이 좋은 딕셔너리로 변경하는 코드 (검수용도)
    def EditGenerationKoChunksToDic(EditGenerationKoChunks):
        EditGenerationKoDicChunks = []
        for Chunks in EditGenerationKoChunks:
            EditId = Chunks['EditId']
            ChunkId = Chunks['ChunkId']
            Tag = Chunks['Tag']
            ActorName = Chunks['ActorName']
            ActorChunk = Chunks['ActorChunk']
            Pause = Chunks['Pause']
            EndTime = Chunks['EndTime']
            Audio = []
            for i in range(max(len(ActorChunk), len(Pause), len(EndTime))):
                AudioDic = {"Chunk": ActorChunk[i] if i < len(ActorChunk) else None, "Pause": Pause[i] if i < len(Pause) else None, "EndTime": EndTime[i] if i < len(EndTime) else None}
                Audio.append(AudioDic)
            EditGenerationKoDicChunks.append({"EditId": EditId, "ChunkId": ChunkId, "Tag": Tag, "ActorName": ActorName, "ActorChunk": Audio})
        
        return EditGenerationKoDicChunks

    ## Dic -> List, EditGenerationKoChunks의 각 요소를 가독성이 좋은 리스트로 변경하는 코드 (프로세스용도)
    def EditGenerationKoChunksToList(EditGenerationKoChunks):
        EditGenerationKoListChunks = []
        for Chunks in EditGenerationKoChunks:
            EditId = Chunks['EditId']
            ChunkId = Chunks['ChunkId']
            Tag = Chunks['Tag']
            ActorName = Chunks['ActorName']
            ActorChunk = Chunks['ActorChunk']
            _ActorChunk = []
            Pause = []
            EndTime = []
            for i in range(len(ActorChunk)):
                _ActorChunk.append(ActorChunk[i]['Chunk'])
                Pause.append(ActorChunk[i]['Pause'])
                EndTime.append(ActorChunk[i]['EndTime'])
            EditGenerationKoListChunks.append({"EditId": EditId, "ChunkId": ChunkId, "Tag": Tag, "ActorName": ActorName, "ActorChunk": _ActorChunk, "Pause": Pause, "EndTime": EndTime})

        return EditGenerationKoListChunks

    EditGenerationKoChunks = EditGenerationKoChunksToList(EditGeneration)
    FilesCount = 0
    file_limit = 100  # 파일 분할 기준
    current_file_index = 1
    CombinedSound = AudioSegment.empty()

    UpdateTQDM = tqdm(EditGenerationKoChunks,
                    total=len(EditGenerationKoChunks),
                    desc='MusicGenerator')

    # 전체 오디오 클립의 누적 길이를 추적하는 변수 추가
    total_duration_seconds = 0
    for Update in UpdateTQDM:
        ActorChunk = Update['ActorChunk']
        for num in range(len(ActorChunk)):
            if len(FilteredFiles) > FilesCount:
                ProcessFileName = f"{projectName}_{Update['EditId']}_{Update['ActorName']}_({num})"
                if ProcessFileName in FilteredFiles[FilesCount]:
                    Update['EndTime'] = []
                    for j in range(len(Update['Pause'])):
                        if len(FilteredFiles) > FilesCount:
                            if '_[' in FilteredFiles[FilesCount]:
                                sound_file = AudioSegment.from_wav(os.path.join(musicLayerPath, FilteredFiles[FilesCount]))
                            else:
                                sound_file = AudioSegment.from_wav(os.path.join(voiceLayerPath, FilteredFiles[FilesCount]))
                                
                            FilesCount += 1
                            PauseDuration_ms = Update['Pause'][j] * 1000
                            silence = AudioSegment.silent(duration = PauseDuration_ms)
                            CombinedSound += sound_file + silence

                            # 누적된 CombinedSound의 길이를 전체 길이 추적 변수에 추가
                            total_duration_seconds += sound_file.duration_seconds + PauseDuration_ms / 1000.0
                            # EndTime에는 누적된 전체 길이를 저장
                            #######################################
                            #######################################
                            Update['EndTime'].append({"PauseId": j, "Time": SecondsToHMS(total_duration_seconds), "Second": total_duration_seconds})
                            #######################################
                            #######################################

                            # 파일 단위로 저장 및 CombinedSound 초기화
                            if FilesCount % file_limit == 0 or FilesCount == len(FilteredFiles):
                                MinNumber = current_file_index * file_limit-file_limit + 1
                                MaxNumber = min(current_file_index * file_limit, len(FilteredFiles))
                                file_name = f"{projectName}_MusicLayer_{MinNumber}-{MaxNumber}.mp3"
                                CombinedSound.export(os.path.join(musicLayerPath, file_name), format = "mp3", bitrate = "320k")
                                CombinedSound = AudioSegment.empty()  # 다음 파일 묶음을 위한 초기화
                                current_file_index += 1

    # for 루프 종료 후 남은 CombinedSound 처리 (특수경우)
    if (not CombinedSound.empty()) and (int(CombinedSound.duration_seconds) >= 1):
        minNumber = current_file_index * file_limit-file_limit + 1
        _maxNumber = FilesCount
        maxNumber = FilesCount + 1

        if minNumber < maxNumber and len(FilteredFiles) == maxNumber:
            file_name = f"{projectName}_MusicLayer_{minNumber}-{maxNumber}.mp3"
            current_file_index += 1
        elif minNumber < _maxNumber and len(FilteredFiles) == _maxNumber:
            file_name = f"{projectName}_MusicLayer_{minNumber}-{maxNumber}.mp3"
            current_file_index += 1

        CombinedSound.export(os.path.join(musicLayerPath, file_name), format = "mp3", bitrate = "320k")

    # 100개 단위로 분할된 파일 합치기
    UpdateTQDM = tqdm(range(1, current_file_index),
                      desc='MusicCombine',
                      total=current_file_index-1)
    
    final_combined = AudioSegment.empty()
    for i in UpdateTQDM:  # tqdm 루프를 사용하여 진행 상황 표시
        part_name = f"{projectName}_MusicLayer_{i*file_limit-file_limit+1}-{min(i*file_limit, len(FilteredFiles))}.mp3"
        part_path = os.path.join(musicLayerPath, part_name)
        part = AudioSegment.from_file(part_path)
        final_combined += part
        # 파일 묶음 삭제
        os.remove(part_path)

    # 마지막 5초 공백 추가
    final_combined += AudioSegment.silent(duration = 5000)  # 5초간의 공백 생성

    # 최종적으로 합쳐진 음성 파일 저장
    print(f"[ 최종 {projectName + '_AudioBook.mp3'} 생성중 ... ]")
    voiceLayerPath = VoiceLayerPathGen(projectName, email, projectName + '_AudioBook.mp3', 'Master')
    final_combined.export(os.path.join(voiceLayerPath), format = "mp3", bitrate = "320k")
    final_combined = AudioSegment.empty()

    ## EditGenerationKoChunks의 Dic(검수)
    EditGenerationKoChunks = EditGenerationKoChunksToDic(EditGenerationKoChunks)
    
    ## EndTitleMusic 최종 시간 자리 수정
    for i, EditGenerationKo in enumerate(EditGenerationKoChunks):
        ActorChunk = EditGenerationKo['ActorChunk']
        for j, chunk in enumerate(ActorChunk):
            if chunk['EndTime'] is not None and chunk['EndTime']['Second'] is not None:
                LastEditChunkId = i
                LastActorChunkId = j
                LastEndTime = chunk['EndTime']
            else:
                chunk['EndTime'] = {"Time": None, "Second": None}
            _LastEditChunkId = i
            _LastActorChunkId = j
            
    EditGenerationKoChunks[LastEditChunkId]['ActorChunk'][LastActorChunkId]['EndTime'] = {"Time": None, "Second": None}
    EditGenerationKoChunks[_LastEditChunkId]['ActorChunk'][_LastActorChunkId]['EndTime'] = LastEndTime

    # MatchedChunksEdit 경로 생성
    fileName = '[' + projectName + '_' + 'AudioBook_Edit].json'
    MatchedChunksPath = VoiceLayerPathGen(projectName, email, fileName, Folder = 'Master')

    ## EndTime이 업데이트 된 EditGenerationKoChunks 저장
    with open(MatchedChunksPath, 'w', encoding = 'utf-8') as json_file:
        json.dump(EditGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)

    return EditGenerationKoChunks

## 프롬프트 요청 및 결과물 Json을 MusicLayer에 업데이트
def MusicLayerUpdate(projectName, email, MainLang = 'Ko', Intro = 'off'):
    print(f"< User: {email} | Project: {projectName} | MusicLayerGenerator 시작 >")
    
    EditGenerationKoChunks = MusicSelector(projectName, email, MainLang = MainLang, Intro = Intro)

    with get_db() as db:
        
        project = GetProject(projectName, email)
        if MainLang == 'Ko':
            project.MixingMasteringKo[1]['AudioBookLayers' + MainLang] = EditGenerationKoChunks
        if MainLang == 'En':
            project.MixingMasteringEn[1]['AudioBookLayers' + MainLang] = EditGenerationKoChunks
        if MainLang == 'Ja':
            project.MixingMasteringJa[1]['AudioBookLayers' + MainLang] = EditGenerationKoChunks
        if MainLang == 'Zh':
            project.MixingMasteringZh[1]['AudioBookLayers' + MainLang] = EditGenerationKoChunks
        if MainLang == 'Es':
            project.MixingMasteringEs[1]['AudioBookLayers' + MainLang] = EditGenerationKoChunks
        
        flag_modified(project, "MixingMastering" + MainLang)
        
        db.add(project)
        db.commit()
        
    print(f"[ User: {email} | Project: {projectName} | MusicLayerGenerator 완료 ]\n")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "노인을위한나라는있다"
    mainLang = 'Ko'
    intro = "off" # Intro = ['한국출판문화산업진흥원' ...]
    #########################################################################