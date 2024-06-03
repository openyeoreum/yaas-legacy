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
import sys
sys.path.append("/yaas")

from datetime import datetime
from langdetect import detect
from google.oauth2.service_account import Credentials
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
    RawLifeGraph = list(FirebaseJson.items())
    # 라이프 그래프 전처리
    DatePattern = re.compile(r"\d{4}-\d{2}-\d{2}")
    PreprocessedLifeGraph = []
    for i in range(len(RawLifeGraph)):
        LifeGraphId = i + 1
        LifeGraphDate = DatePattern.search(RawLifeGraph[i][1]['graph_url']).group()
        Name = RawLifeGraph[i][0].strip()
        Progress = None
        Age = RawLifeGraph[i][1]['age']
        Residence = None
        PhoneNumber = None
        Email = RawLifeGraph[i][1]['email']
        LifeData = []
        LifeDataReasons = []
        QualityCount = 0
        for j in range(len(RawLifeGraph[i][1]['lifeData'])):
            LifeDataId = j + 1
            StartAge = RawLifeGraph[i][1]['lifeData'][j]['startAge']
            EndAge = RawLifeGraph[i][1]['lifeData'][j]['endAge']
            Score = RawLifeGraph[i][1]['lifeData'][j]['score']
            ReasonGlobal = RawLifeGraph[i][1]['lifeData'][j]['reason']
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
        
        LifeGraphDic = {"LifeGraphId": LifeGraphId, "LifeGraphDate": LifeGraphDate, "Name": Name, "Progress": Progress, "Age": Age, "Language": Language, "Residence": Residence, "PhoneNumber": PhoneNumber, "Email": Email, "Quality": _Quality, "LifeData": LifeData}
        if _Quality >= Quality:
            PreprocessedLifeGraph.append(LifeGraphDic)
    # 라이프 그래프 날짜순으로 정리
    DateSortedPreprocessedLifeGraph = sorted(PreprocessedLifeGraph, key = lambda x: datetime.strptime(x["LifeGraphDate"], "%Y-%m-%d"), reverse=True)
    
    return DateSortedPreprocessedLifeGraph

## 라이프그래프 데이터 다운로드
def DownloadLifeGraph(AccountFilePath = '/yaas/storage/s2_Meditation/API_KEY/coursera-meditation-db-firebase-adminsdk-okrn4-80af02fd79.json', Quality = 0):
    # 저장경로 설정
    BeforeLifeGraphStorage = f'/yaas/storage/s2_Meditation/s21_BeforeStorage/s211_BeforeLifeGraph/'
    FileName = f'{Date()}_BeforeLifesGraph.json'
    BeforeLifeGraphPath = BeforeLifeGraphStorage + FileName
    if not os.path.exists(BeforeLifeGraphPath):
        # 서비스 계정
        SERVICE_ACCOUNT_FILE = AccountFilePath
        Credentials = credentials.Certificate(SERVICE_ACCOUNT_FILE)
        firebase_admin.initialize_app(Credentials, {'databaseURL': 'https://coursera-meditation-db.firebaseio.com/'})
        # 다운로드 및 JSON 파일 저장
        reference = db.reference('/')
        FirebaseJson = reference.get()
        LifeGraph = PreprocessingLifeGraph(FirebaseJson, Quality)
        with open(BeforeLifeGraphPath, 'w', encoding = 'utf-8') as BeforeLifeGraphJson:
            json.dump(LifeGraph, BeforeLifeGraphJson, ensure_ascii = False, indent = 4)
        print(f'[ 버전({Date()}) 라이프그래프 다운로드 : {FileName} ]')
    print(f'[ 현재 라이프그래프는 최신버전({Date()}) : {FileName} ]')
    
    return LifeGraph

## 구글 스프레드 시트 업데이트
def UpdateSheet(AccountFilePath = '/yaas/storage/s2_Meditation/API_KEY/courserameditation-028871d3c653.json', FileName = 'Coursera Meditation Project', SheetName = 'sheet1', HeaderRow = 2, Row = 3, Colum = 1, Data = 'Hello, World!'):
    # 서비스 계정
    SERVICE_ACCOUNT_FILE = AccountFilePath
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes = SCOPES)
    client = gspread.authorize(credentials)
    # 읽고 쓰기
    Sheet = client.open(FileName)
    worksheet = Sheet.worksheet(SheetName)
    worksheet.get_all_records(head = HeaderRow)
    worksheet.update_cell(Row, Colum, Data)
    
## 구글 스프레드 시트에 라이프그래프 업데이트

if __name__ == "__main__":
    # DataToSheet()
    DownloadLifeGraph()