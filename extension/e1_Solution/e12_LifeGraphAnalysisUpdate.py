## 라이프그래프 비포, 에프터 서치 후 두 그래프를 합쳐서 에프터에 대한 효과를 설명해주기 -> 해당 효과를 바탕으로 PDF 보고서 만들어주기
## 현재 행복하다는 사람한테는 새로운 방법 제시
## 새로운 일자의 BeforeLifeGraph 업데이트 할때 이전에 있던 라이프 그래프에서 없는 부분만 업데이트 하기(모두 업데이트 하지 말고), 그리고 구글 스프레드 시트에 업데이트 할때는 파일 경로가 없는 녀석만 업데이트
## 분석된 라이프 그래프 이미지 만들기
## 구글 시트에 해당 대상자의 성향도 파악
## 업로드된 라이프 그래프와 그렇지 않은 라이프 그래프 분리
## 프롬프트 업로드(2스탭? 또는 1스탭)
## 메일 또는 컨텐츠로 작성된 라이프 그래프와 그렇지 않은 라이프 그래프의 분리 (사람들이 이미 보낸 라이프 그래프와 그렇지 않은 라이프 그래프의 분리)
## 메일을 1-3차 정도의 피드백으로 분리
## 명상을 시작하고 지속적으로 유지하는 것이 무엇인지에 대한 고민(즉 포도에서만 그치는 것이 아닌 지속적으로 교육까지 고려!)
import os
import re
import json
import time
import gspread
import firebase_admin
import textwrap
import sys
sys.path.append("/yaas")

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


from matplotlib import font_manager, rc
from tqdm import tqdm
from datetime import datetime
from PIL import Image, ImageChops
from langdetect import detect
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from firebase_admin import credentials
from firebase_admin import db
from reportlab.lib.pagesizes import portrait
from reportlab.pdfgen import canvas

from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse

#########################
##### InputList 생성 #####
#########################
### 라이프그래프 데이터 로드 ###
def LoadLifeGraph():
    # 로드경로 설정
    BeforeLifeGraphStorage = '/yaas/storage/s2_Meditation/s21_BeforeStorage/s211_BeforeLifeGraph/'
    # 현재 폴더 파일 리스트
    StoragFileList = os.listdir(BeforeLifeGraphStorage)
    StoragJsonList = [file for file in StoragFileList if file.endswith('.json')]
    SortedStorageFileList = sorted(StoragJsonList, key = lambda x: datetime.strptime(re.search(r'\d{6}-\d{6}', x).group(), '%y%m%d-%H%M%S'), reverse = True)
    # 가장 최신 파일과, 파일이 여러개 있을 경우 필요 없는 하부 파일 삭제
    RecentFileName = SortedStorageFileList[0]
    RecentBeforeLifeGraphPath = BeforeLifeGraphStorage + RecentFileName
    with open(RecentBeforeLifeGraphPath, 'r', encoding = 'utf-8') as BeforeLifeGraphJson:
        BeforeLifeGraphList = json.load(BeforeLifeGraphJson)
        
    return BeforeLifeGraphList, RecentBeforeLifeGraphPath

## 라이프그래프를 InputList로
def LifeGraphToInputList(Answer):
    BeforeLifeGraphList, RecentBeforeLifeGraphPath = LoadLifeGraph()
    
    InputList = []
    for i in range(len(BeforeLifeGraphList)):
        if BeforeLifeGraphList[i]['LifeGraphFile'] is not None and BeforeLifeGraphList[i]['AnalysisData'] == [] and BeforeLifeGraphList[i]['Answer'] >= Answer:
            LifeGraphId = BeforeLifeGraphList[i]['LifeGraphId']
            Language = BeforeLifeGraphList[i]['Language']
            Date = f"[작성일] {BeforeLifeGraphList[i]['LifeGraphDate']}\n"
            Name = f"[이름] {BeforeLifeGraphList[i]['Name']}\n"
            Age = f"[나이] {BeforeLifeGraphList[i]['Age']}\n"
            Email = f"[이메일] {BeforeLifeGraphList[i]['Email']}\n\n"
            LifeGraphText = Date + Name + Age + Email
            for j in range(len(BeforeLifeGraphList[i]['LifeData'])):
                age = f"[시기] {BeforeLifeGraphList[i]['LifeData'][j]['StartAge']}-{BeforeLifeGraphList[i]['LifeData'][j]['EndAge']}\n"
                score = f"[행복지수] {BeforeLifeGraphList[i]['LifeData'][j]['Score']}\n"
                if j < len(BeforeLifeGraphList[i]['LifeData']) - 1:
                    reason = f"[내용] {BeforeLifeGraphList[i]['LifeData'][j]['ReasonGlobal']}\n\n"
                else:
                    reason = f"[내용] {BeforeLifeGraphList[i]['LifeData'][j]['ReasonGlobal']}"
                LifeGraphText = LifeGraphText + age + score + reason
            InputDic = {'Id': i+1, 'LifeGraphId': LifeGraphId, 'Language': Language, 'LifeGraph': LifeGraphText}
            InputList.append(InputDic)
    
    return InputList, RecentBeforeLifeGraphPath

