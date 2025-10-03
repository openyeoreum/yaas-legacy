import os
import re
import json
import time
import random
import base64
import mimetypes
import copy
import anthropic
import sys
sys.path.append("/yaas")

from datetime import datetime
from openai import OpenAI
from PIL import Image
from google import genai
from google.genai import types
from agent.a3_Operation.a31_Operation.a314_Manager import Manager

# ======================================================================
# [a332-1] Operation-LLM
# ======================================================================
# class: LLM
# ======================================================================
class LLM(Manager):

    # -----------------------------
    # --- class-init --------------
    # --- class-func: LLM 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 solution: str = None,
                 next_solution: str = None,
                 process_number: str = None,
                 process_name: str = None,
                 main_lang: str = "Ko") -> None:
        """사용자-프로젝트의 Operation에 통합 LLM 기능을 셋팅하는 클래스입니다.

        Attributes:
            email (str): 이메일
            project_name (str): 프로젝트명
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Audiobook, Translation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
            main_lang (str): 주요 언어 (기본값: "ko")
        """
        # Manager 초기화
        super().__init__(
            email,
            project_name,
            solution,
            next_solution,
            process_number,
            process_name)

        # attributes 설정
        self.main_lang = main_lang

    # -------------------------------------
    # --- func-set: load config -----------
    # --- class-func: api_config 불러오기 ---
    def _load_api_config(self) -> dict:
        """API 설정 JSON 파일을 로드하여 딕셔너리로 반환합니다.

        Returns:
            api_config_dict (dict): API 설정이 담긴 딕셔너리
        """
        # JSON 파일 열기 및 로드
        with open(self.read_path_map("Operation", ["APIConfig"]), 'r', encoding='utf-8') as f:
            api_config_dict = json.load(f)
        
        return api_config_dict

    # --- class-func: api_client 불러오기 ---
    def _load_api_client(self, service: str) -> str:
        """API 클라이언트를 로드하여 반환합니다.

        Args:
            service (str): 사용할 LLM 서비스명 (ex. "OPENAI", "ANTHROPIC", "GOOGLE", "DEEPSEEK")

        Returns:
            api_client (str): API 클라이언트
        """
        # 서비스에 따른 API 클라이언트 로드
        if service == "OPENAI":
            open_ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            return open_ai_client
        elif service == "ANTHROPIC":
            anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            return anthropic_client
        elif service == "GOOGLE":
            google_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            return google_client
        elif service == "DEEPSEEK":
            deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
            return deepseek_client

    # ------------------------------------
    # --- func-set: format message -------
    # --- class-func: file list 텍스트화 ---
    def _format_input_paths_to_str(self, input_paths: list) -> str:
        """파일 리스트를 문자열로 포맷팅하여 반환합니다.

        Args:
            input (list): 파일 리스트

        Returns:
            input_str (str): 포맷팅된 파일 리스트 문자열
        """
        # 파일 리스트 정리
        input_list = [os.path.basename(path) for path in input_paths]

        # 파일 리스트 문자열 정리
        input_str = ""
        if self.main_lang == "Ko":
            for i in range(len(input_list)):
                input_str += f"업로드 자료 {i+1} : {input_list[i]}\n"
        else:
            for i in range(len(input_list)):
                input_str += f"Uploaded Data {i+1} : {input_list[i]}\n"

        return input_str

    # --- class-func: response example 텍스트화 ---
    def _format_response_example_dict_to_str(self, response_example_dict: dict) -> str:
        """딕셔너리 데이터를 JSON 형식의 문자열로 변환합니다.

        Args:
            response_example_dict (dict): 문자열로 변환할 딕셔너리 데이터

        Returns:
            str: JSON 형식으로 포맷팅된 문자열
        """
        # 딕셔너리를 JSON 형식의 문자열로 변환
        response_str = json.dumps(response_example_dict, ensure_ascii=False, indent=4)

        return response_str

    # --- class-func: messages 포맷팅 ---
    def _format_prompt_to_messages(self, input: str | list, memory_note: str) -> str:
        """프롬프트 텍스트를 메세지로 포맷팅하여 반환합니다.

        Returns:
            formatted_prompt (str): 포맷팅된 메세지 텍스트
        """
        # API 설정 불러오기
        message_time = f"current time: {str(datetime.now())}\n\n"

        # 메세지 불러오기
        message_dict = self.read_json("Solution", [self.solution, "Form", self.process_name], ["Message", self.main_lang])

        # InputFormat 불러오기
        input_format = self.read_json("Solution", [self.solution, "Form", self.process_name], ["Format", "InputFormat"])

        # InputFormat이 Text가 아닌 경우에는 파일리스트 정리
        if input_format != "text":
            input_paths = input
            input = self._format_input_paths_to_str(input_paths)

        # ResponseExample 포맷팅
        response_example = self._format_response_example_dict_to_str(message_dict["ResponseExample"])

        # 프롬프트 포맷팅
        system_message = message_dict["Messages"]["System"]
        system_content =  message_time + system_message["Mark"] + system_message["MarkLineBreak"] + system_message["Message"] + system_message["MessageLineBreak"]

        user_message = message_dict["Messages"]["User"]
        _user_content = ""
        for message in user_message[:-1]:
            _user_content += message["Mark"] + message["MarkLineBreak"] + message["Message"] + message["MessageLineBreak"]
        user_content = _user_content + user_message[-1]["Request"] + user_message[-1]["RequestLineBreak"]
        user_content = user_content.format(ResponseExample=response_example)

        assistant_message = message_dict["Messages"]["Assistant"]
        assistant_content = assistant_message["MemoryNote"].format(MemoryNote=memory_note) + assistant_message["MemoryNoteLineBreak"] + assistant_message["ResponseMark"]

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content}
        ]

        return messages

    # --------------------------------------------
    # --- func-set: print request and response ---
    # --- class-func: request와 response 출력 ------
    def _print_request_and_response(self, response: dict, usage: str) -> str:
        """request와 response를 출력합니다.

        Args:
            response (dict): 응답 딕셔너리
            usage (str): 사용량 텍스트

        Print:
            messages_and_response_text (str): request와 response
        """
        # 각 메시지를 형식에 맞는 문자열 생성
        request_parts = []
        for message in self.print_messages:
            role = message["role"]
            content = message["content"]
            request_parts.append(f"* {role}\n\n{content}")

        # 생성된 메시지 목록을 두 줄 띄어쓰기로 합쳐 하나의 문자열 블록생성
        request_block = "\n\n".join(request_parts)

        # 요청 텍스트 생성
        request_text = f"🟦- Request -🟦\n\nService: {self.service}\n\n{request_block}\n\n"

        # 응답 텍스트 생성
        response_text = f"🔴- Response -🔴\n\n{response}\n\n🟥- Usage -🟥\n\n{usage}\n\n"
        
        # request와 response 출력
        request_and_response_text = request_text + response_text

        return request_and_response_text

    # ------------------------------------
    # --- func-set: llm request ----------
    # --- class-func: llm request 초기화 ---
    def _init_request(self,
                      input: str | list,
                      memory_note: str) -> None:
        """llm request를 초기화합니다.

        Args:
            input (list): 입력 데이터
            memory_note (str): 메모리 노트

        Attributes:
            input (list): 입력 데이터(입력 텍스트 또는 파일 리스트)
            memory_note (str): 메모리 노트
            service (str): 서비스(OpenAI, Anthropic, Google, DeepSeek)
            client: llm api 클라이언트
            model (str): 모델(요청 모델)
            reasoning_effort (str): 추론 노력
            input_format (str): 입력 포맷(text, jpeg ..)
            response_format (str): 응답 포맷(text, jpeg ..)
            messages (list): 메시지
            MAX_ATTEMPTS (int): 최대 시도 횟수
        """

        # attributes 설정
        self.input = input
        self.memory_note = memory_note

        api_config_dict = self._load_api_config()
        api_dict = self.read_json("Solution", [self.solution, "Form", self.process_name], ["API"])
        self.service = api_dict["Service"]
        level = api_dict["Level"]
        self.client = self._load_api_client(self.service)
        self.model = api_config_dict["LanguageModel"][self.service][level]["Model"]
        self.reasoning_effort = api_config_dict["LanguageModel"][self.service][level]["ReasoningEffort"]

        format_dict = self.read_json("Solution", [self.solution, "Form", self.process_name], ["Format"])
        self.input_format = format_dict["InputFormat"]
        self.response_format = format_dict["ResponseFormat"]

        self.messages = self._format_prompt_to_messages(self.input, self.memory_note)
        self.print_messages = copy.deepcopy(self.messages)

        self.MAX_ATTEMPTS = 100

    # ------------------------------------
    # --- func-set: normalize response ---
    # --- class-func: json 포멧 정규화 ------
    def _normalize_response_json_format(self, response: str) -> str:
        """응답 문자열을 JSON 형식으로 정규화합니다.

        Args:
            response (str): 응답 문자열

        Returns:
            json_response (str): JSON 형식으로 정규화된 응답 문자열
        """
        pattern = r'(?:\'\'\'|```|\"\"\")(.*?)(?:\'\'\'|```|\"\"\")'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            response = match.group(1).strip()
        response = response.replace('\n', '\\n')

        # 대괄호와 중괄호 인덱스 찾기
        start_index_bracket = response.find('[')
        start_index_brace = response.find('{')

        # 대괄호와 중괄호 인덱스 중 작은 값 찾기
        if start_index_bracket != -1 and start_index_brace != -1:
            start_index = min(start_index_bracket, start_index_brace)
        elif start_index_bracket != -1:
            start_index = start_index_bracket
        elif start_index_brace != -1:
            start_index = start_index_brace
        else:
            start_index = -1

        # 대괄호와 중괄호 인덱스 중 작은 값이 -1이 아닌 경우, json 형식 정규화
        if start_index != -1:
            if response[start_index] == '[':
                end_index = response.rfind(']')
            else:
                end_index = response.rfind('}')
            # 대괄호와 중괄호 인덱스 중 큰 값이 -1이 아닌 경우, json 형식 정규화
            if end_index != -1:
                json_response = response[start_index:end_index+1]
            else:
                json_response = response
        # 대괄호와 중괄호 인덱스 중 작은 값이 -1인 경우, 원본 응답 반환
        else:
            json_response = response

        return json_response

    # ----------------------------------------
    # --- func-set: openai request -----------
    # --- class-func: openai 이미지 파일 업로드 ---
    def _openai_image_files(self) -> None:
        """입력된 이미지 파일들을 OpenAI에 업로드하고 self.messages를 업데이트합니다.

        Effects:
            self.messages[1]["content"]가 문자열일 경우, OpenAI 형식에 맞게 list로 변환
            self.messages[1]["content"]가 list가 아닐 경우, list로 변환
        """
        # - innerfunc: image file 업로드 함수 -
        def upload_single_file(client, image_path: str) -> str:
            """단일 이미지 파일을 업로드하여 파일 ID를 반환합니다.

            Args:
                client: OpenAI 클라이언트
                image_path (str): 이미지 파일 경로

            Returns:
                image_id (str): 업로드된 파일의 ID
            """
            with open(image_path, "rb") as f:
                result = client.files.create(file=f, purpose="vision")
                return result.id
        # - innerfunc end -

        # 모든 이미지 파일을 업로드하고 파일 ID 리스트를 생성
        image_file_ids = [upload_single_file(self.client, image_path) for image_path in self.input]

        # Messages[1]["content"]가 문자열이라면, input_text 블록으로 변환
        if isinstance(self.messages[1]["content"], str):
            self.messages[1]["content"] = [{"type": "input_text", "text": self.messages[1]["content"]}]

        elif not isinstance(self.messages[1]["content"], list):
            self.messages[1]["content"] = []

        # 메시지 포맷에 맞게 이미지 콘텐츠 추가
        image_contents = [{"type": "input_image", "file_id": fid, "detail": "high"} for fid in image_file_ids]
        self.messages[1]["content"].extend(image_contents)

    # --- class-func: openai request 요청 ---
    def openai_request(self,
                       input: str | list,
                       memory_note: str,
                       idx: int,
                       idx_length: int) -> str:
        """OpenAI 요청을 수행합니다.

        Args:
            input (list): 입력 데이터
            memory_note (str): 메모리 노트
            idx (int): 인덱스
            idx_length (int): 인덱스 길이

        Returns:
            response (str): 응답 문자열

        Print:
            request_and_response_text (str): request와 response
            error (str): 에러 메시지
        """
        # request 초기화
        self._init_request(
            input,
            memory_note)

        # 입력 포맷이 jpeg인 경우, 이미지 업로드 함수 호출
        if self.input_format == "jpeg":
            self._openai_image_files()

        # request 요청 및 response 출력
        for _ in range(self.MAX_ATTEMPTS):
            try:
                _response=self.client.responses.create(
                    model=self.model,
                    reasoning={"effort": self.reasoning_effort},
                    input=self.messages,
                    text={"format": {"type": "json_object"}})

                response = _response.output_text
                usage = {
                    'Input': _response.usage.input_tokens,
                    'Output': _response.usage.output_tokens,
                    'Total': _response.usage.total_tokens}

                # request와 response 출력
                request_and_response_text = self._print_request_and_response(response, usage)

                self.print_log("Task", ["Log", "Message"], ["Info", "Message"], idx=idx, idx_length=idx_length, function_name="openai_request", _print=request_and_response_text)

                return response

            except Exception as e:
                self.print_log("Access", ["Log", "Info"], ["Info", "Error"], function_name="openai_request", _print=e)
                time.sleep(random.uniform(2, 5))
                continue

    # ------------------------------------------
    # --- func-set: anthropic request ----------
    # --- class-func: anthropic 이미지 파일 준비 ---
    def _anthropic_image_files(self) -> None:
        """입력된 이미지 파일들을 Base64로 인코딩하여 self.messages에 포함시킵니다.

        Effects:
            self.messages[1]["content"]가 문자열일 경우, Claude 형식에 맞게 list로 변환
        """
        # self.messages[1]["content"]가 문자열일 경우, Claude 형식에 맞게 list로 변환
        if isinstance(self.messages[1]["content"], str):
            self.messages[1]["content"] = [{"type": "text", "text": self.messages[1]["content"]}]

        elif not isinstance(self.messages[1]["content"], list):
            self.messages[1]["content"] = []

        # 기존 텍스트 파트 분리
        text_parts = [part for part in self.messages[1]["content"] if part.get("type") == "text"]
        
        # 이미지 파일들을 읽고 Base64로 인코딩하여 이미지 파트 생성
        image_parts = []
        for image_path in self.input:
            # 파일 확장자로부터 MIME 타입 추정
            mime_type, _ = mimetypes.guess_type(image_path)

            with open(image_path, "rb") as f:
                encoded_string = base64.b64encode(f.read()).decode('utf-8')
            
            image_parts.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": encoded_string,
                }
            })

        # 기존 텍스트 파트와 새로운 이미지 파트를 합쳐 content 업데이트
        self.messages[1]["content"] = text_parts + image_parts

    # --- class-func: anthropic request 요청 ---
    def anthropic_request(self,
                          input: str | list,
                          memory_note: str,
                          idx: int,
                          idx_length: int, 
                          MAX_TOKENS: int = 16000) -> str:
        """Anthropic 요청을 수행합니다.

        Args:
            input (list): 입력 데이터
            memory_note (str): 메모리 노트
            idx (int): 인덱스
            idx_length (int): 인덱스 길이
            MAX_TOKENS (int): 최대 토큰 수

        Returns:
            response (str): 응답 문자열

        Print:
            request_and_response_text (str): request와 response
            error (str): 에러 메시지
        """
        # request 초기화
        self._init_request(
            input,
            memory_note)

        # 입력 포맷이 jpeg인 경우, 이미지 업로드 함수 호출
        if self.input_format == "jpeg":
            self._anthropic_image_files()

        # request 요청 및 response 출력
        for _ in range(self.MAX_ATTEMPTS):
            try:
                _response = self.client.messages.create(
                    model=self.model,
                    max_tokens=MAX_TOKENS,
                    thinking={
                        "type": "enabled",
                        "budget_tokens": self.reasoning_effort},
                    system=self.messages[0]["content"],
                    messages=self.messages[1]["content"] + self.messages[2]["content"])
                
                response = _response.content[0].text
                usage = {
                    'Input': _response.usage.input_tokens,
                    'Output': _response.usage.output_tokens,
                    'Total': _response.usage.input_tokens + _response.usage.output_tokens}

                # request와 response 출력
                request_and_response_text = self._print_request_and_response(response, usage)

                self.print_log("Task", ["Log", "Message"], ["Info", "Message"], idx=idx, idx_length=idx_length, function_name="anthropic_request", _print=request_and_response_text)

                return response

            except Exception as e:
                self.print_log("Access", ["Log", "Info"], ["Info", "Error"], function_name="anthropic_request", _print=e)
                time.sleep(random.uniform(2, 5))
                continue

    # ---------------------------------------
    # --- func-set: google request ----------
    # --- class-func: google 이미지 파일 준비 ---
    def _google_image_files(self) -> list:
        """입력된 이미지 파일들을 Google API가 처리할 수 있는 형식으로 준비합니다.

        Returns:
            image_list (list): Google API에 전달할 이미지 리스트
        """
        # 이미지 리스트 초기화
        image_list = []
        
        # self.input에 있는 각 파일 경로에 대해 반복
        for image_path in self.input:
            # PIL을 사용하여 이미지 파일 열기
            img = Image.open(image_path)
            # 리스트에 이미지 객체 추가
            image_list.append(img)
                
        return image_list

    # --- class-func: google request 요청 ---
    def google_request(self,
                       input: str | list,
                       memory_note: str,
                       idx: int,
                       idx_length: int) -> str:
        """Google 요청을 수행합니다.

        Args:
            input (list): 입력 데이터
            memory_note (str): 메모리 노트
            idx (int): 인덱스
            idx_length (int): 인덱스 길이

        Returns:
            response (str): 응답 문자열

        Print:
            request_and_response_text (str): request와 response
            error (str): 에러 메시지
        """
        # request 초기화
        self._init_request(
            input,
            memory_note)

        # 입력 포맷이 jpeg인 경우, 이미지 업로드 함수 호출
        if self.input_format == "jpeg":
            image_list = self._google_image_files()

        # Google API 요청 및 응답
        for _ in range(self.MAX_ATTEMPTS):
            try:
                # generation_config 설정
                generation_config = types.GenerateContentConfig(
                    system_instruction = self.messages[0]["content"],
                    thinking_config = types.ThinkingConfig(thinking_budget = self.reasoning_effort),
                    response_mime_type = "application/json")

                if self.input_format == "jpeg":
                    _response = self.client.models.generate_content(
                        model=self.model,
                        contents=[self.messages[1]["content"]] + image_list + [self.messages[2]["content"]],
                        config=generation_config)
                    
                else:
                    _response = self.client.models.generate_content(
                        model=self.model,
                        contents=self.messages[1]["content"] + self.messages[2]["content"],
                        config=generation_config)

                response = _response.text
                usage = {
                    'Input': _response.usage_metadata.prompt_token_count,
                    'Output': _response.usage_metadata.candidates_token_count,
                    'Total': _response.usage_metadata.total_token_count}
                
                # request와 response 출력
                request_and_response_text = self._print_request_and_response(response, usage)

                self.print_log("Task", ["Log", "Message"], ["Info", "Message"], idx=idx, idx_length=idx_length, function_name="google_request", _print=request_and_response_text)

                return response

            except Exception as e:
                self.print_log("Access", ["Log", "Info"], ["Info", "Error"], function_name="openai_request", _print=e)
                time.sleep(random.uniform(2, 5))
                continue

    # ----------------------------------------
    # --- func-set: deepseek request ---------
    # --- class-func: deepseek request 요청 ---
    def deepseek_request(self,
                         input: str | list,
                         memory_note: str,
                         idx: int,
                         idx_length: int) -> str:
        """DeepSeek 요청을 수행합니다.

        Args:
            input (list): 입력 데이터
            memory_note (str): 메모리 노트
            idx (int): 인덱스
            idx_length (int): 인덱스 길이

        Returns:
            response (str): 응답 문자열
        """
        # request 초기화
        self._init_request(
            input,
            memory_note)

        # API 요청 및 응답
        for _ in range(self.MAX_ATTEMPTS):
            try:
            # JSON 응답 형식을 요청하는 경우
                _response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    response_format={"type": "json_object"},
                    stream=False)

                response = _response.choices[0].message.content
                usage = {
                    'Input': _response.usage.prompt_tokens,
                    'Output': _response.usage.completion_tokens,
                    'Total': _response.usage.total_tokens
                }
                
                request_and_response_text = self._print_request_and_response(response, usage)
                self.print_log("Task", ["Log", "Message"], ["Info", "Message"], idx=idx, idx_length=idx_length, function_name="deepseek_request", _print=request_and_response_text)

                return response

            except Exception as e:
                self.print_log("Access", ["Log", "Info"], ["Info", "Error"], function_name="deepseek_request", _print=e)
                time.sleep(random.uniform(2, 5))
                continue

