## 라이프 그래프 날짜순으로 csv파일로 업데이트
## 라이프 그래프 양식을 깔끔하게 정리하여 업데이트 + 이미지 자료 첨부
## 메일 또는 컨텐츠로 작성된 라이프 그래프와 그렇지 않은 라이프 그래프의 분리 (사람들이 이미 보낸 라이프 그래프와 그렇지 않은 라이프 그래프의 분리)
## 메일을 1-3차 정도의 피드백으로 분리
## 명상을 시작하고 지속적으로 유지하는 것이 무엇인지에 대한 고민(즉 포도에서만 그치는 것이 아닌 지속적으로 교육까지 고려!)
import os
import re
import json
import gspread
import firebase_admin
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import textwrap
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from langdetect import detect
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from firebase_admin import credentials
from firebase_admin import db

## 오늘 날짜 설정
def Date(Option = "Day"):
    if Option == "Day":
      now = datetime.now()
      date = now.strftime('%y%m%d')
    elif Option == "Second":
      now = datetime.now()
      date = now.strftime('%y%m%d%H%M%S')
    
    return date

## 라이프그래프 데이터 전처리
def PreprocessingLifeGraph(FirebaseJson, Quality):
    # 라이프 그래프의 리스트화
    RawLifeGraphList = list(FirebaseJson.items())
    # 라이프 그래프 전처리
    DatePattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    PreprocessedLifeGraphList = []
    for i in range(len(RawLifeGraphList)):
        LifeGraphId = i + 1
        LifeGraphDate = DatePattern.search(RawLifeGraphList[i][1]['graph_url']).group()
        Name = RawLifeGraphList[i][0].strip()
        Progress = None
        Age = RawLifeGraphList[i][1]['age']
        Residence = None
        PhoneNumber = None
        Email = RawLifeGraphList[i][1]['email']
        LifeData = []
        LifeDataReasons = []
        QualityCount = 0
        for j in range(len(RawLifeGraphList[i][1]['lifeData'])):
            LifeDataId = j + 1
            StartAge = RawLifeGraphList[i][1]['lifeData'][j]['startAge']
            EndAge = RawLifeGraphList[i][1]['lifeData'][j]['endAge']
            Score = RawLifeGraphList[i][1]['lifeData'][j]['score']
            ReasonGlobal = RawLifeGraphList[i][1]['lifeData'][j]['reason']
            LifeDataDic = {"LifeDataId": LifeDataId, "StartAge": StartAge, "EndAge": EndAge, "Score": Score, "ReasonGlobal": ReasonGlobal}
            LifeData.append(LifeDataDic)
            if ReasonGlobal != '':
                QualityCount += 1
            LifeDataReasons.append(ReasonGlobal)
        
        LifeDataReasonsText = " ".join(LifeDataReasons)
        try:
            Language = detect(LifeDataReasonsText)
        except:
            Language = None
        _Quality = QualityCount
        
        LifeGraphDic = {"LifeGraphId": f"{str(LifeGraphId) + '-' + LifeGraphDate}", "LifeGraphDate": LifeGraphDate, "Name": Name, "Progress": Progress, "Age": Age, "Language": Language, "Residence": Residence, "PhoneNumber": PhoneNumber, "Email": Email, "Quality": _Quality, "LifeData": LifeData}
        if _Quality >= Quality:
            PreprocessedLifeGraphList.append(LifeGraphDic)
    # 라이프 그래프 날짜순으로 정리
    DateSortedPreprocessedLifeGraphList = sorted(PreprocessedLifeGraphList, key = lambda x: datetime.strptime(x["LifeGraphDate"], "%Y-%m-%d"), reverse=True)
    
    return DateSortedPreprocessedLifeGraphList

## 라이프그래프 데이터 다운로드 ##
def DownloadLifeGraph(AccountFilePath = '/yaas/storage/s2_Meditation/API_KEY/coursera-meditation-db-firebase-adminsdk-okrn4-80af02fd79.json', Quality = 0):
    # 저장경로 설정
    BeforeLifeGraphStorage = f'/yaas/storage/s2_Meditation/s21_BeforeStorage/s211_BeforeLifeGraph/'
    FileName = f'{Date()}_BeforeLifeGraph.json'
    BeforeLifeGraphPath = BeforeLifeGraphStorage + FileName
    if not os.path.exists(BeforeLifeGraphPath):
        # 서비스 계정
        SERVICE_ACCOUNT_FILE = AccountFilePath
        Credentials = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(Credentials, {'databaseURL': 'https://coursera-meditation-db.firebaseio.com/'})
        # 다운로드 및 JSON 파일 저장
        reference = db.reference('/')
        FirebaseJson = reference.get()
        BeforeLifeGraphList = PreprocessingLifeGraph(FirebaseJson, Quality)
        with open(BeforeLifeGraphPath, 'w', encoding = 'utf-8') as BeforeLifeGraphJson:
            json.dump(BeforeLifeGraphList, BeforeLifeGraphJson, ensure_ascii = False, indent = 4)
        print(f'[ 버전({Date()}) 라이프그래프 다운로드 : {FileName} ]')
        return BeforeLifeGraphList
    else:
        with open(BeforeLifeGraphPath, 'r', encoding = 'utf-8') as BeforeLifeGraphJson:
            BeforeLifeGraphList = json.load(BeforeLifeGraphJson)
        print(f'[ 현재 라이프그래프는 최신버전({Date()}) : {FileName} ]')
        return BeforeLifeGraphList

