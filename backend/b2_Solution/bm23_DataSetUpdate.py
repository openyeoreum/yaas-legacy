import sys
sys.path.append("/yaas")

from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddProjectFeedbackDataSets
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LLMFineTuning

#################################
#################################
##### SolutionDataSetUpdate #####
#################################
#################################

### 솔루션에 프로젝트 데이터셋 업데이트 ###
def SolutionDataSetUpdate(email, projectName):
    
    ############################ 하이퍼 파라미터 설정 ############################
    FeedbackDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s112_FeedbackDataSet/"
    CompleteDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s113_CompleteDataSet/"
    TrainingDataSetPath = "/yaas/storage/s1_Yeoreum/s11_ModelFeedback/s114_TrainingDataSet/"
    #########################################################################


    ####################################################
    ### 11_CharacterDefine Feedback 데이터셋 파인튜닝 ###
    ####################################################
    AddProjectFeedbackDataSets(projectName, email, "CharacterDefine", FeedbackDataSetPath, CompleteDataSetPath)
    LLMFineTuning(projectName, email, "11", "CharacterDefine", TrainingDataSetPath, ModelTokens = "Short", Mode = "Example", Epochs = 3)


    # ########################################################
    # ### 12_CharacterCompletion Feedback 데이터셋 파인튜닝 ###
    # ########################################################
    # AddProjectFeedbackDataSets(projectName, email, "CharacterCompletion", FeedbackDataSetPath, CompleteDataSetPath)
    # LLMFineTuning(projectName, email, "05", "CharacterCompletion", TrainingDataSetPath, ModelTokens = "Short", Mode = "Example", Epochs = 3)

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "데미안"
    #########################################################################

    ### Step4 : 솔루션에 프로젝트 데이터셋 학습진행 및 업데이트 ###
    SolutionDataSetUpdate(email, projectName)