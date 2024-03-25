import os
import sys
import json
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import VoiceDataSet
from backend.b1_Api.b13_Database import get_db

def GetRelationalDataPath():
    RootPath = "/yaas"
    DataPath = "backend/b5_Database/b57_RelationalDatabase"
    return os.path.join(RootPath, DataPath)

def LoadJsonFrame(filepath):
    with open(filepath, 'r') as file:
        DataFrame = json.load(file)
    return DataFrame

def AddSoundDataSetToDB():
    with get_db() as db:
        
        # JSON 데이터 불러오기
        RelationalDataPath = GetRelationalDataPath()
        
        typeCastVoiceDataSet = LoadJsonFrame(RelationalDataPath + "/b572_Character/b572-01_TypeCastVoiceDataSet.json")
        logoDataSet = LoadJsonFrame(RelationalDataPath + "/b573_Logo/b573-01_LogoDataSet.json")
        introDataSet = LoadJsonFrame(RelationalDataPath + "/b574_Intro/b574-01_IntroDataSet.json")
        titleMusicDataSet = LoadJsonFrame(RelationalDataPath + "/b575_Music/b575-01_TitleMusicDataSet.json")
        partMusicDataSet = LoadJsonFrame(RelationalDataPath + "/b575_Music/b575-02_PartMusicDataSet.json")
        indexMusicDataSet = LoadJsonFrame(RelationalDataPath + "/b575_Music/b575-03_IndexMusicDataSet.json")
        ### 아래로 추가되는 데이터셋 작성 ###

        ExistingVoiceDataSet = db.query(VoiceDataSet).first()

        # DB Commit
        if ExistingVoiceDataSet:
                ExistingVoiceDataSet.TypeCastVoiceDataSet = typeCastVoiceDataSet
                ExistingVoiceDataSet.LogoDataSet = logoDataSet
                ExistingVoiceDataSet.IntroDataSet = introDataSet
                ExistingVoiceDataSet.TitleMusicDataSet = titleMusicDataSet
                ExistingVoiceDataSet.PartMusicDataSet = partMusicDataSet
                ExistingVoiceDataSet.IndexMusicDataSet = indexMusicDataSet
                ### 아래로 추가되는 데이터셋 작성 ###
                
                print(f"[ General | AddExistingSoundDataSetToDB 변경사항 업데이트 ]")
        else:
            voiceDataSet = VoiceDataSet(
                TypeCastVoiceDataSet = typeCastVoiceDataSet,
                LogoDataSet = logoDataSet,
                IntroDataSet = introDataSet,
                TitleMusicDataSet = titleMusicDataSet,
                PartMusicDataSet = partMusicDataSet,
                IndexMusicDataSet = indexMusicDataSet
                )
            db.add(voiceDataSet)
            print(f"[ General | AddSoundDataSetToDB 완료 ]")
        db.commit()

if __name__ == "__main__":   
    
    AddSoundDataSetToDB()