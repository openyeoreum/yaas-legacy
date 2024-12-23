import os
import json
import time
import re
import random
import math
import sys
sys.path.append("/yaas")

from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
        
        WebPageTxtDirName = "TotalPublisherData"
        WebPageTxtName = f"{ScrapingTime}_({Id}) {PublisherName}_WebPage.txt"
        WebPageTxtPath = os.path.join(PublisherDataPath, WebPageTxtDirName, WebPageTxtName)
        
        # HTML을 txt 파일로 저장
        with open(WebPageTxtPath, 'w', encoding='utf-8') as f:
            f.write(Driver.page_source)
            
        print(f"< ({Id}) {PublisherName}: 웹페이지 스크래핑 완료 >")
        return WebPageTxtPath
        
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
def PublisherWebScraper(PublisherDataPath):
    ## TotalPublisherDataJson 로드
    TotalPublisherDataJsonName = "TotalPublisherData.json"
    TotalPublisherDataJsonPath = os.path.join(PublisherDataPath, TotalPublisherDataJsonName)
    with open(TotalPublisherDataJsonPath, 'r', encoding = 'utf-8') as PublisherJson:
        TotalPublisherData = json.load(PublisherJson)
    
    ## SeleniumHubDrive 연결
    Driver = SeleniumHubDrive()
    
    ## 출판사 홈페이지 스크래퍼
    ScrapCounter = 0  # 카운터 변수 추가
    for i in range(len(TotalPublisherData)):
        if TotalPublisherData[i]['CustomerInformation']['WebPageTxtPath'] == "":
            Id = TotalPublisherData[i]['Id']
            PublisherName = TotalPublisherData[i]['CustomerInformation']['Name']
            HomePage = TotalPublisherData[i]['CustomerInformation']['HomePage']
            WebPageTxtPath = PublisherHtmlScraper(Driver, PublisherDataPath, Id, PublisherName, HomePage)
            TotalPublisherData[i]['CustomerInformation']['WebPageTxtPath'] = WebPageTxtPath
            
            ## 5회 마다 저장
            ScrapCounter += 1
            if ScrapCounter % 5 == 0:
                with open(TotalPublisherDataJsonPath, 'w', encoding = 'utf-8') as PublisherJson:
                    json.dump(TotalPublisherData, PublisherJson, ensure_ascii = False, indent = 4)

    if ScrapCounter % 5 != 0:
        with open(TotalPublisherDataJsonPath, 'w', encoding = 'utf-8') as PublisherJson:
            json.dump(TotalPublisherData, PublisherJson, ensure_ascii = False, indent = 4)

    ## SeleniumHubDrive 종료
    Driver.quit()

    return TotalPublisherDataJsonPath, TotalPublisherData

## 출판사 스크랩 데이터에서 중요 부분만 남기기
def ExtractingHtml(WebPageTxtPath):
    ## Html 파일 읽기
    with open(WebPageTxtPath, 'r', encoding = 'utf-8') as file:
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
    WebPageKoreanTxtPath = f"{WebPageTxtPath.rsplit('.', 1)[0]}_Extract.txt"
    with open(WebPageKoreanTxtPath, 'w', encoding = 'utf-8') as f:
        f.write(KoreanText)
    
    ## 2. 이메일 텍스트 추출
    EmailPattern = re.compile(r'[a-zA-Z0-9]+[a-zA-Z0-9._%+-]*[a-zA-Z0-9]+@[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})+')
    EmailText = EmailPattern.finditer(text)
    EmailText = [match.group() for match in EmailText]
    
    return EmailText

## 출판사 이메일 및 메인페이지 정보 스크래퍼
def TotalPublisherDataUpdate():
    print(f"[ 출판사 이메일 및 메인페이지 정보 스크래핑 시작 ]\n")
    
    ## 출판사 이메일 및 메인페이지 정보 스크래핑
    PublisherDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_TargetData/s1512_PublisherData/s15121_TotalPublisherData"
    TotalPublisherDataJsonPath, TotalPublisherData = PublisherWebScraper(PublisherDataPath)
    print(f"[ 출판사 이메일 및 메인페이지 정보 업데이트 시작 ]\n")
    ## 기존 토탈 데이터셋
    if TotalPublisherData[-1]['CustomerInformation']['Email'] != "":
        
        print(f"[ 출판사 이메일 및 메인페이지 정보 스크래핑 & 업데이트 완료 ]\n")
    
    else:
        for i in range(len(TotalPublisherData)):
            Id = TotalPublisherData[i]['Id']
            Name = TotalPublisherData[i]['CustomerInformation']['Name']
            WebPageTxtPath = TotalPublisherData[i]['CustomerInformation']['WebPageTxtPath']
            Email = TotalPublisherData[i]['CustomerInformation']['Email']
            if Email == "":
                if WebPageTxtPath != "None":
                    EmailText = ExtractingHtml(WebPageTxtPath)
                    TotalPublisherData[i]['CustomerInformation']['Email'] = EmailText
                elif WebPageTxtPath == "None":
                    TotalPublisherData[i]['CustomerInformation']['Email'] = []
                elif WebPageTxtPath == "":
                    break
        ## 출판사 이메일 업데이트 사항 저장
        with open(TotalPublisherDataJsonPath, 'w', encoding = 'utf-8') as PublisherJson:
            json.dump(TotalPublisherData, PublisherJson, ensure_ascii = False, indent = 4)
            
        print(f"[ ({Id}) ({Name}) 출판사까지 이메일 및 메인페이지 정보 스크래핑 & 업데이트 완료 ]\n")

if __name__ == "__main__":
    
    TotalPublisherDataUpdate()