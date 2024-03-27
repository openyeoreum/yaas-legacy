import os
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
    voiceLayerPath = os.path.join(BasePath, UserFolderName, StorageFolderName, projectName, f"{projectName}_master_audiobook_file", FileName)
    # print(voiceLayerPath)

    return voiceLayerPath

############################
##### MusicMatched 생성 #####
############################
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
def MusicMatchedSelectionGenerationChunks(projectName, email, MainLang = 'Ko', Intro = "off"):
    ## VoiceLayerPath 찾기
    FileName = f'{projectName}_AudioBook.wav'
    VoiceLayerPath = VoiceLayerPathGen(projectName, email, FileName)

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
        
    return EditGeneration, VoiceLayerPath, MatchedMusics

################################################
##### VoiceLayer에 Logo, Intro, Music 합치기 #####
################################################
## VoiceLayer에 Musics 믹싱
def MusicsMixing(projectName, email, MainLang = 'Ko', Intro = "off"):
    
    EditGeneration, VoiceLayerPath, MatchedMusics = MusicMatchedSelectionGenerationChunks(projectName, email, MainLang = 'Ko', Intro = "off")
    
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
    MusicMixingDataDic = None
    StartTime = 0
    for i in range(len(EditGeneration)):
        if i > 0:
            BeforeTag = EditGeneration[i-1]['Tag']
            StartTime = EditGeneration[i-1]['ActorChunk'][-1]['EndTime']['Second']
        
        EditId = EditGeneration[i]['EditId']
        Tag = EditGeneration[i]['Tag']
        EndTime = EditGeneration[i]['ActorChunk'][-1]['EndTime']['Second']
        
        if Tag == 'Title':
            TitleMusicMixingDataDics = [{'EditId': EditId, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime - 2, 'Music': TitleMusic}]
            EditGeneration[i]['Logo'] = Logo
            EditGeneration[i]['Intro'] = Intro
            EditGeneration[i]['Music'] = TitleMusic
            if EditGeneration[i+1]['Tag'] == 'Narrator' and EditGeneration[i+2]['Tag'] in ['Logue', 'Part', 'Chapter', 'Index']:
                TitleActorChunks = EditGeneration[i+1]['ActorChunk']
                StartTime = EndTime
                AddId = 1
                for j in range(min(len(TitleActorChunks), 2)):
                    EndTime = TitleActorChunks[j]['EndTime']['Second']
                    TitleMusicMixingDataDic = {'EditId': EditId + AddId, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime, 'Music': TitleMusic}
                    TitleMusicMixingDataDics.append(TitleMusicMixingDataDic)
                    AddId += 1
                    StartTime = EndTime
                MusicMixingDatas += TitleMusicMixingDataDics
                TitleMusicMixingDataDics = []
                continue

        elif Tag == 'Part':
            MusicMixingDataDic = {'EditId': EditId, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime, 'Music': PartMusic}
            EditGeneration[i]['Music'] = PartMusic
        elif Tag == 'Chapter':
            MusicMixingDataDic = {'EditId': EditId, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime, 'Music': ChapterMusic}
            EditGeneration[i]['Music'] = ChapterMusic
        elif Tag == 'Chapter':
            MusicMixingDataDic = {'EditId': EditId, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime, 'Music': IndexMusic}
            EditGeneration[i]['Music'] = IndexMusic
        elif (BeforeTag not in ['Caption', 'CaptionComment']) and (Tag == 'Caption'):
            MusicMixingDataDic = {'EditId': EditId, 'Tag': Tag, 'StartTime': StartTime, 'EndTime': EndTime, 'Music': CaptionMusic}
            EditGeneration[i]['Music'] = CaptionMusic
        
        if MusicMixingDataDic != None:
            MusicMixingDatas.append(MusicMixingDataDic)
        MusicMixingDataDic = None
        
    for data in MusicMixingDatas:
        print(f'{data}\n\n')
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
    
    ## 각 사운드 생성
    VoiceLayer = AudioSegment.from_wav(VoiceLayerPath)
    Logo_Sound = AudioSegment.from_wav(LogoPath) + AudioSegment.silent(duration = 2000)
    Intro_Sound = AudioSegment.empty()
    if IntroPath != None:
        Intro_Sound = AudioSegment.from_wav(IntroPath) + AudioSegment.silent(duration = 2000)
    TitleMusic_Sound = AudioSegment.from_wav(TitleMusicPath)
    PartMusic_Sound = AudioSegment.from_wav(PartMusicPath)
    ChapterMusic_Sound = AudioSegment.from_wav(ChapterMusicPath)
    IndexMusic_Sound = AudioSegment.from_wav(IndexMusicPath)
    CaptionMusic_Sound = AudioSegment.from_wav(CaptionMusicPath)
    
    ## 누적 추가 시간 생성
    AccumulatedTimesList = []
    
    ## Title 믹싱
    # TitleVoices 및 Setting
    TitleVoices = []
    for MusicMixingData in MusicMixingDatas:
        if MusicMixingData['Tag'] == 'Title':
            TitleVoices.append(VoiceLayer[MusicMixingData['StartTime'] * 1000:MusicMixingData['EndTime'] * 1000])
            print(MusicMixingData['Music']['Setting'])
            Length = MusicMixingData['Music']['Setting']['Length']
    # Mixing
    for i in range(len(TitleVoices)):
        print(TitleVoices[i])
        print(Length[i])
    # ## SoundMixing
    # # Load LogoSound
    # LogoSound = AudioSegment.from_file(LogoPath, format = "mp3")
    # # Logo Silence
    # Silence = AudioSegment.silent(duration = 2000)
    # # Logo Mixing, LogoSound와 공백음 4초 추가
    # LIMixingSound = LogoSound + Silence
    
    # LogoTag = ['Logo']
    # ## IntroSound
    # if IntroPath is not None:
    #     IntroSound = AudioSegment.from_file(IntroPath, format = "mp3")
    #     LIMixingSound += IntroSound + Silence
    #     LogoTag.append('Intro')
        
    # ## Load VoiceLayer_Logo 및 최종저장
    # # VoiceLayerSound = AudioSegment.from_file(VoiceLayerPath, format = "wav")
    # # LIMixingSound += VoiceLayerSound
    # LIMixingSound.export(VoiceLayerLogoPath, format = "wav")
    
    # ## VoiceLayer에 업데이트
    # # 시간, 분, 초로 변환
    # def SecondsToHMS(seconds):
    #     hours = seconds // 3600
    #     minutes = (seconds % 3600) // 60
    #     seconds = seconds % 60
        
    #     return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    # # 시간측정
    # LogoSecond = AudioSegment.from_file(VoiceLayerLogoPath)
    # LogoTime = SecondsToHMS(LogoSecond)
    # # LogoDic 생성
    # LogoEndTime = {"Time": LogoTime, "Second": LogoSecond}
    # LogoDic = [{'Tag': 'Logo', 'Logo': 'EndTime': [LogoEndTime]}]
    # # VoiceLayer EndTime 업데이트
    # for Voice in VoiceLayer:
    #     Voice['EndTime']
    
    

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "노인을위한나라는있다"
    mainLang = 'Ko'
    intro = "off" # Intro = ['한국출판문화산업진흥원' ...]
    #########################################################################
    
    MusicsMixing(projectName, email, MainLang = mainLang, Intro = intro)