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
from agent.a1_Connector.a12_Database import get_db
from sqlalchemy.orm.attributes import flag_modified
from agent.a1_Connector.a13_Models import User, Prompt
from agent.a2_Solution.a21_General.a212_GetDBtable import GetPromptFrame, GetTrainingDataset
from agent.a2_Solution.a21_General.a213_PromptCommit import GetPromptDataPath, LoadJsonFrame


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

## LLM API key 로드
def LoadLLMapiKey(email):
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()
        lLMapiKey = user.LLMapiKey
    
    return lLMapiKey


################################
################################
########## OpenAI API ##########
################################
################################


###############################
##### OpenAI LLM Response #####
###############################
## 프롬프트 요청할 LLMmessages 메세지 구조 생성
def LLMmessages(Process, Input, Model, Root = "agent", promptFramePath = "", Output = "", mode = "Example", input2 = "", inputMemory = "", inputMemory2 = "", outputMemory = "", memoryCounter = "", outputEnder = ""):
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
      promptFrame = GetPromptFrame(Process)
    else:
      with open(promptFramePath, 'r', encoding = 'utf-8') as promptFrameJson:
        promptFrame = [json.load(promptFrameJson)]

    messageTime = "current time: " + str(Date("Second")) + '\n\n'
    
    # messages
    if mode in ["Example", "ExampleFineTuning", "Master"]:
      if mode == "Example":
        Example = promptFrame[0]["Example"]
      elif mode in ["ExampleFineTuning", "Master"]:
        Example = promptFrame[0]["ExampleFineTuning"]

      messages = [
        {
          "role": Example[0]["Role"],
          "content": messageTime + Example[0]["Mark"] + Example[0]["Message"]
        },
        {
          "role": Example[1]["Role"],
          "content": Example[1]["Request"][0]["Mark"] + ConvertQuotes(Model, Example[1]["Request"][0]["Message"]) +
                    Example[1]["Request"][1]["Mark"] + ConvertQuotes(Model, Example[1]["Request"][1]["Message"]) +
                    Example[1]["Request"][2]["Mark"] + ConvertQuotes(Model, Example[1]["Request"][2]["Message"]) +
                    Example[1]["Request"][3]["Mark"] + Example[1]["Request"][3]["InputExampleMark"] + str(Example[1]["Request"][3]["InputExample"]) +
                    Example[1]["Request"][3]["OutputExampleMark"] + str(Example[1]["Request"][3]["OutputExample"]) +
                    Example[1]["Request"][4]["Mark"] + Example[1]["Request"][4]["InputExampleMark"] + str(Example[1]["Request"][4]["InputExample"]) +
                    Example[1]["Request"][4]["OutputExampleMark"] + str(Example[1]["Request"][4]["OutputExample"]) +
                    Example[1]["Request"][5]["Mark"] + Example[1]["Request"][5]["InputExampleMark"] + str(Example[1]["Request"][5]["InputExample"]) +
                    Example[1]["Request"][5]["OutputExampleMark"] + str(Example[1]["Request"][5]["OutputExample"]) +
                    Example[1]["Request"][6]["Mark"] + Example[1]["Request"][6]["InputMark"] + str(Input) + Example[1]["Request"][6]["InputMark2"] + str(input2)
        },
        {
          "role": Example[2]["Role"],
          "content": Example[2]["OutputMark"] + 
                    memoryCounter + 
                    Example[2]["OutputStarter"]
        }
      ]
      
    elif mode in ["Memory", "MemoryFineTuning"]:
      if mode == "Memory":
        Memory = promptFrame[0]["Memory"]
      elif mode == "MemoryFineTuning":
        Memory = promptFrame[0]["MemoryFineTuning"]
        
      messages = [
        {
          "role": Memory[0]["Role"],
          "content": messageTime + Memory[0]["Mark"] + Memory[0]["Message"]
        },
        {
          "role": Memory[1]["Role"],
          "content": Memory[1]["Request"][0]["Mark"] + ConvertQuotes(Model, Memory[1]["Request"][0]["Message"]) +
                    Memory[1]["Request"][1]["Mark"] + ConvertQuotes(Model, Memory[1]["Request"][1]["Message"]) +
                    Memory[1]["Request"][2]["Mark"] + ConvertQuotes(Model, Memory[1]["Request"][2]["Message"]) +
                    Memory[1]["Request"][3]["Mark"] + Memory[1]["Request"][3]["InputExampleMark"] + Memory[1]["Request"][3]["InputExample"] +
                    Memory[1]["Request"][3]["OutputExampleMark"] + Memory[1]["Request"][3]["OutputExample"] +
                    Memory[1]["Request"][4]["Mark"] + Memory[1]["Request"][4]["InputExampleMark"] + Memory[1]["Request"][4]["InputExample"] +
                    Memory[1]["Request"][4]["OutputExampleMark"] + Memory[1]["Request"][4]["OutputExample"] +
                    Memory[1]["Request"][5]["Mark"] + Memory[1]["Request"][5]["InputMark"] +
                    Memory[1]["Request"][5]["InputStarter"] +
                    str(inputMemory) +
                    Memory[1]["Request"][5]["InputEnder"] + Memory[1]["Request"][5]["InputMark2"] + str(inputMemory2)
        },
        {
          "role": Memory[2]["Role"],
          "content": Memory[2]["OutputMark"] + memoryCounter +
                    Memory[2]["OutputStarter"] +
                    str(outputMemory) +
                    str(outputEnder)
        }
      ]
    
    # Training
    elif mode == "ExampleTraining":
      ExampleFineTuning = promptFrame[0]["ExampleFineTuning"]
      messages = [
        {
          "role": ExampleFineTuning[0]["Role"],
          "content": ExampleFineTuning[0]["Mark"] + ExampleFineTuning[0]["Message"]
        },
        {
          "role": ExampleFineTuning[1]["Role"],
          "content": ExampleFineTuning[1]["Request"][0]["Mark"] + ConvertQuotes(Model, ExampleFineTuning[1]["Request"][0]["Message"]) +
                    ExampleFineTuning[1]["Request"][1]["Mark"] + ConvertQuotes(Model, ExampleFineTuning[1]["Request"][1]["Message"]) +
                    ExampleFineTuning[1]["Request"][2]["Mark"] + ConvertQuotes(Model, ExampleFineTuning[1]["Request"][2]["Message"]) +
                    ExampleFineTuning[1]["Request"][6]["Mark"] + ExampleFineTuning[1]["Request"][6]["InputMark"] + str(Input) +
                    ExampleFineTuning[1]["Request"][6]["InputMark2"] + str(input2)
        },
        {
          "role": ExampleFineTuning[2]["Role"],
          "content": ExampleFineTuning[2]["OutputMark"] + ExampleFineTuning[2]["OutputStarter"] + str(Output)
        }
      ]
      
    elif mode == "MemoryTraining":
      MemoryFineTuning = promptFrame[0]["MemoryFineTuning"]
      messages = [
        {
          "role": MemoryFineTuning[0]["Role"],
          "content": MemoryFineTuning[0]["Mark"] + MemoryFineTuning[0]["Message"]
        },
        {
          "role": MemoryFineTuning[1]["Role"],
          "content": MemoryFineTuning[1]["Request"][0]["Mark"] + ConvertQuotes(Model, MemoryFineTuning[1]["Request"][0]["Message"]) +
                    MemoryFineTuning[1]["Request"][1]["Mark"] + ConvertQuotes(Model, MemoryFineTuning[1]["Request"][1]["Message"]) +
                    MemoryFineTuning[1]["Request"][2]["Mark"] + ConvertQuotes(Model, MemoryFineTuning[1]["Request"][2]["Message"]) +
                    MemoryFineTuning[1]["Request"][5]["Mark"] + MemoryFineTuning[1]["Request"][5]["InputMark"] + str(inputMemory) + str(Input) +
                    MemoryFineTuning[1]["Request"][5]["InputMark2"] + str(inputMemory2) + str(input2)
        },
        {
          "role": MemoryFineTuning[2]["Role"],
          "content": MemoryFineTuning[2]["OutputMark"] + MemoryFineTuning[2]["OutputStarter"] + str(Output)
        }
      ]

    encoding = tiktoken.get_encoding("cl100k_base")
    # print(f'messages: {messages}')
    InputTokens = len(encoding.encode(str(Input)))
    messageTokens = len(encoding.encode(str(messages)))
    OutputTokensRatio = promptFrame[0]["OutputTokensRatio"]
    outputTokens = InputTokens * OutputTokensRatio
    totalTokens = messageTokens + outputTokens
    Temperature = promptFrame[0]["Temperature"]

    return messages, outputTokens, totalTokens, Temperature
  
