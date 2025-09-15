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
from google.genai import types
from agent.a2_Solution.a22_Operation.a224_GetProcessData import GetPromptFrame


######################
##### LLM 공통사항 #####
######################
## 오늘 날짜
def Date(Option = "Day"):
    if Option == "Day":
        now = datetime.now()
        date = now.strftime('%y%m%d')
    elif Option == "Second":
        now = datetime.now()
        date = now.strftime('%y%m%d%H%M%S')
    
    return date


################################
################################
########## OpenAI API ##########
################################
################################


###############################
##### OpenAI LLM Response #####
###############################
## 프롬프트 요청할 LLMmessages 메세지 구조 생성
def LLMmessages(Process, Input, Model, MainLang = "ko", Root = "agent", promptFramePath = "", Output = "", mode = "Example", input2 = "", inputMemory = "", inputMemory2 = "", outputMemory = "", memoryNote = "", outputEnder = ""):
    ## '...'을 “...”로 변경하여 Claude에서도 json 형식이 갖춰지도록 구성
    def ConvertQuotes(Model, Message):
        if "claude" in Model:
            Message = Message.replace("‘", "“")
            Message = Message.replace("’", "”")
            if not Message:
                return Message
            QuoteCount = 0
            ConvertMessage = ""
            for char in Message:
                if char == "'":
                    QuoteCount += 1
                    if QuoteCount % 2 == 1:
                        ConvertMessage += "“"
                    else:
                        ConvertMessage += "”"
                else:
                    ConvertMessage += char
            return ConvertMessage
        else:
            return Message
    
    if promptFramePath == "":
        promptFrame = GetPromptFrame(Process, MainLang)
    else:
        with open(promptFramePath, 'r', encoding = 'utf-8') as promptFrameJson:
            promptFrame = json.load(promptFrameJson)

    messageTime = "current time: " + str(Date("Second")) + '\n\n'

    ## InputFormat이 text가 아닌 경우에는 파일리스트 정리
    InputFormat = promptFrame["InputFormat"]
    if InputFormat != "text":
        InputList = [os.path.basename(path) for path in Input]

        Input = ""
        if MainLang == "ko":
            for i in range(len(InputList)):
                Input += f"업로드 자료 {i+1} : {InputList[i]}\n"

        else:
            for i in range(len(InputList)):
                Input += f"Uploaded Data {i+1} : {InputList[i]}\n"

    # messages
    PromptDic = promptFrame["Master"]

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
                        PromptDic[1]["Request"][3]["Mark"] + PromptDic[1]["Request"][3]["InputMasterMark"] + str(PromptDic[1]["Request"][3]["InputMaster"]) +
                        PromptDic[1]["Request"][3]["OutputMasterMark"] + str(PromptDic[1]["Request"][3]["OutputMaster"]) +
                        PromptDic[1]["Request"][4]["Mark"] + PromptDic[1]["Request"][4]["InputMasterMark"] + str(PromptDic[1]["Request"][4]["InputMaster"]) +
                        PromptDic[1]["Request"][4]["OutputMasterMark"] + str(PromptDic[1]["Request"][4]["OutputMaster"]) +
                        PromptDic[1]["Request"][5]["Mark"] + PromptDic[1]["Request"][5]["InputMasterMark"] + str(PromptDic[1]["Request"][5]["InputMaster"]) +
                        PromptDic[1]["Request"][5]["OutputMasterMark"] + str(PromptDic[1]["Request"][5]["OutputMaster"]) +
                        PromptDic[1]["Request"][6]["Mark"] + PromptDic[1]["Request"][6]["InputMark"] + str(Input) + PromptDic[1]["Request"][6]["InputMark2"] + str(input2)
        },
        {
            "role": PromptDic[2]["Role"],
            "content": PromptDic[2]["OutputMark"] + 
                        memoryNote + 
                        PromptDic[2]["OutputStarter"]
        }
    ]

    encoding = tiktoken.get_encoding("cl100k_base")
    # print(f'messages: {messages}')
    InputTokens = len(encoding.encode(str(Input)))
    messageTokens = len(encoding.encode(str(messages)))
    OutputTokensRatio = 1.0
    outputTokens = InputTokens * OutputTokensRatio
    totalTokens = messageTokens + outputTokens
    Temperature = 1.0

    return messages, totalTokens, Temperature
  
