import os
import json
import multiprocessing
import unicodedata
import sys
sys.path.append("/yaas")

from dotenv import load_dotenv
from b2_Solution.bm21_GeneralUpdate import AccountUpdate, SolutionProjectUpdate
from b2_Solution.bm22_DataFrameUpdate import SolutionDataFrameUpdate
from b2_Solution.bm23_DataSetUpdate import SolutionDataSetUpdate

from b4_Creation.bm25_AudiobookUpdate import CreationAudioBookUpdate

### Main1 : 프로젝트 Config 생성 ###
def ConfigUpdate(projectNameList, Narrator, CloneVoiceName, ReadingStyle):

    ConfigPath = '/yaas/backend/yaasconfig.json'
    with open(ConfigPath, 'r', encoding='utf-8') as ConfigJson:
        ConfigData = json.load(ConfigJson)

    for projectName in projectNameList:
        if projectName not in ConfigData:
            ConfigData[projectName] = {
                "email": "yeoreum00128@gmail.com",
                "name": "yeoreum",
                "password": "0128",
                "projectNameList": [projectName],
                "Translations": [],
                "IndexMode": "Define",
                "BookGenre": "Auto",
                "MainLang": "Ko",
                "Narrator": Narrator,
                "CloneVoiceName": CloneVoiceName,
                "ReadingStyle": ReadingStyle,
                "VoiceEnhance": "off",
                "VoiceReverbe": "on",
                "Intro": "off",
                "AudiobookSplitting": "Auto",
                "EndMusicVolume": -10
            }

    with open(ConfigPath, 'w', encoding='utf-8') as ConfigJson:
        json.dump(ConfigData, ConfigJson, ensure_ascii = False, indent = 4)

### Main1 : 솔루션 업데이트 ###
def SolutionUpdate(email, projectNameList, IndexMode, MessagesReview, BookGenre, Translations):

    # ## .env 파일 로드(API_KEY 등 환경 변수 액세스)
    # envPath = os.path.join(os.path.dirname(__file__), '..', 'storage', '.env')
    # load_dotenv(dotenv_path = envPath)

    if isinstance(projectNameList, list):
        ## NFC, NFD 오류 문제 해결 (모두 적용)
        for projectName in projectNameList:
            projectName = unicodedata.normalize('NFC', projectName)
            # ScriptFilesPath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s121_ScriptFiles"
            # if os.path.join(ScriptFilesPath, unicodedata.normalize('NFC', _projectName) + "_Index.txt"):
            #     projectName = unicodedata.normalize('NFC', _projectName)
            # elif os.path.join(ScriptFilesPath, unicodedata.normalize('NFD', _projectName) + "_Index.txt"):
            #     projectName = unicodedata.normalize('NFD', _projectName)
            # elif os.path.join(ScriptFilesPath, unicodedata.normalize('NFKC', _projectName) + "_Index.txt"):
            #     projectName = unicodedata.normalize('NFKC', _projectName)
            # elif os.path.join(ScriptFilesPath, unicodedata.normalize('NFKD', _projectName) + "_Index.txt"):
            #     projectName = unicodedata.normalize('NFKD', _projectName)
            # else:
            #     projectName = _projectName

            ### Step2 : 솔루션에 프로젝트 파일 업데이트 ###
            SolutionProjectUpdate(email, projectName)
            
            ### Step3 : 솔루션에 프로젝트 데이터 프레임 진행 및 업데이트 ###
            SolutionDataFrameUpdate(email, projectName, indexMode = IndexMode, messagesReview = MessagesReview, bookGenre = BookGenre, Translations = Translations)
            
            # ### Step4 : 솔루션에 프로젝트 데이터셋 학습진행 및 업데이트 ###
            # SolutionDataSetUpdate(email, projectName)
    
    else:
        ### Step2 : 솔루션에 프로젝트 파일 업데이트 ###
        SolutionProjectUpdate(email, projectName)
        
        ### Step3 : 솔루션에 프로젝트 데이터 프레임 진행 및 업데이트 ###
        SolutionDataFrameUpdate(email, projectName, indexMode = IndexMode, messagesReview = MessagesReview)
        
        # ### Step4 : 솔루션에 프로젝트 데이터셋 학습진행 및 업데이트 ###
        # SolutionDataSetUpdate(email, projectName)
        
### Main2 : 콘텐츠 제작 ###

def CreationUpdate(email, projectNameList, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, AudiobookSplitting, EndMusicVolume, Macro, Account, VoiceEnhance, VoiceFileGen, MessagesReview):

    if isinstance(projectNameList, list):
        ## NFC, NFD 오류 문제 해결 (모두 적용)
        for projectName in projectNameList:
            projectName = unicodedata.normalize('NFC', projectName)
            # ScriptFilesPath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s121_ScriptFiles"
            # if os.path.join(ScriptFilesPath, unicodedata.normalize('NFC', _projectName) + "_Index.txt"):
            #     projectName = unicodedata.normalize('NFC', _projectName)
            # elif os.path.join(ScriptFilesPath, unicodedata.normalize('NFD', _projectName) + "_Index.txt"):
            #     projectName = unicodedata.normalize('NFD', _projectName)
            # elif os.path.join(ScriptFilesPath, unicodedata.normalize('NFKC', _projectName) + "_Index.txt"):
            #     projectName = unicodedata.normalize('NFKC', _projectName)
            # elif os.path.join(ScriptFilesPath, unicodedata.normalize('NFKD', _projectName) + "_Index.txt"):
            #     projectName = unicodedata.normalize('NFKD', _projectName)
            # else:
            #     projectName = _projectName

            ### Step6 : 크리에이션이 오디오북 제작 ###
            CreationAudioBookUpdate(projectName, email, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, audiobookSplitting = AudiobookSplitting, endMusicVolume = EndMusicVolume, macro = Macro, account = Account, voiceEnhance = VoiceEnhance, voiceFileGen = VoiceFileGen, messagesReview = MessagesReview)
            
