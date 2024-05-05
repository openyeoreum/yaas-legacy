import os
import unicodedata
import json
import requests
import time
import random
import re
import copy
import shutil
import sox
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from time import sleep
from pydub import AudioSegment
from collections import defaultdict
from elevenlabs import Voice, VoiceSettings, save
from elevenlabs.client import ElevenLabs
from sqlalchemy.orm.attributes import flag_modified
from audoai.noise_removal import NoiseRemovalClient
from backend.b1_Api.b14_Models import User
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetSoundDataSet
from backend.b4_Creation.b42_Generator.b423_TypeCastWebMacro import TypeCastMacro
from backend.b4_Creation.b42_Generator.b424_VoiceSplit import VoiceSplit

###########################################
##### SelectionGenerationKoChunks 생성 #####
###########################################
## MainLang의 언어별 SelectionGenerationKoChunks와 Voicedataset 불러오기
def LoadVoiceDataSetCharacters(MainLang):
    
    # MainLang의 언어별 보이스 데이터셋 불러오기
    voiceDataSet = GetSoundDataSet("VoiceDataSet")
    VoiceDataSet = voiceDataSet[0][1]
    
    if MainLang == 'Ko':
        VoiceDataSetCharacters = VoiceDataSet['Characters' + MainLang][1:]
    if MainLang == 'En':
        VoiceDataSetCharacters = VoiceDataSet['Characters' + MainLang][1:]
    # if MainLang == 'Ja':
    #     VoiceDataSetCharacters = VoiceDataSet['Characters' + MainLang][1:]
    # if MainLang == 'Zh':
    #     VoiceDataSetCharacters = VoiceDataSet['Characters' + MainLang][1:]
    # if MainLang == 'Es':
    #     VoiceDataSetCharacters = VoiceDataSet['Characters' + MainLang][1:]
        
    return VoiceDataSetCharacters

## SelectionGenerationKoChunks와 언어별 보이스 데이터셋 불러오기
def LoadSelectionGenerationKoChunks(projectName, email, MainLang):

    VoiceDataSetCharacters = LoadVoiceDataSetCharacters(MainLang)
    
    project = GetProject(projectName, email)
    CharacterCompletion = project.CharacterCompletion[2]['CheckedCharacterTags'][1:]
    
    ## MainLang의 언어별 SelectionGenerationKoChunks 불러오기
    if MainLang == 'Ko':
        SelectionGenerationBookContext = project.SelectionGenerationKo[1]['SelectionGeneration' + MainLang + 'BookContext'][1]
        SelectionGenerationSplitedIndexs = project.SelectionGenerationKo[1]['SelectionGeneration' + MainLang + 'SplitedIndexs'][1:]
    if MainLang == 'En':
        SelectionGenerationBookContext = project.SelectionGenerationEn[1]['SelectionGeneration' + MainLang + 'BookContext'][1]
        SelectionGenerationSplitedIndexs = project.SelectionGenerationEn[1]['SelectionGeneration' + MainLang + 'SplitedIndexs'][1:]
    # if MainLang == 'Ja':
        # SelectionGenerationBookContext = project.SelectionGenerationJa[1]['SelectionGeneration' + MainLang + 'BookContext'][1]
        # SelectionGenerationSplitedIndexs = project.SelectionGenerationJa[1]['SelectionGeneration' + MainLang + 'SplitedIndexs'][1:]
    # if MainLang == 'Zh':
        # SelectionGenerationBookContext = project.SelectionGenerationZh[1]['SelectionGeneration' + MainLang + 'BookContext'][1]
        # SelectionGenerationSplitedIndexs = project.SelectionGenerationZh[1]['SelectionGeneration' + MainLang + 'SplitedIndexs'][1:]
    # if MainLang == 'Es':
        # SelectionGenerationBookContext = project.SelectionGenerationEs[1]['SelectionGeneration' + MainLang + 'BookContext'][1]
        # SelectionGenerationSplitedIndexs = project.SelectionGenerationEs[1]['SelectionGeneration' + MainLang + 'SplitedIndexs'][1:]
    
    # SecondaryNarratorList, TertiaryNarratorList 형성
    SecondaryNarratorList = [CharacterCompletion[0]['MainCharacterList'][0]['MainCharacter']]
    TertiaryNarratorList = []
    for Character in CharacterCompletion[0]['MainCharacterList'][1:]:
        TertiaryNarratorList.append(Character['MainCharacter'])
    
    SelectionGenerationChunks = []
    for i in range(len(SelectionGenerationSplitedIndexs)):
        SelectionGenerationSplitedBodys = SelectionGenerationSplitedIndexs[i]['SelectionGeneration' + MainLang + 'SplitedBodys']
        for j in range(len(SelectionGenerationSplitedBodys)):
            SelectionGenerationSplitedChunks = SelectionGenerationSplitedBodys[j]['SelectionGeneration' + MainLang + 'SplitedChunks']
            for k in range(len(SelectionGenerationSplitedChunks)):
                ChunkId = SelectionGenerationSplitedChunks[k]['ChunkId']
                Chunk = SelectionGenerationSplitedChunks[k]['Chunk']
                Tag = SelectionGenerationSplitedChunks[k]['Tag']
                Voice = SelectionGenerationSplitedChunks[k]['Voice']
                if (Tag == "Character") and (Voice['Character'] in SecondaryNarratorList):
                    Voice['CharacterTag'] = 'SecondaryNarrator'
                if Voice['Character'] in TertiaryNarratorList:
                    Voice['CharacterTag'] = 'TertiaryNarrator'
                SelectionGenerationChunks.append({'ChunkId': ChunkId, 'Tag': Tag, 'Chunk': Chunk, 'Voice': Voice})
    
    return VoiceDataSetCharacters, CharacterCompletion, SelectionGenerationBookContext, SelectionGenerationChunks

#############################
##### MatchedActors 생성 #####
#############################
# NarratorSet에서 ContextScore 계산
def ContextScoreCal(VoiceDataSetCharacters, SelectionGenerationKoBookContext):
    # print(SelectionGenerationKoBookContext)
    BookGenre = SelectionGenerationKoBookContext['Vector']['ContextCompletion']['Genre']
    BookGender = SelectionGenerationKoBookContext['Vector']['ContextCompletion']['Gender']
    BookAge = SelectionGenerationKoBookContext['Vector']['ContextCompletion']['Age']
    BookPersonality = SelectionGenerationKoBookContext['Vector']['ContextCompletion']['Personality']
    BookAtmosphere = SelectionGenerationKoBookContext['Vector']['ContextCompletion']['Emotion']

    for Character in VoiceDataSetCharacters:
        # Quilty 스코어 계산
        QuiltyScore = Character['Quilty']
        QuiltyScore = QuiltyScore
        # Genre 스코어 계산
        CharacterGenre = Character['Context']['Genre']
        GenreScore = 0
        for NGenre in CharacterGenre:
            if NGenre['index'] in BookGenre['GenreRatio']:
                GenreScore += (BookGenre['GenreRatio'][NGenre['index']] * NGenre['Score'])
        GenreScore = GenreScore / 1000
        # Gender 스코어 계산
        CharacterGender = Character['Context']['Gender']
        GenderScore = 0
        for NGender in CharacterGender:
            if NGender['index'] in BookGender['GenderRatio']:
                GenderScore += (BookGender['GenderRatio'][NGender['index']] * NGender['Score'])
        GenderScore = GenderScore / 1000
        # Age 스코어 계산
        CharacterAge = Character['Context']['Age']
        AgeScore = 0
        for NAge in CharacterAge:
            if NAge['index'] in BookAge['AgeRatio']:
                AgeScore += (BookAge['AgeRatio'][NAge['index']] * NAge['Score'])
        AgeScore = AgeScore / 1000
        # Personality 스코어 계산
        CharacterPersonality = Character['Context']['Personality']
        PersonalityScore = 0
        for NPersonality in CharacterPersonality:
            if NPersonality['index'] in BookPersonality['PersonalityRatio']:
                PersonalityScore += (BookPersonality['PersonalityRatio'][NPersonality['index']] * NPersonality['Score'])
        PersonalityScore = PersonalityScore / 1000
        # Atmosphere 스코어 계산
        CharacterAtmosphere = Character['Context']['Atmosphere']
        AtmosphereScore = 0
        for NAtmosphere in CharacterAtmosphere:
            if NAtmosphere['index'] in BookAtmosphere['Emotion']:
                # KeyError에 대한 대처 (프롬프트 실수 또는 기타의 비중이 커서 EmotionRatio에 index 항목이 없는 경우)
                if NAtmosphere['index'] in BookAtmosphere['EmotionRatio']:
                    AtmosphereScore += (BookAtmosphere['EmotionRatio'][NAtmosphere['index']] * NAtmosphere['Score'])
                elif '기타' in BookAtmosphere['EmotionRatio']:
                    AtmosphereScore += (BookAtmosphere['EmotionRatio']['기타'] * NAtmosphere['Score'] * 0.5)
                else:
                    AtmosphereScore += 0
        AtmosphereScore = AtmosphereScore / 1000
        
        ContextScore = (QuiltyScore * GenreScore * GenderScore * AgeScore * PersonalityScore * AtmosphereScore)
        # if '김건' in Character['Name']:
        #     print(Character['Name'])
        #     print(f'QuiltyScore: {QuiltyScore}')
        #     print(f'GenreScore: {GenreScore}')
        #     print(f'GenderScore: {GenreScore}')
        #     print(f'AgeScore: {AgeScore}')
        #     print(f'PersonalityScore: {PersonalityScore}')
        #     print(f'AtmosphereScore: {AtmosphereScore}')
        #     print(f'ContextScore: {ContextScore}')
        #     print('\n\n')
        Character['Choice'] = 'No'
        Character['Score'] = {'ContextScore': 'None'}
        Character['Score']['ContextScore'] = ContextScore
        # print(f"{NarratorName} : {Narrator['ContextScore']}\n\n1. BookGenre:{BookGenre}\nNarratorGenre:{NarratorGenre}\n\n")
        # print(f'2. BookGender:{BookGender}\nNarratorGender:{NarratorGender}\n\n')
        # print(f'3. BookAge:{BookAge}\nNarratorAge:{NarratorAge}\n\n')
        # print(f'4. BookPersonality:{BookPersonality}\nNarratorPersonality:{NarratorPersonality}\n\n')
        # print(f'5. BookAtmosphere:{BookAtmosphere}\nNarratorAtmosphere:{NarratorAtmosphere}\n\n\n\n')
    
    return VoiceDataSetCharacters

