import os
import json
import multiprocessing
import unicodedata
import sys
sys.path.append("/yaas")

from b2_Solution.bm21_GeneralUpdate import AccountUpdate, SolutionProjectUpdate
from backend.b2_Solution.bm22_EstimateUpdate import SolutionEstimateUpdate
from backend.b2_Solution.bm23_DataCollectionUpdate import SolutionDataCollectionUpsert, SolutionDataCollectionSearch
from backend.b2_Solution.bm24_ScriptUpdate import SolutionScriptUpdate
from backend.b2_Solution.bm25_TranslationUpdate import SolutionTranslationUpdate
from backend.b2_Solution.bm26_DataFrameUpdate import SolutionDataFrameUpdate
from backend.b4_Creation.bm29_AudioBookUpdate import CreationAudioBookUpdate


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
def YaasConfigUpdate(StartProjectName, MainLang, Estimate, DataCollection, Search, Script, Translation, TextBook, AudioBook, Marketing):

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

        ### Step3-2 : EstimateConfig 설정 ###
        if Estimate == [] or Estimate == [""] or Estimate == ["None"]:
            EstimateConfig = {}
        else:
            EstimateConfig = {"Estimate": Estimate}

        ### Step3-3 : DataCollectionConfig 설정 ###
        if DataCollection == [] or DataCollection == [""] or DataCollection == ["None"]:
            DataCollectionConfig = {}
        else:
            DataCollectionConfig = {
                "DataCollection": DataCollection
                }

        ### Step3-4 : SearchConfig 설정 ###
        if Search['Search'] == "" or Search['Search'] == " " or Search['Search'] == "None":
            SearchConfig = {}
        else:
            SearchConfig = {
                "Search": Search['Search'],
                "Intention": Search['Intention'],
                "Extension": ["Expertise", "Ultimate"],
                "Collection": Search['Collection'],
                "Range": 10
                }

        ### Step3-5 : ScriptConfig 설정 ###
        if Script == "" or Script == "None":
            ScriptConfig = {}
        else:
            ScriptConfig = {"Script": Script}
            
        ### Step3-6 : TranslationConfig 설정 ###
        if Translation == "" or Translation == "None":
            TranslationConfig = {}
        else:
            TranslationConfig = {
                "MainLang": MainLang,
                "Translation": Translation,
                "BookGenre": "NonFiction", # "NonFiction", "Fiction"
                "Tone": "Normal", # "Informal", "Normal", "Formal"
                "BodyLength": 3000, # 2000, 3000, 4000
                "Editing": "on", # "on", "off"
                "Refinement": "off", # "on", "off"
                "KinfolkStyleRefinement": "on", # "on", "off
                "EditMode": "Auto", # "Auto", "Manual"
                }
            
        ### Step3-7 : TextBookConfig 설정 ###
        if TextBook == "" or TextBook == "None":
            TextBookConfig = {}
        else:
            TextBookConfig = {"TextBook": TextBook}
            
        ### Step3-8 : AudioBookConfig 설정 ###
        if AudioBook == "" or AudioBook == "None":
            AudioBookConfig = {}
        elif AudioBook == "Auto":
            AudioBookConfig = {
                "IndexMode": "Define",
                "BookGenre": "Auto",
                "Narrator": "VoiceActor", # "VoiceActor", "VoiceClone"
                "CloneVoiceName": "",
                "ReadingStyle": "NarratorOnly", # "NarratorOnly", "AllCharacters"
                "VoiceEnhance": "off",
                "VoiceReverbe": "on",
                "Intro": "off", # "on", "off"
                "AudiobookSplitting": "Auto", # "Auto", "Manual"
                "MusicDB": "Template", # "Template", "Database"
                "EndMusicVolume": -10,
                "VoiceFileGen": "off",
                "Bitrate": "320k",
                "Macro": "Auto",
                "Bracket": "Auto",
                "VolumeEqual": "Mastering"
                }
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
            
        ### Step3-9 MarketingConfig 설정 ###
        if Marketing == [] or Marketing == [""] or Marketing == ["None"]:
            MarketingConfig = {}
        else:
            MarketingConfig = {"Marketing": Marketing}
        
        ## YaaSConfig 업데이트
        YaasConfig = {"email": email, "name": name, "password": password, "ProjectName": ProjectName, "MainLang": MainLang, "EstimateConfig": EstimateConfig, "DataCollectionConfig": DataCollectionConfig, "SearchConfig": SearchConfig, "ScriptConfig": ScriptConfig, "TranslationConfig": TranslationConfig, "TextBookConfig": TextBookConfig, "AudioBookConfig": AudioBookConfig, "MarketingConfig": MarketingConfig, "ConfigCompletion": "세팅 완료 후 Completion"}

        ## 업데이트 된 YaaSConfig 저장
        with open(ConfigPath, 'w', encoding = 'utf-8') as ConfigJson:
            json.dump(YaasConfig, ConfigJson, ensure_ascii = False, indent = 4)
        sys.exit(f'\n[ (([{StartProjectName}_config.json])) 세팅을 완료하세요 ]\n({ConfigPath})\n')
    else:
        with open(ConfigPath, 'r', encoding='utf-8') as ConfigJson:
            YaasConfig = json.load(ConfigJson)
        if YaasConfig["ConfigCompletion"] != "Completion":
            sys.exit(f'\n[ (([{StartProjectName}_config.json])) 세팅을 완료하세요 ]\n({ConfigPath})\n')


