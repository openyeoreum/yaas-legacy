import json
import hashlib
import sys
sys.path.append("/yaas")

from datetime import datetime

# ======================================================================
# [a311-1] Operation-Access
# ======================================================================
# class: Access
# ======================================================================
class Access:

    # operation 경로
    access_path = "/yaas/storage/s1_Yeoreum/s11_UserAccess/s111_UserAccess.json"

    # -------------------------------
    # --- class-init ----------------
    # --- class-func: Access 초기화 ---
    def __init__(self, email: str, project_name: str) -> None:
        """이메일 해시 및 타임스탬프 생성 기능을 수행하는 클래스입니다.
        
        Args:
            email (str): 이메일
            project_name (str): 프로젝트명

        Attributes:
            email (str): 해시된 이메일
            project_name (str): 타임스탬프가 추가된 프로젝트명
        """
        # attributes 설정
        # 이메일 해시 및 타임스탬프 생성
        self.email, self.project_name = self._read_or_write_timestamped_project(email, project_name)

    # ---------------------------------
    # --- func-set: hash, timestamp ---
    # --- class-func: email 해시 -------
    def _hash_email(self, email: str) -> str:
        """이메일 주소를 SHA-256으로 해시하여 16진수 문자열로 반환합니다.

        Args:
            email (str): 해시할 이메일 주소

        Returns:
            str: 해시된 이메일 주소의 16진수 문자열
        """
        # 이메일을 utf-8 바이트 문자열로 인코딩
        encoded_email = email.encode('utf-8')

        # SHA-256 해시 객체를 생성하고 업데이트
        hasher = hashlib.sha256()
        hasher.update(encoded_email)

        # 해시된 결과물을 16진수(hexadecimal)로 반환
        return hasher.hexdigest()

    # --- class-func: project name 타임스탬프 ---
    def _timestamped_project_name(self, project_name: str) -> str:
        """프로젝트 이름에 'YYYYMMDD_HHMMSS' 형식의 타임스탬프를 추가합니다.

        Args:
            project_name (str): 원본 프로젝트 이름

        Returns:
            timestamped_project_name (str): 타임스탬프가 추가된 새 프로젝트 이름 (예: '20250924_123311_ProjectName')
        """
        # 'YYYYMMDD_HHMMSS' 형식의 문자열로 포맷팅
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 타임스탬프와 원본 프로젝트 이름을 조합
        timestamped_project_name = f"{timestamp}_{project_name}"

        # 원본 프로젝트 이름과 타임스탬프를 조합하여 반환
        return timestamped_project_name

    # ---------------------------------------
    # --- func-set: read or write project ---
    # --- class-func: access 파일 불러오기 ------
    def _load_access(self) -> dict:
        """Access.json 파일을 불러옵니다.

        Returns:
            access_dict (dict): Access.json 파일 내용
        """
        # access.json 파일 불러오기
        try:
            with open(self.access_path, 'r', encoding='utf-8') as f:
                access_dict = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 파일이 없거나 비어있으면 빈 딕셔너리로 시작
            access_dict = {}

        return access_dict
    
    # --- class-func: 프로젝트 조회 또는 생성 및 JSON 저장/로드 ---
    def _read_or_write_timestamped_project(self, email: str, project_name: str) -> str:
        """이메일과 프로젝트 이름으로 기존 프로젝트를 조회하거나 새 프로젝트 데이터를 생성합니다.

        Args:
            email (str): 사용자 이메일 주소
            project_name (str): 원본 프로젝트 이름

        Returns:
            hashed_email (str): 해시된 이메일 주소
            timestamped_project_name (str): 타임스탬프가 추가된 프로젝트 이름
        """
        # access.json 파일 불러오기
        access_dict = self._load_access()

        # 이메일을 해시하여 사용자 식별
        hashed_email = self._hash_email(email)

        # 사용자의 기존 프로젝트 목록 가져오기
        user_projects = access_dict.get(hashed_email, {})

        # 동일한 이름의 프로젝트가 있는지 확인
        if project_name in user_projects:
            # 있으면 기존 이름 반환
            timestamped_project_name = user_projects[project_name]
            
            return hashed_email, timestamped_project_name
        else:
            # 없으면 새로 생성
            timestamped_project_name = self._timestamped_project_name(project_name)
            
            # 사용자 프로젝트 목록에 새 프로젝트 추가
            user_projects[project_name] = timestamped_project_name
            
            # 전체 데이터에 사용자 프로젝트 목록 업데이트
            access_dict[hashed_email] = user_projects
            
            # 변경된 내용을 JSON 파일에 다시 저장
            with open(self.access_path, 'w', encoding='utf-8') as f:
                json.dump(access_dict, f, indent=4, ensure_ascii=False)
            
            return hashed_email, timestamped_project_name

if __name__ == "__main__":

    # --- class-test ---
    # 인자 설정
    email = "yeoreum00128@gmail.com"
    project_name = "글로벌솔루션여름"

    # 클래스 테스트
    access = Access(
        email,
        project_name)

    hashed_email = access.email
    timestamped_name = access.project_name

    print("Hashed Email:", hashed_email)
    print("Timestamped Project Name:", timestamped_name)