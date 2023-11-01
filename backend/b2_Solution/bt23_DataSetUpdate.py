import sys
sys.path.append("/yaas")

from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2413_DataSetCommit import AddProjectFeedbackDataSets

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "우리는행복을진단한다"
    process = 'IndexDefinePreprocess'
    DataFramePath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b511_DataFrame/"
    RawDataSetPath = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5121_RawDataSet/"
    CompleteDataSet = "/yaas/backend/b5_Database/b51_DatabaseFeedback/b512_DataSet/b5122_CompleteDataSet/"
    #########################################################################