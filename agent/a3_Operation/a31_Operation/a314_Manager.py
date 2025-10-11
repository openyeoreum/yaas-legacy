import os
import json
import sys
sys.path.append("/yaas")

from agent.a3_Operation.a31_Operation.a313_Log import Log

# ======================================================================
# [a314-1] Operation-Manager
# ======================================================================
# class: Manager
# ======================================================================
class Manager(Log):

    # --------------------------------
    # --- class-init -----------------
    # --- class-func: Manager 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 solution: str = None,
                 next_solution: str = None,
                 process_number: str = None,
                 process_name: str = None) -> None:
        """사용자-프로젝트의 Core와 Solution에 통합 Manager 기능을 수행하는 클래스입니다.

        Args:
            email (str): 이메일
            project_name (str): 프로젝트명
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Audiobook, Translation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
            storage_solution_dir_path (str): 사용자-프로젝트-솔루션 디렉토리 경로
            _path (str): 포맷팅된 경로
        """
        # Log 초기화
        super().__init__(
            email,
            project_name,
            solution=solution,
            next_solution=next_solution,
            process_number=process_number,
            process_name=process_name)

    # ---------------------------------------
    # --- func-set: common manager ----------
    # --- class-func: storage json 불러오기 ---
    def load_json(self,
                  work: str,
                  common_keys: list,
                  json_keys: list = None) -> str | dict | list:
        """super().read_path_map(work, common_keys)의 json을 불러옵니다.

        Args:
            work (str): "Core" 또는 "Solution" 또는 "Generation"
            common_keys (list): path_map json의 연속된 키 값 (form_keys, file_keys 사용 권장)
            json_keys (list): 불러온 json_data의 연속된 키 값 (json_keys로 사용 권장)

        Returns:
            data 가져오기 (str | dict | list): super().read_path_map(work, common_keys)[json_keys]
        """
        # super().read_path_map(work, common_keys) 파일 불러오기
        with open(super().read_path_map(work, common_keys), "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # json_data에서 json_keys에 해당하는 경로 가져오기
        json_dict = json_data
        for key in json_keys:
            json_dict = json_dict[key]

        return json_dict

    # --------------------------------------
    # --- func-set: storage dir manager ----
    # --- class-func: storage dir 생성하기 ---
    def make_storage_dir(self,
                         work: str,
                         dir_keys: list) -> None:
        """super().read_path_map(work, keys) 디렉토리를 생성합니다.

        Args:
            work (str): "Core" 또는 "Solution" 또는 "Generation"
            dir_keys (list): path_map json의 연속된 키 값 (dir_keys로 사용 권장)

        Effects:
            dir 생성: super().read_path_map(work, dir_keys)
        """
        if not os.path.exists(super().read_path_map(work, dir_keys)):
            os.makedirs(super().read_path_map(work, dir_keys), exist_ok = True)

    # -------------------------------------------------------
    # --- func-set: storage json manager --------------------
    # --- class-func: form json 복사하여 storage json 생성하기 ---
    def create_storage_json(self,
                            work: str,
                            form_keys: list,
                            file_keys: list) -> None:
        """self.form_path의 json을 복사하여 super().read_path_map(work, file_keys)의 json을 생성합니다.

        Args:
            work (str): "Core" 또는 "Solution" 또는 "Generation"
            form_keys (list): path_map json의 연속된 키 값 (form_keys로 사용 권장)
            file_keys (list): path_map json의 연속된 키 값 (file_keys로 사용 권장)

        Effects:
            form file 복사 (json): self.form_path
            storage file 생성 (json): super().read_path_map(work, file_keys)
        """
        if not os.path.exists(super().read_path_map(work, file_keys)):
            with open(super().read_path_map(work, form_keys), "r", encoding="utf-8") as f:
                form_data = json.load(f)
            with open(super().read_path_map(work, file_keys), "w", encoding="utf-8") as f:
                json.dump(form_data, f, ensure_ascii=False, indent=4)

    # --- class-func: storage json 생성하기 및 덮어쓰기 ---
    def save_storage_json(self,
                               work: str,
                               file_keys: list,
                               json_data: dict) -> None:
        """super().read_path_map(work, file_keys)의 json을 저장합니다.

        Args:
            work (str): "Core" 또는 "Solution" 또는 "Generation"
            file_keys (list): path_map json의 연속된 키 값 (file_keys로 사용 권장)
            json_data (dict): 저장할 데이터

        Effects:
            json 저장 (dict): self.json_path
        """
        with open(super().read_path_map(work, file_keys), "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

    # --- class-func: storage json data 추가하기 ---
    def append_storage_data(self,
                            work: str,
                            file_keys: list,
                            json_keys: list,
                            data: dict) -> None:
        """super().read_path_map(work, file_keys)의 json에 데이터를 추가합니다.

        Args:
            work (str): "Core" 또는 "Solution" 또는 "Generation"
            file_keys (list): path_map json의 연속된 키 값 (file_keys로 사용 권장)
            json_keys (list): 불러온 json_data의 연속된 키 값 (json_keys로 사용 권장)
            data (dict): 추가할 데이터

        Effects:
            data 추가 (dict): super().read_path_map(work, file_keys)[json_keys].append(data)
        """
        # super().read_path_map(work, file_keys) 파일 불러오기
        with open(super().read_path_map(work, file_keys), "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # json_data에서 json_keys에 해당하는 경로 가져오기
        json_dict = json_data
        for key in json_keys:
            json_dict = json_dict[key]
        
        # 데이터 추가
        json_dict.append(data)

        # super().read_path_map(work, file_keys) 파일에 저장
        with open(super().read_path_map(work, file_keys), "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

    # --- class-func: storage json data 수정하기 ---
    def set_storage_json(self,
                         work: str,
                         file_keys: list,
                         json_keys: list,
                         data: str | dict | list) -> None:
        """super().read_path_map(work, file_keys)의 json에 데이터를 수정, 변경합니다.

        Args:
            work (str): "Core" 또는 "Solution" 또는 "Generation"
            file_keys (list): path_map json의 연속된 키 값 (file_keys로 사용 권장)
            json_keys (list): 불러온 json_data의 연속된 키 값 (json_keys로 사용 권장)
            data (str | dict | list): 수정, 변경할 데이터

        Effects:
            data 수정, 변경 (str | dict | list): super().read_path_map(work, file_keys)[json_keys].append(data)
        """
        # super().read_path_map(work, file_keys) 파일 불러오기
        with open(super().read_path_map(work, file_keys), "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # json_data에서 json_keys에 해당하는 경로 가져오기
        json_dict = json_data
        last_key = json_keys[-1]
        for key in json_keys[:-1]:
            json_dict = json_dict[key]
        
        # 데이터 수정, 변경
        json_dict[last_key] = data

        # super().read_path_map(work, file_keys) 파일에 저장
        with open(super().read_path_map(work, file_keys), "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

    # -----------------------------------------------
    # --- func-set: storage txt manager -------------
    # --- class-func: storage txt 생성하기 및 덮어쓰기 ---
    def save_storage_txt(self,
                           work: str,
                           file_keys: list,
                           text: str) -> None:
        """super().read_path_map(work, file_keys)의 txt를 저장합니다.

        Args:
            work (str): "Core" 또는 "Solution" 또는 "Generation"
            file_keys (list): path_map json의 연속된 키 값
            text (str): 저장할 텍스트

        Effects:
            txt 저장 (str): super().read_path_map(work, file_keys)
        """
        # super().read_path_map(work, file_keys) 파일 불러오기
        with open(super().read_path_map(work, file_keys), "w", encoding="utf-8") as f:
            f.write(text)

    # --- class-func: storage txt 불러오기 ---
    def load_storage_txt(self,
                         work: str,
                         file_keys: list) -> str:
        """super().read_path_map(work, file_keys)의 txt를 불러옵니다.

        Args:            
            work (str): "Core" 또는 "Solution" 또는 "Generation"
            file_keys (list): path_map json의 연속된 키 값

        Returns:
            text 불러오기 (str): super().read_path_map(work, file_keys)
        """
        # super().read_path_map(work, file_keys) 파일 불러오기
        with open(super().read_path_map(work, file_keys), "r", encoding="utf-8") as f:
            text = f.read()

        return text

    # --------------------------------------
    # --- func-set: pdf manager ------------
    # --- class-func: storage pdf 생성하기 ---

    # --------------------------------------
    # --- func-set: jpg manager ------------
    # --- class-func: storage jpg 생성하기 ---

    # --------------------------------------
    # --- func-set: wav manager ------------
    # --- class-func: storage wav 생성하기 ---

    # --------------------------------------
    # --- func-set: mp3 manager ------------
    # --- class-func: storage mp3 생성하기 ---

if __name__ == "__main__":

    # --- class-test ---
    # 인자 설정
    email = "yeoreum00128@gmail.com3"
    project_name = "글로벌솔루션여름"
    solution = None
    next_solution = None
    process_number = None
    process_name = None

    # 클래스 테스트
    manager = Manager(
        email=email,
        project_name=project_name,
        solution=solution,
        next_solution=next_solution,
        process_number=process_number,
        process_name=process_name)
    
    # 테스트1: dir 생성
    manager.make_storage_dir("Core", ["Dir", "Project"])

    # 테스트2: json 생성
    manager.create_storage_json("Core", ["Form", "Log"], ["File", "Json", "ProjectLog"])

    # 테스트3: 로그 생성
    manager.print_log("Access", ["Log", "Access"], ["Info", "Hello"])

    # 테스트3: 로그 출력 및 생성
    manager.print_log("Solution", ["Log", "Core"], ["Info", "Start"])

    # 3초 쉬기
    import time
    time.sleep(3)

    # 테스트3: 로그 출력 및 생성
    manager.print_log("Solution", ["Log", "Core"], ["Info", "Complete"])