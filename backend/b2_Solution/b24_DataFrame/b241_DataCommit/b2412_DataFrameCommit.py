import os
import re
import json
import unicodedata
import sys
sys.path.append("/yaas")

from datetime import datetime
from backend.b1_Api.b14_Models import User
from backend.b1_Api.b13_Database import get_db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import Project
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject
from backend.b2_Solution.b23_Project.b231_ProjectCommit import GetProjectDataPath, LoadJsonFrame


############################################
########## DataFrameCommitGeneral ##########
############################################

## 오늘 날짜
def Date(Option = "Day"):
    if Option == "Day":
      now = datetime.now()
      date = now.strftime('%y%m%d')
    elif Option == "Second":
      now = datetime.now()
      date = now.strftime('%y%m%d%H%M%S')
    
    return date

## 업데이트된 OutputMemoryDics 파일 Count 불러오기
def LoadOutputMemory(projectName, email, ProcessNum, DataFramePath):
    # 정규 표현식 패턴 정의
    pattern = re.compile(rf"{re.escape(DataFramePath + email + '_' + projectName + '_' + ProcessNum + '_')}outputMemoryDics_.*\.json")

    OutputMemoryDicsFile = []
    OutputMemoryCount = 0
    for filename in os.listdir(DataFramePath):
        FullPath = os.path.join(DataFramePath, filename)
        if pattern.match(FullPath):
            print(f"< User: {email} | Project: {projectName} | {FullPath} 로드 >")
            with open(FullPath, 'r', encoding='utf-8') as file:
                OutputMemoryDicsFile = json.load(file)
            OutputMemoryCount = len(OutputMemoryDicsFile)
            break  # 첫 번째 일치하는 파일을 찾으면 반복 종료

        normalizedFilename = unicodedata.normalize('NFC', filename)
        normalizedFullPath = os.path.join(DataFramePath, normalizedFilename)
        if pattern.match(normalizedFullPath):
            print(f"< User: {email} | Project: {projectName} | {normalizedFullPath} 로드 >")
            with open(normalizedFullPath, 'r', encoding='utf-8') as file:
                OutputMemoryDicsFile = json.load(file)
            OutputMemoryCount = len(OutputMemoryDicsFile)
            break  # 첫 번째 일치하는 파일을 찾으면 반복 종료

    return OutputMemoryDicsFile, OutputMemoryCount

## 업데이트된 AddOutputMemoryDics 파일 Count 불러오기
def LoadAddOutputMemory(projectName, email, ProcessNum, DataFramePath):
    # 정규 표현식 패턴 정의
    pattern = re.compile(rf"{re.escape(DataFramePath + email + '_' + projectName + '_' + ProcessNum + '_')}addOutputMemoryDics_.*\.json")

    AddOutputMemoryDicsFile = []
    for filename in os.listdir(DataFramePath):
        normalizedFilename = unicodedata.normalize('NFC', filename)
        FullPath = os.path.join(DataFramePath, normalizedFilename)
        if pattern.match(FullPath):
            print(f"< User: {email} | Project: {projectName} | {FullPath} 로드 >")
            with open(FullPath, 'r', encoding='utf-8') as file:
                AddOutputMemoryDicsFile = json.load(file)
            break  # 첫 번째 일치하는 파일을 찾으면 반복 종료

    return AddOutputMemoryDicsFile

## 각 유저별 DataframeFilePaths 찾기
def FindDataframeFilePaths(email, projectName, userStoragePath):
    with get_db() as db:
        user = db.query(User).filter(User.Email == email).first()
        if user is None:
            raise ValueError("User not found with the provided email")
        
        username = user.UserName

        # 데이터프레임 파일 경로 구성
        expectedFilePath = os.path.join(userStoragePath, f"{username}_user", f"{username}_storage", projectName, f"{projectName}_dataframe_file")
        # normalizedFilePath = unicodedata.normalize('NFC', expectedFilePath)

        # 파일 존재 여부 확인
        if os.path.exists(expectedFilePath):
            # 파일이 존재하면 정규화된 파일 경로 반환
            return expectedFilePath + '/'
        else:
            # 파일이 존재하지 않으면, 빈 리스트 반환
            return None

## 업데이트된 OutputMemoryDics 파일 저장하기
def SaveOutputMemory(projectName, email, OutputMemoryDics, ProcessNum, DataFramePath):
    # 정규 표현식 패턴 정의
    pattern = re.compile(rf"{re.escape(email + '_' + projectName + '_' + ProcessNum + '_outputMemoryDics_')}.*\.json")

    # 일치하는 파일 검색
    matched_file = None
    for filename in os.listdir(DataFramePath):
        if pattern.match(filename):
            matched_file = filename
            break

    if matched_file:
        # 일치하는 파일이 있는 경우
        OutputMemoryDicsFilename = os.path.join(DataFramePath, matched_file)
    else:
        # 일치하는 파일이 없는 경우 새 파일명 생성
        OutputMemoryDicsFilename = os.path.join(DataFramePath, email + '_' + projectName + '_' + ProcessNum + '_outputMemoryDics_' + str(Date()) + '.json')

    # OutputMemoryDics 데이터를 파일에 덮어쓰기
    with open(OutputMemoryDicsFilename, 'w', encoding='utf-8') as file:
        json.dump(OutputMemoryDics, file, ensure_ascii = False, indent = 4)
        
## 업데이트된 AddOutputMemoryDics 파일 저장하기
def SaveAddOutputMemory(projectName, email, AddOutputMemoryDics, ProcessNum, DataFramePath):
    # 정규 표현식 패턴 정의
    pattern = re.compile(rf"{re.escape(email + '_' + projectName + '_' + ProcessNum + '_addOutputMemoryDics_')}.*\.json")

    # 일치하는 파일 검색
    matched_file = None
    for filename in os.listdir(DataFramePath):
        if pattern.match(filename):
            matched_file = filename
            break

    if matched_file:
        # 일치하는 파일이 있는 경우
        AddOutputMemoryDicsFilename = os.path.join(DataFramePath, matched_file)
    else:
        # 일치하는 파일이 없는 경우 새 파일명 생성
        AddOutputMemoryDicsFilename = os.path.join(DataFramePath, email + '_' + projectName + '_' + ProcessNum + '_addOutputMemoryDics_' + str(Date()) + '.json')

    # OutputMemoryDics 데이터를 파일에 덮어쓰기
    with open(AddOutputMemoryDicsFilename, 'w', encoding='utf-8') as file:
        json.dump(AddOutputMemoryDics, file, ensure_ascii = False, indent = 4)

###################################################
##### 전체 DataFrame의 MetaData(식별)부분을 업데이트 #####
###################################################
def AddFrameMetaDataToDB(projectName, email):
    with get_db() as db:
        project = GetProject(projectName, email)

        if not project:
            print("Project not found!")
            return
        
        for column in Project.__table__.columns:
            if isinstance(column.type, JSON):
                ProcessData = getattr(project, column.name)
                if ProcessData is None:
                    continue
                ProcessData[0]["UserId"] = project.UserId
                ProcessData[0]["ProjectsStorageID"] = project.ProjectsStorageId
                ProcessData[0]["ProjectId"] = project.ProjectId
                ProcessData[0]["ProjectName"] = project.ProjectName
                setattr(project, column.name, ProcessData)
                flag_modified(project, column.name)

        db.add(project)
        db.commit()


