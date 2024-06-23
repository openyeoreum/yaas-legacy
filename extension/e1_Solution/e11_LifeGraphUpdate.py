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
import urllib.parse
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

## 오늘 날짜 설정
def Date(Option = "Day"):
    if Option == "Day":
      now = datetime.now()
      date = now.strftime('%y%m%d')
      date += '-000000'
    elif Option == "Second":
      now = datetime.now()
      date = now.strftime('%y%m%d-%H%M%S')
    
    return date

## 라이프그래프 데이터 전처리
def PreprocessingLifeGraph(FirebaseJson, Answer):
    # 라이프 그래프의 리스트화
    RawLifeGraphList = list(FirebaseJson.items())
    # 라이프 그래프 전처리
    IdPattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z")
    DatePattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    PreprocessedLifeGraphList = []
    for i in range(len(RawLifeGraphList)):
        url = urllib.parse.unquote(RawLifeGraphList[i][1]['graph_url'])
        LifeGraphId = IdPattern.search(url).group()
        LifeGraphDate = DatePattern.search(url).group()
        name = RawLifeGraphList[i][0].strip()
        Name = re.sub(r'\(\d+\)', '', name)
        Progress = None
        Age = RawLifeGraphList[i][1]['age']
        Nation = None
        if 'region' in RawLifeGraphList[i][1]:
            Residence = RawLifeGraphList[i][1]['region']
        else:
            Residence = None
        PhoneNumber = None
        Email = RawLifeGraphList[i][1]['email']
        Pattern = None
        Negative = None
        Positive = None
        LifeData = []
        AnalysisData = []
        LifeDataReasons = []
        AnswerCount = 0
        for j in range(len(RawLifeGraphList[i][1]['lifeData'])):
            LifeDataId = j + 1
            StartAge = RawLifeGraphList[i][1]['lifeData'][j]['startAge']
            EndAge = RawLifeGraphList[i][1]['lifeData'][j]['endAge']
            Score = RawLifeGraphList[i][1]['lifeData'][j]['score']
            ReasonGlobal = RawLifeGraphList[i][1]['lifeData'][j]['reason']
            LifeDataDic = {"LifeDataId": LifeDataId, "StartAge": StartAge, "EndAge": EndAge, "Score": Score, "ReasonGlobal": ReasonGlobal}
            LifeData.append(LifeDataDic)
            if ReasonGlobal != '':
                AnswerCount += 1
            LifeDataReasons.append(ReasonGlobal)
        
        LifeDataReasonsText = " ".join(LifeDataReasons)
        try:
            Language = detect(LifeDataReasonsText)
        except:
            Language = None
        _Answer = AnswerCount
        
        LifeGraphDic = {"LifeGraphId": LifeGraphId, "LifeGraphDate": LifeGraphDate, "Name": Name, "Progress": Progress, "Age": Age, "Language": Language, "Nation": Nation, "Residence": Residence, "Answer": _Answer, "PhoneNumber": PhoneNumber, "Email": Email, "Pattern": Pattern, "Negative": Negative, "Positive": Positive, "LifeData": LifeData, "LifeGraphFile": None, "AnalysisData": AnalysisData, "LifeGraphAnalysisFile": None}
        if _Answer >= Answer:
            PreprocessedLifeGraphList.append(LifeGraphDic)
    ## 라이프 그래프 날짜역순(같은 날짜는 생성 역순)으로 정리
    DateSortedPreprocessedLifeGraphList = sorted(
        PreprocessedLifeGraphList,
        key=lambda x: datetime.strptime(x["LifeGraphId"], "%Y-%m-%dT%H:%M:%S.%fZ"),
        reverse=True
    )
    return DateSortedPreprocessedLifeGraphList

## 다운받은 라이프그래프 최신데이터와 합치기
def MergeRecentLifeGraph(RecentBeforeLifeGraphList, BeforeLifeGraphList):
    RecentBeforeLifeGraphId = None
    NewBeforeLifeGraphList = []
    if RecentBeforeLifeGraphList != []:
        RecentBeforeLifeGraphId = RecentBeforeLifeGraphList[0]['LifeGraphId']
        for i in range(len(BeforeLifeGraphList)):
            if BeforeLifeGraphList[i]['LifeGraphId'] == RecentBeforeLifeGraphId:
                NewBeforeLifeGraphList = BeforeLifeGraphList[:i]
                break
        MergedBeforeLifeGraphList = NewBeforeLifeGraphList + RecentBeforeLifeGraphList
        return MergedBeforeLifeGraphList
    else:
        return BeforeLifeGraphList
        