########################
##### FilterKo 조건 #####
########################
def LifeGraphAnalysisKoFilter(Response):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        outputJson = json.loads(Response)
    except json.JSONDecodeError:
        return "BSContextDefine, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 딕셔너리가 "작성자정보"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic1 = outputJson['작성자정보']
    except:
        return "BSContextDefine, JSON에서 오류 발생: '작성자정보' 미포함"
    # Error3: 딕셔너리가 "중요시기"의 키로 시작하지 않을때의 예외처리
    try:
        OutputDic2 = outputJson['중요시기']
    except:
        return "BSContextDefine, JSON에서 오류 발생: '중요시기' 미포함"
    # Error3: 자료의 구조가 다를 때의 예외 처리
    if ('작성일' not in OutputDic1 or '작성자' not in OutputDic1 or '나이' not in OutputDic1 or '국적' not in OutputDic1 or '마음패턴' not in OutputDic1 or '마음문제' not in OutputDic1 or '마음능력' not in OutputDic1):
        return "BSContextDefine, JSON에서 오류 발생: JSONKeyError"
    # Error4: "중요시기"가 리스트가 아닐때의 예외처리
    if not isinstance(OutputDic2, list):
        return "BSContextDefine, JSON에서 오류 발생: '중요시기'가 리스트가 아님"
    # Error5: "중요시기" 리스트 내 딕셔너리 자료의 구조가 다를 때의 예외 처리
    for outputDic in OutputDic2:
        if ('시기' not in outputDic or '행복지수' not in outputDic or '내용' not in outputDic or '마음' not in outputDic or '원인' not in outputDic or '예상질문' not in outputDic or '예상답변' not in outputDic):
            return "BSContextDefine, JSON에서 오류 발생: '중요시기'가 리스트 내에서 JSONKeyError"

    return outputJson

