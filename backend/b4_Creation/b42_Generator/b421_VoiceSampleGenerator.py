import os
import requests
import time
import random
import json
import sys
sys.path.append("/yaas")

############################
##### Voice Sample 생성 #####
############################
def TypecastVoiceGeneratorTest(projectName, Name, ChunkId, Chunk, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath):
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
            
def VoiceSampleGen(testerName, name, emotion, pitch, lastpitch):
    Pitch = 0
    pitchname = ''
    if pitch == '다운':
        Pitch = -1
        pitchname = ', 피치다운'
    elif pitch == '업':
        Pitch = 1
        pitchname = ', 피치업'
        
    filename = name + '(' + emotion + pitchname + ')'
    ChunkId = 0
    Chunk = '뿐만 아니라, 여름은 최근 창업진흥원에서 주관하는 대회에서 대상을 수상하며, 그들의 혁신적인 기술과 사회적 기여를 인정받았다. 이준영 대표는 수상 소감에서 "이 상은 단지 우리의 기술적 성과만을 인정하는 것이 아니라, 우리가 추구하는 가치와 비전에 대한 공감을 의미합니다. 우리는 앞으로도 지식의 접근성을 높이고, 누구나 쉽게 지식을 소비할 수 있는 환경을 만드는 것을 목표로 삼고 있습니다.라고 전했다. 주어진 요구사항에 따라 코드를 수정해 보겠습니다. 파일을 하나로 합치기 전에 각 파일에 대한 정보를 확인해야 합니다. 먼저 파일들을 로드하고 각각의 샘플 레이트와 데이터를 확인해 보겠습니다. 파일을 찾을 수 없다는 오류가 발생했습니다.'
    # Chunk = f'지구인들은. {{{{메타버스}}}}에서 살고 있는 셈입니다. 그렇다면 메타버스가 오고 있다는 젠슨 황의 말은 틀렸습니다. 생태계의 현실을 고려해야 한다는 주장이 맞붙었지요. 일론머스크 말대로 웹삼쩜영은 본 사람이 없습니다. 시각적으로 보이게 하려면. 웹삼쩜영에 형체를 만들어 씌워야 하겠지요. 일반인들에게는 그리 필요한 물건도 아니었고. 집에 사놔 봤자. 쓸 수 있는 애플리케이션도 없었기 때문이다. 그러나 트렌드 리더들의 눈은 매섭다. {{{{무브 패스트, 앤드 브레이크 띵스}}}}, 빠르게 움직이고 깨뜨려라. 그 아저씨들 기억나죠요고, 응돈 던지고, 그렇다면 메타버스가 오고 있다는 젠슨 황의 말은 틀린거지?, 그런거지?, 야 너 잠시만 이리로 와봐, 나는 그 사실이 너무 슬픈걸 어떡하니?'
    # Chunk = f"Humans are essentially living in the metaverse. Thus, Jensen Huang's statement that the metaverse is coming is incorrect. The argument that we must consider the reality of the ecosystem has clashed with this. According to Elon Musk, no one has seen Web 3.0. To make it visually apparent, we need to create a form for Web 3.0. It wasn't even necessary for the general public."
    SPEED = [1.05]
    
    RandomSPEED = random.choice(SPEED)

    if emotion == '일반':
        EMOTION = ['normal-1', 'normal-2', 'normal-3', 'normal-4']
    elif emotion == '톤업':
        EMOTION = ['toneup-1', 'toneup-2', 'toneup-3', 'toneup-4']
    elif emotion == '중간톤':
        EMOTION = ['tonemid-1', 'tonemid-2', 'tonemid-3', 'tonemid-4']
    elif emotion == '톤다운':
        EMOTION = ['tonedown-1', 'tonedown-2', 'tonedown-3', 'tonedown-4']
    elif emotion == '슬픔':
        EMOTION = ['sad-1', 'sad-2', 'sad-3', 'sad-4']
    elif emotion == '기쁨':
        EMOTION = ['happy-1', 'happy-2', 'happy-3', 'happy-4']
    elif emotion == '화남':
        EMOTION = ['angry-1', 'angry-2', 'angry-3', 'angry-4']
    elif emotion == '절규':
        EMOTION = ["scream-1", "scream-2", "scream-3"]
    elif emotion == '속삭임':
        EMOTION = ['whisper-1', 'whisper-2', 'whisper-3', 'whisper-4']
    elif emotion == '신뢰':
        EMOTION = ['trustful-1']
    elif emotion == '부드러운':
        EMOTION = ['soft-1', 'soft-2', 'soft-3', 'soft-4']
    elif emotion == '응원':
        EMOTION = ['cheer-1', 'cheer-2', 'cheer-3', 'cheer-4']
    elif emotion == '차가움':
        EMOTION = ['cold-1', 'cold-2', 'cold-3', 'cold-4']
    elif emotion == '설득':
        EMOTION = ['inspire-1', 'inspire-2']
        
    RandomEMOTION = random.choice(EMOTION)
    RandomLASTPITCH = random.choice(lastpitch)
    voiceLayerPath = '/yaas/storage/s1_Yeoreum/s14_VoiceStorage/'
    TypecastVoiceGeneratorTest(testerName, filename, ChunkId, Chunk, RandomEMOTION, RandomSPEED, Pitch, RandomLASTPITCH, voiceLayerPath)

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    testerName = "테스트(가)"
    name = '연우'
    emotionlist = ['중간톤']
    pitch = '다운'
    lastpitch = [-1, -2]
    #########################################################################
    for emotion in emotionlist:
        VoiceSampleGen(testerName, name, emotion, pitch, lastpitch)
        time.sleep(1)