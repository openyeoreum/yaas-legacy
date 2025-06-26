import os
import sys
import json
sys.path.append("/yaas")

from agent.a1_Connector.a13_Models import SoundDataSet
from agent.a1_Connector.a12_Database import get_db

def GetRelationalDataPath():
    RootPath = "/yaas"
    DataPath = "agent/a5_Database/a57_RelationalDatabase"
    return os.path.join(RootPath, DataPath)

def LoadJsonFrame(filepath):
    with open(filepath, 'r') as file:
        DataFrame = json.load(file)
    return DataFrame

def AddSoundDataSetToDB():
    with get_db() as db:
        
        # JSON 데이터 불러오기
        RelationalDataPath = GetRelationalDataPath()
        
        voiceDataSet = LoadJsonFrame(RelationalDataPath + "/a572_Character/a572-01_VoiceDataSet.json")
        logoDataSet = LoadJsonFrame(RelationalDataPath + "/a573_Logo/a573-01_LogoDataSet.json")
        introDataSet = LoadJsonFrame(RelationalDataPath + "/a574_Intro/a574-01_IntroDataSet.json")
        titleMusicDataSet = LoadJsonFrame(RelationalDataPath + "/a575_Music/a575-01_TitleMusicDataSet.json")
        ### 아래로 추가되는 데이터셋 작성 ###

        ExistingSoundDataSet = db.query(SoundDataSet).first()

        # DB Commit
        if ExistingSoundDataSet:
            ExistingSoundDataSet.VoiceDataSet = voiceDataSet
            ExistingSoundDataSet.LogoDataSet = logoDataSet
            ExistingSoundDataSet.IntroDataSet = introDataSet
            ExistingSoundDataSet.TitleMusicDataSet = titleMusicDataSet
            ### 아래로 추가되는 데이터셋 작성 ###
            
            print(f"[ General | AddExistingSoundDataSetToDB 변경사항 업데이트 ]")
        else:
            soundDataSet = SoundDataSet(
                VoiceDataSet = voiceDataSet,
                LogoDataSet = logoDataSet,
                IntroDataSet = introDataSet,
                TitleMusicDataSet = titleMusicDataSet
                ### 아래로 추가되는 데이터셋 작성 ###
                )
            db.add(soundDataSet)
            print(f"[ General | AddSoundDataSetToDB 완료 ]")
        db.commit()

if __name__ == "__main__":   
    
    AddSoundDataSetToDB()