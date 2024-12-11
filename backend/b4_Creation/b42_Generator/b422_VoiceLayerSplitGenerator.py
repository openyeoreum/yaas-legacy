import os
import unicodedata
import json
import math
import requests
import time
import random
import re
import copy
import shutil
import sox
import subprocess
import numpy as np
import pyloudnorm as pyln
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from time import sleep
from difflib import SequenceMatcher
from datetime import datetime
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
    # print(f"@@@@@{CharacterCompletion}")
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
            if VoiceData['Choice'] == 'Narrator' and VoiceData['Quilty'] != 0:
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
    
    ActorChunk = ActorChunk[:-3] + ActorChunk[-3:].replace('.', '').replace(',', '') + '.'
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
            # print(f'{ActorChunk[i]}\n')
            _ActorChunk.append(ActorChunk[i]['Chunk'])
            Pause.append(ActorChunk[i]['Pause'])
            EndTime.append(ActorChunk[i]['EndTime'])
        EditGenerationKoListChunks.append({"EditId": EditId, "ChunkId": ChunkId, "Tag": Tag, "ActorName": ActorName, "ActorChunk": _ActorChunk, "Pause": Pause, "EndTime": EndTime})
    
    return EditGenerationKoListChunks

## TypecastVoice 생성 ##
def ActorVoiceGen(projectName, email, Modify, ModifyFolderPath, BracketsSwitch, bracketsSplitChunksNumber, voiceReverbe, tag, name, Chunk, EL_Chunk, Api, ApiSetting, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath, SplitChunks, MessagesReview):
    attempt = 0

    ### 음성 속도 조절 함수 ###
    def ChangeSpeedIndexVoice(VoicePath, Volume = 1.0, Speed = 1.0, Pad = 1.0, Reverb = 'off', Reverberance = 5, RoomScale = 5, HighFreqDamping = 10, PreDelay = 3):
        CopyFilePath = VoicePath.replace('.wav', '_Change.wav')
        shutil.copyfile(VoicePath, CopyFilePath)
        
        tfm = sox.Transformer()
        # 속도를 줄임 (피치 유지)
        tfm.tempo(Speed, 's')
        # 1초 추가(잔향의 끊어짐 방지)
        tfm.pad(0, Pad)
        if Reverb == 'on':
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
        Volume = ApiSetting['Volume']
        Stability = random.choice(ApiSetting['stability'])
        SimilarityBoost = random.choice(ApiSetting['similarity_boost'])
        Style = random.choice(ApiSetting['style'])
        Model = ApiSetting['models']['Ko']
        
        while attempt < 65:
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
                if Volume != 0:
                    Voice_Audio_Mp3 = Voice_Audio_Mp3 + Volume
                Voice_Audio_Mp3.export(fileName, format = "wav")
                os.remove(fileNameMp3)

                ## VoiceReverbe ##
                if voiceReverbe == 'on':
                    ## tag가 Title, Logue인 경우 ##
                    if tag in ['Title', 'Logue']:
                        print(f"ChangeSpeed(0.89): ({tag}) Voice waiting 1-2 second")
                        ChangeSpeedIndexVoice(fileName, Volume = 1.04, Speed = 0.95, Pad = 0.5, Reverb = 'off')

                    ## tag가 Title, Logue, Part, Chapter, Index인 경우 ##
                    if tag in ['Part', 'Chapter', 'Index']:
                        print(f"ChangeSpeed(0.91): ({tag}) Voice waiting 1-2 second")
                        ChangeSpeedIndexVoice(fileName, Volume = 1.07, Speed = 0.95, Pad = 1.0, Reverb = 'off')
                
                if len(SplitChunks) > 1:
                    ### 음성파일을 분할하는 코드 ###
                    RetryIdList, segment_durations = VoiceSplit(projectName, email, Modify, ModifyFolderPath, BracketsSwitch, bracketsSplitChunksNumber, name, voiceLayerPath, SplitChunks, MessagesReview = MessagesReview)
                    if RetryIdList != []:
                        return RetryIdList
                # 수정 파일 별도 저장
                if len(SplitChunks) == 1 and Modify == "Yes":
                    Voice_Audio_Wav = AudioSegment.from_wav(fileName)
                    InspectionExportPath = fileName.replace("_(0)M.wav", "_(0)Modify.wav")
                    InspectionExportFolder, InspectionExportFile = os.path.split(InspectionExportPath)
                    InspectionExportMasterFilePath = os.path.join(ModifyFolderPath, InspectionExportFile)
                    Voice_Audio_Wav.export(InspectionExportMasterFilePath, format = "wav")

                return "Continue"
                ########## ElevenLabs API 요청 ##########
            except KeyError as e:
                attempt += 1
                print(f"[ KeyError 발생, 1분 후 재시도 {attempt}/65: {e} ]")
                time.sleep(60)  # 1분 대기 후 재시도
                
            except Exception as e:
                attempt += 1
                if attempt >= 5:
                    sys.exit(f"[ 예상치 못한 에러 발생: {e}, 5초 후 재시도 {attempt}/65: {e} ]")
                else:
                    print(f"[ 예상치 못한 에러 발생: {e}, 5초 후 재시도 {attempt}/65: {e} ]")
                    time.sleep(5)

    ################
    ### TypeCast ###
    ################
    if Api == "TypeCast":
        while attempt < 65:
            try:
                ########## TypeCast API 요청 ##########
                API_TOKEN = os.getenv("TYPECAST_API_TOKEN")
                HEADERS = {'Authorization': f'Bearer {API_TOKEN}'}

                # get my actor
                r = requests.get('https://typecast.ai/api/actor', headers = HEADERS)
                my_actors = r.json()['result']
                
                if my_actors[0]['name']['ko'] == name:
                    # print(f'Chunk: {Chunk}')
                    # print(f'RandomEMOTION: {RandomEMOTION}')
                    # print(f'RandomSPEED: {RandomSPEED}')
                    # print(f'Pitch: {Pitch}')
                    # print(f'RandomLASTPITCH: {RandomLASTPITCH}')
                    # print(f'voiceLayerPath: {voiceLayerPath}')
                    # print(f'my_actors: {my_actors}')
                    my_first_actor = my_actors[0]
                    my_first_actor_id = my_first_actor['actor_id']

                    # request speech synthesis
                    r = requests.post('https://typecast.ai/api/speak', headers=HEADERS, json={
                        'text': Chunk, # 음성을 합성하는 문장
                        'lang': 'auto', # text의 언어 코드['en-us', 'ko-kr', 'ja-jp', 'es-es', 'auto'], auto는 자동 언어 감지
                        'actor_id': my_first_actor_id, # 캐릭터 아이디로 Actor API에서 캐릭터를 검색
                        'xapi_hd': True, # 샘플레이트로 True는 고품질(44.1KHz), False는 저품질(16KHz)
                        'model_version': 'latest', # 모델(캐릭터) 버전으로 API를 참고, 최신 모델은 "latest"
                        'xapi_audio_format': 'wav', # 오디오 포멧으로 기본값은 'wav', 'mp3'
                        'emotion_tone_preset': RandomEMOTION,
                        'emotion_prompt': None, # 감정 프롬프트(한/영)를 입력, 입력시 'emotion_tone_preset'는 'emotion_prompt'로 설정
                        'volume': 120, # 오디오 볼륨으로 기본값은 100, 범위: 0.5배는 50 - 2배는 200
                        'speed_x': RandomSPEED, # 말하는 속도로 기본값은 1, 범위: 0.5(빠름) - 1.5(느림)
                        'tempo': 1.0, # 음성 재생속도로 기본값은 1, 범위: 0.5(0.5배 느림) - 2.0(2배 빠름)
                        'pitch': Pitch, # 음성 피치로 기본값은 0, 범위: -12 - 12
                        'max_seconds': 60, # 음성의 최대 길이로 기본값은 30, 범위: 1 - 60
                    #     'force_length': 0, # text의 시간을 max_seconds에 맞추려면 1, 기본값은 0
                        'last_pitch': RandomLASTPITCH
                    })
                    speak_url = r.json()['result']['speak_v2_url']

                    # polling the speech synthesis result
                    for _ in range(120):
                        r = requests.get(speak_url, headers = HEADERS)
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
                            ChangeSpeedIndexVoice(fileName, Volume = 1.07, Speed = 0.95, Pad = 0.5, Reverb = 'off')

                        ## tag가 Title, Logue, Part, Chapter, Index인 경우 ##
                        if tag in ['Part', 'Chapter', 'Index']:
                            print(f"ChangeSpeed(0.91): ({tag}) Voice waiting 1-2 second")
                            ChangeSpeedIndexVoice(fileName, Volume = 1.07, Speed = 0.97, Pad = 1.0, Reverb = 'off')

                        ## tag가 Character인 경우 ##
                        if tag in ['Character']:
                            print(f"ChangeSpeed(1.07): ({tag}) Voice waiting 1-2 second")
                            ChangeSpeedIndexVoice(fileName, Volume = 1.00, Speed = 1.07, Pad = 0.5, Reverb = 'off')

                    if len(SplitChunks) > 1:
                        ### 음성파일을 분할하는 코드 ###
                        RetryIdList, segment_durations = VoiceSplit(projectName, email, Modify, ModifyFolderPath, BracketsSwitch, bracketsSplitChunksNumber, name, voiceLayerPath, SplitChunks, MessagesReview = MessagesReview)
                        if RetryIdList != []:
                            return RetryIdList
                    # 수정 파일 별도 저장
                    if len(SplitChunks) == 1 and Modify == "Yes":
                        Voice_Audio_Wav = AudioSegment.from_wav(fileName)
                        InspectionExportPath = fileName.replace("_(0)M.wav", "_(0)Modify.wav")
                        InspectionExportFolder, InspectionExportFile = os.path.split(InspectionExportPath)
                        InspectionExportMasterFilePath = os.path.join(ModifyFolderPath, InspectionExportFile)
                        Voice_Audio_Wav.export(InspectionExportMasterFilePath, format = "wav")

                    return "Continue"
                else:
                    return name
                ########## TypeCast API 요청 ##########
            except KeyError as e:
                attempt += 1
                print(f"[ KeyError 발생, 1분 후 재시도 {attempt}/65: {e} ]")
                time.sleep(60)  # 1분 대기 후 재시도
                
            except Exception as e:
                attempt += 1
                if attempt >= 5:
                    sys.exit(f"[ 예상치 못한 에러 발생: {e}, 5초 후 재시도 {attempt}/65: {e} ]")
                else:
                    print(f"[ 예상치 못한 에러 발생: {e}, 5초 후 재시도 {attempt}/65: {e} ]")
                    time.sleep(5)
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
def SortAndRemoveDuplicates(editGenerationKoChunks, files, voiceLayerPath, projectName):
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
        # 1. 동일한 EditId에서 가장 큰 DetailEditNum 찾기
        max_detail_nums = {}
        for info in editInfos:
            print(f"[ 파일 생성 또는 EditId 확인 필요: {info} ]")
            edit_id = info['EditId']
            detail_num = info['DetailEditNum']
            max_detail_nums[edit_id] = max(max_detail_nums.get(edit_id, -1), detail_num)

        # 2. RemoveVoiceFileList 생성
        RemoveVoiceFileList = []
        for edit_id, max_num in max_detail_nums.items():
            for i in range(1, 11):
                RemoveVoiceFileList.append({'EditId': edit_id, 'DetailEditNum': max_num + i})

        # 3. 파일 삭제
        # 폴더 내의 모든 파일 리스트를 가져옴
        all_files = os.listdir(voiceLayerPath)
        for item in RemoveVoiceFileList:
            edit_id = item['EditId']
            detail_num = item['DetailEditNum']
            # 정규표현식 패턴 생성
            # 보이스이름이 어떠한 텍스트라도 올 수 있으므로 .*으로 처리
            pattern_with_m = re.compile(rf"{projectName}_{edit_id}_.+\({detail_num}\)M\.wav$")
            pattern_without_m = re.compile(rf"{projectName}_{edit_id}_.+\({detail_num}\)\.wav$")
            
            # 파일명 필터링 및 삭제
            for file_name in all_files:
                file_path = os.path.join(voiceLayerPath, file_name)
                
                if pattern_with_m.match(file_name) or pattern_without_m.match(file_name):
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"[ Chunk의 수가 줄어서, 그 수를 넘어서는 파일 삭제: {file_name} ]")
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
    
    # FilteredFiles의 그룹화 및 EditGenerationKoChunks를 벗어나는 파일 범위 리스트에서 삭제
    FilteredFilesGroups = {}
    # Process each filename
    for filename in UniqueFiles:
        parts = filename.split('_')
        if len(parts) >= 3:
            number = parts[2]  # Extract the 'number' part
            if number not in FilteredFilesGroups:
                FilteredFilesGroups[number] = []
            FilteredFilesGroups[number].append(filename)
        else:
            print(f"Filename '{filename}' does not match the expected format.")

    # Convert the groups to a list of lists, sorted by number
    FilteredGroupFiles = [group for key, group in sorted(FilteredFilesGroups.items(), key=lambda x: float(x[0]) if x[0].replace('.', '', 1).isdigit() else x[0])]

    # FilteredFiles 재구성
    FilteredFiles = []
    for i in range(len(editGenerationKoChunks)):
        for j in range(len(editGenerationKoChunks[i]['Pause'])):
            FilteredFiles.append(FilteredGroupFiles[i][j])

    return FilteredFiles

