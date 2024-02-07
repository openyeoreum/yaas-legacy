import os
import json
import requests
import time
import random
import re
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from pydub import AudioSegment
from backend.b1_Api.b14_Models import User
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetVoiceDataSet

###########################################
##### SelectionGenerationKoChunks 생성 #####
###########################################
def LoadSelectionGenerationKoChunks(projectName, email, voicedataset):
    voiceDataSet = GetVoiceDataSet(voicedataset)
    VoiceDataSet = voiceDataSet[0][1]
    
    project = GetProject(projectName, email)
    
    SelectionGenerationKoBookContext = project.SelectionGenerationKo[1]['SelectionGenerationKoBookContext'][1]
    SelectionGenerationKoSplitedIndexs = project.SelectionGenerationKo[1]['SelectionGenerationKoSplitedIndexs'][1:]
    CharacterCompletion = project.CharacterCompletion[2]['CheckedCharacterTags'][1:]
    SelectionGenerationKoChunks = []
    for i in range(len(SelectionGenerationKoSplitedIndexs)):
        SelectionGenerationKoSplitedBodys = SelectionGenerationKoSplitedIndexs[i]['SelectionGenerationKoSplitedBodys']
        for j in range(len(SelectionGenerationKoSplitedBodys)):
            SelectionGenerationKoSplitedChunks = SelectionGenerationKoSplitedBodys[j]['SelectionGenerationKoSplitedChunks']
            for k in range(len(SelectionGenerationKoSplitedChunks)):
                ChunkId = SelectionGenerationKoSplitedChunks[k]['ChunkId']
                Chunk = SelectionGenerationKoSplitedChunks[k]['Chunk']
                Tag = SelectionGenerationKoSplitedChunks[k]['Tag']
                Voice = SelectionGenerationKoSplitedChunks[k]['Voice']
                SelectionGenerationKoChunks.append({'ChunkId': ChunkId, 'Tag': Tag, 'Chunk': Chunk, 'Voice': Voice})
    
    return VoiceDataSet, CharacterCompletion, SelectionGenerationKoBookContext, SelectionGenerationKoChunks

#############################
##### MatchedActors 생성 #####
#############################
# NarratorSet에서 ContextScore 계산
def ContextScoreCal(VoiceDataSet, SelectionGenerationKoBookContext):
    VoiceDataSetCharacters = VoiceDataSet["Characters"][1:]
    BookGenre = SelectionGenerationKoBookContext['Vector']['ContextCompletion']['Genre']
    BookGender = SelectionGenerationKoBookContext['Vector']['ContextCompletion']['Gender']
    BookAge = SelectionGenerationKoBookContext['Vector']['ContextCompletion']['Age']
    BookPersonality = SelectionGenerationKoBookContext['Vector']['ContextCompletion']['Personality']
    BookAtmosphere = SelectionGenerationKoBookContext['Vector']['ContextCompletion']['Emotion']

    for Character in VoiceDataSetCharacters:
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
                AtmosphereScore += (BookAtmosphere['EmotionRatio'][NAtmosphere['index']] * NAtmosphere['Score'])
        AtmosphereScore = AtmosphereScore / 1000
        
        ContextScore = (GenreScore * GenderScore * AgeScore * PersonalityScore)
        
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
                AgeScore = AgeScore / 10
                # Emotion 스코어 계산
                VoiceEmotion = Voice['Voice']['Emotion']
                EmotionScore = 0
                for VEmotion in VoiceEmotion:
                    if VEmotion['index'] in Character['Emotion']:
                        EmotionScore += (Character['Emotion'][VEmotion['index']] * VEmotion['Score'])
                EmotionScore = EmotionScore / 1000
                
                VoiceScore = (GenderScore * AgeScore * EmotionScore)
                
                Voice['Score'][CharacterTag] = Voice['Score']['ContextScore'] * VoiceScore
                
    return VoiceDataSetCharacters

