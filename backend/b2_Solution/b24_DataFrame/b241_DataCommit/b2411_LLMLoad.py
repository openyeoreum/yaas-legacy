import os
import json
import time
import random
import openai
import tiktoken
import sys
sys.path.append("/yaas")

from datetime import datetime
from backend.b1_Api.b13_Database import get_db
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import User
from backend.b2_Solution.b23_Project.b231_GetDBtable import GetPromptFrame, GetTrainingDataset

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

## 프롬프트 요청할 LLMmessages 메세지 구조 생성
def LLMmessages(Process, Input, Output = "", mode = "Example", inputMemory = "", outputMemory = "", memoryCounter = "", outputEnder = ""):
    promptFrame = GetPromptFrame(Process)
    messageTime = "current time: " + str(Date("Second")) + '\n\n'
    if mode == "Example":
      Example = promptFrame[0]["Example"]
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
                    Example[1]["Request"][6]["Mark"] + Example[1]["Request"][6]["InputMark"] + str(Input)
        },
        {
          "role": Example[2]["Role"],
          "content": Example[2]["OutputMark"] + Example[2]["OutputStarter"]
        }
      ]
      
    elif mode == "Memory":
      Memory = promptFrame[0]["Memory"]
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
                    Memory[1]["Request"][5]["InputEnder"]
        },
        {
          "role": Memory[2]["Role"],
          "content": Memory[2]["OutputMark"] + memoryCounter +
                    Memory[2]["OutputStarter"] +
                    str(outputMemory) +
                    str(outputEnder)
        }
      ]
      
    elif mode == "Training":
      Example = promptFrame[0]["Example"]
      messages = [
        {
          "role": Example[0]["Role"],
          "content": Example[0]["Mark"] + Example[0]["Message"]
        },
        {
          "role": Example[1]["Role"],
          "content": Example[1]["Request"][0]["Mark"] + Example[1]["Request"][0]["Message"] +
                    Example[1]["Request"][1]["Mark"] + Example[1]["Request"][1]["Message"] +
                    Example[1]["Request"][2]["Mark"] + Example[1]["Request"][2]["Message"] +
                    Example[1]["Request"][6]["Mark"] + Example[1]["Request"][6]["InputMark"] + str(Input)
        },
        {
          "role": Example[2]["Role"],
          "content": Example[2]["OutputMark"] + Example[2]["OutputStarter"] + str(Output)
        }
      ]
    
    encoding = tiktoken.get_encoding("cl100k_base")
    # print(f'messages: {messages}')
    InputTokens = len(encoding.encode(Input))
    messageTokens = len(encoding.encode(str(messages)))
    OutputTokensRatio = promptFrame[0]["OutputTokensRatio"]
    OutputTokens = InputTokens * OutputTokensRatio
    totalTokens = messageTokens + OutputTokens
    Temperature = promptFrame[0]["Temperature"]
    
    return messages, totalTokens, Temperature
  
## 프롬프트에 메세지 확인
def LLMmessagesReview(Process, Input, Count, Response, Usage, Model, MODE = "Example", INPUTMEMORY = "", OUTPUTMEMORY = "", MEMORYCOUNTER = "", OUTPUTENDER = ""):

    Messages, TotalTokens, Temperature = LLMmessages(Process, Input, mode = MODE, inputMemory = INPUTMEMORY, outputMemory = OUTPUTMEMORY, memoryCounter = MEMORYCOUNTER, outputEnder = OUTPUTENDER)
    
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
def LLMresponse(projectName, email, Process, Input, Count, Mode = "Example", InputMemory = "", OutputMemory = "", MemoryCounter = "", OutputEnder = "", MaxAttempts = 100, messagesReview = "off"):
    openai.api_key = LoadLLMapiKey(email)
    openai.api_key = os.getenv("OPENAI_API_KEY")
    promptFrame = GetPromptFrame(Process)
    
    Messages, TotalTokens, temperature = LLMmessages(Process, Input, mode = Mode, inputMemory = InputMemory, outputMemory = OutputMemory, memoryCounter = MemoryCounter, outputEnder = OutputEnder)
    
    if TotalTokens < 4500:
      if promptFrame[0]["ExampleFineTunedModel"] != []:
        if Mode == "Example":
          Model = promptFrame[0]["ExampleFineTunedModel"][-1]["Model"]
        elif Mode == "Memory":
          if promptFrame[0]["MemoryFineTunedModel"] != []:
            Model = promptFrame[0]["MemoryFineTunedModel"][-1]["Model"]
          else:
            Model = promptFrame[0]["ShortTokensModel"]
      else:
        Model = promptFrame[0]["ShortTokensModel"]
    else:
      Model = promptFrame[0]["LongTokensModel"]
    Temperature = temperature
    
    for _ in range(MaxAttempts):
      try:
          response = openai.ChatCompletion.create(
              model = Model,
              messages = Messages,
              temperature = Temperature)
          Response = response["choices"][0]["message"]["content"]
          Usage = response["usage"]
          print(f"Project: {projectName} | Process: {Process} | LLMresponse 완료")
          
          if messagesReview == "on":
            LLMmessagesReview(Process, Input, Count, Response, Usage, Model, MODE = Mode, INPUTMEMORY = InputMemory, OUTPUTMEMORY = OutputMemory, MEMORYCOUNTER = MemoryCounter, OUTPUTENDER = OutputEnder)

          return Response, Usage, Model
      
      except openai.error.OpenAIError as e:
          print(f"Project: {projectName} | Process: {Process} | LLMresponse에서 오류 발생: {e}")
          continue
        
