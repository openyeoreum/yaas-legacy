import os
import json
import time
import csv
import re
import random
import ast
import sys
sys.path.append("/yaas")

from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

## TotalPublisherData 수집된 출판사 데이터 추가
def TotalPublisherDataAddition(TotalPublisherDataJsonPath, TotalPublisherDataAdditionCSVPath):
    print(f"[ TotalPublisherDataAddition : 출판사 데이터 추가 시작 ]\n")
    # 도메인 추출 함수
    def ExtractDomain(HomepageUrl: str) -> str:
        if not HomepageUrl:
            return ""
        # 만약 http/https가 빠진 경우도 있을 수 있으니,
        # URL을 urlparse에 넣었을 때 netloc이 없으면 path를 확인합니다.
        parsed = urlparse(HomepageUrl)
        
        if parsed.netloc:  
            return parsed.netloc.strip().lower()  # lower()로 대소문자 통일
        else:
            # "www.yeoreum.me" 형태처럼 스킴 없이 적힌 경우
            # urlparse("www.yeoreum.me").netloc 은 빈 문자열, path에 "www.yeoreum.me"가 들어있음
            return parsed.path.strip().lower()

    # 1) JSON 파일 불러오기
    with open(TotalPublisherDataJsonPath, "r", encoding = "utf-8") as TotalPublisherDataJson:
        TotalPublisherData = json.load(TotalPublisherDataJson)

    # 2) JSON 내 중복검사를 위한 자료구조 생성
    ExistingEmails = set()
    ExistingHomepages = set()

    for entry in TotalPublisherData:
        publisher_info = entry.get("PublisherInformation", {})
        
        # Email 정보 수집
        EmailList = publisher_info.get("Email", [])
        for email in EmailList:
            # 공백 제거, 소문자 통일 등
            ExistingEmails.add(email.strip().lower())
        
        # HomePage 정보 수집
        homepage_str = publisher_info.get("HomePage", "").strip()
        # 홈페이지에 http://, https:// 등이 포함될 수 있으므로 도메인만 추출
        domain = ExtractDomain(homepage_str)
        if domain:
            ExistingHomepages.add(domain)

    # 3) CSV 파일 읽기 및 조건에 따라 필터링
    FilteredRows = []

    with open(TotalPublisherDataAdditionCSVPath, "r", encoding = "utf-8") as TotalPublisherDataAdditionCSV:
        TotalPublisherDataAddition = csv.DictReader(TotalPublisherDataAdditionCSV)
        # reader.fieldnames = ['출판사','홈페이지','이메일','담당자']
        for row in TotalPublisherDataAddition:
            publisher = row.get("출판사", "").strip()
            homepage = row.get("홈페이지", "").strip()
            email = row.get("이메일", "").strip()
            manager = row.get("담당자", "").strip()
            
            # (1) 홈페이지, 이메일 둘 다 없는 경우 스킵
            if (not homepage) and (not email):
                continue
            
            # 이메일/홈페이지 대소문자 통일
            EmailLower = email.lower()
            HomepageDomain = ExtractDomain(homepage)  # http/https 제거 후 도메인만
            
            # (2) 이메일이 JSON 기존 이메일과 중복되면 스킵
            if EmailLower and (EmailLower in ExistingEmails):
                continue
            
            # (3) 이메일이 없고 홈페이지만 있을 경우, 해당 홈페이지(도메인)가 기존과 중복이면 스킵
            if (not EmailLower) and HomepageDomain and (HomepageDomain in ExistingHomepages):
                continue
            
            # 조건을 통과하면 최종 리스트에 추가
            FilteredRows.append({
                "출판사": publisher,
                "홈페이지": homepage,
                "이메일": email,
                "담당자": manager
            })

    # 4) JSON에 합치기
    NewIdStart = max([entry["Id"] for entry in TotalPublisherData]) if TotalPublisherData else 0
    for i, row in enumerate(FilteredRows, start=1):
        NewId = NewIdStart + i
        
        NewEntry = {
            "Id": NewId,
            "PublisherInformation": {
                "Name": row["출판사"],
                "Classification": "출판사",
                "Subcategories": "",
                "Genre": "",
                "Adress": "",
                "ZipCode": "",
                "PhoneNumber": "",
                "HomePage": row["홈페이지"].strip() if row["홈페이지"] else "",
                "WebPageTXTPath": "",
                "Email": [row["이메일"].strip()] if row["이메일"] else "",
                "Manager": row["담당자"].strip(),
                "MainBooks": [],
                "AudioBooks": []
            },
            "MarketingChannel": "",
            "Project": [
                {
                    "Classification": "",
                    "ProjectName": "",
                    "Estimated": "",
                    "Sample": "",
                    "Contracted": "",
                    "Sales": 0
                }
            ],
            "TotalSales": 0,
            "Feedback": []
        }
        
        TotalPublisherData.append(NewEntry)

    # 5) 최종 JSON 파일로 저장
    with open(TotalPublisherDataJsonPath, "w", encoding = "utf-8") as TotalPublisherDataJson:
        json.dump(TotalPublisherData, TotalPublisherDataJson, ensure_ascii = False, indent = 4)
        
    # 6) CSV 파일 이름 변경
    date = datetime.now().strftime("%y%m%d")
    NewTotalPublisherDataAdditionName = f"TotalPublisherDataAddition({date}).csv"
    UpdatedTotalPublisherDataAdditionCSVPath = os.path.join(os.path.dirname(TotalPublisherDataAdditionCSVPath), NewTotalPublisherDataAdditionName)

    os.rename(TotalPublisherDataAdditionCSVPath, UpdatedTotalPublisherDataAdditionCSVPath)

    print(f"[ TotalPublisherDataAddition : 출판사 데이터 추가 완료 ]\n")
    print(f"[ CSV 파일 이름 변경 완료 : {NewTotalPublisherDataAdditionName} ]\n")