# 최고 점수 캐릭터 선정
def HighestScoreVoiceCal(VoiceDataSetCharacters, CharacterTag, Caption = "None"):
    HighestScore = 0  # 최고 점수를 매우 낮은 값으로 초기화
    HighestScoreVoices = []  # 최고 점수를 가진 데이터들을 저장할 리스트

    for VoiceData in VoiceDataSetCharacters:
        if VoiceData['Choice'] == 'No':
            score = VoiceData['Score'][CharacterTag]
            if score > HighestScore:
                HighestScore = score
                HighestScoreVoices = [VoiceData]  # 새로운 최고 점수 데이터로 리스트를 초기화
            elif score == HighestScore:
                HighestScoreVoices.append(VoiceData)  # 현재 점수가 최고 점수와 같다면 리스트에 추가

    # 최고 점수 데이터들 중 랜덤으로 하나를 선택하여 'Choice'를 CharacterTag로 설정
    if HighestScoreVoices:
        HighestScoreVoice = random.choice(HighestScoreVoices)
        HighestScoreVoice['Choice'] = CharacterTag
    else:
        HighestScoreVoice = {'Name': 'None', 'ApiSetting': 'None'}
    
    # CharacterTag가 Narrator인 경우 Caption 선정
    CaptionVoice = "None"
    if CharacterTag == "Narrator":
        for VoiceData in VoiceDataSetCharacters:
            if VoiceData['Name'] == HighestScoreVoice['ApiSetting']['Caption']:
                VoiceData['Choice'] = 'Caption'
                CaptionVoice = VoiceData
                break

    return VoiceDataSetCharacters, HighestScoreVoice, CaptionVoice

# 낭독 TextSetting
def ActorChunkSetting(RawChunk):
    ActorChunk = RawChunk.replace('(0.1)', '.')
    ActorChunk = ActorChunk.replace('(0.2)', '~.')
    ActorChunk = ActorChunk.replace('(0.20)', ',')
    ActorChunk = ActorChunk.replace('(0.3)', ',')
    ActorChunk = ActorChunk.replace('(0.30)', '')
    ActorChunk = ActorChunk.replace('(0.40)', '')
    ActorChunk = ActorChunk.replace('(0.60)', '곬갌끚')
    ActorChunk = ActorChunk.replace('(0.70)', '')
    ActorChunk = ActorChunk.replace('(1.20)', '')
    ActorChunk = ActorChunk.replace('(1.30)', '')
    ActorChunk = ActorChunk.replace('(1.50)', '')
    ActorChunk = ActorChunk.replace('(2.00)', '')
    
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
def ActorMatchedSelectionGenerationKoChunks(projectName, email, voiceDataSet):
    VoiceDataSet, CharacterCompletion, SelectionGenerationKoBookContext, SelectionGenerationKoChunks = LoadSelectionGenerationKoChunks(projectName, email, voiceDataSet)
    
    # CharacterTags 구하기
    CharacterTags = []
    for Character in CharacterCompletion:
        CharacterTags.append(Character['CharacterTag'])
    
    # Characters 점수계산 및 MatchedActors 생성
    MatchedActors = []
    VoiceDataSetCharacters = ContextScoreCal(VoiceDataSet, SelectionGenerationKoBookContext)
    for CharacterTag in CharacterTags:
        VoiceDataSetCharacters = VoiceScoreCal(CharacterCompletion, VoiceDataSetCharacters, CharacterTag)
        VoiceDataSetCharacters, HighestScoreVoice, CaptionVoice = HighestScoreVoiceCal(VoiceDataSetCharacters, CharacterTag)
        MatchedActor = {'CharacterTag': CharacterTag, 'ActorName': HighestScoreVoice['Name'], 'ApiSetting': HighestScoreVoice['ApiSetting']}
        MatchedActors.append(MatchedActor)
        if CaptionVoice != "None":
            CaptionActor = {'CharacterTag': 'Caption', 'ActorName': CaptionVoice['Name'], 'ApiSetting': CaptionVoice['ApiSetting']}
            MatchedActors.append(CaptionActor)

    # ### 테스트 후 삭제 ###
    # with open('VoiceDataSetCharacters.json', 'w', encoding = 'utf-8') as json_file:
    #     json.dump(VoiceDataSetCharacters, json_file, ensure_ascii = False, indent = 4)
    # ### 테스트 후 삭제 ###
    
    # SelectionGenerationKoChunks의 MatchedActors 삽입
    for GenerationKoChunks in SelectionGenerationKoChunks:
        for MatchedActor in MatchedActors:
            if GenerationKoChunks['Tag'] in ['Caption', 'CaptionComment']:
                ChunkCharacterTag = 'Caption'
            else:
                ChunkCharacterTag = GenerationKoChunks['Voice']['CharacterTag']
            if ChunkCharacterTag == MatchedActor['CharacterTag']:
                GenerationKoChunks['ActorName'] = MatchedActor['ActorName']
                GenerationKoChunks['ActorChunk'] = ActorChunkSetting(GenerationKoChunks['Chunk'])
                if '(0.60)' in GenerationKoChunks['Chunk']:
                    # "(0.60)"을 기준으로 모든 부분을 나눔
                    parts = GenerationKoChunks['Chunk'].split("(0.60)")
                    GenerationKoChunks['Chunk'] = [part + "(0.60)" for part in parts[:-1]] + [parts[-1]]
                GenerationKoChunks['ApiSetting'] = MatchedActor['ApiSetting']
                
    # ### 테스트 후 삭제 ### 이 부분에서 Text 수정 UI를 만들어야 함 ###
    # with open('SelectionGenerationKoChunks.json', 'w', encoding = 'utf-8') as json_file:
    #     json.dump(SelectionGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)
    # ### 테스트 후 삭제 ### 이 부분에서 Text 수정 UI를 만들어야 함 ###
    
    return MatchedActors, SelectionGenerationKoChunks
    