### 라이프그래프 데이터 다운로드 ###
def DownloadLifeGraph(Term = 'Day', AccountFilePath = '/yaas/storage/s2_Meditation/API_KEY/coursera-meditation-db-firebase-adminsdk-okrn4-80af02fd79.json', Answer = 0):
    # 저장경로 설정
    BeforeLifeGraphStorage = '/yaas/storage/s2_Meditation/s21_BeforeStorage/s211_BeforeLifeGraph/s2111_BeforeLifeGraph/'
    date = Date(Option = Term)
    FileName = f'{date}_BeforeLifeGraph.json'
    BeforeLifeGraphPath = BeforeLifeGraphStorage + FileName
    # 현재 폴더 파일 리스트
    StoragFileList = os.listdir(BeforeLifeGraphStorage)
    StoragJsonList = [file for file in StoragFileList if file.endswith('.json')]
    SortedStorageFileList = sorted(StoragJsonList, key = lambda x: datetime.strptime(re.search(r'\d{6}-\d{6}', x).group(), '%y%m%d-%H%M%S'), reverse = True)
    if SortedStorageFileList != []:
        # 가장 최신 파일과, 파일이 여러개 있을 경우 필요 없는 하부 파일 삭제
        RecentFileName = SortedStorageFileList[0]
        match = re.search(r'\d{6}-\d{6}', RecentFileName)
        Recentdate = match.group()
    else:
        RecentFileName = '000101-000001_BeforeLifeGraph.json'
    RecentBeforeLifeGraphPath = BeforeLifeGraphStorage + RecentFileName
    if len(SortedStorageFileList) >= 3:
        RemoveFileName = SortedStorageFileList[2:]
        for RemoveFile in RemoveFileName:
            os.remove(BeforeLifeGraphStorage + RemoveFile)

    # 파일명 중 yymmdd-HHmmss 비교 함수 #
    def CompareFilename(fileName, recentFileName, Term):
        Beforedt = datetime.strptime(fileName.split('_')[0], "%y%m%d-%H%M%S")
        Recentdt = datetime.strptime(recentFileName.split('_')[0], "%y%m%d-%H%M%S")
        if Term == 'Second':
            return Beforedt != Recentdt
        elif Term == 'Day':
            return Beforedt.date() != Recentdt.date()

    # 라이프그래프 다운로드 및 업데이트
    if CompareFilename(FileName, RecentFileName, Term):
        # 서비스 계정
        SERVICE_ACCOUNT_FILE = AccountFilePath
        Credentials = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(Credentials, {'databaseURL': 'https://coursera-meditation-db.firebaseio.com/'})
        # 다운로드 및 JSON 파일 저장
        reference = db.reference('/')
        FirebaseJson = reference.get()
        BeforeLifeGraphList = PreprocessingLifeGraph(FirebaseJson, Answer)
        # 다운받은 라이프그래프 최신데이터와 합치기
        try:
            with open(RecentBeforeLifeGraphPath, 'r', encoding = 'utf-8') as RecentBeforeLifeGraphJson:
                RecentBeforeLifeGraphList = json.load(RecentBeforeLifeGraphJson)
        except:
            RecentBeforeLifeGraphList = []
        MergedBeforeLifeGraphList = MergeRecentLifeGraph(RecentBeforeLifeGraphList, BeforeLifeGraphList)
        # 합쳐진 라이프 그래프 저장
        with open(BeforeLifeGraphPath, 'w', encoding = 'utf-8') as BeforeLifeGraphJson:
            json.dump(MergedBeforeLifeGraphList, BeforeLifeGraphJson, ensure_ascii = False, indent = 4)
        print(f'[ 업데이트 옵션 ({Term}) | 버전({date}) 라이프그래프 다운로드 및 업데이트 : {FileName} ]')
        return BeforeLifeGraphPath, MergedBeforeLifeGraphList
    else:
        with open(RecentBeforeLifeGraphPath, 'r', encoding = 'utf-8') as BeforeLifeGraphJson:
            BeforeLifeGraphList = json.load(BeforeLifeGraphJson)
        print(f'[ 업데이트 옵션 ({Term}) | 현재 라이프그래프는 최신버전({Recentdate}) : {RecentFileName} ]')
        return BeforeLifeGraphPath, BeforeLifeGraphList

