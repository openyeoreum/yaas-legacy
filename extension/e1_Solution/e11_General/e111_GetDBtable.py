import sys
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import LifeGraph, Video, ExtensionPrompt
from backend.b1_Api.b13_Database import get_db

def GetLifeGraph(lifeGraphSetName, latestUpdateDate):
    with get_db() as db:       
        LifeGraphFrame = db.query(LifeGraph).filter(LifeGraph.LifeGraphSetName == lifeGraphSetName, LifeGraph.LatestUpdateDate == latestUpdateDate).first()
    return LifeGraphFrame

def GetVideo(videoSetName, latestUpdateDate):
    with get_db() as db:
        VideoFrame = db.query(Video).filter(LifeGraph.VideoSetName == videoSetName, LifeGraph.LatestUpdateDate == latestUpdateDate).first()
    return VideoFrame

def GetExtensionPromptFrame(Process):
    with get_db() as db:
        column = getattr(ExtensionPrompt, Process, None)
        if column is None:
            raise ValueError(f"No such column: {Process}")
        
        # order_by를 사용해 PromptId 기준으로 내림차순 정렬 후 첫 번째 행을 가져옵니다.
        extensionPromptFrame = db.query(column).first()
    return extensionPromptFrame
        
if __name__ == "__main__":
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################
    
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    lifeGraph.LifeGraphSets
    print(len(lifeGraph.LifeGraphSets))