import os
import re
import json
import time
import tiktoken
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetPromptFrame
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2412_DataFrameCommit import FindDataframeFilePaths, AddExistedIndexFrameToDB, AddIndexFrameBodyToDB, IndexFrameCountLoad, InitIndexFrame, IndexFrameCompletionUpdate
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddExistedDataSetToDB, AddProjectContextToDB, AddProjectRawDatasetToDB, AddProjectFeedbackDataSetsToDB

# IndexText 로드
def LoadIndexText(projectName, email):
    # 경로 설정
    TextDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/yeoreum_user/yeoreum_storage/{projectName}/{projectName}_script_file"
    RawIndexTextFilePath = TextDirPath + f'/{projectName}_Index(Raw).txt'
    RawBodyTextFilePath = TextDirPath + f'/{projectName}_Body(Raw).txt'
    
    
    project = GetProject(projectName, email)
    indexText = project.IndexText
    if indexText is None:
      ## [ Script Generation 프로세스 ] 인 경우 ##
      if os.path.exists(RawIndexTextFilePath) and os.path.exists(RawBodyTextFilePath):
        sys.exit(f"\n\n[ ((({projectName}_Index(Raw).txt))), ((({projectName}_Body(Raw).txt))) 파일을 완성한뒤 파일이름 뒤에  -> (Raw) <- 를 제거해 주세요. ]\n({TextDirPath})\n\n1. 타이틀과 로그 부분을 작성\n2. 추가로 필요한 내용 작성\n3. 낭독이 바뀌는 부분에 \"...\" 쌍따옴표 처리\n\n4. 목차(_Index)파일과 본문(_Body) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n5. 본문(_Body)파일 내 쌍따옴표(“대화문”의 완성) 개수 일치 * _Body(검수용) 파일 확인\n6. 캡션 등의 줄바꿈 및 캡션이 아닌 일반 문장은 마지막 온점(.)처리\n\n7. {projectName}_Index(Raw).txt, {projectName}_Body(Raw).txt 파일명에 -> (Raw) <- 를 제거\n\n")
      ## [ General Script 프로세스 ] 인 경우 ##
      else:
        sys.exit(f"\n\n[ ((({projectName}_Index.txt))), ((({projectName}_Body.txt))) 파일을 완성하여 아래 경로에 복사해주세요. ]\n({TextDirPath})\n\n1. 목차(_Index)파일과 본문(_Body) 파일의 목차 일치, 목차에는 온점(.)이 들어갈 수 없으며, 하나의 목차는 줄바꿈이 일어나면 안됨\n2. 본문(_Body)파일 내 쌍따옴표(“대화문”의 완성) 개수 일치 * _Body(검수용) 파일 확인\n\n")
    else:
      _IndexText = indexText.replace('.', '_')
      _IndexText = _IndexText.replace('!', '_')
      _IndexText = _IndexText.replace('?', '_')
      _IndexText = _IndexText.replace("'", '|').replace('’', '|').replace('‘', '|')
      _IndexText = _IndexText.replace('"', '|').replace('“', '|').replace('”', '|')
      _IndexText = _IndexText.replace('/', '&')
    
    return _IndexText

# IndexPreprocess 프롬프트 요청 및 결과물 Text화
def IndexDefinePreprocess(projectName, email, Process = "IndexDefinePreprocess", MaxRetries = 100, mode = "Example", indexMode = "Define", MESSAGESREVIEW = "off"):
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)
    Input = LoadIndexText(projectName, email)

    if indexMode == "Preprocess":
      TotalCount = 0
      ProcessCount = TotalCount + 1
      
      while TotalCount < MaxRetries:
        
        Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, Input, TotalCount + 1, Mode = mode, messagesReview = MESSAGESREVIEW)

        cleanInput = re.sub("[^가-힣]", "", Input)
        cleanResponse = re.sub("[^가-힣]", "", Response)
          
        if cleanInput == cleanResponse:
          print(f"Project: {projectName} | Process: {Process} | CleanTextMatching 완료")

          # DataSets 업데이트
          AddProjectRawDatasetToDB(projectName, email, Process, mode, Model, Usage, Input, Response)
          AddProjectFeedbackDataSetsToDB(projectName, email, Process, Input, Response)

          return Response
        else:
          print(f"Project: {projectName} | Process: {Process} | CleanTextMatching에서 오류 발생: InputTokens({len(cleanInput)}), OutputTokens({len(cleanResponse)})")
          TotalCount += 1

      print(f"Project: {projectName} | Process: {Process}에서 오류 발생: 최대 재시도 횟수를 초과하였습니다.")

    elif indexMode == "Define":
      return Input

