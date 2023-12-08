import re
import tiktoken
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraphFrame
from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import AddExistedLifeGraphFrameToDB, AddLifeGraphFrameLifeGraphsToDB, AddLifeGraphFrameLifeDataToDB, LifeGraphFrameCountLoad, InitLifeGraphFrame, UpdatedLifeGraphFrame, LifeGraphFrameCompletionUpdate

# LifeGraphSet 로드
def LoadLifeGraphSet(Process):
    lifeGraph = GetLifeGraphFrame(Process)
    lifeGraphSets = lifeGraph.LifeGraphSets
    
    return lifeGraphSets

## Body최초 전처리

if __name__ == "__main__":
    ############################ 하이퍼 파라미터 설정 ############################
    process = 'LifeGraphFrame'
    LifeGraphFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData"
    #########################################################################
    lifeGraph = LoadLifeGraphSet(process)
    print(len(lifeGraph))