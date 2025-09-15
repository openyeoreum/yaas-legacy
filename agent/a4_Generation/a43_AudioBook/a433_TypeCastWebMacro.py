import os
import random
import time
import sys
sys.path.append("/yaas")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

## TypeCastAPI 드라이브
def TypeCastAPIDrive(email):
    print(f"[ User: {email} | TypeCastAPIDrive 연결 시도 ]\n")
    # Selenium Grid URL
    hub_url = "http://selenium:4444/wd/hub"

    # Chrome 옵션 설정
    options = Options()
    options.add_argument('--no-sandbox')  # 샌드박스 모드 비활성화
    options.add_argument('--disable-dev-shm-usage')  # /dev/shm 사용량 제한 해제
    options.add_argument('--disable-blink-features=AutomationControlled')  # /dev/shm 사용량 제한 해제
    options.add_argument('--headless')  # 브라우저 없이 실행하는 headless 모드 비활성화

    # 원격 WebDriver 연결
    driver = webdriver.Remote(command_executor = hub_url, options = options)
    print(f"[ User: {email} | TypeCastAPIDrive 연결 완료 ]\n")

    return driver

## TypeCastAPI 로그인
def TypeCastAPILogin(driver, email, password):
    wait = WebDriverWait(driver, 10)
    # 웹사이트 열기
    driver.get("https://biz.typecast.ai/login")

    # 로그인 정보 입력 필드 찾기 및 입력 (실제 아이디와 비밀번호로 대체해야 함)
    username = driver.find_element(By.NAME, "email")
    Password = driver.find_element(By.NAME, "password")
    username.send_keys(email)
    Password.send_keys(password)
    time.sleep(random.randint(3, 5))
    
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'q-btn') and @type='submit']")))
    login_button.click()

    page_loaded = wait.until(EC.url_to_be("https://biz.typecast.ai/org/overview"))
    time.sleep(random.randint(1, 2))
    print(f"[ User: {email} | TypeCastAPILogin 완료 ]\n")

## TypeCastAPICharacter 변경
def TypeCastAPICharacter(driver, email, name):
    wait = WebDriverWait(driver, 25)
    time.sleep(random.randint(9, 11))
    
    # 캐릭터 변경 버튼 클릭을 위해 대기
    change_character_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/div/div[2]/main/main/div/div/div[2]/div[2]/div/div[1]/div[2]/button/span[2]/span")))
    change_character_button.click()
    time.sleep(random.randint(3, 5))

    # 캐릭터 변경 버튼 클릭 후 iframe으로 컨텍스트 전환
    iframe = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "character-select-iframe")))
    driver.switch_to.frame(iframe)
    time.sleep(random.randint(3, 5))
    
    # 검색 입력 필드에 접근
    search_input = driver.find_element(By.ID, "search")
    search_input.send_keys(name)
    search_input.send_keys(Keys.ENTER)
    time.sleep(random.randint(3, 5))

    # 검색 결과의 첫 번째 캐릭터 선택
    first_search_result = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/div[5]/div/div[2]/div/div[3]/div/div/div[1]/div/div[1]/div/div[1]/div[3]/div[1]/strong")))
    first_search_result.click()
    time.sleep(random.randint(1, 3))

    # "캐릭터 변경" 버튼 클릭
    change_character_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/div[5]/div/div[3]/div/button/span")))
    change_character_button.click()

    time.sleep(random.randint(10, 15))
    # driver.save_screenshot("/yaas/TypeCastAPICharacter_" + name + ".png")
    print(f"[ User: {email} | Character: {name} | TypeCastAPICharacter 완료 ]\n")

## TypeCastAPI 로그아웃
def TypeCastAPILogout(email, driver):
    time.sleep(random.randint(0, 1))
    driver.quit()
    time.sleep(random.randint(1, 2))
    print(f"[ User: {email} | TypeCastAPILogout 완료 ]\n")
    
## TypeCastAPICharacter 통합 함수
def TypeCastMacro(name, account):
    ############################ 하이퍼 파라미터 설정 ############################
    email = account
    password = os.getenv("TYPECAST_PASSWORD")
    ## TypeCastAPI 드라이브
    driver = TypeCastAPIDrive(email)
    #########################################################################

    ## TypeCastAPI 로그인
    TypeCastAPILogin(driver, email, password)
    
    ## TypeCastAPICharacter 변경
    TypeCastAPICharacter(driver, email, name)
    
    ## TypeCastAPI 로그아웃
    TypeCastAPILogout(email, driver)
    
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    names = ["연우", "김건", "만년대리"]
    #########################################################################
    for name in names:
        TypeCastMacro(name)