import os
import unicodedata
import sys
import re
import time
import random
import copy
import shutil
import sox
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
    fileName = '[' + projectName + '_' + 'MatchedMusics].json'
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
    
    editGeneration, MatchedMusics = MusicMatchedSelectionGenerationChunks(projectName, email, MainLang = 'Ko', Intro = 'off')
    
    ## EditGeneration 내에 Part, Chapter 유무 확인
    PartSwitch = False
    ChapterSwitch = False
    for Edit in editGeneration:
        if Edit['Tag'] == 'Part':
            PartSwitch = True
        elif Edit['Tag'] == 'Chapter':
            ChapterSwitch = True
            
    PartChapterSwitch = False
    if PartSwitch and ChapterSwitch:
        PartChapterSwitch = True
    
    ## EditGeneration에서 Tag 추출하기
    # SubChapterPart 우선 선정
    for matchedMusic in MatchedMusics:
        if matchedMusic['Tag'] != None:
            if 'SubChapterPart' in matchedMusic['Tag']:
                matchedSubChapterPart = matchedMusic
    
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
                    ChapterMusic = matchedSubChapterPart
            else:
                if 'MainChapterPart' in matchedMusic['Tag']:
                    if PartSwitch:
                        PartMusic = matchedMusic
                        ChapterMusic = matchedSubChapterPart
                    if ChapterSwitch:
                        ChapterMusic = matchedMusic
                        PartMusic = matchedSubChapterPart
                        
            if 'Index' in matchedMusic['Tag']:
                IndexMusic = matchedMusic
            if 'Caption' in matchedMusic['Tag']:
                CaptionMusic = matchedMusic

    ## _Intro2_가 Title앞에 존재하는 경우 ##
    _Intro2_VoiceFileNames = []
    if editGeneration[0]['Tag'] == 'Intro':
        EditId = editGeneration[0]['EditId']
        ActorName = editGeneration[0]['ActorName']
        for a in range(len(editGeneration[0]['ActorChunk'])):
            _Intro2_VoiceFileNames.append([f'{projectName}_{EditId}_{ActorName}_({a})M.wav', f'{projectName}_{EditId}_{ActorName}_({a}).wav'])
        EditGeneration = editGeneration[1:]
    else:
        EditGeneration = editGeneration
    ## _Intro2_가 Title앞에 존재하는 경우 ##

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
            if (EditGeneration[i+1]['Tag'] in ['Narrator', 'Caption']) and (EditGeneration[i+2]['Tag'] in ['Logue', 'Part', 'Chapter', 'Index']) or (EditGeneration[i+1]['Tag'] in ['Narrator', 'Caption']) and (EditGeneration[i+2]['Tag'] in ['Narrator', 'Caption']) and (EditGeneration[i+3]['Tag'] in ['Logue', 'Part', 'Chapter', 'Index']) or (EditGeneration[i+1]['Tag'] in ['Narrator', 'Caption']) and (EditGeneration[i+2]['Tag'] in ['Narrator', 'Caption']) and (EditGeneration[i+3]['Tag'] in ['Narrator', 'Caption']) and (EditGeneration[i+4]['Tag'] in ['Logue', 'Part', 'Chapter', 'Index']) or (EditGeneration[i+1]['Tag'] in ['Narrator', 'Caption']) and (EditGeneration[i+2]['Tag'] in ['Narrator', 'Caption']) and (EditGeneration[i+3]['Tag'] in ['Narrator', 'Caption']) and (EditGeneration[i+4]['Tag'] in ['Narrator', 'Caption']) and (EditGeneration[i+5]['Tag'] in ['Logue', 'Part', 'Chapter', 'Index']):
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
    
    return editGeneration, _Intro2_VoiceFileNames, MusicMixingDatas, LogoPath, IntroPath, TitleMusicPath, PartMusicPath, ChapterMusicPath, IndexMusicPath, CaptionMusicPath

## Musics 파일 볼륨 값 일치시키기 (볼륨이 Volume값 보다 작을 경우에는 원본 볼륨을 유지)
def MusicsVolume(MusicPath, Volume):
    # 오디오 파일 로드
    audio = AudioSegment.from_file(MusicPath)
    # 현재 평균 볼륨 차이 계산
    ChangeIndBFS = Volume - audio.dBFS
    
    # 볼륨 조정 조건 추가: 현재 볼륨이 목표 볼륨보다 클 경우에만 볼륨을 조정
    if audio.dBFS > Volume:
        NormalizedAudio = audio.apply_gain(ChangeIndBFS)
    else:
        # 볼륨이 기준보다 낮거나 같으면 원본 오디오를 그대로 반환
        NormalizedAudio = audio
    
    return NormalizedAudio