##################################
##### 01_IndexDefine Process #####
##################################
## 1. 1-0 IndexFrame이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedIndexFrameToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.IndexFrame[1] = ExistedDataFrame[1]
        
        flag_modified(project, "IndexFrame")
        
        db.add(project)
        db.commit()

## 1. 1-2 IndexFrame의 Body(본문)부분 업데이트 형식
def UpdateIndexTags(project, IndexId, IndexTag, Index):
    
    updateIndexTags = {
        "IndexId": IndexId,
        "IndexTag": IndexTag,
        "Index": Index
    }
    
    project.IndexFrame[1]["IndexTags"].append(updateIndexTags)
    # Count 업데이트
    project.IndexFrame[0]["IndexCount"] = IndexId

## 1. 1-3 IndexFrame의 Body(본문)부분 업데이트
def AddIndexFrameBodyToDB(projectName, email, IndexId, IndexTag, Index):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        UpdateIndexTags(project, IndexId, IndexTag, Index)
        
        flag_modified(project, "IndexFrame")
        
        db.add(project)
        db.commit()

## 1. IndexFrameCount 가져오기
def IndexFrameCountLoad(projectName, email):

    project = GetProject(projectName, email)
    IndexCount = project.IndexFrame[0]["IndexCount"]
    Completion = project.IndexFrame[0]["Completion"]
    
    return IndexCount, Completion
        
