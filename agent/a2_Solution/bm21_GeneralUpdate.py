import sys
sys.path.append("/yaas")

from agent.a2_Solution.a21_General.a211_Access import SetupProjectAccess
from agent.a2_Solution.a21_General.a212_Project import SetupProject
from agent.a2_Solution.a21_General.a213_TrainingDataset import SetupTrainingDataset

#################################
#################################
##### SolutionGeneralUpdate #####
#################################
#################################

### 솔루션에 계정 업데이트 ###
def AccountUpdate(email, projectName):

    ### a211_Access ###
    SetupProjectAccess(projectName, email)

### 솔루션에 프로젝트 업데이트 ###
def SolutionProjectUpdate(email, projectName):

    ### a212_ProjectCommit ###
    SetupProject(projectName, email)

    ### a213_TrainingDatasetCommit ###
    SetupTrainingDataset(projectName, email)

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