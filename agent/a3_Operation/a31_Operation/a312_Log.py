import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from agent.a3_Operation.a31_Operation.a311_Access import Access

# ======================================================================
# [a312-1] Operation-Log
# ======================================================================
# class: Log
# ======================================================================
class Log(Access):

    # operation 경로
    log_file_path = "/yaas/agent/a2_DataFrame/a21_Operation/a212_LogConfig.json"

    # ----------------------------
    # --- class-init -------------
    # --- class-func: Log 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 solution: str = None,
                 next_solution: str = None,
                 process_number: str = None,
                 process_name: str = None,
                 idx: int = None,
                 idx_length: int = None) -> None:
        """사용자-프로젝트의 Operation에 통합 Log 기능을 수행하는 클래스입니다.

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
        self.project_log_file_path = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/{self.email}/{self.project_name}/{self.project_name}_project_log.json"

    # ---------------------------------------
    # --- func-set: print and append log ----
    # --- class-func: log_config 불러오기 -----
    def _load_log_config(self) -> dict:
        """로깅 설정 JSON 파일을 로드하여 딕셔너리로 반환합니다.

        Returns:
            log_config_dict (dict): 로깅 설정이 담긴 딕셔너리
        """
        # JSON 파일 열기 및 로드
        with open(self.log_file_path, 'r', encoding='utf-8') as file:
            log_config_dict = json.load(file)
        
        return log_config_dict

    # --- class-func: log data 추가하기 ---
    def _append_log_data(self,
                         timestamp: str,
                         info: str) -> None:
        """현재 로그 데이터를 프로젝트 로그 파일에 추가합니다.

        Args:
            timestamp (str): 'YYYY-MM-DD HH:MM:SS' 형식의 타임스탬프 문자열
            info (str): 'Start', 'End', 'Stop' 등 로그 정보

        Effects:
            log_json_data 추가 (dict): self.project_log_file_path["Log"].append(log_data)
        """
        # 현재 로그 데이터를 딕셔너리로 생성
        current_log_data = {
            "Timestamp": timestamp,
            "Solution": self.solution,
            "NextSolution": self.next_solution if self.next_solution is not None else "",
            "ProcessNumber": self.process_number,
            "ProcessName": self.process_name,
            "Info": info
        }

        # self.project_log_file_path 파일 불러오기
        with open(self.project_log_file_path, 'r', encoding='utf-8') as log_json_file:
            log_json_data = json.load(log_json_file)

        # 현재 로그 데이터를 기존 로그 데이터에 추가
        log_json_data["Log"].append(current_log_data)

        # 업데이트된 로그 데이터를 다시 파일에 저장
        with open(self.project_log_file_path, 'w', encoding='utf-8') as file:
            json.dump(log_json_data, file, ensure_ascii=False, indent=4)

    # --- class-func: log data 가져오고 포맷팅하고 출력하기 ---
    def print_log(self,
                  logginig: str,
                  logginig_keys: list,
                  info_keys: list,
                  function_name = None,
                  message: str = None) -> str:
        """로깅 설정에서 지정된 키에 해당하는 로깅 데이터를 가져와 포맷팅합니다.

        Args:
            logginig (str): 로깅 종류 (예: "Access", "Work", "Task")
            logginig_keys (list): 로깅 데이터에서 가져올 키들의 리스트
            info_keys (list): 추가 정보에서 가져올 키들의 리스트
            function_name (str, optional): 함수 이름 (예: "InputPreprocess", "Prompt" 등)
            message (str, optional): 출력할 추가 정보

        Print:
            formatted_log_data (str): 포맷팅된 로깅 데이터
        """
        # Welcome YaaS 패턴
        welcome_yaas = """

        __          __  _                           __     __          _____ 
        \ \        / / | |                          \ \   / /         / ____|
         \ \  /\  / /__| | ___ ___  _ __ ___   ___   \ \_/ /_ _  __ _| (___  
          \ \/  \/ / _ \ |/ __/ _ \| '_ ` _ \ / _ \   \   / _` |/ _` |\___ \ 
           \  /\  /  __/ | (_| (_) | | | | | |  __/    | | (_| | (_| |____) |
            \/  \/ \___|_|\___\___/|_| |_| |_|\___|    |_|\__,_|\__,_|_____/ 

        """
        # log_config_dict 불러오기
        log_config_dict = self._load_log_config()[logginig.capitalize()]

        # log_config_dict에서 keys에 해당하는 로깅 출력 가져오기
        # log keys
        log = log_config_dict
        for key in logginig_keys:
            log = log[key]

        # info keys
        info = log_config_dict
        for key in info_keys:
            info = info[key]
        
        # 'YYYYMMDD_HHMMSS' 형식의 문자열로 포맷팅
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # info 포맷팅
        formatted_info = info.format(Print=message if message is not None else "")

        # loggig 포맷팅
        formatted_loggig_data = log.format(
            Timestamp=timestamp,
            Email=self.email,
            ProjectName=self.project_name,
            Solution=self.solution,
            NextSolution=self.next_solution,
            ProcessNumber=self.process_number,
            ProcessName=self.process_name,
            FunctionName=function_name if function_name is not None else "",
            Info=formatted_info,
            Idx=self.idx if self.idx is not None else 0,
            IdxLength=self.idx_length if self.idx_length is not None else 0)

        # formatting된 loggig 출력
        if logginig == "Access" and "Access" in logginig_keys:
            print(welcome_yaas)
        print(formatted_loggig_data)

        # log data 추가
        _info = info_keys[-1]
        if logginig == "work" and _info in ["Start", "End", "Stop"]:
            self._append_log_data(timestamp, _info)

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
    log = Log(
        email,
        project_name,
        solution=solution,
        next_solution=next_solution,
        process_number=process_number,
        process_name=process_name,
        idx=idx,
        idx_length=idx_length)

    log.print_log(
        "access",
        ["Log", "Access"],
        ["Info", "Hello"])