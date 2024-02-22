from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import random
import time

# Selenium Grid URL
hub_url = "http://selenium:4444/wd/hub"

# Chrome 옵션 설정
options = Options()
options.add_argument('--no-sandbox')  # 샌드박스 모드 비활성화
options.add_argument('--disable-dev-shm-usage')  # /dev/shm 사용량 제한 해제
options.add_argument('--disable-blink-features=AutomationControlled')  # /dev/shm 사용량 제한 해제
options.add_argument('--headless')  # 브라우저 없이 실행하는 headless 모드 비활성화

# 원격 WebDriver 연결
driver = webdriver.Remote(command_executor=hub_url, options=options)
wait = WebDriverWait(driver, 10)

# 웹사이트 열기
driver.get("https://biz.typecast.ai/login")

# 로그인 정보 입력 필드 찾기 및 입력 (실제 아이디와 비밀번호로 대체해야 함)
username = driver.find_element(By.NAME, "email")
password = driver.find_element(By.NAME, "password")
username.send_keys("lucidsun0128@naver.com")
password.send_keys("Dhvmsdufma1!")

time.sleep(random.randint(3, 5))
login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'q-btn') and @type='submit']")))
login_button.click()

page_loaded = wait.until(EC.url_to_be("https://biz.typecast.ai/org/overview"))

# 로그인 후 캐릭터 변경 버튼 클릭을 위해 대기
change_character_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '캐릭터 변경')]")))
change_character_button.click()
time.sleep(random.randint(7, 9))

# XPath를 사용하여 검색창 찾기
search_input = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="search"]')))

# 검색창에 '김건' 입력
search_input.send_keys("김건")
driver.save_screenshot("/yaas/after_character_change1.png")
# 필요에 따라 검색 실행 코드 추가
search_input.send_keys(Keys.ENTER)

driver.save_screenshot("/yaas/after_character_change2.png")
driver.quit()