from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Selenium Grid URL
hub_url = "http://selenium:4444/wd/hub"

# Chrome 옵션 설정
options = Options()
options.add_argument('--no-sandbox')  # 샌드박스 모드 비활성화
options.add_argument('--disable-dev-shm-usage')  # /dev/shm 사용량 제한 해제
# options.add_argument('--headless')  # 브라우저 없이 실행하는 headless 모드 비활성화

# 원격 WebDriver 연결
driver = webdriver.Remote(command_executor=hub_url, options=options)

# 웹사이트 열기
driver.get("https://biz.typecast.ai/login")
if "https://biz.typecast.ai/login" in driver.current_url:
    print("웹사이트 열기 성공")

# 로그인 정보 입력 필드 찾기 및 입력 (실제 아이디와 비밀번호로 대체해야 함)
username = driver.find_element(By.NAME, "email")
password = driver.find_element(By.NAME, "password")
username.send_keys("lucidsun0128@naver.com")
password.send_keys("Dhvmsdufma1!")

wait = WebDriverWait(driver, 10)
login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[@for='password']//input[@type='password']")))
login_button.click()
if login_button.is_enabled():
    print("로그인 버튼 클릭 완료")
else:
    print("로그인 버튼을 클릭할 수 없습니다.")

wait = WebDriverWait(driver, 20)
try:
    # 로그인 성공 페이지 URL로 리디렉션이 완료될 때까지 대기
    page_loaded = wait.until(EC.url_to_be("https://biz.typecast.ai/org/overview"))
    print("로그인 성공")
except TimeoutException:
    print("로그인 실패 또는 페이지 로딩 시간 초과")
    
driver.quit()

# # 로그인 후 캐릭터 변경 버튼 클릭을 위해 대기
# wait = WebDriverWait(driver, 10)
# change_character_button = wait.until(EC.element_to_be_clickable((By.ID, "change_character_button_id")))  # 실제 버튼 ID로 대체
# change_character_button.click()

# # 캐릭터 검색바 찾기 및 캐릭터명 입력
# search_bar = driver.find_element(By.ID, "search_bar_id")  # 실제 검색바 ID로 대체
# search_bar.send_keys("캐릭터명")

# # 검색 실행 버튼 찾기 및 클릭
# search_button = driver.find_element(By.ID, "search_icon_id")  # 실제 검색 버튼 ID로 대체
# search_button.click()

# # 검색 결과에서 첫 번째 캐릭터 선택 (XPATH는 실제 웹 페이지 구조에 따라 대체해야 함)
# character_to_select = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='character_class_name'][1]")))  # 실제 클래스 이름으로 대체
# character_to_select.click()

# # 캐릭터 변경 버튼 클릭
# change_button = driver.find_element(By.ID, "change_button_id")  # 실제 변경 버튼 ID로 대체
# change_button.click()

# # 변경된 캐릭터 확인 및 브라우저 닫기
# print("캐릭터 변경 완료")
# driver.quit()