# NarratorSet에서 VoiceScore 계산
def VoiceScoreCal(CharacterCompletion, VoiceDataSetCharacters, CharacterTag):
    for Character in CharacterCompletion:
        if Character['CharacterTag'] == CharacterTag:
            for Voice in VoiceDataSetCharacters:
                # Gender 스코어 계산
                VoiceGender = Voice['Voice']['Gender']
                if Character['Gender'] in VoiceGender:
                    GenderScore = 1
                elif (Character['Gender'] not in VoiceGender) and (Character['Gender'] == '남' or Character['Gender'] == '여'):
                    GenderScore = 0
                else:
                    GenderScore = 0.5
                # Age 스코어 계산
                VoiceAge = Voice['Voice']['Age']
                AgeScore = 0
                for VAge in VoiceAge:
                    if VAge['index'] == Character['Age']:
                        AgeScore += VAge['Score']
                AgeScore = AgeScore / 3.5
                # Role 스코어 계산
                VoiceRole = Voice['Voice']['Role']
                RoleScore = 0
                if Character['CharacterTag'] == "Narrator":
                    RoleScore = VoiceRole[0]['Score']
                    NARoleScore = VoiceRole[1]['Score']
                else:
                    RoleScore = VoiceRole[1]['Score']
                RoleScore = RoleScore / 10
                # Emotion 스코어 계산
                VoiceEmotion = Voice['Voice']['Emotion']
                EmotionScore = 0
                for VEmotion in VoiceEmotion:
                    if VEmotion['index'] in Character['Emotion']:
                        EmotionScore += (Character['Emotion'][VEmotion['index']] * VEmotion['Score'])
                EmotionScore = EmotionScore / 1000
                
                VoiceScore = (GenderScore * AgeScore * RoleScore * EmotionScore)
                
                Voice['Score'][CharacterTag] = Voice['Score']['ContextScore'] * VoiceScore
                if CharacterTag == "Narrator":
                    NAVoiceScore = (GenderScore * AgeScore * NARoleScore * EmotionScore)
                    Voice['Score']['NarratorActor'] = Voice['Score']['ContextScore'] * NAVoiceScore
                
    return VoiceDataSetCharacters

# 최고 점수 캐릭터 선정
def HighestScoreVoiceCal(VoiceDataSetCharacters, CharacterTag, CharacterGender):
    
    def _highestScoreVoice(VoiceDataSetCharacters, CheckCharacterTag, CharacterTag, CharacterGender, Grade):
        highestScore = 0  # 최고 점수를 매우 낮은 값으로 초기화
        highestScoreVoices = []  # 최고 점수를 가진 데이터들을 저장할 리스트
        for VoiceData in VoiceDataSetCharacters:
            # CharacterGender가 '남', '여'가 아니거나, 또는 VoiceData의 성별에 포함될 때 점수 합산 진행
            if (CharacterGender not in ['남', '여']) or (CharacterGender in VoiceData['Voice']['Gender']):
                if Grade in VoiceData['Grade'] and VoiceData['Choice'] == 'No':
                    score = VoiceData['Score'][CharacterTag]
                    if score > highestScore:
                        highestScore = score
                        highestScoreVoices = [VoiceData]  # 새로운 최고 점수 데이터로 리스트를 초기화
                    elif score == highestScore:
                        highestScoreVoices.append(VoiceData)  # 현재 점수가 최고 점수와 같다면 리스트에 추가

        # 최고 점수 데이터들 중 랜덤으로 하나를 선택하여 'Choice'를 CharacterTag로 설정
        if highestScoreVoices:
            highestScoreVoice = random.choice(highestScoreVoices)
            highestScoreVoice['Choice'] = CheckCharacterTag
        else:
            highestScoreVoice = {'Name': 'None', 'ApiSetting': 'None'}
            
        return highestScoreVoice

    HighestScoreVoice = "None"
    CaptionVoice = "None"
    SecondaryVoice = "None"
    TertiaryVoice = "None"
    # CharacterTag가 "Narrator"일 경우
    if CharacterTag == "Narrator":
        HighestScoreVoice = _highestScoreVoice(VoiceDataSetCharacters, CharacterTag, CharacterTag, CharacterGender, "Main")
        CaptionVoice = _highestScoreVoice(VoiceDataSetCharacters, 'Caption', CharacterTag, CharacterGender, "Caption")
        SecondaryVoice = _highestScoreVoice(VoiceDataSetCharacters, 'SecondaryNarrator', 'NarratorActor', CharacterGender, "Actor")
        TertiaryVoice = _highestScoreVoice(VoiceDataSetCharacters, 'TertiaryNarrator', 'NarratorActor', CharacterGender, "Actor")
    
    # CharacterTag가 "CharacterN"일 경우
    else:
        HighestScoreVoice = _highestScoreVoice(VoiceDataSetCharacters, CharacterTag, CharacterTag, CharacterGender, "Actor")

    # CharacterGender가 '남', '여'가 아닐 경우 (중성캐릭터의 나레이터 대체)
    NeuterCharacterTag = "None"
    NeuterActorName = "None"
    if (CharacterTag != "Narrator") and (CharacterGender not in ['남', '여']):
        NeuterCharacterTag = CharacterTag
        for VoiceData in VoiceDataSetCharacters:
            if VoiceData['Choice'] == 'Narrator':
                # VoiceData의 깊은 복사본을 생성
                ModifiedVoiceData = copy.deepcopy(VoiceData)
                # 복사본에 대해 변경 적용
                # 이름
                NeuterActorName = ModifiedVoiceData['Name'][:-1] + ', 중성)'
                ModifiedVoiceData['Name'] = NeuterActorName
                # 감정
                NeuterVoiceEmotion = ModifiedVoiceData['ApiSetting']['emotion_tone_preset']['neuter_emotion_tone_preset']
                ModifiedVoiceData['ApiSetting']['emotion_tone_preset']['emotion_tone_preset'] = NeuterVoiceEmotion
                # 볼륨
                NeuterVoiceVolume = ModifiedVoiceData['ApiSetting']['volume'] * 1.05
                ModifiedVoiceData['ApiSetting']['volume'] = NeuterVoiceVolume
                # 속도
                NeuterVoiceSpeed = [ModifiedVoiceData['ApiSetting']['speed_x'][0] * 100 / 105]
                ModifiedVoiceData['ApiSetting']['speed_x'] = NeuterVoiceSpeed
                # 피치
                NeuterVoicePitch = ModifiedVoiceData['ApiSetting']['pitch'] + 1
                ModifiedVoiceData['ApiSetting']['pitch'] = NeuterVoicePitch
                # 라스트피치
                NeuterVoiceLastPitch = [-2]
                ModifiedVoiceData['ApiSetting']['last_pitch'] = NeuterVoiceLastPitch

                # 변경된 복사본을 HighestScoreVoice로 사용
                HighestScoreVoice = ModifiedVoiceData
                break

    return VoiceDataSetCharacters, HighestScoreVoice, CaptionVoice, SecondaryVoice, TertiaryVoice, NeuterActorName, NeuterCharacterTag

