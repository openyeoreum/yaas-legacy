import os
import json
import sys
sys.path.append("/yaas")

from agent.a3_Operation.a31_Operation.a313_Base import Base

# ======================================================================
# [a314-1] Operation-Manager
# ======================================================================
# class: Manager
# ======================================================================
class Manager(Base):

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
        # Base 초기화
        super().__init__(
            email,
            project_name,
            solution=solution,
            next_solution=next_solution,
            process_number=process_number,
            process_name=process_name)

    # -----------------------------------------
    # --- func-set: dir manager ---------------
    # --- class-func: storage dir 생성하기 ------
    def make_dir(self,
                 work: str,
                 dir_keys: list) -> None:
        """self._read_path(work, dir_keys) 디렉토리를 생성합니다.

        Args:
            work (str): "core" 또는 "solution" 또는 "generation"
            dir_keys (list): core_paths 또는 solution_paths 또는 generation_paths json의 연속된 키 값

        Effects:
            dir 생성: self._read_path(work, dir_keys)
        """
        if not os.path.exists(self._read_path(work, dir_keys)):
            os.makedirs(self._read_path(work, dir_keys), exist_ok = True)

    # -----------------------------------------------------------
    # --- func-set: json manager --------------------------------
    # --- class-func: form json 복사하여 storage json 생성하기 ------
    def create_json(self,
                    work: str,
                    form_keys: list,
                    file_keys: list) -> None:
        """self.form_path의 json을 복사하여 self._read_path(work, file_keys)의 json을 생성합니다.

        Args:
            work (str): "core" 또는 "solution" 또는 "generation"
            form_keys (list): core_paths 또는 solution_paths 또는 generation_paths json의 연속된 키 값
            file_keys (list): core_paths 또는 solution_paths 또는 generation_paths json의 연속된 키 값

        Effects:
            form file 복사 (json): self.form_path
            storage file 생성 (json): self._read_path(work, file_keys)
        """
        if not os.path.exists(self._read_path(work, file_keys)):
            with open(self._read_path(work, form_keys), "r", encoding="utf-8") as form_file:
                form_data = json.load(form_file)
            with open(self._read_path(work, file_keys), "w", encoding="utf-8") as storage_file:
                json.dump(form_data, storage_file, ensure_ascii=False, indent=4)

    # --- class-func: storage json 저장하기 ---
    def overwrite_json(self,
                       work: str,
                       file_keys: list,
                       json_data: dict) -> None:
        """self._read_path(work, file_keys)의 json을 저장합니다.

        Args:
            work (str): "core" 또는 "solution" 또는 "generation"
            file_keys (list): core_paths 또는 solution_paths 또는 generation_paths json의 연속된 키 값
            json_data (dict): 저장할 데이터

        Effects:
            json 저장 (dict): self.json_path
        """
        with open(self._read_path(work, file_keys), "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

    # --- class-func: storage json 불러오기 ---
    def load_json(self,
                  work: str,
                  file_keys: list) -> dict:
        """self._read_path(work, file_keys)의 json을 불러옵니다.

        Args:
            work (str): "core" 또는 "solution" 또는 "generation"
            file_keys (list): core_paths 또는 solution_paths 또는 generation_paths json의 연속된 키 값

        Returns:
            json_data 불러오기 (dict): self._read_path(work, file_keys)
        """
        with open(self._read_path(work, file_keys), "r", encoding="utf-8") as json_file:
            json_data = json.load(json_file)
        return json_data

    # --- class-func: storage json data 추가하기 ---
    def append_data(self,
                    work: str,
                    file_keys: list,
                    json_keys: list,
                    data: dict) -> None:
        """self._read_path(work, file_keys)의 json에 데이터를 추가합니다.

        Args:
            work (str): "core" 또는 "solution" 또는 "generation"
            file_keys (list): core_paths 또는 solution_paths 또는 generation_paths json의 연속된 키 값
            json_keys (list): 불러온 json_data의 연속된 키 값
            data (dict): 추가할 데이터

        Effects:
            data 추가 (dict): self._read_path(work, file_keys)[json_keys].append(data)
        """
        # self._read_path(work, file_keys) 파일 불러오기
        with open(self._read_path(work, file_keys), "r", encoding="utf-8") as json_file:
            json_data = json.load(json_file)

        # json_data에서 json_keys에 해당하는 경로 가져오기
        json_dict = json_data
        for key in json_keys:
            json_dict = json_dict[key]
        
        # 데이터 추가
        json_dict.append(data)

        # self._read_path(work, file_keys) 파일에 저장
        with open(self._read_path(work, file_keys), "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

    # --- class-func: storage json data 수정하기 ---
    def set_json(self,
                 work: str,
                 file_keys: list,
                 json_keys: list,
                 data: str | dict | list) -> None:
        """self._read_path(work, file_keys)의 json에 데이터를 수정, 변경합니다.

        Args:
            work (str): "core" 또는 "solution" 또는 "generation"
            file_keys (list): core_paths 또는 solution_paths 또는 generation_paths json의 연속된 키 값
            json_keys (list): 불러온 json_data의 연속된 키 값
            data (str | dict | list): 수정, 변경할 데이터

        Effects:
            data 수정, 변경 (str | dict | list): self._read_path(work, file_keys)[json_keys].append(data)
        """
        # self._read_path(work, file_keys) 파일 불러오기
        with open(self._read_path(work, file_keys), "r", encoding="utf-8") as json_file:
            json_data = json.load(json_file)

        # json_data에서 json_keys에 해당하는 경로 가져오기
        json_dict = json_data
        last_key = json_keys[-1]
        for key in json_keys[:-1]:
            json_dict = json_dict[key]
        
        # 데이터 수정, 변경
        json_dict[last_key] = data

        # self._read_path(work, file_keys) 파일에 저장
        with open(self._read_path(work, file_keys), "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

    # --- class-func: storage json data 가져오기 ---
    def read_json(self,
                  work: str,
                  file_keys: list,
                  json_keys: list) -> str | dict | list:
        """self._read_path(work, file_keys)의 json에서 데이터를 가져옵니다.

        Args:
            work (str): "core" 또는 "solution" 또는 "generation"
            file_keys (list): core_paths 또는 solution_paths 또는 generation_paths json의 연속된 키 값
            json_keys (list): 불러온 json_data의 연속된 키 값

        Returns:
            data 가져오기 (str | dict | list): self._read_path(work, file_keys)[json_keys]
        """
        # self._read_path(work, file_keys) 파일 불러오기
        with open(self._read_path(work, file_keys), "r", encoding="utf-8") as json_file:
            json_data = json.load(json_file)

        # json_data에서 json_keys에 해당하는 경로 가져오기
        json_dict = json_data
        for key in json_keys:
            json_dict = json_dict[key]
        
        return json_dict

    # -----------------------------------------
    # --- func-set: txt manager ---------------
    # --- class-func: storage txt 생성하기 ------
    def create_txt(self,
                   work: str,
                   file_keys: list,
                   text: str) -> None:
        """self._read_path(work, file_keys)의 txt를 저장합니다.

        Args:
            work (str): "core" 또는 "solution" 또는 "generation"
            file_keys (list): core_paths 또는 solution_paths 또는 generation_paths json의 연속된 키 값
            text (str): 저장할 텍스트

        Effects:
            txt 저장 (str): self._read_path(work, file_keys)
        """
        # self._read_path(work, file_keys) 파일 불러오기
        with open(self._read_path(work, file_keys), "w", encoding="utf-8") as txt_file:
            txt_file.write(text)

    # --- class-func: storage txt 불러오기 ---
    def load_txt(self,
                 work: str,
                 file_keys: list) -> str:
        """self._read_path(work, file_keys)의 txt를 불러옵니다.

        Args:            
            work (str): "core" 또는 "solution" 또는 "generation"
            file_keys (list): core_paths 또는 solution_paths 또는 generation_paths json의 연속된 키 값

        Returns:
            text 불러오기 (str): self._read_path(work, file_keys)
        """
        # self._read_path(work, file_keys) 파일 불러오기
        with open(self._read_path(work, file_keys), "r", encoding="utf-8") as txt_file:
            text = txt_file.read()

        return text

    # -----------------------------------------
    # --- func-set: pdf manager ---------------
    # --- class-func: storage pdf 생성하기 ------

    # -----------------------------------------
    # --- func-set: jpg manager ---------------
    # --- class-func: storage jpg 생성하기 ------

    # -----------------------------------------
    # --- func-set: wav manager ---------------
    # --- class-func: storage wav 생성하기 ------

    # -----------------------------------------
    # --- func-set: mp3 manager ---------------
    # --- class-func: storage mp3 생성하기 ------

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
    manager.make_dir("core", ["Dir", "Project"])

    # 테스트2: json 생성
    manager.create_json("core", ["Form", "LogPath"], ["File", "Json", "ProjectLog"])

    # 테스트3: 로그 생성
    manager.print_log("access", ["Log", "Access"], ["Info", "Hello"])

    # 테스트3: 로그 출력 및 생성
    manager.print_log("solution", ["Log", "Core"], ["Info", "Start"])

    # 3초 쉬기
    import time
    time.sleep(3)

    # 테스트3: 로그 출력 및 생성
    manager.print_log("solution", ["Log", "Core"], ["Info", "End"])