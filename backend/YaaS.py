import os
import json
import multiprocessing
import unicodedata
import sys
sys.path.append("/yaas")

from b2_Solution.bm21_GeneralUpdate import AccountUpdate, SolutionProjectUpdate
from backend.b2_Solution.bm22_EstimateUpdate import SolutionEstimateUpdate
from backend.b2_Solution.bm25_DataFrameUpdate import SolutionDataFrameUpdate
from backend.b4_Creation.bm28_AudioBookUpdate import CreationAudioBookUpdate


#################################
#################################
### Step3 : 프로젝트 Config 설정 ###
#################################
#################################

## YaaSConfig 로드
def LoadYaaSConfig(ProjectName):
    ConfigPath = f'/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{ProjectName}/{ProjectName}_config.json'
    if not os.path.exists(ConfigPath):
        with open(ConfigPath, 'w', encoding = 'utf-8') as ConfigJson:
            json.dump({}, ConfigJson, ensure_ascii = False, indent = 4)
    
    with open(ConfigPath, 'r', encoding='utf-8') as ConfigJson:
        YaasConfig = json.load(ConfigJson)
        
    return YaasConfig, ConfigPath

## YaaSConfig 설정
def YaasConfigUpdate(StartProjectName, MainLang, Translations, Estimate, DataCollection, Script, TextBook, AudioBook, Marketing):

    ## YaaSConfig 로드
    YaasConfig, ConfigPath = LoadYaaSConfig(StartProjectName)

    ## YaaSConfig 설정
    if YaasConfig == {}:
        print(f"[ Project: {StartProjectName} | Config.json 생성 및 설정 ]")
        
        ### Step3-1 : Project 설정 ###
        email = "yeoreum00128@gmail.com"
        name = "yeoreum"
        password = "0128"
        ProjectName = StartProjectName
        MainLang = MainLang
        Translations = Translations
        
        ### Step3-2 : EstimateConfig 설정 ###
        if Estimate == ["None"]:
            EstimateConfig = {}
        else:
            EstimateConfig = {
                "Estimate": Estimate
                }
            
        ### Step3-3 : DataCollectionConfig 설정 ###
        if DataCollection == ["None"]:
            DataCollectionConfig = {}
        else:
            DataCollectionConfig = {"DataCollection": DataCollection}
            
        ### Step3-4 : ScriptConfig 설정 ###
        if Script == ["None"]:
            ScriptConfig = {}
        else:
            ScriptConfig = {"Script": Script}
            
        ### Step3-5 : TextBookConfig 설정 ###
        if TextBook == ["None"]:
            TextBookConfig = {}
        else:
            TextBookConfig = {"TextBook": TextBook}
            
        ### Step3-6 : AudioBookConfig 설정 ###
        if AudioBook == "None":
            AudioBookConfig = {}
        else:
            CloneVoiceName = AudioBook
            if "(" in CloneVoiceName and ")" in CloneVoiceName:
                Narrator = "VoiceActor"
            else:
                Narrator = "VoiceClone"
            AudioBookConfig = {
                "IndexMode": "Define",
                "BookGenre": "Auto",
                "Narrator": Narrator,
                "CloneVoiceName": CloneVoiceName,
                "ReadingStyle": "NarratorOnly",
                "VoiceEnhance": "off",
                "VoiceReverbe": "on",
                "Intro": "off",
                "AudiobookSplitting": "Auto",
                "MusicDB": "Template",
                "EndMusicVolume": -10,
                "VoiceFileGen": "off",
                "Bitrate": "320k",
                "Macro": "Auto",
                "Bracket": "Auto",
                "VolumeEqual": "Mastering"
                }
            
        ### Step3-7 MarketingConfig 설정 ###
        if Marketing == ["None"]:
            MarketingConfig = {}
        else:
            MarketingConfig = {"Marketing": Marketing}
        
        ## YaaSConfig 업데이트
        YaasConfig = {"email": email, "name": name, "password": password, "ProjectName": ProjectName, "MainLang": MainLang, "Translations": Translations, "EstimateConfig": EstimateConfig, "DataCollectionConfig": DataCollectionConfig, "ScriptConfig": ScriptConfig, "TextBookConfig": TextBookConfig, "AudioBookConfig": AudioBookConfig, "MarketingConfig": MarketingConfig}

    ## 업데이트 된 YaaSConfig 저장
    with open(ConfigPath, 'w', encoding = 'utf-8') as ConfigJson:
        json.dump(YaasConfig, ConfigJson, ensure_ascii = False, indent = 4)


