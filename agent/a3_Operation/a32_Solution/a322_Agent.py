import os
import re
import shutil
import json
import time
import spacy
import copy
import sys
sys.path.append("/yaas")

from PyPDF2 import PdfReader, PdfWriter
from agent.a3_Operation.a32_Solution.a321_LLM import LLM

# ======================================================================
# [a332-1] Operation-Agent
# ======================================================================
# class: Agent
# ======================================================================
class Agent(LLM):

    # ------------------------------
    # --- class-init ---------------
    # --- class-func: Agent 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 solution: str,
                 next_solution: str,
                 process_number: str,
                 process_name: str,
                 main_lang: str = "Ko") -> None:
        """사용자-프로젝트의 Operation에 통합 Agent 기능을 셋팅하는 클래스입니다.

        Attributes:
            email (str): 이메일
            project_name (str): 프로젝트명
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Audiobook, Translation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
            main_lang (str): 주요 언어 (기본값: "ko")
        """
        # LLM 초기화
        super().__init__(
            email,
            project_name,
            solution,
            next_solution,
            process_number,
            process_name,
            main_lang)

    # ----------------------------------------
    # --- func-set: input --------------------
    # --- class-func: input_list 생성 및 처리 ---
    def _create_input_list(self):
        """input_list를 생성합니다.
        
        Effects:
            input_list 생성 (dict): self.read_path_map("Solution", [self.solution, "File", "Json", "InputList"])
        
        Returns:
            input_list (dict): input_list
        """
        # input_list 존재 여부 확인
        if os.path.exists(self.read_path_map("Solution", [self.solution, "File", "Json", "InputList"])):
            # input_list 불러오기
            input_list = self.load_json("Solution", [self.solution, "File", "Json", "InputList"])
        else:
            # # input_list 생성
            # inputs, comparison_inputs = self.input_list_func()
            inputs = ["test1", "test2", "test3"]
            comparison_inputs = ["test1", "test2", "test3"]

            # input_list 생성
            input_list = []
            for i, input in enumerate(inputs):
                input_list.append({
                    "Id": i + 1,
                    "Input": input,
                    "ComparisonInput": comparison_inputs[i]})
            
            # input_list 저장
            self.save_storage_json("Solution", [self.solution, "File", "Json", "InputList"], input_list)

        return input_list

    # --- class-func: input을 후처리 ---
    def _post_process_input(self):
        """input을 후처리 합니다."""
        pass

    # --- class-func: comparison_input을 후처리 ---
    def _post_process_comparison_input(self):
        """comparison_input을 후처리 합니다."""
        pass

    # -------------------------------------------------------------
    # --- func-set: check, completion -----------------------------
    # --- class-func: process_middle_frame의 파일, 카운트, 완료 체크 ---
    def _check_process_middle_frame(self):
        """process_middle_frame의 파일, 카운트, 완료 체크 합니다.
        
        Returns:
            input_count (int): input_count
            middle_frame_completion (bool): middle_frame_completion
        """
        input_count = 1
        middle_frame_completion = False

        # process_middle_frame이 존재하지 않는 경우
        if not os.path.exists(self.read_path_map("Solution", [self.solution, "File", "Json", "MiddleFrame"])):
            return input_count, middle_frame_completion
        else:
            # process_middle_frame 불러오기
            solution_process_middle_frame = self.load_json("Solution", [self.solution, "File", "Json", "MiddleFrame"])

            # input_count, middle_frame_completion 확인
            next_input_count = solution_process_middle_frame[0]['InputCount'] + 1
            middle_frame_completion = solution_process_middle_frame[0]['Completion']

            return next_input_count, middle_frame_completion

    # --- class-func: solution_edit의 파일, 완료 체크 ---
    def _check_solution_edit(self):
        """solution_edit의 파일, 완료 체크 합니다.

        Returns:
        """
        # - innerfunc: edit check 함수 -
        def edit_check_func(solution_edit, edit_check, edit_response_completion, edit_response_post_process_completion, edit_output_completion):
            # edit_check 확인
            edit_check = True
            
            # edit_response_completion 확인
            if solution_edit[f"{self.process_name}ResponseCompletion"] == 'Completion':
                edit_response_completion = True
            
            # edit_response_post_process_completion 확인
            if solution_edit.get(f"{self.process_name}ResponsePostProcessCompletion") == 'Completion':
                edit_response_post_process_completion = True
            
            # edit_output_completion 확인
            if solution_edit[f"{self.process_name}OutputCompletion"] == 'Completion':
                edit_output_completion = True

            return edit_check, edit_response_completion, edit_response_post_process_completion, edit_output_completion
        # - innerfunc end -

        # edit_check 초기화
        edit_check = False
        edit_response_completion = False
        edit_response_post_process_completion = False
        edit_output_completion = False

        # solution_edit 경로가 존재하는지 확인 후 불러오기
        if os.path.exists(self.read_path_map("Solution", [self.solution, "File", "Json", "Edit"])):
            # solution_edit 체크
            solution_edit = self.load_json("Solution", [self.solution, "File", "Json", "Edit"])

            # 입력 수 체크 안함 (입력의 카운트가 의미가 없는 경우 예시로 IndexDefine 등)
            if self.ignore_count_check:
                if self.process_name in solution_edit.keys():
                    edit_check, edit_response_completion, edit_response_post_process_completion, edit_output_completion = edit_check_func(solution_edit, edit_check, edit_response_completion, edit_response_post_process_completion, edit_output_completion)
            else:
                # 입력 수의 기준키 설정 (InputCount의 수가 단순 데이터 리스트의 총 개수랑 맞지 않는 경우)
                if self.input_count_key:
                    if self.process_name in solution_edit.keys() and solution_edit[self.process_name][-1][self.input_count_key] == self.total_input_count * self.outputs_per_input:
                        edit_check, edit_response_completion, edit_response_post_process_completion, edit_output_completion = edit_check_func(solution_edit, edit_check, edit_response_completion, edit_response_post_process_completion, edit_output_completion)
                
                # 일반적인 입력 수 체크
                else:
                    if self.process_name in solution_edit and len(solution_edit[self.process_name]) == self.total_input_count * self.outputs_per_input:
                        edit_check, edit_response_completion, edit_response_post_process_completion, edit_output_completion = edit_check_func(solution_edit, edit_check, edit_response_completion, edit_response_post_process_completion, edit_output_completion)

        return edit_check, edit_response_completion, edit_response_post_process_completion, edit_output_completion

    # -------------------------------
    # --- func-set: agent run -------
    # --- class-func: agent 초기화 ---
    def _init_agent(self,
                    input_list_func: callable,
                    response_preprocess_func: callable,
                    response_post_process_func: callable,
                    output_func: callable,

                    response_mode: str,
                    edit_mode: bool,
                    auto_template: bool,
                    outputs_per_input: int,
                    input_count_key: str,
                    ignore_count_check: bool,
                    filter_pass: bool) -> None:
        """agent를 초기화 합니다.

        Args:
            input_list_func (callable): 입력 리스트 생성 함수
            response_preprocess_func (callable): 응답 전처리 함수
            response_post_process_func (callable): 응답 후처리 함수
            output_func (callable): 출력 함수

            response_mode (str): LLM 모드 사용 여부 ("Prompt", "Algorithm", "Manual")
            edit_mode (bool): 편집 모드
            auto_template (bool): 자동 템플릿 사용 여부
            outputs_per_input (int): 출력 배수
            input_count_key (str): 입력 수의 기준키
            ignore_count_check (bool): 입력 수 체크 무시 여부
            filter_pass (bool): 필터 오류 3회가 넘어가는 경우 그냥 패스 여부
        
        Effects:
            input_list 생성
            total_input_count 설정
            input_count 및 middle_frame_completion 설정
            edit_check 및 edit_response_completion 및 edit_response_post_process_completion 및 edit_output_completion 설정

        Attributes:
            input_list_func (callable): 입력 리스트 생성 함수
            response_preprocess_func (callable): 응답 전처리 함수
            response_post_process_func (callable): 응답 후처리 함수
            output_func (callable): 출력 함수

            response_mode (str): LLM 모드 사용 여부 ("Prompt", "Algorithm", "Manual")
            edit_mode (bool): 편집 모드
            auto_template (bool): 자동 템플릿 사용 여부
            outputs_per_input (int): 출력 배수
            input_count_key (str): 입력 수의 기준키
            ignore_count_check (bool): 입력 수 체크 무시 여부
            filter_pass (bool): 필터 오류 3회가 넘어가는 경우 그냥 패스 여부

            input_list (list): 입력 리스트
            total_input_count (int): 입력 수
            input_count (int): 입력 수
            middle_frame_completion (bool): middle_frame_completion
            edit_check (bool): edit_check
            edit_response_completion (bool): edit_response_completion
            edit_response_post_process_completion (bool): edit_response_post_process_completion
            edit_output_completion (bool): edit_output_completion
        """
        # attributes 설정
        # func 설정
        self.input_list_func = input_list_func
        self.response_preprocess_func = response_preprocess_func
        self.response_post_process_func = response_post_process_func
        self.output_func = output_func

        # mode 설정
        self.response_mode = response_mode
        self.edit_mode = edit_mode
        self.auto_template = auto_template
        self.outputs_per_input = outputs_per_input
        self.input_count_key = input_count_key
        self.ignore_count_check = ignore_count_check
        self.filter_pass = filter_pass

        # input_list 설정
        self.input_list = self._create_input_list()
        self.total_input_count = len(self.input_list)

        # input_count 및 middle_frame_completion 설정
        self.input_count, self.middle_frame_completion = self._check_process_middle_frame()
        self.edit_check, self.edit_response_completion, self.edit_response_post_process_completion, self.edit_output_completion = self._check_solution_edit()

    # --- class-func: agent 실행 ---
    def run_agent(self,
                  input_list_func: callable = None,
                  response_preprocess_func: callable = None,
                  response_post_process_func: callable = None,
                  output_func: callable = None,

                  response_mode: bool = True,
                  edit_mode: bool = True,
                  auto_template: bool = True,
                  outputs_per_input: int = 1,
                  input_count_key: str = None,
                  ignore_count_check: bool = False,
                  filter_pass: bool = False) -> None:
        """agent를 실행합니다.

        Args:
            input_list_func (callable): 입력 리스트 생성 함수
            response_preprocess_func (callable): 응답 전처리 함수
            response_post_process_func (callable): 응답 후처리 함수
            output_func (callable): 출력 함수

            response_mode (str): LLM 모드 사용 여부 ("Prompt", "Algorithm", "Manual")
            edit_mode (bool): 편집 모드 (기본값: True)
            auto_template (bool): 자동 템플릿 사용 여부 (기본값: True)
            outputs_per_input (int): 출력 배수 (기본값: 1)
            input_count_key (str): 입력 수의 기준키 (기본값: None)
            ignore_count_check (bool): 입력 수 체크 무시 여부 (기본값: False)
            filter_pass (bool): 필터 오류 3회가 넘어가는 경우 그냥 패스 여부 (기본값: False)
        """
        # run 초기화
        self._init_agent(input_list_func,
            response_preprocess_func,
            response_post_process_func,
            output_func,
            response_mode,
            edit_mode,
            auto_template,
            outputs_per_input,
            input_count_key,
            ignore_count_check,
            filter_pass)

        # edit_check 확인
        if not self.edit_check:
            if not self.middle_frame_completion:
                for i in range(self.input_count - 1, self.total_input_count):
                    ## Input 생성
                    input_count = self.input_list[i]['Id']
                    input = self.input_list[i]['Input']
                    comparison_input = self.input_list[i]['ComparisonInput']
                    memory_note = self.input_list[i]['MemoryNote']

                    if self.response_mode == "Prompt":
                        ## Response 생성
                        response = self.request_llm(input, self.memory_note, input_count, self.total_input_count)
                    if self.response_mode in ["Algorithm", "Manual"]:
                        response = input

                    ## DataFrame 저장
                    self._update_process_data_frame(input_count, response)

            ## Edit 저장
            self._update_solution_edit()
            print(f"[ {self.ProcessInfo}Update 완료 ]\n")

            if self.edit_mode == "Manual":
                sys.exit(f"[ {self.ProjectName}_Script_Edit 생성 완료 -> {self.ProcessName}: (({self.ProcessName}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({self.ProcessName}Completion: Completion))으로 변경 ]\n\n{self.SolutionEditPath}")

        if self.edit_mode == "Manual":
            if self.edit_check:
                if not self.edit_response_completion:
                    ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                    sys.exit(f"[ {self.ProjectName}_Script_Edit -> {self.ProcessName}: (({self.ProcessName}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({self.ProcessName}Completion: Completion))으로 변경 ]\n\n{self.SolutionEditPath}")
        if self.edit_response_completion:
            print(f"[ {self.ProcessInfo}Update는 이미 완료됨 ]\n")

        ## Edit 불러오기
        SolutionEdit = self._load_edit()

        ## Response 후처리
        if self.edit_response_post_process_completion:
            print(f"[ {self.ProcessInfo}Response 후처리는 이미 완료됨 ]\n")
        else:
            self._response_post_process(SolutionEdit)

        ## Output 실행
        if self.edit_output_completion:
            print(f"[ {self.ProcessInfo}Output은 이미 완료됨 ]\n")
        else:
            self._create_output(SolutionEdit)

        return SolutionEdit

if __name__ == "__main__":

    # --- class-test ---
    # 인자 설정
    email = "yeoreum00128@gmail.com"
    project_name = "글로벌솔루션여름"
    solution = "ScriptSegmentation"
    next_solution = "Audiobook"
    process_number = "P99"
    process_name = "PDFMainLangCheck"

    # 클래스 테스트
    agent = Agent(
        email,
        project_name,
        solution,
        next_solution,
        process_number,
        process_name)