# 낭독 TextSetting
def ActorChunkSetting(RawChunk):
    ActorChunk = RawChunk.replace('(0.1)', '.')
    ActorChunk = ActorChunk.replace('(0.2)', '~.')
    ActorChunk = ActorChunk.replace('(0.20)', ',')
    ActorChunk = ActorChunk.replace('(0.3)', ',')
    ActorChunk = ActorChunk.replace('(0.30)', '')
    ActorChunk = ActorChunk.replace('(0.40)', '')
    ActorChunk = ActorChunk.replace('(0.60)', '곬갌끚')
    ActorChunk = ActorChunk.replace('(0.51)', '')
    ActorChunk = ActorChunk.replace('(0.55)', '')
    ActorChunk = ActorChunk.replace('(0.59)', '')
    ActorChunk = ActorChunk.replace('(0.65)', '')
    ActorChunk = ActorChunk.replace('(0.70)', '')
    ActorChunk = ActorChunk.replace('(0.75)', '')
    ActorChunk = ActorChunk.replace('(0.80)', '')
    ActorChunk = ActorChunk.replace('(0.91)', '')
    ActorChunk = ActorChunk.replace('(1.00)', '')
    ActorChunk = ActorChunk.replace('(1.10)', '')
    ActorChunk = ActorChunk.replace('(1.20)', '')
    ActorChunk = ActorChunk.replace('(1.30)', '')
    ActorChunk = ActorChunk.replace('(1.50)', '')
    ActorChunk = ActorChunk.replace('(2.00)', '')
    ActorChunk = ActorChunk.replace('(3.00)', '')
    
    ActorChunk = ActorChunk.replace(',,', ',')
    ActorChunk = ActorChunk.replace(',.', ',')
    ActorChunk = ActorChunk.replace('.,', ',')
    ActorChunk = ActorChunk.replace('..', '.')
    
    ActorChunk = ActorChunk.replace('\n', '')

    SFXPattern = r"<효과음시작[0-9]{1,5}>|<효과음끝[0-9]{1,5}>"
    ActorChunk = re.sub(SFXPattern, "", ActorChunk)
    
    ETCPattern = r'[^\w\s~.,?]'
    ActorChunk = re.sub(ETCPattern, '', ActorChunk)
    
    if '곬갌끚' in ActorChunk:
        ActorChunk = ActorChunk.split("곬갌끚")
        
    if not isinstance(ActorChunk, list):
        ActorChunk = [ActorChunk]
    
    return ActorChunk

# 낭독 ActorMatching
def ActorMatchedSelectionGenerationChunks(projectName, email, MainLang):
    voiceDataSetCharacters, CharacterCompletion, SelectionGenerationKoBookContext, SelectionGenerationKoChunks = LoadSelectionGenerationKoChunks(projectName, email, MainLang)
    
    # CharacterTags 구하기 (케릭터 태그와 성별 선정)
    CharacterTags = []
    for Character in CharacterCompletion:
        CharacterTags.append({'CharacterTag': Character['CharacterTag'], 'CharacterGender': Character['Gender']})
    
    # Characters 점수계산 및 MatchedActors 생성
    MatchedActors = []
    VoiceDataSetCharacters = ContextScoreCal(voiceDataSetCharacters, SelectionGenerationKoBookContext)
    for character in CharacterTags:
        CharacterTag = character['CharacterTag']
        CharacterGender = character['CharacterGender']
        VoiceDataSetCharacters = VoiceScoreCal(CharacterCompletion, VoiceDataSetCharacters, CharacterTag)
        VoiceDataSetCharacters, HighestScoreVoice, CaptionVoice, SecondaryVoice, TertiaryVoice, NeuterActorName, NeuterCharacterTag = HighestScoreVoiceCal(VoiceDataSetCharacters, CharacterTag, CharacterGender)
        MatchedActor = {'CharacterTag': CharacterTag, 'ActorName': HighestScoreVoice['Name'], 'ApiSetting': HighestScoreVoice['ApiSetting']}
        MatchedActors.append(MatchedActor)
        if CaptionVoice != "None":
            CaptionActor = {'CharacterTag': 'Caption', 'ActorName': CaptionVoice['Name'], 'ApiSetting': CaptionVoice['ApiSetting']}
            MatchedActors.append(CaptionActor)
        if SecondaryVoice != "None":
            SecondaryActor = {'CharacterTag': 'SecondaryNarrator', 'ActorName': SecondaryVoice['Name'], 'ApiSetting': SecondaryVoice['ApiSetting']}
            MatchedActors.append(SecondaryActor)
        if TertiaryVoice != "None":
            TertiaryActor = {'CharacterTag': 'TertiaryNarrator', 'ActorName': TertiaryVoice['Name'], 'ApiSetting': TertiaryVoice['ApiSetting']}
            MatchedActors.append(TertiaryActor)
        ## 중성 캐릭터를 VoiceDataSetCharacters에 합치기
        if NeuterCharacterTag != 'None':
            NeuterVoiceId = VoiceDataSetCharacters[-1]['CharacterId'] + 1
            HighestScoreVoice['CharacterId'] = NeuterVoiceId
            NeuterVoice = HighestScoreVoice
            VoiceDataSetCharacters.append(NeuterVoice)

    # ### 테스트 후 삭제 ###
    # with open('VoiceDataSetCharacters.json', 'w', encoding = 'utf-8') as json_file:
    #     json.dump(VoiceDataSetCharacters, json_file, ensure_ascii = False, indent = 4)
    # with open('MatchedActors.json', 'w', encoding = 'utf-8') as json_file:
    #     json.dump(MatchedActors, json_file, ensure_ascii = False, indent = 4)
    # with open('CharacterTags.json', 'w', encoding = 'utf-8') as json_file:
    #     json.dump(CharacterTags, json_file, ensure_ascii = False, indent = 4)
    # ### 테스트 후 삭제 ###
        
    # SelectionGenerationKoChunks의 MatchedActors 삽입
    for GenerationKoChunks in SelectionGenerationKoChunks:
        ## 중성 캐릭터의 ActorName과 CharacterTag 변경
        if (GenerationKoChunks['Tag'] == "Character") and (GenerationKoChunks['Voice']['CharacterTag'] == "Narrator"):
            GenerationKoChunks['ActorName'] = NeuterActorName
            GenerationKoChunks['Voice']['CharacterTag'] = NeuterCharacterTag
        
        ## 캐릭터가 선정되지 않은 경우 'TertiaryNarrator' 배정
        if GenerationKoChunks['Voice']['CharacterTag'] == 'None':
            GenerationKoChunks['Voice']['CharacterTag'] = 'TertiaryNarrator'
            
        if GenerationKoChunks['Tag'] in ['Caption', 'CaptionComment']:
            ChunkCharacterTag = 'Caption'
            GenerationKoChunks['Voice']['CharacterTag'] = 'Caption'
        else:
            ChunkCharacterTag = GenerationKoChunks['Voice']['CharacterTag']
            
        for MatchedActor in MatchedActors:
            if ChunkCharacterTag == MatchedActor['CharacterTag']:
                GenerationKoChunks['ActorName'] = MatchedActor['ActorName']
                GenerationKoChunks['ActorChunk'] = ActorChunkSetting(GenerationKoChunks['Chunk'])
                if '(0.60)' in GenerationKoChunks['Chunk']:
                    # "(0.60)"을 기준으로 모든 부분을 나눔
                    parts = GenerationKoChunks['Chunk'].split("(0.60)")
                    GenerationKoChunks['Chunk'] = [part + "(0.60)" for part in parts[:-1]] + [parts[-1]]
                GenerationKoChunks['ApiSetting'] = MatchedActor['ApiSetting']
                
        # name 값을 기준으로 그룹화(API 변경 횟수 절감)
        GroupedData = defaultdict(list)
        for Actor in MatchedActors:
            name = Actor["ApiSetting"]["name"]
            GroupedData[name].append(Actor)
        # 정렬된 그룹을 기반으로 최종 리스트 재구성
        SortedMatchedActors = []
        for name in sorted(GroupedData.keys()):
            SortedMatchedActors.extend(GroupedData[name])
                
    # ### 테스트 후 삭제 ### 이 부분에서 Text 수정 UI를 만들어야 함 ###
    # with open('SelectionGenerationKoChunks.json', 'w', encoding = 'utf-8') as json_file:
    #     json.dump(SelectionGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)
    # ### 테스트 후 삭제 ### 이 부분에서 Text 수정 UI를 만들어야 함 ###
    
    return SortedMatchedActors, SelectionGenerationKoChunks, VoiceDataSetCharacters
    
## VoiceLayerPath(TTS 저장) 경로 생성
def VoiceLayerPathGen(projectName, email, FileName, Folder):
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

#######################################
##### VoiceLayerGenerator 파일 생성 #####
#######################################
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
        for i in range(len(ActorChunk)):
            AudioDic = {"Chunk": ActorChunk[i], "Pause": Pause[i], "EndTime": EndTime[i]}
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

