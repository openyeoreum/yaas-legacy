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
                 process_name: str = None) -> None:
        """사용자-프로젝트의 Operation에 통합 LLM 기능을 수행하는 클래스입니다.

        Attributes:
            email (str): 이메일
            project_name (str): 프로젝트명
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Audiobook, Translation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
        """
        # Manager 초기화
        super().__init__(
            email,
            project_name,
            solution,
            next_solution,
            process_number,
            process_name)

    # -------------------------------------
    # --- func-set: load config, form -----
    # --- class-func: api_config 불러오기 ---
    def _load_api_config(self) -> dict:
        """API 설정 JSON 파일을 로드하여 딕셔너리로 반환합니다.

        Returns:
            api_config_dict (dict): API 설정이 담긴 딕셔너리
        """
        # JSON 파일 열기 및 로드
        with open(self.api_file_path, 'r', encoding='utf-8') as file:
            api_config_dict = json.load(file)
        
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

    # --- class-func: solution 계산 ---

    # ------------------------------
    # --- func-set: llm request ----
    # --- class-func: openai 요청 ---
    def openai_request():