## Musics 믹싱
def MusicsMixing(projectName, email, MainLang = 'Ko', Intro = 'off'):
    
    EditGeneration, _Intro2_VoiceFileNames, MusicMixingDatas, LogoPath, IntroPath, TitleMusicPath, PartMusicPath, ChapterMusicPath, IndexMusicPath, CaptionMusicPath = MusicsMixingPath(projectName, email, MainLang = MainLang, Intro = Intro)
    ## 각 사운드 생성
    Volume = -30 # 볼륨은 최대 값을 0으로 산정 -값이 클수록 볼륨이 작음(-25 ~ -32)
    Logo_Audio = AudioSegment.from_wav(LogoPath) + AudioSegment.silent(duration = 3000)
    Intro_Audio = AudioSegment.empty()
    if IntroPath != None:
        Intro_Audio = AudioSegment.from_wav(IntroPath) + AudioSegment.silent(duration = 3500)
    
    ## _Intro2_가 Title앞에 존재하는 경우 ##
    _Intro2_Audio = AudioSegment.empty()
    if EditGeneration[0]['Tag'] == 'Intro':
        ActorChunk = EditGeneration[0]['ActorChunk']
        for a in range(len(ActorChunk)):
            if os.path.exists(VoiceLayerPathGen(projectName, email, _Intro2_VoiceFileNames[a][0])):
                _Intro2_Voice = AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, _Intro2_VoiceFileNames[a][0]))
            elif os.path.exists(VoiceLayerPathGen(projectName, email, _Intro2_VoiceFileNames[a][1])):
                _Intro2_Voice = AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, _Intro2_VoiceFileNames[a][1]))
            _Intro2_Audio += _Intro2_Voice + AudioSegment.silent(duration = ActorChunk[a]['Pause'] * 1000)
    ## _Intro2_가 Title앞에 존재하는 경우 ##

    TitleMusic_Audio = MusicsVolume(TitleMusicPath, Volume)
    PartMusic_Audio = MusicsVolume(PartMusicPath, Volume)
    ChapterMusic_Audio = MusicsVolume(ChapterMusicPath, Volume)
    IndexMusic_Audio = MusicsVolume(IndexMusicPath, Volume)
    CaptionMusic_Audio = MusicsVolume(CaptionMusicPath, Volume)
    
    ### 초기화: Mixed Audio누적 추가 시간 생성 ###
    MixedMusicAudio = Logo_Audio + Intro_Audio + _Intro2_Audio
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
            Pause = MusicMixingData['Pause']
            # 파일 선별
            TitleVoice = AudioSegment.empty()
            if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[0]))) and ('M' in VoiceFileNames[0]):
                M_Switch = 1
            else:
                M_Switch = 0
            for j in range(len(VoiceFileNames)):
                if M_Switch == 1:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' in VoiceFileNames[j]):
                        TitleVoice += (AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j])) + AudioSegment.silent(duration = Pause * 1000))
                        LastVoiceFileName = VoiceFileNames[j]
                else:
                    if (os.path.exists(VoiceLayerPathGen(projectName, email, VoiceFileNames[j]))) and ('M' not in VoiceFileNames[j]):
                        TitleVoice += (AudioSegment.from_wav(VoiceLayerPathGen(projectName, email, VoiceFileNames[j])) + AudioSegment.silent(duration = Pause * 1000))
                        LastVoiceFileName = VoiceFileNames[j]
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
    # 볼륨을 5dB 낮춤
    MixedTitleEndMusicAudio = MixedTitleEndMusicAudio - 5
    
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
                
                # 목소리가 남는 경우 처리
                ExtraSoundDuration = len(PartMusic_Audio) - Length[0] * 1000
                if len(PartVoice) > ExtraSoundDuration:
                    ExtraPartVoiceLength = len(PartVoice) - ExtraSoundDuration
                    ExtraPartVoice = PartVoice[-ExtraPartVoiceLength:]
                    MixedMusicAudio += ExtraPartVoice
                    
            else:
                _PartVoice = AudioSegment.silent(duration = Length[0] * 1000) + PartVoice
                MixedMusicAudio = _PartVoice.overlay(PartMusic_Audio, position = 0)
                
                # 음악이 남는 경우 처리
                if len(PartMusic_Audio) > len(_PartVoice):
                    ExtraSoundDuration = len(PartMusic_Audio) - len(_PartVoice)
                    ExtraPartMusic = PartMusic_Audio[-ExtraSoundDuration:]
                    MixedMusicAudio += ExtraPartMusic
                    
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
                
                # 목소리가 남는 경우 처리
                ExtraSoundDuration = len(ChapterMusic_Audio) - Length[0] * 1000
                if len(ChapterVoice) > ExtraSoundDuration:
                    ExtraChapterVoiceLength = len(ChapterVoice) - ExtraSoundDuration
                    ExtraChapterVoice = ChapterVoice[-ExtraChapterVoiceLength:]
                    MixedMusicAudio += ExtraChapterVoice
                    
            else:
                _ChapterVoice = AudioSegment.silent(duration = Length[0] * 1000) + ChapterVoice
                MixedMusicAudio = _ChapterVoice.overlay(ChapterMusic_Audio, position = 0)
                
                # 음악이 남는 경우 처리
                if len(ChapterMusic_Audio) > len(_ChapterVoice):
                    ExtraSoundDuration = len(ChapterMusic_Audio) - len(_ChapterVoice)
                    ExtraChapterMusic = ChapterMusic_Audio[-ExtraSoundDuration:]
                    MixedMusicAudio += ExtraChapterMusic
                
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
                
                # 목소리가 남는 경우 처리
                ExtraSoundDuration = len(IndexMusic_Audio) - Length[0] * 1000
                if len(IndexVoice) > ExtraSoundDuration:
                    ExtraIndexVoiceLength = len(IndexVoice) - ExtraSoundDuration
                    ExtraIndexVoice = IndexVoice[-ExtraIndexVoiceLength:]
                    MixedMusicAudio += ExtraIndexVoice
                
            else:
                _IndexVoice = AudioSegment.silent(duration = Length[0] * 1000) + IndexVoice
                MixedMusicAudio = _IndexVoice.overlay(IndexMusic_Audio, position = 0)
                
                # 음악이 남는 경우 처리
                if len(IndexMusic_Audio) > len(_IndexVoice):
                    ExtraSoundDuration = len(IndexMusic_Audio) - len(_IndexVoice)
                    ExtraIndexMusic = IndexMusic_Audio[-ExtraSoundDuration:]
                    MixedMusicAudio += ExtraIndexMusic
                
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
                
                # 목소리가 남는 경우 처리
                ExtraSoundDuration = len(CaptionMusic_Audio) - Length[0] * 1000
                if len(CaptionVoice) > ExtraSoundDuration:
                    ExtraCaptionVoiceLength = len(CaptionVoice) - ExtraSoundDuration
                    ExtraCaptionVoice = CaptionVoice[-ExtraCaptionVoiceLength:]
                    MixedMusicAudio += ExtraCaptionVoice
                
            else:
                _CaptionVoice = AudioSegment.silent(duration = Length[0] * 1000) + CaptionVoice
                MixedMusicAudio = _CaptionVoice.overlay(CaptionMusic_Audio, position = 0)
                
                # 음악이 남는 경우 처리
                if len(CaptionMusic_Audio) > len(_CaptionVoice):
                    ExtraSoundDuration = len(CaptionMusic_Audio) - len(_CaptionVoice)
                    ExtraCaptionMusic = CaptionMusic_Audio[-ExtraSoundDuration:]
                    MixedMusicAudio += ExtraCaptionMusic
                
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