# IndexDefine 프롬프트 요청 및 결과물 Json화
def IndexDefineProcess(projectName, email, Process = "IndexDefine", Input = None, MaxRetries = 100, IndexMode = "Define", Mode = "Example", MessagesReview = "off"):
    if Input == None:
      Input = IndexDefinePreprocess(projectName, email, mode = Mode, indexMode = IndexMode, MESSAGESREVIEW = MessagesReview)
    Input = Input.replace("'", "")
    Input = Input.replace('"', '')
    
    # DataSetsContext 업데이트
    AddProjectContextToDB(projectName, email, Process)
    
    TotalCount = 0
    
    while TotalCount < MaxRetries:
      
      Response, Usage, Model = OpenAI_LLMresponse(projectName, email, Process, Input, TotalCount + 1, Mode = Mode, messagesReview = MessagesReview)

      cleanInput = re.sub("[^가-힣]", "", Input)
      cleanResponse = re.sub("[^가-힣]", "", Response)
      # print("\n\n1. Response: {}\n\n2. cleanResponse: {}\n\n3. cleanIndexText: {}\n\n".format(Response, cleanResponse, cleanIndexText))
      # print(Response)
      if cleanInput == cleanResponse:
        print(f"Project: {projectName} | Process: {Process} | CleanTextMatching 완료")
        
        Response = Response.replace("<태그된 목차4.json>", "")
        # Response = Response.replace("[{'Title':'", "").replace("[{'Title': '", "")
        # Response = Response.replace('[{"Title":"', '').replace('[{"Title": "', '')
        # Response = Response.replace('"{"Title": ', '')
        Response = Response.replace('```json', '')
        Response = Response.replace('```', '')
        Response = re.sub(r'^"', '', Response)
        Response = re.sub(r"^'", '', Response)
        
        promptFrame = GetPromptFrame(Process)
        Example = promptFrame[0]["Example"]
        responseData = Example[2]["OutputStarter"] + Response
        responseData = responseData.replace("'", "\"")
        try:
            responseContent = json.loads(responseData)
        except json.JSONDecodeError:
            # JSON 형식이 아닐 때의 예외 처리
            print(f"Project: {projectName} | Process: {Process} | JSONDecode에서 오류 발생: JSONDecodeError")
            TotalCount += 1
            continue

        responseUsage = [{"Response":{
            "Model": Model,
            "InputTokens": Usage["Input"],
            "OutputTokens": Usage["Output"]}}
        ]
        responseJson = responseUsage + responseContent
        print(f"Project: {projectName} | Process: {Process} | JSONDecode 완료")

        # DataSets 업데이트
        AddProjectRawDatasetToDB(projectName, email, Process, Mode, Model, Usage, Input, responseJson)
        AddProjectFeedbackDataSetsToDB(projectName, email, Process, Input, responseJson)

        return responseJson

      else:
        print(f"Project: {projectName} | Process: {Process} | CleanTextMatching에서 오류 발생: InputTokens({len(cleanInput)}), OutputTokens({len(cleanResponse)})")
        TotalCount += 1

