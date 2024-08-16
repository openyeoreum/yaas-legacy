import os
import json
import multiprocessing
import sys
sys.path.append("/yaas")

from backend.main import YaaS

## yaasconfig 로드
def Loadyaasconfig(yaasconfigPath = '/yaas/backend/yaasconfig.json'):
    with open(yaasconfigPath, 'r') as f:
        yaasconfig = json.load(f)
    return yaasconfig

## MultiProcessing
def MultiProcessing(projectNameList, MessagesReview, VoiceFileGen, MainProcess, Macro, Account, yaasconfigPath = '/yaas/backend/yaasconfig.json'):
    yaasconfig = Loadyaasconfig(yaasconfigPath = yaasconfigPath)
    
    print(f"[ Projects: {projectNameList} | MultiProcessing 시작 ]")
    
    processes = []
    for projectName in projectNameList:
        YaasConfig = yaasconfig[projectName]
        Process = multiprocessing.Process(target = YaaS,
                                          args = (YaasConfig["email"], YaasConfig["name"], YaasConfig["password"], YaasConfig["projectNameList"], YaasConfig["Translations"], YaasConfig["IndexMode"], MessagesReview, YaasConfig["BookGenre"], YaasConfig["Narrator"], YaasConfig["CloneVoiceName"], YaasConfig["VoiceReverbe"], YaasConfig["MainLang"], YaasConfig["Intro"], YaasConfig["AudiobookSplitting"], YaasConfig["VoiceEnhance"], VoiceFileGen, MainProcess, Macro, Account))
        processes.append(Process)
        Process.start()
        
    # 모든 프로세스가 종료될 때까지 기다림
    for p in processes:
        p.join()
        
    print(f"[ Projects: {projectNameList} | MultiProcessing 완료 ]")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    projectNameList = ['240801_빨간풍차가있는집'] # '240223_나는외식창업에적합한사람인가', '240223_나무에서만난경영지혜', '240223_노인을위한나라는있다', '240223_마케터의무기들', '240405_빌리월터스겜블러', '240412_카이스트명상수업', '240418_부카출판사', '240426_목소리의힘', '240523_고객검증', '240705_도산안창호', '240801_빨간풍차가있는집', '240802_암을이기는천연항암제', '240812_룰루레몬스토리', '240815_노유파'
    MessagesReview = "on" # 'on', 'off' : on 은 모든 프롬프트 출력, off 는 모든 프롬프트 비출력
    VoiceFileGen = "off" # 'on', 'off' : on 은 Voice.wav 파일 생성, off 는 Voice.wav 파일 비생성
    MainProcess = "Solution&Creation" # 'Solution', 'Creation'
    Macro = "Auto" # 'Auto', 'Manual' : Auto는 API 캐릭터 변경 자동, Manual은 API 캐릭터 변경 수동
    Account = "khsis3516@naver.com" # 'yeoreum00128@naver.com', 'lucidsun0128@naver.com', 'ahyeon00128@naver.com', 'khsis3516@naver.com', 'lunahyeon00128@naver.com'
    #########################################################################
    
    MultiProcessing(projectNameList, MessagesReview, VoiceFileGen, MainProcess, Macro, Account, yaasconfigPath = '/yaas/backend/yaasconfig.json')