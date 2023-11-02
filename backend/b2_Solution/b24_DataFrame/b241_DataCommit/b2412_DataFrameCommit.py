import sys
sys.path.append("/yaas")

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import Project
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b23_Project.b231_GetDBtable import GetProject
from backend.b2_Solution.b23_Project.b232_ProjectCommit import GetProjectDataPath, LoadJsonFrame

###################################################
##### 전체 DataFrame의 MetaData(식별)부분을 업데이트 #####
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

###############################
##### IndexDefine Process #####
## 1. 1-1 IndexFrame이 이미 ExistedFrame으로 존재할때 업데이트
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

###########################################
##### BodySplit, IndexTagging Process #####
## 2. 1-1 BodyFrame이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedBodyFrameToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.BodyFrame[1] = ExistedDataFrame[1]
        project.BodyFrame[2] = ExistedDataFrame[2]
        
        flag_modified(project, "BodyFrame")
        
        db.add(project)
        db.commit()
        
## 2. 1-2 BodyFrame의 Body(본문) Body부분 업데이트 형식
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

## 2. 1-3 BodyFrame의 Body(본문) Body부분 업데이트
def AddBodyFrameBodyToDB(projectName, email, IndexId, IndexTag, Index):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSplitedBodyScripts(project, IndexId, IndexTag, Index)
        
        flag_modified(project, "BodyFrame")
        
        db.add(project)
        db.commit()

## 2. 2-1 BodyFrame의 Body(본문) TagChunks부분 업데이트 형식
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

## 2. 2-2 BodyFrame의 Body(본문) TagChunks부분 업데이트
def AddBodyFrameChunkToDB(projectName, email, ChunkId, Tag, Chunk):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateSplitedBodyTagChunks(project, ChunkId, Tag, Chunk)
        
        flag_modified(project, "BodyFrame")
        
        db.add(project)
        db.commit()
        
## 2. 3-1 BodyFrame의 Bodys(부문) Bodys부분 업데이트 형식
def UpdateBodys(project, Task, Body, Character):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    BodyId = len(project.BodyFrame[2]["Bodys"])
    
    updateBodys = {
        "BodyId": BodyId,
        "Task": Task,
        "Body": Body,
        "Character": Character
    }
    
    project.BodyFrame[2]["Bodys"].append(updateBodys)
    
## 2. 3-2 BodyFrame의 Bodys(부문) Bodys부분 업데이트
def AddBodyFrameBodysToDB(projectName, email, Task, Body, Character):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateBodys(project, Task, Body, Character)
        
        flag_modified(project, "BodyFrame")
        
        db.add(project)
        db.commit()
        
## 2. BodyFrame의Count의 가져오기
def BodyFrameCountLoad(projectName, email):

    project = GetProject(projectName, email)
    IndexCount = project.BodyFrame[0]["IndexCount"]
    BodyCount = project.BodyFrame[0]["BodyCount"]
    ChunkCount = project.BodyFrame[0]["ChunkCount"]
    Completion = project.BodyFrame[0]["Completion"]
    
    return IndexCount, BodyCount, ChunkCount, Completion

## 2. BodyFrame의 초기화
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
        
## 2. 업데이트된 BodyFrame 출력
def UpdatedBodyFrame(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)

    return project.BodyFrame

## 2. BodyFrameCompletion 업데이트
def BodyFrameCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.BodyFrame[0]["Completion"] = "Yes"

        flag_modified(project, "BodyFrame")

        db.add(project)
        db.commit()

###############################
##### BodySummary Process #####
## 3. 1-1 SummaryBodyFrame이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedSummaryBodyFrameToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.SummaryBodyFrame[1] = ExistedDataFrame[1]
        
        flag_modified(project, "SummaryBodyFrame")
        
        db.add(project)
        db.commit()
        
## 3. 1-2 SummaryBodyFrame의 BodySummaryScripts(본문)부분 업데이트 형식
def UpdateSummaryBodyTags(project, BodyId, Summary, BodySummaryScript):
    
    updateBodySummaryScripts = {
        "BodyId": BodyId,
        "Summary": Summary,
        "BodySummaryScript": BodySummaryScript
    }
    
    project.SummaryBodyFrame[1]["BodySummaryScripts"].append(updateBodySummaryScripts)
    # Count 업데이트
    project.SummaryBodyFrame[0]["BodyCount"] = BodyId
    
## 3. 1-3 SummaryBodyFrame의 SummaryBodyFrame(본문)부분 업데이트
def AddSummaryBodyFrameBodyToDB(projectName, email, BodyId, Summary, BodySummaryScript):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        UpdateSummaryBodyTags(project, BodyId, Summary, BodySummaryScript)
        
        flag_modified(project, "SummaryBodyFrame")
        
        db.add(project)
        db.commit()
        
## 3. SummaryBodyFrameCount의 가져오기
def SummaryBodyFrameCountLoad(projectName, email):

    project = GetProject(projectName, email)
    BodyCount = project.SummaryBodyFrame[0]["BodyCount"]
    Completion = project.SummaryBodyFrame[0]["Completion"]
    
    return BodyCount, Completion

