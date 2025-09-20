import os
import json
import sys
sys.path.append("/yaas")

from agent.a3_Operation.a31_Operation.a311_Base import Base

# ======================================================================
# [a312-1] Operation-CRUD
# ======================================================================
# class: CRUD
# ======================================================================

class CRUD(Base):

    # -----------------------------
    # --- class-init --------------
    # --- class-func: CRUD 초기화 ---
    def __init__(self) -> None:
        """사용자-프로젝트의 Core와 Solution에 통합 CRUD 기능을 수행하는 클래스입니다.
        """

    # --- class-func: user_dir 생성 ---
    def make_user_dir(self) -> None:
        """사용자 디렉토리 /{email}을 생성합니다.

        Effects:
            dir 생성: /{email}
        """

    # --- class-func: user_file 생성 ---
    def build_user_file(self) -> None:
        """사용자 디렉토리 내에 파일을 생성합니다.

        Effects:
            file 복사/생성 (json): _Form.json -> {email}_user_.json
        """

    # --- class-func: user_data 작성 ---
    def write_user_data(self) -> None:
        """사용자 디렉토리 내 파일의 내용을 작성합니다.

        Effects:
            data 작성 (str | dict | list): {email}_user_.json
        """

    # --- class-func: user_data 읽기 ---
    def read_user_data(self) -> str | dict | list:
        """사용자 디렉토리 내 파일의 내용을 읽습니다.

        Returns:
            data (str | dict | list): {email}_user_.json
        """

    # --- class-func: user_data 업데이트 ---
    def update_user_data(self) -> None:
        """사용자 디렉토리 내 파일의 내용을 수정/변경합니다.

        Effects:
            data 수정/변경 (str | dict | list): {email}_user_.json
        """


    # ------------------------------------
    # --- func-set: core -----------------
    # --- class-func: core_dir 생성 ---
    def make_core_dir(self) -> None:
        """프로젝트 디렉토리 /{project_name}을 생성합니다.

        Effects:
            dir 생성: /{project_name}
        """

    # --- class-func: core_file 생성 ---
    def build_core_file(self) -> None:
        """
        """

    # --- class-func: core_data 작성 ---
    def write_core_data(self) -> None:
        """
        """

    # --- class-func: core_data 읽기 ---
    def read_core_data(self) -> str | dict | list:
        """
        """

    # --- class-func: core_data 업데이트 ---
    def update_core_data(self) -> None:
        """
        """

    # ------------------------------------
    # --- func-set: solution -------------
    # --- class-func: solution_dir 생성 ---
    def make_solution_dir(self) -> None:
        """
        """

    # --- class-func: solution_file 생성 ---
    def build_solution_file(self) -> None:
        """
        """

    # --- class-func: solution_data 작성 ---
    def write_solution_data(self) -> None:
        """
        """

    # --- class-func: solution_data 읽기 ---
    def read_solution_data(self) -> str | dict | list:
        """
        """

    # --- class-func: solution_data 업데이트 ---
    def update_solution_data(self) -> None:
        """
        """