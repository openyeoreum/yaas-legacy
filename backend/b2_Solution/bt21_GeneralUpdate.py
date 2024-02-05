import sys
sys.path.append("/yaas")

from backend.b2_Solution.b21_General.b212_PromptCommit import AddPromptToDB
from backend.b2_Solution.b21_General.b213_TrainingDatasetCommit import AddTrainingDatasetToDB
from backend.b2_Solution.b21_General.b214_VoiceDatasetCommit import AddVoiceDataSetToDB
from backend.b2_Solution.b22_User.b221_UserCommit import AddUserToDB
from backend.b2_Solution.b22_User.b223_ProjectsStorageCommit import AddProjectsStorageToDB
from backend.b2_Solution.b23_Project.b231_ProjectCommit import AddProjectToDB
from backend.b2_Solution.b23_Project.b232_ProjectFileCommit import MoveTextFile, AddTextToDB

#################################
#################################
##### SolutionGeneralUpdate #####
#################################
#################################

### 솔루션에 계정 업데이트 ###
def SolutionAccountUpdate(email, name, password):

    ### b212_PromptCommit ###
    AddPromptToDB()
    
    ### b214_PromptCommit ###
    AddVoiceDataSetToDB()

    ### b221_UserCommit ###
    AddUserToDB(email, name, password)
    # AddUserToDB('junsun0128@gmail.com', 'junyoung', '0128')
    # AddUserToDB('ahyeon0128@gmail.com', 'ahyeon', '0128')

    ### b223_ProjectsStorageCommit ###
    AddProjectsStorageToDB(name, email)
    # AddProjectsStorageToDB('junyoung', 'junsun0128@gmail.com')
    # AddProjectsStorageToDB('ahyeon', 'ahyeon0128@gmail.com')

### 솔루션에 프로젝트 업데이트 ###
def SolutionProjectUpdate(email, projectName):

    ### b232_ProjectCommit ###
    AddProjectToDB(projectName, email)
    # AddProjectToDB('빨간머리앤', email)
    # AddProjectToDB('웹3.0메타버스', email)
    # AddProjectToDB('나는선비로소이다', email)
    # AddProjectToDB('나는노비로소이다', email)
    # AddProjectToDB('카이스트명상수업', email)
    # AddProjectToDB('우리는행복을진단한다', email)
    # AddProjectToDB('살아서천국극락낙원에가는방법', email)

    ### b233_ProjectFileCommit ###
    # AddTextToDB
    AddTextToDB(projectName, email)
    # AddTextToDB('빨간머리앤', email)
    # AddTextToDB('웹3.0메타버스', email)
    # AddTextToDB('나는선비로소이다', email)
    # AddTextToDB('나는노비로소이다', email)
    # AddTextToDB('카이스트명상수업', email)
    # AddTextToDB('우리는행복을진단한다', email)
    # AddTextToDB('살아서천국극락낙원에가는방법', email)

    ### b212_TrainingDatasetCommit ###
    AddTrainingDatasetToDB(projectName, email)
    # AddTrainingDatasetToDB('빨간머리앤', email)
    # AddTrainingDatasetToDB('웹3.0메타버스', email)
    # AddTrainingDatasetToDB('나는선비로소이다', email)
    # AddTrainingDatasetToDB('나는노비로소이다', email)
    # AddTrainingDatasetToDB('카이스트명상수업', email)
    # AddTrainingDatasetToDB('우리는행복을진단한다', email)
    # AddTrainingDatasetToDB('살아서천국극락낙원에가는방법', email)

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    name = "yeoreum"
    password = "0128"
    projectNameList = ['데미안', '빨간머리앤', '웹3.0메타버스', '나는선비로소이다', '나는노비로소이다', '카이스트명상수업', '우리는행복을진단한다', '웹3.0메타버스', '살아서천국극락낙원에가는방법']
    #########################################################################
    
    SolutionAccountUpdate(email, name, password)
    for projectName in projectNameList:
        SolutionProjectUpdate(email, projectName)