if __name__ == "__main__":

    # --- class-test ---
    # 인자 설정
    email = "yeoreum00128@gmail.com"
    project_name = "글로벌솔루션여름"
    solution = "ScriptSegmentation"
    next_solution = "Audiobook"
    process_number = "P02"
    process_name = "PDFMainLangCheck"

    # 클래스 테스트
    llm = LLM(
        email,
        project_name,
        solution=solution,
        next_solution=next_solution,
        process_number=process_number,
        process_name=process_name)

    input = [
        "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/yeoreum00128@gmail.com/250911_스크립트테스트/250911_스크립트테스트_script/250911_스크립트테스트_mixed_script_file/250911_스크립트테스트_SampleScript(AudioBook)_jpeg/250911_스크립트테스트_Script(AudioBook)(1).jpeg",
        "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/yeoreum00128@gmail.com/250911_스크립트테스트/250911_스크립트테스트_script/250911_스크립트테스트_mixed_script_file/250911_스크립트테스트_SampleScript(AudioBook)_jpeg/250911_스크립트테스트_Script(AudioBook)(2).jpeg",
        "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/yeoreum00128@gmail.com/250911_스크립트테스트/250911_스크립트테스트_script/250911_스크립트테스트_mixed_script_file/250911_스크립트테스트_SampleScript(AudioBook)_jpeg/250911_스크립트테스트_Script(AudioBook)(3).jpeg",
        "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/yeoreum00128@gmail.com/250911_스크립트테스트/250911_스크립트테스트_script/250911_스크립트테스트_mixed_script_file/250911_스크립트테스트_SampleScript(AudioBook)_jpeg/250911_스크립트테스트_Script(AudioBook)(4).jpeg",
        "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/yeoreum00128@gmail.com/250911_스크립트테스트/250911_스크립트테스트_script/250911_스크립트테스트_mixed_script_file/250911_스크립트테스트_SampleScript(AudioBook)_jpeg/250911_스크립트테스트_Script(AudioBook)(5).jpeg",
        "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/yeoreum00128@gmail.com/250911_스크립트테스트/250911_스크립트테스트_script/250911_스크립트테스트_mixed_script_file/250911_스크립트테스트_SampleScript(AudioBook)_jpeg/250911_스크립트테스트_Script(AudioBook)(6).jpeg",
        "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/yeoreum00128@gmail.com/250911_스크립트테스트/250911_스크립트테스트_script/250911_스크립트테스트_mixed_script_file/250911_스크립트테스트_SampleScript(AudioBook)_jpeg/250911_스크립트테스트_Script(AudioBook)(7).jpeg",
        "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/yeoreum00128@gmail.com/250911_스크립트테스트/250911_스크립트테스트_script/250911_스크립트테스트_mixed_script_file/250911_스크립트테스트_SampleScript(AudioBook)_jpeg/250911_스크립트테스트_Script(AudioBook)(8).jpeg",
        "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/yeoreum00128@gmail.com/250911_스크립트테스트/250911_스크립트테스트_script/250911_스크립트테스트_mixed_script_file/250911_스크립트테스트_SampleScript(AudioBook)_jpeg/250911_스크립트테스트_Script(AudioBook)(9).jpeg",
        "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/yeoreum00128@gmail.com/250911_스크립트테스트/250911_스크립트테스트_script/250911_스크립트테스트_mixed_script_file/250911_스크립트테스트_SampleScript(AudioBook)_jpeg/250911_스크립트테스트_Script(AudioBook)(10).jpeg"
        ]

    # openai request
    response = llm.openai_request(
        input=input,
        memory_note="",
        idx=1,
        idx_length=1)

    # anthropic request
    response = llm.anthropic_request(
        input=input,
        memory_note="",
        idx=1,
        idx_length=1)

    # google request
    response = llm.google_request(
        input=input,
        memory_note="",
        idx=1,
        idx_length=1)

    # deepseek request
    response = llm.deepseek_request(
        input=input,
        memory_note="",
        idx=1,
        idx_length=1)