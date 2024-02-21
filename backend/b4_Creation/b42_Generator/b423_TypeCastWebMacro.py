import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

url = 'https://biz.typecast.ai/org/overview'
# 타입캐스트 웹사이트 열기

options = Options()
options.add_argument("--start-maximized")
options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options = options)

driver.get(url)

# try:
    
    # # '캐릭터 변경' 버튼을 찾아 클릭
    # change_button = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.XPATH, '//button[./*[contains(text(), "캐릭터 변경")]]'))
    # )
    # change_button.click()

    # # 검색창에 '김건' 입력 후 돋보기 버튼 클릭
    # search_box = WebDriverWait(driver, 10).until(
    #     EC.visibility_of_element_located((By.XPATH, '//input[@placeholder="원하는 목소리 스타일을 묘사하거나 캐릭터 이름을 입력하세요"]'))
    # )
    # search_box.send_keys('김건')

    # search_button = driver.find_element(By.XPATH, '//button[@title="검색"]')
    # search_button.click()

    # # 검색 결과 중 '김건' 이름을 가진 캐릭터 클릭
    # character = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "김건")]/ancestor::div[@role="button"]'))
    # )
    # character.click()

    # # '캐릭터 변경' 버튼을 찾아 클릭
    # change_button = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.XPATH, '//button[./*[contains(text(), "캐릭터 변경")]]'))
    # )
    # change_button.click()

# finally:
#     # 모든 동작이 끝난 후 드라이버 종료
#     driver.quit()