##############################################################################################
##############################################################################################
### Step4-8 : 'Estimate', 'DataCollection', 'Script', 'TextBook', 'AudioBook', 'Marketing' ###
##############################################################################################
##############################################################################################


### Step4 : AudioBook 업데이트 ###
def EstimateUpdate(email, ProjectName, Estimate):
    
    ### Step4-1 : AudioBook 데이터 프레임 ###
    SolutionEstimateUpdate(ProjectName, email, Estimate)

### Step8 : AudioBook 업데이트 ###
def AudioBookUpdate(email, ProjectName, Translations, IndexMode, BookGenre, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, AudiobookSplitting, MusicDB, EndMusicVolume, Macro, Bracket, VolumeEqual, Account, VoiceEnhance, VoiceFileGen, Bitrate, MessagesReview):
    
    ### Step8-1 : AudioBook 데이터 프레임 ###
    SolutionDataFrameUpdate(email, ProjectName, indexMode = IndexMode, messagesReview = MessagesReview)
    
    ### Step8-2 : AudioBook 제작 ###
    CreationAudioBookUpdate(ProjectName, email, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, audiobookSplitting = AudiobookSplitting, musicDB = MusicDB, endMusicVolume = EndMusicVolume, macro = Macro, bracket = Bracket, volumeEqual = VolumeEqual, account = Account, voiceEnhance = VoiceEnhance, voiceFileGen = VoiceFileGen, bitrate = Bitrate, messagesReview = MessagesReview)


###############################################################################################################
###############################################################################################################
### Main2 : YaaS에서 통합으로 'Estimate', 'DataCollection', 'Script', 'TextBook', 'AudioBook', 'Marketing' 제작 ###
###############################################################################################################
###############################################################################################################


def YaaS(email, ProjectName, MainLang, Translations, EstimateConfig, DataCollectionConfig, ScriptConfig, TextBookConfig, AudioBookConfig, MarketingConfig, MessagesReview, Account):
    
    ### Step4 : Estimate 업데이트 ###
    if EstimateConfig != "None":
        EstimateUpdate(email, ProjectName, EstimateConfig['Estimate'])
    
    ### Step5 : DataCollection 업데이트 ###
    if DataCollectionConfig != "None":
        pass
    
    ### Step6 : Script 업데이트 ###
    if ScriptConfig != "None":
        pass
        
    ### Step7 : TextBook 업데이트 ###
    if TextBookConfig != "None":
        pass
    
    ### Step8 : AudioBook 업데이트 ###
    if AudioBookConfig != "None":
        AudioBookUpdate(email, ProjectName, Translations, AudioBookConfig['IndexMode'], AudioBookConfig['BookGenre'], AudioBookConfig['Narrator'], AudioBookConfig['CloneVoiceName'], AudioBookConfig['ReadingStyle'], AudioBookConfig['VoiceReverbe'], MainLang, AudioBookConfig['Intro'], AudioBookConfig['AudiobookSplitting'], AudioBookConfig['MusicDB'], AudioBookConfig['EndMusicVolume'], AudioBookConfig['Macro'], AudioBookConfig['Bracket'], AudioBookConfig['VolumeEqual'], Account, AudioBookConfig['VoiceEnhance'], AudioBookConfig['VoiceFileGen'], AudioBookConfig['Bitrate'], MessagesReview)
    
    ### Step9 : Marketing 업데이트 ###
    if MarketingConfig != "None":
        pass