## VoiceLayerPath(TTS 저장) 경로 생성
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
    BasePath = '/yaas/storage/s1_Yeoreum/s11_UserStorage'

    # 최종 경로 생성
    voiceLayerPath = os.path.join(BasePath, UserFolderName, StorageFolderName, projectName, f"{projectName}_mixed_audiobook_file", "VoiceLayers", FileName)
    # print(voiceLayerPath)

    return voiceLayerPath

#######################################
##### VoiceLayerGenerator 파일 생성 #####
#######################################
## TypecastVoice 생성 ##
def TypecastVoiceGen(name, Chunk, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath):
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
            'volume': 100, # 오디오 볼륨으로 기본값은 100, 범위: 0.5배는 50 - 2배는 200, 
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
                with open(voiceLayerPath, 'wb') as f:
                    f.write(r.content)
                break
            else:
                print(f"status: {ret['status']}, waiting 1 second")
                time.sleep(1)
        return "Continue"
    else:
        return name

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
def SortAndRemoveDuplicates(VoiceLayerFileName, files):
    # 파일명에서 필요한 정보를 추출하는 함수
    def ExtractFileInfo(FileName):
        match = re.match(r"(.+)_(\d+)_(.+?)\((.+?)\)_\((\d+)\)(M?)\.wav", FileName)
        if match:
            # 생성넘버, 세부생성넘버, M의 유무를 반환
            return {
                'base_name': match.group(1),
                'gen_num': int(match.group(2)),
                'detail_gen_num': int(match.group(5)),
                'has_M': match.group(6) == 'M'
            }
        return None

    # 파일 정보를 기반으로 정렬 및 중복 제거
    SortedFiles = sorted(files, key = lambda File: (
        ExtractFileInfo(File)['gen_num'],
        ExtractFileInfo(File)['detail_gen_num'],
        not ExtractFileInfo(File)['has_M']  # 'M'이 없는 파일을 우선 정렬
    ))

    # 중복 제거
    UniqueFiles = []
    seen = set()
    for file in SortedFiles:
        info = ExtractFileInfo(file)
        identifier = (info['base_name'], info['gen_num'], info['detail_gen_num'])
        if identifier not in seen:
            UniqueFiles.append(file)
            seen.add(identifier)
        elif info['has_M']:  # 'M'이 포함된 파일이면 이전 'M'이 없는 파일을 대체
            # 마지막으로 추가된 파일이 'M'이 없는 파일인지 확인하고, 맞다면 제거
            if UniqueFiles and ExtractFileInfo(UniqueFiles[-1])['has_M'] == False and ExtractFileInfo(UniqueFiles[-1])['gen_num'] == info['gen_num'] and ExtractFileInfo(UniqueFiles[-1])['detail_gen_num'] == info['detail_gen_num']:
                UniqueFiles.pop()  # 'M'이 없는 파일 제거
            UniqueFiles.append(file)

    return UniqueFiles