## SeleniumHubDrive 연결
def SeleniumHubDrive():
    print(f"[ SeleniumHubDrive : 출판사 홈페이지 연결 시도 ]\n")
    hub_url = "http://selenium:4444/wd/hub"
    options = Options()
    
    # 기본 옵션
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # 봇 감지 우회를 위한 추가 옵션
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--incognito')
    options.add_argument('--disable-automation')
    options.add_argument('--disable-notifications')
    options.add_argument('--start-maximized')
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # 일반적인 크롬 User-Agent 설정
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Remote(command_executor=hub_url, options=options)
    driver.delete_all_cookies()
    
    print(f"[ SeleniumHubDrive : 출판사 홈페이지 연결 완료 ]\n")
    return driver

## URL에 프로토콜이 없으면 https://를 추가
def ValidateAndFixUrl(url):
    if not url:
        return "None"
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

## 출판사 메인 페이지 Html 스크래퍼
def PublisherHtmlScraper(Driver, PublisherDataPath, Id, PublisherName, HomePage):
    try:
        # URL 검증 및 수정
        FixedUrl = ValidateAndFixUrl(HomePage)
        if not FixedUrl:
            print(f"< ({Id}) {PublisherName}: 유효하지 않은 URL({HomePage}) 입니다. >")
            return "None"
            
        print(f"< ({Id}) {PublisherName}: 접속 시도 URL - {FixedUrl} >")
        
        # 출판사 홈페이지 접속
        Driver.get(FixedUrl)
        time.sleep(random.uniform(5, 7))
        
        # 페이지 로드 확인
        WebDriverWait(Driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # 현재 시간을 파일명에 포함
        ScrapingTime = datetime.now().strftime("%Y%m%d%H%M%S")
        
        WebPageTxtDirName = "TotalPublisherDataTXT"
        WebPageTxtName = f"{ScrapingTime}_({Id}) {PublisherName}_WebPage.txt"
        WebPageTXTPath = os.path.join(PublisherDataPath, WebPageTxtDirName, WebPageTxtName)
        
        # HTML을 txt 파일로 저장
        with open(WebPageTXTPath, 'w', encoding='utf-8') as f:
            f.write(Driver.page_source)
            
        print(f"< ({Id}) {PublisherName}: 웹페이지 스크래핑 완료 >")
        return WebPageTXTPath
        
    except TimeoutException:
        print(f"< ({Id}) {PublisherName}: 페이지 로딩 시간 초과. 서버 응답이 없습니다. >")
        return "None"
    except NoSuchElementException:
        print(f"< ({Id}) {PublisherName}: 페이지 구조가 변경되었거나 필요한 요소를 찾을 수 없습니다. >")
        return "None"
    except Exception as e:
        print(f"< ({Id}) {PublisherName}: 예상치 못한 에러 발생 - {str(e)} >")
        print(f"< 시도한 URL: {HomePage} -> {FixedUrl} >")
        return "None"
    
## 출판사 메인페이지 정보 스크래퍼
def PublisherWebScraper(PublisherDataPath, TotalPublisherDataJsonPath):
    ## TotalPublisherDataJson 로드
    with open(TotalPublisherDataJsonPath, 'r', encoding = 'utf-8') as PublisherJson:
        TotalPublisherData = json.load(PublisherJson)
    if TotalPublisherData[-1]['PublisherInformation']['WebPageTXTPath'] == "":
        ## SeleniumHubDrive 연결
        Driver = SeleniumHubDrive()

        ## 출판사 홈페이지 스크래퍼
        ScrapCounter = 0  # 카운터 변수 추가
        for i in range(len(TotalPublisherData)):
            if TotalPublisherData[i]['PublisherInformation']['WebPageTXTPath'] == "" and TotalPublisherData[i]['PublisherInformation']['HomePage'] != "":
                Id = TotalPublisherData[i]['Id']
                PublisherName = TotalPublisherData[i]['PublisherInformation']['Name']
                HomePage = TotalPublisherData[i]['PublisherInformation']['HomePage']
                WebPageTXTPath = PublisherHtmlScraper(Driver, PublisherDataPath, Id, PublisherName, HomePage)
                TotalPublisherData[i]['PublisherInformation']['WebPageTXTPath'] = WebPageTXTPath

                ## 10회 마다 저장
                ScrapCounter += 1
                if ScrapCounter % 10 == 0:
                    with open(TotalPublisherDataJsonPath, 'w', encoding = 'utf-8') as PublisherJson:
                        json.dump(TotalPublisherData, PublisherJson, ensure_ascii = False, indent = 4)

        if ScrapCounter % 10 != 0:
            with open(TotalPublisherDataJsonPath, 'w', encoding = 'utf-8') as PublisherJson:
                json.dump(TotalPublisherData, PublisherJson, ensure_ascii = False, indent = 4)

        ## SeleniumHubDrive 종료
        Driver.quit()

    return TotalPublisherDataJsonPath, TotalPublisherData

## 출판사 스크랩 데이터에서 중요 부분만 남기기
def ExtractingHtml(WebPageTXTPath):
    ## Html 파일 읽기
    with open(WebPageTXTPath, 'r', encoding = 'utf-8') as file:
        content = file.read()
    ## HTML에서 한글과 이메일 주변 텍스트 추출(태그 제거)
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text()

    ## 1. 한글 추출
    KoreanPattern = re.compile('[가-힣]+')
    KoreanText = ' '.join(KoreanPattern.findall(text))
    # 연속된 줄바꿈을 최대 2개로 제한
    KoreanText = re.sub(r'\n{3,}', '\n\n', KoreanText)
    # 각 줄의 좌우 공백만 제거하되 줄바꿈은 유지
    KoreanText = '\n'.join(line.strip() for line in KoreanText.splitlines(True))
    # 연속된 공백을 하나로 통일
    KoreanText = re.sub(r'\s+', ' ', KoreanText)
    # 한글 텍스트 저장
    WebPageKoreanTxtPath = f"{WebPageTXTPath.rsplit('.', 1)[0]}_Extract.txt"
    with open(WebPageKoreanTxtPath, 'w', encoding = 'utf-8') as f:
        f.write(KoreanText)
    
    ## 2. 이메일 텍스트 추출
    EmailPattern = re.compile(r'[a-zA-Z0-9]+[a-zA-Z0-9._%+-]*[a-zA-Z0-9]+@[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})+')
    EmailText = EmailPattern.finditer(text)
    EmailText = [match.group() for match in EmailText]
    # 중복 제거
    EmailText = list(set(EmailText))
    
    return EmailText

## Name, Email 데이터를 CSV로 저장
def SaveEmailToCSV(TotalPublisherData, TotalPublisherDataCSVPath, ChunkSize = 500):
    os.makedirs(TotalPublisherDataCSVPath, exist_ok = True)

    # 1) 모든 (Name, Email) 쌍을 'flatten' 형태로 수집할 리스트
    FlattenedData = []

    for item in TotalPublisherData:
        name = item["PublisherInformation"].get("Name", "")
        email = item["PublisherInformation"].get("Email", "")
        if email == ['']:
            email = []

        # 이메일이 비어있지 않은 경우만 처리
        if email:
            # 하나의 Name에 여러 이메일이 있을 경우 -> 각각 flatten_data에 추가
            for e_mail in email:
                FlattenedData.append((name, e_mail))
    # 2) 최대 500행씩 CSV 저장
    # FlattenedData는 이미 (Name, Email) 쌍으로 '한 행에 들어갈 데이터'가 준비된 상태
    for start_idx in range(0, len(FlattenedData), ChunkSize):
        end_idx = start_idx + ChunkSize
        chunk = FlattenedData[start_idx:end_idx]

        # 파일명 생성 (ex: 1_PublisherEmail(500).csv)
        FileIndex = (start_idx // ChunkSize) + 1
        NumChunk = len(chunk)
        CSVFileName = f"{FileIndex}_PublisherEmail({NumChunk}).csv"
        CSVFilePath = os.path.join(TotalPublisherDataCSVPath, CSVFileName)

        # CSV 파일 쓰기
        with open(CSVFilePath, 'w', encoding = 'utf-8', newline = '') as csvfile:
            writer = csv.writer(csvfile)
            # 헤더 작성
            writer.writerow(["Name", "Email"])

            # 실제 데이터 작성 (chunk에 들어있는 (Name, Email) 쌍)
            for name, e in chunk:
                writer.writerow([name, e])

    print(f"[ SaveEmaiToCSV : ({CSVFileName})까지 저장 완료 ]")
        
## 출판사 이메일 및 메인페이지 정보 스크래퍼
def PublisherDataUpdate():
    print(f"[ 출판사 이메일 및 메인페이지 정보 스크래핑 시작 ]\n")
    
    PublisherDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s152_TargetData/s1522_PublisherData/s15221_TotalPublisherData"
    TotalPublisherDataCSVPath = os.path.join(PublisherDataPath, "TotalPublisherDataCSV")
    TotalPublisherDataJsonPath = os.path.join(PublisherDataPath, "TotalPublisherData.json")
    TotalPublisherDataAdditionCSVPath = os.path.join(PublisherDataPath, "TotalPublisherDataAddition", "TotalPublisherDataAddition.csv")
    
    ## TotalPublisherData 수집된 출판사 데이터 추가(TotalPublisherDataAddition.csv가 존재할때)
    if os.path.exists(TotalPublisherDataAdditionCSVPath):
        TotalPublisherDataAddition(TotalPublisherDataJsonPath, TotalPublisherDataAdditionCSVPath)
    else:
        print(f"\n[ TotalPublisherDataAddition : 새로운 출판사 이메일 추가가 필요하면 아래 경로에 csv파일을 추가해주세요. ]\n{TotalPublisherDataAdditionCSVPath}\n\n1. yymmdd_TotalPublisherData.json 파일로 최신화 할 경우 해당 파일을 출판사, 홈페이지, 이메일, 담당자 열로 분리하여 csv파일로 저장해주세요.\n2. 저장 후 yymmdd_TotalPublisherData.json에서 csv로 변환된 딕셔너리는 삭제해주세요.\n3. csv파일을 TotalPublisherDataAddition 폴더에 넣어주세요.\n4. 스크립트를 실행하면 자동으로 TotalPublisherData.json에 추가됩니다.\n5. csv파일은 TotalPublisherDataAddition 폴더에 TotalPublisherDataAddition(yymmdd).csv로 저장됩니다.\n6. 이후 스크립트는 자동으로 TotalPublisherData.json에 추가된 출판사 정보를 업데이트합니다.\n7. yymmdd_TotalPublisherData.json는 다시 남은 딕셔너리부터 수집하면 됩니다.")
        
    ## 출판사 이메일 및 메인페이지 정보 스크래핑
    TotalPublisherDataJsonPath, TotalPublisherData = PublisherWebScraper(PublisherDataPath, TotalPublisherDataJsonPath)
    print(f"[ 출판사 이메일 및 메인페이지 정보 업데이트 시작 ]\n")
    ## 기존 토탈 데이터셋
    if TotalPublisherData[-1]['PublisherInformation']['Email'] != "":
        print(f"[ 출판사 이메일 및 메인페이지 정보 스크래핑 & 업데이트 완료 ]\n")
    else:
        for i in range(len(TotalPublisherData)):
            Id = TotalPublisherData[i]['Id']
            Name = TotalPublisherData[i]['PublisherInformation']['Name']
            WebPageTXTPath = TotalPublisherData[i]['PublisherInformation']['WebPageTXTPath']
            if WebPageTXTPath != "None":
                EmailText = ExtractingHtml(WebPageTXTPath)
                if TotalPublisherData[i]['PublisherInformation']['Email'] == "":
                    TotalPublisherData[i]['PublisherInformation']['Email'] = EmailText
                else:
                    TotalPublisherData[i]['PublisherInformation']['Email'] += EmailText
            elif WebPageTXTPath == "None":
                if TotalPublisherData[i]['PublisherInformation']['Email'] == "":
                    TotalPublisherData[i]['PublisherInformation']['Email'] = []
            elif WebPageTXTPath == "":
                break
        ## 출판사 이메일 업데이트 사항 저장
        with open(TotalPublisherDataJsonPath, 'w', encoding = 'utf-8') as PublisherJson:
            json.dump(TotalPublisherData, PublisherJson, ensure_ascii = False, indent = 4)
            
        print(f"[ ({Id}) ({Name}) 출판사까지 이메일 및 메인페이지 정보 스크래핑 & 업데이트 완료 ]\n")
    
    ## Name, Email 데이터를 CSV로 저장
    SaveEmailToCSV(TotalPublisherData, TotalPublisherDataCSVPath)
    

if __name__ == "__main__":
    
    PublisherDataUpdate()