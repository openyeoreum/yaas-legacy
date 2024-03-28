import os
import unicodedata
import sys
import json
sys.path.append("/yaas")

from tqdm import tqdm
from pydub import AudioSegment
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
    
    ## PartMusicDataSet 불러오기
    soundDataSet = GetSoundDataSet("PartMusicDataSet")
    PartMusicDataSet = soundDataSet[0][1]['PartMusics'][1:]
    
    ## IndexMusicDataSet 불러오기
    soundDataSet = GetSoundDataSet("IndexMusicDataSet")
    IndexMusicDataSet = soundDataSet[0][1]['IndexMusics'][1:]
    
    return SelectionGeneration, EditGeneration, LogoDataSet, IntroDataSet, TitleMusicDataSet, PartMusicDataSet, IndexMusicDataSet

############################
##### MusicMatched 생성 #####
############################
## VoiceLayerPath 경로 생성
def VoiceLayerPathGen(projectName, email, FileName):
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
    LayerPath = os.path.join(BasePath, UserFolderName, StorageFolderName, projectName, f"{projectName}_mixed_audiobook_file", "VoiceLayers", FileName)
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
    SelectionGeneration, EditGeneration, LogoDataSet, IntroDataSet, TitleMusicDataSet, PartMusicDataSet, IndexMusicDataSet = LoadMusicDataSet(projectName, email, MainLang = MainLang)
    
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
        MatchedTitleMusicDic = {'Tag': 'Title', 'FilePath': MatchedTitleMusic['FilePath'], 'Setting': MatchedTitleMusic['Setting']}
        MatchedMusics.append(MatchedTitleMusicDic)

        ## PartMusicDataSet에서 PartMusicPath 찾기
        PartMusicScoreList = []
        for PartMusic in PartMusicDataSet:
            # GenreScore 계산
            GenreScores = PartMusic['PartMusic']['Genre']
            MergedGenreScore = 0
            for GenreScore in GenreScores:
                if GenreScore['index'] in GenreRatio:
                    MergedGenreScore += (GenreScore['Score'] * GenreRatio[GenreScore['index']])
            # GenderScore 계산
            GenderScores = PartMusic['PartMusic']['Gender']
            MergedGenderScore = 0
            for GenderScore in GenderScores:
                if GenderScore['index'] in GenderRatio:
                    MergedGenderScore += (GenderScore['Score'] * GenderRatio[GenderScore['index']])
            # AgeScore 계산
            AgeScores = PartMusic['PartMusic']['Age']
            MergedAgeScore = 0
            for AgeScore in AgeScores:
                if AgeScore['index'] in AgeRatio:
                    MergedAgeScore += (AgeScore['Score'] * AgeRatio[AgeScore['index']])
            # PersonalityScore 계산
            PersonalityScores = PartMusic['PartMusic']['Personality']
            MergedPersonalityScore = 0
            for PersonalityScore in PersonalityScores:
                if PersonalityScore['index'] in PersonalityRatio:
                    MergedPersonalityScore += (PersonalityScore['Score'] * PersonalityRatio[PersonalityScore['index']])
            # EmotionScore 계산
            EmotionScores = PartMusic['PartMusic']['Emotion']
            MergedEmotionScore = 0
            for EmotionScore in EmotionScores:
                if EmotionScore['index'] in EmotionRatio:
                    MergedEmotionScore += (EmotionScore['Score'] * EmotionRatio[EmotionScore['index']])
            # PartMusic Score 합산
            PartMusicScoreList.append((MergedGenreScore/1000) * (MergedGenderScore/1000) * (MergedAgeScore/1000) * (MergedPersonalityScore/1000) * (MergedEmotionScore/1000))       
        # PartMusic, ChapterMusic FilePath 도출
        SortedMatchedPartScores = sorted(PartMusicScoreList, reverse = True)
        # PartMusic
        MatchedPartMusic = PartMusicDataSet[PartMusicScoreList.index(SortedMatchedPartScores[0])]
        MatchedPartMusicDic = {'Tag': 'Part', 'FilePath': MatchedPartMusic['FilePath'], 'Setting': MatchedPartMusic['Setting']}
        MatchedMusics.append(MatchedPartMusicDic)
        # ChapterMusic
        MatchedChapterMusic = PartMusicDataSet[PartMusicScoreList.index(SortedMatchedPartScores[1])]
        MatchedChapterMusicDic = {'Tag': 'Chapter', 'FilePath': MatchedChapterMusic['FilePath'], 'Setting': MatchedChapterMusic['Setting']}
        MatchedMusics.append(MatchedChapterMusicDic)
        
        ## IndexMusicDataSet에서 IndexMusicPath 찾기
        IndexMusicScoreList = []
        for IndexMusic in IndexMusicDataSet:
            # GenreScore 계산
            GenreScores = IndexMusic['IndexMusic']['Genre']
            MergedGenreScore = 0
            for GenreScore in GenreScores:
                if GenreScore['index'] in GenreRatio:
                    MergedGenreScore += (GenreScore['Score'] * GenreRatio[GenreScore['index']])
            # GenderScore 계산
            GenderScores = IndexMusic['IndexMusic']['Gender']
            MergedGenderScore = 0
            for GenderScore in GenderScores:
                if GenderScore['index'] in GenderRatio:
                    MergedGenderScore += (GenderScore['Score'] * GenderRatio[GenderScore['index']])
            # AgeScore 계산
            AgeScores = IndexMusic['IndexMusic']['Age']
            MergedAgeScore = 0
            for AgeScore in AgeScores:
                if AgeScore['index'] in AgeRatio:
                    MergedAgeScore += (AgeScore['Score'] * AgeRatio[AgeScore['index']])
            # PersonalityScore 계산
            PersonalityScores = IndexMusic['IndexMusic']['Personality']
            MergedPersonalityScore = 0
            for PersonalityScore in PersonalityScores:
                if PersonalityScore['index'] in PersonalityRatio:
                    MergedPersonalityScore += (PersonalityScore['Score'] * PersonalityRatio[PersonalityScore['index']])
            # EmotionScore 계산
            EmotionScores = IndexMusic['IndexMusic']['Emotion']
            MergedEmotionScore = 0
            for EmotionScore in EmotionScores:
                if EmotionScore['index'] in EmotionRatio:
                    MergedEmotionScore += (EmotionScore['Score'] * EmotionRatio[EmotionScore['index']])
            # IndexMusic Score 합산
            IndexMusicScoreList.append((MergedGenreScore/1000) * (MergedGenderScore/1000) * (MergedAgeScore/1000) * (MergedPersonalityScore/1000) * (MergedEmotionScore/1000))
        # IndexMusic, CaptionMusic FilePath 도출
        SortedMatchedIndexScores = sorted(IndexMusicScoreList, reverse = True)
        # IndexMusic
        MatchedIndexMusic = IndexMusicDataSet[IndexMusicScoreList.index(SortedMatchedIndexScores[0])]
        MatchedIndexMusicDic = {'Tag': 'Index', 'FilePath': MatchedIndexMusic['FilePath'], 'Setting': MatchedIndexMusic['Setting']}
        MatchedMusics.append(MatchedIndexMusicDic)
        # CaptionMusic
        MatchedCaptionMusic = IndexMusicDataSet[IndexMusicScoreList.index(SortedMatchedIndexScores[1])]
        MatchedCaptionMusicDic = {'Tag': 'Caption', 'FilePath': MatchedCaptionMusic['FilePath'], 'Setting': MatchedCaptionMusic['Setting']}
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
    
    ## EditGeneration에서 Tag 추출하기
    # TagMusic 선정
    Intro = None
    for matchedMusic in MatchedMusics:
        if matchedMusic['Tag'] != None:
            if 'Logo' in matchedMusic['Tag']:
                Logo = matchedMusic
            elif 'Intro' in matchedMusic['Tag']:
                Intro = matchedMusic
            elif 'Title' in matchedMusic['Tag']:
                TitleMusic = matchedMusic
            elif 'Part' in matchedMusic['Tag']:
                PartMusic = matchedMusic
            elif 'Chapter' in matchedMusic['Tag']:
                ChapterMusic = matchedMusic
            elif 'Index' in matchedMusic['Tag']:
                IndexMusic = matchedMusic
            elif 'Caption' in matchedMusic['Tag']:
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
        EndTime = EditGeneration[i]['ActorChunk'][-1]['EndTime']['Second']
        VoiceFileName = []
        for k in range(len(EditGeneration[i]['ActorChunk'])):
            VoiceFileName.append(f'{projectName}_{EditId}_{ActorName}_({k})M.wav')
            VoiceFileName.append(f'{projectName}_{EditId}_{ActorName}_({k}).wav')
        
        if Tag == 'Title':
            TitleMusicMixingDataDics = [{'EditId': EditId, 'ActorChunkId': 0, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': TitleMusic}]
            EditGeneration[i]['Logo'] = Logo
            EditGeneration[i]['Intro'] = Intro
            EditGeneration[i]['Music'] = TitleMusic
            if EditGeneration[i+1]['Tag'] == 'Narrator' and EditGeneration[i+2]['Tag'] in ['Logue', 'Part', 'Chapter', 'Index']:
                TitleActorChunks = EditGeneration[i+1]['ActorChunk']
                EditId = EditGeneration[i+1]['EditId']
                StartTime = EndTime
                for j in range(min(len(TitleActorChunks), 2)):
                    EndTime = TitleActorChunks[j]['EndTime']['Second']
                    VoiceFileName = [f'{projectName}_{EditId}_{ActorName}_({j})M.wav', f'{projectName}_{EditId}_{ActorName}_({j}).wav']
                    TitleMusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': j, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': TitleMusic}
                    TitleMusicMixingDataDics.append(TitleMusicMixingDataDic)
                    StartTime = EndTime
                MusicMixingDatas += TitleMusicMixingDataDics
                TitleMusicMixingDataDics = []
                continue

        elif Tag == 'Part':
            MusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': 0, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': PartMusic}
            EditGeneration[i]['Music'] = PartMusic
        elif Tag == 'Chapter':
            MusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': 0, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': ChapterMusic}
            EditGeneration[i]['Music'] = ChapterMusic
        elif Tag == 'Chapter':
            MusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': 0, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': IndexMusic}
            EditGeneration[i]['Music'] = IndexMusic
        elif (BeforeTag not in ['Caption', 'CaptionComment']) and (Tag == 'Caption'):
            MusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': 0, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': VoiceFileName, 'Music': CaptionMusic}
            EditGeneration[i]['Music'] = CaptionMusic

        elif i >= (len(EditGeneration)-2):
            ActorChunk = EditGeneration[i]['ActorChunk']
            print(i)
            for z in range(len(ActorChunk)):
                EndTime = ActorChunk[z]['EndTime']['Second']
                Chunk = ActorChunk[z]['Chunk']
                EndMusicMixingDataDic = {'EditId': EditId, 'ActorChunkId': z, 'Tag': 'TitleEnd', 'Chunk': Chunk, 'StartTime': StartTime, 'EndTime': EndTime, 'VoiceFileName': [VoiceFileName[z*2], VoiceFileName[z*2+1]], 'Music': TitleMusic}
                StartTime = EndTime
                EndMusicMixingDatas.append(EndMusicMixingDataDic)
                print(f'{EndMusicMixingDataDic}\n\n')
                EndMusicMixingDataDic = None
        
        if MusicMixingDataDic != None:
            MusicMixingDatas.append(MusicMixingDataDic)
        MusicMixingDataDic = None
        
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
    
    return MusicMixingDatas, LogoPath, IntroPath, TitleMusicPath, PartMusicPath, ChapterMusicPath, IndexMusicPath, CaptionMusicPath