## voiceLayer의 모든 볼륨을 일정하게 만듬(아주 중요!)
## 동일화된 Voice파일들 원본을 Raw_로 저장(여러번 실행시 음질저하 문제 해결을 위해 아주 중요!)
def VolumeEqualization(voiceLayerPath, RawFiles, Mode = 'Raw', target_lufs = -23.0, extra_gain_db = 2.0):
    print('[ VolumeEqualization : Mastering ]')
    if Mode == 'Raw':
        # 백업 폴더 생성
        backup_folder = os.path.join(voiceLayerPath, 'VolumeEqualizationBackup')
        # 폴더가 존재하면 삭제
        if os.path.exists(backup_folder):
            shutil.rmtree(backup_folder)
        # 빈 폴더 생성
        os.makedirs(backup_folder, exist_ok = True)

    # 오디오 파일 로드
    audio_segments = [AudioSegment.from_wav(os.path.join(voiceLayerPath, filename)) for filename in RawFiles]
    meter = pyln.Meter(44100)  # 표준 샘플 레이트

    UpdateTQDM = tqdm(audio_segments,
                      total=len(audio_segments),
                      desc=f'{Mode}_VolumeEqualization')

    for i, audio in enumerate(audio_segments):
        try:
            # 오디오를 numpy array로 변환 (LUFS 측정용)
            audio_samples = np.array(audio.get_array_of_samples(), dtype=np.float32) / (1 << (audio.sample_width * 8 - 1))
            
            # 짧은 오디오 확인 및 파일명 출력
            if len(audio_samples) < meter.block_size:
                UpdateTQDM.update(1)  # tqdm 업데이트
                continue  # 짧은 파일은 건너뛰기

            # LUFS 측정
            loudness = meter.integrated_loudness(audio_samples)
            # 목표 LUFS에 맞춰 볼륨 조정
            adjustment_db = target_lufs - loudness
            adjusted_audio = audio.apply_gain(adjustment_db)
            # 추가 볼륨 증가
            adjusted_audio = adjusted_audio.apply_gain(extra_gain_db)
            # 클리핑 방지
            if adjusted_audio.max_dBFS > 0:
                adjusted_audio = adjusted_audio.normalize()
            # 기존 파일을 백업 폴더에 복사
            original_file = os.path.join(voiceLayerPath, RawFiles[i])
            if Mode == 'Raw':
                backup_file = os.path.join(backup_folder, RawFiles[i])
                shutil.copyfile(original_file, backup_file)
            # 새로운 오디오로 기존 파일 덮어쓰기
            adjusted_audio.export(original_file, format = 'wav')
            # tqdm 업데이트
            UpdateTQDM.update(1)

        except ValueError as e:
            if Mode == 'Raw':
                # 오류 발생 시 파일을 백업 폴더에 복사
                original_file = os.path.join(voiceLayerPath, RawFiles[i])
                backup_file = os.path.join(backup_folder, RawFiles[i])
                shutil.copyfile(original_file, backup_file)
            UpdateTQDM.update(1)  # tqdm 업데이트 후 계속 진행

    # tqdm 닫기
    UpdateTQDM.close()
    # 메모리 해제
    audio_segments = []

## 생성된 음성파일 합치기
def VoiceGenerator(projectName, email, EditGenerationKoChunks, MatchedChunksPath, Narrator, CloneVoiceName, CloneVoiceActorPath, VoiceEnhance = 'off', VoiceFileGen = 'on', VolumeEqual = 'Mixing'):
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
    # VoiceFilePattern = r".*?_(\d+(?:\.\d+)?)_([가-힣]+\(.*?\))_\((\d+)\)M?\.wav"
    VoiceFilePattern = r".*?_(\d+(?:\.\d+)?)_([가-힣A-Za-z]+\(.*?\))_\((\d+)\)M?\.wav"

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
    FilteredFiles = SortAndRemoveDuplicates(EditGenerationKoChunks, Files, voiceLayerPath, projectName)
    #### VolumeEqualization ####
    if VolumeEqual == "Mastering":
        VolumeEqualization(voiceLayerPath, FilteredFiles)
    #### VolumeEqualization ####
    FilesCount = 0
    file_limit = 100  # 파일 분할 기준
    current_file_index = 1
    CombinedSound = AudioSegment.empty()
    VoiceEnhanceCompletionSwitch = False
    if Narrator == 'VoiceClone':
        with open(CloneVoiceActorPath, 'r', encoding = 'utf-8') as CloneVoiceActorJson:
            CloneVoiceActor = json.load(CloneVoiceActorJson)
        VoiceEnhanceCompletion = CloneVoiceActor['ApiSetting']['VoiceEnhanceCompletion']

    UpdateTQDM = tqdm(EditGenerationKoChunks,
                    total = len(EditGenerationKoChunks),
                    desc = 'VoiceGenerator')

    #### DeNoise ####
    # DeNoiseVoiceLayer경로 및 폴더 생성
    Project_DeNoiseVoiceLayerPath = voiceLayerPath.replace('/VoiceLayers/', f'/VoiceLayers/{projectName}_DeNoiseVoiceLayer/')
    DeNoiseVoiceLayerPath = os.path.join(Project_DeNoiseVoiceLayerPath, 'DeNoiseVoiceLayer')
    DeNoiseVoicesFilePath = os.path.join(Project_DeNoiseVoiceLayerPath, f'{projectName}_DeNoiseVoiceBook.wav')
    VoiceBookSplitList = [{'DeNoiseVoice_SplitPoint': 'No'}, {'DeNoiseVoiceBookFilePath': DeNoiseVoicesFilePath, 'Length': None}]
    if not os.path.exists(DeNoiseVoiceLayerPath):
        os.makedirs(DeNoiseVoiceLayerPath)
    #### DeNoise ####

    # 전체 오디오 클립의 누적 길이를 추적하는 변수 추가
    total_duration_seconds = 0
    Length = 0
    CombinedSoundLength = 0
    for Update in UpdateTQDM:
        Update['EndTime'] = []
        for j in range(len(Update['Pause'])):
            VoiceFilePath = os.path.join(voiceLayerPath, FilteredFiles[FilesCount])
            DeNoiseVoiceFilePath = os.path.join(DeNoiseVoiceLayerPath, FilteredFiles[FilesCount])
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
            
            #### DeNoise .json 생성 ####
            voice_ms = sound_file.duration_seconds
            pause_ms = silence.duration_seconds
            Start = Length
            End = Length + voice_ms
            CombinedSound_ms = CombinedSoundLength + CombinedSound.duration_seconds
            CombinedSoundData_ms = End + pause_ms
            VoiceBookSplitDic = {'DeNoiseVoiceFilePath': DeNoiseVoiceFilePath, 'Length': {'CombinedSound': CombinedSound_ms * 1000, 'CombinedSoundData': CombinedSoundData_ms * 1000, 'Start': Start * 1000, 'End': End * 1000, 'Voice': voice_ms * 1000, 'Pause': pause_ms * 1000}}
            VoiceBookSplitList.append(VoiceBookSplitDic)
            LengthDifference =  CombinedSoundData_ms - CombinedSound_ms
            Length +=  voice_ms + pause_ms - LengthDifference
            #### DeNoise .json 생성 ####

            # 누적된 CombinedSound의 길이를 전체 길이 추적 변수에 추가
            total_duration_seconds += sound_file.duration_seconds + PauseDuration_ms / 1000.0
            # EndTime에는 누적된 전체 길이를 저장
            Update['EndTime'].append(total_duration_seconds)

            # 파일 단위로 저장 및 CombinedSound 초기화
            if FilesCount % file_limit == 0 or FilesCount == len(FilteredFiles):
                MinNumber = current_file_index * file_limit - file_limit + 1
                MaxNumber = min(current_file_index * file_limit, len(FilteredFiles))
                file_name = f"{projectName}_VoiceLayer_{MinNumber}-{MaxNumber}.wav"
                CombinedSound.export(os.path.join(voiceLayerPath, file_name), format = "wav")
                CombinedSoundLength += CombinedSound.duration_seconds
                CombinedSound = AudioSegment.empty()  # 다음 파일 묶음을 위한 초기화
                current_file_index += 1
    
    # VoiceBook 최종 시간 입력
    VoiceBookSplitList[1]['Length'] = VoiceBookSplitList[-1]['Length']['End'] + len(silence)

    # for 루프 종료 후 남은 CombinedSound 처리 (특수경우)
    if not CombinedSound.empty():
        MinNumber = (current_file_index - 1) * file_limit + 1
        MaxNumber = FilesCount
        file_name = f"{projectName}_VoiceLayer_{MinNumber}-{MaxNumber}.wav"
        CombinedSound.export(os.path.join(voiceLayerPath, file_name), format="wav")
        # CombinedSound 초기화 필요 없음

    # 저자 성우 음성 노이즈 제거 되었다면 "Completion" 생성
    if VoiceEnhanceCompletionSwitch:
        CloneVoiceActor['ApiSetting']['VoiceEnhanceCompletion'] = "Completion"
        with open(CloneVoiceActorPath, 'w', encoding = 'utf-8') as CloneVoiceActorJson:
            json.dump(CloneVoiceActor, CloneVoiceActorJson, ensure_ascii = False, indent = 4)
        
    # 최종 파일 합치기
    FinalCombined = AudioSegment.empty()
    for i in range(1, current_file_index + 1):  # current_file_index + 1로 수정
        MinNumber = (i - 1) * file_limit + 1
        if i * file_limit < FilesCount:
            MaxNumber = i * file_limit
        else:
            MaxNumber = FilesCount  # 마지막 파일의 MaxNumber는 FilesCount로 설정
        part_name = f"{projectName}_VoiceLayer_{MinNumber}-{MaxNumber}.wav"
        part_path = os.path.join(voiceLayerPath, part_name)
        # 파일이 존재하는지 확인
        if os.path.exists(part_path):
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
        
        #### DeNoise ####
        # VoiceBookSplitList 저장
        VoiceBookSplitListName = '[' + projectName + '_' + 'DeNoiseVoice_SplitPoint].json'
        VoiceBookSplitListPath = VoiceLayerPathGen(projectName, email, VoiceBookSplitListName, 'Mixed')
        with open(VoiceBookSplitListPath, 'w', encoding = 'utf-8') as VoiceBookSplitListJson:
            json.dump(VoiceBookSplitList, VoiceBookSplitListJson, ensure_ascii = False, indent = 4)

        # DeNoiseVoiceLayer 폴더에 {projectName}_DeNoiseVoiceBook 파일이 존재할 경우 분할 처리
        if os.path.exists(DeNoiseVoicesFilePath):
            if not os.path.exists(VoiceBookSplitList[2]['DeNoiseVoiceFilePath']):
                print(f"[ De-Noise Voice 파일 분할 저장 ]\n{DeNoiseVoicesFilePath}")
                SplitData = VoiceBookSplitList[2:]

                UpdateTQDM = tqdm(SplitData,
                    total = len(SplitData),
                    desc = 'DeNoiseVoiceFileSplit')

                # DeNoiseVoice 파일 분할
                for Dic in UpdateTQDM:
                    start_ms = int(Dic['Length']['Start'])  # 시작 시간 (밀리초)
                    end_ms = int(Dic['Length']['End'])      # 종료 시간 (밀리초)
                    SplitedDeNoiseVoicePath = Dic['DeNoiseVoiceFilePath']
                    start_sec = start_ms / 1000
                    duration_sec = (end_ms - start_ms) / 1000
                    cmd = [
                        'ffmpeg',
                        '-ss', str(start_sec),
                        '-t', str(duration_sec),
                        '-i', DeNoiseVoicesFilePath,
                        '-acodec', 'pcm_s16le',  # WAV 형식으로 인코딩
                        '-ar', '44100',          # 샘플링 레이트 설정 (필요에 따라 조정)
                        SplitedDeNoiseVoicePath
                    ]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print(f"[ >>> 수동적인 De-Noise Voice 작업이 필요하다면 아래 경로에 '_VoiceBook.wav'파일을 DeNoising 하여, '_DeNoiseVoiceBook.wav' 파일을 생성 및 '_DeNoiseVoiceLayer' 폴더에 넣어주세요. <<< ]\n{DeNoiseVoicesFilePath}")
        #### DeNoise ####
    
    ## EditGenerationKoChunks의 Dic(검수)
    EditGenerationKoChunks = EditGenerationKoChunksToDic(EditGenerationKoChunks)
    ## EndTime이 업데이트 된 EditGenerationKoChunks 저장
    with open(MatchedChunksPath, 'w', encoding = 'utf-8') as json_file:
        json.dump(EditGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)
        
    return EditGenerationKoChunks