#################################################################################################################################
#################################################################################################################################
### Main1 : YaaS Multiprocessing에서 병렬로 'Estimate', 'DataCollection', 'Script', 'TextBook', 'AudioBook', 'Marketing' 동시 제작 ###
#################################################################################################################################
#################################################################################################################################


def MultiProcessing(User, ProjectNameList, MainLang, Translations, Estimate, DataCollection, Script, TextBook, AudioBook, Marketing, MessagesReview, Account):
    ## ProjectNameList NFC 정규화
    StartProjectName = unicodedata.normalize("NFC", ProjectNameList["StartProjectName"])
    NFCProjectNameList = []
    for ProjectName in ProjectNameList["ContinueProjectNameList"]:
        NFCProjectNameList.append(unicodedata.normalize("NFC", ProjectName))
    projectNameList = []
    for _ProjectName in (NFCProjectNameList + [StartProjectName]):
        if len(_ProjectName.split('_')[0]) == 6:
            projectNameList.append(_ProjectName)
        else:
            sys.exit(f'[ 잘못된 프로젝트 이름: ("{_ProjectName}"), YYMMDD_프로젝트명 형식으로 입력 또는 리스트를 비워주세요 ]')
    
    print(f"[ Projects: {projectNameList} | 병렬 프로세스(MultiProcessing) 시작 ]")
    
    ## MultiProcessing 실행
    MultiProcess = []
    for projectName in projectNameList:
        ### Step1 : 솔루션에 계정정보 업데이트 ###
        AccountUpdate(User['email'], User['name'], User['password'])
        ### Step2 : 솔루션에 프로젝트 파일 업데이트 ###
        SolutionProjectUpdate(User['email'], StartProjectName)
        ### Step3 : 프로젝트 Config 설정 ###
        if projectName == StartProjectName:
            YaasConfigUpdate(StartProjectName, MainLang, Translations, Estimate, DataCollection, Script, TextBook, AudioBook, Marketing)
        ## Config 불러오기
        YaasConfig, ConfigPath = LoadYaaSConfig(projectName)
        
        Process = multiprocessing.Process(target = YaaS, args = (YaasConfig["email"], YaasConfig["ProjectName"], YaasConfig["MainLang"], YaasConfig["Translations"], YaasConfig["EstimateConfig"], YaasConfig["DataCollectionConfig"], YaasConfig["ScriptConfig"], YaasConfig["TextBookConfig"], YaasConfig["AudioBookConfig"], YaasConfig["MarketingConfig"], MessagesReview, Account))
        MultiProcess.append(Process)
        Process.start()
        
    ## 모든 프로세스가 종료될 때까지 기다림
    for process in MultiProcess:
        process.join()
        
    print(f"[ Projects: {projectNameList} | 병렬 프로세스(MultiProcessing) 완료 ]")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    ## ProjectNameList ##
    # '240223_나는외식창업에적합한사람인가', '240223_나무에서만난경영지혜', '240223_노인을위한나라는있다', '240223_마케터의무기들', '240405_빌리월터스겜블러', '240412_카이스트명상수업', '240705_도산안창호', '240801_빨간풍차가있는집', '240802_암을이기는천연항암제', '240919_암을이기는천연항암제요약', '240812_룰루레몬스토리', '240815_노유파', '240908_나무스토리텔링', '240910_AI미래시나리오2030', '240925_불멸의지혜', '241005_그해여름필립로커웨이에서일어난소설같은일', '241009_책갈피와책수레', '241010_틈틈이낭만', '241024_오성삼유튜브', '241024_서울장애인가족지원센터당선작13선', '241029_누가정부창업지원을받는가', '241116_베이버터와다섯개의빛', '241118_세종교육청우리반오디오북새움중1학년8반', '241118_세종교육청우리반오디오북아름초5학년5반', '241118_세종교육청우리반오디오북아름초1학년1반', '241127_엄마의첫공부', '241128_끌리는이들에겐이유가있다', '241204_개정교육과정초등교과별이해연수', '241210_공부하듯주식해서보화찾기요약', '241210_끌리는이들에겐이유가있다요약', '241210_나는외식창업에적합한사람인가요약'
    
    ## ScriptGen ##
    # 디폴트: {"ScriptGen": "off", "RawMode": "on", "Model": "ANTHROPIC", "Process": "", "Mode": "Master", "MainKey": "", "KeyList": []}
    # 샘플제작: {"ScriptGen": "on", "RawMode": "on", "Model": "ANTHROPIC", "Process": "Sample_Script", "Mode": "Master", "MainKey": "단락", "KeyList": ["선생님의 소개", "아이가 작성한 시", "선생님의 칭찬"]}
    # 우리반시집: {"ScriptGen": "on", "RawMode": "off", "Model": "ANTHROPIC", "Process": "SejongCityOfficeOfEducation_Poem", "Mode": "Master", "MainKey": "단락", "KeyList": ["선생님의 소개", "아이가 작성한 시", "선생님의 칭찬"]}
    # 빼기명상을통한나의변화: {"ScriptGen": "on", "RawMode": "off", "Model": "ANTHROPIC", "Process": "ChangesAfterMeditation_Script", "Mode": "Master", "MainKey": "글내용", "KeyList": ["목차", "내용"]}

    User = {"email": "yeoreum00128@gmail.com", "name": "yeoreum", "password": "0128"}
    ProjectNameList = {"StartProjectName": "241204_개정교육과정초등교과별이해연수", "ContinueProjectNameList": []}
    MainLang = "Ko" # 'Ko', 'En', 'Ja', 'Zh', 'Es' ... 중 메인이 되는 언어를 선택
    Translations = [] # 'En', 'Ja', 'Zh', 'Es' ... 중 다중 선택
    
    Estimate = ["TextBook", "AudioBook", "VideoBook"] # 'None', 'TextBook', 'AudioBook', 'VideoBook' ... 중 필요한 견적을 다중 선택
    DataCollection = ["None"] # 'None', 'Book', 'Meditation', 'Architect' ... 중 데이터 수집이 필요한 도메인을 다중 선택
    Script = ["None"] # 'None', 'SejongCityOfficeOfEducation_Poem', 'ChangesAfterMeditation_Script', 'Sample_Script', 'ONDOBook', 'ONDOMeditation', 'ONDOArchitect', 'LifeGraphAnalysis', 'InstagramTemplate1', 'BlogTemplate1' ... 중 스크립트 생성 템플릿을 다중 선택
    TextBook = ["None"] # 'None', 'ONDOBook', 'ONDOMeditation', 'ONDOArchitect', 'LifeGraphAnalysis' ... 중 텍스트북 제작 템플릿을 다중 선택
    AudioBook = "진미옥" # 'None', '클로닝성우이름', '성우이름(특성)' ... 중 선택
    Marketing = ["None"] # 'None', 'InstagramTemplate1', 'BlogTemplate1' ... 중 마케팅 제작 템플릿을 다중 선택
    
    MessagesReview = "on" # 'on', 'off' : on 은 모든 프롬프트 출력, off 는 모든 프롬프트 비출력
    Account = "junyoung8@nate.com" # 'yeoreum00128@naver.com', 'lucidsun0128@naver.com', 'ahyeon00128@naver.com', 'khsis3516@naver.com', 'lunahyeon00128@naver.com', 'kka6887@hanmail.net', 'aldus5909@naver.com', 'junyoung8@nate.com' ... 중 선택

    #########################################################################

    MultiProcessing(User, ProjectNameList, MainLang, Translations, Estimate, DataCollection, Script, TextBook, AudioBook, Marketing, MessagesReview, Account)