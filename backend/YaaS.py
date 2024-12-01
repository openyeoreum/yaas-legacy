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
def ConfigUpdate(projectNameList, ScriptGen, Narrator, CloneVoiceName, ReadingStyle):

    ConfigPath = '/yaas/backend/yaasconfig.json'
    with open(ConfigPath, 'r', encoding = 'utf-8') as ConfigJson:
        ConfigData = json.load(ConfigJson)

    for projectName in projectNameList:
        if projectName not in ConfigData:
            ConfigData[projectName] = {
                "email": "yeoreum00128@gmail.com",
                "name": "yeoreum",
                "password": "0128",
                "projectNameList": [projectName],
                "Translations": [],
                "ScriptGen": ScriptGen,
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

    with open(ConfigPath, 'w', encoding = 'utf-8') as ConfigJson:
        json.dump(ConfigData, ConfigJson, ensure_ascii = False, indent = 4)

### Main1 : 솔루션 업데이트 ###
def SolutionUpdate(email, projectNameList, ScriptGen, IndexMode, MessagesReview, BookGenre, Translations):

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
            SolutionProjectUpdate(email, projectName, ScriptGen)
            
            ### Step3 : 솔루션에 프로젝트 데이터 프레임 진행 및 업데이트 ###
            SolutionDataFrameUpdate(email, projectName, scriptGen = ScriptGen, indexMode = IndexMode, messagesReview = MessagesReview, bookGenre = BookGenre, Translations = Translations)
            
            # ### Step4 : 솔루션에 프로젝트 데이터셋 학습진행 및 업데이트 ###
            # SolutionDataSetUpdate(email, projectName)
    
    else:
        ### Step2 : 솔루션에 프로젝트 파일 업데이트 ###
        SolutionProjectUpdate(email, projectName, ScriptGen)
        
        ### Step3 : 솔루션에 프로젝트 데이터 프레임 진행 및 업데이트 ###
        SolutionDataFrameUpdate(email, projectName, scriptGen = ScriptGen, indexMode = IndexMode, messagesReview = MessagesReview)
        
        # ### Step4 : 솔루션에 프로젝트 데이터셋 학습진행 및 업데이트 ###
        # SolutionDataSetUpdate(email, projectName)
        
### Main2 : 콘텐츠 제작 ###

def CreationUpdate(email, projectNameList, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, AudiobookSplitting, EndMusicVolume, Macro, Bracket, VolumeEqual, Account, VoiceEnhance, VoiceFileGen, Bitrate, MessagesReview):

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
            CreationAudioBookUpdate(projectName, email, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, audiobookSplitting = AudiobookSplitting, endMusicVolume = EndMusicVolume, macro = Macro, bracket = Bracket, volumeEqual = VolumeEqual, account = Account, voiceEnhance = VoiceEnhance, voiceFileGen = VoiceFileGen, bitrate = Bitrate, messagesReview = MessagesReview)
            
### YaaS : YaaS의 통합으로 'Solution', 'Solution&Creation' ###

def YaaS(email, name, password, projectNameList, Translations, ScriptGen, IndexMode, MessagesReview, BookGenre, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, AudiobookSplitting, EndMusicVolume, VoiceEnhance, VoiceFileGen, Bitrate, MainProcess, Macro, Bracket, VolumeEqual, Account):

    if MainProcess == 'Solution':
        AccountUpdate(email, name, password)
        SolutionUpdate(email, projectNameList, ScriptGen, IndexMode, MessagesReview, BookGenre, Translations)
        
    elif MainProcess == 'Solution&Creation':
        AccountUpdate(email, name, password)
        SolutionUpdate(email, projectNameList, ScriptGen, IndexMode, MessagesReview, BookGenre, Translations)
        CreationUpdate(email, projectNameList, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, AudiobookSplitting, EndMusicVolume, Macro, Bracket, VolumeEqual, Account, VoiceEnhance, VoiceFileGen, Bitrate, MessagesReview)

### YaaS Multiprocessing : 오디오북 병렬 제작 ###

## yaasconfig 로드
def Loadyaasconfig(yaasconfigPath = '/yaas/backend/yaasconfig.json'):
    with open(yaasconfigPath, 'r') as f:
        yaasconfig = json.load(f)
    return yaasconfig

## MultiProcessing
def MultiProcessing(projectNameList, ScriptGen, Narrator, CloneVoiceName, ReadingStyle, MessagesReview, VoiceFileGen, Bitrate, MainProcess, Macro, Bracket, VolumeEqual, Account, yaasconfigPath = '/yaas/backend/yaasconfig.json'):
    print(f"[ Projects: {projectNameList} | 병렬 프로세스(MultiProcessing) 시작 ]")
    ConfigUpdate(projectNameList, ScriptGen, Narrator, CloneVoiceName, ReadingStyle)
    yaasconfig = Loadyaasconfig(yaasconfigPath = yaasconfigPath)
    
    processes = []
    for projectName in projectNameList:
        YaasConfig = yaasconfig[projectName]
        Process = multiprocessing.Process(target = YaaS, args = (YaasConfig["email"], YaasConfig["name"], YaasConfig["password"], YaasConfig["projectNameList"], YaasConfig["Translations"], YaasConfig["ScriptGen"], YaasConfig["IndexMode"], MessagesReview, YaasConfig["BookGenre"], YaasConfig["Narrator"], YaasConfig["CloneVoiceName"], YaasConfig["ReadingStyle"], YaasConfig["VoiceReverbe"], YaasConfig["MainLang"], YaasConfig["Intro"], YaasConfig["AudiobookSplitting"], YaasConfig["EndMusicVolume"], YaasConfig["VoiceEnhance"], VoiceFileGen, Bitrate, MainProcess, Macro, Bracket, VolumeEqual, Account))
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
    ## projectNameList ##
    # '240223_나는외식창업에적합한사람인가', '240223_나무에서만난경영지혜', '240223_노인을위한나라는있다', '240223_마케터의무기들', '240405_빌리월터스겜블러', '240412_카이스트명상수업', '240705_도산안창호', '240801_빨간풍차가있는집', '240802_암을이기는천연항암제', '240919_암을이기는천연항암제요약', '240812_룰루레몬스토리', '240815_노유파', '240908_나무스토리텔링', '240910_AI미래시나리오2030', '240925_불멸의지혜', '241005_그해여름필립로커웨이에서일어난소설같은일', '241009_책갈피와책수레', '241010_틈틈이낭만', '241024_오성삼유튜브', '241024_서울장애인가족지원센터당선작13선', '241029_누가정부창업지원을받는가', '241116_베이버터와다섯개의빛', '241118_세종교육청우리반오디오북새움중1학년8반', '241118_세종교육청우리반오디오북아름초5학년5반', '241118_세종교육청우리반오디오북아름초1학년1반', '241127_엄마의첫공부', '241128_끌리는이들에겐이유가있다'
    
    ## ScriptGen ##
    # 디폴트: {"ScriptGen": "off", "RawMode": "on", "Process": "", "Mode": "Master", "MainKey": "", "KeyList": []}
    # 우리반시집: {"ScriptGen": "on", "RawMode": "off", "Process": "SejongCityOfficeOfEducation_Poem", "Mode": "Master", "MainKey": "단락", "KeyList": ["선생님의 소개", "아이가 작성한 시", "선생님의 칭찬"]}
    # 빼기명상을통한나의변화: {"ScriptGen": "on", "RawMode": "off", "Process": "ChangesAfterMeditation_Script", "Mode": "Master", "MainKey": "글내용", "KeyList": ["목차", "내용"]}

    projectNameList = ['240412_카이스트명상수업']
    ScriptGen = {"ScriptGen": "off", "RawMode": "on", "Process": "", "Mode": "Master", "MainKey": "", "KeyList": []} # 'Gen' : 'on', 'off' : on 은 스크립트 생성으로 시작, off 는 스트립트 생성 필요없음 / 'RawMode' : 'on', 'off' : on 은 _Index(Raw).txt 및 _Body(Raw).txt 생성, off 는 _Index.txt 및 _Body.txt 생성 / 'Process' : 'SejongCityOfficeOfEducation_Poem' ... / 'MainKey', 'KeyList' : '메인키': ['프롬프트 결과로', '나오는 KeyList', '작성']
    Narrator = "VoiceActor" # 'VoiceActor', 'VoiceClone' : VoiceActor 은 일반성우 나레이터, VoiceClone 은 저자성우 나레이터
    CloneVoiceName = "이덕주(낭독)" # 'Narrator = 'VoiceActor' 인 경우 '저자명(특성)' 작성, 'Narrator' = 'VoiceClone' 인 경우 '저자명' 작성
    ReadingStyle = "AllCharacters" # 'AllCharacters', 'NarratorOnly' : AllCharacters 는 등장인물별 목소리로 낭독, NarratorOnly 는 1인 나레이터 낭독
    MessagesReview = "on" # 'on', 'off' : on 은 모든 프롬프트 출력, off 는 모든 프롬프트 비출력
    VoiceFileGen = "off" # 'on', 'off' : on 은 Voice.wav 파일 생성, off 는 Voice.wav 파일 비생성
    Bitrate = "320k" # 320k, 192k, 128k, 64k : 최종 저장되는 오디오북 mp3파일의 음질
    MainProcess = "Solution&Creation" # 'Solution', 'Solution&Creation'
    Macro = "Auto" # 'Auto', 'Manual' : Auto는 API 캐릭터 변경 자동, Manual은 API 캐릭터 변경 수동
    Bracket = "Auto" # 'Auto', 'Manual', 'Practice' : Auto는 대괄호 자동, Manual은 대괄호 수동, Practice는 연습
    VolumeEqual = "Mastering" # 'Mixing', 'Mastering' : Mixing은 작업중, Mastering은 최종 마무리로 모든 음성 일률화
    Account = "lunahyeon00128@naver.com" # 'yeoreum00128@naver.com', 'lucidsun0128@naver.com', 'ahyeon00128@naver.com', 'khsis3516@naver.com', 'lunahyeon00128@naver.com', 'kka6887@hanmail.net', 'aldus5909@naver.com'
    #########################################################################

    MultiProcessing(projectNameList, ScriptGen, Narrator, CloneVoiceName, ReadingStyle, MessagesReview, VoiceFileGen, Bitrate, MainProcess, Macro, Bracket, VolumeEqual, Account)