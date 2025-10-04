import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from agent.a3_Operation.a31_Operation.a312_Base import Base

# ======================================================================
# [a313-1] Operation-Log
# ======================================================================
# class: Log
# ======================================================================
class Log(Base):

    # operation 경로
    log_file_path = "/yaas/agent/a2_DataFrame/a21_Operation/a212_LogMap.json"

    # ----------------------------
    # --- class-init -------------
    # --- class-func: Log 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 solution: str = None,
                 next_solution: str = None,
                 process_number: str = None,
                 process_name: str = None) -> None:
        """사용자-프로젝트의 Operation에 통합 Log 기능을 수행하는 클래스입니다.

        Attributes:
            email (str): 이메일
            project_name (str): 프로젝트명
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Audiobook, Translation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
        """
        # Base 초기화
        super().__init__(
            email,
            project_name,
            solution,
            next_solution,
            process_number,
            process_name)

    # ---------------------------------------
    # --- func-set: print and append log ----
    # --- class-func: log_map 불러오기 -----
    def _load_log_map(self) -> dict:
        """로그 설정 JSON 파일을 로드하여 딕셔너리로 반환합니다.

        Returns:
            log_map_dict (dict): 로그 설정이 담긴 딕셔너리
        """
        # JSON 파일 열기 및 로드
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            log_map_dict = json.load(f)
        
        return log_map_dict

    # --- class-func: log data 추가하기 ---
    def _append_log_data(self,
                         timestamp: str,
                         _solution: str,
                         _info: str) -> None:
        """현재 로그 데이터를 프로젝트 로그 파일에 추가하고, 유효한 운영 시간만 계산하여 업데이트합니다.

        Args:
            timestamp (str): 'YYYY-MM-DD HH:MM:SS' 형식의 타임스탬프 문자열
            _solution (str): 'Core', 'Solution', 'Process', 'Task'
            _info (str): 'Start', 'End', 'Stop' 등 로그 정보

        Effects:
            log_json_data 추가 (dict): self.project_log_file_path["Log"].append(log_data)
            OperatingTime 업데이트: 'core' 작업의 'Start'부터 'Stop' 또는 'End'까지의 시간만 합산하여 업데이트합니다.
        """
        # - innerfunc: timestamp 계산기 -
        def calculate_timestamp_difference_func(start_timestamp: str, end_timestamp: str) -> int:
            """
            'YYYY-MM-DD HH:MM:SS' 형식의 두 시간 문자열을 받아
            시간 차이를 'HH:MM:SS' 형식과 초로 반환합니다.

            Args:
                start_timestamp (str): 시작 시간 문자열
                end_timestamp (str): 종료 시간 문자열

            Returns:
                tuple[str, int]: ('HH:MM:SS' 형식의 시간 차이, 총 시간 차이(초))
            """
            time_format = "%Y-%m-%d %H:%M:%S"
            start_time = datetime.strptime(start_timestamp, time_format)
            end_time = datetime.strptime(end_timestamp, time_format)
            time_delta = end_time - start_time
            
            total_seconds = int(time_delta.total_seconds())
            
            return total_seconds
        # - innerfunc end -

        # 현재 로그 데이터를 딕셔너리로 생성
        current_log_data = {
            "Timestamp": timestamp,
            "Work": _solution,
            "Solution": self.solution,
            "NextSolution": self.next_solution,
            "ProcessNumber": self.process_number,
            "ProcessName": self.process_name,
            "Info": _info
        }

        # ProjectLog 파일 불러오기
        with open(self.read_path_map("Core", ["File", "Json", "ProjectLog"]), 'r', encoding='utf-8') as f:
            log_json_data = json.load(f)

        # 첫 로그 데이터인 경우 Email과 ProjectName 추가
        if len(log_json_data["Log"]) == 1:
            log_json_data["Email"] = self.email
            log_json_data["ProjectName"] = self.project_name

        # 현재 로그 데이터를 기존 로그 데이터에 추가
        log_json_data["Log"].append(current_log_data)
        
        # OperatingTime 계산
        total_operating_seconds = 0
        start_timestamp_for_session = None

        # "Work"가 "Core"인 로그만 필터링하여 계산
        core_logs = [log for log in log_json_data["Log"] if log.get("Work") == "Core"]

        for log in core_logs:
            # 타임스탬프와 정보가 유효한지 확인
            current_timestamp = log.get("Timestamp")
            current_info = log.get("Info")
            if not current_timestamp or not current_info:
                continue

            if current_info == "Start":
                # 새로운 세션 시작으로 간주하고 시작 시간 기록
                start_timestamp_for_session = current_timestamp
            elif current_info in ["Stop", "End"]:
                # 세션이 시작된 상태에서 Stop 또는 End를 만나면 시간 계산
                if start_timestamp_for_session:
                    duration_seconds = calculate_timestamp_difference_func(
                        start_timestamp_for_session, 
                        current_timestamp
                    )
                    total_operating_seconds += duration_seconds
                    # 계산 후 세션 시작 시간 초기화
                    start_timestamp_for_session = None

        # 계산된 총 운영 시간을 HH:MM:SS 형식으로 변환
        hours, remainder = divmod(total_operating_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_total_time = f"{hours:02}:{minutes:02}:{seconds:02}"

        # 최종 OperatingTime 업데이트
        log_json_data["OperatingTime"]["Time"] = formatted_total_time
        log_json_data["OperatingTime"]["Second"] = total_operating_seconds
        # --- 로직 수정 끝 ---

        # 업데이트된 로그 데이터를 다시 ProjectLog 파일에 저장
        with open(self.read_path_map("Core", ["File", "Json", "ProjectLog"]), 'w', encoding='utf-8') as f:
            json.dump(log_json_data, f, ensure_ascii=False, indent=4)

    # --- class-func: log data 가져오고 포맷팅하고 출력하기 ---
    def print_log(self,
                  log: str,
                  log_keys: list,
                  info_keys: list,
                  idx: int = None,
                  idx_length: int = None,
                  function_name = None,
                  _print: str = None) -> str:
        """로그 설정에서 지정된 키에 해당하는 로그 데이터를 가져와 포맷팅합니다.

        Args:
            log (str): 로그 종류 (예: "Access", "Work", "Task")
            log_keys (list): 로그 데이터에서 가져올 키들의 리스트
            info_keys (list): 추가 정보에서 가져올 키들의 리스트
            idx (int, optional): 솔루션 안에 프로세스 안에 테스크 인덱스 번호로 jpg, wav, mp3 등 file명에 사용 (기본값: None)
            idx_length (int, optional): idx의 전체 길이 (기본값: None)
            function_name (str, optional): 함수 이름 (예: "InputPreprocess", "Prompt" 등)
            print (str, optional): 출력할 추가 정보

        Print:
            formatted_log_data (str): 포맷팅된 로그 데이터
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
        # log_map_dict 불러오기
        log_map_dict = self._load_log_map()[log]

        # log_map_dict에서 keys에 해당하는 로그 출력 가져오기
        # log keys
        _log = log_map_dict
        for key in log_keys:
            _log = _log[key]

        # info keys
        info = log_map_dict
        for key in info_keys:
            info = info[key]
        
        # 'YYYYMMDD_HHMMSS' 형식의 문자열로 포맷팅
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # info 포맷팅
        formatted_info = info.format(Print=_print if _print is not None else "")

        # loggig 포맷팅
        formatted_loggig_data = _log.format(
            Timestamp=timestamp,
            Email=self.email,
            ProjectName=self.project_name,
            Solution=self.solution,
            NextSolution=self.next_solution,
            ProcessNumber=self.process_number,
            ProcessName=self.process_name,
            FunctionName=function_name if function_name is not None else "",
            Info=formatted_info,
            Idx=idx if idx is not None else 0,
            IdxLength=idx_length if idx_length is not None else 0)

        # formatting된 loggig 출력
        if log == "Access" and "Access" in log_keys:
            print(welcome_yaas)
        print(formatted_loggig_data)

        # log data 추가
        _info = info_keys[-1]
        if log == "Solution" and _info in ["Start", "End", "Stop"]:
            _solution = log_keys[-1]

            self._append_log_data(timestamp,
                                  _solution,
                                  _info)

if __name__ == "__main__":

    # --- class-test ---
    # 인자 설정
    email = "yeoreum00128@gmail.com"
    project_name = "글로벌솔루션여름"
    solution = "ScriptSegmentation"
    next_solution = "Audiobook"
    process_number = "PT01"
    process_name = "ScriptLoad"

    # 클래스 테스트
    log = Log(
        email,
        project_name,
        solution=solution,
        next_solution=next_solution,
        process_number=process_number,
        process_name=process_name)