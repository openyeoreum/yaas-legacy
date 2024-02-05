import os
import glob
import unicodedata
import hashlib
# from dotenv import load_dotenv
import sys

sys.path.append("/yaas")

from backend.b1_Api.b14_Models import User, SeoulNow
from backend.b1_Api.b13_Database import get_db

def GetBasePath():
    sys.path.append("/yaas")
    relativePath = 'storage/s1_Yeoreum/s11_UserStorage'
    # 현재 파일의 디렉토리 경로 얻기
    CurrentDir = os.path.dirname(os.path.abspath(__file__))
    # 현재 디렉토리와 상대 경로를 결합하여 최종 경로 생성
    finalPath = os.path.join(CurrentDir, relativePath)

    return finalPath

### 이메일과 현재 시간을 기반으로 UserId를 생성하는 함수
def GenerateUserId(email: str) -> str:
    UniqueString = email + str(SeoulNow())
    return hashlib.sha256(UniqueString.encode('utf-8')).hexdigest()

### User 테이블과 폴더를 생성하는 함수
def AddUserToDB(email, username, password):
    
    with get_db() as db:
        # UserId 생성
        GeneratedUserId = GenerateUserId(email)
        # BasePath 생성
        BasePath = GetBasePath()

        # 가능한 모든 UserPath 검색
        possiblePaths = glob.glob(os.path.join(BasePath, f"{username}_user"))
        # 존재하는 경로 사용
        if possiblePaths:
            userPath = max(possiblePaths, key = os.path.getctime)
            profileImageFilePath = os.path.join(userPath, f"{os.path.basename(userPath)}_profile_image")
        else:
            # 존재하는 경로가 없으면 새로운 경로 생성
            userPath = os.path.join(BasePath, f"{username}_user")
            profileImageFilePath = os.path.join(userPath, f"{username}_profile_image")
            # 새로운 폴더 생성
            os.makedirs(userPath, exist_ok=True)
        
        # APIkey 가져오기
        tTSapiKey = os.getenv("TTSapiKey")
        lLMapiKey = os.getenv("LLMapiKey")
        
        ExistingUser = db.query(User).filter(User.Email == email).first()
        
        # User 객체 생성 및 초기 정보 입력
        if not ExistingUser:
            user = User(
                UserId = GeneratedUserId,
                Email = email,
                UserName = username,
                UserPath = userPath,
                ProfileImagePath = profileImageFilePath,
                TTSapiKey = tTSapiKey,
                LLMapiKey = lLMapiKey
                )
            user.SetPassword(password)
            db.add(user)
            # 사용자 폴더 생성
            os.makedirs(userPath, exist_ok = True)
            
            db.commit()
            print(f"[ Email: {email} | Username: {username} | AddUserToDB 완료 ]")
        else:
            print(f"[ Email: {email} | Username: {username} | AddUserToDB가 이미 완료됨 ]")

if __name__ == "__main__":
    
    AddUserToDB('yeoreum00128@gmail.com', 'yeoreum', '0128')
    AddUserToDB('junsun0128@gmail.com', 'junyoung', '0128')
    AddUserToDB('ahyeon0128@gmail.com', 'ahyeon', '0128')