## Musics 믹싱
def MusicsMixing(projectName, email, MainLang = 'Ko', Intro = 'off'):
    
    MusicMixingDatas, LogoPath, IntroPath, TitleMusicPath, PartMusicPath, ChapterMusicPath, IndexMusicPath, CaptionMusicPath = MusicsMixingPath(projectName, email, MainLang = MainLang, Intro = Intro)
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
            elif os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[1])):
                TitleVoice = AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[1]))
            MusicFilePath = MusicLayerPathGen(projectName, email, VoiceFileNames[1])
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
    MixedTitleEndMusicAudio = TitleMusic_Audio[Length[i+2] * 1000:]
    
    # FadeIn
    
    
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
            # 파일 선별
            PartVoice = AudioSegment.empty()
            if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[0]))) and ('M' in VoiceFileNames[0]):
                M_Switch = 1
            else:
                M_Switch = 0
            for j in range(len(VoiceFileNames)):
                if M_Switch == 1:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' in VoiceFileNames[j]):
                        PartVoice += AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))
                        LastVoiceFileName = VoiceFileNames[j]
                else:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' not in VoiceFileNames[j]):
                        PartVoice += AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))
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
            # 파일 선별
            ChapterVoice = AudioSegment.empty()
            if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[0]))) and ('M' in VoiceFileNames[0]):
                M_Switch = 1
            else:
                M_Switch = 0
            for j in range(len(VoiceFileNames)):
                if M_Switch == 1:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' in VoiceFileNames[j]):
                        ChapterVoice += AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))
                        LastVoiceFileName = VoiceFileNames[j]
                else:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' not in VoiceFileNames[j]):
                        ChapterVoice += AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))
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
            # 파일 선별
            IndexVoice = AudioSegment.empty()
            if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[0]))) and ('M' in VoiceFileNames[0]):
                M_Switch = 1
            else:
                M_Switch = 0
            for j in range(len(VoiceFileNames)):
                if M_Switch == 1:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' in VoiceFileNames[j]):
                        IndexVoice += AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))
                        LastVoiceFileName = VoiceFileNames[j]
                else:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' not in VoiceFileNames[j]):
                        IndexVoice += AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))
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
            # 파일 선별
            CaptionVoice = AudioSegment.empty()
            if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[0]))) and ('M' in VoiceFileNames[0]):
                M_Switch = 1
            else:
                M_Switch = 0
            for j in range(len(VoiceFileNames)):
                if M_Switch == 1:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' in VoiceFileNames[j]):
                        CaptionVoice += AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))
                        LastVoiceFileName = VoiceFileNames[j]
                else:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' not in VoiceFileNames[j]):
                        CaptionVoice += AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))
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
        