## 파일과 Edit간 불일치시 FilteredFiles 재구성
def MatchEditWithVoiceFile(EditGeneration, FilteredFiles):
    MatchedFilteredFiles = []
    for Edit in EditGeneration:
        EditId = Edit['EditId']
        ActorChunk = Edit['ActorChunk']
        for ChunkId in range(len(ActorChunk)):
            EditIdText = f'_{EditId}_'
            ChunkIdText = f'({ChunkId})'
            
            for file in FilteredFiles:
                if EditIdText in file and ChunkIdText in file:
                    MatchedFilteredFiles.append(file)
                    FilteredFiles.pop(0)
                    break
    
    return MatchedFilteredFiles

## 생성된 음성파일 합치기
def MusicSelector(projectName, email, CloneVoiceName = "저자명", MainLang = 'Ko', Intro = 'off'):
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
    MusicFilePattern = r".*?_(\d+(?:\.\d+)?)_([가-힣]+\(.*?\))_\((\d+)\)M?_([^\.]+)\.wav"
    for i in range(len(MusicRawFiles)):
        MusicFileMatch = re.match(MusicFilePattern, MusicRawFiles[i])
        if MusicFileMatch == None:
            normalizeMusicRawFile = unicodedata.normalize('NFC', MusicRawFiles[i])
            MusicFileMatch = re.match(MusicFilePattern, normalizeMusicRawFile)
        
        if MusicFileMatch:
            chunkid, actorname, _, tagmusic = MusicFileMatch.groups()
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

    # 목차 단위로 나누기 위한 FileLimitList 만들기
    IndexsTags = ['Part', 'Chapter', 'Index']
    FileLimitList = []
    Second = 0
    LastSplitSecond = 0
    LastValidEditId = None # 1시간을 초과하기 전의 마지막 유효한 EditId를 추적
    EditEndTimes = [] # 각 파일 끝 시간을 기록하기 위한 리스트

    for edit in EditGeneration:
        EditId = edit['EditId']
        Tag = edit['Tag']
        if edit['ActorChunk'][-1]['EndTime']['Second'] is not None:
            Second = edit['ActorChunk'][-1]['EndTime']['Second']
        
        # 'Part', 'Chapter', 'Index' 태그가 있는지 확인하고, 누적 시간을 추적합니다.
        if Tag in IndexsTags:
            if Second - LastSplitSecond < 3600:  # 60분을 아직 초과하지 않은 경우
                LastValidEditId = EditId  # 현재 EditId를 유효한 분할 후보로 업데이트
            else:  # 60분을 초과하는 경우
                if LastValidEditId is not None:
                    FileLimitList.append(LastValidEditId - 1)  # 마지막 유효한 분할 지점을 추가
                    EditEndTimes.append(Second)  # 파일 끝 시간 기록
                    LastSplitSecond = Second  # 마지막 분할 지점을 현재 초과 지점으로 업데이트
                    LastValidEditId = EditId  # 현재 EditId를 새로운 유효한 후보로 설정

    # 마지막 파일 합성1: 마지막으로 남은 분할 후보가 10분 이상일 경우 추가
    if (Second - LastSplitSecond > 600) and (LastValidEditId is not None and LastValidEditId not in FileLimitList):
        FileLimitList.append(LastValidEditId - 1)
        EditEndTimes.append(Second)  # 마지막 파일 끝 시간 추가
        
    # 마지막 파일 합성2: 뒷부분 2개의 파일의 시간 합이 70분 이하일 경우 두 파일
    if len(EditEndTimes) > 1 and (EditEndTimes[-1] - EditEndTimes[-2] <= 4000):
        FileLimitList.pop()
    
    # 마지막 파일 합성3: 파일의 길이가 짧아서 오디오북이 총 1시간이 안되는 경우 마지막 번호 추가
    if FileLimitList == []:
        FileLimitList.append(EditId)

    ## _Speed.wav 파일 생성 (Clone Voice 속도 조절시) ##
    # Speed 변수 가져오기
    MatchedActorsfileName = projectName + '_' + 'MatchedVoices.json'
    MatchedActorsPath = VoiceLayerPathGen(projectName, email, MatchedActorsfileName, 'Mixed')
    with open(MatchedActorsPath, 'r', encoding = 'utf-8') as MatchedActorsJson:
        MatchedActors = json.load(MatchedActorsJson)

    CloneVoiceSpeed = 1
    CloneVoicePitch = 0
    for MatchedActor in MatchedActors:
        if (CloneVoiceName in MatchedActor['ActorName']) and (projectName in MatchedActor['ActorName']):
            CloneVoiceSpeed = MatchedActor['ApiSetting']['Speed']
            CloneVoicePitch =  MatchedActor['ApiSetting']['Pitch']
    
    # Speed 변수가 1이 아닌 경우 속도 조절
    if CloneVoiceSpeed != 1 or CloneVoicePitch != 0:
        
        UpdateTQDM = tqdm(FilteredFiles,
                        total = len(FilteredFiles),
                        desc = 'CloneVoiceSpeed & Pitch')
        
        _SpeedRemoveList = []
        for Update in UpdateTQDM:
            if ('_[' not in Update) and (CloneVoiceName in Update):
                VoiceFilePath = os.path.join(voiceLayerPath, Update)
                _SpeedFilePath = VoiceFilePath.replace('.wav', '_Speed.wav')
                if os.path.exists(_SpeedFilePath):
                    os.remove(_SpeedFilePath)
                
                tfm = sox.Transformer()
                if CloneVoicePitch != 1:
                    tfm.tempo(CloneVoiceSpeed, 's')
                if CloneVoicePitch != 0:
                    tfm.pitch(CloneVoicePitch)
                tfm.build(VoiceFilePath, _SpeedFilePath)
                
                _SpeedRemoveList.append(_SpeedFilePath)
    ## _Speed.wav 파일 생성 (Clone Voice 속도 조절시) ##

    ## 파일과 Edit간 불일치시 FilteredFiles 재구성
    FilteredFiles = MatchEditWithVoiceFile(EditGeneration, FilteredFiles)

    # 오디오북 생성
    EditGenerationKoChunks = EditGenerationKoChunksToList(EditGeneration)
    FilesCount = 0
    SplitCount = 0
    CombinedSize = 0
    CombinedCount = 0
    CombinedSoundFilePaths = []
    RawPreviewSound = None
    FileRunningTimeList = []

    ## _Intro2_가 Title앞에 존재하는 경우 ##
    if EditGenerationKoChunks[0]['Tag'] == 'Intro':
        CombinedSound = AudioSegment.from_wav(os.path.join(musicLayerPath, FilteredFiles[1]))
        FilteredFiles = FilteredFiles[2:]
    ## _Intro2_가 Title앞에 존재하는 경우 ##
    else:
        CombinedSound = AudioSegment.from_wav(os.path.join(musicLayerPath, FilteredFiles[0]))
        FilteredFiles = FilteredFiles[1:]
    CombinedSounds = AudioSegment.empty()
    total_duration_seconds = CombinedSound.duration_seconds

    UpdateTQDM = tqdm(EditGenerationKoChunks[1:],
                    total = len(EditGenerationKoChunks[1:]),
                    desc = 'MusicGenerator')

    # 전체 오디오 클립의 누적 길이를 추적하는 변수 추가
    for Update in UpdateTQDM:
        EditId = Update['EditId']
        Tag = Update['Tag']
        # if EditId in [1, 2, 3, 4, 5, 6]: ######
        #     print(f'------------------\n------------------\nUpdate: {Update}') ######
        ActorChunk = Update['ActorChunk']
        for _chunknum in range(len(ActorChunk)):
            if len(FilteredFiles) > FilesCount:
                # Pause의 개수 설정 (실제 파일개수와 Puase 개수를 일치화)
                PauseSearchFileName = f"{projectName}_{Update['EditId']}_{Update['ActorName']}_("
                PauseNum = 0
                for FileName in FilteredFiles:
                    if PauseSearchFileName in FileName:
                        PauseNum += 1
                    if (PauseNum > 0) and (PauseSearchFileName not in FileName):
                        break
                if EditId == 2 and Tag in ['Narrator', 'Caption']:
                    SlicePause = Update['Pause'][len(ActorChunk) - PauseNum:]
                else:
                    SlicePause = Update['Pause'][-PauseNum:]
                
                # 일치하는 파일이름으로 해당 파일 믹싱 (Pause 설정 및 EndTime 기록 등)
                ProcessFileName = f"{projectName}_{Update['EditId']}_{Update['ActorName']}_({_chunknum})"
                if ProcessFileName in FilteredFiles[FilesCount]:
                    # print(f'FilteredFiles[FilesCount]: {FilteredFiles[FilesCount]}')
                    # print(f'ProcessFileName: {ProcessFileName}')
                    Update['EndTime'] = []
                    # Index 구분 (EndTime 중복 방지)
                    PauseCount = None
                    if '_[' in FilteredFiles[FilesCount]:
                        Pause = [SlicePause[-1]]
                        PauseCount = len(SlicePause)
                    else:
                        Pause = SlicePause
                    # print(f'Pause: {len(ActorChunk)}, {PauseNum}, {Pause}\n\n')
                    for _pausenum in range(len(Pause)):
                        if len(FilteredFiles) > FilesCount:
                            if '_[' in FilteredFiles[FilesCount]:
                                _VoiceFilePath = os.path.join(musicLayerPath, FilteredFiles[FilesCount])
                                with open(_VoiceFilePath, 'rb') as _mVoiceFile:
                                    sound_file = AudioSegment.from_wav(_mVoiceFile)
                            else:
                                _VoiceFilePath = os.path.join(voiceLayerPath, FilteredFiles[FilesCount])
                                with open(_VoiceFilePath, 'rb') as mVoiceFile:
                                    sound_file = AudioSegment.from_wav(mVoiceFile)
                            
                            # CloneVoice의 끊어읽기 시간을 고려해서 CloneVoice Puase시간 추가
                            AddPause = 0
                            if (CloneVoiceName in FilteredFiles[FilesCount]) and (_pausenum == len(Pause)-1):
                                AddPause = 0.3
                            PauseDuration_ms = (Pause[_pausenum] + AddPause) * 1000
                            # if EditId in [1, 2, 3, 4, 5, 6]: ######
                            #     print(f'{EditId}, {FilteredFiles[FilesCount]}, {SlicePause}, {PauseNum}, {Pause}, {FilesCount} : {PauseDuration_ms}') ######
                            silence = AudioSegment.silent(duration = PauseDuration_ms)
                            
                            ## _Speed.wav 파일 선택 (Clone Voice 속도 조절시) ##
                            if CloneVoiceSpeed != 1:
                                if ('_[' not in FilteredFiles[FilesCount]) and (Tag in ['Narrator', 'Caption']) and (CloneVoiceName in FilteredFiles[FilesCount]):
                                    # Caption의 경우 첫번째 제목 부분은 음성 속도를 원래대로
                                    if not (Tag == 'Caption' and _pausenum == 0):
                                        _VoiceFilePath = os.path.join(voiceLayerPath, FilteredFiles[FilesCount])
                                        _SpeedFilePath = _VoiceFilePath.replace('.wav', '_Speed.wav')
                                        # Voice 속도를 빠르게
                                        sound_file = AudioSegment.from_wav(_SpeedFilePath)
                                        # Pause 속도를 빠르게
                                        PauseDuration_ms = PauseDuration_ms/CloneVoiceSpeed
                                        silence = AudioSegment.silent(duration = PauseDuration_ms)
                            ## _Speed.wav 파일 선택 (Clone Voice 속도 조절시) ##
                            
                            CombinedSound += sound_file + silence
                            CombinedSize += 1
                            FilesCount += 1
                            
                            # 100개 단위로 CombinedSound 분할 합성
                            if CombinedSize == 100:
                                CombinedSoundFileName = f"{projectName}_MusicLayer_({CombinedCount}).wav"
                                CombinedCount += 1
                                CombinedSoundFilePath = MusicLayerPathGen(projectName, email, CombinedSoundFileName)
                                CombinedSoundFilePaths.append(CombinedSoundFilePath)
                                CombinedSound.export(CombinedSoundFilePath, format = "wav")
                                CombinedSound = AudioSegment.empty()
                                CombinedSize = 0

                            # 누적된 CombinedSound의 길이를 전체 길이 추적 변수에 추가
                            total_duration_seconds += sound_file.duration_seconds + PauseDuration_ms / 1000.0
                            # EndTime에는 누적된 전체 길이를 저장
                            
                            ## EndTime 시간 저장(Index와 Non Index 구분)
                            if PauseCount:
                                for i in range(PauseCount - 1):
                                    Update['EndTime'].append({"Time": None, "Second": None})
                            # # 디버깅 모드
                            # Update['EndTime'].append({"PauseId": _pausenum + 1, "Time": SecondsToHMS(total_duration_seconds), "Second": total_duration_seconds})
                            Update['EndTime'].append({"Time": SecondsToHMS(total_duration_seconds), "Second": total_duration_seconds})

            # 파일 단위로 저장 및 CombinedSound 초기화
            if (EditId == FileLimitList[SplitCount]) and (_chunknum == len(ActorChunk) - 1):
                if CombinedSize > 0:
                    CombinedSoundFileName = f"{projectName}_MusicLayer_({CombinedCount}).wav"
                    CombinedCount += 1
                    CombinedSoundFilePath = MusicLayerPathGen(projectName, email, CombinedSoundFileName)
                    CombinedSoundFilePaths.append(CombinedSoundFilePath)
                    CombinedSound.export(CombinedSoundFilePath, format = "wav")
                    CombinedSound = AudioSegment.empty()
                    CombinedSize = 0
                
                for FilePath in CombinedSoundFilePaths:
                    TempSound = AudioSegment.from_mp3(FilePath)
                    CombinedSounds += TempSound
                    os.remove(FilePath)

                MasterLayerPath = VoiceLayerPathGen(projectName, email, f"{projectName}_AudioBook_({SplitCount + 1}).mp3", 'Master')
                
                # 첫번째 파일이 미리듣기 파일
                if RawPreviewSound == None:
                    RawPreviewSound = CombinedSounds
                    PreviewSoundPath = MasterLayerPath.replace('_(1).mp3', '_(Preview).mp3')
                
                try:
                    with open(MasterLayerPath, "wb") as MVoiceFile:
                        CombinedSounds.export(MVoiceFile, format = "mp3", bitrate = "320k")
                        FileRunningTimeList.append(CombinedSounds.duration_seconds)
                        CombinedSounds = AudioSegment.empty()
                    # struct.error: 'L' format requires 0 <= number <= 4294967295 에러 방지 (4GB 용량 문제 방지)
                except:
                    CombinedSoundsPart1 = CombinedSounds[:len(CombinedSounds)//2]
                    CombinedSoundsPart2 = CombinedSounds[len(CombinedSounds)//2:]
                    CombinedSounds = AudioSegment.empty()
                    
                    CombinedSoundsPart1Path = MasterLayerPath.replace(".mp3", "part1.mp3")
                    with open(CombinedSoundsPart1Path, "wb") as P1MVoiceFile:
                        print(f"[ 대용량 파일 분할 저장: {CombinedSoundsPart1Path} ]")
                        CombinedSoundsPart1.export(P1MVoiceFile, format = "mp3", bitrate = "320k")
                        CombinedSoundsPart1 = AudioSegment.from_file(CombinedSoundsPart1Path)
                        CombinedSounds += CombinedSoundsPart1
                        CombinedSoundsPart1 = AudioSegment.empty()
                    os.remove(CombinedSoundsPart1Path)
                    
                    CombinedSoundsPart2Path = MasterLayerPath.replace(".mp3", "part2.mp3")
                    with open(CombinedSoundsPart2Path, "wb") as P2MVoiceFile:
                        print(f"[ 대용량 파일 분할 저장: {CombinedSoundsPart2Path} ]")
                        CombinedSoundsPart2.export(P2MVoiceFile, format = "mp3", bitrate = "320k")
                        CombinedSoundsPart2 = AudioSegment.from_file(CombinedSoundsPart2Path)
                        CombinedSounds += CombinedSoundsPart2
                        CombinedSoundsPart2 = AudioSegment.empty()
                    os.remove(CombinedSoundsPart2Path)
                    
                    with open(MasterLayerPath, "wb") as MVoiceFile:
                        CombinedSounds.export(MVoiceFile, format = "mp3", bitrate = "320k")
                        FileRunningTimeList.append(CombinedSounds.duration_seconds)
                        CombinedSounds = AudioSegment.empty()

                CombinedSoundFilePaths = []
                if SplitCount < len(FileLimitList) - 1:
                    SplitCount += 1
                    
    # for 루프 종료 후 남은 CombinedSound 처리 (특수경우)
    if (not CombinedSound.empty()) and (int(CombinedSound.duration_seconds) >= 1):
        if CombinedSize > 0:
            CombinedSoundFileName = f"{projectName}_MusicLayer_({CombinedCount}).wav"
            CombinedCount += 1
            CombinedSoundFilePath = MusicLayerPathGen(projectName, email, CombinedSoundFileName)
            CombinedSoundFilePaths.append(CombinedSoundFilePath)
            CombinedSound.export(CombinedSoundFilePath, format = "wav")
            CombinedSound = AudioSegment.empty()
            CombinedSize = 0
        
        for FilePath in CombinedSoundFilePaths:
            TempSound = AudioSegment.from_mp3(FilePath)
            CombinedSounds += TempSound
            os.remove(FilePath)

        MasterLayerPath = VoiceLayerPathGen(projectName, email, f"{projectName}_AudioBook_({SplitCount + 2}).mp3", 'Master')
        
        # 첫번째 파일이 미리듣기 파일
        if RawPreviewSound == None:
            RawPreviewSound = CombinedSounds
            PreviewSoundPath = MasterLayerPath.replace('(1).mp3', '(Preview).mp3')
        
        try:
            with open(MasterLayerPath, "wb") as MVoiceFile:
                CombinedSounds.export(MVoiceFile, format = "mp3", bitrate = "320k")
                FileRunningTimeList.append(CombinedSounds.duration_seconds)
                CombinedSounds = AudioSegment.empty()
            # struct.error: 'L' format requires 0 <= number <= 4294967295 에러 방지 (4GB 용량 문제 방지)
        except:
            CombinedSoundsPart1 = CombinedSounds[:len(CombinedSounds)//2]
            CombinedSoundsPart2 = CombinedSounds[len(CombinedSounds)//2:]
            CombinedSounds = AudioSegment.empty()
            
            CombinedSoundsPart1Path = MasterLayerPath.replace(".mp3", "_Part1.mp3")
            with open(CombinedSoundsPart1Path, "wb") as P1MVoiceFile:
                print(f"[ 대용량 파일 분할 저장: {CombinedSoundsPart1Path} ]")
                CombinedSoundsPart1.export(P1MVoiceFile, format = "mp3", bitrate = "320k")
                CombinedSoundsPart1 = AudioSegment.from_file(CombinedSoundsPart1Path)
                CombinedSounds += CombinedSoundsPart1
                CombinedSoundsPart1 = AudioSegment.empty()
            os.remove(CombinedSoundsPart1Path)
            
            CombinedSoundsPart2Path = MasterLayerPath.replace(".mp3", "_Part2.mp3")
            with open(CombinedSoundsPart2Path, "wb") as P2MVoiceFile:
                print(f"[ 대용량 파일 분할 저장: {CombinedSoundsPart2Path} ]")
                CombinedSoundsPart2.export(P2MVoiceFile, format = "mp3", bitrate = "320k")
                CombinedSoundsPart2 = AudioSegment.from_file(CombinedSoundsPart2Path)
                CombinedSounds += CombinedSoundsPart2
                CombinedSoundsPart2 = AudioSegment.empty()
            os.remove(CombinedSoundsPart2Path)
            
            with open(MasterLayerPath, "wb") as MVoiceFile:
                CombinedSounds.export(MVoiceFile, format = "mp3", bitrate = "320k")
                FileRunningTimeList.append(CombinedSounds.duration_seconds)
                CombinedSounds = AudioSegment.empty()

        CombinedSoundFilePaths = []

    ## _Speed.wav 파일 모두 삭제 (Clone Voice 속도 조절시) ##
    if CloneVoiceSpeed != 1:
        for _SpeedFile in _SpeedRemoveList:
            os.remove(_SpeedFile)
    ## _Speed.wav 파일 모두 삭제 (Clone Voice 속도 조절시) ##
        
    ## EditGenerationKoChunks의 Dic(검수)
    EditGenerationKoChunks = EditGenerationKoChunksToDic(EditGenerationKoChunks)
    
    ## TitleMusic 최종 시간 자리 수정
    ## _Intro2_가 Title앞에 존재하는 경우 ##
    if EditGenerationKoChunks[0]['Tag'] == 'Intro':
        for i in range(len(EditGenerationKoChunks[0]['ActorChunk'])):
            EditGenerationKoChunks[0]['ActorChunk'][i]['EndTime'] = {"Time": None, "Second": None}
            
        TitleSectionEditGenerationKo = EditGenerationKoChunks[2]
    ## _Intro2_가 Title앞에 존재하는 경우 ##
    else:
        TitleSectionEditGenerationKo = EditGenerationKoChunks[1]
    NoneEndTimes = []
    nonNoneEndTimes = []
    
    for i in range(len(TitleSectionEditGenerationKo['ActorChunk'])):
        if TitleSectionEditGenerationKo['ActorChunk'][i]['EndTime'] is None:
            NoneEndTimes.append(TitleSectionEditGenerationKo['ActorChunk'][i]['EndTime'])
        else:
            nonNoneEndTimes.append(TitleSectionEditGenerationKo['ActorChunk'][i]['EndTime'])
    EndTimes = NoneEndTimes + nonNoneEndTimes
    
    for i in range(len(TitleSectionEditGenerationKo['ActorChunk'])):
        TitleSectionEditGenerationKo['ActorChunk'][i]['EndTime'] = EndTimes[i]
    
    ## _Intro2_가 Title앞에 존재하는 경우 ##
    if EditGenerationKoChunks[0]['Tag'] == 'Intro':
        EditGenerationKoChunks[2] = TitleSectionEditGenerationKo
    ## _Intro2_가 Title앞에 존재하는 경우 ##
    else:
        EditGenerationKoChunks[1] = TitleSectionEditGenerationKo
    
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

    ## Title이 여러개인 경우 최종시간 ##
    if EditGenerationKoChunks[0]['Tag'] == 'Title':
        for i in range(len(EditGenerationKoChunks[0]['ActorChunk'])):
            EditGenerationKoChunks[0]['ActorChunk'][i]['EndTime'] = {"Time": None, "Second": None}

    # MatchedChunksEdit 경로 생성
    fileName = '[' + projectName + '_' + 'AudioBook_Edit].json'
    MatchedChunksPath = VoiceLayerPathGen(projectName, email, fileName, Folder = 'Master')

    ## EndTime이 업데이트 된 EditGenerationKoChunks 저장
    with open(MatchedChunksPath, 'w', encoding = 'utf-8') as json_file:
        json.dump(EditGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)

    return EditGenerationKoChunks, FileLimitList, FileRunningTimeList, RawPreviewSound, PreviewSoundPath, _VoiceFilePath

## 10-15분 미리듣기 생성 ##
def AudiobookPreviewGen(EditGenerationKoChunks, RawPreviewSound, PreviewSoundPath):
    if RawPreviewSound.duration_seconds >= 900:
        PreviewSecond = 0
        for i in range(len(EditGenerationKoChunks)):
            Second = EditGenerationKoChunks[i]['ActorChunk'][-1]['EndTime']['Second']
            if Second is not None:
                if Second > 900:
                    break
                elif 600 <= Second <= 900:
                    PreviewSecond = Second
                    try:
                        if EditGenerationKoChunks[i+1]['Tag'] in ['Logue', 'Part', 'Chapter', 'Index']:
                            break
                    except IndexError:
                        break
    
        if PreviewSecond != 0:
            PreviewSound = RawPreviewSound[:PreviewSecond * 1000 + 50]
            
            with open(PreviewSoundPath, "wb") as PreviewFile:
                PreviewSound.export(PreviewFile, format = "mp3", bitrate = "320k")
                PreviewSound = AudioSegment.empty()
        
        RawPreviewSound = AudioSegment.empty()

## 오디오북 메타데이터 생성 ##
def AudiobookMetaDataGen(projectName, email, EditGenerationKoChunks, FileLimitList, FileRunningTimeList, VoiceFilePath):
    
    # 시간, 분, 초로 변환
    def SecondsToHMS(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    MetaDataSet = [{'ProjectName': projectName, 'RunningTime': SecondsToHMS(sum(FileRunningTimeList))}]
    
    IndexTag = EditGenerationKoChunks[0]['Tag']
    IndexTitles = []
    for ActorChunk in EditGenerationKoChunks[0]['ActorChunk']:
        Chunk = ActorChunk['Chunk']
        IndexTitles.append(Chunk.replace('.', '').replace(',', '').replace('~', ''))
    IndexTitle = ' '.join(IndexTitles)
    
    if len(FileLimitList) > 1:
        for i in range(len(FileLimitList)):
            for j in range(len(EditGenerationKoChunks)):
                if FileLimitList[i] == EditGenerationKoChunks[j]['EditId']:
                                
                    MetaData = {'FileId': i+1, 'Index': IndexTag, 'IndexTitle': IndexTitle, 'RunningTime': SecondsToHMS(FileRunningTimeList[i])}
                    MetaDataSet.append(MetaData)
                    
                    # IndexTitle
                    IndexTag = EditGenerationKoChunks[j+1]['Tag']
                    IndexTitles = []
                    for ActorChunk in EditGenerationKoChunks[j+1]['ActorChunk']:
                        Chunk = ActorChunk['Chunk']
                        IndexTitles.append(Chunk.replace('.', '').replace(',', '').replace('~', ''))
                    IndexTitle = ' '.join(IndexTitles)
        try:
            MetaData = {'FileId': i+2, 'Index': IndexTag, 'IndexTitle': IndexTitle, 'RunningTime': SecondsToHMS(FileRunningTimeList[i+1])}
            MetaDataSet.append(MetaData)
        except:
            sys.exit(f'[ (FileRunningTimeList: {FileRunningTimeList}), (LastVoiceFilePath: {VoiceFilePath}) ]\n[ 해당 EditId 이후 파일 삭제 요망, Edit과 VoiceLayer 음성.wav 파일간에 불일치 확인 ]')

    fileName = '[' + projectName + '_' + 'AudioBook_MetaDate].json'
    MetaDatePath = VoiceLayerPathGen(projectName, email, fileName, Folder = 'Master')

    with open(MetaDatePath, 'w', encoding = 'utf-8') as json_file:
        json.dump(MetaDataSet, json_file, ensure_ascii = False, indent = 4)

## 프롬프트 요청 및 결과물 Json을 MusicLayer에 업데이트
def MusicLayerUpdate(projectName, email, CloneVoiceName = "저자명", MainLang = 'Ko', Intro = 'off'):
    print(f"< User: {email} | Project: {projectName} | MusicLayerGenerator 시작 >")
    
    EditGenerationKoChunks, FileLimitList, FileRunningTimeList, RawPreviewSound, PreviewSoundPath, _VoiceFilePath = MusicSelector(projectName, email, CloneVoiceName = CloneVoiceName, MainLang = MainLang, Intro = Intro)
    
    ## 10-15분 미리듣기 생성
    AudiobookPreviewGen(EditGenerationKoChunks, RawPreviewSound, PreviewSoundPath)
    
    ## 오디오북 메타데이터 생성
    AudiobookMetaDataGen(projectName, email, EditGenerationKoChunks, FileLimitList, FileRunningTimeList, _VoiceFilePath)

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