## 파인튜닝 데이터셋 생성
def LLMTrainingDatasetGenerator(projectName, email, Process, DataSetPath, processDataset):
    ###                                                                   ^^^^^^^^^^^^^^ 테스트 후 삭제 ###   
    trainingDataset = GetTrainingDataset(projectName, email)
    ProcessDataset = getattr(trainingDataset, Process)

    filename = DataSetPath + Process + 'DataSet_Training_' + Date() + '.jsonl'
    
    base, ext = os.path.splitext(filename)
    counter = 0
    Newfilename = filename
    while os.path.exists(Newfilename):
        counter += 1
        Newfilename = f"{base}({counter}) {ext}"
    
    ProcessDataset = processDataset ### < --- 테스트 후 삭제 ###
    
    IOList = ProcessDataset["FeedbackDataset"][1:]
    TotalTokens = 0
    
    with open(Newfilename, 'w', encoding='utf-8') as file:
      for i in range(len(IOList)):
        Input = IOList[i]["Input"]
        output = IOList[i]["Feedback"]
        
        messages, totalTokens = LLMmessages(Process, Input, Output = output, mode = "Training")
        
        TrainingData = {"messages": [messages[0], messages[1], messages[2]]}

        file.write(json.dumps(TrainingData, ensure_ascii=False) + '\n')
        
        TotalTokens += totalTokens
    
    return open(Newfilename, 'rb')
    
## 파인튜닝 파일 업로드 생성
def LLMTrainingDatasetUpload(projectName, email, Process, DataSetPath, processDataset, MaxAttempts = 100):
    ###                                                                ^^^^^^^^^^^^^^ 테스트 후 삭제 ###  
    openai.api_key = LoadLLMapiKey(email)
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # LLMTrainingDataset 업로드
    LLMTrainingDataset = LLMTrainingDatasetGenerator(projectName, email, Process, DataSetPath, processDataset)
    ###                                                                                        ^^^^^^^^^^^^^^ 테스트 후 삭제 ###  
    UploadedFile = openai.File.create(
      file = LLMTrainingDataset,
      purpose = 'fine-tune'
    )
    time.sleep(random.randint(10, 15))
    
    for _ in range(MaxAttempts):
      if UploadedFile["status"] != "uploaded":
        print(f"Project: {projectName} | Process: {Process} | LLMTrainingDatasetUploading ... 기다려주세요.")
        time.sleep(random.randint(10, 15))
        continue
      else:
        FileId = UploadedFile["id"]
        print(f"Project: {projectName} | Process: {Process} | LLMTrainingDatasetUpload 완료")
        
    return FileId

## 파인튜닝
def LLMFineTuning(projectName, email, Process, DataSetPath, processDataset, Model = "gpt-3.5-turbo", Epochs = 3, MaxAttempts = 100):
    ###                                                                              ^^^^^^^^^^^^^^ 테스트 후 삭제 ###
    with get_db() as db:
        openai.api_key = LoadLLMapiKey(email)
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        FileId = LLMTrainingDatasetUpload(projectName, email, Process, DataSetPath, processDataset)
      
        FineTuningJob = openai.FineTuningJob.create(
          training_file = FileId,
          model = Model,
          hyperparameters={"n_epochs":Epochs}
        )
        time.sleep(random.randint(60, 90))
        
        for _ in range(MaxAttempts):
          if FineTuningJob["status"] != "succeeded":
            print(f"Project: {projectName} | Process: {Process} | LLMFineTuning ... 기다려주세요.")
            time.sleep(random.randint(60, 90))
            continue
          else:
            FineTuninedModel = FineTuningJob["fine_tuned_model"]
            TrainedTokens = FineTuningJob["trained_tokens"]
            TrainingFile = FineTuningJob["training_file"]
            print(f"Project: {projectName} | Process: {Process} | LLMFineTuning 완료")
            
        promptFrame = GetPromptFrame(Process)
        promptFrame[0]['ExampleFineTunedModel'].append({"Id" : Process + '-' + str(Date("Second")), "Model" :FineTuninedModel})
        
        flag_modified(promptFrame, Process)
        
        db.add(promptFrame)
        db.commit()
        
    # openai.File.delete(TrainingFile)
    
    return FineTuninedModel, TrainedTokens
    
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    process = 'IndexDefinePreprocess'
    DataFramePath = "/yaas/backend/b5_Database/b50_DatabaseTest/b53_ProjectDataTest/"
    DataSetPath = "/yaas/backend/b5_Database/b50_DatabaseTest/b55_TrainingDataTest/"
    #########################################################################

    # with open(DataSetPath + "yeoreum00128@gmail.com_우리는행복을진단한다_04_BodyCharacterDefineDataSet_231022.json", 'r', encoding='utf-8') as file:
    #     processDataset = json.load(file)
    
    # FineTuninedModel, TrainedTokens = LLMFineTuning(projectName, email, process, DataSetPath, processDataset)
    
    # print(FineTuninedModel, TrainedTokens)
        
    # LLMFineTuning(projectName, email, process, DataSetPath, processDataset)
    # FileId = "file-7IcoiyDE9P4pf6CZx5nHemX1"
    # Model = "gpt-3.5-turbo"
    # Epochs = 4
    # LLMFineTuning(FileId, Model, Epochs)  
    
    # completion = openai.ChatCompletion.create(
    #   model="ft:gpt-3.5-turbo-0613:yeoreum::8CTTEzmS",
    #   messages=[
    #     {"role": "user", "content": "안녕 GPT!"}
    #   ]
    # )
    
    promptFrame = GetPromptFrame(process)
    print(promptFrame[0]['ExampleFineTunedModel'])