## 생성된 수정(Modify)파일 합치기
def ModifiedVoiceGenerator(ModifyFolderPath, ModifyFolderName, VolumeEqual):
    ModifyFileName = ModifyFolderName + '.wav'
    ModifyFilePath = os.path.join(ModifyFolderPath, ModifyFileName)
    # 파일 이름을 파싱하여 정렬하기 위한 함수
    ModifyStoragePath = "/yaas/storage/s1_Yeoreum/s19_ModifyStorage/"
    SentenceSeparatorPath = ModifyStoragePath + "1_ModifySound_문장사이음.wav"
    ParagraphSeparatorPath = ModifyStoragePath + "2_ModifySound_문단사이음.wav"
    # EditID 소리 출력
    Number_0_Path = ModifyStoragePath + "3_ModifySound_Zero.wav"
    Number_1_Path = ModifyStoragePath + "3_ModifySound_One.wav"
    Number_2_Path = ModifyStoragePath + "3_ModifySound_Two.wav"
    Number_3_Path = ModifyStoragePath + "3_ModifySound_Three.wav"
    Number_4_Path = ModifyStoragePath + "3_ModifySound_Four.wav"
    Number_5_Path = ModifyStoragePath + "3_ModifySound_Five.wav"
    Number_6_Path = ModifyStoragePath + "3_ModifySound_Six.wav"
    Number_7_Path = ModifyStoragePath + "3_ModifySound_Seven.wav"
    Number_8_Path = ModifyStoragePath + "3_ModifySound_Eight.wav"
    Number_9_Path = ModifyStoragePath + "3_ModifySound_Nine.wav"
    Number_Point_Path = ModifyStoragePath + "3_ModifySound_Point.wav"
    NumberSoundMap = {'0': Number_0_Path, '1': Number_1_Path, '2': Number_2_Path, '3': Number_3_Path, '4': Number_4_Path, '5': Number_5_Path, '6': Number_6_Path, '7': Number_7_Path, '8': Number_8_Path, '9': Number_9_Path, '.': Number_Point_Path}
    # EditID 소리 합성 함수
    def AudioNumber(number_str):
        # Create an empty AudioSegment
        audioNumber = AudioSegment.silent(duration=0)
        # Iterate over each character in the number string
        for char in number_str:
            if char in NumberSoundMap:
                # Load the corresponding sound file
                sound_file = NumberSoundMap[char]
                audio_segment = AudioSegment.from_file(sound_file) - 5
                # Append the audio segment to the output audio
                audioNumber += audio_segment
        
        return audioNumber

    # 문장과 문단 사이 소리 로드
    SentenceSeparator = AudioSegment.from_wav(SentenceSeparatorPath) - 5
    ParagraphSeparator = AudioSegment.from_wav(ParagraphSeparatorPath) - 5

    # 파일 이름을 파싱하여 정렬하기 위한 함수
    def ParseFilename(filename):
        parts = filename.split('_')
        paragraph = float(parts[2])
        if paragraph.is_integer():  # 소수점 이하가 0인 경우
            paragraph = int(paragraph)  # 정수로 변환
        sentence = int(parts[-1].split('(')[-1].split(')')[0])
        return paragraph, sentence

    # 폴더 내의 모든 .wav 파일 목록 추출
    RawModifiedFiles = [f for f in os.listdir(ModifyFolderPath) if f.endswith("Modify.wav")]
    # 모든 .wav 파일 목록의 노멀라이즈
    RawModifiedFiles = [unicodedata.normalize('NFC', s) for s in RawModifiedFiles]

    #### VolumeEqualization ####
    if VolumeEqual == "Mastering":
        VolumeEqualization(ModifyFolderPath, RawModifiedFiles, Mode = 'Modify')
    #### VolumeEqualization ####

    ## 폴더 내에 파일이 있으면 합치기 시작
    if RawModifiedFiles != []:
        # 파일을 정렬
        SortedModifiedFiles = sorted(RawModifiedFiles, key = ParseFilename)

        # 정렬된 파일을 병합
        FinalCombined = AudioSegment.empty()
        previous_paragraph = None
        previous_sentence = None

        UpdateTQDM = tqdm(SortedModifiedFiles,
                        total = len(SortedModifiedFiles),
                        desc = 'ModifiedVoiceGenerator')

        audio_segments = []

        for Update in UpdateTQDM:
            ModifiedFilePath = os.path.join(ModifyFolderPath, Update)
            ModifiedVoice = AudioSegment.from_wav(ModifiedFilePath)
            
            CurrentParagraph, CurrentSentence = ParseFilename(Update)

            if previous_paragraph is not None:
                if CurrentParagraph != previous_paragraph:
                    audio_segments.append(ParagraphSeparator)
                elif CurrentSentence != previous_sentence:
                    audio_segments.append(SentenceSeparator)
            
            audio_segments.append(ModifiedVoice)
            previous_paragraph = CurrentParagraph
            previous_sentence = CurrentSentence

        # 모든 세그먼트를 한 번에 합치기
        FinalCombined = sum(audio_segments)

        try:
            with open(ModifyFilePath, "wb") as VoiceFile:
                FinalCombined.export(VoiceFile, format = "wav")
                FinalCombined = AudioSegment.empty()
            # struct.error: 'L' format requires 0 <= number <= 4294967295 에러 방지 (4GB 용량 문제 방지)
        except:
            os.remove(ModifyFilePath)
            ModifyFilePathMp3 = ModifyFilePath.replace(".wav", ".mp3")
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
                TempPath = ModifyFilePathMp3.replace(".mp3", f"_Part{i+1}.mp3")
                with open(TempPath, "wb") as file:
                    print(f"[ 대용량 파일 분할 저장: {TempPath} ]")
                    part.export(file, format = "mp3", bitrate = "320k")
                    LoadedPart = AudioSegment.from_file(TempPath)
                    FinalCombinedPart1 += LoadedPart  # 파트 합치기
                os.remove(TempPath)  # 임시 파일 삭제
            FinalCombined = AudioSegment.empty()  # 메모리 해제
            
            # 최종 파일 저장
            with open(ModifyFilePathMp3.replace(".mp3", f"_(1).mp3"), "wb") as FinalCombined_file:
                FinalCombinedPart1.export(FinalCombined_file, format = "mp3", bitrate = "320k")
            FinalCombinedPart1 = AudioSegment.empty()  # 메모리 해제
                
            # 각 파트를 임시 파일로 저장 후 다시 로드하여 합치기
            FinalCombinedPart2 = AudioSegment.empty()
            for i, part in enumerate(parts[4:8]):
                TempPath = ModifyFilePathMp3.replace(".mp3", f"_Part{i+5}.mp3")
                with open(TempPath, "wb") as file:
                    print(f"[ 대용량 파일 분할 저장: {TempPath} ]")
                    part.export(file, format = "mp3", bitrate = "320k")
                    LoadedPart = AudioSegment.from_file(TempPath)
                    FinalCombinedPart2 += LoadedPart  # 파트 합치기
                os.remove(TempPath)  # 임시 파일 삭제

            # 최종 파일 저장
            with open(ModifyFilePathMp3.replace(".mp3", f"_(2).mp3"), "wb") as FinalCombined_file:
                FinalCombinedPart2.export(FinalCombined_file, format = "mp3", bitrate = "320k")
            FinalCombinedPart2 = AudioSegment.empty()  # 메모리 해제
                
            # 각 파트를 임시 파일로 저장 후 다시 로드하여 합치기
            FinalCombinedPart3 = AudioSegment.empty()
            for i, part in enumerate(parts[8:]):
                TempPath = ModifyFilePathMp3.replace(".mp3", f"_Part{i+9}.mp3")
                with open(TempPath, "wb") as file:
                    print(f"[ 대용량 파일 분할 저장: {TempPath} ]")
                    part.export(file, format = "mp3", bitrate = "320k")
                    LoadedPart = AudioSegment.from_file(TempPath)
                    FinalCombinedPart3 += LoadedPart  # 파트 합치기
                os.remove(TempPath)  # 임시 파일 삭제

            # 최종 파일 저장
            with open(ModifyFilePathMp3.replace(".mp3", f"_(3).mp3"), "wb") as FinalCombined_file:
                FinalCombinedPart3.export(FinalCombined_file, format = "mp3", bitrate = "320k")
            FinalCombinedPart3 = AudioSegment.empty()  # 메모리 해제
    ## 폴더 내에 파일이 없으면 폴더 삭제
    else:
        os.rmdir(ModifyFolderPath)

