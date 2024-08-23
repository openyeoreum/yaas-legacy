import os
import re
import json
import csv
import gspread
import sys
sys.path.append("/yaas")

import pandas as pd

from datetime import datetime
from google.oauth2.service_account import Credentials

#########################
##### InputList 생성 #####
#########################
### 라이프그래프 데이터 로드 ###
def LoadLifeGraph():
    # 로드경로 설정
    BeforeLifeGraphStorage = '/yaas/storage/s2_Meditation/s21_BeforeStorage/s211_BeforeLifeGraph/s2111_BeforeLifeGraph/'
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

## 세미나 구글폼 불러오기
def LoadGoogleForm(ReactionYYMM, AccountFilePath = '/yaas/storage/s2_Meditation/API_KEY/courserameditation-028871d3c653.json', ProjectName = 'Coursera Meditation Project'):   
    SheetName = f"{ReactionYYMM}_GoogleForm"
    
    SERVICE_ACCOUNT_FILE = AccountFilePath
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes = SCOPES)
    client = gspread.authorize(credentials)
    # 스프레드시트 읽고 쓰기
    Sheet = client.open(ProjectName)
    worksheet = Sheet.worksheet(SheetName)
    
    # 스프레드시트 읽고 쓰기
    Sheet = client.open(ProjectName)
    worksheet = Sheet.worksheet(SheetName)
    
    # 워크시트 데이터를 가져와 JSON 형식으로 변환
    GoogleFormList = worksheet.get_all_records()  # 행 단위로 데이터 가져오기
    
    return GoogleFormList

