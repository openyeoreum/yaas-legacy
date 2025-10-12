import os
import sys
sys.path.append("/yaas")

from agent.a3_Operation.a32_Solution.a322_Agent import Agent

# ======================================================================
# [a333-1] Operation-Solution
# ======================================================================
# class: Solution
# ======================================================================
class Solution(Agent):

    # ---------------------------------
    # --- class-init ------------------
    # --- class-func: Solution 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 solution: str,
                 next_solution: str,
                 process_number: str,
                 process_name: str) -> None:
        """사용자-프로젝트의 Operation에 통합 Solution 기능을 셋팅하는 클래스입니다.

        Attributes:
            email (str): 이메일
            project_name (str): 프로젝트명
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Audiobook, Translation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
        """
        # Agent 초기화
        super().__init__(
            email,
            project_name,
            solution,
            next_solution,
            process_number,
            process_name)

    # --- class-func: solution 디렉토리 생성 ---
    def _make_solution_dir(self):
        """path_map의 solution dir 경로 키 리스트를 순회하며 solution dir 생성합니다.
        
        Effects:
            solution dir 생성: self.make_storage_dir("Solution", ["Solution", self.solution, "Dir", paths_key])
        """
        # path_map의 solution dir 경로 키 리스트 가져오기
        solution_dir_paths_dict = super().load_json("Operation", ["PathMap"], ["Solution", self.solution, "Dir"])
        paths_key_list = list(solution_dir_paths_dict.keys())

        # paths_key_list 순회하며 solution dir 생성
        for paths_key in paths_key_list:
            super().make_storage_dir("Solution", ["Solution", self.solution, "Dir", paths_key])

    # --------------------------------
    # --- func-set: inputs -----------
    # --- class-func: inputs 전처리 ---
    def _preprocess_inputs(self):
        """inputs를 전처리 합니다."""
        pass

    # --- class-func: inputs 생성 ---
    def _create_inputs(self):
        """inputs를 생성 합니다."""
        pass

    # ----------------------------------
    # --- func-set: response -----------
    # --- class-func: response 전처리 ---
    def _preprocess_response(self):
        """response를 전처리 합니다."""
        pass

    # --- class-func: response 후처리 ---
    def _postprocess_response(self):
        """response를 후처리 합니다."""
        pass

    # ------------------------------
    # --- func-set: output ---------
    # --- class-func: output 생성 ---
    def _create_output(self):
        """output을 생성 합니다."""
        pass

    # --------------------------------
    # --- func-set: solution run -----
    # --- class-func: run solution ---
    def run_solution(self,
                     response_mode: bool = True,
                     edit_mode: bool = True,
                     outputs_per_input: int = 1,
                     input_count_key: str = None,
                     ignore_count_check: bool = False,
                     filter_pass: bool = False,
                     main_lang: str = "Ko") -> None:
        """solution을 실행 합니다.

        Args:
            response_mode (bool): response 모드
            edit_mode (bool): 편집 모드
            outputs_per_input (int): 출력 배수
            input_count_key (str): input 수의 기준키
            ignore_count_check (bool): 입력 수 체크 무시 여부
            filter_pass (bool): 필터 오류 3회가 넘어가는 경우 그냥 패스 여부
            main_lang (str): 주요 언어

        Effects:
            Agent 실행
        """
        # Solutionmode 초기화
        # Agent 실행
        super().run_agent(
            self._create_inputs,
            self._preprocess_response,
            self._postprocess_response,
            self._create_output,

            response_mode,
            edit_mode,
            outputs_per_input,
            input_count_key,
            ignore_count_check,
            filter_pass,
            main_lang)

    # --- class-func: return solution edit ---
    def return_solution_edit(self):
        pass