## CloneVoice 셋팅
def CloneVoiceSetting(projectName, Narrator, CloneVoiceName, MatchedActors, CloneVoiceActorPath, SelectionGenerationKoChunks):
    ## Narrator가 "CloneVoice" 인 경우 CloneVoiceDic 생성 ##
    if Narrator == 'VoiceClone' and CloneVoiceName != '':
        CloneVoiceFolderPath = CloneVoiceActorPath.replace('CloneVoice_Setting].json', 'CloneVoice_File]')
        if not os.path.exists(CloneVoiceActorPath):
            if not os.path.exists(CloneVoiceActorPath):
                os.mkdir(CloneVoiceFolderPath)
                print(f'[ 클로닝할 보이스 파일이 필요합니다 : {CloneVoiceFolderPath}, 보이스 파일을 폴더에 넣은 후 "VoiceFileCompletion": "Completion"으로 변경해 주세요 ]')
            CloneVoiceActor = {
                "Name": f"{CloneVoiceName}({projectName})-저자클로닝",
                "ApiSetting": {
                    "name": f"{CloneVoiceName}",
                    "Api": "ElevenLabs",
                    "voice_id": "Voice_id",
                    "stability": [0.80],
                    "similarity_boost": [0.80],
                    "style": [0.00],
                    "models": {"Ko": "eleven_multilingual_v2", "En": "eleven_turbo_v2_5", "Zh": "eleven_multilingual_v2"},
                    "Volume": 0,
                    "Speed": 1.10,
                    "Pitch": 0,
                    "VoiceFileSetting": {"Speed": 1.0, "Volume": 1.0, "Pitch": -0.3, "Reverbe": 'off'},
                    "VoiceFileCompletion": "세팅 완료 후 Completion",
                    "SettingCompletion": "세팅 완료 후 Completion",
                    "VoiceEnhanceCompletion": "None"
                }
            }
            with open(CloneVoiceActorPath, 'w', encoding = 'utf-8') as CloneVoiceActorJson:
                json.dump(CloneVoiceActor, CloneVoiceActorJson, ensure_ascii = False, indent = 4)
            sys.exit(f'[ 클론보이스 세팅을 완료하세요 : {CloneVoiceActorPath} ]')
        else:
            with open(CloneVoiceActorPath, 'r', encoding = 'utf-8') as CloneVoiceActorJson:
                CloneVoiceActor = json.load(CloneVoiceActorJson)
            VoiceFileCompletion = CloneVoiceActor['ApiSetting']['VoiceFileCompletion']
            Name = CloneVoiceActor['Name']
            Voice_id = CloneVoiceActor['ApiSetting']['voice_id']
            Stability = CloneVoiceActor['ApiSetting']['stability'][0]
            SimilarityBoost = CloneVoiceActor['ApiSetting']['similarity_boost'][0]
            Style = CloneVoiceActor['ApiSetting']['style'][0]
            
            Api_key = os.getenv("ELEVENLABS_API_KEY")
            client = ElevenLabs(api_key = Api_key)
            
            texts = [
                f"안녕하세요. 이 오디오북은, 여름의 인공지능 클로닝 기술로 제작된, {CloneVoiceName} 보이스로 낭독되었습니다.",
                f"Hello. This audiobook was, narrated in {CloneVoiceName}'s voice, produced using 여름's AI cloning technology.",
                f"你好.这本有声读物是由여름的人工智能克隆技术制作的,{CloneVoiceName}声音朗读的."
                ]
            langs = ["Ko", "En", "Zh"]
            
            if VoiceFileCompletion != 'Completion':
                sys.exit(f'[ 1) 클로닝할 보이스 파일이 필요합니다 : {CloneVoiceFolderPath}, 보이스 파일을 폴더에 넣어주세요 ]\n[ 2) "VoiceFileSetting" 값을 완성해 주세요 ]\n[ 3) "VoiceFileCompletion": "Completion"으로 변경해 주세요 ]')
            else:
                if Voice_id == "Voice_id":                   
                    # 클로닝할 보이스 파일 리스트 생성
                    VoiceFiles = os.listdir(CloneVoiceFolderPath)
                    _voiceFiles = [os.path.join(CloneVoiceFolderPath, file) for file in VoiceFiles if file.lower().endswith('.mp3')]
                    if '_CloningSetted' not in _voiceFiles[0]:
                        _SettedVoiceFiles = [os.path.join(CloneVoiceFolderPath, file.replace('.mp3', '_CloningSetted.mp3')) for file in VoiceFiles if file.lower().endswith('.mp3')]
                    
                    # 클로닝할 보이스 파일에 VoiceFileSetting 적용
                    CloneVoiceSpeed = CloneVoiceActor['ApiSetting']['VoiceFileSetting']['Speed']
                    CloneVoiceVolume = CloneVoiceActor['ApiSetting']['VoiceFileSetting']['Volume']
                    CloneVoicePitch = CloneVoiceActor['ApiSetting']['VoiceFileSetting']['Pitch']
                    CloneVoiceReverbe = CloneVoiceActor['ApiSetting']['VoiceFileSetting']['Reverbe']
                    if CloneVoiceSpeed != 1 or CloneVoiceVolume != 1 or CloneVoicePitch != 0 or CloneVoiceReverbe != 'off':
                        for i in range(len(_voiceFiles)):
                            tfm = sox.Transformer()
                            if CloneVoiceSpeed != 1:
                                tfm.tempo(CloneVoiceSpeed, 's')
                            if CloneVoiceVolume != 1:
                                tfm.vol(CloneVoiceVolume)
                            if CloneVoicePitch != 0:
                                tfm.pitch(CloneVoicePitch)
                            if CloneVoiceReverbe == 'on':
                                tfm.pad(0, 1)
                                tfm.reverb(reverberance = 4, room_scale = 4, high_freq_damping = 8, pre_delay = 2)
                            tfm.build(_voiceFiles[i], _SettedVoiceFiles[i])
                        _voiceFiles = _SettedVoiceFiles
                    
                    # 보이스 클로닝
                    VOICE = client.clone(
                        name = Name,
                        description = f"{Stability}/{SimilarityBoost}/{Style}",
                        files = _voiceFiles,
                    )
                    
                    # voice_id 생성 및 json 저장
                    CloneVoiceActor['ApiSetting']['voice_id'] = VOICE.voice_id
                    with open(CloneVoiceActorPath, 'w', encoding = 'utf-8') as CloneVoiceActorJson:
                        json.dump(CloneVoiceActor, CloneVoiceActorJson, ensure_ascii = False, indent = 4)

                    # 클로닝된 보이스 샘플 생성
                    for i in range(len(texts)):
                        if langs[i] == 'En':
                            Style = 0
                        Voice_Audio = client.generate(
                            text = texts[i],
                            voice = Voice(
                                voice_id = CloneVoiceActor['ApiSetting']['voice_id'],
                                settings = VoiceSettings(stability = Stability, similarity_boost = SimilarityBoost, style = Style, use_speaker_boost = True)
                            ),
                            model = CloneVoiceActor['ApiSetting']['models'][langs[i]]
                        )
                        SampleFile = f'{Name}_{Stability}-{SimilarityBoost}-{Style}_ClonedVoice({langs[i]}).mp3'
                        print(f"VoiceGen: completion, {SampleFile} waiting 1-5 second")
                        SamplefileName = os.path.join(CloneVoiceFolderPath, SampleFile)
                        save(Voice_Audio, SamplefileName)
                        
                    sys.exit(f'[ 샘플 {SamplefileName} 확인 후, 클론보이스 세팅을 완료하세요 : {CloneVoiceActorPath} ]')
                
            # 클론보이스 세팅이 완료되었는지 확인
            SettingCompletion = CloneVoiceActor['ApiSetting']['SettingCompletion']
            if SettingCompletion != 'Completion':
                # 클로닝된 보이스 샘플 생성
                for i in range(len(texts)):
                    if langs[i] == 'En':
                        Style = 0
                    Voice_Audio = client.generate(
                        text = texts[i],
                        voice = Voice(
                            voice_id = CloneVoiceActor['ApiSetting']['voice_id'],
                            settings = VoiceSettings(stability = Stability, similarity_boost = SimilarityBoost, style = Style, use_speaker_boost = True)
                        ),
                        model = CloneVoiceActor['ApiSetting']['models'][langs[i]]
                    )
                    SampleFile = f'{Name}_{Stability}-{SimilarityBoost}-{Style}_ClonedVoice({langs[i]}).mp3'
                    print(f"VoiceGen: completion, {SampleFile} waiting 1-5 second")
                    SamplefileName = os.path.join(CloneVoiceFolderPath, SampleFile)
                    save(Voice_Audio, SamplefileName)
                sys.exit(f'[ 샘플 {SamplefileName} 확인 후, 클론보이스 세팅을 완료하세요 : {CloneVoiceActorPath} ]')
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
    
    ## Narrator가 "VoiceActor" 이면서 성우가 지정된 경우 CloneVoiceDic 생성 ##
    elif Narrator == 'VoiceActor' and CloneVoiceName != '':
        # VoiceDataSetPath 로드
        VoiceDataSetPath = "/yaas/backend/b5_Database/b57_RelationalDatabase/b572_Character/b572-01_VoiceDataSet.json"
        with open(VoiceDataSetPath, 'r', encoding = 'utf-8') as VoiceDataSetJson:
            VoiceDataSet = json.load(VoiceDataSetJson)
        VoiceActos = VoiceDataSet[1]['CharactersKo']
        
        ## VoiceActor 매칭
        for VoiceActor in VoiceActos:
            if VoiceActor['Name'] == CloneVoiceName:
                MatchedVoiceActor = VoiceActor
        print(MatchedVoiceActor)
        ## MatchedVoices 변경
        for _Matched in MatchedActors:
            if _Matched['CharacterTag'] == 'Narrator':
                BeforeNarratorName = _Matched['ActorName']
                AfterNarratorName = MatchedVoiceActor['Name']
                _Matched['ActorName'] = AfterNarratorName
                _Matched['ApiSetting'] = MatchedVoiceActor['ApiSetting']
                
        ## AudioBook_Edit 변경
        if BeforeNarratorName != AfterNarratorName:
            for _Edit in SelectionGenerationKoChunks:
                if _Edit['ActorName'] == BeforeNarratorName:
                    _Edit['ActorName'] = AfterNarratorName
        
        return MatchedActors, SelectionGenerationKoChunks

    else:
        return MatchedActors, SelectionGenerationKoChunks