# IndexDefine 프롬프트 요청 및 결과물이 긴 경우 나누어 처리
def IndexDefineDivision(projectName, email, maxTokens = 4000, mode = "Example", indexMode = "Define", messagesReview = "off"):
    indexText = LoadIndexText(projectName, email)
    encoding = tiktoken.get_encoding("cl100k_base")
    indexTokens = len(encoding.encode(indexText))
    
    # indexTokens이 maxTokens을 넘으면 분할작업 시작
    if indexTokens >= maxTokens:
      print(f"--- IndexDefineDivision 모드, 토큰수: {indexTokens} ---")
      # preprocessedIndexText를 둘다 앞부분에 Title을 붙혀서 2개로 분할
      preprocessedIndexText = IndexDefinePreprocess(projectName, email, mode = mode, MESSAGESREVIEW = messagesReview)
      # print(f"{type(preprocessedIndexText)}\npreprocessedIndexText: {preprocessedIndexText}")
      sections = preprocessedIndexText.split('\n\n')
      totalTokens = sum(len(section.split()) for section in sections)
      halfTokens = totalTokens / 2
      
      accumulatedTokens = 0
      splitIndex = 0
      for i, section in enumerate(sections):
        accumulatedTokens += len(section.split())
        if accumulatedTokens >= halfTokens:
          splitIndex = i
          break
        
      firstIndexText = '\n\n'.join(sections[:splitIndex+1])
      firstIndexTextTitle = firstIndexText.split("\n")[0]
      # print(f"firstIndexText: {firstIndexText}")
      secondIndexText = firstIndexTextTitle + "\n\n" + '\n\n'.join(sections[splitIndex+1:])
      # print(f"secondIndexText: {secondIndexText}")
      
      # 분할된 InputText를 바탕으로 IndexDefineProcess프로세스를 분할하여 2번 실행
      print("--- FirstIndexDefineProcess 시작 ---")
      FirstIndexDefineProcess = IndexDefineProcess(projectName, email, Input = firstIndexText, Mode = mode, IndexMode = indexMode, MessagesReview = messagesReview)
      print("--- FirstIndexDefineProcess 완료 ---")
      print("--- SecondIndexDefineProcess 시작 ---")
      SecondIndexDefineProcess = IndexDefineProcess(projectName, email, Input = secondIndexText, Mode = mode, IndexMode = indexMode, MessagesReview = messagesReview)
      print("--- SecondIndexDefineProcess 완료 ---")
      
      # 분할된 출력의 결합 (SecondIndexDefineProcess의 경우 타이틀 제거)
      combineResponseJson = FirstIndexDefineProcess[1:] + SecondIndexDefineProcess[2:]
      # print(f"combineResponseJson: {combineResponseJson}\n\n")
      print("--- IndexDefineDivision 완료 ---")
      
      return combineResponseJson
    
    else:
      responseJson = IndexDefineProcess(projectName, email, Mode = mode, IndexMode = indexMode, MessagesReview = messagesReview)[1:]
      
      return responseJson

# 프롬프트 요청 및 결과물 Json을 IndexFrame에 업데이트
def IndexFrameUpdate(projectName, email, MessagesReview = "off", Mode = "Example", IndexMode = "Define", ExistedDataFrame = None, ExistedDataSet1 = None, ExistedDataSet2 = None):
    print(f"< User: {email} | Project: {projectName} | 01_IndexFrameUpdate 시작 >")
    # IndexFrame의 Count값 가져오기
    IndexCount, Completion = IndexFrameCountLoad(projectName, email)
    if Completion == "No":
      
        if ExistedDataFrame != None:
          # 이전 작업이 존재할 경우 가져온 뒤 업데이트
          AddExistedIndexFrameToDB(projectName, email, ExistedDataFrame)
          AddExistedDataSetToDB(projectName, email, "IndexDefinePreprocess", ExistedDataSet1)
          AddExistedDataSetToDB(projectName, email, "IndexDefine", ExistedDataSet2)
          print(f"[ User: {email} | Project: {projectName} | 01_IndexFrameUpdate은 ExistedIndexFrame으로 대처됨 ]\n")
        else:
          responseJson = IndexDefineDivision(projectName, email, mode = Mode, indexMode = IndexMode, messagesReview = MessagesReview)
          
          # ResponseJson을 IndexCount로 슬라이스
          ResponseJson = responseJson[IndexCount:]
          ResponseJsonCount = len(ResponseJson)
          
          IndexId = IndexCount
          
          # TQDM 셋팅
          UpdateTQDM = tqdm(ResponseJson,
                            total = ResponseJsonCount,
                            desc = 'IndexFrameUpdate')
          # i값 수동 생성
          i = 0
          for Update in UpdateTQDM:
              UpdateTQDM.set_description(f'IndexFrameUpdate: {Update}')
              time.sleep(0.0001)
              IndexId += 1
              IndexTag = list(ResponseJson[i].keys())[0]
              Index = ResponseJson[i][IndexTag]

              AddIndexFrameBodyToDB(projectName, email, IndexId, IndexTag, Index)
              # i값 수동 업데이트
              i += 1
              
          UpdateTQDM.close()
          # Completion "Yes" 업데이트
          IndexFrameCompletionUpdate(projectName, email)
          print(f"[ User: {email} | Project: {projectName} | 01_IndexFrameUpdate 완료 ]\n")
    
    else:
        print(f"[ User: {email} | Project: {projectName} | 01_IndexFrameUpdate은 이미 완료됨 ]\n")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################