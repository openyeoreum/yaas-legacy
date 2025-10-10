import os
import re
import json
import spacy
import copy
import sys
sys.path.append("/yaas")

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
                 process_name: str) -> None:
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
            process_name)

    # --- class-func: function 초기화 ---
    def _init_function(self,
                       inputs_func: callable,
                       preprocess_response_func: callable,
                       postprocess_response_func: callable,
                       output_func: callable) -> None:
        """사용자-프로젝트의 Operation에 통합 Agent의 function을 초기화합니다.

        Args:
            inputs_func (callable): inputs_func
            preprocess_response_func (callable): preprocess_response_func
            postprocess_response_func (callable): postprocess_response_func
            output_func (callable): output_func

        Attributes:
            inputs_func (callable): inputs_func
            preprocess_response_func (callable): preprocess_response_func
            postprocess_response_func (callable): postprocess_response_func
            output_func (callable): output_func
        """

        # attributes 설정
        self.inputs_func = inputs_func
        self.preprocess_response_func = preprocess_response_func
        self.postprocess_response_func = postprocess_response_func
        self.output_func = output_func

    # --- class-func: mode 초기화 ---
    def _init_mode(self,
                   response_mode: str,
                   edit_mode: bool,
                   outputs_per_input: int,
                   input_count_key: str,
                   ignore_count_check: bool,
                   filter_pass: bool,
                   main_lang: str = "Ko") -> None:
        """사용자-프로젝트의 Operation에 통합 Agent의 mode을 초기화합니다.

        Args:
            response_mode (str): response_mode
            edit_mode (bool): edit_mode
            outputs_per_input (int): outputs_per_input
            input_count_key (str): input_count_key
            ignore_count_check (bool): ignore_count_check
            filter_pass (bool): filter_pass
            main_lang (str): main_lang

        Attributes:
            response_mode (str): response_mode
            edit_mode (bool): edit_mode
            outputs_per_input (int): outputs_per_input
            input_count_key (str): input_count_key
            ignore_count_check (bool): ignore_count_check
            filter_pass (bool): filter_pass
            main_lang (str): main_lang
        """
        # LLM main_lang 초기화
        super()._init_main_lang(main_lang)

        # attributes 설정
        self.response_mode = response_mode
        self.edit_mode = edit_mode
        self.outputs_per_input = outputs_per_input
        self.input_count_key = input_count_key
        self.ignore_count_check = ignore_count_check
        self.filter_pass = filter_pass

    # ----------------------------------------
    # --- func-set: requset input ------------
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
            # input_list 생성
            inputs, comparison_inputs = self.inputs_func()

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
    def _postprocess_input(self):
        """input을 후처리 합니다."""
        pass

    # --- class-func: comparison_input을 후처리 ---
    def _postprocess_comparison_input(self):
        """comparison_input을 후처리 합니다."""
        pass

    # ----------------------------------------------------------------------
    # --- func-set: check, completion --------------------------------------
    # --- class-func: solution_process_middle_frame의 파일, 카운트, 완료 체크 ---
    def _check_process_middle_frame(self):
        """process_middle_frame의 파일, 카운트, 완료 체크 합니다.
        
        Returns:
            input_count (int): input_count
            middle_frame_completion (bool): middle_frame_completion
        """
        input_count = 1
        middle_frame_completion = False

        # solution_process_middle_frame이 존재 여부 확인
        if os.path.exists(self.read_path_map("Solution", [self.solution, "File", "Json", "MiddleFrame"])):
            solution_process_middle_frame = self.load_json("Solution", [self.solution, "File", "Json", "MiddleFrame"])

            # input_count, middle_frame_completion 확인
            next_input_count = solution_process_middle_frame[0]['InputCount'] + 1
            middle_frame_completion = solution_process_middle_frame[0]['Completion']

            return next_input_count, middle_frame_completion
        else:
            return input_count, middle_frame_completion

    # --- class-func: solution_edit의 파일, 완료 체크 ---
    def _check_solution_edit(self):
        """solution_edit의 파일, 완료 체크 합니다.

        Returns:
        """
        # - innerfunc: edit check 함수 -
        def edit_check_func(solution_edit, edit_check, edit_response_completion, edit_response_postprocess_completion, edit_output_completion):
            # edit_check 확인
            edit_check = True
            
            # edit_response_completion 확인
            if solution_edit[f"{self.process_name}ResponseCompletion"] == 'Completion':
                edit_response_completion = True
            
            # edit_response_postprocess_completion 확인
            if solution_edit.get(f"{self.process_name}ResponsePostProcessCompletion") == 'Completion':
                edit_response_postprocess_completion = True
            
            # edit_output_completion 확인
            if solution_edit[f"{self.process_name}OutputCompletion"] == 'Completion':
                edit_output_completion = True

            return edit_check, edit_response_completion, edit_response_postprocess_completion, edit_output_completion
        # - innerfunc end -

        # edit_check 초기화
        edit_check = False
        edit_response_completion = False
        edit_response_postprocess_completion = False
        edit_output_completion = False

        # solution_edit 존재 여부 확인
        if os.path.exists(self.read_path_map("Solution", [self.solution, "File", "Json", "Edit"])):
            # solution_edit 체크
            solution_edit = self.load_json("Solution", [self.solution, "File", "Json", "Edit"])

            # 입력 수 체크 안함 (입력의 카운트가 의미가 없는 경우 예시로 IndexDefine 등)
            if self.ignore_count_check:
                if self.process_name in solution_edit.keys():
                    edit_check, edit_response_completion, edit_response_postprocess_completion, edit_output_completion = edit_check_func(solution_edit, edit_check, edit_response_completion, edit_response_postprocess_completion, edit_output_completion)
            else:
                # 입력 수의 기준키 설정 (InputCount의 수가 단순 데이터 리스트의 총 개수랑 맞지 않는 경우)
                if self.input_count_key:
                    if self.process_name in solution_edit.keys() and solution_edit[self.process_name][-1][self.input_count_key] == self.total_input_count * self.outputs_per_input:
                        edit_check, edit_response_completion, edit_response_postprocess_completion, edit_output_completion = edit_check_func(solution_edit, edit_check, edit_response_completion, edit_response_postprocess_completion, edit_output_completion)
                
                # 일반적인 입력 수 체크
                else:
                    if self.process_name in solution_edit and len(solution_edit[self.process_name]) == self.total_input_count * self.outputs_per_input:
                        edit_check, edit_response_completion, edit_response_postprocess_completion, edit_output_completion = edit_check_func(solution_edit, edit_check, edit_response_completion, edit_response_postprocess_completion, edit_output_completion)

        return edit_check, edit_response_completion, edit_response_postprocess_completion, edit_output_completion

    # -----------------------------------
    # --- func-set: response filter ------
    # --- class-func: response filter ---
    def _response_filter(self, response: str, comparison_input: str, response_structure: dict) -> dict:
        """response filter를 수행합니다.

        Args:
            response (str): response
            comparison_input: str: comparison_input
            response_structure (dict): response_structure

        Effects:
            response filter 수행 (dict): self.response_filter(response, comparison_input, response_structure)

        Returns:
            filtered_response (dict): filtered_response
        """
        # filter1: json 포멧화
        # - innerfunc: json 형식 체크 함수 -
        def format_json(response: str) -> str:
            """response를 json으로 포맷팅하여 반환합니다.
            
            Returns:
                response (dict): json 형식의 response
            """
            try:
                filtered_response = json.loads(response)
                return filtered_response
            except json.JSONDecodeError:
                return "JsonFormatError: 응답 형식이 (Json)이 아닙니다"
        # - innerfunc end -

        # Filter2: filtered_response 전처리
        # NOTE: filtered_response 전처리도 values_check에 포함시킬지 고민

        # filter3: key 체크
        # - innerfunc: key 체크 함수 -
        def check_key(filtered_response: dict, response_structure: dict) -> dict:
            """response_structure에 맞는 key 체크를 실행합니다.

            Args:
                filtered_response (dict): filtered_response
                response_structure (dict): response_structure

            Returns:
                filtered_response (dict): filtered_response
            """
            # type map 정의
            type_map = {
                "int": int,
                "str": str,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict
            }
            value_type = type_map.get(response_structure["ValueType"])

            if filtered_response and response_structure["Key"] in filtered_response:
                if value_type == "int" and isinstance(filtered_response[response_structure["Key"]], str):
                    if filtered_response[response_structure["Key"]].isdigit() or (filtered_response[response_structure["Key"]].startswith("-") and filtered_response[response_structure["Key"]][1:].isdigit()):
                        try:
                            filtered_response[response_structure["Key"]] = int(filtered_response[response_structure["Key"]])
                        except ValueError:
                            return f"KeyTypeError: ({response_structure['Key']}) 키의 데이터 타입이 ({value_type})가 아닙니다"
                
                if isinstance(filtered_response[response_structure["Key"]], value_type):
                    return filtered_response
                else:
                    return f"KeyTypeError: ({response_structure['Key']}) 키의 데이터 타입이 ({value_type})가 아닙니다"
            else:
                return f"CheckKeyError: ({response_structure['Key']}) 키가 누락되었습니다"
        # - innerfunc end -

        # filter4: values 체크
        # - innerfunc: values 체크 함수 -
        def values_check(filtered_response: dict, response_structure: dict, comparison_input: str) -> dict:
            """response_structure에 맞는 value 체크를 실행합니다.

            Args:
                filtered_response (dict): filtered_response
                response_structure (dict): response_structure
                comparison_input (str): comparison_input

            Returns:
                filtered_response (dict): filtered_response
            """
            _value = filtered_response[response_structure["Key"]]
            for value_check_dict in response_structure["ValueCheckList"]:
                value_check = value_check_dict["ValueCheck"]
                # value check item 처리
                if isinstance(value_check_dict['ValueCheckItem'], list):
                    value_check_item = value_check_dict['ValueCheckItem']
                else:
                    value_check_item = [item.strip() for item in str(value_check_dict['ValueCheckItem']).split(",")]
                # comparison input 처리
                if isinstance(comparison_input, list):
                    comparison_input_item = comparison_input
                else:
                    comparison_input_item = [item.strip() for item in str(comparison_input).split(",")]

                # filter4-1: listDataAnswerRangeCheck, 벨류가 리스트인 경우 객관식 답의 범주 체크 (ValueCheckItem: 객관식 답의 범주 리스트)
                if value_check == "listDataAnswerRangeCheck":
                    value_check_target = comparison_input_item if value_check_item[0] in ["", "ComparisonInput"] else value_check_item

                    for value in _value:
                        if value not in value_check_target:
                            return f"ListDataAnswerRangeCheckError: ({value}) 항목은 ({value_check_target})에 포함되지 않습니다"

                # Filter4-2: listDataInclusionCheck, 벨류가 리스트인 경우 꼭 포함되어야할 데이터 체크 (ValueCheckItem: 포함되어야할 데이터 리스트)
                if value_check == "listDataInclusionCheck":
                    value_check_target = comparison_input_item if value_check_item[0] in ["", "ComparisonInput"] else value_check_item

                    for check_item in value_check_target:
                        if check_item not in _value:
                            return f"ListDataInclusionCheckError: ({check_item}) 항목이 ({_value})에 포함되어야 합니다"

                # filter4-3: listDataExclusionCheck, 벨류가 리스트인 경우 꼭 포함되지 말아야할 데이터 체크 (ValueCheckItem: 포함되지 말아야할 데이터 리스트)
                if value_check == "listDataExclusionCheck":
                    value_check_target = comparison_input_item if value_check_item[0] in ["", "ComparisonInput"] else value_check_item

                    for check_item in value_check_target:
                        if check_item in _value:
                            return f"ListDataExclusionCheckError: ({check_item}) 항목이 ({_value})에 포함되어서는 안됩니다"

                # filter4-4: listDataLengthCheck, 벨류가 리스트인 경우 리스트의 길이 체크 (ValueCheckItem: 리스트의 길이 [정수])
                if value_check == "listDataLengthCheck":
                    value_check_target = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]

                    if len(_value) != int(value_check_target):
                        return f"ListDataLengthCheckError: ({_value}) 의 개수는 ({value_check_target}) 개가 되어야 합니다."

                # filter4-5: listDataRangeCheck, 벨류가 리스트인 경우 리스트 길이의 범위 체크 (ValueCheckItem: 리스트의 길이 범위 [최소, 최대])
                if value_check == "listDataRangeCheck":
                    min_target = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]
                    max_target = comparison_input_item[1] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[1]

                    if not (int(min_target) <= len(_value) <= int(max_target)):
                        return f"ListDataRangeCheckError: ({_value}) 의 개수는 ({min_target}) 개 이상 ({max_target}) 개 이하여야 합니다."

                # filter4-6: strDataAnswerRangeCheck, 벨류가 문자인 경우 객관식 답의 범주 체크 (ValueCheckItem: 객관식 답의 범주 리스트)
                if value_check == "strDataAnswerRangeCheck":
                    value_check_target = comparison_input_item if value_check_item[0] in ["", "ComparisonInput"] else value_check_item

                    if _value not in value_check_target:
                        return f"StrDataAnswerRangeCheckError: ({_value}) 항목은 ({value_check_target})에 포함되지 않습니다"

                # filter4-7: strDataInclusionCheck, 벨류가 문자인 경우 꼭 포함되어야할 문자 체크 (ValueCheckItem: 포함되어야할 문자 리스트)
                if value_check == "strDataInclusionCheck":
                    value_check_target = comparison_input_item if value_check_item[0] in ["", "ComparisonInput"] else value_check_item

                    for check_item in value_check_target:
                        if check_item not in _value:
                            return f"StrDataInclusionCheckError: ({check_item}) 항목이 ({_value})에 포함되어야 합니다"

                # filter4-8: strDataExclusionCheck, 벨류가 문자인 경우 꼭 포함되지 말아야할 문자 체크 (ValueCheckItem: 포함되지 말아야할 문자 리스트)
                if value_check == "strDataExclusionCheck":
                    value_check_target = comparison_input_item if value_check_item[0] in ["", "ComparisonInput"] else value_check_item

                    for check_item in value_check_target:
                        if check_item in _value:
                            return f"StrDataExclusionCheckError: ({check_item}) 항목이 ({_value})에 포함되어서는 안됩니다"

                # filter4-9: strDataSameCheck, 벨류가 문자인 경우 문자 일치 여부 체크 (ValueCheckItem: 비교할 문자)
                if value_check == "strDataSameCheck":
                    value_check_target = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]

                    if _value != value_check_target:
                        return f"StrDataSameCheckError: ({_value}) 는 ({value_check_target}) 여야 합니다"

                # filter4-10: strCleanDataSameCheck, 특수문자/공백 제거 후 동일성 체크
                if value_check == "strCleanDataSameCheck":
                    value_check_target = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]

                    clean_value = re.sub(r'\W+', '', _value, flags=re.UNICODE)
                    clean_value_check_target = re.sub(r'\W+', '', value_check_target, flags=re.UNICODE)
                    if clean_value != clean_value_check_target:
                        return f"StrCleanDataSameCheckError: ({_value}) 는 ({value_check_target}) 여야 합니다"

                # filter4-11: strDataLengthCheck, 문자열 길이 일치 여부 체크
                if value_check == "strDataLengthCheck":
                    value_check_target = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]

                    if len(_value) != int(value_check_target):
                        return f"StrDataLengthCheckError: ({_value}) 의 개수는 ({value_check_target}) 개가 되어야 합니다."

                # filter4-12: strCleanDataLengthCheck, 특수문자/공백 제거 후 문자열 길이 일치 여부 체크
                if value_check == "strCleanDataLengthCheck":
                    value_check_target = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]

                    clean_value = re.sub(r'\W+', '', _value, flags=re.UNICODE)
                    clean_value_check_target = re.sub(r'\W+', '', value_check_target, flags=re.UNICODE)
                    if len(clean_value) != len(clean_value_check_target):
                        return f"StrCleanDataLengthCheckError: ({_value}) 의 개수는 ({value_check_target}) 개가 되어야 합니다."

                # filter4-13: strDataRangeCheck, 문자열 길이의 범위 체크 (ValueCheckItem: 문자열의 길이 범위 [최소, 최대])
                if value_check == "strDataRangeCheck":
                    min_target = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]
                    max_target = comparison_input_item[1] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[1]

                    if not (int(min_target) <= len(_value) <= int(max_target)):
                        return f"StrDataRangeCheckError: ({_value}) 의 개수는 ({min_target}) 개 이상 ({max_target}) 개 이하여야 합니다."

                # filter4-14: strDataStartEndInclusionCheck, 문자열 처음과 끝에 존재해야하는 필수 문자 체크 (ValueCheckItem: 문자열 처음과 끝에 존재해야하는 문자 리스트 [시작 문자, 끝 문자], 시작 문자 또는 끝 문자중 존재하지 않는 부분은 빈문자 ""로 작성)
                if value_check == "strDataStartEndInclusionCheck":
                    start_target = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]
                    end_target = comparison_input_item[1] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[1]

                    if start_target not in _value[0:len(start_target)+10] or end_target not in _value[-len(end_target)-10:-1]:
                        return f"StrDataStartEndInclusionCheckError: ({_value}) 는 ({start_target}) 로 시작하고 ({end_target}) 로 끝나야 합니다"

                # filter4-15: strDataStartEndExclusionCheck, 문자열 처음과 끝에 존재하지 말아야할 문자 체크 (ValueCheckItem: 문자열 처음과 끝에 존재하지 말아야할 문자 리스트 [시작 문자, 끝 문자], 시작 문자 또는 끝 문자중 존재하지 않는 부분은 빈문자 ""로 작성)
                if value_check == "strDataStartEndExclusionCheck":
                    start_check_item = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]
                    end_check_item = comparison_input_item[1] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[1]

                    start_check_item = "(포@함-방$지_문^구#)" if len(start_check_item) == 0 else start_check_item
                    end_check_item = "(포@함-방$지_문^구#)" if len(end_check_item) == 0 else end_check_item

                    if start_check_item in _value[0:len(start_check_item)+20] or end_check_item in _value[-len(end_check_item)-20:-1]:
                        return f"StrDataStartEndExclusionCheckError: ({_value}) 는 ({start_check_item}) 로 시작하고 ({end_check_item}) 로 끝나지 않아야 합니다"

                # filter4-16: strMainLangCheck, 문자열 주요 언어 체크 (ValueCheckItem: 주요 언어 코드 ko, en, ja, zh 등)
                if value_check == "strMainLangCheck":
                    # - inner-innerfunc: spaCy 기반 언어 감지 함수 -
                    def detect_lang_with_spacy(text):
                        """spaCy 기반 언어 감지 (가능하면 SpacyFastlang, 안되면 SpacyLangdetect), 모두 실패하면 간단한 유니코드 휴리스틱으로 추정, 반환: ISO 639-1 첫글자 대문자 코드(가능한 경우), 실패 시 'unknown'
                        Args:
                            text (str): 텍스트

                        Returns:
                            str: 언어 코드 (예: Ko, En)
                        """
                        # spacy_fastlang 및 spacy_langdetect 설치 여부 확인
                        try:
                            from spacy_fastlang import Language as FastLang  # type: ignore
                        except ImportError:
                            FastLang = None

                        try:
                            from spacy_langdetect import LanguageDetector  # type: ignore
                        except ImportError:
                            LanguageDetector = None
                        
                        # spacy_fastlang 시도
                        try:
                            if FastLang is not None:
                                nlp = spacy.blank("xx")
                                if "language_detector" not in nlp.pipe_names:
                                    nlp.add_pipe("language_detector")
                                doc = nlp(text)
                                lang_attr = getattr(doc._, "language", None)
                                if isinstance(lang_attr, str) and 2 <= len(lang_attr) <= 3:
                                    # 수정된 부분 1
                                    return lang_attr.lower().capitalize()
                                if isinstance(lang_attr, dict) and "language" in lang_attr:
                                    # 수정된 부분 2
                                    return str(lang_attr["language"]).lower().capitalize()
                        except Exception:
                            pass

                        # spacy_langdetect 시도
                        try:
                            if LanguageDetector is not None:
                                @spacy.Language.factory("language_detector")
                                def create_lang_detector(nlp, name):
                                    return LanguageDetector()

                                nlp = spacy.blank("xx")
                                if "language_detector" not in nlp.pipe_names:
                                    nlp.add_pipe("language_detector")
                                doc = nlp(text)
                                lang_attr = getattr(doc._, "language", None)
                                if isinstance(lang_attr, dict) and "language" in lang_attr:
                                    # 수정된 부분 3
                                    return str(lang_attr["language"]).lower().capitalize()
                        except Exception:
                            pass

                        # 휴리스틱(유니코드 범위 기반 간단 추정)
                        try:
                            hangul = len(re.findall(r"[가-힣]", text))
                            kana = len(re.findall(r"[\u3040-\u309F\u30A0-\u30FF]", text))
                            hanzi = len(re.findall(r"[\u4E00-\u9FFF]", text))
                            latin = len(re.findall(r"[A-Za-z]", text))

                            counts = {
                                "ko": hangul,
                                "ja": kana,
                                "zh": hanzi,
                                "en": latin,
                            }
                            best = max(counts.items(), key=lambda x: x[1])
                            # 수정된 부분 4
                            return best[0].capitalize() if best[1] > 0 else "Unknown"
                        except Exception:
                            return "Unknown"
                    # - inner-innerfunc end -

                    # filter4-16-2: 주요 언어 체크
                    value_check_target = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]
                    value_check_target = value_check_target.lower()

                    detected_lang = detect_lang_with_spacy(_value).lower()
                    if detected_lang != value_check_target:
                        return f"StrMainLangCheckError: ({_value}) 의 주요 언어는 ({value_check_target}) 여야 합니다 (감지된 언어: {detected_lang})"

                # filter4-17: intDataAnswerRangeCheck, 벨류가 숫자인 경우 답의 범주 체크 (ValueCheckItem: 객관식 답의 범주 리스트)
                if value_check == "intDataAnswerRangeCheck":
                    value_check_target = comparison_input_item if value_check_item[0] in ["", "ComparisonInput"] else value_check_item
                    value_check_target = [int(item) for item in value_check_target]

                    if isinstance(_value, int) or (isinstance(_value, str) and _value.isdigit()):
                        filtered_response[response_structure["Key"]] = int(_value)
                        if _value not in value_check_target:
                            return f"IntDataAnswerRangeCheckError: ({_value}) 항목은 ({value_check_target})에 포함되지 않습니다"
                
                # filter4-18: intDataRangeCheck, 벨류가 숫자인 경우 수의 범위 체크 (ValueCheckItem: 수의 범위 [최소, 최대])
                if value_check == "intDataRangeCheck":
                    min_target = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]
                    max_target = comparison_input_item[1] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[1]

                    if isinstance(_value, int) or (isinstance(_value, str) and _value.isdigit()):
                        filtered_response[response_structure["Key"]] = int(_value)
                        if not (int(min_target) <= _value <= int(max_target)):
                            return f"IntDataRangeCheckError: ({_value}) 의 개수는 ({min_target}) 개 이상 ({max_target}) 개 이하여야 합니다."
                
                # filter4-19: intDataSameCheck, 벨류가 숫자인 경우 수 일치 여부 체크 (ValueCheckItem: 비교할 숫자)
                if value_check == "intDataSameCheck":
                    value_check_target = comparison_input_item[0] if value_check_item[0] in ["", "ComparisonInput"] else value_check_item[0]

                    if isinstance(_value, int) or (isinstance(_value, str) and _value.isdigit()):
                        filtered_response[response_structure["Key"]] = int(_value)
                        self.print_log("Task", ["Log", "Function"], ["Info", "Error"], function_name="agent._response_filter.value_check -> intDataSameCheck", _print=f"{int(value_check_target)} -> {int(_value)}")
                        if _value != int(value_check_target):
                            return f"IntDataSameCheckError: ({filtered_response[response_structure["Key"]]}) 는 ({value_check_target}) 여야 합니다."

            return filtered_response
        # - innerfunc end -

        # filter error1: main_check
        # filter error1-1: format_json
        filtered_response = format_json(response)
        if isinstance(filtered_response, str):
            filtered_response_error_message = filtered_response
            return filtered_response_error_message
        
        # filter error1-2: main_check_key
        filtered_response = check_key(filtered_response, response_structure)
        if isinstance(filtered_response, str):
            filtered_response_error_message = filtered_response
            return filtered_response_error_message
               
        # filter error1-3: main_values_check
        filtered_response = values_check(filtered_response, response_structure, comparison_input)
        if isinstance(filtered_response, str):
            filtered_response_error_message = filtered_response
            return filtered_response_error_message
        
        
        # filter error2: sub-check
        # filter error2(1): main_value_type이 dict인 경우
        if response_structure["ValueType"] == "dict":
            sub_filtered_response = filtered_response[response_structure["Key"]]
            for i in range(len(response_structure["Value"])):

                # filter error2(1)-2: sub_check_key
                _sub_filtered_response = check_key(sub_filtered_response, response_structure["Value"][i])
                if isinstance(_sub_filtered_response, str):
                    filtered_response_error_message = _sub_filtered_response
                    return filtered_response_error_message

                # filter error2(1)-3: sub_values_check
                _sub_filtered_response = values_check(sub_filtered_response, response_structure["Value"][i], comparison_input)
                if isinstance(_sub_filtered_response, str):
                    filtered_response_error_message = _sub_filtered_response
                    return filtered_response_error_message
                
                # filter error2(1)-4: sub_value_type이 dict 또는 list인 경우에만 sub_Sub 체크
                # sub_value_type이 dict인 경우
                if response_structure["Value"][i]["ValueType"] == "dict":
                    sub_sub_filtered_response = sub_filtered_response[response_structure["Value"][i]["Key"]]
                    for j in range(len(response_structure["Value"][i]["Value"])):
                        
                        # filter error2(1)-4-1: sub_sub_check_key
                        _sub_sub_filtered_response = check_key(sub_sub_filtered_response, response_structure["Value"][i]["Value"][j])
                        if isinstance(_sub_sub_filtered_response, str):
                            filtered_response_error_message = _sub_sub_filtered_response
                            return filtered_response_error_message

                        # filter error2(1)-4-2: sub_sub_values_check
                        _sub_sub_filtered_response = values_check(sub_sub_filtered_response, response_structure["Value"][i]["Value"][j], comparison_input)
                        if isinstance(_sub_sub_filtered_response, str):
                            filtered_response_error_message = _sub_sub_filtered_response
                            return filtered_response_error_message

                # filter error2(1)-4: sub_value_type이 list인 경우
                if response_structure["Value"][i]["ValueType"] == "list":
                    for sub_sub_filtered_response in sub_filtered_response[response_structure["Value"][i]["Key"]]:
                        for j in range(len(response_structure["Value"][i]["Value"])):

                            # filter error2(1)-4-1: sub_sub_check_key
                            _sub_sub_filtered_response = check_key(sub_sub_filtered_response, response_structure["Value"][i]["Value"][j])
                            if isinstance(_sub_sub_filtered_response, str):
                                filtered_response_error_message = _sub_sub_filtered_response
                                return filtered_response_error_message

                            # filter error2(1)-4-2: sub_sub_values_check
                            _sub_sub_filtered_response = values_check(sub_sub_filtered_response, response_structure["Value"][i]["Value"][j], comparison_input)
                            if isinstance(_sub_sub_filtered_response, str):
                                filtered_response_error_message = _sub_sub_filtered_response
                                return filtered_response_error_message

        # filter error2(2): main_value_type이 list인 경우
        if response_structure["ValueType"] == "list":
            for sub_filtered_response in filtered_response[response_structure["Key"]]:
                for i in range(len(response_structure["Value"])):

                    # filter error2(2)-2: sub_check_key
                    _sub_filtered_response = check_key(sub_filtered_response, response_structure["Value"][i])
                    if isinstance(_sub_filtered_response, str):
                        filtered_response_error_message = _sub_filtered_response
                        return filtered_response_error_message

                    # filter error2(2)-3: sub_values_check
                    _sub_filtered_response = values_check(sub_filtered_response, response_structure["Value"][i], comparison_input)
                    if isinstance(_sub_filtered_response, str):
                        filtered_response_error_message = _sub_filtered_response
                        return filtered_response_error_message

                    # filter error2(2)-4: sub_value_type이 dict 또는 list인 경우에만 sub_Sub 체크
                    # sub_value_type이 dict인 경우
                    if response_structure["Value"][i]["ValueType"] == "dict":
                        sub_sub_filtered_response = sub_filtered_response[response_structure["Value"][i]["Key"]]
                        for j in range(len(response_structure["Value"][i]["Value"])):
                            
                            # filter error2(2)-4-1: sub_sub_check_key
                            _sub_sub_filtered_response = check_key(sub_sub_filtered_response, response_structure["Value"][i]["Value"][j])
                            if isinstance(_sub_sub_filtered_response, str):
                                filtered_response_error_message = _sub_sub_filtered_response
                                return filtered_response_error_message

                            # filter error2(2)-4-2: sub_sub_values_check
                            _sub_sub_filtered_response = values_check(sub_sub_filtered_response, response_structure["Value"][i]["Value"][j], comparison_input)
                            if isinstance(_sub_sub_filtered_response, str):
                                filtered_response_error_message = _sub_sub_filtered_response
                                return filtered_response_error_message

                    # filter error2(2)-4: sub_value_type이 list인 경우
                    if response_structure["Value"][i]["ValueType"] == "list":
                        for sub_sub_filtered_response in sub_filtered_response[response_structure["Value"][i]["Key"]]:
                            for j in range(len(response_structure["Value"][i]["Value"])):

                                # filter error2(2)-4-1: sub_sub_check_key
                                _sub_sub_filtered_response = check_key(sub_sub_filtered_response, response_structure["Value"][i]["Value"][j])
                                if isinstance(_sub_sub_filtered_response, str):
                                    filtered_response_error_message = _sub_sub_filtered_response
                                    return filtered_response_error_message

                                # filter error2(2)-4-2: sub_sub_values_check
                                _sub_sub_filtered_response = values_check(sub_sub_filtered_response, response_structure["Value"][i]["Value"][j], comparison_input)
                                if isinstance(_sub_sub_filtered_response, str):
                                    filtered_response_error_message = _sub_sub_filtered_response
                                    return filtered_response_error_message

        # 모든 조건을 만족하면 필터링된 응답 반환
        return filtered_response[response_structure["Key"]]

    # --------------------------------------------------------
    # --- func-set: response update --------------------------
    # --- class-func: solution_process_middle_frame 업데이트 ---
    def _update_process_middle_frame(self, input_count: int, response: dict) -> None:
        """solution_process_middle_frame을 업데이트합니다.

        Args:
            input_count (int): 입력 수
            response (dict): 응답
        """
         # - innerfunc: response의 global 통합 함수 -
        def update_solution_process_global_data(solution_process_data: dict) -> dict:
            """response의 global, ko의 global 통합 함수
            
            Args:
                solution_process_data (dict): 응답

            Returns:
                solution_process_data (dict): 응답
            """
            if self.main_lang == "ko":
                # solution_process_middle_frame wordpairs 불러오기
                word_pairs = self.load_json("Solution", [self.solution, "Form", self.process_name, "MiddleFrame"], json_keys=["WordPairs"])
                
                # solution_process_data global 통합
                if word_pairs != []:
                    # solution_process_data가 dict인 경우
                    if isinstance(solution_process_data, dict):
                        for word_pair in word_pairs:
                            for i, ko_value in enumerate(word_pair["ko"]):
                                if solution_process_data[word_pair["key"]] == ko_value:
                                    solution_process_data[word_pair["key"]] = word_pair["global"][i]

                    # solution_process_data가 list인 경우
                    elif isinstance(solution_process_data, list):
                        for i in range(len(solution_process_data)):
                            for word_pair in word_pairs:
                                for j, ko_value in enumerate(word_pair["ko"]):
                                    if solution_process_data[i][word_pair["key"]] == ko_value:
                                        solution_process_data[i][word_pair["key"]] = word_pair["global"][j]

            return solution_process_data
        # - innerfunc end -

        # solution_process_middle_frame 존재 여부 확인
        if os.path.exists(self.read_path_map("Solution", [self.solution, "File", "Json", "MiddleFrame"])):
            solution_process_middle_frame = self.load_json("Solution", [self.solution, "File", "Json", "MiddleFrame"])
        else:
            solution_process_middle_frame = self.load_json("Solution", [self.solution, "Form", self.process_name, "MiddleFrame", self.main_lang])

        # solution_process_info 데이터 업데이트
        solution_process_info = solution_process_middle_frame[0].copy()
        for key, value_expression in solution_process_info.items():
            if key in ["InputCount", "Completion"]:
                continue
            
            actual_value = value_expression
            if isinstance(value_expression, str) and value_expression.startswith("eval(") and value_expression.endswith(")"):
                # "eval("와 ")" 부분을 제외한 안쪽 코드만 추출
                code_to_eval = eval(value_expression[5:-1])
                actual_value = eval(code_to_eval)

            solution_process_middle_frame[0][key] = actual_value
        
        # solution_process_data 데이터 업데이트
        # response가 dict인 경우
        solution_process_data = copy.deepcopy(solution_process_middle_frame[1][0])
        if isinstance(solution_process_data, dict):
            for key, value_expression in solution_process_data.items():
                actual_value = value_expression
                if isinstance(value_expression, str) and value_expression.startswith("eval(") and value_expression.endswith(")"):
                    # "eval("와 ")" 부분을 제외한 안쪽 코드만 추출
                    code_to_eval = value_expression[5:-1]
                    actual_value = eval(code_to_eval)

                solution_process_data[key] = actual_value
        
        # response가 list인 경우
        elif isinstance(solution_process_data, list):
            for i in range(len(solution_process_data)):
                for key, value_expression in solution_process_data[i].items():
                    actual_value = value_expression
                    if isinstance(value_expression, str) and value_expression.startswith("eval(") and value_expression.endswith(")"):
                        # "eval("와 ")" 부분을 제외한 안쪽 코드만 추출
                        code_to_eval = value_expression[5:-1]
                        actual_value = eval(code_to_eval)

                    solution_process_data[i][key] = actual_value
        
        # solution_process_middle_frame 데이터 프레임 업데이트
        solution_process_middle_frame[1].append(update_solution_process_global_data(solution_process_data))
        
        # solution_process_middle_frame process_count 및 completion 업데이트
        solution_process_middle_frame[0]['InputCount'] = input_count
        if input_count == self.total_input_count:
            solution_process_middle_frame[0]['Completion'] = 'Yes'
        
        # solution_process_middle_frame 저장
        self.save_storage_json("Solution", [self.solution, "File", "Json", "MiddleFrame"], solution_process_middle_frame)

    # --- class-func: solution_edit 업데이트 ---
    def _update_solution_edit(self):
        """solution_edit을 업데이트합니다.
        """
        # solution_process_middle_frame 불러온 뒤 completion 확인
        solution_project_middle_frame = self.load_json("Solution", [self.solution, "File", "Json", "MiddleFrame"])
        if solution_project_middle_frame["Completion"] == "Yes":
            # solution_edit 존재 여부 확인
            if os.path.exists(self.read_path_map("Solution", [self.solution, "File", "Json", "Edit"])):
                solution_edit = self.load_json("Solution", [self.solution, "File", "Json", "Edit"])
            # solution_edit 존재 안할때
            else:
                solution_edit = {}
            
            # solution_edit 업데이트
            solution_edit[self.process_name] = []
            if self.edit_mode:
                solution_edit[f"{self.process_name}ResponseCompletion"] = "Completion"
            else:
                solution_edit[f"{self.process_name}ResponseCompletion"] = "완료 후 Completion"
            solution_edit[f"{self.process_name}ResponsePostProcessCompletion"] = "완료 후 자동 Completion"
            solution_edit[f"{self.process_name}OutputCompletion"] = "완료 후 자동 Completion"

            solution_project_data_list = solution_project_middle_frame[1]
            for i in range(1, len(solution_project_data_list)):
                solution_project_data = solution_project_data_list[i]
                solution_edit[self.process_name].append(solution_project_data)

            # solution_project_middle_frame에서 추가 데이터가 존재하는 경우 예외 저장
            if len(solution_project_middle_frame) > 2:
                for i, additional_data in enumerate(solution_project_middle_frame[2:], start=1):
                    additional_key = f"{self.process_name}AdditionalData{i}"
                    solution_edit[additional_key] = additional_data

            # solution_edit 저장
            self.save_storage_json("Solution", [self.solution, "File", "Json", "Edit"], solution_edit)

    # ------------------------------------------
    # --- func-set: response pre/postprocess ---
    # --- class-func: response 전처리 ------------
    def _preprocess_response(self, response: dict) -> dict:
        """response를 전처리합니다.

        Args:
            response (dict): response

        Returns:
            response (dict): response
        """
        # response 전처리 함수 실행
        response = self.preprocess_response_func(response)

        return response
    
    # --- class-func: response 후처리 ---
    def _postprocess_response(self, solution_edit: dict) -> dict:
        """response를 후처리합니다.

        Args:
            solution_edit (dict): solution_edit

        Effects:
            solution_edit 업데이트
        """
        solution_edit_process = solution_edit[self.process_name]

        # solution_edit_process 후처리 함수 실행
        if self.postprocess_response_func(solution_edit_process):
            solution_edit[f"{self.process_name}ResponsePostProcessCompletion"] = "Completion"

            # solution_edit 저장
            self.save_storage_json("Solution", [self.solution, "File", "Json", "Edit"], solution_edit)

    # -------------------------------
    # --- func-set: output create ---
    # --- class-func: output 생성 ----
    def _create_output(self, solution_edit: dict) -> dict:
        """output을 생성합니다.

        Args:
            solution_edit (dict): solution_edit

        Effects:
            solution_edit 업데이트
        """
        solution_edit_process = solution_edit[self.process_name]

        # solution_edit_process 출력 함수 실행
        if self.output_func(solution_edit_process):
            solution_edit[f"{self.process_name}OutputCompletion"] = "Completion"

            # solution_edit 저장
            self.save_storage_json("Solution", [self.solution, "File", "Json", "Edit"], solution_edit)

    # -------------------------------------
    # --- func-set: agent run -------------
    # --- class-func: agent request 요청 ---
    def _request_agent(self,
                       input: str | list,
                       memory_note: str,
                       input_count: int,
                       total_input_count: int,
                       comparison_input: str | list) -> str:
        """agent request 요청을 수행합니다.

        Args:
            input (str | list): 입력 데이터
            memory_note (str): 메모리 노트
            input_count (int): 인덱스
            total_input_count (int): 인덱스 길이
            comparison_input (str | list): 비교 입력 데이터
        """
        error_count = 0
        while True:
            # request llm 요청
            response = self.request_llm(input, memory_note, input_count, total_input_count)

            # 생성된 response 필터
            filtered_response = self._response_filter(response, comparison_input, self.response_structure)

            # 필터 에외처리, JSONDecodeError 처리
            if isinstance(filtered_response, str):
                error_count += 1
                self.print_log("Task", ["Log", "Function"], ["Info", "Error"], function_name="agent._request_agent", _print=f"오류횟수 {error_count}회, 10초 후 프롬프트 재시도")

                # filter error 3회시 해당 프로세스 사용 안함 예외처리
                if self.filter_pass and error_count >= 3:
                    self.print_log("Task", ["Log", "Function"], ["Info", "Complete"], function_name="agent._request_agent", _print="ErrorPass 완료")

                    return "ErrorPass"

                # filter error 10회시 프롬프트 종료
                if error_count >= 10:
                    self.print_log("Task", ["Log", "Function"], ["Info", "Error"], function_name="agent._request_agent", _print=f"오류횟수 {error_count}회 초과, 프롬프트 종료", exit=True)

                continue

            self.print_log("Task", ["Log", "Function"], ["Info", "Complete"], function_name="agent._request_agent", _print="filtered_response, JSONDecode 완료")

            return filtered_response

    # --- class-func: agent 실행 ---
    def run_agent(self,
                  inputs_func: callable = None,
                  preprocess_response_func: callable = None,
                  postprocess_response_func: callable = None,
                  output_func: callable = None,

                  response_mode: bool = True,
                  edit_mode: bool = True,
                  outputs_per_input: int = 1,
                  input_count_key: str = None,
                  ignore_count_check: bool = False,
                  filter_pass: bool = False) -> None:
        """agent를 실행합니다.

        Args:
            inputs_func (callable): 입력 리스트 생성 함수
            preprocess_response_func (callable): 응답 전처리 함수
            postprocess_response_func (callable): 응답 후처리 함수
            output_func (callable): 출력 함수

            response_mode (str): LLM 모드 사용 여부 ("Prompt", "Algorithm", "Manual")
            edit_mode (bool): 편집 모드 (기본값: True)
            outputs_per_input (int): 출력 배수 (기본값: 1)
            input_count_key (str): 입력 수의 기준키 (기본값: None)
            ignore_count_check (bool): 입력 수 체크 무시 여부 (기본값: False)
            filter_pass (bool): 필터 오류 3회가 넘어가는 경우 그냥 패스 여부 (기본값: False)
        """
        # function 초기화
        self._init_function(inputs_func,
            preprocess_response_func,
            postprocess_response_func,
            output_func)

        # mode 초기화
        self._init_mode(response_mode,
            edit_mode,
            outputs_per_input,
            input_count_key,
            ignore_count_check,
            filter_pass)

        # Start 로그 출력
        self.print_log("Solution", ["Log", "Task"], ["Info", "Start"], input_count=self.input_count, total_input_count=self.total_input_count)

        # edit_check 확인
        if not self.edit_check:
            if not self.middle_frame_completion:
                for i in range(self.input_count - 1, self.total_input_count):
                    # input_count, input, comparison_input, memory_note 생성
                    input_count = self.input_list[i]['Id']
                    input = self.input_list[i]['Input']
                    comparison_input = self.input_list[i]['ComparisonInput']
                    memory_note = self.input_list[i]['MemoryNote']

                    if self.response_mode == "Prompt":
                        # response 생성
                        response = self._request_agent(input, memory_note, input_count, self.total_input_count, comparison_input)
                        # response 전처리
                        response = self._preprocess_response(response)
                    if self.response_mode in ["Algorithm", "Manual"]:
                        response = input

                    # middle_frame 저장
                    self._update_process_middle_frame(input_count, response)

            # solution_edit 저장
            self._update_solution_edit()

            if not self.edit_mode:
                self.print_log("Task", ["Log", "Function"], ["Info", "Manual"], function_name="agent.run_agent", _print=f"{self.ProjectName}_Script_Edit 생성 완료 -> {self.ProcessName}: (({self.ProcessName}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({self.ProcessName}Completion: Completion))으로 변경", exit=True)

        if not self.edit_mode:
            if self.edit_check:
                if not self.edit_response_completion:
                    ## 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ##
                    self.print_log("Task", ["Log", "Function"], ["Info", "Manual"], function_name="agent.run_agent", _print=f"{self.ProjectName}_Script_Edit -> {self.ProcessName}: (({self.ProcessName}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({self.ProcessName}Completion: Completion))으로 변경", exit=True)

        # solution_edit 불러오기
        solution_edit = self.load_json("Solution", [self.solution, "File", "Json", "Edit"])

        # response 후처리
        if not self.edit_response_postprocess_completion:
            self._postprocess_response(solution_edit)

        # output 생성
        if not self.edit_output_completion:
            self._create_output(solution_edit)

            # Complete 로그 출력
            self.print_log("Solution", ["Log", "Task"], ["Info", "Complete"], input_count=self.input_count, total_input_count=self.total_input_count)
        else:
            # Skip 로그 출력
            self.print_log("Solution", ["Log", "Task"], ["Info", "Skip"], input_count=self.input_count, total_input_count=self.total_input_count)

        return solution_edit

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