## 생성된 음성파일 합치기
def MusicSelector(projectName, email, EditGenerationKoChunks, MatchedChunksPath):
    # VoiceLayerFileName = projectName + "_VoiceLayer.wav"
    # normalizeVoiceLayerFileName = unicodedata.normalize('NFC', VoiceLayerFileName)
    voiceLayerPath = VoiceLayerPathGen(projectName, email, '', 'Mixed')

    # 폴더 내의 모든 .wav 파일 목록 추출
    RawFiles = [f for f in os.listdir(voiceLayerPath) if f.endswith('.wav')]
    # 모든 .wav 파일 목록의 노멀라이즈
    RawFiles = [unicodedata.normalize('NFC', s) for s in RawFiles]
    # # VoiceLayer 파일이 생성되었을 경우 해당 파일명을 RawFiles 리스트에서 삭제
    # if (VoiceLayerFileName in RawFiles) or (normalizeVoiceLayerFileName in RawFiles):
    #     try:
    #         RawFiles.remove(VoiceLayerFileName)
    #     except ValueError:
    #         pass
    #     try:
    #         RawFiles.remove(normalizeVoiceLayerFileName)
    #     except ValueError:
    #         pass
    # 성우 변경 파일이 생성되었을 경우 이전 성우 파일명으로 새로운 RawFiles 리스트에서 생성
    Files = []
    VoiceFilePattern = r".*?_(\d+(?:\.\d+)?)_([가-힣]+\(.*?\))_\((\d+)\)M?\.wav"
    for i in range(len(RawFiles)):
        VoiceFileMatch = re.match(VoiceFilePattern, RawFiles[i])
        if VoiceFileMatch == None:
            normalizeRawFile = unicodedata.normalize('NFC', RawFiles[i])
            VoiceFileMatch = re.match(VoiceFilePattern, normalizeRawFile)
        
        if VoiceFileMatch:
            chunkid, actorname, _ = VoiceFileMatch.groups()
        for j in range(len(EditGenerationKoChunks)):
            if float(chunkid) == EditGenerationKoChunks[j]['EditId'] and actorname == EditGenerationKoChunks[j]['ActorName']:
                Files.append(RawFiles[i])
                break

    # 시간, 분, 초로 변환
    def SecondsToHMS(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    # 폴더 내의 모든 .wav 파일 목록 정렬/필터
    FilteredFiles = SortAndRemoveDuplicates(EditGenerationKoChunks, Files)
    FilesCount = 0
    file_limit = 100  # 파일 분할 기준
    current_file_index = 1
    CombinedSound = AudioSegment.empty()

    UpdateTQDM = tqdm(EditGenerationKoChunks,
                    total=len(EditGenerationKoChunks),
                    desc='VoiceGenerator')

    # 전체 오디오 클립의 누적 길이를 추적하는 변수 추가
    total_duration_seconds = 0
    for Update in UpdateTQDM:
        Update['EndTime'] = []
        for j in range(len(Update['Pause'])):
            sound_file = AudioSegment.from_wav(os.path.join(voiceLayerPath, FilteredFiles[FilesCount]))
            PauseDuration_ms = Update['Pause'][j] * 1000
            silence = AudioSegment.silent(duration = PauseDuration_ms)
            CombinedSound += sound_file + silence
            FilesCount += 1

            # 누적된 CombinedSound의 길이를 전체 길이 추적 변수에 추가
            total_duration_seconds += sound_file.duration_seconds + PauseDuration_ms / 1000.0
            # EndTime에는 누적된 전체 길이를 저장
            Update['EndTime'].append(total_duration_seconds)

            # 파일 단위로 저장 및 CombinedSound 초기화
            if FilesCount % file_limit == 0 or FilesCount == len(FilteredFiles):
                MinNumber = current_file_index*file_limit-file_limit+1
                MaxNumber = min(current_file_index*file_limit, len(FilteredFiles))
                file_name = f"{projectName}_VoiceLayer_{MinNumber}-{MaxNumber}.wav"
                CombinedSound.export(os.path.join(voiceLayerPath, file_name), format = "wav")
                CombinedSound = AudioSegment.empty()  # 다음 파일 묶음을 위한 초기화
                current_file_index += 1

    # for 루프 종료 후 남은 CombinedSound 처리 (특수경우)
    if not CombinedSound.empty():
        minNumber = current_file_index*file_limit-file_limit+1
        _maxNumber = FilesCount
        maxNumber = FilesCount + 1
        
        if minNumber < maxNumber and len(FilteredFiles) == maxNumber:
            file_name = f"{projectName}_VoiceLayer_{minNumber}-{maxNumber}.wav"
            current_file_index += 1
        elif minNumber < _maxNumber and len(FilteredFiles) == _maxNumber:
            file_name = f"{projectName}_VoiceLayer_{minNumber}-{maxNumber}.wav"
            current_file_index += 1
            
        CombinedSound.export(os.path.join(voiceLayerPath, file_name), format = "wav")

    # 최종 파일 합치기
    final_combined = AudioSegment.empty()
    for i in range(1, current_file_index):
        part_name = f"{projectName}_VoiceLayer_{i*file_limit-file_limit+1}-{min(i*file_limit, len(FilteredFiles))}.wav"
        part_path = os.path.join(voiceLayerPath, part_name)
        part = AudioSegment.from_wav(part_path)
        final_combined += part
        # 파일 묶음 삭제
        os.remove(part_path)

    # wav파일과 Edit의 시간 오차율 교정
    final_combined_seconds = final_combined.duration_seconds
    seconds_error_rate = final_combined_seconds/total_duration_seconds
    for Chunks in EditGenerationKoChunks:
        EndTime = Chunks['EndTime']
        for i in range(len(EndTime)):
            RawSecond = copy.deepcopy(EndTime[i])
            Second = RawSecond * seconds_error_rate
            Time = SecondsToHMS(Second)
            EndTime[i] = {"Time": Time, "Second": Second}
    
    # 마지막 5초 공백 추가
    final_combined += AudioSegment.silent(duration = 5000)  # 5초간의 공백 생성

    # 최종적으로 합쳐진 음성 파일 저장
    voiceLayerPath = VoiceLayerPathGen(projectName, email, projectName + '_AudioBook.wav', 'Master')
    final_combined.export(os.path.join(voiceLayerPath), format = "wav")
    final_combined = AudioSegment.empty()
    
    ## EditGenerationKoChunks의 Dic(검수)
    EditGenerationKoChunks = EditGenerationKoChunksToDic(EditGenerationKoChunks)
    ## EndTime이 업데이트 된 EditGenerationKoChunks 저장
    with open(MatchedChunksPath, 'w', encoding = 'utf-8') as json_file:
        json.dump(EditGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)
        
    return EditGenerationKoChunks

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "노인을위한나라는있다"
    mainLang = 'Ko'
    intro = "off" # Intro = ['한국출판문화산업진흥원' ...]
    #########################################################################
    
    MusicsMixing(projectName, email, MainLang = mainLang, Intro = intro)