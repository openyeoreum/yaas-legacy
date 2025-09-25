import os
import json
import sys
sys.path.append("/yaas")

### ProjectList.json 경로 불러오기 ###
def LoadProjectListPath():
    return f'/yaas/storage/s1_Yeoreum/s12_UserStorage/s121_Projects.json'

### Project_ProjectAccess.json 경로 불러오기 ###
def LoadProjectAccessPath(projectName, email):
    return f'/yaas/storage/s1_Yeoreum/s12_UserStorage/s122_Access/{email}_{projectName}_Access.json'

### ProjectStorage 기본 경로 불러오기 ###
def LoadProjectStoragePath(email):
    return f'/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}'

### ProjectAccess 생성 ###
def SetupProjectAccess(projectName, email):
    ## 1. Project_ProjectAccess.json 경로 불러오기
    ProjectListPath = LoadProjectListPath()
    ProjectAccessJsonPath = LoadProjectAccessPath(projectName, email)
    ProjectStoragePath = LoadProjectStoragePath(email)
    
    ## 2. ProjectList 업데이트
    with open(ProjectListPath, 'r', encoding='utf-8') as ProjectListJson:
        ProjectListData = json.load(ProjectListJson)
    
    if f"{email}_{projectName}" not in ProjectListData:
        ProjectListData.append(f"{email}_{projectName}")
        
    with open(ProjectListPath, 'w', encoding='utf-8') as ProjectListJson:
        json.dump(ProjectListData, ProjectListJson, ensure_ascii=False, indent=4)

    ## 3. 최초 ProjectAccessData 생성
    ProjectAccessData = {'ProjectName': projectName, 'ProjectNameHistory': [projectName], 'Email': email}

    ## 4. Project_ProjectAccess.json이 없을 때만 생성
    ## 4-1. Project_ProjectAccess.json 생성
    if not os.path.exists(ProjectAccessJsonPath):
        with open(ProjectAccessJsonPath, 'w', encoding = 'utf-8') as ProjectAccessJson:
            json.dump(ProjectAccessData, ProjectAccessJson, ensure_ascii = False, indent = 4)
        
        ## 4-2. ProjectStorage 폴더 생성
        if not os.path.exists(ProjectStoragePath):
            os.makedirs(ProjectStoragePath, exist_ok = True)

        print(f"[ Email: {email} | Project: {projectName} | CreateProjectAccess 완료 ]")
    else:
        print(f"[ Email: {email} | Project: {projectName} | CreateProjectAccess가 이미 완료됨 ]")

### ProjectAccess projectName 수정 ###
def UpdateProjectAccessName(projectName, newProjectName, email):
    ## 1. Project_ProjectAccess.json 경로 불러오기
    ProjectAccessJsonPath = LoadProjectAccessPath(projectName, email)
    ProjectPath = LoadProjectStoragePath(email) + f'/{projectName}'
    
    ## 2. Project_ProjectAccess.json 불러오기
    if not os.path.exists(ProjectAccessJsonPath):
        return None
    else:
        with open(ProjectAccessJsonPath, 'r', encoding = 'utf-8') as ProjectAccessJson:
            ProjectAccessData = json.load(ProjectAccessJson)

    ## 3. projectName 수정
    if 'ProjectName' in ProjectAccessData:
        ProjectAccessData['ProjectName'] = newProjectName
        ProjectAccessData['ProjectNameHistory'].append(newProjectName)

    ## 4. Project_ProjectAccess.json에 저장
    with open(ProjectAccessJsonPath, 'w', encoding = 'utf-8') as ProjectAccessJson:
        json.dump(ProjectAccessData, ProjectAccessJson, ensure_ascii = False, indent = 4)

    ## 5. Project 폴더트리 이름 변경
    if os.path.exists(ProjectPath):
        newProjectPath = LoadProjectStoragePath(email) + f'/{newProjectName}'
        os.rename(ProjectPath, newProjectPath)

### ProjectAccess 불러오기 ###
def LoadProjectAccess(projectName, email, Key):
    ## 1. Project_ProjectAccess.json 경로 불러오기
    ProjectAccessJsonPath = LoadProjectAccessPath(projectName, email)
    
    ## 2. Project_ProjectAccess.json 불러오기
    if not os.path.exists(ProjectAccessJsonPath):
        return None
    else:
        with open(ProjectAccessJsonPath, 'r', encoding = 'utf-8') as ProjectAccessJson:
            ProjectAccessData = json.load(ProjectAccessJson)

    ## 3. ProjectAccessData에서 Key에 해당하는 값 반환
    if Key not in ProjectAccessData:
        return None
    else:
        return ProjectAccessData[Key]
    
### ProjectAccess 업데이트 ###
def UpdateProjectAccess(projectName, email, Key, Value):
    ## 1. Project_ProjectAccess.json 경로 불러오기
    ProjectAccessJsonPath = LoadProjectAccessPath(projectName, email)

    ## 2. Project_ProjectAccess.json 불러오기
    if not os.path.exists(ProjectAccessJsonPath):
        return None
    else:
        with open(ProjectAccessJsonPath, 'r', encoding = 'utf-8') as ProjectAccessJson:
            ProjectAccessData = json.load(ProjectAccessJson)

    ## 3. ProjectAccessData 업데이트
    ProjectAccessData[Key] = Value

    ## 4. Project_ProjectAccess.json에 저장
    with open(ProjectAccessJsonPath, 'w', encoding = 'utf-8') as ProjectAccessJson:
        json.dump(ProjectAccessData, ProjectAccessJson, ensure_ascii = False, indent = 4)

### ProjectAccess 통제 ### <- 해당 부분은 프로젝트를 어디서부터 시작할지에 대한 통제 
