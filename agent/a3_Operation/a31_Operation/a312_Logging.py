import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from agent.a3_Operation.a31_Operation.a311_Access import Access

# ======================================================================
# [a312-1] Operation-Logging
# ======================================================================
# class: Logging
# ======================================================================
class Logging(Access):

    # operation 경로
    log_file_path = "/yaas/agent/a2_DataFrame/a21_Operation/a212_Logging.json"

    # --------------------------------
    # --- class-init -----------------
    # --- class-func: Logging 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 solution: str = None,
                 next_solution: str = None,
                 process_number: str = None,
                 process_name: str = None,
                 idx: int = None,
                 idx_length: int = None) -> None:
        """사용자-프로젝트의 Operation에 통합 Logging 기능을 수행하는 클래스입니다.

        Attributes:
            email (str): 이메일
            project_name (str): 프로젝트명
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Audiobook, Translation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
            idx (int): 솔루션 안에 프로세스 안에 테스크 인덱스 번호
            idx_length (int): idx의 전체 길이
        """
        # Access 초기화
        super().__init__(
            email,
            project_name)

        # attributes 설정
        self.solution = solution
        self.next_solution = next_solution
        self.process_number = process_number
        self.process_name = process_name
        self.idx = idx
        self.idx_length = idx_length

    # -----------------------------------------
    # --- func-set: print logging -------------
    # --- class-func: logging_config 불러오기 ---
    def _load_logging_config(self) -> dict:
        """로깅 설정 JSON 파일을 로드하여 딕셔너리로 반환합니다.

        Returns:
            logging_config_dict (dict): 로깅 설정이 담긴 딕셔너리
        """
        # JSON 파일 열기 및 로드
        with open(self.log_file_path, 'r', encoding='utf-8') as file:
            logging_config_dict = json.load(file)
        
        return logging_config_dict

    # --- logging_data 가져오고 포맷팅하고 출력하기 ---
    def print_logging(self,
                      logginig: str,
                      logginig_keys: list,
                      info_keys: list = None,
                      print: str = None) -> str:
        """로깅 설정에서 지정된 키에 해당하는 로깅 데이터를 가져와 포맷팅합니다.

        Args:
            logginig (str): 로깅 종류 (예: "Access", "Work", "Task")
            logginig_keys_list (list): 로깅 설정에서 접근할 키들의 리스트의 리스트 (ex. [["Logging", "Core"], ["Info", "Run"]])
            print (str, optional): 출력할 추가 정보

        Print:
            formatted_logging_data (str): 포맷팅된 로깅 데이터
        """
        # logging_config_dict 불러오기
        logging_config_dict = self._load_logging_config().get(logginig, {})

        # logging_config_dict에서 keys에 해당하는 경로 가져오기
        logging = logging_config_dict
        for key in logginig_keys:
            logging = logging[key]

        info = logging_config_dict
        for key in info_keys:
            info = info[key]
        
        # 'YYYYMMDD_HHMMSS' 형식의 문자열로 포맷팅
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # loggig 포맷팅
        formatted_loggig = logging.format(
            Timestamp=timestamp,
            Email=self.email,
            ProjectName=self.project_name,
            Solution=self.solution,
            NextSolution=self.next_solution,
            ProcessNumber=self.process_number,
            ProcessName=self.process_name,
            Idx=self.idx if self.idx is not None else 0,
            IdxLength=self.idx_length if self.idx_length is not None else 0)

        # info 포맷팅
        formatted_info = info.format(Print=print if print is not None else "")

        # 최종 로깅 데이터 출력
        formatted_logging_data = f"{formatted_loggig}{formatted_info}"

        print(formatted_logging_data)

if __name__ == "__main__":

    # --- class-test ---
    # 인자 설정
    email = "yeoreum00128@gmail.com"
    project_name = "글로벌솔루션여름"
    solution = "ScriptSegmentation"
    next_solution = "Audiobook"
    process_number = "PT01"
    process_name = "ScriptLoad"
    idx = 1
    idx_length = 10

    # 클래스 테스트
    logging = Logging(
        email,
        project_name,
        solution=solution,
        next_solution=next_solution,
        process_number=process_number,
        process_name=process_name,
        idx=idx,
        idx_length=idx_length)
    
    logginig = "Work"
    logginig_keys = ["Logging", "Core"]
    info_keys = ["Info", "Run"]

    logging.print_logging(
        logginig,
        logginig_keys,
        info_keys=info_keys)