## 프롬프트에 메세지 확인
def LLMmessagesReview(Process, Input, Count, Response, Usage, Model, MAINLANG = "ko", ROOT = "agent", PromptFramePath = "", MODE = "Example", INPUT2 = "", INPUTMEMORY = "", OUTPUTMEMORY = "", MEMORYCOUNTER = "", OUTPUTENDER = ""):

    Messages, TotalTokens, Temperature = LLMmessages(Process, Input, Model, MainLang = MAINLANG, Root = ROOT, promptFramePath = PromptFramePath, mode = MODE, input2 = INPUT2, inputMemory = INPUTMEMORY, outputMemory = OUTPUTMEMORY, memoryNote = MEMORYCOUNTER, outputEnder = OUTPUTENDER)

    TextMessagesList = [f"\n############# Messages #############\n",
                        f"Messages: ({Count}), ({Model}), ({MODE}), (Tep:{Temperature})\n",
                        f"####################################\n\n",
                        "Expected Tokens: ", str(TotalTokens), "\n\n",
                        "* ", str(Messages[0]["role"]), "\n\n",
                        str(Messages[0]["content"]), "\n\n",
                        "* ", str(Messages[1]["role"]), "\n\n",
                        str(Messages[1]["content"]), "\n\n",
                        "* ", str(Messages[2]["role"]), "\n\n",
                        str(Messages[2]["content"])]
    TextMessages = "".join(TextMessagesList)
    TextReponseList = [f"\n\n############# Response #############\n\n",
                       f"{Response}",
                       f"\n\n############## Usage ###############\n\n",
                       f"Usage: {Usage}",
                       f"\n\n####################################\n"]
    TextReponse = "".join(TextReponseList)
    
    return print(TextMessages + TextReponse)
  
## 프롬프트 실행
def OpenAI_LLMresponse(projectName, email, Process, Input, Count, mainLang = "ko", root = "agent", PromptFramePath = "", Mode = "Master", Input2 = "", InputMemory = "", OutputMemory = "", MemoryNote = "", OutputEnder = "", MaxAttempts = 100, messagesReview = "off"):
    OpenAIClient = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
    if PromptFramePath == "":
        promptFrame = GetPromptFrame(Process, mainLang)
    else:
        with open(PromptFramePath, 'r', encoding = 'utf-8') as promptFrameJson:
            promptFrame = json.load(promptFrameJson)

    Messages, TotalTokens, temperature = LLMmessages(Process, Input, 'gpt', MainLang = mainLang, Root = root, promptFramePath = PromptFramePath, mode = Mode, input2 = Input2, inputMemory = InputMemory, outputMemory = OutputMemory, memoryNote = MemoryNote, outputEnder = OutputEnder)

    inputFormat = promptFrame["InputFormat"]
    Model = promptFrame["OpenAI"]["MasterModel"]

    # Temperature = temperature
    ReasoningEffort = promptFrame["OpenAI"]["ReasoningEffort"]

    # JPEG 파일 업로드 함수(파일 업로드 → file_id 리스트)
    def UploadJPEG(JPEGFilePath):
        with open(JPEGFilePath, "rb") as JPEGFile:
            result = OpenAIClient.files.create(file = JPEGFile, purpose = "vision")
            return result.id
    
    # InputFormat이 jpeg인 경우, 이미지 파일 업로드 후 Messages[1]["content"]에 이미지 블록 추가
    if inputFormat == "jpeg":
        # 파일 업로드 → file_id 리스트
        imageFileIds = [UploadJPEG(JPEGFilePath) for JPEGFilePath in Input]

        # Messages[1]["content"]가 문자열이라면, input_text 블록으로 변환
        if isinstance(Messages[1]["content"], str):
            Messages[1]["content"] = [{"type": "input_text", "text": Messages[1]["content"]}]

        elif not isinstance(Messages[1]["content"], list):
            Messages[1]["content"] = []

        # 이미지 블록들 추가 (append X, extend O)
        Messages[1]["content"].extend({"type": "input_image", "file_id": fid, "detail": "high"} for fid in imageFileIds)

    for _ in range(MaxAttempts):
        try:
            # JSON 출력을 요청하는 경우
            if promptFrame["OutputFormat"] == 'json':
                response = OpenAIClient.responses.create(
                    model = Model,
                    reasoning = {"effort": ReasoningEffort},
                    input = Messages,
                    text = {"format": {"type": "json_object"}}
                )
            # 일반 텍스트 출력을 요청하는 경우
            else:
                response = OpenAIClient.responses.create(
                    model = Model,
                    reasoning = {"effort": ReasoningEffort},
                    input = Messages
                )
                
            Response = response.output_text
            Usage = {
                'Input': response.usage.input_tokens,
                'Output': response.usage.output_tokens,
                'Total': response.usage.total_tokens
            }
          
            if isinstance(email, str):
                print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMresponse 완료")
            else:
                print(f"LifeGraphName: {projectName} | Process: {Process} | OpenAI_LLMresponse 완료")
            
            if messagesReview == "on":
                LLMmessagesReview(Process, Input, Count, Response, Usage, Model, MAINLANG = mainLang, ROOT = root, MODE = Mode, INPUT2 = Input2, INPUTMEMORY = InputMemory, OUTPUTMEMORY = OutputMemory, MEMORYCOUNTER = MemoryNote, OUTPUTENDER = OutputEnder)

            return Response, Usage, Model
      
        except Exception as e:
            if isinstance(email, str):
                print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMresponse에서 오류 발생\n\n{e}")
            else:
                print(f"LifeGraphName: {projectName} | Process: {Process} | OpenAI_LLMresponse에서 오류 발생\n\n{e}")
            time.sleep(random.uniform(5, 10))
            continue


