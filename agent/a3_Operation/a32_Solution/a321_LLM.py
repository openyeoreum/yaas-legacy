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
# [a332-1] Solution-LLM
# ======================================================================
# class: LLM
# ======================================================================
class Manager(Manager):

    # ----------------------------
    # --- class-init -------------
    # --- class-func: LLM 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 solution: str = None,
                 next_solution: str = None,
                 process_number: str = None,
                 process_name: str = None,
                 main_lang: str = "ko") -> None:
        """사용자-프로젝트의 Operation에 통합 LLM 기능을 수행하는 클래스입니다.

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
            service (str): 사용할 LLM 서비스명 (ex. OpenAI, AnthropicAI, GoogleAI, DeepSeek)
        Returns:
            api_client (str): API 클라이언트
        """
        # 서비스에 따른 API 클라이언트 로드
        if service == "OpenAI":
            open_ai_client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
            return open_ai_client
        elif service == "AnthropicAI":
            anthropic_client = anthropic.Anthropic(api_key = os.getenv("ANTHROPIC_API_KEY"))
            return anthropic_client
        elif service == "GoogleAI":
            google_client = genai.Client(api_key= os.getenv("GEMINI_API_KEY"))
            return google_client
        elif service == "DeepSeek":
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
        message_dict = self._load_message_dict()

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
    def _print_request_and_response(self, service: str, messages: list, response: dict, usage: str) -> str:
        """request와 response를 출력합니다.

        Args:
            service (str): 서비스명 (예: "OpenAI", "AnthropicAI", "GoogleAI", "DeepSeek")
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

    # ------------------------------
    # --- func-set: llm request ----
    # --- class-func: openai 요청 ---
    def openai_request():
        pass

if __name__ == "__main__":