########################################################################################################################
########################################################################################################################
### Step4-11 : 'Estimate', 'DataCollection', 'Search', 'Script', 'Translation', 'TextBook', 'AudioBook', 'Marketing' ###
########################################################################################################################
########################################################################################################################

### Step4 : EstimateUpdate 업데이트 ###
def EstimateUpdate(email, ProjectName, Estimate):
    
    ### Step4-1 : Estimate 생성 ###
    SolutionEstimateUpdate(ProjectName, email, Estimate)
    
### Step5 : DataCollectionUpsert 업데이트 ###
def DataCollectionUpsert(email, ProjectName, DataCollection, MessagesReview):
    
    ### Step5-1 : DataCollection 업서트 ###
    SolutionDataCollectionUpsert(ProjectName, email, DataCollection, MessagesReview)

### Step6 : Search 업데이트 ###
def DataCollectionSearch(email, ProjectName, Search, Intention, Extension, Collection, Range, MessagesReview):
    
    ### Step6-1 : DataCollection 검색 ###
    SolutionDataCollectionSearch(ProjectName, email, Search, Intention, Extension, Collection, Range, MessagesReview)
    
### Step7 : ScriptUpdate 업데이트 ###
def ScriptUpdate(email, ProjectName, Script, Intention, MessagesReview):
    
    ### Step7-1 : Script 생성 ###
    SolutionScriptUpdate(ProjectName, email, Script, Intention, MessagesReview)

### Step8 : Translation 업데이트 ###
def TranslationUpdate(email, ProjectName, MainLang, Translation, BookGenre, Tone, BodyLength, Editing, Refinement, KinfolkStyleRefinement, EditMode, MessagesReview):
    
    ### Step8-1 : Translation 번역 ###
    SolutionTranslationUpdate(ProjectName, email, MainLang, Translation, BookGenre, Tone, BodyLength, Editing, Refinement, KinfolkStyleRefinement, EditMode, MessagesReview)

### Step9 : TextBook 업데이트 ###

### Step10 : AudioBook 업데이트 ###
def AudioBookUpdate(email, ProjectName, IndexMode, BookGenre, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, AudiobookSplitting, MusicDB, EndMusicVolume, Macro, Bracket, VolumeEqual, Account, VoiceEnhance, VoiceFileGen, Bitrate, MessagesReview):
    
    ### Step10-1 : AudioBook 데이터 프레임 ###
    SolutionDataFrameUpdate(email, ProjectName, MainLang, indexMode = IndexMode, messagesReview = MessagesReview)
    
    ### Step10-2 : AudioBook 제작 ###
    CreationAudioBookUpdate(ProjectName, email, Narrator, CloneVoiceName, ReadingStyle, VoiceReverbe, MainLang, Intro, audiobookSplitting = AudiobookSplitting, musicDB = MusicDB, endMusicVolume = EndMusicVolume, macro = Macro, bracket = Bracket, volumeEqual = VolumeEqual, account = Account, voiceEnhance = VoiceEnhance, voiceFileGen = VoiceFileGen, bitrate = Bitrate, messagesReview = MessagesReview)
    
