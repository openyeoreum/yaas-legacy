import os
import re
import json
import unicodedata
import sys
import time
sys.path.append("/yaas")

from datetime import datetime
from agent.a2_Solution.a21_General.a212_Project import GetProjectDataPath, LoadJsonFrame
from agent.a2_Solution.a21_General.a214_GetProcessData import GetProject, SaveProject


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
    
    # 문자열 정규화
    DataFramePathNFCNormalized = unicodedata.normalize('NFC', DataFramePath)
    DataFramePathNFDNormalized = unicodedata.normalize('NFD', DataFramePath)
    
    ## 한글의 유니코드 문제로 인해 일반과 노멀라이즈를 2개로 분리하여 가장 최근 파일찾기 실행
    try:
        DataFramePathList = os.listdir(DataFramePath)
        dataFramePath = DataFramePath
    except:
        try:
            DataFramePathList = os.listdir(DataFramePathNFCNormalized)
            dataFramePath = DataFramePathNFCNormalized
        except:
            DataFramePathList = os.listdir(DataFramePathNFDNormalized)
            dataFramePath = DataFramePathNFDNormalized
        
    for filename in DataFramePathList:
        FullPath = os.path.join(dataFramePath, filename)
        if pattern.match(FullPath):
            print(f"< User: {email} | Project: {projectName} | {FullPath} 로드 >")
            with open(FullPath, 'r', encoding = 'utf-8') as file:
                OutputMemoryDicsFile = json.load(file)
            OutputMemoryCount = len(OutputMemoryDicsFile)
            break  # 첫 번째 일치하는 파일을 찾으면 반복 종료

        normalizedFilename = unicodedata.normalize('NFC', filename)
        normalizedFullPath = os.path.join(dataFramePath, normalizedFilename)
        if pattern.match(normalizedFullPath):
            print(f"< User: {email} | Project: {projectName} | {normalizedFullPath} 로드 >")
            with open(normalizedFullPath, 'r', encoding = 'utf-8') as file:
                OutputMemoryDicsFile = json.load(file)
            OutputMemoryCount = len(OutputMemoryDicsFile)
            break  # 첫 번째 일치하는 파일을 찾으면 반복 종료

    return OutputMemoryDicsFile, OutputMemoryCount

## 업데이트된 AddOutputMemoryDics 파일 Count 불러오기
def LoadAddOutputMemory(projectName, email, ProcessNum, DataFramePath):
    # 정규 표현식 패턴 정의
    pattern = re.compile(rf"{re.escape(DataFramePath + email + '_' + projectName + '_' + ProcessNum + '_')}addOutputMemoryDics_.*\.json")

    # 문자열 정규화
    DataFramePathNFCNormalized = unicodedata.normalize('NFC', DataFramePath)
    DataFramePathNFDNormalized = unicodedata.normalize('NFD', DataFramePath)

    ## 한글의 유니코드 문제로 인해 일반과 노멀라이즈를 2개로 분리하여 가장 최근 파일찾기 실행
    try:
        DataFramePathList = os.listdir(DataFramePath)
        dataFramePath = DataFramePath
    except:
        try:
            DataFramePathList = os.listdir(DataFramePathNFCNormalized)
            dataFramePath = DataFramePathNFCNormalized
        except:
            DataFramePathList = os.listdir(DataFramePathNFDNormalized)
            dataFramePath = DataFramePathNFDNormalized

    AddOutputMemoryDicsFile = []
    for filename in DataFramePathList:
        normalizedFilename = unicodedata.normalize('NFC', filename)
        FullPath = os.path.join(dataFramePath, normalizedFilename)
        if pattern.match(FullPath):
            print(f"< User: {email} | Project: {projectName} | {FullPath} 로드 >")
            with open(FullPath, 'r', encoding = 'utf-8') as file:
                AddOutputMemoryDicsFile = json.load(file)
            break  # 첫 번째 일치하는 파일을 찾으면 반복 종료

    return AddOutputMemoryDicsFile

## 각 유저별 DataframeFilePaths 찾기
def FindDataframeFilePaths(email, projectName, userStoragePath):
    # 데이터프레임 파일 경로 구성
    expectedFilePath = os.path.join(userStoragePath, f"{email}", projectName, f"{projectName}_audiobook", f"{projectName}_dataframe_audiobook_file")
    normalizedFilePath = unicodedata.normalize('NFC', expectedFilePath)

    # 파일 존재 여부 확인
    if os.path.exists(expectedFilePath):
        # 파일이 존재하면 정규화된 파일 경로 반환
        return expectedFilePath + '/'
    elif os.path.exists(normalizedFilePath):
        # 파일이 존재하면 정규화된 파일 경로 반환
        return normalizedFilePath + '/'
    else:
        # 파일이 존재하지 않으면, 빈 리스트 반환
        return None

## 업데이트된 OutputMemoryDics 파일 저장하기
def SaveOutputMemory(projectName, email, OutputMemoryDics, ProcessNum, DataFramePath):
    # 정규 표현식 패턴 정의
    pattern = re.compile(rf"{re.escape(email + '_' + projectName + '_' + ProcessNum + '_outputMemoryDics_')}.*\.json")
    
    # 문자열 정규화
    DataFramePathNFCNormalized = unicodedata.normalize('NFC', DataFramePath)
    DataFramePathNFDNormalized = unicodedata.normalize('NFD', DataFramePath)

    ## 한글의 유니코드 문제로 인해 일반과 노멀라이즈를 2개로 분리하여 가장 최근 파일찾기 실행
    try:
        try:
            DataFramePathList = os.listdir(DataFramePath)
        except:
            try:
                DataFramePathList = os.listdir(DataFramePathNFCNormalized)
            except:
                DataFramePathList = os.listdir(DataFramePathNFDNormalized)
    except:
        # 갑자기 발생하는 원인 모를 오류를 위해서 0.01초 휴식 후 재시도
        time.sleep(0.01)
        try:
            DataFramePathList = os.listdir(DataFramePath)
        except:
            try:
                DataFramePathList = os.listdir(DataFramePathNFCNormalized)
            except:
                DataFramePathList = os.listdir(DataFramePathNFDNormalized)

    # 일치하는 파일 검색
    matched_file = None
    for filename in DataFramePathList:
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
    with open(OutputMemoryDicsFilename, 'w', encoding = 'utf-8') as file:
        json.dump(OutputMemoryDics, file, ensure_ascii = False, indent = 4)
        
