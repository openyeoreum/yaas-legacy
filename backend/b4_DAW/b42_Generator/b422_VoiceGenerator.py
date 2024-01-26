import os
import requests
import time
import re
import sys
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import User
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject

###########################################
##### SelectionGenerationKoChunks 생성 #####
###########################################
def LoadSelectionGenerationKoChunks(projectName, email):
    project = GetProject(projectName, email)
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
    
    return SelectionGenerationKoChunks

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

# def ActorMatching(CharacterTag, Language, Gender, Age, Emotion):

# def ActorMatching(CharacterTag, Language, Gender, Age, Emotion):

# def ActorSetting(ActorName, Emotion):

# def TextSetting(Text):

def TypecastVoiceGenerator(TEXT, EMOTION):
    api_token = os.getenv("TYPECAST_API_TOKEN")
    HEADERS = {'Authorization': f'Bearer {api_token}'}

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
    email = "yeoreum00128@gmail.com"
    projectName = "데미안"
    #########################################################################
    # SelectionGenerationKoChunks = LoadSelectionGenerationKoChunks(projectName, email)
    # for i in range(len(SelectionGenerationKoChunks)):
    #     print(SelectionGenerationKoChunks[i])
    VoiceCharacter = 'Narrater'
    final_path = VoiceLayerPath(projectName, email, VoiceCharacter)
    print(final_path)
        
    # TEXT = '지구인들은. 메타버스에서 살고 있는 셈입니다. 그렇다면 메타버스가 오고 있다는 젠슨 황의 말은 틀렸습니다. 그러나. 아직 여운이 남아 있긴 합니다. 스크린 골프 이야기로 돌아가 보죠. 지금은 현실세계와. 가상세계 간. 경계가 나뉘어져 있습니다. 스크린이. 경계선입니다. 스크린 이쪽은. 물리적 현실세계. 저쪽은. 초월적 가상세계니까요. 그런데. 기술이 더 발달하면, 스크린이 없어질 수 있습니다.'
    # EMOTION = 'tonedown-1'
    # TypecastVoiceGenerator(TEXT, EMOTION)