import sys
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import LifeGraph, Video, ExtensionPrompt
from backend.b1_Api.b13_Database import get_db

def GetLifeGraphFrame(Process):
    with get_db() as db:
        column = getattr(LifeGraph, Process, None)
        if column is None:
            raise ValueError(f"No such column: {Process}")
        
        # order_by를 사용해 PromptId 기준으로 내림차순 정렬 후 첫 번째 행을 가져옵니다.
        LifeGraphFrame = db.query(column).first()
    return LifeGraphFrame

def GetVideoFrame(Process):
    with get_db() as db:
        column = getattr(Video, Process, None)
        if column is None:
            raise ValueError(f"No such column: {Process}")
        
        # order_by를 사용해 PromptId 기준으로 내림차순 정렬 후 첫 번째 행을 가져옵니다.
        VideoFrame = db.query(column).first()
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
    
    GetLifeGraphFrame("IndexDefinePreprocess")