## 세미나 구글폼 불러오기
def LoadReaction(ReactionYYMM):
    ReactionFolder = f'{ReactionYYMM}_reaction'
    EmailReactionsPath = f'/yaas/storage/s2_Meditation/s21_BeforeStorage/s211_BeforeLifeGraph/s2114_BeforeLifeGraphReaction/{ReactionFolder}'
    ReactionsPath = EmailReactionsPath + f"/{ReactionFolder}"
    # EmailReactionsPath가 존재하지 않으면 디렉토리 생성
    if not os.path.exists(ReactionsPath):
        os.makedirs(ReactionsPath)
    # 합칠 파일 이름들
    fileNames = ['전송', '수신거부', '발송실패', '발송성공', '오픈', '클릭']
    # 각 파일 별로 데이터를 결합
    FolderNameList = []
    for fileName in fileNames:
        CombinedReaction = pd.DataFrame()  # 빈 DataFrame 생성
        # 각 날짜별 폴더를 순회
        for FolderName in os.listdir(EmailReactionsPath):
            FolderPath = os.path.join(EmailReactionsPath, FolderName)
            if os.path.isdir(FolderPath):  # 폴더인 경우에만 진행
                if FolderName not in FolderNameList:
                    FolderNameList.append(FolderName)
                FilePath = os.path.join(FolderPath, fileName + '.csv')
                if os.path.exists(FilePath):  # 파일이 존재하는 경우
                    data = pd.read_csv(FilePath)  # CSV 파일 읽기
                    CombinedReaction = pd.concat([CombinedReaction, data], ignore_index = True)  # 데이터 결합

        # 결합된 데이터를 JSON 형식으로 최종 폴더에 저장
        CombinedFilePath = os.path.join(ReactionsPath, f"{ReactionFolder}_{fileName + '.json'}")
        CombinedReaction.to_json(CombinedFilePath, orient = 'records', force_ascii = False, indent = 4)  # JSON으로 저장
    print(f"[ {', '.join(FolderNameList)} 병합 완료 ]")

    ## 통합 json 데이터 구성
    # 발송 데이터 전체 로드 및 병합
    ReactionJson = []
    # 전송 로드
    with open(os.path.join(ReactionsPath, f"{ReactionFolder}_{fileNames[0] + '.json'}"), 'r', encoding = 'utf-8-sig') as Json:
        SendList = json.load(Json)
    for SendData in SendList:
        name = SendData['name']
        email = SendData['email']
        Reaction = '1_NoEmail'
        SendDic = {'Name': name, 'Email': email, 'EmailDate': None, 'Residence': None, 'PhoneNumber': None, 'Reaction': Reaction}
        ReactionJson.append(SendDic)
        
    # 수신거부 로드
    with open(os.path.join(ReactionsPath, f"{ReactionFolder}_{fileNames[1] + '.json'}"), 'r', encoding = 'utf-8-sig') as Json:
        UnsubscribeList = json.load(Json)
    for UnsubscribeData in UnsubscribeList:
        for ReactionData in ReactionJson:
            UnsubscribeDataEmail = UnsubscribeData['이메일 주소'].lower().replace(' ', '')
            ReactionDataEmail = ReactionData['Email'].lower().replace(' ', '')
            if UnsubscribeDataEmail == ReactionDataEmail:
                ReactionData['Reaction'] = '2_Unsubscribe'

    # 발송실패 로드
    with open(os.path.join(ReactionsPath, f"{ReactionFolder}_{fileNames[2] + '.json'}"), 'r', encoding = 'utf-8-sig') as Json:
        SendingFailureList = json.load(Json)
    for SendingFailureData in SendingFailureList:
        for ReactionData in ReactionJson:
            SendingFailureDataEmail = SendingFailureData['이메일 주소'].lower().replace(' ', '')
            ReactionDataEmail = ReactionData['Email'].lower().replace(' ', '')
            if SendingFailureDataEmail == ReactionDataEmail:
                ReactionData['EmailDate'] = SendingFailureData['발송완료일']
                ReactionData['Reaction'] = '3_SendingFailure'

    # 발송성공 로드
    with open(os.path.join(ReactionsPath, f"{ReactionFolder}_{fileNames[3] + '.json'}"), 'r', encoding = 'utf-8-sig') as Json:
        SentSuccessfullyList = json.load(Json)
    for SentSuccessfullyData in SentSuccessfullyList:
        for ReactionData in ReactionJson:
            SentSuccessfullyDataEmail = SentSuccessfullyData['이메일 주소'].lower().replace(' ', '')
            ReactionDataEmail = ReactionData['Email'].lower().replace(' ', '')
            if SentSuccessfullyDataEmail == ReactionDataEmail:
                ReactionData['EmailDate'] = SentSuccessfullyData['발송완료일']
                ReactionData['Reaction'] = '4_SentSuccessfully'
        
    # 오픈 로드
    with open(os.path.join(ReactionsPath, f"{ReactionFolder}_{fileNames[4] + '.json'}"), 'r', encoding = 'utf-8-sig') as Json:
        OpenList = json.load(Json)
    for OpenData in OpenList:
        for ReactionData in ReactionJson:
            OpenDataEmail = OpenData['이메일 주소'].lower().replace(' ', '')
            ReactionDataEmail = ReactionData['Email'].lower().replace(' ', '')
            if OpenDataEmail == ReactionDataEmail:
                ReactionData['Reaction'] = f"5_Open({OpenData['오픈(중복 포함)']})"
                
    # 클릭 로드
    with open(os.path.join(ReactionsPath, f"{ReactionFolder}_{fileNames[5] + '.json'}"), 'r', encoding = 'utf-8-sig') as Json:
        ClickList = json.load(Json)
    for ClickData in ClickList:
        for ReactionData in ReactionJson:
            ClickDataEmail = ClickData['이메일 주소'].lower().replace(' ', '')
            ReactionDataEmail = ReactionData['Email'].lower().replace(' ', '')
            if ClickDataEmail == ReactionDataEmail:
                ReactionData['Reaction'] = f"6_Click({ClickData['클릭(중복 포함)']})"
                
    # 구글폼 로드
    GoogleFormList = LoadGoogleForm(ReactionYYMM)
    # 조건을 만족하지 못하는 GoogleFormData는 별도로 저장
    UnMatchedGoogleFormData = []

    for GoogleFormData in GoogleFormList:
        matched = False  # 현재 GoogleFormData에 대해 조건이 일치했는지 추적하는 변수
        for ReactionData in ReactionJson:
            GoogleFormDataEmail = GoogleFormData['Email Address'].split('@')[0].lower().replace(' ', '')
            ReactionDataEmail = ReactionData['Email'].split('@')[0].lower().replace(' ', '')
            if GoogleFormDataEmail == ReactionDataEmail:
                ReactionData['Residence'] = GoogleFormData['Country of Residence']
                ReactionData['PhoneNumber'] = GoogleFormData['Phone Number (Including Country Code)\nex) +82 000 0000 0000']
                ReactionData['Reaction'] = "7_SubmitGoogleForm"
                matched = True  # 조건이 일치하면 matched를 True로 설정
        if not matched:
            UnMatchedGoogleFormData.append({'Name': GoogleFormData['Full Name'], "Residence": GoogleFormData['Country of Residence'], 'Email': GoogleFormData['Email Address'],  'PhoneNumber': GoogleFormData['Phone Number (Including Country Code)\nex) +82 000 0000 0000']})  # 조건이 일치하지 않은 경우에만 저장

    with open(os.path.join(ReactionsPath, f"{ReactionFolder}_종합.json"), 'w', encoding = 'utf-8') as jsonfile:
        json.dump(ReactionJson, jsonfile, ensure_ascii = False, indent = 4)
        
    print(f"[ ({len(UnMatchedGoogleFormData)})개의 구글폼 데이터가 전체 데이터베이스에 이메일 매칭 안됨 ]\n[ (코세라 데이터베이스)와 ({ReactionFolder}_구글폼매칭실패.json)를 직접 매칭해주세요. ]")
    with open(os.path.join(ReactionsPath, f"{ReactionFolder}_구글폼매칭실패.json"), 'w', encoding = 'utf-8') as json_file:
        json.dump(UnMatchedGoogleFormData, json_file, ensure_ascii = False, indent = 4)

    return EmailReactionsPath, ReactionJson