### Step11 : Marketing 업데이트 ###

###############################################################################################################
###############################################################################################################
### Main2 : YaaS에서 통합으로 'DataCollection', 'Script', 'Estimate', 'TextBook', 'AudioBook', 'Marketing' 제작 ###
###############################################################################################################
###############################################################################################################


### Main2 : YaaS 실행 ###
def YaaS(email, ProjectName, MainLang, EstimateConfig, DataCollectionConfig, SearchConfig, ScriptConfig, TranslationConfig, TextBookConfig, AudioBookConfig, MarketingConfig, MessagesReview, Account):

    ### Step4 : Estimate 업데이트 ###
    if EstimateConfig != {}:
        EstimateUpdate(email, ProjectName, EstimateConfig['Estimate'])

    ### Step5 : DataCollection 업데이트 ###
    if DataCollectionConfig != {}:
        DataCollectionUpsert(email, ProjectName, DataCollectionConfig['DataCollection'], MessagesReview)
    
    ### Step6 : Search 업데이트 ###
    if SearchConfig != {}:
        DataCollectionSearch(email, ProjectName, SearchConfig['Search'], SearchConfig['Intention'], SearchConfig['Extension'], SearchConfig['Collection'], SearchConfig['Range'], MessagesReview)
    
    ### Step7 : Script 업데이트 ###
    if ScriptConfig != {}:
        ScriptUpdate(email, ProjectName, ScriptConfig['Script'], ScriptConfig['Intention'], MessagesReview)
    
    ### Step8 : Translation 업데이트 ###
    if TranslationConfig != {}:
        TranslationUpdate(email, ProjectName, TranslationConfig['MainLang'], TranslationConfig['Translation'], TranslationConfig['BookGenre'], TranslationConfig['Tone'], TranslationConfig['BodyLength'], TranslationConfig['Editing'], TranslationConfig['Refinement'], TranslationConfig['KinfolkStyleRefinement'], TranslationConfig['EditMode'], MessagesReview)
        
    ### Step9 : TextBook 업데이트 ###
    if TextBookConfig != {}:
        pass
    
    ### Step10 : AudioBook 업데이트 ###
    if AudioBookConfig != {}:
        AudioBookUpdate(email, ProjectName, AudioBookConfig['IndexMode'], AudioBookConfig['BookGenre'], AudioBookConfig['Narrator'], AudioBookConfig['CloneVoiceName'], AudioBookConfig['ReadingStyle'], AudioBookConfig['VoiceReverbe'], MainLang, AudioBookConfig['Intro'], AudioBookConfig['AudiobookSplitting'], AudioBookConfig['MusicDB'], AudioBookConfig['EndMusicVolume'], AudioBookConfig['Macro'], AudioBookConfig['Bracket'], AudioBookConfig['VolumeEqual'], Account, AudioBookConfig['VoiceEnhance'], AudioBookConfig['VoiceFileGen'], AudioBookConfig['Bitrate'], MessagesReview)
    
    ### Step11 : Marketing 업데이트 ###
    if MarketingConfig != {}:
        pass


#################################################################################################################################
#################################################################################################################################
### Main1 : YaaS Multiprocessing에서 병렬로 'Estimate', 'DataCollection', 'Script', 'TextBook', 'AudioBook', 'Marketing' 동시 제작 ###
#################################################################################################################################
#################################################################################################################################


### Main1-1 : YaaS Multiprocessing 모두 종료 ###
def YaaSMultiprocessingExit(projectNameList, MultiProcess):

    ## MultiProcessing 종료
    print(f"\n\n[ Projects: {projectNameList} | 모든 병렬 프로세스(YaaS Multiprocessing) 종료 ]")
    for process in MultiProcess:
        if process.is_alive():
            process.terminate()

