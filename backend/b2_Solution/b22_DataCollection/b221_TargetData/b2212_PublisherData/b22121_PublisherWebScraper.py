import os
import json
import time
import re
import random
import math
import sys
sys.path.append("/yaas")

from datetime import datetime
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

## 출판사 홈페이지 스크래퍼
def PublisherScraper(Driver, PublisherDataPath, Id, PublisherName, HomePage):
    try:
        # URL 검증 및 수정
        FixedUrl = ValidateAndFixUrl(HomePage)
        if not FixedUrl:
            print(f"[ ({Id}) {PublisherName}: 유효하지 않은 URL({HomePage}) 입니다. ]")
            return "None"
            
        print(f"[ ({Id}) {PublisherName}: 접속 시도 URL - {FixedUrl} ]")
        
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
            
        print(f"[ ({Id}) {PublisherName}: 웹페이지 스크래핑 완료 ]")
        return WebPageTxtPath
        
    except TimeoutException:
        print(f"[ ({Id}) {PublisherName}: 페이지 로딩 시간 초과. 서버 응답이 없습니다. ]")
        return "None"
    except NoSuchElementException:
        print(f"[ ({Id}) {PublisherName}: 페이지 구조가 변경되었거나 필요한 요소를 찾을 수 없습니다. ]")
        return "None"
    except Exception as e:
        print(f"[ ({Id}) {PublisherName}: 예상치 못한 에러 발생 - {str(e)} ]")
        print(f"[ 시도한 URL: {HomePage} -> {FixedUrl} ]")
        return "None"
    
## 교보문고 베스트셀러 스크래퍼
def BestsellerWebScraper(PublisherDataPath):
    ## TotalPublisherDataJson 로드
    TotalPublisherDataJsonName = "TotalPublisherData.json"
    TotalPublisherDataJsonPath = os.path.join(PublisherDataPath, TotalPublisherDataJsonName)
    with open(TotalPublisherDataJsonPath, 'r', encoding = 'utf-8') as json_file:
        TotalPublisherData = json.load(json_file)
    
    ## SeleniumHubDrive 연결
    Driver = SeleniumHubDrive()
    
    ## 출판사 홈페이지 스크래퍼
    for i in range(len(TotalPublisherData)):
        if TotalPublisherData[i]['CustomerInformation']['WebPageTxtPath'] == "":
            Id = TotalPublisherData[i]['Id']
            PublisherName = TotalPublisherData[i]['CustomerInformation']['Name']
            HomePage = TotalPublisherData[i]['CustomerInformation']['HomePage']
            WebPageTxtPath = PublisherScraper(Driver, PublisherDataPath, Id, PublisherName, HomePage)
            TotalPublisherData[i]['CustomerInformation']['WebPageTxtPath'] = WebPageTxtPath
            with open(TotalPublisherDataJsonPath, 'w', encoding='utf-8') as json_file:
                json.dump(TotalPublisherData, json_file, ensure_ascii = False, indent = 4)
    
    ## SeleniumHubDrive 종료
    Driver.quit()
    
    return TotalPublisherData

## 교보문고 베스트셀러 스크래퍼
def TotalPublisherDataUpdate():
    ## TotalPublisherDataJson 경로
    PublisherDataPath = "/yaas/storage/s1_Yeoreum/s15_DataCollectionStorage/s151_TargetData/s1512_PublisherData/s15121_TotalPublisherData"
    print(f"[ 출판사 메일 스크래핑 시작 ]\n")
    
    ## 베스트셀러 도서 스크래핑
    TotalPublisherData = BestsellerWebScraper(PublisherDataPath)
    print(f"[ TotalPublisherData 업데이트 시작 ]\n")
    # ## 기존 토탈 데이터셋
    
    # if os.path.exists(TotalBookDataPath):
    #     with open(TotalBookDataPath, 'r', encoding = 'utf-8') as BooksJson:
    #         TotalBookDataList = json.load(BooksJson)

    #     ## 토탈 데이터셋 ISBNList 구축
    #     TotalBookDataISBNList = []
    #     for TotalBookData in TotalBookDataList:
    #         TotalBookDataISBNList.append(TotalBookData['ISBN'])
        
    #     ## 스크래핑 데이터의 토탈 데이터셋 업데이트
    #     for BookData in BookDataList:
    #         Update = True
    #         if BookData['ISBN'] in TotalBookDataISBNList:
    #             Update = False
    #             Id = TotalBookDataISBNList.index(BookData['ISBN'])
    #         if Update:
    #             TotalBookDataList.append(BookData)
    #         else:
    #             # Date 추가
    #             if BookData['Rank'][0] not in TotalBookDataList[Id]['Rank']:
    #                 TotalBookDataList[Id]['Rank'] += BookData['Rank']
    #             TotalBookDataList[Id]['BookPurchasedList'] = BookData['BookPurchasedList']
    #             TotalBookDataList[Id]['CommentsCount'] = BookData['CommentsCount']

    #     with open(TotalBookDataPath, 'w', encoding = 'utf-8') as BooksJson:
    #         json.dump(TotalBookDataList, BooksJson, ensure_ascii = False, indent = 4)
    # else:
    #     with open(TotalBookDataPath, 'w', encoding = 'utf-8') as BooksJson:
    #         json.dump(BookDataList, BooksJson, ensure_ascii = False, indent = 4)

    # print(f"[ {period} 베스트셀러 도서 스크래핑 & 업데이트 완료 ]\n")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################

    #########################################################################
    TotalPublisherDataUpdate()