## TypecastVoice 생성 ##
def ActorVoiceGen(projectName, email, voiceReverbe, tag, name, Chunk, EL_Chunk, Api, ApiSetting, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath, SplitChunks, MessagesReview):
    attempt = 0

    ### 음성 속도 조절 함수 ###
    def ChangeSpeedIndexVoice(VoicePath, Volume = 1.0, Speed = 1.0, Pad = 1.0, Reverberance = 5, RoomScale = 5, HighFreqDamping = 10, PreDelay = 3):
        CopyFilePath = VoicePath.replace('.wav', '_Change.wav')
        shutil.copyfile(VoicePath, CopyFilePath)
        
        tfm = sox.Transformer()
        # 속도를 줄임 (피치 유지)
        tfm.tempo(Speed, 's')
        # 1초 추가(잔향의 끊어짐 방지)
        tfm.pad(0, Pad)
        # 잔향(리버브) 추가
        tfm.reverb(reverberance = Reverberance, room_scale = RoomScale, high_freq_damping = HighFreqDamping, pre_delay = PreDelay)
        # 볼륨 조절
        tfm.vol(Volume)
        # 변환 실행
        tfm.build(CopyFilePath, VoicePath)
        
        os.remove(CopyFilePath)

    ##################
    ### ElevenLabs ###
    ##################
    if Api == "ElevenLabs":
        # Api Setting
        VoiceId = ApiSetting['voice_id']
        Stability = random.choice(ApiSetting['stability'])
        SimilarityBoost = random.choice(ApiSetting['similarity_boost'])
        Style = random.choice(ApiSetting['style'])
        Model = ApiSetting['model']
        
        while attempt < 60:
            try:
                ########## ElevenLabs API 요청 ##########
                Api_key = os.getenv("ELEVENLABS_API_KEY")
                client = ElevenLabs(api_key = Api_key)
                
                Voice_Audio = client.generate(
                    text = EL_Chunk,
                    voice = Voice(
                        voice_id = VoiceId,
                        settings = VoiceSettings(stability = Stability, similarity_boost = SimilarityBoost, style = Style, use_speaker_boost = True)
                    ),
                    model = Model
                )

                if len(SplitChunks) == 1:
                    if "M.wav" in voiceLayerPath:
                        fileName = voiceLayerPath.replace("M.wav", "_(0)M.wav")
                    else:
                        fileName = voiceLayerPath.replace(".wav", "_(0).wav")
                else:
                    fileName = voiceLayerPath

                print(f"VoiceGen: completion, {name} waiting 1-5 second")
                
                fileNameMp3 = fileName.replace(".wav", ".mp3")
                save(Voice_Audio, fileNameMp3)
                
                # mp3으로 저장된 파일을 wav로 변경
                Voice_Audio_Mp3 = AudioSegment.from_mp3(fileNameMp3)
                Voice_Audio_Mp3.export(fileName, format = "wav")
                os.remove(fileNameMp3)

                ## VoiceReverbe ##
                if voiceReverbe == 'on':
                    ## tag가 Title, Logue인 경우 ##
                    if tag in ['Title', 'Logue']:
                        print(f"ChangeSpeed(0.89): ({tag}) Voice waiting 1-2 second")
                        ChangeSpeedIndexVoice(fileName, Volume = 1.00, Speed = 0.89, Pad = 0.5, Reverberance = 3, RoomScale = 3, HighFreqDamping = 6, PreDelay = 2)

                    ## tag가 Title, Logue, Part, Chapter, Index인 경우 ##
                    if tag in ['Part', 'Chapter', 'Index']:
                        print(f"ChangeSpeed(0.91): ({tag}) Voice waiting 1-2 second")
                        ChangeSpeedIndexVoice(fileName, Volume = 1.00, Speed = 0.91, Pad = 1.0, Reverberance = 5, RoomScale = 5, HighFreqDamping = 10, PreDelay = 3)
                
                if len(SplitChunks) > 1:
                    ### 음성파일을 분할하는 코드 ###
                    VoiceSplit(projectName, email, name, voiceLayerPath, SplitChunks, MessagesReview = MessagesReview)

                return "Continue"
                ########## ElevenLabs API 요청 ##########
            except KeyError:
                attempt += 1
                print(f"[ KeyError 발생, 재시도 {attempt}/60 ]")
                time.sleep(60)  # 1분 대기 후 재시도
                
            except Exception as e:
                sys.exit(f"[ 예상치 못한 에러 발생: {e} ]")

    ################
    ### TypeCast ###
    ################
    if Api == "TypeCast":
        while attempt < 60:
            try:
                ########## TypeCast API 요청 ##########
                api_token = os.getenv("TYPECAST_API_TOKEN")
                HEADERS = {'Authorization': f'Bearer {api_token}'}

                # get my actor
                r = requests.get('https://typecast.ai/api/actor', headers = HEADERS)
                my_actors = r.json()['result']
                
                if my_actors[0]['name']['ko'] == name:
                    # print(Chunk)
                    # print(RandomEMOTION)
                    # print(RandomSPEED)
                    # print(Pitch)
                    # print(RandomLASTPITCH)
                    # print(voiceLayerPath)
                    # print(my_actors)
                    my_first_actor = my_actors[0]
                    my_first_actor_id = my_first_actor['actor_id']

                    # request speech synthesis
                    r = requests.post('https://typecast.ai/api/speak', headers = HEADERS, json = {
                        'text': Chunk, # 음성을 합성하는 문장
                        'actor_id': my_first_actor_id, # 캐릭터 아이디로 Actor API에서 캐릭터를 검색
                        'lang': 'auto', # text의 언어 코드['en-us', 'ko-kr', 'ja-jp', 'es-es', 'auto'], auto는 자동 언어 감지
                        'xapi_hd': True, # 샘플레이트로 True는 고품질(44.1KHz), False는 저품질(16KHz)
                        'xapi_audio_format': 'wav', # 오디오 포멧으로 기본값은 'wav', 'mp3'
                        'model_version': 'latest', # 모델(캐릭터) 버전으로 API를 참고, 최신 모델은 "latest"
                        'emotion_tone_preset': RandomEMOTION, # 감정으로, actor_id를 사용하여 Actor API 에서 캐릭터에 사용 가능한 감정을 검색
                        'emotion_prompt': None, # 감정 프롬프트(한/영)를 입력, 입력시 'emotion_tone_preset'는 'emotion_prompt'로 설정
                        'volume': 120, # 오디오 볼륨으로 기본값은 100, 범위: 0.5배는 50 - 2배는 200, 
                        'speed_x': RandomSPEED, # 말하는 속도로 기본값은 1, 범위: 0.5(빠름) - 1.5(느림)
                        'tempo': 1.0, # 음성 재생속도로 기본값은 1, 범위: 0.5(0.5배 느림) - 2.0(2배 빠름)
                        'pitch': Pitch, # 음성 피치로 기본값은 0, 범위: -12 - 12
                        'max_seconds': 60, # 음성의 최대 길이로 기본값은 30, 범위: 1 - 60
                        'force_length': 0, # text의 시간을 max_seconds에 맞추려면 1, 기본값은 0
                        'last_pitch': RandomLASTPITCH, # 문장 끝의 피치제어로, 기본값은 0, 범위: -2(최저) - 2(최고)
                    })
                    speak_url = r.json()['result']['speak_v2_url']

                    # polling the speech synthesis result
                    for _ in range(120):
                        r = requests.get(speak_url, headers=HEADERS)
                        ret = r.json()['result']
                        # audio is ready
                        if ret['status'] == 'done':
                            # download audio file
                            r = requests.get(ret['audio_download_url'])
                            if len(SplitChunks) == 1:
                                if "M.wav" in voiceLayerPath:
                                    fileName = voiceLayerPath.replace("M.wav", "_(0)M.wav")
                                else:
                                    fileName = voiceLayerPath.replace(".wav", "_(0).wav")
                            else:
                                fileName = voiceLayerPath
                            with open(fileName, 'wb') as f:
                                f.write(r.content)
                            break
                        else:
                            print(f"VoiceGen: {ret['status']}, {name} waiting 1 second")
                            time.sleep(1)

                    ## VoiceReverbe ##
                    if voiceReverbe == 'on':
                        ## tag가 Title, Logue인 경우 속도 ##
                        if tag in ['Title', 'Logue']:
                            print(f"ChangeSpeed(0.89): ({tag}) Voice waiting 1-2 second")
                            ChangeSpeedIndexVoice(fileName, Volume = 1.00, Speed = 0.89, Pad = 0.5, Reverberance = 3, RoomScale = 3, HighFreqDamping = 6, PreDelay = 2)

                        ## tag가 Title, Logue, Part, Chapter, Index인 경우 ##
                        if tag in ['Part', 'Chapter', 'Index']:
                            print(f"ChangeSpeed(0.91): ({tag}) Voice waiting 1-2 second")
                            ChangeSpeedIndexVoice(fileName, Volume = 1.00, Speed = 0.91, Pad = 1.0, Reverberance = 5, RoomScale = 5, HighFreqDamping = 10, PreDelay = 3)

                        ## tag가 Character인 경우 ##
                        if tag in ['Character']:
                            print(f"ChangeSpeed(1.07): ({tag}) Voice waiting 1-2 second")
                            ChangeSpeedIndexVoice(fileName, Volume = 1.00, Speed = 1.07, Pad = 0.5, Reverberance = 5, RoomScale = 5, HighFreqDamping = 10, PreDelay = 3)

                    if len(SplitChunks) > 1:
                        ### 음성파일을 분할하는 코드 ###
                        VoiceSplit(projectName, email, name, voiceLayerPath, SplitChunks, MessagesReview = MessagesReview)

                    return "Continue"
                else:
                    return name
                ########## TypeCast API 요청 ##########
            except KeyError:
                attempt += 1
                print(f"[ KeyError 발생, 재시도 {attempt}/60 ]")
                time.sleep(60)  # 1분 대기 후 재시도

            except Exception as e:
                sys.exit(f"[ 예상치 못한 에러 발생: {e} ]")
        sys.exit("[ 1시간째 API 무응답, 요금을 충전하세요. ]")

