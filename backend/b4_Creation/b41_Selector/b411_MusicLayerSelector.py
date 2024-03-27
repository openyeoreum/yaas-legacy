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
    voiceLayerPath = os.path.join(BasePath, UserFolderName, StorageFolderName, projectName, f"{projectName}_mixed_audiobook_file", "VoiceLayers", FileName)
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
    FileName = f'{projectName}_VoiceLayer_Logo.wav'
    VoiceLayerPath = VoiceLayerPathGen(projectName, email, FileName)

    ## MatchedMusics 파일 경로 생성
    fileName = '[' + projectName + '_' + 'MatchedMusics.json'
    MatchedMusicLayerPath = MusicLayerPathGen(projectName, email, fileName)
    
    if not os.path.exists(MatchedMusicLayerPath):
        SelectionGeneration, EditGeneration, LogoDataSet, IntroDataSet, TitleMusicDataSet, PartMusicDataSet, IndexMusicDataSet = LoadMusicDataSet(projectName, email, MainLang = MainLang)
        
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
                MatchedLogoDic = {'Type': 'Logo', 'FilePath': Logo['FilePath'], 'Setting': Logo['Setting']}
                break
        MatchedMusics.append(MatchedLogoDic)
        
        ## IntroDataSet에서 IntroPath 찾기
        MatchedIntroDic = {'Type': None, 'FilePath': None, 'Setting': None}
        if Intro != "off":
            for Intro in IntroDataSet:
                if (Intro['Intro']['Type'] == Intro) and (Intro['Intro']['Language'] == MainLang):
                    MatchedIntroDic = {'Type': 'Intro', 'FilePath': Intro['FilePath'], 'Setting': Intro['Setting']}
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
        MatchedTitleMusicDic = {'Type': 'TitleMusic', 'FilePath': MatchedTitleMusic['FilePath'], 'Setting': MatchedTitleMusic['Setting']}
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
        # PartMusic FilePath 도출
        MatchedPartMusic = PartMusicDataSet[PartMusicScoreList.index(max(PartMusicScoreList))]
        MatchedPartMusicDic = {'Type': 'PartMusic', 'FilePath': MatchedPartMusic['FilePath'], 'Setting': MatchedPartMusic['Setting']}
        MatchedMusics.append(MatchedPartMusicDic)
        
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
        MatchedIndexMusicDic = {'Type': 'IndexMusic', 'FilePath': MatchedIndexMusic['FilePath'], 'Setting': MatchedIndexMusic['Setting']}
        MatchedMusics.append(MatchedIndexMusicDic)
        # CaptionMusic
        MatchedCaptionMusic = IndexMusicDataSet[IndexMusicScoreList.index(SortedMatchedIndexScores[1])]
        MatchedCaptionMusicDic = {'Type': 'CaptionMusic', 'FilePath': MatchedCaptionMusic['FilePath'], 'Setting': MatchedCaptionMusic['Setting']}
        MatchedMusics.append(MatchedCaptionMusicDic)
        
        ## MatchedMusics 파일 생성
        with open(MatchedMusicLayerPath, 'w', encoding='utf-8') as MatchedMusicsJson:
            json.dump(MatchedMusics, MatchedMusicsJson, ensure_ascii=False, indent=4)
    else:
        with open(MatchedMusicLayerPath, 'r', encoding = 'utf-8') as MatchedMusicsJson:
            MatchedMusics = json.load(MatchedMusicsJson)
        
    return VoiceLayerPath, MatchedMusics

# ################################################
# ##### VoiceLayer에 Logo, Intro, Music 합치기 #####
# ################################################
# ## VoiceLayer에 Intro, Logo 믹싱
# def LogoIntroMixing(projectName, email, MainLang = 'Ko', Intro = "off"):
    
#     VoiceLayer, LogoPath, IntroPath, VoiceLayerLogoPath = MusicPathGen(projectName, email, MainLang = MainLang, Intro = Intro)
    
#     ## SoundMixing
#     # Load LogoSound
#     LogoSound = AudioSegment.from_file(LogoPath, format = "mp3")
#     # Logo Silence
#     Silence = AudioSegment.silent(duration = 2000)
#     # Logo Mixing, LogoSound와 공백음 4초 추가
#     LIMixingSound = LogoSound + Silence
    
#     LogoTag = ['Logo']
#     ## IntroSound
#     if IntroPath is not None:
#         IntroSound = AudioSegment.from_file(IntroPath, format = "mp3")
#         LIMixingSound += IntroSound + Silence
#         LogoTag.append('Intro')
        
#     ## Load VoiceLayer_Logo 및 최종저장
#     # VoiceLayerSound = AudioSegment.from_file(VoiceLayerPath, format = "wav")
#     # LIMixingSound += VoiceLayerSound
#     LIMixingSound.export(VoiceLayerLogoPath, format = "wav")
    
#     ## VoiceLayer에 업데이트
#     # 시간, 분, 초로 변환
#     def SecondsToHMS(seconds):
#         hours = seconds // 3600
#         minutes = (seconds % 3600) // 60
#         seconds = seconds % 60
        
#         return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
#     # 시간측정
#     LogoSecond = AudioSegment.from_file(VoiceLayerLogoPath)
#     LogoTime = SecondsToHMS(LogoSecond)
#     # LogoDic 생성
#     LogoEndTime = {"Time": LogoTime, "Second": LogoSecond}
#     LogoDic = [{'Tag': 'Logo', 'Logo': 'EndTime': [LogoEndTime]}]
#     # VoiceLayer EndTime 업데이트
#     for Voice in VoiceLayer:
#         Voice['EndTime']
    
    

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "노인을위한나라는있다"
    mainLang = 'Ko'
    intro = "off" # Intro = ['한국출판문화산업진흥원' ...]
    #########################################################################
    
    VoiceLayerPath, MatchedMusics = MusicMatchedSelectionGenerationChunks(projectName, email, MainLang = mainLang, Intro = intro)
    
    print(f'1: {MatchedMusics[0]}\n\n')
    print(f'2: {MatchedMusics[1]}\n\n')
    print(f'3: {MatchedMusics[2]}\n\n')
    print(f'4: {MatchedMusics[3]}\n\n')
    print(f'5: {MatchedMusics[4]}\n\n')
    print(f'6: {MatchedMusics[5]}\n\n')