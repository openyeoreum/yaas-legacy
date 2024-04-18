import os
import multiprocessing
import unicodedata
import sys
sys.path.append("/yaas")

from b2_Solution.bm21_GeneralUpdate import AccountUpdate, SolutionProjectUpdate
from b2_Solution.bm22_DataFrameUpdate import SolutionDataFrameUpdate
from b2_Solution.bm23_DataSetUpdate import SolutionDataSetUpdate

from b4_Creation.bm25_AudiobookUpdate import CreationAudioBookUpdate

### Sub1 : 한글 유니코드 정규화 ###
def NormalizeUnicode(Code = "NFC", StoragePath = "/yaas/storage"):
    for DirPath, DirNames, FileNames in os.walk(StoragePath, topdown = False):
        # 파일 이름 정규화 및 변경
        for filename in FileNames:
            NormalizedFilename = unicodedata.normalize(Code, filename)
            if filename != NormalizedFilename:
                OriginalFilePath = os.path.join(DirPath, filename)
                NewFilePath = os.path.join(DirPath, NormalizedFilename)
                os.rename(OriginalFilePath, NewFilePath)
                print(f"[ 파일 이름 {Code} 변경: '{filename}' -> {Code}: '({NormalizedFilename})' ]")

        # 디렉토리 이름 정규화 및 변경
        for dirname in DirNames:
            NormalizedDirname = unicodedata.normalize(Code, dirname)
            if dirname != NormalizedDirname:
                OriginalDirPath = os.path.join(DirPath, dirname)
                NewDirPath = os.path.join(DirPath, NormalizedDirname)
                os.rename(OriginalDirPath, NewDirPath)
                print(f"[ 디렉토리 이름 {Code} 변경: '{dirname}' -> {Code}: '({NormalizedDirname})' ]")

### Main1 : 솔루션 업데이트 ###
def SolutionUpdate(email, projectNameList, MessagesReview, BookGenre):

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
            SolutionDataFrameUpdate(email, projectName, messagesReview = MessagesReview, bookGenre = BookGenre)
            
            # ### Step4 : 솔루션에 프로젝트 데이터셋 학습진행 및 업데이트 ###
            # SolutionDataSetUpdate(email, projectName)
    
    else:
        ### Step2 : 솔루션에 프로젝트 파일 업데이트 ###
        SolutionProjectUpdate(email, projectName)
        
        ### Step3 : 솔루션에 프로젝트 데이터 프레임 진행 및 업데이트 ###
        SolutionDataFrameUpdate(email, projectName, messagesReview = MessagesReview)
        
        # ### Step4 : 솔루션에 프로젝트 데이터셋 학습진행 및 업데이트 ###
        # SolutionDataSetUpdate(email, projectName)
        
### Main2 : 콘텐츠 제작 ###

def CreationUpdate(email, projectNameList, VoiceDataSet, MainLang, Intro, Macro, Account, Split, MessagesReview):

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
            CreationAudioBookUpdate(projectName, email, VoiceDataSet, MainLang, Intro, macro = Macro, account = Account, split = Split, messagesReview = MessagesReview)
            
### YaaS : YaaS의 통합으로 'Solution', 'Creation' ###

def YaaS(email, name, password, projectNameList, MessagesReview, BookGenre, VoiceDataSet, MainLang, Intro, MainProcess, Macro, Account, Split):

    if MainProcess == 'Solution':
        AccountUpdate(email, name, password)
        SolutionUpdate(email, projectNameList, MessagesReview, BookGenre)
        
    elif MainProcess == 'Creation':
        AccountUpdate(email, name, password)
        SolutionUpdate(email, projectNameList, MessagesReview, BookGenre)
        CreationUpdate(email, projectNameList, VoiceDataSet, MainLang, Intro, Macro, Account, Split, MessagesReview)

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    name = "yeoreum"
    password = "0128"
    projectNameList = ['마케터의무기들'] # '빌리윌터스겜블러', '나는외식창업에적합한사람인가', '나무에서만난경영지혜', '마케터의무기들', '노인을위한나라는있다', '인공지능오디오북의새로운지평', '노인을위한나라는있다, '데미안', '우리는행복을진단한다', '웹3.0메타버스', '살아서천국극락낙원에가는방법', '빨간머리앤', '나는선비로소이다', '나는노비로소이다', '카이스트명상수업'
    MessagesReview = "on"
    BookGenre = "Auto" # 'Auto', '문학', '비문학', '아동', '시', '학술'
    VoiceDataSet = "TypeCastVoiceDataSet"
    MainLang = "Ko" # 'Ko', 'En'
    Intro = "off" # Intro = ['한국출판문화산업진흥원' ...]
    MainProcess = "Creation" # 'Solution', 'Creation'
    Macro = "Auto" # 'Auto', 'Manual' : Auto는 API 캐릭터 변겅 자동, Manual은 API 캐릭터 변경 수동
    Account = "yeoreum00128@naver.com" # 'lucidsun0128@naver.com', 'ahyeon00128@naver.com'
    Split = "Auto" # 'Auto', 'Manual' : Auto는 긴 음성 생성 후 분할(비용이 작음), Manual은 짧은 음성 분할 생성(비용이 큼)
    #########################################################################

    # NormalizeUnicode('NFD')
    YaaS(email, name, password, projectNameList, MessagesReview, BookGenre, VoiceDataSet, MainLang, Intro, MainProcess, Macro, Account, Split)