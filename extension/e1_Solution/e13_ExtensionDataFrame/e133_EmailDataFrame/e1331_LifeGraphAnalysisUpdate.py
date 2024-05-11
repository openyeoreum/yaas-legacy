import re
import json
import tiktoken
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from extension.e1_Solution.e11_General.e111_GetDBtable import GetExtensionPromptFrame
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraph
from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import LoadExtensionOutputMemory, SaveExtensionOutputMemory, AddExistedLifeGraphContextDefineToDB, AddLifeGraphContextDefineContextChunksToDB, AddLifeGraphContextDefineLifeDataContextTextsToDB, LifeGraphContextDefineCountLoad, InitLifeGraphContextDefine, LifeGraphContextDefineCompletionUpdate, UpdatedLifeGraphContextDefine

#########################
##### InputList 생성 #####
#########################
## LifeGraphTranslationKo 로드
def LoadLifeGraphsEn(lifeGraphSetName, latestUpdateDate):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphsEn = lifeGraph.LifeGraphTranslationEn[1]['LifeGraphsEn'][1:]
    LifeGraphs = lifeGraph.LifeGraphFrame[1]['LifeGraphs'][1:]
    
    return LifeGraphsEn, LifeGraphs

## LoadLifeGraphsEn의 inputList 치환
def LoadLifeGraphsEnToInputList(lifeGraphSetName, latestUpdateDate):
    LifeGraphsEn, LifeGraphs = LoadLifeGraphsEn(lifeGraphSetName, latestUpdateDate)
    
    InputList = []
    for i in range(len(LifeGraphsEn)):
        LifeGraphDate = LifeGraphsEn[i]['LifeGraphDate']
        Name = LifeGraphsEn[i]['Name']
        Age = LifeGraphsEn[i]['Age']
        Residence = LifeGraphsEn[i]['Residence']['Area']

        if Translation != 'ko':
            Tag = 'Pass'
        else:
            Tag = 'Continue'
            
        InputDic = {'Id': Id, Tag: TextKo}
        InputList.append(InputDic)
        
    return InputList
    
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################
    
    LoadLifeDataTextsKo(lifeGraphSetName, latestUpdateDate)