## 생성된 음성 합치기 ##
## Pause 추출
def ExtractPause(chunk):
    # 정규 표현식을 사용하여 텍스트 끝 부분의 괄호와 숫자를 찾음
    match = re.search(r'\((\d+(\.\d+)?)\)$', chunk)
    if match:
        floatVal = float(match.group(1))
        if floatVal.is_integer():
            Pause = int(floatVal)
        else:
            Pause = floatVal
        return Pause
    else:
        # 숫자를 찾지 못했다면, 빈 문자열 반환
        return 0

## 생성된 음성파일 정렬/필터
def SortAndRemoveDuplicates(editGenerationKoChunks, files, voiceLayerPath):
    # 파일명에서 필요한 정보를 추출하는 함수
    def ExtractFileInfo(FileName, removeList):
        match = re.match(r"(.+)\_(\d+(\.\d+)?)\_(.+?\(.+?\))\_\((\d+)\)(M?)\.wav", FileName)
        if match == None:
            normalizeFileName = unicodedata.normalize('NFC', FileName)
            match = re.match(r"(.+)\_(\d+(\.\d+)?)\_(.+?\(.+?\))\_\((\d+)\)(M?)\.wav", normalizeFileName)
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
                os.remove(voiceLayerPath + FileName)
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

    ## None 부분과, EditGenerationKoChunks에 존재하지 않는 부분은 제거
    # editGenerationKoChunks의 데이터 리스트 추출
    editInfos = []
    for editChunks in editGenerationKoChunks:
        EditId = editChunks['EditId']
        ActorName = editChunks['ActorName']
        ActorChunk = editChunks['ActorChunk']
        editInfo = {'EditId': EditId, 'ActorName': ActorName, 'DetailEditNum': None}
        for i in range(len(ActorChunk)):
            editInfo = {'EditId': EditId, 'ActorName': ActorName, 'DetailEditNum': i}
            editInfos.append(editInfo)
               
    # None 부분, editInfos에 존재하지 않는 파일명 제거
    FilteredSortedFiles = []
    CheckedEditInfos = []
    i = 0
    for file in SortedFiles:
        fileInfos = ExtractFileInfo(file, RemoveList)  # 파일 정보 추출
        for editInfo in editInfos:
            if (editInfo['EditId'] == fileInfos['gen_num']) and \
                (editInfo['ActorName'] == fileInfos['name_with_info']) and \
                (editInfo['DetailEditNum'] == fileInfos['detail_gen_num']):
                FilteredSortedFiles.append(file)
                CheckedEditInfos.append(editInfo)
                
    # CheckedEditInfos의 중복 제거
    _CheckedEditInfos = []
    if CheckedEditInfos:
        _CheckedEditInfos.append(CheckedEditInfos[0])
        for CheckedEditInfo in CheckedEditInfos[1:]:
            if CheckedEditInfo != _CheckedEditInfos[-1]:
                _CheckedEditInfos.append(CheckedEditInfo)
                
    # editInfos(검수데이터)와 중복제거된 _CheckedEditInfos(생성파일)의 비교
    for checkedEditInfo in _CheckedEditInfos:
        if checkedEditInfo in editInfos:
            editInfos.remove(checkedEditInfo)
    
    # editInfos에 남은 파일이 있는지 확인 (생성되지 못한 파일)
    if editInfos != []:
        for editInfo in editInfos:
            print(f"[ 파일 생성 또는 EditId 확인 필요: {editInfo} ]")
        sys.exit()

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
def VoiceGenerator(projectName, email, EditGenerationKoChunks, MatchedChunksPath, Narrator, CloneVoiceName, CloneVoiceActorPath, VoiceEnhance = 'off', VoiceFileGen = 'on'):
    noise_removal = NoiseRemovalClient(api_key = os.getenv("AUDO_API_KEY"))
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
    FilteredFiles = SortAndRemoveDuplicates(EditGenerationKoChunks, Files, voiceLayerPath)
    FilesCount = 0
    file_limit = 100  # 파일 분할 기준
    current_file_index = 1
    CombinedSound = AudioSegment.empty()
    VoiceEnhanceCompletionSwitch = False
    with open(CloneVoiceActorPath, 'r', encoding = 'utf-8') as CloneVoiceActorJson:
        CloneVoiceActor = json.load(CloneVoiceActorJson)
    VoiceEnhanceCompletion = CloneVoiceActor['ApiSetting']['VoiceEnhanceCompletion']

    UpdateTQDM = tqdm(EditGenerationKoChunks,
                    total = len(EditGenerationKoChunks),
                    desc = 'VoiceGenerator')

    # 전체 오디오 클립의 누적 길이를 추적하는 변수 추가
    total_duration_seconds = 0
    for Update in UpdateTQDM:
        Update['EndTime'] = []
        for j in range(len(Update['Pause'])):
            VoiceFilePath = os.path.join(voiceLayerPath, FilteredFiles[FilesCount])
            ## VoiceEnhance
            if (Narrator == 'VoiceClone') and (CloneVoiceName in FilteredFiles[FilesCount]) and (VoiceEnhanceCompletion != 'Completion') and (VoiceEnhance == 'on'):
                result = noise_removal.process(VoiceFilePath)
                sleep(2.0)
                result.save(VoiceFilePath)
                sleep(1.0)
                print(f"[ VoiceEnhance: {FilteredFiles[FilesCount]} ]")
                VoiceEnhanceCompletionSwitch = True
            with open(VoiceFilePath, 'rb') as VoiceFile:
                sound_file = AudioSegment.from_wav(VoiceFile)
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
    if (not CombinedSound.empty()) and (int(CombinedSound.duration_seconds) >= 1):
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

    # 저자 성우 음성 노이즈 제거 되었다면 "Completion" 생성
    if VoiceEnhanceCompletionSwitch:
        CloneVoiceActor['ApiSetting']['VoiceEnhanceCompletion'] = "Completion"
        with open(CloneVoiceActorPath, 'w', encoding = 'utf-8') as CloneVoiceActorJson:
            json.dump(CloneVoiceActor, CloneVoiceActorJson, ensure_ascii = False, indent = 4)
    
    # 최종 파일 합치기
    FinalCombined = AudioSegment.empty()
    for i in range(1, current_file_index):
        part_name = f"{projectName}_VoiceLayer_{i*file_limit-file_limit+1}-{min(i*file_limit, len(FilteredFiles))}.wav"
        part_path = os.path.join(voiceLayerPath, part_name)
        part = AudioSegment.from_wav(part_path)
        FinalCombined += part
        # 파일 묶음 삭제
        os.remove(part_path)

    # wav파일과 Edit의 시간 오차율 교정
    FinalCombined_seconds = FinalCombined.duration_seconds
    seconds_error_rate = FinalCombined_seconds/total_duration_seconds
    for Chunks in EditGenerationKoChunks:
        EndTime = Chunks['EndTime']
        for i in range(len(EndTime)):
            RawSecond = copy.deepcopy(EndTime[i])
            Second = RawSecond * seconds_error_rate
            Time = SecondsToHMS(Second)
            EndTime[i] = {"Time": Time, "Second": Second}
    
    # 마지막 5초 공백 추가
    FinalCombined += AudioSegment.silent(duration = 5000)  # 5초간의 공백 생성

    # 최종적으로 합쳐진 음성 파일 저장
    voiceLayerPath = VoiceLayerPathGen(projectName, email, projectName + '_VoiceBook.wav', 'Master')
    if VoiceFileGen == 'on':
        try:
            with open(voiceLayerPath, "wb") as VoiceFile:
                FinalCombined.export(VoiceFile, format = "wav")
                FinalCombined = AudioSegment.empty()
            # struct.error: 'L' format requires 0 <= number <= 4294967295 에러 방지 (4GB 용량 문제 방지)
        except:
            os.remove(voiceLayerPath)
            voiceLayerPathMp3 = voiceLayerPath.replace(".wav", ".mp3")
            # 오디오 파일을 12개의 파트로 나눈 후 3분할로 저장
            PartLength = len(FinalCombined) // 12
            parts = []
            for i in range(12):
                start = i * PartLength
                if i == 11:  # 마지막 파트에서는 나머지 모두를 포함
                    part = FinalCombined[start:]
                else:
                    part = FinalCombined[start:start+PartLength]
                parts.append(part)

            # 각 파트를 임시 파일로 저장 후 다시 로드하여 합치기
            FinalCombinedPart1 = AudioSegment.empty()
            for i, part in enumerate(parts[:4]):
                TempPath = voiceLayerPathMp3.replace(".mp3", f"_Part{i+1}.mp3")
                with open(TempPath, "wb") as file:
                    print(f"[ 대용량 파일 분할 저장: {TempPath} ]")
                    part.export(file, format = "mp3", bitrate = "320k")
                    LoadedPart = AudioSegment.from_file(TempPath)
                    FinalCombinedPart1 += LoadedPart  # 파트 합치기
                os.remove(TempPath)  # 임시 파일 삭제
            FinalCombined = AudioSegment.empty()  # 메모리 해제
            
            # 최종 파일 저장
            with open(voiceLayerPathMp3.replace(".mp3", f"_(1).mp3"), "wb") as FinalCombined_file:
                FinalCombinedPart1.export(FinalCombined_file, format = "mp3", bitrate = "320k")
                FinalCombinedPart1 = AudioSegment.empty()  # 메모리 해제
                
            # 각 파트를 임시 파일로 저장 후 다시 로드하여 합치기
            FinalCombinedPart2 = AudioSegment.empty()
            for i, part in enumerate(parts[4:8]):
                TempPath = voiceLayerPathMp3.replace(".mp3", f"_Part{i+5}.mp3")
                with open(TempPath, "wb") as file:
                    print(f"[ 대용량 파일 분할 저장: {TempPath} ]")
                    part.export(file, format = "mp3", bitrate = "320k")
                    LoadedPart = AudioSegment.from_file(TempPath)
                    FinalCombinedPart2 += LoadedPart  # 파트 합치기
                os.remove(TempPath)  # 임시 파일 삭제

            # 최종 파일 저장
            with open(voiceLayerPathMp3.replace(".mp3", f"_(2).mp3"), "wb") as FinalCombined_file:
                FinalCombinedPart2.export(FinalCombined_file, format = "mp3", bitrate = "320k")
                FinalCombinedPart2 = AudioSegment.empty()  # 메모리 해제
                
            # 각 파트를 임시 파일로 저장 후 다시 로드하여 합치기
            FinalCombinedPart3 = AudioSegment.empty()
            for i, part in enumerate(parts[8:]):
                TempPath = voiceLayerPathMp3.replace(".mp3", f"_Part{i+9}.mp3")
                with open(TempPath, "wb") as file:
                    print(f"[ 대용량 파일 분할 저장: {TempPath} ]")
                    part.export(file, format = "mp3", bitrate = "320k")
                    LoadedPart = AudioSegment.from_file(TempPath)
                    FinalCombinedPart3 += LoadedPart  # 파트 합치기
                os.remove(TempPath)  # 임시 파일 삭제

            # 최종 파일 저장
            with open(voiceLayerPathMp3.replace(".mp3", f"_(3).mp3"), "wb") as FinalCombined_file:
                FinalCombinedPart3.export(FinalCombined_file, format = "mp3", bitrate = "320k")
                FinalCombinedPart3 = AudioSegment.empty()  # 메모리 해제
    
    ## EditGenerationKoChunks의 Dic(검수)
    EditGenerationKoChunks = EditGenerationKoChunksToDic(EditGenerationKoChunks)
    ## EndTime이 업데이트 된 EditGenerationKoChunks 저장
    with open(MatchedChunksPath, 'w', encoding = 'utf-8') as json_file:
        json.dump(EditGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)
        
    return EditGenerationKoChunks