###################################
###################################
########## ANTHROPIC API ##########
###################################
###################################


##################################
##### ANTHROPIC LLM Response #####
##################################
## JsonParsing의 Filter(Error 예외처리)
def JsonParsingFilter(Response, RawResponse):
    # Error1: JSON 형식 예외 처리
    try:
        TestResponse = json.loads(Response)
    except json.JSONDecodeError:
        return "BodyTranslation, JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: Json 내용 동일성 확인
    # 1단계: 백슬래시로 시작하는 모든 이스케이프 시퀀스(백슬래시와 그 다음 한 글자)를 제거합니다.
    Response_no_escape = re.sub(r'\\.', '', Response)
    RawResponse_no_escape = re.sub(r'\\.', '', RawResponse)

    # 2단계: 나머지 특수문자, 공백, 줄바꿈 등을 제거하여 알파벳(다국어 포함)과 숫자만 남깁니다. 단 "는 남김
    Response_clean = re.sub(r'[^\w\d"]', '', Response_no_escape, flags = re.UNICODE)
    Response_clean = Response_clean.replace('_', '')
    RawResponse_clean = re.sub(r'[^\w\d"]', '', RawResponse_no_escape, flags = re.UNICODE)
    RawResponse_clean = RawResponse_clean.replace('_', '')

    ResponseLength = len(Response_clean)
    RawResponseLength = len(RawResponse_clean)
    if ResponseLength != RawResponseLength:
        return f"BodyTranslation, JSONDecode에서 오류 발생: Json 내용의 텍스트 수가 다름 Response({ResponseLength}), RawResponse({RawResponseLength})"
      
    # 3단계: RawResponse의 데이터 형태 확인 및 일치화
    RawResponse = RawResponse.strip()
    DictType = False
    if RawResponse.startswith('{') and RawResponse.endswith('}'):
        DictType = True
    elif RawResponse.startswith('[') and RawResponse.endswith(']'):
        DictType = False
        
    # Response에서 필요없는 대괄호 형성 문제 해결
    if DictType:
        Response = RemoveListBrackets(Response)

    return Response

## JsonParsing 결과 형태가 리스트인 경우 대괄호 제거
def RemoveListBrackets(ResponseStr):
    ResponseStr = ResponseStr.strip()
    # 문자열이 '[{'로 시작하고 '}]'로 끝나는지 확인
    if ResponseStr.strip().startswith('[{') and ResponseStr.strip().endswith('}]'):
        # 첫 번째 '[' 제거
        temp = ResponseStr.strip()[1:]
        # 마지막 ']' 제거
        result = temp[:-1]
        return result
    else:
        # 이미 대괄호가 없거나 형식이 다른 경우 원본 반환
        return ResponseStr
      
