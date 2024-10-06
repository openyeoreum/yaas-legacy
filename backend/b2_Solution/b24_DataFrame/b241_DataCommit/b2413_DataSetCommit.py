import os
import re
import unicodedata
import json
import sys
sys.path.append("/yaas")

from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import TrainingDataset
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetTrainingDataset


#########################################################
##### 전체 TrainingDataSet의 MetaData(식별)부분을 업데이트 #####
#########################################################
def AddDataSetMetaDataToDB(projectName, email):
    with get_db() as db:
        trainingDataset = GetTrainingDataset(projectName, email)

        if not trainingDataset:
            print("TrainingDataset not found!")
            return
        
        for column in TrainingDataset.__table__.columns:
            if isinstance(column.type, JSON):
                ProcessData = getattr(trainingDataset, column.name)
                if ProcessData is None:
                    continue
                ProcessData["UserId"] = trainingDataset.UserId
                ProcessData["ProjectsStorageID"] = trainingDataset.ProjectsStorageId
                ProcessData["ProjectId"] = trainingDataset.ProjectId
                ProcessData["ProjectName"] = trainingDataset.ProjectName
                setattr(trainingDataset, column.name, ProcessData)
                flag_modified(trainingDataset, column.name)

        db.add(trainingDataset)
        db.commit()


###########################
##### General Process #####
###########################
## 1. 1-1 IndexFrame이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedDataSetToDB(projectName, email, Process, ExistedDataSet):
    with get_db() as db:
    
        trainingDataset = GetTrainingDataset(projectName, email)
        ProcessDataset = getattr(trainingDataset, Process)
        ProcessDataset["TaskName"] = ExistedDataSet["TaskName"]
        ProcessDataset["UserId"] = ExistedDataSet["UserId"]
        ProcessDataset["ProjectsStorageID"] = ExistedDataSet["ProjectsStorageID"]
        ProcessDataset["ProjectId"] = ExistedDataSet["ProjectId"]
        ProcessDataset["ProjectName"] = ExistedDataSet["ProjectName"]
        ProcessDataset["RawDataSetCount"] = ExistedDataSet["RawDataSetCount"]
        ProcessDataset["FeedbackDatasetCount"] = ExistedDataSet["FeedbackDatasetCount"]
        ProcessDataset["EmbeddingDatasetCount"] = ExistedDataSet["EmbeddingDatasetCount"]
        ProcessDataset["Completion"] = ExistedDataSet["Completion"]
        ProcessDataset["Accuracy"] = ExistedDataSet["Accuracy"]
        ProcessDataset["Context"] = ExistedDataSet["Context"]
        ProcessDataset["RawDataset"] = ExistedDataSet["RawDataset"]
        
        flag_modified(trainingDataset, Process)
        
        db.add(trainingDataset)
        db.commit()
        
## 1. 1-1 UpdateProjectContext 업데이트 형식
def UpdateProjectContext(ProcessDataset, Process, Language = "None", Genre = "None", Gender = "None", Age = "None", Personality = "None", Emotion = "None", Environment = "None", Situation = "None", Era = "None", Culture = "None"):
    
    updateContext = {
        "Language": Language,
        "Genre": Genre,
        "Gender": Gender,
        "Age": Age,
        "Personality": Personality,
        "Emotion": Emotion,
        "Environment": Environment,
        "Situation": Situation,
        "Era": Era,
        "Culture": Culture
    }
    
    ProcessDataset["TaskName"] = Process
    ProcessDataset["Context"].update(updateContext)
    ProcessDataset["FeedbackCompletion"] = "No"
    
## 1. 1-2 ProjectContext 부분 업데이트
def AddProjectContextToDB(projectName, email, Process, language = "None", genre = "None", gender = "None", age = "None", personality = "None", emotion = "None", environment = "None", situation = "None", era = "None", culture = "None"):
    with get_db() as db:
    
        trainingDataset = GetTrainingDataset(projectName, email)
        ProcessDataset = getattr(trainingDataset, Process)
        UpdateProjectContext(ProcessDataset, Process, Language = language, Genre = genre, Gender = gender, Age = age, Personality = personality, Emotion = emotion, Environment = environment, Situation = situation, Era = era, Culture = culture)
        
        flag_modified(trainingDataset, Process)
        
        db.add(trainingDataset)
        db.commit()
        
## 1. 1-3 UpdateProjectRawDataset 업데이트 형식
def UpdateProjectRawDataset(ProcessDataset, Mode, Model, Usage, Input, Output, InputMemory = "None"):
    DataSetId = len(ProcessDataset["RawDataset"])
    updateRawDataset = {
        "DataSetId": DataSetId,
        "Mode": Mode,
        "TrainingModel": Model,
        "Tokens": Usage,
        "InputMemory": InputMemory,
        "Input": Input,
        "Output": Output
    }
    
    ProcessDataset["RawDataset"].append(updateRawDataset)
    ProcessDataset["RawDataSetCount"] = DataSetId
    