## 생성된 음성파일 합치기
def VoiceGenerator(projectName, email, EditGenerationKoChunks):
    VoiceLayerFileName = projectName + "_VoiceLayer.wav"
    voiceLayerPath = VoiceLayerPathGen(projectName, email, '')

    # 폴더 내의 모든 .wav 파일 목록 추출
    RawFiles = [f for f in os.listdir(voiceLayerPath) if f.endswith('.wav')]
    # VoiceLayer 파일이 생성되었을 경우 해당 파일명을 RawFiles 리스트에서 삭제
    if VoiceLayerFileName in RawFiles:
        RawFiles.remove(VoiceLayerFileName)
    # 성우 변경 파일이 생성되었을 경우 이전 성우 파일명으로 새로운 RawFiles 리스트에서 생성
    Files = []
    VoiceFilePattern = r".*?_(\d+)_([가-힣]+\([가-힣]+\)).*?\.wav"
    for i in range(len(RawFiles)):
        VoiceFileMatch = re.match(VoiceFilePattern, RawFiles[i])
        if VoiceFileMatch:
            chunkid, actorname = VoiceFileMatch.groups()
        for j in range(len(EditGenerationKoChunks)):
            if int(chunkid) == EditGenerationKoChunks[j]['ChunkId'] and actorname == EditGenerationKoChunks[j]['ActorName']:
                Files.append(RawFiles[i])
                break
    
    # 폴더 내의 모든 .wav 파일 목록 정렬/필터
    FilteredFiles = SortAndRemoveDuplicates(VoiceLayerFileName, Files)
    
    CombinedSound = AudioSegment.empty()
    SilenceDuration_ms = 1000  # 기본값, 실제로는 사용되지 않음

    FilesCount = 0
    for i in range(len(EditGenerationKoChunks)):
        for j in range(len(EditGenerationKoChunks[i]['Pause'])):
            sound_file = AudioSegment.from_wav(os.path.join(voiceLayerPath, FilteredFiles[FilesCount]))
            PauseDuration_ms = EditGenerationKoChunks[i]['Pause'][j] * 1000  # 초를 밀리초로 변환
            silence = AudioSegment.silent(duration=PauseDuration_ms)
            CombinedSound += sound_file + silence
            FilesCount += 1

    # 마지막 파일에 추가된 쉬는 시간을 제거
    CombinedSound = CombinedSound[:-SilenceDuration_ms]

    # 최종적으로 합쳐진 음성 파일 저장
    CombinedSound.export(os.path.join(voiceLayerPath, projectName + "_VoiceLayer.wav"), format = "wav")


