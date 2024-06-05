import os
import multiprocessing
import unicodedata
import sys
sys.path.append("/yaas")

from dotenv import load_dotenv
from b2_Solution.bm21_GeneralUpdate import AccountUpdate, SolutionProjectUpdate
from b2_Solution.bm22_DataFrameUpdate import SolutionDataFrameUpdate
from b2_Solution.bm23_DataSetUpdate import SolutionDataSetUpdate

from b4_Creation.bm25_AudiobookUpdate import CreationAudioBookUpdate

### Main1 : 솔루션 업데이트 ###
def SolutionUpdate(email, projectNameList, IndexMode, MessagesReview, BookGenre):

    ## .env 파일 로드(API_KEY 등 환경 변수 액세스)
    envPath = os.path.join(os.path.dirname(__file__), '..', 'storage', '.env')
    load_dotenv(dotenv_path = envPath)


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
            SolutionDataFrameUpdate(email, projectName, indexMode = IndexMode, messagesReview = MessagesReview, bookGenre = BookGenre)
            
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

def CreationUpdate(email, projectNameList, Narrator, CloneVoiceName, VoiceReverbe, MainLang, Intro, AudiobookSplitting, Macro, Account, VoiceEnhance, VoiceFileGen, MessagesReview):

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
            CreationAudioBookUpdate(projectName, email, Narrator, CloneVoiceName, VoiceReverbe, MainLang, Intro, audiobookSplitting = AudiobookSplitting, macro = Macro, account = Account, voiceEnhance = VoiceEnhance, voiceFileGen = VoiceFileGen, messagesReview = MessagesReview)
            
### YaaS : YaaS의 통합으로 'Solution', 'Creation' ###

def YaaS(email, name, password, projectNameList, IndexMode, MessagesReview, BookGenre, Narrator, CloneVoiceName, VoiceReverbe, MainLang, Intro, AudiobookSplitting, VoiceEnhance, VoiceFileGen, MainProcess, Macro, Account):

    if MainProcess == 'Solution':
        AccountUpdate(email, name, password)
        SolutionUpdate(email, projectNameList, IndexMode, MessagesReview, BookGenre)
        
    elif MainProcess == 'Creation':
        AccountUpdate(email, name, password)
        SolutionUpdate(email, projectNameList, IndexMode, MessagesReview, BookGenre)
        CreationUpdate(email, projectNameList, Narrator, CloneVoiceName, VoiceReverbe, MainLang, Intro, AudiobookSplitting, Macro, Account, VoiceEnhance, VoiceFileGen, MessagesReview)

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    name = "yeoreum"
    password = "0128"
    projectNameList = ['240223_나는외식창업에적합한사람인가'] # '240223_나는외식창업에적합한사람인가', '240223_나무에서만난경영지혜', '240223_노인을위한나라는있다', '240223_마케터의무기들', '240405_빌리월터스겜블러', '240412_카이스트명상수업', '240418_부카출판사', '240426_목소리의힘', '240523_고객검증'
    IndexMode = "Define" # 'Define', 'Preprocess' : Define 은 Index 전처리 필요 없음, Preprocess 는 Index 전처리 필요함
    MessagesReview = "on" # 'on', 'off' : on 은 모든 프롬프트 출력, off 는 모든 프롬프트 비출력
    BookGenre = "Auto" # 'Auto', '문학', '비문학', '아동', '시', '학술'
    MainLang = "Ko" # 'Ko', 'En'
    Narrator = "VoiceActor" # 'VoiceActor', 'VoiceClone' : VoiceActor 은 일반성우 나레이터, VoiceClone 은 저자성우 나레이터
    CloneVoiceName = "이덕주" # Narrator = "VoiceClone" 인 경우 '저자명' 작성
    VoiceEnhance = "off" # 'on', 'off' : on 은 클론보이스 노이즈 제거, off 는 클론보이스 노이즈 제거 비활성
    VoiceReverbe = "on" # 'on', 'off' : on 은 인덱스와 대화문에 리버브 적용, off 는 리버브 미적용
    Intro = "off" # Intro = ['한국출판문화산업진흥원' ...]
    AudiobookSplitting = "Auto" # 'Auto', 'Manual' : Auto 는 오디오북 자동 분할, Manual 은 오디오북 수동 분할
    VoiceFileGen = "on" # 'on', 'off' : on 은 Voice.wav 파일 생성, off 는 Voice.wav 파일 비생성
    MainProcess = "Solution" # 'Solution', 'Creation'
    Macro = "Auto" # 'Auto', 'Manual' : Auto는 API 캐릭터 변경 자동, Manual은 API 캐릭터 변경 수동
    Account = "khsis3516@naver.com" # 'yeoreum00128@naver.com', 'lucidsun0128@naver.com', 'ahyeon00128@naver.com', 'khsis3516@naver.com'
    #########################################################################

    YaaS(email, name, password, projectNameList, IndexMode, MessagesReview, BookGenre, Narrator, CloneVoiceName, VoiceReverbe, MainLang, Intro, AudiobookSplitting, VoiceEnhance, VoiceFileGen, MainProcess, Macro, Account)