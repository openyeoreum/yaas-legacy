import sys
sys.path.append("/yaas")

from agent.a2_Solution.a21_General.a212_PromptCommit import AddPromptToDB
from agent.a2_Solution.a21_General.a213_TrainingDatasetCommit import AddTrainingDatasetToDB
from agent.a2_Solution.a21_General.a214_SoundDatasetCommit import AddSoundDataSetToDB
from agent.a2_Solution.a21_General.a215_UserCommit import AddUserToDB
from agent.a2_Solution.a21_General.a217_ProjectsStorageCommit import AddProjectsStorageToDB
from agent.a2_Solution.a21_General.a218_ProjectCommit import AddProjectToDB
from agent.a2_Solution.a21_General.a219_ProjectFileCommit import AddTextToDB

#################################
#################################
##### SolutionGeneralUpdate #####
#################################
#################################

### 솔루션에 계정 업데이트 ###
def AccountUpdate(email, name, password):

    ### a212_PromptCommit ###
    AddPromptToDB()
    
    ### a214_SoundDataSetCommit ###
    AddSoundDataSetToDB()

    ### a215_UserCommit ###
    AddUserToDB(email, name, password)
    # AddUserToDB('junsun0128@gmail.com', 'junyoung', '0128')
    # AddUserToDB('ahyeon0128@gmail.com', 'ahyeon', '0128')

    ### a217_ProjectsStorageCommit ###
    AddProjectsStorageToDB(email)
    # AddProjectsStorageToDB('junyoung', 'junsun0128@gmail.com')
    # AddProjectsStorageToDB('ahyeon', 'ahyeon0128@gmail.com')

### 솔루션에 프로젝트 업데이트 ###
def SolutionProjectUpdate(email, projectName):

    ### a218_ProjectCommit ###
    AddProjectToDB(projectName, email)
    # AddProjectToDB('빨간머리앤', email)
    # AddProjectToDB('웹3.0메타버스', email)
    # AddProjectToDB('나는선비로소이다', email)
    # AddProjectToDB('나는노비로소이다', email)
    # AddProjectToDB('카이스트명상수업', email)
    # AddProjectToDB('우리는행복을진단한다', email)
    # AddProjectToDB('살아서천국극락낙원에가는방법', email)
    
    ### a219_ProjectsStorageCommit ###
    AddTextToDB(projectName, email)

    ### a212_TrainingDatasetCommit ###
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
    projectNameList = ['노인을위한나라는있다', '데미안', '빨간머리앤', '웹3.0메타버스', '나는선비로소이다', '나는노비로소이다', '카이스트명상수업', '우리는행복을진단한다', '웹3.0메타버스', '살아서천국극락낙원에가는방법']
    #########################################################################
    
    ### Step1 : 솔루션에 계정 업데이트 ###
    AccountUpdate(email, name, password)
    
    ### Step2 : 솔루션에 프로젝트 파일 업데이트 ###
    for projectName in projectNameList:
        SolutionProjectUpdate(email, projectName)