### YaaS : YaaS의 통합으로 'Solution', 'Solution&Creation' ###

def YaaS(email, name, password, projectNameList, Translations, IndexMode, MessagesReview, BookGenre, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, AudiobookSplitting, EndMusicVolume, VoiceEnhance, VoiceFileGen, MainProcess, Macro, Account):

    if MainProcess == 'Solution':
        AccountUpdate(email, name, password)
        SolutionUpdate(email, projectNameList, IndexMode, MessagesReview, BookGenre, Translations)
        
    elif MainProcess == 'Solution&Creation':
        AccountUpdate(email, name, password)
        SolutionUpdate(email, projectNameList, IndexMode, MessagesReview, BookGenre, Translations)
        CreationUpdate(email, projectNameList, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, AudiobookSplitting, EndMusicVolume, Macro, Account, VoiceEnhance, VoiceFileGen, MessagesReview)

### YaaS Multiprocessing : 오디오북 병렬 제작 ###

## yaasconfig 로드
def Loadyaasconfig(yaasconfigPath = '/yaas/backend/yaasconfig.json'):
    with open(yaasconfigPath, 'r') as f:
        yaasconfig = json.load(f)
    return yaasconfig

## MultiProcessing
def MultiProcessing(projectNameList, Narrator, CloneVoiceName, ReadingStyle, MessagesReview, VoiceFileGen, MainProcess, Macro, Account, yaasconfigPath = '/yaas/backend/yaasconfig.json'):
    print(f"[ Projects: {projectNameList} | 병렬 프로세스(MultiProcessing) 시작 ]")
    ConfigUpdate(projectNameList, Narrator, CloneVoiceName, ReadingStyle)
    yaasconfig = Loadyaasconfig(yaasconfigPath = yaasconfigPath)
    
    processes = []
    for projectName in projectNameList:
        YaasConfig = yaasconfig[projectName]
        Process = multiprocessing.Process(target = YaaS, args = (YaasConfig["email"], YaasConfig["name"], YaasConfig["password"], YaasConfig["projectNameList"], YaasConfig["Translations"], YaasConfig["IndexMode"], MessagesReview, YaasConfig["BookGenre"], YaasConfig["Narrator"], YaasConfig["CloneVoiceName"], YaasConfig["ReadingStyle"], YaasConfig["VoiceReverbe"], YaasConfig["MainLang"], YaasConfig["Intro"], YaasConfig["AudiobookSplitting"], YaasConfig["EndMusicVolume"], YaasConfig["VoiceEnhance"], VoiceFileGen, MainProcess, Macro, Account))
        processes.append(Process)
        Process.start()
        
    # 모든 프로세스가 종료될 때까지 기다림
    for p in processes:
        p.join()
        
    print(f"[ Projects: {projectNameList} | 병렬 프로세스(MultiProcessing) 완료 ]")

## 추가 병렬 진행 : 코세라 라이프 그래프 최신화
## 추가 병렬 진행 : 교보문고 베스트셀러 스크래핑

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    ## '240223_나는외식창업에적합한사람인가', '240223_나무에서만난경영지혜', '240223_노인을위한나라는있다', '240223_마케터의무기들', '240405_빌리월터스겜블러', '240412_카이스트명상수업', '240418_부카출판사', '240426_목소리의힘', '240523_고객검증', '240705_도산안창호', '240801_빨간풍차가있는집', '240802_암을이기는천연항암제', '240919_암을이기는천연항암제요약', '240812_룰루레몬스토리', '240815_노유파', '240908_나무스토리텔링', '240910_AI미래시나리오2030', '240925_불멸의지혜'
    
    projectNameList = ['240925_불멸의지혜']
    Narrator = "VoiceClone" # 'VoiceActor', 'VoiceClone' : VoiceActor 은 일반성우 나레이터, VoiceClone 은 저자성우 나레이터
    CloneVoiceName = "정회준" # 'Narrator' = 'VoiceClone' 인 경우 '저자명' 작성
    ReadingStyle = "NarratorOnly" # 'AllCharacters', 'NarratorOnly' : AllCharacters 는 등장인물별 목소리로 낭독, NarratorOnly 는 1인 나레이터 낭독
    MessagesReview = "on" # 'on', 'off' : on 은 모든 프롬프트 출력, off 는 모든 프롬프트 비출력
    VoiceFileGen = "off" # 'on', 'off' : on 은 Voice.wav 파일 생성, off 는 Voice.wav 파일 비생성
    MainProcess = "Solution&Creation" # 'Solution', 'Solution&Creation'
    Macro = "Auto" # 'Auto', 'Manual' : Auto는 API 캐릭터 변경 자동, Manual은 API 캐릭터 변경 수동
    Account = "khsis3516@naver.com" # 'yeoreum00128@naver.com', 'lucidsun0128@naver.com', 'ahyeon00128@naver.com', 'khsis3516@naver.com', 'lunahyeon00128@naver.com'
    #########################################################################
    
    MultiProcessing(projectNameList, Narrator, CloneVoiceName, ReadingStyle, MessagesReview, VoiceFileGen, MainProcess, Macro, Account)