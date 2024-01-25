import os
import json
import time
import random
import tiktoken
import openai
import sys
sys.path.append("/yaas")

from datetime import datetime
from openai import OpenAI
from backend.b1_Api.b13_Database import get_db
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import User, Prompt
from backend.b2_Solution.b21_General.b211_GetDBtable import GetPromptFrame, GetTrainingDataset
from backend.b2_Solution.b21_General.b212_PromptCommit import GetPromptDataPath, LoadJsonFrame
from extension.e1_Solution.e11_General.e111_GetDBtable import GetExtensionPromptFrame


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
        lLMapiKey = user.TTSapiKey
    
    return lLMapiKey


########################
##### LLM Response #####
########################
## 프롬프트 요청할 LLMmessages 메세지 구조 생성
def LLMmessages(Process, Input, Root = "backend", Output = "", mode = "Example", input2 = "", inputMemory = "", inputMemory2 = "", outputMemory = "", memoryCounter = "", outputEnder = ""):
    if Root == "backend":
      promptFrame = GetPromptFrame(Process)
    elif Root == "extension":
      promptFrame = GetExtensionPromptFrame(Process)
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
          "content": Example[1]["Request"][0]["Mark"] + Example[1]["Request"][0]["Message"] +
                    Example[1]["Request"][1]["Mark"] + Example[1]["Request"][1]["Message"] +
                    Example[1]["Request"][2]["Mark"] + Example[1]["Request"][2]["Message"] +
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
          "content": Memory[1]["Request"][0]["Mark"] + Memory[1]["Request"][0]["Message"] +
                    Memory[1]["Request"][1]["Mark"] + Memory[1]["Request"][1]["Message"] +
                    Memory[1]["Request"][2]["Mark"] + Memory[1]["Request"][2]["Message"] +
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
          "content": ExampleFineTuning[1]["Request"][0]["Mark"] + ExampleFineTuning[1]["Request"][0]["Message"] +
                    ExampleFineTuning[1]["Request"][1]["Mark"] + ExampleFineTuning[1]["Request"][1]["Message"] +
                    ExampleFineTuning[1]["Request"][2]["Mark"] + ExampleFineTuning[1]["Request"][2]["Message"] +
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
          "content": MemoryFineTuning[1]["Request"][0]["Mark"] + MemoryFineTuning[1]["Request"][0]["Message"] +
                    MemoryFineTuning[1]["Request"][1]["Mark"] + MemoryFineTuning[1]["Request"][1]["Message"] +
                    MemoryFineTuning[1]["Request"][2]["Mark"] + MemoryFineTuning[1]["Request"][2]["Message"] +
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
    OutputTokens = InputTokens * OutputTokensRatio
    totalTokens = messageTokens + OutputTokens
    Temperature = promptFrame[0]["Temperature"]
    
    return messages, totalTokens, Temperature
  