## Json파싱 오류 해결
def JsonParsingProcess(projectName, email, RawResponse, FilterFunc, MainLang = "ko", LLM = "GOOGLE"):
    Process = "JsonParsing"
    ErrorCount = 1
    while True:
        if LLM == "GOOGLE":
            Response, Usage, Model = GOOGLE_LLMresponse(projectName, email, Process, RawResponse, ErrorCount, mainLang = MainLang, messagesReview = "off")
        if LLM == "OpenAI":
            Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, RawResponse, ErrorCount, mainLang = MainLang, messagesReview = "off")
        FilteredResponse = FilterFunc(Response, RawResponse)
        
        if 'JSONDecode에서 오류 발생:' in FilteredResponse:
            print(f"Project: {projectName} | ErrorCount: {Process} {ErrorCount}/5 | {FilteredResponse}")
            ErrorCount += 1
            print(f"Project: {projectName} | ErrorCount: {Process} {ErrorCount}/5 | "
                f"오류횟수 {ErrorCount}회, 3초 후 프롬프트 재시도")
            
            if ErrorCount >= 5:
                print(f"Project: {projectName} | ErrorCount: {Process} {ErrorCount}/5 | "
                        f"오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
                return Response
            time.sleep(10)
            continue
        
        print(f"Project: {projectName} | ErrorCount: {Process} {ErrorCount}/5 | JSONDecode 완료")
        return FilteredResponse

## 프롬프트 실행
def ANTHROPIC_LLMresponse(projectName, email, Process, Input, Count, mainLang = "ko", root = "agent", PromptFramePath = "", Mode = "Master", Input2 = "", InputMemory = "", OutputMemory = "", MemoryNote = "", OutputEnder = "", MaxAttempts = 100, messagesReview = "off"):

    AnthropicAIClient = anthropic.Anthropic(api_key = os.getenv("ANTHROPIC_API_KEY"))
    if PromptFramePath == "":
        promptFrame = GetPromptFrame(Process, mainLang)
    else:
        with open(PromptFramePath, 'r', encoding = 'utf-8') as promptFrameJson:
            promptFrame = json.load(promptFrameJson)


    Messages, TotalTokens, temperature = LLMmessages(Process, Input, 'claude', MainLang = mainLang, Root = root, promptFramePath = PromptFramePath, mode = Mode, input2 = Input2, inputMemory = InputMemory, outputMemory = OutputMemory, memoryNote = MemoryNote, outputEnder = OutputEnder)

    inputFormat = promptFrame["InputFormat"]
    Model = promptFrame["ANTHROPIC"]["MasterModel"]
    
    for _ in range(MaxAttempts):
      try:
          if promptFrame["OutputFormat"] == 'json':
            response = AnthropicAIClient.messages.create(
                model = Model,
                max_tokens = 4096,
                system = Messages[0]["content"],
                messages = [{"role": "user", "content": f"{Messages[1]['content']}\n\n{Messages[2]['content']}\n\nAssistant: ```json"}]
            )
          else:
            response = AnthropicAIClient.messages.create(
                model = Model,
                max_tokens = 4096,
                system = Messages[0]["content"],
                messages = [{"role": "user", "content": f"{Messages[1]['content']}\n\n{Messages[2]['content']}"}]
            )
          Response = response.content[0].text
          Usage = {'Input': response.usage.input_tokens,
                   'Output': response.usage.output_tokens,
                   'Total': response.usage.input_tokens + response.usage.output_tokens}
          
          # Response Mode 전처리1: ([...]와 {...}중 하나로 전처리)
          if promptFrame["OutputFormat"] == 'json':
              pattern = r'(?:\'\'\'|```|\"\"\")(.*?)(?:\'\'\'|```|\"\"\")'
              match = re.search(pattern, Response, re.DOTALL)
              if match:
                  Response = match.group(1).strip()
              Response = Response.replace('\n', '\\n')
              StartIndexBracket = Response.find('[')
              StartIndexBrace = Response.find('{')
              if StartIndexBracket != -1 and StartIndexBrace != -1:
                  StartIndex = min(StartIndexBracket, StartIndexBrace)
              elif StartIndexBracket != -1:
                  StartIndex = StartIndexBracket
              elif StartIndexBrace != -1:
                  StartIndex = StartIndexBrace
              else:
                  StartIndex = -1
              if StartIndex != -1:
                  if Response[StartIndex] == '[':
                      EndIndex = Response.rfind(']')
                  else:
                      EndIndex = Response.rfind('}')
                  if EndIndex != -1:
                      JsonResponse = Response[StartIndex:EndIndex+1]
                  else:
                      JsonResponse = Response
              else:
                  JsonResponse = Response
          else:
              JsonResponse = Response
          
          if isinstance(email, str):
              print(f"Project: {projectName} | Process: {Process} | ANTHROPIC_LLMresponse 완료")
          else:
              print(f"LifeGraphName: {projectName} | Process: {Process} | ANTHROPIC_LLMresponse 완료")
          
          if messagesReview == "on":
              LLMmessagesReview(Process, Input, Count, JsonResponse, Usage, Model, MAINLANG = mainLang, ROOT = root, MODE = Mode, INPUT2 = Input2, INPUTMEMORY = InputMemory, OUTPUTMEMORY = OutputMemory, MEMORYCOUNTER = MemoryNote, OUTPUTENDER = OutputEnder)

          ## Response Mode 전처리2: JsonParsing의 재구조화
          if ":" in JsonResponse and "{" in JsonResponse and "}" in JsonResponse:
              try:
                  TestResponse = json.loads(JsonResponse)
              except json.JSONDecodeError:
                  print(f"Project: {projectName} | Process: {Process} | ANTHROPIC_LLMresponse 파싱오류 | JsonParsingProcess 시작")
                  JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter, MainLang = mainLang, LLM = "GOOGLE")
                  try:
                      TestResponse = json.loads(JsonResponse)
                  except json.JSONDecodeError:
                      JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter, MainLang = mainLang, LLM = "OpenAI")

          return JsonResponse, Usage, Model
      
      except Exception as e:
          if isinstance(email, str):
            print(f"Project: {projectName} | Process: {Process} | ANTHROPIC_LLMresponse에서 오류 발생\n\n{e}")
          else:
            print(f"LifeGraphName: {projectName} | Process: {Process} | ANTHROPIC_LLMresponse에서 오류 발생\n\n{e}")
          time.sleep(random.uniform(5, 10))
          continue