### 라이프그래프 분석 ###
def LifeGraphAnalysisProcess(projectName, email, Process = "LifeGraphAnalysis", MessagesReview = "on", mode = "Master", Answer = 6):
    ## LifeGraphAnalysisProcess
    promptFrameKoPath = "/yaas/extension/e3_Database/e31_PromptData/e311_LifeGraphPrompt/b311-01_LifeGraphAnalysisKo.json"
    InputList, RecentBeforeLifeGraphPath = LifeGraphToInputList(Answer)
    with open(RecentBeforeLifeGraphPath, 'r', encoding = 'utf-8') as RecentBeforeLifeGraph:
        RecentBeforeLifeGraphList = json.load(RecentBeforeLifeGraph)
    ErrorCount = 0
    InputCount = len(InputList)
    i = 0
    
    while i < InputCount:
        Input = InputList[i]['LifeGraph']
        Language = InputList[i]['Language']
        ProcessCount = i + 1
        
        ## LifeGraphAnalysisProcess Response 생성
        # 라이프 그래프 언어가 한글인 경우
        if Language == 'ko':
            print(Language)
            Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, Input, ProcessCount, PromptFramePath = promptFrameKoPath, Mode = mode, messagesReview = MessagesReview)
            Filter = LifeGraphAnalysisKoFilter(Response)
            
            if isinstance(Filter, str):
                print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | {Filter}")
                ErrorCount += 1
                print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | 오류횟수 {ErrorCount}회, 2분 후 프롬프트 재시도")
                time.sleep(120)
                if ErrorCount == 5:
                    sys.exit(f"Project: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | 오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
                continue
            else:
                OutputDic = Filter
                print(f"Project: {projectName} | Process: {Process} {ProcessCount}/{InputCount} | JSONDecode 완료")
                ErrorCount = 0
                
                ## RecentBeforeLifeGraph 업데이트
                for BeforeLifeGraph in RecentBeforeLifeGraphList:
                    if BeforeLifeGraph['LifeGraphId'] == InputList[i]['LifeGraphId']:
                        BeforeLifeGraph['Residence'] = OutputDic['작성자정보']
                        BeforeLifeGraph['Pattern'] = OutputDic['작성자정보']
                        BeforeLifeGraph['Negative'] = OutputDic['작성자정보']
                        BeforeLifeGraph['Positive'] = OutputDic['작성자정보']
                        LifeData = BeforeLifeGraph['LifeData']
                        AnalysisData = []
                        for Data in OutputDic['중요시기']:
                            StartAge, EndAge = map(int, Data['시기'].split('-'))
                            for data in LifeData:
                                if StartAge == data['StartAge'] and EndAge == data['EndAge']:
                                    LifeDataId = data['LifeDataId']
                                    break
                            Score = Data['행복지수']
                            ReasonGlobal = Data['내용']
                            Problem = Data['마음']
                            Reason = Data['원인']
                            Question = Data['예상질문']
                            Answer = Data['예상답변']
                            AnalysisDataDic = {'LifeDataId': LifeDataId, 'StartAge': StartAge, 'EndAge': EndAge, 'Score': Score, 'ReasonGlobal': ReasonGlobal, 'Problem': Problem, 'Reason': Reason, 'Question': Question, 'Answer': Answer, }
                            AnalysisData.append(AnalysisDataDic)
                        BeforeLifeGraph['AnalysisData'] = AnalysisData
                        break
                    
                with open(RecentBeforeLifeGraphPath, 'w', encoding = 'utf-8') as RecentBeforeLifeGraphJson:
                    json.dump(RecentBeforeLifeGraphList, RecentBeforeLifeGraphJson, ensure_ascii = False, indent = 4)
        # # 라이프 그래프 언어가 한글이 아닌 경우
        # else:
        
        # 다음 아이템으로 이동
        i += 1

## 라이프그래프의 이미지화(PNG)
def LifeGraphToPNG(LifeGraphDate, Name, Age, Language, Email, LifeData):   
    # 기본 폰트 설정, Noto Sans CJK 폰트 경로 설정
    font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font_prop = font_manager.FontProperties(fname = font_path)
    rc('font', family = font_prop.get_name())
    plt.rcParams['axes.unicode_minus'] = False  # 유니코드 마이너스 설정
    
    PNGPaths = []
    FilePath = f"/yaas/storage/s2_Meditation/s21_BeforeStorage/s211_BeforeLifeGraph/s2113_BeforeLifeGraphAnalysisPDF/"
    FileName = f"{LifeGraphDate.replace('-', '')}_{Name}({Age})_LifeGraph"
    PDFPath = FilePath + FileName + '.pdf'

    ## 표지 페이지 생성
    fig, ax = plt.subplots(figsize = (8.27, 11.69))  # A4 크기 (인치 단위)
    fig.subplots_adjust(left = 0.05, right = 0.95, top = 0.9, bottom = 0.1)  # 여백 설정
    ax.text(0.01, 0.99, f"\nDate             :  {LifeGraphDate}\nName          :  {Name}\nAge               :  {Age}\nEmail           :  {Email}\nLanguage  :  {Language}", wrap = True, horizontalalignment = 'left', verticalalignment = 'top', fontsize = 11, transform = ax.transAxes)
    ax.axis('off')  # 텍스트 영역의 축 숨기기
    
    # 표지 페이지 저장
    PNGPath = FilePath + FileName + '(0).png'
    PNGPaths.append(PNGPath)
    plt.savefig(PNGPath, dpi = 300)
    plt.close()

    ## 첫번째 페이지 생성
    DataFrame = pd.DataFrame(LifeData)
    DataFrame['AgeRange'] = DataFrame['StartAge'].astype(str) + '-' + DataFrame['EndAge'].astype(str)
    def ScoreToColor(score):
        if score >= 0:
            return plt.cm.Greens(score / 10)
        else:
            return plt.cm.Reds(-score / 10)
    DataFrame['Color'] = DataFrame['Score'].apply(ScoreToColor)

    # 지정된 여백으로 그림 및 축 생성, 여백 설정
    fig, ax = plt.subplots(2, 1, figsize = (8.27, 11.69))  # A4 크기 (인치 단위)
    fig.subplots_adjust(left = 0.1, right = 0.9, top = 0.9, bottom = 0.1, hspace = 0.4)  # 플롯 사이에 공간 추가

    # 상단 그래프
    sns.barplot(x = 'AgeRange', y = 'Score', hue = 'AgeRange', data = DataFrame, palette = DataFrame['Color'].to_list(), dodge = False, ax = ax[0])
    ax[0].set_title(f'\n\n', fontweight = 'bold')
    ax[0].set_xlabel(f'\nAge', fontweight = 'bold')
    ax[0].set_ylabel('Happiness Score', fontweight = 'bold')
    # ax[0].legend().remove() # 범례 제거
    ax[0].set_yticks(range(-10, 11, 2)) # y축 눈금을 2단위로 설정
    ax[0].axhline(0, color='black', linewidth=0.5) # y=0 위치에 수평선 추가
    for index, row in DataFrame.iterrows():
        if {row['Score']} != 0:
            ax[0].text(index, row['Score'] / 2, str(row['Score']), color = 'white', ha = "center", weight = 'bold')

    # 원형숫자로 변경
    def NumberConverter(Number):
        ConvertedNumbers = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑪', '⑫', '⑬', '⑭', '⑮']
        Number = int(Number)
        return ConvertedNumbers[Number-1]

    # 하단 절반을 위한 텍스트 준비 (단어 줄바꿈 포함)
    if Language == 'en':
        Width = 70
    else:
        Width = 50
    WrappedTexts = []
    TotalRows = len(DataFrame)
    for index, row in DataFrame.iterrows():
        if row['LifeDataId'] <= 9:
            wrapped_text = "\n       ".join(textwrap.wrap(row['ReasonGlobal'], width = Width))
        else:
            wrapped_text = "\n         ".join(textwrap.wrap(row['ReasonGlobal'], width = Width))
            
        if index == TotalRows - 1:
            WrappedTexts.append(f"{NumberConverter(row['LifeDataId'])}   {row['StartAge']}-{row['EndAge']} ({row['Score']}) :  {wrapped_text}")
        else:
            WrappedTexts.append(f"{NumberConverter(row['LifeDataId'])}   {row['StartAge']}-{row['EndAge']} ({row['Score']}) :  {wrapped_text}\n")
        
    # 첫 번째는 22개, 그 후에는 50개 단위로 묶기
    ProfileText = f"|    {LifeGraphDate}    |    {Name}    |    0-{Age}    |\n\n\n"
    ReasonText = ProfileText + "\n".join(WrappedTexts)
    ReasonLines = ReasonText.split('\n')
    PagedReasonLines = [ReasonLines[:22]] + [ReasonLines[i:i+50] for i in range(22, len(ReasonLines), 50)]

    # 하단 텍스트
    ax[1].text(0.01, 0.99, "\n".join(PagedReasonLines[0]), wrap = True, horizontalalignment = 'left', verticalalignment = 'top', fontsize = 11, transform = ax[1].transAxes)
    ax[1].axis('off')  # 텍스트 영역의 축 숨기기

    # 첫번째 페이지 저장
    PNGPath = FilePath + FileName + '(1).png'
    PNGPaths.append(PNGPath)
    plt.savefig(PNGPath, dpi = 300)
    plt.close()
    
    ## 두번째 페이지부터 생성
    if len(PagedReasonLines) >= 2:
        _PagedReasonLines = PagedReasonLines[1:]
        for i in range(len(_PagedReasonLines)):
            fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4 크기 (인치 단위)
            fig.subplots_adjust(left = 0.1, right = 0.9, top = 0.9, bottom = 0.1)  # 여백 설정
            ax.text(0.01, 0.99, "\n".join(_PagedReasonLines[i]), wrap = True, horizontalalignment = 'left', verticalalignment = 'top', fontsize = 11, transform = ax.transAxes)
            ax.axis('off')  # 텍스트 영역의 축 숨기기

            # 두번째 페이지부터 저장
            PNGPath = FilePath + FileName + f'({i+2}).png'
            PNGPaths.append(PNGPath)
            plt.savefig(PNGPath, dpi = 300)
            plt.close()
            
    return FileName, PDFPath, PNGPaths

### 라이프그래프의 이미지를 PDF로 묶기 ###
def PNGsToPDF(PNGPaths, PDFPath):
    # 디자인 포멧 경로
    DesignFormatPath = "/yaas/storage/s2_Meditation/Design_Format/LifeGraph_Design_Format/LifeGraph_Design_Format_"
    
    # 첫 번째 이미지 크기에 맞는 PDF 생성
    FirstImage = Image.open(PNGPaths[0])
    FirstWidth, FirstHeight = FirstImage.size
    pdf = canvas.Canvas(PDFPath, pagesize=portrait((FirstWidth, FirstHeight)))

    for i in range(len(PNGPaths)):
        # 그래프 이미지와 디자인 포멧 불러오기
        image = Image.open(PNGPaths[i])
        DesignFormat = Image.open(DesignFormatPath + f"{i}.png")
        # 그래프 이미지와 디자인 포멧 합치기
        image = image.convert("RGBA")
        DesignFormat = DesignFormat.convert("RGBA")
        BlendedImage = ImageChops.multiply(DesignFormat, image)
        # 합쳐진 이미지 임시저장
        BlendedImage.save(PNGPaths[i], "PNG", optimize=True)
        # 이미지를 PDF에 추가
        pdf.drawImage(PNGPaths[i], 0, 0)
        pdf.showPage()
        # PDF로 저장된 PNG 파일 제거
        os.remove(PNGPaths[i])

    # PDF 파일 저장
    pdf.save()

## 추가행 업데이트
def AddRowToSheet(BeforeLifeGraphList, AccountFilePath = '/yaas/storage/s2_Meditation/API_KEY/courserameditation-028871d3c653.json', ProjectName = 'Coursera Meditation Project', SheetName = 'BeforeLifeGraph'):
    ## Sheet에서 최신 Id 가져오기
    # 서비스 계정
    SERVICE_ACCOUNT_FILE = AccountFilePath
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes = SCOPES)
    client = gspread.authorize(credentials)
    # 스프레드시트 읽고 쓰기
    Sheet = client.open(ProjectName)
    worksheet = Sheet.worksheet(SheetName)
    # 가장 최신 id 가져오기
    RecentId = worksheet.acell('A3').value
    
    ## Sheet에서 가져온 최신 Id가 BeforeLifeGraphList에서 몇 번째 데이터인지 찾기
    for i in range(len(BeforeLifeGraphList)):
        if BeforeLifeGraphList[i]['LifeGraphId'] == RecentId:
            AddNum = i
            break

    ## AddNum 만큼 새로운 행 추가
    if AddNum > 0:
        # 2행 다음부터 AddNum 만큼의 새로운 행 추가
        NewRows = [[''] * worksheet.col_count] * AddNum
        worksheet.insert_rows(NewRows, row = 3)
        print(f'[ 스프레드 시트({SheetName})에 ({AddNum})개의 빈 행 추가 ]')
    else:
        print(f'[ 스프레드 시트({SheetName})에 추가할 빈 행 없음 ]')