## 3. SummaryBodyFrame의 초기화
def InitSummaryBodyFrame(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.SummaryBodyFrame[0]["BodyCount"] = 0
        project.SummaryBodyFrame[0]["Completion"] = "No"
        project.SummaryBodyFrame[1] = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-05_SummaryBodyFrame.json")[1]
        
        flag_modified(project, "SummaryBodyFrame")
        
        db.add(project)
        db.commit()

## 3. 업데이트된 SummaryBodyFrame 출력
def UpdatedSummaryBodyFrame(projectName, email):
    with get_db() as db:
        project = GetProject(projectName, email)

    return project.SummaryBodyFrame

## 3. SummaryBodyFrameCompletion 업데이트
def SummaryBodyFrameCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.SummaryBodyFrame[0]["Completion"] = "Yes"

        flag_modified(project, "SummaryBodyFrame")

        db.add(project)
        db.commit()

#######################################
##### BodyCharacterDefine Process #####
## 4. 1-1 BodyCharacterDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedBodyCharacterDefineToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.BodyCharacterDefine[1] = ExistedDataFrame[1]
        project.BodyCharacterDefine[2] = ExistedDataFrame[2]
        
        flag_modified(project, "BodyCharacterDefine")
        
        db.add(project)
        db.commit()
        
## 4. 1-1 BodyCharacterDefine의 Body(본문) BodyCharacters부분 업데이트 형식
def UpdateChunkCharacters(project, CharacterChunkId, ChunkId, Chunk, Character, Type, Role, Listener):    
    updateCharacterChunks = {
        "CharacterChunkId": CharacterChunkId,
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Character": Character,
        "Type": Type,
        "Role": Role,
        "Listener": Listener
    }
    
    project.BodyCharacterDefine[1]["CharacterChunks"].append(updateCharacterChunks)
    project.BodyCharacterDefine[0]["CharacterChunkCount"] = CharacterChunkId
    
## 4. 1-2 BodyCharacterDefine의 Body(본문) BodyCharacters부분 업데이트
def AddBodyCharacterDefineChunksToDB(projectName, email, CharacterChunkId, ChunkId, Chunk, Character, Type, Role, Listener):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateChunkCharacters(project, CharacterChunkId, ChunkId, Chunk, Character, Type, Role, Listener)
        
        flag_modified(project, "BodyCharacterDefine")
        
        db.add(project)
        db.commit()

## 4. 2-1 BodyCharacterDefine의 Character(부문) CharacterTags부분 업데이트 형식
def UpdateCharacterTags(project, CharacterTag, CharacterList, Character):
    # 새롭게 생성되는 BodyId는 SplitedBodyScripts의 Len값과 동일
    CharacterId = len(project.BodyCharacterDefine[2]["CharacterTags"]) -1
    
    updateCharacterTags = {
        "CharacterId": CharacterId,
        "CharacterTag": CharacterTag,
        "CharacterList": CharacterList,
        "Character": Character
    }
    
    project.BodyCharacterDefine[2]["CharacterTags"].append(updateCharacterTags)
    project.BodyCharacterDefine[0]["CharacterCount"] = CharacterId
    
## 4. 2-2 BodyCharacterDefine의 Character(부문) CharacterTags부분 업데이트
def AddBodyCharacterDefineCharacterTagsToDB(projectName, email, CharacterTag, CharacterList, Character):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateCharacterTags(project, CharacterTag, CharacterList, Character)
        
        flag_modified(project, "BodyCharacterDefine")
        
        db.add(project)
        db.commit()

## 4. BodyCharacterDefine의Count의 가져오기
def BodyCharacterDefineCountLoad(projectName, email):

    project = GetProject(projectName, email)
    CharacterChunkCount = project.BodyCharacterDefine[0]["CharacterChunkCount"]
    CharacterCount = project.BodyCharacterDefine[0]["CharacterCount"]
    Completion = project.BodyCharacterDefine[0]["Completion"]
    
    return CharacterChunkCount, CharacterCount, Completion

## 4. BodyCharacterDefine의 초기화
def InitBodyCharacterDefine(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.BodyCharacterDefine[0]["CharacterChunkCount"] = 0
        project.BodyCharacterDefine[0]["CharacterCount"] = 0
        project.BodyCharacterDefine[0]["Completion"] = "No"
        project.BodyCharacterDefine[1] = LoadJsonFrame(ProjectDataPath + "/b532_BodyDefine/b532-01_BodyCharacterDefine.json")[1]
        project.BodyCharacterDefine[2] = LoadJsonFrame(ProjectDataPath + "/b532_BodyDefine/b532-01_BodyCharacterDefine.json")[2]
        
        flag_modified(project, "BodyCharacterDefine")
        
        db.add(project)
        db.commit()
        
## 4. 업데이트된 BodyCharacterDefine 출력
def UpdatedBodyCharacterDefine(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)

    return project.BodyCharacterDefine

## 4. BodyCharacterDefineCompletion 업데이트
def BodyCharacterDefineCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.BodyCharacterDefine[0]["Completion"] = "Yes"

        flag_modified(project, "BodyCharacterDefine")

        db.add(project)
        db.commit()

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    process = 'IndexDefinePreprocess'
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    #########################################################################