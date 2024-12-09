import os
import json
import unicodedata
import re
import math
import sys
sys.path.append("/yaas")

from matplotlib import font_manager, rc
import matplotlib.pyplot as plt
from datetime import datetime
from PIL import Image, ImageChops
from reportlab.lib.pagesizes import portrait
from reportlab.pdfgen import canvas

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
def SampleSettingGen(projectName, email):
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
                        "Lenth(estimate)": f"{math.ceil(SampleScriptLenth/10000)*10000:,}자",
                        "RunningTime(s)": RunningTime,
                        "RunningTime(hms)": SecondsToHMS(RunningTime),
                        "RunningTime(estimate)": SecondsToHMS(math.ceil(RunningTime / 1800) * 1800),
                        "VoiceActorPrice(raw)": VoiceActorPrice,
                        "VoiceActorPrice(estimate)": f"{int(math.ceil(VoiceActorPrice/200000)*200000):,}원",
                        "VoiceActorPrice(vat)": f"{int(math.ceil(VoiceActorPrice/200000)*200000/10):,}원",
                        "VoiceActorPrice(estimate+vat)": f"{int(math.ceil(VoiceActorPrice/200000)*200000*1.1):,}원",
                        "VoiceClonePrice(raw)": VoiceClonePrice,
                        "VoiceClonePrice(estimate)": f"{int(math.ceil(VoiceClonePrice/250000)*250000):,}원",
                        "VoiceClonePrice(vat)": f"{int(math.ceil(VoiceClonePrice/250000)*250000/10):,}원",
                        "VoiceClonePrice(estimate+vat)": f"{int(math.ceil(VoiceClonePrice/250000)*250000*1.1):,}원",
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
                return SampleSetting, ScriptFilePath
            else:
                sys.exit(f"\n[ 샘플 세팅을 완료하세요 : {ScriptFilePath} ]\n")
    else:
        sys.exit(f"\n[ 아래 폴더에 ((({projectName + '_Script.txt'}))) 파일을 넣어주세요 ]\n({ScriptFilePath})\n")

## 오늘 날짜
def Date(Option = "Day"):
    if Option == "Day":
      now = datetime.now()
      date = now.strftime('%y%m%d')
    elif Option == "Second":
      now = datetime.now()
      date = now.strftime('%y%m%d%H%M%S')
    
    return date

### 라이프그래프의 이미지를 PDF로 묶기 ###
def PNGsToPDF(EstimatePNGPaths, EstimatePDFPath):
    # 디자인 포멧 경로
    DesignFormatPath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s121_Samples/s1211_SampleSet/Design_Format/s121_Estimate_Format_"
    
    # 첫 번째 이미지 크기에 맞는 PDF 생성
    FirstImage = Image.open(EstimatePNGPaths[0])
    FirstWidth, FirstHeight = FirstImage.size
    pdf = canvas.Canvas(EstimatePDFPath, pagesize = portrait((FirstWidth, FirstHeight)))

    for i in range(len(EstimatePNGPaths)):
        # 그래프 이미지와 디자인 포멧 불러오기
        text = Image.open(EstimatePNGPaths[i]).convert("RGBA")
        DesignFormat = Image.open(DesignFormatPath + f"{i}.png").convert("RGBA")
        # 이미지 크기 맞추기
        if text.size != DesignFormat.size:
            text = text.resize(DesignFormat.size)
        # 그래프 이미지와 디자인 포멧 합치기
        CompositeImage = Image.alpha_composite(DesignFormat, text)
        # 합쳐진 이미지 임시저장
        CompositeImage.save(EstimatePNGPaths[i], "PNG", optimize = True)
        # 이미지를 PDF에 추가
        pdf.drawImage(EstimatePNGPaths[i], 0, 0)
        pdf.showPage()
        # PDF로 저장된 PNG 파일 제거
        os.remove(EstimatePNGPaths[i])
    
    # 마지막 라이센스 이미지를 PDF에 추가
    pdf.drawImage("/yaas/storage/s1_Yeoreum/s12_UserStorage/s121_Samples/s1211_SampleSet/Design_Format/s121_Estimate_Format_2.png", 0, 0)
    pdf.showPage()
    
    # PDF 파일 저장
    pdf.save()