## CloneVoice 셋팅
def CloneVoiceSetting(projectName, Narrator, CloneVoiceName, MatchedActors, CloneVoiceActorPath, SelectionGenerationKoChunks):
    ## Narrator가 "CloneVoice" 인 경우 CloneVoiceDic 생성 ##
    if Narrator == 'VoiceClone':
        if not os.path.exists(CloneVoiceActorPath):
            CloneVoiceActor = {
                "Name": f"{CloneVoiceName}({projectName})",
                "ApiSetting": {
                    "name": f"{CloneVoiceName}",
                    "Api": "ElevenLabs",
                    "voice_id": "Voice_id",
                    "stability": [0.60, 0.65, 0.70, 0.75],
                    "similarity_boost": [0.80, 0.82, 0.84, 0.86, 0.88],
                    "style": [0.00],
                    "model": "eleven_multilingual_v2",
                    "SettingCompletion": "세팅 완료 후 Completion으로 변경",
                    "VoiceEnhanceCompletion": "None"
                }
            }
            with open(CloneVoiceActorPath, 'w', encoding = 'utf-8') as CloneVoiceActorJson:
                json.dump(CloneVoiceActor, CloneVoiceActorJson, ensure_ascii = False, indent = 4)
            sys.exit(f'[ 클론보이스 세팅을 완료하세요 : {CloneVoiceActorPath} ]')
        else:
            with open(CloneVoiceActorPath, 'r', encoding = 'utf-8') as CloneVoiceActorJson:
                CloneVoiceActor = json.load(CloneVoiceActorJson)
            
            # 클론보이스 세팅이 완료되었는지 확인
            SettingCompletion = CloneVoiceActor['ApiSetting']['SettingCompletion']
            if SettingCompletion != 'Completion':
                sys.exit(f'[ 클론보이스 세팅을 완료하세요 : {CloneVoiceActorPath} ]')
            else:
                ## MatchedVoices 변경
                for _Matched in MatchedActors:
                    if _Matched['CharacterTag'] == 'Narrator':
                        BeforeNarratorName = _Matched['ActorName']
                        AfterNarratorName = CloneVoiceActor['Name']
                        _Matched['ActorName'] = AfterNarratorName
                        _Matched['ApiSetting'] = CloneVoiceActor['ApiSetting']
                        
                ## AudioBook_Edit 변경
                if BeforeNarratorName != AfterNarratorName:
                    for _Edit in SelectionGenerationKoChunks:
                        if _Edit['ActorName'] == BeforeNarratorName:
                            _Edit['ActorName'] = AfterNarratorName
        
        return MatchedActors, SelectionGenerationKoChunks
    
    return MatchedActors, SelectionGenerationKoChunks

