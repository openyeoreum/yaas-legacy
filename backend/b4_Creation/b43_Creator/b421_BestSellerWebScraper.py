import os
import json
import time
import re
import random
import sys
sys.path.append("/yaas")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

## SeleniumHubDrive 연결
def SeleniumHubDrive():
    print(f"[ SeleniumHubDrive 연결 시도 ]\n")
    hub_url = "http://selenium:4444/wd/hub"
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Remote(command_executor=hub_url, options=options)
    print(f"[ SeleniumHubDrive 연결 완료 ]\n")
    return driver

## BookElement 강제 클릭
def ClickBookElement(driver, wait, BookXpaths):
    for Xpath in BookXpaths:
        try:
            BookElement = wait.until(EC.element_to_be_clickable((By.XPATH, Xpath)))
            time.sleep(1)
            driver.execute_script("arguments[0].scrollIntoView(true);", BookElement)
            time.sleep(2)
            driver.execute_script("arguments[0].click();", BookElement)  # 강제 클릭
            return True
        except Exception as e:
            print(f"< {Xpath} 클릭에 실패, 재시도 : {e} >")
            time.sleep(1)
    return False

## ClassName기반 스크랩
def ClassNameScrape(wait, ClassName, childClassName = None):
    DataList = []
    try:
        if childClassName is None:
            Datas = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, ClassName)))
            for Data in Datas:
                DataList.append(Data.text)
        else:
            Datas = wait.until(EC.presence_of_all_elements_located((By.XPATH, f"//*[@class='{ClassName}']//*[@class='{childClassName}']")))
            for Data in Datas:
                DataList.append(Data.text)
        return DataList
    except (TimeoutException, NoSuchElementException):
        return DataList

## DataList의 텍스트 변환
def DataListToDataText(DataList, DataText):
    if DataList != []:
        DataList = DataText
    else:
        DataList = None
    return DataList

## 도서상세정보 스크랩
def BookDetailsScraper(Rank, Date, driver, wait):
    # 페이지가 로드될 때까지 대기
    wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/header/div[2]/div")))

    ## ISBN
    ISBN = ClassNameScrape(wait, "tbl_row_wrap")
    ISBN = DataListToDataText(ISBN, re.search(r'ISBN (\d+)', ISBN[0]).group(1) if ISBN else ISBN)
    ## 도서제목
    Title = ClassNameScrape(wait, "prod_title_area", "prod_title")
    Title = DataListToDataText(Title, Title[0] if Title else Title)
    ## 작가
    Author = ClassNameScrape(wait, "author")
    Author = DataListToDataText(Author, Author[0] if Author else Author)
    ## 작가정보
    AuthorInfo = ClassNameScrape(wait, "writer_info_box", "info_text")
    AuthorInfo = DataListToDataText(AuthorInfo, '\n'.join(AuthorInfo) if AuthorInfo else AuthorInfo)        
    ## 출판사, 발행일
    PublishedData = ClassNameScrape(wait, "prod_info_text.publish_date")
    PublishedData = DataListToDataText(PublishedData, PublishedData[0].split(" · ") if PublishedData else PublishedData)
    try:
        Publish = PublishedData[0]
    except:
        Publish = None
    try:
        PublishedDate = PublishedData[1]
    except:
        PublishedDate = None
    ## 도서 카테고리
    IntroCategory = ClassNameScrape(wait, "intro_category_list")
    IntroCategory = DataListToDataText(IntroCategory, IntroCategory[0].split(" > ") if IntroCategory else IntroCategory)
    ## 책소개(인트로)
    Intro = ClassNameScrape(wait, "intro_bottom")
    Intro = DataListToDataText(Intro, Intro[0] if Intro else Intro)
    ## 목차
    BookIndex = ClassNameScrape(wait, "book_contents_item")
    BookIndex = DataListToDataText(BookIndex, BookIndex[0] if BookIndex else BookIndex)
    ## 도서정보(리뷰)
    BookReviews = ClassNameScrape(wait, "product_detail_area.book_publish_review")
    BookReviews = DataListToDataText(BookReviews, BookReviews[0].replace('\n펼치기', '') if BookReviews else BookReviews)
    ## 함께 구매한 책들
    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.prod_info.purchase_together_item')))
        BookPurchaseds = driver.find_elements(By.CSS_SELECTOR, '.prod_info.purchase_together_item')
        BookPurchasedList = []
        for BookPurchased in BookPurchaseds:
            prod_name = BookPurchased.get_attribute('data-product-name')
            prod_author = BookPurchased.get_attribute('data-product-author')
            BookPurchasedList.append({"title": prod_name, "author": prod_author})
    except:
        BookPurchasedList = []
    ## 구매리뷰
    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.comment_list .comment_item')))
        Comments = driver.find_elements(By.CSS_SELECTOR, '.comment_list .comment_item')
        CommentList = []
        for Comment in Comments:
            comment_text = Comment.find_element(By.CSS_SELECTOR, '.comment_text').text
            btn_like = Comment.find_element(By.CSS_SELECTOR, '.btn_like').text
            CommentList.append({"comment": comment_text, "like": btn_like})
    except:
        CommentList = []
    
    return {"Rank": Rank, "Date": Date, "ISBN": ISBN, "Title": Title, "Author": Author, "AuthorInfo": AuthorInfo, "Publish": Publish, "PublishedDate": PublishedDate, "IntroCategory": IntroCategory, "Intro": Intro, "BookIndex": BookIndex, "BookReviews": BookReviews, "BookPurchasedList": BookPurchasedList, "CommentList": CommentList}

