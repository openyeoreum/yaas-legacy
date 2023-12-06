import os
import sys
import json
sys.path.append("/yaas")

from sqlalchemy import desc
from backend.b1_Api.b14_Models import Video
from backend.b1_Api.b13_Database import get_db

def GetVideoDataPath(relativePath='../../e4_Database/e42_ProjectData/e424_Video/'):
    CurrentDir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(CurrentDir, relativePath)

def LoadJsonFrame(filepath):
    with open(filepath, 'r') as file:
        DataFrame = json.load(file)
    return DataFrame

def AddVideoToDB(videoSetName, videoSetWriter, videoSetPlatform, videoSetChannel, videoSetLanguage, latestUpdateDate):
    with get_db() as db:
        
        # JSON 데이터 불러오기
        GetVideoDataPath = GetVideoDataPath()
        
        videoFrame = LoadJsonFrame(GetVideoDataPath + "/e4241_RawData/e4241-02_VideoFrame.json")
        videoPreprocess = LoadJsonFrame(GetVideoDataPath + "/e4242_Preprocess/e4242-01_VideoPreprocess.json")
        videoTranslationKo = LoadJsonFrame(GetVideoDataPath + "/e4242_Preprocess/e4242-02_VideoTranslationKo.json")
        videoTranslationEn = LoadJsonFrame(GetVideoDataPath + "/e4242_Preprocess/e4242-03_VideoTranslationEn.json")
        videoContextDefine = LoadJsonFrame(GetVideoDataPath + "/e4243_Context/e4243-01_VideoContextDefine.json")
        videoContextCompletion = LoadJsonFrame(GetVideoDataPath + "/e4242_Preprocess/e4243-02_VideoContextCompletion.json")
        videoNCEMDefine = LoadJsonFrame(GetVideoDataPath + "/e4243_Context/e4243-03_VideoNCEMDefine.json")
        videoNCEMMatching = LoadJsonFrame(GetVideoDataPath + "/e4243_Context/e4243-04_VideoNCEMMatching.json")
        ### 아래로 추가되는 프롬프트 작성 ###

        ExistingVideo = db.query(Video).filter(Video.VideoSetName == videoSetName, Video.VideoSetWriter == videoSetWriter, Video.LatestUpdateDate == latestUpdateDate).order_by(desc(Video.LatestUpdateDate)).first()

        # DB Commit
        if ExistingVideo:
                ExistingVideo.VideoSetName = videoSetName
                ExistingVideo.VideoSetWriter = videoSetWriter
                ExistingVideo.VideoSetPlatform = videoSetPlatform
                ExistingVideo.VideoSetChannel = videoSetChannel
                ExistingVideo.VideoSetLanguage = videoSetLanguage
                ExistingVideo.LatestUpdateDate = latestUpdateDate
                ExistingVideo.VideoFrame = videoFrame
                ExistingVideo.VideoPreprocess = videoPreprocess
                ExistingVideo.VideoTranslationKo = videoTranslationKo
                ExistingVideo.VideoTranslationEn = videoTranslationEn
                ExistingVideo.VideoContextDefine = videoContextDefine
                ExistingVideo.VideoContextCompletion = videoContextCompletion
                ExistingVideo.VideoNCEMDefine = videoNCEMDefine
                ExistingVideo.VideoNCEMMatching = videoNCEMMatching
                ### 아래로 추가되는 프롬프트 작성 ###
                
                print(f"[ ExtensionProject | AddVideoToDB 변경사항 업데이트 ]")
        else:
            Video = Video(
                VideoSetName = videoSetName,
                VideoSetWriter = videoSetWriter,
                VideoSetPlatform = videoSetPlatform,
                VideoSetChannel = videoSetChannel,
                VideoSetLanguage = videoSetLanguage,
                LatestUpdateDate = latestUpdateDate,
                VideoFrame = videoFrame,
                VideoPreprocess = videoPreprocess,
                VideoTranslationKo = videoTranslationKo,
                VideoTranslationEn = videoTranslationEn,
                VideoContextDefine = videoContextDefine,
                VideoContextCompletion = videoContextCompletion,
                VideoNCEMDefine = videoNCEMDefine,
                VideoNCEMMatching = videoNCEMMatching
                ### 아래로 추가되는 프롬프트 작성 ###
                )
            db.add(Video)
            print(f"[ ExtensionProject | AddVideoToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":   
    
    AddVideoToDB("MaumMeditation", "Hoe-Jun Jeong", "Youtube", "MeditationLifeOrg", "Ko", 23120601)