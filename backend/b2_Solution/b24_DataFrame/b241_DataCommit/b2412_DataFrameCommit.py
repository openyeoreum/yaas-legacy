import sys
sys.path.append("/yaas")

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import Project
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject
from backend.b2_Solution.b23_Project.b231_ProjectCommit import GetProjectDataPath, LoadJsonFrame


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
##### 02_BodySplit, IndexTagging Process #####
##############################################
## 2. 1-0 BodyFrame이 이미 ExistedFrame으로 존재할때 업데이트
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


##################################
##### 06_BodySummary Process #####
##################################
## 6. 1-0 SummaryBodyFrame이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedSummaryBodyFrameToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.SummaryBodyFrame[1] = ExistedDataFrame[1]
        
        flag_modified(project, "SummaryBodyFrame")
        
        db.add(project)
        db.commit()
        
## 6. 1-2 SummaryBodyFrame의 BodySummaryScripts(본문)부분 업데이트 형식
def UpdateSummaryBodyTags(project, BodyId, Summary, BodySummaryScript):
    
    updateBodySummaryScripts = {
        "BodyId": BodyId,
        "Summary": Summary,
        "BodySummaryScript": BodySummaryScript
    }
    
    project.SummaryBodyFrame[1]["BodySummaryScripts"].append(updateBodySummaryScripts)
    # Count 업데이트
    project.SummaryBodyFrame[0]["BodyCount"] = BodyId
    
## 6. 1-3 SummaryBodyFrame의 SummaryBodyFrame(본문)부분 업데이트
def AddSummaryBodyFrameBodyToDB(projectName, email, BodyId, Summary, BodySummaryScript):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        UpdateSummaryBodyTags(project, BodyId, Summary, BodySummaryScript)
        
        flag_modified(project, "SummaryBodyFrame")
        
        db.add(project)
        db.commit()
        
## 6. SummaryBodyFrameCount의 가져오기
def SummaryBodyFrameCountLoad(projectName, email):

    project = GetProject(projectName, email)
    BodyCount = project.SummaryBodyFrame[0]["BodyCount"]
    Completion = project.SummaryBodyFrame[0]["Completion"]
    
    return BodyCount, Completion