## 1. 1-4 ProjectRawDataset 부분 업데이트
def AddProjectRawDatasetToDB(projectName, email, Process, Mode, Model, Usage, Input, Output, INPUTMEMORY = "None"):
    with get_db() as db:
    
        trainingDataset = GetTrainingDataset(projectName, email)
        ProcessDataset = getattr(trainingDataset, Process)
        UpdateProjectRawDataset(ProcessDataset, Mode, Model, Usage, Input, Output, InputMemory = INPUTMEMORY)
        
        flag_modified(trainingDataset, Process)
        
        db.add(trainingDataset)
        db.commit()
        
## 1. 1-5 UpdateProjectFeedbackDataSets 업데이트 형식
def UpdateProjectFeedbackDataSets(ProcessDataset, Input, Output, InputMemory = "None"):
    DataSetId = len(ProcessDataset["FeedbackDataset"])
    updateFeedbackDataset = {
        "DataSetId": DataSetId,
        "InputMemory": InputMemory,
        "Input": Input,
        "Feedback": Output,
        "Check": "No",
        "Accuracy": "None"
    }
    
    ProcessDataset["FeedbackDataset"].append(updateFeedbackDataset)
    ProcessDataset["FeedbackDatasetCount"] = DataSetId
    
## 1. 1-6 ProjectFeedbackDataSets 부분 업데이트
def AddProjectFeedbackDataSetsToDB(projectName, email, Process, Input, Output, INPUTMEMORY = "None"):
    with get_db() as db:
    
        trainingDataset = GetTrainingDataset(projectName, email)
        ProcessDataset = getattr(trainingDataset, Process)
        UpdateProjectFeedbackDataSets(ProcessDataset, Input, Output, InputMemory = INPUTMEMORY)
        
        flag_modified(trainingDataset, Process)
        
        db.add(trainingDataset)
        db.commit()
        
## 1. 1-7 UpdateProjectEmbeddingDataSets 업데이트 형식
def UpdateProjectEmbeddingDataSets(ProcessDataset, InputEmbedding, OutputEmbedding, InputMemoryEmbedding = "None"):
    DataSetId = len(ProcessDataset["EmbeddingDataset"])
    updateFeedbackDataset = {
        "DataSetId": DataSetId,
        "InputMemoryEmbedding": InputMemoryEmbedding,
        "InputEmbedding": InputEmbedding,
        "OutputEmbedding": OutputEmbedding,
    }
    
    ProcessDataset["EmbeddingDataset"].append(updateFeedbackDataset)
    ProcessDataset["EmbeddingDatasetCount"] = DataSetId
    
## 1. 1-8 UpdateProjectEmbeddingDataSets 부분 업데이트
def AddProjectEmbeddingDataSetsToDB(projectName, email, Process, InputEmbedding, OutputEmbedding, inputMemoryEmbedding = "None"):
    with get_db() as db:
    
        trainingDataset = GetTrainingDataset(projectName, email)
        ProcessDataset = getattr(trainingDataset, Process)
        UpdateProjectEmbeddingDataSets(ProcessDataset, InputEmbedding, OutputEmbedding, InputMemoryEmbedding = inputMemoryEmbedding)
        
        flag_modified(trainingDataset, Process)
        
        db.add(trainingDataset)
        db.commit()
    
## 1. DataSetCount 가져오기
def DataSetCountLoad(projectName, email, Process):

    trainingDataset = GetTrainingDataset(projectName, email)
    ProcessDataset = getattr(trainingDataset, Process)
    RawDataSetCount = ProcessDataset["RawDataSetCount"]
    FeedbackDatasetCount = ProcessDataset["FeedbackDatasetCount"]
    EmbeddingDatasetCount = ProcessDataset["EmbeddingDatasetCount"]
    Completion = ProcessDataset["Completion"]
    
    return RawDataSetCount, FeedbackDatasetCount, EmbeddingDatasetCount, Completion