## 업데이트된 AddOutputMemoryDics 파일 저장하기
def SaveAddOutputMemory(projectName, email, AddOutputMemoryDics, ProcessNum, DataFramePath):
    # 정규 표현식 패턴 정의
    pattern = re.compile(rf"{re.escape(email + '_' + projectName + '_' + ProcessNum + '_addOutputMemoryDics_')}.*\.json")
    
    # 문자열 정규화
    DataFramePathNFCNormalized = unicodedata.normalize('NFC', DataFramePath)
    DataFramePathNFDNormalized = unicodedata.normalize('NFD', DataFramePath)

    ## 한글의 유니코드 문제로 인해 일반과 노멀라이즈를 2개로 분리하여 가장 최근 파일찾기 실행
    try:
        try:
            DataFramePathList = os.listdir(DataFramePath)
        except:
            try:
                DataFramePathList = os.listdir(DataFramePathNFCNormalized)
            except:
                DataFramePathList = os.listdir(DataFramePathNFDNormalized)
    except:
        # 갑자기 발생하는 원인 모를 오류를 위해서 0.01초 휴식 후 재시도
        time.sleep(0.01)
        try:
            DataFramePathList = os.listdir(DataFramePath)
        except:
            try:
                DataFramePathList = os.listdir(DataFramePathNFCNormalized)
            except:
                DataFramePathList = os.listdir(DataFramePathNFDNormalized)

    # 일치하는 파일 검색
    matched_file = None
    for filename in DataFramePathList:
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
    with open(AddOutputMemoryDicsFilename, 'w', encoding = 'utf-8') as file:
        json.dump(AddOutputMemoryDics, file, ensure_ascii = False, indent = 4)

###################################################
##### 전체 DataFrame의 MetaData(식별)부분을 업데이트 #####
###################################################
def AddFrameMetaDataToDB(projectName, email):
    project = GetProject(projectName, email)

    project["ProjectName"] = projectName

    SaveProject(projectName, email, project)


#####################################
##### 00_ScriptGen Process #####
#####################################
## 0-1. 1-0 ScriptGen이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedScriptGenToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["ScriptGenFrame"][1] = ExistedDataFrame[1]

    SaveProject(projectName, email, project)

## 0-1. 1-1 ScriptGen의 Scripts(페이지) updateScripts 업데이트 형식
def UpdateScripts(DataFrame, ScriptId, Script):    
    updateScripts = {
        "ScriptId": ScriptId,
        "Script": Script
    }
    
    DataFrame[1]["Scripts"].append(updateScripts)
    DataFrame[0]["ScriptCount"] = ScriptId

    return DataFrame
    
## 0-1. 1-2 ScriptGen의 Scripts(페이지) updateScripts 업데이트
def AddScriptGenBookPagesToDB(DataFrame, ScriptId, Script):

    DataFrame = UpdateScripts(DataFrame, ScriptId, Script)

    return DataFrame

## 0-1. ScriptGen의Count의 가져오기
def ScriptGenCountLoad(projectName, email):
    project = GetProject(projectName, email)

    ScriptCount = project["ScriptGenFrame"][0]["ScriptCount"]
    Completion = project["ScriptGenFrame"][0]["Completion"]
    
    return ScriptCount, Completion
        
## 0-1. 업데이트된 ScriptGen 출력
def UpdatedScriptGen(projectName, email):
    project = GetProject(projectName, email)

    return project["ScriptGenFrame"]

