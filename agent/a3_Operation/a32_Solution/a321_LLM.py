import os
import re
import json
import time
import random
import tiktoken
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

    # operation 경로
    api_file_path = "/yaas/agent/a2_DataFrame/a21_Operation/a213_APIConfig.json"

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
    # --- func-set: load config, form -----
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

    # --- class-func: load prompt ---
    def _load_prompt(self) -> str:
        """지정된 프롬프트 이름에 해당하는 프롬프트 텍스트를 로드하여 반환합니다.

        Returns:
            prompt_text (str): 불러온 프롬프트 텍스트
        """
        # 프롬프트 가져오기
        prompt = self.read_json("Solution", [self.solution, "Form", self.process_name], ["Prompt", self.main_lang])

        return prompt

    # --- class-func: 파일리스트 정리 ---

    # --- class-func: format prompt ---
    def format_prompt(self) -> str:
        """프롬프트 텍스트를 포맷팅하여 반환합니다.

        Returns:
            formatted_prompt (str): 포맷팅된 프롬프트 텍스트
        """
        # 프롬프트 불러오기
        prompt = self._load_prompt()

        # API 설정 불러오기
        message_time = f"current time: {str(Date("Second"))}\n\n"

        # 프롬프트 포맷팅
        messages = [
            {
                "role": PromptDic[0]["Role"],
                "content": messageTime + PromptDic[0]["Mark"] + PromptDic[0]["Message"]
            },
            {
                "role": PromptDic[1]["Role"],
                "content": PromptDic[1]["Request"][0]["Mark"] + ConvertQuotes(Model, PromptDic[1]["Request"][0]["Message"]) +
                PromptDic[1]["Request"][1]["Mark"] + ConvertQuotes(Model, PromptDic[1]["Request"][1]["Message"]) +
                PromptDic[1]["Request"][2]["Mark"] + ConvertQuotes(Model, PromptDic[1]["Request"][2]["Message"]) +
                PromptDic[1]["Request"][6]["Mark"] + PromptDic[1]["Request"][6]["InputMark"] + str(Input) + PromptDic[1]["Request"][6]["InputMark2"] + str(input2)
            },
            {
                "role": PromptDic[2]["Role"],
                "content": PromptDic[2]["OutputMark"] + memoryNote
            }
        ]

        return formatted_prompt

    # ------------------------------
    # --- func-set: llm request ----
    # --- class-func: openai 요청 ---
    def openai_request():