import os
import json
import sys
sys.path.append("/yaas")

from agent.a3_Operation.a31_Operation.a311_Base import Base

# ======================================================================
# [a312-1] Operation-Manager
# ======================================================================
# class: Manager
# ======================================================================
class Manager(Base):

    # --------------------------------
    # --- class-init -----------------
    # --- class-func: Manager 초기화 ---
    def __init__(self, email: str, project_name: str, work: str, form_keys: list = None, dir_keys: list = None, file_keys: list = None, solution: str = None, next_solution: str = None, process_number: str = None, process_name: str = None, idx: int = None) -> None:
        """사용자-프로젝트의 Core와 Solution에 통합 Manager 기능을 수행하는 클래스입니다.
        """
        # Base 초기화
        super().__init__(email, project_name, work, form_keys=form_keys, dir_keys=dir_keys, file_keys=file_keys, solution=solution, next_solution=next_solution, process_number=process_number, process_name=process_name, idx=idx)

    # -----------------------------------------
    # --- func-set: dir manager ---------------
    # --- class-func: storage dir 생성하기 ------
    def make_dir(self) -> None:
        """self.dir_path 디렉토리를 생성합니다.

        Effects:
            dir 생성: self.dir_path
        """
        if self.dir_path is not None:
            if not os.path.exists(self.dir_path):
                os.makedirs(self.dir_path, exist_ok = True)
        else:
            print("오류처리")

    # -----------------------------------------------------------
    # --- func-set: json manager --------------------------------
    # --- class-func: form json 복사하여 storage json 생성하기 ------
    def create_json(self) -> None:
        """self.form_path의 json을 복사하여 self.file_path의 json을 생성합니다.

        Effects:
            form file 복사 (json): self.form_path
            storage file 생성 (json): self.file_path
        """
        if self.form_path is not None and self.file_path is not None:
            if not os.path.exists(self.file_path):
                with open(self.form_path, "r", encoding="utf-8") as form_file:
                    form_data = json.load(form_file)
                with open(self.file_path, "w", encoding="utf-8") as storage_file:
                    json.dump(form_data, storage_file, ensure_ascii=False, indent=4)
        else:
            print("오류처리")

    # --- class-func: storage json 저장하기 ---
    def overwrite_json(self, json_data: dict) -> None:
        """self.file_path의 json을 저장합니다.

        Args:
            json_data (dict): 저장할 데이터

        Effects:
            json 저장 (dict): self.json_path
        """
        if self.file_path is not None:
            with open(self.file_path, "w", encoding="utf-8") as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)
        else:
            print("오류처리")

    # --- class-func: storage json 불러오기 ---
    def load_json(self) -> dict:
        """self.file_path의 json을 불러옵니다.

        Returns:
            json_data 불러오기 (dict): self.file_path
        """
        if self.file_path is not None:
            with open(self.file_path, "r", encoding="utf-8") as json_file:
                json_data = json.load(json_file)
            return json_data
        else:
            print("오류처리")

    # --- class-func: storage json data 추가하기 ---
    def append_data(self, json_keys: list, data: dict) -> None:
        """self.file_path의 json에 데이터를 추가합니다.

        Effects:
            data 추가 (dict): self.file_path[json_keys].append(data)
        """
        if self.file_path is not None:
            # self.file_path 파일 불러오기
            with open(self.file_path, "r", encoding="utf-8") as json_file:
                json_data = json.load(json_file)

            # json_data에서 json_keys에 해당하는 경로 가져오기
            json_dict = json_data
            for key in json_keys:
                json_dict = json_dict[key]
            
            # 데이터 추가
            json_dict.append(data)

            # self.file_path 파일에 저장
            with open(self.file_path, "w", encoding="utf-8") as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)
        else:
            print("오류처리")

    # --- class-func: storage json data 수정하기 ---
    def set_json(self, json_keys: list, data: str | dict | list) -> None:
        """self.file_path의 json에 데이터를 수정, 변경합니다.

        Effects:
            data 수정, 변경 (str | dict | list): self.file_path[json_keys].append(data)
        """
        if self.file_path is not None:
            # self.file_path 파일 불러오기
            with open(self.file_path, "r", encoding="utf-8") as json_file:
                json_data = json.load(json_file)

            # json_data에서 json_keys에 해당하는 경로 가져오기
            json_dict = json_data
            last_key = json_keys[-1]
            for key in json_keys[:-1]:
                json_dict = json_dict[key]
            
            # 데이터 수정, 변경
            json_dict[last_key] = data

            # self.file_path 파일에 저장
            with open(self.file_path, "w", encoding="utf-8") as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)
        else:
            print("오류처리")

    # --- class-func: storage json data 가져오기 ---
    def read_json(self, json_keys: list) -> str | dict | list:
        """self.file_path의 json에서 데이터를 가져옵니다.

        Returns:
            data 가져오기 (str | dict | list): self.file_path[json_keys]
        """
        if self.file_path is not None:
            # self.file_path 파일 불러오기
            with open(self.file_path, "r", encoding="utf-8") as json_file:
                json_data = json.load(json_file)

            # json_data에서 json_keys에 해당하는 경로 가져오기
            json_dict = json_data
            for key in json_keys:
                json_dict = json_dict[key]
            
            return json_dict
        else:
            print("오류처리")

    # -----------------------------------------
    # --- func-set: txt manager ---------------
    # --- class-func: storage txt 생성하기 ------
    def create_txt(self, text: str) -> None:
        """self.file_path의 txt를 저장합니다.

        Args:
            text (str): 저장할 텍스트

        Effects:
            txt 저장 (str): self.file_path
        """
        if self.file_path is not None:
            with open(self.file_path, "w", encoding="utf-8") as txt_file:
                txt_file.write(text)
        else:
            print("오류처리")

    # --- class-func: storage txt 불러오기 ---
    def load_txt(self) -> str:
        """self.file_path의 txt를 불러옵니다.

        Returns:
            text 불러오기 (str): self.file_path
        """
        if self.file_path is not None:
            with open(self.file_path, "r", encoding="utf-8") as txt_file:
                text = txt_file.read()
            return text
        else:
            print("오류처리")

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
    # core dir 생성 인자
    email = "yeoreum00128@gmail.com"
    project_name = "250911_오늘도불안한엄마들에게"
    work = "solution"
    form_keys = None
    dir_keys = ["Storage", "Upload", "DirPath"]
    file_keys = None
    solution = "ScriptSegmentation"
    next_solution = "Audiobook"
    process_number = "PT01"
    process_name = "ScriptLoad"
    idx = None

    # core dir 생성
    manager = Manager(email, project_name, work, form_keys=form_keys, dir_keys=dir_keys, file_keys=file_keys, solution=solution, next_solution=next_solution, process_number=process_number, process_name=process_name, idx=idx)