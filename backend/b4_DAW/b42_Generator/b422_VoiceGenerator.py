import os
import requests
import time
import random
import re
import sys
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import User
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetVoiceDataSet

###########################################
##### SelectionGenerationKoChunks 생성 #####
###########################################
def LoadSelectionGenerationKoChunks(projectName, email, voiceDataSet):
    project = GetProject(projectName, email)
    VoiceDataSet = GetVoiceDataSet(voiceDataSet)
    SelectionGenerationKoBookContext = project.SelectionGenerationKo[1]['SelectionGenerationKoBookContext'][1]
    SelectionGenerationKoSplitedIndexs = project.SelectionGenerationKo[1]['SelectionGenerationKoSplitedIndexs'][1:]
    
    SelectionGenerationKoChunks = []
    for i in range(len(SelectionGenerationKoSplitedIndexs)):
        SelectionGenerationKoSplitedBodys = SelectionGenerationKoSplitedIndexs[i]['SelectionGenerationKoSplitedBodys']
        for j in range(len(SelectionGenerationKoSplitedBodys)):
            SelectionGenerationKoSplitedChunks = SelectionGenerationKoSplitedBodys[j]['SelectionGenerationKoSplitedChunks']
            for k in range(len(SelectionGenerationKoSplitedChunks)):
                ChunkId = SelectionGenerationKoSplitedChunks[k]['ChunkId']
                Chunk = SelectionGenerationKoSplitedChunks[k]['Chunk']
                Voice = SelectionGenerationKoSplitedChunks[k]['Voice']
                SelectionGenerationKoChunks.append({'ChunkId': ChunkId, 'Chunk': Chunk, 'Voice': Voice})
    
    return SelectionGenerationKoBookContext, SelectionGenerationKoChunks

def ActorMatching(projectName, email):
    SelectionGenerationKoBookContext, SelectionGenerationKoChunks = LoadSelectionGenerationKoChunks(projectName, email)
    # print(SelectionGenerationKoBookContext['Vector'])
    for i in range(len(SelectionGenerationKoChunks)):
        print(f"{i+1}: {SelectionGenerationKoChunks[i]['Context']}, {SelectionGenerationKoChunks[i]['Voice']}")

# def TextSetting(Text):

## VoiceLayerPath(TTS 저장) 경로 생성
def VoiceLayerPath(projectName, email, VoiceCharacter):
    # 데이터베이스에서 사용자 이름 찾기
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()
        if user is None:
            raise ValueError("User not found with the provided email")
        
        username = user.UserName

    # 첫번째, 두번째 폴더 패턴: 시간 스탬프와 사용자 이름을 포함
    FirstFolderPattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2}_'+ re.escape(username) + '_user')
    SecondFolderPattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2}_'+ re.escape(username) + '_storage')
    base_path = '/yaas/storage/s1_Yeoreum/s11_UserStorage'

    # 첫 번째 폴더 찾기
    first_folder = None
    for folder in os.listdir(base_path):
        if FirstFolderPattern.match(folder):
            first_folder = folder
            break
    if not first_folder:
        raise FileNotFoundError("First pattern folder not found")

    # 두 번째 폴더 찾기
    SecondFolderPath = os.path.join(base_path, first_folder)
    SecondFolder = None
    for folder in os.listdir(SecondFolderPath):
        if SecondFolderPattern.match(folder):
            SecondFolder = folder
            break
    if not SecondFolder:
        raise FileNotFoundError("Second pattern folder not found")

    # 최종 경로 생성
    voiceLayerPath = os.path.join(SecondFolderPath, SecondFolder, projectName, f"{projectName}_mixed_audiobook_file", "VoiceLayers", VoiceCharacter)

    return voiceLayerPath

def TypecastVoiceGenerator(projectName, email, Name, ChunkId, Chunk, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath):
    api_token = os.getenv("TYPECAST_API_TOKEN")
    HEADERS = {'Authorization': f'Bearer {api_token}'}

    # get my actor
    r = requests.get('https://typecast.ai/api/actor', headers = HEADERS)
    my_actors = r.json()['result']
    print(my_actors)
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
            with open(voiceLayerPath + projectName + '_' + str(ChunkId) + '_' + Name + '.wav', 'wb') as f:
                f.write(r.content)
            break
        else:
            print(f"status: {ret['status']}, waiting 1 second")
            time.sleep(1)
            
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "웹3.0메타버스"
    #########################################################################
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
    # TypecastVoiceGenerator(projectName, email, Name, ChunkId, Chunk, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath)
    
    ActorMatching(projectName, email)