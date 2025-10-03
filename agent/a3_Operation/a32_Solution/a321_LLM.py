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
        if service == "ANTHROPIC":
            anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            return anthropic_client
        if service == "GOOGLE":
            google_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            return google_client
        if service == "DEEPSEEK":
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
        assistant_content = assistant_message["MemoryNote"].format(MemoryNote=memory_note or "") + assistant_message["MemoryNoteLineBreak"] + assistant_message["ResponseMark"]

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
        self.max_tokens = None
        if "MaxTokens" in api_config_dict["LanguageModel"][self.service][level]:
            self.max_tokens = api_config_dict["LanguageModel"][self.service][level]["MaxTokens"]

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

    # ---------------------------------------------
    # --- func-set: openai request ----------------
    # --- class-func: openai 이미지 파일 합성 메세지 ---
    def _image_files_added_openai_messages(self) -> None:
        """입력된 이미지 파일들을 OpenAI API에 전달할 수 있는 형식으로 준비합니다.

        Returns:
            openai_messages (list): OpenAI API에 전달할 메시지 리스트
        """
        # - innerfunc: image file 업로드 함수 -
        def upload_single_file(client,
                               image_path: str) -> str:
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

        # 메시지 포맷에 맞게 이미지 파트 추가
        image_parts = [{"type": "input_image", "file_id": fid, "detail": "high"} for fid in image_file_ids]
        self.messages[1]["content"].extend(image_parts)

        # openai_messages 설정
        openai_messages = self.messages

        return openai_messages

    # --- class-func: openai request 요청 ---
    def openai_request(self) -> str:
        """OpenAI에 요청합니다.

        Returns:
            response (str): 응답 문자열
            usage (dict): 사용 정보
        """
        # openai_messages 설정
        openai_messages = self.messages
        if self.input_format == "jpeg":
            openai_messages = self._image_files_added_openai_messages()

        # request 요청
        _response = self.client.responses.create(
            model=self.model,
            reasoning={"effort": self.reasoning_effort},
            input=openai_messages,
            text={"format": {"type": "json_object"}})

        # 응답 출력
        response = _response.output_text

        # 사용 정보 출력
        usage = {
            'Input': _response.usage.input_tokens,
            'Output': _response.usage.output_tokens,
            'Total': _response.usage.total_tokens}

        return response, usage

    # ------------------------------------------------
    # --- func-set: anthropic request ----------------
    # --- class-func: anthropic 이미지 파일 합성 메세지 ---
    def _image_files_added_anthropic_messages(self) -> None:
        """입력된 이미지 파일들을 Base64로 인코딩하여 API에 전달할 수 있는 형식으로 준비합니다.

        Returns:
            anthropic_messages (list): API에 전달할 메시지 리스트
        """
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
                    "data": encoded_string}})

        # self.messages[1]["content"]가 문자열일 경우, Claude 형식에 맞게 list로 변환
        if isinstance(self.messages[1]["content"], str):
            user_message_list = [{"type": "text", "text": self.messages[1]["content"]}]

        elif not isinstance(self.messages[1]["content"], list):
            user_message_list = []
        
        # 메시지 포맷에 맞게 이미지 파트 및 assistant_message 추가
        user_message_list.extend(image_parts)
        user_message_list.append({"type": "text", "text": self.messages[2]["content"]})

        # anthropic_messages 설정
        anthropic_messages = [{"role": "user", "content": user_message_list}]

        return anthropic_messages

    # --- class-func: anthropic request 요청 ---
    def anthropic_request(self,
                          MAX_TOKENS: int = 16000) -> str:
        """Anthropic에 요청합니다.

        Args:
            MAX_TOKENS (int): 최대 토큰 수

        Returns:
            response (str): 응답 문자열
            usage (dict): 사용 정보
        """        
        # anthropic_messages 설정
        anthropic_messages = [self.messages[1], self.messages[2]]
        if self.input_format == "jpeg":
            anthropic_messages = self._image_files_added_anthropic_messages()

        # request 요청
        # 추론 토큰이 0인 경우
        if self.reasoning_effort == 0:
            _response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=self.messages[0]["content"],
                messages=anthropic_messages)

            # 응답 출력
            response = _response.content[0].text

        # 추론 토큰이 0이 아닌 경우, 추론 노력 설정
        else:
            _response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                thinking={
                    "type": "enabled",
                    "budget_tokens": self.reasoning_effort},
                system=self.messages[0]["content"],
                messages=anthropic_messages)
        
            # 응답 출력
            response = next((block.text for block in _response.content if block.type == "text"), None)

        # 사용 정보 출력
        usage = {
            'Input': _response.usage.input_tokens,
            'Output': _response.usage.output_tokens,
            'Total': _response.usage.input_tokens + _response.usage.output_tokens}

        return response, usage

    # --------------------------------------------
    # --- func-set: google request ---------------
    # --- class-func: google 이미지 파일 합성 메세지 ---
    def _image_files_added_google_messages(self) -> list:
        """입력된 이미지 파일들을 Google API에 전달할 수 있는 형식으로 준비합니다.

        Returns:
            google_messages (list): Google API에 전달할 메시지 리스트
        """
        # user_message_list 설정
        user_message = [self.messages[1]["content"]]

        # 이미지 파트 초기화
        image_parts = []
        
        # self.input에 있는 각 파일 경로에 대해 반복
        for image_path in self.input:
            # PIL을 사용하여 이미지 파일 열기
            img = Image.open(image_path)
            # 리스트에 이미지 객체 추가
            image_parts.append(img)

        # assistant_message 설정
        assistant_message = [self.messages[2]["content"]]

        # google_messages 설정
        google_messages = user_message + image_parts + assistant_message

        return google_messages

    # --- class-func: google request 요청 ---
    def google_request(self) -> str:
        """Google에 요청합니다.

        Returns:
            response (str): 응답 문자열
            usage (dict): 사용 정보
        """
        # google_messages 설정
        google_messages = [self.messages[1]["content"], self.messages[2]["content"]]
        if self.input_format == "jpeg":
            google_messages = self._image_files_added_google_messages()

        # request 요청
        _response = self.client.models.generate_content(
            model=self.model,
            contents=google_messages,
            config=types.GenerateContentConfig(
                system_instruction=self.messages[0]["content"],
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(
                    thinking_budget=self.reasoning_effort
                )
            )
        )

        # 응답 출력
        response = _response.text

        # 사용 정보 출력
        usage = {
            'Input': _response.usage_metadata.prompt_token_count,
            'Output': _response.usage_metadata.candidates_token_count,
            'Total': _response.usage_metadata.total_token_count}

        return response, usage

    # --- class-func: deepseek 이미지 파일 합성 메세지 ---
    def _image_files_added_deepseek_messages(self) -> None:
        """입력된 이미지 파일들을 DeepSeek API에 전달할 수 있는 형식으로 준비합니다.

        Returns:
            deepseek_messages (list): DeepSeek API에 전달할 메시지 리스트
        """

        # deepseek_messages 설정
        deepseek_messages = self.messages

        return deepseek_messages

    # ----------------------------------------
    # --- func-set: deepseek request ---------
    # --- class-func: deepseek request 요청 ---
    def deepseek_request(self) -> str:
        """DeepSeek에 요청합니다.

        Returns:
            response (str): 응답 문자열
            usage (dict): 사용 정보
        """
        # deepseek_messages 설정
        deepseek_messages = self.messages
        if self.input_format == "jpeg":
            deepseek_messages = self._image_files_added_deepseek_messages()

        # request 요청
        _response = self.client.chat.completions.create(
            model=self.model,
            messages=deepseek_messages,
            response_format={"type": "json_object"},
            stream=False)

        # 응답 출력
        response = _response.choices[0].message.content

        # 사용 정보 출력
        usage = {
            'Input': _response.usage.prompt_tokens,
            'Output': _response.usage.completion_tokens,
            'Total': _response.usage.total_tokens}

        return response, usage
    
    # ---------------------------------
    # --- func-set: llm run -----------
    # --- class-func: json 응답 후처리 ---
    def _clean_json_response(self,
                             response: str) -> dict | list:
        """응답에서 JSON을 추출하고 파싱합니다.
        
        Args:
            response (str): 응답 문자열

        Returns:
            dict/list: 유효한 JSON인 경우 파싱된 Python 객체
            str: JSON을 찾지 못한 경우 원본 문자열
        """
        
        # 먼저 응답 전체가 이미 유효한 JSON인지 확인
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass  # JSON이 아니므로 추출 작업 진행
        
        # 코드 블록 확인 및 추출
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
            r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
            r"'''json\s*([\s\S]*?)\s*'''",  # '''json ... '''
            r"'''\s*([\s\S]*?)\s*'''",       # ''' ... '''
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response)
            if match:
                extracted = match.group(1).strip()
                # 추출한 내용이 유효한 JSON인지 확인
                try:
                    return json.loads(extracted)
                except json.JSONDecodeError:
                    continue
        
        # 코드 블록에서 찾지 못했으면 전체 응답에서 JSON 찾기
        extracted = response
        
        # JSON 객체/배열 추출
        # 가장 바깥쪽 { } 또는 [ ] 찾기
        json_patterns = [
            r'(\{(?:[^{}]|(?:\{(?:[^{}]|\{[^{}]*\})*\}))*\})',  # 중첩된 객체 처리
            r'(\[[\s\S]*\])',  # 배열
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, extracted)
            if match:
                json_str = match.group(1).strip()
                
                # JSON 유효성 검증 및 파싱
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        
        # 모든 패턴 실패 시, 원본에서 직접 JSON 찾기
        # 첫 { 부터 마지막 } 까지
        first_brace = extracted.find('{')
        last_brace = extracted.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_str = extracted[first_brace:last_brace+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # 첫 [ 부터 마지막 ] 까지 (배열인 경우)
        first_bracket = extracted.find('[')
        last_bracket = extracted.rfind(']')
        
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            json_str = extracted[first_bracket:last_bracket+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # 최후의 수단: 원본 반환 (JSON이 아닐 수 있음)
        return extracted.strip()

    # --- class-func: llm run 요청 ---
    def run(self,
            input: str | list,
            memory_note: str,
            idx: int,
            idx_length: int) -> str:
        """LLM 요청을 수행합니다.

        Args:
            input (list): 입력 데이터
            memory_note (str): 메모리 노트
            idx (int): 인덱스
            idx_length (int): 인덱스 길이

        Returns:
            response (str): 응답 문자열
        """
        # request 초기화
        self._init_request(input, memory_note)

        # Google API 요청 및 응답
        for _ in range(self.MAX_ATTEMPTS):
            try:
                if self.service == "OPENAI":
                    response, usage = self.openai_request()
                if self.service == "ANTHROPIC":
                    response, usage = self.anthropic_request(self.max_tokens)
                if self.service == "GOOGLE":
                    response, usage = self.google_request()
                if self.service == "DEEPSEEK":
                    response, usage = self.deepseek_request()

                # JSON 응답 후처리
                response = self._clean_json_response(response)

                # request와 response 출력
                request_and_response_text = self._print_request_and_response(response, usage)

                self.print_log("Task", ["Log", "Message"], ["Info", "Message"], idx=idx, idx_length=idx_length, function_name="llm.run", _print=request_and_response_text)

                return response

            except Exception as e:
                self.print_log("Task", ["Log", "Info"], ["Info", "Error"], function_name="openai_request", _print=e)
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

    # 클래스 테스트
    llm = LLM(
        email,
        project_name,
        solution=solution,
        next_solution=next_solution,
        process_number=process_number,
        process_name=process_name)

    # run
    response = llm.run(
        input=input,
        memory_note="",
        idx=1,
        idx_length=1)