## 6. SummaryBodyFrame의 초기화
def InitSummaryBodyFrame(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.SummaryBodyFrame[0]["BodyCount"] = 0
        project.SummaryBodyFrame[0]["Completion"] = "No"
        project.SummaryBodyFrame[1] = LoadJsonFrame(ProjectDataPath + "/b531_Script/b531-06_SummaryBodyFrame.json")[1]
        
        flag_modified(project, "SummaryBodyFrame")
        
        db.add(project)
        db.commit()

## 6. 업데이트된 SummaryBodyFrame 출력
def UpdatedSummaryBodyFrame(projectName, email):
    with get_db() as db:
        project = GetProject(projectName, email)

    return project.SummaryBodyFrame

## 6. SummaryBodyFrameCompletion 업데이트
def SummaryBodyFrameCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.SummaryBodyFrame[0]["Completion"] = "Yes"

        flag_modified(project, "SummaryBodyFrame")

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
def UpdateChunkContexts(project, ContextChunkId, ChunkId, Chunk, Reader, Purpose, Subject, Phrases, Importance):    
    updateContextChunks = {
        "ContextChunkId": ContextChunkId,
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Reader": Reader,
        "Purpose": Purpose,
        "Subject": Subject,
        "Phrases": Phrases,
        "Importance": Importance
    }
    
    project.ContextDefine[1]["ContextChunks"].append(updateContextChunks)
    project.ContextDefine[0]["ContextChunkCount"] = ContextChunkId
    
## 7. 1-2 ContextDefine의 Body(본문) updateContextChunks 업데이트
def AddContextDefineChunksToDB(projectName, email, ContextChunkId, ChunkId, Chunk, Reader, Purpose, Subject, Phrases, Importance):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateChunkContexts(project, ContextChunkId, ChunkId, Chunk, Reader, Purpose, Subject, Phrases, Importance)
        
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

## 8. 1-1 ContextCompletion의 Body(본문) ContextCompeletions 업데이트 형식
def UpdateCompeletionContexts(project, ContextChunkId, ChunkId, Chunk, Genre, Gender, Age, Personality, Emotion, Importance):    
    updateContextCompeletions = {
        "ContextChunkId": ContextChunkId,
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Genre": Genre,
        "Gender": Gender,
        "Age": Age,
        "Personality": Personality,
        "Emotion": Emotion,
        "Importance": Importance
    }
    
    project.ContextCompletion[1]["ContextCompeletions"].append(updateContextCompeletions)
    project.ContextCompletion[0]["ContextChunkCount"] = ContextChunkId
    
## 8. 1-2 ContextCompletion의 Body(본문) ContextCompeletions 업데이트
def AddContextCompletionChunksToDB(projectName, email, ContextChunkId, ChunkId, Chunk, Genre, Gender, Age, Personality, Emotion, Importance):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateCompeletionContexts(project, ContextChunkId, ChunkId, Chunk, Genre, Gender, Age, Personality, Emotion, Importance)
        
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
##### 09_NCEMDefine Process #####
#####################################
## 9. 1-0 NCEMDefine이 이미 ExistedFrame으로 존재할때 업데이트
def AddExistedNCEMDefineToDB(projectName, email, ExistedDataFrame):
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.NCEMDefine[1] = ExistedDataFrame[1]
        project.NCEMDefine[2] = ExistedDataFrame[2]
        
        flag_modified(project, "NCEMDefine")
        
        db.add(project)
        db.commit()

## 9. 1-1 NCEMDefine의 Body(본문) NCEMCompeletions 업데이트 형식
def UpdateCompeletionNCEMs(project, NCEMChunkId, ChunkId, Chunk, Domain, Needs, CVC, PotentialEnergy, Accuracy):    
    updateNCEMCompeletions = {
        "NCEMChunkId": NCEMChunkId,
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Domain": Domain,
        "Needs": Needs,
        "CVC": CVC,
        "PotentialEnergy": PotentialEnergy,
        "Accuracy": Accuracy
    }
    
    project.NCEMDefine[1]["NCEMCompeletions"].append(updateNCEMCompeletions)
    project.NCEMDefine[0]["NCEMChunkCount"] = NCEMChunkId
    
## 9. 1-2 NCEMDefine의 Body(본문) NCEMCompeletions 업데이트
def AddNCEMDefineChunksToDB(projectName, email, NCEMChunkId, ChunkId, Chunk, Domain, Needs, CVC, PotentialEnergy, Accuracy):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateCompeletionNCEMs(project, NCEMChunkId, ChunkId, Chunk, Domain, Needs, CVC, PotentialEnergy, Accuracy)
        
        flag_modified(project, "NCEMDefine")
        
        db.add(project)
        db.commit()
        
## 9. 2-1 NCEMDefine의 NCEM(부문) NCEMTags부분 업데이트 형식
def updateCheckedNCEMTags(project, NCEMTag, NCEMList, NCEM):
    # 새롭게 생성되는 NCEMId는 CheckedNCEMTags의 Len값과 동일
    NCEMId = len(project.NCEMDefine[2]["CheckedNCEMTags"]) -1
    
    ### 실제 테스크시 수정 요망 ###
    updateCheckedNCEMTags = {
        "NCEMId": NCEMId,
        "NCEMTag": NCEMTag,
        "NCEMList": NCEMList,
        "NCEM": NCEM
    }
    
    project.NCEMDefine[2]["CheckedNCEMTags"].append(updateCheckedNCEMTags)
    project.NCEMDefine[0]["NCEMCount"] = NCEMId
    
## 9. 2-2 NCEMDefine의 NCEM(부문) NCEMTags부분 업데이트
def AddNCEMDefineCheckedNCEMTagsToDB(projectName, email, NCEMTag, NCEMList, NCEM):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        updateCheckedNCEMTags(project, NCEMTag, NCEMList, NCEM)
        
        flag_modified(project, "NCEMDefine")
        
        db.add(project)
        db.commit()
        
## 9. NCEMDefine의Count의 가져오기
def NCEMDefineCountLoad(projectName, email):

    project = GetProject(projectName, email)
    NCEMChunkCount = project.NCEMDefine[0]["NCEMChunkCount"]
    NCEMCount = project.NCEMDefine[0]["NCEMCount"]
    Completion = project.NCEMDefine[0]["Completion"]
    
    return NCEMChunkCount, NCEMCount, Completion

## 9. NCEMDefine의 초기화
def InitNCEMDefine(projectName, email):
    ProjectDataPath = GetProjectDataPath()
    with get_db() as db:
    
        project = GetProject(projectName, email)
        project.NCEMDefine[0]["NCEMChunkCount"] = 0
        project.NCEMDefine[0]["NCEMCount"] = 0
        project.NCEMDefine[0]["Completion"] = "No"
        project.NCEMDefine[1] = LoadJsonFrame(ProjectDataPath + "/b532_Context/b532-03_NCEMDefine.json")[1]
        project.NCEMDefine[2] = LoadJsonFrame(ProjectDataPath + "/b532_Context/b532-03_NCEMDefine.json")[2]

        flag_modified(project, "NCEMDefine")
        
        db.add(project)
        db.commit()
        
## 9. 업데이트된 NCEMDefine 출력
def UpdatedNCEMDefine(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        
    return project.NCEMDefine
        
## 9. NCEMDefineCompletion 업데이트
def NCEMDefineCompletionUpdate(projectName, email):
    with get_db() as db:

        project = GetProject(projectName, email)
        project.NCEMDefine[0]["Completion"] = "Yes"

        flag_modified(project, "NCEMDefine")

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
        
## 12. 1-1 CharacterCompletion의 Body(본문) CharacterCompeletions 업데이트 형식
def UpdateCompeletionCharacters(project, CharacterChunkId, ChunkId, Chunk, Character, MainCharacter, AuthorRelationship):    
    updateCharacterCompeletions = {
        "CharacterChunkId": CharacterChunkId,
        "ChunkId": ChunkId,
        "Chunk": Chunk,
        "Character": Character,
        "MainCharacter": MainCharacter,
        "AuthorRelationship": AuthorRelationship
    }
    
    project.CharacterCompletion[1]["CharacterCompeletions"].append(updateCharacterCompeletions)
    project.CharacterCompletion[0]["CharacterChunkCount"] = CharacterChunkId
    
## 12. 1-2 CharacterCompletion의 Body(본문) CharacterCompeletions 업데이트
def AddCharacterCompletionChunksToDB(projectName, email, CharacterChunkId, ChunkId, Chunk, Character, MainCharacter, AuthorRelationship):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        UpdateCompeletionCharacters(project, CharacterChunkId, ChunkId, Chunk, Character, MainCharacter, AuthorRelationship)
        
        flag_modified(project, "CharacterCompletion")
        
        db.add(project)
        db.commit()
        
## 12. 2-1 CharacterCompletion의 Character(부문) CharacterTags부분 업데이트 형식
def updateCheckedCharacterTags(project, CharacterTag, CharacterList, Character):
    # 새롭게 생성되는 CharacterId는 CharacterTags의 Len값과 동일
    CharacterId = len(project.CharacterCompletion[2]["CharacterTags"]) -1
    
    ### 실제 테스크시 수정 요망 ###
    updateCheckedCharacterTags = {
        "CharacterId": CharacterId,
        "CharacterTag": CharacterTag,
        "CharacterList": CharacterList,
        "Character": Character
    }
    
    project.CharacterCompletion[2]["CheckedCharacterTags"].append(updateCheckedCharacterTags)
    project.CharacterCompletion[0]["CharacterCount"] = CharacterId
    
## 12. 2-2 CharacterCompletion의 Character(부문) CharacterTags부분 업데이트
def AddCharacterCompletionCheckedCharacterTagsToDB(projectName, email, CharacterTag, CharacterList, Character):
    with get_db() as db:
        
        project = GetProject(projectName, email)
        updateCheckedCharacterTags(project, CharacterTag, CharacterList, Character)
        
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
        
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    process = 'IndexDefinePreprocess'
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    #########################################################################
    
    project = GetProject(projectName, email)
    print(project.CharacterCompletion)