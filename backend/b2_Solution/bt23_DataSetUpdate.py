import sys
sys.path.append("/yaas")

from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddProjectFeedbackDataSets
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LLMFineTuning

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    FeedbackDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5122_FeedbackDataSet/"
    CompleteDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5123_CompleteDataSet/"
    TrainingDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5124_TrainingDataSet/"
    #########################################################################

    ####################################################
    ### 04_BodyCharacterDefine Feedback 데이터셋 파인튜닝 ###
    ####################################################
    AddProjectFeedbackDataSets(projectName, email, "BodyCharacterDefine", FeedbackDataSetPath, CompleteDataSetPath)
    LLMFineTuning(projectName, email, "04", "BodyCharacterDefine", TrainingDataSetPath, ModelTokens = "Short", Mode = "Example", Epochs = 3)