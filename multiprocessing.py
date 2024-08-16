import json
import multiprocessing
import sys
sys.path.append("/yaas")

from backend.main import YaaS

# yaasconfig 로드
def Loadyaasconfig(yaasconfigPath):
    with open(yaasconfigPath, 'r') as f:
        yaasconfig = json.load(f)
    return yaasconfig

def MultiProcessing(yaasconfigPath = '/yaas/yaasconfig.json'):
    yaasconfig = Loadyaasconfig(yaasconfigPath)
    
    return None

if __name__ == "__main__":
    # JSON 파일로부터 설정 읽기
    configurations = load_configurations('config.json')

    processes = []
    for config in configurations:
        # 각 설정을 사용하여 새로운 프로세스를 생성
        p = multiprocessing.Process(target=YaaS, args=(
            config["email"], config["name"], config["password"], config["projectNameList"], config["IndexMode"],
            config["MessagesReview"], config["BookGenre"], config["Narrator"], config["CloneVoiceName"],
            config["VoiceReverbe"], config["MainLang"], config["Intro"], config["AudiobookSplitting"],
            config["VoiceEnhance"], config["VoiceFileGen"], config["MainProcess"], config["Macro"],
            config["Account"]
        ))
        processes.append(p)
        p.start()

    # 모든 프로세스가 종료될 때까지 기다림
    for p in processes:
        p.join()

    print("All processes are completed.")