## 1. DataSet 초기화
def InitRawDataSet(projectName, email, Process):
    with get_db() as db:
    
        trainingDataset = GetTrainingDataset(projectName, email)
        ProcessDataset = getattr(trainingDataset, Process)
        ProcessDataset["RawDataSetCount"] = 0
        ProcessDataset["FeedbackDatasetCount"] = 0
        ProcessDataset["EmbeddingDatasetCount"] = 0
        ProcessDataset["Completion"] = "No"
        ProcessDataset["Accuracy"] = {}
        ProcessDataset["Context"] = {
            "Language": "Ko",
            "Genre": "None",
            "Gender": "None",
            "Age": "None",
            "Personality": "None",
            "Emotion": "None",
            "Environment": "None",
            "Situation": "None",
            "Era": "None",
            "Culture": "None"
            }
        ProcessDataset["RawDataset"] = [
            {
                "DataSetId": 0,
                "Mode": "None",
                "TrainingModel": "None",
                "Tokens": "None",
                "InputMemory": "None",
                "Input": "None",
                "Output": "None"
            }
        ]
        ProcessDataset["FeedbackDataset"] = [
            {
                "DataSetId": 0,
                "InputMemory": "None",
                "Input": "None",
                "Feedback": "None",
                "Check": "No",
                "Accuracy": "None"
            }
        ]
        ProcessDataset["FeedbackCompletion"] = "No"
        ProcessDataset["EmbeddingDataset"] = [
            {
                "DataSetId": 0,
                "InputMemoryEmbedding": "None",
                "InputEmbedding": "None",
                "OutputEmbedding": "None"
            }
        ]
        flag_modified(trainingDataset, Process)
        
        db.add(trainingDataset)
        db.commit()
        
## 1. 업데이트된 DataSet 출력
def UpdatedDataSet(projectName, email, Process):
    with get_db() as db:
        trainingDataset = GetTrainingDataset(projectName, email)
        ProcessDataset = getattr(trainingDataset, Process)

    return ProcessDataset

## 1. DataSetCompletion 업데이트
def DataSetCompletionUpdate(projectName, email, Process):
    with get_db() as db:
        trainingDataset = GetTrainingDataset(projectName, email)
        ProcessDataset = getattr(trainingDataset, Process)
        ProcessDataset["Completion"] = "Yes"

        flag_modified(trainingDataset, Process)

        db.add(trainingDataset)
        db.commit()
        
## 1. 업데이트된 DataSet 파일저장
def SaveDataSet(projectName, email, ProcessNumber, Process, RawDataSetPath):
    with get_db() as db:
        trainingDataset = GetTrainingDataset(projectName, email)
        ProcessDataset = getattr(trainingDataset, Process)
    # 현재 날짜 및 시간을 가져옵니다.
    now = datetime.now()
    date = now.strftime('%y%m%d')
    filename = RawDataSetPath + email + '_' + projectName + '_' + str(ProcessNumber) + '_' + str(Process) + 'DataSet_' + date + '.json'
    
    base, ext = os.path.splitext(filename)
    counter = 0
    Newfilename = filename
    while os.path.exists(Newfilename):
        counter += 1
        Newfilename = f"{base} ({counter}){ext}"
    with open(Newfilename, 'w', encoding='utf-8') as f:
        json.dump(ProcessDataset, f, ensure_ascii = False, indent = 4)


#########################################
### 2. 피드백 데이터셋 Accuracy 측정 및 저장 ###
#########################################
## 2. 2-1 피드백 데이터셋 불러오기
def LoadExistedDataSets(projectName, email, Process, FeedbackDataSetPath):
    # 문자열 정규화
    EmailNormalized = unicodedata.normalize('NFC', email)
    ProjectNameNormalized = unicodedata.normalize('NFC', projectName)
    ProcessNormalized = unicodedata.normalize('NFC', Process)
    
    # 정규 표현식으로 파일명에서 생성날짜와 프로세스 이름 추출
    patternSTR = rf"{re.escape(EmailNormalized)}_{re.escape(ProjectNameNormalized)}_\d+(-\d+)?_{re.escape(ProcessNormalized)}DataSet_(\d+).json"
    pattern = re.compile(patternSTR)
    
    MaxDate = 0
    RecentFile = None

    ## NFC, NFD 오류 문제 해결 (모두 적용)
    if os.path.exists(unicodedata.normalize('NFC', FeedbackDataSetPath)):
        FeedbackDataSetPath = unicodedata.normalize('NFC', FeedbackDataSetPath)
    elif os.path.exists(unicodedata.normalize('NFD', FeedbackDataSetPath)):
        FeedbackDataSetPath = unicodedata.normalize('NFD', FeedbackDataSetPath)

    for FileName in os.listdir(FeedbackDataSetPath):
        FileNameNormalized = unicodedata.normalize('NFC', FileName)
        match = pattern.match(FileNameNormalized)       
        if match:
            date = int(match.group(2))
            if date > MaxDate:
                MaxDate = date
                RecentFile = FileName

    if RecentFile:
        FullPath = os.path.join(FeedbackDataSetPath, RecentFile)
        with open(FullPath, 'r', encoding='utf-8') as file:
            ExistedDataSet = json.load(file)
            # print(RecentFile)
            return RecentFile, ExistedDataSet

    return None, None