## 프롬프트 요청 및 결과물 VoiceLayerGenerator
def VoiceLayerGenerator(projectName, email, voiceDataSet, Mode = "Manual"):
    print(f"< User: {email} | Project: {projectName} | VoiceLayerGenerator 시작 >")
    MatchedActors, SelectionGenerationKoChunks = ActorMatchedSelectionGenerationKoChunks(projectName, email, voiceDataSet)
    for MatchedActor in MatchedActors:
        Actor = MatchedActor['ActorName']

        print(f"< Project: {projectName} | Actor: {Actor} | VoiceLayerGenerator 시작 >")
        # MatchedActors 경로 생성
        fileName = projectName + '_' + 'MatchedVoices.json'
        MatchedActorsPath = VoiceLayerPathGen(projectName, email, fileName)
        # MatchedChunksEdit 경로 생성
        fileName = '[' + projectName + '_' + 'VoiceLayer_Edit].json'
        MatchedChunksPath = VoiceLayerPathGen(projectName, email, fileName)
        OriginFileName = '' + projectName + '_' + 'VoiceLayer_Origin.json'
        MatchedChunksOriginPath = VoiceLayerPathGen(projectName, email, OriginFileName)
        
        ## MatchedChunksPath.json이 존재하면 해당 파일로 VoiceLayerGenerator 진행, 아닐경우 새롭게 생성
        if not os.path.exists(MatchedChunksPath):
            # SelectionGenerationKoChunks의 EditGenerationKoChunks화
            EditGenerationKoChunks = []
            for GenerationKoChunk in SelectionGenerationKoChunks:
                chunkid = GenerationKoChunk['ChunkId']
                tag = GenerationKoChunk['Tag']
                actorname = GenerationKoChunk['ActorName']
                actorchunks = GenerationKoChunk['ActorChunk']
                
                # Pause 추출
                if isinstance(GenerationKoChunk['Chunk'], list):
                    chunks = GenerationKoChunk['Chunk']
                else:
                    chunks = [GenerationKoChunk['Chunk']]
                pauses = []
                for chunk in chunks:
                    pause = ExtractPause(chunk)
                    pauses.append(pause)
                    
                EditGenerationKoChunk = {"ChunkId": chunkid, "Tag": tag, "ActorName": actorname, "ActorChunk": actorchunks, "Pause": pauses}
                EditGenerationKoChunks.append(EditGenerationKoChunk)
            # MatchedActors, MatchedChunks 저장
            fileName = projectName + '_' + 'MatchedVoices.json'
            MatchedActorsPath = VoiceLayerPathGen(projectName, email, fileName)
            with open(MatchedActorsPath, 'w', encoding = 'utf-8') as json_file:
                json.dump(MatchedActors, json_file, ensure_ascii = False, indent = 4)
            with open(MatchedChunksPath, 'w', encoding = 'utf-8') as json_file:
                json.dump(EditGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)
            with open(MatchedChunksOriginPath, 'w', encoding = 'utf-8') as json_file:
                json.dump(EditGenerationKoChunks, json_file, ensure_ascii = False, indent = 4)
        else:
            with open(MatchedActorsPath, 'r', encoding = 'utf-8') as MatchedActorsJson:
                MatchedActors = json.load(MatchedActorsJson)
            with open(MatchedChunksPath, 'r', encoding = 'utf-8') as MatchedChunksJson:
                EditGenerationKoChunks = json.load(MatchedChunksJson)

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
        
        ## VoiceDataSet 불러오기
        VoiceDataSet, CharacterCompletion, SelectionGenerationKoBookContext, SelectionGenerationKoChunks = LoadSelectionGenerationKoChunks(projectName, email, voiceDataSet)

        ## 히스토리 불러오기
        fileName = projectName + '_' + 'VoiceLayer_History_' + Actor + '.json'
        MatchedChunkHistorysPath = VoiceLayerPathGen(projectName, email, fileName)
        if os.path.exists(MatchedChunkHistorysPath):
            with open(MatchedChunkHistorysPath, 'r', encoding = 'utf-8') as MatchedChunkHistorysJson:
                GenerationKoChunkHistorys = json.load(MatchedChunkHistorysJson)
        else:
            GenerationKoChunkHistorys = []

        ### 생성시작 ###
        for Update in UpdateTQDM:
            UpdateTQDM.set_description(f"ChunkToSpeech: ({Update['ActorName']}), {Update['ActorChunk']}")
            ChunkId = Update['ChunkId']
            Name = Update['ActorName']
            Chunks = Update['ActorChunk']
            
            ## 수정생성(Modify) 여부확인 ##
            Modify = "No"
            for History in GenerationKoChunkHistorys:
                if History['ChunkId'] == ChunkId:
                    if History['ActorName'] != Name:
                        History['ActorName'] = Name
                        Modify = "Yes"
                    if History['ActorChunk'] != Chunks:
                        History['ActorChunk'] = Chunks
                        Modify = "Yes"

            ## 보이스 선정 ##
            for VoiceData in VoiceDataSet['Characters']:
                if Name == VoiceData['Name']:
                    ApiSetting = VoiceData['ApiSetting']
                    name = ApiSetting['name']
                    ApiToken = ApiSetting['ApiToken']
                    EMOTION = ApiSetting['emotion_tone_preset']['emotion_tone_preset']
                    SPEED = ApiSetting['speed_x']
                    Pitch = ApiSetting['pitch']
            
            ## 'Narrator', 'Character' 태그가 아닌 경우 끝음 조절하기 ##
            if Update['Tag'] not in ['Narrator', 'Character']:
                LASTPITCH = [-2]
            else:
                LASTPITCH = ApiSetting['last_pitch']

            for i in range(len(Chunks)):
                Chunk = Chunks[i]
                
                # 단어로 끝나는 경우 끝음 조절하기
                if '?' not in Chunk[-2:]:
                    if '.' not in Chunk[-2:]:
                        lastpitch = [-2]
                    elif '다' not in Chunk[-2:]:
                        lastpitch = [-2]
                    else:
                        lastpitch = LASTPITCH
                else:
                    lastpitch = LASTPITCH
                RandomEMOTION = random.choice(EMOTION)
                RandomSPEED = random.choice(SPEED)
                RandomLASTPITCH = random.choice(lastpitch)
                
                ## 수정 여부에 따라 파일명 변경 ##
                if Modify == "Yes":
                    FileName = projectName + '_' + str(ChunkId) + '_' + Name + '_' + f'({str(i)})' + 'M.wav'
                    voiceLayerPath = VoiceLayerPathGen(projectName, email, FileName)
                    
                    with open(MatchedChunkHistorysPath, 'w', encoding = 'utf-8') as json_file:
                        json.dump(GenerationKoChunkHistorys, json_file, ensure_ascii = False, indent = 4)
                    
                    cp = TypecastVoiceGen(name, Chunk, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath)
                    if cp != 'Continue':
                        print(f'\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n@  캐릭터 불일치 -----> [TypeCastAPI의 캐릭터를 ( {cp} ) 으로 변경하세요!] <-----  @\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n')
                        sys.exit()
                else:
                    FileName = projectName + '_' + str(ChunkId) + '_' + Name + '_' + f'({str(i)})' + '.wav'
                    voiceLayerPath = VoiceLayerPathGen(projectName, email, FileName)
                    if not os.path.exists(voiceLayerPath):
                        cp = TypecastVoiceGen(name, Chunk, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath)

                        if cp == 'Continue':
                            ## 히스토리 저장 ##
                            GenerationKoChunkHistory = {"ChunkId": ChunkId, "Tag": Update['Tag'], "ActorName": Name, "ActorChunk": Chunks}
                            GenerationKoChunkHistorys.append(GenerationKoChunkHistory)
                            with open(MatchedChunkHistorysPath, 'w', encoding = 'utf-8') as json_file:
                                json.dump(GenerationKoChunkHistorys, json_file, ensure_ascii = False, indent = 4)
                        else:
                            print(f'\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n@  캐릭터 불일치 -----> [TypeCastAPI의 캐릭터를 ( {cp} ) 으로 변경하세요!] <-----  @\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n')
                            sys.exit()
                
    ## 최종 생성된 음성파일 합치기 ##
    time.sleep(0.1)
    VoiceGenerator(projectName, email, EditGenerationKoChunks)

    print(f"[ User: {email} | Project: {projectName} | VoiceLayerGenerator 완료 ]\n")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "웹3.0메타버스"
    voiceDataSet = "TypeCastVoiceDataSet"
    mode = "Manual"
    #########################################################################
        
    
    
    
    
    # ##########
    # ##########
    # ##### 테스트 후 삭제 #####
    # def TypecastVoiceGeneratorTest(projectName, email, Name, ChunkId, Chunk, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath):
    #     api_token = os.getenv("TYPECAST_API_TOKEN")
    #     HEADERS = {'Authorization': f'Bearer {api_token}'}

    #     # get my actor
    #     r = requests.get('https://typecast.ai/api/actor', headers = HEADERS)
    #     my_actors = r.json()['result']
    #     print(my_actors)
    #     my_first_actor = my_actors[0]
    #     my_first_actor_id = my_first_actor['actor_id']

    #     # request speech synthesis
    #     r = requests.post('https://typecast.ai/api/speak', headers = HEADERS, json = {
    #         'text': Chunk, # 음성을 합성하는 문장
    #         'actor_id': my_first_actor_id, # 캐릭터 아이디로 Actor API에서 캐릭터를 검색
    #         'lang': 'auto', # text의 언어 코드['en-us', 'ko-kr', 'ja-jp', 'es-es', 'auto'], auto는 자동 언어 감지
    #         'xapi_hd': True, # 샘플레이트로 True는 고품질(44.1KHz), False는 저품질(16KHz)
    #         'xapi_audio_format': 'wav', # 오디오 포멧으로 기본값은 'wav', 'mp3'
    #         'model_version': 'latest', # 모델(캐릭터) 버전으로 API를 참고, 최신 모델은 "latest"
    #         'emotion_tone_preset': RandomEMOTION, # 감정으로, actor_id를 사용하여 Actor API 에서 캐릭터에 사용 가능한 감정을 검색
    #         'emotion_prompt': None, # 감정 프롬프트(한/영)를 입력, 입력시 'emotion_tone_preset'는 'emotion_prompt'로 설정
    #         'volume': 100, # 오디오 볼륨으로 기본값은 100, 범위: 0.5배는 50 - 2배는 200, 
    #         'speed_x': RandomSPEED, # 말하는 속도로 기본값은 1, 범위: 0.5(빠름) - 1.5(느림)
    #         'tempo': 1.0, # 음성 재생속도로 기본값은 1, 범위: 0.5(0.5배 느림) - 2.0(2배 빠름)
    #         'pitch': Pitch, # 음성 피치로 기본값은 0, 범위: -12 - 12
    #         'max_seconds': 60, # 음성의 최대 길이로 기본값은 30, 범위: 1 - 60
    #         'force_length': 0, # text의 시간을 max_seconds에 맞추려면 1, 기본값은 0
    #         'last_pitch': RandomLASTPITCH, # 문장 끝의 피치제어로, 기본값은 0, 범위: -2(최저) - 2(최고)
    #     })
    #     speak_url = r.json()['result']['speak_v2_url']

    #     # polling the speech synthesis result
    #     for _ in range(120):
    #         r = requests.get(speak_url, headers=HEADERS)
    #         ret = r.json()['result']
    #         # audio is ready
    #         if ret['status'] == 'done':
    #             # download audio file
    #             r = requests.get(ret['audio_download_url'])
    #             with open(voiceLayerPath + projectName + '_' + str(ChunkId) + '_' + Name + '.wav', 'wb') as f:
    #                 f.write(r.content)
    #             break
    #         else:
    #             print(f"status: {ret['status']}, waiting 1 second")
    #             time.sleep(1)
    #
    # ##########
    # ##########
    # Name = '아리(일반)'
    # ChunkId = 0
    # Chunk = f'지구인들은. {{{{메타버스}}}}에서 살고 있는 셈입니다. 그렇다면 메타버스가 오고 있다는 젠슨 황의 말은 틀렸습니다. 생태계의 현실을 고려해야 한다는 주장이 맞붙었지요. 일론머스크 말대로 웹삼쩜영은 본 사람이 없습니다. 시각적으로 보이게 하려면. 웹삼쩜영에 형체를 만들어 씌워야 하겠지요. 일반인들에게는 그리 필요한 물건도 아니었고. 집에 사놔 봤자. 쓸 수 있는 애플리케이션도 없었기 때문이다. 그러나 트렌드 리더들의 눈은 매섭다. {{{{무브 패스트, 앤드 브레이크 띵스}}}}, 빠르게 움직이고 깨뜨려라.'
    # Pitch = 0
    # SPEED = [1.05]
    # RandomSPEED = random.choice(SPEED)
    # EMOTION = ['normal-1']
    # RandomEMOTION = random.choice(EMOTION)
    # LASTPITCH = [-1]
    # RandomLASTPITCH = random.choice(LASTPITCH)
    # voiceLayerPath = '/yaas/voice/'
    # TypecastVoiceGeneratorTest(projectName, email, Name, ChunkId, Chunk, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath)
    # ##########
    # ##########



    ##########
    ##########
    VoiceLayerGenerator(projectName, email, voiceDataSet, Mode = mode)
    ##########
    ##########
    
    
    
    # ##########
    # ##########
    # from pydub import AudioSegment

    # # 오디오 파일 로드
    # bass = "/yaas/storage/s1_Yeoreum/s11_UserStorage/2024-01-25 09:37:55.937106+09:00_yeoreum_user/2024-01-25 09:37:56.595297+09:00_yeoreum_storage/웹3.0메타버스/웹3.0메타버스_mixed_audiobook_file/VoiceLayers/"
    # audio1 = AudioSegment.from_file(bass + "웹3.0메타버스_1_연우(중간톤)_(0).wav")
    # audio2 = AudioSegment.from_file(bass + "웹3.0메타버스_2_연우(중간톤)_(0).wav")
    # audio3 = AudioSegment.from_file(bass + "웹3.0메타버스_3_연우(중간톤)_(0).wav")
    # audio4 = AudioSegment.from_file(bass + "웹3.0메타버스_4_연우(중간톤)_(0).wav")
    # audio5 = AudioSegment.from_file(bass + "웹3.0메타버스_5_연우(중간톤)_(0).wav")
    # audio6 = AudioSegment.from_file(bass + "웹3.0메타버스_6_연우(중간톤)_(0).wav")
    # audio7 = AudioSegment.from_file(bass + "웹3.0메타버스_7_연우(중간톤)_(0).wav")
    # audio8 = AudioSegment.from_file(bass + "웹3.0메타버스_8_연우(중간톤)_(0).wav")
    # audio9 = AudioSegment.from_file(bass + "웹3.0메타버스_9_연우(중간톤)_(0).wav")
    # audio10 = AudioSegment.from_file(bass + "웹3.0메타버스_10_연우(중간톤)_(0).wav")
    # audio11 = AudioSegment.from_file(bass + "웹3.0메타버스_11_연우(중간톤)_(0).wav")
    # audio12 = AudioSegment.from_file(bass + "웹3.0메타버스_12_연우(중간톤)_(0).wav")
    # audio13 = AudioSegment.from_file(bass + "웹3.0메타버스_13_연우(중간톤)_(0).wav")
    # audio14 = AudioSegment.from_file(bass + "웹3.0메타버스_14_연우(중간톤)_(0).wav")
    # audio15 = AudioSegment.from_file(bass + "웹3.0메타버스_15_연우(중간톤)_(0).wav")
    # audio16 = AudioSegment.from_file(bass + "웹3.0메타버스_16_연우(중간톤)_(0).wav")
    # audio17 = AudioSegment.from_file(bass + "웹3.0메타버스_17_연우(중간톤)_(0).wav")
    # audio18 = AudioSegment.from_file(bass + "웹3.0메타버스_18_연우(중간톤)_(0).wav")
    # audio19 = AudioSegment.from_file(bass + "웹3.0메타버스_19_연우(중간톤)_(0).wav")
    # audio20 = AudioSegment.from_file(bass + "웹3.0메타버스_20_연우(중간톤)_(0).wav")
    # audio21 = AudioSegment.from_file(bass + "웹3.0메타버스_21_연우(중간톤)_(0).wav")
    # audio22 = AudioSegment.from_file(bass + "웹3.0메타버스_22_연우(중간톤)_(0).wav")
    # audio23 = AudioSegment.from_file(bass + "웹3.0메타버스_23_연우(중간톤)_(0).wav")
    # audio24 = AudioSegment.from_file(bass + "웹3.0메타버스_24_연우(중간톤)_(0).wav")
    # audio25 = AudioSegment.from_file(bass + "웹3.0메타버스_25_연우(중간톤)_(0).wav")
    # audio26 = AudioSegment.from_file(bass + "웹3.0메타버스_26_연우(중간톤)_(0).wav")
    # audio27 = AudioSegment.from_file(bass + "웹3.0메타버스_27_연우(중간톤)_(0).wav")

    # # 0.8초의 침묵(공백) 생성
    # silence20 = AudioSegment.silent(duration = 2000) # 단위는 밀리초
    # silence15 = AudioSegment.silent(duration = 1500) # 단위는 밀리초
    # silence07 = AudioSegment.silent(duration = 700) # 단위는 밀리초

    # # 오디오 조각 사이에 침묵 추가하여 합치기
    # combined_audio = audio1 + silence20 + audio2 + silence15 + audio3 + silence07 + audio4 + silence07 + audio5 + silence07 + audio6 + silence07 + audio7 + silence07 + audio8 + silence07 + audio9 + silence07 + audio10 + silence07 + audio11 + silence07 + audio12 + silence07 + audio13 + silence07 + audio14 + silence07 + audio15 + silence07 + audio16 + silence07 + audio17 + silence07 + audio18 + silence07 + audio19 + silence07 + audio20 + silence07 + audio21 + silence07 + audio22 + silence07 + audio23 + silence07 + audio24 + silence07 + audio25 + silence07 + audio26 + silence07 + audio27
    
    # combined_audio.export(bass + "audio.wav", format="wav")
    # #########
    # #########