## 0-1. ScriptGenCompletion 업데이트
def ScriptGenCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["ScriptGenFrame"] = DataFrame
    project["ScriptGenFrame"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


#####################################
##### 00_BookPreprocess Process #####
#####################################
## 0-1. 1-0 BookPreprocess이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedBookPreprocessToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["BookPreprocessFrame"][1] = ExistedDataFrame[1]
    
    SaveProject(projectName, email, project)

## 0-1. 1-1 BookPreprocess의 BookPages(페이지) updateBookPages 업데이트 형식
def UpdateBookPreprocessBookPages(DataFrame, PageId, PageElement, Script):    
    updateBookPages = {
        "PageId": PageId,
        "PageElement": PageElement,
        "Script": Script
    }
    
    DataFrame[1]["BookPages"].append(updateBookPages)
    DataFrame[0]["PageCount"] = PageId

    return DataFrame
    
## 0-1. 1-2 BookPreprocess의 BookPages(페이지) updateBookPages 업데이트
def AddBookPreprocessBookPagesToDB(DataFrame, PageId, PageElement, Script):

    DataFrame = UpdateBookPreprocessBookPages(DataFrame, PageId, PageElement, Script)
    
    return DataFrame
        
## 0-1. BookPreprocess의Count의 가져오기
def BookPreprocessCountLoad(projectName, email):
    project = GetProject(projectName, email)

    PageCount = project["BookPreprocessFrame"][0]["PageCount"]
    Completion = project["BookPreprocessFrame"][0]["Completion"]
    
    return PageCount, Completion
        
## 0-1. 업데이트된 BookPreprocess 출력
def UpdatedBookPreprocess(projectName, email):
    project = GetProject(projectName, email)

    return project["BookPreprocessFrame"]

## 0-1. BookPreprocessCompletion 업데이트
def BookPreprocessCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["BookPreprocessFrame"] = DataFrame
    project["BookPreprocessFrame"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)
        
        
##################################
##### 01_IndexDefine Process #####
##################################
## 1. 1-0 IndexFrame이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedIndexFrameToDB(projectName, email, ExistedDataFrame):   
    project = GetProject(projectName, email)
    
    project["IndexFrame"][1] = ExistedDataFrame[1]
        
    SaveProject(projectName, email, project)

## 1. 1-2 IndexFrame의 Body(본문)부분 업데이트 형식
def UpdateIndexTags(DataFrame, IndexId, IndexTag, Index):
    
    updateIndexTags = {
        "IndexId": IndexId,
        "IndexTag": IndexTag,
        "Index": Index
    }
    
    DataFrame[1]["IndexTags"].append(updateIndexTags)
    DataFrame[0]["IndexCount"] = IndexId

    return DataFrame

## 1. 1-3 IndexFrame의 Body(본문)부분 업데이트
def AddIndexFrameBodyToDB(DataFrame, IndexId, IndexTag, Index):   

    DataFrame = UpdateIndexTags(DataFrame, IndexId, IndexTag, Index)
    
    return DataFrame

## 1. IndexFrameCount 가져오기
def IndexFrameCountLoad(projectName, email):

    project = GetProject(projectName, email)
    IndexCount = project["IndexFrame"][0]["IndexCount"]
    Completion = project["IndexFrame"][0]["Completion"]
    
    return IndexCount, Completion
        
## 1. 업데이트된 IndexFrame 출력
def UpdatedIndexFrame(projectName, email):
    project = GetProject(projectName, email)

    return project["IndexFrame"]

## 1. IndexFrameCompletion 업데이트
def IndexFrameCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["IndexFrame"] = DataFrame
    project["IndexFrame"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


##############################################
##### 02-1_DuplicationPreprocess Process #####
##############################################
## 2-1. 1-0 DuplicationPreprocess이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedDuplicationPreprocessToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)
    
    project["DuplicationPreprocessFrame"][1] = ExistedDataFrame[1]
        
    SaveProject(projectName, email, project)

## 2-1. 1-1 DuplicationPreprocess의 Body(본문) updateContextChunks 업데이트 형식
def UpdateDuplicationPreprocessScripts(DataFrame, PreprocessId, Index, Duplication, DuplicationScript):    
    updatePreprocessScripts = {
        "PreprocessId": PreprocessId,
        "Index": Index,
        "Duplication": Duplication,
        "DuplicationScript": DuplicationScript
    }
    
    DataFrame[1]["PreprocessScripts"].append(updatePreprocessScripts)
    DataFrame[0]["PreprocessCount"] = PreprocessId

    return DataFrame
    
## 2-1. 1-2 DuplicationPreprocess의 Body(본문) updateContextChunks 업데이트
def AddDuplicationPreprocessScriptsToDB(DataFrame, PreprocessId, Index, Duplication, DuplicationScript):

    DataFrame = UpdateDuplicationPreprocessScripts(DataFrame, PreprocessId, Index, Duplication, DuplicationScript)
        
    return DataFrame
        
## 2-1. DuplicationPreprocess의Count의 가져오기
def DuplicationPreprocessCountLoad(projectName, email):
    project = GetProject(projectName, email)

    PreprocessCount = project["DuplicationPreprocessFrame"][0]["PreprocessCount"]
    Completion = project["DuplicationPreprocessFrame"][0]["Completion"]
    
    return PreprocessCount, Completion
        
## 2-1. 업데이트된 DuplicationPreprocess 출력
def UpdatedDuplicationPreprocess(projectName, email):
    project = GetProject(projectName, email)

    return project["DuplicationPreprocessFrame"]

## 2-1. DuplicationPreprocessCompletion 업데이트
def DuplicationPreprocessCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["DuplicationPreprocessFrame"] = DataFrame
    project["DuplicationPreprocessFrame"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


################################################
##### 02-2_PronunciationPreprocess Process #####
################################################
## 2-2. 1-0 PronunciationPreprocess이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedPronunciationPreprocessToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["PronunciationPreprocessFrame"][1] = ExistedDataFrame[1]
        
    SaveProject(projectName, email, project)

## 2-2. 1-1 PronunciationPreprocess의 Body(본문) updateContextChunks 업데이트 형식
def UpdatePronunciationPreprocessScripts(DataFrame, PreprocessId, Index, Pronunciation, PronunciationScript):    
    updatePreprocessScripts = {
        "PreprocessId": PreprocessId,
        "Index": Index,
        "Pronunciation": Pronunciation,
        "PronunciationScript": PronunciationScript
    }
    
    DataFrame[1]["PreprocessScripts"].append(updatePreprocessScripts)
    DataFrame[0]["PreprocessCount"] = PreprocessId

    return DataFrame
    
## 2-2. 1-2 PronunciationPreprocess의 Body(본문) updateContextChunks 업데이트
def AddPronunciationPreprocessScriptsToDB(DataFrame, PreprocessId, Index, Pronunciation, PronunciationScript):

    DataFrame = UpdatePronunciationPreprocessScripts(DataFrame, PreprocessId, Index, Pronunciation, PronunciationScript)
        
    return DataFrame
        
## 2-2. PronunciationPreprocess의Count의 가져오기
def PronunciationPreprocessCountLoad(projectName, email):

    project = GetProject(projectName, email)
    PreprocessCount = project["PronunciationPreprocessFrame"][0]["PreprocessCount"]
    Completion = project["PronunciationPreprocessFrame"][0]["Completion"]
    
    return PreprocessCount, Completion
        
## 2-2. 업데이트된 PronunciationPreprocess 출력
def UpdatedPronunciationPreprocess(projectName, email):
    project = GetProject(projectName, email)

    return project["PronunciationPreprocessFrame"]

## 2-2. PronunciationPreprocessCompletion 업데이트
def PronunciationPreprocessCompletionUpdate(projectName, email):
    project = GetProject(projectName, email)

    project["PronunciationPreprocessFrame"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


##############################################
##### 03_BodySplit, IndexTagging Process #####
##############################################
## 3. 1-0 BodyFrame이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedBodyFrameToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["BodyFrame"][1] = ExistedDataFrame[1]
    project["BodyFrame"][2] = ExistedDataFrame[2]
        
    SaveProject(projectName, email, project)
        
## 3. 1-2 BodyFrame의 Body(본문) Body부분 업데이트 형식
def UpdateSplitedBodyScripts(DataFrame, IndexId, IndexTag, Index):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(DataFrame[1]["SplitedBodyScripts"])
    
    updateSplitedBodyScripts = {
        "IndexId": IndexId,
        "IndexTag": IndexTag,
        "Index": Index,
        "BodyId": BodyId,
        "SplitedBodyChunks": []
    }
    
    DataFrame[1]["SplitedBodyScripts"].append(updateSplitedBodyScripts)
    # Count 업데이트
    DataFrame[0]["IndexCount"] = IndexId
    DataFrame[0]["BodyCount"] = BodyId

    return DataFrame

## 3. 1-3 BodyFrame의 Body(본문) Body부분 업데이트
def AddBodyFrameBodyToDB(DataFrame, IndexId, IndexTag, Index):

    DataFrame = UpdateSplitedBodyScripts(DataFrame, IndexId, IndexTag, Index)
        
    return DataFrame

## 3. 2-1 BodyFrame의 Body(본문) TagChunks부분 업데이트 형식
def UpdateSplitedBodyTagChunks(DataFrame, ChunkId, Tag, Chunk):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(DataFrame[1]["SplitedBodyScripts"]) -1
    
    updateSplitedBodyChunks = {
        "ChunkId": ChunkId,
        "Tag": Tag,
        "Chunk":Chunk
    }
    
    DataFrame[1]["SplitedBodyScripts"][BodyId]["SplitedBodyChunks"].append(updateSplitedBodyChunks)
    # Count 업데이트
    DataFrame[0]["ChunkCount"] = ChunkId

    return DataFrame

## 3. 2-2 BodyFrame의 Body(본문) TagChunks부분 업데이트
def AddBodyFrameChunkToDB(DataFrame, ChunkId, Tag, Chunk):

    DataFrame = UpdateSplitedBodyTagChunks(DataFrame, ChunkId, Tag, Chunk)
        
    return DataFrame
        
## 3. 3-1 BodyFrame의 Bodys(부문) Bodys부분 업데이트 형식
def UpdateBodys(DataFrame, ChunkIds, Task, Body, Correction, Character, Context = "None", SFX = "None"):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(DataFrame[2]["Bodys"])
    
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
    
    DataFrame[2]["Bodys"].append(updateBodys)

    return DataFrame
    
## 3. 3-2 BodyFrame의 Bodys(부문) Bodys부분 업데이트
def AddBodyFrameBodysToDB(DataFrame, ChunkIds, Task, Body, Correction, Character, context = "None", sfx = "None"):

    DataFrame = UpdateBodys(DataFrame, ChunkIds, Task, Body, Correction, Character, Context = context, SFX = sfx)
        
    return DataFrame
                
## 3. BodyFrame의Count의 가져오기
def BodyFrameCountLoad(projectName, email):

    project = GetProject(projectName, email)
    IndexCount = project["BodyFrame"][0]["IndexCount"]
    BodyCount = project["BodyFrame"][0]["BodyCount"]
    ChunkCount = project["BodyFrame"][0]["ChunkCount"]
    Completion = project["BodyFrame"][0]["Completion"]
    
    return IndexCount, BodyCount, ChunkCount, Completion
        
## 3. 업데이트된 BodyFrame 출력
def UpdatedBodyFrame(projectName, email):
    project = GetProject(projectName, email)

    return project["BodyFrame"]

## 3. BodyFrameCompletion 업데이트
def BodyFrameCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["BodyFrame"] = DataFrame
    project["BodyFrame"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)
        

##################################################
##### 04_HalfBodySplit, IndexTagging Process #####
##################################################
## 4. 1-0 HalfBodyFrame이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedHalfBodyFrameToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["HalfBodyFrame"][1] = ExistedDataFrame[1]
    project["HalfBodyFrame"][2] = ExistedDataFrame[2]
        
    SaveProject(projectName, email, project)
        
## 4. 1-2 HalfBodyFrame의 Body(본문) Body부분 업데이트 형식
def UpdateSplitedHalfBodyScripts(DataFrame, IndexId, IndexTag, Index):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(DataFrame[1]["SplitedBodyScripts"])
    
    updateSplitedBodyScripts = {
        "IndexId": IndexId,
        "IndexTag": IndexTag,
        "Index": Index,
        "BodyId": BodyId,
        "SplitedBodyChunks": []
    }
    
    DataFrame[1]["SplitedBodyScripts"].append(updateSplitedBodyScripts)
    # Count 업데이트
    DataFrame[0]["IndexCount"] = IndexId
    DataFrame[0]["BodyCount"] = BodyId

    return DataFrame

## 4. 1-3 HalfBodyFrame의 Body(본문) Body부분 업데이트
def AddHalfBodyFrameBodyToDB(DataFrame, IndexId, IndexTag, Index):
    project = GetProject(projectName, email)

    DataFrame = UpdateSplitedHalfBodyScripts(project, IndexId, IndexTag, Index)
        
    return DataFrame

## 4. 2-1 HalfBodyFrame의 Body(본문) TagChunks부분 업데이트 형식
def UpdateSplitedHalfBodyTagChunks(DataFrame, ChunkId, Tag, Chunk):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(DataFrame[1]["SplitedBodyScripts"]) -1
    
    updateSplitedBodyChunks = {
        "ChunkId": ChunkId,
        "Tag": Tag,
        "Chunk":Chunk
    }
    
    DataFrame[1]["SplitedBodyScripts"][BodyId]["SplitedBodyChunks"].append(updateSplitedBodyChunks)
    # Count 업데이트
    DataFrame[0]["ChunkCount"] = ChunkId

    return DataFrame

## 4. 2-2 HalfBodyFrame의 Body(본문) TagChunks부분 업데이트
def AddHalfBodyFrameChunkToDB(DataFrame, ChunkId, Tag, Chunk):

    DataFrame = UpdateSplitedHalfBodyTagChunks(DataFrame, ChunkId, Tag, Chunk)
        
    return DataFrame
        
## 4. 3-1 HalfBodyFrame의 Bodys(부문) Bodys부분 업데이트 형식
def UpdateHalfBodys(DataFrame, ChunkIds, Task, Body, Correction, Character, Context = "None", SFX = "None"):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(DataFrame[2]["Bodys"])
    
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
    
    DataFrame[2]["Bodys"].append(updateBodys)

    return DataFrame
    
## 4. 3-2 HalfBodyFrame의 Bodys(부문) Bodys부분 업데이트
def AddHalfBodyFrameBodysToDB(DataFrame, ChunkIds, Task, Body, Correction, Character, context = "None", sfx = "None"):

    DataFrame = UpdateHalfBodys(DataFrame, ChunkIds, Task, Body, Correction, Character, Context = context, SFX = sfx)
        
    return DataFrame
                
## 4. HalfBodyFrame의Count의 가져오기
def HalfBodyFrameCountLoad(projectName, email):

    project = GetProject(projectName, email)
    IndexCount = project["HalfBodyFrame"][0]["IndexCount"]
    BodyCount = project["HalfBodyFrame"][0]["BodyCount"]
    ChunkCount = project["HalfBodyFrame"][0]["ChunkCount"]
    Completion = project["HalfBodyFrame"][0]["Completion"]
    
    return IndexCount, BodyCount, ChunkCount, Completion
        
## 4. 업데이트된 HalfBodyFrame 출력
def UpdatedHalfBodyFrame(projectName, email):
    project = GetProject(projectName, email)

    return project["HalfBodyFrame"]

## 4. HalfBodyFrameCompletion 업데이트
def HalfBodyFrameCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)
    
    project["HalfBodyFrame"] = DataFrame
    project["HalfBodyFrame"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


####################################
##### 06_CaptionCompletion Process #####
####################################
## 6. 1-0 CaptionCompletion이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedCaptionCompletionToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)
    
    project["CaptionFrame"][1] = ExistedDataFrame[1]
        
    SaveProject(projectName, email, project)

## 6. 1-1 CaptionCompletion의 Body(본문) updateContextChunks 업데이트 형식
def UpdateCaptionCompletions(DataFrame, CaptionId, CaptionTag, CaptionType, Reason, Importance, ChunkIds, SplitedCaptionChunks):    
    updateCaptionCompletions = {
        "CaptionId": CaptionId,
        "CaptionTag": CaptionTag,
        "CaptionType": CaptionType,
        "Reason": Reason,
        "Importance": Importance,
        "ChunkIds": ChunkIds,
        "SplitedCaptionChunks": SplitedCaptionChunks
    }
    
    DataFrame[1]["CaptionCompletions"].append(updateCaptionCompletions)
    DataFrame[0]["CaptionCount"] = CaptionId

    return DataFrame
    
## 6. 1-2 CaptionCompletion의 Body(본문) updateContextChunks 업데이트
def AddCaptionCompletionChunksToDB(DataFrame, CaptionId, CaptionTag, CaptionType, Reason, Importance, ChunkIds, SplitedCaptionChunks):
    
    DataFrame = UpdateCaptionCompletions(DataFrame, CaptionId, CaptionTag, CaptionType, Reason, Importance, ChunkIds, SplitedCaptionChunks)
        
    return DataFrame
        
## 6. CaptionCompletion의Count의 가져오기
def CaptionCompletionCountLoad(projectName, email):

    project = GetProject(projectName, email)
    CaptionCount = project["CaptionFrame"][0]["CaptionCount"]
    Completion = project["CaptionFrame"][0]["Completion"]
    
    return CaptionCount, Completion
        
## 6. 업데이트된 CaptionCompletion 출력
def UpdatedCaptionCompletion(projectName, email):
    project = GetProject(projectName, email)

    return project["CaptionFrame"]

## 6. CaptionCompletionCompletion 업데이트
def CaptionCompletionCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)
    
    project["CaptionFrame"] = DataFrame
    project["CaptionFrame"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


####################################
##### 07_ContextDefine Process #####
####################################
## 7. 1-0 ContextDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedContextDefineToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)
    
    project["ContextDefine"][1] = ExistedDataFrame[1]
        
    SaveProject(projectName, email, project)

## 7. 1-1 ContextDefine의 Body(본문) updateContextChunks 업데이트 형식
def UpdateChunkContexts(DataFrame, ContextChunkId, ChunkId, Chunk, Phrases, Reader, Subject, Purpose, Reason, Question, Importance):    
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
    
    DataFrame[1]["ContextChunks"].append(updateContextChunks)
    DataFrame[0]["ContextChunkCount"] = ContextChunkId

    return DataFrame
    
## 7. 1-2 ContextDefine의 Body(본문) updateContextChunks 업데이트
def AddContextDefineChunksToDB(DataFrame, ContextChunkId, ChunkId, Chunk, Phrases, Reader, Subject, Purpose, Reason, Question, Importance):
    
    DataFrame = UpdateChunkContexts(DataFrame, ContextChunkId, ChunkId, Chunk, Phrases, Reader, Subject, Purpose, Reason, Question, Importance)
        
    return DataFrame
        
## 7. ContextDefine의Count의 가져오기
def ContextDefineCountLoad(projectName, email):

    project = GetProject(projectName, email)
    ContextChunkCount = project["ContextDefine"][0]["ContextChunkCount"]
    ContextCount = project["ContextDefine"][0]["ContextCount"]
    Completion = project["ContextDefine"][0]["Completion"]
    
    return ContextChunkCount, ContextCount, Completion
        
## 7. 업데이트된 ContextDefine 출력
def UpdatedContextDefine(projectName, email):
    project = GetProject(projectName, email)

    return project["ContextDefine"]

## 7. ContextDefineCompletion 업데이트
def ContextDefineCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["ContextDefine"] = DataFrame
    project["ContextDefine"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


########################################
##### 08_ContextCompletion Process #####
########################################
## 8. 1-0 ContextCompletion이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedContextCompletionToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["ContextCompletion"][1] = ExistedDataFrame[1]
    project["ContextCompletion"][2] = ExistedDataFrame[2]
        
    SaveProject(projectName, email, project)

## 8. 1-1 ContextCompletion의 Body(본문) ContextCompletions 업데이트 형식
def UpdateCompletionContexts(DataFrame, ContextChunkId, ChunkId, Chunk, Genre, Gender, Age, Personality, Emotion, Accuracy):    
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
    
    DataFrame[1]["ContextCompletions"].append(updateContextCompletions)
    DataFrame[0]["ContextChunkCount"] = ContextChunkId

    return DataFrame
    
## 8. 1-2 ContextCompletion의 Body(본문) ContextCompletions 업데이트
def AddContextCompletionChunksToDB(DataFrame, ContextChunkId, ChunkId, Chunk, Genre, Gender, Age, Personality, Emotion, Accuracy):

    DataFrame = UpdateCompletionContexts(DataFrame, ContextChunkId, ChunkId, Chunk, Genre, Gender, Age, Personality, Emotion, Accuracy)
        
    return DataFrame
        
## 8. 2-1 ContextCompletion의 Context(부문) ContextTags부분 업데이트 형식
def updateCheckedContextTags(DataFrame, ContextTag, ContextList, Context):
    # 새롭게 생성되는 ContextId는 CheckedContextTags의 Len값과 동일
    ContextId = len(DataFrame[2]["CheckedContextTags"]) -1
    
    ### 실제 테스크시 수정 요망 ###
    updateCheckedContextTags = {
        "ContextId": ContextId,
        "ContextTag": ContextTag,
        "ContextList": ContextList,
        "Context": Context
    }
    
    DataFrame[2]["CheckedContextTags"].append(updateCheckedContextTags)
    DataFrame[0]["ContextCount"] = ContextId

    return DataFrame
    
## 8. 2-2 ContextCompletion의 Context(부문) ContextTags부분 업데이트
def AddContextCompletionCheckedContextTagsToDB(DataFrame, ContextTag, ContextList, Context):

    DataFrame = updateCheckedContextTags(DataFrame, ContextTag, ContextList, Context)
        
    return DataFrame
        
## 8. ContextCompletion의Count의 가져오기
def ContextCompletionCountLoad(projectName, email):

    project = GetProject(projectName, email)
    ContextChunkCount = project["ContextCompletion"][0]["ContextChunkCount"]
    ContextCount = project["ContextCompletion"][0]["ContextCount"]
    Completion = project["ContextCompletion"][0]["Completion"]
    
    return ContextChunkCount, ContextCount, Completion
        
## 8. 업데이트된 ContextCompletion 출력
def UpdatedContextCompletion(projectName, email):
    project = GetProject(projectName, email)
        
    return project["ContextCompletion"]
        
## 8. ContextCompletionCompletion 업데이트
def ContextCompletionCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["ContextCompletion"] = DataFrame
    project["ContextCompletion"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


#####################################
##### 09_WMWMDefine Process #####
#####################################
## 9. 1-0 WMWMDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedWMWMDefineToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["WMWMDefine"][1] = ExistedDataFrame[1]
    project["WMWMDefine"][2] = ExistedDataFrame[2]
        
    SaveProject(projectName, email, project)

## 9. 1-1 WMWMDefine의 Body(본문) WMWMCompletions 업데이트 형식
def UpdateCompletionWMWMs(DataFrame, WMWMChunkId, ChunkId, Chunk, Needs, ReasonOfNeeds, Wisdom, ReasonOfWisdom, Mind, ReasonOfPotentialMind, Wildness, ReasonOfWildness, Accuracy):    
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
    
    DataFrame[1]["WMWMCompletions"].append(updateWMWMCompletions)
    DataFrame[0]["WMWMChunkCount"] = WMWMChunkId

    return DataFrame
    
## 9. 1-2 WMWMDefine의 Body(본문) WMWMCompletions 업데이트
def AddWMWMDefineChunksToDB(DataFrame, WMWMChunkId, ChunkId, Chunk, Needs, ReasonOfNeeds, Wisdom, ReasonOfWisdom, Mind, ReasonOfPotentialMind, Wildness, ReasonOfWildness, Accuracy):

    DataFrame = UpdateCompletionWMWMs(DataFrame, WMWMChunkId, ChunkId, Chunk, Needs, ReasonOfNeeds, Wisdom, ReasonOfWisdom, Mind, ReasonOfPotentialMind, Wildness, ReasonOfWildness, Accuracy)
        
    return DataFrame
        
## 9. 2-1 WMWMDefine의 WMWM(부문) WMWMTags부분 업데이트 형식
def updateWMWMQuerys(DataFrame, WMWMChunkId, ChunkId, Vector, WMWM):
    # 새롭게 생성되는 WMWMId는 WMWMQuerys의 Len값과 동일
    WMWMId = len(DataFrame[2]["WMWMQuerys"]) -1
    
    ### 실제 테스크시 수정 요망 ###
    updateWMWMQuerys = {
        "WMWMChunkId": WMWMChunkId,
        "ChunkId": ChunkId,
        "Vector": Vector,
        "WMWM": WMWM
    }
    
    DataFrame[2]["WMWMQuerys"].append(updateWMWMQuerys)
    DataFrame[0]["WMWMCount"] = WMWMId

    return DataFrame
    
## 9. 2-2 WMWMDefine의 WMWM(부문) WMWMTags부분 업데이트
def AddWMWMDefineWMWMQuerysToDB(DataFrame, WMWMChunkId, ChunkId, Vector, WMWM):

    DataFrame = updateWMWMQuerys(DataFrame, WMWMChunkId, ChunkId, Vector, WMWM)
        
    return DataFrame
        
## 9. WMWMDefine의Count의 가져오기
def WMWMDefineCountLoad(projectName, email):

    project = GetProject(projectName, email)
    WMWMChunkCount = project["WMWMDefine"][0]["WMWMChunkCount"]
    WMWMCount = project["WMWMDefine"][0]["WMWMCount"]
    Completion = project["WMWMDefine"][0]["Completion"]
    
    return WMWMChunkCount, WMWMCount, Completion
        
## 9. 업데이트된 WMWMDefine 출력
def UpdatedWMWMDefine(projectName, email):
    project = GetProject(projectName, email)
        
    return project["WMWMDefine"]
        
## 9. WMWMDefineCompletion 업데이트
def WMWMDefineCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["WMWMDefine"] = DataFrame
    project["WMWMDefine"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


#####################################
##### 10_WMWMMatching Process #####
#####################################
## 10. 1-0 WMWMDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedWMWMMatchingToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["WMWMMatching"][1] = ExistedDataFrame[1]
        
    SaveProject(projectName, email, project)

## 10. 1-1 WMWMMatching의 Body(본문) SplitedChunkContexts 업데이트 형식
def UpdateSplitedChunkContexts(DataFrame, ChunkId, Chunk, Vector, WMWM):    
    updateSplitedChunkContexts = {
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Vector": Vector,
        "WMWM": WMWM
    }
    
    DataFrame[1]["SplitedChunkContexts"].append(updateSplitedChunkContexts)
    DataFrame[0]["WMWMChunkCount"] = ChunkId

    return DataFrame
    
## 10. 1-2 WMWMMatching의 Body(본문) SplitedChunkContexts 업데이트
def AddWMWMMatchingChunksToDB(DataFrame, ChunkId, Chunk, Vector, WMWM):
    
    DataFrame = UpdateSplitedChunkContexts(DataFrame, ChunkId, Chunk, Vector, WMWM)
        
    return DataFrame
        
## 10. 1-3 WMWMMatching의 Body(본문) SplitedBodyContexts 업데이트 형식
def UpdateSplitedBodyContexts(DataFrame, BodyId, Phrases, Vector, WMWM):    
    updateSplitedBodyContexts = {
        "BodyId": BodyId,
        "Phrases": Phrases,
        "Vector": Vector,
        "WMWM": WMWM
    }
    
    DataFrame[1]["SplitedBodyContexts"].append(updateSplitedBodyContexts)
    DataFrame[0]["WMWMBodyCount"] = BodyId

    return DataFrame
    
## 10. 1-4 WMWMMatching의 Body(본문) SplitedBodyContexts 업데이트
def AddWMWMMatchingBODYsToDB(DataFrame, BodyId, Phrases, Vector, WMWM):

    DataFrame = UpdateSplitedBodyContexts(DataFrame, BodyId, Phrases, Vector, WMWM)
        
    return DataFrame
        
## 10. 1-5 WMWMMatching의 Index(본문) SplitedIndexContexts 업데이트 형식
def UpdateSplitedIndexContexts(DataFrame, IndexId, Index, Phrases, Vector, WMWM):    
    updateSplitedIndexContexts = {
        "IndexId": IndexId,
        "Index": Index,
        "Phrases": Phrases,
        "Vector": Vector,
        "WMWM": WMWM
    }
    
    DataFrame[1]["SplitedIndexContexts"].append(updateSplitedIndexContexts)
    DataFrame[0]["WMWMIndexCount"] = IndexId

    return DataFrame
    
## 10. 1-6 WMWMMatching의 Index(본문) SplitedIndexContexts 업데이트
def AddWMWMMatchingIndexsToDB(DataFrame, IndexId, Index, Phrases, Vector, WMWM):

    DataFrame = UpdateSplitedIndexContexts(DataFrame, IndexId, Index, Phrases, Vector, WMWM)
        
    return DataFrame
        
## 10. 1-7 WMWMMatching의 Book(본문) SplitedBookContexts 업데이트 형식
def UpdateBookContexts(DataFrame, BookId, Title, Phrases, Vector, WMWM):    
    updateBookContexts = {
        "BookId": BookId,
        "Title": Title,
        "Phrases": Phrases,
        "Vector": Vector,
        "WMWM": WMWM
    }
    
    DataFrame[1]["BookContexts"].append(updateBookContexts)

    return DataFrame
    
## 10. 1-8 WMWMMatching의 Book(본문) SplitedBookContexts 업데이트
def AddWMWMMatchingBookToDB(DataFrame, BookId, Title, Phrases, Vector, WMWM):

    DataFrame = UpdateBookContexts(DataFrame, BookId, Title, Phrases, Vector, WMWM)
        
    return DataFrame
        
## 10. WMWMMatching의Count의 가져오기
def WMWMMatchingCountLoad(projectName, email):

    project = GetProject(projectName, email)
    WMWMChunkCount = project["WMWMMatching"][0]["WMWMChunkCount"]
    WMWMBodyCount = project["WMWMMatching"][0]["WMWMBodyCount"]
    WMWMIndexCount = project["WMWMMatching"][0]["WMWMIndexCount"]
    Completion = project["WMWMMatching"][0]["Completion"]
    
    return WMWMChunkCount, WMWMBodyCount, WMWMIndexCount, Completion
        
## 10. 업데이트된 WMWMMatching 출력
def UpdatedWMWMMatching(projectName, email):
    project = GetProject(projectName, email)
        
    return project["WMWMMatching"]
        
## 10. WMWMMatchingCompletion 업데이트
def WMWMMatchingCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["WMWMMatching"] = DataFrame
    project["WMWMMatching"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


######################################
##### 11_CharacterDefine Process #####
######################################
## 11. 1-0 CharacterDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedCharacterDefineToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["CharacterDefine"][1] = ExistedDataFrame[1]
        
    SaveProject(projectName, email, project)
        
## 11. 1-1 CharacterDefine의 Body(본문) updateCharacterChunks 업데이트 형식
def UpdateChunkCharacters(DataFrame, CharacterChunkId, ChunkId, Chunk, Character, Type, Gender, Age, Emotion, Role, Listener):    
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
    
    DataFrame[1]["CharacterChunks"].append(updateCharacterChunks)
    DataFrame[0]["CharacterChunkCount"] = CharacterChunkId

    return DataFrame
    
## 11. 1-2 CharacterDefine의 Body(본문) updateCharacterChunks 업데이트
def AddCharacterDefineChunksToDB(DataFrame, CharacterChunkId, ChunkId, Chunk, Character, Type, Gender, Age, Emotion, Role, Listener):

    DataFrame = UpdateChunkCharacters(DataFrame, CharacterChunkId, ChunkId, Chunk, Character, Type, Gender, Age, Emotion, Role, Listener)
        
    return DataFrame

## 11. CharacterDefine의Count의 가져오기
def CharacterDefineCountLoad(projectName, email):

    project = GetProject(projectName, email)
    CharacterChunkCount = project["CharacterDefine"][0]["CharacterChunkCount"]
    CharacterCount = project["CharacterDefine"][0]["CharacterCount"]
    Completion = project["CharacterDefine"][0]["Completion"]
    
    return CharacterChunkCount, CharacterCount, Completion
        
## 11. 업데이트된 CharacterDefine 출력
def UpdatedCharacterDefine(projectName, email):
    project = GetProject(projectName, email)

    return project["CharacterDefine"]

## 11. CharacterDefineCompletion 업데이트
def CharacterDefineCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["CharacterDefine"] = DataFrame
    project["CharacterDefine"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


##########################################
##### 12_CharacterCompletion Process #####
##########################################
## 12. 1-0 CharacterCompletion이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedCharacterCompletionToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["CharacterCompletion"][1] = ExistedDataFrame[1]
    project["CharacterCompletion"][2] = ExistedDataFrame[2]
        
    SaveProject(projectName, email, project)
        
## 12. 1-1 CharacterCompletion의 Body(본문) CharacterCompletions 업데이트 형식
def UpdateCompletionCharacters(DataFrame, CharacterChunkId, ChunkId, Chunk, Character, MainCharacter, AuthorRelationship, Context, Voice):    
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
    
    DataFrame[1]["CharacterCompletions"].append(updateCharacterCompletions)
    DataFrame[0]["CharacterChunkCount"] = CharacterChunkId

    return DataFrame

## 12. 1-2 CharacterCompletion의 Body(본문) CharacterCompletions 업데이트
def AddCharacterCompletionChunksToDB(DataFrame, CharacterChunkId, ChunkId, Chunk, Character, MainCharacter, AuthorRelationship, Context, Voice):

    DataFrame = UpdateCompletionCharacters(DataFrame, CharacterChunkId, ChunkId, Chunk, Character, MainCharacter, AuthorRelationship, Context, Voice)
        
    return DataFrame
        
## 12. 2-1 CharacterCompletion의 Character(부문) CharacterTags부분 업데이트 형식
def UpdateCheckedCharacterTags(DataFrame, CharacterTag, Gender, Age, Emotion, Frequency, MainCharacterList):
    # 새롭게 생성되는 CharacterId는 CharacterTags의 Len값과 동일
    CharacterId = len(DataFrame[2]["CheckedCharacterTags"])
    
    ### 실제 테스크시 수정 요망 ###
    updateCheckedCharacterTags = {
        "CharacterId": CharacterId,
        "CharacterTag": CharacterTag,
        "Gender": Gender,
        "Age": Age,
        "Emotion": Emotion,
        "Frequency": Frequency,
        "MainCharacterList": MainCharacterList
    }
    
    DataFrame[2]["CheckedCharacterTags"].append(updateCheckedCharacterTags)
    DataFrame[0]["CharacterCount"] = CharacterId

    return DataFrame
    
## 12. 2-2 CharacterCompletion의 Character(부문) CharacterTags부분 업데이트
def AddCharacterCompletionCheckedCharacterTagsToDB(DataFrame, CharacterTag, Gender, Age, Emotion, Frequency, MainCharacterList):

    DataFrame = UpdateCheckedCharacterTags(DataFrame, CharacterTag, Gender, Age, Emotion, Frequency, MainCharacterList)
        
    return DataFrame
        
## 12. CharacterCompletion의Count의 가져오기
def CharacterCompletionCountLoad(projectName, email):

    project = GetProject(projectName, email)
    CharacterChunkCount = project["CharacterCompletion"][0]["CharacterChunkCount"]
    CharacterCount = project["CharacterCompletion"][0]["CharacterCount"]
    Completion = project["CharacterCompletion"][0]["Completion"]
    
    return CharacterChunkCount, CharacterCount, Completion
        
## 12. 업데이트된 CharacterCompletion 출력
def UpdatedCharacterCompletion(projectName, email):
    project = GetProject(projectName, email)
        
    return project["CharacterCompletion"]
        
## 12. CharacterCompletionCompletion 업데이트
def CharacterCompletionCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["CharacterCompletion"] = DataFrame
    project["CharacterCompletion"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


####################################
##### 14_SoundMatching Process #####
####################################
## 14. 1-0 SoundMatching이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedSoundMatchingToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["SoundMatching"][1] = ExistedDataFrame[1]
        
    SaveProject(projectName, email, project)
        
## 14. 1-1 SoundMatching의 Body(본문) SoundSplitedBodys 업데이트 형식
def UpdateSoundSplitedIndexs(DataFrame, IndexId, Sounds):
    updateSoundSplitedIndexs = {
        "IndexId": IndexId,
        "Sounds": Sounds
    }
    
    DataFrame[1]["SoundSplitedIndexs"].append(updateSoundSplitedIndexs)
    DataFrame[0]["IndexCount"] = IndexId

    return DataFrame
    
## 14. 1-2 SoundMatching의 Body(본문) SoundSplitedBodys 업데이트
def AddSoundSplitedIndexsToDB(DataFrame, IndexId, Sounds):

    DataFrame = UpdateSoundSplitedIndexs(DataFrame, IndexId, Sounds)
        
    return DataFrame
        
## 14. SoundMatching의Count의 가져오기
def SoundMatchingCountLoad(projectName, email):

    project = GetProject(projectName, email)
    BodyCount = project["SoundMatching"][0]["BodyCount"]
    Completion = project["SoundMatching"][0]["Completion"]
    
    return BodyCount, Completion
        
## 14. 업데이트된 SoundMatching 출력
def UpdatedSoundMatching(projectName, email):
    project = GetProject(projectName, email)
        
    return project["SoundMatching"]
        
## 14. SoundMatchingCompletion 업데이트
def SoundMatchingCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["SoundMatching"] = DataFrame
    project["SoundMatching"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


###################################
##### 15_SFXMatching Process #####
###################################
## 15. 1-0 SFXMatching이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedSFXMatchingToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["SFXMatching"][1] = ExistedDataFrame[1]
        
    SaveProject(projectName, email, project)
        
## 15. 1-1 SFXMatching의 Body(본문) SFXSplitedBodys 업데이트 형식
def UpdateSFXSplitedBodys(DataFrame, SFXSplitedBodyChunks):
    BodyId = len(DataFrame[1]["SFXSplitedBodys"])
    
    updateSFXSplitedBodys = {
        "BodyId": BodyId,
        "SFXSplitedBodyChunks": SFXSplitedBodyChunks
    }
    
    DataFrame[1]["SFXSplitedBodys"].append(updateSFXSplitedBodys)
    DataFrame[0]["BodyCount"] = BodyId

    return DataFrame
    
## 15. 1-2 SFXMatching의 Body(본문) SFXSplitedBodys 업데이트
def AddSFXSplitedBodysToDB(DataFrame, SFXSplitedBodyChunks):

    DataFrame = UpdateSFXSplitedBodys(DataFrame, SFXSplitedBodyChunks)
        
    return DataFrame
        
## 15. SFXMatching의Count의 가져오기
def SFXMatchingCountLoad(projectName, email):

    project = GetProject(projectName, email)
    BodyCount = project["SFXMatching"][0]["BodyCount"]
    Completion = project["SFXMatching"][0]["Completion"]
    
    return BodyCount, Completion
        
## 15. 업데이트된 SFXMatching 출력
def UpdatedSFXMatching(projectName, email):
    project = GetProject(projectName, email)
        
    return project["SFXMatching"]
        
## 15. SFXMatchingCompletion 업데이트
def SFXMatchingCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["SFXMatching"] = DataFrame
    project["SFXMatching"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


###################################
##### 21_CorrectionKo Process #####
###################################
## 21. 1-0 CorrectionKo이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedCorrectionKoToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["CorrectionKo"][1] = ExistedDataFrame[1]
        
    SaveProject(projectName, email, project)
        
## 21. 1-1 CorrectionKo의 Body(본문) CorrectionKoSplitedBodys 업데이트 형식
def UpdateCorrectionKoSplitedBodys(DataFrame):
    BodyId = len(DataFrame[1]["CorrectionKoSplitedBodys"])
    
    updateCorrectionKoSplitedBodys = {
        "BodyId": BodyId,
        "CorrectionKoSplitedBodyChunks": []
    }
    
    DataFrame[1]["CorrectionKoSplitedBodys"].append(updateCorrectionKoSplitedBodys)
    DataFrame[0]["BodyCount"] = BodyId

    return DataFrame
    
## 21. 1-2 CorrectionKo의 Body(본문) CorrectionKoSplitedBodys 업데이트
def AddCorrectionKoSplitedBodysToDB(projectName, email, DataFrame):

    DataFrame = UpdateCorrectionKoSplitedBodys(DataFrame)
        
    return DataFrame
        
## 21. 2-1 CorrectionKo의 Body(본문) CorrectionKoChunk 업데이트 형식
def UpdateCorrectionKoSplitedChunks(DataFrame, ChunkId, Tag, ChunkTokens):
    # 새롭게 생성되는 BodyId는 CorrectionKoSplitedBodys의 Len값과 동일
    BodyId = len(DataFrame[1]["CorrectionKoSplitedBodys"]) -1
    
    updateCorrectionKoChunkTokens = {
        "ChunkId": ChunkId,
        "Tag": Tag,
        "CorrectionKoChunkTokens": ChunkTokens
    }
    
    DataFrame[1]["CorrectionKoSplitedBodys"][BodyId]["CorrectionKoSplitedBodyChunks"].append(updateCorrectionKoChunkTokens)
    DataFrame[0]["BodyCount"] = BodyId
    # Count 업데이트
    DataFrame[0]["ChunkCount"] = ChunkId

    return DataFrame
    
## 21. 2-2 CorrectionKo의 Body(본문) CorrectionKoChunk 업데이트
def AddCorrectionKoChunksToDB(DataFrame, ChunkId, Tag, ChunkTokens):

    DataFrame = UpdateCorrectionKoSplitedChunks(DataFrame, ChunkId, Tag, ChunkTokens)
        
    return DataFrame
        
## 21. CorrectionKo의Count의 가져오기
def CorrectionKoCountLoad(projectName, email):

    project = GetProject(projectName, email)
    BodyCount = project["CorrectionKo"][0]["BodyCount"]
    ChunkCount = project["CorrectionKo"][0]["ChunkCount"]
    Completion = project["CorrectionKo"][0]["Completion"]
    
    return BodyCount, ChunkCount, Completion
        
## 21. 업데이트된 CorrectionKo 출력
def UpdatedCorrectionKo(projectName, email):
    project = GetProject(projectName, email)
        
    return project["CorrectionKo"]
        
## 21. CorrectionKoCompletion 업데이트
def CorrectionKoCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["CorrectionKo"] = DataFrame
    project["CorrectionKo"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)


#############################################
##### 26_SelectionGenerationKo Process #####
#############################################
## 26. 1-0 SelectionGenerationKo이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedSelectionGenerationKoToDB(projectName, email, ExistedDataFrame):
    project = GetProject(projectName, email)

    project["SelectionGenerationKo"][1] = ExistedDataFrame[1]
        
    SaveProject(projectName, email, project)

## 26. 1-1 SelectionGenerationKo의 Body(본문) SelectionGenerationKoSplitedBodys 업데이트 형식
def UpdateSelectionGenerationKoBookContext(DataFrame, SelectionGenerationKoBookContext):
    
    DataFrame[1]["SelectionGenerationKoBookContext"].append(SelectionGenerationKoBookContext)

    return DataFrame
    
## 26. 1-2 SelectionGenerationKo의 Body(본문) SelectionGenerationKoSplitedBodys 업데이트
def AddSelectionGenerationKoBookContextToDB(DataFrame, SelectionGenerationKoBookContext):

    DataFrame = UpdateSelectionGenerationKoBookContext(DataFrame, SelectionGenerationKoBookContext)
        
    return DataFrame

## 26. 1-1 SelectionGenerationKo의 Body(본문) SelectionGenerationKoSplitedBodys 업데이트 형식
def UpdateSelectionGenerationKoSplitedIndexs(DataFrame, IndexId, IndexTag, Index, IndexContext, Music, Sound, SelectionGenerationKoSplitedBodys):
    
    updateSelectionGenerationKoSplitedIndex = {
        "IndexId": IndexId,
        "IndexTag": IndexTag,
        "Index": Index,
        "IndexContext": IndexContext,
        "Music": Music,
        "Sound": Sound,
        "SelectionGenerationKoSplitedBodys": SelectionGenerationKoSplitedBodys
    }
    
    DataFrame[1]["SelectionGenerationKoSplitedIndexs"].append(updateSelectionGenerationKoSplitedIndex)
    DataFrame[0]["IndexCount"] = IndexId

    return DataFrame
    
## 26. 1-2 SelectionGenerationKo의 Body(본문) SelectionGenerationKoSplitedBodys 업데이트
def AddSelectionGenerationKoSplitedIndexsToDB(DataFrame, IndexId, IndexTag, Index, IndexContext, Music, Sound, SelectionGenerationKoSplitedBodys):

    DataFrame = UpdateSelectionGenerationKoSplitedIndexs(DataFrame, IndexId, IndexTag, Index, IndexContext, Music, Sound, SelectionGenerationKoSplitedBodys)
        
    return DataFrame
        
## 26. SelectionGenerationKo의Count의 가져오기
def SelectionGenerationKoCountLoad(projectName, email):

    project = GetProject(projectName, email)
    IndexCount = project["SelectionGenerationKo"][0]["IndexCount"]
    Completion = project["SelectionGenerationKo"][0]["Completion"]
    
    return IndexCount, Completion
        
## 26. 업데이트된 SelectionGenerationKo 출력
def UpdatedSelectionGenerationKo(projectName, email):
    project = GetProject(projectName, email)
        
    return project["SelectionGenerationKo"]
        
## 26. SelectionGenerationKoCompletion 업데이트
def SelectionGenerationKoCompletionUpdate(projectName, email, DataFrame):
    project = GetProject(projectName, email)

    project["SelectionGenerationKo"] = DataFrame
    project["SelectionGenerationKo"][0]["Completion"] = "Yes"

    SaveProject(projectName, email, project)

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    process = 'IndexDefinePreprocess'
    userStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"
    DataFramePath = FindDataframeFilePaths(email, projectName, userStoragePath)
    RawDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s111_RawDataSet/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################