## 프롬프트에 메세지 확인
def LLMmessagesReview(Process, Input, Count, Response, Usage, Model, ROOT = "backend", MODE = "Example", INPUT2 = "", INPUTMEMORY = "", OUTPUTMEMORY = "", MEMORYCOUNTER = "", OUTPUTENDER = ""):

    Messages, TotalTokens, Temperature = LLMmessages(Process, Input, Root = ROOT, mode = MODE, input2 = INPUT2, inputMemory = INPUTMEMORY, outputMemory = OUTPUTMEMORY, memoryCounter = MEMORYCOUNTER, outputEnder = OUTPUTENDER)
    
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
def LLMresponse(projectName, email, Process, Input, Count, root = "backend", Mode = "Example", Input2 = "", InputMemory = "", OutputMemory = "", MemoryCounter = "", OutputEnder = "", MaxAttempts = 100, messagesReview = "off"):
    # client = OpenAI(api_key = LoadLLMapiKey(email))
    client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
    if root == "backend":
      promptFrame = GetPromptFrame(Process)
    elif root == "extension":
      promptFrame = GetExtensionPromptFrame(Process)
    
    Messages, TotalTokens, temperature = LLMmessages(Process, Input, Root = root, mode = Mode, input2 = Input2, inputMemory = InputMemory, outputMemory = OutputMemory, memoryCounter = MemoryCounter, outputEnder = OutputEnder)

    if Mode == "Master":
      Model = promptFrame[0]["MasterModel"]
    else:
      if TotalTokens < 14000:
        if Mode in ["Example", "Memory"]:
          Model = promptFrame[0]["BaseModel"]["ShortTokensModel"]
        if Mode == "ExampleFineTuning":
          if promptFrame[0]["ExampleFineTunedModel"]["ShortTokensModel"] != []:
            Model = promptFrame[0]["ExampleFineTunedModel"]["ShortTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["BaseModel"]["ShortTokensModel"]
        if Mode == "MemoryFineTuning":
          if promptFrame[0]["MemoryFineTunedModel"]["ShortTokensModel"] != []:
            Model = promptFrame[0]["MemoryFineTunedModel"]["ShortTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["BaseModel"]["ShortTokensModel"]

      else:
        if Mode in ["Example", "Memory"]:
          Model = promptFrame[0]["BaseModel"]["LongTokensModel"]
        if Mode == "ExampleFineTuning":
          if promptFrame[0]["ExampleFineTunedModel"]["LongTokensModel"] != []:
            Model = promptFrame[0]["ExampleFineTunedModel"]["LongTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["BaseModel"]["LongTokensModel"]
        if Mode == "MemoryFineTuning":
          if promptFrame[0]["MemoryFineTunedModel"]["LongTokensModel"] != []:
            Model = promptFrame[0]["MemoryFineTunedModel"]["LongTokensModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["BaseModel"]["LongTokensModel"]

    Temperature = temperature

    for _ in range(MaxAttempts):
      try:
          if promptFrame[0]["OutputFormat"] == 'json':
            response = client.chat.completions.create(
                model = Model,
                response_format = {"type": "json_object"},
                messages = Messages,
                temperature = Temperature)
          else:
            response = client.chat.completions.create(
                model = Model,
                messages = Messages,
                temperature = Temperature)
          Response = response.choices[0].message.content
          Usage = {'Input': response.usage.prompt_tokens,
                   'Output': response.usage.completion_tokens,
                   'Total': response.usage.total_tokens}
          
          if isinstance(email, str):
            print(f"Project: {projectName} | Process: {Process} | LLMresponse 완료")
          else:
            print(f"LifeGraphSetName: {projectName} | Process: {Process} | LLMresponse 완료")
          
          if messagesReview == "on":
            LLMmessagesReview(Process, Input, Count, Response, Usage, Model, ROOT = root, MODE = Mode, INPUTMEMORY = InputMemory, OUTPUTMEMORY = OutputMemory, MEMORYCOUNTER = MemoryCounter, OUTPUTENDER = OutputEnder)

          return Response, Usage, Model
      
      except Exception as e:
          if isinstance(email, str):
            print(f"Project: {projectName} | Process: {Process} | LLMresponse에서 오류 발생\n\n{e}")
          else:
            print(f"LifeGraphSetName: {projectName} | Process: {Process} | LLMresponse에서 오류 발생\n\n{e}")
          time.sleep(random.uniform(5, 10))
          continue
      # except openai.APIError as e:
      #     print(f"Project: {projectName} | Process: {Process} | LLMresponse에서 오류 발생: OpenAI API returned an API Error: {e}")
      #     time.sleep(random.uniform(5, 10))
      #     continue
      # except openai.APIConnectionError as e:
      #     print(f"Project: {projectName} | Process: {Process} | LLMresponse에서 오류 발생: Failed to connect to OpenAI API: {e}")
      #     time.sleep(random.uniform(5, 10))
      #     continue
      # except openai.RateLimitError as e:
      #     print(f"Project: {projectName} | Process: {Process} | LLMresponse에서 오류 발생: OpenAI API request exceeded rate limit: {e}")
      #     time.sleep(random.uniform(5, 10))
      #     continue
      # except openai.APIStatusError as e:
      #     print(f"Project: {projectName} | Process: {Process} | LLMresponse에서 오류 발생: API status error in LLMresponse: {e.status_code}, {e.response}")
      #     time.sleep(random.uniform(5, 10))
      #     continue


##########################
##### LLM FineTuning #####
##########################
## 파인튜닝 데이터셋 생성
def LLMTrainingDatasetGenerator(projectName, email, ProcessNumber, Process, TrainingDataSetPath, Mode = "Example"):  
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
      
      with open(newFilename, 'w', encoding='utf-8') as file:
        for i in range(len(IOList)):
          # "InputMemory"가 "None"일 경우 빈 텍스트("") 처리
          if IOList[i]["InputMemory"] == "None":
            InputMemory = ""
          else:
            InputMemory = IOList[i]["InputMemory"]
          Input = IOList[i]["Input"]
          output = IOList[i]["Feedback"]
          
          messages, totalTokens, Temperature = LLMmessages(Process, Input, Output = output, mode = MOde, inputMemory = InputMemory)
          
          TrainingData = {"messages": [messages[0], messages[1], messages[2]]}

          file.write(json.dumps(TrainingData, ensure_ascii = False) + '\n')
          
          TotalTokens += totalTokens
      
      return filename, open(newFilename, 'rb')
    else:
      print(f"Project: {projectName} | Process: {Process} | FeedbackCompletion에서 오류 발생: Feedback이 완료 되지 않았습니다.")
      return None, None
    
## 파인튜닝 파일 업로드 생성
def LLMTrainingDatasetUpload(projectName, email, ProcessNumber, Process, TrainingDataSetPath, mode = "Example", MaxAttempts = 100):
    client = OpenAI(api_key = LoadLLMapiKey(email))
    client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
    
    # LLMTrainingDataset 업로드
    filename, LLMTrainingDataset = LLMTrainingDatasetGenerator(projectName, email, ProcessNumber, Process, TrainingDataSetPath, Mode = mode)
    UploadedFile = client.files.create(
      file = LLMTrainingDataset,
      purpose = 'fine-tune'
    )
    time.sleep(random.randint(15, 20))
    
    for _ in range(MaxAttempts):
      uploadedFile = client.files.retrieve(UploadedFile.id)
      if uploadedFile.status == "processed":
        FileId = uploadedFile.id
        # 파일이름에 FileId 붙이기
        FilePath, oldFilename = os.path.split(filename)
        base, ext = os.path.splitext(oldFilename)
        newFilename = f"{base}_{FileId}{ext}"
        newFilePath = os.path.join(FilePath, newFilename)
        os.rename(filename, newFilePath)
        
        print(f"Project: {projectName} | Process: {Process} | LLMTrainingDatasetUpload 완료")
        break
      else:
        print(f"Project: {projectName} | Process: {Process} | LLMTrainingDatasetUploading ... 기다려주세요.")
        time.sleep(random.randint(10, 15))
        continue

    return newFilename, FileId

## 파인튜닝
def LLMFineTuning(projectName, email, ProcessNumber, Process, TrainingDataSetPath, ModelTokens = "Short", Mode = "Example", Epochs = 3, MaxAttempts = 100):
    with get_db() as db:
      client = OpenAI(api_key = LoadLLMapiKey(email))
      client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
      
      newFilename, FileId = LLMTrainingDatasetUpload(projectName, email, ProcessNumber, Process, TrainingDataSetPath, mode = Mode)

      # 토큰수별 모델 선정
      if ModelTokens == "Short":
        BaseModel = "gpt-3.5-turbo"
      elif ModelTokens == "Long":
        BaseModel = "gpt-3.5-turbo-16k"
      
      # FineTuning 요청
      FineTuningJob = client.fine_tuning.jobs.create(
        training_file = FileId,
        model = BaseModel,
        hyperparameters={"n_epochs":Epochs}
      )
      time.sleep(random.randint(60, 90))
      
      for _ in range(MaxAttempts):

        fineTuningJob = client.fine_tuning.jobs.retrieve(FineTuningJob.id)
        if fineTuningJob.status == "succeeded":
          FineTunedModel = fineTuningJob.fine_tuned_model
          TrainedTokens = fineTuningJob.trained_tokens
          TrainingFile = fineTuningJob.training_file
          print(f"Project: {projectName} | Process: {Process} | LLMFineTuning 완료")
          break
        else:
          print(f"Project: {projectName} | Process: {Process} | LLMFineTuning ... 기다려주세요.")
          time.sleep(random.randint(60, 90))
          continue
      
      prompt = db.query(Prompt).first()
      column = getattr(Prompt, Process, None)
      promptFrame = db.query(column).first()
      
      # Prompt 모델 업데이트
      fineTunedModelDic = {"Id" : Process + '-' + str(Date("Second")), "Model" :FineTunedModel}
      print(fineTunedModelDic)
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
      
    with open(newFilename, "a", encoding="utf-8") as file:
      jsonLine = json.dumps(fineTunedModelDic)
      file.write(jsonLine)
        
    # client.File.delete(TrainingFile)
    
    return FineTunedModel, TrainedTokens
    
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    userStoragePath = "/yaas/backend/b6_Storage/b62_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    FeedbackDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5122_FeedbackDataSet/"
    CompleteDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5123_CompleteDataSet/"
    TrainingDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5124_TrainingDataSet/"
    #########################################################################

    LLMFineTuning(projectName, email, "05", "CharacterCompletion", TrainingDataSetPath, ModelTokens = "Short", Mode = "Example", Epochs = 3)