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
from PIL import Image
from reportlab.lib.pagesizes import portrait
from reportlab.pdfgen import canvas

##########################
##########################
##### EstimateUpdate #####
##########################
##########################

### 시간, 분, 초로 변환 ###
def SecondsToHMS(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

### SciptFile의 EstimateSetting ###
def EstimateSettingGen(projectName, Estimate, Estimates):
    ScriptFilePath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script_file"
    ScriptFile = f"{projectName}_Script.txt"
    ProjectScriptFilePath = os.path.join(ScriptFilePath, ScriptFile)
    EstimateFilePath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_estimate_file"
    EstimateFile = f"[{projectName}_{Estimate}Estimate_Setting].json"
    ProjectEstimateFilePath = os.path.join(EstimateFilePath, EstimateFile)
    RunningTimeDataPath = f"/yaas/storage/s1_Yeoreum/s14_EstimateStorage/s141_RunningTimeData"
    
    if not os.path.exists(EstimateFilePath):
        os.makedirs(EstimateFilePath)
    
    ## 01_ScriptText 불러오기 ##
    if os.path.exists(ProjectScriptFilePath):
        with open(ProjectScriptFilePath, 'r', encoding = 'utf-8') as TextFile:
            EstimateScript = TextFile.read()
            EstimateScript = unicodedata.normalize('NFC', EstimateScript)
        EstimateScriptLenth = len(EstimateScript) * 0.99 # 텍스트 퍼센트율 조정
        
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
        RunningTime = EstimateScriptLenth * AverageRunningTimeRatio
        
        ## 04_Estimate_Setting Json 생성 ##
        if Estimate == "TextBook":
            StandardPrice = 1000000 * EstimateScriptLenth/10000
            PremiumPrice = 1250000 * EstimateScriptLenth/10000
        if Estimate == "AudioBook":
            StandardPrice = 200000 * EstimateScriptLenth/10000
            PremiumPrice = 250000 * EstimateScriptLenth/10000
        if Estimate == "VideoBook":
            StandardPrice = 400000 * EstimateScriptLenth/10000
            PremiumPrice = 500000 * EstimateScriptLenth/10000
        if not os.path.exists(ProjectEstimateFilePath):
            projectname = ""
            client = ""
            
            ## 사전 작업된 EstimateSetting에서 프로젝트 이름, 클라이언트 이름 불러오기
            for estimate in Estimates:
                estimate_file = f"[{projectName}_{estimate}Estimate_Setting].json"
                Project_estimate_file_path = os.path.join(EstimateFilePath, estimate_file)
                if os.path.exists(Project_estimate_file_path):
                    with open(Project_estimate_file_path, 'r', encoding = 'utf-8') as JsonFile:
                        EstimateSetting = json.load(JsonFile)
                        projectname = EstimateSetting['EstimateSetting']['ProjectName']
                        client = EstimateSetting['EstimateSetting']['Client']
                        break
                    
            EstimateSetting = {
                    "ProjectName": f"{projectName}",
                    "EstimateSetting": {
                        "ProjectName": projectname,
                        "Client": client,
                        "Lenth(raw)": EstimateScriptLenth,
                        "Lenth(estimate)": f"{math.ceil(EstimateScriptLenth/10000)*10000:,}자",
                        "RunningTime(s)": RunningTime,
                        "RunningTime(hms)": SecondsToHMS(RunningTime),
                        "RunningTime(estimate)": SecondsToHMS(math.ceil(RunningTime / 1800) * 1800),
                        "StandardPrice(raw)": StandardPrice,
                        "StandardPrice(estimate)": f"{int(math.ceil(StandardPrice/200000)*200000):,}원",
                        "StandardPrice(vat)": f"{int(math.ceil(StandardPrice/200000)*200000/10):,}원",
                        "StandardPrice(estimate+vat)": f"{int(math.ceil(StandardPrice/200000)*200000*1.1):,}원",
                        "PremiumPrice(raw)": PremiumPrice,
                        "PremiumPrice(estimate)": f"{int(math.ceil(PremiumPrice/250000)*250000):,}원",
                        "PremiumPrice(vat)": f"{int(math.ceil(PremiumPrice/250000)*250000/10):,}원",
                        "PremiumPrice(estimate+vat)": f"{int(math.ceil(PremiumPrice/250000)*250000*1.1):,}원",
                    }
                }
            
            ## EstimateSetting Json 파일저장
            with open(ProjectEstimateFilePath, 'w', encoding = 'utf-8') as JsonFile:
                json.dump(EstimateSetting, JsonFile, indent = 4, ensure_ascii = False)
                
            ## 사전 작업된 EstimateSetting에서 프로젝트 이름, 클라이언트 이름이 존재할 경우 return 아닐 경우 sys.exit
            if projectname != "" and client != "":
                return EstimateSetting, EstimateFilePath
            else:
                sys.exit(f"\n[ {Estimate} 세팅 : (([{projectName}_{Estimate}Estimate_Setting].json)) 세팅을 완료하세요 ]\n({ProjectEstimateFilePath})\n")
        else:
            with open(ProjectEstimateFilePath, 'r', encoding = 'utf-8') as JsonFile:
                EstimateSetting = json.load(JsonFile)
            if EstimateSetting['EstimateSetting']['ProjectName'] != "" and EstimateSetting['EstimateSetting']['Client'] != "":
                return EstimateSetting, EstimateFilePath
            else:
                sys.exit(f"\n[ {Estimate} 세팅 : (([{projectName}_{Estimate}Estimate_Setting].json)) 세팅을 완료하세요 ]\n({ProjectEstimateFilePath})\n")
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

## 긴 문자열을 단어 단위로 나눔
def SplitProjectName(ProjectName, MaxLength = 16):
    # 입력된 문자열의 길이가 MaxLength 이하면 그대로 반환
    if len(ProjectName) <= MaxLength:
        return ProjectName
    
    # 입력된 문자열의 길이가 MaxLength 초과하면 줄 분리
    words = ProjectName.split()
    SplitedProjcetName = []
    CurrentLine = []
    CurrentLength = 0
    
    for word in words:
        word_length = len(word) + (1 if CurrentLine else 0)
        if CurrentLength + word_length <= MaxLength:
            CurrentLine.append(word)
            CurrentLength += word_length
        else:
            if CurrentLine:
                SplitedProjcetName.append(' '.join(CurrentLine))
            CurrentLine = [word]
            CurrentLength = len(word)
    if CurrentLine:
        SplitedProjcetName.append(' '.join(CurrentLine))
    
    return '\n'.join(SplitedProjcetName)

## 라이프그래프의 이미지를 PDF로 묶기
def PNGsToPDF(EstimatePNGPaths, EstimatePDFPath, Estimate):
    # 디자인 포멧 경로
    if Estimate == "TextBook":
        DesignFormatPath = "/yaas/storage/s1_Yeoreum/s14_EstimateStorage/s142_TextBookEstemateTemplate/TextBookEstimateTemplate_"
    if Estimate == "AudioBook":
        DesignFormatPath = "/yaas/storage/s1_Yeoreum/s14_EstimateStorage/s143_AudioBookEstemateTemplate/AudioBookEstimateTemplate_"
    if Estimate == "VideoBook":
        DesignFormatPath = "/yaas/storage/s1_Yeoreum/s14_EstimateStorage/s144_VideoBookEstemateTemplate/VideoBookEstimateTemplate_"
    
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
    pdf.drawImage(f"{DesignFormatPath}2.png", 0, 0)
    pdf.showPage()
    
    # PDF 파일 저장
    pdf.save()

##########################
##########################
##### EstimateUpdate #####
##########################
##########################

### EstimatePDF 생성 ###
def SolutionEstimateUpdate(projectName, email, Estimates):
    for i, Estimate in enumerate(Estimates):
        EstimateSetting, EstimateFilePath = EstimateSettingGen(projectName, Estimate, Estimates)
        
        print(f"< User: {email} | Project: {projectName} | 0{i+1}_{Estimate}_EstimateUpdate 시작 >")

        EstimatePNGPaths = []
        EstimateFolderPath = os.path.join(EstimateFilePath, f"{projectName}_{Estimate}Estimate")
        EstimateFileName = f"{projectName}_{Estimate}Estimate"
        EstimatePDFPath = os.path.join(EstimateFolderPath, f'{EstimateFileName}.pdf')

        if not os.path.exists(EstimatePDFPath):
            ## 견적서 데이터
            Project = EstimateSetting['EstimateSetting']['ProjectName']
            Client = EstimateSetting['EstimateSetting']['Client']
            Lenth = EstimateSetting['EstimateSetting']['Lenth(estimate)']
            
            StandardPriceVAT = EstimateSetting['EstimateSetting']['StandardPrice(estimate+vat)']
            StandardPrice = EstimateSetting['EstimateSetting']['StandardPrice(estimate)']
            VoiceActorVAT = EstimateSetting['EstimateSetting']['StandardPrice(vat)']
            
            PremiumPriceVAT = EstimateSetting['EstimateSetting']['PremiumPrice(estimate+vat)']
            PremiumPrice = EstimateSetting['EstimateSetting']['PremiumPrice(estimate)']
            VoiceCloneVAT = EstimateSetting['EstimateSetting']['PremiumPrice(vat)']
            
            ## 기본 폰트 설정, Noto Sans CJK 폰트 경로 설정
            font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
            font_prop = font_manager.FontProperties(fname = font_path)
            rc('font', family = font_prop.get_name())
            plt.rcParams['axes.unicode_minus'] = False  # 유니코드 마이너스 설정
            
            ## 01_Estimate 폴더 생성
            if not os.path.exists(EstimateFolderPath):
                os.makedirs(EstimateFolderPath)

            ## 02_표지 페이지 생성
            fig, ax = plt.subplots(figsize = (8.27, 11.69))  # A4 크기 (인치 단위)
            fig.patch.set_alpha(0.0) # 투명 배경
            ax.patch.set_alpha(0.0) # 투명 배경
            fig.subplots_adjust(left = 0.05, right = 0.95, top = 0.9, bottom = 0.1)  # 여백 설정
            # 제목
            ax.text(0.6, 1.04, f"일자: {Date()}\n\n도서: {SplitProjectName(Project)}\n\n의뢰: {Client}",
            fontsize = 14, weight = 'bold', transform = ax.transAxes, color = 'white', va = 'top', ha = 'left')
            ax.axis('off')  # 텍스트 영역의 축 숨기기
            
            # 표지 페이지 저장
            EstimatePNG0Path = os.path.join(EstimateFolderPath, f'{EstimateFileName}(0).png')
            EstimatePNGPaths.append(EstimatePNG0Path)
            plt.savefig(EstimatePNG0Path, dpi = 300, transparent = True)
            plt.close()

            ## 03_견적서 페이지 생성
            
            # 견적 옵션
            if Estimate == "TextBook":
                EstimateTitle = "매거진 기획&제작 견적서"
                Option1 = "스탠다드"
                Option2 = "프리미엄    "
                Lenth1 = "20-30페이지"
                Lenth2 = "30-40페이지"
            if Estimate == "AudioBook":
                EstimateTitle = "오디오북 제작 견적서"
                Option1 = "성우 보이스"
                Option2 = "클로닝 보이스"
                Lenth1 = Lenth
                Lenth2 = Lenth
            if Estimate == "VideoBook":
                EstimateTitle = "아바타 영상 제작 견적서"
                Option1 = "앵커 아바타"
                Option2 = "클로닝 아바타"
                Lenth1 = Lenth
                Lenth2 = Lenth
            
            fig, ax = plt.subplots(figsize = (8.27, 11.69))  # A4 크기 (인치 단위)
            fig.patch.set_alpha(0.0) # 투명 배경
            ax.patch.set_alpha(0.0) # 투명 배경
            fig.subplots_adjust(left = 0.05, right = 0.95, top = 0.9, bottom = 0.1)  # 여백 설정
            # 제목
            ax.text(0.05, 1, f"『{Project}』 {Client}  |  {EstimateTitle}", 
            fontsize = 14, weight = 'bold', transform = ax.transAxes, color = 'white')
            # 성우 보이스
            ax.text(0.05, 0.8, f"선택1: {Option1}        {Lenth1}       {StandardPriceVAT} (부가세포함)\n\n                                                                       {StandardPrice} ({VoiceActorVAT})", 
            fontsize = 11, weight = 'bold', transform = ax.transAxes, color = 'white')
            # 클로닝 보이스
            ax.text(0.05, 0.5, f"선택2: {Option2}    {Lenth2}       {PremiumPriceVAT} (부가세포함)\n\n                                                                       {PremiumPrice} ({VoiceCloneVAT})", 
            fontsize = 11, weight = 'bold', transform = ax.transAxes, color = 'white')
            ax.axis('off')  # 텍스트 영역의 축 숨기기
            
            # 견적서 페이지 저장
            EstimatePNG1Path = os.path.join(EstimateFolderPath, f'{EstimateFileName}(1).png')
            EstimatePNGPaths.append(EstimatePNG1Path)
            plt.savefig(EstimatePNG1Path, dpi = 300, transparent = True)
            plt.close()
            
            PNGsToPDF(EstimatePNGPaths, EstimatePDFPath, Estimate)
            
            print(f"[ User: {email} | Project: {projectName} | 0{i+1}_{Estimate}_EstimateUpdate 완료 ]\n")
        else:
            print(f"[ User: {email} | Project: {projectName} | 0{i+1}_{Estimate}_EstimateUpdate가 이미 완료됨 ]\n")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    ProjectName = '241204_개정교육과정초등교과별이해연수'
    #########################################################################
    
    SolutionEstimateUpdate(ProjectName, email)