## 구글 스프레드 시트 업데이트
def UpdateSheet(AccountFilePath = '/yaas/storage/s2_Meditation/API_KEY/courserameditation-028871d3c653.json', ProjectName = 'Coursera Meditation Project', SheetName = 'BeforeLifeGraph', Type = 'Text', HeaderRow = 2, Row = 3, Colum = 1, Data = 'Hello', SubData = 'World!', FileName = 'None', FilePath = 'None', FolderId = '16SB0qJBhEwCugqOe_bV7QYecFj922u1J'):
    # 서비스 계정
    SERVICE_ACCOUNT_FILE = AccountFilePath
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes = SCOPES)
    client = gspread.authorize(credentials)
    # 스프레드시트 읽고 쓰기
    Sheet = client.open(ProjectName)
    worksheet = Sheet.worksheet(SheetName)
    worksheet.get_all_records(head = HeaderRow)
    if Type == 'Text':
        worksheet.update_cell(Row, Colum, Data)
    elif Type == 'Link':
        # 파일을 구글 드라이브에 업로드
        driveservice = build('drive', 'v3', credentials = credentials)
        FileMetadata = {'name': FileName + '.pdf', 'parents': [FolderId]}
        Media = MediaFileUpload(FilePath, mimetype = 'application/pdf')
        File = driveservice.files().create(body = FileMetadata, media_body = Media, fields = 'id').execute()
        # 파일을 구글 드라이브에 업로드
        FileId = File.get('id')
        FileLink = f'https://drive.google.com/file/d/{FileId}/view?usp=sharing'
        # 스프레드시트 링크 삽입
        worksheet.update_cell(Row, Colum, f'=HYPERLINK("{FileLink}", "{SubData}")')
    