### EstimatePDFGen 생성 ###
def EstimateToPNG(projectName, email):
    SampleSetting, ScriptFilePath = SampleSettingGen(projectName, email)
    
    ## 견적서 데이터
    Project = SampleSetting['EstimateSetting']['ProjectName']
    Client = SampleSetting['EstimateSetting']['Client']
    Lenth = SampleSetting['EstimateSetting']['Lenth(estimate)']
    
    VoiceActorPriceVAT = SampleSetting['EstimateSetting']['VoiceActorPrice(estimate+vat)']
    VoiceActorPrice = SampleSetting['EstimateSetting']['VoiceActorPrice(estimate)']
    VoiceActorVAT = SampleSetting['EstimateSetting']['VoiceActorPrice(vat)']
    
    VoiceClonePriceVAT = SampleSetting['EstimateSetting']['VoiceClonePrice(estimate+vat)']
    VoiceClonePrice = SampleSetting['EstimateSetting']['VoiceClonePrice(estimate)']
    VoiceCloneVAT = SampleSetting['EstimateSetting']['VoiceClonePrice(vat)']
    
    ## 기본 폰트 설정, Noto Sans CJK 폰트 경로 설정
    font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font_prop = font_manager.FontProperties(fname = font_path)
    rc('font', family = font_prop.get_name())
    plt.rcParams['axes.unicode_minus'] = False  # 유니코드 마이너스 설정
    
    EstimatePNGPaths = []
    EstimateFolderPath = os.path.join(ScriptFilePath, "Estimate")
    EstimateFileName = f"{projectName}_Estimate"
    EstimatePDFPath = os.path.join(EstimateFolderPath, f'{EstimateFileName}.pdf')
    
    ## 01_Estimate 폴더 생성
    if not os.path.exists(EstimateFolderPath):
        os.makedirs(EstimateFolderPath)

    ## 02_표지 페이지 생성
    fig, ax = plt.subplots(figsize = (8.27, 11.69))  # A4 크기 (인치 단위)
    fig.patch.set_alpha(0.0) # 투명 배경
    ax.patch.set_alpha(0.0) # 투명 배경
    fig.subplots_adjust(left = 0.05, right = 0.95, top = 0.9, bottom = 0.1)  # 여백 설정
    # 제목
    ax.text(0.6, 0.925, f"일자: {Date()}\n\n도서: {Project}\n\n의뢰: {Client}",
    fontsize = 14, weight = 'bold', transform = ax.transAxes, color = 'white')
    ax.axis('off')  # 텍스트 영역의 축 숨기기
    
    # 표지 페이지 저장
    EstimatePNG0Path = os.path.join(EstimateFolderPath, f'{EstimateFileName}(0).png')
    EstimatePNGPaths.append(EstimatePNG0Path)
    plt.savefig(EstimatePNG0Path, dpi = 300, transparent = True)
    plt.close()

    ## 03_견적서 페이지 생성
    fig, ax = plt.subplots(figsize = (8.27, 11.69))  # A4 크기 (인치 단위)
    fig.patch.set_alpha(0.0) # 투명 배경
    ax.patch.set_alpha(0.0) # 투명 배경
    fig.subplots_adjust(left = 0.05, right = 0.95, top = 0.9, bottom = 0.1)  # 여백 설정
    # 제목
    ax.text(0.05, 1, f"『{Project}』 {Client}  |  오디오북 제작 견적서", 
    fontsize = 14, weight = 'bold', transform = ax.transAxes, color = 'white')
    # 성우 보이스
    ax.text(0.05, 0.8, f"선택1: 성우 보이스        {Lenth}       {VoiceActorPriceVAT} (부가세포함)\n\n                                                                       {VoiceActorPrice} ({VoiceActorVAT})", 
    fontsize = 11, weight = 'bold', transform = ax.transAxes, color = 'white')
    # 클로닝 보이스
    ax.text(0.05, 0.5, f"선택2: 클로닝 보이스    {Lenth}       {VoiceClonePriceVAT} (부가세포함)\n\n                                                                       {VoiceClonePrice} ({VoiceCloneVAT})", 
    fontsize = 11, weight = 'bold', transform = ax.transAxes, color = 'white')
    ax.axis('off')  # 텍스트 영역의 축 숨기기
    
    # 견적서 페이지 저장
    EstimatePNG1Path = os.path.join(EstimateFolderPath, f'{EstimateFileName}(1).png')
    EstimatePNGPaths.append(EstimatePNG1Path)
    plt.savefig(EstimatePNG1Path, dpi = 300, transparent = True)
    plt.close()
    
    PNGsToPDF(EstimatePNGPaths, EstimatePDFPath)
### Sample 보고서 제작 및 업데이트 ###
# 1. 견적서 및 계약서 등 모든 서류 제작
# 2. 샘플을 위한 Body 분리
# 3. 나레이터셋 선정(샘플 2-3개)
# 4. 전달 이메일 작성?

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241206_테스트'
    #########################################################################
    
    EstimateToPNG(ProjectName, email)