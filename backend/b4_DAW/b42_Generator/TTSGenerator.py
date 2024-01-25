import requests
import time

# def TypecastActorSetting(ActorNane, Emotion):

# def TypecastTextSetting(Text):

def TypecastTTSGen(APITOKEN, TEXT, EMOTION):
    HEADERS = {'Authorization': f'Bearer {APITOKEN}'}

    TEXT = '그때 그의 인사는 우리를 흉내 내긴 했으나, 그럼에도 너무나 어른스러웠고. 점잖았다.'

    EMOTION = 'tonedown-1'

    # get my actor
    r = requests.get('https://typecast.ai/api/actor', headers=HEADERS)
    my_actors = r.json()['result']
    my_first_actor = my_actors[0]
    my_first_actor_id = my_first_actor['actor_id']

    # request speech synthesis
    r = requests.post('https://typecast.ai/api/speak', headers=HEADERS, json={
        'text': TEXT,
        'lang': 'auto',
        'actor_id': my_first_actor_id,
        'xapi_hd': True,
        'model_version': 'latest',
        'emotion_tone_preset': EMOTION
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
            with open(TEXT + '.wav', 'wb') as f:
                f.write(r.content)
            break
        else:
            print(f"status: {ret['status']}, waiting 1 second")
            time.sleep(1)
            
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    APITOKEN = '__pltPqcmDToHtmHEBpGxAB58GY4KyyerqHKNexzh2FY3'
    #########################################################################

    TypecastTTSGen(APITOKEN, TEXT, EMOTION)