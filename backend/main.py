import os
import sys
sys.path.append("/yaas")

from b2_Solution.bm21_GeneralUpdate import AccountUpdate, SolutionProjectUpdate
from b2_Solution.bm22_DataFrameUpdate import SolutionDataFrameUpdate
from b2_Solution.bm23_DataSetUpdate import SolutionDataSetUpdate

### Main1 : 솔루션 업데이트 ###
def SolutionUpdate(email, projectNameList, MessagesReview):

    if isinstance(projectNameList, list):
        for projectName in projectNameList:

            ### Step2 : 솔루션에 프로젝트 파일 업데이트 ###
            SolutionProjectUpdate(email, projectName)
            
            ### Step3 : 솔루션에 프로젝트 데이터 프레임 진행 및 업데이트 업데이트 ###
            SolutionDataFrameUpdate(email, projectName, messagesReview = MessagesReview)
            
            # ### Step4 : 솔루션에 프로젝트 데이터셋 학습진행 및 업데이트 업데이트 ###
            # SolutionDataSetUpdate(email, projectName)
    
    else:
        ### Step2 : 솔루션에 프로젝트 파일 업데이트 ###
        SolutionProjectUpdate(email, projectName)
        
        ### Step3 : 솔루션에 프로젝트 데이터 프레임 진행 및 업데이트 업데이트 ###
        SolutionDataFrameUpdate(email, projectName, messagesReview = MessagesReview)
        
        # ### Step4 : 솔루션에 프로젝트 데이터셋 학습진행 및 업데이트 업데이트 ###
        # SolutionDataSetUpdate(email, projectName)

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    name = "yeoreum"
    password = "0128"
    projectNameList = ['노인을위한나라는있다'] # , '데미안', '빨간머리앤', '웹3.0메타버스', '나는선비로소이다', '나는노비로소이다', '카이스트명상수업', '우리는행복을진단한다', '웹3.0메타버스', '살아서천국극락낙원에가는방법']
    MessagesReview = "on"
    #########################################################################

    AccountUpdate(email, name, password)
    SolutionUpdate(email, projectNameList, MessagesReview)