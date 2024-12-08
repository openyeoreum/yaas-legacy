import os
import json
import unicodedata
import re
import math
import sys
sys.path.append("/yaas")

from backend.b4_Creation.b43_Creator.b431_BestSellerWebScraper import BestsellerWebScraper

##########################
##########################
##### ContentsUpdate #####
##########################
##########################
### 시간, 분, 초로 변환 ###
def SecondsToHMS(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

### SciptFile의 SampleSetting ###
def SampleSetting(projectName, email):
    ScriptFilePath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s121_Samples/s1211_SampleSet/{projectName}_Sample"
    try:
        os.makedirs(ScriptFilePath, exist_ok = True)
    except Exception as e:
        print(f"Error in makedirs: {e}")
    
    ScriptFile = f"{projectName}_Script.txt"
    ProjectScriptFilePath = os.path.join(ScriptFilePath, ScriptFile)
    SampleFile = f"{projectName}_Sample_Setting.json"
    ProjectSampleFilePath = os.path.join(ScriptFilePath, SampleFile)
    RunningTimeDataPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s121_Samples/s1212_RunningTimeData"
    
    ## 01_ScriptText 불러오기 ##
    if os.path.exists(ProjectScriptFilePath):
        with open(ProjectScriptFilePath, 'r', encoding = 'utf-8') as TextFile:
            SampleScript = TextFile.read()
            SampleScript = unicodedata.normalize('NFC', SampleScript)
        SampleScriptLenth = len(SampleScript) * 0.99 # 텍스트 퍼센트율 조정
        
        ## 02_RunningTimeData 불러오기 ##
        RunningTimeRatioList = []
        for RunningTimeDataFile in os.listdir(RunningTimeDataPath):
            ## RunningTime.json 파일찾기
            if re.search(r'.*RunningTime\.json$', RunningTimeDataFile):
                RunningTimeDataFilePath = os.path.join(RunningTimeDataPath, RunningTimeDataFile)
                with open(RunningTimeDataFilePath, 'r', encoding='utf-8') as JsonFile:
                    RunningTimeData = json.load(JsonFile)
                    
                ## 비율 계산 (RunningTime / BodyScriptLength)
                if RunningTimeData["BodyScriptLenth"] > 0:  # 0으로 나누기 방지
                    RunningTimeRatio = RunningTimeData["RunningTime"] / RunningTimeData["BodyScriptLenth"]
                    RunningTimeRatioList.append(RunningTimeRatio)
        AverageRunningTimeRatio = sum(RunningTimeRatioList) / len(RunningTimeRatioList)
        
        ## 03_ScriptText RunningTime 계산 ##
        RunningTime = SampleScriptLenth * AverageRunningTimeRatio
        VoiceActorPrice = 200000 * SampleScriptLenth/10000
        VoiceClonePrice = 250000 * SampleScriptLenth/10000
        
        ## 04_Sample_Setting Json 생성 ##
        if not os.path.exists(ProjectSampleFilePath):
            SampleSetting = {
                    "ProjectName": f"{projectName}",
                    "EstimateSetting": {
                        "ProjectName": "",
                        "Client": "",
                        "Lenth(raw)": SampleScriptLenth,
                        "Lenth(estimate)": math.ceil(SampleScriptLenth/10000)*10000,
                        "RunningTime(s)": RunningTime,
                        "RunningTime(hms)": SecondsToHMS(RunningTime),
                        "RunningTime(estimate)": SecondsToHMS(math.ceil(RunningTime / 1800) * 1800),
                        "VoiceActorPrice(raw)": VoiceActorPrice,
                        "VoiceActorPrice(estimate)": f"{math.ceil(VoiceActorPrice/200000)*200000:,}원",
                        "VoiceClonePrice(raw)": VoiceClonePrice,
                        "VoiceClonePrice(estimate)": f"{math.ceil(VoiceClonePrice/250000)*250000:,}원",
                    }
                }
            ## SampleSetting Json 파일저장
            with open(ProjectSampleFilePath, 'w', encoding = 'utf-8') as JsonFile:
                json.dump(SampleSetting, JsonFile, indent = 4, ensure_ascii = False)
            sys.exit(f"\n[ 샘플 세팅을 완료하세요 : {ScriptFilePath} ]\n")
        else:
            with open(ProjectSampleFilePath, 'r', encoding = 'utf-8') as JsonFile:
                SampleSetting = json.load(JsonFile)
            if SampleSetting['EstimateSetting']['ProjectName'] != "" and SampleSetting['EstimateSetting']['Client'] != "":
                return SampleSetting
            else:
                sys.exit(f"\n[ 샘플 세팅을 완료하세요 : {ScriptFilePath} ]\n")
    else:
        sys.exit(f"\n[ 아래 폴더에 ((({projectName + '_Script.txt'}))) 파일을 넣어주세요 ]\n({ScriptFilePath})\n")

### SciptFile의 RunningTime 계산 ###
def EstimateGen(projectName, email):
    SampleSetting = SampleSetting(projectName, email)
        
### Sample 보고서 제작 및 업데이트 ###
# 1. 견적서 및 계약서 등 모든 서류 제작
# 2. 샘플을 위한 Body 분리
# 3. 나레이터셋 선정(샘플 2-3개)
# 4. 

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241206_테스트'
    #########################################################################
    
    SampleSetting(ProjectName, email)