## 교보문고 베스트셀러 스크래퍼
def BestsellerScraper(driver, period = 'Weekly'):
    BookDataList = []
    LastRank = 0
    EndSwitch = False
    wait = WebDriverWait(driver, 10)
    # period 값에 따른 페이지 설정
    if period == 'Weekly':
        Period = '002'
        BookDataPath = "/yaas/storage/s1_Yeoreum/s18_MarketDataStorage/s181_BookData/s1811_WeeklyBookData/"
    elif period == 'Monthly':
        Period = '003'
        BookDataPath = "/yaas/storage/s1_Yeoreum/s18_MarketDataStorage/s181_BookData/s1812_MonthlyBookData/"
    elif period == 'Yearly':
        Period = '004'
        BookDataPath = "/yaas/storage/s1_Yeoreum/s18_MarketDataStorage/s181_BookData/s1813_YearlyBookData/"

    # 기존 파일 확인 후 스크래핑 시작 페이지와 파일번호 설정 (i, j)
    driver.get(f"https://product.kyobobook.co.kr/bestseller/total?period={Period}#?page=1&per=50") # period=002(주간), period=003(월간), period=004(연간)
    time.sleep(random.uniform(5, 7))
    DateXpath = "/html/body/div[3]/main/section[2]/div/section/div[2]/div/div[2]/div[1]/span"
    Date = wait.until(EC.presence_of_element_located((By.XPATH, DateXpath))).text
    FilePath = BookDataPath + f"{Date}_{period}BookData.json"
    if LastRank == 0 and os.path.exists(FilePath):
        with open(FilePath, 'r', encoding='utf-8') as BooksJson:
            BookDataList = json.load(BooksJson)
            LastRank = BookDataList[-1]['Rank']
    
    # Rank 산출 역순으로 (start_i, start_j)값 선정
    if LastRank != 0:
        start_i = (LastRank // 50) + 1
        start_j = (LastRank % 50) + 1
    else:
        start_i = 1
        start_j = 1

    for i in range(start_i, 21): # 1, 21
        for j in range(start_j if i == start_i else 1, 51): # 1, 51
            try:
                PageURL = f"https://product.kyobobook.co.kr/bestseller/total?period=00{Period}#?page={i}&per=50"
                driver.get(PageURL) # period=002(주간), period=003(월간), period=004(연간)
                time.sleep(random.uniform(5, 7))
                CurrentURL = driver.current_url
                Rank = ((i-1) * 50) + j
                
                # 페이지 정보가 넘어서는지 확인 절차
                if PageURL not in CurrentURL:
                    print(f'CurrentURL: {CurrentURL}')
                    print(f'PageURL   : {PageURL}')
                    print(f"< {Rank}위 도서는 전체 페이지에 포함되지 않음, 마지막까지 스크래핑 완료 >")
                    EndSwitch = True
                    break
                
                # 교보문고 베스트셀러 페이지 중간 광고 전후 태그 변화에 따른 ol[n] 및 lo[n] 변화
                BookXpaths = None
                if 1 <= j <= 10:
                    BookXpaths = [
                        f"/html/body/div[3]/main/section[2]/div/section/div[2]/div/div[2]/div[3]/ol[1]/li[{j}]/div[2]/div[1]/a/span/img",
                        f"/html/body/div[3]/main/section[2]/div/section/div[2]/div/div[2]/div[3]/ol[1]/li[{j}]/div[2]/div[1]/div/a/span[1]",
                        f"/html/body/div[3]/main/section[2]/div/section/div[2]/div/div[2]/div[3]/ol[1]/li[{j}]/div[2]/div[1]/div/a/span[2]",
                        f"/html/body/div[3]/main/section[2]/div/section/div[2]/div/div[2]/div[3]/ol[1]/li[{j}]/div[2]/div[2]/div[3]/div/div/a"
                    ]
                elif 11 <= j <= 50:
                    BookXpaths = [
                        f"/html/body/div[3]/main/section[2]/div/section/div[2]/div/div[2]/div[3]/ol[2]/li[{j - 10}]/div[2]/div[1]/a/span/img",
                        f"/html/body/div[3]/main/section[2]/div/section/div[2]/div/div[2]/div[3]/ol[2]/li[{j - 10}]/div[2]/div[1]/div/a/span[1]",
                        f"/html/body/div[3]/main/section[2]/div/section/div[2]/div/div[2]/div[3]/ol[2]/li[{j - 10}]/div[2]/div[1]/div/a/span[2]",
                        f"/html/body/div[3]/main/section[2]/div/section/div[2]/div/div[2]/div[3]/ol[2]/li[{j - 10}]/div[2]/div[2]/div[3]/div/div/a"
                    ]
                if BookXpaths is not None:
                    if not ClickBookElement(driver, wait, BookXpaths):
                        continue
                    
                    BookData = BookDetailsScraper(Rank, Date, driver, wait)
                    BookDataList.append(BookData)
                    with open(FilePath, 'w', encoding = 'utf-8') as BooksJson:
                        json.dump(BookDataList, BooksJson, ensure_ascii = False, indent = 4)
                    print(f"[ {Rank}위 도서 : {BookData['Title']} ]")
                    RandomSleepTime = random.uniform(1, 2)
                    time.sleep(RandomSleepTime)
            except Exception:
                print(f"< {Rank}위 도서는 스크래핑 실패, 패스 >")
                continue
        if EndSwitch:
            break  # 모든 반복문을 종료함

## 교보문고 베스트셀러 스크래퍼
def BestsellerWebScraper(period):
    print(f"[ {period} 베스트셀러 도서 스크래핑 시작 ]\n")
    
    driver = SeleniumHubDrive()
    BestsellerScraper(driver, period) ## Daily, Weekly, Monthly
    driver.quit()
    
    print(f"[ {period} 베스트셀러 도서 스크래핑 완료 ]\n")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    period = 'Weekly' ## 'Total', 'Weekly', 'Monthly', 'Yearly'
    #########################################################################
    BestsellerWebScraper(period)