import os
import re
import json
import time
import sys
sys.path.append("/yaas")

from datetime import datetime
from backend.b2_Solution.b25_DataFrame.b251_DataCommit.b2511_LLMLoad import OpenAI_LLMresponse, ANTHROPIC_LLMresponse

#####################
##### Input 생성 #####
#####################
## Process1: Index 불러오기
def LoadIndex():
    with open("/yaas/backend/b2_Solution/b25_DataFrame/b251_DataCommit/b2510_Index.json", "r") as f:
        Index = json.load(f)
    return Index

################################
##### Process 진행 및 업데이트 #####
################################
## Translation 프롬프트 요청 및 결과물 Json화
def TranslationProcessUpdate(projectName, email, MainLang, Translation, mode = "Master", MessagesReview = "on"):
    print(f"< User: {email} | Translation: {projectName} ({Translation}) >>> ({MainLang}) | TranslationUpdate 시작 >")
    sys.exit()