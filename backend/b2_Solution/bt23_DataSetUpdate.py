import sys
sys.path.append("/yaas")

from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddProjectFeedbackDataSets
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LLMFineTuning

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "데미안"
    FeedbackDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5122_FeedbackDataSet/"
    CompleteDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5123_CompleteDataSet/"
    TrainingDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5124_TrainingDataSet/"
    #########################################################################

    ####################################################
    ### 10_CharacterDefine Feedback 데이터셋 파인튜닝 ###
    ####################################################
    AddProjectFeedbackDataSets(projectName, email, "CharacterDefine", FeedbackDataSetPath, CompleteDataSetPath)
    LLMFineTuning(projectName, email, "10", "CharacterDefine", TrainingDataSetPath, ModelTokens = "Short", Mode = "Example", Epochs = 3)
    
    # ########################################################
    # ### 11_CharacterCompletion Feedback 데이터셋 파인튜닝 ###
    # ########################################################
    # AddProjectFeedbackDataSets(projectName, email, "CharacterCompletion", FeedbackDataSetPath, CompleteDataSetPath)
    # LLMFineTuning(projectName, email, "05", "CharacterCompletion", TrainingDataSetPath, ModelTokens = "Short", Mode = "Example", Epochs = 3)