## 프롬프트 요청 및 결과물 VoiceLayerGenerator
def VoiceLayerSplitGenerator(projectName, email, Narrator = 'VoiceActor', CloneVoiceName = '저자명', ReadingStyle = 'AllCharacters', VoiceReverbe = 'on', MainLang = 'Ko', Mode = "Manual", Macro = "Auto", Bracket = "Manual", VolumeEqual = "Mixing", Account = "None", VoiceEnhance = 'off', VoiceFileGen = 'on', MessagesReview = "off"):
    MatchedActors, SelectionGenerationKoChunks, VoiceDataSetCharacters = ActorMatchedSelectionGenerationChunks(projectName, email, MainLang)

    ## Modify 시간에 맞추어 폴더 생성 및 이전 끊긴 히스토리 합치기 ##
    BaseModifyFolder = f"[{projectName}_Modified]"
    BaseModifiedFolderPath = VoiceLayerPathGen(projectName, email, BaseModifyFolder, 'Master')
    
    # 경로를 정규화(NFC)하여 파일 시스템 문제를 해결
    if os.path.exists(unicodedata.normalize('NFC', BaseModifiedFolderPath)):
        BaseModifiedFolderPath = unicodedata.normalize('NFC', BaseModifiedFolderPath)
    elif os.path.exists(unicodedata.normalize('NFD', BaseModifiedFolderPath)):
        BaseModifiedFolderPath = unicodedata.normalize('NFD', BaseModifiedFolderPath)
    
    ModifyTime = datetime.now().strftime("%Y%m%d%H%M%S")
    ModifyFolder = f"{ModifyTime}_Modified_Part"
    ModifyFolderPath = os.path.join(BaseModifiedFolderPath, ModifyFolder)
    
    # Modify 시간에 맞추어 폴더 생성
    if not os.path.exists(ModifyFolderPath):
        os.makedirs(ModifyFolderPath)
    
    # [{projectName}_Modified] 폴더 안에 있는 모든 폴더를 검사
    for folderName in os.listdir(BaseModifiedFolderPath):
        folderPath = os.path.join(BaseModifiedFolderPath, folderName)
        
        # 폴더인지 확인
        if os.path.isdir(folderPath):
            # 폴더 안의 파일 목록 가져오기
            files = os.listdir(folderPath)
            
            # 빈 폴더인 경우 삭제
            if not files:
                if folderPath != ModifyFolderPath:
                    os.rmdir(folderPath)
                    continue
            
            ## "n_Modified_Part.wav" 또는 "n_Modified_Par_(n).mp3" 파일이 있는지 확인
            # "_Modified_Part.wav" 파일이 있는지 확인
            wavFileFound = any(file.endswith("_Modified_Part.wav") for file in files)
            # "_Modified_Part_(n).mp3" 파일이 있는지 확인
            mp3FileFound = any(re.match(r".*_Modified_Part_\(\d+\)\.mp3$", file) for file in files)
            # 둘 중 하나라도 찾으면 True
            ModifiedPartFileFound = wavFileFound or mp3FileFound

            if not ModifiedPartFileFound:
                # 폴더 내 파일을 ModifyFolderPath로 이동
                for file in files:
                    if folderPath != ModifyFolderPath:
                        shutil.move(os.path.join(folderPath, file), ModifyFolderPath)
                # 빈 폴더 삭제, 단 ModifyFolderPath는 삭제하지 않음
                if folderPath != ModifyFolderPath:
                    os.rmdir(folderPath)
    ## Modify 시간에 맞추어 폴더 생성 및 이전 끊긴 히스토리 합치기 ##
    
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
    MatchedChunks = []
    if os.path.exists(unicodedata.normalize('NFC', MatchedActorsPath)) or os.path.exists(unicodedata.normalize('NFD', MatchedActorsPath)):
        try:
            print(unicodedata.normalize('NFC', MatchedActorsPath))
            with open(unicodedata.normalize('NFC', MatchedActorsPath), 'r', encoding = 'utf-8') as MatchedActorsJson:
                MatchedActors = json.load(MatchedActorsJson)
            print(unicodedata.normalize('NFC', MatchedChunksPath))
            with open(unicodedata.normalize('NFC', MatchedChunksPath), 'r', encoding = 'utf-8') as MatchedChunksJson:
                MatchedChunks = json.load(MatchedChunksJson)
        except:
            try:
                print(unicodedata.normalize('NFD', MatchedActorsPath))
                with open(unicodedata.normalize('NFD', MatchedActorsPath), 'r', encoding = 'utf-8') as MatchedActorsJson:
                    MatchedActors = json.load(MatchedActorsJson)
                print(unicodedata.normalize('NFD', MatchedChunksPath))
                with open(unicodedata.normalize('NFD', MatchedChunksPath), 'r', encoding = 'utf-8') as MatchedChunksJson:
                    MatchedChunks = json.load(MatchedChunksJson)
            except:
                sys.exit(f'[ MatchedVoices 파일이 이미 생성됨, 삭제해주세요 : {MatchedActorsPath} ]')

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

    ## 모든 인물 전체 히스토리 불러오기 (Modify 검사 용도)
    GenerationKoChunkAllHistory = []
    for _MatchedActor in MatchedActors:
        _Actor = _MatchedActor['ActorName']
        _fileName = projectName + '_' + 'VoiceLayer_History_' + _Actor + '.json'
        MatchedChunkHistoryPath = VoiceLayerPathGen(projectName, email, _fileName, 'Mixed')
        if os.path.exists(MatchedChunkHistoryPath):
            with open(MatchedChunkHistoryPath, 'r', encoding = 'utf-8') as MatchedChunkHistoryJson:
                GenerationKoChunkHistory = json.load(MatchedChunkHistoryJson)
        else:
            GenerationKoChunkHistory = []
        GenerationKoChunkAllHistory += GenerationKoChunkHistory

    #### EditGenerationKoChunks에 중복 EditId 문제 해결 ####
    ## Chunk의 토큰 수가 큰 경우의 해결, 또는 빈 리스트 제거
    _MatchedChunks = copy.deepcopy(MatchedChunks)
    MatchedChunks = []
    for _chunk_ in _MatchedChunks:
        ActorChunk = _chunk_['ActorChunk']
        if ActorChunk == []:
            continue
        ChunkTokens = 0
        SplitActorChunk = []
        for __chunk in ActorChunk:
            chunk = __chunk['Chunk']
            ChunkLength = len(chunk)
            if ChunkTokens + ChunkLength >= 400:
                MatchedChunks.append({"EditId": _chunk_['EditId'], "ChunkId": _chunk_['ChunkId'], "Tag": _chunk_['Tag'], "ActorName": _chunk_['ActorName'], "ActorChunk": SplitActorChunk})
                SplitActorChunk = []
                ChunkTokens = 0
            SplitActorChunk.append(__chunk)
            ChunkTokens += ChunkLength
        if SplitActorChunk:
            MatchedChunks.append({"EditId": _chunk_['EditId'], "ChunkId": _chunk_['ChunkId'], "Tag": _chunk_['Tag'], "ActorName": _chunk_['ActorName'], "ActorChunk": SplitActorChunk})

    ## EditId가 동일한 경우 해결
    for i in range(len(MatchedChunks)):
        if i > 0 and MatchedChunks[i]["EditId"] == MatchedChunks[i-1]["EditId"]:
            count = 1
            while i + count < len(MatchedChunks) and MatchedChunks[i + count]["EditId"] == MatchedChunks[i]["EditId"]:
                count += 1
            for j in range(count):
                MatchedChunks[i + j]["EditId"] = round(MatchedChunks[i + j]["EditId"] + 0.01 * (j + 1), 2)
    #### EditGenerationKoChunks에 중복 EditId 문제 해결 ####

    #### Brackets 자동 생성 ####
    # 완전 일치 확인 함수
    def ExactMatch(chunk1, chunk2):
        return re.sub(r'[^가-힣]', '', chunk1) == re.sub(r'[^가-힣]', '', chunk2)

    # 90% 이상 일치 확인 함수
    def SimilarMatch(chunk1, chunk2, threshold = 0.9):
        return SequenceMatcher(None, re.sub(r'[^가-힣]', '', chunk1), re.sub(r'[^가-힣]', '', chunk2)).ratio() >= threshold
    
    if Bracket != "Manual" and GenerationKoChunkAllHistory != []:
        ## 대괄호 전처리(대괄호의 위치 및 과반수에 따라 조정)
        for i in range(len(MatchedChunks)):
            BracketCount = 0
            OneBracketList = []
            ModifyCount = 0
            ChunkCount = len(MatchedChunks[i]['ActorChunk'])
            EditID = MatchedChunks[i]['EditId']
            ActorNAME = MatchedChunks[i]['ActorName']
            for j in range(ChunkCount):
                Chunk = MatchedChunks[i]['ActorChunk'][j]['Chunk']
                
                ## 1. 대괄호 전처리
                if "[[" in Chunk[:3] and "]]" in Chunk[-3:]:
                    Chunk = Chunk.replace('[[[', '').replace(']]]', '').replace('[[', '').replace(']]', '')
                    MatchedChunks[i]['ActorChunk'][j]['Chunk'] = f'[[{Chunk}]]'
                    BracketCount += 1
                elif Chunk[:3].count("[") == 1 and Chunk[-3:].count("]") == 1:
                    Chunk = Chunk[:2].replace("[", "") + Chunk[2:]
                    Chunk = Chunk[:-2] + Chunk[-2:].replace("]", "")
                    MatchedChunks[i]['ActorChunk'][j]['Chunk'] = f'[{Chunk}]'
                    OneBracketList.append(j)
            # if OneBracketList != []:
            #     print(f'{i}: {OneBracketList}')
            
            ## 2. 대괄호 개수를 통한 처리
            if BracketCount > ChunkCount / 2:
                for s in range(ChunkCount):
                    Chunk = MatchedChunks[i]['ActorChunk'][s]['Chunk']
                    Chunk = Chunk.replace('[[', '[').replace(']]', ']')
                    MatchedChunks[i]['ActorChunk'][s]['Chunk'] = Chunk
                    
            ## 3. 수정의 과반수에 따라 조정
            ExistedHistory = False
            for k in range(len(GenerationKoChunkAllHistory)):
                ## AA. 같은 EditId에 이름이 같을때(기존 히스토리에 해당 데이터가 있을때)
                if GenerationKoChunkAllHistory[k]['EditId'] == EditID and GenerationKoChunkAllHistory[k]['ActorName'] == ActorNAME:
                    ExistedHistory = True
                    HistoryPauseCount = len(GenerationKoChunkAllHistory[k]['Pause'])
                    
                    ## History와 Edit의 문장 일치도 확인
                    ChunkMatching = True
                    if 'ActorChunks' in GenerationKoChunkAllHistory[k]:
                        # print(GenerationKoChunkAllHistory[k]['EditId'])
                        # print(GenerationKoChunkAllHistory[k])
                        ChunkMatching = False
                        HistoryActorChunks = GenerationKoChunkAllHistory[k]['ActorChunks']
                        if len(HistoryActorChunks) == ChunkCount:
                            # 2개인 경우에는 한쪽이 바뀌는 것은 문제 없음
                            if ChunkCount == 2:
                                if ExactMatch(MatchedChunks[i]['ActorChunk'][0]['Chunk'], GenerationKoChunkAllHistory[k]['ActorChunks'][0]) or ExactMatch(MatchedChunks[i]['ActorChunk'][-1]['Chunk'], GenerationKoChunkAllHistory[k]['ActorChunks'][-1]):
                                    ChunkMatching = True
                            # 2개가 아닌 경우는 양쪽이 안 바뀌면 문제 없음, 한쪽만 바뀌는 것은 문제
                            else:
                                if (ExactMatch(MatchedChunks[i]['ActorChunk'][0]['Chunk'], GenerationKoChunkAllHistory[k]['ActorChunks'][0]) and
                                    SimilarMatch(MatchedChunks[i]['ActorChunk'][-1]['Chunk'], GenerationKoChunkAllHistory[k]['ActorChunks'][-1])) or \
                                (SimilarMatch(MatchedChunks[i]['ActorChunk'][0]['Chunk'], GenerationKoChunkAllHistory[k]['ActorChunks'][0]) and
                                    ExactMatch(MatchedChunks[i]['ActorChunk'][-1]['Chunk'], GenerationKoChunkAllHistory[k]['ActorChunks'][-1])):
                                    ChunkMatching = True
                            
                                # print(f'{i}_ChunkMatching: {ChunkMatching}')
                    # print(f'{i}_ChunkMatching: {ChunkMatching}')
                    ## A. 문장 개수가 다르거나, 새로운 문장이 생성되었을 때 ##
                    if (ChunkCount != HistoryPauseCount) or (not ChunkMatching):
                        for g in range(ChunkCount):
                            edit_chunk = MatchedChunks[i]['ActorChunk'][g]['Chunk']
                            MatchedChunks[i]['ActorChunk'][g]['Chunk'] = edit_chunk.replace('[[', '').replace(']]', '')
                            edit_chunk = MatchedChunks[i]['ActorChunk'][g]['Chunk']
                            if (g in OneBracketList) and ("[" not in edit_chunk[:3] and "]" not in edit_chunk[-3:]):
                                MatchedChunks[i]['ActorChunk'][g]['Chunk'] = f'[{edit_chunk}]'
                                # print(MatchedChunks[i]['ActorChunk'][g]['Chunk'])
                                
                    ## B. 문장 개수 또는 문장의 위치가 같고, 기존에 있던 문장일 때 ##
                    else:
                        HistoryChunk = GenerationKoChunkAllHistory[k]['ActorChunk']
                        EditChunk = MatchedChunks[i]['ActorChunk']
                        ## 3-1. ModifyCount 체크
                        for l in range(ChunkCount):
                            edit_chunk = EditChunk[l]['Chunk'].replace('[[', '[').replace(']]', ']')
                            if edit_chunk not in HistoryChunk:
                                # print(f'{EditID}_HistoryChunk: {HistoryChunk}')
                                # print(f'{EditID}_edit_chunk: {edit_chunk}\n')
                                ModifyCount += 1
                                EditChunk[l]['Chunk'] = f'[[{edit_chunk}]]'.replace('[[[', '[[').replace(']]]', ']]')
                        ## 3-2. ModifyCount 과반수 확인
                        if ModifyCount > ChunkCount / 2:
                            for f in range(ChunkCount):
                                edit_chunk = EditChunk[f]['Chunk']
                                EditChunk[f]['Chunk'] = edit_chunk.replace('[[', '').replace(']]', '')
                                edit_chunk = EditChunk[f]['Chunk']
                                if (f in OneBracketList) and ("[" not in edit_chunk[:3] and "]" not in edit_chunk[-3:]):
                                    EditChunk[f]['Chunk'] = f'[{edit_chunk}]'
            ## BB. 기존 히스토리에 해당 데이터가 없을때
            if not ExistedHistory:
                for h in range(ChunkCount):
                    edit_chunk = MatchedChunks[i]['ActorChunk'][h]['Chunk']
                    MatchedChunks[i]['ActorChunk'][h]['Chunk'] = edit_chunk.replace('[[', '').replace(']]', '')
                    edit_chunk = MatchedChunks[i]['ActorChunk'][h]['Chunk']
                    if (h in OneBracketList) and ("[" not in edit_chunk[:3] and "]" not in edit_chunk[-3:]):
                        MatchedChunks[i]['ActorChunk'][h]['Chunk'] = f'[{edit_chunk}]'
                        # print(MatchedChunks[i]['ActorChunk'][h]['Chunk'])
        with open(MatchedChunksPath, 'w', encoding = 'utf-8') as MatchedChunks_Json:
            json.dump(MatchedChunks, MatchedChunks_Json, ensure_ascii = False, indent = 4)
        if Bracket == "Practice":
            sys.exit(f"[ ((Bracket = {Bracket}))는 연습모드로 실제 수정&생성에는 ((Bracket = Auto 또는 Manual))로 변경해주세요. ]")
        else:
            print(f"[ ((Bracket = {Bracket}))로 Edit 파일의 대괄호가 자동으로 처리되었습니다. ]")
    ## 1. 대괄호 1개가 ModifyCount > ChunkCount / 2일때 해제되는 문제
    ## 2. 수정 이전 문장의 개수를 파악하는 문제
    ##### 3. 문장의 순서 또는 내용이 변경된 경우 -> 이 경우는 현재 파악못함 #####
    #### Brackets 자동 생성 ####

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
            
            ## 빈 ActorChunk 삭제 및 목차 및 문장 끝 후처리
            for i in range(len(EditGenerationKoChunks)):
                _tag = EditGenerationKoChunks[i]['Tag']
                # 'ActorChunk'를 역순으로 순회합니다
                for j in reversed(range(len(EditGenerationKoChunks[i]['ActorChunk']))):
                    # 문장 끝 후처리
                    _ActorChunk = EditGenerationKoChunks[i]['ActorChunk'][j]
                    _ActorChunk = _ActorChunk.strip()
                    _ActorChunk = _ActorChunk.replace('.,', ',').replace(',~.', ',').replace('..', '.')
                    _ActorChunk = re.sub(r'^[\.,~]+', '', _ActorChunk)  # 앞부분의 ',', '.', '~' 제거
                    if _tag not in ['Title', 'Logue', 'Part', 'Chapter', 'Index']:
                        if i in [1, 2]:
                            modified_ActorChunk = re.sub(r'[\.,~\s]{1,3}$', '', _ActorChunk)
                            modified_ActorChunk = modified_ActorChunk.strip()
                            modified_ActorChunk = f'[{modified_ActorChunk}]'
                        else:
                            modified_ActorChunk = re.sub(r'[\.,~\s]{1,3}$', '.', _ActorChunk)
                            modified_ActorChunk = modified_ActorChunk.strip()
                    # 목차 후처리
                    if _tag in ['Title', 'Logue', 'Part', 'Chapter', 'Index']:
                        modified_ActorChunk = re.sub(r'[\.,~\s]{1,3}$', '', _ActorChunk)
                        modified_ActorChunk = modified_ActorChunk.strip()
                        modified_ActorChunk = f'[{modified_ActorChunk}]'
                    EditGenerationKoChunks[i]['ActorChunk'][j] = modified_ActorChunk
                    # 빈 ActorChunk 삭제
                    if extract_text(EditGenerationKoChunks[i]['ActorChunk'][j]) == '':
                        del EditGenerationKoChunks[i]['ActorChunk'][j]
                        del EditGenerationKoChunks[i]['Pause'][j]
                        del EditGenerationKoChunks[i]['EndTime'][j]
            
            ## Index 정렬(Part:1 - Chapter:2 - Index:3 으로 태그 순서 정렬)
            def SorIndexTags(EditGenerationKoChunks):
                # Part, Chapter, Index 태그에 대한 우선순위를 정의합니다.
                TagOrder = ["Part", "Chapter", "Index"]
                FoundTags = []
                
                # Part, Chapter, Index 태그가 존재하는지 확인
                for chunk in EditGenerationKoChunks:
                    tag = chunk.get("Tag")
                    if tag in TagOrder and tag not in FoundTags:
                        FoundTags.append(tag)
                # 태그들이 존재하는 순서에 맞춰 Part, Chapter, Index로 변경
                for chunk in EditGenerationKoChunks:
                    tag = chunk.get("Tag")
                    if tag in FoundTags:
                        # 태그 순서를 변경하여 Part, Chapter, Index 순서로 매핑
                        new_tag = TagOrder[FoundTags.index(tag)]
                        chunk["Tag"] = new_tag
                
                return EditGenerationKoChunks

            EditGenerationKoChunks = SorIndexTags(EditGenerationKoChunks)            
            ## EditGenerationKoChunks의 Dic(검수)
            EditGenerationKoChunks = EditGenerationKoChunksToDic(EditGenerationKoChunks)
            
            #### ReadingStyle: NarratorOnly와 AllCharacters의 설정 ####
            ## 마지막 스튜디오 여름 관련 문구 삭제(해당 문구는 캐릭터가 없는 경우를 위해 제공됨으로 실제 오디오북 제작에는 필요 없음)
            EndingChunks = ['끝까지', '들어주셔서', '스튜디오', '열어가겠습니다']
            # 특정 리스트에서 해당 항목이 몇 개 포함되어 있는지 세는 함수
            def CountMatchingChunks(target, chunks):
                return sum(1 for chunk in chunks if chunk in target)
            # EditGenerationKoChunks[-2]와 [-1]을 검사하여 삭제하는 함수
            if 'ActorChunk' in EditGenerationKoChunks[-2]:
                matched_count = sum(CountMatchingChunks(actor_chunk['Chunk'], EndingChunks) for actor_chunk in EditGenerationKoChunks[-2]['ActorChunk'])
                if matched_count >= 2:
                    del EditGenerationKoChunks[-2]

            if 'ActorChunk' in EditGenerationKoChunks[-1]:
                matched_count = sum(CountMatchingChunks(actor_chunk['Chunk'], EndingChunks) for actor_chunk in EditGenerationKoChunks[-1]['ActorChunk'])
                if matched_count >= 2:
                    del EditGenerationKoChunks[-1]
            
            #### ReadingStyle: NarratorOnly와 AllCharacters의 설정 ####
            if ReadingStyle == 'NarratorOnly':
                for MatchedActor in MatchedActors:
                    if MatchedActor['CharacterTag'] == 'Narrator':
                        NarratorActorName = MatchedActor['ActorName']
                    if MatchedActor['CharacterTag'] == 'SecondaryNarrator':
                        SecondaryNarratorActorName = MatchedActor['ActorName']
                    
                for chunk in EditGenerationKoChunks:
                    if chunk['Tag'] == 'Character':
                        chunk['ActorName'] = SecondaryNarratorActorName
                    else:
                        chunk['ActorName'] = NarratorActorName
            #### ReadingStyle: NarratorOnly와 AllCharacters의 설정 ####
            
            # MatchedActors, MatchedChunks 저장 (Dic 저장 후 다시 List로 변환)
            fileName = projectName + '_' + 'MatchedVoices.json'
            MatchedActorsPath = VoiceLayerPathGen(projectName, email, fileName, 'Mixed')
            with open(MatchedActorsPath, 'w', encoding = 'utf-8') as json_file:
                json.dump(MatchedActors, json_file, ensure_ascii = False, indent = 4)
            with open(MatchedChunksPath, 'w', encoding = 'utf-8') as json_file:
                json.dump(EditGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)
            with open(MatchedChunksOriginPath, 'w', encoding = 'utf-8') as json_file:
                json.dump(EditGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)
            
            ## EditGenerationKoChunks의 List(프로세스)
            EditGenerationKoChunks = EditGenerationKoChunksToList(EditGenerationKoChunks)
        else:
            with open(MatchedChunksPath, 'r', encoding = 'utf-8') as MatchedChunksJson:
                _EditGenerationKoChunks = json.load(MatchedChunksJson)
                
            ## EditGenerationKoChunks의 Dic(프로세스)
            EditGenerationKoChunks = EditGenerationKoChunksToList(_EditGenerationKoChunks)

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
            Tag = Update['Tag']
            Name = Update['ActorName']
            Pause = Update['Pause']
            
            ### ElevenLabs, TypeCast Chunk Modify ###
            ## 끝에서부터 3개의 문자에서 '.', ',', ' '가 있으면 이를 제거 후 마지막에 '.' 표기
            def ModifyELChunk(chunk):
                # 1. Chunk 마지막 3개의 글자 중에 . 과 , 이 포함되어 있으면 이를 모두 삭제하고 .하나만 표기
                chunk = chunk[:-3] + chunk[-3:].replace('.', '').replace(',', '') + '.'
                # 2. ~.은 ,로 변경
                chunk = chunk.replace('~.', ',')
                # 3. Chunk의 마지막 3개를 제외하고 .이 포함되면 이를 모두 삭제
                chunk = chunk[:-3].replace('.', '') + chunk[-3:]
                # 4. ~,는 .로 변경
                chunk = chunk.replace('~,', '.')
                return chunk
            ## 끝에서부터 3개의 문자에서 '.', ',', ' '가 있으면 이를 제거 후 마지막에 ',' 표기
            def ModifyTCChunk(chunk):
                # Chunk 마지막 3개의 글자 중에 . 과 , 이 포함되어 있으면 이를 모두 삭제하고 ,하나만 표기
                chunk = chunk[:-3] + chunk[-3:].replace('.', '').replace(',', '') + ','
                return chunk
            ### ElevenLabs, TypeCast Chunk Modify ###
            ### RetryVoiceGen ###
            def RetryVoiceGen(name, retry, RetryIdList, SplitChunks):
                print(f"[[RetryVoiceGen: {name}]]")
                retry += 1
                SplitSents = SplitChunks
                # 1. SentList의 복구 ('[]' 이전으로 복구)
                RawSplitSents = []
                for SplitSent in SplitSents:
                    if SplitSent['제거'] == 'No':
                        RawSplitSents.append(SplitSent)
                
                # 2. RawSplitSents에서 RetryIdList(다시 재생성 해야하는 음성)
                RetrySplitSents = []
                RetryELChunks = []
                RetryChunks = []
                i = 1
                for RetryId in RetryIdList:
                    # RetryChunks 합치기
                    FrontWords = "지금 생성될 내용은"
                    MiddleWords = RawSplitSents[RetryId]['낭독문장']
                    EndWords = "문장 입니다"
                    _retryChunk = f'{FrontWords}, "{MiddleWords}", {EndWords}'
                    # RetryChunks 합치기
                    RetryChunks.append(ModifyTCChunk(_retryChunk))
                    RetryELChunks.append(ModifyELChunk(_retryChunk))
                    # RetrySplitSents 합치기
                    RetrySplitSents.append({'낭독문장번호': i, '낭독문장': FrontWords, '제거': 'Yes'})
                    RetrySplitSents.append({'낭독문장번호': i + 1, '낭독문장': FrontWords, '제거': 'Yes'})
                    RetrySplitSents.append({'낭독문장번호': i + 2, '낭독문장': FrontWords, '제거': 'Yes'})
                    i += 3
                
                Chunk = " ".join(RetryChunks)
                EL_Chunk = " ".join(RetryELChunks)
                SplitChunks = RetrySplitSents
                BracketsSwitch = True
                bracketsSplitChunksNumber = RetryIdList
                return retry, BracketsSwitch, bracketsSplitChunksNumber, Chunk, EL_Chunk, SplitChunks
            ### RetryVoiceGen ###
            ## Brackets 부분 생성 적용 ##
            BracketsSwitch = False
            BracketsNumber = []
            for i in range(len(Update['ActorChunk'])):
                if '[[' in Update['ActorChunk'][i] and ']]' in Update['ActorChunk'][i]:
                    Update['ActorChunk'][i] = Update['ActorChunk'][i].replace('[[', '[').replace(']]', ']')
                    BracketsSwitch = True
                    BracketsNumber.append(i + 1)
            
            ## [[내용]]을 [내용]으로 다시 되돌리기(다음에 다시 사용되기 위함)
            if BracketsSwitch:
                for _EditGenerationKoChunk in _EditGenerationKoChunks:
                    if _EditGenerationKoChunk['EditId'] == EditId:
                        print(f'_EditGenerationKoChunk: {_EditGenerationKoChunk}')
                        _EditGenerationActorChunk = _EditGenerationKoChunk['ActorChunk']
                        for i in range(len(_EditGenerationActorChunk)):
                            if i + 1 in BracketsNumber:
                                _EditGenerationChunk = _EditGenerationActorChunk[i]['Chunk']
                                _EditGenerationKoChunk['ActorChunk'][i]['Chunk'] = _EditGenerationChunk.replace('[[', '[').replace(']]', ']')
                                print(_EditGenerationKoChunk['ActorChunk'][i]['Chunk'])
                # with open(MatchedChunksPath, 'w', encoding = 'utf-8') as MatchedChunksJson:
                #     json.dump(_EditGenerationKoChunks, MatchedChunksJson, ensure_ascii = False, indent = 4)
            
            ## ElevenLabs Chunk Modify ##
            EL_Chunk = None
            if Api == 'ElevenLabs':
                ELChunks = []
                BracketsELChunks = []
                for idx, _ELChunk in enumerate(Update['ActorChunk']):
                    if _ELChunk.strip().startswith('[') and _ELChunk.strip().endswith(']'):
                        _ELChunk = f'지금 생성될 내용은, "{_ELChunk.strip().strip("[]")}", 문장 입니다'
                        if idx + 1 in BracketsNumber:
                            ELChunk = ModifyELChunk(_ELChunk)
                            BracketsELChunks.append(ELChunk)
                    ELChunk = ModifyELChunk(_ELChunk)
                    ELChunks.append(ELChunk)                    
                if BracketsSwitch:
                    EL_Chunk = " ".join(BracketsELChunks)
                else:
                    EL_Chunk = " ".join(ELChunks)
            # print(f"ChunkModify: ({EL_Chunk})")
            ## TypeCast Chunk Modify ##
            Chunk = None
            if Api == 'TypeCast':
                Chunks = []
                BracketsChunks = []
                for idx, _Chunk in enumerate(Update['ActorChunk']):
                    if _Chunk.strip().startswith('[') and _Chunk.strip().endswith(']'):
                        _Chunk = f'지금 생성될 내용은, "{_Chunk.strip().strip("[]")}", 문장 입니다'
                        if idx + 1 in BracketsNumber:
                            _Chunk = ModifyTCChunk(_Chunk)
                            BracketsChunks.append(_Chunk)
                    _chunk = ModifyTCChunk(_Chunk)
                    Chunks.append(_chunk)
                if BracketsSwitch:
                    Chunk = " ".join(BracketsChunks)
                else:
                    Chunk = " ".join(Chunks)
            
            OriginChunk = " ".join(Update['ActorChunk'])
            ChunkCount = len(Update['ActorChunk']) - 1 # 파일의 마지막 순번을 표기

            #### Split을 위한 딕셔너리 리스트 생성 ####
            RawSplitChunks = [chunk.replace('~.', '').replace('~,', '').replace('.,', '').replace('.,', '') for chunk in Update['ActorChunk']]
            # '[내용]'인 부분은 단어의 부드러운 음성 처리 방법
            rawSplitChunks = []
            removeSplitChunksNumber = []
            Number = 1
            bracketsSplitChunks = []
            removeBracketsSplitChunksNumber = []
            bracketsSplitChunksNumber = []
            bracketNumber = 1
            for i in range(len(RawSplitChunks)):
                if RawSplitChunks[i].strip().startswith('[') and RawSplitChunks[i].strip().endswith(']'):
                    # Brackets 부분일 경우 해당 부분 문장만 bracketsSplitChunks로 추가
                    if BracketsSwitch:
                        if i + 1 in BracketsNumber:
                            bracketsSplitChunks.append('지금 생성될 내용은')
                            bracketsSplitChunks.append(f"{RawSplitChunks[i].strip().strip('[]')}")
                            bracketsSplitChunks.append('문장 입니다')
                            removeBracketsSplitChunksNumber.append(bracketNumber)
                            bracketsSplitChunksNumber.append(i)
                            removeBracketsSplitChunksNumber.append(bracketNumber + 2)
                            bracketNumber += 3

                    rawSplitChunks.append('지금 생성될 내용은')
                    rawSplitChunks.append(f"{RawSplitChunks[i].strip().strip('[]')}")
                    rawSplitChunks.append('문장 입니다')
                    removeSplitChunksNumber.append(Number)
                    removeSplitChunksNumber.append(Number + 2)
                    Number += 2
                else:
                    rawSplitChunks.append(RawSplitChunks[i])
                Number += 1
            
            # Brackets 부분일 경우 rawSplitChunks를 bracketsSplitChunks로 교체
            if BracketsSwitch:
                rawSplitChunks = bracketsSplitChunks
                removeSplitChunksNumber = removeBracketsSplitChunksNumber
            SplitChunks = []
            for i in range(len(rawSplitChunks)):
                Remove = 'No'
                if i + 1 in removeSplitChunksNumber:
                    Remove = 'Yes'
                SplitChunk = {'낭독문장번호': i + 1, '낭독문장': rawSplitChunks[i], '제거': Remove}
                # print(f'SplitChunk: ({SplitChunk})')
                SplitChunks.append(SplitChunk)

            # if BracketsSwitch:
            #     print(f'1. EL_Chunk: {EL_Chunk}\n')
            #     print(f'2. Chunk: {Chunk}\n')
            #     print(f'3. SplitChunks: {SplitChunks}\n')
            #     print(f'4. BracketsSwitch: {BracketsSwitch}\n')
            #     print(f'5. bracketsSplitChunksNumber: {bracketsSplitChunksNumber}\n')
            #     print(f'6. removeSplitChunksNumber: {removeSplitChunksNumber}')
            #     sys.exit()
            #### Split을 위한 딕셔너리 리스트 생성 ####

            ## 수정생성(Modify) 여부확인 ##
            Modify = "No"
            if BracketsSwitch:
                Modify = "Yes"
            ActorModify = "No"
            NewActorSwitch = 1
            edit_id_found = False  # EditId가 발견되었는지 여부를 추적

            FloatEditIdList = []
            for AllHistory in GenerationKoChunkAllHistory:
                AllHistoryEditId = AllHistory['EditId']
                if AllHistoryEditId % 1 != 0:
                    FloatEditIdList.append(AllHistoryEditId)
                if AllHistoryEditId == EditId:
                    edit_id_found = True  # EditId가 발견되었음을 표시
                    OriginName = AllHistory['ActorName']
                    if AllHistory['ActorName'] == Name:
                        NewActorSwitch = 0
                        
            # 새로운 EditId(예를들면 1.01과 같은)가 중간에 발생할 경우 Modify
            if EditId % 1 != 0 and EditId not in FloatEditIdList:
                Modify = "Yes"

            # for 루프가 끝난 후 EditId가 하나도 발견되지 않은 경우 NewActorSwitch를 0으로 설정
            if not edit_id_found:
                NewActorSwitch = 0

            if NewActorSwitch == 1 and GenerationKoChunkAllHistory != []:
                ActorModify = "Yes"
                Modify = "Yes"
                print(f"[ ActorModify: {ActorModify}, (성우) 변경 ]\n({OriginName})\n({Name})")
            ChunkModify = "No"
            
            for History in GenerationKoChunkHistorys:
                if History['EditId'] == EditId and History["ActorName"] == Name:
                    if History['ActorChunk'] != OriginChunk:
                        ChunkModify = "Yes"
                        Modify = "Yes"
                        print(f"[ ChunkModify: {ChunkModify}, (내용) 변경 ]\n({History['ActorChunk']})\n({OriginChunk})")
                        History['ActorChunk'] = OriginChunk.replace('[[', '[').replace(']]', ']')
                        History['ActorChunks'] = Update['ActorChunk']
                    if History['Tag'] != Tag:
                        History['Tag'] = Tag
                    if History['Pause'] != Pause:
                        History['Pause'] = Pause

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
                if '?' not in OriginChunk[-3:]:
                    if '.' not in OriginChunk[-3:]:
                        lastpitch = [-2]
                    elif '다' not in OriginChunk[-3:]:
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
                else:
                    FileName = projectName + '_' + str(EditId) + '_' + Name + '.wav'
                if ChunkModify == "Yes":
                    voiceLayerPath = VoiceLayerPathGen(projectName, email, FileName, 'Mixed')
                    retry = 0
                    while retry <= 3:
                        ChangedName = ActorVoiceGen(projectName, email, Modify, ModifyFolderPath, BracketsSwitch, bracketsSplitChunksNumber, VoiceReverbe, Update['Tag'], name, Chunk, EL_Chunk, Api, ApiSetting, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath, SplitChunks, MessagesReview)
                        ## retry 시작 (잘못 짤린 음성의 재생성) ##
                        if not isinstance(ChangedName, list):
                            break
                        RetryIdList = ChangedName
                        retry, BracketsSwitch, bracketsSplitChunksNumber, Chunk, EL_Chunk, SplitChunks = RetryVoiceGen(name, retry, RetryIdList, SplitChunks)

                    if ChangedName != 'Continue':
                        if Macro == "Auto":
                            TypeCastMacro(ChangedName, Account)
                            time.sleep(random.randint(3, 5))
                            restart = True
                        else:
                            print(f'\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n@  캐릭터 불일치 -----> [TypeCastAPI의 캐릭터를 ( {ChangedName} ) 으로 변경하세요!] <-----  @\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n')
                            sys.exit()
                    else:
                        ## [[내용]]을 [내용]으로 다시 되돌리기(다음에 다시 사용되기 위함)
                        if BracketsSwitch:
                            with open(MatchedChunksPath, 'w', encoding = 'utf-8') as MatchedChunksJson:
                                json.dump(_EditGenerationKoChunks, MatchedChunksJson, ensure_ascii = False, indent = 4)
                        ## [[내용]]을 [내용]으로 다시 되돌리기(다음에 다시 사용되기 위함)
                        with open(MatchedChunkHistorysPath, 'w', encoding = 'utf-8') as json_file:
                            json.dump(GenerationKoChunkHistorys, json_file, ensure_ascii = False, indent = 4)
                else:
                    voiceLayerPath = VoiceLayerPathGen(projectName, email, FileName, 'Mixed')
                    if not (os.path.exists(voiceLayerPath.replace(".wav", "") + f'_({ChunkCount}).wav') or os.path.exists(voiceLayerPath.replace(".wav", "") + f'_({ChunkCount})M.wav')):
                        retry = 0
                        while retry <= 3:
                            ChangedName = ActorVoiceGen(projectName, email, Modify, ModifyFolderPath, BracketsSwitch, bracketsSplitChunksNumber, VoiceReverbe, Update['Tag'], name, Chunk, EL_Chunk, Api, ApiSetting, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath, SplitChunks, MessagesReview)
                            ## retry 시작 (잘못 짤린 음성의 재생성) ##
                            if not isinstance(ChangedName, list):
                                break
                            RetryIdList = ChangedName
                            retry, BracketsSwitch, bracketsSplitChunksNumber, Chunk, EL_Chunk, SplitChunks = RetryVoiceGen(name, retry, RetryIdList, SplitChunks)

                        if ChangedName == 'Continue':
                            ## [[내용]]을 [내용]으로 다시 되돌리기(다음에 다시 사용되기 위함)
                            if BracketsSwitch:
                                with open(MatchedChunksPath, 'w', encoding = 'utf-8') as MatchedChunksJson:
                                    json.dump(_EditGenerationKoChunks, MatchedChunksJson, ensure_ascii = False, indent = 4)
                            ## [[내용]]을 [내용]으로 다시 되돌리기(다음에 다시 사용되기 위함)
                            ## 히스토리 저장 ##
                            # 동일한 EditId와 ActorName을 가진 항목이 있는지 확인
                            AddSwitch = True  # 새 항목을 추가해야 하는지 여부를 나타내는 플래그
                            for history in GenerationKoChunkHistorys:
                                if history["EditId"] == EditId and history["ActorName"] == Name:
                                    AddSwitch = False
                                    break

                            # 동일한 EditId와 ActorName을 가진 항목이 없을 경우 새 항목 추가
                            if AddSwitch:
                                GenerationKoChunkHistory = {"EditId": EditId, "Tag": Update['Tag'], "ActorName": Name, "ActorChunk": OriginChunk, "ActorChunks": Update['ActorChunk'], "Pause": Pause}
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
    EditGenerationKoChunks = VoiceGenerator(projectName, email, EditGenerationKoChunks, MatchedChunksPath, Narrator, CloneVoiceName, CloneVoiceActorPath, VoiceEnhance = VoiceEnhance, VoiceFileGen = VoiceFileGen, VolumeEqual = VolumeEqual)
    ## 최종 생성된 수정부분 음성파일 합치기 ##
    ModifiedVoiceGenerator(ModifyFolderPath, ModifyFolder, VolumeEqual)
    
    return EditGenerationKoChunks

## 프롬프트 요청 및 결과물 Json을 VoiceLayer에 업데이트
def VoiceLayerUpdate(projectName, email, Narrator = 'VoiceActor', CloneVoiceName = '저자명', ReadingStyle = 'AllCharacters', VoiceReverbe = 'on', MainLang = 'Ko', Mode = "Manual", Macro = "Auto", Bracket = "Manual", VolumeEqual = "Mixing", Account = "None", Intro = "None", VoiceEnhance = 'off', VoiceFileGen = "on", MessagesReview = "off"):
    print(f"< User: {email} | Project: {projectName} | VoiceLayerGenerator 시작 >")
    EditGenerationKoChunks = VoiceLayerSplitGenerator(projectName, email, Narrator = Narrator, CloneVoiceName = CloneVoiceName, ReadingStyle = ReadingStyle, VoiceReverbe = VoiceReverbe, MainLang = MainLang, Mode = Mode, Macro = Macro, Bracket = Bracket, VolumeEqual = VolumeEqual, Account = Account, VoiceEnhance = VoiceEnhance, VoiceFileGen = VoiceFileGen, MessagesReview = MessagesReview)

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