## 라이프그래프의 이미지화(PNG)
def LifeGraphToPNG(LifeGraphDate, Name, Age, Language, Residence, Email, LifeData):   
    # 기본 폰트 설정, Noto Sans CJK 폰트 경로 설정
    font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font_prop = font_manager.FontProperties(fname = font_path)
    rc('font', family = font_prop.get_name())
    plt.rcParams['axes.unicode_minus'] = False  # 유니코드 마이너스 설정
    
    PNGPaths = []
    FilePath = f"/yaas/storage/s2_Meditation/s21_BeforeStorage/s211_BeforeLifeGraph/s2112_BeforeLifeGraphPDF/"
    FileName = f"{LifeGraphDate.replace('-', '')}_{Name}({Age})_LifeGraph"
    PDFPath = FilePath + FileName + '.pdf'

    ## 표지 페이지 생성
    fig, ax = plt.subplots(figsize = (8.27, 11.69))  # A4 크기 (인치 단위)
    fig.subplots_adjust(left = 0.05, right = 0.95, top = 0.9, bottom = 0.1)  # 여백 설정
    ax.text(0.01, 0.99, f"\nDate             :  {LifeGraphDate}\nName          :  {Name}\nAge               :  {Age}\nResidence :  {Residence}\nEmail           :  {Email}\nLanguage  :  {Language}", wrap = True, horizontalalignment = 'left', verticalalignment = 'top', fontsize = 11, transform = ax.transAxes)
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
    ProfileText = f"|    {LifeGraphDate}    |    {Name}    |    0-{Age}    |    {Residence}    |\n\n\n"
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
    DesignFormatPath = "/yaas/storage/s2_Meditation/Design_Format/s2112_BeforeLifeGraphPDF_Format/s2112_BeforeLifeGraphPDF_Format_"
    
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
    AddNum = 0
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
        if BeforeLifeGraphList[i]['LifeGraphFile'] is None:
            # 라이프그래프 데이터 추출
            Id = BeforeLifeGraphList[i]['LifeGraphId']
            Date = BeforeLifeGraphList[i]['LifeGraphDate']
            Name = BeforeLifeGraphList[i]['Name']
            Age = BeforeLifeGraphList[i]['Age']
            Language = BeforeLifeGraphList[i]['Language']
            Residence = BeforeLifeGraphList[i]['Residence']
            Answer = BeforeLifeGraphList[i]['Answer']
            Email = BeforeLifeGraphList[i]['Email']
            LifeData = BeforeLifeGraphList[i]['LifeData']
            
            # 라이프그래프 파일 생성
            fileName, PDFPath, PNGPaths = LifeGraphToPNG(Date, Name, Age, Language, Residence, Email, LifeData)
            PNGsToPDF(PNGPaths, PDFPath)
            BeforeLifeGraphList[i]['LifeGraphFile'] = PDFPath
            
            # 구글 스프레드 시트 업데이트
            row = i + 3
            UpdateSheet(Row = row, Colum = 1, Data = Id)
            UpdateSheet(Row = row, Colum = 2, Data = Date)
            UpdateSheet(Row = row, Colum = 3, Data = Name)
            UpdateSheet(Row = row, Colum = 4, Data = Age)
            UpdateSheet(Row = row, Colum = 5, Data = Language)
            UpdateSheet(Row = row, Colum = 6, Data = Residence)
            UpdateSheet(Row = row, Colum = 7, Data = Answer)
            UpdateSheet(Row = row, Colum = 11, Data = Email)
            UpdateSheet(Row = row, Type = 'Link', Colum = 12, Data = PDFPath, SubData = f'({Name})의 라이프그래프 보기/다운로드', FileName = fileName, FilePath = PDFPath)
            
            UpdateCount += 1
            if UpdateCount >= 5:
                with open(BeforeLifeGraphPath, 'w', encoding = 'utf-8') as BeforeLifeGraphJson:
                    json.dump(BeforeLifeGraphList, BeforeLifeGraphJson, ensure_ascii = False, indent = 4)
                UpdateCount = 0
            time.sleep(4)
        
    if UpdateCount > 0:
        with open(BeforeLifeGraphPath, 'w', encoding = 'utf-8') as BeforeLifeGraphJson:
            json.dump(BeforeLifeGraphList, BeforeLifeGraphJson, ensure_ascii = False, indent = 4)

#########################
### 라이프 그래프 업데이트 ###
#########################
def LifeGraphUpdate(term):
    BeforeLifeGraphPath, BeforeLifeGraphList = DownloadLifeGraph(Term = term)
    UpdateBeforeLifeGraphToSheet(BeforeLifeGraphPath, BeforeLifeGraphList)
    
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    term = "Second"
    #########################################################################
    LifeGraphUpdate(term)