## 프롬프트에 메세지 확인
def LLMmessagesReview(Process, Input, Count, Response, Usage, Model, ROOT = "agent", PromptFramePath = "", MODE = "Example", INPUT2 = "", INPUTMEMORY = "", OUTPUTMEMORY = "", MEMORYCOUNTER = "", OUTPUTENDER = ""):

    Messages, outputTokens, TotalTokens, Temperature = LLMmessages(Process, Input, Model, Root = ROOT, promptFramePath = PromptFramePath, mode = MODE, input2 = INPUT2, inputMemory = INPUTMEMORY, outputMemory = OUTPUTMEMORY, memoryCounter = MEMORYCOUNTER, outputEnder = OUTPUTENDER)
    
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
def OpenAI_LLMresponse(projectName, email, Process, Input, Count, root = "agent", PromptFramePath = "", Mode = "Example", Input2 = "", InputMemory = "", OutputMemory = "", MemoryCounter = "", OutputEnder = "", MaxAttempts = 100, messagesReview = "off"):
    # OpenAIClient = OpenAI(api_key = LoadLLMapiKey(email))
    OpenAIClient = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
    if PromptFramePath == "":
      promptFrame = GetPromptFrame(Process)
    else:
      with open(PromptFramePath, 'r', encoding = 'utf-8') as promptFrameJson:
        promptFrame = [json.load(promptFrameJson)]

    Messages, outputTokens, TotalTokens, temperature = LLMmessages(Process, Input, 'gpt', Root = root, promptFramePath = PromptFramePath, mode = Mode, input2 = Input2, inputMemory = InputMemory, outputMemory = OutputMemory, memoryCounter = MemoryCounter, outputEnder = OutputEnder)

    if Mode == "Master":
      Model = promptFrame[0]["OpenAI"]["MasterModel"]
    else:
      if TotalTokens < 20000:
        if Mode in ["Example", "Memory"]:
          Model = promptFrame[0]["OpenAI"]["BaseModel"]["ShortTokensModel"]
        if Mode == "ExampleFineTuning":
          if promptFrame[0]["OpenAI"]["ExampleFineTunedModel"]["ShortTokensModel"] != []:
            Model = promptFrame[0]["OpenAI"]["ExampleFineTunedModel"]["ShortTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["OpenAI"]["BaseModel"]["ShortTokensModel"]
        if Mode == "MemoryFineTuning":
          if promptFrame[0]["OpenAI"]["MemoryFineTunedModel"]["ShortTokensModel"] != []:
            Model = promptFrame[0]["OpenAI"]["MemoryFineTunedModel"]["ShortTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["OpenAI"]["BaseModel"]["ShortTokensModel"]

      else:
        if Mode in ["Example", "Memory"]:
          Model = promptFrame[0]["OpenAI"]["BaseModel"]["LongTokensModel"]
        if Mode == "ExampleFineTuning":
          if promptFrame[0]["OpenAI"]["ExampleFineTunedModel"]["LongTokensModel"] != []:
            Model = promptFrame[0]["OpenAI"]["ExampleFineTunedModel"]["LongTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["OpenAI"]["BaseModel"]["LongTokensModel"]
        if Mode == "MemoryFineTuning":
          if promptFrame[0]["OpenAI"]["MemoryFineTunedModel"]["LongTokensModel"] != []:
            Model = promptFrame[0]["OpenAI"]["MemoryFineTunedModel"]["LongTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["OpenAI"]["BaseModel"]["LongTokensModel"]

    Temperature = temperature
    ReasoningEffort = promptFrame[0]["OpenAI"]["ReasoningEffort"]

    for _ in range(MaxAttempts):
      try:
          if promptFrame[0]["OutputFormat"] == 'json':
            if Model in ['o4-mini', 'o3']:
              response = OpenAIClient.chat.completions.create(
                  model = Model,
                  reasoning_effort = ReasoningEffort,
                  response_format = {"type": "json_object"},
                  messages = Messages)
            else:
              response = OpenAIClient.chat.completions.create(
                  model = Model,
                  response_format = {"type": "json_object"},
                  messages = Messages,
                  temperature = Temperature)
          else:
            if Model in ['o4-mini', 'o3']:
              response = OpenAIClient.chat.completions.create(
                  model = Model,
                  reasoning_effort = ReasoningEffort,
                  messages = Messages)
            else:
              response = OpenAIClient.chat.completions.create(
                  model = Model,
                  messages = Messages,
                  temperature = Temperature)
          Response = response.choices[0].message.content
          Usage = {'Input': response.usage.prompt_tokens,
                   'Output': response.usage.completion_tokens,
                   'Total': response.usage.total_tokens}
          
          if isinstance(email, str):
            print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMresponse 완료")
          else:
            print(f"LifeGraphName: {projectName} | Process: {Process} | OpenAI_LLMresponse 완료")
          
          if messagesReview == "on":
            LLMmessagesReview(Process, Input, Count, Response, Usage, Model, ROOT = root, PromptFramePath = PromptFramePath, MODE = Mode, INPUT2 = Input2, INPUTMEMORY = InputMemory, OUTPUTMEMORY = OutputMemory, MEMORYCOUNTER = MemoryCounter, OUTPUTENDER = OutputEnder)

          return Response, Usage, Model
      
      except Exception as e:
          if isinstance(email, str):
            print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMresponse에서 오류 발생\n\n{e}")
          else:
            print(f"LifeGraphName: {projectName} | Process: {Process} | OpenAI_LLMresponse에서 오류 발생\n\n{e}")
          time.sleep(random.uniform(5, 10))
          continue
      # except openai.APIError as e:
      #     print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMresponse에서 오류 발생: OpenAI API returned an API Error: {e}")
      #     time.sleep(random.uniform(5, 10))
      #     continue
      # except openai.APIConnectionError as e:
      #     print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMresponse에서 오류 발생: Failed to connect to OpenAI API: {e}")
      #     time.sleep(random.uniform(5, 10))
      #     continue
      # except openai.RateLimitError as e:
      #     print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMresponse에서 오류 발생: OpenAI API request exceeded rate limit: {e}")
      #     time.sleep(random.uniform(5, 10))
      #     continue
      # except openai.APIStatusError as e:
      #     print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMresponse에서 오류 발생: API status error in OpenAI_LLMresponse: {e.status_code}, {e.response}")
      #     time.sleep(random.uniform(5, 10))
      #     continue


#################################
##### OpenAI LLM FineTuning #####
#################################
## 파인튜닝 데이터셋 생성
def OpenAI_LLMTrainingDatasetGenerator(projectName, email, ProcessNumber, Process, TrainingDataSetPath, Mode = "Example"):  
    trainingDataset = GetTrainingDataset(projectName, email)
    ProcessDataset = getattr(trainingDataset, Process)

    filename = TrainingDataSetPath + email + '_' + projectName + '_' + ProcessNumber + '_' + Process + 'DataSet_' + str(Date()) + '.jsonl'
    
    base, ext = os.path.splitext(filename)
    counter = 0
    newFilename = filename
    while os.path.exists(newFilename):
        counter += 1
        newFilename = f"{base} ({counter}){ext}"
    
    if ProcessDataset["FeedbackCompletion"] == "Yes":
      if Mode == "Example":
        MOde = "ExampleTraining"
      elif Mode == "Memory":
        MOde = "MemoryTraining"
      IOList = ProcessDataset["FeedbackDataset"][1:]
      TotalTokens = 0
      
      with open(newFilename, 'w', encoding = 'utf-8') as file:
        for i in range(len(IOList)):
          # "InputMemory"가 "None"일 경우 빈 텍스트("") 처리
          if IOList[i]["InputMemory"] == "None":
            InputMemory = ""
          else:
            InputMemory = IOList[i]["InputMemory"]
          Input = IOList[i]["Input"]
          output = IOList[i]["Feedback"]
          
          messages, outputTokens, totalTokens, Temperature = LLMmessages(Process, Input, 'gpt', Output = output, mode = MOde, inputMemory = InputMemory)
          
          TrainingData = {"messages": [messages[0], messages[1], messages[2]]}

          file.write(json.dumps(TrainingData, ensure_ascii = False) + '\n')
          
          TotalTokens += totalTokens
      
      return filename, open(newFilename, 'rb')
    else:
      print(f"Project: {projectName} | Process: {Process} | FeedbackCompletion에서 오류 발생: Feedback이 완료 되지 않았습니다.")
      return None, None
    
## 파인튜닝 파일 업로드 생성
def OpenAI_LLMTrainingDatasetUpload(projectName, email, ProcessNumber, Process, TrainingDataSetPath, mode = "Example", MaxAttempts = 100):
    OpenAIClient = OpenAI(api_key = LoadLLMapiKey(email))
    OpenAIClient = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
    
    # LLMTrainingDataset 업로드
    filename, LLMTrainingDataset = OpenAI_LLMTrainingDatasetGenerator(projectName, email, ProcessNumber, Process, TrainingDataSetPath, Mode = mode)
    UploadedFile = OpenAIClient.files.create(
      file = LLMTrainingDataset,
      purpose = 'fine-tune'
    )
    time.sleep(random.randint(15, 20))
    
    for _ in range(MaxAttempts):
      uploadedFile = OpenAIClient.files.retrieve(UploadedFile.id)
      if uploadedFile.status == "processed":
        FileId = uploadedFile.id
        # 파일이름에 FileId 붙이기
        FilePath, oldFilename = os.path.split(filename)
        base, ext = os.path.splitext(oldFilename)
        newFilename = f"{base}_{FileId}{ext}"
        newFilePath = os.path.join(FilePath, newFilename)
        os.rename(filename, newFilePath)
        
        print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMTrainingDatasetUpload 완료")
        break
      else:
        print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMTrainingDatasetUploading ... 기다려주세요.")
        time.sleep(random.randint(10, 15))
        continue

    return newFilename, FileId

## 파인튜닝
def OpenAI_LLMFineTuning(projectName, email, ProcessNumber, Process, TrainingDataSetPath, ModelTokens = "Short", Mode = "Example", Epochs = 3, MaxAttempts = 100):
    with get_db() as db:
      OpenAIClient = OpenAI(api_key = LoadLLMapiKey(email))
      OpenAIClient = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
      
      newFilename, FileId = OpenAI_LLMTrainingDatasetUpload(projectName, email, ProcessNumber, Process, TrainingDataSetPath, mode = Mode)

      # 토큰수별 모델 선정
      if ModelTokens == "Short":
        BaseModel = "gpt-4.1-mini"
      elif ModelTokens == "Long":
        BaseModel = "gpt-4.1-mini"
      
      # FineTuning 요청
      FineTuningJob = OpenAIClient.fine_tuning.jobs.create(
        training_file = FileId,
        model = BaseModel,
        hyperparameters={"n_epochs":Epochs}
      )
      time.sleep(random.randint(60, 90))
      
      for _ in range(MaxAttempts):

        fineTuningJob = OpenAIClient.fine_tuning.jobs.retrieve(FineTuningJob.id)
        if fineTuningJob.status == "succeeded":
          FineTunedModel = fineTuningJob.fine_tuned_model
          TrainedTokens = fineTuningJob.trained_tokens
          TrainingFile = fineTuningJob.training_file
          print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMFineTuning 완료")
          break
        else:
          print(f"Project: {projectName} | Process: {Process} | OpenAI_LLMFineTuning ... 기다려주세요.")
          time.sleep(random.randint(60, 90))
          continue
      
      prompt = db.query(Prompt).first()
      column = getattr(Prompt, Process, None)
      promptFrame = db.query(column).first()
      
      # Prompt 모델 업데이트
      fineTunedModelDic = {"Id" : Process + '-' + str(Date("Second")), "Model" :FineTunedModel}
      if Mode == "Example":
        if ModelTokens == "Short":
          promptFrame[0]['ExampleFineTunedModel']['ShortTokensModel'].append(fineTunedModelDic)
        elif ModelTokens == "Long":
          promptFrame[0]['ExampleFineTunedModel']['LongTokensModel'].append(fineTunedModelDic)
          
      elif Mode == "Memory":
        if ModelTokens == "Short":
          promptFrame[0]['MemoryFineTunedModel']['ShortTokensModel'].append(fineTunedModelDic)
        elif ModelTokens == "Long":
          promptFrame[0]['MemoryFineTunedModel']['LongTokensModel'].append(fineTunedModelDic)

      flag_modified(prompt, Process)
      
      db.merge(prompt)
      db.commit()
      
    with open(newFilename, "a", encoding = "utf-8") as file:
      jsonLine = json.dumps(fineTunedModelDic)
      file.write(jsonLine)
        
    # OpenAIClient.File.delete(TrainingFile)
    
    return FineTunedModel, TrainedTokens


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
def JsonParsingProcess(projectName, email, RawResponse, FilterFunc, LLM = "GOOGLE"):
    Process = "JsonParsing"
    ErrorCount = 1
    while True:
        if LLM == "GOOGLE":
            Response, Usage, Model = GOOGLE_LLMresponse(projectName, email, Process, RawResponse, ErrorCount, Mode = "Master", messagesReview = "off")
        if LLM == "OpenAI":
            Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, RawResponse, ErrorCount, Mode = "Master", messagesReview = "off")
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
def ANTHROPIC_LLMresponse(projectName, email, Process, Input, Count, root = "agent", PromptFramePath = "", Mode = "Example", Input2 = "", InputMemory = "", OutputMemory = "", MemoryCounter = "", OutputEnder = "", MaxAttempts = 100, messagesReview = "off"):

    AnthropicAIClient = anthropic.Anthropic(api_key = os.getenv("ANTHROPIC_API_KEY"))
    if PromptFramePath == "":
      promptFrame = GetPromptFrame(Process)
    else:
      with open(PromptFramePath, 'r', encoding = 'utf-8') as promptFrameJson:
        promptFrame = [json.load(promptFrameJson)]

    
    Messages, outputTokens, TotalTokens, temperature = LLMmessages(Process, Input, 'claude', Root = root, promptFramePath = PromptFramePath, mode = Mode, input2 = Input2, inputMemory = InputMemory, outputMemory = OutputMemory, memoryCounter = MemoryCounter, outputEnder = OutputEnder)

    if Mode == "Master":
      Model = promptFrame[0]["ANTHROPIC"]["MasterModel"]
    else:
      if TotalTokens < 14000:
        if Mode in ["Example", "Memory"]:
          Model = promptFrame[0]["ANTHROPIC"]["BaseModel"]["ShortTokensModel"]
        if Mode == "ExampleFineTuning":
          if promptFrame[0]["OpenAI"]["ExampleFineTunedModel"]["ShortTokensModel"] != []:
            Model = promptFrame[0]["ANTHROPIC"]["ExampleFineTunedModel"]["ShortTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["ANTHROPIC"]["BaseModel"]["ShortTokensModel"]
        if Mode == "MemoryFineTuning":
          if promptFrame[0]["OpenAI"]["MemoryFineTunedModel"]["ShortTokensModel"] != []:
            Model = promptFrame[0]["ANTHROPIC"]["MemoryFineTunedModel"]["ShortTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["ANTHROPIC"]["BaseModel"]["ShortTokensModel"]

      else:
        if Mode in ["Example", "Memory"]:
          Model = promptFrame[0]["ANTHROPIC"]["BaseModel"]["LongTokensModel"]
        if Mode == "ExampleFineTuning":
          if promptFrame[0]["OpenAI"]["ExampleFineTunedModel"]["LongTokensModel"] != []:
            Model = promptFrame[0]["ANTHROPIC"]["ExampleFineTunedModel"]["LongTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["ANTHROPIC"]["BaseModel"]["LongTokensModel"]
        if Mode == "MemoryFineTuning":
          if promptFrame[0]["OpenAI"]["MemoryFineTunedModel"]["LongTokensModel"] != []:
            Model = promptFrame[0]["ANTHROPIC"]["MemoryFineTunedModel"]["LongTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["ANTHROPIC"]["BaseModel"]["LongTokensModel"]
    
    for _ in range(MaxAttempts):
      try:
          if promptFrame[0]["OutputFormat"] == 'json':
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
          if promptFrame[0]["OutputFormat"] == 'json':
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
              LLMmessagesReview(Process, Input, Count, JsonResponse, Usage, Model, ROOT = root, MODE = Mode, INPUT2 = Input2, INPUTMEMORY = InputMemory, OUTPUTMEMORY = OutputMemory, MEMORYCOUNTER = MemoryCounter, OUTPUTENDER = OutputEnder)

          ## Response Mode 전처리2: JsonParsing의 재구조화
          if ":" in JsonResponse and "{" in JsonResponse and "}" in JsonResponse:
              try:
                  TestResponse = json.loads(JsonResponse)
              except json.JSONDecodeError:
                  print(f"Project: {projectName} | Process: {Process} | ANTHROPIC_LLMresponse 파싱오류 | JsonParsingProcess 시작")
                  JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter)
                  try:
                      TestResponse = json.loads(JsonResponse)
                  except json.JSONDecodeError:
                      JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter, LLM = "OpenAI")

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
def GOOGLE_LLMresponse(projectName, email, Process, Input, Count, root = "agent", PromptFramePath = "", Mode = "Example", Input2 = "", InputMemory = "", OutputMemory = "", MemoryCounter = "", OutputEnder = "", MaxAttempts = 100, messagesReview = "off"):

    GoogleAIClient = genai.Client(api_key= os.getenv("GEMINI_API_KEY"), http_options={'api_version':'v1alpha'})
    if PromptFramePath == "":
      promptFrame = GetPromptFrame(Process)
    else:
      with open(PromptFramePath, 'r', encoding = 'utf-8') as promptFrameJson:
        promptFrame = [json.load(promptFrameJson)]

    Messages, outputTokens, TotalTokens, temperature = LLMmessages(Process, Input, 'claude', Root = root, promptFramePath = PromptFramePath, mode = Mode, input2 = Input2, inputMemory = InputMemory, outputMemory = OutputMemory, memoryCounter = MemoryCounter, outputEnder = OutputEnder)

    Model = promptFrame[0]["GOOGLE"]["MasterModel"]
    
    for _ in range(MaxAttempts):
      try:
          Response = ''
          if promptFrame[0]["OutputFormat"] == 'json':
            for responseChunk in GoogleAIClient.models.generate_content_stream(
                model = Model,
                contents = [
                  types.Content(
                    role = "user",
                    parts = [types.Part.from_text(text = f"{Messages[0]['content']}\n\n{Messages[1]['content']}\n\n{Messages[2]['content']}\n\nAssistant: ```json"),],
                    ),
                ],
                config = types.GenerateContentConfig(response_mime_type = "application/json",)
            ):
              Response += responseChunk.text
          else:
            for responseChunk in GoogleAIClient.models.generate_content_stream(
                model = Model,
                contents = [
                  types.Content(
                    role = "user",
                    parts = [types.Part.from_text(text = f"{Messages[0]['content']}\n\n{Messages[1]['content']}\n\n{Messages[2]['content']}\n\nAssistant: ```json"),],
                    ),
                ],
                config = types.GenerateContentConfig(response_mime_type = "text/plain",)
            ):
              Response += responseChunk.text
          Usage = {'Input': responseChunk.usage_metadata.prompt_token_count,
                    'Output': responseChunk.usage_metadata.candidates_token_count,
                    'Total': responseChunk.usage_metadata.total_token_count}
          # Response Mode 전처리1: ([...]와 {...}중 하나로 전처리)
          if promptFrame[0]["OutputFormat"] == 'json':
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
              LLMmessagesReview(Process, Input, Count, JsonResponse, Usage, Model, ROOT = root, MODE = Mode, INPUT2 = Input2, INPUTMEMORY = InputMemory, OUTPUTMEMORY = OutputMemory, MEMORYCOUNTER = MemoryCounter, OUTPUTENDER = OutputEnder)

          ## Response Mode 전처리2: JsonParsing의 재구조화
          if ":" in JsonResponse and "{" in JsonResponse and "}" in JsonResponse:
              try:
                  TestResponse = json.loads(JsonResponse)
              except json.JSONDecodeError:
                  print(f"Project: {projectName} | Process: {Process} | GOOGLE_LLMresponse 파싱오류 | JsonParsingProcess 시작")
                  JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter)
                  try:
                      TestResponse = json.loads(JsonResponse)
                  except json.JSONDecodeError:
                      JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter, LLM = "OpenAI")

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
def DEEPSEEK_LLMresponse(projectName, email, Process, Input, Count, root = "agent", PromptFramePath = "", Mode = "Example", Input2 = "", InputMemory = "", OutputMemory = "", MemoryCounter = "", OutputEnder = "", MaxAttempts = 100, messagesReview = "off"):
    DeepSeekClient = OpenAI(api_key = os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
    if PromptFramePath == "":
      promptFrame = GetPromptFrame(Process)
    else:
      with open(PromptFramePath, 'r', encoding = 'utf-8') as promptFrameJson:
        promptFrame = [json.load(promptFrameJson)]

    Messages, outputTokens, TotalTokens, temperature = LLMmessages(Process, Input, 'claude', Root = root, promptFramePath = PromptFramePath, mode = Mode, input2 = Input2, inputMemory = InputMemory, outputMemory = OutputMemory, memoryCounter = MemoryCounter, outputEnder = OutputEnder)

    Model = promptFrame[0]["DEEPSEEK"]["MasterModel"]
    
    for _ in range(MaxAttempts):
      try:
          if promptFrame[0]["OutputFormat"] == 'json':
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
          if promptFrame[0]["OutputFormat"] == 'json':
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
              LLMmessagesReview(Process, Input, Count, JsonResponse, Usage, Model, ROOT = root, MODE = Mode, INPUT2 = Input2, INPUTMEMORY = InputMemory, OUTPUTMEMORY = OutputMemory, MEMORYCOUNTER = MemoryCounter, OUTPUTENDER = OutputEnder)

          ## Response Mode 전처리2: JsonParsing의 재구조화
          if ":" in JsonResponse and "{" in JsonResponse and "}" in JsonResponse:
              try:
                  TestResponse = json.loads(JsonResponse)
              except json.JSONDecodeError:
                  print(f"Project: {projectName} | Process: {Process} | DEEPSEEK_LLMresponse 파싱오류 | JsonParsingProcess 시작")
                  JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter)
                  try:
                      TestResponse = json.loads(JsonResponse)
                  except json.JSONDecodeError:
                      JsonResponse = JsonParsingProcess(projectName, email, JsonResponse, JsonParsingFilter, LLM = "OpenAI")

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