### Main1-2 : YaaS Multiprocessing 실행 ###
def YaaSMultiProcessing(User, ProjectNameList, MainLang, Estimate, DataCollection, Search, Script, Translation, TextBook, AudioBook, Marketing, MessagesReview, Account):

    ## ProjectNameList NFC 정규화
    StartProjectName = unicodedata.normalize("NFC", ProjectNameList["StartProjectName"])
    NFCProjectNameList = []
    for ProjectName in ProjectNameList["ContinueProjectNameList"]:
        NFCProjectNameList.append(unicodedata.normalize("NFC", ProjectName))
    

    ## ProjectNameList 유효성 검사
    projectNameList = []
    for _ProjectName in (NFCProjectNameList + [StartProjectName]):
        if _ProjectName != "" and _ProjectName != "None":
            if len(_ProjectName.split('_')[0]) == 6:
                projectNameList.append(_ProjectName)
            else:
                sys.exit(f'[ 잘못된 프로젝트 이름: (({_ProjectName})) -> ((YYMMDD_프로젝트명)) 형식으로 프로젝트 이름을 변경해주세요 ]')
    
    ## MultiProcessing 실행
    print(f"[ Projects: {projectNameList} | 병렬 프로세스(MultiProcessing) 시작 ]")
    
    if projectNameList != []:
        MultiProcess = []
        for projectName in projectNameList:
            ### Step1 : 솔루션에 계정정보 업데이트 ###
            AccountUpdate(User['email'], User['name'], User['password'])
            ### Step2 : 솔루션에 프로젝트 파일 업데이트 ###
            SolutionProjectUpdate(User['email'], projectName)
            ### Step3 : 프로젝트 Config 설정 ###
            if projectName == StartProjectName:
                YaasConfigUpdate(StartProjectName, MainLang, Estimate, DataCollection, Search, Script, Translation, TextBook, AudioBook, Marketing)
            ## Config 불러오기
            YaasConfig, ConfigPath = LoadYaaSConfig(projectName)
            
            try:
                Process = multiprocessing.Process(target = YaaS, args = (YaasConfig["email"], YaasConfig["ProjectName"], YaasConfig["MainLang"], YaasConfig["EstimateConfig"], YaasConfig["DataCollectionConfig"], YaasConfig["SearchConfig"], YaasConfig["ScriptConfig"], YaasConfig["TranslationConfig"], YaasConfig["TextBookConfig"], YaasConfig["AudioBookConfig"], YaasConfig["MarketingConfig"], MessagesReview, Account))
            except KeyError:
                YaaSMultiprocessingExit(projectNameList, MultiProcess)
                sys.exit(f'\n\n[ (({projectName}))는 처음 시작하는 (StartProject) 입니다 ]\n[ >>> ((ProjectNameList = {{"StartProjectName": "{projectName}", "ContinueProjectNameList": [...]}})) <<< 와 같이 StartProjectName 에서 시작하세요 ]\n\n')
                
            MultiProcess.append(Process)
            Process.start()
            
        ## 모든 프로세스가 종료될 때까지 기다림
        for process in MultiProcess:
            process.join()
        
    print(f"[ Projects: {projectNameList} | 병렬 프로세스(YaaS MultiProcessing) 완료 ]")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    ## ProjectNameList ##
    # '250101_스튜디오여름'
    # '240223_나는외식창업에적합한사람인가', '240223_나무에서만난경영지혜', '240223_노인을위한나라는있다', '240223_마케터의무기들', '240405_빌리월터스겜블러', '240412_카이스트명상수업', '240705_도산안창호', '240801_빨간풍차가있는집', '240802_암을이기는천연항암제', '240919_암을이기는천연항암제요약', '240812_룰루레몬스토리', '240815_노유파', '240908_나무스토리텔링', '240910_AI미래시나리오2030', '240925_불멸의지혜', '241005_그해여름필립로커웨이에서일어난소설같은일', '241009_책갈피와책수레', '241010_틈틈이낭만', '241024_오성삼유튜브', '241024_서울장애인가족지원센터당선작13선', '241029_누가정부창업지원을받는가', '241116_베이버터와다섯개의빛', '241118_세종교육청우리반오디오북새움중1학년8반', '241118_세종교육청우리반오디오북아름초5학년5반', '241118_세종교육청우리반오디오북아름초1학년1반', '241127_엄마의첫공부', '241128_끌리는이들에겐이유가있다', '241204_개정교육과정초등교과별이해연수', '241210_공부하듯주식해서보화찾기요약', '241210_끌리는이들에겐이유가있다요약', '241210_나는외식창업에적합한사람인가요약', '241226_법이사라진내멋대로마을을지켜줘', '250111_프로스트와베타', '250201_멘진', '250202_정년그깊은독백', '250225_격몽', '250206_업데이트', '250213_요한복음삼장', '250221_킹제임스성경의역사', '250221_성경샘플', '250221_지식정보인프라96호', '250226_생각하는대로그렇게된다', '250304_데미안', '250309_방법서설', '250312_모방의법칙', '250320_언캐니한것들의목소리', '250322_에밀', '250323_돈버는법'

    User = {"email": "yeoreum00128@gmail.com", "name": "yeoreum", "password": "0128"}
    ProjectNameList = {"StartProjectName": "", "ContinueProjectNameList": ["250312_모방의법칙"]}
    
    MainLang = "Ko" # 'Ko', 'En', 'Ja', 'Zh', 'Es' ... 중 메인이 되는 언어를 선택
    Estimate = ["AudioBook"] # [], 'TextBook', 'AudioBook', 'VideoBook' ... 중 필요한 견적을 다중 선택
    DataCollection = [] # [], 'Book', 'Meditation', 'Architect' ... 중 데이터 수집이 필요한 도메인을 다중 선택
    Search = {"Search": "", "Intention": "Similarity", "Collection": "Book"} # Search: "", Search: SearchTerm, Match: PublisherData_(Id) // # Intention: Demand, Supply, Similarity ... // Extension: Expertise, Ultimate, Detail, Rethink ... // Collection: Entire, Target, Trend, Publisher, Book ... // Range: 10-100
    Script = "" # ScriptUpload: '' // BookScriptGen: 'BookScript' // InstantScriptGen: 'SejongCityOfficeOfEducation_Poem', 'ChangesAfterMeditation_Script', 'Sample_Script', 'ONDOBook', 'ONDOMeditation', 'ONDOArchitect', 'LifeGraphAnalysis', 'InstagramTemplate1', 'BlogTemplate1' ... 중 스크립트 생성 템플릿을 선택
    Translation = "" # '', 'Auto', 'En', 'Ja', 'Zh', 'Es' ... 중 원문언어를 선택
    TextBook = "" # '', 'ONDOBook', 'ONDOMeditation', 'ONDOArchitect', 'LifeGraphAnalysis' ... 중 텍스트북 제작 템플릿을 다중 선택
    AudioBook = "" # '', 'Auto', '클로닝성우이름', '성우이름(특성)' ... 중 선택
    Marketing = [] # [] 'InstagramTemplate1', 'BlogTemplate1' ... 중 마케팅 제작 템플릿을 다중 선택
    
    MessagesReview = "on" # 'on', 'off' : on 은 모든 프롬프트 출력, off 는 모든 프롬프트 비출력
    Account = "kka6887@naver.com" # 'yeoreum00128@naver.com', 'lucidsun0128@naver.com', 'ahyeon00128@naver.com', 'khsis3516@naver.com', 'lunahyeon00128@naver.com', 'kka6887@hanmail.net', 'aldus5909@naver.com', 'junyoung8@nate.com', 'kka6887@naver.com' ... 중 선택

    #########################################################################

    YaaSMultiProcessing(User, ProjectNameList, MainLang, Estimate, DataCollection, Search, Script, Translation, TextBook, AudioBook, Marketing, MessagesReview, Account)