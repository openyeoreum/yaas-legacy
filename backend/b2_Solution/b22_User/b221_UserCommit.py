import os
import hashlib
from dotenv import load_dotenv
import sys

sys.path.append("/yaas")

from backend.b1_Api.b14_Models import User, SeoulNow
from backend.b1_Api.b13_Database import get_db

def GetBasePath(relativePath='../../b6_Storage/b62_UserStorage/'):
    CurrentDir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(CurrentDir, relativePath)

### 이메일과 현재 시간을 기반으로 UserId를 생성하는 함수
def GenerateUserId(email: str) -> str:
    UniqueString = email + str(SeoulNow())
    return hashlib.sha256(UniqueString.encode('utf-8')).hexdigest()

### User 테이블과 폴더를 생성하는 함수
def AddUserToDB(email, username, password):
    # .env 파일 로드
    load_dotenv("/yaas/backend/.env")
    
    with get_db() as db:
        # UserId 생성
        GeneratedUserId = GenerateUserId(email)
        # BasePath 생성
        BasePath = GetBasePath()
        # UserPath 생성
        userPath = os.path.join(BasePath, f"{SeoulNow()}_{GeneratedUserId}")
        # ProfileImageFilePath 생성
        profileImageFilePath = os.path.join(userPath, f"{SeoulNow()}_{username}_profile_image")
        
        # APIkey 가져오기
        tTSapiKey = os.getenv("TTSapiKey")
        lLMapiKey = os.getenv("LLMapiKey")
        
        # User 객체 생성 및 초기 정보 입력
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
        db.commit()

    # 폴더 생성
    if not os.path.exists(userPath):
        os.makedirs(userPath)

if __name__ == "__main__":
    
    AddUserToDB('yeoreum00128@gmail.com', 'yeoreum', '0128')
    AddUserToDB('junsun0128@gmail.com', 'junyoung', '0128')
    AddUserToDB('ahyeon0128@gmail.com', 'ahyeon', '0128')