## 라이프그래프의 이미지화(PNG)
def LifeGraphToPNG(LifeGraphDate, Name, Age, Language, Email, LifeData):
    PNGPaths = []
    FilePath = f"/yaas/storage/s2_Meditation/s21_BeforeStorage/s211_BeforeLifeGraph/BeforeLifeGraphImages/"
    FileName = f"{LifeGraphDate.replace('-', '')}_{Name}({Age})_LifeGraph"
    PDFPath = FilePath + FileName + '.pdf'

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
    ax[0].set_title(f'{Email}\n{FileName}\n', fontweight = 'bold')
    ax[0].set_xlabel('\nAge', fontweight = 'bold')
    ax[0].set_ylabel('Happiness Score', fontweight = 'bold')
    # ax[0].legend().remove() # 범례 제거
    ax[0].set_yticks(range(-10, 11, 2)) # y축 눈금을 2단위로 설정
    ax[0].axhline(0, color='black', linewidth=0.5) # y=0 위치에 수평선 추가
    for index, row in DataFrame.iterrows():
        if {row['Score']} != 0:
            ax[0].text(index, row['Score'] / 2, str(row['Score']), color = 'white', ha = "center", weight = 'bold')

    # 하단 절반을 위한 텍스트 준비 (단어 줄바꿈 포함)
    if Language == 'en':
        Width = 70
    else:
        Width = 50
    WrappedTexts = []
    for index, row in DataFrame.iterrows():
        if row['LifeDataId'] <= 9:
            wrapped_text = "\n    ".join(textwrap.wrap(row['ReasonGlobal'], width = Width))
        else:
            wrapped_text = "\n      ".join(textwrap.wrap(row['ReasonGlobal'], width = Width))
        WrappedTexts.append(f"{row['LifeDataId']}. {row['StartAge']}-{row['EndAge']}: {wrapped_text}\n")
        
    # 첫 번째는 25개, 그 후에는 54개 단위로 묶기
    ReasonText = "\n".join(WrappedTexts)
    ReasonLines = ReasonText.split('\n')
    PagedReasonLines = [ReasonLines[:25]] + [ReasonLines[i:i+54] for i in range(25, len(ReasonLines), 54)]

    # 하단 텍스트
    ax[1].text(0.01, 0.99, "\n".join(PagedReasonLines[0]), wrap = True, horizontalalignment = 'left', verticalalignment = 'top', fontsize = 11, transform = ax[1].transAxes)
    ax[1].axis('off')  # 텍스트 영역의 축 숨기기

    # 첫번째 페이지 저장
    PNGPath = FilePath + FileName + '(1).png'
    PNGPaths.append(PNGPath)
    plt.savefig(PNGPath, dpi = 300)
    plt.close()
    
    # 두번째 페이지부터 저장
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

## 라이프그래프의 이미지를 PDF로 묶기
def PNGsToPDF(PNGPaths, PDFPath):
    # PDF로 저장
    A4Width, A4Height = A4
    pdf = canvas.Canvas(PDFPath, pagesize = A4)

    for PNGPath in PNGPaths:
        image = Image.open(PNGPath)
        # 이미지 크기 조정
        ImageWidth, ImageHeight = image.size
        AspectRatio = ImageWidth / ImageHeight
        if AspectRatio > 1:
            NewWidth = A4Width
            NewHeight = A4Width / AspectRatio
        else:
            NewHeight = A4Height
            NewWidth = A4Height * AspectRatio
        # 중앙에 이미지 배치
        x = (A4Width - NewWidth) / 2
        y = (A4Height - NewHeight) / 2
        # 이미지 크기 조정
        image = image.resize((int(NewWidth), int(NewHeight)), Image.LANCZOS)
        # 이미지를 PDF에 추가
        pdf.drawImage(PNGPath, x, y, width=NewWidth, height=NewHeight)
        pdf.showPage()
        # PDF로 저장된 PNG 파일 제거
        os.remove(PNGPath)
    pdf.save()

## 구글 스프레드 시트 업데이트
def UpdateSheet(AccountFilePath = '/yaas/storage/s2_Meditation/API_KEY/courserameditation-028871d3c653.json', ProjectName = 'Coursera Meditation Project', SheetName = 'sheet1', Type = 'Text', HeaderRow = 2, Row = 3, Colum = 1, Data = 'Hello', SubData = 'World!', FileName = 'None', FilePath = 'None', FolderId = '16SB0qJBhEwCugqOe_bV7QYecFj922u1J'):
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
    
## 구글 스프레드 시트에 라이프그래프 업데이트 ##
def UpdateBeforeLifeGraphToSheet(BeforeLifeGraphList):
    for i in tqdm(range(len(BeforeLifeGraphList)), desc = "Updating Life Graphs"):
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
        UpdateSheet(Row = row, Colum = 5, Data = Email)
        UpdateSheet(Row = row, Type = 'Link', Colum = 6, Data = PDFPath, SubData = f'({Name})의 라이프그래프 보기/다운로드', FileName = fileName, FilePath = PDFPath)

### 라이프 그래프 업데이트 ###
def LifeGraphUpdate():
    BeforeLifeGraphList = DownloadLifeGraph()
    UpdateBeforeLifeGraphToSheet(BeforeLifeGraphList)
    
if __name__ == "__main__":
    LifeGraphUpdate()