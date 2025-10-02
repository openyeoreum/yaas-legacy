import os
import re
import json
import time
import random
import tiktoken
import textwrap
import anthropic
import sys
sys.path.append("/yaas")

from datetime import datetime
from openai import OpenAI
from google import genai
from agent.a3_Operation.a31_Operation.a314_Manager import Manager

# ======================================================================
# [a332-1] Operation-LLM: Setting
# ======================================================================
# class: Setting
# ======================================================================
class Setting(Manager):

    # --------------------------------
    # --- class-init -----------------
    # --- class-func: Setting 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 solution: str = None,
                 next_solution: str = None,
                 process_number: str = None,
                 process_name: str = None,
                 main_lang: str = "ko") -> None:
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
            open_ai_client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
            return open_ai_client
        elif service == "ANTHROPIC":
            anthropic_client = anthropic.Anthropic(api_key = os.getenv("ANTHROPIC_API_KEY"))
            return anthropic_client
        elif service == "GOOGLE":
            google_client = genai.Client(api_key= os.getenv("GEMINI_API_KEY"))
            return google_client
        elif service == "DEEPSEEK":
            deepseek_client = OpenAI(api_key = os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
            return deepseek_client

    # ----------------------------------
    # --- func-set: load message -------
    # --- class-func: message 불러오기 ---
    def _load_message(self) -> str:
        """지정된 프롬프트 이름에 해당하는 프롬프트 텍스트를 로드하여 반환합니다.

        Returns:
            message_dict (dict): 불러온 메시지 딕셔너리
        """
        # 프롬프트 불러오기
        message_dict = self.read_json("Solution", [self.solution, "Form", self.process_name], ["Prompt", self.main_lang])

        # 프롬프트 언어 설정
        if self.main_lang == "Ko":
            message_dict = message_dict["Ko"]
        else:
            message_dict = message_dict["Global"]

        return message_dict

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
        if self.main_lang == "ko":
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
    def _format_prompt_to_messages(self, input: list, memory_note: str) -> str:
        """프롬프트 텍스트를 포맷팅하여 반환합니다.

        Returns:
            formatted_prompt (str): 포맷팅된 프롬프트 텍스트
        """
        # API 설정 불러오기
        message_time = f"current time: {str(datetime('Second'))}\n\n"

        # 프롬프트 불러오기
        message_dict = self._load_message()

        # 프롬프트["InputFormat"]이 Text가 아닌 경우에는 파일리스트 정리
        if message_dict["InputFormat"] != "text":
            input_paths = input
            input = self._format_input_paths_to_str(input_paths)

        # ResponseExample 포맷팅
        response_example = self._format_response_example_dict_to_str(message_dict["ResponseExample"])

        # 프롬프트 포맷팅
        system_message = message_dict["Messages"]["System"]
        system_content =  message_time +system_message["Mark"] + system_message["MarkLineBreak"] + system_message["Message"] + system_message["MessageLineBreak"]

        user_message = message_dict["Messages"]["User"]
        _user_content = ""
        for message in user_message[:-1]:
            _user_content += message["Mark"] + message["MarkLineBreak"] + message["Message"] + message["MessageLineBreak"]
            _user_content.format(ResponseExample=response_example)
        user_content = _user_content + user_message[-1]["Request"] + user_message[-1]["RequestLineBreak"]

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
    def print_request_and_response(self, service: str, messages: list, response: dict, usage: str) -> str:
        """request와 response를 출력합니다.

        Args:
            service (str): 서비스명 (예: "OPENAI", "ANTHROPIC", "GOOGLE", "DEEPSEEK")
            messages (list): 메시지 리스트
            response (dict): 응답 딕셔너리
            usage (str): 사용량 텍스트

        Print:
            messages_and_response_text (str): request와 response
        """
        # 각 메시지를 형식에 맞는 문자열 생성
        request_parts = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            request_parts.append(f"* {role}\n\n{content}")

        # 생성된 메시지 목록을 두 줄 띄어쓰기로 합쳐 하나의 문자열 블록생성
        request_block = "\n\n".join(request_parts)

        # 요청 텍스트 생성
        request_text = f"🟦- Request -🟦\nService: {service}\n\n{request_block}\n\n"

        # 응답 텍스트 생성
        response_text = f"🟦- Response -🟦\n{response}\n\n🟦- Usage -🟦\n{usage}"
        
        # request와 response 출력
        request_and_response_text = request_text + response_text
        print(request_and_response_text)

# ======================================================================
# [a332-2] Operation-LLM: Request
# ======================================================================
# class: Request
# ======================================================================
class Request(Setting):

    # --------------------------------
    # --- class-init -----------------
    # --- class-func: Request 초기화 ---
    def __init__(self,
                 input: list = None,
                 memory_note: str = None) -> None:
        """사용자-프로젝트의 Operation에 통합 LLM 기능을 수행하는 클래스입니다.

        Attributes:
            input (list): 입력 데이터
            memory_note (str): 메모리 노트
        """

        # attributes 설정
        self.input = input
        self.memory_note = memory_note

        api_config_dict = self._load_api_config()
        api_dict = self.read_json("Solution", [self.solution, "Form", self.process_name], ["API"])
        service = api_dict["Service"]
        _model = api_dict["Model"]
        self.client = self._load_api_client(service)
        self.model = api_config_dict["LanguageModel"][service][_model]["Model"]
        self.reasoning_effort = api_config_dict["LanguageModel"][service][_model]["ReasoningEffort"]

        format_dict = self.read_json("Solution", [self.solution, "Form", self.process_name], ["Format"])
        self.input_format = format_dict["InputFormat"]
        self.response_format = format_dict["ResponseFormat"]

        self.messages = self._format_prompt_to_messages(self.input, self.memory_note)

        self.MAX_ATTEMPTS = 100

    # ----------------------------------
    # --- func-set: llm request --------
    # --- class-func: 이미지 파일 업로드 ---
    def _upload_image_files(self) -> None:
        """입력된 이미지 파일들을 OpenAI에 업로드하고 self.messages를 업데이트합니다.
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
        image_contents = [
            {"type": "input_image", "file_id": fid, "detail": "high"}
            for fid in image_file_ids
        ]
        self.messages[1]["content"].extend(image_contents)

    # --- class-func: llm request 요청 ---
    def openai_request(self):
        """OpenAI 요청을 수행합니다.

        Returns:
            response (str): 응답 문자열
            usage (dict): 사용량 딕셔너리
        """
        # 입력 포맷이 jpeg인 경우, 이미지 업로드 함수 호출
        if self.input_format == "jpeg":
            self._upload_image_files()

        # request 요청 및 response 출력
        for _ in range(self.MAX_ATTEMPTS):
            try:
                if self.response_format == "json":
                    response = self.client.responses.create(
                        model = self.model,
                        reasoning = {"effort": self.reasoning_effort},
                        input = self.messages,
                        text = {"format": {"type": "json_object"}}
                    )
                else:
                    response = self.client.responses.create(
                        model = self.model,
                        reasoning = {"effort": self.reasoning_effort},
                        input = self.messages
                    )
                
                response = response.output_text
                usage = {
                    'Input': response.usage.input_tokens,
                    'Output': response.usage.output_tokens,
                    'Total': response.usage.total_tokens
                }

                # request와 response 출력
                self.print_request_and_response(self.service, self.messages, response, usage)
                
                return response, usage

            except Exception as e:
                print(f"OpenAI 요청 오류: {e}")
                time.sleep(random.uniform(5, 10))
                continue





if __name__ == "__main__":

    # --- class-test ---
    # 인자 설정
    email = "yeoreum00128@gmail.com3"
    project_name = "글로벌솔루션여름"