### 구글 스프레드 시트에 라이프그래프 업데이트 ###
def UpdateBeforeLifeGraphToSheet(BeforeLifeGraphPath, BeforeLifeGraphList):
    # 추가행 업데이트
    AddRowToSheet(BeforeLifeGraphList)
    # 라이프 그래프 업데이트
    UpdateCount = 0
    for i in tqdm(range(len(BeforeLifeGraphList)), desc = "[ 라이프그래프 구글시트 업데이트 ]"):
        if 'LifeGraphFile' not in BeforeLifeGraphList[i]:
            # 라이프그래프 데이터 추출
            Id = BeforeLifeGraphList[i]['LifeGraphId']
            Date = BeforeLifeGraphList[i]['LifeGraphDate']
            Name = BeforeLifeGraphList[i]['Name']
            Age = BeforeLifeGraphList[i]['Age']
            Language = BeforeLifeGraphList[i]['Language']
            Email = BeforeLifeGraphList[i]['Email']
            LifeData = BeforeLifeGraphList[i]['LifeData']
            
            # 라이프그래프 파일 생성
            fileName, PDFPath, PNGPaths = LifeGraphToPNG(Date, Name, Age, Language, Email, LifeData)
            PNGsToPDF(PNGPaths, PDFPath)
            BeforeLifeGraphList[i]['LifeGraphFile'] = PDFPath
            
            # 구글 스프레드 시트 업데이트
            row = i + 3
            UpdateSheet(Row = row, Colum = 1, Data = Id)
            UpdateSheet(Row = row, Colum = 2, Data = Date)
            UpdateSheet(Row = row, Colum = 3, Data = Name)
            UpdateSheet(Row = row, Colum = 4, Data = Age)
            UpdateSheet(Row = row, Colum = 8, Data = Email)
            UpdateSheet(Row = row, Type = 'Link', Colum = 9, Data = PDFPath, SubData = f'({Name})의 라이프그래프 보기/다운로드', FileName = fileName, FilePath = PDFPath)
            
            UpdateCount += 1
            if UpdateCount >= 5:
                with open(BeforeLifeGraphPath, 'w', encoding = 'utf-8') as BeforeLifeGraphJson:
                    json.dump(BeforeLifeGraphList, BeforeLifeGraphJson, ensure_ascii = False, indent = 4)
                UpdateCount = 0
            time.sleep(4)
        
    if UpdateCount > 0:
        with open(BeforeLifeGraphPath, 'w', encoding = 'utf-8') as BeforeLifeGraphJson:
            json.dump(BeforeLifeGraphList, BeforeLifeGraphJson, ensure_ascii = False, indent = 4)