###############################
##### GOOGLE LLM Response #####
###############################

## 프롬프트 실행
def GOOGLE_LLMresponse(projectName, email, Process, Input, Count, mainLang = "ko", root = "agent", PromptFramePath = "", Mode = "Master", Input2 = "", InputMemory = "", OutputMemory = "", MemoryNote = "", OutputEnder = "", MaxAttempts = 100, messagesReview = "off"):

    GoogleAIClient = genai.Client(api_key= os.getenv("GEMINI_API_KEY"), http_options={'api_version':'v1alpha'})
    if PromptFramePath == "":
        promptFrame = GetPromptFrame(Process, mainLang)
    else:
        with open(PromptFramePath, 'r', encoding = 'utf-8') as promptFrameJson:
            promptFrame = json.load(promptFrameJson)

    Messages, TotalTokens, temperature = LLMmessages(Process, Input, 'claude', MainLang = mainLang, Root = root, promptFramePath = PromptFramePath, mode = Mode, input2 = Input2, inputMemory = InputMemory, outputMemory = OutputMemory, memoryNote = MemoryNote, outputEnder = OutputEnder)

    inputFormat = promptFrame["InputFormat"]
    Model = promptFrame["GOOGLE"]["MasterModel"]

    # JPEG 파일 업로드 함수
    def UploadJPEG(JPEGFilePath):
        with open(JPEGFilePath, "rb") as f:
            jpegBytes = f.read()
        return types.Part.from_bytes(data = jpegBytes, mime_type = "image/jpeg")

    # InputFormat이 jpeg인 경우, 이미지 파일들을 Part 리스트로 변환
    ImageFiles = []
    if inputFormat == "jpeg":
        ImageFiles = [UploadJPEG(path) for path in Input]

    for _ in range(MaxAttempts):
        try:
            Response = ''
            if promptFrame["OutputFormat"] == 'json':
                for responseChunk in GoogleAIClient.models.generate_content_stream(
                    model = Model,
                    contents = [
                    types.Content(
                        role = "user",
                        parts = [types.Part.from_text(text = f"{Messages[0]['content']}\n\n{Messages[1]['content']}\n\n{Messages[2]['content']}\n\n"),] + ImageFiles,
                        ),
                    ],
                    config = types.GenerateContentConfig(response_mime_type = "application/json",)
                ):
                    if responseChunk.text is not None:
                        Response += responseChunk.text
            else:
                for responseChunk in GoogleAIClient.models.generate_content_stream(
                    model = Model,
                    contents = [
                    types.Content(
                        role = "user",
                        parts = [types.Part.from_text(text = f"{Messages[0]['content']}\n\n{Messages[1]['content']}\n\n{Messages[2]['content']}\n\n"),] + ImageFiles,
                        ),
                    ],
                    config = types.GenerateContentConfig(response_mime_type = "text/plain",)
                ):
                    if responseChunk.text is not None:
                        Response += responseChunk.text
            Usage = {
                'Input': responseChunk.usage_metadata.prompt_token_count,
                'Output': responseChunk.usage_metadata.candidates_token_count,
                'Total': responseChunk.usage_metadata.total_token_count
            }
            
            # Response Mode 전처리1: ([...]와 {...}중 하나로 전처리)
            if promptFrame["OutputFormat"] == 'json':
                pattern = r'(?:\'\'\'|```|\"\"\")(.*?)(?:\'\'\'|```|\"\"\")'
                match = re.search(pattern, Response, re.DOTALL)
                if match:
                    Response = match.group(1).strip()
                Response = Response.replace('\n', '\\n')
                StartIndexBracket = Response.find('[')
                StartIndexBrace = Response.find('{')
                if StartIndexBracket != -1 and StartIndexBrace != -1:
                    StartIndex = min(StartIndexBracket, StartIndexBrace)
                elif StartIndexBracket != -1:
                    StartIndex = StartIndexBracket
                elif StartIndexBrace != -1:
                    StartIndex = StartIndexBrace
                else:
                    StartIndex = -1
                if StartIndex != -1:
                    if Response[StartIndex] == '[':
                        EndIndex = Response.rfind(']')
                    else:
                        EndIndex = Response.rfind('}')
                    if EndIndex != -1:
                        JsonResponse = Response[StartIndex:EndIndex+1]
                    else:
                        JsonResponse = Response
                else:
                    JsonResponse = Response
            else:
                JsonResponse = Response
            
            if isinstance(email, str):
                print(f"Project: {projectName} | Process: {Process} | GOOGLE_LLMresponse 완료")
            else:
                print(f"LifeGraphName: {projectName} | Process: {Process} | GOOGLE_LLMresponse 완료")
            
            if messagesReview == "on":
                LLMmessagesReview(Process, Input, Count, JsonResponse, Usage, Model, MAINLANG = mainLang, ROOT = root, MODE = Mode, INPUT2 = Input2, INPUTMEMORY = InputMemory, OUTPUTMEMORY = OutputMemory, MEMORYCOUNTER = MemoryNote, OUTPUTENDER = OutputEnder)

            ## Response Mode 전처리2: JsonParsing의 재구조화
            if ":" in JsonResponse and "{" in JsonResponse and "}" in JsonResponse:
                try:
                    TestResponse = json.loads(JsonResponse)
                except json.JSONDecodeError:
                    print(f"Project: {projectName} | Process: {Process} | GOOGLE_LLMresponse 파싱오류 | JsonParsingProcess 시작")
                    JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter, MainLang = mainLang, LLM = "GOOGLE")
                    try:
                        TestResponse = json.loads(JsonResponse)
                    except json.JSONDecodeError:
                        JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter, MainLang = mainLang, LLM = "OpenAI")

            return JsonResponse, Usage, Model
        
        except Exception as e:
            if isinstance(email, str):
                print(f"Project: {projectName} | Process: {Process} | GOOGLE_LLMresponse에서 오류 발생\n\n{e}")
            else:
                print(f"LifeGraphName: {projectName} | Process: {Process} | GOOGLE_LLMresponse에서 오류 발생\n\n{e}")
            time.sleep(random.uniform(5, 10))
            continue
        