## 구글시트 업데이트
def UpdateSheet(ColumNames, CSVFilePath, AccountFilePath = '/yaas/storage/s2_Meditation/API_KEY/courserameditation-028871d3c653.json', ProjectName = 'Coursera Meditation Project', SheetName = 'BeforeLifeGraph'):
    # 서비스 계정
    SERVICE_ACCOUNT_FILE = AccountFilePath
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes = SCOPES)
    client = gspread.authorize(credentials)
    # 스프레드시트 읽고 쓰기
    Sheet = client.open(ProjectName)
    worksheet = Sheet.worksheet(SheetName)
    
    # 시트의 헤더(첫 번째 행) 가져오기
    SheetHeaders = worksheet.row_values(2)

    # CSV 파일에서 데이터 읽기
    with open(CSVFilePath, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        CSVData = list(reader)  # CSV 데이터
    
    _ColumNames = ColumNames[2:]
    # CSV 열 이름과 Google Sheets 열 이름을 매칭하여 업데이트
    for ColumName in _ColumNames:
        if ColumName in SheetHeaders:
            CSVColumnData = [row[ColumName] for row in CSVData]
            SheetColumnIndex = SheetHeaders.index(ColumName) + 1
            
            # Google Sheets의 3번째 행부터 업데이트 (CSV는 2번째 행부터 시작)
            CellRange = f'{chr(64+SheetColumnIndex)}3:{chr(64+SheetColumnIndex)}{len(CSVData)+2}'
            CellList = worksheet.range(CellRange)

            # CSV 데이터를 Google Sheets 셀에 할당
            for i, cell in enumerate(CellList):
                cell.value = CSVColumnData[i]

            # 업데이트 적용
            worksheet.update_cells(CellList)

    sys.exit()

### 라이프그래프 이메일 반응 ###
def LifeGraphReactionProcess(ReactionYYMM):
    BeforeLifeGraphList, RecentBeforeLifeGraphPath = LoadLifeGraph()
    EmailReactionsPath, ReactionJson = LoadReaction(ReactionYYMM)
    
    for ReactionData in ReactionJson:
        for BeforeLifeGraph in BeforeLifeGraphList:
            ReactionDataEmail = ReactionData['Email'].split('@')[0].lower().replace(' ', '')
            BeforeLifeGraphEmail = BeforeLifeGraph['Email'].split('@')[0].lower().replace(' ', '')
            if ReactionDataEmail == BeforeLifeGraphEmail:
                EmailDate = ReactionData['EmailDate']
                Residence = ReactionData['Residence']
                PhoneNumber = ReactionData['PhoneNumber']
                Reaction = ReactionData['Reaction']
                ReactionDic = {"EmailDate": EmailDate, "Residence": Residence, "PhoneNumber": PhoneNumber, "Reaction": Reaction}
                BeforeLifeGraph[f'{ReactionYYMM}_ReactionData'] = ReactionDic
    
    # BeforeLifeGraphList 최신화
    with open(RecentBeforeLifeGraphPath, 'w', encoding='utf-8') as BeforeLifeGraphJson:
        json.dump(BeforeLifeGraphList, BeforeLifeGraphJson, ensure_ascii = False, indent = 4)
    
    ## CSV 저장
    # CSV 파일로 저장할 파일명 설정
    CSVFileName = f'{ReactionYYMM}_reaction.csv'
    CSVFilePath = os.path.join(EmailReactionsPath, CSVFileName)

    # CSV 파일에 저장할 필드 이름 (컬럼 이름)
    ColumNames = ['row', 'name', 'residence(GF)', 'expected residence', 'pattern', 'negative', 'positive', 'phone number', 'send', f'{ReactionYYMM}_email']

    # CSV 파일 생성 및 데이터 쓰기
    with open(CSVFilePath, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = ColumNames)
        # CSV 파일에 헤더 쓰기
        writer.writeheader()
        # 데이터 쓰기
        for i in range(len(BeforeLifeGraphList)):
            ReactionDataDic = {
                'row': i,
                'name': None,
                'residence(GF)': None,
                'expected residence': None,
                'pattern': None,
                'negative': None,
                'positive': None,
                'phone number': None,
                'send': None,
                f'{ReactionYYMM}_email': None
            }
            
            ReactionDataDic['name'] = BeforeLifeGraphList[i]['Name']
            ReactionDataDic['expected residence'] = BeforeLifeGraphList[i]['Residence']
            ReactionDataDic['pattern'] = BeforeLifeGraphList[i]['Pattern']
            if BeforeLifeGraphList[i]['Negative'] is not None:
                ReactionDataDic['negative'] = ', '.join(BeforeLifeGraphList[i]['Negative'])
            if BeforeLifeGraphList[i]['Positive'] is not None:
                ReactionDataDic['positive'] = ', '.join(BeforeLifeGraphList[i]['Positive'])
            
            if f'{ReactionYYMM}_ReactionData' in BeforeLifeGraphList[i]:
                ReactionDataDic['residence(GF)'] = BeforeLifeGraphList[i][f'{ReactionYYMM}_ReactionData']['Residence']
                ReactionDataDic['phone number'] = BeforeLifeGraphList[i][f'{ReactionYYMM}_ReactionData']['PhoneNumber']
                ReactionDataDic['send'] = f'{ReactionYYMM} email'
                ReactionDataDic[f'{ReactionYYMM}_email'] = BeforeLifeGraphList[i][f'{ReactionYYMM}_ReactionData']['Reaction']
            
            # CSV 파일에 ReactionDataDic 추가
            writer.writerow(ReactionDataDic)
    
    UpdateSheet(ColumNames, CSVFilePath)
                
    print(f"[ {CSVFileName} 생성 및 구글시트 업데이트 완료 ]")

if __name__ == "__main__":
    ############################ 하이퍼 파라미터 설정 ############################
    email = "General"
    projectName = "Meditation"
    ReactionYYMM = "2408"
    #########################################################################
    LifeGraphReactionProcess(ReactionYYMM)
    
    # 1) 메일주소없음(1_NoEmail)
    # 2) 수신거부(2_Unsubscribe)
    # 3) 발송실패(3_SendingFailure)
    # 4) 발송성공(4_SentSuccessfully)
    # 5) 오픈(5_Open(n))
    # 6) 구글폼클릭[채널](6_Click(n))
    # 7) 구글폼작성(7_SubmitGoogleForm)
    # 8) 연락처없음(8_NoNumber)
    # 9) 연락(9_Contact)
    # 10) 세미나(10_Seminar)
    # 11) 격려(11_Encouragement)
    # 12) 등록(12_Registration)
    # 13) 과정(13_MeditationStage(n))
    # 14) 휴먼(14_OnBreak(yymmdd))