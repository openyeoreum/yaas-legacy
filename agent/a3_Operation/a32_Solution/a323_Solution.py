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

        # solution dir 생성
        self._make_solution_dir()

    # --- class-func: form 초기화 ---
    def _init_form(self):
        """form을 초기화합니다."""
        # form 불러오기
        form_dict = super().load_json("Solution", [self.solution, "Form", self.process_name])

        # info 설정
        info_dict = form_dict["AgentForm"]["Info"]
        self.process_name = info_dict["ProcessName"]
        self.next_solution = info_dict["NextSolution"]
        self.auto_template = info_dict["AutoTemplate"]
        self.file_extension = info_dict["FileExtension"]
        self.main_lang = info_dict["MainLang"]
        self.input_count = info_dict["InputCount"]
        self.completion = info_dict["Completion"]

        # mode 설정
        mode_dict = form_dict["AgentForm"]["Mode"]
        self.response_mode = mode_dict["ResponseMode"]
        self.edit_mode = mode_dict["EditMode"]
        self.outputs_per_input = mode_dict["OutputsPerInput"]
        self.input_count_key = mode_dict["InputCountKey"]
        self.ignore_count_check = mode_dict["IgnoreCountCheck"]
        self.filter_pass = mode_dict["FilterPass"]

        # function 설정
        function_dict = form_dict["AgentForm"]["Function"]
        self.preprocess_inputs = function_dict["PreprocessInputs"]
        self.inputs = function_dict["Inputs"]
        self.preprocess_response = function_dict["PreprocessResponse"]
        self.postprocess_response = function_dict["PostprocessResponse"]
        self.outputs = function_dict["Outputs"]

    # ------------------------------------
    # --- func-set: make dir -------------
    # --- class-func: solution dir 생성 ---
    def _make_solution_dir(self):
        """path_map의 solution dir 경로 키 리스트를 순회하며 solution dir 생성합니다.
        
        Effects:
            solution dir 생성: self.make_storage_dir("Solution", ["Solution", self.solution, "Dir", paths_key])
        """
        # path_map의 solution dir 경로 키 리스트 가져오기
        solution_dir_paths_dict = super().load_json("Operation", ["PathMap"], ["Solution", self.solution, "Dir"])
        paths_key_list = list(solution_dir_paths_dict.keys())

        # paths_key_list 순회하며 solution dir 생성
        if not os.path.exists(super().read_path_map("Solution", ["Solution", self.solution, "Dir", paths_key_list[0]])):
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
                     main_lang: str = "Ko") -> None:
        """solution을 실행 합니다.

        Effects:
            Agent 실행
        """
        # agent 실행
        super().run_agent(
            self.response_mode,
            self.edit_mode,
            self.outputs_per_input,
            self.input_count_key,
            self.ignore_count_check,
            self.filter_pass,

            self._create_inputs,
            self._preprocess_response,
            self._postprocess_response,
            self._create_output)

    # --- class-func: return solution edit ---
    def return_solution_edit(self):
        pass