## 1. IndexFrame의 초기화
def InitIndexFrame(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.IndexFrame[0]["IndexCount"] = 0
        project.IndexFrame[0]["Completion"] = "No"
        project.IndexFrame[1] = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-01_IndexFrame.json")[1]
        
        flag_modified(project, "IndexFrame")
        
        db.add(project)
        db.commit()
        
## 1. 업데이트된 IndexFrame 출력
def UpdatedIndexFrame(projectName, email):
    with get_db() as db:
        project = GetProject(projectName, email)

    return project.IndexFrame

## 1. IndexFrameCompletion 업데이트
def IndexFrameCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.IndexFrame[0]["Completion"] = "Yes"

        flag_modified(project, "IndexFrame")

        db.add(project)
        db.commit()


##############################################
##### 03_BodySplit, IndexTagging Process #####
##############################################
## 3. 1-0 BodyFrame이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedBodyFrameToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.BodyFrame[1] = ExistedDataFrame[1]
        project.BodyFrame[2] = ExistedDataFrame[2]
        
        flag_modified(project, "BodyFrame")
        
        db.add(project)
        db.commit()
        
## 3. 1-2 BodyFrame의 Body(본문) Body부분 업데이트 형식
def UpdateSplitedBodyScripts(project, IndexId, IndexTag, Index):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(project.BodyFrame[1]["SplitedBodyScripts"])
    
    updateSplitedBodyScripts = {
        "IndexId": IndexId,
        "IndexTag": IndexTag,
        "Index": Index,
        "BodyId": BodyId,
        "SplitedBodyChunks": []
    }
    
    project.BodyFrame[1]["SplitedBodyScripts"].append(updateSplitedBodyScripts)
    # Count 업데이트
    project.BodyFrame[0]["IndexCount"] = IndexId
    project.BodyFrame[0]["BodyCount"] = BodyId

## 3. 1-3 BodyFrame의 Body(본문) Body부분 업데이트
def AddBodyFrameBodyToDB(projectName, email, IndexId, IndexTag, Index):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSplitedBodyScripts(project, IndexId, IndexTag, Index)
        
        flag_modified(project, "BodyFrame")
        
        db.add(project)
        db.commit()

## 3. 2-1 BodyFrame의 Body(본문) TagChunks부분 업데이트 형식
def UpdateSplitedBodyTagChunks(project, ChunkId, Tag, Chunk):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(project.BodyFrame[1]["SplitedBodyScripts"]) -1
    
    updateSplitedBodyChunks = {
        "ChunkId": ChunkId,
        "Tag": Tag,
        "Chunk":Chunk
    }
    
    project.BodyFrame[1]["SplitedBodyScripts"][BodyId]["SplitedBodyChunks"].append(updateSplitedBodyChunks)
    # Count 업데이트
    project.BodyFrame[0]["ChunkCount"] = ChunkId

## 3. 2-2 BodyFrame의 Body(본문) TagChunks부분 업데이트
def AddBodyFrameChunkToDB(projectName, email, ChunkId, Tag, Chunk):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSplitedBodyTagChunks(project, ChunkId, Tag, Chunk)
        
        flag_modified(project, "BodyFrame")
        
        db.add(project)
        db.commit()
        
## 3. 3-1 BodyFrame의 Bodys(부문) Bodys부분 업데이트 형식
def UpdateBodys(project, ChunkIds, Task, Body, Correction, Character, Context = "None", SFX = "None"):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(project.BodyFrame[2]["Bodys"])
    
    updateBodys = {
        "BodyId": BodyId,
        "ChunkId": ChunkIds,
        "Task": Task,
        "Body": Body,
        "Correction": Correction,
        "Character": Character,
        "Context": Context,
        "SFX": SFX
    }
    
    project.BodyFrame[2]["Bodys"].append(updateBodys)
    
## 3. 3-2 BodyFrame의 Bodys(부문) Bodys부분 업데이트
def AddBodyFrameBodysToDB(projectName, email, ChunkIds, Task, Body, Correction, Character, context = "None", sfx = "None"):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateBodys(project, ChunkIds, Task, Body, Correction, Character, Context = context, SFX = sfx)
        
        flag_modified(project, "BodyFrame")
        
        db.add(project)
        db.commit()
                
## 3. BodyFrame의Count의 가져오기
def BodyFrameCountLoad(projectName, email):

    project = GetProject(projectName, email)
    IndexCount = project.BodyFrame[0]["IndexCount"]
    BodyCount = project.BodyFrame[0]["BodyCount"]
    ChunkCount = project.BodyFrame[0]["ChunkCount"]
    Completion = project.BodyFrame[0]["Completion"]
    
    return IndexCount, BodyCount, ChunkCount, Completion

## 3. BodyFrame의 초기화
def InitBodyFrame(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.BodyFrame[0]["IndexCount"] = 0
        project.BodyFrame[0]["BodyCount"] = 0
        project.BodyFrame[0]["ChunkCount"] = 0
        project.BodyFrame[0]["Completion"] = "No"
        project.BodyFrame[1] = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-03_BodyFrame.json")[1]
        project.BodyFrame[2] = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-03_BodyFrame.json")[2]
        
        flag_modified(project, "BodyFrame")
        
        db.add(project)
        db.commit()
        
## 3. 업데이트된 BodyFrame 출력
def UpdatedBodyFrame(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)

    return project.BodyFrame

## 3. BodyFrameCompletion 업데이트
def BodyFrameCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.BodyFrame[0]["Completion"] = "Yes"

        flag_modified(project, "BodyFrame")

        db.add(project)
        db.commit()
        

##################################################
##### 04_HalfBodySplit, IndexTagging Process #####
##################################################
## 4. 1-0 HalfBodyFrame이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedHalfBodyFrameToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.HalfBodyFrame[1] = ExistedDataFrame[1]
        project.HalfBodyFrame[2] = ExistedDataFrame[2]
        
        flag_modified(project, "HalfBodyFrame")
        
        db.add(project)
        db.commit()
        
## 4. 1-2 HalfBodyFrame의 Body(본문) Body부분 업데이트 형식
def UpdateSplitedHalfBodyScripts(project, IndexId, IndexTag, Index):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(project.HalfBodyFrame[1]["SplitedBodyScripts"])
    
    updateSplitedBodyScripts = {
        "IndexId": IndexId,
        "IndexTag": IndexTag,
        "Index": Index,
        "BodyId": BodyId,
        "SplitedBodyChunks": []
    }
    
    project.HalfBodyFrame[1]["SplitedBodyScripts"].append(updateSplitedBodyScripts)
    # Count 업데이트
    project.HalfBodyFrame[0]["IndexCount"] = IndexId
    project.HalfBodyFrame[0]["BodyCount"] = BodyId

## 4. 1-3 HalfBodyFrame의 Body(본문) Body부분 업데이트
def AddHalfBodyFrameBodyToDB(projectName, email, IndexId, IndexTag, Index):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSplitedHalfBodyScripts(project, IndexId, IndexTag, Index)
        
        flag_modified(project, "HalfBodyFrame")
        
        db.add(project)
        db.commit()

## 4. 2-1 HalfBodyFrame의 Body(본문) TagChunks부분 업데이트 형식
def UpdateSplitedHalfBodyTagChunks(project, ChunkId, Tag, Chunk):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(project.HalfBodyFrame[1]["SplitedBodyScripts"]) -1
    
    updateSplitedBodyChunks = {
        "ChunkId": ChunkId,
        "Tag": Tag,
        "Chunk":Chunk
    }
    
    project.HalfBodyFrame[1]["SplitedBodyScripts"][BodyId]["SplitedBodyChunks"].append(updateSplitedBodyChunks)
    # Count 업데이트
    project.HalfBodyFrame[0]["ChunkCount"] = ChunkId

## 4. 2-2 HalfBodyFrame의 Body(본문) TagChunks부분 업데이트
def AddHalfBodyFrameChunkToDB(projectName, email, ChunkId, Tag, Chunk):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSplitedHalfBodyTagChunks(project, ChunkId, Tag, Chunk)
        
        flag_modified(project, "HalfBodyFrame")
        
        db.add(project)
        db.commit()
        
## 4. 3-1 HalfBodyFrame의 Bodys(부문) Bodys부분 업데이트 형식
def UpdateHalfBodys(project, ChunkIds, Task, Body, Correction, Character, Context = "None", SFX = "None"):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(project.HalfBodyFrame[2]["Bodys"])
    
    updateBodys = {
        "BodyId": BodyId,
        "ChunkId": ChunkIds,
        "Task": Task,
        "Body": Body,
        "Correction": Correction,
        "Character": Character,
        "Context": Context,
        "SFX": SFX
    }
    
    project.HalfBodyFrame[2]["Bodys"].append(updateBodys)
    
## 4. 3-2 HalfBodyFrame의 Bodys(부문) Bodys부분 업데이트
def AddHalfBodyFrameBodysToDB(projectName, email, ChunkIds, Task, Body, Correction, Character, context = "None", sfx = "None"):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateHalfBodys(project, ChunkIds, Task, Body, Correction, Character, Context = context, SFX = sfx)
        
        flag_modified(project, "HalfBodyFrame")
        
        db.add(project)
        db.commit()
                
## 4. HalfBodyFrame의Count의 가져오기
def HalfBodyFrameCountLoad(projectName, email):

    project = GetProject(projectName, email)
    IndexCount = project.HalfBodyFrame[0]["IndexCount"]
    BodyCount = project.HalfBodyFrame[0]["BodyCount"]
    ChunkCount = project.HalfBodyFrame[0]["ChunkCount"]
    Completion = project.HalfBodyFrame[0]["Completion"]
    
    return IndexCount, BodyCount, ChunkCount, Completion

## 4. HalfBodyFrame의 초기화
def InitHalfBodyFrame(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.HalfBodyFrame[0]["IndexCount"] = 0
        project.HalfBodyFrame[0]["BodyCount"] = 0
        project.HalfBodyFrame[0]["ChunkCount"] = 0
        project.HalfBodyFrame[0]["Completion"] = "No"
        project.HalfBodyFrame[1] = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-03_BodyFrame.json")[1]
        project.HalfBodyFrame[2] = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-03_BodyFrame.json")[2]
        
        flag_modified(project, "HalfBodyFrame")
        
        db.add(project)
        db.commit()
        
## 4. 업데이트된 HalfBodyFrame 출력
def UpdatedHalfBodyFrame(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)

    return project.HalfBodyFrame

## 4. HalfBodyFrameCompletion 업데이트
def HalfBodyFrameCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.HalfBodyFrame[0]["Completion"] = "Yes"

        flag_modified(project, "HalfBodyFrame")

        db.add(project)
        db.commit()


####################################
##### 06_CaptionCompletion Process #####
####################################
## 6. 1-0 CaptionCompletion이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedCaptionCompletionToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.CaptionFrame[1] = ExistedDataFrame[1]
        
        flag_modified(project, "CaptionFrame")
        
        db.add(project)
        db.commit()

## 6. 1-1 CaptionCompletion의 Body(본문) updateContextChunks 업데이트 형식
def UpdateCaptionCompletions(project, CaptionId, CaptionTag, CaptionType, Reason, Importance, ChunkIds, SplitedCaptionChunks):    
    updateCaptionCompletions = {
        "CaptionId": CaptionId,
        "CaptionTag": CaptionTag,
        "CaptionType": CaptionType,
        "Reason": Reason,
        "Importance": Importance,
        "ChunkIds": ChunkIds,
        "SplitedCaptionChunks": SplitedCaptionChunks
    }
    
    project.CaptionFrame[1]["CaptionCompletions"].append(updateCaptionCompletions)
    project.CaptionFrame[0]["CaptionCount"] = CaptionId
    
## 6. 1-2 CaptionCompletion의 Body(본문) updateContextChunks 업데이트
def AddCaptionCompletionChunksToDB(projectName, email, CaptionId, CaptionTag, CaptionType, Reason, Importance, ChunkIds, SplitedCaptionChunks):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateCaptionCompletions(project, CaptionId, CaptionTag, CaptionType, Reason, Importance, ChunkIds, SplitedCaptionChunks)
        
        flag_modified(project, "CaptionFrame")
        
        db.add(project)
        db.commit()
        
## 6. CaptionCompletion의Count의 가져오기
def CaptionCompletionCountLoad(projectName, email):

    project = GetProject(projectName, email)
    CaptionCount = project.CaptionFrame[0]["CaptionCount"]
    Completion = project.CaptionFrame[0]["Completion"]
    
    return CaptionCount, Completion

## 6. CaptionCompletion의 초기화
def InitCaptionCompletion(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.CaptionFrame[0]["CaptionCount"] = 0
        project.CaptionFrame[0]["Completion"] = "No"
        project.CaptionFrame[1] = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-04_CaptionFrame.json")[1]

        flag_modified(project, "CaptionFrame")
        
        db.add(project)
        db.commit()
        
## 6. 업데이트된 CaptionCompletion 출력
def UpdatedCaptionCompletion(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)

    return project.CaptionFrame

## 6. CaptionCompletionCompletion 업데이트
def CaptionCompletionCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.CaptionFrame[0]["Completion"] = "Yes"

        flag_modified(project, "CaptionFrame")

        db.add(project)
        db.commit()


####################################
##### 07_ContextDefine Process #####
####################################
## 7. 1-0 ContextDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedContextDefineToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.ContextDefine[1] = ExistedDataFrame[1]
        
        flag_modified(project, "ContextDefine")
        
        db.add(project)
        db.commit()

## 7. 1-1 ContextDefine의 Body(본문) updateContextChunks 업데이트 형식
def UpdateChunkContexts(project, ContextChunkId, ChunkId, Chunk, Phrases, Reader, Subject, Purpose, Reason, Question, Importance):    
    updateContextChunks = {
        "ContextChunkId": ContextChunkId,
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Phrases": Phrases,
        "Reader": Reader,
        "Subject": Subject,
        "Purpose": Purpose,
        "Reason": Reason,
        "Question": Question,
        "Importance": Importance
    }
    
    project.ContextDefine[1]["ContextChunks"].append(updateContextChunks)
    project.ContextDefine[0]["ContextChunkCount"] = ContextChunkId
    
## 7. 1-2 ContextDefine의 Body(본문) updateContextChunks 업데이트
def AddContextDefineChunksToDB(projectName, email, ContextChunkId, ChunkId, Chunk, Phrases, Reader, Subject, Purpose, Reason, Question, Importance):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateChunkContexts(project, ContextChunkId, ChunkId, Chunk, Phrases, Reader, Subject, Purpose, Reason, Question, Importance)
        
        flag_modified(project, "ContextDefine")
        
        db.add(project)
        db.commit()
        
## 7. ContextDefine의Count의 가져오기
def ContextDefineCountLoad(projectName, email):

    project = GetProject(projectName, email)
    ContextChunkCount = project.ContextDefine[0]["ContextChunkCount"]
    ContextCount = project.ContextDefine[0]["ContextCount"]
    Completion = project.ContextDefine[0]["Completion"]
    
    return ContextChunkCount, ContextCount, Completion

## 7. ContextDefine의 초기화
def InitContextDefine(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.ContextDefine[0]["ContextChunkCount"] = 0
        project.ContextDefine[0]["ContextCount"] = 0
        project.ContextDefine[0]["Completion"] = "No"
        project.ContextDefine[1] = LoadJsonFrame(ProjectDataPath + "/b532_Context/b532-01_ContextDefine.json")[1]
        
        flag_modified(project, "ContextDefine")
        
        db.add(project)
        db.commit()
        
## 7. 업데이트된 ContextDefine 출력
def UpdatedContextDefine(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)

    return project.ContextDefine

## 7. ContextDefineCompletion 업데이트
def ContextDefineCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.ContextDefine[0]["Completion"] = "Yes"

        flag_modified(project, "ContextDefine")

        db.add(project)
        db.commit()


########################################
##### 08_ContextCompletion Process #####
########################################
## 8. 1-0 ContextCompletion이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedContextCompletionToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.ContextCompletion[1] = ExistedDataFrame[1]
        project.ContextCompletion[2] = ExistedDataFrame[2]
        
        flag_modified(project, "ContextCompletion")
        
        db.add(project)
        db.commit()

## 8. 1-1 ContextCompletion의 Body(본문) ContextCompletions 업데이트 형식
def UpdateCompletionContexts(project, ContextChunkId, ChunkId, Chunk, Genre, Gender, Age, Personality, Emotion, Accuracy):    
    updateContextCompletions = {
        "ContextChunkId": ContextChunkId,
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Genre": Genre,
        "Gender": Gender,
        "Age": Age,
        "Personality": Personality,
        "Emotion": Emotion,
        "Accuracy": Accuracy
    }
    
    project.ContextCompletion[1]["ContextCompletions"].append(updateContextCompletions)
    project.ContextCompletion[0]["ContextChunkCount"] = ContextChunkId
    
## 8. 1-2 ContextCompletion의 Body(본문) ContextCompletions 업데이트
def AddContextCompletionChunksToDB(projectName, email, ContextChunkId, ChunkId, Chunk, Genre, Gender, Age, Personality, Emotion, Accuracy):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateCompletionContexts(project, ContextChunkId, ChunkId, Chunk, Genre, Gender, Age, Personality, Emotion, Accuracy)
        
        flag_modified(project, "ContextCompletion")
        
        db.add(project)
        db.commit()
        
## 8. 2-1 ContextCompletion의 Context(부문) ContextTags부분 업데이트 형식
def updateCheckedContextTags(project, ContextTag, ContextList, Context):
    # 새롭게 생성되는 ContextId는 CheckedContextTags의 Len값과 동일
    ContextId = len(project.ContextCompletion[2]["CheckedContextTags"]) -1
    
    ### 실제 테스크시 수정 요망 ###
    updateCheckedContextTags = {
        "ContextId": ContextId,
        "ContextTag": ContextTag,
        "ContextList": ContextList,
        "Context": Context
    }
    
    project.ContextCompletion[2]["CheckedContextTags"].append(updateCheckedContextTags)
    project.ContextCompletion[0]["ContextCount"] = ContextId
    
## 8. 2-2 ContextCompletion의 Context(부문) ContextTags부분 업데이트
def AddContextCompletionCheckedContextTagsToDB(projectName, email, ContextTag, ContextList, Context):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        updateCheckedContextTags(project, ContextTag, ContextList, Context)
        
        flag_modified(project, "ContextCompletion")
        
        db.add(project)
        db.commit()
        
## 8. ContextCompletion의Count의 가져오기
def ContextCompletionCountLoad(projectName, email):

    project = GetProject(projectName, email)
    ContextChunkCount = project.ContextCompletion[0]["ContextChunkCount"]
    ContextCount = project.ContextCompletion[0]["ContextCount"]
    Completion = project.ContextCompletion[0]["Completion"]
    
    return ContextChunkCount, ContextCount, Completion

## 8. ContextCompletion의 초기화
def InitContextCompletion(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.ContextCompletion[0]["ContextChunkCount"] = 0
        project.ContextCompletion[0]["ContextCount"] = 0
        project.ContextCompletion[0]["Completion"] = "No"
        project.ContextCompletion[1] = LoadJsonFrame(ProjectDataPath + "/b532_Context/b532-02_ContextCompletion.json")[1]
        project.ContextCompletion[2] = LoadJsonFrame(ProjectDataPath + "/b532_Context/b532-02_ContextCompletion.json")[2]

        flag_modified(project, "ContextCompletion")
        
        db.add(project)
        db.commit()
        
## 8. 업데이트된 ContextCompletion 출력
def UpdatedContextCompletion(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        
    return project.ContextCompletion
        
## 8. ContextCompletionCompletion 업데이트
def ContextCompletionCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.ContextCompletion[0]["Completion"] = "Yes"

        flag_modified(project, "ContextCompletion")

        db.add(project)
        db.commit()


#####################################
##### 09_WMWMDefine Process #####
#####################################
## 9. 1-0 WMWMDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedWMWMDefineToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.WMWMDefine[1] = ExistedDataFrame[1]
        project.WMWMDefine[2] = ExistedDataFrame[2]
        
        flag_modified(project, "WMWMDefine")
        
        db.add(project)
        db.commit()

## 9. 1-1 WMWMDefine의 Body(본문) WMWMCompletions 업데이트 형식
def UpdateCompletionWMWMs(project, WMWMChunkId, ChunkId, Chunk, Needs, ReasonOfNeeds, Wisdom, ReasonOfWisdom, Mind, ReasonOfPotentialMind, Wildness, ReasonOfWildness, Accuracy):    
    updateWMWMCompletions = {
        "WMWMChunkId": WMWMChunkId,
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Needs": Needs,
        "ReasonOfNeeds": ReasonOfNeeds,
        "Wisdom": Wisdom,
        "ReasonOfWisdom": ReasonOfWisdom,
        "Mind": Mind,
        "ReasonOfPotentialMind": ReasonOfPotentialMind,
        "Wildness": Wildness,
        "ReasonOfWildness": ReasonOfWildness,
        "Accuracy": Accuracy
    }
    
    project.WMWMDefine[1]["WMWMCompletions"].append(updateWMWMCompletions)
    project.WMWMDefine[0]["WMWMChunkCount"] = WMWMChunkId
    
## 9. 1-2 WMWMDefine의 Body(본문) WMWMCompletions 업데이트
def AddWMWMDefineChunksToDB(projectName, email, WMWMChunkId, ChunkId, Chunk, Needs, ReasonOfNeeds, Wisdom, ReasonOfWisdom, Mind, ReasonOfPotentialMind, Wildness, ReasonOfWildness, Accuracy):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateCompletionWMWMs(project, WMWMChunkId, ChunkId, Chunk, Needs, ReasonOfNeeds, Wisdom, ReasonOfWisdom, Mind, ReasonOfPotentialMind, Wildness, ReasonOfWildness, Accuracy)
        
        flag_modified(project, "WMWMDefine")
        
        db.add(project)
        db.commit()
        
## 9. 2-1 WMWMDefine의 WMWM(부문) WMWMTags부분 업데이트 형식
def updateWMWMQuerys(project, WMWMChunkId, ChunkId, Vector, WMWM):
    # 새롭게 생성되는 WMWMId는 WMWMQuerys의 Len값과 동일
    WMWMId = len(project.WMWMDefine[2]["WMWMQuerys"]) -1
    
    ### 실제 테스크시 수정 요망 ###
    updateWMWMQuerys = {
        "WMWMChunkId": WMWMChunkId,
        "ChunkId": ChunkId,
        "Vector": Vector,
        "WMWM": WMWM
    }
    
    project.WMWMDefine[2]["WMWMQuerys"].append(updateWMWMQuerys)
    project.WMWMDefine[0]["WMWMCount"] = WMWMId
    
## 9. 2-2 WMWMDefine의 WMWM(부문) WMWMTags부분 업데이트
def AddWMWMDefineWMWMQuerysToDB(projectName, email, WMWMChunkId, ChunkId, Vector, WMWM):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        updateWMWMQuerys(project, WMWMChunkId, ChunkId, Vector, WMWM)
        
        flag_modified(project, "WMWMDefine")
        
        db.add(project)
        db.commit()
        
## 9. WMWMDefine의Count의 가져오기
def WMWMDefineCountLoad(projectName, email):

    project = GetProject(projectName, email)
    WMWMChunkCount = project.WMWMDefine[0]["WMWMChunkCount"]
    WMWMCount = project.WMWMDefine[0]["WMWMCount"]
    Completion = project.WMWMDefine[0]["Completion"]
    
    return WMWMChunkCount, WMWMCount, Completion

## 9. WMWMDefine의 초기화
def InitWMWMDefine(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.WMWMDefine[0]["WMWMChunkCount"] = 0
        project.WMWMDefine[0]["WMWMCount"] = 0
        project.WMWMDefine[0]["Completion"] = "No"
        project.WMWMDefine[1] = LoadJsonFrame(ProjectDataPath + "/b532_Context/b532-03_WMWMDefine.json")[1]
        project.WMWMDefine[2] = LoadJsonFrame(ProjectDataPath + "/b532_Context/b532-03_WMWMDefine.json")[2]

        flag_modified(project, "WMWMDefine")
        
        db.add(project)
        db.commit()
        
## 9. 업데이트된 WMWMDefine 출력
def UpdatedWMWMDefine(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        
    return project.WMWMDefine
        
## 9. WMWMDefineCompletion 업데이트
def WMWMDefineCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.WMWMDefine[0]["Completion"] = "Yes"

        flag_modified(project, "WMWMDefine")

        db.add(project)
        db.commit()


#####################################
##### 10_WMWMMatching Process #####
#####################################
## 10. 1-0 WMWMDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedWMWMMatchingToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.WMWMMatching[1] = ExistedDataFrame[1]
        
        flag_modified(project, "WMWMMatching")
        
        db.add(project)
        db.commit()

## 10. 1-1 WMWMMatching의 Body(본문) SplitedChunkContexts 업데이트 형식
def UpdateSplitedChunkContexts(project, ChunkId, Chunk, Vector, WMWM):    
    updateSplitedChunkContexts = {
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Vector": Vector,
        "WMWM": WMWM
    }
    
    project.WMWMMatching[1]["SplitedChunkContexts"].append(updateSplitedChunkContexts)
    project.WMWMMatching[0]["WMWMChunkCount"] = ChunkId
    
## 10. 1-2 WMWMMatching의 Body(본문) SplitedChunkContexts 업데이트
def AddWMWMMatchingChunksToDB(projectName, email, ChunkId, Chunk, Vector, WMWM):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSplitedChunkContexts(project, ChunkId, Chunk, Vector, WMWM)
        
        flag_modified(project, "WMWMMatching")
        
        db.add(project)
        db.commit()
        
## 10. 1-3 WMWMMatching의 Body(본문) SplitedBodyContexts 업데이트 형식
def UpdateSplitedBodyContexts(project, BodyId, Phrases, Vector, WMWM):    
    updateSplitedBodyContexts = {
        "BodyId": BodyId,
        "Phrases": Phrases,
        "Vector": Vector,
        "WMWM": WMWM
    }
    
    project.WMWMMatching[1]["SplitedBodyContexts"].append(updateSplitedBodyContexts)
    project.WMWMMatching[0]["WMWMBodyCount"] = BodyId
    
## 10. 1-4 WMWMMatching의 Body(본문) SplitedBodyContexts 업데이트
def AddWMWMMatchingBODYsToDB(projectName, email, BodyId, Phrases, Vector, WMWM):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSplitedBodyContexts(project, BodyId, Phrases, Vector, WMWM)
        
        flag_modified(project, "WMWMMatching")
        
        db.add(project)
        db.commit()
        
## 10. 1-5 WMWMMatching의 Index(본문) SplitedIndexContexts 업데이트 형식
def UpdateSplitedIndexContexts(project, IndexId, Index, Phrases, Vector, WMWM):    
    updateSplitedIndexContexts = {
        "IndexId": IndexId,
        "Index": Index,
        "Phrases": Phrases,
        "Vector": Vector,
        "WMWM": WMWM
    }
    
    project.WMWMMatching[1]["SplitedIndexContexts"].append(updateSplitedIndexContexts)
    project.WMWMMatching[0]["WMWMIndexCount"] = IndexId
    
## 10. 1-6 WMWMMatching의 Index(본문) SplitedIndexContexts 업데이트
def AddWMWMMatchingIndexsToDB(projectName, email, IndexId, Index, Phrases, Vector, WMWM):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSplitedIndexContexts(project, IndexId, Index, Phrases, Vector, WMWM)
        
        flag_modified(project, "WMWMMatching")
        
        db.add(project)
        db.commit()
        
## 10. 1-7 WMWMMatching의 Book(본문) SplitedBookContexts 업데이트 형식
def UpdateBookContexts(project, BookId, Title, Phrases, Vector, WMWM):    
    updateBookContexts = {
        "BookId": BookId,
        "Title": Title,
        "Phrases": Phrases,
        "Vector": Vector,
        "WMWM": WMWM
    }
    
    project.WMWMMatching[1]["BookContexts"].append(updateBookContexts)
    
## 10. 1-8 WMWMMatching의 Book(본문) SplitedBookContexts 업데이트
def AddWMWMMatchingBookToDB(projectName, email, BookId, Title, Phrases, Vector, WMWM):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateBookContexts(project, BookId, Title, Phrases, Vector, WMWM)
        
        flag_modified(project, "WMWMMatching")
        
        db.add(project)
        db.commit()
        
## 10. WMWMMatching의Count의 가져오기
def WMWMMatchingCountLoad(projectName, email):

    project = GetProject(projectName, email)
    WMWMChunkCount = project.WMWMMatching[0]["WMWMChunkCount"]
    WMWMBodyCount = project.WMWMMatching[0]["WMWMBodyCount"]
    WMWMIndexCount = project.WMWMMatching[0]["WMWMIndexCount"]
    Completion = project.WMWMMatching[0]["Completion"]
    
    return WMWMChunkCount, WMWMBodyCount, WMWMIndexCount, Completion

## 10. WMWMMatching의 초기화
def InitWMWMMatching(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.WMWMMatching[0]["WMWMChunkCount"] = 0
        project.WMWMMatching[0]["WMWMBodyCount"] = 0
        project.WMWMMatching[0]["WMWMIndexCount"] = 0
        project.WMWMMatching[0]["Completion"] = "No"
        project.WMWMMatching[1] = LoadJsonFrame(ProjectDataPath + "/b532_Context/b532-04_WMWMMatching.json")[1]

        flag_modified(project, "WMWMMatching")
        
        db.add(project)
        db.commit()
        
## 10. 업데이트된 WMWMMatching 출력
def UpdatedWMWMMatching(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        
    return project.WMWMMatching
        
## 10. WMWMMatchingCompletion 업데이트
def WMWMMatchingCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.WMWMMatching[0]["Completion"] = "Yes"

        flag_modified(project, "WMWMMatching")

        db.add(project)
        db.commit()


######################################
##### 11_CharacterDefine Process #####
######################################
## 11. 1-0 CharacterDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedCharacterDefineToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.CharacterDefine[1] = ExistedDataFrame[1]
        
        flag_modified(project, "CharacterDefine")
        
        db.add(project)
        db.commit()
        
## 11. 1-1 CharacterDefine의 Body(본문) updateCharacterChunks 업데이트 형식
def UpdateChunkCharacters(project, CharacterChunkId, ChunkId, Chunk, Character, Type, Gender, Age, Emotion, Role, Listener):    
    updateCharacterChunks = {
        "CharacterChunkId": CharacterChunkId,
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Character": Character,
        "Type": Type,
        "Gender": Gender,
        "Age": Age,
        "Emotion": Emotion,
        "Role": Role,
        "Listener": Listener
    }
    
    project.CharacterDefine[1]["CharacterChunks"].append(updateCharacterChunks)
    project.CharacterDefine[0]["CharacterChunkCount"] = CharacterChunkId
    
## 11. 1-2 CharacterDefine의 Body(본문) updateCharacterChunks 업데이트
def AddCharacterDefineChunksToDB(projectName, email, CharacterChunkId, ChunkId, Chunk, Character, Type, Gender, Age, Emotion, Role, Listener):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateChunkCharacters(project, CharacterChunkId, ChunkId, Chunk, Character, Type, Gender, Age, Emotion, Role, Listener)
        
        flag_modified(project, "CharacterDefine")
        
        db.add(project)
        db.commit()

## 11. CharacterDefine의Count의 가져오기
def CharacterDefineCountLoad(projectName, email):

    project = GetProject(projectName, email)
    CharacterChunkCount = project.CharacterDefine[0]["CharacterChunkCount"]
    CharacterCount = project.CharacterDefine[0]["CharacterCount"]
    Completion = project.CharacterDefine[0]["Completion"]
    
    return CharacterChunkCount, CharacterCount, Completion

## 11. CharacterDefine의 초기화
def InitCharacterDefine(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.CharacterDefine[0]["CharacterChunkCount"] = 0
        project.CharacterDefine[0]["CharacterCount"] = 0
        project.CharacterDefine[0]["Completion"] = "No"
        project.CharacterDefine[1] = LoadJsonFrame(ProjectDataPath + "/b533_Character/b533-01_CharacterDefine.json")[1]
        
        flag_modified(project, "CharacterDefine")
        
        db.add(project)
        db.commit()
        
## 11. 업데이트된 CharacterDefine 출력
def UpdatedCharacterDefine(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)

    return project.CharacterDefine

## 11. CharacterDefineCompletion 업데이트
def CharacterDefineCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.CharacterDefine[0]["Completion"] = "Yes"

        flag_modified(project, "CharacterDefine")

        db.add(project)
        db.commit()


##########################################
##### 12_CharacterCompletion Process #####
##########################################
## 12. 1-0 CharacterCompletion이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedCharacterCompletionToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.CharacterCompletion[1] = ExistedDataFrame[1]
        project.CharacterCompletion[2] = ExistedDataFrame[2]
        
        flag_modified(project, "CharacterCompletion")
        
        db.add(project)
        db.commit()
        
## 12. 1-1 CharacterCompletion의 Body(본문) CharacterCompletions 업데이트 형식
def UpdateCompletionCharacters(project, CharacterChunkId, ChunkId, Chunk, Character, MainCharacter, AuthorRelationship, Context, Voice):    
    updateCharacterCompletions = {
        "CharacterChunkId": CharacterChunkId,
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Character": Character,
        "MainCharacter": MainCharacter,
        "AuthorRelationship": AuthorRelationship,
        "Context": Context,
        "Voice": Voice
    }
    
    project.CharacterCompletion[1]["CharacterCompletions"].append(updateCharacterCompletions)
    project.CharacterCompletion[0]["CharacterChunkCount"] = CharacterChunkId
    
## 12. 1-2 CharacterCompletion의 Body(본문) CharacterCompletions 업데이트
def AddCharacterCompletionChunksToDB(projectName, email, CharacterChunkId, ChunkId, Chunk, Character, MainCharacter, AuthorRelationship, Context, Voice):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateCompletionCharacters(project, CharacterChunkId, ChunkId, Chunk, Character, MainCharacter, AuthorRelationship, Context, Voice)
        
        flag_modified(project, "CharacterCompletion")
        
        db.add(project)
        db.commit()
        
## 12. 2-1 CharacterCompletion의 Character(부문) CharacterTags부분 업데이트 형식
def updateCheckedCharacterTags(project, CharacterTag, Gender, Age, Emotion,MainCharacterList):
    # 새롭게 생성되는 CharacterId는 CharacterTags의 Len값과 동일
    CharacterId = len(project.CharacterCompletion[2]["CheckedCharacterTags"])
    
    ### 실제 테스크시 수정 요망 ###
    updateCheckedCharacterTags = {
        "CharacterId": CharacterId,
        "CharacterTag": CharacterTag,
        "Gender": Gender,
        "Age": Age,
        "Emotion": Emotion,
        "MainCharacterList": MainCharacterList
    }
    
    project.CharacterCompletion[2]["CheckedCharacterTags"].append(updateCheckedCharacterTags)
    project.CharacterCompletion[0]["CharacterCount"] = CharacterId
    
## 12. 2-2 CharacterCompletion의 Character(부문) CharacterTags부분 업데이트
def AddCharacterCompletionCheckedCharacterTagsToDB(projectName, email, CharacterTag, Gender, Age, Emotion, MainCharacterList):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        updateCheckedCharacterTags(project, CharacterTag, Gender, Age, Emotion,MainCharacterList)
        
        flag_modified(project, "CharacterCompletion")
        
        db.add(project)
        db.commit()
        
## 12. CharacterCompletion의Count의 가져오기
def CharacterCompletionCountLoad(projectName, email):

    project = GetProject(projectName, email)
    CharacterChunkCount = project.CharacterCompletion[0]["CharacterChunkCount"]
    CharacterCount = project.CharacterCompletion[0]["CharacterCount"]
    Completion = project.CharacterCompletion[0]["Completion"]
    
    return CharacterChunkCount, CharacterCount, Completion

## 12. CharacterCompletion의 초기화
def InitCharacterCompletion(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.CharacterCompletion[0]["CharacterChunkCount"] = 0
        project.CharacterCompletion[0]["CharacterCount"] = 0
        project.CharacterCompletion[0]["Completion"] = "No"
        project.CharacterCompletion[1] = LoadJsonFrame(ProjectDataPath + "/b533_Character/b533-02_CharacterCompletion.json")[1]
        project.CharacterCompletion[2] = LoadJsonFrame(ProjectDataPath + "/b533_Character/b533-02_CharacterCompletion.json")[2]

        flag_modified(project, "CharacterCompletion")
        
        db.add(project)
        db.commit()
        
## 12. 업데이트된 CharacterCompletion 출력
def UpdatedCharacterCompletion(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        
    return project.CharacterCompletion
        
## 12. CharacterCompletionCompletion 업데이트
def CharacterCompletionCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.CharacterCompletion[0]["Completion"] = "Yes"

        flag_modified(project, "CharacterCompletion")

        db.add(project)
        db.commit()


####################################
##### 14_SoundMatching Process #####
####################################
## 14. 1-0 SoundMatching이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedSoundMatchingToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.SoundMatching[1] = ExistedDataFrame[1]
        
        flag_modified(project, "SoundMatching")
        
        db.add(project)
        db.commit()
        
## 14. 1-1 SoundMatching의 Body(본문) SoundSplitedBodys 업데이트 형식
def UpdateSoundSplitedIndexs(project, IndexId, Sounds):
    updateSoundSplitedIndexs = {
        "IndexId": IndexId,
        "Sounds": Sounds
    }
    
    project.SoundMatching[1]["SoundSplitedIndexs"].append(updateSoundSplitedIndexs)
    project.SoundMatching[0]["IndexCount"] = IndexId
    
## 14. 1-2 SoundMatching의 Body(본문) SoundSplitedBodys 업데이트
def AddSoundSplitedIndexsToDB(projectName, email, IndexId, Sounds):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSoundSplitedIndexs(project, IndexId, Sounds)
        
        flag_modified(project, "SoundMatching")
        
        db.add(project)
        db.commit()
        
## 14. SoundMatching의Count의 가져오기
def SoundMatchingCountLoad(projectName, email):

    project = GetProject(projectName, email)
    BodyCount = project.SoundMatching[0]["BodyCount"]
    Completion = project.SoundMatching[0]["Completion"]
    
    return BodyCount, Completion

## 14. SoundMatching의 초기화
def InitSoundMatching(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.SoundMatching[0]["BodyCount"] = 0
        project.SoundMatching[0]["Completion"] = "No"
        project.SoundMatching[1] = LoadJsonFrame(ProjectDataPath + "/b535_Sound/b535-01_SoundMatching.json")[1]
        
        flag_modified(project, "SoundMatching")
        
        db.add(project)
        db.commit()
        
## 14. 업데이트된 SoundMatching 출력
def UpdatedSoundMatching(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        
    return project.SoundMatching
        
## 14. SoundMatchingCompletion 업데이트
def SoundMatchingCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.SoundMatching[0]["Completion"] = "Yes"

        flag_modified(project, "SoundMatching")

        db.add(project)
        db.commit()


###################################
##### 15_SFXMatching Process #####
###################################
## 15. 1-0 SFXMatching이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedSFXMatchingToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.SFXMatching[1] = ExistedDataFrame[1]
        
        flag_modified(project, "SFXMatching")
        
        db.add(project)
        db.commit()
        
## 15. 1-1 SFXMatching의 Body(본문) SFXSplitedBodys 업데이트 형식
def UpdateSFXSplitedBodys(project, SFXSplitedBodyChunks):
    BodyId = len(project.SFXMatching[1]["SFXSplitedBodys"])
    
    updateSFXSplitedBodys = {
        "BodyId": BodyId,
        "SFXSplitedBodyChunks": SFXSplitedBodyChunks
    }
    
    project.SFXMatching[1]["SFXSplitedBodys"].append(updateSFXSplitedBodys)
    project.SFXMatching[0]["BodyCount"] = BodyId
    
## 15. 1-2 SFXMatching의 Body(본문) SFXSplitedBodys 업데이트
def AddSFXSplitedBodysToDB(projectName, email, SFXSplitedBodyChunks):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSFXSplitedBodys(project, SFXSplitedBodyChunks)
        
        flag_modified(project, "SFXMatching")
        
        db.add(project)
        db.commit()
        
## 15. SFXMatching의Count의 가져오기
def SFXMatchingCountLoad(projectName, email):

    project = GetProject(projectName, email)
    BodyCount = project.SFXMatching[0]["BodyCount"]
    Completion = project.SFXMatching[0]["Completion"]
    
    return BodyCount, Completion

## 15. SFXMatching의 초기화
def InitSFXMatching(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.SFXMatching[0]["BodyCount"] = 0
        project.SFXMatching[0]["Completion"] = "No"
        project.SFXMatching[1] = LoadJsonFrame(ProjectDataPath + "/b536_SFX/b536-01_SFXMatching.json")[1]

        flag_modified(project, "SFXMatching")
        
        db.add(project)
        db.commit()
        
## 15. 업데이트된 SFXMatching 출력
def UpdatedSFXMatching(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        
    return project.SFXMatching
        
## 15. SFXMatchingCompletion 업데이트
def SFXMatchingCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.SFXMatching[0]["Completion"] = "Yes"

        flag_modified(project, "SFXMatching")

        db.add(project)
        db.commit()


###################################
##### 21_CorrectionKo Process #####
###################################
## 21. 1-0 CorrectionKo이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedCorrectionKoToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.CorrectionKo[1] = ExistedDataFrame[1]
        
        flag_modified(project, "CorrectionKo")
        
        db.add(project)
        db.commit()
        
## 21. 1-1 CorrectionKo의 Body(본문) CorrectionKoSplitedBodys 업데이트 형식
def UpdateCorrectionKoSplitedBodys(project):
    BodyId = len(project.CorrectionKo[1]["CorrectionKoSplitedBodys"])
    
    updateCorrectionKoSplitedBodys = {
        "BodyId": BodyId,
        "CorrectionKoSplitedBodyChunks": []
    }
    
    project.CorrectionKo[1]["CorrectionKoSplitedBodys"].append(updateCorrectionKoSplitedBodys)
    project.CorrectionKo[0]["BodyCount"] = BodyId
    
## 21. 1-2 CorrectionKo의 Body(본문) CorrectionKoSplitedBodys 업데이트
def AddCorrectionKoSplitedBodysToDB(projectName, email):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateCorrectionKoSplitedBodys(project)
        
        flag_modified(project, "CorrectionKo")
        
        db.add(project)
        db.commit()
        
## 21. 2-1 CorrectionKo의 Body(본문) CorrectionKoChunk 업데이트 형식
def UpdateCorrectionKoSplitedChunks(project, ChunkId, Tag, ChunkTokens):
    # 새롭게 생성되는 BodyId는 CorrectionKoSplitedBodys의 Len값과 동일
    BodyId = len(project.CorrectionKo[1]["CorrectionKoSplitedBodys"]) -1
    
    updateCorrectionKoChunkTokens = {
        "ChunkId": ChunkId,
        "Tag": Tag,
        "CorrectionKoChunkTokens": ChunkTokens
    }
    
    project.CorrectionKo[1]["CorrectionKoSplitedBodys"][BodyId]["CorrectionKoSplitedBodyChunks"].append(updateCorrectionKoChunkTokens)
    project.CorrectionKo[0]["BodyCount"] = BodyId
    # Count 업데이트
    project.CorrectionKo[0]["ChunkCount"] = ChunkId
    
## 21. 2-2 CorrectionKo의 Body(본문) CorrectionKoChunk 업데이트
def AddCorrectionKoChunksToDB(projectName, email, ChunkId, Tag, ChunkTokens):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateCorrectionKoSplitedChunks(project, ChunkId, Tag, ChunkTokens)
        
        flag_modified(project, "CorrectionKo")
        
        db.add(project)
        db.commit()
        
## 21. CorrectionKo의Count의 가져오기
def CorrectionKoCountLoad(projectName, email):

    project = GetProject(projectName, email)
    BodyCount = project.CorrectionKo[0]["BodyCount"]
    ChunkCount = project.CorrectionKo[0]["ChunkCount"]
    Completion = project.CorrectionKo[0]["Completion"]
    
    return BodyCount, ChunkCount, Completion

## 21. CorrectionKo의 초기화
def InitCorrectionKo(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.CorrectionKo[0]["IndexCount"] = 0
        project.CorrectionKo[0]["ChunkCount"] = 0
        project.CorrectionKo[0]["Completion"] = "No"
        project.CorrectionKo[1] = LoadJsonFrame(ProjectDataPath + "/b538_Correction/b538-01_CorrectionKo.json")[1]

        flag_modified(project, "CorrectionKo")
        
        db.add(project)
        db.commit()
        
## 21. 업데이트된 CorrectionKo 출력
def UpdatedCorrectionKo(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        
    return project.CorrectionKo
        
## 21. CorrectionKoCompletion 업데이트
def CorrectionKoCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.CorrectionKo[0]["Completion"] = "Yes"

        flag_modified(project, "CorrectionKo")

        db.add(project)
        db.commit()


#############################################
##### 26_SelectionGenerationKo Process #####
#############################################
## 26. 1-0 SelectionGenerationKo이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedSelectionGenerationKoToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.SelectionGenerationKo[1] = ExistedDataFrame[1]
        
        flag_modified(project, "SelectionGenerationKo")
        
        db.add(project)
        db.commit()

## 26. 1-1 SelectionGenerationKo의 Body(본문) SelectionGenerationKoSplitedBodys 업데이트 형식
def UpdateSelectionGenerationKoBookContext(project, SelectionGenerationKoBookContext):
    
    project.SelectionGenerationKo[1]["SelectionGenerationKoBookContext"].append(SelectionGenerationKoBookContext)
    
## 26. 1-2 SelectionGenerationKo의 Body(본문) SelectionGenerationKoSplitedBodys 업데이트
def AddSelectionGenerationKoBookContextToDB(projectName, email, SelectionGenerationKoBookContext):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSelectionGenerationKoBookContext(project, SelectionGenerationKoBookContext)
        
        flag_modified(project, "SelectionGenerationKo")
        
        db.add(project)
        db.commit()

## 26. 1-1 SelectionGenerationKo의 Body(본문) SelectionGenerationKoSplitedBodys 업데이트 형식
def UpdateSelectionGenerationKoSplitedIndexs(project, IndexId, IndexTag, Index, IndexContext, Music, Sound, SelectionGenerationKoSplitedBodys):
    
    updateSelectionGenerationKoSplitedIndex = {
        "IndexId": IndexId,
        "IndexTag": IndexTag,
        "Index": Index,
        "IndexContext": IndexContext,
        "Music": Music,
        "Sound": Sound,
        "SelectionGenerationKoSplitedBodys": SelectionGenerationKoSplitedBodys
    }
    
    project.SelectionGenerationKo[1]["SelectionGenerationKoSplitedIndexs"].append(updateSelectionGenerationKoSplitedIndex)
    project.SelectionGenerationKo[0]["IndexCount"] = IndexId
    
## 26. 1-2 SelectionGenerationKo의 Body(본문) SelectionGenerationKoSplitedBodys 업데이트
def AddSelectionGenerationKoSplitedIndexsToDB(projectName, email, IndexId, IndexTag, Index, IndexContext, Music, Sound, SelectionGenerationKoSplitedBodys):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSelectionGenerationKoSplitedIndexs(project, IndexId, IndexTag, Index, IndexContext, Music, Sound, SelectionGenerationKoSplitedBodys)
        
        flag_modified(project, "SelectionGenerationKo")
        
        db.add(project)
        db.commit()
        
## 26. SelectionGenerationKo의Count의 가져오기
def SelectionGenerationKoCountLoad(projectName, email):

    project = GetProject(projectName, email)
    IndexCount = project.SelectionGenerationKo[0]["IndexCount"]
    Completion = project.SelectionGenerationKo[0]["Completion"]
    
    return IndexCount, Completion

## 26. SelectionGenerationKo의 초기화
def InitSelectionGenerationKo(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.SelectionGenerationKo[0]["IndexCount"] = 0
        project.SelectionGenerationKo[0]["Completion"] = "No"
        project.SelectionGenerationKo[1] = LoadJsonFrame(ProjectDataPath + "/b539_SelectionGeneration/b539-01_SelectionGenerationKo.json")[1]

        flag_modified(project, "SelectionGenerationKo")
        
        db.add(project)
        db.commit()
        
## 26. 업데이트된 SelectionGenerationKo 출력
def UpdatedSelectionGenerationKo(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        
    return project.SelectionGenerationKo
        
## 26. SelectionGenerationKoCompletion 업데이트
def SelectionGenerationKoCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.SelectionGenerationKo[0]["Completion"] = "Yes"

        flag_modified(project, "SelectionGenerationKo")

        db.add(project)
        db.commit()

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    process = 'IndexDefinePreprocess'
    userStoragePath = "/yaas/storage/s1_Yeoreum/s11_UserStorage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################