## 2. 2-2 피드백 데이터셋 Accuracy 측정
def SimpleAccuracy(Output, Feedback):
    matched = 0
    total = len(Output)
    for i in range(total):
        if Output[i] == Feedback[i]:
            matched += 1
    return matched / total

def ElementsAccuracy(Output, Feedback):
    matched = 0
    total = 0
    for i in range(len(Output)):
        for key in Output[i]:
            total += len(Output[i][key])
            matched += sum(1 for k, v in Output[i][key].items() if Feedback[i][key].get(k) == v)
    return matched / total

def OutputAccuracy(ExistedDataSet):

    RawDataset = ExistedDataSet["RawDataset"][1:]
    FeedbackDataset = ExistedDataSet["FeedbackDataset"]
    
    TotalSimpleAccuracy = 0
    TotalElementsAccuracy = 0
    
    for i in range(len(RawDataset)):
        Output = RawDataset[i]["Output"]
        Feedback = FeedbackDataset[i+1]["Feedback"]
        
        simpleAccuracy = SimpleAccuracy(Output, Feedback)
        elementsAccuracy = ElementsAccuracy(Output, Feedback)
        
        TotalSimpleAccuracy += simpleAccuracy
        TotalElementsAccuracy += elementsAccuracy
        
        FeedbackDataset[i+1]["Accuracy"] = {"Simple": simpleAccuracy, "Elements": elementsAccuracy}
    
    AverageSimpleAccuracy = TotalSimpleAccuracy / len(RawDataset)
    AverageElementsAccuracy = TotalElementsAccuracy / len(RawDataset)
    ExistedDataSet["Accuracy"] = {"Simple": AverageSimpleAccuracy, "Elements": AverageElementsAccuracy}
                
    return ExistedDataSet

## 2. 2-3 피드백 데이터셋 저장하기
def SaveFeedbackDataSet(projectName, Process, RecentFile, AccuracyDataSet, FeedbackDataSetPath, CompleteDataSetPath):
    # 기존 파일 경로
    OldFilePath = os.path.join(FeedbackDataSetPath, RecentFile)
    # 새로운 경로 및 파일명 생성
    NewFileName = RecentFile.replace('.json', '_Complete.json')
    NewFilePath = os.path.join(CompleteDataSetPath, NewFileName)
    
    # 기존 파일 삭제
    if os.path.exists(OldFilePath):
        os.remove(OldFilePath)
    
    # 새로운 파일에 AccuracyDataSet 저장
    with open(NewFilePath, 'w', encoding = 'utf-8') as NewFile:
        json.dump(AccuracyDataSet, NewFile, ensure_ascii = False, indent = 4)
        
    print(f"Project: {projectName} | Process: {Process} | AddProjectFeedbackDataSets 완료, SaveFeedbackDataSet: {NewFilePath}")

## 2. 2-4 피드백 데이터셋 업데이트
def AddProjectFeedbackDataSets(projectName, email, Process, FeedbackDataSetPath, CompleteDataSetPath):
    RecentFile, ExistedDataSet = LoadExistedDataSets(projectName, email, Process, FeedbackDataSetPath)
    if ExistedDataSet:
        if ExistedDataSet["FeedbackCompletion"] == "Yes":
            AccuracyDataSet = OutputAccuracy(ExistedDataSet)
            with get_db() as db:
                trainingDataset = GetTrainingDataset(projectName, email)
                ProcessDataset = getattr(trainingDataset, Process)
                ProcessDataset["Accuracy"] = AccuracyDataSet["Accuracy"]
                ProcessDataset["FeedbackDataset"] = AccuracyDataSet["FeedbackDataset"]
                ProcessDataset["FeedbackCompletion"] = "Yes"
                
                flag_modified(trainingDataset, Process)

                db.add(trainingDataset)
                db.commit()
                
            SaveFeedbackDataSet(projectName, Process, RecentFile, AccuracyDataSet, FeedbackDataSetPath, CompleteDataSetPath)
        else:
            print(f"Project: {projectName} | Process: {Process} | FeedbackCompletion에서 오류 발생: Feedback이 완료 되지 않았습니다.")
    else:
        print(f"Project: {projectName} | Process: {Process} | LoadExistedDataSets에서 오류 발생: ExistedDataSets이 존재 하지 않습니다.")
        
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    process = 'CharacterDefine'
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    FeedbackDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s112_FeedbackDataSet/"
    CompleteDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s113_CompleteDataSet/"
    TrainingDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s114_TrainingDataSet/"
    #########################################################################