# #########################
# ### 라이프 그래프 업데이트 ###
# #########################
# def LifeGraphUpdate():
#     BeforeLifeGraphPath, BeforeLifeGraphList = DownloadLifeGraph()
#     UpdateBeforeLifeGraphToSheet(BeforeLifeGraphPath, BeforeLifeGraphList)
    
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "General"
    projectName = "Meditation"
    #########################################################################
    # LifeGraphAnalysisProcess(projectName, email)
    
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd

    # 데이터 생성
    data = pd.DataFrame({
        'x': range(10),
        'y': [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    })

    # A4 용지 크기 설정 (in inches)
    fig = plt.figure(figsize=(11.7, 8.3))

    # 그래프 그리기
    ax1 = fig.add_subplot(212)  # 2행 1열 중 2번째 영역
    sns.lineplot(x='x', y='y', data=data, ax=ax1)
    ax1.set_title('Line Plot')

    # 텍스트 추가
    ax2 = fig.add_subplot(224)  # 2행 2열 중 4번째 영역
    ax2.axis('off')  # 축 제거
    text = "This is an example text in the lower right quadrant of the A4 page."
    ax2.text(0.5, 0.5, text, horizontalalignment='center', verticalalignment='center', fontsize=12)

    # 여백 조정
    plt.subplots_adjust(hspace=0.3, wspace=0.3)

    # PDF 파일로 저장
    output_path = "/yaas/test.pdf"
    plt.savefig(output_path, format='pdf')