## 프롬프트 요청 및 결과물 VoiceLayerGenerator
def VoiceLayerSplitGenerator(projectName, email, Narrator = 'VoiceActor', CloneVoiceName = '저자명', VoiceReverbe = 'on', MainLang = 'Ko', Mode = "Manual", Macro = "Auto", Account = "None", VoiceEnhance = 'off', VoiceFileGen = 'on', MessagesReview = "off"):
    MatchedActors, SelectionGenerationKoChunks, VoiceDataSetCharacters = ActorMatchedSelectionGenerationChunks(projectName, email, MainLang)
    
    ## MatchedActors 가 존재하면 함수에서 호출된 MatchedActors를 json파일에서 대처
    # MatchedActors 경로 생성
    fileName = projectName + '_' + 'MatchedVoices.json'
    MatchedActorsPath = VoiceLayerPathGen(projectName, email, fileName, 'Mixed')
    fileName = '[' + projectName + '_' + 'CloneVoice_Setting].json'
    CloneVoiceActorPath = VoiceLayerPathGen(projectName, email, fileName, 'Master')
    # MatchedChunksEdit 경로 생성
    fileName = '[' + projectName + '_' + 'AudioBook_Edit].json'
    MatchedChunksPath = VoiceLayerPathGen(projectName, email, fileName, 'Master')
    OriginFileName = '' + projectName + '_' + 'VoiceLayer_Origin.json'
    MatchedChunksOriginPath = VoiceLayerPathGen(projectName, email, OriginFileName, 'Mixed')
    
    ## CloneVoice 셋팅
    MatchedActors, SelectionGenerationKoChunks = CloneVoiceSetting(projectName, Narrator, CloneVoiceName, MatchedActors, CloneVoiceActorPath, SelectionGenerationKoChunks)

    if os.path.exists(MatchedActorsPath):
        with open(MatchedActorsPath, 'r', encoding = 'utf-8') as MatchedActorsJson:
            MatchedActors = json.load(MatchedActorsJson)
        with open(MatchedChunksPath, 'r', encoding = 'utf-8') as MatchedChunksJson:
            MatchedChunks = json.load(MatchedChunksJson)

        ## AudioBook_Edit에 새로운 ActorName이 발생한 경우 이를 MatchedActors에 추가
        # MatchedActors 검토
        MatchedActorNames = []
        for _Matched in MatchedActors:
            if _Matched['ActorName'] not in MatchedActorNames:
                MatchedActorNames.append(_Matched['ActorName'])
        
        # AudioBook_Edit 검토
        EditActorNames = []
        for _Edit in MatchedChunks:
            if _Edit['ActorName'] not in EditActorNames:
                EditActorNames.append(_Edit['ActorName'])

        # 새롭게 추가될 ActorNames
        NewActorNames = [actor for actor in EditActorNames if actor not in MatchedActorNames]

        # 새롭게 추가될 ActorNames이 존재할 경우 MatchedActors 업데이트
        if NewActorNames != []:
            for Characters in VoiceDataSetCharacters:
                if Characters['Name'] in NewActorNames:
                    NewActorDic = {"CharacterTag": "NewCharacter", "ActorName": Characters['Name'], "ApiSetting": Characters['ApiSetting']}
                    MatchedActors.append(NewActorDic)
            # 새롭게 추가된 캐릭터 내용 저장 (덮어쓰기)
            with open(MatchedActorsPath, 'w', encoding = 'utf-8') as MatchedActorsJson:
                json.dump(MatchedActors, MatchedActorsJson, ensure_ascii = False, indent = 4)

    ## MatchedActor 순서대로 Speech 생성
    for MatchedActor in MatchedActors:
        Api = MatchedActor['ApiSetting']['Api']
        Actor = MatchedActor['ActorName']

        print(f"< Project: {projectName} | Actor: {Actor} | VoiceLayerGenerator 시작 >")
        
        ## MatchedChunksPath.json이 존재하면 해당 파일로 VoiceLayerGenerator 진행, 아닐경우 새롭게 생성
        if (not os.path.exists(MatchedChunksPath)) and (not os.path.exists(unicodedata.normalize('NFC', MatchedChunksPath))) and (not os.path.exists(unicodedata.normalize('NFD', MatchedChunksPath))):
            # SelectionGenerationKoChunks의 EditGenerationKoChunks화
            EditGenerationKoChunks = []
            #### Split을 위한 문장을 합치는 코드 ####
            tempChunk = None

            def appendAndResetTemp(tempChunk, newChunk):
                if tempChunk:
                    EditGenerationKoChunks.append(tempChunk)
                return newChunk

            def splitChunksAndPauses(chunks, pauses, max_length = 350):
                split_chunks = []
                split_pauses = []
                current_chunk = []
                current_pause = []
                current_length = 0

                for chunk, pause in zip(chunks, pauses):
                    if current_length + len(chunk) > max_length:
                        split_chunks.append(current_chunk)
                        split_pauses.append(current_pause)
                        current_chunk = [chunk]
                        current_pause = [pause]
                        current_length = len(chunk)
                    else:
                        current_chunk.append(chunk)
                        current_pause.append(pause)
                        current_length += len(chunk)

                if current_chunk:  # Add remaining chunks and pauses
                    split_chunks.append(current_chunk)
                    split_pauses.append(current_pause)

                return split_chunks, split_pauses
            
            # 언어만 남기는 함수 추가
            def extract_text(text):
                return re.sub(r'[^가-힣a-zA-Z0-9]', '', text)

            for GenerationKoChunk in SelectionGenerationKoChunks:
                chunkid = GenerationKoChunk['ChunkId']
                tag = GenerationKoChunk['Tag']
                actorname = GenerationKoChunk['ActorName']
                actorchunks = [chunk + "," for chunk in GenerationKoChunk['ActorChunk']]

                if isinstance(GenerationKoChunk['Chunk'], list):
                    chunks = GenerationKoChunk['Chunk']
                else:
                    chunks = [GenerationKoChunk['Chunk']]
                pauses = [ExtractPause(chunk) for chunk in chunks]

                newChunk = {"EditId": None, "ChunkId": [chunkid], "Tag": tag, "ActorName": actorname, "ActorChunk": actorchunks, "Pause": pauses, "Endtime": None}

                if tempChunk and len(' '.join(tempChunk['ActorChunk'] + actorchunks)) <= 350 and (tempChunk['Tag'] == tag and tempChunk['ActorName'] == actorname):
                    # 기존 문장과 새로운 문장을 언어만 남긴 상태로 비교
                    combined_text = extract_text(' '.join(tempChunk['ActorChunk']))
                    new_text = extract_text(' '.join(actorchunks))
                    if new_text not in combined_text:  # 새로운 문장이 기존 문장에 포함되어 있지 않은 경우에만 합침
                        tempChunk['ActorChunk'] += actorchunks
                        tempChunk['Pause'] += pauses
                        tempChunk['ChunkId'] += [chunkid]
                    else:  # 새로운 문장이 기존 문장에 포함되어 있는 경우, 새로운 딕셔너리로 시작
                        tempChunk = appendAndResetTemp(tempChunk, newChunk)
                else:
                    if tempChunk:  # Check and split before resetting if needed
                        combined_text = ' '.join(tempChunk['ActorChunk'])
                        if len(combined_text) > 350:
                            split_chunks, split_pauses = splitChunksAndPauses(tempChunk['ActorChunk'], tempChunk['Pause'])
                            for sc, sp in zip(split_chunks, split_pauses):
                                split_chunk = {"EditId": None, "ChunkId": tempChunk['ChunkId'], "Tag": tempChunk['Tag'], "ActorName": tempChunk['ActorName'], "ActorChunk": sc, "Pause": sp, "Endtime": None}
                                EditGenerationKoChunks.append(split_chunk)
                            tempChunk = None  # Reset after splitting
                    tempChunk = appendAndResetTemp(tempChunk, newChunk)

            if tempChunk:
                EditGenerationKoChunks.append(tempChunk)
            
            ## EditId 선정 및 EndTime을 Pause개수대로 None으로 초기화
            EditId = 1
            for NewGenerationKoChunk in EditGenerationKoChunks[:]:
                if NewGenerationKoChunk['ActorChunk']:
                    NewGenerationKoChunk['EditId'] = EditId
                    NewGenerationKoChunk['EndTime'] = [None] * len(NewGenerationKoChunk['Pause'])
                    EditId += 1
                else:
                    EditGenerationKoChunks.remove(NewGenerationKoChunk)
            
            ## 빈 ActorChunk 삭제
            for i in range(len(EditGenerationKoChunks)):
                for j in range(len(EditGenerationKoChunks[i]['ActorChunk'])):
                    if extract_text(EditGenerationKoChunks[i]['ActorChunk'][j]) == '':
                        del EditGenerationKoChunks[i]['ActorChunk'][j]
                        del EditGenerationKoChunks[i]['Pause'][j]
                        del EditGenerationKoChunks[i]['EndTime'][j]
            #### Split을 위한 문장을 합치는 코드 ####
            
            ## EditGenerationKoChunks의 Dic(검수)
            EditGenerationKoChunks = EditGenerationKoChunksToDic(EditGenerationKoChunks)
            
            # MatchedActors, MatchedChunks 저장 (Dic 저장 후 다시 List로 변환)
            fileName = projectName + '_' + 'MatchedVoices.json'
            MatchedActorsPath = VoiceLayerPathGen(projectName, email, fileName, 'Mixed')
            with open(MatchedActorsPath, 'w', encoding = 'utf-8') as json_file:
                json.dump(MatchedActors, json_file, ensure_ascii = False, indent = 4)
            with open(MatchedChunksPath, 'w', encoding = 'utf-8') as json_file:
                json.dump(EditGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)
            with open(MatchedChunksOriginPath, 'w', encoding = 'utf-8') as json_file:
                json.dump(EditGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)
            
            ## EditGenerationKoChunks의 Dic(프로세스)
            EditGenerationKoChunks = EditGenerationKoChunksToList(EditGenerationKoChunks)
        else:
            with open(MatchedChunksPath, 'r', encoding = 'utf-8') as MatchedChunksJson:
                EditGenerationKoChunks = json.load(MatchedChunksJson)
                
                ## EditGenerationKoChunks의 Dic(프로세스)
                EditGenerationKoChunks = EditGenerationKoChunksToList(EditGenerationKoChunks)

        ## 일부만 생성하는지, 전체를 생성하는지의 옵션
        if Mode == 'Manual':
            GenerationKoChunks = []
            for GenerationKoChunk in EditGenerationKoChunks:
                if GenerationKoChunk['ActorName'] == Actor:
                    GenerationKoChunks.append(GenerationKoChunk)
        elif Mode == 'Auto':
            GenerationKoChunks = EditGenerationKoChunks

        ## VoiceLayerGenerator 생성
        GenerationKoChunksCount = len(GenerationKoChunks)
        
        ## TQDM 셋팅
        UpdateTQDM = tqdm(GenerationKoChunks,
                        total = GenerationKoChunksCount,
                        desc = 'VoiceLayerGenerator')

        ## 히스토리 불러오기
        fileName = projectName + '_' + 'VoiceLayer_History_' + Actor + '.json'
        MatchedChunkHistorysPath = VoiceLayerPathGen(projectName, email, fileName, 'Mixed')
        if os.path.exists(MatchedChunkHistorysPath):
            with open(MatchedChunkHistorysPath, 'r', encoding = 'utf-8') as MatchedChunkHistorysJson:
                GenerationKoChunkHistorys = json.load(MatchedChunkHistorysJson)
        else:
            GenerationKoChunkHistorys = []

        ### 생성시작 ###
        _LastPitchSwitch = 0
        for Update in UpdateTQDM:
            UpdateTQDM.set_description(f"ChunkToSpeech: ({Update['ActorName']}), {Update['EditId']}: {Update['ActorChunk']}")
            EditId = Update['EditId']
            Name = Update['ActorName']
            Pause = Update['Pause']
            
            ## ElevenLabs Chunk Modify ##
            def ModifyELChunk(chunk):
                # 1. Chunk 마지막 3개의 글자 중에 . 과 , 이 포함되어 있으면 이를 모두 삭제하고 .하나만 표기
                if '.' in chunk[-3:] or ',' in chunk[-3:]:
                    chunk = chunk[:-3] + chunk[-3:].replace('.', '').replace(',', '') + '.'
                # 2. ~.은 ,로 변경
                chunk = chunk.replace('~.', ',')
                # 3. Chunk의 마지막 3개를 제외하고 .이 포함되면 이를 모두 삭제
                chunk = chunk[:-3].replace('.', '') + chunk[-3:]
                return chunk
            
            ## ElevenLabs Chunk
            EL_Chunk = None
            if Api == 'ElevenLabs':
                ELChunks = []
                for _ELChunk in Update['ActorChunk']:
                    ELChunk = ModifyELChunk(_ELChunk)
                    ELChunks.append(ELChunk)
                EL_Chunk = " ".join(ELChunks)
                # print(f"ChunkModify: ({EL_Chunk})")
            ## ElevenLabs Chunk Modify ##

            Chunk = " ".join(Update['ActorChunk'])
            ChunkCount = len(Update['ActorChunk']) - 1 # 파일의 마지막 순번을 표기

            #### Split을 위한 딕셔너리 리스트 생성 ####
            rawSplitChunks = [chunk.replace('~.', '').replace('.,', '').replace('.,', '') for chunk in Update['ActorChunk']]
            SplitChunks = []
            for i in range(len(rawSplitChunks)):
                SplitChunk = {'낭독문장번호': i + 1, '낭독문장': rawSplitChunks[i]}
                SplitChunks.append(SplitChunk)
            #### Split을 위한 딕셔너리 리스트 생성 ####

            ## 수정생성(Modify) 여부확인 ##
            Modify = "No"
            for History in GenerationKoChunkHistorys:
                if History['EditId'] == EditId:
                    if History['ActorName'] != Name:
                        History['ActorName'] = Name
                        Modify = "Yes"
                    if History['ActorChunk'] != Chunk:
                        History['ActorChunk'] = Chunk
                        Modify = "Yes"
                    if History['Pause'] != Pause:
                        History['Pause'] = Pause
                        Modify = "Yes"

            ## TypeCast ApiSetting ##
            if Api == 'TypeCast':
                ## 보이스 선정 ##                
                for VoiceData in VoiceDataSetCharacters:
                    if Name == VoiceData['Name']:
                        ApiSetting = VoiceData['ApiSetting']
                        name = ApiSetting['name']
                        EMOTION = ApiSetting['emotion_tone_preset']['emotion_tone_preset']
                        SPEED = ApiSetting['speed_x']
                        Pitch = ApiSetting['pitch']
                
                ## 'Narrator', 'Character' 태그가 아닌 경우 끝음 조절하기 ##
                if Update['Tag'] not in ['Narrator', 'Character']:
                    LASTPITCH = [-2]
                    _LastPitchSwitch = 1
                elif _LastPitchSwitch == 1:
                    LASTPITCH = [-2]
                    _LastPitchSwitch = 0
                else:
                    LASTPITCH = ApiSetting['last_pitch']
            
            ## ElevenLabs ApiSetting ##
            elif Api == 'ElevenLabs':
                ApiSetting = MatchedActor['ApiSetting']
                name = ApiSetting['name']
                EMOTION = ['None']
                SPEED = [1.00]
                Pitch = 0
                LASTPITCH = [0]
            
            ## TypeCastMacro에 따른 restart 코드 ##
            restart = True
            while restart:
                restart = False  # 반복 시작 시 재시작 플래그를 초기화                   
                # 단어로 끝나는 경우 끝음 조절하기
                if '?' not in Chunk[-3:]:
                    if '.' not in Chunk[-3:]:
                        lastpitch = [-2]
                    elif '다' not in Chunk[-3:]:
                        lastpitch = [-2]
                    else:
                        lastpitch = LASTPITCH
                else:
                    lastpitch = LASTPITCH
                ## 'Narrator', 'Character' 태그가 아닌 경우 감정은 가장 평범한 1번 감정으로 하기 ##
                if Update['Tag'] in ['Narrator', 'Character']:
                    RandomEMOTION = random.choice(EMOTION)
                else:
                    RandomEMOTION = EMOTION[0]
                RandomSPEED = random.choice(SPEED)
                RandomLASTPITCH = random.choice(lastpitch)

                ## 수정 여부에 따라 파일명 변경 ##
                if Modify == "Yes":
                    FileName = projectName + '_' + str(EditId) + '_' + Name + 'M.wav'
                    voiceLayerPath = VoiceLayerPathGen(projectName, email, FileName, 'Mixed')
                    ChangedName = ActorVoiceGen(projectName, email, VoiceReverbe, Update['Tag'], name, Chunk, EL_Chunk, Api, ApiSetting, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath, SplitChunks, MessagesReview)
                    if ChangedName != 'Continue':
                        if Macro == "Auto":
                            TypeCastMacro(ChangedName, Account)
                            time.sleep(random.randint(3, 5))
                            restart = True
                        else:
                            print(f'\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n@  캐릭터 불일치 -----> [TypeCastAPI의 캐릭터를 ( {ChangedName} ) 으로 변경하세요!] <-----  @\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n')
                            sys.exit()
                    else:
                        with open(MatchedChunkHistorysPath, 'w', encoding = 'utf-8') as json_file:
                            json.dump(GenerationKoChunkHistorys, json_file, ensure_ascii = False, indent = 4)
                else:
                    FileName = projectName + '_' + str(EditId) + '_' + Name + '.wav'
                    voiceLayerPath = VoiceLayerPathGen(projectName, email, FileName, 'Mixed')
                    if not os.path.exists(voiceLayerPath.replace(".wav", "") + f'_({ChunkCount}).wav') and not os.path.exists(voiceLayerPath.replace(".wav", "") + f'_({ChunkCount})M.wav'):
                        ChangedName = ActorVoiceGen(projectName, email, VoiceReverbe, Update['Tag'], name, Chunk, EL_Chunk, Api, ApiSetting, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath, SplitChunks, MessagesReview)

                        if ChangedName == 'Continue':
                            ## 히스토리 저장 ##
                            # 동일한 EditId와 ActorName을 가진 항목이 있는지 확인
                            AddSwitch = True  # 새 항목을 추가해야 하는지 여부를 나타내는 플래그
                            for history in GenerationKoChunkHistorys:
                                if history["EditId"] == EditId and history["ActorName"] == Name:
                                    AddSwitch = False
                                    break

                            # 동일한 EditId와 ActorName을 가진 항목이 없을 경우 새 항목 추가
                            if AddSwitch:
                                GenerationKoChunkHistory = {"EditId": EditId, "Tag": Update['Tag'], "ActorName": Name, "ActorChunk": Chunk, "Pause": Pause}
                                GenerationKoChunkHistorys.append(GenerationKoChunkHistory)
                                with open(MatchedChunkHistorysPath, 'w', encoding = 'utf-8') as json_file:
                                    json.dump(GenerationKoChunkHistorys, json_file, ensure_ascii = False, indent = 4)
                            ## 히스토리 저장 ##
                        else:
                            if Macro == "Auto":
                                TypeCastMacro(ChangedName, Account)
                                time.sleep(random.randint(3, 5))
                                restart = True
                            else:
                                print(f'\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n@  캐릭터 불일치 -----> [TypeCastAPI의 캐릭터를 ( {ChangedName} ) 으로 변경하세요!] <-----  @\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n')
                                sys.exit()

    ## 최종 생성된 음성파일 합치기 ##
    time.sleep(0.1)
    EditGenerationKoChunks = VoiceGenerator(projectName, email, EditGenerationKoChunks, MatchedChunksPath, Narrator, CloneVoiceName, CloneVoiceActorPath, VoiceEnhance = VoiceEnhance, VoiceFileGen = VoiceFileGen)
    
    return EditGenerationKoChunks

## 프롬프트 요청 및 결과물 Json을 VoiceLayer에 업데이트
def VoiceLayerUpdate(projectName, email, Narrator = 'VoiceActor', CloneVoiceName = '저자명', VoiceReverbe = 'on', MainLang = 'Ko', Mode = "Manual", Macro = "Auto", Account = "None", Intro = "None", VoiceEnhance = 'off', VoiceFileGen = "on", MessagesReview = "off"):
    print(f"< User: {email} | Project: {projectName} | VoiceLayerGenerator 시작 >")
    
    EditGenerationKoChunks = VoiceLayerSplitGenerator(projectName, email, Narrator = Narrator, CloneVoiceName = CloneVoiceName, VoiceReverbe = VoiceReverbe, MainLang = MainLang, Mode = Mode, Macro = Macro, Account = Account, VoiceEnhance = VoiceEnhance, VoiceFileGen = VoiceFileGen, MessagesReview = MessagesReview)

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
        
    print(f"[ User: {email} | Project: {projectName} | VoiceLayerGenerator 완료 ]\n")
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "웹3.0메타버스"
    mainLang = 'Ko'
    mode = "Manual"
    macro = "Manual"
    #########################################################################