#################################
##### DEEPSEEK LLM Response #####
#################################

## 프롬프트 실행
def DEEPSEEK_LLMresponse(projectName, email, Process, Input, Count, mainLang = "ko", root = "agent", PromptFramePath = "", Mode = "Master", Input2 = "", InputMemory = "", OutputMemory = "", MemoryNote = "", OutputEnder = "", MaxAttempts = 100, messagesReview = "off"):
    DeepSeekClient = OpenAI(api_key = os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
    if PromptFramePath == "":
      promptFrame = GetPromptFrame(Process, mainLang)
    else:
      with open(PromptFramePath, 'r', encoding = 'utf-8') as promptFrameJson:
        promptFrame = json.load(promptFrameJson)

    Messages, TotalTokens, temperature = LLMmessages(Process, Input, 'claude', MainLang = mainLang, Root = root, promptFramePath = PromptFramePath, mode = Mode, input2 = Input2, inputMemory = InputMemory, outputMemory = OutputMemory, memoryNote = MemoryNote, outputEnder = OutputEnder)

    inputFormat = promptFrame["InputFormat"]
    Model = promptFrame["DEEPSEEK"]["MasterModel"]
    
    for _ in range(MaxAttempts):
      try:
          if promptFrame["OutputFormat"] == 'json':
            response = DeepSeekClient.chat.completions.create(
                model = Model,
                messages = [
                    {"role": "system", "content": f"{Messages[0]['content']}"},
                    {"role": "user", "content": f"{Messages[1]['content']}\n\n{Messages[2]['content']}\n```json"},
                ],
                stream = False
            )
          else:
            response = DeepSeekClient.chat.completions.create(
                model = Model,
                messages = [
                    {"role": "system", "content": f"{Messages[0]['content']}"},
                    {"role": "user", "content": f"{Messages[1]['content']}\n\n{Messages[2]['content']}"},
                ],
                stream = False
            )
          Response = response.choices[0].message.content
          Usage = {'Input': response.usage.prompt_tokens,
                  'Output': response.usage.completion_tokens,
                  'Total': response.usage.total_tokens }
          
          # Response Mode 전처리1: ([...]와 {...}중 하나로 전처리)
          if promptFrame["OutputFormat"] == 'json':
              pattern = r'(?:\'\'\'|```|\"\"\")(.*?)(?:\'\'\'|```|\"\"\")'
              match = re.search(pattern, Response, re.DOTALL)
              if match:
                  Response = match.group(1).strip()
              Response = Response.replace('\n', '\\n')
              StartIndexBracket = Response.find('[')
              StartIndexBrace = Response.find('{')
              if StartIndexBracket != -1 and StartIndexBrace != -1:
                  StartIndex = min(StartIndexBracket, StartIndexBrace)
              elif StartIndexBracket != -1:
                  StartIndex = StartIndexBracket
              elif StartIndexBrace != -1:
                  StartIndex = StartIndexBrace
              else:
                  StartIndex = -1
              if StartIndex != -1:
                  if Response[StartIndex] == '[':
                      EndIndex = Response.rfind(']')
                  else:
                      EndIndex = Response.rfind('}')
                  if EndIndex != -1:
                      JsonResponse = Response[StartIndex:EndIndex+1]
                  else:
                      JsonResponse = Response
              else:
                  JsonResponse = Response
          else:
              JsonResponse = Response
          
          if isinstance(email, str):
              print(f"Project: {projectName} | Process: {Process} | DEEPSEEK_LLMresponse 완료")
          else:
              print(f"LifeGraphName: {projectName} | Process: {Process} | DEEPSEEK_LLMresponse 완료")
          
          if messagesReview == "on":
              LLMmessagesReview(Process, Input, Count, JsonResponse, Usage, Model, MAINLANG = mainLang, ROOT = root, MODE = Mode, INPUT2 = Input2, INPUTMEMORY = InputMemory, OUTPUTMEMORY = OutputMemory, MEMORYCOUNTER = MemoryNote, OUTPUTENDER = OutputEnder)

          ## Response Mode 전처리2: JsonParsing의 재구조화
          if ":" in JsonResponse and "{" in JsonResponse and "}" in JsonResponse:
              try:
                  TestResponse = json.loads(JsonResponse)
              except json.JSONDecodeError:
                  print(f"Project: {projectName} | Process: {Process} | DEEPSEEK_LLMresponse 파싱오류 | JsonParsingProcess 시작")
                  JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter, MainLang = mainLang, LLM = "GOOGLE")
                  try:
                      TestResponse = json.loads(JsonResponse)
                  except json.JSONDecodeError:
                      JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter, MainLang = mainLang, LLM = "OpenAI")

          return JsonResponse, Usage, Model
      
      except Exception as e:
          if isinstance(email, str):
            print(f"Project: {projectName} | Process: {Process} | DEEPSEEK_LLMresponse에서 오류 발생\n\n{e}")
          else:
            print(f"LifeGraphName: {projectName} | Process: {Process} | DEEPSEEK_LLMresponse에서 오류 발생\n\n{e}")
          time.sleep(random.uniform(5, 10))
          continue

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"
    FeedbackDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s112_FeedbackDataSet/"
    CompleteDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s113_CompleteDataSet/"
    TrainingDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s114_TrainingDataSet/"
    #########################################################################